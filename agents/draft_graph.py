from langgraph.graph import StateGraph, START, END
import asyncio
from typing_extensions import TypedDict

class State(TypedDict):
    student_id: int
    student_data: str
    
    course_id: int
    course_data: str

    enrollments: list
    is_allowed: bool

    final_text: str

    bot_analyze_text: str 
    
async def progress_agent(state: State):
    print("First agent is working")
    current_text = state.get("bot_analyze_text","")
    new_issue= "Student: Mops Mopsov, Details: Got only 35 ECTS out of 60\n"
    updated_text= current_text+new_issue
    return {"bot_analyze_text": updated_text}

async def study_right_agent(state: State):
    print("Second agent is working")
    current_text = state.get("bot_analyze_text","")
    new_issue = "Student: Sharik Sharikov, Details: Study right expires in 9 months\n"
    updated_text = current_text+new_issue
    return{"bot_analyze_text": updated_text}

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
    if current_text !="":
        return{"is_allowed":False}
    else:
        return {"is_allowed": True}
    
async def course_agent(state: State):
    print("Fifth agent is working")
    course_info="Course: Matematiikan perusteet tietotekniikassa 1, Status: 45/50 students enrolled\n"
    return {"course_data":course_info}

def route_after_status(state: State):
    allowed = state.get("is_allowed",True)

    if allowed==False:
        return "go_to_recommendation"
    else:
        return "go_to_end"

graph=StateGraph(State)

graph.add_node("progress_node", progress_agent)
graph.add_node("study_right_node", study_right_agent)
graph.add_node("recommendation_node", recommendation_agent)
graph.add_node("status_node",status_agent)
graph.add_node("course_node",course_agent)


graph.add_edge(START, "progress_node")
graph.add_edge("progress_node", "study_right_node")
graph.add_edge("study_right_node", "status_node")     
graph.add_conditional_edges(
    "status_node",
    route_after_status,
    {
        "go_to_recommendation": "recommendation_node",
        "go_to_end":END
    }
)
graph.add_edge("course_node","recommendation_node")
graph.add_edge("recommendation_node", END)

app=graph.compile()

async def main():
    initial_state = {
        "student_id": 0,
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