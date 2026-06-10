from langgraph.graph import StateGraph, START, END
import asyncio
from typing_extensions import TypedDict
from datetime import datetime

STUDENTS_DB = {
    1: {"idstudent": 1,"student_number": "H123456", "fname": "Nikita", "lname":"Mopsov", "email": "aleksandr.starchenkov@tuni.fi","study_right": "Insinööri (AMK), tietotekniikka" , "valid_from":"2024-08-01","valid_until":"2028-07-31"},
    2: {"idstudent": 2,"student_number": "H234567", "fname": "Anna", "lname":"Mäkinen", "email": "anna.makinen@tuni.fi","study_right": "Insinööri (AMK), tietotekniikka" , "valid_from":"2024-08-01","valid_until":"2028-07-31"}
}

class State(TypedDict):
    student_name: str
    student_data: str
    
    course_id: int
    course_data: str

    enrollments: list
    is_allowed: bool

    final_text: str

    bot_analyze_text: str 
    
async def progress_agent(state: State):
    print("First agent is working")
    name = state.get("student_name","")
    found = False
    for student in STUDENTS_DB.values():
        full_name= student["fname"]+" "+student["lname"]
        if full_name==name:
            found= True
            new_issue = f"Student: {full_name}"
    if not found:
        new_issue = f"Student: {name}, Details: Not found in database\n"
    current_text= state.get("bot_analyze_text","")
    return {"bot_analyze_text": current_text+new_issue}

async def study_right_agent(state: State):
    print("Second agent is working")
    name= state.get("student_name","")
    found = False
    for student in STUDENTS_DB.values():
        full_name= student["fname"]+" "+student["lname"]
        if full_name==name:
            found = True
            today = datetime.now()
            right_time = student["valid_until"]
            format_string= "%Y-%m-%d"
            date_obj= datetime.strptime(right_time,format_string)
            left_study_right= (date_obj - today).days / 30
            if left_study_right<6:
                new_issue= f"Student:{full_name} has critical situation\n"
                current_text=state.get("bot_analyze_text","")
                return {"bot_analyze_text": current_text+new_issue}
            elif left_study_right<12:
                new_issue= f"Student:{full_name} has warning situation\n"
                current_text=state.get("bot_analyze_text","")
                return {"bot_analyze_text": current_text+new_issue}
            else:
                new_issue= f"Student:{full_name} has good situation\n"
                current_text=state.get("bot_analyze_text","")
                return {"bot_analyze_text": current_text+new_issue}
    if not found:
        new_issue = f"Student: {full_name}, Details: Not found in database\n"
    current_text= state.get("bot_analyze_text","")
    return {"bot_analyze_text": current_text+new_issue}

async def recommendation_agent(state: State):
    print("Third agent is working")
    all_issues = state.get("bot_analyze_text","")
    result= "Hi, there is result information about students:\n"
    course_text = state.get("course_data", "")
    full_report = result+all_issues+course_text
    return {"final_text": full_report}

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
    
    current_text=state.get("bot_analyze_text","")
    return{"bot_analyze_text": current_text+verdict}

def route_after_status(state: State):
    allowed = state.get("is_allowed",True)

    if not allowed:
        return "go_to_analytics"
    else:
        return "go_to_end"

graph=StateGraph(State)

graph.add_node("progress_node", progress_agent)
graph.add_node("study_right_node", study_right_agent)
graph.add_node("recommendation_node", recommendation_agent)
graph.add_node("status_node",status_agent)
graph.add_node("analytics_node",analytics_agent)
graph.add_node("course_node",course_agent)


graph.add_edge(START, "progress_node")
graph.add_edge("progress_node", "study_right_node")
graph.add_edge("study_right_node", "status_node")     
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
        "student_name": "Nikita Mopsov",
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

    print("\nFinal text from final_text")
    print(result["final_text"])
    
    print("Is student allowed?:", result["is_allowed"])

asyncio.run(main())