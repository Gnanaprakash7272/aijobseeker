"""
Real Job Discovery Engine
- Adzuna API : live jobs from the web (India + Global)
- LinkedIn   : generate smart deep-link search URL from extracted skills
- IndeedIN   : generate deep-link for Indeed India search
"""
import os
import httpx
from typing import List, Dict, Any
from urllib.parse import urlencode, quote_plus

ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID",  "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")

# Country codes supported by Adzuna
COUNTRY_MAP = {
    "india": "in",
    "us": "us",
    "uk": "gb",
    "australia": "au",
    "canada": "ca",
}


async def fetch_adzuna_jobs(
    keywords: List[str],
    location: str = "india",
    results_per_page: int = 6
) -> List[Dict[str, Any]]:
    """Call Adzuna API to get live job listings."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        return []          # fall through to fallback

    country = COUNTRY_MAP.get(location.lower(), "in")
    query   = " ".join(keywords[:4])

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id":           ADZUNA_APP_ID,
        "app_key":          ADZUNA_APP_KEY,
        "results_per_page": results_per_page,
        "what":             query,
        "content-type":     "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url, params=params)
            if r.status_code != 200:
                return []
            results = r.json().get("results", [])
            jobs = []
            for j in results:
                jobs.append({
                    "title":         j.get("title", "N/A"),
                    "company":       j.get("company", {}).get("display_name", "N/A"),
                    "location":      j.get("location", {}).get("display_name", location.title()),
                    "salary":        _format_salary(j),
                    "apply_link":    j.get("redirect_url", "#"),
                    "source":        "Adzuna",
                    "description":   j.get("description", "")[:200],
                    "matched_skills": keywords[:3],
                    "score":         "Live",
                    "tags":          ["Live Job", j.get("category", {}).get("label", "Tech")],
                })
            return jobs
    except Exception as e:
        print(f"Adzuna error: {e}")
        return []


def _format_salary(job: dict) -> str:
    lo = job.get("salary_min")
    hi = job.get("salary_max")
    if lo and hi:
        return f"₹{int(lo):,} – ₹{int(hi):,}"
    if lo:
        return f"₹{int(lo):,}+"
    return "Negotiable"


def generate_linkedin_search_url(skills: List[str], location: str = "India") -> str:
    """Generate a direct LinkedIn Jobs search URL for the candidate's skills."""
    keywords = " ".join(skills[:5])
    params = {
        "keywords": keywords,
        "location": location,
        "f_TPR":    "r604800",   # last 7 days
        "f_E":      "4",         # Senior level
    }
    return "https://www.linkedin.com/jobs/search/?" + urlencode(params)


def generate_indeed_search_url(skills: List[str], location: str = "India") -> str:
    """Generate a direct Indeed India search URL."""
    query = " OR ".join(skills[:3])
    params = {"q": query, "l": location}
    return "https://in.indeed.com/jobs?" + urlencode(params)


def generate_naukri_search_url(skills: List[str]) -> str:
    """Naukri.com deep-link (biggest job board in India)."""
    keywords = "%2C".join(quote_plus(s) for s in skills[:4])
    return f"https://www.naukri.com/{'-'.join(s.lower().replace(' ','-') for s in skills[:3])}-jobs"


# ── Fallback demo jobs when no Adzuna key ─────────────────────────────────
DEMO_LOCAL_JOBS = [
    {
        "title": "Senior ML Engineer",
        "company": "Zoho Corporation",
        "location": "Chennai, India (Hybrid)",
        "salary": "₹30L – ₹50L",
        "apply_link": "https://careers.zoho.com",
        "source": "Direct",
        "description": "Build and deploy large-scale ML systems for Zoho's CRM product suite.",
        "matched_skills": ["Python", "Machine Learning", "Deep Learning"],
        "score": "95%",
        "tags": ["Chennai", "Product"],
    },
    {
        "title": "AI Research Engineer",
        "company": "Freshworks",
        "location": "Chennai, India (Onsite)",
        "salary": "₹25L – ₹45L",
        "apply_link": "https://www.freshworks.com/company/careers/",
        "source": "Direct",
        "description": "Work on Freddy AI – Freshworks's flagship AI assistant. NLP, LLM fine-tuning.",
        "matched_skills": ["NLP", "LangChain", "Python"],
        "score": "91%",
        "tags": ["Chennai", "AI Product"],
    },
    {
        "title": "Data Scientist – NLP",
        "company": "Infosys",
        "location": "Bangalore / Remote",
        "salary": "₹18L – ₹32L",
        "apply_link": "https://www.infosys.com/careers/",
        "source": "Direct",
        "description": "Design NLP pipelines and GenAI solutions for global enterprise clients.",
        "matched_skills": ["Python", "NLP", "Transformers"],
        "score": "88%",
        "tags": ["Pan-India", "Enterprise"],
    },
    {
        "title": "MLOps Engineer",
        "company": "Razorpay",
        "location": "Bangalore, India",
        "salary": "₹22L – ₹40L",
        "apply_link": "https://razorpay.com/jobs/",
        "source": "Direct",
        "description": "Own the ML infrastructure, CI/CD pipelines, and model serving at Razorpay.",
        "matched_skills": ["Kubernetes", "MLOps", "Python"],
        "score": "86%",
        "tags": ["Fintech", "Onsite"],
    },
    {
        "title": "LLM Engineer",
        "company": "CRED",
        "location": "Bangalore, India (Hybrid)",
        "salary": "₹28L – ₹48L",
        "apply_link": "https://careers.cred.club/",
        "source": "Direct",
        "description": "Build RAG pipelines and fine-tune open-source LLMs for CRED's financial products.",
        "matched_skills": ["LLM", "RAG", "Python"],
        "score": "89%",
        "tags": ["Fintech", "Startup"],
    },
    {
        "title": "AI Product Engineer",
        "company": "PhonePe",
        "location": "Bangalore, India",
        "salary": "₹24L – ₹42L",
        "apply_link": "https://www.phonepe.com/en/careers.html",
        "source": "Direct",
        "description": "Design AI-driven recommendation engines and fraud detection systems at scale.",
        "matched_skills": ["Python", "Deep Learning", "Recommendation Systems"],
        "score": "84%",
        "tags": ["Payments", "Scale"],
    },
]
