import asyncio
from dotenv import load_dotenv
load_dotenv()
from job_discovery import fetch_adzuna_jobs

async def test():
    result = await fetch_adzuna_jobs(['Python', 'Machine Learning', 'Deep Learning'], 'india')
    print(f'Got {len(result)} live jobs from Adzuna')
    for j in result:
        print(f"  [{j['company']}] {j['title']} | {j['location']} | {j['salary']}")
        print(f"    Apply: {j['apply_link'][:80]}")

asyncio.run(test())
