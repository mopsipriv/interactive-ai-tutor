import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dialog_states import incoming_commands, get_user_session, UserState
from draft_graph import app as graph

app = FastAPI(title="OpenClaw FSM Gateway")

class IncomingMessage(BaseModel):
    user_id: str
    text: str

STATIC_COMMANDS = {
    "/help": "📜 Available commands:\n/start — Log in\n/logout — Log out\n/profile — My profile\n/help — Help",
    "help": "📜 Available commands:\n/start — Log in\n/logout — Log out\n/profile — My profile\n/help — Help",
}

@app.post("/webhook")
async def handle_message(payload: IncomingMessage):
    user_id = payload.user_id
    text = payload.text.strip()
    clean_text = text.lower()

    session = get_user_session(user_id)
    current_state = session.get("state", UserState.UNAUTH)

    if current_state != UserState.AUTHORIZED:
        response_text = await incoming_commands(user_id, text)
        return {"type": "direct_reply", "text": response_text}

    if clean_text in ["/logout", "logout"]:
        response_text = await incoming_commands(user_id, text)
        return {"type": "direct_reply", "text": response_text}

    if clean_text in STATIC_COMMANDS:
        return {"type": "direct_reply", "text": STATIC_COMMANDS[clean_text]}

    user_data = session.get("user_data", {})
    user_role = session.get("role", "student")

    graph_state = {
        "command": "ask",
        "user_role": user_role,
        "rag_query": text,
        "filter_name": f"{user_data.get('fname', '')} {user_data.get('lname', '')}".strip(),
        "teacher_id": user_data.get("idteacher", 0),
        "user_id": user_id
    }

    graph_result = await graph.ainvoke(graph_state)
    final_text = graph_result.get("rag_answer") or graph_result.get("final_text") or "Запрос обработан."

    return {"type": "llm_reply", "text": final_text}