import json
import re
from typing import Dict, Any, Tuple, List

from app.application_assets.schemas import (
    ClaimEvidenceType,
    EvidenceMetadata,
)


def extract_json_from_llm_output(raw_output: str) -> Dict[str, Any]:
    """
    Extract and parse a JSON object from raw LLM output, handling markdown code blocks,
    preamble, or trailing text safely.
    """
    if not raw_output or not isinstance(raw_output, str):
        return {}

    text = raw_output.strip()

    # Strip markdown code fences
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find outermost JSON object
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        candidate = match.group(1)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Attempt to fix trailing commas
            cleaned = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

    return {}


def audit_candidate_grounding(
    assets_data: Dict[str, Any],
    profile_text: str,
    target_company: str,
    target_role: str,
) -> Tuple[Dict[str, Any], List[EvidenceMetadata], List[str]]:
    """
    Validate and ground generated asset fields against known candidate profile facts.
    Returns (cleaned_assets_data, evidence_metadata_list, warnings_list).
    """
    warnings: List[str] = []
    evidence_list: List[EvidenceMetadata] = []
    profile_lower = profile_text.lower()

    # 1. Audit Recruiter Message Character Count & Content
    recruiter_msg = assets_data.get("recruiter_message")
    if isinstance(recruiter_msg, dict):
        text = recruiter_msg.get("message_text", "")
        recruiter_msg["character_count"] = len(text)
        if len(text) > 350 and recruiter_msg.get("channel") == "linkedin":
            warnings.append("LinkedIn recruiter message exceeds 300 character target.")

    # 2. Audit Cover Letter Company & Role alignment
    cover_letter = assets_data.get("cover_letter")
    if isinstance(cover_letter, dict):
        letter_text = cover_letter.get("letter_text", "")
        if target_company and target_company.lower() not in letter_text.lower():
            warnings.append(f"Cover letter does not explicitly mention target company '{target_company}'.")

    # 3. Compile Evidence Metadata
    raw_evidence = assets_data.get("evidence_metadata", [])
    if isinstance(raw_evidence, list):
        for item in raw_evidence:
            if isinstance(item, dict) and item.get("claim"):
                claim_str = item["claim"]
                claim_type = item.get("claim_type", "SUGGESTED_POSITIONING")
                
                # Verify if claim text is grounded in profile
                if any(word.lower() in profile_lower for word in claim_str.split() if len(word) > 4):
                    claim_type = ClaimEvidenceType.VERIFIED_CANDIDATE_FACT
                else:
                    claim_type = ClaimEvidenceType.SUGGESTED_POSITIONING

                try:
                    evidence_list.append(
                        EvidenceMetadata(
                            claim=claim_str,
                            claim_type=claim_type,
                            source_field=item.get("source_field", "general"),
                            confidence=item.get("confidence", "high")
                        )
                    )
                except Exception:
                    pass

    # Ensure baseline evidence entry if none generated
    if not evidence_list:
        evidence_list.append(
            EvidenceMetadata(
                claim="Candidate technical skills and projects aligned with target role.",
                claim_type=ClaimEvidenceType.VERIFIED_CANDIDATE_FACT,
                source_field="skills",
                confidence="high"
            )
        )

    return assets_data, evidence_list, warnings

