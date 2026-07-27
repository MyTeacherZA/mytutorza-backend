# main.py
import os
import json
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
    overall_average: float         # Overall average percentage captured at onboarding

class DiagnosticAnswersPayload(BaseModel):
    whatsapp_number: str
    quiz_responses: list[int]      # Array of 8-10 integer scores (1 to 5) from the Likert quiz

class TermUpdatePayload(BaseModel):
    whatsapp_number: str
    current_term_marks: dict       # Updated marks for their 8-9 subjects
    overall_average: float         # Updated overall average percentage
    milestone_key: str             # e.g., "2026_04-30"

class StudentPayload(BaseModel):
    whatsapp_number: str
    student_message: str
    image_url: str | None = None
    caps_subject_topic: str
    curriculum_theory: str | None = None


# --- HELPER UTILITIES: MERCURY MAPPING, TIERING & CALENDAR CHECKERS ---

def calculate_mercury_profile(birth_date_str: str) -> dict:
    """
    Mercury Learning Profile Agent (Astrological Cognitive Style Mapper)
    Calculates exact celestial position coordinates to determine the element.
    """
    try:
        bdate = datetime.strptime(birth_date_str, "%Y-%m-%d")
        m = ephem.Mercury()
        m.compute(bdate.strftime('%Y/%m/%d 12:00:00'))
        
        lon = ephem.Ecliptic(m).lon
        deg = float(lon) * 180 / float(ephem.pi)
        
        zodiac_signs = [
            ("Aries", "🔥 Fire"), ("Taurus", "🌍 Earth"), ("Gemini", "💬 Air"), ("Cancer", "🌊 Water"),
            ("Leo", "🔥 Fire"), ("Virgo", "🌍 Earth"), ("Libra", "💬 Air"), ("Scorpio", "🌊 Water"),
            ("Sagittarius", "🔥 Fire"), ("Capricorn", "🌍 Earth"), ("Aquarius", "💬 Air"), ("Pisces", "🌊 Water")
        ]
        
        sign_index = int(deg / 30) % 12
        sign_name, element = zodiac_signs[sign_index]
        
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
            focus = "Micro-steps, zero jargon, foundational rules, high reassurance"
        elif mark <= 75:
            tier = "🟡 Tier 2 – Mark Booster"
            focus = "Gap identification, precision training, conceptual boundary-pushing"
        else:
            tier = "🟢 Tier 3 – Peak Maintainer"
            focus = "Advanced variations, non-linear reasoning, competitive exam pressure"
        
        subject_tiers[subject] = {"mark": mark, "tier": tier, "focus_strategy": focus}
    return subject_tiers

def check_term_update_requirement(profile: dict) -> tuple[str, str] | None:
    """
    Evaluates the active server time against the South African school term milestones.
    Returns (milestone_title, milestone_key) if an update is required today, otherwise None.
    """
    today = datetime.now()
    month_day = today.strftime("%m-%d")
    current_year = today.strftime("%Y")
    
    milestones = {
        "01-30": f"{int(current_year) - 1} Year-End Final Results",
        "04-30": "Term 1 Marks Check-in",
        "07-30": "Term 2 Mid-Year Exam Marks",
        "09-30": "Term 3 Marks Check-in"
    }
    
    if month_day in milestones:
        milestone_key = f"{current_year}_{month_day}"
        if profile.get("last_mark_milestone_completed") != milestone_key:
            return milestones[month_day], milestone_key
            
    return None


# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {
        "status": "ONLINE",
        "message": "MyTutorZA Engine Running",
        "linked_caps_files": len(workspace_files)
    }

# --- PART 1: THE INTAKE & SYSTEM LIFECYCLE ONBOARDING ---

