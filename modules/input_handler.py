from .text_extraction import extract_text_from_file, extract_text_from_youtube, extract_text_from_url, extract_dataframe_from_file

def handle_inputs(files, youtube_url, website_url):
    texts = []
    dataframes = []
    if files:
        for file in files:
            # Check if it's a dataframe file first
            df = extract_dataframe_from_file(file)
            if df is not None:
                dataframes.append({"name": file.name, "df": df})
                # Convert first few rows to text for basic search capability if desired
                texts.append(f"Data from {file.name}:\n" + df.head(10).to_string())
            else:
                texts.append(extract_text_from_file(file))
    if youtube_url:
        texts.append(extract_text_from_youtube(youtube_url))
    if website_url:
        texts.append(extract_text_from_url(website_url))
    return texts, dataframes
