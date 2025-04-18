from langchain_community.vectorstores import Chroma

def init_vector_store(embedding_function):
    return Chroma(embedding_function=embedding_function, persist_directory="./chroma_db")
