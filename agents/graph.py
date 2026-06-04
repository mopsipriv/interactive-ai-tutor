from langgraph.graph import StateGraph, START, END
from agents.state import State
from database.db_connector import get_student_from_db, get_courses_from_db, get_student_enrollments

async def load_student_node(state: State):
    current_id = state["student_id"]
    result = await get_student_from_db(current_id)
    return {"student_data": str(result)}

async def load_course_node(state: State):
    current_id= state["course_id"]
    result= await get_courses_from_db(current_id)
    return {"course_data": str(result)}

async def load_enrollment_node(state: State):
    current_id = state["student_id"]
    result = await get_student_enrollments(current_id)
    return {"enrollments": result}

async def check_access_node(state: State):
    enrollments = state["enrollments"]
    is_allowed = False 
    
    for enrollment in enrollments:
        if enrollment["idcourse"]==3 and enrollment["status"]=="completed":
            is_allowed=True
            break

    return {"is_allowed": is_allowed}

async def format_answer_node(state:State):
    data=state["student_data"]
    course_data= state["course_data"]
    is_allowed = state["is_allowed"]
    if "Not found" in data:
        text = "Error: Student and course were not found"
    else:
        access_status = "Accessed to the project" if is_allowed else "Access blocked (Basic course is not passed)"
        text = (
            f"Data from database:"
            f"Student: {data}\n"
            f"Course:{course_data}\n"
            f"Status of access:{access_status}\n")

        
    return {"final_text": text}

graph=StateGraph(State)

graph.add_node("db_node", load_student_node)
graph.add_node("course_node", load_course_node)
graph.add_node("enrollment_node", load_enrollment_node)
graph.add_node("check_node", check_access_node)
graph.add_node("ai_node", format_answer_node)


graph.add_edge(START, "db_node")
graph.add_edge("db_node", "course_node")
graph.add_edge("course_node", "enrollment_node")
graph.add_edge("enrollment_node", "check_node")
graph.add_edge("check_node", "ai_node")         
graph.add_edge("ai_node", END)

app=graph.compile()