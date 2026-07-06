from langgraph.graph import StateGraph, START, END
import asyncio
from typing_extensions import TypedDict
from datetime import datetime
from typing import Annotated
import typing
import operator
import os
from dotenv import load_dotenv
from groq import Groq
from database.db_connector import get_all_students, get_student_enrollments, get_student_by_course,get_course_id_by_name,get_student_id_by_name,enroll_student,get_all_courses,update_grade


load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


STUDENTS_DB = {
    1: {"idstudent": 1,"student_number": "H123456", "fname": "Nikita", "lname":"Mopsov", "email": "nikita.mopsov@tuni.fi","study_right": "Insinööri (AMK), tietotekniikka" , "valid_from":"2024-08-01","valid_until":"2028-07-31","credits_earned":10, "credits_expected":30, "completed_courses": []},
    2: {"idstudent": 2,"student_number": "H234567", "fname": "Lena", "lname":"Golovach", "email": "lena.golovach@tuni.fi","study_right": "Insinööri (AMK), tietotekniikka" , "valid_from":"2024-08-01","valid_until":"2028-07-31","credits_earned":30, "credits_expected":90,"completed_courses":[3,5,6]},
    3: {"idstudent": 3,"student_number": "H789123", "fname": "Papich", "lname":"Veneckiy", "email": "jfasjdfjfad@tuni.fi","study_right": "Insinööri (AMK), tietotekniikka" , "valid_from":"2024-08-01","valid_until":"2028-07-31","credits_earned":120, "credits_expected":120,"completed_courses":[3]}
}

TUTOR_CALENDAR = {
    1: "January: Spring semester begins. Organize orientation meetings with new students.",
    2: "February: Mid-winter check-in. Review student progress and study rights.",
    3: "March: Spring exam period approaching. Identify students at risk.",
    4: "April: Spring exams. Monitor student performance closely.",
    5: "May: Semester ending. Final progress review for all students.",
    6: "June: Summer break begins. Send summary reports to coordinators.",
    7: "July: Summer break. No active tutoring sessions.",
    8: "August: Autumn semester begins. Welcome new students, organize first meetings.",
    9: "September: First month check-in. Verify all students are enrolled correctly.",
    10: "October: Mid-semester review. Check credit accumulation and study rights.",
    11: "November: Autumn exam period approaching. Support students at risk.",
    12: "December: Autumn exams. Final check before winter break."
}

PROJECTS_DB = {
    1: {"project_name": "AI Chatbot Development", "required_courses": [3, 6, 8]},
    2: {"project_name": "Web Application Project", "required_courses": [3, 4, 7]}
}

class State(TypedDict):
    students: list
    student_data: str
    filter_name: str
    
    course_id: int
    course_data: str

    enrollments: list
    is_allowed: bool

    final_text: str

    calendar_info: str

    student_messages:str


    bot_analyze_text: Annotated[str, operator.add]

    filter_course: str 

    enroll_student_name: str
    enroll_course_name: str
    enroll_result: str

    show_courses: bool
    courses_list: str

    grade_student_name:str
    grade_course_name:str
    grade_value: str
    grade_result: str



    
async def progress_agent(state: State):
    print("First agent is working")
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
    print("Second agent is working")
    students= state.get("students",[])
    new_issue=""
    for student in students:
        full_name= student["fname"]+" "+student["lname"]
        today = datetime.now()
        date_obj = student["valid_until"]
        left_study_right= (date_obj - today.date()).days / 30
        if left_study_right<6:
            new_issue+= f"Student:{full_name} has critical situation\n"
        elif left_study_right<12:
            new_issue+= f"Student:{full_name} has warning situation\n"
        else:
            new_issue+= f"Student:{full_name} has study right\n"
    return {"bot_analyze_text": new_issue}

async def recommendation_agent(state: State):
    print("Third Groq agent is working")
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
    print("Forth agent is working")
    current_text = state.get("bot_analyze_text","")
    if "critical" in current_text or "warning" in current_text or "Not found" in current_text:
        return{"is_allowed":False}
    else:
        return {"is_allowed": True}
    

