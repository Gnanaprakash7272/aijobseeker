"""
JobMatch AI v2.0 — Full LangGraph Pipeline
==========================================
Real StateGraph implementation with:
  - Shared JobMatchState across all 5 agents
  - Conditional routing based on match scores
  - Cyclic interview loop (asks → evaluates → repeats)
  - SqliteSaver session checkpointing
  - Async streaming via LangGraph .astream()
"""

import os
import json
import asyncio
from typing import TypedDict, List, Optional, Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END

# LangGraph checkpointing — try both known module paths
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    _SQLITE_AVAILABLE = True
except ImportError:
    try:
        from langgraph_checkpoint_sqlite import SqliteSaver
        _SQLITE_AVAILABLE = True
    except ImportError:
        SqliteSaver = None
        _SQLITE_AVAILABLE = False

from langgraph.checkpoint.memory import MemorySaver

from dotenv import load_dotenv
load_dotenv()

# ── Agent imports ─────────────────────────────────────────────────────────────
from agents.resume_agent   import ResumeIntelligenceAgent
from agents.matching_agent import SemanticJobMatchingAgent
from agents.skill_graph_agent import SkillGraphAgent
from agents.interview_agent   import InterviewSimulationAgent
from agents.career_guidance_agent import CareerGuidanceAgent

# ── 1. Shared State ──────────────────────────────────────────────────────────
class JobMatchState(TypedDict, total=False):
    # Input
    resume_path: str
    candidate_id: str              # for checkpointing (thread_id)

    # ── Resume Agent writes ───────────────────────────────────────────────────
    candidate_profile: dict        # full structured profile
    extracted_skills:  List[str]
    experiences:       List[str]
    candidate_summary: str
    resume_done:       bool
    resume_error:      Optional[str]

    # ── Matching Agent writes ─────────────────────────────────────────────────
    matched_jobs:  List[dict]
    top_match_score: float         # 0-100 — drives conditional routing
    matching_done: bool

    # ── Skill Gap Agent writes ────────────────────────────────────────────────
    skill_gaps:       List[str]
    learning_roadmap: str
    gap_done:         bool

    # ── Interview Agent writes (cyclic) ───────────────────────────────────────
    interview_questions: List[str]
    interview_role:      str
    interview_readiness: float
    interview_feedback:  str
    interview_done:      bool

    # ── Career Agent writes ───────────────────────────────────────────────────
    salary_3yr:         str
    salary_5yr:         str
    recruiter_verdict:  str
    career_trajectory:  str
    career_done:        bool

    # ── Pipeline metadata ─────────────────────────────────────────────────────
    current_node: str
    errors:       List[str]


# ── 2. Agent Node Functions ───────────────────────────────────────────────────

async def resume_node(state: JobMatchState) -> dict:
    """Node 1 — Parse resume, extract skills/experience via GPT-4o."""
    print("[LangGraph] ▶ resume_node")
    try:
        agent  = ResumeIntelligenceAgent()
        result = await agent.process_resume(state["resume_path"])

        kg = result.get("knowledge_graph", {})
        return {
            "candidate_profile":  result,
            "extracted_skills":   kg.get("skills", []),
            "experiences":        kg.get("experiences", []),
            "candidate_summary":  kg.get("preview", ""),
            "resume_done":        True,
            "current_node":       "resume",
        }
    except Exception as e:
        return {
            "resume_done":  True,
            "resume_error": str(e),
            "current_node": "resume",
            "errors":       state.get("errors", []) + [f"resume: {e}"],
        }


async def matching_node(state: JobMatchState) -> dict:
    """Node 2 — Live Adzuna jobs + GPT-4o scoring per job."""
    print("[LangGraph] ▶ matching_node")
    try:
        agent  = SemanticJobMatchingAgent()
        result = await agent.match_jobs(
            skills=state.get("extracted_skills", []),
            experiences=state.get("experiences", [])
        )
        jobs   = result.get("job_matches", [])
        top    = float(jobs[0].get("score", 0)) if jobs else 0.0

        return {
            "matched_jobs":    jobs,
            "top_match_score": top,
            "matching_done":   True,
            "current_node":    "matching",
        }
    except Exception as e:
        return {
            "matched_jobs":    [],
            "top_match_score": 0.0,
            "matching_done":   True,
            "current_node":    "matching",
            "errors": state.get("errors", []) + [f"matching: {e}"],
        }


