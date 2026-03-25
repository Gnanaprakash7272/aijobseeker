from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import os
import shutil
import json
import asyncio
from pydantic import BaseModel
from dotenv import load_dotenv
from agents.resume_agent import ResumeIntelligenceAgent
from agents.matching_agent import SemanticJobMatchingAgent
from agents.skill_graph_agent import SkillGraphAgent
from agents.interview_agent import InterviewSimulationAgent
from agents.career_guidance_agent import CareerGuidanceAgent
from job_discovery import (
    fetch_adzuna_jobs,
    generate_linkedin_search_url,
    generate_indeed_search_url,
    generate_naukri_search_url,
    DEMO_LOCAL_JOBS,
)
from report_generator import generate_report
from fastapi.responses import StreamingResponse, Response

# ── LangGraph pipeline (primary) ──────────────────────────────────────────────
try:
    from langgraph_orchestrator import run_langgraph_stream
    LANGGRAPH_AVAILABLE = True
    print("[main] ✓ LangGraph pipeline loaded")
except Exception as _lg_err:
    LANGGRAPH_AVAILABLE = False
    print(f"[main] ⚠ LangGraph unavailable ({_lg_err}), using legacy pipeline")


app = FastAPI(title="JobMatch AI v2.0 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def sse_event(agent: str, status: str, data: dict) -> str:
    """Format a Server-Sent Event message."""
    payload = json.dumps({"agent": agent, "status": status, "data": data})
    return f"data: {payload}\n\n"

async def run_pipeline_stream(file_path: str):
    """Generator that runs each agent and yields SSE events."""
    openai_key = os.getenv("OPENAI_API_KEY")
    
    # ── Agent 1: Resume Intelligence ──
    # ── Agent 1: Resume Intelligence (Real PyMuPDF + GPT-4o) ──
    yield sse_event("resume", "running", {"message": "Parsing resume with PyMuPDF and masking PII..."})
    resume_result = {}
    skills: list = []
    experiences: list = []
    try:
        resume_agent = ResumeIntelligenceAgent(api_key=openai_key)
        resume_result = await resume_agent.process_resume(file_path)
        kg = resume_result.get("knowledge_graph", {})
        if isinstance(kg, dict):
            skills = kg.get("skills", [])
            experiences = kg.get("experiences", [])
        yield sse_event("resume", "done", resume_result)
    except Exception as e:
        yield sse_event("resume", "error", {"message": str(e)})

    # ── Agent 2: Real Job Matching via Adzuna + GPT-4o scoring ──
    yield sse_event("matching", "running", {"message": f"Searching live jobs for: {', '.join(skills[:4])}..."})
    job_matches: list = []
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        # 1. Pull real live jobs from Adzuna using extracted skills
        live_jobs = await fetch_adzuna_jobs(skills, "india", results_per_page=8)
        if not live_jobs:
            live_jobs = DEMO_LOCAL_JOBS[:6]

        # 2. If OpenAI available, score each job vs candidate profile using GPT-4o
        if openai_key and skills:
            llm = ChatOpenAI(model="gpt-4o", api_key=openai_key, temperature=0)
            candidates_str = ", ".join(skills[:10])
            
            for job in live_jobs[:6]:
                job_desc = f"{job['title']} at {job['company']} — {job.get('description','')[:200]}"
                score_prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a senior technical recruiter. Return ONLY a JSON object with 2 keys: 'score' (integer 60-99) and 'matched_skills' (list of 2-3 strings from candidate skills that match this role). No markdown."),
                    ("user", f"Candidate skills: {candidates_str}\n\nJob: {job_desc}")
                ])
                try:
                    resp = await (score_prompt | llm).ainvoke({})
                    raw = resp.content.strip()
                    # strip markdown if present
                    raw = raw.replace("```json","").replace("```","").strip()
                    parsed = json.loads(raw)
                    job["score"] = f"{parsed.get('score', 85)}%"
                    job["matched_skills"] = parsed.get("matched_skills", skills[:2])
                except Exception:
                    job["score"] = "85%"
                    job["matched_skills"] = skills[:2]
            
            # Sort by score descending
            live_jobs = sorted(live_jobs[:6], key=lambda j: int(str(j.get("score","75")).replace("%","")), reverse=True)
        else:
            for i, job in enumerate(live_jobs[:6]):
                job["score"] = f"{95 - i*3}%"
                job["matched_skills"] = skills[:2] if skills else ["Python", "AI"]

        job_matches = live_jobs[:6]
        yield sse_event("matching", "done", {"job_matches": job_matches})
    except Exception as e:
        yield sse_event("matching", "error", {"message": str(e)})

    # ── Agent 3: Real Skill Gap Analysis via GPT-4o ──
    yield sse_event("gaps", "running", {"message": "GPT-4o comparing your skills vs top job requirements..."})
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        if openai_key and skills and job_matches:
            llm = ChatOpenAI(model="gpt-4o", api_key=openai_key, temperature=0)
            top_jobs_str = "; ".join([f"{j['title']} at {j['company']}" for j in job_matches[:3]])
            gap_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a senior technical career coach. Return a JSON object with 2 keys: 'missing_skills' (list of 4 specific technical skills the candidate needs for these roles), 'roadmap' (one actionable sentence). No markdown."),
                ("user", f"Candidate has: {', '.join(skills[:10])}\nTop matched jobs: {top_jobs_str}\nExperience: {'; '.join(experiences[:3]) if experiences else 'Not specified'}")
            ])
            resp = await (gap_prompt | llm).ainvoke({})
            raw = resp.content.strip().replace("```json","").replace("```","").strip()
            gap_data = json.loads(raw)
        else:
            # Basic set difference fallback
            target = {"Kubernetes", "MLOps", "GraphRAG", "RLHF", "Vector Databases", "LangGraph"}
            have = set(s.lower() for s in skills)
            missing = [s for s in target if s.lower() not in have][:4]
            gap_data = {
                "missing_skills": missing or ["GraphRAG", "Kubernetes", "MLOps", "RLHF"],
                "roadmap": "Focus on deploying LLMs at scale with MLOps tooling, then advance to RLHF and GraphRAG."
            }

        yield sse_event("gaps", "done", gap_data)
    except Exception as e:
        yield sse_event("gaps", "error", {"message": str(e)})

    # ── Agent 4: Real Personalised Interview Questions via GPT-4o ──
    yield sse_event("interview", "running", {"message": "GPT-4o generating role-specific interview questions..."})
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
        import re

        top_job_title = job_matches[0]["title"] if job_matches else "ML Engineer"
        
        if openai_key and skills:
            llm = ChatOpenAI(model="gpt-4o", api_key=openai_key, temperature=0.4)
            q_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a senior technical interviewer at a FAANG company. Generate 4 challenging but fair interview questions. Return a JSON list of strings only. No markdown."),
                ("user", f"Role being interviewed for: {top_job_title}\nCandidate skills: {', '.join(skills[:8])}\nExperience: {'; '.join(experiences[:2]) if experiences else 'Various tech roles'}")
            ])
            resp = await (q_prompt | llm).ainvoke({})
            raw = resp.content.strip().replace("```json","").replace("```","").strip()
            m = re.search(r'\[.*?\]', raw, re.DOTALL)
            questions = json.loads(m.group()) if m else json.loads(raw)

            # GPT-4o readiness scoring
            score_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a strict technical recruiter. Return ONLY a JSON with 2 keys: 'readiness_score' (float 6.0-9.8) and 'feedback' (one constructive sentence). No markdown."),
                ("user", f"Evaluate this candidate for {top_job_title}:\nSkills: {', '.join(skills)}\nExperience entries: {len(experiences)}")
            ])
            sr = await (score_prompt | llm).ainvoke({})
            raw_s = sr.content.strip().replace("```json","").replace("```","").strip()
            score_data = json.loads(raw_s)
        else:
            questions = [
                f"How would you architect a production-ready {skills[0] if skills else 'ML'} pipeline from scratch?",
                "Explain the trade-offs between fine-tuning vs RAG for enterprise LLM applications.",
                "How do you monitor and mitigate model drift in a real-time inference system?",
                "Walk through a time you improved latency or throughput of an ML system significantly."
            ]
            score_data = {"readiness_score": 8.2, "feedback": "Strong profile. Add MLOps depth to differentiate at FAANG level."}

        yield sse_event("interview", "done", {
            "readiness_score": score_data.get("readiness_score", 8.2),
            "questions": questions,
            "feedback": score_data.get("feedback", "Strong technical depth."),
            "role": top_job_title
        })
    except Exception as e:
        yield sse_event("interview", "error", {"message": str(e)})

    # ── Agent 5: Real Career Trajectory + Salary Prediction via GPT-4o ──
    yield sse_event("career", "running", {"message": "Running Recruiter War Room simulation with GPT-4o..."})
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        if openai_key and skills:
            llm = ChatOpenAI(model="gpt-4o", api_key=openai_key, temperature=0.3)
            career_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a top-tier career strategist with 20 years recruiting at Google, OpenAI, and McKinsey. Return ONLY a JSON with 4 keys: 'trajectory' (2 sentences, specific), 'recruiter_verdict' (string like '3/3 Strong Hire'), 'salary_3yr' (realistic range string), 'salary_5yr' (realistic range string). No markdown."),
                ("user", f"Candidate profile:\nSkills: {', '.join(skills)}\nExperience: {'; '.join(experiences[:3]) if experiences else 'Technical roles'}\nTop job match: {job_matches[0]['title'] if job_matches else 'ML Engineer'} at {job_matches[0]['company'] if job_matches else 'Tech Company'}")
            ])
            resp = await (career_prompt | llm).ainvoke({})
            raw = resp.content.strip().replace("```json","").replace("```","").strip()
            career_data = json.loads(raw)
        else:
            career_data = {
                "trajectory": "Based on your technical profile, you are positioned for a Senior ML Engineer role within 18 months. Developing MLOps and distributed systems skills will accelerate your path to Staff Engineer within 4 years.",
                "recruiter_verdict": "2/3 Recruiters: Hire",
                "salary_3yr": "₹25L – ₹45L / $140k – $200k",
                "salary_5yr": "₹40L – ₹80L / $200k – $320k"
            }

        yield sse_event("career", "done", career_data)
    except Exception as e:
        yield sse_event("career", "error", {"message": str(e)})

    # ── Done ──
    yield sse_event("complete", "done", {"message": "All 5 agents complete."})
    if os.path.exists(file_path):
        os.remove(file_path)


