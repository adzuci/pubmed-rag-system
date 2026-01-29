import logging
import os

import requests
import streamlit as st


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mamoru-ui")

LOGO_URL = "https://raw.githubusercontent.com/adzuci/pubmed-rag-system/main/assets/mamoru-project-logo-transparent.png"
DEFAULT_RAG_API_URL = "https://pye2ftvvg5.execute-api.us-east-1.amazonaws.com"

st.set_page_config(
    page_title="Mamoru Project",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown(
    """
<style>
  /* Base colors - dark theme */
  :root {
    --bg-primary: #0b0f14;
    --bg-secondary: #111827;
    --text-primary: #f9fafb;
    --text-secondary: #e5e7eb;
    --text-muted: #9ca3af;
    --border-color: #1f2937;
    --border-focus: #2563eb;
    --button-primary: #2563eb;
    --button-primary-hover: #1d4ed8;
    --button-text: #ffffff;
  }
  
  .main { background-color: var(--bg-primary); }
  .block-container { 
    padding-top: 0.5rem; 
    padding-bottom: 120px; 
    max-width: 900px; 
    margin: 0 auto; 
    background-color: var(--bg-primary);
  }
  
  /* Header */
  .header-container { 
    text-align: center; 
    padding: 3rem 1rem 2rem; 
    margin-bottom: 2rem; 
    background-color: var(--bg-primary);
  }
  .header-logo { 
    margin-bottom: 1.5rem; 
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 1rem 0;
  }
  .header-logo img {
    filter: drop-shadow(0 4px 20px rgba(0, 0, 0, 0.4));
    transition: all 0.3s ease;
    max-width: 100%;
    height: auto;
  }
  .header-logo img:hover {
    transform: scale(1.02);
    filter: drop-shadow(0 6px 24px rgba(37, 99, 235, 0.3));
  }
  .header-subtitle { 
    color: var(--text-muted); 
    font-size: 0.95em; 
    margin-top: 1rem; 
    line-height: 1.6;
  }
  
  /* Chat container */
  .chat-container { 
    min-height: calc(100vh - 500px); 
    padding-bottom: 140px; 
    background-color: var(--bg-primary);
  }
  
  /* Fixed input at bottom */
  .input-container { 
    position: fixed; 
    bottom: 0; 
    left: 0; 
    right: 0; 
    background: var(--bg-primary); 
    border-top: 1px solid var(--border-color); 
    padding: 1rem; 
    z-index: 100;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
  }
  .input-wrapper { 
    max-width: 900px; 
    margin: 0 auto; 
  }
  .input-wrapper [data-testid="column"] {
    padding: 0;
  }
  
  /* Buttons */
  .stButton>button { 
    background: var(--button-primary); 
    color: var(--button-text); 
    border-radius: 8px; 
    padding: 0.6rem 1.5rem; 
    font-weight: 500;
    height: 44px;
    border: none;
  }
  .stButton>button:hover { 
    background: var(--button-primary-hover); 
    color: var(--button-text); 
  }
  
  /* Input fields */
  .stTextInput>div>div>input { 
    border-radius: 12px; 
    border: 1px solid var(--border-color);
    padding: 0.75rem 1rem;
    font-size: 1em;
    background-color: var(--bg-secondary);
    color: var(--text-primary);
  }
  .stTextInput>div>div>input:focus { 
    border-color: var(--border-focus);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
    outline: none;
  }
  .stTextInput>div>div>input::placeholder {
    color: var(--text-muted);
  }
  
  /* Welcome message */
  .welcome-message { 
    text-align: center; 
    padding: 2rem 1rem 3rem; 
    background-color: var(--bg-primary);
    margin-top: 1rem;
  }
  .welcome-title { 
    font-size: 1.25em; 
    margin-bottom: 0.5rem; 
    font-weight: 600; 
    color: var(--text-primary);
  }
  .welcome-subtitle { 
    color: var(--text-muted); 
    font-size: 0.95em; 
    line-height: 1.6;
  }
  
  /* Sample questions */
  .sample-questions { 
    margin-top: 2rem; 
    max-width: 700px;
    margin-left: auto;
    margin-right: auto;
    background-color: var(--bg-primary);
  }
  .sample-questions h4 { 
    text-align: center; 
    color: var(--text-secondary); 
    margin-bottom: 1rem; 
    font-size: 1em;
    font-weight: 600;
  }
  .sample-button { margin-bottom: 0.5rem; }
  
  /* Chat messages - ensure proper contrast */
  [data-testid="stChatMessage"] { 
    padding: 1rem 0; 
  }
  [data-testid="stChatMessage"] p {
    color: var(--text-primary);
  }
  
  /* Sidebar */
  [data-testid="stSidebar"] { 
    background-color: var(--bg-primary); 
  }
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3 {
    color: var(--text-primary);
  }
  [data-testid="stSidebar"] p {
    color: var(--text-secondary);
  }
  [data-testid="stSidebar"] input {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    border-color: var(--border-color);
  }
  
  /* Info boxes and expanders */
  .stInfo {
    background-color: #1e3a5f;
    border-left: 4px solid var(--button-primary);
  }
  .stInfo p {
    color: var(--text-secondary);
  }
  
  /* Expanders */
  [data-testid="stExpander"] {
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
  }
  [data-testid="stExpander"] summary {
    color: var(--text-secondary);
  }
  
  /* Error messages */
  .stAlert {
    background-color: #7f1d1d;
    border-left: 4px solid #dc2626;
  }
  .stAlert p {
    color: #fca5a5;
  }
  
  /* Spinner */
  .stSpinner > div {
    border-color: var(--button-primary);
  }
  
  /* Ensure all text has proper contrast */
  p, span, div, label {
    color: var(--text-primary);
  }
  
  /* Chat message content */
  [data-testid="stChatMessageContent"] {
    color: var(--text-primary);
  }
  
  /* Markdown content */
  .stMarkdown {
    color: var(--text-primary);
  }
  .stMarkdown p {
    color: var(--text-primary);
  }
  .stMarkdown code {
    background-color: #1e293b;
    color: var(--text-primary);
    border: 1px solid var(--border-color);
  }
  
  /* JSON display */
  .stJson {
    background-color: #1e293b;
    border: 1px solid var(--border-color);
  }
  
  /* Sample question buttons */
  .sample-questions button {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
  }
  .sample-questions button:hover {
    background-color: #1e293b;
    border-color: var(--button-primary);
  }
</style>
<script>
  // Make Enter key trigger submit
  function setupEnterKey() {
    const inputs = document.querySelectorAll('input[data-testid="stTextInput"]');
    inputs.forEach(input => {
      input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          const buttons = document.querySelectorAll('button[kind="primaryFormSubmit"]');
          if (buttons.length > 0) {
            buttons[buttons.length - 1].click();
          }
        }
      });
    });
  }
  // Run on load and after Streamlit reruns
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupEnterKey);
  } else {
    setupEnterKey();
  }
  // Also setup after Streamlit reruns
  const observer = new MutationObserver(setupEnterKey);
  observer.observe(document.body, { childList: true, subtree: true });
</script>
""",
    unsafe_allow_html=True,
)

# Header with logo
st.markdown(
    """
<div class="header-container">
  <div class="header-logo">
    <img src="{logo_url}" width="220" alt="Mamoru Project">
  </div>
  <p class="header-subtitle">Safeguarding clinical knowledge for dementia care through grounded answers and trusted sources.</p>
</div>
""".format(
        logo_url=LOGO_URL
    ),
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
    st.header("⚙️ Configuration")
    default_api = (
        os.getenv("RAG_API_URL") or os.getenv("RAG_API_ENDPOINT") or DEFAULT_RAG_API_URL
    )
    default_api = normalize_api_url(default_api)
    api_url = st.text_input(
        "API base URL",
        value=default_api,
        placeholder="https://api-id.execute-api.us-east-1.amazonaws.com",
        help="The base URL for the RAG API endpoint (without /query suffix)",
    )
    st.markdown("---")
    st.subheader("ℹ️ How it works")
    st.markdown(
        """
This service is built on top of a database of relevant PubMed article abstracts 
focused on dementia care and caregiving. When you ask a question:

1. **Retrieval**: Searches the knowledge base for relevant abstracts and clinical evidence
2. **Generation**: Uses AI to synthesize an evidence-based answer from the retrieved sources
3. **Citation**: Provides source citations so you can verify and explore further

Built with AWS Bedrock Knowledge Bases, OpenSearch Serverless, and Claude. 

[GitHub Repository](https://github.com/adzuci/pubmed-rag-system)
"""
    )


def render_chat(history):
    """Render chat history in a scrollable container."""
    if not history:
        st.markdown(
            """
<div class="welcome-message">
  <p class="welcome-title">Ask a question to get started</p>
  <p class="welcome-subtitle">I'll help you find evidence-based answers about dementia care using relevant PubMed research papers and clinical evidence.</p>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sample-questions">', unsafe_allow_html=True)
        st.markdown("#### Try a sample question")
        samples = [
            "What are evidence-based strategies for managing sleep disturbances in people with dementia?",
            "What does the research say about caregiver burden in early-stage Alzheimer's disease?",
            "Are there effective non-pharmacological interventions for agitation in dementia patients?",
            "What interventions help reduce caregiver stress and burnout?",
        ]

        for idx, sample in enumerate(samples):
            if st.button(sample, use_container_width=True, key=f"sample_{idx}"):
                st.session_state["pending_question"] = sample
                st.session_state["auto_submit"] = True
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Render chat messages
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


# Chat container with scrolling
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
render_chat(st.session_state.chat_history)
st.markdown("</div>", unsafe_allow_html=True)

# Fixed input area at bottom
st.markdown('<div class="input-container">', unsafe_allow_html=True)
st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)

# Get pending question from sample button click, or use empty string
initial_value = st.session_state.get("pending_question", "")
if initial_value:
    # Clear pending question after using it
    del st.session_state["pending_question"]

col_input, col_button = st.columns([10, 1], gap="small")

with col_input:
    question = st.text_input(
        "",
        value=initial_value,
        placeholder="Ask a question about dementia care...",
        label_visibility="collapsed",
        key="question_input",
    )

with col_button:
    ask = st.button("Ask", type="primary", use_container_width=True, key="ask_button")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

auto_submit = bool(st.session_state.get("auto_submit"))
if ask or auto_submit:
    # Get API URL from sidebar or use default
    api_url = (
        normalize_api_url(api_url)
        if api_url
        else normalize_api_url(DEFAULT_RAG_API_URL)
    )
    if not api_url:
        st.error("Please set the API base URL in the sidebar (⚙️ icon).")
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
    # Clear auto_submit and rerun to show new answer (input will be empty on rerun)
    st.session_state["auto_submit"] = False
    st.rerun()
