#!/usr/bin/env python3
"""
Prototype: AI Career Advisor (CLI)
Simplified version — role recommendation, mini-roadmap, mock interview.
"""

import random

# --- Mini role database ---
ROLES = {
    "Frontend Engineer": ["javascript", "react", "html", "css"],
    "Backend Engineer": ["python", "sql", "api", "java"],
    "Data Scientist": ["python", "ml", "pandas", "numpy"]
}

INTERVIEW_QUESTIONS = {
    "Frontend Engineer": "Explain how React’s virtual DOM improves performance.",
    "Backend Engineer": "How would you design a REST API for an online store?",
    "Data Scientist": "What is the difference between precision and recall?"
}

# --- Helpers ---
def recommend_role(skills):
    best_role, best_score = None, -1
    for role, req_skills in ROLES.items():
        score = len(set(skills) & set(req_skills))
        if score > best_score:
            best_role, best_score = role, score
    return best_role, best_score

def roadmap(role):
    return [
        f"Week 1: Learn basics of {role} core skills",
        "Week 2: Build a mini project",
        "Week 3: Add testing + deployment",
        "Week 4: Prepare resume & apply"
    ]

# --- Main ---
def main():
    print("🚀 Prototype: AI Career Advisor")
    name = input("Enter your name: ") or "Student"
    skills = input("Enter your skills (comma separated): ").lower().split(",")
    skills = [s.strip() for s in skills if s.strip()]

    role, score = recommend_role(skills)
    print(f"\nHi {name}, best matching role: {role} ({score} skills matched).")

    print("\n📌 4-Week Roadmap:")
    for step in roadmap(role):
        print(" -", step)

    print("\n🎤 Mock Interview:")
    q = INTERVIEW_QUESTIONS.get(role, "Tell me about yourself.")
    print("Q:", q)
    ans = input("Your answer: ")
    print("✅ Feedback: Good effort! Try adding technical keywords + an example.\n")

if __name__ == "__main__":
    main()