@app.get("/")
async def health_check():
    return {"status": "online", "version": "2.0.0", "mode": "SSE Streaming"}


@app.get("/local-jobs")
async def local_jobs(skills: str = "", location: str = "india"):
    """Return live local jobs from Adzuna + LinkedIn / Indeed / Naukri search links."""
    skill_list = [s.strip() for s in skills.split(",") if s.strip()] if skills else []

    # Try real Adzuna jobs first
    adzuna_jobs = await fetch_adzuna_jobs(skill_list, location)
    local = adzuna_jobs if adzuna_jobs else DEMO_LOCAL_JOBS

    # Attach matched_skills based on provided skill list
    if skill_list:
        for job in local:
            if not job.get("matched_skills"):
                job["matched_skills"] = skill_list[:3]

    return {
        "jobs": local,
        "search_links": {
            "linkedin": generate_linkedin_search_url(skill_list, location.title()),
            "indeed":   generate_indeed_search_url(skill_list, location.title()),
            "naukri":   generate_naukri_search_url(skill_list),
        },
        "source": "Adzuna Live" if adzuna_jobs else "Curated Demo (Add ADZUNA_APP_ID for live)"
    }



@app.post("/analyze-career-stream")
async def analyze_career_stream(file: UploadFile = File(...)):
    """Real-time SSE streaming endpoint. Uses LangGraph StateGraph (with legacy fallback)."""
    import uuid
    temp_path    = f"temp_{file.filename}"
    candidate_id = str(uuid.uuid4())[:8]   # short unique session ID

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Choose pipeline: real LangGraph (primary) or legacy sequential (fallback)
    if LANGGRAPH_AVAILABLE:
        pipeline = run_langgraph_stream(temp_path, candidate_id=candidate_id)
    else:
        pipeline = run_pipeline_stream(temp_path)

    return StreamingResponse(
        pipeline,
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "X-Pipeline":        "LangGraph" if LANGGRAPH_AVAILABLE else "Legacy",
        }
    )


