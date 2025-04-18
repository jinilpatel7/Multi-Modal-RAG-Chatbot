from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def preprocess_and_split_text(text, chunk_size=1000, chunk_overlap=200):
    text = clean_text(text)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = splitter.split_text(text)
    return chunks[:50]