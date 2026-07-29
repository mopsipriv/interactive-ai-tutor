from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import os
import aiohttp
from dotenv import load_dotenv
from datetime import datetime
from database.db_connector import (
    get_all_teachers,
    get_students_by_teacher,
    get_pending_requests,
    get_student_enrollments
)
from rag.rag_retriever import retrieve
from agents.risk_utils import calculate_risk_level
load_dotenv() 

TEACHER_TELEGRAM_IDS = {
    1: os.getenv("MY_TELEGRAM_ID", "")
}

async def send_telegram_message(chat_id:str,text:str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url,json={"chat_id":chat_id,"text":text}) as response:
                if not response.ok:
                    print(f"Telegram error: {response.status}")
    except Exception as e:
        print(f"Failed to send message: {e}")

async def generate_brief_for_teacher(teacher_id:int,teacher_name:str):
    students = await get_students_by_teacher(teacher_id)
    if not students:
        return None
    for student in students:
        enrollments = await get_student_enrollments(student["idstudent"])
        credits_earned=0
        for enrollment in enrollments:
            if enrollment["status"] == "completed":
                credits_earned += enrollment["credit"]  
        student["credits_earned"] = credits_earned

        valid_from = student["valid_from"]
        if isinstance(valid_from, str):
            date_obj = datetime.strptime(valid_from, "%Y-%m-%d").date()
        else:
            date_obj = valid_from
        days_passed = (datetime.now().date() - date_obj).days
        student["credits_expected"] = (days_passed / 182) * 30
    at_risk = []
    for student in students:
        level, reason = calculate_risk_level(student)
        if level in ("critical", "warning"):
            at_risk.append((student["fname"] + " " + student["lname"], level, reason))
    
    pending = await get_pending_requests(teacher_id)
    
    month_name = datetime.now().strftime("%B")
    calendar_hint = retrieve(f"{month_name} tutoring actions checklist")
    
    brief = f"\n🌅 Weekly Brief for {teacher_name}\n"
    brief += f"{'━'*35}\n"
    
    if at_risk:
        brief += f"⚠️  At-risk students: {len(at_risk)}\n"
        for name, level, reason in at_risk:
            icon = "🔴" if level == "critical" else "🟡"
            brief += f"   {icon} {name} — {reason}\n"
    else:
        brief += "✅ All students on track\n"
    
    brief += "\n"
    
    if pending:
        brief += f"📥 Pending requests: {len(pending)}\n"
        for req in pending[:3]:
            brief += f"   • {req['fname']} {req['lname']} → {req['course_name']}\n"
    else:
        brief += "📥 No pending requests\n"
    
    brief += "\n"
    
    clean_hint = "\n".join(
        line for line in calendar_hint.split("\n") 
        if not line.startswith("[Source:")
    ).strip()
    sentences = clean_hint.split(".")[:2]
    hint = ". ".join(s.strip() for s in sentences if s.strip()) + "."
    brief += f"📅 {month_name} reminder: {hint}\n"
    
    brief += f"\nType 'risk' for details, 'requests' to review.\n"
    
    return brief

async def weekly_brief_job():
    print("🔄 Scheduler: weekly_brief_job triggered!")
    teachers = await get_all_teachers()
    print(f"🔄 Found {len(teachers)} teachers")
    for teacher in teachers:
        teacher_id = teacher["idteacher"]
        if teacher_id not in TEACHER_TELEGRAM_IDS:
            continue
        chat_id = TEACHER_TELEGRAM_IDS[teacher_id]
        brief = await generate_brief_for_teacher(teacher_id,teacher["fname"] + " " + teacher["lname"])
        if brief is None:
            print(f"No brief generated for teacher {teacher_id}")
            continue
            
        await send_telegram_message(chat_id, brief)
        