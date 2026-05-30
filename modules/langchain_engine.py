"""
langchain_engine.py
────────────────────────────────────────────────────────────────────────────
Two query paths:
  1. Tabular data → SQL generation via LCEL + DuckDB execution
     • LLM generates clean SQL from schema context
     • DuckDB executes it directly against pandas DataFrames
     • Returns: answer (NL), sql_query (str), dataframe (DataFrame)

  2. Documents → vector-store RAG via LCEL (no heavy init on startup)

Heavy models (HuggingFace, ChromaDB) are loaded via @st.cache_resource
so they are initialised exactly once per server process.
"""

import os
import re
import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

from .preprocessing import preprocess_and_split_text


# ─────────────────────────────────────────────────────────────────────────────
# Cached resources (loaded ONCE per server process)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading embedding model (first time only)…")
def _get_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


@st.cache_resource(show_spinner="Initialising vector store…")
def _get_db():
    from langchain_chroma import Chroma
    return Chroma(embedding_function=_get_embeddings(), persist_directory="./chroma_db")


# ─────────────────────────────────────────────────────────────────────────────
# LLM factory
# ─────────────────────────────────────────────────────────────────────────────

def get_llm(provider: str, model_name: str, api_key: str):
    """Return the appropriate LangChain chat model."""
    if provider == "OpenRouter":
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1,
            max_tokens=2048,
        )
    elif provider == "OpenAI":
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=0.1,
            max_tokens=2048,
        )
    elif provider == "Gemini":
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.1,
            convert_system_message_to_human=True,
            max_retries=1,
        )
    raise ValueError(f"Unsupported provider: {provider}")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_schema_context(dataframes: dict) -> str:
    """Build a detailed schema string for the LLM prompt."""
    lines = []
    for table_name, df in dataframes.items():
        lines.append(f"Table name: {table_name}")
        lines.append(f"  Rows: {len(df):,}")
        lines.append("  Columns:")
        for col in df.columns:
            dtype = str(df[col].dtype)
            # Show distinct sample values for non-numeric cols (up to 8)
            if df[col].dtype == object:
                samples = df[col].dropna().unique()[:8].tolist()
                lines.append(f"    - {col} [{dtype}]  sample values: {samples}")
            else:
                try:
                    mn, mx = df[col].min(), df[col].max()
                    lines.append(f"    - {col} [{dtype}]  range: {mn} to {mx}")
                except Exception:
                    lines.append(f"    - {col} [{dtype}]")
        lines.append("")
    return "\n".join(lines)


def _clean_sql(raw: str) -> str:
    """Strip markdown fences and whitespace from LLM SQL output."""
    raw = raw.strip()
    # Remove ```sql ... ``` or ``` ... ```
    raw = re.sub(r"^```(?:sql)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _execute_sql(sql: str, dataframes: dict):
    """Run SQL against the loaded DataFrames using DuckDB."""
    import duckdb
    conn = duckdb.connect()
    for name, df in dataframes.items():
        # DuckDB can reference a pandas DataFrame registered this way
        conn.register(name, df)
    result_df = conn.execute(sql).df()
    conn.close()
    return result_df


# ─────────────────────────────────────────────────────────────────────────────
# Vector store helpers
# ─────────────────────────────────────────────────────────────────────────────

def add_texts_to_vectorstore(texts: list[str]):
    db = _get_db()
    chunks = []
    for text in texts:
        if text:
            chunks.extend(preprocess_and_split_text(text))
    if chunks:
        db.add_texts(chunks)


def reset_vectorstore():
    db = _get_db()
    db.delete_collection()
    _get_db.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Main query handler
# ─────────────────────────────────────────────────────────────────────────────

def handle_user_query(query: str, llm, dataframes: dict | None = None, status_box=None) -> dict:
    """
    Route the query and return a result dict:
      {
        "answer":    str,            # Natural-language response
        "sql_query": str | None,     # SQL that was generated & run (if any)
        "dataframe": DataFrame|None, # Result table (if SQL was used)
      }
    """

    # Helper for status updates
    def log_status(msg):
        if status_box:
            status_box.write(msg)

    # ── PATH 1: Tabular data ─────────────────────────────────────────────────
    if dataframes:
        log_status("Building database schema context…")
        schema_ctx = _build_schema_context(dataframes)

        # Step 1 — Generate SQL
        log_status("Generating SQL query…")
        sql_prompt = PromptTemplate.from_template(
            """You are an expert SQL data analyst. The user has the following tables available:

{schema}

User question: {question}

Write a single DuckDB-compatible SQL query to answer this question precisely.
- Reference tables by their exact names shown above.
- For date filtering use: CURRENT_DATE, INTERVAL, DATE_TRUNC etc.
- For text search use: ILIKE '%keyword%'
- If the question involves joining tables, use appropriate JOINs.

Return ONLY the SQL query. No explanation. No markdown fences."""
        )
        sql_chain = sql_prompt | llm | StrOutputParser()
        raw_sql = sql_chain.invoke({"schema": schema_ctx, "question": query})
        sql_query = _clean_sql(raw_sql)

        # Step 2 — Execute SQL
        log_status("Executing SQL against dataframes…")
        try:
            result_df = _execute_sql(sql_query, dataframes)
        except Exception as exec_err:
            log_status(f"SQL error detected. Asking AI to fix it…")
            fix_prompt = PromptTemplate.from_template(
                """The following SQL query failed with error: {error}

SQL:
{sql}

Schema:
{schema}

Fix the SQL and return ONLY the corrected query. No explanation."""
            )
            fix_chain = fix_prompt | llm | StrOutputParser()
            fixed_sql = _clean_sql(fix_chain.invoke({
                "error": str(exec_err),
                "sql": sql_query,
                "schema": schema_ctx,
            }))
            try:
                result_df = _execute_sql(fixed_sql, dataframes)
                sql_query = fixed_sql
            except Exception as e2:
                return {
                    "answer": f"Could not execute the SQL query.\n\nAttempted SQL:\n```sql\n{sql_query}\n```\n\nError: {e2}",
                    "sql_query": sql_query,
                    "dataframe": None,
                }

        # Step 3 — Generate natural-language answer from the result
        log_status("Formulating natural language answer from results…")
        result_summary = result_df.head(20).to_string(index=False) if not result_df.empty else "No rows returned."
        answer_prompt = PromptTemplate.from_template(
            """The user asked: {question}

The following SQL was executed:
{sql}

Result ({rows} rows):
{result}

Provide a clear, concise natural-language answer to the user's question based on the result above.
Be specific with numbers and facts. Do not show code."""
        )
        answer_chain = answer_prompt | llm | StrOutputParser()
        answer = answer_chain.invoke({
            "question": query,
            "sql": sql_query,
            "rows": len(result_df),
            "result": result_summary,
        })

        return {"answer": answer, "sql_query": sql_query, "dataframe": result_df}

    # ── PATH 2: Document RAG ─────────────────────────────────────────────────
    log_status("Searching documents vector store…")
    db = _get_db()
    docs = db.as_retriever(search_kwargs={"k": 5}).invoke(query)
    context = "\n\n".join(d.page_content for d in docs)

    log_status("Generating answer from context…")
    rag_prompt = PromptTemplate.from_template(
        """You are a knowledgeable assistant. Answer using ONLY the context below.
If the context doesn't contain enough information, say so clearly.

Context:
{context}

Question: {question}

Answer:"""
    )
    answer = (rag_prompt | llm | StrOutputParser()).invoke({"context": context, "question": query})
    return {"answer": answer, "sql_query": None, "dataframe": None}
