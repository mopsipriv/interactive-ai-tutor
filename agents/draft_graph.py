from langgraph.graph import StateGraph, START, END
import asyncio
from typing_extensions import TypedDict
from datetime import datetime
from typing import Annotated
import operator
import os
from dotenv import load_dotenv
from groq import Groq
from database.db_connector import get_student_enrollments, get_teacher_by_email, get_student_by_number, get_teacher_groups
from langchain_mcp_adapters.client import MultiServerMCPClient
import json
from agents.constants import TUTOR_CALENDAR, PROJECTS_DB
from agents.state import State
from database.auth import verify_password
from rag.rag_retriever import retrieve

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import warnings
warnings.filterwarnings("ignore")
import time

mcp_client = MultiServerMCPClient({
    "tutor_server": {
        "url": os.getenv("MCP_URL", "http://127.0.0.1:8000/sse"),
        "transport": "sse"
    }
})



load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
async def progress_agent(state: State):
    students = state.get("students", [])
    new_issue = ""
    for student in students:
        full_name = student["fname"] + " " + student["lname"]
        progress = student["credits_expected"] - student["credits_earned"]
        if progress > 15:
            new_issue += f"Student: {full_name} has critical situation. Student does not have enough credits.\n"
        elif progress > 5 and progress < 15:
            new_issue += f"Student: {full_name} has warning situation. Student does not have enough credits.\n"
        else:
            new_issue += f"Student: {full_name} has good situation. Student has enough credits.\n"
        
    current_text = state.get("bot_analyze_text", "")
    return {"bot_analyze_text": current_text + new_issue}


async def study_right_agent(state: State):
    students = state.get("students", [])
    new_issue = ""
    for student in students:
        full_name = student["fname"] + " " + student["lname"]
        today = datetime.now()
        date_obj = datetime.strptime(student["valid_until"], "%Y-%m-%d").date()
        left_study_right = (date_obj - today.date()).days / 30
        if left_study_right < 6:
            new_issue += f"Student: {full_name} has critical situation (study right)\n"
        elif left_study_right < 12:
            new_issue += f"Student: {full_name} has warning situation (study right)\n"
        else:
            new_issue += f"Student: {full_name} has study right\n"
            
    current_text = state.get("bot_analyze_text", "")
    return {"bot_analyze_text": current_text + new_issue}

async def recommendation_agent(state: State):
    all_issues = state.get("bot_analyze_text","")
    calendar = state.get("calendar_info", "")
    response = client.chat.completions.create(
        messages=[
                {"role": "system", "content": "You are an AI assistant helping a tutor teacher at a university. You receive automated analysis of student progress and study rights. Write a clear and concise summary message for the teacher. Use bullet points for each student with an issue. Maximum 150 words. Do not use formal letter format."},
                {"role": "user", "content": all_issues + "\n" + calendar}
        ],
        model="llama-3.3-70b-versatile",
        max_completion_tokens=1024,
    )
    result_text = response.choices[0].message.content
    return {"final_text": result_text}


async def status_agent(state: State):
    current_text = state.get("bot_analyze_text","")
    if "critical" in current_text or "warning" in current_text or "Not found" in current_text:
        return{"is_allowed":False}
    else:
        return {"is_allowed": True}
    

async def analytics_agent(state: State):
    allowed = state.get("is_allowed", True)
    if allowed:
        verdict = "All checks passed. The student is cleared for enrollment.\n"
    else:
        verdict = "Enrollment Blocked. Student must contact the coordinator.\n"
        
    current_text = state.get("bot_analyze_text", "")
    return {"bot_analyze_text": current_text + verdict}


async def fetch_students_agent(state: State):
    filter_name = state.get("filter_name", "")
    tools = await mcp_client.get_tools()
    teacher_id = state.get("teacher_id", 0)
    if teacher_id:
        get_students_tool = next(t for t in tools if t.name == "get_students_by_teacher_tool")
        raw_result = await get_students_tool.ainvoke({"teacher_id": teacher_id})
    else:
        get_students_tool = next(t for t in tools if t.name == "get_students_tool")
        raw_result = await get_students_tool.ainvoke({})
    all_students = json.loads(raw_result[0]["text"])
    
    if filter_name != "":
        all_students = [s for s in all_students if (s["fname"] + " " + s["lname"]) == filter_name]
    
    for student in all_students:
        enrollments = await get_student_enrollments(student["idstudent"])
        completed_credits = 0
        completed_courses = []
        for enrollment in enrollments:
            if enrollment["status"] == "completed":
                completed_courses.append(enrollment["idcourse"])
                completed_credits += enrollment["credit"]
        student["completed_courses"] = completed_courses
        student["credits_earned"] = completed_credits
        
        today = datetime.now()
        date_obj = datetime.strptime(student["valid_from"], "%Y-%m-%d").date()
        days_passed = (today.date() - date_obj).days
        semesters = days_passed / 182
        total_credits = semesters * 30
        student["credits_expected"] = total_credits

    return {"students": all_students}

    
async def calendar_agent(state: State):
    today= datetime.now()
    month=today.month
    calendar_info = TUTOR_CALENDAR[month]
    return {"calendar_info": calendar_info}


async def communication_agent(state: State):
    current_text=state.get("bot_analyze_text","")
    response = client.chat.completions.create(
        messages=[
                {"role": "system", "content": "You are an AI assistant at a university. You receive student analysis data. Write a short personal message directly to each student who has a problem with credits or study right. Address them by name.Add information about problem. Maximum 100 words total."},
                {"role": "user", "content": current_text + "\n"}
        ],
        model="llama-3.3-70b-versatile",
        max_completion_tokens=1024,
    )
    result_text = response.choices[0].message.content
    return {"student_messages": result_text}


async def eligibility_agent(state: State):
    new_issue= ""
    students = state.get("students",[])
    for student in students:
        for project in PROJECTS_DB.values():
            eligible = True
            required = project["required_courses"]
            completed = student["completed_courses"]
            for course in required:
                if course not in completed:
                    eligible = False
            full_name = student["fname"] + " " + student["lname"]
            project_name = project["project_name"]
            if eligible:
                new_issue += f"{full_name} is eligible for {project_name}\n"
            else:
                new_issue += f"{full_name} is not eligible for {project_name}\n"

    return {"eligibility_report": new_issue}


