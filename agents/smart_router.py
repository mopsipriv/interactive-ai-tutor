import os
import re
import json
import time
import logging
from typing import Dict, Any, List, Optional
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SmartRouter")

app = FastAPI(title="Smart Router for OpenClaw", version="1.0.0")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek").lower()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

UPSTREAM_URL = os.getenv("UPSTREAM_LLM_URL", "https://api.deepseek.com/chat/completions")

LOGIN_FSM: Dict[str, Dict[str, Any]] = {}

def get_fsm(chat_id: str) -> Dict[str, Any]:
    if chat_id not in LOGIN_FSM:
        LOGIN_FSM[chat_id] = {
            "state": "IDLE",
            "role": None,
            "identifier": None,
        }
    return LOGIN_FSM[chat_id]

def reset_fsm(chat_id: str):
    LOGIN_FSM[chat_id] = {
        "state": "IDLE",
        "role": None,
        "identifier": None,
    }

def extract_clean_user_message(messages: List[Dict[str, Any]]) -> str:
    """Extracts actual user input text, stripping OpenClaw internal context headers."""
    # 1. Search for clean user text after context tag or in pure message
    for m in reversed(messages):
        if m.get("role") == "user":
            content = m.get("content", "")
            if isinstance(content, str):
                content = content.strip()
                if "<<<END_OPENCLAW_INTERNAL_CONTEXT>>>" in content:
                    tail = content.split("<<<END_OPENCLAW_INTERNAL_CONTEXT>>>")[-1].strip()
                    if tail:
                        return tail
                elif not content.startswith("<<<BEGIN_OPENCLAW"):
                    return content
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        txt = item.get("text", "").strip()
                        if "<<<END_OPENCLAW_INTERNAL_CONTEXT>>>" in txt:
                            tail = txt.split("<<<END_OPENCLAW_INTERNAL_CONTEXT>>>")[-1].strip()
                            if tail:
                                return tail
                        elif not txt.startswith("<<<BEGIN_OPENCLAW"):
                            return txt

    # 2. Fallback: extract last User: entry from OpenClaw context history
    for m in reversed(messages):
        content = str(m.get("content", ""))
        user_lines = re.findall(r"User:\s*([^\n\r]+)", content)
        if user_lines:
            last_line = user_lines[-1].strip()
            if last_line:
                return last_line

    return ""

