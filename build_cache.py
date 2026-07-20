# --- build_cache.py ---
import os
import time
import zipfile
import requests
from google import genai
from google.genai import types

# 1. Initialize Gemini
GEMINI_API_KEY = os.getenv("gemini_api_key")
if not GEMINI_API_KEY:
    raise ValueError("Missing 'gemini_api_key' environment variable.")

client = genai.Client(api_key=GEMINI_API_KEY)

# 2. Extract your Google Drive File ID from your link
# Paste your copied Google Drive zip file link inside the quotes below:
DRIVE_ZIP_LINK = "PASTE_YOUR_GOOGLE_DRIVE_ZIP_LINK_HERE"

def download_and_unzip(url):
    print("Extracting Drive ID and starting secure download...")
    # Convert standard view link to direct download link
    if "/d/" in url:
        file_id = url.split("/d/")[1].split("/")[0]
    else:
        raise ValueError("Invalid Google Drive Link format.")
        
    download_url = f"https://docs.google.com/uc?export=download&id={file_id}"
    
    os.makedirs("./curriculum_pdfs", exist_ok=True)
    zip_path = "./curriculum.zip"
    
    # Stream download the file
    response = requests.get(download_url, stream=True)
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                
    print("Download complete. Unzipping all 200 files into production storage...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall("./curriculum_pdfs")
    print("Unzipped successfully.")

# Execute download setup
download_and_unzip(DRIVE_ZIP_LINK)

# 3. Process and upload files to Gemini
PDF_DIRECTORY = "./curriculum_pdfs"
uploaded_file_objects = []

print("Uploading files to Gemini API...")
for file_name in os.listdir(PDF_DIRECTORY):
    if file_name.lower().endswith('.pdf'):
        file_path = os.path.join(PDF_DIRECTORY, file_name)
        print(f"Processing: {file_name}")
        uploaded_file = client.files.upload(file=file_path)
        uploaded_file_objects.append(uploaded_file)

print("Waiting for Gemini servers to align content parameters...")
for f in uploaded_file_objects:
    live_file = client.files.get(name=f.name)
    while live_file.state.name == "PROCESSING":
        time.sleep(2)
        live_file = client.files.get(name=f.name)

print("Building long-term semantic context cache...")
system_instruction = (
    "You are the ultimate personalized core of MyTeacherZA. You operate strictly under "
    "the official Department of Basic Education (DBE) planners and the CAPS curriculum matrix "
    "provided in these documents. You treat all 11 official South African languages with equal "
    "academic rigour, precision, and formal standardized terminology."
)

curriculum_cache = client.caches.create(
    model="gemini-2.5-pro", 
    config=types.CreateCachedContentConfig(
        contents=uploaded_file_objects,
        displayName="myteacherza_drive_vault",
        ttl="259200s",
        system_instruction=system_instruction
    )
)

print("\n" + "="*60)
print("SUCCESS: CONTEXT CACHE GENERATED FROM DRIVE")
print(f"CACHE ID / NAME: {curriculum_cache.name}")
print("="*60)
