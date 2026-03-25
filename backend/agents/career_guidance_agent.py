from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any, List
import operator

class CareerGuidanceAgent:
    def __init__(self, openai_api_key: str = None):
        if openai_api_key:
            self.llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)
        else:
            self.llm = None

    async def generate_career_trajectory(self, candidate_summary: str, market_trends: Dict[str, Any]) -> str:
        """Create a predictive 1-year and 3-year career projection."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Chief Career Strategist. Based on the candidate's skills, interview performance, and market trends, "
                       "generate a comprehensive 3-stage career trajectory (Immediate, 1-Year, 3-Year)."),
            ("user", f"Candidate Summary: {candidate_summary}\n\nMarket Trends: {market_trends}")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content

    async def recruiter_war_room_consensus(self, candidate_data: Dict[str, Any], interview_data: Dict[str, Any]) -> str:
        """Simulate a debate between 3 specialized recruiters to provide a ultimate hiring consensus."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Conduct a 'Recruiter War Room' simulation. You represent 3 personas:\n"
                       "1. The 'Technical Hawk' (Focus on core competency)\n"
                       "2. The 'Culture Guard' (Focus on team fit)\n"
                       "3. The 'Negotiator' (Focus on budget and market demand)\n\n"
                       "Debate the candidate's profilr and provide a Final Decision Report (Hire/Pass/Hold)."),
            ("user", f"Candidate Portfolio: {candidate_data}\n\nInterview Simulation Results: {interview_data}")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content

    async def fetch_web_trends(self, queries: List[str]) -> List[str]:
        """Fetch industry trends using web search results (Placeholder)."""
        # Integrate with Tavily or Google Search API
        return ["AI/LLM Engineers are in 40% higher demand than last year.", "Salary benchmarks: 140k - 190k base."]
