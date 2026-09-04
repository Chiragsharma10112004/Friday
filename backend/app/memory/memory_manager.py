import json
import re
import logging
from typing import Optional

from app.core.brain.manager import process_message
from app.memory.repository import save_memory, get_all_memory

logger = logging.getLogger("friday.memory")

MEMORY_PROMPT = """
You are a memory extraction engine.

Extract ONLY permanent facts about the user.

Return ONLY valid JSON.

If there are no permanent facts return {}.

Example:
{
    "name": "Chirag Sharma",
    "favorite_language": "Python",
    "university": "GITAM University"
}
"""


def build_memory_context(db) -> str:
    """
    Build a comprehensive context string combining:
    1. Structured User Profile (from user_profile table)
    2. Long-term key-value memories (from user_memory table)
    3. Active career & application intelligence pipeline summary
    """
    sections = []

    # 1. Structured User Profile
    try:
        from app.profile.repository import get_profile
        profile = get_profile(db)
        if profile:
            profile_facts = []
            if profile.first_name or profile.last_name:
                full_name = f"{profile.first_name or ''} {profile.last_name or ''}".strip()
                if full_name:
                    profile_facts.append(f"name: {full_name}")
            if profile.email:
                profile_facts.append(f"email: {profile.email}")
            if profile.headline:
                profile_facts.append(f"headline: {profile.headline}")
            if profile.location:
                profile_facts.append(f"location: {profile.location}")
            if profile.university:
                profile_facts.append(f"university: {profile.university}")
            if profile.skills:
                profile_facts.append(f"skills: {profile.skills}")
            if profile.target_roles:
                profile_facts.append(f"target_roles: {profile.target_roles}")
            if profile.preferred_locations:
                profile_facts.append(f"preferred_locations: {profile.preferred_locations}")
            
            if profile_facts:
                sections.append("User Profile:\n" + "\n".join(profile_facts))
    except Exception as e:
        logger.debug("Could not load user profile into memory context: %s", e)

    # 2. Long-term key-value memory
    try:
        memory = get_all_memory(db)
        if memory:
            memory_facts = [f"{key}: {value}" for key, value in memory.items()]
            sections.append("Known facts about the user:\n" + "\n".join(memory_facts))
    except Exception as e:
        logger.debug("Could not load user memory into memory context: %s", e)

    # 3. Active Applications & Career Intelligence Pipeline Summary
    try:
        from app.career_intelligence.service import get_application_health_list
        from app.application_pipeline.service import get_pipeline_summary
        summary = get_pipeline_summary(db)
        health_report = get_application_health_list(db)
        
        pipeline_info = []
        if summary:
            pipeline_info.append(
                f"Total Applications: {summary.total_applications}, "
                f"Status Breakdown: {summary.status_counts}"
            )
        if health_report and health_report.items:
            pipeline_info.append(
                f"Application Health Summary: {health_report.healthy_count} Healthy, "
                f"{health_report.attention_needed_count} Attention Needed, "
                f"{health_report.stale_count} Stale, {health_report.critical_count} Critical."
            )
            for item in health_report.items[:5]:
                issues_str = f" (Issues: {', '.join(item.issues)})" if item.issues else ""
                recs_str = f" [Recommended: {', '.join(item.recommendations)}]" if item.recommendations else ""
                pipeline_info.append(
                    f"- {item.company} ({item.role}): Status={item.status}, "
                    f"Health={item.health_status} (Score {item.health_score}/100){issues_str}{recs_str}"
                )
        
        if pipeline_info:
            sections.append("Active Job Application & Career Pipeline Status:\n" + "\n".join(pipeline_info))
    except Exception as e:
        logger.debug("Could not load application pipeline summary into context: %s", e)

    if not sections:
        return ""

    return "\n\n".join(sections)


