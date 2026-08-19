import json
import re

from app.core.brain.manager import process_message


CANDIDATE_PROFILE = """
CANDIDATE:
Chirag Sharma

EDUCATION:
B.Tech in Computer Science and Business Systems
GITAM University
Graduated August 2026
CGPA: 8.46/10

TARGET ROLES:
AI Engineer
Generative AI Engineer
Backend Engineer
Software Engineer
Machine Learning Engineer

IMPLEMENTED / HANDS-ON EXPERIENCE:

Languages:
Python, JavaScript, TypeScript, C++, SQL

Backend:
FastAPI, REST APIs, WebSockets

AI / Machine Learning:
Machine Learning, LSTM, ARIMA, Model Evaluation, Pandas, NumPy

AI Systems:
Ollama, Qwen2.5, Local LLM Inference, LLM Integration, Prompt Engineering

Web:
React.js, Next.js, HTML5, CSS3

Databases:
PostgreSQL, MongoDB

Tools:
Git, GitHub, Figma

PROJECT EXPERIENCE:

FRIDAY PERSONAL AI ASSISTANT:
Built a modular personal AI assistant using Python and FastAPI.

Implemented:
- FastAPI backend
- Ollama integration
- Qwen2.5 local LLM inference
- AI provider architecture
- Brain and orchestration architecture
- REST API interaction

Relevant experience:
- Large Language Models
- Generative AI
- LLM Integration
- Local LLM Inference
- AI backend development

BITCOIN PRICE FORECASTING:
Implemented LSTM and ARIMA models.

Relevant experience:
- Python
- Machine Learning
- Time Series Forecasting
- Model Evaluation
- MAPE

BITCOIN DAY TRADING BOT:
Built a real-time trading prototype.

Relevant experience:
- Python
- Machine Learning
- WebSockets
- Live market data
- Real-time data processing

DRUG SUPPLY CHAIN TRACKING SYSTEM:
Built a blockchain-based pharmaceutical supply chain system.

Relevant experience:
- Next.js
- Solidity
- Ethers.js
- MetaMask
- Hardhat

DESIGNED / PLANNED:

- RAG
- Embeddings
- Vector Databases
- Redis
- Docker
- AWS
- CI/CD
- External device integration
- Multi-service integration

These technologies are NOT fully implemented.
They must only be considered partial matches when relevant to the job.

STRICT TRUTHFULNESS RULES:

Do not invent skills.
Do not claim professional experience when only project experience exists.
Do not classify planned technologies as implemented.
Do not claim production deployment experience.

Qwen2.5 + Ollama + Local LLM Inference demonstrate experience with:
- Large Language Models
- LLMs
- Generative AI
- AI model integration
- Local AI systems

FRIDAY and other project names must NEVER be returned as skills.
"""


def normalize_skill(skill: str) -> str:
    skill = skill.lower().strip()
    skill = re.sub(r"[^a-z0-9+#.\s]", "", skill)
    return " ".join(skill.split())


def skill_in_job_description(skill: str, job_description: str) -> bool:
    skill = normalize_skill(skill)
    jd = normalize_skill(job_description)

    if skill in jd:
        return True

    aliases = {
        "large language models": [
            "llm",
            "llms",
            "large language model",
            "language models"
        ],
        "generative ai": [
            "genai",
            "generative ai",
            "llm"
        ],
        "local llm inference": [
            "local llm",
            "llm inference",
            "large language model"
        ],
        "llm integration": [
            "llm",
            "language model",
            "generative ai",
            "genai"
        ],
        "machine learning": [
            "machine learning",
            "ml"
        ],
        "real-time data processing": [
            "real time",
            "realtime",
            "streaming",
            "live data"
        ],
        "time series forecasting": [
            "time series",
            "forecasting",
            "prediction"
        ],
        "rest apis": [
            "rest api",
            "restful",
            "api development"
        ],
        "vector databases": [
            "vector database",
            "vector store"
        ],
        "cloud platforms": [
            "aws",
            "azure",
            "gcp",
            "cloud platform",
            "cloud computing"
        ]
    }

    for alias in aliases.get(skill, []):
        if alias in jd:
            return True

    return False


def clean_skill_list(skills: list) -> list:
    cleaned = []
    seen = set()

    for skill in skills:
        if not isinstance(skill, str):
            continue

        skill = skill.strip()

        if not skill:
            continue

        normalized = normalize_skill(skill)

        if normalized and normalized not in seen:
            seen.add(normalized)
            cleaned.append(skill)

    return cleaned


def filter_relevant_skills(skills: list, job_description: str) -> list:
    return [
        skill
        for skill in clean_skill_list(skills)
        if skill_in_job_description(skill, job_description)
    ]


def remove_category_overlaps(data: dict) -> dict:
    category_order = [
        "strong_matches",
        "project_matches",
        "partial_matches",
        "missing_skills",
        "learnable_skills"
    ]

    used = set()

    for category in category_order:
        result = []

        for skill in data.get(category, []):
            normalized = normalize_skill(skill)

            if normalized in used:
                continue

            result.append(skill)
            used.add(normalized)

        data[category] = result

    return data


