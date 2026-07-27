# main.py 
import os
import ephem  # Fast, lightweight astronomical library for real-time Mercury coordinates
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from google import genai
from google.genai import types

# 1. Initialize FastAPI
app = FastAPI(title="MyTutorZA Backend", version="1.0")

# 2. Grab secure credentials from the Cloud Environment Variables
SUPABASE_URL = os.getenv("supabase_url")
SUPABASE_KEY = os.getenv("supabase_key")
GEMINI_API_KEY = os.getenv("gemini_api_key")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing Supabase credentials in environment variables!")

# 3. Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 4. Initialize Gemini Client & Cloud File Vault
client = genai.Client(api_key=GEMINI_API_KEY)
workspace_files = []

@app.on_event("startup")
def load_workspace_assets():
    """
    Warms up the server on boot by connecting to your Gemini Cloud Storage
    and building a live pointer array of all 3,000+ CAPS curriculum files.
    """
    global workspace_files
    try:
        print("🔗 Connecting Render backend to Gemini Cloud Workspace...")
        workspace_files = list(client.files.list())
        print(f"✅ Connection secure! Grounded to {len(workspace_files)} official CAPS curriculum documents.")
    except Exception as e:
        print(f"⚠️ Warning (Workspace asset sync failed): {e}")
        workspace_files = []

# --- DATACLASSES & SCHEMAS ---

class RegistrationPayload(BaseModel):
    whatsapp_number: str
    first_name: str
    surname: str
    age: int
    grade: int                     # 8 - 12
    current_term: int              # 1 - 4
    birth_date: str                # YYYY-MM-DD
    preferred_language: str        # e.g., "English", "isiZulu", "Afrikaans"
    current_term_marks: dict       # e.g., {"Mathematics": 45, "Physical Sciences": 78}

class DiagnosticAnswersPayload(BaseModel):
    whatsapp_number: str
    quiz_responses: list[int]      # Array of 8-10 integer scores (1 to 5) from the Likert quiz

class StudentPayload(BaseModel):
    whatsapp_number: str
    student_message: str
    image_url: str | None = None
    caps_subject_topic: str
    curriculum_theory: str | None = None


# --- HELPER UTILITIES: THE MERCURY CALCULATOR & ACADEMIC TIERING ---

def calculate_mercury_profile(birth_date_str: str) -> dict:
    """
    Mercury Learning Profile Agent (Astrological Cognitive Style Mapper)
    Calculates exact celestial position coordinates to determine the element.
    """
    try:
        # Parse birth date, defaulting to noon for accuracy safety bounds
        bdate = datetime.strptime(birth_date_str, "%Y-%m-%d")
        
        # Initialize ephem planetary calculation body
        m = ephem.Mercury()
        m.compute(bdate.strftime('%Y/%m/%d 12:00:00'))
        
        # Convert longitude coordinates to Zodiac arc degrees
        lon = ephem.Ecliptic(m).lon
        deg = float(lon) * 180 / float(ephem.pi)
        
        # Map 360-degree arc directly onto the 12 signs
        zodiac_signs = [
            ("Aries", "🔥 Fire"), ("Taurus", "🌍 Earth"), ("Gemini", "💬 Air"), ("Cancer", "🌊 Water"),
            ("Leo", "🔥 Fire"), ("Virgo", "🌍 Earth"), ("Libra", "💬 Air"), ("Scorpio", "🌊 Water"),
            ("Sagittarius", "🔥 Fire"), ("Capricorn", "🌍 Earth"), ("Aquarius", "💬 Air"), ("Pisces", "🌊 Water")
        ]
        
        sign_index = int(deg / 30) % 12
        sign_name, element = zodiac_signs[sign_index]
        
        # Map element types directly onto specific delivery actions
        delivery_maps = {
            "🔥 Fire": {"label": "Intuitive-Dynamic Learner", "strategy": "High-energy, big-picture framing, rapid actionable challenges, low hand-holding."},
            "🌍 Earth": {"label": "Structured-Systematic Learner", "strategy": "Concrete examples, step-by-step logic loops, hyper-organized pacing, practical relevance."},
            "💬 Air": {"label": "Conceptual-Collaborative Learner", "strategy": "Theoretical boundary-pushing, conversational Socratic dialog, pattern recognition mappings."},
            "🌊 Water": {"label": "Immersive-Empathetic Learner", "strategy": "High narrative focus, deep situational context, highly reassuring tone structure, intuitive flow."}
        }
        
        return {
            "mercury_sign": sign_name,
            "element": element,
            "cognitive_style_label": delivery_maps[element]["label"],
            "delivery_instructions": delivery_maps[element]["strategy"]
        }
    except Exception:
        # Sturdy, fail-safe backup parameters in case of input parsing faults
        return {"mercury_sign": "Unknown", "element": "🌍 Earth", "cognitive_style_label": "Structured-Systematic Learner", "delivery_instructions": "Concrete examples, step-by-step loops."}