async def course_student_agent(state: State):
    new_issue=""
    filter_course = state.get("filter_course","")
    tools = await mcp_client.get_tools()
    if filter_course!="":
        get_students_course_tool = next(t for t in tools if t.name == "get_student_by_course_tool")
        raw_students_course = await get_students_course_tool.ainvoke({"course_name":filter_course})
        if not raw_students_course:
            return {"course_report": f"Error: Course '{filter_course}' not found."}
        students = json.loads(raw_students_course[0]["text"])

        if not students:
            return {"course_report": f"No students found on course '{filter_course}'."}

        new_issue = f"Students on course {filter_course}:\n"
        for student in students:
            new_issue += f"- {student['fname']} {student['lname']}: {student['status']}, grade: {student['grade']}\n"

    return {"course_report": new_issue}


async def enroll_agent(state: State):
    enroll_student_name=state.get("enroll_student_name","")
    enroll_course_name=state.get("enroll_course_name","")
    if enroll_student_name == "" or enroll_course_name == "":
        return {"enroll_result": ""}
    parts = enroll_student_name.split()
    if len(parts) < 2:
        return {"enroll_result": "Error: Student not found"}
    fname,lname = enroll_student_name.split()[:2]
    tools= await mcp_client.get_tools()
    get_student_id_tool = next(t for t in tools if t.name == "get_student_id_by_name_tool")
    raw_student_id = await get_student_id_tool.ainvoke({"fname":fname, "lname":lname})
    if not raw_student_id:
        return {"enroll_result": "Error: student not found"}
    idstudent = json.loads(raw_student_id[0]["text"])

    get_course_id_tool = next(t for t in tools if t.name == "get_course_id_by_name_tool")
    raw_course_id = await get_course_id_tool.ainvoke({"course_name": enroll_course_name})
    if not raw_course_id:
        return {"enroll_result": "Error: course not found"}
    idcourse = json.loads(raw_course_id[0]["text"])

    if idstudent is None:
        return {"enroll_result": "Error: student not found"}
    if idcourse is None:
        return {"enroll_result": "Error: course not found"}

    enroll_tool = next(t for t in tools if t.name == "enroll_student_tool")
    raw_enroll = await enroll_tool.ainvoke({"student_id":idstudent, "course_id":idcourse})
    enroll = raw_enroll[0]["text"]    
    return {"enroll_result": enroll}

async def course_list_agent(state: State):
    new_issue=""
    courses=state.get("show_courses","")
    tools= await mcp_client.get_tools()
    if courses is True:
        all_courses_tool = next(t for t in tools if t.name == "get_all_courses_tool")
        raw_all_courses = await all_courses_tool.ainvoke({})
        all_courses = json.loads(raw_all_courses[0]["text"])
        for course in all_courses:
            new_issue += f"- {course['course_code']}: {course['course_name']} ({course['credit']} credits)\n"
    return {"courses_list": new_issue}


async def grade_agent(state: State):
    grade_student_name=state.get("grade_student_name","")
    grade_course_name=state.get("grade_course_name","")
    grade_value= state.get("grade_value","")
    if grade_student_name == "" or grade_course_name == "" or grade_value == "":
        return {"grade_result": ""}
    parts = grade_student_name.split()
    if len(parts) < 2:
        return {"grade_result": "Error: Student or Course not found"}
    tools= await mcp_client.get_tools()
    fname,lname = grade_student_name.split()[:2]
    
    get_student_id_tool = next(t for t in tools if t.name == "get_student_id_by_name_tool")
    raw_student_id = await get_student_id_tool.ainvoke({"fname":fname, "lname":lname})
    if not raw_student_id:
        return {"grade_result": "Error: student not found"}
    idstudent = json.loads(raw_student_id[0]["text"])
    
    get_course_id_tool = next(t for t in tools if t.name == "get_course_id_by_name_tool")
    raw_course_id = await get_course_id_tool.ainvoke({"course_name":grade_course_name})
    if not raw_course_id:
        return {"grade_result": "Error: course not found"}
    idcourse = json.loads(raw_course_id[0]["text"])
    
    if idstudent is None:
        return {"grade_result": "Error: student not found"}
    if idcourse is None:
        return {"grade_result": "Error: course not found"}
    
    update_grade_tool = next(t for t in tools if t.name== "update_grade_tool")
    raw_grade_result = await update_grade_tool.ainvoke({"student_id":idstudent, "course_id":idcourse, "grade": grade_value})
    grade_result = raw_grade_result[0]["text"]
    
    return {"grade_result": grade_result}


async def profile_agent(state: State):
    new_issue=""
    filter_name = state.get("filter_name","")
    if filter_name == "":
        return {"student_profile": ""}
    parts = filter_name.split()
    if len(parts) < 2:
        return {"student_profile": "Error: please provide full name (first and last name)"}
    tools = await mcp_client.get_tools()
    fname,lname = filter_name.split()[:2]
   
    get_student_id_tool = next(t for t in tools if t.name == "get_student_id_by_name_tool")
    raw_student_id = await get_student_id_tool.ainvoke({"fname":fname,"lname":lname})
    if not raw_student_id:
        return {"student_profile": f"Error: Student '{filter_name}' not found."}
    idstudent = json.loads(raw_student_id[0]["text"])

    get_profile_tool = next(t for t in tools if t.name == "get_student_profile_tool")
    raw_profile = await get_profile_tool.ainvoke({"student_id":idstudent})
    student_profile = json.loads(raw_profile[0]["text"])

    if student_profile:
        first = student_profile[0] 
        new_issue = f"Student: {first['fname']} {first['lname']}\n"
        new_issue += f"Email: {first['email']}\n"
        new_issue += f"Study right: {first['valid_until']}\n"
        new_issue += "Courses:\n"
        for row in student_profile:
            new_issue += f"- {row['course_name']}: {row['status']}, grade: {row['grade']}\n"
    return {"student_profile":new_issue}


