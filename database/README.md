# Interactive AI Tutor

An AI-powered tutoring assistant for university tutors and students, built with LangGraph, MCP, and Groq LLM. Simulates a Peppi-like academic records system.

## Features

**Teachers:**
- Monitor student progress, credits, study rights, and project eligibility
- Enroll students, update grades and enrollment status
- View analytics (course stats, group performance)
- View curriculum by semester
- Approve or reject student enrollment requests
- AI-generated risk reports and student recommendations
- Query history logging
- Export reports

**Students:**
- View own academic profile and study plan
- Check project eligibility
- Get AI-powered study recommendations (RAG-based)
- Request enrollment in courses
- Track status of enrollment requests
- Ask questions about curriculum and tutoring guidelines

## Tech stack

LangGraph (20+ agents) · MCP (15+ tools) · MySQL · Groq (Llama 3.3) · RAG (Chroma + sentence-transformers) · bcrypt authentication · Docker · CI/CD

## Run with Docker

```bash
docker-compose up -d mysql mcp_server

docker run -it --rm --network interactive-ai-tutor_default \
  --env-file agents/.env \
  -e DB_HOST=mysql -e DB_USER=root -e DB_PASSWORD=admin \
  -e DB_NAME=peppi_db -e MCP_URL=http://peppi-mcp:8000/sse \
  interactive-ai-tutor-app python -m agents.draft_graph
```

## Run locally

```bash
# Terminal 1
fastmcp run mcp_server.py --transport sse

# Terminal 2
python -m agents.draft_graph
```

## Status

✅ LangGraph + MCP, MySQL, bcrypt auth, teacher/student roles, analytics, curriculum, RAG, enrollment requests, Docker, CI/CD
🔜 Telegram/OpenClaw integration