#!/usr/bin/env python3
"""
career_advisor.py
A single-file CLI "AI" Career Advisor: maps skills, recommends roles, builds
a 12-week roadmap, simulates mock interviews, and can save/load profiles.
Standard-library only.
"""

import json
import random
import textwrap
import os
from datetime import datetime

# ---------- Role database ----------
# Each role has: required skills (keywords), a short description, trending tags
ROLES = {
    "Frontend Engineer": {
        "skills": ["javascript", "react", "html", "css", "typescript", "ui", "accessibility"],
        "desc": "Build user-facing web interfaces. Emphasize performance and UX.",
        "tags": ["web", "frontend"]
    },
    "Backend Engineer": {
        "skills": ["python", "node.js", "java", "sql", "rest", "api", "microservices", "databases"],
        "desc": "Server-side systems, APIs, data modeling and business logic.",
        "tags": ["backend", "api"]
    },
    "Full-stack Engineer": {
        "skills": ["javascript", "react", "node.js", "sql", "html", "css", "rest"],
        "desc": "Handles both frontend and backend; versatile product engineering.",
        "tags": ["web", "fullstack"]
    },
    "Data Scientist / ML Engineer": {
        "skills": ["python", "machine learning", "ml", "pandas", "numpy", "statistics", "tensorflow", "pytorch"],
        "desc": "Analyze data and build ML models; productionize models for products.",
        "tags": ["ai", "ml", "data"]
    },
    "DevOps / SRE": {
        "skills": ["docker", "kubernetes", "aws", "gcp", "ci/cd", "monitoring", "infrastructure"],
        "desc": "Ensure reliability, scalability and deployment automation.",
        "tags": ["cloud", "infra"]
    },
    "Data Engineer": {
        "skills": ["etl", "sql", "spark", "hadoop", "airflow", "databases", "python"],
        "desc": "Design data pipelines and engineering systems for analytics.",
        "tags": ["data", "etl"]
    },
    "QA / Test Automation": {
        "skills": ["selenium", "testing", "automation", "pytest", "integration tests", "qa"],
        "desc": "Automation and verification of product quality and regressions.",
        "tags": ["testing", "qa"]
    },
    "Product Manager (Technical)": {
        "skills": ["communication", "roadmap", "stakeholders", "metrics", "product", "analytics"],
        "desc": "Define product vision, prioritize features with technical teams.",
        "tags": ["product"]
    }
}

TRENDING_BOOST_TAGS = {
    # tags considered 'hot' — give small boost if role matches these
    "ai": 0.08,
    "ml": 0.08,
    "cloud": 0.06,
    "data": 0.05,
    "web": 0.03
}

# ---------- Interview question bank ----------
INTERVIEW_QUESTIONS = {
    "Frontend Engineer": [
        ("Explain the virtual DOM and why React uses it.", ["react", "virtual", "dom", "diff", "reconciliation"]),
        ("How do you optimize web performance?", ["lazy", "bundle", "cdn", "cache", "minify", "critical"])
    ],
    "Backend Engineer": [
        ("Describe how you would design a RESTful API for a book store.", ["rest", "endpoints", "http", "status", "auth", "crud"]),
        ("Explain database indexing and when to use it.", ["index", "query", "performance", "b-tree", "select"])
    ],
    "Data Scientist / ML Engineer": [
        ("Explain bias-variance tradeoff.", ["bias", "variance", "overfit", "underfit", "regularization"]),
        ("Describe how you'd evaluate a classification model.", ["accuracy", "precision", "recall", "f1", "roc", "auc"])
    ],
    "DevOps / SRE": [
        ("How do you design a CI/CD pipeline?", ["ci", "cd", "pipeline", "automation", "tests", "deploy"]),
        ("What is infrastructure as code?", ["terraform", "ansible", "declarative", "provision"])
    ],
    "Default": [
        ("Tell me about a challenging problem you solved.", ["problem", "challenge", "impact", "team", "learned"]),
        ("How do you keep your skills up to date?", ["learn", "courses", "projects", "reading", "practice"])
    ]
}

# ---------- Helper utilities ----------
def normalize(skill_str):
    """Normalize a skill string: lower and strip punctuation-ish characters."""
    return skill_str.strip().lower()

def tokenize_skills(skills_list):
    """Return normalized set of skills from user input list."""
    out = set()
    for s in skills_list:
        if not s:
            continue
        s = s.replace("_", " ").replace("-", " ")
        tokens = [t.strip() for t in s.split(",")] if "," in s else [s]
        for tok in tokens:
            tok = normalize(tok)
            if tok:
                out.add(tok)
    return out

