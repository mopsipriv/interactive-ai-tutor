# Interactive AI Tutor Assistant

An AI-powered tutoring assistant for university tutors and students at OAMK (Oulu University of Applied Sciences). Built with LangGraph, MCP, and DeepSeek LLM. Supports two real degree programs: **TVT2025S-OHJ** (Finnish) and **DIN2025S** (English).

## Features

### Teacher
- Monitor student progress, credits, study rights, and risk status
- Enroll students in courses, update grades and enrollment status
- Approve or reject student enrollment requests
- View curriculum by year (TVT and DIN programs)
- View analytics — course stats, group performance
- AI-generated risk reports on login
- Query history logging
- Export reports (risk, analytics, courses)
- Morning brief on login (at-risk students + pending requests)

### Student
- View own academic profile and full study plan with progress indicators (✅🔄📋❌)
- Check project eligibility based on completed prerequisites
- Get AI-powered study recommendations (RAG-based)
- Request enrollment in courses
- Track status of enrollment requests
- Ask questions about curriculum, courses, and study guidelines

## Tech Stack

| Component | Technology |
|---|---|
| Agent framework | LangGraph 20+ agents, Router pattern |
| LLM | DeepSeek (`deepseek-v4-flash`) via OpenClaw |
| MCP server | FastMCP, 15+ tools |
| Database | MySQL 8.0 (`peppi_db`) |
| Authentication | bcrypt, teacher/student roles, 3-attempt lockout |
| RAG | Chroma + sentence-transformers (CPU-only), 88 chunks |
| Telegram | OpenClaw gateway |
| Infrastructure | Docker, docker-compose, GitHub Actions CI/CD |

## Programs in the System

**TVT2025S-OHJ** — Tietotekniikan tutkinto-ohjelma, Ohjelmistokehitys
- 4 years, 240 credits, taught in Finnish
- 36 real courses with official codes (IN00CS84, IN00DL11, etc.)

**DIN2025S** — Degree Programme in Information Technology
- 4 years, 240 credits, taught in English
- 34 courses with official OAMK codes (ID00CS34, ID00EK08, etc.)

## Database

- **15 students** (10 TVT + 5 DIN) with realistic progress scenarios
- **10 teachers** across 4 group cohorts (TVT24SPO, TVT25SPO, AVOVAY25S, DIN25SPO)
- **72 courses** from official OAMK curriculum
- **3 projects** with prerequisite checks (AI Chatbot, Web App, Mobile App)
- **42 enrollments** with realistic grade distribution

## Commands

### Teacher
```
profile    — Student profile by name or number
course     — Students in a specific course
enroll     — Enroll student in a course
grade      — Update student grade
status     — Update enrollment status
group      — All students in a group
bulk       — Enroll entire group in a course
courses    — All available courses
curriculum — Program curriculum by year
analytics  — Course or group analytics
risk       — At-risk student report
history    — Teacher query history
ask        — RAG-powered question answering
export     — Export reports to file
requests   — Pending enrollment requests
approve    — Approve or reject a request
me         — Teacher profile
password   — Change password
help       — Show all commands
```

### Student
```
profile      — Own academic profile
eligibility  — Project eligibility check
recommend    — AI course recommendations
courses      — All available courses
plan         — Full study plan with progress
ask          — RAG-powered question answering
request      — Request enrollment in a course
my_requests  — Track enrollment request status
password     — Change password
help         — Show all commands
```

## RAG Knowledge Base

The system uses RAG (Retrieval-Augmented Generation) with real OAMK course descriptions:

- `course_descriptions.txt` — DIN2025S course descriptions (English)
- `course_descriptions_tvt.txt` — TVT2025S-OHJ course descriptions (Finnish)
- `curriculum_guide.txt` — Program structure and prerequisites
- `student_faq.txt` — Student FAQ with real course codes
- `study_right_guide.txt` — Study right and credit pace guidelines
- `tutoring_calendar.txt` — Month-by-month tutoring calendar

Smart chunking: documents with `---` separators are chunked per course (one course = one chunk), others use character-based chunking with overlap.

## Run with Docker

```bash
# Clone and configure
git clone https://github.com/mopsipriv/interactive-ai-tutor.git
cd interactive-ai-tutor
cp agents/.env.example agents/.env  # fill in DB credentials and API keys
cp agents/.env .env

# Start all services
docker compose up -d

# Run interactive CLI
docker compose run --rm app
```

### Services
| Container | Description | Port |
|---|---|---|
| `peppi-mysql` | MySQL database | 3306 |
| `peppi-mcp` | FastMCP server (SSE) | 8000 |
| `peppi-app` | LangGraph CLI app | — |

## Run Locally

```bash
# Terminal 1 — MCP server
fastmcp run mcp_server.py --transport sse --host 0.0.0.0 --port 8000

# Terminal 2 — App
python -m agents.draft_graph
```

## Architecture

```
Telegram
   ↓
OpenClaw Gateway (DeepSeek LLM)
   ↓
MCP Server (FastMCP, 15+ tools)
   ↓
LangGraph (20+ agents, Router pattern)
   ↓
MySQL (peppi_db) + Chroma (RAG)
```

### Agent Flow
```
Input → router_by_command
   ├── Teacher commands → profile/enroll/grade/risk/analytics/...
   ├── Student commands → profile/plan/eligibility/ask/...
   └── Shared → curriculum/courses/password/help
```

## Security

- Passwords hashed with bcrypt (`$2b$12$...`)
- Teachers see only students in their own groups (via `group_cohort.idteacher`)
- Enrollment request ownership verified before approve/reject
- Password input via `getpass` (hidden from terminal)
- MySQL connection pooling (`aiomysql.create_pool`, maxsize=10)
- OpenClaw: Telegram allowlist (single user ID), dangerous commands denied

## CI/CD

GitHub Actions pipeline runs on push to `main` and `rag-implementation` branches:
- Lint and syntax checks
- Docker build verification

## Project Status

✅ LangGraph 20+ agents with Router pattern  
✅ FastMCP server with 15+ tools  
✅ MySQL database with real TVT + DIN curriculum  
✅ bcrypt authentication, teacher/student roles  
✅ RAG system with official OAMK course descriptions  
✅ Enrollment requests workflow  
✅ Analytics, risk reports, curriculum, export  
✅ Docker + docker-compose deployment  
✅ GitHub Actions CI/CD  
✅ OpenClaw + Telegram bot connected  
✅ Connection pooling, ownership checks, getpass security  
🔜 Full Telegram end-to-end command routing  
🔜 Morning Brief on teacher login  
🔜 Prerequisites check on enroll  
🔜 Inline Telegram buttons and MarkdownV2 formatting  

## Solo Development Note

This project was originally planned as a group project (2 students). Due to the partner being unresponsive for over a month, the entire implementation was completed solo. All architecture decisions, database design, agent logic, MCP integration, RAG system, Docker setup, and Telegram integration were designed and implemented by one person.
