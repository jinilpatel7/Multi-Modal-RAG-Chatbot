"""
text_extraction.py  –  All heavy imports are lazy (inside functions).
easyocr / pytesseract removed; image text extraction uses pytesseract-free
approach via PyMuPDF for embedded PDFs, and Pillow for plain images.
"""

import tempfile
import re
import io
import pandas as pd


# ── Helpers ──────────────────────────────────────────────────────────────────

def extract_text_from_file(file) -> str:
    """Route a Streamlit UploadedFile to the correct extractor."""
    name = file.name.lower()

    # ── Tabular files → handled as DataFrames, not text ──────────────────
    if name.endswith((".csv", ".xls", ".xlsx")):
        df = extract_dataframe_from_file(file)
        return f"[{file.name}]\n{df.to_string(index=False)}" if df is not None else ""

    # ── PDF ──────────────────────────────────────────────────────────────
    if name.endswith(".pdf"):
        import fitz  # PyMuPDF
        text = ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        doc = fitz.open(tmp_path)
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    # ── Word doc ─────────────────────────────────────────────────────────
    if name.endswith(".docx"):
        import docx2txt
        return docx2txt.process(file)

    # ── Plain text ────────────────────────────────────────────────────────
    if name.endswith(".txt") or file.type == "text/plain":
        return file.read().decode("utf-8", errors="ignore")

    # ── Images  (basic: return a note — OCR requires easyocr / tesseract) ─
    if file.type and file.type.startswith("image"):
        return f"[Image uploaded: {file.name} — text extraction not enabled]"

    # ── Fallback ──────────────────────────────────────────────────────────
    try:
        return file.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return f"[Extraction error for {file.name}: {e}]"


def extract_dataframe_from_file(file):
    """Return a pandas DataFrame for CSV / Excel files, else None."""
    name = file.name.lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(file)
        if name.endswith((".xls", ".xlsx")):
            return pd.read_excel(file)
    except Exception:
        pass
    return None


def extract_text_from_youtube(url: str) -> str:
    """Fetch the transcript of a YouTube video."""
    try:
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        if not match:
            return f"[Invalid YouTube URL: {url}]"
        video_id = match.group(1)
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join(t["text"] for t in transcript)
    except Exception as e:
        return f"[YouTube Error: {e}]"


def extract_text_from_url(url: str) -> str:
    """Scrape visible text from a webpage."""
    try:
        import requests
        from bs4 import BeautifulSoup
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        return f"[Web Error: {e}]"