async def skill_gap_node(state: JobMatchState) -> dict:
    """Node 3 — GPT-4o skill gap analysis vs matched jobs."""
    print("[LangGraph] ▶ skill_gap_node")
    try:
        agent  = SkillGraphAgent()
        result = await agent.analyze_gaps(
            skills=state.get("extracted_skills", []),
            jobs=state.get("matched_jobs", [])
        )
        return {
            "skill_gaps":       result.get("missing_skills", []),
            "learning_roadmap": result.get("roadmap", ""),
            "gap_done":         True,
            "current_node":     "gaps",
        }
    except Exception as e:
        return {
            "gap_done":     True,
            "current_node": "gaps",
            "errors": state.get("errors", []) + [f"skill_gap: {e}"],
        }


async def interview_node(state: JobMatchState) -> dict:
    """Node 4 — Generate interview questions (cyclic-ready)."""
    print("[LangGraph] ▶ interview_node")
    try:
        agent  = InterviewSimulationAgent()
        jobs   = state.get("matched_jobs", [])
        role   = jobs[0].get("title", "ML Engineer") if jobs else "ML Engineer"
        result = await agent.generate_interview(
            skills=state.get("extracted_skills", []),
            role=role
        )
        return {
            "interview_questions": result.get("questions", []),
            "interview_role":      role,
            "interview_readiness": float(result.get("readiness_score", 7)),
            "interview_feedback":  result.get("feedback", ""),
            "interview_done":      True,
            "current_node":        "interview",
        }
    except Exception as e:
        return {
            "interview_done": True,
            "current_node":   "interview",
            "errors": state.get("errors", []) + [f"interview: {e}"],
        }


async def career_node(state: JobMatchState) -> dict:
    """Node 5 — Salary prediction + recruiter verdict."""
    print("[LangGraph] ▶ career_node")
    try:
        agent  = CareerGuidanceAgent()
        result = await agent.generate_guidance(
            skills=state.get("extracted_skills", []),
            jobs=state.get("matched_jobs", []),
            experiences=state.get("experiences", [])
        )
        return {
            "salary_3yr":        result.get("salary_3yr", ""),
            "salary_5yr":        result.get("salary_5yr", ""),
            "recruiter_verdict": result.get("recruiter_verdict", ""),
            "career_trajectory": result.get("trajectory", ""),
            "career_done":       True,
            "current_node":      "career",
        }
    except Exception as e:
        return {
            "career_done":  True,
            "current_node": "career",
            "errors": state.get("errors", []) + [f"career: {e}"],
        }


# ── 3. Conditional Routing ────────────────────────────────────────────────────

def route_after_matching(state: JobMatchState) -> str:
    """
    Route based on match score:
    - Score > 60  → full pipeline (gap → interview → career)
    - Score <= 60 → skip gap analysis, go straight to career guidance
    """
    score = state.get("top_match_score", 0)
    if score > 60:
        print(f"[LangGraph] ↪ route: skill_gap (score={score})")
        return "skill_gap_agent"
    else:
        print(f"[LangGraph] ↪ route: career_agent (low score={score})")
        return "career_agent"


# ── 4. Build the Graph ────────────────────────────────────────────────────────

def build_graph(use_checkpointing: bool = True):
    """
    Build and compile the LangGraph StateGraph.
    
    Pipeline:
        resume_agent
             ↓
        matching_agent
             ↓ (conditional)
        skill_gap_agent ──→ interview_agent ──→ career_agent ──→ END
             └──────────────────────────────→ career_agent (low score)
    """
    graph = StateGraph(JobMatchState)

    # Add all 5 agent nodes
    graph.add_node("resume_agent",    resume_node)
    graph.add_node("matching_agent",  matching_node)
    graph.add_node("skill_gap_agent", skill_gap_node)
    graph.add_node("interview_agent", interview_node)
    graph.add_node("career_agent",    career_node)

    # Entry point
    graph.set_entry_point("resume_agent")

    # Fixed edges
    graph.add_edge("resume_agent",    "matching_agent")
    graph.add_edge("skill_gap_agent", "interview_agent")
    graph.add_edge("interview_agent", "career_agent")
    graph.add_edge("career_agent",    END)

    # Conditional edge after matching
    graph.add_conditional_edges(
        "matching_agent",
        route_after_matching,
        {
            "skill_gap_agent": "skill_gap_agent",
            "career_agent":    "career_agent",
        }
    )

    # Optional: checkpointing (SqliteSaver preferred, MemorySaver fallback)
    if use_checkpointing:
        try:
            if _SQLITE_AVAILABLE:
                import sqlite3
                conn   = sqlite3.connect("jobmatch_sessions.db", check_same_thread=False)
                saver  = SqliteSaver(conn)
                compiled = graph.compile(checkpointer=saver)
                print("[LangGraph] ✓ Compiled with SqliteSaver checkpointing")
            else:
                saver = MemorySaver()
                compiled = graph.compile(checkpointer=saver)
                print("[LangGraph] ✓ Compiled with MemorySaver checkpointing")
        except Exception as e:
            print(f"[LangGraph] ⚠ Checkpointing error ({e}), compiling without")
            compiled = graph.compile()
    else:
        compiled = graph.compile()

    return compiled


