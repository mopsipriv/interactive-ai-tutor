from langgraph.graph import StateGraph, START, END
import asyncio
from typing_extensions import TypedDict
from datetime import datetime
from typing import Annotated
import operator
import os
from dotenv import load_dotenv
from groq import Groq
from database.db_connector import get_all_students, get_student_enrollments, get_student_by_course,get_course_id_by_name,get_student_id_by_name,enroll_student,get_all_courses,update_grade,get_student_profile,update_enrollment_status,get_students_by_group, get_teacher_by_email, get_student_by_number
from langchain_mcp_adapters.client import MultiServerMCPClient
import json
from agents.constants import TUTOR_CALENDAR, PROJECTS_DB
from agents.state import State
from database.auth import verify_password


mcp_client = MultiServerMCPClient({
    "tutor_server": {
        "url": "http://127.0.0.1:8000/mcp",
        "transport": "streamable_http"
    }
})

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
async def progress_agent(state: State):
    students = state.get("students",[])
    new_issue= ""
    for student in students:
        full_name= student["fname"]+" "+student["lname"]
        progress= student["credits_expected"] - student["credits_earned"]
        if progress>15:
            new_issue+= f"Student:{full_name} has critical situation. Student does not have enought credits.\n"
        elif progress>5 and progress<15:
            new_issue+= f"Student:{full_name} has warning situation. Student does not have enought credits.\n"
        else:
            new_issue+= f"Student:{full_name} has good situation. Student has enought credits.\n"
        
    return {"bot_analyze_text": new_issue}


async def study_right_agent(state: State):
    students= state.get("students",[])
    new_issue=""
    for student in students:
        full_name= student["fname"]+" "+student["lname"]
        today = datetime.now()
        date_obj = datetime.strptime(student["valid_until"], "%Y-%m-%d").date()
        left_study_right= (date_obj - today.date()).days / 30
        if left_study_right<6:
            new_issue+= f"Student:{full_name} has critical situation\n"
        elif left_study_right<12:
            new_issue+= f"Student:{full_name} has warning situation\n"
        else:
            new_issue+= f"Student:{full_name} has study right\n"
    return {"bot_analyze_text": new_issue}


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
    allowed = state.get("is_allowed",True)
    if allowed:
        verdict = "All checks passed. The student is cleared for enrollment.\n"
    else:
        verdict = "Enrollment Blocked. Student must contact the coordinator.\n"
    return{"bot_analyze_text": verdict}


async def fetch_students_agent(state: State):
    filter_name = state.get("filter_name","")
    tools = await mcp_client.get_tools()
    get_students_tool = next(t for t in tools if t.name == "get_students_tool")
    raw_result = await get_students_tool.ainvoke({})
    all_students = json.loads(raw_result[0]["text"])
    
    for student in all_students:
        enrollments = await get_student_enrollments(student["idstudent"])
        completed_credits = 0
        completed_courses = []
        credits_expected = 0
        for enrollment in enrollments:
            if enrollment["status"] == "completed":
                completed_courses.append(enrollment["idcourse"])
                completed_credits += enrollment["credit"]
        student["completed_courses"] = completed_courses
        student["credits_earned"] = completed_credits
        today = datetime.now()
        date_obj = datetime.strptime(student["valid_from"], "%Y-%m-%d").date()
        days_passed= (today.date()-date_obj).days
        semesters= days_passed/182
        total_credits=semesters*30
        student["credits_expected"]= total_credits

    if filter_name != "":
        for student in all_students:
            full_name = student["fname"] + " " + student["lname"]
            if full_name == filter_name:
                return {"students": [student]}
    else:
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
        students = json.loads(raw_students_course[0]["text"])

        new_issue = f"Students on course {filter_course}:\n"
        for student in students:
            new_issue += f"- {student['fname']} {student['lname']}: {student['status']}, grade: {student['grade']}\n"

    return {"bot_analyze_text": new_issue}


