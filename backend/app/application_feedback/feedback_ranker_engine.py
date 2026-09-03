from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.autonomous_workflow.job_ranker import JobRankerEngine
from app.autonomous_workflow.schemas import WorkflowPriority
from app.application_feedback.models import FeedbackLearningSignal
from app.application_feedback.schemas import FeedbackRankResponse, SignalType
from app.application_feedback.repository import FeedbackRepository


class FeedbackRankerEngine:
    """
    Feedback-aware job prioritization engine.
    Enhances baseline match scoring by applying historical outcome signals,
    recurring skill gap penalties, and company rejection risk flags.
    """

    @classmethod
    def rank_with_feedback(
        cls,
        db: Session,
        company: str,
        role: str,
        match_score: int,
        missing_skills: Optional[List[str]] = None,
        platform: Optional[str] = "generic",
        profile_id: Optional[int] = None,
    ) -> FeedbackRankResponse:
        base_ranking = JobRankerEngine.rank_job(
            match_score=match_score,
            missing_skills_count=len(missing_skills) if missing_skills else 0,
        )

        base_score = base_ranking.final_score
        adjusted_score = base_score
        adjustments: List[str] = []
        risk_flags: List[str] = list(base_ranking.risk_flags)

        signals = FeedbackRepository.list_learning_signals(db, profile_id=profile_id)
        norm_company = company.strip().lower()
        norm_missing = [s.strip().lower() for s in (missing_skills or [])]

        for sig in signals:
            # 1. Company Rejection Signal
            if sig.signal_type == SignalType.COMPANY_REJECTION_CLUSTER.value:
                if sig.affected_company and sig.affected_company.strip().lower() == norm_company:
                    adjusted_score = max(0, adjusted_score - 15)
                    adjustments.append(f"Historical rejection cluster at {company} (-15 score penalty)")
                    risk_flags.append(f"Multiple previous rejections from {company}")

            # 2. Recurring Skill Gap Signal
            elif sig.signal_type == SignalType.SKILL_GAP_IDENTIFIED.value:
                if sig.affected_skill and sig.affected_skill.strip().lower() in norm_missing:
                    adjusted_score = max(0, adjusted_score - 10)
                    adjustments.append(f"Critical historical skill gap: {sig.affected_skill} (-10 score penalty)")
                    risk_flags.append(f"Requires {sig.affected_skill} which caused past interview rejections")

        adjusted_score = max(0, min(100, adjusted_score))

        # Re-derive priority tier
        if adjusted_score >= 85:
            prio = "URGENT"
            rec = "STRONGLY_RECOMMENDED"
        elif adjusted_score >= 70:
            prio = "HIGH"
            rec = "RECOMMENDED"
        elif adjusted_score >= 55:
            prio = "MEDIUM"
            rec = "CONSIDER"
        else:
            prio = "LOW"
            rec = "LOW_FIT"

        return FeedbackRankResponse(
            base_score=base_score,
            adjusted_score=adjusted_score,
            priority=prio,
            recommendation=rec,
            feedback_adjustments=adjustments,
            risk_flags=risk_flags,
        )
