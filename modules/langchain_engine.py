import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from .preprocessing import preprocess_and_split_text
from .vector_store import init_vector_store

embeddings = None
db = None
retriever = None
qa_chain = None

def initialize_chain():
    global embeddings, db, retriever, qa_chain

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})

    db = init_vector_store(embeddings)
    retriever = db.as_retriever()

    llm = HuggingFaceHub(
        repo_id="mistralai/Mistral-7B-Instruct-v0.3",
        model_kwargs={"temperature": 0.3, "max_new_tokens": 512}
    )

    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="""
        You are a helpful assistant. You must answer ONLY using the provided context.

        Context: {context}
        
        Question: {question}

        Answer:
        """
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt_template}
    )

def add_texts_to_vectorstore(texts):
    global db
    processed_chunks = []
    for text in texts:
        chunks = preprocess_and_split_text(text)
        processed_chunks.extend(chunks)
    db.add_texts(processed_chunks)

def handle_user_query(query):
    global qa_chain
    result = qa_chain.invoke({"query": query})
    return result['result'] if isinstance(result, dict) else result

def reset_conversation():
    global db
    db.delete_collection()
    db = init_vector_store(embeddings)
