import logging
import os

import requests
import streamlit as st


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mamoru-ui")

st.set_page_config(page_title="Mamoru Project", page_icon="🧠", layout="wide")

st.markdown(
    """
<style>
  :root { color-scheme: dark; }
  .main { background-color: #0b0f14; }
  .block-container { padding-top: 2rem; max-width: 1100px; }
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

st.markdown(
    """
<div class="mamoru-hero">
  <span class="mamoru-pill">Mamoru Project</span>
  <h1>PubMed RAG Prototype</h1>
  <p class="mamoru-muted">Safeguarding clinical knowledge for dementia care through grounded answers and trusted sources.</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Configuration")
    default_api = os.getenv("RAG_API_URL", "").rstrip("/")
    api_url = st.text_input(
        "API base URL",
        value=default_api,
        placeholder="https://api-id.execute-api.us-east-1.amazonaws.com",
    )
    st.caption("Set `RAG_API_URL` to prefill this.")

col_left, col_right = st.columns([1.2, 1], gap="large")

with col_left:
    st.markdown('<div class="mamoru-card">', unsafe_allow_html=True)
    question = st.text_area(
        "Ask a question",
        height=140,
        placeholder="What are common caregiver challenges in dementia care?",
    )
    ask = st.button("Ask", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="mamoru-card">', unsafe_allow_html=True)
    st.subheader("How it works")
    st.markdown(
        """
- Retrieves evidence from the Bedrock knowledge base
- Uses PubMed-derived sources stored in S3
- Returns a single-turn, grounded response
"""
    )
    st.markdown("</div>", unsafe_allow_html=True)

if ask:
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

    if resp.status_code != 200:
        st.error(f"API error ({resp.status_code}): {resp.text}")
        st.stop()

    payload = resp.json()
    st.markdown("---")
    st.subheader("Answer")
    st.write(payload.get("answer", ""))

    sources = payload.get("sources", [])
    if sources:
        st.subheader("Sources")
        for idx, source in enumerate(sources, start=1):
            with st.expander(f"Source {idx}", expanded=False):
                st.write(source.get("text", ""))
                st.json(source.get("metadata", {}))
