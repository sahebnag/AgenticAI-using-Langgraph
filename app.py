import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NewsGenie",
    page_icon="🗞️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Header */
    .ng-header { text-align:center; padding: 0.5rem 0 0.25rem; }
    .ng-header h1 { font-size: 2.4rem; font-weight: 800; margin: 0;
                    background: linear-gradient(90deg,#2563eb,#7c3aed);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .ng-header p  { color: #6b7280; font-size: 1rem; margin: 0.25rem 0 0; }

    /* Category badge */
    .cat-badge { display:inline-block; padding:0.2rem 0.75rem;
                 border-radius: 999px; font-size:0.78rem; font-weight:600;
                 background:#ede9fe; color:#5b21b6; margin-bottom:0.5rem; }

    /* Sidebar section headers */
    .sidebar-section { font-size:0.75rem; font-weight:700; letter-spacing:0.08em;
                       text-transform:uppercase; color:#9ca3af; margin:1rem 0 0.25rem; }

    /* Status chip */
    .step-chip { background:#f0fdf4; border:1px solid #bbf7d0; border-radius:6px;
                 padding:0.25rem 0.6rem; font-size:0.8rem; color:#166534;
                 margin:0.2rem 0; display:block; }

    /* Error chip */
    .err-chip  { background:#fef2f2; border:1px solid #fecaca; border-radius:6px;
                 padding:0.25rem 0.6rem; font-size:0.8rem; color:#991b1b;
                 margin:0.2rem 0; display:block; }
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ─────────────────────────────────────────────────────
if "messages"  not in st.session_state: st.session_state.messages  = []   # display history
if "lc_history" not in st.session_state: st.session_state.lc_history = []  # LangChain message objects
if "category"  not in st.session_state: st.session_state.category  = "Technology"

CATEGORIES = ["Technology", "Finance", "Sports", "Health", "Science", "Entertainment", "General"]

CATEGORY_ICONS = {
    "Technology":    "💻",
    "Finance":       "📈",
    "Sports":        "⚽",
    "Health":        "🏥",
    "Science":       "🔬",
    "Entertainment": "🎬",
    "General":       "🌐",
}

# ── Helper: check keys ─────────────────────────────────────────────────────────
def _openai_ready() -> bool:
    k = os.getenv("OPENAI_API_KEY", "")
    return bool(k and k not in ("", "your_openai_api_key_here"))

def _newsapi_ready() -> bool:
    k = os.getenv("NEWS_API_KEY", "")
    return bool(k and k not in ("", "your_newsapi_key_here"))

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🗞️ NewsGenie")
    st.caption("AI-Powered Information & News Assistant")
    st.divider()

    st.markdown('<div class="sidebar-section">API Keys</div>', unsafe_allow_html=True)
    openai_input = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        placeholder="sk-...",
        help="Required. Get it at platform.openai.com/api-keys",
    )
    if openai_input:
        os.environ["OPENAI_API_KEY"] = openai_input

    newsapi_input = st.text_input(
        "NewsAPI Key",
        type="password",
        value=os.getenv("NEWS_API_KEY", ""),
        placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        help="Optional but recommended. Free key at newsapi.org",
    )
    if newsapi_input:
        os.environ["NEWS_API_KEY"] = newsapi_input

    # Key status
    col_a, col_b = st.columns(2)
    col_a.markdown(f"{'🟢' if _openai_ready() else '🔴'} OpenAI")
    col_b.markdown(f"{'🟢' if _newsapi_ready() else '🟡'} NewsAPI")
    if not _newsapi_ready():
        st.caption("Without a NewsAPI key, news is fetched via web search (less structured).")

    st.divider()
    st.markdown('<div class="sidebar-section">News Category</div>', unsafe_allow_html=True)
    chosen = st.radio(
        "Select category",
        CATEGORIES,
        index=CATEGORIES.index(st.session_state.category),
        format_func=lambda c: f"{CATEGORY_ICONS[c]}  {c}",
        label_visibility="collapsed",
    )
    if chosen != st.session_state.category:
        st.session_state.category = chosen

    st.divider()
    st.markdown('<div class="sidebar-section">Session</div>', unsafe_allow_html=True)
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages   = []
        st.session_state.lc_history = []
        st.rerun()

    st.divider()
    st.markdown('<div class="sidebar-section">How it works</div>', unsafe_allow_html=True)
    st.markdown("""
1. **Classify** — GPT-4o-mini decides: news or general query
2. **Route** — LangGraph sends to the right agent
3. **Fetch** — NewsAPI → web search fallback
4. **Respond** — GPT-4o synthesises a clear answer
""")

# ── Main header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ng-header">
  <h1>🗞️ NewsGenie</h1>
  <p>Your AI-powered information &amp; real-time news assistant</p>
</div>
""", unsafe_allow_html=True)

cat = st.session_state.category
st.markdown(
    f'<div style="text-align:center">'
    f'<span class="cat-badge">{CATEGORY_ICONS[cat]} Active category: {cat}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── Example prompts (shown only when chat is empty) ────────────────────────────
if not st.session_state.messages:
    st.markdown("---")
    st.markdown("##### Try asking…")
    eg_cols = st.columns(3)
    examples = [
        (f"Show me the latest {cat} news",       "📰"),
        ("What is artificial intelligence?",      "🤖"),
        ("Summarise today's top business stories","📊"),
    ]
    for col, (text, icon) in zip(eg_cols, examples):
        if col.button(f"{icon} {text}", use_container_width=True):
            st.session_state._pending = text
    st.markdown("---")

# ── Chat history ───────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🗞️"):
        st.markdown(msg["content"])
        if msg.get("meta"):
            st.caption(msg["meta"])

# ── Chat input ─────────────────────────────────────────────────────────────────
pending = st.session_state.pop("_pending", None)
user_input = st.chat_input("Ask about news or anything else…") or pending

if user_input:
    if not _openai_ready():
        st.error("Please enter your OpenAI API key in the sidebar to start.")
        st.stop()

    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    # Agent thinking UI
    with st.chat_message("assistant", avatar="🗞️"):
        status_box = st.empty()
        steps: list[str] = []

        def on_step(msg: str):
            steps.append(msg)
            with status_box.container():
                for s in steps:
                    st.markdown(f'<span class="step-chip">⚙️ {s}</span>', unsafe_allow_html=True)

        try:
            from agent import chat as ng_chat

            reply, updated_history = ng_chat(
                user_message=user_input,
                category=st.session_state.category.lower(),
                history=st.session_state.lc_history,
                on_step=on_step,
            )

            st.session_state.lc_history = updated_history
            status_box.empty()

            timestamp = datetime.now().strftime("%H:%M · %d %b %Y")
            st.markdown(reply)
            st.caption(f"🕐 {timestamp}  |  Category: {st.session_state.category}")

            st.session_state.messages.append({
                "role":    "assistant",
                "content": reply,
                "meta":    f"🕐 {timestamp}  |  Category: {st.session_state.category}",
            })

        except ImportError as e:
            status_box.empty()
            st.markdown(
                f'<span class="err-chip">❌ Missing package: {e} — run <code>pip install -r requirements.txt</code></span>',
                unsafe_allow_html=True,
            )
        except Exception as e:
            status_box.empty()
            err_msg = str(e)
            # Surface common errors helpfully
            if "api_key" in err_msg.lower() or "authentication" in err_msg.lower():
                st.error("Invalid or missing OpenAI API key. Check the sidebar.")
            elif "rate" in err_msg.lower():
                st.warning("Rate limit hit. Please wait a moment and try again.")
            else:
                st.error(f"Something went wrong: {err_msg}")
