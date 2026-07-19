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

# --- MYTEACHERZA FREE GEMINI CHAT ENGINE (AGENTS 6-13 INTEGRATION) ---
from google import genai
from pydantic import BaseModel

# Initialize the free Gemini client using your environment variable
# Make sure you name your key 'GEMINI_API_KEY' in your Render environment setup
client = genai.Client()

class StudentPayload(BaseModel):
    whatsapp_number: str
    student_message: str
    image_url: str | None = None
    academic_tier: str          # e.g., "Tier 3: Critical Support"
    cognitive_style: str        # e.g., "Visual-Spatial Learner"
    delivery_element: str       # e.g., "Earth (Structured, Step-by-Step)"
    caps_subject_topic: str     # e.g., "Mathematics Grade 11 - Quadratics"
    curriculum_theory: str      # Textbook rules / DBE planner details

@app.post("/api/v1/tutor/chat")
async def handle_tutor_request(payload: StudentPayload):
    try:
        # Detect if student wants practice or general explanation (Agent 10: Mode Router)
        is_practice_request = any(word in payload.student_message.lower() for word in ["practice", "question", "quiz", "test", "activity", "exam"])

        # Compile the multi-agent instructions combining your onboarding logic (Agents 1-5)
        system_prompt = f"""
        You are the core intelligence engine of MyTeacherZA, a premium South African learning platform. 
        You operate seamlessly across the entire CAPS curriculum, utilizing official DBE guidelines.
        
        The student you are interacting with has been profiled using your Onboarding & Psychology system (Agents 1-5):
        - Academic Performance Tier: {payload.academic_tier}
        - Cognitive Processing Vector: {payload.cognitive_style}
        - Communication / Element Delivery Style: {payload.delivery_element}
        
        Your instructions change dynamically based on the student's request:
        """

        if is_practice_request:
            # Embody Agent 12 (Activities Coach) & Agent 13 (Exam Invigilator)
            system_prompt += f"""
            ACTIVATION: You are now acting as 'MyTeacherZA — The Activities Coach' and 'The Mock Exam Invigilator'.
            - Reference the current CAPS topic: {payload.caps_subject_topic} and context: {payload.curriculum_theory}.
            - Your task is to provide precision practice or mirror an NSC exam environment.
            - If the textbook/planner examples are exhausted, GENERATE a brand-new, original practice question.
            - This question must perfectly mirror the exact difficulty, styling, and marking standards found in official South African past papers and textbooks.
            - Present the question clearly, and wait for the student to answer before providing the marking memorandum rules.
            """
        else:
            # Embody Agent 11 (The Tutor) with integrated Web-Style Knowledge
            system_prompt += f"""
            ACTIVATION: You are now acting as 'MyTeacherZA — The Tutor'.
            - Your task is to explain and remediate conceptual gaps for the CAPS topic: {payload.caps_subject_topic}.
            - Current Baseline Material: {payload.curriculum_theory}.
            - Use clear, real-world analogies to make the concept click.
            - Tailor the explanation strictly to a {payload.cognitive_style} who thrives under the {payload.delivery_element} communication style.
            - Apply a strict Socratic Method: guide the student step-by-step with small prompts. NEVER just give the answer away.
            """

        system_prompt += """
        WHATSAPP FORMATTING RULES:
        - Keep responses short, concise, and highly scannable.
        - Use bold text (*text*) for emphasis and key terms.
        - Use bullet points to break down multi-step concepts cleanly on a mobile screen.
        """

        # Execute via the highly optimized, free gemini-2.5-flash model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Student Message: {payload.student_message}\nImage Attachment: {payload.image_url if payload.image_url else 'None'}",
            config={'system_instruction': system_prompt, 'temperature': 0.3}
        )

        ai_response = response.text

        return {
            "status": "success",
            "whatsapp_number": payload.whatsapp_number,
            "response_text": ai_response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

 
