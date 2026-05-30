"""
Multi-Modal RAG Chatbot  –  app.py
Fixes:
  1. Infinite loop — use session-state flag to track "message already sent"
  2. Gemini model names — updated to gemini-2.0-flash / gemini-2.5-flash
  3. Data preview — show 5 rows + schema when data loads
"""

import os
import warnings
# Suppress benign warnings and transformers __path__ access messages
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*Accessing.*__path__.*")

import streamlit as st
from dotenv import load_dotenv

from htmlTemplates import css, user_msg_html, bot_msg_html
from modules.input_handler import handle_inputs
from modules.bigquery_loader import load_data_from_bigquery, credentials_available, credentials_filename
from modules.langchain_engine import (
    get_llm,
    add_texts_to_vectorstore,
    handle_user_query,
    reset_vectorstore,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Multi-Modal RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(css, unsafe_allow_html=True)
load_dotenv()

# ── Session-state defaults ────────────────────────────────────────────────────
def _init(key, val):
    if key not in st.session_state:
        st.session_state[key] = val

_init("chat_history",    [])
_init("dataframes",      {})
_init("bq_queries",      [{"name": "Query 1", "sql": ""}])
_init("provider",        "OpenRouter")
_init("model_name",      os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo"))
_init("api_key",         os.getenv("OPENROUTER_API_KEY", ""))
_init("_pending_query",  None)   # anti-loop flag
_init("_input_counter",  0)       # incremented to reset the text input widget

# ── Default models per provider ───────────────────────────────────────────────
PROVIDER_DEFAULTS = {
    "OpenRouter": "openai/gpt-3.5-turbo",
    "OpenAI":     "gpt-4o-mini",
    "Gemini":     "gemini-2.0-flash",
}

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div style="font-size:1.3rem;font-weight:700;color:#ff7a00;margin-bottom:0.2rem;">🤖 RAG Chatbot</div>'
        '<div style="font-size:0.78rem;color:#888;margin-bottom:1.2rem;">Multi-Modal · BigQuery · Analytics</div>',
        unsafe_allow_html=True,
    )

    # ── File & Web ──────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">📂 File & Web Sources</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Docs, Images, CSVs, Excel",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt", "csv", "xlsx", "xls"],
        label_visibility="collapsed",
    )
    youtube_url = st.text_input("🎬 YouTube URL", placeholder="https://youtube.com/watch?v=...")
    website_url = st.text_input("🌐 Website URL", placeholder="https://example.com")

    if st.button("⚡ Extract & Index", use_container_width=True, type="primary"):
        if not (uploaded_files or youtube_url or website_url):
            st.warning("Add at least one source first.")
        else:
            with st.status("Processing sources…", expanded=True) as status:
                texts, dfs = handle_inputs(uploaded_files, youtube_url, website_url)
                if texts:
                    st.write(f"Indexing {len(texts)} text chunk(s)…")
                    add_texts_to_vectorstore(texts)
                for df_dict in dfs:
                    lbl = df_dict["name"]
                    st.session_state.dataframes[lbl] = df_dict["df"]
                    st.write(f"Loaded **{lbl}** — {len(df_dict['df'])} rows")
                status.update(label="Done!", state="complete")
            st.toast("Data indexed!", icon="✅")

    # ── BigQuery ────────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">☁️ BigQuery</div>', unsafe_allow_html=True)

    if credentials_available():
        st.success(f"🔑 Auto-detected: **{credentials_filename()}**", icon="✅")
        bq_json = st.file_uploader("Override credentials (optional)", type=["json"],
                                   key="bq_json_up", label_visibility="collapsed")
    else:
        st.caption("💡 Place JSON in `credentials/` folder to skip uploading each time.")
        bq_json = st.file_uploader("Service Account JSON", type=["json"],
                                   key="bq_json_up", label_visibility="collapsed")

    # ── Multiple SQL queries ────────────────────────────────────────────────
    st.markdown("**SQL Queries**")
    st.caption("Each query loads a named dataset. AI can join them automatically.")

    queries = st.session_state.bq_queries
    for i, q in enumerate(queries):
        col_name, col_del = st.columns([3, 1])
        with col_name:
            queries[i]["name"] = st.text_input(
                "Name", value=q["name"], key=f"qname_{i}",
                label_visibility="collapsed", placeholder=f"Dataset {i+1} name",
            )
        with col_del:
            if len(queries) > 1 and st.button("✕", key=f"del_q_{i}", help="Remove"):
                st.session_state.bq_queries.pop(i)
                st.rerun()
        queries[i]["sql"] = st.text_area(
            "SQL", value=q["sql"], key=f"qsql_{i}", height=80,
            label_visibility="collapsed",
            placeholder="SELECT * FROM `project.dataset.table` LIMIT 1000",
        )

    col_add, col_load = st.columns(2)
    with col_add:
        if st.button("+ Add Query", use_container_width=True):
            n = len(st.session_state.bq_queries) + 1
            st.session_state.bq_queries.append({"name": f"Query {n}", "sql": ""})
            st.rerun()

    with col_load:
        if st.button("Load All", use_container_width=True, type="primary"):
            json_content = bq_json.getvalue().decode() if bq_json else None
            any_loaded = False
            with st.status("Loading BigQuery data…", expanded=True) as bq_status:
                for q in st.session_state.bq_queries:
                    if not q["sql"].strip():
                        st.write(f"Skipping **{q['name']}** — empty SQL.")
                        continue
                    st.write(f"Running **{q['name']}**…")
                    df, err = load_data_from_bigquery(json_content, q["sql"])
                    if err:
                        st.error(f"{q['name']}: {err}")
                    else:
                        lbl = q["name"] or f"BQ_{len(st.session_state.dataframes)+1}"
                        st.session_state.dataframes[lbl] = df
                        st.write(f"Loaded **{lbl}** — {len(df):,} rows, {len(df.columns)} cols")
                        any_loaded = True
                bq_status.update(
                    label="All done!" if any_loaded else "Nothing loaded.",
                    state="complete" if any_loaded else "error",
                )
            if any_loaded:
                st.toast("BigQuery data loaded!", icon="✅")

    # ── Loaded datasets ─────────────────────────────────────────────────────
    if st.session_state.dataframes:
        st.markdown('<div class="sidebar-section">📋 Loaded Datasets</div>', unsafe_allow_html=True)
        for name, df in st.session_state.dataframes.items():
            with st.expander(f"**{name}** — {len(df):,} rows × {len(df.columns)} cols"):
                st.dataframe(df.head(5), use_container_width=True)
                st.caption(f"Columns: {', '.join(df.columns.tolist())}")

    st.divider()
    if st.button("🗑️ Reset Session", use_container_width=True):
        reset_vectorstore()
        st.session_state.chat_history   = []
        st.session_state.dataframes     = {}
        st.session_state.bq_queries     = [{"name": "Query 1", "sql": ""}]
        st.session_state._pending_query = None
        st.toast("Session reset!", icon="🗑️")
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# MAIN AREA
# ═══════════════════════════════════════════════════════════════════════════
st.markdown(
    '''<div class="app-header">
        <div>
            <h1>🤖 Multi-Modal RAG Chatbot</h1>
            <p>Ask questions about your documents, spreadsheets, BigQuery data, YouTube videos &amp; websites.</p>
        </div>
    </div>''',
    unsafe_allow_html=True,
)

