from langgraph.graph import StateGraph, START, END
from agents.state import State
from database.mock_db import get_student_from_db

async def load_student_node(state: State):
    current_id = state["student_id"]
    result = await get_student_from_db(current_id)
    return {"student_data": str(result)}

async def format_answer_node(state:State):
    data=state["student_data"]
    if "Not found" in data:
        text = "Error:Student was not found"
    else:
        text = f"Data from database{data}"
        
    return {"final_text": text}

graph=StateGraph(State)

graph.add_node("db_node",load_student_node)
graph.add_node("ai_node",format_answer_node)

graph.add_edge(START, "db_node")
graph.add_edge("db_node","ai_node")
graph.add_edge("ai_node",END)

app=graph.compile()