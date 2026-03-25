import spacy
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import requests
from utils.parser import get_text_from_file
from utils.masker import mask_pii

# Load spaCy model for basic NER (optional, GPT-4o will do the heavy lifting)
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

class ParsedResume(BaseModel):
    status: str = Field(description="Processing status", default="LIVE PDF PARSED via GPT-4o")
    preview: str = Field(description="A 2 sentence professional summary of the candidate's core profile")
    skills: List[str] = Field(description="Technical and soft skills extracted")
    experiences: List[str] = Field(description="List of past roles and companies")

class ResumeIntelligenceAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        if api_key:
            self.llm = ChatOpenAI(model="gpt-4o", api_key=api_key)
        else:
            self.llm = None
        
    def extract_github_url(self, text: str) -> str:
        """Simple regex or LLM based GitHub URL extraction."""
        # Using spaCy to find URLs or keywords
        doc = nlp(text)
        for token in doc:
            if "github.com/" in token.text:
                return token.text
        return None

    def analyze_github_portfolio(self, github_url: str) -> Dict[str, Any]:
        """Scrape basic data from GitHub profile/repositories."""
        if not github_url:
            return {"status": "none"}
        
        # Placeholder for GitHub analysis logic
        # In production, use graphql or rest api with token
        return {"status": "success", "found_url": github_url, "analysis": "High activity in Python, JavaScript."}

    async def process_resume(self, file_path: str) -> Dict[str, Any]:
        """End-to-end resume intelligence pipeline."""
        # 1. Parsing
        raw_text = get_text_from_file(file_path)
        
        # 2. Extract GitHub Profile
        github_url = self.extract_github_url(raw_text)
        github_stats = self.analyze_github_portfolio(github_url)
        
        # 3. Privacy (PII Masking)
        masked_text = mask_pii(raw_text)
        
        # 4. Semantic Extraction with GPT-4o
        if not self.llm:
            return {
                "knowledge_graph": {
                    "status": "LIVE PDF PARSED - NO LLM KEY",
                    "preview": masked_text[:150] + "...",
                    "skills": ["Add OPENAI_API_KEY to see real skills"]
                },
                "github_stats": github_stats,
                "is_masked": True
            }

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert technical recruiter AI. Extract a structured knowledge graph from the resume. "
                       "Identify Skills, Experience, Education, and Projects. Return strictly according to the schema."),
            ("user", "{text}")
        ])
        
        chain = prompt | self.llm.with_structured_output(ParsedResume)
        try:
            response = await chain.ainvoke({"text": masked_text})
            structured_data = response.dict()
        except:
            structured_data = {
                "status": "LIVE PDF PARSED - NO LLM KEY or PARSE FAILED",
                "preview": "Could not parse correctly using GPT-4o. Check API Key.",
                "skills": [],
                "experiences": []
            }
        
        return {
            "knowledge_graph": structured_data,
            "github_stats": github_stats,
            "is_masked": True
        }
