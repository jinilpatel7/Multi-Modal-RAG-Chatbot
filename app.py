import streamlit as st
from dotenv import load_dotenv
from modules.input_handler import handle_inputs
from modules.langchain_engine import (
    initialize_chain,
    handle_user_query,
    add_texts_to_vectorstore,
    reset_conversation
)
from htmlTemplates import css, bot_template, user_template
import re

st.set_page_config(page_title="Multi-Modal RAG Chatbot", layout="wide")
st.title("🤖 Multi-Modal RAG Chatbot")
st.write(css, unsafe_allow_html=True)

load_dotenv()

if "conversation" not in st.session_state:
    initialize_chain()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""

def clean_answer(answer):
    """Remove prompt template artifacts from the answer."""
    if "Answer:" in answer:
        answer = answer.split("Answer:", 1)[-1].strip()
    answer = re.sub(r'^You are a helpful assistant.*?\n+', '', answer, flags=re.DOTALL)
    return answer.strip()

user_question = st.text_input("Ask a question based on uploaded content")
if user_question:
    answer = handle_user_query(user_question)
    answer = clean_answer(answer)
    st.session_state.chat_history.append({"role": "user", "content": user_question})
    st.session_state.chat_history.append({"role": "bot", "content": answer})

for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.write(user_template.replace("{{MSG}}", message["content"]), unsafe_allow_html=True)
    elif message["role"] == "bot":
        st.write(bot_template.replace("{{MSG}}", message["content"]), unsafe_allow_html=True)

with st.sidebar:
    st.subheader("Your Input Sources")
    uploaded_files = st.file_uploader("Upload documents/images", accept_multiple_files=True)
    youtube_url = st.text_input("Enter YouTube URL")
    website_url = st.text_input("Enter Website URL")

    if st.button("Extract Text"):
        with st.spinner("Processing inputs..."):
            texts = handle_inputs(uploaded_files, youtube_url, website_url)
            combined_text = "\n\n".join(texts)
            st.session_state.extracted_text = combined_text
            add_texts_to_vectorstore(texts)

    if st.session_state.extracted_text:
        st.subheader("Extracted Text")
        st.text_area("", st.session_state.extracted_text, height=400)

if st.button("Exit Chat"):
    reset_conversation()
    st.session_state.chat_history = []
    st.session_state.extracted_text = ""
    st.success("Chat cleared!")