import json
import re

from sqlalchemy.orm import Session

from app.core.brain.manager import process_message
from app.profile.models import UserProfile


def build_candidate_profile(profile: UserProfile) -> str:
    return f"""
CANDIDATE:
{profile.first_name or ""} {profile.last_name or ""}

HEADLINE:
{profile.headline or ""}

CURRENT STATUS:
{profile.current_status or ""}

EDUCATION:
Degree: {profile.degree or ""}
Branch: {profile.branch or ""}
University: {profile.university or ""}
Graduation Year: {profile.graduation_year or ""}
CGPA: {profile.cgpa or ""}

PROFESSIONAL SUMMARY:
{profile.summary or ""}

SKILLS:
{profile.skills or ""}

PROJECTS:
{profile.projects or ""}

EXPERIENCE:
{profile.experience or ""}

TARGET ROLES:
{profile.target_roles or ""}

JOB PREFERENCES:
Preferred Locations: {profile.preferred_locations or ""}
Remote Preference: {profile.remote_preference or ""}
Job Type: {profile.job_type_preference or ""}

STRICT TRUTHFULNESS RULES:
- Do not invent skills.
- Do not exaggerate experience.
- Do not claim professional experience when only project experience exists.
- Only classify technologies explicitly present in this profile as demonstrated experience.
- Do not claim production deployment experience unless explicitly stated.
- Project names must NEVER be returned as skills.
"""


def normalize_skill(skill: str) -> str:
    skill = skill.lower().strip()
    skill = re.sub(r"[^a-z0-9+#.\s]", "", skill)
    return " ".join(skill.split())


def skill_in_job_description(
    skill: str,
    job_description: str
) -> bool:

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


def filter_relevant_skills(
    skills: list,
    job_description: str
) -> list:

    return [
        skill
        for skill in clean_skill_list(skills)
        if skill_in_job_description(
            skill,
            job_description
        )
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
            if normalize_skill(skill)
            not in project_names
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

    for skill in data.get(
        "missing_skills",
        []
    ):

        normalized = normalize_skill(skill)

        if normalized not in llm_skills:
            missing.append(skill)

    data["missing_skills"] = missing

    learnable = []

    for skill in data.get(
        "learnable_skills",
        []
    ):

        normalized = normalize_skill(skill)

        if normalized not in llm_skills:
            learnable.append(skill)

    data["learnable_skills"] = learnable

    return data


def ensure_reason(data: dict) -> dict:

    reason = data.get(
        "reason",
        ""
    ).strip()

    if reason:
        return data

    strong_count = len(
        data.get("strong_matches", [])
    )

    project_count = len(
        data.get("project_matches", [])
    )

    partial_count = len(
        data.get("partial_matches", [])
    )

    missing_count = len(
        data.get("missing_skills", [])
    )

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

    total = (
        strong
        + project
        + partial
        + missing
    )

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

        text = text.split(
            "```json",
            1
        )[1].split(
            "```",
            1
        )[0].strip()

    elif "```" in text:

        text = text.split(
            "```",
            1
        )[1].split(
            "```",
            1
        )[0].strip()

    data = json.loads(text)

    data.setdefault("match_score", 0)
    data.setdefault(
        "recommendation",
        "MAYBE"
    )

    data.setdefault(
        "strong_matches",
        []
    )

    data.setdefault(
        "project_matches",
        []
    )

    data.setdefault(
        "partial_matches",
        []
    )

    data.setdefault(
        "missing_skills",
        []
    )

    data.setdefault(
        "learnable_skills",
        []
    )

    data.setdefault(
        "reason",
        ""
    )

    data.setdefault(
        "resume_focus",
        ""
    )

    data.setdefault(
        "interview_topics",
        []
    )

    return clean_analysis(
        data,
        job_description
    )


def analyze_job(
    job_description: str,
    db: Session
) -> dict:

    profile = db.query(
        UserProfile
    ).first()

    if not profile:
        raise ValueError(
            "Master profile not found. "
            "Create a profile before analyzing jobs."
        )

    candidate_profile = build_candidate_profile(
        profile
    )

    prompt = f"""
You are FRIDAY's Job Application Agent.

Analyze the candidate profile against the job description.

CANDIDATE PROFILE:
{candidate_profile}

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
Skills where the candidate has direct hands-on
implementation or demonstrated practical experience.

project_matches:
Skills demonstrated specifically through projects.

partial_matches:
Related knowledge, transferable experience,
or skills with limited demonstrated evidence.

missing_skills:
Important job requirements without demonstrated
experience in the candidate profile.

learnable_skills:
Missing skills that are realistic to learn before
an interview.

RULES:

1. Do not invent skills.
2. Do not exaggerate experience.
3. Do not claim professional experience when only project experience exists.
4. Do not return project names as skills.
5. Only include job-description-relevant skills.
6. Do not place the same skill in multiple categories.
7. Treat technologies explicitly present in the candidate profile as evidence.
8. reason must never be empty.
9. recommendation must be exactly APPLY, MAYBE, or SKIP.
"""

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    response = process_message(
        messages,
        task="job_analysis"
    )

    return extract_json(
        response,
        job_description
    )