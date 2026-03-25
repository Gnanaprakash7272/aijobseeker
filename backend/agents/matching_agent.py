import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Any
import httpx

class SemanticJobMatchingAgent:
    def __init__(self, openai_api_key: str = None, pinecone_api_key: str = None, index_name: str = None):
        if openai_api_key and openai_api_key.strip():
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=openai_api_key)
            self.llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)
        else:
            self.embeddings = None
            self.llm = None
            
        if pinecone_api_key and pinecone_api_key.strip() and index_name:
            try:
                from pinecone import Pinecone
                self.pc = Pinecone(api_key=pinecone_api_key)
                self.index = self.pc.Index(index_name)
            except Exception as e:
                print(f"Pinecone Initialization Error: {e}")
                self.index = None
        else:
            self.index = None
        
    async def generate_embedding(self, text: str) -> List[float]:
        if not self.embeddings: return []
        return await self.embeddings.aembed_query(text)

    async def find_matches(self, vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.index: return []
        query_response = self.index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True
        )
        return query_response['matches']

    async def explain_match(self, candidate_profile: str, job_description: str) -> str:
        if not self.llm: return "Semantic explanation unavailable (No API Key)."
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a senior career advisor. Given a candidate profile and a job description, explain exactly why they are a good match."),
            ("user", f"Candidate Profile: {candidate_profile}\n\nJob Description: {job_description}")
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        return response.content

    async def live_pulse_market_data(self, keyword: str, location: str = "us") -> Dict[str, Any]:
        app_id = os.getenv("ADZUNA_APP_ID")
        app_key = os.getenv("ADZUNA_APP_KEY")
        if not app_id or not app_key:
            return {"status": "demo", "results": [{"title": "Demo Job", "salary_min": 100000}]}
        url = f"https://api.adzuna.com/v1/api/jobs/{location}/search/1"
        params = {"app_id": app_id, "app_key": app_key, "results_per_page": 5, "what": keyword}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                return {"status": "success", "results": response.json().get("results", [])}
            except:
                return {"status": "error"}