async def enroll_agent(state: State):
    enroll_student_name=state.get("enroll_student_name","")
    enroll_course_name=state.get("enroll_course_name","")
    if enroll_student_name == "" or enroll_course_name == "":
        return {"enroll_result": ""}
    fname,lname = enroll_student_name.split()[:2]
    tools= await mcp_client.get_tools()
    get_student_id_tool = next(t for t in tools if t.name == "get_student_id_by_name_tool")
    raw_student_id = await get_student_id_tool.ainvoke({"fname":fname, "lname":lname})
    idstudent = json.loads(raw_student_id[0]["text"])

    get_course_id_tool = next(t for t in tools if t.name == "get_course_id_by_name_tool")
    raw_course_id = await get_course_id_tool.ainvoke({"course_name": enroll_course_name})
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
    tools= await mcp_client.get_tools()
    fname,lname = grade_student_name.split()[:2]
    
    get_student_id_tool = next(t for t in tools if t.name == "get_student_id_by_name_tool")
    raw_student_id = await get_student_id_tool.ainvoke({"fname":fname, "lname":lname})
    idstudent = json.loads(raw_student_id[0]["text"])
    
    get_course_id_tool = next(t for t in tools if t.name == "get_course_id_by_name_tool")
    raw_course_id = await get_course_id_tool.ainvoke({"course_name":grade_course_name})
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
    tools = await mcp_client.get_tools()
    fname,lname = filter_name.split()[:2]
   
    get_student_id_tool = next(t for t in tools if t.name == "get_student_id_by_name_tool")
    raw_student_id = await get_student_id_tool.ainvoke({"fname":fname,"lname":lname})
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
    tools = await mcp_client.get_tools()
    
    fname,lname = status_student_name.split()[:2]
    get_student_id_tool = next(t for t in tools if t.name == "get_student_id_by_name_tool")
    raw_student_id = await get_student_id_tool.ainvoke({"fname":fname,"lname":lname})
    idstudent = json.loads(raw_student_id[0]["text"])

    get_course_id_tool = next(t for t in tools if t.name == "get_course_id_by_name_tool")
    raw_course_id = await get_course_id_tool.ainvoke({"course_name":status_course_name})
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
    students = json.loads(raw_students_group[0]["text"])

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
    students = json.loads(raw_students_group[0]["text"])
    
    get_course_id_tool = next(t for t in tools if t.name == "get_course_id_by_name_tool")
    raw_course_id = await get_course_id_tool.ainvoke({"course_name":bulk_course_code})
    idcourse = json.loads(raw_course_id[0]["text"])
    
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
    print("Nineteenth agent is working")
    profile = state.get("student_profile", "")
    eligibility = state.get("eligibility_report", "")
    progress = state.get("bot_analyze_text", "")
    
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a friendly AI assistant helping a university student understand their academic progress. Give clear, encouraging, actionable advice. Maximum 100 words."},
            {"role": "user", "content": f"{profile}\n{eligibility}\n{progress}"}
        ],
        model="llama-3.3-70b-versatile",
        max_completion_tokens=512,
    )
    return {"student_recommendation": response.choices[0].message.content}



def route_after_status(state: State):
    allowed = state.get("is_allowed",True)

    if not allowed:
        return "go_to_analytics"
    else:
        return "go_to_end"
    

graph=StateGraph(State)

graph.add_node("fetch_node",fetch_students_agent)
graph.add_node("progress_node", progress_agent)
graph.add_node("study_right_node", study_right_agent)
graph.add_node("recommendation_node", recommendation_agent)
graph.add_node("status_node",status_agent)
graph.add_node("analytics_node",analytics_agent)
graph.add_node("eligibility_node", eligibility_agent)
graph.add_node("course_students_node",course_student_agent)
graph.add_node("enroll_node",enroll_agent)
graph.add_node("calendar_node",calendar_agent)
graph.add_node("communication_node",communication_agent)
graph.add_node("course_list_node", course_list_agent)
graph.add_node("grade_node", grade_agent)
graph.add_node("profile_node",profile_agent)
graph.add_node("update_status_node",status_update_agent)
graph.add_node("risk_report_node",risk_report_agent)
graph.add_node("group_report_node",group_report_agent)
graph.add_node("bulk_enroll_node",bulk_enroll_agent)
graph.add_node("student_recommendation_note",student_recommendation_agent)


graph.add_edge(START, "fetch_node")
graph.add_edge(START, "course_students_node")
graph.add_edge(START, "enroll_node")
graph.add_edge("enroll_node", END)
graph.add_edge(START, "course_list_node")
graph.add_edge("course_list_node", END)
graph.add_edge(START, "grade_node")
graph.add_edge("grade_node", END)
graph.add_edge(START,"profile_node")
graph.add_edge("profile_node",END)
graph.add_edge(START,"update_status_node")
graph.add_edge("update_status_node",END)
graph.add_edge(START,"group_report_node")
graph.add_edge("group_report_node",END)
graph.add_edge(START,"bulk_enroll_node")
graph.add_edge("bulk_enroll_node",END)
graph.add_edge(START,"student_recommendation_note")
graph.add_edge("student_recommendation_note",END)
graph.add_edge("fetch_node", "risk_report_node")
graph.add_edge("risk_report_node", "status_node")
graph.add_edge("fetch_node", "progress_node")
graph.add_edge("course_students_node", "status_node")
graph.add_edge("fetch_node", "study_right_node")
graph.add_edge("study_right_node", "status_node")     
graph.add_edge("progress_node", "status_node")
graph.add_edge("fetch_node", "eligibility_node")
graph.add_edge("eligibility_node", "status_node")
graph.add_edge("fetch_node", "calendar_node")
graph.add_conditional_edges(
    "status_node",
    route_after_status,
    {
        "go_to_analytics": "analytics_node",
        "go_to_end": END
    }
)
graph.add_edge("analytics_node", "recommendation_node")
graph.add_edge("analytics_node","communication_node")
graph.add_edge("calendar_node", "status_node")
graph.add_edge("communication_node", END)

