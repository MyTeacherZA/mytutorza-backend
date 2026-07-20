# --- build_cache.py ---
import os
import time
from google import genai
from google.genai import types

# 1. Grab the API key your server already uses
GEMINI_API_KEY = os.getenv("gemini_api_key")
if not GEMINI_API_KEY:
    raise ValueError("Missing 'gemini_api_key' environment variable.")

client = genai.Client(api_key=GEMINI_API_KEY)

# 2. Point to our local folder
PDF_DIRECTORY = "./curriculum_pdfs" 

if not os.path.exists(PDF_DIRECTORY):
    raise FileNotFoundError(f"The folder {PDF_DIRECTORY} does not exist. Please upload your PDFs.")

uploaded_file_objects = []
print("Starting upload of local curriculum files to Gemini API...")

# 3. Read the folder and upload files one by one
for file_name in os.listdir(PDF_DIRECTORY):
    if file_name.lower().endswith('.pdf'):
        file_path = os.path.join(PDF_DIRECTORY, file_name)
        print(f"Uploading: {file_name}...")
        
        uploaded_file = client.files.upload(file=file_path)
        uploaded_file_objects.append(uploaded_file)

if not uploaded_file_objects:
    print("No PDF files found in the folder. Please add your documents first.")
    exit()

print("Waiting for Gemini servers to process the documents...")
for f in uploaded_file_objects:
    live_file = client.files.get(name=f.name)
    while live_file.state.name == "PROCESSING":
        time.sleep(2)
        live_file = client.files.get(name=f.name)
    if live_file.state.name == "FAILED":
        print(f"File {live_file.display_name} failed processing.")

print("All files ready! Generating the long-term context cache...")

system_instruction = (
    "You are the ultimate personalized core of MyTeacherZA. You operate strictly under "
    "the official Department of Basic Education (DBE) planners and the CAPS curriculum matrix "
    "provided in these documents. You treat all 11 official South African languages with equal "
    "academic rigour, precision, and formal standardized terminology."
)

# 4. Lock them into the server-side cache
curriculum_cache = client.caches.create(
    model="gemini-2.5-pro", 
    config=types.CreateCachedContentConfig(
        contents=uploaded_file_objects,
        displayName="myteacherza_local_vault",
        ttl="259200s", # 3-day token lifespan
        system_instruction=system_instruction
    )
)

print("\n" + "="*60)
print("SUCCESS: CONTEXT CACHE GENERATED")
print(f"CACHE ID / NAME: {curriculum_cache.name}")
print("="*60)
