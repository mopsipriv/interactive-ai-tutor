# Interactive AI Tutor

An AI-powered tutoring assistant for university tutors and students, built with LangGraph, MCP, and Groq LLM. Simulates a Peppi-like academic records system.

## Features

- **Teachers:** monitor student progress, credits, study rights, and project eligibility; enroll students, update grades; generate AI reports; view analytics and curriculum
- **Students:** view their own profile, check project eligibility, get AI recommendations, view study plan

## Tech stack

LangGraph (20+ agents) · MCP (15+ tools) · MySQL · Groq (Llama 3.3) · bcrypt authentication · Docker

## Run with Docker

```bash
# Start MySQL and MCP server
docker-compose up -d mysql mcp_server

# Run the application
docker run -it --rm --network interactive-ai-tutor_default \
  --env-file agents/.env \
  -e DB_HOST=mysql -e DB_USER=root -e DB_PASSWORD=admin \
  -e DB_NAME=peppi_db -e MCP_URL=http://peppi-mcp:8000/sse \
  interactive-ai-tutor-app python -m agents.draft_graph
```

## Run locally (development)

```bash
# Terminal 1 - MCP server
fastmcp run mcp_server.py --transport http

# Terminal 2 - Application  
python -m agents.draft_graph
```

## Status

✅ LangGraph + MCP integration, MySQL database, bcrypt auth, teacher/student roles, analytics, curriculum, Docker
🔜 RAG, Telegram/OpenClaw integration