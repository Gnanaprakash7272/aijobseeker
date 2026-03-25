print("Checking Resume Agent...")
try:
    from agents.resume_agent import ResumeIntelligenceAgent
    print("Resume Agent OK")
except Exception as e:
    print(f"Resume Agent Error: {e}")

print("\nChecking Matching Agent...")
try:
    from agents.matching_agent import SemanticJobMatchingAgent
    print("Matching Agent OK")
except Exception as e:
    print(f"Matching Agent Error: {e}")

print("\nChecking Skill Graph Agent...")
try:
    from agents.skill_graph_agent import SkillGraphAgent
    print("Skill Graph Agent OK")
except Exception as e:
    print(f"Skill Graph Agent Error: {e}")

print("\nChecking Interview Agent...")
try:
    from agents.interview_agent import InterviewSimulationAgent
    print("Interview Agent OK")
except Exception as e:
    print(f"Interview Agent Error: {e}")

print("\nChecking Career Agent...")
try:
    from agents.career_guidance_agent import CareerGuidanceAgent
    print("Career Agent OK")
except Exception as e:
    print(f"Career Agent Error: {e}")
