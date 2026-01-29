import logging
import os

import requests
import streamlit as st


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mamoru-ui")

LOGO_URL = "https://raw.githubusercontent.com/adzuci/pubmed-rag-system/main/assets/mamoru-project-logo.png"
DEFAULT_RAG_API_URL = "https://pye2ftvvg5.execute-api.us-east-1.amazonaws.com"

st.set_page_config(page_title="Mamoru Project", page_icon="🧠", layout="wide")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown(
    """
<style>
  :root { color-scheme: dark; }
  .main { background-color: #0b0f14; }
  .block-container { padding-top: 2rem; max-width: 1100px; }
  .mamoru-logo { display: flex; align-items: center; justify-content: center; margin: 0.25rem 0 0.75rem; }
  .mamoru-hero { border: 1px solid #1c2430; background: #111827; padding: 1.5rem; border-radius: 16px; }
  .mamoru-pill { display: inline-block; padding: 0.25rem 0.6rem; border-radius: 999px; background: #1e293b; color: #93c5fd; font-size: 0.8rem; }
  .mamoru-card { border: 1px solid #1f2937; background: #0f172a; padding: 1.25rem; border-radius: 16px; }
  .mamoru-muted { color: #9ca3af; }
  .stButton>button { background: #2563eb; color: white; border-radius: 10px; padding: 0.5rem 1.1rem; }
  .stButton>button:hover { background: #1d4ed8; color: white; }
</style>
""",
    unsafe_allow_html=True,
)

logo_col_left, logo_col_mid, logo_col_right = st.columns([1, 2, 1])
with logo_col_mid:
    st.markdown('<div class="mamoru-logo">', unsafe_allow_html=True)
    st.image(LOGO_URL, width=92)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
<div class="mamoru-hero">
  <h1>Mamoru Project</h1>
  <p class="mamoru-muted">Safeguarding clinical knowledge for dementia care through grounded answers and trusted sources.</p>
  <p class="mamoru-muted" style="font-size: 0.9em; margin-top: 0.5rem;">This system uses a curated subset of dementia and caregiver-related peer-reviewed articles from PubMed to inform research-backed answers.</p>
</div>
""",
    unsafe_allow_html=True,
)


def normalize_api_url(value: str) -> str:
    if not value:
        return ""
    cleaned = value.strip()
    if cleaned.endswith("/query"):
        cleaned = cleaned[: -len("/query")]
    if cleaned.endswith("/"):
        cleaned = cleaned[:-1]
    if not cleaned.startswith(("http://", "https://")):
        cleaned = f"https://{cleaned}"
    return cleaned


with st.sidebar:
    st.header("Configuration")
    default_api = os.getenv("RAG_API_URL") or os.getenv("RAG_API_ENDPOINT") or ""
    if not default_api:
        default_api = DEFAULT_RAG_API_URL
    default_api = normalize_api_url(default_api)
    api_url = st.text_input(
        "API base URL",
        value=default_api,
        placeholder="https://api-id.execute-api.us-east-1.amazonaws.com",
    )
    st.caption("Set `RAG_API_URL` to prefill this.")
    st.markdown("---")
    st.subheader("How it works")
    st.markdown(
        """
- Retrieves evidence from the Bedrock knowledge base
- Uses PubMed-derived sources stored in S3
- Returns a single-turn, grounded response
"""
    )


def render_chat(history):
    """Render chat history in a scrollable container."""
    if not history:
        st.info(
            "Ask a question to get started. I’ll help you find evidence-based answers about dementia care."
        )

        st.markdown("#### Try a sample question")
        samples = [
            "What are evidence-based strategies for managing sleep disturbances in people with dementia?",
            "What does the research say about caregiver burden in early-stage Alzheimer’s disease?",
            "Are there effective non-pharmacological interventions for agitation in dementia patients?",
            "What interventions help reduce caregiver stress and burnout?",
        ]

        cols = st.columns(2, gap="small")
        for idx, sample in enumerate(samples):
            col = cols[idx % 2]
            if col.button(sample, use_container_width=True, key=f"sample_{idx}"):
                st.session_state["question_input"] = sample
                st.session_state["auto_submit"] = True
                st.rerun()
        return

    # Create a scrollable container for chat
    chat_container = st.container()
    with chat_container:
        for entry in history:
            with st.chat_message("user"):
                st.write(entry.get("question", ""))
            with st.chat_message("assistant"):
                st.write(entry.get("answer", ""))
                sources = entry.get("sources", [])
                if sources:
                    with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
                        for idx, source in enumerate(sources, start=1):
                            st.markdown(f"**Source {idx}**")
                            st.write(source.get("text", ""))
                            st.json(source.get("metadata", {}))


# Render chat history first (scrollable)
render_chat(st.session_state.chat_history)

# Input area at the bottom (fixed)
st.markdown("---")
with st.container():
    col1, col2 = st.columns([10, 1])
    with col1:
        question = st.text_input(
            "",
            placeholder="Ask a question about dementia care...",
            label_visibility="collapsed",
            key="question_input",
        )
    with col2:
        ask = st.button("Ask", type="primary", use_container_width=True)

auto_submit = bool(st.session_state.get("auto_submit"))
if ask or auto_submit:
    api_url = normalize_api_url(api_url)
    if not api_url:
        st.error("Set the API base URL.")
        st.stop()
    if not question.strip():
        st.error("Enter a question.")
        st.stop()

    logger.info("rag_query: %s", question.strip())

    with st.spinner("Retrieving sources and drafting answer..."):
        try:
            resp = requests.post(
                f"{api_url}/query",
                json={"question": question.strip()},
                timeout=30,
            )
        except requests.RequestException as exc:
            st.error(f"Request failed: {exc}")
            st.stop()

    if resp.status_code == 404:
        st.error(
            "API returned 404. Double-check the base URL (no /query suffix) "
            "and include https://."
        )
        st.stop()
    if resp.status_code != 200:
        st.error(f"API error ({resp.status_code}): {resp.text}")
        st.stop()

    payload = resp.json()
    st.session_state.chat_history.append(
        {
            "question": question.strip(),
            "answer": payload.get("answer", ""),
            "sources": payload.get("sources", []),
        }
    )
    # Clear the input and rerun to show new answer
    st.session_state["auto_submit"] = False
    st.session_state["question_input"] = ""
    st.rerun()
