# main.py
import os
import json
import random
import ephem  
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from supabase import create_client, Client
from google import genai
from google.genai import types

# 1. Initialize FastAPI Application Configuration
app = FastAPI(
    title="MyTutorZA Comprehensive Core Backend Engine", 
    version="2.0.0"
)

# 2. Secure Cloud Environment Variables Configuration
SUPABASE_URL = os.getenv("supabase_url")
SUPABASE_KEY = os.getenv("supabase_key")
GEMINI_API_KEY = os.getenv("gemini_api_key")

TWILIO_ACCOUNT_SID = os.getenv("twilio_account_sid")
TWILIO_AUTH_TOKEN = os.getenv("twilio_auth_token")
TWILIO_NUMBER = os.getenv("twilio_number")

PAYFAST_MERCHANT_ID = os.getenv("payfast_merchant_id")
PAYFAST_MERCHANT_KEY = os.getenv("payfast_merchant_key")
PAYFAST_RETURN_URL = "https://mytutorza.co.za/dashboard" 

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("CRITICAL: Missing required Supabase credentials.")

# 3. Initialize Production Supabase Infrastructure
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 4. Initialize Core GenAI Multi-Agent Language Engine
client = genai.Client(api_key=GEMINI_API_KEY)
workspace_files = []

@app.on_event("startup")
def verify_and_load_caps_workspace():
    global workspace_files
    try:
        workspace_files = list(client.files.list())
        print(f"🚀 SYSTEM SECURE: Grounded dynamically to {len(workspace_files)} official CAPS curriculum resources.")
    except Exception as e:
        print(f"⚠️ WORKSPACE DETACHED: Check your Gemini API workspace setup properties. Error: {e}")
        workspace_files = []


# --- DATACLASSES & SCHEMAS MATCHING BUSINESS SPECIFICATIONS ---

class WhatsAppOnboardingIntakePayload(BaseModel):
    whatsapp_number: str
    full_name: str
    surname: str
    age: int
    grade: int = Field(..., ge=8, le=12)  # Enforces strict Grades 8-12 bounds
    current_term: int = Field(..., ge=1, le=4)
    preferred_language: str
    birth_year: str
    birth_month: str
    birth_day: str
    psychometric_yes_no_responses: list[str]  # Exactly 8 to 10 strings matching "Yes" or "No"

class WebPortalAccountCreationPayload(BaseModel):
    whatsapp_number: str
    username: str
    password: str
    remember_me: bool = False

class WebPortal2ColumnMarksPayload(BaseModel):
    whatsapp_number: str
    current_term_subjects: list[str]     # Left Column Input fields (8 to 9 subjects)
    current_term_percentages: list[float] # Right Column Adjacent Input fields matching indexes
    overall_average: float
    current_term: int = Field(..., ge=1, le=4)
    device_fingerprint: str
    force_migration: bool = False

class CredentialRecoveryRequest(BaseModel):
    whatsapp_number: str

class VerificationResetPayload(BaseModel):
    whatsapp_number: str
    otp_code: str
    new_password: str

class PaymentVerificationTriggerPayload(BaseModel):
    whatsapp_number: str

class PayFastGateHandshakePayload(BaseModel):
    whatsapp_number: str
    otp_entered: str
    payment_method: str  # '1voucher', 'eft', or 'card'

class ScheduledMilestonePayload(BaseModel):
    whatsapp_number: str
    current_term_subjects: list[str]
    current_term_percentages: list[float]
    overall_average: float
    milestone_key: str

class InteractiveTutoringPayload(BaseModel):
    whatsapp_number: str
    student_message: str
    caps_subject_topic: str
    image_url: str | None = None


# --- CALCULATION UTILITIES FOR PERSISTENCE OVERRIDES ---