app=graph.compile()

async def main():
    role = input("Are you a teacher or student? (teacher/student): ")

    if role == "teacher":
        email = input("Enter your email: ")
        password = input("Enter your password: ")
        teacher = await get_teacher_by_email(email)
        if teacher is None:
            print("Access denied. Teacher not found")
            return
        if not verify_password(password, teacher["password_hash"]):
            print("Access denied. Wrong password")
            return
        print(f"Welcome, {teacher['fname']} {teacher['lname']}!")
    
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
            "eligibility_report": ""
        }
        while True:
            choice = input("What would you like to see? (profile / eligibility / recommend / exit): ")

            if choice == "exit":
                print("Goodbye!")
                break

            if choice == "profile":
                result = await app.ainvoke(initial_state)
                print(result["student_profile"])

            elif choice == "eligibility":
                result = await app.ainvoke(initial_state)
                print("Your project eligibility:")
                print(result["eligibility_report"])

            elif choice == "recommend":
                result = await app.ainvoke(initial_state)
                print("Your personal recommendation:")
                print(result["student_recommendation"])
        
        return


    name = input("Enter student name or press Enter for all: ")
    course = input("Enter course name or press Enter to skip: ")
    enroll_name = input("Enter student name to enroll (or press Enter to skip): ")
    enroll_course = input("Enter course to enroll in (or press Enter to skip): ")
    show_courses = input("Show all courses? (yes/no): ")
    grade_student = input("Enter student name to grade (or press Enter to skip): ")
    grade_course = input("Enter course name: ")
    grade_value = input("Enter grade (1-5): ")
    student_profile = input("Enter student name to see his profile or press Enter to skip: ")
    status_student = input("Enter student name to update status (or press Enter to skip): ")
    status_course = input("Enter course name: ")
    status_value = input("Enter status (planned/ongoing/completed): ")
    group_code = input("Enter group code to see students (or press Enter to skip): ")
    bulk_group = input("Enter group code for bulk enroll (or press Enter to skip): ")
    bulk_course = input("Enter course name for bulk enroll: ")
    initial_state = {
        "students": [],
        "student_data": "",
        "course_id": 0,
        "course_data": "",
        "enrollments": [],
        "is_allowed": True,
        "bot_analyze_text": "",
        "final_text": "",
        "calendar_info":"",
        "student_messages":"",
        "filter_name": student_profile if student_profile else name,
        "filter_course":course,
        "enroll_course_name":"",
        "enroll_student_name":"",
        "enroll_result": "",
        "enroll_student_name": enroll_name,
        "enroll_course_name": enroll_course,
        "show_courses": show_courses=="yes", 
        "courses_list": "",
        "grade_student_name": grade_student,
        "grade_course_name": grade_course,
        "grade_value": grade_value,
        "grade_result": "",
        "student_profile": "",
        "status_student_name": status_student,
        "status_course_name": status_course,
        "status_value": status_value,
        "status_update_result": "",
        "risk_report":"",
        "group_report":"",
        "filter_group":group_code,
        "bulk_group_code": bulk_group,
        "bulk_course_name": bulk_course,
        "bulk_enroll_result": ""
    }

    result = await app.ainvoke(initial_state)

    if enroll_name and enroll_course:
        print(result["enroll_result"])
    elif course:
        print(result["bot_analyze_text"])
    elif name:
        print(result["final_text"])
        print(result["student_messages"])
    elif show_courses.lower() == "yes":
        print(result["courses_list"])
    elif grade_student and grade_course:
        print(result["grade_result"])
    elif student_profile:
        print(result["student_profile"])
    elif status_student and status_course:
        print(result["status_update_result"])
    elif group_code:
        print(result["group_report"])
    elif bulk_group and bulk_course:
        print(result["bulk_enroll_result"])
    else:
        print(result["risk_report"])

asyncio.run(main())
