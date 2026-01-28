import os

import requests
import streamlit as st


st.set_page_config(page_title="PubMed RAG", page_icon="🧠")
st.title("PubMed RAG Prototype")

default_api = os.getenv("RAG_API_URL", "").rstrip("/")
api_url = st.text_input("API base URL", value=default_api, placeholder="https://api-id.execute-api.us-east-1.amazonaws.com")
question = st.text_area("Question", height=120)

if st.button("Ask"):
    if not api_url:
        st.error("Set the API base URL.")
        st.stop()
    if not question.strip():
        st.error("Enter a question.")
        st.stop()

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
    st.subheader("Answer")
    st.write(payload.get("answer", ""))

    sources = payload.get("sources", [])
    if sources:
        st.subheader("Sources")
        for idx, source in enumerate(sources, start=1):
            st.markdown(f"**Source {idx}**")
            st.write(source.get("text", ""))
            st.json(source.get("metadata", {}))
