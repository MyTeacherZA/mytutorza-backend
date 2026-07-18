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


# --- CREWAI DYNAMIC TUNER ENGINE (AGENTS 6-13 INTERACTION ENDPOINT) ---
from pydantic import BaseModel
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import SerperDevTool # Tool allowing Agent 11 to search the web

# 1. Structured data input package coming from your frontend/database
class StudentPayload(BaseModel):
    whatsapp_number: str
    student_message: str
    image_url: str | None = None
    academic_tier: str          # e.g., "Tier 3: Critical Support"
    cognitive_style: str        # e.g., "Visual-Spatial Learner"
    delivery_element: str       # e.g., "Earth (Structured, Step-by-Step)"
    caps_subject_topic: str     # e.g., "Mathematics Grade 11 - Quadratic Equations"
    curriculum_theory: str      # Textbook rules/DBE planning text pulled from Drive

@app.post("/api/v1/tutor/chat")
async def handle_tutor_request(payload: StudentPayload):
    try:
        # 2. Dynamic Backstory Compilation
        # Automatically embeds the results from Agents 1-5 (Onboarding & Psychology Profiling)
        persona_role = f"Dynamic South African CAPS Master Educator specialized for {payload.academic_tier}"
        
        dynamic_backstory = f"""
        You are an elite, highly empathetic educator executing the South African CAPS curriculum.
        Your teaching alignment matrix is strictly customized to this student profile:
        - Cognitive Processing Vector: {payload.cognitive_style}
        - Communication / Element Delivery Style: {payload.delivery_element}
        - Academic Performance Tier: {payload.academic_tier}
        
        You dynamically embody one of Three Faces depending on student intent:
        1. MyTeacherZA - The Tutor (Agent 11): Teaches, remediates core conceptual gaps.
        2. MyTeacherZA - The Activities Coach (Agent 12): Runs precision practice, tracks answers.
        3. MyTeacherZA - The Mock Exam Invigilator (Agent 13): Mimics strict NSC-mirror exam conditions.
        
        Adapt your language, pacing, and scaffolding to match this matrix perfectly. Never give 
        the answer away—use a strict Socratic method to guide them to the next logical step. 
        Format responses cleanly with bolding and bullet points for WhatsApp mobile view limits.
        """

        # 3. Setup the Single Dynamic Agent with Web Search capabilities
        web_search_tool = SerperDevTool()
        
        dynamic_tutor_agent = Agent(
            role=persona_role,
            goal="Provide immediate, personalized, CAPS-aligned academic guidance, practice, or assessment.",
            backstory=dynamic_backstory,
            tools=[web_search_tool],
            allow_delegation=False,
            verbose=False,
            llm=LLM(model="openai/gpt-4o-mini") # Lightning-fast, cost-optimized processing
        )

        # 4. Formulate the Execution Task with your exact custom tweaks
        delivery_task = Task(
            description=f"""
            Analyze the student's message and activate the correct Face:
            
            1. IF THE STUDENT NEEDS AN EXPLANATION (Face 11: The Tutor):
               - Assess the CAPS topic context: {payload.caps_subject_topic} and theory baseline: {payload.curriculum_theory}.
               - USE THE WEB search tool to find alternative real-world analogies or alternative educational frameworks if textbook explanations feel dry.
               - Filter all web insights strictly through the student's cognitive processing vector ({payload.cognitive_style}) and delivery element style ({payload.delivery_element}).
               
            2. IF THE STUDENT NEEDS PRACTICE OR TESTING (Face 12 & 13: Coach / Invigilator):
               - Assess the baseline textbook exercises/exam memo content provided.
               - IF the student has exhausted the textbook or planners, GENERATE a completely original, brand-new practice activity or exam question from scratch.
               - Ensure your generated questions strictly mirror the structure, difficulty formatting, and marking guidelines set by official DBE and NSC standards.
            
            Student Message: "{payload.student_message}"
            Image Attachment Link: {payload.image_url if payload.image_url else 'None'}
            
            Instructions:
            - Formulate a tailored, highly impactful Socratic response.
            - Provide a clear guiding question or highlight the immediate next logical sub-step.
            - Format with clean markdown bold text and short bullet points optimized for WhatsApp mobile screens.
            """,
            expected_output="A perfectly formatted WhatsApp message tailored to the student's processing style.",
            agent=dynamic_tutor_agent
        )

        # 5. Run the single-task pipeline immediately on Render
        crew = Crew(
            agents=[dynamic_tutor_agent],
            tasks=[delivery_task],
            process=Process.sequential,
            verbose=False
        )
        
        result = crew.kickoff()
        
        return {
            "status": "success",
            "whatsapp_number": payload.whatsapp_number,
            "response_text": str(result)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