class InterviewAnswerRequest(BaseModel):
    question: str
    answer: str
    role: str = "ML Engineer"
    skills: list[str] = []

@app.post("/interview/evaluate")
async def evaluate_interview_answer(req: InterviewAnswerRequest):
    """GPT-4o evaluates a candidate's interview answer in real time."""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return {
            "score": 7.5,
            "feedback": "Good answer structure. Add API key for real GPT-4o evaluation.",
            "better_answer_hint": "Consider quantifying the impact of your work with metrics.",
            "stars": 3
        }

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model="gpt-4o", api_key=openai_key, temperature=0.2)
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a strict but fair senior technical interviewer.
Evaluate the candidate's answer to the interview question.
Return ONLY a JSON object (no markdown) with 4 keys:
- score: integer 1-10
- feedback: string (2 sentences: what was good, what was missing)
- better_answer_hint: string (one specific improvement tip)
- stars: integer 1-5 (1=poor, 3=average, 5=excellent)"""),
            ("user", f"Role: {req.role}\nCandidate skills: {', '.join(req.skills[:6])}\n\nQuestion: {req.question}\n\nCandidate's Answer: {req.answer}")
        ])
        resp = await (prompt | llm).ainvoke({})
        raw = resp.content.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        return {
            "score": 7,
            "feedback": f"Answer received. Evaluation error: {str(e)[:80]}",
            "better_answer_hint": "Structure your answer using STAR method (Situation, Task, Action, Result).",
            "stars": 3
        }



# Keep old endpoint for backwards compat
@app.post("/analyze-career")
async def analyze_career(file: UploadFile = File(...)):
    """Legacy endpoint."""
    raise HTTPException(status_code=308, detail="Use /analyze-career-stream with SSE.")


# ── Cover Letter Generator ────────────────────────────────────────────────────
class CoverLetterRequest(BaseModel):
    job_title: str
    company: str
    job_description: str = ""
    candidate_skills: list[str] = []
    candidate_experiences: list[str] = []
    candidate_summary: str = ""
    tone: str = "professional"  # professional | friendly | confident


@app.post("/cover-letter")
async def generate_cover_letter(req: CoverLetterRequest):
    """GPT-4o generates a personalised cover letter for a specific job."""
    openai_key = os.getenv("OPENAI_API_KEY")

    if not openai_key:
        return {
            "cover_letter": f"""Dear Hiring Manager at {req.company},

