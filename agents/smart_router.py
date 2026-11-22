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

def format_openai_response(content: str, model: str = "deepseek-v4-flash") -> Dict[str, Any]:
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
        teacher = await get_teacher_by_email(email)
        if not teacher:
            return False, "Teacher not found"
        if not verify_password(password, teacher["password_hash"]):
            return False, "Wrong password"
        name = f"{teacher['fname']} {teacher['lname']}"
        await save_telegram_session(clean_chat_id, "teacher", teacher["idteacher"], name)
        return True, name
    except Exception as e:
        logger.error(f"Teacher login error: {e}")
        return False, str(e)

async def perform_student_login(chat_id: str, student_number: str, password: str) -> tuple[bool, str]:
    try:
        from database.db_connector import get_student_by_number, save_telegram_session
        from database.auth import verify_password
        clean_chat_id = chat_id.replace("telegram:", "")
        student = await get_student_by_number(student_number)
        if not student:
            return False, "Student not found"
        if not verify_password(password, student["password_hash"]):
            return False, "Wrong password"
        name = f"{student['fname']} {student['lname']}"
        await save_telegram_session(clean_chat_id, "student", student["idstudent"], name)
        return True, name
    except Exception as e:
        logger.error(f"Student login error: {e}")
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

async def handle_deterministic_response(text: str, chat_id: str) -> Optional[str]:
    clean = text.strip()
    lower = clean.lower()
    fsm = get_fsm(chat_id)

    if lower in ["back", "cancel", "peruuta"]:
        reset_fsm(chat_id)
        session = await check_db_session(chat_id)
        if not session:
            return LOGIN_STEP_0
        role = session.get("user_role")
        name = session.get("user_name", "")
        return f"🎓 Welcome, {name}!\n\n" + (TEACHER_MENU if role == "teacher" else STUDENT_MENU)

    if lower in ["/logout", "logout", "kirjaudu ulos", "🚪 logout"]:
        return await perform_logout(chat_id)

    session = await check_db_session(chat_id)

    if not session:
        if fsm["state"] == "IDLE" or lower in ["/start", "start", "hi", "hello", "hei", "moi", "login"]:
            if lower in ["teacher", "opettaja"]:
                fsm["state"] = "AWAITING_IDENTIFIER"
                fsm["role"] = "teacher"
                return "Enter your email:"
            elif lower in ["student", "opiskelija"]:
                fsm["state"] = "AWAITING_IDENTIFIER"
                fsm["role"] = "student"
                return "Enter your student number (e.g. H100001):"
            else:
                fsm["state"] = "AWAITING_ROLE"
                return LOGIN_STEP_0

        if fsm["state"] == "AWAITING_ROLE":
            if lower in ["teacher", "opettaja"]:
                fsm["state"] = "AWAITING_IDENTIFIER"
                fsm["role"] = "teacher"
                return "Enter your email:"
            elif lower in ["student", "opiskelija"]:
                fsm["state"] = "AWAITING_IDENTIFIER"
                fsm["role"] = "student"
                return "Enter your student number (e.g. H100001):"
            else:
                return "Please choose your role:\nReply: \"teacher\"  or  \"student\""

        if fsm["state"] == "AWAITING_IDENTIFIER":
            fsm["identifier"] = clean
            fsm["state"] = "AWAITING_PASSWORD"
            return "Enter your password:"

        if fsm["state"] == "AWAITING_PASSWORD":
            password = clean
            role = fsm["role"]
            identifier = fsm["identifier"]
            reset_fsm(chat_id)

            if role == "teacher":
                success, result = await perform_teacher_login(chat_id, identifier, password)
                if success:
                    return f"🎓 Welcome, {result}! You are logged in as teacher.\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" + TEACHER_MENU
            else:
                success, result = await perform_student_login(chat_id, identifier, password)
                if success:
                    return f"🎓 Welcome, {result}! You are logged in as student.\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" + STUDENT_MENU

            return "❌ Login failed. Try again.\n\nAre you a teacher or student?\nReply: teacher  or  student"

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

    user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            content = m.get("content", "")
            if isinstance(content, str):
                user_msg = content
            elif isinstance(content, list):
                # Multimodal or blocks
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        user_msg += item.get("text", "")
            break

    chat_id = "default_user"
    for m in messages:
        content = str(m.get("content", ""))
        match = re.search(r"chat_id[:=]\s*(\w+)", content)
        if match:
            chat_id = match.group(1)
            break
        match_tg = re.search(r"telegram:(\d+)", content)
        if match_tg:
            chat_id = match_tg.group(1)
            break

    logger.info(f"Incoming message from chat_id={chat_id}: '{user_msg}'")

    deterministic_answer = await handle_deterministic_response(user_msg, chat_id)
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