def _extract_facts_rule_based(message: str) -> dict:
    """
    Deterministic rule-based fact extraction for common self-introductions and preference statements.
    Guarantees deterministic learning even if LLM parsing fails or model is offline.
    """
    facts = {}
    cleaned = message.strip()

    # Favorite language: "My favorite language is Python" / "My favorite programming language is Python"
    m = re.search(r"my favorite (?:programming )?language is ([A-Za-z0-9+#\.\s]+)", cleaned, re.IGNORECASE)
    if m:
        facts["favorite_language"] = m.group(1).strip().rstrip(".").rstrip(",")

    # Name: "My name is John Doe" / "Call me John"
    m = re.search(r"(?:my name is|call me)\s+([A-Za-z\s]+)", cleaned, re.IGNORECASE)
    if m:
        val = m.group(1).strip().rstrip(".").rstrip(",")
        words = [w.lower() for w in val.split()]
        if len(words) <= 4 and not any(w in words for w in ["a", "an", "the", "looking", "trying", "working", "not"]):
            facts["name"] = val

    # Email: "My email is user@example.com"
    m = re.search(r"my email is\s+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", cleaned, re.IGNORECASE)
    if m:
        facts["email"] = m.group(1).strip()

    # Location: "I live in San Francisco" / "My location is New York"
    m = re.search(r"(?:i live in|my location is)\s+([A-Za-z\s,]+)", cleaned, re.IGNORECASE)
    if m:
        facts["location"] = m.group(1).strip().rstrip(".").rstrip(",")

    # Target Role: "My target role is Backend Engineer" / "I am looking for a Senior Developer role"
    m = re.search(r"my target role is\s+([A-Za-z\s]+)", cleaned, re.IGNORECASE)
    if m:
        facts["target_role"] = m.group(1).strip().rstrip(".").rstrip(",")

    # Remember that X is Y
    m = re.search(r"remember that ([A-Za-z0-9_\s]+) is ([A-Za-z0-9_\s\.\-]+)", cleaned, re.IGNORECASE)
    if m:
        key = m.group(1).strip().lower().replace(" ", "_")
        val = m.group(2).strip().rstrip(".")
        facts[key] = val

    return facts


def process_memory(db, message: str):
    """
    Extract permanent facts about the user from the incoming message
    using both LLM intelligence and deterministic rule-based extraction.
    """
    # 1. Deterministic Rule-Based Extraction
    rule_facts = _extract_facts_rule_based(message)
    for key, value in rule_facts.items():
        if key and value:
            save_memory(db, key, str(value))

    # If rule-based extraction already captured facts, or if message is clearly a query/greeting, skip LLM extraction
    if rule_facts:
        return

    clean_msg = message.strip().lower()
    if clean_msg.startswith(("what", "where", "how", "who", "when", "why", "can you", "could you", "summarize", "tell me", "list", "show", "is ")) or clean_msg in {"hi", "hello", "hey"}:
        return

    messages = [
        {
            "role": "system",
            "content": MEMORY_PROMPT
        },
        {
            "role": "user",
            "content": message
        }
    ]

    try:
        result = process_message(messages, task="memory_extraction")
        if result:
            # Strip markdown code blocks
            cleaned_result = result.strip()
            if "```json" in cleaned_result:
                cleaned_result = cleaned_result.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_result:
                cleaned_result = cleaned_result.split("```")[1].split("```")[0].strip()

            memory_dict = None
            try:
                memory_dict = json.loads(cleaned_result)
            except json.JSONDecodeError:
                match = re.search(r"\{.*\}", result, re.DOTALL)
                if match:
                    try:
                        memory_dict = json.loads(match.group())
                    except Exception:
                        pass

            if isinstance(memory_dict, dict):
                for key, value in memory_dict.items():
                    if key and value is not None and str(value).strip():
                        save_memory(db, str(key).strip(), str(value).strip())
    except Exception as err:
        logger.debug("LLM memory extraction skipped or failed: %s", err)
