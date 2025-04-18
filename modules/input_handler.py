from modules.text_extraction import extract_text_from_file, extract_text_from_youtube, extract_text_from_url

def handle_inputs(files, youtube_url, website_url):
    texts = []
    if files:
        for file in files:
            texts.append(extract_text_from_file(file))
    if youtube_url:
        texts.append(extract_text_from_youtube(youtube_url))
    if website_url:
        texts.append(extract_text_from_url(website_url))
    return texts

