from neo4j import GraphDatabase
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class SkillGraphAgent:
    def __init__(self, uri: str = None, user: str = None, password: str = None, openai_api_key: str = None):
        if uri and user and password:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        else:
            self.driver = None
        if openai_api_key:
            self.llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)
        else:
            self.llm = None

    def close(self):
        self.driver.close()

    async def get_skill_gaps(self, candidate_skills: List[str], target_job_skills: List[str]) -> Dict[str, Any]:
        """Perform Cypher-based gap analysis on the ESCO skill ontology."""
        with self.driver.session() as session:
            # Cypher query to find missing skills and their prerequisite relationships
            query = """
            MATCH (s:Skill)
            WHERE s.name IN $target_skills AND NOT s.name IN $candidate_skills
            OPTIONAL MATCH (s)<-[:IS_PREREQUISITE_FOR]-(pre:Skill)
            RETURN s.name AS missing_skill, collect(pre.name) AS prerequisites, s.level AS level
            """
            result = session.run(query, candidate_skills=candidate_skills, target_skills=target_job_skills)
            gaps = [record.data() for record in result]
            
            return {
                "direct_gaps": gaps,
                "complexity_score": len(gaps) * 0.2
            }

    async def generate_learning_roadmap(self, gap_results: Dict[str, Any]) -> str:
        """Use GPT-4o to turn the graph gaps into a structured learning roadmap."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a senior technical trainer. Create a prioritized 12-week learning roadmap based on the skill gaps provided. "
                       "Order them by difficulty and prerequisite dependency."),
            ("user", f"Skill Gaps: {gap_results}")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content

    async def auto_resume_generator(self, candidate_data: Dict[str, Any], target_job: Dict[str, Any]) -> str:
        """Optimize user bullet points for the target role while maintaining honesty (Placeholder)."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a specialized Resume Optimizer. Take the candidate's achievements and re-word them to highlight "
                       "keywords and metrics that match the target job description. Do NOT hallucinate skills the candidate does not have."),
            ("user", f"Candidate: {candidate_data}\n\nTarget Job: {target_job}")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content
