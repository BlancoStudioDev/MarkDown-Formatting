import requests
import json
import os
from pypdf import PdfReader

# Configuration
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL_ID = "qwen/qwen3-vl-8b" # You might want to make this dynamic or fetch from API
NORMS_FILE = "SSMD_Norme editoriali (2025_01_07).docx.pdf"
TARGET_FILE = "salvatore_aranzulla.txt"
OUTPUT_FILE = "salvatore_aranzulla_formatted.md"
CHUNK_SIZE = 3000 # Approximate characters per "page"

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        print(f"Successfully extracted {len(text)} characters from norms file.")
        return text
    except Exception as e:
        print(f"Error reading PDF norms: {e}")
        return ""

def read_target_file(file_path):
    """Reads the content of the target text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading target file: {e}")
        return None

def chunk_text(text, chunk_size):
    """Splits text into chunks of approximately chunk_size, respecting paragraphs."""
    chunks = []
    current_chunk = ""
    paragraphs = text.split('\n\n') # Assumes paragraphs are separated by double newlines

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) < chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = paragraph + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def process_chunk(chunk, norms, chunk_index, total_chunks):
    """Sends a chunk to LM Studio for formatting."""
    
    system_prompt = f"""You are a professional editor. Your task is to format the provided text into Markdown, strictly following the editorial norms provided below.
    
    IMPORTANT RULES:
    1. DO NOT change the content of the text. Only change the formatting (e.g., make titles actual Markdown headers like # Title).
    2. Apply the formatting rules described in the "Editorial Norms" section.
    3. If a rule is not mentioned in the norms, do not apply it.
    4. Return ONLY the formatted Markdown text. Do not add conversational filler.

    --- EDITORIAL NORMS START ---
    {norms}
    --- EDITORIAL NORMS END ---
    """

    user_message = f"Here is the text to format (Part {chunk_index + 1}/{total_chunks}):\n\n{chunk}"

    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.1, # Low temperature for consistent formatting
        "stream": False
    }

    try:
        print(f"Processing chunk {chunk_index + 1}/{total_chunks}...")
        response = requests.post(LM_STUDIO_URL, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            formatted_text = result['choices'][0]['message']['content']
            return formatted_text
        else:
            print(f"Error from API: {response.status_code} - {response.text}")
            return f"<!-- Error processing chunk {chunk_index + 1} -->\n{chunk}"
    except Exception as e:
        print(f"Exception processing chunk: {e}")
        return f"<!-- Exception processing chunk {chunk_index + 1} -->\n{chunk}"

def main():
    print("--- Document Processor Started ---")

    # 1. Load Norms
    if os.path.exists(NORMS_FILE):
        norms_text = extract_text_from_pdf(NORMS_FILE)
    else:
        print(f"Warning: Norms file '{NORMS_FILE}' not found. Proceeding without specific norms.")
        norms_text = "No specific editorial norms provided. Use standard Markdown formatting."

    # 2. Load Target File
    if not os.path.exists(TARGET_FILE):
        print(f"Error: Target file '{TARGET_FILE}' not found.")
        return

    content = read_target_file(TARGET_FILE)
    if not content:
        return

    # 3. Chunk Content
    chunks = chunk_text(content, CHUNK_SIZE)
    print(f"Split document into {len(chunks)} chunks (approx {CHUNK_SIZE} chars each).")

    # 4. Process Chunks
    formatted_content = ""
    for i, chunk in enumerate(chunks):
        formatted_chunk = process_chunk(chunk, norms_text, i, len(chunks))
        formatted_content += formatted_chunk + "\n\n"

    # 5. Save Output
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        print(f"Successfully saved formatted document to: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error saving output file: {e}")

if __name__ == "__main__":
    main()
