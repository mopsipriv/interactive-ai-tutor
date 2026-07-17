# Interactive AI Tutor

An AI-powered tutoring assistant for university tutors and students, built with LangGraph, MCP, and Groq LLM. Simulates a Peppi-like academic records system.

## Features

- **Teachers:** monitor student progress, credits, study rights, and project eligibility; enroll students, update grades; generate AI reports and personalized student messages
- **Students:** view their own profile, check project eligibility, get AI recommendations

## Tech stack

LangGraph (19 agents) · MCP (13 tools) · MySQL · Groq (Llama 3.3) · bcrypt authentication

## Run

```bash
pip install -r requirements.txt
fastmcp run mcp_server.py --transport http   # terminal 1
python -m agents.draft_graph                  # terminal 2
```

## Status

✅ LangGraph + MCP integration, real database, auth, teacher/student roles
🔜 RAG, Telegram/OpenClaw integration, Docker Compose