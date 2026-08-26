from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.autonomous_workflow.schemas import WorkflowPriority


class JobRankingResult(BaseModel):
    final_score: int = Field(ge=0, le=100)
    priority: WorkflowPriority
    recommendation: str
    reasons: List[str]
    risk_flags: List[str]


class JobRankerEngine:
    """
    Intelligent, deterministic ranking and prioritization engine for job opportunities and workflows.
    """

    DEFAULT_URGENT_THRESHOLD = 85
    DEFAULT_HIGH_THRESHOLD = 70
    DEFAULT_MEDIUM_THRESHOLD = 55

    @classmethod
    def rank_job(
        cls,
        match_score: Optional[int] = None,
        recommendation: Optional[str] = None,
        missing_skills_count: int = 0,
        has_referral: bool = False,
        is_remote: Optional[bool] = None,
        urgent_flag: bool = False,
    ) -> JobRankingResult:
        reasons: List[str] = []
        risk_flags: List[str] = []

        base_score = match_score if match_score is not None else 65

        # Factor adjustments
        score = base_score
        if has_referral:
            score = min(100, score + 10)
            reasons.append("Employee referral connection available (+10 match advantage)")

        if missing_skills_count > 3:
            risk_flags.append(f"Multiple skill gaps identified ({missing_skills_count} missing requirements)")
        elif missing_skills_count == 0 and match_score is not None and match_score >= 80:
            reasons.append("Complete skills alignment with target job requirements")

        if is_remote:
            reasons.append("Remote workplace flexibility")

        # Determine priority and recommendation
        if score >= cls.DEFAULT_URGENT_THRESHOLD or urgent_flag:
            priority = WorkflowPriority.URGENT if (urgent_flag or score >= 90) else WorkflowPriority.HIGH
            rec = "STRONGLY_RECOMMENDED"
            reasons.append("Top-tier match alignment for immediate application preparation")
        elif score >= cls.DEFAULT_HIGH_THRESHOLD:
            priority = WorkflowPriority.HIGH
            rec = "RECOMMENDED"
            reasons.append("Strong profile alignment suitable for tailored submission")
        elif score >= cls.DEFAULT_MEDIUM_THRESHOLD:
            priority = WorkflowPriority.MEDIUM
            rec = "CONSIDER"
            reasons.append("Moderate profile alignment; asset tailoring recommended")
        else:
            priority = WorkflowPriority.LOW
            rec = "LOW_FIT"
            risk_flags.append("Low overall alignment with candidate target profile")

        return JobRankingResult(
            final_score=max(0, min(100, score)),
            priority=priority,
            recommendation=rec,
            reasons=reasons,
            risk_flags=risk_flags
        )
