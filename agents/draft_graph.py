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

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


STUDENTS_DB = {
    1: {"idstudent": 1,"student_number": "H123456", "fname": "Nikita", "lname":"Mopsov", "email": "nikita.mopsov@tuni.fi","study_right": "Insinööri (AMK), tietotekniikka" , "valid_from":"2024-08-01","valid_until":"2028-07-31","credits_earned":10, "credits_expected":30},
    2: {"idstudent": 2,"student_number": "H234567", "fname": "Lena", "lname":"Golovach", "email": "lena.golovach@tuni.fi","study_right": "Insinööri (AMK), tietotekniikka" , "valid_from":"2024-08-01","valid_until":"2028-07-31","credits_earned":30, "credits_expected":90},
    3: {"idstudent": 3,"student_number": "H789123", "fname": "Papich", "lname":"Veneckiy", "email": "jfasjdfjfad@tuni.fi","study_right": "Insinööri (AMK), tietotekniikka" , "valid_from":"2024-08-01","valid_until":"2028-07-31","credits_earned":120, "credits_expected":120}
}

class State(TypedDict):
    students: list
    student_data: str
    
    course_id: int
    course_data: str

    enrollments: list
    is_allowed: bool

    final_text: str

    bot_analyze_text: Annotated[str, operator.add]
    
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
        right_time = student["valid_until"]
        format_string= "%Y-%m-%d"
        date_obj= datetime.strptime(right_time,format_string)
        left_study_right= (date_obj - today).days / 30
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
    response = client.chat.completions.create(
        messages=[
                {"role": "system", "content": "You are a tutor assistant.You receive student analysis data and write a short professional report for the teacher"},
                {"role": "user", "content": all_issues}
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
    
async def course_agent(state: State):
    print("Fifth agent is working")
    course_info="Course: Matematiikan perusteet tietotekniikassa 1, Status: 45/50 students enrolled\n"
    return {"course_data":course_info}

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
    all_students = list(STUDENTS_DB.values())
    return {"students":all_students}


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
graph.add_node("course_node",course_agent)

graph.add_edge(START, "fetch_node")
graph.add_edge("fetch_node", "progress_node")
graph.add_edge("fetch_node", "study_right_node")
graph.add_edge("study_right_node", "status_node")     
graph.add_edge("progress_node", "status_node")
graph.add_conditional_edges(
    "status_node",
    route_after_status,
    {
        "go_to_analytics": "analytics_node",
        "go_to_end": END
    }
)
graph.add_edge("analytics_node", "course_node")
graph.add_edge("course_node","recommendation_node")
graph.add_edge("recommendation_node", END)

app=graph.compile()

async def main():
    initial_state = {
        "students": [],
        "student_data": "",
        "course_id": 0,
        "course_data": "",
        "enrollments": [],
        "is_allowed": True,
        "bot_analyze_text": "",
        "final_text": ""
    }

    print("Start of graph")
    result = await app.ainvoke(initial_state)

    graph_image = app.get_graph().draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(graph_image)

    print("\nFinal text from final_text")
    print(result["final_text"])
    
    print("Is student allowed?:", result["is_allowed"])

asyncio.run(main())