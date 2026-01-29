import logging
import os
import re

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

# Google Analytics tracking
st.markdown(
    """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-3TZ2EQTPMP"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-3TZ2EQTPMP');
</script>
""",
    unsafe_allow_html=True,
)

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
    padding-bottom: 150px; 
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
  
  /* Chat container - scrollable above fixed input */
  .chat-container { 
    min-height: auto; 
    padding-bottom: 120px; 
    background-color: var(--bg-primary);
    max-height: calc(100vh - 200px);
    overflow-y: auto;
    margin-bottom: 0;
  }
  
  /* Status message area (above input, ChatGPT-like) - doesn't shift input */
  .status-message-container {
    position: fixed !important;
    bottom: 80px !important;
    left: 0 !important;
    right: 0 !important;
    max-width: 900px;
    margin: 0 auto;
    padding: 0 1rem;
    z-index: 999 !important;
    pointer-events: none;
    height: auto;
  }
  .status-message-container > div {
    pointer-events: auto;
    background: transparent;
  }
  .status-message-container > div > div {
    background: transparent !important;
  }
  
  /* Fixed input at bottom - always visible */
  .input-container { 
    position: fixed !important; 
    bottom: 0 !important; 
    left: 0 !important; 
    right: 0 !important; 
    background: var(--bg-primary) !important; 
    border-top: 1px solid var(--border-color); 
    padding: 1rem; 
    z-index: 1000 !important;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
    width: 100%;
  }
  .input-wrapper { 
    max-width: 900px; 
    margin: 0 auto; 
  }
  .input-wrapper [data-testid="column"] {
    padding: 0 0.25rem;
  }
  .input-wrapper [data-testid="column"]:first-child {
    flex: 1;
  }
  .input-wrapper [data-testid="column"]:last-child {
    flex-shrink: 0;
    display: flex;
    align-items: center;
  }
  
  /* Buttons */
  .stButton>button { 
    background: var(--button-primary); 
    color: var(--button-text); 
    border-radius: 8px; 
    padding: 0.6rem 1.2rem; 
    font-weight: 500;
    height: 38px;
    border: none;
    white-space: nowrap;
    margin-top: 0;
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
    height: 38px;
    box-sizing: border-box;
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
    padding: 2rem 1rem 1.5rem; 
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
    margin-top: 1rem; 
    margin-bottom: 1rem;
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
  
  /* User avatar padding (red human emoji) - target the avatar container */
  [data-testid="stChatMessage"] {
    padding-left: 1rem !important;
  }
  /* User message avatar - add padding inside the avatar square */
  [data-testid="stChatMessage"] [data-testid="stChatAvatar"] {
    padding: 1rem !important;
    margin-left: 0.5rem !important;
    margin-right: 0.75rem !important;
  }
  /* Ensure user message container has left padding */
  [data-testid="stChatMessage"] > div:first-child {
    padding-left: 0.5rem !important;
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
    margin-top: 1rem;
  }
  [data-testid="stExpander"] summary {
    color: var(--text-secondary);
    font-weight: 600;
  }
  /* Sources styling */
  .sources-container {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-color);
  }
  .sources-container [data-testid="stExpander"] {
    margin-bottom: 0.5rem;
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
  // Make Enter key trigger submit (ChatGPT-like behavior)
  document.addEventListener('keydown', function(e) {
    // Only handle Enter key on text inputs
    if (e.target.tagName === 'INPUT' && e.target.getAttribute('data-testid') === 'stTextInput') {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        
        // Find the Ask button - try multiple selectors
        let askButton = document.querySelector('button[data-testid*="ask_button"]');
        if (!askButton) {
          // Try by key attribute directly
          askButton = document.querySelector('button[key*="ask_button"]');
        }
        if (!askButton) {
          askButton = document.querySelector('button[kind="primaryFormSubmit"]');
        }
        if (!askButton) {
          // Fallback: find button with "Ask" text near the input
          const inputContainer = e.target.closest('.input-wrapper') || e.target.closest('.input-container');
          if (inputContainer) {
            const buttons = Array.from(inputContainer.querySelectorAll('button'));
            askButton = buttons.find(btn => btn.textContent && btn.textContent.trim() === 'Ask');
          }
        }
        if (askButton && !askButton.disabled) {
          setTimeout(() => askButton.click(), 10);
          return false;
        }
      }
    }
  }, true);
  
  // Auto-scroll to bottom when new messages appear
  function autoScroll() {
    // Try to scroll the chat container
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    // Also scroll the main block container
    const blockContainer = document.querySelector('.block-container');
    if (blockContainer) {
      blockContainer.scrollTop = blockContainer.scrollHeight;
    }
    // Also scroll window to bottom (for mobile/fallback)
    setTimeout(() => {
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }, 100);
  }
  
  // Run on load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(autoScroll, 200);
    });
  } else {
    setTimeout(autoScroll, 200);
  }
  
  // Also scroll after Streamlit reruns (when new content is added)
  const scrollObserver = new MutationObserver((mutations) => {
    // Check if new chat messages were added
    let shouldScroll = false;
    mutations.forEach(mutation => {
      if (mutation.addedNodes.length > 0) {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === 1 && (
            node.querySelector && (
              node.querySelector('[data-testid="stChatMessage"]') ||
              node.matches && node.matches('[data-testid="stChatMessage"]')
            )
          )) {
            shouldScroll = true;
          }
        });
      }
    });
    if (shouldScroll) {
      setTimeout(autoScroll, 500);
    }
  });
  scrollObserver.observe(document.body, { childList: true, subtree: true });
  
  // Also listen for Streamlit's custom events
  window.addEventListener('load', () => setTimeout(autoScroll, 300));
  
  // Force scroll after Streamlit reruns complete
  window.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'streamlit:rerun') {
      setTimeout(autoScroll, 600);
    }
  });
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

    # Read version from VERSION file or environment variable
    try:
        # Try environment variable first (set by Dockerfile)
        image_version = os.getenv("APP_VERSION", "")
        if not image_version:
            # Try VERSION file in same directory as app.py (container)
            version_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "VERSION"
            )
            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    image_version = f.read().strip()
            else:
                # Fallback to repo root (for local development)
                repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                version_file = os.path.join(repo_root, "VERSION")
                if os.path.exists(version_file):
                    with open(version_file, "r") as f:
                        image_version = f.read().strip()
                else:
                    image_version = "unknown"
    except Exception:
        image_version = "unknown"

    st.text_input(
        "Image version",
        value=f"v{image_version}",
        disabled=True,
        help="Current UI container image version",
    )

    st.markdown("---")
    st.subheader("ℹ️ How it works")
    st.markdown(
        """
This service searches a knowledge base of PubMed articles on dementia care. 
When you ask a question, it retrieves relevant abstracts and clinical evidence, 
synthesizes an evidence-based answer, and provides source links for verification.

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
        samples = [
            "What are evidence-based strategies for managing sleep disturbances in people with dementia?",
            "What does the research say about caregiver burden in early-stage Alzheimer's disease?",
            "Are there effective non-pharmacological interventions for agitation in dementia patients?",
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
            # Debug: log sources to help diagnose
            if sources:
                logger.info(f"Found {len(sources)} sources for entry")
                logger.info(
                    f"First source structure: {sources[0] if sources else 'None'}"
                )
            if sources and len(sources) > 0:
                st.markdown('<div class="sources-container">', unsafe_allow_html=True)
                st.markdown(f"**📚 Sources ({len(sources)})**")
                for idx, source in enumerate(sources, start=1):
                    # Handle both dict and direct metadata access
                    source_text = ""
                    if isinstance(source, dict):
                        metadata = source.get("metadata", {}) or {}
                        source_text = source.get("text", "") or ""
                        # Also check if metadata is nested or flat
                        if not metadata and isinstance(source.get("metadata"), dict):
                            metadata = source.get("metadata", {})
                    else:
                        metadata = {}
                        source_text = str(source) if source else ""

                    # Try multiple ways to get PMID
                    pmid = None
                    if isinstance(metadata, dict):
                        pmid = (
                            metadata.get("pmid")
                            or metadata.get("PMID")
                            or metadata.get("id")
                        )
                    title = (
                        metadata.get("title", "") if isinstance(metadata, dict) else ""
                    )

                    # Try to find PMID in text if not in metadata
                    if not pmid and source_text:
                        pmid_match = re.search(
                            r"PMID[:\s]+(\d+)", source_text, re.IGNORECASE
                        )
                        if pmid_match:
                            pmid = pmid_match.group(1)

                    # Create expander with source content
                    expander_label = f"Source {idx}"
                    if title:
                        expander_label = f"Source {idx}: {title[:50]}{'...' if len(title) > 50 else ''}"
                    elif pmid:
                        expander_label = f"Source {idx} (PMID: {pmid})"

                    with st.expander(expander_label, expanded=False):
                        # Show abstract/text
                        if source_text:
                            st.markdown("**Abstract:**")
                            st.markdown(source_text)

                        # Show metadata if available
                        if metadata:
                            st.markdown("**Metadata:**")
                            st.json(metadata)

                        # Show PubMed link if PMID available
                        if pmid:
                            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}"
                            st.markdown(
                                f'<a href="{pubmed_url}" target="_blank" rel="noopener noreferrer" style="color: var(--button-primary);">🔗 View on PubMed</a>',
                                unsafe_allow_html=True,
                            )
                st.markdown("</div>", unsafe_allow_html=True)


# Chat container with scrolling
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
render_chat(st.session_state.chat_history)
st.markdown("</div>", unsafe_allow_html=True)

# Status message area (above input, ChatGPT-like)
status_container = st.empty()

# Fixed input area at bottom
st.markdown('<div class="input-container">', unsafe_allow_html=True)
st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)

# Get pending question from sample button click, or use empty string
initial_value = st.session_state.get("pending_question", "")
# Clear input after answer is submitted
if st.session_state.get("clear_input", False):
    initial_value = ""
    st.session_state["clear_input"] = False
if initial_value:
    # Clear pending question after using it
    del st.session_state["pending_question"]

col_input, col_button = st.columns([1, 0.15], gap="small")

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

    # Show retrieving message above input (ChatGPT-like) - positioned fixed, doesn't shift input
    with status_container.container():
        st.markdown(
            '<div style="text-align: center; color: var(--text-muted); padding: 0.5rem 1rem; font-size: 0.9em; background: transparent;">'
            "🔄 Retrieving sources and drafting answer..."
            "</div>",
            unsafe_allow_html=True,
        )

    try:
        resp = requests.post(
            f"{api_url}/query",
            json={"question": question.strip()},
            timeout=30,
        )
    except requests.RequestException as exc:
        status_container.empty()
        st.error(f"Request failed: {exc}")
        st.stop()

    # Clear status message
    status_container.empty()

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
    # Debug: log payload structure
    logger.info(f"API response keys: {payload.keys()}")
    logger.info(f"Sources in payload: {payload.get('sources', [])}")
    sources_list = payload.get("sources", [])
    if not isinstance(sources_list, list):
        sources_list = []
    st.session_state.chat_history.append(
        {
            "question": question.strip(),
            "answer": payload.get("answer", ""),
            "sources": sources_list,
        }
    )
    # Clear auto_submit and mark input for clearing
    st.session_state["auto_submit"] = False
    st.session_state["clear_input"] = True
    # Trigger scroll after rerun completes
    st.markdown(
        '<script>setTimeout(() => { window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" }); const chatContainer = document.querySelector(".chat-container"); if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight; }, 800);</script>',
        unsafe_allow_html=True,
    )
    st.rerun()
