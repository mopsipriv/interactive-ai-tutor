import os
import re
import hmac
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
ROUTER_API_KEY = os.getenv("ROUTER_API_KEY", "").strip()

MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_SECONDS = int(os.getenv("LOGIN_LOCKOUT_SECONDS", "300"))
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "24"))
MAX_LLM_HISTORY_MESSAGES = int(os.getenv("MAX_LLM_HISTORY_MESSAGES", "6"))
ESTIMATED_TOKENS_PER_DETERMINISTIC_HIT = 6000

ROUTER_METRICS: Dict[str, Any] = {
    "started_at": int(time.time()),
    "total_requests": 0,
    "deterministic_handled": 0,
    "llm_forwarded": 0,
}


def get_metrics_snapshot() -> Dict[str, Any]:
    total = ROUTER_METRICS["total_requests"]
    det = ROUTER_METRICS["deterministic_handled"]
    llm = ROUTER_METRICS["llm_forwarded"]
    ratio = round((det / total) * 100, 1) if total > 0 else 0.0
    return {
        "uptime_seconds": int(time.time() - ROUTER_METRICS["started_at"]),
        "total_requests": total,
        "deterministic_handled": det,
        "llm_forwarded": llm,
        "deterministic_ratio_pct": ratio,
        "estimated_tokens_saved": det * ESTIMATED_TOKENS_PER_DETERMINISTIC_HIT,
    }

LOGIN_FSM: Dict[str, Dict[str, Any]] = {}
LOGIN_ATTEMPTS: Dict[str, Dict[str, Any]] = {}
EXPIRED_SESSION_NOTICES: set = set()


def get_lockout_remaining(chat_id: str) -> int:
    """Returns remaining lockout seconds for chat_id (0 if not locked)."""
    rec = LOGIN_ATTEMPTS.get(chat_id)
    if not rec:
        return 0
    locked_until = rec.get("locked_until", 0.0)
    if locked_until <= 0:
        return 0
    remaining = int(locked_until - time.time())
    if remaining <= 0:
        LOGIN_ATTEMPTS.pop(chat_id, None)
        return 0
    return remaining


def record_failed_login(chat_id: str) -> tuple[int, bool]:
    """Records a failed login attempt. Returns (attempts_left, is_now_locked)."""
    rec = LOGIN_ATTEMPTS.setdefault(chat_id, {"count": 0, "locked_until": 0.0})
    rec["count"] += 1
    if rec["count"] >= MAX_LOGIN_ATTEMPTS:
        rec["locked_until"] = time.time() + LOCKOUT_SECONDS
        return 0, True
    return MAX_LOGIN_ATTEMPTS - rec["count"], False


def clear_login_attempts(chat_id: str):
    LOGIN_ATTEMPTS.pop(chat_id, None)


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