def score_role(user_skills_set, role_key):
    role = ROLES[role_key]
    req = set(role["skills"])
    # base overlap ratio
    overlap = len(user_skills_set & req)
    ratio = overlap / max(1, len(req))
    # raw base score 0..1
    score = 0.6 * ratio + 0.2 * min(0.5, overlap / max(1, len(user_skills_set)))  # preference for overlap
    # trending boost
    for tag in role.get("tags", []):
        score += TRENDING_BOOST_TAGS.get(tag, 0)
    # clamp
    score = max(0.0, min(1.0, score))
    # reason
    reason_parts = []
    if overlap > 0:
        reason_parts.append(f"{overlap} matching skill(s)")
    else:
        reason_parts.append("No direct skill matches")
    if any(t in ["ai","ml","cloud","data"] for t in role.get("tags", [])):
        reason_parts.append("Role aligned with trending areas")
    return score, "; ".join(reason_parts)

def top_role_recommendations(user_skills, top_n=4):
    user_skills_set = tokenize_skills(user_skills)
    scored = []
    for role in ROLES:
        score, reason = score_role(user_skills_set, role)
        scored.append((role, score, reason))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]

def skill_gap_for_role(user_skills_set, role_key):
    req = set(ROLES[role_key]["skills"])
    missing = sorted(list(req - user_skills_set))
    present = sorted(list(req & user_skills_set))
    return present, missing

# ---------- Roadmap builder ----------
def build_12_week_roadmap(chosen_role, user_skills):
    user_set = tokenize_skills(user_skills)
    present, missing = skill_gap_for_role(user_set, chosen_role)
    roadmap = []
    # Strategy:
    # - Weeks 1-4: fundamentals + address top-missing (1 per week)
    # - Weeks 5-8: build project(s) integrating missing + CI/CD / infra basics
    # - Weeks 9-10: interview prep & DS
    # - Weeks 11-12: portfolio + apply
    missing_top = missing[:4]  # up to 4 important gaps
    week = 1
    # Weeks 1-4
    for i in range(4):
        if i < len(missing_top):
            task = f"Learn fundamentals of **{missing_top[i]}** (3-6 hrs) — small exercises & mini-tutorial."
        else:
            task = "Deepen core fundamentals and practice small exercises (4-6 hrs)."
        roadmap.append((f"Week {week}", task)); week += 1
    # Weeks 5-8 project-focused
    roadmap.append((f"Week {week}", f"Start a guided project for {chosen_role}, include at least one missing skill."))
    week += 1
    roadmap.append((f"Week {week}", "Continue project; add tests, version control and CI steps.")); week += 1
    roadmap.append((f"Week {week}", "Add deployment / demo (host on free tier) and write README.")); week += 1
    roadmap.append((f"Week {week}", "Polish UI/UX and fix performance issues; get feedback.")); week += 1
    # Weeks 9-10 interview and DS practice
    roadmap.append((f"Week {week}", "Practice mock interviews: behavioral + 5 coding problems (2-3 hrs/day).")); week += 1
    roadmap.append((f"Week {week}", "Data structures and algorithms: targeted practice (arrays, maps, recursion).")); week += 1
    # Weeks 11-12 apply & network
    roadmap.append((f"Week {week}", "Prepare tailored resume and LinkedIn; publish project demo (portfolio).")); week += 1
    roadmap.append((f"Week {week}", "Apply to roles, network, and schedule mock interviews with peers/mentors."))
    return roadmap, present, missing

# ---------- Mock interview evaluator ----------
def evaluate_mock_answer(role, question, answer_text):
    answer = answer_text.lower()
    # baseline random fluency/clarity factor
    fluency = random.uniform(0.7, 0.95)
    keywords = []
    if role in INTERVIEW_QUESTIONS:
        # try to find matching keywords for the specific question
        for q, kws in INTERVIEW_QUESTIONS[role]:
            if q == question:
                keywords = kws
                break
    else:
        # fallback
        keywords = INTERVIEW_QUESTIONS["Default"][0][1]
    key_matches = sum(1 for kw in keywords if kw in answer)
    # score composition
    score = int(40 + (key_matches * 12) + (fluency * 40))
    score = max(0, min(100, score))
    # feedback heuristics
    feedback = []
    if key_matches == 0:
        feedback.append("Try to mention core technical keywords related to the question.")
    else:
        feedback.append(f"You referenced {key_matches} important concept(s). Good.")
    if "example" not in answer and key_matches > 0:
        feedback.append("Include a concrete example or short mini-diagram of your approach.")
    if score > 80:
        feedback.append("Strong answer — clear structure and relevant keywords.")
    elif score > 60:
        feedback.append("Solid answer — try improving examples and edge-case discussion.")
    else:
        feedback.append("Work on structure: start with a one-sentence summary, then steps, then trade-offs.")
    return score, " ".join(feedback)

# ---------- Persistence ----------
def save_profile(path, profile):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
    return path

