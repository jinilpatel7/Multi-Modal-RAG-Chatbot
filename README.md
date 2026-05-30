A streamlined AI chatbot that uses **Retrieval-Augmented Generation (RAG)** to answer user questions from various input types — including documents, images (OCR), YouTube videos, and websites.

Built with **Streamlit**, **LangChain**, **ChromaDB**, and **Hugging Face Transformers**, this app provides an interactive and contextual AI experience from your own content.

---

## ✨ Features

- 📁 Upload documents: `PDF`, `DOCX`, `TXT`, and images (`PNG`, `JPG`) with OCR
- 📺 Add a YouTube video URL — it fetches the transcript using `youtube-transcript-api`
- 🌐 Add a Website URL — it scrapes and extracts main content using `BeautifulSoup`
- 💬 Ask natural language questions and receive answers based **only on your input content**
- 🧠 Powered by `Mistral-7B-Instruct` via Hugging Face API
- 📚 Automatic text chunking and preprocessing for optimal retrieval
- 🗂️ Stores content using semantic embeddings with `ChromaDB`
- 🔄 "Exit Chat" button clears all inputs, vector database, and chat history

---

## 🧱 Tech Stack

| Layer         | Tools Used                                    |
|---------------|-----------------------------------------------|
| Frontend UI   | Streamlit                                     |
| LLM Backend   | LangChain + Hugging Face Inference API        |
| Embeddings    | all-MiniLM-L6-v2 via `HuggingFaceEmbeddings`  |
| OCR           | EasyOCR                                       |
| Parsing       | PyMuPDF, docx2txt, Pillow                     |
| Scraping      | BeautifulSoup + Requests                      |
| YouTube       | youtube-transcript-api                        |
| Vector Store  | ChromaDB                                      |
