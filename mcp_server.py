from fastmcp import FastMCP
from typing import Optional

from database.db_connector import (
    get_all_students,
    get_student_by_course,
    get_all_courses,
    get_student_profile,
    enroll_student,
    update_grade,
    get_students_by_group,
    get_course_id_by_name,
    get_student_id_by_name,
    update_enrollment_status,
    get_student_from_db,
    get_courses_from_db,
    get_student_enrollments,
    get_teacher_query_history,
    log_teacher_query,
    get_curriculum,
    get_student_curriculum_progress,
    get_course_analytics,
    get_group_analytics,
    get_students_by_teacher,
    create_enrollment_request,
    get_pending_requests,
    approve_request,
    reject_request,
    get_student_requests,
    get_all_projects_with_requirements,
    save_telegram_session,
    get_telegram_session,
    delete_telegram_session,
    get_teacher_by_email,
    get_student_by_number,
    get_students_with_risk_data
)

from database.auth import verify_password
from agents.risk_utils import calculate_risk_level
from rag.rag_retriever import retrieve
from datetime import datetime


mcp = FastMCP("Tutor Server")

@mcp.tool
async def get_students_tool() -> list:
    """Get all students from the database"""
    students = await get_all_students()
    for s in students:
        s.pop("password_hash", None)
    return students

@mcp.tool
async def get_student_by_course_tool(course_name: str) -> list:
    """Get students enrolled in a specific course"""
    students = await get_student_by_course(course_name)
    for s in students:
        s.pop("password_hash",None)
    return students

@mcp.tool
async def get_all_courses_tool() -> list:
    """Get all courses from the database"""
    return await get_all_courses()

@mcp.tool
async def get_student_profile_tool(student_id:int) -> list:
    """Get full profile of a student including all courses"""
    students = await get_student_profile(student_id)
    for s in students:
        s.pop("password_hash", None)
    return students

@mcp.tool
async def enroll_student_tool(student_id:int, course_id:int) ->str:
    """Enroll a student into a course"""
    return await enroll_student(student_id,course_id)

@mcp.tool
async def update_grade_tool(student_id:int, course_id:int, grade:int) ->str:
    """Update a students grade in course"""
    return await update_grade(student_id,course_id,grade)

@mcp.tool
async def get_students_by_group_tool(group_code:str) ->list:
    """Get all students by their group"""
    students = await get_students_by_group(group_code)
    for s in students:
        s.pop("password_hash",None)
    return students

@mcp.tool
async def get_course_id_by_name_tool(course_name:str) -> Optional[int]:
    """Get course id by course name"""
    return await get_course_id_by_name(course_name)


@mcp.tool
async def get_student_id_by_name_tool(fname:str, lname:str) -> Optional[int]:
    """Get student id by first and last name"""
    return await get_student_id_by_name(fname, lname)

@mcp.tool
async def update_enrollment_status_tool(student_id:int,course_id:int,status:str) ->str:
    """Update enrollment status for a student in a course"""
    return await update_enrollment_status(student_id,course_id,status)

@mcp.tool
async def get_student_from_db_tool(student_id: int) -> dict | str:
    """Get a single student by their id"""
    student = await get_student_from_db(student_id)
    if isinstance(student, dict):
        student.pop("password_hash", None)
    return student

@mcp.tool
async def get_courses_from_db_tool(course_id: int) ->list:
    """Get a single course by its id"""
    return await get_courses_from_db(course_id)

@mcp.tool
async def get_student_enrollments_tool(student_id: int) ->list:
    """Get all enrollments for a student with course names"""
    return await get_student_enrollments(student_id)

@mcp.tool
async def log_teacher_query_tool(teacher_id:int, query_text:str, intent:str, result:str)-> str:
    """Log a teacher's query for history tracking"""
    return await log_teacher_query(teacher_id,query_text,intent,result)

@mcp.tool
async def get_teacher_query_history_tool(teacher_id:int,limit: int=10)->list:
    """Function getting history"""
    return await get_teacher_query_history(teacher_id,limit)

@mcp.tool
async def get_curriculum_tool(program_code: str)->list:
    """Get full curriculum for a program"""
    return await get_curriculum(program_code)

@mcp.tool
async def get_student_curriculum_progress_tool(student_id:int , program_code:str)->list:
    """Get student's progress through the curriculum"""
    return await get_student_curriculum_progress(student_id, program_code)

@mcp.tool
async def get_course_analytics_tool() -> list:
    """Get analytics for all courses - avg grade, completion rate"""
    return await get_course_analytics()

@mcp.tool
async def get_group_analytics_tool(group_code: str) -> dict:
    """Get analytics for a specific group - avg credits earned"""
    return await get_group_analytics(group_code)

@mcp.tool
async def get_students_by_teacher_tool(teacher_id: int) -> list:
    """Get students belonging to this teacher's groups"""
    students = await get_students_by_teacher(teacher_id)
    for s in students:
        s.pop("password_hash", None)
    return students

