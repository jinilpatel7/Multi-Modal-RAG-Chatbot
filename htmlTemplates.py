css = '''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global reset ─────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}
.stApp {
    background: #f9f9f9;
}

/* ── Sidebar ───────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #f0e8df;
}
[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem;
}

/* ── Main header ─────────────────────────────────────────── */
.app-header {
    background: linear-gradient(135deg, #ff6b00 0%, #ff9a00 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: 0 4px 24px rgba(255,107,0,0.18);
}
.app-header h1 {
    color: #fff !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    padding: 0 !important;
}
.app-header p {
    color: rgba(255,255,255,0.85) !important;
    margin: 0 !important;
    font-size: 0.9rem;
}

/* ── Chat messages ───────────────────────────────────────── */
.chat-row {
    display: flex;
    gap: 14px;
    margin-bottom: 1rem;
    animation: fadeUp 0.25s ease both;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
.chat-row.user-row  { flex-direction: row-reverse; }
.chat-row.bot-row   { flex-direction: row; }

.chat-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    flex-shrink: 0;
    object-fit: cover;
    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}

.chat-bubble {
    max-width: 72%;
    padding: 0.85rem 1.1rem;
    border-radius: 16px;
    line-height: 1.55;
    font-size: 0.92rem;
    word-wrap: break-word;
}
.chat-bubble.user-bubble {
    background: linear-gradient(135deg, #ff7a00, #ff9d00);
    color: #fff;
    border-bottom-right-radius: 4px;
    box-shadow: 0 2px 12px rgba(255,120,0,0.22);
}
.chat-bubble.bot-bubble {
    background: #ffffff;
    color: #1a1a1a;
    border: 1px solid #ede8e3;
    border-bottom-left-radius: 4px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}

/* ── Input area styling ───────────────────────────────────── */
.stTextInput > div > div > input {
    border-radius: 12px !important;
    border: 1.5px solid #e0d6cc !important;
    padding: 0.6rem 1rem !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.92rem !important;
    transition: border 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: #ff7a00 !important;
    box-shadow: 0 0 0 3px rgba(255,122,0,0.12) !important;
}

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button {
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"] {
    background: #ff7a00 !important;
    border: none !important;
    color: #fff !important;
}
.stButton > button[kind="primary"]:hover {
    background: #e06c00 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(255,120,0,0.3) !important;
}
.stButton > button[kind="secondary"] {
    border: 1.5px solid #ff7a00 !important;
    color: #ff7a00 !important;
    background: transparent !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #fff4ec !important;
}

/* ── Tabs ──────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #f0ebe6;
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    padding: 0.4rem 1.2rem !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    color: #666 !important;
    background: transparent !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: #ff7a00 !important;
    color: #fff !important;
}

/* ── Cards / expanders ───────────────────────────────────── */
.info-card {
    background: #fff;
    border: 1px solid #f0e8df;
    border-left: 4px solid #ff7a00;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}
.info-card h4 {
    color: #ff7a00;
    margin: 0 0 0.3rem 0;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* ── Sidebar labels ───────────────────────────────────────── */
.sidebar-section {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #ff7a00;
    margin: 1.2rem 0 0.5rem 0;
}

/* ── Dataframe table ──────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ── Divider ─────────────────────────────────────────────── */
hr { border-color: #f0e8df !important; }
</style>
'''

USER_AVATAR = "https://api.dicebear.com/7.x/thumbs/svg?seed=user&backgroundColor=ff9a00"
BOT_AVATAR  = "https://api.dicebear.com/7.x/bottts-neutral/svg?seed=bot&backgroundColor=ffffff"

def user_msg_html(content: str) -> str:
    return f'''
<div class="chat-row user-row">
  <img class="chat-avatar" src="{USER_AVATAR}" />
  <div class="chat-bubble user-bubble">{content}</div>
</div>'''

def bot_msg_html(content: str) -> str:
    return f'''
<div class="chat-row bot-row">
  <img class="chat-avatar" src="{BOT_AVATAR}" />
  <div class="chat-bubble bot-bubble">{content}</div>
</div>'''