def calculate_astrological_mercury_profile(year: str, month: str, day: str) -> dict:
    try:
        month_normalization = {
            "january": "01", "february": "02", "march": "03", "april": "04", "may": "05", "june": "06",
            "july": "07", "august": "08", "september": "09", "october": "10", "november": "11", "december": "12"
        }
        clean_m = month_normalization.get(month.lower().strip(), month.zfill(2))
        clean_d = day.strip().zfill(2)
        birth_date_iso = f"{year.strip()}-{clean_m}-{clean_d}"
        
        bdate = datetime.strptime(birth_date_iso, "%Y-%m-%d")
        m = ephem.Mercury()
        m.compute(bdate.strftime('%Y/%m/%d 12:00:00'))
        
        deg = float(ephem.Ecliptic(m).lon) * 180 / float(ephem.pi)
        zodiac_signs = [
            ("Aries", "🔥 Fire"), ("Taurus", "🌍 Earth"), ("Gemini", "💬 Air"), ("Cancer", "🎨 Water"),
            ("Leo", "🔥 Fire"), ("Virgo", "🌍 Earth"), ("Libra", "💬 Air"), ("Scorpio", "🎨 Water"),
            ("Sagittarius", "🔥 Fire"), ("Capricorn", "🌍 Earth"), ("Aquarius", "💬 Air"), ("Pisces", "🎨 Water")
        ]
        sign_index = int(deg / 30) % 12
        sign_name, element = zodiac_signs[sign_index]
        
        elemental_delivery_map = {
            "🔥 Fire": {"label": "Intuitive-Dynamic Learner", "strategy": "High-energy, interactive framing, challenge-driven loops."},
            "🌍 Earth": {"label": "Structured-Systematic Learner", "strategy": "Step-by-step sequential logic, explicit real-world context."},
            "💬 Air": {"label": "Conceptual-Collaborative Learner", "strategy": "Socratic dialogue parameters, thought-provoking theories."},
            "🎨 Water": {"label": "Immersive-Empathetic Learner", "strategy": "High narrative focus, deep contextual framing, high reassurance."}
        }
        
        return {
            "birth_date": birth_date_iso,
            "mercury_sign": sign_name,
            "delivery_element": element,
            "cognitive_style_label": elemental_delivery_map[element]["label"],
            "delivery_instructions": elemental_delivery_map[element]["strategy"]
        }
    except Exception:
        return {
            "birth_date": f"{year}-{month}-{day}",
            "mercury_sign": "Unknown",
            "delivery_element": "🌍 Earth",
            "cognitive_style_label": "Structured Learner",
            "delivery_instructions": "Default to clean sequential micro-steps."
        }