async def status_update_agent(state: State):
    status_student_name = state.get("status_student_name","")
    status_course_name= state.get("status_course_name","")
    status_value = state.get("status_value","")
    if status_student_name == "" or status_course_name == "" or status_value == "":
        return {"status_update_result": ""}
    parts = status_student_name.split()
    if len(parts) < 2:
        return {"status_update_result": "Error: Student or Course not found"}
    
    tools = await mcp_client.get_tools()
    
    fname,lname = status_student_name.split()[:2]
    get_student_id_tool = next(t for t in tools if t.name == "get_student_id_by_name_tool")
    raw_student_id = await get_student_id_tool.ainvoke({"fname":fname,"lname":lname})
    if not raw_student_id:
        return {"status_update_result": "Error: student not found"}
    idstudent = json.loads(raw_student_id[0]["text"])

    get_course_id_tool = next(t for t in tools if t.name == "get_course_id_by_name_tool")
    raw_course_id = await get_course_id_tool.ainvoke({"course_name":status_course_name})
    if not raw_course_id:
        return {"status_update_result": "Error: course not found"}
    idcourse = json.loads(raw_course_id[0]["text"])
    
    if idstudent is None:
        return {"status_update_result": "Error: student not found"}
    if idcourse is None:
        return {"status_update_result": "Error: course not found"}
    
    status_update_tool = next(t for t in tools if t.name== "update_enrollment_status_tool")
    raw_status_update= await status_update_tool.ainvoke({"student_id":idstudent, "course_id":idcourse, "status": status_value})
    status_update_result = raw_status_update[0]["text"]
    return {"status_update_result": status_update_result}


async def risk_report_agent(state: State):
    new_issue = "=== Risk Report ===\n"
    students = state.get("students",[])
    for student in students:
        full_name = student["fname"] + " " + student["lname"]
        progress = student["credits_expected"] - student["credits_earned"]
        today = datetime.now()
        date_obj = datetime.strptime(student["valid_until"], "%Y-%m-%d").date()
        left_study_right = (date_obj - today.date()).days / 30
        issues = []
        if progress > 15:
            issues.append("🔴Critical credits!")
        elif progress > 5:
            issues.append("🟡Warning credits!")

        if left_study_right < 6:
            issues.append("🔴Study right expires soon")
        elif left_study_right < 12:
            issues.append("🟡Study right expires during year")

        if issues:
            new_issue += f"{full_name}:\n"
            for issue in issues:
                new_issue += f"  {issue}\n"
        else:
            new_issue += f"🟢{full_name}: Everything is good\n"
    
    return {"risk_report": new_issue}


async def group_report_agent(state:State):
    new_issue=""
    filter_group = state.get("filter_group","")
    if filter_group == "":
        return {"group_report": ""}
    tools = await mcp_client.get_tools()
    get_students_group_tool = next(t for t in tools if t.name == "get_students_by_group_tool")
    raw_students_group = await get_students_group_tool.ainvoke({"group_code":filter_group})
    if not raw_students_group:
        return {"group_report": f"Error: Group '{filter_group}' not found."}
    students = json.loads(raw_students_group[0]["text"])

    if not students:
        return {"group_report": f"Error: No students found in group '{filter_group}'."}

    new_issue = f"Students in group {filter_group}:\n"
    for student in students:
        new_issue += f"- {student['fname']} {student['lname']} ({student['student_number']})\n"

    return {"group_report": new_issue}



async def bulk_enroll_agent(state: State):
    bulk_group_code = state.get("bulk_group_code", "")
    bulk_course_code = state.get("bulk_course_name", "")
    if bulk_group_code == "" or bulk_course_code == "":
        return {"bulk_enroll_result": ""}
    tools = await mcp_client.get_tools()
    
    get_students_group_tool = next(t for t in tools if t.name == "get_students_by_group_tool")
    raw_students_group = await get_students_group_tool.ainvoke({"group_code":bulk_group_code})
    if not raw_students_group:
        return {"bulk_enroll_result": f"Error: Group '{bulk_group_code}' not found."}
    students = json.loads(raw_students_group[0]["text"])
    
    if not students:
        return {"bulk_enroll_result": f"Error: No students found in group '{bulk_group_code}'."}
    
    get_course_id_tool = next(t for t in tools if t.name == "get_course_id_by_name_tool")
    raw_course_id = await get_course_id_tool.ainvoke({"course_name":bulk_course_code})
    if not raw_course_id:
        return {"bulk_enroll_result": f"Error: Course '{bulk_course_code}' not found."}
    idcourse = json.loads(raw_course_id[0]["text"])
    
    if idcourse is None:
        return {"bulk_enroll_result": f"Error: Course '{bulk_course_code}' not found."}
    
    success_count = 0
    student_enroll_tool = next(t for t in tools if t.name == "enroll_student_tool")
    for student in students:
        raw_student_enroll = await student_enroll_tool.ainvoke({"student_id":student["idstudent"],"course_id":idcourse})
        result = raw_student_enroll[0]["text"]
        
        if "successfully" in result:
            success_count += 1
    new_issue = f"Enrolled {success_count} out of {len(students)} students"
    return {"bulk_enroll_result": new_issue}


async def student_recommendation_agent(state: State):
    profile = state.get("student_profile", "")
    eligibility = state.get("eligibility_report", "")
    progress = state.get("bot_analyze_text", "")
    
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a friendly academic advisor AI. You receive a student's actual course data, eligibility status, and progress info. Reference SPECIFIC courses, grades, and situations by name from the data provided. Give concrete, actionable next steps (e.g. 'finish course X to unlock project Y').  Be encouraging but specific.  Maximum 100 words."},
            {"role": "user", "content": f"Student profile:\n{profile}\n\nProject eligibility:\n{eligibility}\n\nProgress status:\n{progress}"}
        ],
        model="llama-3.3-70b-versatile",
        max_completion_tokens=512,
    )
    return {"student_recommendation": response.choices[0].message.content}

async def curriculum_agent(state: State):
    filter_program = state.get("filter_program", "")
    if filter_program == "":
        return {"curriculum_info": ""}
    
    tools = await mcp_client.get_tools()

    curriculum_tool = next(t for t in tools if t.name == "get_curriculum_tool")
    raw_curriculum = await curriculum_tool.ainvoke({"program_code":filter_program})
    if not raw_curriculum:
        return {"curriculum_info": f"Error: Program '{filter_program}' not found."}
    curriculum = json.loads(raw_curriculum[0]["text"])
    new_issue = f"=== Curriculum: {filter_program} ===\n"
    current_semester = None
    for course in curriculum:
        if course["semester"] != current_semester:
            current_semester = course["semester"]
            new_issue += f"\nSemester {current_semester}:\n"
        new_issue += f"  - {course['course_name']} ({course['credit']}cr) [{course['course_type']}]\n"
    
    return {"curriculum_info": new_issue}


