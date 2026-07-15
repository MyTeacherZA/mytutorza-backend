# main.py
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client

# 1. Initialize FastAPI
app = FastAPI(title="MyTutorZA Backend", version="1.0")

# 2. Grab secure credentials from the Cloud Environment Variables
SUPABASE_URL = os.getenv("supabase_url")
SUPABASE_KEY = os.getenv("supabase_key")
GEMINI_API_KEY = os.getenv("gemini_api_key")

# Ensure critical variables are present when starting
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing Supabase credentials in environment variables!")

# 3. Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- ENDPOINTS ---

# Root status check
@app.get("/")
def read_root():
    return {
        "status": "ONLINE",
        "message": "MyTutorZA Backend is running 24/7",
        "timestamp": datetime.now().isoformat()
    }

# Live subscription check endpoint
@app.get("/api/subscription/check/{student_id}")
def check_subscription(student_id: str):
    try:
        # Query Supabase 'subscriptions' table
        response = supabase.table("subscriptions").select("*").eq("student_id", student_id).execute()
        
        if not response.data:
            return {
                "status": "INACTIVE",
                "reason": "No subscription record found in cloud database."
            }
            
        record = response.data[0]
        expiry_str = record.get("expires_at")
        
        # Handle datetime parsing from ISO or custom formats
        try:
            expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
        except ValueError:
            expiry = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
        
        if datetime.now() > expiry:
            return {
                "status": "EXPIRED",
                "reason": f"Subscription expired on {expiry_str}"
            }
            
        return {
            "status": record.get("status", "ACTIVE"),
            "expires_at": expiry_str,
            "token": record.get("transaction_token", "SUPABASE_SECURE_TX")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")