def strip_openclaw_wrapper(raw: str) -> str:
    """Strips OpenClaw metadata wrappers (internal context blocks, lite Conversation info JSON, queued prefix)."""
    text = raw.strip()
    if not text:
        return ""

    # 1. Remove ALL <<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>> ... <<<END_OPENCLAW_INTERNAL_CONTEXT>>> blocks.
    #    These contain old conversation history, NOT the current user message.
    if "<<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>>" in text:
        text = re.sub(
            r"<<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>>[\s\S]*?<<<END_OPENCLAW_INTERNAL_CONTEXT>>>",
            "",
            text,
        ).strip()
        # Handle unclosed marker just in case
        if "<<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>>" in text:
            text = text.split("<<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>>")[0].strip()
        if not text:
            return ""

    # 2. Queued user message wrapper
    queued_match = re.search(
        r"\[Queued user message[^\]]*\]\s*\n(.+?)(?:\n\nContinue|\nContinue|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if queued_match:
        candidate = queued_match.group(1).strip()
        if candidate:
            text = candidate

    # 3. Lite Conversation info / Sender metadata wrappers:
    #    [Wed 2026-11-25 13:20 UTC] Conversation info: ⟦openclaw:ctx⟧\n```json\n{...}\n```\n\n<actual message>
    if "Conversation info" in text or "Sender (" in text or "⟦openclaw:ctx⟧" in text:
        cleaned = re.sub(
            r"(?:^|\n)(?:\[[^\]]+\]\s*)?(?:Conversation info|Sender)[^\n]*\n```(?:json)?\s*[\s\S]*?```\s*",
            "\n",
            text,
            flags=re.IGNORECASE,
        ).strip()
        text = cleaned

    # 4. Strip OpenClaw Runtime metadata footer (appended on first turn of a new session)
    text = re.sub(r"\n+Runtime:\s*agent=[^\n]*", "", text).strip()

    # 5. Strip leading timestamp/sender brackets like [Wed 2026-11-25 13:20 UTC] or [Telegram 12345]
    text = re.sub(r"^(?:\[[^\]]+\]\s*)+", "", text).strip()
    return text


def extract_chat_id(messages: List[Dict[str, Any]]) -> str:
    """
    Reliably extracts numeric Telegram chat_id from OpenClaw JSON metadata.
    Never matches natural-language words like 'from this chat'.
    """
    patterns = [
        r'"chat_id"\s*:\s*"?(?:telegram:(?:direct:)?)?(\d{5,15})"?',
        r'"sender"\s*:\s*\{[^}]*"id"\s*:\s*"?(\d{5,15})"?',
        r'telegram:(?:direct:)?(\d{5,15})',
        r'(?:chat_id|user_id|sender_id)\s*[:=]\s*"?(\d{5,15})"?',
    ]
    for m in reversed(messages):
        content = _message_to_text(m.get("content", ""))
        for pat in patterns:
            match = re.search(pat, content, re.IGNORECASE)
            if match:
                return match.group(1)
    # Last-resort fallback: any 7-12 digit ID in user/system metadata
    for m in reversed(messages):
        if m.get("role") in ("user", "system"):
            content = _message_to_text(m.get("content", ""))
            match_num = re.search(r"\b(\d{7,12})\b", content)
            if match_num:
                return match_num.group(1)
    return "default_user"


def _message_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        return "\n".join(parts)
    return str(content or "")


def extract_clean_user_message(messages: List[Dict[str, Any]]) -> str:
    """
    Extracts the actual current user input text from the latest turn in messages[],
    skipping OpenClaw internal-context-only injections and stopping at the previous assistant turn.
    """
    for m in reversed(messages):
        role = m.get("role")
        if role == "assistant":
            break
        if role == "user":
            raw = _message_to_text(m.get("content", ""))
            cleaned = strip_openclaw_wrapper(raw)
            if cleaned:
                return cleaned
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
🚀 projects — OAMK projects & prerequisites
👤 profile [name] — student profile
✏️ enroll [student] [course]
📝 grade [student] [course] [1-5]
🌅 morning brief
✅ approve [id] / ❌ reject [id]
📈 stats — AI router savings metrics
🔑 change password
🚪 logout"""

STUDENT_MENU = """🎓 Welcome! You are logged in as student.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 Student Commands:
👤 my profile — your profile
📋 my courses — your enrollments
📊 my progress — study plan
🔍 courses — all courses
🚀 projects — project eligibility
📝 enroll [course] — request enrollment
📬 my requests — request status
🔑 change password
🚪 logout"""

LOGIN_STEP_0 = """🔐 Login to AI Tutor (OAMK)

Are you a teacher or student?
Reply: "teacher"  or  "student\""""

async def check_db_session(chat_id: str) -> Optional[Dict[str, Any]]:
    try:
        from database.db_connector import get_telegram_session, delete_telegram_session
        clean_chat_id = chat_id.replace("telegram:", "")
        session = await get_telegram_session(clean_chat_id)
        if not session:
            return None

        # Check session TTL (default 24h) using DB-calculated session_age_sec or logged_in_at
        ttl_sec = SESSION_TTL_HOURS * 3600
        age_sec = session.get("session_age_sec")
        if age_sec is None and session.get("logged_in_at"):
            from datetime import datetime
            ts = session["logged_in_at"]
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            age_sec = (datetime.now() - ts).total_seconds()

        if age_sec is not None and age_sec > ttl_sec:
            logger.info(f"Session expired for chat_id={clean_chat_id} (age={int(age_sec)}s > {ttl_sec}s)")
            await delete_telegram_session(clean_chat_id)
            reset_fsm(chat_id)
            EXPIRED_SESSION_NOTICES.add(chat_id)
            return None

        return session
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


def _format_dt(val: Any) -> str:
    if val is None:
        return "—"
    return str(val)[:16]


def _format_student_profile(rows: List[Dict[str, Any]]) -> str:
    """Formats rows returned by get_student_profile() into a clean profile card."""
    if not rows:
        return "Profile not found."
    p = rows[0]
    credits_earned = sum(
        int(r.get("credit") or 0)
        for r in rows
        if r.get("status") == "completed" and r.get("course_name")
    )
    pct = min(100, round((credits_earned / 240) * 100))
    filled = int(pct / 10)
    bar = "▓" * filled + "░" * (10 - filled)

    group = p.get("group_code") or "—"
    program = p.get("study_right") or "TVT2025S-OHJ"
    valid_until = p.get("valid_until") or "—"

    lines = [
        "👤 STUDENT PROFILE",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"Name: {p.get('fname')} {p.get('lname')} ({p.get('student_number')})",
        f"📧 Email: {p.get('email') or '—'}",
        f"👥 Group: {group}",
        f"📚 Program: {program}",
        f"📅 Study right until: {valid_until}",
        f"📊 Credits: {bar} {credits_earned}/240 ({pct}%)",
    ]

    enrolled_courses = [r for r in rows if r.get("course_name")]
    if enrolled_courses:
        lines.append("\n📋 Recent Courses:")
        for c in enrolled_courses[:12]:
            st = c.get("status") or ""
            icon = "✅" if st == "completed" else ("🔄" if st == "ongoing" else "📋")
            code = c.get("course_code") or ""
            grade_str = f" — grade {c['grade']}" if c.get("grade") else ""
            lines.append(f"  {icon} {c['course_name']} ({code}, {c.get('credit', 0)}cr){grade_str}")
        if len(enrolled_courses) > 12:
            lines.append(f"  ... and {len(enrolled_courses) - 12} more (type 'my courses')")

    return "\n".join(lines)


async def _pick_course(query: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Finds a single course by code or name; returns (course_dict, error_message)."""
    from database.db_connector import search_courses_by_name
    q = query.strip()
    if not q:
        return None, "Please specify a course code or name (e.g. IN00DL12 or Pilvipalvelut)."
    matches = await search_courses_by_name(q)
    if not matches:
        return None, f"❌ Course '{q}' not found. Type 'courses' to see available courses."
    # Prefer exact code or exact name match (case-insensitive)
    for m in matches:
        if m["course_code"].lower() == q.lower() or m["course_name"].lower() == q.lower():
            return m, None
    if len(matches) == 1:
        return matches[0], None
    opts = "\n".join(f"• {m['course_code']} — {m['course_name']}" for m in matches[:6])
    return None, f"Multiple courses match '{q}'. Please use the exact course code:\n{opts}"


async def _resolve_student_and_course(rest: str) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[str]]:
    """Parses '<student> <course>' supporting H-numbers, course codes, or full names."""
    from database.db_connector import search_students_by_name
    s = rest.strip()
    if not s:
        return None, None, None

    student_q = ""
    course_q = ""

    # Pattern 1: starts with student number (e.g. H100001 IN00DL12 or H100001 Pilvipalvelut)
    m_num = re.match(r"^(H\d+)\s+(.+)$", s, re.IGNORECASE)
    if m_num:
        student_q, course_q = m_num.group(1), m_num.group(2).strip()
    else:
        # Pattern 2: contains a course code (e.g. John Smith IN00DL12 or John Smith T009015)
        m_code = re.search(r"\b([A-Z]{2}\d{2}[A-Z]{2}\d{2}|T\d{6})\b", s, re.IGNORECASE)
        if m_code and m_code.start() > 0:
            student_q = s[:m_code.start()].strip()
            course_q = m_code.group(1).strip()
        else:
            # Pattern 3: first 2 words = full name, rest = course; fallback to 1 word
            parts = s.split()
            if len(parts) >= 3:
                cand2 = " ".join(parts[:2])
                st2 = await search_students_by_name(cand2)
                if st2:
                    student_q, course_q = cand2, " ".join(parts[2:])
                else:
                    student_q, course_q = parts[0], " ".join(parts[1:])
            elif len(parts) == 2:
                student_q, course_q = parts[0], parts[1]
            else:
                return None, None, None

    students = await search_students_by_name(student_q)
    if not students:
        return None, None, f"❌ Student '{student_q}' not found."
    student = None
    for st in students:
        full = f"{st['fname']} {st['lname']}".lower()
        if st["student_number"].lower() == student_q.lower() or full == student_q.lower():
            student = st
            break
    if not student:
        if len(students) == 1:
            student = students[0]
        else:
            opts = "\n".join(f"• {st['fname']} {st['lname']} ({st['student_number']})" for st in students[:5])
            return None, None, f"Multiple students match '{student_q}'. Please use student number:\n{opts}"

    course, err = await _pick_course(course_q)
    if err:
        return None, None, err
    return student, course, None


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
        # 3.0 Notify user if their previous session just expired
        if chat_id in EXPIRED_SESSION_NOTICES:
            EXPIRED_SESSION_NOTICES.discard(chat_id)
            fsm["state"] = "AWAITING_ROLE"
            return f"⏱ Your session expired after {SESSION_TTL_HOURS}h. Please log in again.\n\n{LOGIN_STEP_0}"

        # 3.1 Rate-limit lockout check
        lock_rem = get_lockout_remaining(chat_id)
        if lock_rem > 0:
            mins, secs = divmod(lock_rem, 60)
            wait_str = f"{mins}m {secs}s" if mins else f"{secs}s"
            return f"⛔ Too many failed login attempts. Please wait {wait_str} and try again."

        # 3a. AWAITING_PASSWORD: clean_text already has all OpenClaw wrappers stripped
        if fsm["state"] == "AWAITING_PASSWORD":
            password = clean_text.splitlines()[-1].strip() if clean_text else ""

            if password:
                role = fsm.get("role", "teacher")
                identifier = fsm.get("identifier", "")
                logger.info(f"-> Attempting {role} login for '{identifier}' with password (len={len(password)})")
                if role == "teacher":
                    success, result = await perform_teacher_login(chat_id, identifier, password)
                    if success:
                        reset_fsm(chat_id)
                        clear_login_attempts(chat_id)
                        menu_body = TEACHER_MENU.split("\n", 1)[1] if "\n" in TEACHER_MENU else TEACHER_MENU
                        return (
                            f"🎓 Welcome, {result}! You are logged in as teacher.\n"
                            f"🔒 Security tip: delete your password message from this chat.\n"
                            f"{menu_body}"
                        )
                else:
                    success, result = await perform_student_login(chat_id, identifier, password)
                    if success:
                        reset_fsm(chat_id)
                        clear_login_attempts(chat_id)
                        menu_body = STUDENT_MENU.split("\n", 1)[1] if "\n" in STUDENT_MENU else STUDENT_MENU
                        return (
                            f"🎓 Welcome, {result}! You are logged in as student.\n"
                            f"🔒 Security tip: delete your password message from this chat.\n"
                            f"{menu_body}"
                        )

                # Failed login -> track attempt & keep FSM convenient for retry
                attempts_left, locked = record_failed_login(chat_id)
                if locked:
                    reset_fsm(chat_id)
                    mins = LOCKOUT_SECONDS // 60
                    return f"⛔ Too many failed login attempts. Login is locked for {mins} minutes."

                if "Wrong password" in str(result):
                    # Keep role + identifier so user only re-enters password
                    return (
                        f"❌ Wrong password ({attempts_left} attempts remaining).\n"
                        f"Please enter your password again, or type \"cancel\" to start over:"
                    )

                # Account not found -> return to identifier step for the same role
                fsm["state"] = "AWAITING_IDENTIFIER"
                fsm["identifier"] = None
                id_label = "email" if role == "teacher" else "student number (e.g. H100001)"
                return (
                    f"❌ Account '{identifier}' not found ({attempts_left} attempts remaining).\n"
                    f"Please enter your {id_label}, or type \"cancel\" to switch role:"
                )
            else:
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

    # Authenticated sub-FSM: password change flow
    if fsm["state"] in ("CHG_PASS_CURRENT", "CHG_PASS_NEW"):
        return await _handle_password_change_fsm(fsm, clean_text, chat_id, role, user_id)

    if lower in ["/start", "start", "menu", "valikko", "help", "/help"]:
        menu = TEACHER_MENU if role == "teacher" else STUDENT_MENU
        menu_body = menu.split("\n", 1)[1] if "\n" in menu else menu
        return f"🎓 Welcome, {name}! You are logged in as {role}.\n{menu_body}"

    # Strip leading decorative emojis for command prefix matching
    cmd_text = re.sub(r"^[^\w/]+\s*", "", clean_text).strip()
    cmd_lower = cmd_text.lower()

    if cmd_lower in ["change password", "vaihda salasana", "password", "/password"]:
        fsm["state"] = "CHG_PASS_CURRENT"
        return '🔑 Enter your current password (or type "cancel"):'

    if role == "teacher":
        if cmd_lower in ["risk", "riskit", "risk report"]:
            from mcp_server import get_risk_report_tool
            res = await get_risk_report_tool(user_id)
            await _audit_teacher_action(user_id, cmd_text, "risk_report", res)
            return res

        if cmd_lower in ["requests", "pyynnöt", "pending requests"]:
            from database.db_connector import get_pending_requests
            reqs = await get_pending_requests(user_id)
            if not reqs:
                res = "📥 No pending enrollment requests."
            else:
                res = f"📥 Pending Requests ({len(reqs)}):\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                for r in reqs:
                    res += (
                        f"• Request #{r.get('idrequest')}: {r.get('fname')} {r.get('lname')} "
                        f"({r.get('group_code')}) → {r.get('course_name')} ({r.get('course_code')}) "
                        f"[{_format_dt(r.get('requested_at'))}]\n"
                    )
                res += "\nReply: approve [id] or reject [id]"
            await _audit_teacher_action(user_id, cmd_text, "pending_requests", res)
            return res

        if cmd_lower in ["students", "opiskelijat", "my students"]:
            from database.db_connector import get_students_by_teacher
            st_list = await get_students_by_teacher(user_id)
            if not st_list:
                res = "👥 No students found for your cohorts."
            else:
                res = f"👥 Your Students ({len(st_list)}):\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                for s in st_list[:20]:
                    group = s.get("group_code") or "—"
                    res += f"• {s.get('fname')} {s.get('lname')} ({s.get('student_number')}) — {group}\n"
            await _audit_teacher_action(user_id, cmd_text, "list_students", res)
            return res

        if cmd_lower in ["morning brief", "brief", "weekly brief"]:
            from mcp_server import get_morning_brief_tool
            brief = await get_morning_brief_tool(user_id, name)
            res = brief or "🌅 No students assigned to your cohorts yet."
            await _audit_teacher_action(user_id, cmd_text, "morning_brief", res)
            return res

        if cmd_lower in ["analytics", "course analytics", "analytiikka"]:
            from database.db_connector import get_course_analytics
            rows = await get_course_analytics()
            if not rows:
                res = "📊 No course analytics data available yet."
            else:
                res = f"📊 Course Analytics ({len(rows)} courses):\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                for r in rows[:20]:
                    avg = f"{float(r['avg_grade']):.1f}" if r.get("avg_grade") is not None else "—"
                    total = int(r.get("total_students") or 0)
                    done = int(r.get("completed_count") or 0)
                    pct = round((done / total) * 100) if total else 0
                    res += f"• {r['course_code']} {r['course_name']}: {done}/{total} completed ({pct}%), avg grade {avg}\n"
            await _audit_teacher_action(user_id, cmd_text, "course_analytics", res)
            return res

        if cmd_lower == "curriculum" or cmd_lower.startswith("curriculum "):
            from database.db_connector import get_curriculum
            prog_arg = cmd_text[len("curriculum"):].strip().upper() or "TVT2025S-OHJ"
            rows = await get_curriculum(prog_arg)
            if not rows:
                return f"❌ Curriculum '{prog_arg}' not found.\nAvailable programs: TVT2025S-OHJ, DIN2025S"
            res = f"📖 Curriculum: {prog_arg}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            current_year = None
            for r in rows:
                if r["year_of_study"] != current_year:
                    current_year = r["year_of_study"]
                    res += f"\n\nYear {current_year}:"
                res += f"\n  • {r['course_code']} — {r['course_name']} ({r['credit']}cr)"
            await _audit_teacher_action(user_id, cmd_text, "curriculum", f"Viewed {prog_arg}")
            return res

        if cmd_lower == "profile" or cmd_lower.startswith("profile "):
            from database.db_connector import (
                search_students_by_name,
                get_student_profile,
                verify_student_ownership,
            )
            query = cmd_text[len("profile"):].strip()
            if not query:
                return "Usage: profile [student name or number]\nExample: profile John Smith  or  profile H100001"
            matches = await search_students_by_name(query)
            if not matches:
                return f"❌ Student '{query}' not found."
            chosen = None
            for m in matches:
                if m["student_number"].lower() == query.lower() or f"{m['fname']} {m['lname']}".lower() == query.lower():
                    chosen = m
                    break
            if not chosen:
                if len(matches) == 1:
                    chosen = matches[0]
                else:
                    opts = "\n".join(f"• {m['fname']} {m['lname']} ({m['student_number']})" for m in matches[:6])
                    return f"Multiple students found for '{query}'. Please specify:\n{opts}"
            if not await verify_student_ownership(chosen["idstudent"], user_id):
                denied = f"⛔ Access denied: {chosen['fname']} {chosen['lname']} ({chosen['student_number']}) is not in your assigned student groups."
                await _audit_teacher_action(user_id, cmd_text, "student_profile_denied", denied)
                return denied
            prof_rows = await get_student_profile(chosen["idstudent"])
            res = _format_student_profile(prof_rows)
            await _audit_teacher_action(user_id, cmd_text, "student_profile", f"Viewed {chosen['student_number']}")
            return res

        m_approve = re.match(r"^approve\s+#?(\d+)$", cmd_lower)
        if m_approve:
            from database.db_connector import approve_request
            req_id = int(m_approve.group(1))
            result = await approve_request(req_id, user_id)
            prefix = "✅ " if not result.startswith("Error") else "❌ "
            res = f"{prefix}Request #{req_id}: {result}"
            await _audit_teacher_action(user_id, cmd_text, "approve_request", res)
            return res

        m_reject = re.match(r"^reject\s+#?(\d+)$", cmd_lower)
        if m_reject:
            from database.db_connector import reject_request
            req_id = int(m_reject.group(1))
            result = await reject_request(req_id, user_id)
            prefix = "✅ " if not result.startswith("Error") else "❌ "
            res = f"{prefix}Request #{req_id}: {result}"
            await _audit_teacher_action(user_id, cmd_text, "reject_request", res)
            return res

        if cmd_lower == "enroll" or cmd_lower.startswith("enroll "):
            from database.db_connector import enroll_student, verify_student_ownership
            rest = cmd_text[len("enroll"):].strip()
            student, course, err = await _resolve_student_and_course(rest)
            if err:
                return err
            if not student or not course:
                return "Usage: enroll [student] [course]\nExample: enroll H100001 IN00DL12  or  enroll John Smith Pilvipalvelut"
            if not await verify_student_ownership(student["idstudent"], user_id):
                denied = f"⛔ Access denied: {student['fname']} {student['lname']} ({student['student_number']}) is not in your assigned student groups."
                await _audit_teacher_action(user_id, cmd_text, "enroll_student_denied", denied)
                return denied
            result = await enroll_student(student["idstudent"], course["idcourse"])
            prefix = "✅ " if "successfully" in result.lower() else "ℹ️ "
            res = f"{prefix}{student['fname']} {student['lname']} ({student['student_number']}) → {course['course_name']} ({course['course_code']}): {result}"
            await _audit_teacher_action(user_id, cmd_text, "enroll_student", res)
            return res

        if cmd_lower in ["stats", "metrics", "router stats", "ai stats"]:
            m = get_metrics_snapshot()
            # Include the current 'stats' call itself (already counted in total_requests)
            det = m["deterministic_handled"] + (1 if m["total_requests"] > m["deterministic_handled"] + m["llm_forwarded"] else 0)
            total = max(m["total_requests"], det + m["llm_forwarded"])
            ratio = round((det / total) * 100, 1) if total > 0 else 100.0
            saved = det * ESTIMATED_TOKENS_PER_DETERMINISTIC_HIT
            mins, secs = divmod(m["uptime_seconds"], 60)
            hrs, mins = divmod(mins, 60)
            uptime_str = f"{hrs}h {mins}m {secs}s" if hrs else (f"{mins}m {secs}s" if mins else f"{secs}s")
            res = (
                "📈 Smart Router AI Optimization Metrics\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 Upstream LLM Provider: {LLM_PROVIDER}\n"
                f"⏱ Uptime: {uptime_str}\n"
                f"📨 Total Requests: {total}\n"
                f"⚡ Deterministic (0 tokens): {det}\n"
                f"🧠 Forwarded to LLM (RAG): {m['llm_forwarded']}\n"
                f"💰 Deterministic Ratio: {ratio}%\n"
                f"🔋 Estimated Tokens Saved: ~{saved:,}"
            )
            await _audit_teacher_action(user_id, cmd_text, "router_stats", f"ratio={ratio}%")
            return res

        if cmd_lower in ["projects", "projektit", "all projects"]:
            from database.db_connector import get_all_projects_with_requirements, get_all_courses
            projects = await get_all_projects_with_requirements()
            if not projects:
                return "🚀 No projects found in the database."
            courses_map = {c["idcourse"]: c for c in await get_all_courses()}
            lines = [f"🚀 OAMK Projects ({len(projects)}):", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
            for p in projects:
                req_labels = []
                for cid in p.get("required_courses", []):
                    c = courses_map.get(cid)
                    req_labels.append(f"{c['course_code']} ({c['course_name']})" if c else f"Course #{cid}")
                req_str = ", ".join(req_labels) if req_labels else "None"
                lines.append(f"\n📌 {p['project_name']}")
                if p.get("description"):
                    lines.append(f"   {p['description']}")
                lines.append(f"   📋 Prerequisites: {req_str}")
            res = "\n".join(lines)
            await _audit_teacher_action(user_id, cmd_text, "list_projects", f"{len(projects)} projects")
            return res

        if cmd_lower == "grade" or cmd_lower.startswith("grade "):
            from database.db_connector import update_grade, verify_student_ownership
            rest = cmd_text[len("grade"):].strip()
            m_grade = re.match(r"^(.+?)\s+(\d+)$", rest)
            if not m_grade:
                return "Usage: grade [student] [course] [1-5]\nExample: grade H100001 IN00DL12 5  or  grade John Smith Pilvipalvelut 4"
            sc_part, grade_val = m_grade.group(1).strip(), int(m_grade.group(2))
            if grade_val < 1 or grade_val > 5:
                return "❌ Grade must be between 1 and 5."
            student, course, err = await _resolve_student_and_course(sc_part)
            if err:
                return err
            if not student or not course:
                return "Usage: grade [student] [course] [1-5]\nExample: grade H100001 IN00DL12 5"
            if not await verify_student_ownership(student["idstudent"], user_id):
                denied = f"⛔ Access denied: {student['fname']} {student['lname']} ({student['student_number']}) is not in your assigned student groups."
                await _audit_teacher_action(user_id, cmd_text, "grade_student_denied", denied)
                return denied
            result = await update_grade(student["idstudent"], course["idcourse"], grade_val)
            prefix = "✅ " if "successfully" in result.lower() else "❌ "
            res = f"{prefix}{student['fname']} {student['lname']} — {course['course_name']} ({course['course_code']}): grade {grade_val} ({result})"
            await _audit_teacher_action(user_id, cmd_text, "grade_student", res)
            return res

    if role == "student":
        if cmd_lower in ["my profile", "profile", "profiili"]:
            from database.db_connector import get_student_profile
            prof = await get_student_profile(user_id)
            return _format_student_profile(prof)

        if cmd_lower in ["my courses", "omat kurssit"]:
            from database.db_connector import get_student_enrollments
            courses = await get_student_enrollments(user_id)
            if not courses:
                return "📋 You have no enrolled courses yet. Type 'courses' to browse available courses."
            res = f"📋 My Courses ({len(courses)}):\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for c in courses:
                st = c.get("status") or ""
                icon = "✅" if st == "completed" else ("🔄" if st == "ongoing" else "📋")
                grade_str = f" (grade: {c['grade']})" if c.get("grade") else ""
                res += f"{icon} {c.get('course_name')} ({c.get('course_code')}, {c.get('credit', 0)}cr) — {st}{grade_str}\n"
            return res

        if cmd_lower in ["courses", "all courses", "kurssit"]:
            from database.db_connector import get_all_courses
            courses = await get_all_courses()
            if not courses:
                return "No courses found in catalog."
            res = f"🔍 All OAMK Courses ({len(courses)}):\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            current_year = None
            for c in sorted(courses, key=lambda x: (x.get("year_of_study", 9), x.get("course_code", ""))):
                if c.get("year_of_study") != current_year:
                    current_year = c.get("year_of_study")
                    res += f"\n\nYear {current_year}:"
                res += f"\n  • {c['course_code']} — {c['course_name']} ({c['credit']}cr)"
            res += "\n\nTo request enrollment: enroll [course code or name]"
            return res

        if cmd_lower in ["my progress", "progress", "study plan", "opintosuunnitelma"]:
            from mcp_server import get_student_plan_tool
            from database.db_connector import get_student_from_db
            st = await get_student_from_db(user_id)
            prog_code = st.get("study_right", "TVT2025S-OHJ") if isinstance(st, dict) else "TVT2025S-OHJ"
            return await get_student_plan_tool(user_id, prog_code)

        if cmd_lower == "enroll" or cmd_lower.startswith("enroll "):
            from database.db_connector import create_enrollment_request
            course_q = cmd_text[len("enroll"):].strip()
            course, err = await _pick_course(course_q)
            if err:
                return err
            result = await create_enrollment_request(user_id, course["idcourse"])
            if result.startswith("Error"):
                return f"❌ {result}"
            return (
                f"✅ Enrollment request submitted for {course['course_name']} ({course['course_code']}).\n"
                f"Your teacher will review it shortly. Type 'my requests' to check status."
            )

        if cmd_lower in ["projects", "my projects", "projektit"]:
            from database.db_connector import (
                get_all_projects_with_requirements,
                get_all_courses,
                get_student_enrollments,
            )
            projects = await get_all_projects_with_requirements()
            if not projects:
                return "🚀 No projects available yet."
            courses_map = {c["idcourse"]: c for c in await get_all_courses()}
            enrollments = await get_student_enrollments(user_id)
            completed_ids = {e["idcourse"] for e in enrollments if e.get("status") == "completed"}

            lines = [f"🚀 Project Eligibility ({len(projects)} projects):", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
            for p in projects:
                req_ids = p.get("required_courses", [])
                missing = [cid for cid in req_ids if cid not in completed_ids]
                if not missing:
                    status_line = "✅ Eligible — all prerequisites completed!"
                else:
                    miss_names = []
                    for cid in missing:
                        c = courses_map.get(cid)
                        miss_names.append(f"{c['course_code']} {c['course_name']}" if c else f"Course #{cid}")
                    status_line = f"⏳ Missing ({len(missing)}): " + ", ".join(miss_names)
                lines.append(f"\n📌 {p['project_name']}")
                if p.get("description"):
                    lines.append(f"   {p['description']}")
                lines.append(f"   {status_line}")
            return "\n".join(lines)

        if cmd_lower in ["my requests", "omat pyynnöt", "requests"]:
            from database.db_connector import get_student_requests
            reqs = await get_student_requests(user_id)
            if not reqs:
                return "📬 You have no enrollment requests."
            res = f"📬 Your Enrollment Requests ({len(reqs)}):\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for r in reqs:
                st = r.get("status") or "pending"
                icon = "✅" if st == "approved" else ("❌" if st == "rejected" else "⏳")
                res += (
                    f"{icon} #{r.get('idrequest')} {r.get('course_name')} ({r.get('course_code')}) — "
                    f"{st} [{_format_dt(r.get('requested_at'))}]\n"
                )
            return res

    return None

async def _audit_teacher_action(teacher_id: int, query_text: str, intent: str, result: str):
    """Logs teacher actions to teacher_query_log for auditability (best-effort, non-blocking on error)."""
    try:
        from database.db_connector import log_teacher_query
        await log_teacher_query(teacher_id, query_text[:500], intent[:50], result[:500])
    except Exception as e:
        logger.debug(f"Audit log skipped: {e}")


async def _handle_password_change_fsm(
    fsm: Dict[str, Any],
    clean_text: str,
    chat_id: str,
    role: str,
    user_id: int,
) -> str:
    """2-step deterministic password change flow (CHG_PASS_CURRENT -> CHG_PASS_NEW)."""
    from database.auth import verify_password, hash_password
    from database.db_connector import (
        get_teacher_by_id,
        get_student_from_db,
        update_teacher_password,
        update_student_password,
    )

    candidate = clean_text.splitlines()[-1].strip() if clean_text else ""

    if fsm["state"] == "CHG_PASS_CURRENT":
        if not candidate:
            return '🔑 Enter your current password (or type "cancel"):'
        account = await (get_teacher_by_id(user_id) if role == "teacher" else get_student_from_db(user_id))
        if not isinstance(account, dict) or not verify_password(candidate, account.get("password_hash", "")):
            return '❌ Current password is incorrect. Try again, or type "cancel":'
        fsm["state"] = "CHG_PASS_NEW"
        return '✅ Current password verified.\nNow enter your new password (min 6 characters), or type "cancel":'

    if fsm["state"] == "CHG_PASS_NEW":
        if len(candidate) < 6:
            return '❌ Password must be at least 6 characters long. Enter a new password, or type "cancel":'
        new_hash = hash_password(candidate)
        res = await (
            update_teacher_password(user_id, new_hash)
            if role == "teacher"
            else update_student_password(user_id, new_hash)
        )
        reset_fsm(chat_id)
        if res.startswith("Error"):
            return f"❌ Could not update password: {res}"
        if role == "teacher":
            await _audit_teacher_action(user_id, "change password", "change_password", "Password updated")
        return (
            "✅ Password updated successfully!\n"
            "🔒 Security tip: delete your password messages from this chat."
        )

    reset_fsm(chat_id)
    return "Cancelled."


def trim_conversation_history(
    messages: List[Dict[str, Any]],
    max_non_system: int = MAX_LLM_HISTORY_MESSAGES,
) -> List[Dict[str, Any]]:
    """
    Sliding-window history trimmer for LLM token optimization.
    Keeps all system messages + the last `max_non_system` conversational turns,
    and strips bloated OpenClaw INTERNAL_CONTEXT blocks from prior user turns.
    """
    system_msgs = [m for m in messages if m.get("role") == "system"]
    conv_msgs = [m for m in messages if m.get("role") != "system"]

    if len(conv_msgs) > max_non_system:
        start_idx = len(conv_msgs) - max_non_system
        # Never start slice with an orphaned tool response
        while start_idx > 0 and conv_msgs[start_idx].get("role") == "tool":
            start_idx -= 1
        conv_msgs = conv_msgs[start_idx:]

    cleaned_conv: List[Dict[str, Any]] = []
    for m in conv_msgs:
        if m.get("role") == "user":
            raw = _message_to_text(m.get("content", ""))
            stripped = strip_openclaw_wrapper(raw)
            if not stripped:
                continue  # skip pure INTERNAL_CONTEXT injection messages
            cleaned_conv.append({"role": "user", "content": stripped})
        else:
            cleaned_conv.append(m)

    return system_msgs + cleaned_conv


async def enrich_payload_with_rag(payload: Dict[str, Any], user_msg: str, chat_id: str) -> Dict[str, Any]:
    """Trims conversation history (sliding window) and enriches semantic LLM queries with OAMK RAG documents."""
    messages = payload.get("messages", [])
    if not user_msg or not messages:
        return payload
    # Do not inject extra system context during multi-step tool call continuations
    if messages[-1].get("role") == "tool":
        return payload

    trimmed_msgs = trim_conversation_history(messages, MAX_LLM_HISTORY_MESSAGES)

    rag_context = ""
    try:
        from rag.rag_retriever import retrieve
        rag_res = retrieve(user_msg, top_k=3)
        if rag_res and "No relevant information found" not in rag_res:
            rag_context = rag_res
    except Exception as e:
        logger.warning(f"RAG retrieval skipped due to error: {e}")

    session = await check_db_session(chat_id)
    role_info = ""
    if session:
        role_info = f"Current authenticated user: {session.get('user_name')} (role: {session.get('user_role')}).\n"

    enriched = dict(payload)
    new_msgs = list(trimmed_msgs)
    if rag_context or role_info:
        extra_system = (
            "You are the OAMK AI Tutor Assistant.\n"
            f"{role_info}"
            "Answer clearly and concisely based on OAMK official documents below when relevant. "
            "Do not invent student grades or personal database records; direct the user to menu commands "
            "(e.g. 'students', 'risk', 'my courses', 'my progress') for live database queries.\n"
        )
        if rag_context:
            extra_system += f"\n--- OAMK Knowledge Base (RAG) ---\n{rag_context}\n--- End Knowledge Base ---"
        new_msgs.insert(0, {"role": "system", "content": extra_system})

    enriched["messages"] = new_msgs
    return enriched


async def forward_to_upstream_llm(payload: Dict[str, Any]) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    forward_payload = dict(payload)
    # Ensure JSON response (avoid SSE stream parse error if client requested stream=True)
    forward_payload["stream"] = False
    forward_payload.pop("stream_options", None)

    if LLM_PROVIDER == "deepseek":
        headers["Authorization"] = f"Bearer {DEEPSEEK_API_KEY}"
        url = "https://api.deepseek.com/chat/completions"
        if forward_payload.get("model") in ["deepseek/deepseek-v4.1-flash", "deepseek-v4.1-flash", "deepseek/deepseek-v4-flash", "deepseek-v4-flash"]:
            forward_payload["model"] = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    elif LLM_PROVIDER == "groq":
        headers["Authorization"] = f"Bearer {GROQ_API_KEY}"
        url = "https://api.groq.com/openai/v1/chat/completions"
        if "model" in forward_payload and "deepseek" in forward_payload["model"]:
            forward_payload["model"] = "llama-3.3-70b-versatile"
    elif LLM_PROVIDER == "openai":
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
        url = "https://api.openai.com/v1/chat/completions"
    else:
        headers["Authorization"] = f"Bearer {DEEPSEEK_API_KEY}"
        url = UPSTREAM_URL

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=forward_payload, headers=headers)
        if resp.status_code != 200:
            logger.error(f"Upstream error {resp.status_code}: {resp.text}")
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

def verify_router_api_key(request: Request):
    """
    Enforces Bearer token authentication between OpenClaw and Smart Router
    when ROUTER_API_KEY is configured in environment.
    """
    expected = os.getenv("ROUTER_API_KEY", ROUTER_API_KEY).strip()
    if not expected:
        return
    auth_header = request.headers.get("authorization", "")
    prefix = "bearer "
    if not auth_header.lower().startswith(prefix):
        logger.warning("Rejected unauthenticated request to Smart Router (missing Bearer token)")
        raise HTTPException(status_code=401, detail="Unauthorized: missing Bearer token")
    provided = auth_header[len(prefix):].strip()
    if not hmac.compare_digest(provided, expected):
        logger.warning("Rejected unauthenticated request to Smart Router (invalid Bearer token)")
        raise HTTPException(status_code=401, detail="Unauthorized: invalid Bearer token")


@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(request: Request):
    verify_router_api_key(request)
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    messages: List[Dict[str, Any]] = data.get("messages", [])
    if not messages:
        return format_openai_response("No messages provided.")

    user_msg = extract_clean_user_message(messages)
    chat_id = extract_chat_id(messages)

    fsm_state = get_fsm(chat_id)["state"]
    tail_summary = [
        (m.get("role"), len(_message_to_text(m.get("content", ""))), _message_to_text(m.get("content", ""))[:45].replace("\n", "\\n"))
        for m in messages[-4:]
    ]
    is_secret_step = fsm_state in ("AWAITING_PASSWORD", "CHG_PASS_CURRENT", "CHG_PASS_NEW")
    safe_msg = "***" if is_secret_step and user_msg else user_msg
    logger.info(f"Incoming message from chat_id={chat_id} (fsm={fsm_state}): '{safe_msg}' | tail={tail_summary}")

    ROUTER_METRICS["total_requests"] += 1
    deterministic_answer = await handle_deterministic_response(user_msg, chat_id, messages)
    if deterministic_answer is not None:
        ROUTER_METRICS["deterministic_handled"] += 1
        logger.info(f"-> Handled DETERMINISTICALLY (0 tokens): {deterministic_answer[:40]}...")
        return format_openai_response(deterministic_answer, model=data.get("model", "deepseek-v4-flash"))

    ROUTER_METRICS["llm_forwarded"] += 1
    logger.info("-> Forwarding to upstream LLM (Semantic/RAG query)...")
    enriched_data = await enrich_payload_with_rag(data, user_msg, chat_id)
    return await forward_to_upstream_llm(enriched_data)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "provider": LLM_PROVIDER,
        "auth_enabled": bool(os.getenv("ROUTER_API_KEY", ROUTER_API_KEY).strip()),
    }

@app.get("/metrics")
async def metrics(request: Request):
    verify_router_api_key(request)
    return get_metrics_snapshot()

if __name__ == "__main__":
    port = int(os.getenv("ROUTER_PORT", 8080))
    logger.info(f"Starting Smart Router on port {port}...")
    uvicorn.run("agents.smart_router:app", host="0.0.0.0", port=port, reload=False)