async def student_plan_agent(state: State):
    filter_name = state.get("filter_name","")
    filter_program = state.get("filter_program","")
    if filter_name == "" or filter_program == "" :
        return {"student_plan":""}
    
    tools = await mcp_client.get_tools()

    parts = filter_name.split()
    if len(parts) < 2:
        return {"student_plan": "Error: please provide full name"}
    fname, lname = parts[:2]
    get_student_id_tool = next(t for t in tools if t.name == "get_student_id_by_name_tool")
    raw_student_id = await get_student_id_tool.ainvoke({"fname":fname,"lname":lname})
    if not raw_student_id:
        return {"student_plan": "Error: student not found"}
    idstudent = json.loads(raw_student_id[0]["text"])

    get_student_by_curriculum_tool = next(t for t in tools if t.name == "get_student_curriculum_progress_tool")
    raw_student_curriculum = await get_student_by_curriculum_tool.ainvoke({"student_id": idstudent, "program_code": filter_program})
    if not raw_student_curriculum:
        return {"student_plan": f"Error: No curriculum found for program '{filter_program}'."}
    progress = json.loads(raw_student_curriculum[0]["text"])

    new_issue = f"=== Study Plan: {filter_name} ({filter_program}) ===\n"
    current_semester = None
    for course in progress:
        if course["semester"] != current_semester:
            current_semester = course["semester"]
            new_issue += f"\nSemester {current_semester}:\n"
        
        status = course["enrollment_status"]
        if status == "completed":
            icon = "✅"
            detail = f"completed, grade: {course['grade']}"
        elif status == "ongoing":
            icon = "🔄"
            detail = "ongoing"
        elif status == "planned":
            icon = "📋"
            detail = "planned"
        else:
            icon = "❌"
            detail = "not enrolled yet"
        
        new_issue += f"  {icon} {course['course_name']} ({course['credit']}cr) - {detail}\n"
    
    return {"student_plan": new_issue}


async def analytics_report_agent(state: State):
    filter_analytics = state.get("filter_analytics","")
    if filter_analytics == "":
        return {"analytics_report": ""}
    
    tools = await mcp_client.get_tools()

    if filter_analytics== "courses":
        get_analytics_tool = next(t for t in tools if t.name == "get_course_analytics_tool")
        raw_analytics = await get_analytics_tool.ainvoke({})
        if not raw_analytics:
            return {"analytics_report": "Error: no analytics data found."}
        analytics = json.loads(raw_analytics[0]["text"])

        new_issue = "=== Course Analytics ===\n"
        for course in analytics:
            total = course["total_students"]
            completed = int(course["completed_count"])
            avg = round(float(course["avg_grade"]), 1) if course["avg_grade"] else "N/A"
            percent = round(completed / total * 100) if total > 0 else 0
            new_issue += f"{course['course_code']} {course['course_name']}:\n"
            new_issue += f"  Students: {total} | Avg grade: {avg} | Completed: {completed}/{total} ({percent}%)\n"
    
        return {"analytics_report": new_issue}

    elif filter_analytics == "group":
        filter_group = state.get("filter_group", "")
        if filter_group == "":
            return {"analytics_report": "Error: group code not provided."}
        
        get_gr_analytics_tool = next(t for t in tools if t.name == "get_group_analytics_tool")
        raw_gr_analytics = await get_gr_analytics_tool.ainvoke({"group_code": filter_group})
        if not raw_gr_analytics:
            return {"analytics_report": f"Error: Group '{filter_group}' not found."}
        analytics = json.loads(raw_gr_analytics[0]["text"])
        
        new_issue = f"=== Group Analytics: {filter_group} ===\n"
        new_issue += f"Total students: {analytics['total_students']}\n"
        new_issue += f"Average credits earned: {analytics['avg_credits_earned']}\n"
        
        return {"analytics_report": new_issue}
    