async def analytics_agent(state: State):
    print("Sixth agent is working")
    allowed = state.get("is_allowed",True)
    if allowed:
        verdict = "All checks passed. The student is cleared for enrollment.\n"
    else:
        verdict = "Enrollment Blocked. Student must contact the coordinator.\n"
    return{"bot_analyze_text": verdict}

async def fetch_students_agent(state: State):
    print("Fetch agent is working")
    filter_name = state.get("filter_name","")
    all_students = await get_all_students()
    
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
        date_obj= student["valid_from"]
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
    print("Seventh agent is working")
    today= datetime.now()
    month=today.month
    calendar_info = TUTOR_CALENDAR[month]
    return {"calendar_info": calendar_info}

async def communication_agent(state: State):
    print("Eighth agent is working")
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
    print("Ninth agent is working")
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

    return {"bot_analyze_text": new_issue}

async def course_student_agent(state: State):
    print("Tenth agent is working")
    new_issue=""
    filter_course = state.get("filter_course","")
    if filter_course!="":
        students=await get_student_by_course(filter_course)
        new_issue = f"Students on course {filter_course}:\n"
        for student in students:
            new_issue += f"- {student['fname']} {student['lname']}: {student['status']}, grade: {student['grade']}\n"

    return {"bot_analyze_text": new_issue}

async def enroll_agent(state: State):
    print("Eleventh agent is working")
    enroll_student_name=state.get("enroll_student_name","")
    enroll_course_name=state.get("enroll_course_name","")
    if enroll_student_name == "" or enroll_course_name == "":
        return {"enroll_result": ""}
    fname,lname = enroll_student_name.split()[:2]
    idstudent = await get_student_id_by_name(fname, lname)
    idcourse = await get_course_id_by_name(enroll_course_name)
    if idstudent is None:
        return {"enroll_result": "Error: student not found"}
    if idcourse is None:
        return {"enroll_result": "Error: course not found"}
    enroll = await enroll_student(idstudent, idcourse)
    return {"enroll_result": enroll}

async def course_list_agent(state: State):
    print("Twelveth agent is working")
    new_issue=""
    courses=state.get("show_courses","")
    if courses is True:
        all_courses = await get_all_courses()
        for course in all_courses:
            new_issue += f"- {course['course_code']}: {course['course_name']} ({course['credit']} credits)\n"
    return {"courses_list": new_issue}

async def grade_agent(state: State):
    print("Thirteenth agent is working")
    grade_student_name=state.get("grade_student_name","")
    grade_course_name=state.get("grade_course_name","")
    grade_value= state.get("grade_value","")
    if grade_student_name == "" or grade_course_name == "" or grade_value == "":
        return {"grade_result": ""}
    fname,lname = grade_student_name.split()[:2]
    idstudent = await get_student_id_by_name(fname, lname)
    idcourse = await get_course_id_by_name(grade_course_name)
    grade_result= await update_grade(idstudent,idcourse,grade_value)
    if idstudent is None:
        return {"grade_result": "Error: student not found"}
    if idcourse is None:
        return {"grade_result": "Error: course not found"}
    grade_result = await update_grade(idstudent, idcourse, grade_value)
    return {"grade_result": grade_result}

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

graph.add_edge(START, "fetch_node")
graph.add_edge(START, "course_students_node")
graph.add_edge(START, "enroll_node")
graph.add_edge("enroll_node", END)
graph.add_edge(START, "course_list_node")
graph.add_edge("course_list_node", END)
graph.add_edge(START, "grade_node")
graph.add_edge("grade_node", END)
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
    name = input("Enter student name or press Enter for all: ")
    course = input("Enter course name or press Enter to skip: ")
    enroll_name = input("Enter student name to enroll (or press Enter to skip): ")
    enroll_course = input("Enter course to enroll in (or press Enter to skip): ")
    show_courses = input("Show all courses? (yes/no): ")
    grade_student = input("Enter student name to grade (or press Enter to skip): ")
    grade_course = input("Enter course name: ")
    grade_value = input("Enter grade (1-5): ")
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
        "filter_name": name,
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
        "grade_result": ""
        
    }

    print("Start of graph")
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
    else:
        print(result["final_text"])

asyncio.run(main())