def load_profile(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- CLI helpers ----------
def wrap(s, indent=0):
    return textwrap.fill(s, width=78, subsequent_indent=" " * indent)

def print_header(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78 + "\n")

def input_skills_prompt():
    print("Enter comma-separated skills (e.g., 'Python, React, SQL'):")
    raw = input("Skills: ").strip()
    if raw == "":
        return []
    # split on commas or semicolons or newline
    parts = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
    return parts

def main_menu():
    print_header("Hack.Vision — CLI AI Career Advisor (Prototype)")
    name = input("What's your name? (press Enter for 'Student'): ").strip() or "Student"
    print(f"Welcome, {name} 👋")
    user_skills = input_skills_prompt()
    profile = {
        "name": name,
        "skills": user_skills,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    while True:
        print("\nMain Menu — choose an action:")
        print("  1) Show role recommendations")
        print("  2) View personalized 12-week roadmap")
        print("  3) Mock interview simulator")
        print("  4) Skill-gap analysis for a role")
        print("  5) Save profile")
        print("  6) Load profile")
        print("  7) Quick tips for 'evolving job market'")
        print("  0) Exit")
        choice = input("Choice: ").strip()
        if choice == "1":
            recs = top_role_recommendations(profile["skills"], top_n=6)
            print_header("Role Recommendations")
            for role, score, reason in recs:
                print(f"- {role:22} | Score: {int(score*100)}% | {reason}")
            # choose top
            if recs:
                top_role = recs[0][0]
                print(f"\nTop suggestion: {top_role} — {ROLES[top_role]['desc']}")
        elif choice == "2":
            recs = top_role_recommendations(profile["skills"], top_n=1)
            if not recs:
                print("No recommendations yet — add skills first.")
                continue
            chosen_role = recs[0][0]
            roadmap, present, missing = build_12_week_roadmap(chosen_role, profile["skills"])
            print_header(f"12-Week Roadmap — Target: {chosen_role}")
            print(f"Detected skills relevant to role: {', '.join(present) if present else 'None'}")
            print(f"Top missing skills to focus on: {', '.join(missing[:6]) if missing else 'None'}\n")
            for w, t in roadmap:
                print(f"{w:8} - {t}")
        elif choice == "3":
            recs = top_role_recommendations(profile["skills"], top_n=3)
            if not recs:
                print("Add skills first to generate interview questions.")
                continue
            # Pick role for interview
            print("Which role shall we simulate interview for?")
            for idx, (role, score, _) in enumerate(recs, start=1):
                print(f"  {idx}) {role} (score {int(score*100)}%)")
            print("  0) Enter custom role")
            sel = input("Select: ").strip()
            if sel == "0":
                role = input("Enter role name: ").strip()
            else:
                try:
                    role = recs[int(sel)-1][0]
                except Exception:
                    role = recs[0][0]
            # choose question
            banks = INTERVIEW_QUESTIONS.get(role, INTERVIEW_QUESTIONS.get("Default"))
            q_idx = random.randrange(len(banks))
            question, _ = banks[q_idx]
            print_header(f"Mock Interview — Role: {role}")
            print("Question:")
            print(wrap(question, indent=4))
            print("\nType your short answer (one paragraph). Press Enter when done.")
            ans = input("Answer: ").strip()
            score, feedback = evaluate_mock_answer(role, question, ans)
            print(f"\nSimulated score: {score}/100")
            print("Feedback:", feedback)
        elif choice == "4":
            # pick a role
            print("Available roles:")
            for i, r in enumerate(ROLES.keys(), start=1):
                print(f"  {i}) {r}")
            idx = input("Pick role by number: ").strip()
            try:
                idx = int(idx)-1
                role = list(ROLES.keys())[idx]
            except Exception:
                print("Invalid choice.")
                continue
            present, missing = skill_gap_for_role(tokenize_skills(profile["skills"]), role)
            print_header(f"Skill-gap Analysis for: {role}")
            print("Required skills for role:", ", ".join(ROLES[role]["skills"]))
            print("You have:", ", ".join(present) if present else "None")
            print("You are missing (prioritize these):", ", ".join(missing) if missing else "None")
        elif choice == "5":
            filename = input("Save filename (e.g., profile.json): ").strip() or "profile.json"
            saved = save_profile(filename, profile)
            print(f"Profile saved to {saved}")
        elif choice == "6":
            filename = input("Path to profile JSON: ").strip()
            if not os.path.exists(filename):
                print("File not found.")
            else:
                loaded = load_profile(filename)
                profile = loaded
                print(f"Loaded profile for {profile.get('name','(unknown)')}, skills: {', '.join(profile.get('skills',[]))}")
        elif choice == "7":
            print_header("Quick Tips — Evolving Job Market")
            tips = [
                "1) Learn one cloud platform (AWS/GCP/Azure) and one IaC tool (Terraform).",
                "2) Build 2-3 portfolio projects with deployed demos (GitHub + live demo).",
                "3) Practice data structures & algorithms weekly (30-60 mins).",
                "4) Focus on communication: write README, explain trade-offs in interviews.",
                "5) Keep a learning log and adapt to new tools (micro-certifications help).",
                "6) Network: join local meetups, open-source, and mentorship channels."
            ]
            for t in tips:
                print(wrap(t, indent=4))
        elif choice == "0":
            print("Good luck — keep building! 👋")
            break
        else:
            print("Unknown choice — try again.")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nExiting. Bye!")