async def rag_agent(state: State):
    rag_query = state.get("rag_query", "")
    if rag_query == "":
        return {"rag_answer": ""}
    
    context = retrieve(rag_query)
    
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": """You are a helpful academic advisor for a Finnish university tutoring system. 
            Answer questions using ONLY the provided context below - do not use outside knowledge.
            If the context contains relevant information, give a clear, complete answer with specific details (course names, dates, numbers).
            If the context is truly unrelated to the question, say "I don't have specific information about that in my knowledge base, but here's what I found that might be related: [briefly mention what WAS found]"
            Keep answers concise but complete - aim for 2-4 sentences unless the question requires a list."""},
            {"role": "user", "content": f"Context from tutoring documents:\n{context}\n\nQuestion: {rag_query}"}
        ],
        model="llama-3.3-70b-versatile",
        max_completion_tokens=512,
    )
    return {"rag_answer": response.choices[0].message.content}
    
async def run_agent_with_timer(app, state):
    print("Processing...", end="", flush=True)
    start = time.time()
    result = await app.ainvoke(state)
    elapsed = round(time.time() - start, 1)
    print(f" done ({elapsed}s)")
    return result

async def request_course_agent(state: State):
    request_course = state.get("request_course_name","")
    filter_name = state.get("filter_name","")
    if request_course == "" or filter_name == "":
        return {"request_result":""}

    tools = await mcp_client.get_tools()

    parts = filter_name.split()
    if len(parts) < 2:
        return {"request_result": "Error: please provide full name"}
    fname, lname = parts[:2]
    get_student_id_tool = next(t for t in tools if t.name == "get_student_id_by_name_tool")
    raw_student_id = await get_student_id_tool.ainvoke({"fname":fname,"lname":lname})
    if not raw_student_id:
        return {"request_result": "Error: student not found"}
    idstudent = json.loads(raw_student_id[0]["text"])

    get_course_id_tool = next(t for t in tools if t.name == "get_course_id_by_name_tool")
    raw_course_id = await get_course_id_tool.ainvoke({"course_name":request_course})
    if not raw_course_id:
        return {"request_result": f"Error: Course '{request_course}' not found."}
    idcourse = json.loads(raw_course_id[0]["text"])

    create_enrollment_tool = next(t for t in tools if t.name == "create_enrollment_request_tool")
    raw_create_enrollment = await create_enrollment_tool.ainvoke({"student_id": idstudent, "course_id": idcourse})
    if not raw_create_enrollment:
        return {"request_result":"Error creating request"}
    result_text = raw_create_enrollment[0]["text"]

    return {"request_result": result_text}


async def view_requests_agent(state:State):
    teacher_id = state.get("teacher_id",0)
    if not teacher_id:
        return {"pending_requests_list": "Error: Teacher ID is missing"}
    
    tools = await mcp_client.get_tools()
    get_requests_tool = next(t for t in tools if t.name == "get_pending_requests_tool")
    raw_requests = await get_requests_tool.ainvoke({"teacher_id":teacher_id})
    if not raw_requests:
        return {"pending_requests_list": "No pending requests found."}
    requests = json.loads(raw_requests[0]["text"])
    if not requests:
        return {"pending_requests_list": "No pending enrollment requests found."}


    lines = ["=== Pending Enrollment Requests ==="]
    for r in requests:
        req_date = str(r["requested_at"]).split("T")[0]
        lines.append(
            f"[Request ID: {r['idrequest']}] {r['fname']} {r['lname']} → {r['course_name']} ({r['course_code']}) | {req_date}"
        )
    lines.append("\nTo approve/reject: use command 'approve' and enter the Request ID shown above.")

    return {"pending_requests_list": "\n".join(lines)}
    

async def handle_request_agent(state:State):
    request_id = state.get("request_id","")
    request_action = state.get("request_action","")
    if request_id == "" or request_action == "":
        return {"request_action_result":""}

    tools = await mcp_client.get_tools()

    if request_action == "approve":
        approve_tool = next(t for t in tools if t.name == "approve_request_tool")
        raw_approve = await approve_tool.ainvoke({"request_id":request_id})
        if not raw_approve:
            return {"request_action_result":"Error. Can not approve"}
        approve = raw_approve[0]["text"]
        return {"request_action_result": approve}

    if request_action == "reject":
        reject_tool = next(t for t in tools if t.name == "reject_request_tool")
        raw_reject = await reject_tool.ainvoke({"request_id": request_id})
        if not raw_reject:
            return {"request_action_result": "Error. Can not reject"}
        reject = raw_reject[0]["text"]
        return {"request_action_result": reject}

    return {"request_action_result": "Error: Unknown action"}

async def my_requests_agent(state:State):
    filter_name = state.get("filter_name","")
    if filter_name == "":
        return {"my_requests_list": ""}

    tools = await mcp_client.get_tools()

    parts = filter_name.split()
    if len(parts) < 2:
        return {"my_requests_list": "Error: please provide full name"}
    fname, lname = parts[:2]
    get_student_id_tool = next(t for t in tools if t.name == "get_student_id_by_name_tool")
    raw_student_id = await get_student_id_tool.ainvoke({"fname":fname,"lname":lname})
    if not raw_student_id:
        return {"my_requests_list": "Error: student not found"}
    idstudent = json.loads(raw_student_id[0]["text"])

    student_requests_tool = next(t for t in tools if t.name == "get_student_requests_tool")
    raw_student_requests= await student_requests_tool.ainvoke({"student_id":idstudent})
    if not raw_student_requests:
        return {"my_requests_list": "Error: Request list is not available"}
    student_requests = json.loads(raw_student_requests[0]["text"])

    if not student_requests:
        return {"my_requests_list": "You have no enrollment requests yet."}
    
    lines = ["=== Your Enrollment Requests ==="]
    for r in student_requests:
        if r["status"] == "approved":
            icon = "✅"
        elif r["status"] == "rejected":
            icon = "❌"
        else:
            icon = "⏳"
        
        req_date = str(r["requested_at"]).split("T")[0]
        lines.append(f"{icon} {r['course_name']} ({r['course_code']}) - {r['status']} | requested {req_date}")
    
    return {"my_requests_list": "\n".join(lines)}



def router_by_command(state: State):
    cmd = state.get("command", "")
    role = state.get("user_role", "student")
    
    teacher_commands = ["profile", "course", "enroll", "grade", "status", "group", "bulk", "courses", "curriculum", "analytics", "risk", "ask", "help", "export", "requests", "approve"]
    student_commands = ["profile", "eligibility", "recommend", "courses", "plan", "ask", "help","request", "my_requests"]
    
    if role == "student" and cmd not in student_commands:
        return END
    if role == "teacher" and cmd not in teacher_commands:
        return END

    routes = {
        "profile": "profile_node",
        "course": "course_students_node",
        "enroll": "enroll_node",
        "grade": "grade_node",
        "status": "update_status_node",
        "group": "group_report_node",
        "bulk": "bulk_enroll_node",
        "courses": "course_list_node",
        "curriculum": "curriculum_node",
        "analytics": "analytics_report_node",
        "risk": "fetch_node",
        "eligibility": "fetch_node",
        "recommend": "fetch_node",
        "plan": "student_plan_node",
        "ask": "rag_node",
        "request": "request_course_node",
        "requests": "view_requests_node",
        "approve": "handle_request_node",
        "my_requests": "my_requests_node"
    }
    
    result = routes.get(cmd, END)
    return result


def route_after_status(state: State):
    cmd = state.get("command", "")
    if cmd == "recommend":
        return "go_to_profile"
    if cmd == "eligibility":
        return "go_to_end"
    if cmd == "risk":
        return "go_to_end"
    
    allowed = state.get("is_allowed", True)
    if not allowed:
        return "go_to_analytics"
    else:
        return "go_to_end"

graph = StateGraph(State)

# adding nodes
graph.add_node("fetch_node", fetch_students_agent)
graph.add_node("progress_node", progress_agent)
graph.add_node("study_right_node", study_right_agent)
graph.add_node("eligibility_node", eligibility_agent)
graph.add_node("calendar_node", calendar_agent)
graph.add_node("risk_report_node", risk_report_agent)
graph.add_node("status_node", status_agent)
graph.add_node("analytics_node", analytics_agent)
graph.add_node("recommendation_node", recommendation_agent)
graph.add_node("communication_node", communication_agent)
graph.add_node("course_students_node", course_student_agent)
graph.add_node("enroll_node", enroll_agent)
graph.add_node("grade_node", grade_agent)
graph.add_node("update_status_node", status_update_agent)
graph.add_node("group_report_node", group_report_agent)
graph.add_node("bulk_enroll_node", bulk_enroll_agent)
graph.add_node("course_list_node", course_list_agent)
graph.add_node("curriculum_node", curriculum_agent)
graph.add_node("analytics_report_node", analytics_report_agent)
graph.add_node("profile_node", profile_agent)
graph.add_node("student_recommendation_node", student_recommendation_agent)
graph.add_node("student_plan_node", student_plan_agent)
graph.add_node("rag_node", rag_agent)
graph.add_node("request_course_node", request_course_agent)
graph.add_node("view_requests_node", view_requests_agent)
graph.add_node("handle_request_node", handle_request_agent)
graph.add_node("my_requests_node", my_requests_agent)

# start
graph.add_conditional_edges(START, router_by_command)

# simple nodes
simple_nodes = [
    "enroll_node", "course_list_node", "grade_node",
    "update_status_node", "group_report_node", "bulk_enroll_node",
    "curriculum_node", "analytics_report_node", "student_plan_node",
    "course_students_node", "rag_node", "request_course_node",
    "view_requests_node", "handle_request_node", "my_requests_node"
]
for node in simple_nodes:
    graph.add_edge(node, END)

# profile/recommendation
graph.add_edge("profile_node", "student_recommendation_node")
graph.add_edge("student_recommendation_node", END)

# risk/eligibility/recommend
graph.add_edge("fetch_node", "progress_node")
graph.add_edge("progress_node", "study_right_node")
graph.add_edge("study_right_node", "eligibility_node")
graph.add_edge("eligibility_node", "calendar_node")
graph.add_edge("calendar_node", "risk_report_node")
graph.add_edge("risk_report_node", "status_node")

graph.add_conditional_edges(
    "status_node",
    route_after_status,
    {
        "go_to_analytics": "analytics_node",
        "go_to_profile": "profile_node",
        "go_to_end": END
    }
)
graph.add_edge("analytics_node", "recommendation_node")
graph.add_edge("analytics_node", "communication_node")
graph.add_edge("recommendation_node", END)
graph.add_edge("communication_node", END)

app = graph.compile()

async def main():
    print("""
