import easyocr
import docx2txt
import fitz 
from PIL import Image
from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
import requests
import tempfile
import re
import io


reader = easyocr.Reader(['en'], gpu=False)

def extract_text_from_file(file):
    if file.type.startswith("image"):
        try:
            image_bytes = file.read()
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            result = reader.readtext(image_bytes, detail=0)
            return "\n".join(result)
        except Exception as e:
            return f"[Image Extraction Error: {e}]"
        
    elif file.name.endswith(".pdf"):
        text = ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file.read())
            doc = fitz.open(tmp_file.name)
            for page in doc:
                text += page.get_text()
        return text

    elif file.name.endswith(".docx"):
        return docx2txt.process(file)

    else:
        return file.read().decode('utf-8')

def extract_text_from_youtube(url):
    extracted_text = ""
    try:
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        if match:
            video_id = match.group(1)
        else:
            return f"[Invalid YouTube URL: {url}]"

        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        extracted_text = " ".join([t['text'] for t in transcript])

    except Exception as e:
        extracted_text = f"[YouTube Extraction Error: {e}]"

    return extracted_text

def extract_text_from_url(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        return f"[Web Extraction Error: {e}]"