def remove_known_project_names(data: dict) -> dict:
    project_names = {
        "friday personal ai assistant",
        "bitcoin price forecasting",
        "bitcoin day trading bot",
        "drug supply chain tracking system"
    }

    categories = [
        "strong_matches",
        "project_matches",
        "partial_matches",
        "missing_skills",
        "learnable_skills"
    ]

    for category in categories:
        data[category] = [
            skill
            for skill in data.get(category, [])
            if normalize_skill(skill) not in project_names
        ]

    return data


def fix_semantic_matches(data: dict) -> dict:
    llm_skills = {
        "large language models",
        "large language model",
        "llm",
        "llms",
        "generative ai",
        "genai"
    }

    missing = []

    for skill in data.get("missing_skills", []):
        normalized = normalize_skill(skill)

        if normalized not in llm_skills:
            missing.append(skill)

    data["missing_skills"] = missing

    learnable = []

    for skill in data.get("learnable_skills", []):
        normalized = normalize_skill(skill)

        if normalized not in llm_skills:
            learnable.append(skill)

    data["learnable_skills"] = learnable

    return data


def ensure_reason(data: dict) -> dict:
    reason = data.get("reason", "").strip()

    if reason:
        return data

    strong_count = len(data.get("strong_matches", []))
    project_count = len(data.get("project_matches", []))
    partial_count = len(data.get("partial_matches", []))
    missing_count = len(data.get("missing_skills", []))

    data["reason"] = (
        f"The candidate has {strong_count} direct skill matches, "
        f"{project_count} relevant project-level matches, "
        f"{partial_count} partial matches, and "
        f"{missing_count} identified skill gaps."
    )

    return data


def clean_analysis(
    data: dict,
    job_description: str
) -> dict:

    categories = [
        "strong_matches",
        "project_matches",
        "partial_matches",
        "missing_skills",
        "learnable_skills"
    ]

    for category in categories:
        data[category] = clean_skill_list(
            data.get(category, [])
        )

    data = remove_known_project_names(data)

    for category in [
        "strong_matches",
        "project_matches",
        "partial_matches",
        "missing_skills"
    ]:
        data[category] = filter_relevant_skills(
            data[category],
            job_description
        )

    data = fix_semantic_matches(data)
    data = remove_category_overlaps(data)

    data["learnable_skills"] = list(
        data.get("missing_skills", [])
    )

    strong = len(data["strong_matches"])
    project = len(data["project_matches"])
    partial = len(data["partial_matches"])
    missing = len(data["missing_skills"])

    total = strong + project + partial + missing

    if total > 0:
        score = (
            strong * 100
            + project * 80
            + partial * 50
        ) / total
    else:
        score = 0

    data["match_score"] = round(score)

    if data["match_score"] >= 75:
        data["recommendation"] = "APPLY"
    elif data["match_score"] >= 55:
        data["recommendation"] = "MAYBE"
    else:
        data["recommendation"] = "SKIP"

    data = ensure_reason(data)

    return data

def extract_json(
    text: str,
    job_description: str
) -> dict:

    text = text.strip()

    if "```json" in text:
        text = text.split("```json", 1)[1].split(
            "```", 1
        )[0].strip()

    elif "```" in text:
        text = text.split("```", 1)[1].split(
            "```", 1
        )[0].strip()

    data = json.loads(text)

    data.setdefault("match_score", 0)
    data.setdefault("recommendation", "MAYBE")

    data.setdefault("strong_matches", [])
    data.setdefault("project_matches", [])
    data.setdefault("partial_matches", [])

    data.setdefault("missing_skills", [])
    data.setdefault("learnable_skills", [])

    data.setdefault("reason", "")
    data.setdefault("resume_focus", "")
    data.setdefault("interview_topics", [])

    return clean_analysis(
        data,
        job_description
    )


def analyze_job(job_description: str) -> dict:
    prompt = f"""
You are FRIDAY's Job Application Agent.

Analyze the candidate profile against the job description.

CANDIDATE PROFILE:
{CANDIDATE_PROFILE}

JOB DESCRIPTION:
{job_description}

Return ONLY valid JSON.

Use this exact structure:

{{
  "match_score": 0,
  "recommendation": "APPLY",
  "strong_matches": [],
  "project_matches": [],
  "partial_matches": [],
  "missing_skills": [],
  "learnable_skills": [],
  "reason": "",
  "resume_focus": "",
  "interview_topics": []
}}

CLASSIFICATION:

strong_matches:
Direct hands-on implementation.

project_matches:
Skills demonstrated through projects.

partial_matches:
Planned or designed knowledge only.

missing_skills:
Important JD requirements without demonstrated experience.

learnable_skills:
Missing skills realistic to learn before interview.

RULES:

1. Do not invent skills.
2. Do not exaggerate experience.
3. Do not return project names as skills.
4. Only include JD-relevant skills.
5. Do not place the same skill in multiple categories.
6. Generative AI and LLMs are relevant experience because
   the candidate has implemented Ollama and Qwen2.5 integration.
7. Planned technologies are partial matches only when
   mentioned in the job description.
8. reason must never be empty.
9. recommendation must be exactly APPLY, MAYBE, or SKIP.
"""

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    response = process_message(messages)

    return extract_json(
        response,
        job_description
    )