tab_chat, tab_settings = st.tabs(["💬 Chat", "⚙️ Settings"])

# ── SETTINGS TAB ─────────────────────────────────────────────────────────────
with tab_settings:
    st.subheader("LLM Configuration")
    col1, col2 = st.columns(2)

    with col1:
        provider = st.selectbox(
            "Provider",
            ["OpenRouter", "OpenAI", "Gemini"],
            index=["OpenRouter", "OpenAI", "Gemini"].index(st.session_state.provider),
        )
        model_name = st.text_input(
            "Model Name",
            value=st.session_state.model_name
                  if st.session_state.provider == provider
                  else PROVIDER_DEFAULTS[provider],
        )

    with col2:
        api_key = st.text_input("API Key", type="password", value=st.session_state.api_key)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Settings", type="primary"):
            st.session_state.provider   = provider
            st.session_state.model_name = model_name
            st.session_state.api_key    = api_key
            st.toast("Settings saved!", icon="✅")

    st.divider()
    st.subheader("Provider & Model Guide")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="info-card"><h4>OpenRouter</h4>'
            'Models: <code>openai/gpt-4o-mini</code>, <code>anthropic/claude-3.5-sonnet</code><br>'
            'Keys at openrouter.ai</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(
            '<div class="info-card"><h4>OpenAI</h4>'
            'Models: <code>gpt-4o</code>, <code>gpt-4o-mini</code><br>'
            'Keys at platform.openai.com</div>', unsafe_allow_html=True)
    with c3:
        st.markdown(
            '<div class="info-card"><h4>Gemini</h4>'
            'Models: <code>gemini-2.0-flash</code>, <code>gemini-2.5-flash-preview-05-20</code><br>'
            'Keys at aistudio.google.com</div>', unsafe_allow_html=True)

    if st.session_state.dataframes:
        st.divider()
        st.subheader("Loaded Datasets Schema")
        for name, df in st.session_state.dataframes.items():
            with st.expander(f"**{name}** — {len(df):,} rows × {len(df.columns)} cols"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Column Types**")
                    schema_df = df.dtypes.reset_index()
                    schema_df.columns = ["Column", "Type"]
                    schema_df["Type"] = schema_df["Type"].astype(str)
                    st.dataframe(schema_df, use_container_width=True, hide_index=True)
                with col_b:
                    st.markdown("**Sample (5 rows)**")
                    st.dataframe(df.head(5), use_container_width=True)

# ── CHAT TAB ─────────────────────────────────────────────────────────────────
with tab_chat:

    # Dataset status bar
    if st.session_state.dataframes:
        ds_names = " · ".join(f"**{k}** ({len(v):,} rows)" for k, v in st.session_state.dataframes.items())
        st.info(f"Active datasets: {ds_names}  —  AI can join & analyse all together.", icon="📊")

    # ── Chat history ────────────────────────────────────────────────────────
    for i, msg in enumerate(st.session_state.chat_history):
        if msg["role"] == "user":
            st.markdown(user_msg_html(msg["content"]), unsafe_allow_html=True)
        elif msg["role"] == "data_preview":
            # System message: data loaded preview
            with st.expander(f"📊 Data Loaded: **{msg['name']}** — {msg['rows']:,} rows × {msg['cols']} columns", expanded=False):
                st.dataframe(msg["df"].head(5), use_container_width=True)
                st.caption(f"Columns: {', '.join(msg['df'].columns.tolist())}")
        else:
            st.markdown(bot_msg_html(msg["content"]), unsafe_allow_html=True)

            # Show generated SQL query
            if msg.get("sql_query"):
                with st.expander("🔍 View SQL Query", expanded=False):
                    st.code(msg["sql_query"], language="sql")

            # Show result dataframe
            if msg.get("df") is not None and not msg["df"].empty:
                st.caption(f"Result: {len(msg['df']):,} rows × {len(msg['df'].columns)} columns")
                st.dataframe(msg["df"], use_container_width=True)

            # Report button — uses this message's result df, else first loaded df
            report_df = msg.get("df") if msg.get("df") is not None else (
                next(iter(st.session_state.dataframes.values())) if st.session_state.dataframes else None
            )
            if report_df is not None:
                if st.button("📊 Generate Report", key=f"report_{i}"):
                    import plotly.express as px
                    num_cols = report_df.select_dtypes(include="number").columns.tolist()
                    cat_cols = report_df.select_dtypes(exclude="number").columns.tolist()
                    if num_cols and cat_cols:
                        fig = px.bar(report_df.head(30), x=cat_cols[0], y=num_cols[0],
                                     color_discrete_sequence=["#ff7a00"],
                                     title=f"{num_cols[0]} by {cat_cols[0]}")
                    elif num_cols:
                        fig = px.histogram(report_df, x=num_cols[0],
                                           color_discrete_sequence=["#ff7a00"],
                                           title=f"Distribution of {num_cols[0]}")
                    else:
                        fig = None
                    if fig:
                        fig.update_layout(paper_bgcolor="#fff", plot_bgcolor="#fff", font_family="Inter")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No numeric columns available for charting.")

    st.divider()

    # ── Input ───────────────────────────────────────────────────────────────
    col_input, col_send = st.columns([6, 1])
    with col_input:
        # Key includes counter so incrementing it creates a fresh empty widget
        input_key = f"chat_input_{st.session_state._input_counter}"
        user_question = st.text_input(
            "Ask anything",
            placeholder="Ask a question about your data, documents, or anything…",
            key=input_key,
            label_visibility="collapsed",
        )
    with col_send:
        send = st.button("Send ➤", type="primary", use_container_width=True)

    # ── Anti-infinite-loop: only process if this is a NEW question ──────────
    trigger = user_question.strip() if (send or user_question) else ""
    already_sent = (trigger == st.session_state.get("_pending_query", ""))

    if trigger and not already_sent:
        if not st.session_state.api_key:
            st.warning("⚠️ Configure your API Key in the **Settings** tab first.")
        else:
            # Mark as in-flight so next rerun skips it
            st.session_state._pending_query = trigger
            st.session_state.chat_history.append({"role": "user", "content": trigger})

            with st.status("Thinking…", expanded=True) as status_box:
                try:
                    status_box.write("Initialising LLM…")
                    llm = get_llm(
                        st.session_state.provider,
                        st.session_state.model_name,
                        st.session_state.api_key,
                    )
                    dfs = st.session_state.dataframes if st.session_state.dataframes else None
                    
                    # We will pass the status box down to handle_user_query to write updates
                    result = handle_user_query(trigger, llm, dfs, status_box)
                    
                    answer    = result.get("answer", str(result))
                    sql_query = result.get("sql_query", None)
                    result_df = result.get("dataframe", None)
                    status_box.update(label="Done!", state="complete")
                    
                except Exception as e:
                    answer    = f"Error: {e}"
                    sql_query = None
                    result_df = None
                    status_box.update(label="Failed.", state="error")

            st.session_state.chat_history.append({
                "role":      "bot",
                "content":   answer,
                "sql_query": sql_query,
                "df":        result_df,
            })
            st.session_state._pending_query = None
            st.session_state._input_counter += 1
            st.rerun()