I am writing to express my strong interest in the {req.job_title} position at {req.company}. With expertise in {', '.join(req.candidate_skills[:4])}, I am confident in my ability to contribute meaningfully to your team.

[Add OPENAI_API_KEY to .env for a fully personalised GPT-4o generated letter]

Sincerely,
[Your Name]""",
            "word_count": 60,
            "tone_used": req.tone
        }

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model="gpt-4o", api_key=openai_key, temperature=0.7)

        tone_instruction = {
            "professional": "Write in a highly professional, formal tone — concise and impactful.",
            "friendly": "Write in a warm, personable tone while remaining professional.",
            "confident": "Write in a bold, confident tone that asserts the candidate's value proposition strongly."
        }.get(req.tone, "Write in a highly professional tone.")

        skills_str = ", ".join(req.candidate_skills[:8]) if req.candidate_skills else "various technical skills"
        exp_str    = "; ".join(req.candidate_experiences[:3]) if req.candidate_experiences else "professional experience"
        summary    = req.candidate_summary or f"A skilled professional with expertise in {skills_str}."

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a world-class career coach and professional writer.
{tone_instruction}
Write a compelling, personalised 3-paragraph cover letter (250-320 words).
- Paragraph 1: Strong opening hook mentioning the role and company specifically.
- Paragraph 2: 2-3 concrete achievements or skills that directly match this role.
- Paragraph 3: Forward-looking closing with a specific call to action.
Do NOT use placeholders like [Your Name] — the letter should end with 'Sincerely,' only.
Do NOT add any preamble, just output the letter directly."""),
            ("user", f"""Job: {req.job_title} at {req.company}
Job Description: {req.job_description[:400] if req.job_description else 'Not provided'}
Candidate Profile:
- Summary: {summary}
- Skills: {skills_str}
- Experience: {exp_str}""")
        ])

        resp = await (prompt | llm).ainvoke({})
        letter = resp.content.strip()
        word_count = len(letter.split())

        return {
            "cover_letter": letter,
            "word_count": word_count,
            "tone_used": req.tone,
            "target_role": req.job_title,
            "target_company": req.company
        }

    except Exception as e:
        return {
            "cover_letter": f"Error generating letter: {str(e)}",
            "word_count": 0,
            "tone_used": req.tone
        }


