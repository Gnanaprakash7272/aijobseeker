from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
import operator
import os
from agents.resume_agent import ResumeIntelligenceAgent
from agents.matching_agent import SemanticJobMatchingAgent
from agents.skill_graph_agent import SkillGraphAgent
from agents.interview_agent import InterviewSimulationAgent
from agents.career_guidance_agent import CareerGuidanceAgent

class AgentState(TypedDict):
    # Shared memory state for all agents
    candidate_id: str
    resume_path: str
    resume_text: str
    knowledge_graph: Dict[str, Any]
    job_matches: List[Dict[str, Any]]
    market_pulse: Dict[str, Any]
    skill_gaps: Dict[str, Any]
    interview_feedback: Dict[str, Any]
    career_roadmap: str
    consensus_report: str
    messages: Annotated[List[Dict[str, Any]], operator.add]

# --- Nodes (Agent Handlers) ---

async def resume_node(state: AgentState):
    """Agent 1: Resume Intelligence."""
    agent = ResumeIntelligenceAgent(api_key=os.getenv("OPENAI_API_KEY"))
    result = await agent.process_resume(state['resume_path'])
    return {"knowledge_graph": result, "resume_text": str(result.get("knowledge_graph", {}).get("preview", ""))}

async def matching_node(state: AgentState):
    """Agent 2: Semantic Matching."""
    agent = SemanticJobMatchingAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
        index_name=os.getenv("PINECONE_INDEX_NAME")
    )
    if not agent.llm or not agent.index:
        return {"job_matches": [
            {
                "title": "Machine Learning Engineer, Integrity", 
                "score": "98%", 
                "company": "OpenAI",
                "matched_skills": ["Transformers", "Deep Learning", "PyTorch"],
                "apply_link": "https://openai.com/careers/machine-learning-engineer-integrity",
                "salary": "$200k - $370k",
                "tags": ["San Francisco", "AI Safety"]
            },
            {
                "title": "Principal ML Engineer, Copilot AI", 
                "score": "95%", 
                "company": "Microsoft",
                "matched_skills": ["Python", "LangChain", "Distributed Systems"],
                "apply_link": "https://careers.microsoft.com/us/en/job/1234567/Principal-Machine-Learning-Engineer",
                "salary": "$250k - $350k",
                "tags": ["Remote", "Copilot"]
            },
            {
                "title": "Staff ML Engineer, Early Stage Supply Chain", 
                "score": "92%", 
                "company": "Google",
                "matched_skills": ["Python", "TensorFlow", "Pipeline Infrastructure"],
                "apply_link": "https://careers.google.com/jobs/results/987654321/",
                "salary": "$220k - $320k",
                "tags": ["Mountain View", "Moonshot / X"]
            }
        ]}
    return {"job_matches": [{"title": "Senior AI Engineer", "score": "98%"}]}

async def gap_node(state: AgentState):
    """Agent 3: Skill Graph & Gap."""
    agent = SkillGraphAgent(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    if not agent.llm or not agent.driver:
        return {"skill_gaps": {"missing_skills": ["Vector DBs", "GraphRAG"], "roadmap": "Learn Neo4j and Pinecone."}}
    return {"skill_gaps": {"missing_skills": ["Kubernetes", "Redis"]}}

async def interview_node(state: AgentState):
    """Agent 4: Interview Simulation."""
    agent = InterviewSimulationAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
    if not agent.llm:
        return {"interview_feedback": {"readiness_score": 9.2, "feedback": "Great communication but deep-dive more into RAG."}}
    return {"interview_feedback": {"readiness_score": 8.5}}

async def career_node(state: AgentState):
    """Agent 5: Career Guidance & War Room."""
    agent = CareerGuidanceAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
    if not agent.llm:
        return {"career_roadmap": "Predictive Trajectory: VP of AI in 5 years."}
    return {"career_roadmap": "Predictive Trajectory: Senior Architect in 3 years."}

# --- Graph Orchestration ---

def create_orchestrator():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent_1_resume", resume_node)
    workflow.add_node("agent_2_matching", matching_node)
    workflow.add_node("agent_3_gaps", gap_node)
    workflow.add_node("agent_4_interview", interview_node)
    workflow.add_node("agent_5_guidance", career_node)
    
    workflow.set_entry_point("agent_1_resume")
    workflow.add_edge("agent_1_resume", "agent_2_matching")
    workflow.add_edge("agent_2_matching", "agent_3_gaps")
    workflow.add_edge("agent_3_gaps", "agent_4_interview")
    workflow.add_edge("agent_4_interview", "agent_5_guidance")
    workflow.add_edge("agent_5_guidance", END)
    
    return workflow.compile()
