## Research and Technology Choices

### LangGraph

I chose LangGraph because I needed agents that could communicate with each other and handle different situations differently. For example, when a teacher asks for a risk report the system needs to run through several agents in sequence fetch students, analyze progress, check study rights, then generate the report. But when a student asks for course recommendations, it takes a completely different path. With LangGraph I can define these branches if this command was chosen, go this way, if another command, go a different way. A simple chain of functions would not handle this kind of conditional routing cleanly.

### MCP (Model Context Protocol)

MCP made it much easier to connect agents to tools and the database. Instead of agents calling database functions directly, they call MCP tools by name. This also meant that when I connected OpenClaw for Telegram, it automatically discovered all 25 tools from the MCP server without any extra configuration. It is a clean separation the agents do not need to know how the database works, just what tools are available.

### MySQL instead of Supabase

The original assignment suggested Supabase, but I chose MySQL because it is a straightforward relational database that runs on any server without depending on cloud platforms. Full control over the data, easy to set up with Docker, and fast for the kinds of queries this system needs. Supabase adds features like real-time subscriptions and a built-in REST API, but none of that was needed here. It would have been extra complexity for no benefit.

### RAG

Without RAG, the system would have two bad options: either hardcode all the answers (inflexible, breaks when courses change) or ask the LLM directly (it would make up answers about OAMK courses it does not actually know). RAG solves this by storing the real official course descriptions in a vector database and retrieving the relevant ones for each question. When a student asks about Linux Administration, the system finds the actual IN00DU04 course description and bases the answer on that not random information from training data.

### DeepSeek instead of Groq for Telegram

DeepSeek tokens are cheaper. For a Telegram bot that processes every message with system prompts and context, token cost adds up quickly. DeepSeek costs $0.14 per million input tokens which is much lower than comparable models, so the $2 budget covers thousands of interactions instead of hundreds.

### Working solo on a 3-person project

The project was designed for 3 students but I did it alone. It was not particularly difficult, it was interesting to learn new technologies hands-on. LangGraph, MCP, RAG, and APScheduler were all new to me at the start. Working alone actually helped keep the architecture consistent since every decision about the database, agents, and integrations was made with full understanding of how everything connects.
