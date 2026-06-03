# ⚡ JobMatch AI v2.0 — Real-Time Agentic Recruitment Platform

> **5 AI agents stream career intelligence in real-time** — live job matching, skill gap analysis, AI mock interviews, cover letters, salary prediction, and PDF reports. All powered by GPT-4o + LangGraph + Adzuna API.

![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-1.1-blue)
![GPT-4o](https://img.shields.io/badge/GPT--4o-OpenAI-412991?logo=openai)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

---

## 🚀 Quick Start (Local Development)

### 1. Clone & configure
```bash
git clone https://github.com/yourname/jobmatch-ai.git
cd jobmatch-ai

# Backend secrets
cp backend/.env.example backend/.env
# Edit backend/.env and add:
#   OPENAI_API_KEY=sk-...
#   ADZUNA_APP_ID=...
#   ADZUNA_APP_KEY=...
```

### 2. Start Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** 🎉

---

## 🐳 Production Deployment (Docker)

### Prerequisites
- Docker Desktop installed
- API keys ready

### One-command deploy
```bash
# 1. Set your API keys in backend/.env
cp backend/.env.example backend/.env
# Edit backend/.env

# 2. Build & launch all services
docker-compose up --build -d

# 3. Open the app
# http://localhost:80   → Full app via Nginx
# http://localhost:3000 → Frontend direct
# http://localhost:8000 → Backend API direct
```

### Stop
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f backend    # backend logs
docker-compose logs -f frontend   # frontend logs
docker-compose logs -f nginx      # nginx logs
```

---

## 🧠 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Nginx (:80)                         │
│          /  → frontend:3000   /api/ → backend:8000      │
└──────────────────┬────────────────────┬─────────────────┘
                   │                    │
         ┌─────────▼────────┐  ┌───────▼ ─────────────┐
         │  Next.js 14      │  │  FastAPI + LangGraph │
         │  (frontend:3000) │  │  (backend:8000)      │
         └──────────────────┘  └───────┬──────────────┘
                                       │  SSE Stream
                               ┌───────▼─────────────────────────────┐
                               │         LangGraph StateGraph        │
                               │                                     │
                               │  resume_agent                       │
                               │       ↓                             │
                               │  matching_agent                     │
                               │       ↓ (conditional routing)       │
                               │  skill_gap_agent                    │
                               │       ↓                             │
                               │  interview_agent                    │
                               │       ↓                             │
                               │  career_agent → END                 │
                               └─────────────────────────────────────┘
```

---

## 🤖 5 AI Agents

| Agent | LangGraph Node | Tools Used |
|---|---|---|
| **Resume Intelligence** | `resume_agent` | PyMuPDF + GPT-4o structured extraction |
| **Semantic Job Matching** | `matching_agent` | Adzuna API + GPT-4o scoring |
| **Skill Gap Analyser** | `skill_gap_agent` | GPT-4o vs job requirements |
| **AI Mock Interview** | `interview_agent` | GPT-4o question generation + evaluation |
| **Career War Room** | `career_agent` | GPT-4o salary prediction + verdict |

---

## ✨ Features

- **Real-Time SSE Streaming** — watch all 5 agents work live
- **LangGraph StateGraph** — shared state, conditional routing, session checkpointing
- **Live Job Discovery** — Adzuna API + LinkedIn/Indeed/Naukri deep links
- **AI Cover Letter Generator** — 3 tones × any job → GPT-4o letter in seconds  
- **Interactive Mock Interview** — type answers → GPT-4o scores + coaches you
- **ATS Resume Scorer** — know your ATS compatibility before applying
- **Application Tracker** — Kanban: Saved → Applied → Interview → Offer
- **PDF Report Export** — download beautiful branded analysis report
- **localStorage Persistence** — analysis survives page refresh
- **Landing Page** — full SaaS-style marketing page

---

## 🔑 Environment Variables

```env
# backend/.env

# Required
OPENAI_API_KEY=sk-proj-...

# Required for live jobs (get free at https://developer.adzuna.com)
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

---

## 📁 Project Structure

```
jobseekerproject/
├── backend/
│   ├── agents/
│   │   ├── resume_agent.py          # GPT-4o skill extraction
│   │   ├── matching_agent.py        # Adzuna + job scoring
│   │   ├── skill_graph_agent.py     # Gap analysis
│   │   ├── interview_agent.py       # Question generation
│   │   └── career_guidance_agent.py # Salary prediction
│   ├── langgraph_orchestrator.py    # ← LangGraph StateGraph pipeline
│   ├── main.py                      # FastAPI endpoints
│   ├── job_discovery.py             # Adzuna API client
│   ├── report_generator.py          # PDF report (reportlab)
│   ├── utils/
│   │   ├── parser.py               # PyMuPDF resume parser
│   │   └── masker.py               # PII masking
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx                # Landing page
│   │   └── dashboard/page.tsx      # Main dashboard (7 tabs)
│   ├── Dockerfile
│   └── next.config.ts
├── nginx.conf                       # Reverse proxy
├── docker-compose.yml               # One-command deploy
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **AI Orchestration** | LangGraph 1.1 (StateGraph, SqliteSaver) |
| **LLM** | OpenAI GPT-4o (via LangChain) |
| **Backend** | FastAPI + Uvicorn |
| **Streaming** | Server-Sent Events (SSE) |
| **Resume Parsing** | PyMuPDF |
| **PDF Reports** | ReportLab |
| **Job Data** | Adzuna REST API |
| **Frontend** | Next.js 14 + Tailwind CSS v4 |
| **State** | localStorage + LangGraph SqliteSaver |
| **Proxy** | Nginx Alpine |
| **Containers** | Docker + Docker Compose |

---

## 📄 License

MIT — free to use, modify, and deploy.

---

*Built with GPT-4o + LangGraph + Adzuna API + Next.js*
