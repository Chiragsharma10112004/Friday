import json
from collections import defaultdict
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.application_feedback.models import ApplicationAssetVersion, ApplicationOutcomeFeedback
from app.application_feedback.schemas import AssetPerformanceResponse, OutcomeType
from app.application_feedback.repository import FeedbackRepository
from app.application_pipeline.models import TrackedApplication


class AssetVersioningEngine:
    """
    Manages snapshotting of resume and cover letter versions for applications,
    and analyzes conversion performance of different tailored asset configurations.
    """

    @classmethod
    def record_snapshot(
        cls,
        db: Session,
        application_id: int,
        workflow_id: Optional[int] = None,
        resume_summary: Optional[str] = None,
        resume_bullets: Optional[List[str]] = None,
        cover_letter_text: Optional[str] = None,
        customizations_applied: Optional[List[str]] = None,
        asset_score_at_application: Optional[int] = None,
    ) -> ApplicationAssetVersion:
        return FeedbackRepository.create_asset_version(
            db=db,
            application_id=application_id,
            workflow_id=workflow_id,
            resume_summary=resume_summary,
            resume_bullets=resume_bullets,
            cover_letter_text=cover_letter_text,
            customizations_applied=customizations_applied,
            asset_score_at_application=asset_score_at_application,
        )

    @classmethod
    def analyze_asset_performance(cls, db: Session) -> List[AssetPerformanceResponse]:
        """
        Analyzes interview and offer rates grouped by customization keywords and asset versions.
        """
        versions = FeedbackRepository.list_all_asset_versions(db)
        outcomes = FeedbackRepository.list_outcome_feedback(db)

        # Map application_id -> outcome
        outcome_map: Dict[int, ApplicationOutcomeFeedback] = {o.application_id: o for o in outcomes}

        # Group stats by customization focus / tag
        stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"apps": 0, "interviews": 0, "offers": 0})

        for v in versions:
            customizations = json.loads(v.customizations_applied_json) if v.customizations_applied_json else ["Standard Profile"]
            if not customizations:
                customizations = ["Standard Profile"]

            outcome = outcome_map.get(v.application_id)
            is_interview = False
            is_offer = False

            if outcome:
                if outcome.outcome_type in (
                    OutcomeType.OFFER_RECEIVED.value,
                    OutcomeType.OFFER_ACCEPTED.value,
                    OutcomeType.OFFER_DECLINED.value,
                ):
                    is_interview = True
                    is_offer = True
                elif outcome.outcome_type in (
                    OutcomeType.REJECTED_AFTER_SCREEN.value,
                    OutcomeType.REJECTED_AFTER_TECHNICAL.value,
                    OutcomeType.REJECTED_AFTER_FINAL.value,
                ):
                    is_interview = True

            for cust in customizations:
                clean_cust = cust.strip().title()
                stats[clean_cust]["apps"] += 1
                if is_interview:
                    stats[clean_cust]["interviews"] += 1
                if is_offer:
                    stats[clean_cust]["offers"] += 1

        results: List[AssetPerformanceResponse] = []
        for focus, data in sorted(stats.items(), key=lambda x: x[1]["apps"], reverse=True):
            interview_rate = (data["interviews"] / data["apps"]) * 100.0 if data["apps"] > 0 else 0.0
            results.append(
                AssetPerformanceResponse(
                    customization_focus=focus,
                    applications_count=data["apps"],
                    interviews_count=data["interviews"],
                    offers_count=data["offers"],
                    interview_rate=round(interview_rate, 2),
                )
            )

        return results