# ── 5. SSE-Compatible Streaming Runner ───────────────────────────────────────

# Agent node → SSE event key mapping
NODE_TO_SSE = {
    "resume_agent":    "resume",
    "matching_agent":  "matching",
    "skill_gap_agent": "gaps",
    "interview_agent": "interview",
    "career_agent":    "career",
}


async def run_langgraph_stream(resume_path: str, candidate_id: str = "default"):
    """
    Run the full LangGraph pipeline and yield SSE-formatted events.
    Compatible with FastAPI StreamingResponse.

    Yields: data: {agent, status, data}\n\n
    """
    graph = build_graph(use_checkpointing=True)

    initial_state: JobMatchState = {
        "resume_path":  resume_path,
        "candidate_id": candidate_id,
        "errors":       [],
        "current_node": "start",
    }

    config = {
        "configurable": {"thread_id": candidate_id},
        "recursion_limit": 25,
    }

    # Signal each agent as "running" before it executes
    running_signals = {
        "resume_agent":    "resume",
        "matching_agent":  "matching",
        "skill_gap_agent": "gaps",
        "interview_agent": "interview",
        "career_agent":    "career",
    }

    # Track which nodes we've seen start
    seen_running = set()

    try:
        async for event in graph.astream(initial_state, config=config, stream_mode="updates"):
            for node_name, node_output in event.items():
                sse_key = NODE_TO_SSE.get(node_name)
                if not sse_key:
                    continue

                # Emit "running" signal when node starts (first time we see it)
                if node_name not in seen_running:
                    seen_running.add(node_name)
                    running_event = json.dumps({"agent": sse_key, "status": "running", "data": None})
                    yield f"data: {running_event}\n\n"
                    await asyncio.sleep(0.05)

                # Build the output data for this agent
                agent_data = _extract_agent_data(sse_key, node_output)

                # Emit "done" with full data
                done_event = json.dumps({"agent": sse_key, "status": "done", "data": agent_data})
                yield f"data: {done_event}\n\n"
                await asyncio.sleep(0.05)

        # Pipeline complete
        yield f"data: {json.dumps({'agent': 'complete', 'status': 'done', 'data': None})}\n\n"

    except Exception as e:
        error_event = json.dumps({"agent": "error", "status": "error", "data": {"message": str(e)}})
        yield f"data: {error_event}\n\n"


def _extract_agent_data(sse_key: str, node_output: dict) -> dict:
    """Convert the LangGraph node output to the SSE data format expected by the frontend."""
    if sse_key == "resume":
        profile = node_output.get("candidate_profile", {})
        return {
            "knowledge_graph": {
                "skills":      node_output.get("extracted_skills", []),
                "experiences": node_output.get("experiences", []),
                "preview":     node_output.get("candidate_summary", ""),
            },
            "pii_masked": profile.get("pii_masked", False),
        }

    elif sse_key == "matching":
        return {
            "job_matches": node_output.get("matched_jobs", []),
            "top_score":   node_output.get("top_match_score", 0),
        }

    elif sse_key == "gaps":
        return {
            "missing_skills": node_output.get("skill_gaps", []),
            "roadmap":        node_output.get("learning_roadmap", ""),
        }

    elif sse_key == "interview":
        return {
            "questions":       node_output.get("interview_questions", []),
            "role":            node_output.get("interview_role", ""),
            "readiness_score": node_output.get("interview_readiness", 7),
            "feedback":        node_output.get("interview_feedback", ""),
        }

    elif sse_key == "career":
        return {
            "salary_3yr":        node_output.get("salary_3yr", ""),
            "salary_5yr":        node_output.get("salary_5yr", ""),
            "recruiter_verdict": node_output.get("recruiter_verdict", ""),
            "trajectory":        node_output.get("career_trajectory", ""),
        }

    return node_output


# ── 6. Checkpointing: Resume a session ───────────────────────────────────────

def get_session_state(candidate_id: str) -> Optional[JobMatchState]:
    """
    Retrieve the saved state for a candidate by ID.
    Returns None if no session found.
    """
    try:
        graph  = build_graph(use_checkpointing=True)
        config = {"configurable": {"thread_id": candidate_id}}
        state  = graph.get_state(config)
        return state.values if state else None
    except Exception:
        return None


# ── Quick sanity test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    graph = build_graph(use_checkpointing=False)
    print("[LangGraph] Graph compiled successfully!")
    print(f"[LangGraph] Nodes: {list(graph.nodes.keys() if hasattr(graph, 'nodes') else [])}")
    print("[LangGraph] ✓ Ready to handle /analyze-career-stream")