# ── Resume Score (ATS Check) ──────────────────────────────────────────────────
class ResumeScoreRequest(BaseModel):
    skills: list[str] = []
    experiences: list[str] = []
    job_title: str = "ML Engineer"


@app.post("/resume-score")
async def score_resume(req: ResumeScoreRequest):
    """GPT-4o scores the resume for ATS compatibility and overall strength."""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return {"ats_score": 72, "overall_score": 78, "suggestions": ["Add OPENAI_API_KEY for real scoring."]}

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model="gpt-4o", api_key=openai_key, temperature=0)
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an ATS (Applicant Tracking System) expert and senior recruiter.
Score the candidate's resume and return ONLY a JSON object (no markdown) with these keys:
- ats_score: integer 0-100 (ATS keyword match estimate)
- overall_score: integer 0-100 (overall resume strength)
- strengths: list of 3 strings (what's good)
- suggestions: list of 3 strings (specific improvements)
- verdict: string (one-line hiring verdict)"""),
            ("user", f"Target role: {req.job_title}\nSkills: {', '.join(req.skills)}\nExperience: {'; '.join(req.experiences[:4])}")
        ])
        resp = await (prompt | llm).ainvoke({})
        raw = resp.content.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        return {"ats_score": 75, "overall_score": 80, "suggestions": [str(e)[:100]], "strengths": [], "verdict": "Error"}


# ── PDF Report ────────────────────────────────────────────────────────────────
class ReportRequest(BaseModel):
    skills: list[str] = []
    experiences: list[str] = []
    summary: str = ""
    job_matches: list[dict] = []
    gap_data: dict = {}
    interview_data: dict = {}
    career_data: dict = {}
    ats_score: dict = {}
    candidate_name: str = "Candidate"


@app.post("/report/pdf")
async def generate_pdf_report(req: ReportRequest):
    """Generate and return a branded PDF career analysis report."""
    try:
        pdf_bytes = generate_report({
            "skills":         req.skills,
            "experiences":    req.experiences,
            "summary":        req.summary,
            "job_matches":    req.job_matches,
            "gap_data":       req.gap_data,
            "interview_data": req.interview_data,
            "career_data":    req.career_data,
            "ats_score":      req.ats_score,
        })
        filename = f"JobMatch_AI_Report_{req.candidate_name.replace(' ','_')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