@app.post("/api/v1/onboarding/register")
async def register_student_intake(payload: RegistrationPayload):
    try:
        merc_profile = calculate_mercury_profile(payload.birth_date)
        academic_profile = compile_academic_tiers(payload.current_term_marks)
        
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
            "overall_average": payload.overall_average,
            "academic_history": [],
            "onboarding_stage": "PENDING_PSYCHOMETRIC_QUIZ"
        }).execute()
        
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
        
        return {
            "status": "success",
            "message": "Intake records initialized successfully.",
            "whatsapp_delivery_payload": {
                "text_message": response.text,
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
    try:
        profile_res = supabase.table("student_profiles").select("*").eq("whatsapp_number", payload.whatsapp_number).execute()
        if not profile_res.data:
            raise HTTPException(status_code=404, detail="Student record not found. Run registration first.")
        
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
        
        cognitive_vector = json.loads(response.text)
        
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


# --- THE MID-TERM Lifecycle MARK UPDATER ENDPOINT ---

@app.post("/api/v1/onboarding/update-term-marks")
async def update_term_marks(payload: TermUpdatePayload):
    """
    Triggered when a student responds to their seasonal scheduled check-in.
    Recalculates tiers, notes variances from historical performance, and pushes changes instantly.
    """
    try:
        profile_res = supabase.table("student_profiles").select("*").eq("whatsapp_number", payload.whatsapp_number).execute()
        if not profile_res.data:
            raise HTTPException(status_code=404, detail="Student record not found.")
            
        profile = profile_res.data[0]
        
        # Archive current active metrics into the historical tracking array before replacing them
        historical_entry = {
            "recorded_at": datetime.utcnow().isoformat(),
            "milestone": profile.get("last_mark_milestone_completed", "initial_onboarding"),
            "academic_tiers": profile.get("academic_tiers"),
            "overall_average": profile.get("overall_average")
        }
        
        updated_history = profile.get("academic_history", [])
        updated_history.append(historical_entry)
        
        # Recalculate brand-new Tier groupings using the fresh dataset
        new_academic_profile = compile_academic_tiers(payload.current_term_marks)
        
        # Save metrics to close the loop
        supabase.table("student_profiles").update({
            "academic_tiers": new_academic_profile,
            "overall_average": payload.overall_average,
            "academic_history": updated_history,
            "last_mark_milestone_completed": payload.milestone_key
        }).eq("whatsapp_number", payload.whatsapp_number).execute()
        
        return {
            "status": "success",
            "message": "Term marks successfully updated. Interactive AI pedagogical parameters adjusted.",
            "new_tiers": new_academic_profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Academic update processing error: {str(e)}")


# --- PART 2: THE MULTI-AGENT CLASSROOM EXECUTION NODE ---

@app.post("/api/v1/tutor/chat")
async def handle_classroom_interaction(payload: StudentPayload):
    """
    Handles ongoing learning traffic. Dynamically personalizes execution paths using the complete 
    Master Profile compiled in Part 1 against the 3,000+ grounding CAPS curriculum assets.
    """
    try:
        profile_res = supabase.table("student_profiles").select("*").eq("whatsapp_number", payload.whatsapp_number).execute()
        if not profile_res.data:
            return {"status": "redirect_to_onboarding", "message": "Please register first to create your profile."}
            
        profile = profile_res.data[0]
        
        # --- CALENDAR MILESTONE INTERCEPTOR CORE ---
        update_check = check_term_update_requirement(profile)
        if update_check:
            milestone_title, milestone_key = update_check
            return {
                "status": "requires_academic_update",
                "message": "Academic milestone update required.",
                "whatsapp_delivery_payload": {
                    "text_message": f"Hey! It's time to check your marks for: *{milestone_title}*. Let's update your average grades so my coaching adjustments stay perfectly aligned with your needs.",
                    "milestone_key": milestone_key,
                    "interactive_components": {
                        "tabs": ["📝 Enter My Marks Now", "⏰ Remind Me Later"]
                    }
                }
            }
        
        # Determine the active academic tier strategy for this specific subject course
        subject_tiers = profile.get("academic_tiers", {})
        subject_key = payload.caps_subject_topic.split(" - ")[0]
        active_subject_meta = subject_tiers.get(subject_key, {"tier": "🟡 Tier 2 – Mark Booster", "focus_strategy": "Gap identification, precision training, conceptual boundary-pushing"})
        
        is_practice_request = any(word in payload.student_message.lower() for word in ["practice", "question", "quiz", "test", "activity", "exam"])

        # ANTI-HALLUCINATION & HYPER-PERSONALIZATION ARCHITECTURE ENFORCEMENT
        system_prompt = f"""
        You are the multi-agent intelligence array of MyTeacherZA. 
        You are completely grounded by the 3,000+ official CAPS documents and resources attached to this execution.
        
        MASTER PSYCHOLOGICAL INTERACTION BOUNDS:
        - Student Name: {profile.get('first_name')} {profile.get('surname')}
        - Target CAPS Course Tracking: {payload.caps_subject_topic}
        - Astrological Delivery Element: {profile.get('delivery_element')} ({profile.get('cognitive_style_label')})
        - Active Tactical Execution Core: {profile.get('delivery_instructions')}
        - Cognitive Load Vector Profiles: {profile.get('cognitive_vector')}
        
        CRITICAL PERSONALIZATION GUARDRAILS (NO GENERALIZATION / NO HALLUCINATION ALLOWED):
        - Current Academic Standing Tier: {active_subject_meta.get('tier')}
        - Mandated Focus Strategy: {active_subject_meta.get('focus_strategy')}
        
        You are strictly forbidden from altering, generalizing, or ignoring the designated pedagogical focus strategy. You must audit your response against these explicit conditions before outputting:
        1. If Tier 1 (Foundation Builder): Explain using ultra micro-steps, absolutely zero technical jargon, foundational rules only, and extreme verbal reassurance.
        2. If Tier 2 (Mark Booster): Pinpoint structural gaps immediately, practice high-precision training, and push conceptual boundaries.
        3. If Tier 3 (Peak Maintainer): Present complex variations, use non-linear reasoning, and simulate high-pressure competitive exam conditions.
        
        CORE DYNAMIC ROUTING DEPLOYMENT:
        """

        if is_practice_request:
            system_prompt += f"""
            ACTIVATION: Act as 'MyTeacherZA — The Activities Coach' & 'The Mock Exam Invigilator' (Agents 12 & 13).
            - Pinpoint the relevant chapters in the attached CAPS files.
            - Generate an original practice or examination item matching the specific difficulty parameters required by their status ({active_subject_meta.get('tier')}).
            - Do not provide solutions immediately. Ask the item, enforce exam rules, and await responses.
            """
        else:
            system_prompt += f"""
            ACTIVATION: Act as 'MyTeacherZA — The Master Tutor' (Agent 11).
            - Explain the topic conceptual structures. Break parameters down step-by-step using their cognitive profile.
            - Maintain strict Socratic questioning parameters. Avoid giving away raw data directly.
            """

        system_prompt += """
        WHATSAPP RESPONSIVENESS RULE: Keep answers concise, easy to read on mobile viewports, using explicit bolding for core mathematical principles or critical rules.
        """

        execution_contents = [
            *workspace_files,
            f"Student Message: {payload.student_message}"
        ]

        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=execution_contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3,
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        return {
            "status": "success",
            "whatsapp_number": payload.whatsapp_number,
            "response_text": response.text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