╔═══════════════════════════════════════════╗
║         AI Tutor Assistant v1.0           ║
║     Peppi-like Academic Records System    ║
╚═══════════════════════════════════════════╝
""")
    role = input("Login as: (teacher / student): ")

    if role == "teacher":
        while True:
            email = input("Enter your email: ").strip()
            if "@" in email and "." in email:
                break
            print("Error: invalid email format. Please try again.")

        password = input("Enter your password: ")
        teacher = await get_teacher_by_email(email)
        if teacher is None:
            print("Access denied. Teacher not found")
            return
        if not verify_password(password, teacher["password_hash"]):
            print("Access denied. Wrong password")
            return
        print(f"Welcome, {teacher['fname']} {teacher['lname']}!")

        base_state = {
            "user_role": "teacher",
            "students": [], 
            "student_data": "", 
            "course_id": 0, 
            "course_data": "",
            "enrollments": [], 
            "is_allowed": True, 
            "bot_analyze_text": "",
            "final_text": "", 
            "calendar_info": "", 
            "student_messages": "",
            "filter_name": "", 
            "filter_course": "", 
            "enroll_course_name": "",
            "enroll_student_name": "", 
            "enroll_result": "", 
            "show_courses": False,
            "courses_list": "", 
            "grade_student_name": "",
            "grade_course_name": "",
            "grade_value": "", 
            "grade_result": "", 
            "student_profile": "",
            "status_student_name": "", 
            "status_course_name": "", 
            "status_value": "",
            "status_update_result": "", 
            "risk_report": "", 
            "group_report": "",
            "filter_group": "", 
            "bulk_group_code": "",
            "bulk_course_name": "",
            "bulk_enroll_result": "", 
            "eligibility_report": "",
            "course_report": "",
            "filter_program": "",
            "curriculum_info": "",
            "student_plan": "",
            "filter_analytics": "",
            "analytics_report": "",
            "command":"",
            "rag_query": "",
            "rag_answer": "",
            "teacher_id": teacher["idteacher"],
            "request_course_name":"",
            "request_result": "",
            "pending_requests_list":"",
            "request_id": 0,
            "request_action": "",
            "request_action_result": ""
        }

        quick_state = base_state.copy()
        quick_state["command"] = "risk"
        quick_result = await app.ainvoke(quick_state)
        risk_text = quick_result.get("risk_report", "")
        critical_count = risk_text.count("🔴")
        if critical_count > 0:
            print(f"⚠️  {critical_count} student(s) currently at risk. Type 'risk' to see details.")

        while True:
            command = input("\nCommand (profile/course/enroll/grade/status/group/bulk/courses/risk/history/curriculum/analytics/ask/help/export/me/requests/approve/exit): ")

            if command == "exit":
                print("Goodbye!")
                break

            state = base_state.copy()
            tools = await mcp_client.get_tools()
            state["command"] = command
            log_tool = next(t for t in tools if t.name == "log_teacher_query_tool")

            if command == "profile":
                name = input("Student name: ")
                state["filter_name"] = name
                result = await run_agent_with_timer(app, state)
                if not result["student_profile"]:
                    print(f"Error: Student '{name}' not found.")
                else:
                    print(result["student_profile"])
                await log_tool.ainvoke({
                    "teacher_id": teacher["idteacher"],
                    "query_text": f"profile: {name}",
                    "intent": "profile",
                    "result": (result["student_profile"] or "not found")[:200]
                })

            elif command == "course":
                course = input("Course name: ")
                state["filter_course"] = course
                result = await run_agent_with_timer(app, state)
                if "not found" in result["course_report"]:
                    print(result["course_report"])
                    print("Tip: use 'courses' command to see all available courses.")
                else:
                    print(result["course_report"])
                await log_tool.ainvoke({
                    "teacher_id": teacher["idteacher"],
                    "query_text": f"course: {course}",
                    "intent": "course",
                    "result": (result["course_report"] or "not found")[:200]
                })


            elif command == "enroll":
                enroll_name = input("Student name: ")
                enroll_course = input("Course name: ")
                state["enroll_student_name"] = enroll_name
                state["enroll_course_name"] = enroll_course
                result = await run_agent_with_timer(app, state)
                if "Error" in result["enroll_result"]:
                    print(result["enroll_result"])
                    print("Tip: use 'courses' command to see all available courses.")
                else:
                    print(result["enroll_result"])
                await log_tool.ainvoke({
                    "teacher_id": teacher["idteacher"],
                    "query_text": f"enroll: {enroll_name} -> {enroll_course}",
                    "intent": "enroll",
                    "result": (result["enroll_result"] or "not found")[:200]
                })
                

            elif command == "grade":
                grade_student = input("Student name: ")
                grade_course = input("Course name: ")
                while True:
                    grade_value = input("Grade (1-5): ")
                    if grade_value in ["1", "2", "3", "4", "5"]:
                        break
                    print("Error: grade must be a number between 1 and 5. Try again.")
                confirm = input(f"Set grade {grade_value} for '{grade_student}' in '{grade_course}'? (yes/no): ")
                if confirm.lower() != "yes":
                    print("Cancelled.")
                    continue

                state["grade_student_name"] = grade_student
                state["grade_course_name"] = grade_course
                state["grade_value"] = grade_value
                result = await run_agent_with_timer(app, state)
                if "Error" in result["grade_result"]:
                    print(result["grade_result"])
                    print("Tip: use 'courses' command to see all available courses.")
                else:
                    print(result["grade_result"])
                await log_tool.ainvoke({
                    "teacher_id": teacher["idteacher"],
                    "query_text": f"grade: {grade_student} -> {grade_course} = {grade_value}",
                    "intent": "grade",
                    "result": (result["grade_result"] or "not found")[:200]
                })

            elif command == "status":
                status_student = input("Student name: ")
                status_course = input("Course name: ")
                while True:
                    status_value = input("Status (planned/ongoing/completed): ")
                    if status_value in ["planned","ongoing","completed"]:
                        break
                    print("Error: status must be only planned or ongoing or completed. Try again")
                    
                state["status_student_name"] = status_student
                state["status_course_name"] = status_course
                state["status_value"] = status_value
                result = await run_agent_with_timer(app, state)
                if "Error" in result["status_update_result"]:
                    print(result["status_update_result"])
                    print("Tip: use 'courses' command to see all available courses.")
                else:
                    print(result["status_update_result"])
                await log_tool.ainvoke({
                    "teacher_id": teacher["idteacher"],
                    "query_text": f"status: {status_student} -> {status_course} = {status_value}",
                    "intent": "status",
                    "result": (result["status_update_result"] or "not found")[:200]
                })

            elif command == "group":
                group_code = input("Group code: ")
                state["filter_group"] = group_code
                result = await run_agent_with_timer(app, state)
                if not result["group_report"]:
                    print(f"Error: Group {group_code} not found.")
                else:
                    print(result["group_report"])
                await log_tool.ainvoke({
                    "teacher_id": teacher["idteacher"],
                    "query_text": f"group: {group_code}",
                    "intent": "group",
                    "result": (result["group_report"] or "not found")[:200]
                })

            elif command == "bulk":
                bulk_group = input("Group code: ")
                bulk_course = input("Course name: ")
                confirm = input(f"Enroll all students from '{bulk_group}' to '{bulk_course}'? (yes/no): ")
                if confirm.lower() != "yes":
                    print("Cancelled.")
                    continue
                state["bulk_group_code"] = bulk_group
                state["bulk_course_name"] = bulk_course
                result = await run_agent_with_timer(app, state)
                if not result["bulk_enroll_result"]:
                    print(f"Error: Group '{bulk_group}' or Course '{bulk_course}' not found.")
                    print("Tip: use 'courses' command to see all available courses.")
                else:
                    print(result["bulk_enroll_result"])
                await log_tool.ainvoke({
                    "teacher_id": teacher["idteacher"],
                    "query_text": f"bulk: {bulk_group} -> {bulk_course}",
                    "intent": "bulk",
                    "result": (result["bulk_enroll_result"] or "not found")[:200]
                })

            elif command == "courses":
                state["show_courses"] = True
                result = await run_agent_with_timer(app, state)
                print(result["courses_list"])
                await log_tool.ainvoke({
                    "teacher_id": teacher["idteacher"],
                    "query_text": "courses: show all",
                    "intent": "courses",
                    "result": (result["courses_list"] or "")[:200]
                })

            elif command == "risk":
                state["command"] = command
                result = await run_agent_with_timer(app, state)
                print(result["risk_report"])
                await log_tool.ainvoke({
                    "teacher_id": teacher["idteacher"],
                    "query_text": "risk: show report",
                    "intent": "risk",
                    "result": (result["risk_report"] or "")[:200]
                })

            elif command == "history":
                history_tool = next(t for t in tools if t.name == "get_teacher_query_history_tool")
                raw_history = await history_tool.ainvoke({"teacher_id": teacher["idteacher"], "limit": 10})
                history = json.loads(raw_history[0]["text"]) if raw_history else []
                if not history:
                    print("No history found.")
                else:
                    print("Your recent queries:")
                    for record in history:
                        print(f"[{record['created_at']}] {record['intent']}: {record['query_text']}")

            elif command == "curriculum":
                program = input("Program code (e.g. TVT): ")
                state["filter_program"] = program
                result = await run_agent_with_timer(app, state)
                if "Error" in result["curriculum_info"]:
                    print(result["curriculum_info"])
                else:
                    print(result["curriculum_info"])
                await log_tool.ainvoke({
                    "teacher_id": teacher["idteacher"],
                    "query_text": f"curriculum: {program}",
                    "intent": "curriculum",
                    "result": result["curriculum_info"][:200]
                })

            elif command == "analytics":
                print("Analytics type: (courses / group)")
                analytics_type = input("Type: ")
                state["filter_analytics"] = analytics_type
                if analytics_type == "group":
                    group = input("Group code: ")
                    state["filter_group"] = group
                result = await run_agent_with_timer(app, state)
                print(result["analytics_report"])
                await log_tool.ainvoke({
                    "teacher_id": teacher["idteacher"],
                    "query_text": f"analytics: {analytics_type}",
                    "intent": "analytics",
                    "result": result["analytics_report"][:200]
                })
            
            elif command == "ask":
                question = input("Your question: ")
                state["rag_query"] = question
                result = await run_agent_with_timer(app, state)
                print(result["rag_answer"])

            elif command == "export":
                print("Export type: (risk / analytics / courses)")
                export_type = input("Type: ")
                
                quick_state = base_state.copy()
                quick_state["command"] = export_type
                
                if export_type == "analytics":
                    quick_state["filter_analytics"] = "courses"
                
                export_result = await app.ainvoke(quick_state)
                
                field_map = {
                    "risk": "risk_report",
                    "analytics": "analytics_report", 
                    "courses": "courses_list"
                }
                
                content = export_result.get(field_map.get(export_type, ""), "No data")
                filename = f"report_{export_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Report saved to {filename}")


            elif command == "help":
                print("""
                Available commands:
                profile    - View student's full profile
                course     - List students enrolled in a course
                enroll     - Enroll a student to a course
                grade      - Update student's grade (1-5)
                status     - Update enrollment status (planned/ongoing/completed)
                group      - List all students in a group
                bulk       - Enroll entire group to a course
                courses    - Show all available courses
                curriculum - View program curriculum by semester
                analytics  - View course or group analytics
                risk       - Show at-risk students report
                history    - View your recent query history
                ask        - Ask a question about tutoring guidelines
                help       - Show this help message
                export     - Export reports
                me         - Own information
                requests   - See all requests
                approve    - Approve requests to course for student
                exit       - Logout
                """)

            elif command == "me":
                groups = await get_teacher_groups(teacher["idteacher"])
                print(f"\n👤 {teacher['fname']} {teacher['lname']}")
                print(f"📧 {teacher['email']}")
                print("\nYour groups:")
                for group in groups:
                    print(f"  - {group['group_code']}: {group['student_count']} students")

            elif command == "requests":
                result = await run_agent_with_timer(app, state)
                print(result["pending_requests_list"])

            elif command == "approve":
                req_id = input("Request ID: ")
                action = input("Approve or reject? (approve/reject): ")
                state["request_id"] = int(req_id)
                state["request_action"] = action
                result = await run_agent_with_timer(app, state)
                print(result["request_action_result"])

            else:
                print("Unknown command. Try: profile/course/enroll/grade/status/group/bulk/courses/risk/history/curriculum/analytics/ask/help/export/me/requests/approve/exit")

    
    if role == "student":
        student_number = input("Enter your student number: ")
        password = input("Enter your password: ")
        student = await get_student_by_number(student_number)
        if student is None:
            print("Access denied. Student not found")
            return
        if not verify_password(password, student["password_hash"]):
            print("Access denied. Wrong password")
            return
        print(f"Welcome, {student['fname']} {student['lname']}!")

        student_full_name = f"{student['fname']} {student['lname']}"
        initial_state = {
            "user_role": "student",
            "students": [],
            "student_data": "",
            "course_id": 0,
            "teacher_id":0,
            "course_data": "",
            "enrollments": [],
            "is_allowed": True,
            "bot_analyze_text": "",
            "final_text": "",
            "calendar_info": "",
            "student_messages": "",
            "filter_name": student_full_name,
            "filter_course": "",
            "enroll_course_name": "",
            "enroll_student_name": "",
            "enroll_result": "",
            "show_courses": False,
            "courses_list": "",
            "grade_student_name": "",
            "grade_course_name": "",
            "grade_value": "",
            "grade_result": "",
            "student_profile": "",
            "status_student_name": "",
            "status_course_name": "",
            "status_value": "",
            "status_update_result": "",
            "risk_report": "",
            "group_report": "",
            "filter_group": "",
            "bulk_group_code": "",
            "bulk_course_name": "",
            "bulk_enroll_result": "",
            "eligibility_report": "",
            "course_report": "",
            "filter_program": "",
            "curriculum_info": "",
            "student_plan": "",
            "filter_analytics": "",
            "analytics_report": "",
            "command":"",
            "rag_query": "",
            "rag_answer": "",
            "request_course_name":"",
            "request_result": "",
            "pending_requests_list":"",
            "request_id": 0,
            "request_action": "",
            "request_action_result": "",
            "my_requests_list": ""
        }
        while True:
            choice = input("What would you like to see? (profile / eligibility / recommend / courses / plan / ask / help / request / my_requests / exit ): ")

            state = initial_state.copy()
            tools = await mcp_client.get_tools()
            state["command"] = choice

            if choice == "exit":
                print("Goodbye!")
                break

            if choice == "profile":
                result = await run_agent_with_timer(app, state)
                print(result["student_profile"])

            elif choice == "eligibility":
                result = await run_agent_with_timer(app, state)
                print("Your project eligibility:")
                print(result["eligibility_report"])

            elif choice == "recommend":
                result = await run_agent_with_timer(app, state)
                print("Your personal recommendation:")
                print(result["student_recommendation"])

            elif choice == "courses":
                state["show_courses"] = True
                result = await run_agent_with_timer(app, state)
                print(result["courses_list"])

            elif choice == "plan":
                group_code = student.get("group_code", "TVT")
                state["filter_program"] = "".join(filter(str.isalpha, group_code)) or "TVT"
                result = await run_agent_with_timer(app, state)
                print(result["student_plan"])

            elif choice == "ask":
                question = input("Your question: ")
                state["rag_query"] = question
                result = await run_agent_with_timer(app, state)
                print(result["rag_answer"])

            elif choice == "help":
                print("""
            Available commands:
                profile     - View your academic profile
                eligibility - Check your project eligibility
                recommend   - Get AI-powered study recommendation
                courses     - View all available courses
                plan        - View your study plan progress
                ask         - Ask a question about your studies
                request     - Request enrollment in a course
                my_requests - View status of your enrollment requests
                help        - Show this help message
                exit        - Logout
            """)

            elif choice == "request":
                courses_state = initial_state.copy()
                courses_state["command"] = "courses"
                courses_state["show_courses"] = True
                courses_result = await run_agent_with_timer(app, courses_state)
                print("Available courses:")
                print(courses_result["courses_list"])
                
                course_name = input("\nEnter course name to request: ")
                state["request_course_name"] = course_name
                result = await run_agent_with_timer(app, state)
                print(result["request_result"])

            elif choice == "my_requests":
                result = await run_agent_with_timer(app, state)
                print(result["my_requests_list"])
            
            else:
                print("Unknown command. Try: profile / eligibility / recommend / courses / plan / ask / help / request / my_requests / exit ")

if __name__ == "__main__":
    asyncio.run(main())