@mcp.tool
async def create_enrollment_request_tool(student_id:int,course_id:int)-> str:
    """Create enrollment request to the course"""
    return await create_enrollment_request(student_id,course_id)
    
@mcp.tool
async def get_pending_requests_tool(teacher_id:int)-> list:
    """Get pending requests courses"""
    return await get_pending_requests(teacher_id)
    
@mcp.tool
async def approve_request_tool(request_id:int, teacher_id:int)->str:
    """Approve request for course"""
    return await approve_request(request_id, teacher_id)
    
@mcp.tool
async def reject_request_tool(request_id:int, teacher_id:int)->str:
    """Reject request for course"""
    return await reject_request(request_id, teacher_id)

@mcp.tool
async def get_student_requests_tool(student_id: int) -> list:
    """Get all enrollment requests for a student"""
    return await get_student_requests(student_id)

@mcp.tool
async def get_all_projects_with_requirements_tool() -> list:
    """Get all projects with their required course IDs"""
    return await get_all_projects_with_requirements()

@mcp.tool
async def get_session_tool(chat_id: str) -> dict | None:
    """Get current Telegram session for chat_id"""
    clean_chat_id = chat_id.replace("telegram:", "")
    return await get_telegram_session(clean_chat_id)

@mcp.tool
async def login_teacher_tool(chat_id: str, email: str, password: str) -> str:
    """Login teacher by email and password"""
    clean_chat_id = chat_id.replace("telegram:", "")
    teacher = await get_teacher_by_email(email)
    if not teacher:
        return "Error: Teacher not found"
    if not verify_password(password, teacher["password_hash"]):
        return "Error: Wrong password"
    name = f"{teacher['fname']} {teacher['lname']}"
    await save_telegram_session(clean_chat_id, "teacher", teacher["idteacher"], name)
    return f"OK:{teacher['idteacher']}:{name}"

@mcp.tool
async def login_student_tool(chat_id: str, student_number: str, password: str) -> str:
    """Login student by student number and password"""
    clean_chat_id = chat_id.replace("telegram:", "")
    print(f"DEBUG: number='{student_number}' password='{password[:3]}***' chat='{chat_id}'")
    
    student = await get_student_by_number(student_number)
    if not student:
        return "Error: Student not found"
    if not verify_password(password, student["password_hash"]):
        return f"Error: Wrong password (got hash {student['password_hash'][:10]})"
    name = f"{student['fname']} {student['lname']}"
    await save_telegram_session(clean_chat_id, "student", student["idstudent"], name)
    return f"OK:{student['idstudent']}:{name}"


@mcp.tool
async def logout_tool(chat_id: str) -> str:
    """Logout from Telegram session"""
    clean_chat_id = chat_id.replace("telegram:", "")
    await delete_telegram_session(clean_chat_id)
    return "Logged out successfully"



@mcp.tool
async def get_risk_report_tool(teacher_id: int) -> str:
    """Generate risk report for all students of a teacher"""
    students = await get_students_with_risk_data(teacher_id)
    if not students:
        return "No students found."
    
    report = "=== Risk Report ===\n"
    for student in students:
        full_name = f"{student['fname']} {student['lname']}"
        credits_earned = student["credits_earned"]
        pct = int(credits_earned / 240 * 100)
        bar = "▓" * int(pct / 10) + "░" * (10 - int(pct / 10))
        
        level, reason = calculate_risk_level(student)
        
        if level == "critical":
            report += f"\n🔴 {full_name}: {bar} {credits_earned}/240 ({pct}%)\n   {reason}\n"
        elif level == "warning":
            report += f"\n🟡 {full_name}: {bar} {credits_earned}/240 ({pct}%)\n   {reason}\n"
        elif level == "info":
            report += f"\nℹ️  {full_name}: {bar} {credits_earned}/240 ({pct}%)\n   {reason}\n"
        else:
            report += f"\n🟢 {full_name}: {bar} {credits_earned}/240 ({pct}%)\n"
    
    return report

@mcp.tool
async def get_morning_brief_tool(teacher_id:int,teacher_name:str):
    """Get morning brief for teacher"""
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

@mcp.tool
async def get_student_plan_tool(student_id: int, program_code: str) -> str:
    """Get student study plan with progress indicators"""
    progress = await get_student_curriculum_progress(student_id, program_code)
    if not progress:
        return "No curriculum found for this program."
    
    plan = f"=== Study Plan: {program_code} ===\n"
    current_year = None
    
    for course in progress:
        if course["year_of_study"] != current_year:
            current_year = course["year_of_study"]
            plan += f"\nYear {current_year}:\n"
        
        status = course["enrollment_status"]
        if status == "completed":
            icon = "✅"
        elif status == "ongoing":
            icon = "🔄"
        elif status == "planned":
            icon = "📋"
        else:
            icon = "❌"
        
        grade = f" (grade: {course['grade']})" if course["grade"] else ""
        plan += f"  {icon} {course['course_name']} ({course['credit']}cr){grade}\n"
    
    return plan

if __name__=="__main__":
    mcp.run()