def format_openai_response(content: str, model: str = "deepseek-v4.1-flash") -> Dict[str, Any]:
    return {
        "id": f"chatcmpl-smart-{int(time.time() * 1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }

TEACHER_MENU = """🎓 Welcome! You are logged in as teacher.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 Teacher Commands:
👥 students — your students
⚠️ risk — risk report
📥 requests — pending requests
📊 analytics — course analytics
📖 curriculum [TVT2025S-OHJ/DIN2025S]
👤 profile [name] — student profile
✏️ enroll [student] [course]
📝 grade [student] [course] [1-5]
🌅 morning brief
✅ approve [id] / ❌ reject [id]
🚪 logout"""

STUDENT_MENU = """🎓 Welcome! You are logged in as student.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 Student Commands:
👤 my profile — your profile
📋 my courses — your enrollments
📊 my progress — study plan
🔍 courses — all courses
📝 enroll [course] — request enrollment
📬 my requests — request status
🚪 logout"""

LOGIN_STEP_0 = """🔐 Login to AI Tutor (OAMK)

Are you a teacher or student?
Reply: "teacher"  or  "student\""""

async def check_db_session(chat_id: str) -> Optional[Dict[str, Any]]:
    try:
        from database.db_connector import get_telegram_session
        clean_chat_id = chat_id.replace("telegram:", "")
        return await get_telegram_session(clean_chat_id)
    except Exception as e:
        logger.error(f"Error checking session: {e}")
        return None

async def perform_teacher_login(chat_id: str, email: str, password: str) -> tuple[bool, str]:
    try:
        from database.db_connector import get_teacher_by_email, save_telegram_session
        from database.auth import verify_password
        clean_chat_id = chat_id.replace("telegram:", "")
        clean_email = email.strip().lower()
        teacher = await get_teacher_by_email(clean_email)
        if not teacher:
            logger.warning(f"Teacher login failed: '{clean_email}' not found")
            return False, "Teacher not found"
        
        is_valid = verify_password(password.strip(), teacher.get("password_hash", ""))
        logger.info(f"Checking teacher password for {clean_email}: valid={is_valid}")
        if not is_valid:
            return False, "Wrong password"
        name = f"{teacher['fname']} {teacher['lname']}"
        await save_telegram_session(clean_chat_id, "teacher", teacher["idteacher"], name)
        logger.info(f"Teacher login SUCCESS: {name} (chat_id={clean_chat_id})")
        return True, name
    except Exception as e:
        logger.error(f"Teacher login error: {e}", exc_info=True)
        return False, str(e)

async def perform_student_login(chat_id: str, student_number: str, password: str) -> tuple[bool, str]:
    try:
        from database.db_connector import get_student_by_number, save_telegram_session
        from database.auth import verify_password
        clean_chat_id = chat_id.replace("telegram:", "")
        clean_num = student_number.strip().upper()
        student = await get_student_by_number(clean_num)
        if not student:
            logger.warning(f"Student login failed: '{clean_num}' not found")
            return False, "Student not found"
        
        is_valid = verify_password(password.strip(), student.get("password_hash", ""))
        logger.info(f"Checking student password for {clean_num}: valid={is_valid}")
        if not is_valid:
            return False, "Wrong password"
        name = f"{student['fname']} {student['lname']}"
        await save_telegram_session(clean_chat_id, "student", student["idstudent"], name)
        logger.info(f"Student login SUCCESS: {name} (chat_id={clean_chat_id})")
        return True, name
    except Exception as e:
        logger.error(f"Student login error: {e}", exc_info=True)
        return False, str(e)

async def perform_logout(chat_id: str) -> str:
    try:
        from database.db_connector import delete_telegram_session
        clean_chat_id = chat_id.replace("telegram:", "")
        await delete_telegram_session(clean_chat_id)
        reset_fsm(chat_id)
        return "🔒 You have been logged out. Send /start to login again."
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return "Logged out."

def extract_password_from_raw(raw_content: str) -> Optional[str]:
    """
    Try to extract password from raw OpenClaw message content.
    Handles queued format, new OpenClaw lite format, and plain text.
    Returns None for classic OpenClaw context (password not in payload).
    """
    # Classic OpenClaw context format (<<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>>) -
    # password is NOT included in the payload on first delivery.
    if "<<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>>" in raw_content:
        if "<<<END_OPENCLAW_INTERNAL_CONTEXT>>>" in raw_content:
            tail = raw_content.split("<<<END_OPENCLAW_INTERNAL_CONTEXT>>>")[-1].strip()
            if tail and len(tail) < 100:
                first_line = tail.split('\n')[0].strip()
                return first_line if first_line else None
        return None  # No password in classic format

    # Queued message format: [timestamp] [Queued user message...]\npassword\nContinue...
    queued_match = re.search(r'\[Queued user message[^\]]*\]\s*\n(.+?)(?:\n|$)', raw_content, re.IGNORECASE)
    if queued_match:
        candidate = queued_match.group(1).strip()
        if candidate and not re.search(r'^(continue|task|transcript)', candidate, re.IGNORECASE):
            return candidate

    # New OpenClaw lite format: [timestamp] Conversation info...\n```json\n{...}\n```\n\n<user_input>
    # Extract last non-empty line that isn't JSON/markdown/metadata
    lines = [l.strip() for l in raw_content.split('\n') if l.strip()]
    if lines:
        last_line = lines[-1]
        skip_patterns = r'^(\{|\}|```|Conversation|⟦|continue|task|transcript)'
        if last_line and not re.search(skip_patterns, last_line, re.IGNORECASE):
            # Sanity check: should look like a user input (not too long, not structured)
            if len(last_line) < 150 and ':' not in last_line[:5]:
                return last_line

    return None


async def handle_deterministic_response(text: str, chat_id: str, messages: List[Dict[str, Any]] = None) -> Optional[str]:
    """
    Evaluates message against deterministic rules (Login, FSM, Static commands, Menu).
    Returns response string if handled deterministically, or None if LLM is needed.
    messages: raw messages list from OpenClaw payload (for password extraction).
    """
    # Clean up prefixes from telegram/openclaw e.g. [Telegram 12345] or [Name]
    clean_text = re.sub(r"^\[.*?\]\s*", "", text).strip()
    clean_lower = re.sub(r'["\'`«»]', '', clean_text).strip().lower()
    lower = clean_lower
    fsm = get_fsm(chat_id)

    # 1. Global cancel / back
    if clean_lower in ["back", "cancel", "peruuta"]:
        reset_fsm(chat_id)
        session = await check_db_session(chat_id)
        if not session:
            return LOGIN_STEP_0
        role = session.get("user_role")
        name = session.get("user_name", "")
        return f"🎓 Welcome, {name}!\n\n" + (TEACHER_MENU if role == "teacher" else STUDENT_MENU)

    # 2. Logout command
    if clean_lower in ["/logout", "logout", "kirjaudu ulos", "🚪 logout"]:
        return await perform_logout(chat_id)

    # Check active session in DB
    session = await check_db_session(chat_id)

    # 3. If NOT logged in -> process Login FSM
    if not session:
        # 3a. AWAITING_PASSWORD: try to extract password from raw payload
        if fsm["state"] == "AWAITING_PASSWORD":
            password = None

            # Try raw message content (queued format has password directly)
            if messages:
                for m in reversed(messages):
                    if m.get("role") == "user":
                        raw = str(m.get("content", ""))
                        password = extract_password_from_raw(raw)
                        if password:
                            break

            # Fallback: try last User: line in history IF it's not email/student number
            if not password and messages:
                for m in reversed(messages):
                    content = str(m.get("content", ""))
                    user_lines = re.findall(r"User:\s*([^\n\r]+)", content)
                    if user_lines:
                        last_user = user_lines[-1].strip()
                        is_email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", last_user)
                        is_student = re.search(r"\bH\d+\b", last_user, re.IGNORECASE)
                        is_role = re.search(r"^(teacher|student|opettaja|opiskelija)$", last_user, re.IGNORECASE)
                        if last_user and not is_email and not is_student and not is_role and len(last_user) > 2:
                            password = last_user
                        break

            if password:
                role = fsm.get("role", "teacher")
                identifier = fsm.get("identifier", "")
                reset_fsm(chat_id)
                logger.info(f"-> Attempting {role} login for '{identifier}' with extracted password")
                if role == "teacher":
                    success, result = await perform_teacher_login(chat_id, identifier, password)
                    if success:
                        return f"🎓 Welcome, {result}! You are logged in as teacher.\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" + TEACHER_MENU
                else:
                    success, result = await perform_student_login(chat_id, identifier, password)
                    if success:
                        return f"🎓 Welcome, {result}! You are logged in as student.\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" + STUDENT_MENU
                return "❌ Login failed. Try again.\n\nAre you a teacher or student?\nReply: teacher  or  student"
            else:
                # Password not in payload yet (normal OpenClaw format before queued delivery)
                # Keep FSM state AWAITING_PASSWORD and re-prompt
                logger.info(f"-> Password not in payload for chat_id={chat_id}, re-prompting (FSM stays AWAITING_PASSWORD)")
                return "Enter your password:"

        # 3b. If waiting for identifier (email or student number)
        if fsm["state"] == "AWAITING_IDENTIFIER":
            if fsm.get("role") == "teacher":
                match_email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", clean_text)
                fsm["identifier"] = match_email.group(0) if match_email else clean_text
            else:
                match_num = re.search(r"\bH\d+\b", clean_text, re.IGNORECASE)
                fsm["identifier"] = match_num.group(0).upper() if match_num else clean_text
            fsm["state"] = "AWAITING_PASSWORD"
            return "Enter your password:"

        # 3c. Check role selection
        if re.search(r"\b(teacher|opettaja)\b", lower):
            fsm["state"] = "AWAITING_IDENTIFIER"
            fsm["role"] = "teacher"
            return "Enter your email:"

        if re.search(r"\b(student|opiskelija)\b", lower):
            fsm["state"] = "AWAITING_IDENTIFIER"
            fsm["role"] = "student"
            return "Enter your student number (e.g. H100001):"

        # 3d. Check direct email entry
        if re.search(r"[\w\.-]+@[\w\.-]+\.\w+", clean_text):
            email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", clean_text).group(0)
            fsm["role"] = "teacher"
            fsm["identifier"] = email_match
            fsm["state"] = "AWAITING_PASSWORD"
            return "Enter your password:"

        # 3e. Check direct student number entry
        if re.search(r"\bH\d+\b", clean_text, re.IGNORECASE):
            st_match = re.search(r"\bH\d+\b", clean_text, re.IGNORECASE).group(0).upper()
            fsm["role"] = "student"
            fsm["identifier"] = st_match
            fsm["state"] = "AWAITING_PASSWORD"
            return "Enter your password:"

        # Greeting or start
        if re.search(r"\b(start|hi|hello|hei|moi|login)\b", lower) or lower.startswith("/start"):
            fsm["state"] = "AWAITING_ROLE"
            return LOGIN_STEP_0

        # Default fallback for unauthorized
        return LOGIN_STEP_0

    role = session.get("user_role")
    user_id = session.get("user_id")
    name = session.get("user_name", "")

    if lower in ["/start", "start", "menu", "valikko", "help", "/help"]:
        return f"🎓 Welcome, {name}!\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" + (TEACHER_MENU if role == "teacher" else STUDENT_MENU)

    if role == "teacher":
        if lower in ["⚠️ risk", "risk", "riskit", "risk report"]:
            from mcp_server import get_risk_report_tool
            return await get_risk_report_tool(user_id)

        if lower in ["📥 requests", "requests", "pyynnöt"]:
            from mcp_server import get_pending_requests_tool
            reqs = await get_pending_requests_tool(user_id)
            if not reqs:
                return "📥 No pending enrollment requests."
            res = "📥 Pending Requests:\n"
            for r in reqs:
                res += f"• Request #{r.get('idrequest')}: {r.get('fname')} {r.get('lname')} → {r.get('course_name')} ({r.get('created_at')})\n"
            return res

        if lower in ["👥 students", "students", "opiskelijat"]:
            from mcp_server import get_students_by_teacher_tool
            st_list = await get_students_by_teacher_tool(user_id)
            if not st_list:
                return "👥 No students found for your cohorts."
            res = f"👥 Your Students ({len(st_list)}):\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for s in st_list[:15]:
                res += f"• {s.get('fname')} {s.get('lname')} ({s.get('student_number')}) — {s.get('group_code')}\n"
            return res

        if lower in ["🌅 morning brief", "morning brief"]:
            from mcp_server import get_morning_brief_tool
            return await get_morning_brief_tool(user_id, name)

    if role == "student":
        if lower in ["👤 my profile", "my profile", "profile", "profiili"]:
            from mcp_server import get_student_profile_tool
            prof = await get_student_profile_tool(user_id)
            if not prof:
                return "Profile not found."
            p = prof[0]
            pct = round((p.get('credits_earned', 0) / 240) * 100)
            return f"STUDENT PROFILE:\n👤 {p.get('fname')} {p.get('lname')} — {p.get('student_number')}\n📚 Program: {p.get('program_code')}\n📅 Study right: {p.get('study_right_end')}\n📊 Progress: {p.get('credits_earned', 0)}/240 ({pct}%)"

        if lower in ["📋 my courses", "my courses", "courses"]:
            from mcp_server import get_student_enrollments_tool
            courses = await get_student_enrollments_tool(user_id)
            if not courses:
                return "No enrolled courses."
            res = "COURSES:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for c in courses:
                icon = "✅" if c.get("status") == "completed" else ("🔄" if c.get("status") == "enrolled" else "📋")
                res += f"{icon} {c.get('course_name')} ({c.get('course_code')}) — {c.get('status')} {c.get('grade') or ''}\n"
            return res

        if lower in ["📊 my progress", "my progress", "progress"]:
            from mcp_server import get_student_plan_tool, get_student_from_db_tool
            st = await get_student_from_db_tool(user_id)
            prog_code = st.get("program_code", "TVT2025S-OHJ") if isinstance(st, dict) else "TVT2025S-OHJ"
            return await get_student_plan_tool(user_id, prog_code)

        if lower in ["📬 my requests", "my requests"]:
            from mcp_server import get_student_requests_tool
            reqs = await get_student_requests_tool(user_id)
            if not reqs:
                return "📬 You have no enrollment requests."
            res = "📬 Your Requests:\n"
            for r in reqs:
                res += f"• {r.get('course_name')}: {r.get('status')} ({r.get('created_at')})\n"
            return res

    return None

async def forward_to_upstream_llm(payload: Dict[str, Any]) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    
    if LLM_PROVIDER == "deepseek":
        headers["Authorization"] = f"Bearer {DEEPSEEK_API_KEY}"
        url = "https://api.deepseek.com/chat/completions"
        if payload.get("model") in ["deepseek/deepseek-v4.1-flash", "deepseek-v4.1-flash", "deepseek/deepseek-v4-flash", "deepseek-v4-flash"]:
            payload["model"] = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    elif LLM_PROVIDER == "groq":
        headers["Authorization"] = f"Bearer {GROQ_API_KEY}"
        url = "https://api.groq.com/openai/v1/chat/completions"
        if "model" in payload and "deepseek" in payload["model"]:
            payload["model"] = "llama-3.3-70b-versatile"
    elif LLM_PROVIDER == "openai":
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
        url = "https://api.openai.com/v1/chat/completions"
    else:
        headers["Authorization"] = f"Bearer {DEEPSEEK_API_KEY}"
        url = UPSTREAM_URL

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code != 200:
            logger.error(f"Upstream error {resp.status_code}: {resp.text}")
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    messages: List[Dict[str, Any]] = data.get("messages", [])
    if not messages:
        return format_openai_response("No messages provided.")

    user_msg = extract_clean_user_message(messages)

    chat_id = "default_user"
    for m in reversed(messages):
        content = str(m.get("content", ""))
        match = re.search(r"(?:chat_id|user_id|sender_id|peer|from)[:=\s]+(\w+)", content, re.IGNORECASE)
        if match:
            chat_id = match.group(1)
            break
        match_tg = re.search(r"telegram[:_](\d+)", content, re.IGNORECASE)
        if match_tg:
            chat_id = match_tg.group(1)
            break
        match_num = re.search(r"\b(\d{7,12})\b", content)
        if match_num:
            chat_id = match_num.group(1)
            break

    logger.info(f"Incoming message from chat_id={chat_id}: '{user_msg}'")

    deterministic_answer = await handle_deterministic_response(user_msg, chat_id, messages)
    if deterministic_answer is not None:
        logger.info(f"-> Handled DETERMINISTICALLY (0 tokens): {deterministic_answer[:40]}...")
        return format_openai_response(deterministic_answer, model=data.get("model", "deepseek-v4-flash"))

    logger.info("-> Forwarding to upstream LLM (Semantic/RAG query)...")
    return await forward_to_upstream_llm(data)

@app.get("/health")
async def health():
    return {"status": "ok", "provider": LLM_PROVIDER}

if __name__ == "__main__":
    port = int(os.getenv("ROUTER_PORT", 8080))
    logger.info(f"Starting Smart Router on port {port}...")
    uvicorn.run("agents.smart_router:app", host="0.0.0.0", port=port, reload=False)
