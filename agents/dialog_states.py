import re
from database.db_connector import check_credentials_in_db

class UserState:
    UNAUTH = "UNAUTH"
    AWAITING_ROLE = "AWAITING_ROLE"
    AWAITING_EMAIL = "AWAITING_EMAIL"
    AWAITING_STUDENT_NUMBER = "AWAITING_STUDENT_NUMBER"
    AWAITING_PASSWORD = "AWAITING_PASSWORD"
    AUTHORIZED = "AUTHORIZED"

USER_SESSIONS = {}

def get_user_session(user_id: str):
    if user_id not in USER_SESSIONS:
        USER_SESSIONS[user_id] = {
            "state": UserState.UNAUTH,
            "role": None,
            "email": None,
            "student_number": None,
            "user_data": None
        }
    return USER_SESSIONS[user_id]

async def incoming_commands(user_id: str, text: str):
    clean_text = text.strip().lower()
    session = get_user_session(user_id)

    if clean_text in ["/start", "hi", "start"]:
        if session["state"] == UserState.AUTHORIZED:
            return "👋 You are already logged in! Ask a question about students or courses."

        session["state"] = UserState.AWAITING_ROLE
        USER_SESSIONS[user_id] = session
        return "🎓 Welcome to OAMK AI Tutor!\n\nWho are you?\n👨‍🏫 Write 'teacher'\n👨‍🎓 Write 'student'"

    if clean_text in ["/logout", "logout"]:
        USER_SESSIONS[user_id] = {
            "state": UserState.UNAUTH,
            "role": None,
            "email": None,
            "student_number": None,
            "user_data": None
        }
        return "🔒 You have been logged out. Send /start to login again."

    current_state = session.get("state", UserState.UNAUTH)

    if current_state == UserState.AWAITING_ROLE:
        if clean_text == "teacher":
            session["role"] = "teacher"
            session["state"] = UserState.AWAITING_EMAIL
            USER_SESSIONS[user_id] = session
            return "🎓 Login for (teacher) — Step 1 of 2\n\n📧 Enter your email:"
        elif clean_text == "student":
            session["role"] = "student"
            session["state"] = UserState.AWAITING_STUDENT_NUMBER
            USER_SESSIONS[user_id] = session
            return "🎓 Login for (student) — Step 1 of 2\n\n📧 Enter your student number (e.g., H100001):"
        else:
            return "❌ Please enter 'teacher' or 'student'."

    if current_state == UserState.AWAITING_EMAIL:
        if re.match(r"[^@]+@[^@]+\.[^@]+", text.strip()):
            session["email"] = text.strip()
            session["state"] = UserState.AWAITING_PASSWORD
            USER_SESSIONS[user_id] = session
            return "🎓 Sign In — Step 2 of 2\n\n🔑 Enter your password:"
        else:
            return "❌ Invalid email format. Please try again:"

    if current_state == UserState.AWAITING_STUDENT_NUMBER:
        if re.match(r"^H\d+$", text.strip(), re.IGNORECASE):
            session["student_number"] = text.strip().upper()
            session["state"] = UserState.AWAITING_PASSWORD
            USER_SESSIONS[user_id] = session
            return "🎓 Sign In — Step 2 of 2\n\n🔑 Enter your password:"
        else:
            return "❌ Invalid student number format (e.g., H100001). Please try again:"

    if current_state == UserState.AWAITING_PASSWORD:
        identifier = session.get("email") or session.get("student_number")
        role = session.get("role")
        password = text.strip()

        user_data = await check_credentials_in_db(identifier, password, role)

        if user_data:
            session["state"] = UserState.AUTHORIZED
            session["user_data"] = user_data
            USER_SESSIONS[user_id] = session
            return "✅ Authorization successful! You can now ask any questions regarding the study process."
        else:
            session["state"] = UserState.UNAUTH
            USER_SESSIONS[user_id] = session
            return "❌ Incorrect password or login. Enter /start to try again."

    if current_state == UserState.AUTHORIZED:
        return None

    return "🔒 Please log in first. Type /start to begin."