def compile_academic_tiers(marks: dict) -> dict:
    """
    Academic Tier & Profile Compiler Agent
    Calculates Tier per subject based on explicit Department of Basic Education scale thresholds.
    """
    subject_tiers = {}
    for subject, mark in marks.items():
        if mark < 40:
            tier = "🔴 Tier 1 – Foundation Builder"
            focus = "Micro-steps, zero jargon, foundational rules, high reassurance."
        elif mark <= 75:
            tier = "🟡 Tier 2 – Mark Booster"
            focus = "Gap identification, precision training, conceptual boundary-pushing."
        else:
            tier = "🟢 Tier 3 – Peak Maintainer"
            focus = "Advanced variations, non-linear reasoning, competitive exam pressure."
        
        subject_tiers[subject] = {"mark": mark, "tier": tier, "focus_strategy": focus}
    return subject_tiers


# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {
        "status": "ONLINE",
        "message": "MyTutorZA Engine Running",
        "linked_caps_files": len(workspace_files)
    }

# --- PART 1: THE INTAKE & PSYCHOMETRIC QUIZ MANAGER ---

@app.post("/api/v1/onboarding/register")
async def register_student_intake(payload: RegistrationPayload):
    """
    Step A: Intake Collector, Mercury Profile computation, and Academic Tier calculations.
    Fires the 8-10 item psychometric profiling evaluation back to the student.
    """
    try:
        # 1. Run the Mercury Planetary Mapping System
        merc_profile = calculate_mercury_profile(payload.birth_date)
        
        # 2. Run the Academic Tier Compiler
        academic_profile = compile_academic_tiers(payload.current_term_marks)
        
        # 3. Build a permanent entry record in Supabase
        supabase.table("student_profiles").upsert({
            "whatsapp_number": payload.whatsapp_number,
            "first_name": payload.first_name,
            "surname": payload.surname,
            "age": payload.age,
            "grade": payload.grade,
            "current_term": payload.current_term,
            "birth_date": payload.birth_date,
            "preferred_language": payload.preferred_language,
            "mercury_sign": merc_profile["mercury_sign"],
            "delivery_element": merc_profile["element"],
            "cognitive_style_label": merc_profile["cognitive_style_label"],
            "delivery_instructions": merc_profile["delivery_instructions"],
            "academic_tiers": academic_profile,
            "onboarding_stage": "PENDING_PSYCHOMETRIC_QUIZ"
        }).execute()
        
        # 4. Generate the onboarding questionnaire via Gemini
        quiz_generation_prompt = f"""
        You are acting as the Educational Psychologist & Cognitive Profiler Agent.
        The student {payload.first_name} has registered. You have determined their Mercury Cognitive Element is {merc_profile['element']}.
        
        Generate exactly 8 simple, highly relatable Likert-scale questions (scored 1 to 5) to evaluate their standing across these 4 core psychological vectors:
        - Dimension A: Field Independence vs. Field Dependence (Does patterns lock out distractors or take global views?)
        - Dimension B: Conceptual Tempo (Impulsive vs. Reflective processing speeds)
        - Dimension C: Working Memory / Cognitive Load Capacity limits
        - Dimension D: Verbalizer vs. Visualizer preferences
        
        Format the output perfectly as a welcoming WhatsApp broadcast message. Tell them to respond back using a simple comma-separated string of numbers (e.g., 4,3,5,2,1,4,5,2).
        Make the context localized, warm, and distinctly friendly to a South African grade {payload.grade} learner.
        """
        
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=["Generate onboarding quiz setup."],
            config=types.GenerateContentConfig(
                system_instruction=quiz_generation_prompt,
                temperature=0.4
            )
        )
        
        return {
            "status": "success",
            "message": "Intake completed. Dispatching psychometric items.",
            "whatsapp_payload": response.text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration Pipeline Error: {str(e)}")


@app.post("/api/v1/onboarding/submit-quiz")
async def evaluate_psychometric_quiz(payload: DiagnosticAnswersPayload):
    """
    Step B: Processes quiz inputs, outputs the dynamic math vector, and seals the Master Student Profile.
    """
    try:
        # Read the existing profile from the database
        profile_res = supabase.table("student_profiles").select("*").eq("whatsapp_number", payload.whatsapp_number).execute()
        if not profile_res.data:
            raise HTTPException(status_code=404, detail="Student record not found. Run registration first.")
            
        student_data = profile_res.data[0]
        
        # System instructions to evaluate and score the Likert matrix array
        profiler_prompt = f"""
        You are the Educational Psychologist scoring agent. Convert these raw quiz responses: {payload.quiz_responses}
        Into a clean, normalized psychological JSON scoring object spanning these exact four criteria strings:
        - analytical (Field Independence level: 0 to 100)
        - fast_processor (Conceptual Tempo / Speed preference: 0 to 100)
        - global (Field Dependence integration scale: 0 to 100)
        - visualizer (Visual preference vs verbal preference scale: 0 to 100)
        
        You MUST return ONLY a valid JSON object matching this structure:
        {{
           "analytical": 80,
           "fast_processor": 30,
           "global": 65,
           "visualizer": 90
        }}
        """
        
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=[f"Scores: {payload.quiz_responses}"],
            config=types.GenerateContentConfig(
                system_instruction=profiler_prompt,
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        
        import json
        cognitive_vector = json.loads(response.text)
        
        # Save finalized vector variables to close onboarding loop
        supabase.table("student_profiles").update({
            "cognitive_vector": cognitive_vector,
            "onboarding_stage": "COMPLETED",
            "finalized_at": datetime.utcnow().isoformat()
        }).eq("whatsapp_number", payload.whatsapp_number).execute()
        
        return {
            "status": "success",
            "message": "Master Student Profile successfully locked and compiled.",
            "cognitive_vector": cognitive_vector
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Psychometric Compilation Error: {str(e)}")


# --- PART 2: THE MULTI-AGENT CLASSROOM EXECUTION NODE (AGENTS 6-13) ---

# ... [Keep your imports, helper functions, and database configs exactly as they are at the top] ...

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {
        "status": "ONLINE",
        "message": "MyTutorZA Engine Running",
        "linked_caps_files": len(workspace_files)
    }

# --- PART 1: THE INTAKE & PSYCHOMETRIC QUIZ MANAGER ---

@app.post("/api/v1/onboarding/register")
async def register_student_intake(payload: RegistrationPayload):
    """
    Step A: Process initial info, compute Mercury element, and generate 
    highly structured interactive components for the WhatsApp Gateway.
    """
    try:
        # 1. Run the Mercury Planetary Mapping System
        merc_profile = calculate_mercury_profile(payload.birth_date)
        
        # 2. Run the Academic Tier Compiler
        academic_profile = compile_academic_tiers(payload.current_term_marks)
        
        # 3. Build/Update permanent entry record in Supabase
        supabase.table("student_profiles").upsert({
            "whatsapp_number": payload.whatsapp_number,
            "first_name": payload.first_name,
            "surname": payload.surname,
            "age": payload.age,
            "grade": payload.grade,
            "current_term": payload.current_term,
            "birth_date": payload.birth_date,
            "preferred_language": payload.preferred_language,
            "mercury_sign": merc_profile["mercury_sign"],
            "delivery_element": merc_profile["element"],
            "cognitive_style_label": merc_profile["cognitive_style_label"],
            "delivery_instructions": merc_profile["delivery_instructions"],
            "academic_tiers": academic_profile,
            "onboarding_stage": "PENDING_PSYCHOMETRIC_QUIZ"
        }).execute()
        
        # 4. Generate the personalized welcome text script
        welcome_prompt = f"""
        You are acting as the warm, supportive Educational Psychologist Agent for MyTeacherZA.
        The student {payload.first_name} has registered. Their Mercury Cognitive Element is {merc_profile['element']}.
        
        Write a short, engaging welcome message introducing them to their personalized learning journey. 
        Acknowledge their grade ({payload.grade}) and preferred language ({payload.preferred_language}) naturally.
        End by letting them know they are about to complete a quick 3-minute interactive learning style discovery quiz.
        Keep it to 2-3 short sentences max, perfect for a mobile screen.
        """
        
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=["Generate brief onboarding intro."],
            config=types.GenerateContentConfig(
                system_instruction=welcome_prompt,
                temperature=0.4
            )
        )
        
        # 5. Return structured interactive data to the WhatsApp automation flow
        return {
            "status": "success",
            "message": "Intake records initialized successfully.",
            "whatsapp_delivery_payload": {
                "text_message": response.text,
                
                # Structural blueprints for your WhatsApp template/API manager:
                "interactive_components": {
                    "grade_selector": {
                        "type": "list_menu",
                        "title": "Select Your Grade",
                        "options": ["Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
                    },
                    "birthdate_prompt": {
                        "type": "text_reply_capture",
                        "placeholder": "DD/MM/YYYY"
                    },
                    "quiz_tabs": {
                        "type": "quick_reply_buttons",
                        "instruction": "Tap the tab that best describes you for each scenario:",
                        "buttons": [
                            {"id": "5", "title": "🤩 Strongly Agree"},
                            {"id": "4", "title": "🙂 Agree"},
                            {"id": "3", "title": "😐 Neutral"},
                            {"id": "2", "title": "🙁 Disagree"},
                            {"id": "1", "title": "❌ Strongly Disagree"}
                        ]
                    }
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration Pipeline Error: {str(e)}")

@app.post("/api/v1/onboarding/submit-quiz")
async def evaluate_psychometric_quiz(payload: DiagnosticAnswersPayload):
# ... [Keep the rest of the file exactly as it was, including the classroom engine below] ...