def analyze_cognitive_profile_dimensions(responses: list[str]) -> dict:
    try:
        analysis_prompt = (
            "Analyze these raw Yes/No user replies to a custom psychometric test measuring:\n"
            "Dimension A: Field Independence vs. Dependence\n"
            "Dimension B: Conceptual Tempo (Impulsive vs Reflective)\n"
            "Dimension C: Working Memory/Cognitive Load\n"
            "Dimension D: Verbalizer vs Visualizer.\n"
            "Output absolute values from 0-100 inside strict JSON layout with exactly these keys: "
            "'analytical', 'fast_processor', 'global', 'visualizer'."
        )
        response = client.models.generate_content(
            model='gemini-flash-latest', 
            contents=[f"User Psychometric Responses: {responses}"],
            config=types.GenerateContentConfig(
                system_instruction=analysis_prompt, 
                temperature=0.1, 
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception:
        return {"analytical": 50, "fast_processor": 50, "global": 50, "visualizer": 50}

def process_strict_academic_tiers(subjects: list[str], percentages: list[float]) -> dict:
    compiled_tiers = {}
    for sub, pct in zip(subjects, percentages):
        clean_sub = sub.strip()
        if pct < 40.0:
            tier = "🔴 Tier 1 – Foundation Builder"
            focus = "Micro-steps execution, completely zero academic jargon, foundational core rules, extreme verbal reassurance."
        elif pct <= 75.0:
            tier = "🟡 Tier 2 – Mark Booster"
            focus = "Structural gap identification, high-precision training, concept boundary-pushing exercises."
        else:
            tier = "🟢 Tier 3 – Peak Maintainer"
            focus = "Advanced complex variations, non-linear reasoning challenges, extreme high-pressure competitive exam simulation."
            
        compiled_tiers[clean_sub] = {
            "mark": pct,
            "tier": tier,
            "focus_strategy": focus
        }
    return compiled_tiers

def inspect_calendar_milestone_gates(profile: dict) -> tuple[str, str] | None:
    today = datetime.now()
    month_day = today.strftime("%m-%d")
    current_year = today.strftime("%Y")
    
    milestones = {
        "04-30": "Term 1 Marks Update Required",
        "07-30": "Term 2 Marks Update Required",
        "09-30": "Term 3 Marks Update Required",
        "01-30": "Prior Year-End Final Marks Update Required"
    }
    
    if month_day in milestones:
        milestone_key = f"{current_year}_{month_day}"
        if profile.get("last_mark_milestone_completed") != milestone_key:
            return milestones[month_day], milestone_key
    return None


# =====================================================================
# PART 1: CHAT ONBOARDING INTAKE & PORTAL IDENTITY SETUP
# =====================================================================

@app.post("/api/v1/onboarding/whatsapp-profile-intake")
async def collect_whatsapp_profile_intake(payload: WhatsAppOnboardingIntakePayload):
    try:
        astro_meta = calculate_astrological_mercury_profile(payload.birth_year, payload.birth_month, payload.birth_day)
        cognitive_vector = analyze_cognitive_profile_dimensions(payload.psychometric_yes_no_responses)
        
        supabase.table("student_profiles").upsert({
            "whatsapp_number": payload.whatsapp_number,
            "full_name": payload.full_name,
            "surname": payload.surname,
            "age": payload.age,
            "grade": payload.grade,
            "current_term": payload.current_term,
            "preferred_language": payload.preferred_language,
            "birth_date": astro_meta["birth_date"],
            "mercury_sign": astro_meta["mercury_sign"],
            "delivery_element": astro_meta["delivery_element"],
            "cognitive_style_label": astro_meta["cognitive_style_label"],
            "delivery_instructions": astro_meta["delivery_instructions"],
            "cognitive_vector": cognitive_vector,
            "payment_verified": False,
            "onboarding_stage": "PENDING_PORTAL_CREDENTIALS"
        }).execute()
        
        portal_redirect_url = f"https://mytutorza.co.za/portal-setup?whatsapp={payload.whatsapp_number}"
        return {
            "status": "success",
            "message": "Conversational onboarding saved. Directing user immediately to web portal for identity lock.",
            "redirect_target": portal_redirect_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/auth/register-portal-account")
async def register_portal_account(payload: WebPortalAccountCreationPayload):
    try:
        username_check = supabase.table("student_profiles").select("*").eq("username", payload.username).execute()
        if username_check.data:
            raise HTTPException(status_code=400, detail="This username is already taken. Please try a different variant.")
            
        supabase.table("student_profiles").update({
            "username": payload.username,
            "portal_password": payload.password, 
            "remember_me_enabled": payload.remember_me,
            "onboarding_stage": "PENDING_WEB_MARKS"
        }).eq("whatsapp_number", payload.whatsapp_number).execute()
        
        return {"status": "success", "message": "Portal identity profile created successfully."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/onboarding/portal-marks-submit")
async def process_portal_marks_submit(payload: WebPortal2ColumnMarksPayload):
    try:
        if len(payload.current_term_subjects) != len(payload.current_term_percentages):
            raise HTTPException(status_code=400, detail="Mismatched input lengths between subjects and percentages.")
            
        profile_res = supabase.table("student_profiles").select("*").eq("whatsapp_number", payload.whatsapp_number).execute()
        if not profile_res.data:
            raise HTTPException(status_code=444, detail="No matching profile record found for this number.")
            
        profile = profile_res.data[0]
        active_session = profile.get("active_device_session")
        barred_until_iso = profile.get("barred_device_until")
        
        # 1. 24-Hour Device Suspension Evaluation
        if barred_until_iso:
            barred_until_time = datetime.fromisoformat(barred_until_iso)
            if datetime.utcnow() < barred_until_time and profile.get("last_barred_device") == payload.device_fingerprint:
                time_remaining = barred_until_time - datetime.utcnow()
                hours_remaining = round(time_remaining.total_seconds() / 3600, 1)
                raise HTTPException(
                    status_code=403,
                    detail=f"Access Denied Loop: This browser configuration is temporarily blacklisted to protect against account sharing. Try again in {hours_remaining} hours."
                )
                
        # 2. Footprint Resolution Handshake
        if active_session and active_session != payload.device_fingerprint:
            if not payload.force_migration:
                return {
                    "status": "device_footprint_conflict",
                    "message": "Security Alert: This profile has an active open session on another device.",
                    "prompt_choice": "Would you like to invalidate your previous session and migrate your primary workspace to this device? Warning: The previous device will be locked out for 24 hours."
                }
            else:
                # Force migration confirmed: Lock out old footprint for exactly 24 hours
                lockout_expiration = (datetime.utcnow() + timedelta(days=1)).isoformat()
                supabase.table("student_profiles").update({
                    "last_barred_device": active_session,
                    "barred_device_until": lockout_expiration
                }).eq("whatsapp_number", payload.whatsapp_number).execute()

        # 3. Save Marks Independent of Paywall
        academic_tiers = process_strict_academic_tiers(payload.current_term_subjects, payload.current_term_percentages)
        
        supabase.table("student_profiles").update({
            "academic_tiers": academic_tiers,
            "overall_average": payload.overall_average,
            "current_term": payload.current_term,
            "active_device_session": payload.device_fingerprint,
            "onboarding_stage": "COMPLETED"
        }).eq("whatsapp_number", payload.whatsapp_number).execute()
        
        return {"status": "success", "message": "Two-column academic profile successfully updated and active device bound."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- SECURITY CORE: CREDENTIAL RECOVERY SYSTEM ---

@app.post("/api/v1/auth/forgot-credentials")
async def initiate_forgot_credentials_recovery(payload: CredentialRecoveryRequest):
    try:
        profile_res = supabase.table("student_profiles").select("*").eq("whatsapp_number", payload.whatsapp_number).execute()
        if not profile_res.data:
            raise HTTPException(status_code=404, detail="No student record matches this phone number.")
            
        recovery_otp = str(random.randint(100000, 999999))
        
        supabase.table("student_profiles").update({
            "recovery_otp_token": recovery_otp,
            "recovery_otp_expiry": (datetime.utcnow() + timedelta(minutes=15)).isoformat()
        }).eq("whatsapp_number", payload.whatsapp_number).execute()
        
        print(f"📟 [Twilio API] Recovery token {recovery_otp} sent to WhatsApp endpoint: {payload.whatsapp_number}")
        return {"status": "success", "message": "Account validation code broadcasted. Verify via WhatsApp to reset credentials."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/auth/reset-recovered-credentials")
async def reset_recovered_credentials(payload: VerificationResetPayload):
    try:
        profile_res = supabase.table("student_profiles").select("*").eq("whatsapp_number", payload.whatsapp_number).execute()
        if not profile_res.data:
            raise HTTPException(status_code=404, detail="Identity record mapping missing.")
            
        profile = profile_res.data[0]
        
        if profile.get("recovery_otp_token") != payload.otp_code:
            raise HTTPException(status_code=400, detail="Invalid account authorization verification string.")
            
        supabase.table("student_profiles").update({
            "portal_password": payload.new_password,
            "recovery_otp_token": None
        }).eq("whatsapp_number", payload.whatsapp_number).execute()
        
        return {
            "status": "success",
            "message": "Credentials updated successfully.",
            "username_reminder": profile.get("username")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# PART 2: BILLING GATEWAY WITH PRE-TRANSACTION OTP CHALLENGE
# =====================================================================

@app.post("/api/v1/billing/trigger-pre-payment-otp")
async def trigger_pre_payment_otp(payload: PaymentVerificationTriggerPayload):
    try:
        billing_otp = str(random.randint(100000, 999999))
        
        supabase.table("student_profiles").update({
            "active_billing_otp": billing_otp,
            "billing_otp_timestamp": datetime.utcnow().isoformat()
        }).eq("whatsapp_number", payload.whatsapp_number).execute()
        
        print(f"📟 [Twilio Gateway] Pre-payment challenge code {billing_otp} dispatched to: {payload.whatsapp_number}")
        return {"status": "success", "message": "Security confirmation token sent via WhatsApp. Verify to route to secure payment form."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/billing/verify-otp-and-bind-payfast")
async def verify_otp_and_bind_payfast(payload: PayFastGateHandshakePayload):
    try:
        profile_res = supabase.table("student_profiles").select("*").eq("whatsapp_number", payload.whatsapp_number).execute()
        if not profile_res.data:
            raise HTTPException(status_code=404, detail="Subscriber profile row missing.")
            
        profile = profile_res.data[0]
        if profile.get("active_billing_otp") != payload.otp_entered:
            raise HTTPException(status_code=400, detail="Invalid security verification token string. Payment route frozen.")
            
        payfast_endpoint = "https://sandbox.payfast.co.za/eng/process"
        redirect_query = (
            f"?merchant_id={PAYFAST_MERCHANT_ID}"
            f"&merchant_key={PAYFAST_MERCHANT_KEY}"
            f"&return_url={PAYFAST_RETURN_URL}?whatsapp={payload.whatsapp_number}"
            f"&item_name=MyTutorZA+Premium+Monthly+Access+Sub"
            f"&amount=20.00"
            f"&payment_method={payload.payment_method}"
        )
        
        return {
            "status": "identity_verified",
            "payfast_redirect_url": f"{payfast_endpoint}{redirect_query}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# PART 3: LIFECYCLE MANAGEMENT: ACADEMIC HISTORY ARRAYS
# =====================================================================

@app.post("/api/v1/onboarding/process-scheduled-milestone")
async def process_scheduled_milestone(payload: ScheduledMilestonePayload):
    try:
        profile_res = supabase.table("student_profiles").select("*").eq("whatsapp_number", payload.whatsapp_number).execute()
        if not profile_res.data:
            raise HTTPException(status_code=404, detail="Student profile not found.")
            
        profile = profile_res.data[0]
        
        history_entry = {
            "archive_timestamp": datetime.utcnow().isoformat(),
            "milestone_marker": profile.get("last_mark_milestone_completed", "initial_onboarding"),
            "academic_tiers": profile.get("academic_tiers"),
            "overall_average": profile.get("overall_average")
        }
        
        historical_archive = profile.get("academic_history", [])
        historical_archive.append(history_entry)
        
        fresh_tiers = process_strict_academic_tiers(payload.current_term_subjects, payload.current_term_percentages)
        
        supabase.table("student_profiles").update({
            "academic_tiers": fresh_tiers,
            "overall_average": payload.overall_average,
            "academic_history": historical_archive,
            "last_mark_milestone_completed": payload.milestone_key
        }).eq("whatsapp_number", payload.whatsapp_number).execute()
        
        return {"status": "success", "message": "Academic history captured. Current term tracking recalculated.", "new_tiers": fresh_tiers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# PART 4: HARD-GATED PERSONALIZATION AI TUTORING CORE ENGINE
# =====================================================================

@app.post("/api/v1/tutor/chat-session")
async def process_classroom_interaction(payload: InteractiveTutoringPayload):
    """
    Coordinates multi-agent framework across Agent 11, 12, and 13.
    Hard-gated by billing status validations and terminal calendar checkpoint hooks.
    """
    try:
        profile_res = supabase.table("student_profiles").select("*").eq("whatsapp_number", payload.whatsapp_number).execute()
        if not profile_res.data:
            return {
                "status": "unregistered",
                "response_text": "Greetings! Please finish registration and complete your academic onboarding before entering the workspace rooms."
            }
            
        profile = profile_res.data[0]
        
        # 1. SUBSCRIPTION HARD-PAYWALL ACCESS GATE
        if not profile.get("payment_verified", False):
            return {
                "status": "subscription_required",
                "response_text": "Sorry, I can't respond. Please pay your R20 subscription to unlock your personal AI classroom tutor dashboard engine."
            }
            
        # 2. SCHEDULED CALENDAR MILESTONE INTERCEPTOR
        milestone_alert = inspect_calendar_milestone_gates(profile)
        if milestone_alert:
            alert_label, milestone_code = milestone_alert
            return {
                "status": "requires_academic_update",
                "response_text": f"Attention: It's time to sync your results for *{alert_label}*. Head over to your web dashboard profile to update your 2-column marks layout link so our coaching stays perfectly aligned: {PAYFAST_RETURN_URL}?whatsapp={payload.whatsapp_number}&milestone={milestone_code}"
            }
            
        # 3. EXTRACT RELEVANT ACADEMIC TIER PARAMETERS
        student_tiers = profile.get("academic_tiers", {})
        subject_search_key = payload.caps_subject_topic.split(" - ")[0].strip()
        
        matched_tier_meta = student_tiers.get(
            subject_search_key, 
            {"tier": "🟡 Tier 2 – Mark Booster", "focus_strategy": "Structural gap identification, high-precision training, concept boundary-pushing exercises."}
        )
        
        # 4. DISPATCH USER REPLIES TO DYNAMIC INTENT INTELLIGENCE MULTI-AGENTS
        msg_normalized = payload.student_message.lower()
        is_practice_intent = any(w in msg_normalized for w in ["practice", "homework", "exercise", "activity", "task"])
        is_exam_intent = any(w in msg_normalized for w in ["exam", "test", "quiz", "mock", "assess"])
        
        base_system_prompt = f"""
        You are the multi-agent cognitive array powering MyTeacherZA, completely grounded by the official CAPS files provided.
        
        MASTER CONTEXT LOCK:
        - Student Identifier: {profile.get('full_name')} {profile.get('surname')}
        - Active Subject Domain: {payload.caps_subject_topic}
        - Cognitive Delivery Style Element: {profile.get('delivery_element')} ({profile.get('cognitive_style_label')})
        - Active Tactical Instructions: {profile.get('delivery_instructions')}
        - Mental Processing Vector Metrics: {profile.get('cognitive_vector')}
        
        CRITICAL PERSONALIZATION GUARDRAILS (NO GENERALIZATION / NO HALLUCINATION ALLOWED):
        - Current Academic Standing Tier: {matched_tier_meta.get('tier')}
        - Mandated Focus Strategy: {matched_tier_meta.get('focus_strategy')}
        
        You are strictly prohibited from altering or diluting the target pedagogical focus strategy parameters. 
        Before generating your reply, you must pass your text through this execution rule matrix:
        1. If Tier 1 (Foundation Builder): Explain using ultra micro-steps, absolutely zero academic jargon, foundational rules only, and extreme verbal reassurance.
        2. If Tier 2 (Mark Booster): Pinpoint structural gaps immediately, practice high-precision training, and push conceptual boundaries.
        3. If Tier 3 (Peak Maintainer): Present complex variations, use non-linear reasoning, and simulate high-pressure competitive exam conditions.
        
        MULTI-AGENT ROUTING RULES:
        """
        
        if is_practice_intent:
            base_system_prompt += """
            DEPLOYMENT: Activate 'Agent 12 — The Homework & Activities Coach'.
            Locate relevant exercise layouts within the CAPS resources. Provide an active learning challenge matching their exact tier strategy. Break concepts down interactively without exposing answers instantly.
            """
        elif is_exam_intent:
            base_system_prompt += """
            DEPLOYMENT: Activate 'Agent 13 — The Mock Exam Invigilator'.
            Enforce formal test parameters. Generate itemized evaluation challenges corresponding strictly to their tier profile. Do not render solutions upfront. Await student response submission.
            """
        else:
            base_system_prompt += """
            DEPLOYMENT: Activate 'Agent 11 — The Master Tutor'.
            Execute deep conceptual mapping using Socratic dialog criteria. Use the student's Mercury delivery instructions to contextualize difficult conceptual milestones.
            """
            
        base_system_prompt += """
        WHATSAPP MOBILE COGNITIVE RULE: Maintain optimal scannability for phone viewports. Use short paragraphs and bold text for core structural formulas, laws, or guidelines.
        """
        
        execution_payload = [*workspace_files, f"Student Input Message: {payload.student_message}"]
        
        ai_response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=execution_payload,
            config=types.GenerateContentConfig(
                system_instruction=base_system_prompt,
                temperature=0.25,
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        
        return {
            "status": "success",
            "whatsapp_number": payload.whatsapp_number,
            "response_text": ai_response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

