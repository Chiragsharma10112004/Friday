import json
from collections import Counter
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.application_pipeline.models import TrackedApplication, ApplicationTimelineEvent, ApplicationStatusHistory
from app.application_pipeline.schemas import ApplicationStatus
from app.application_feedback.models import ApplicationOutcomeFeedback, FeedbackLearningSignal
from app.application_feedback.schemas import (
    OutcomeType,
    FeedbackStage,
    DifficultyRating,
    ExperienceRating,
    SignalType,
)
from app.application_feedback.repository import FeedbackRepository


class OutcomeEngine:
    """
    Intelligent engine that processes application/interview outcomes, updates application states,
    extracts structured feedback patterns, and discovers actionable learning signals.
    """

    @classmethod
    def record_outcome_and_sync_pipeline(
        cls,
        db: Session,
        application_id: int,
        outcome_type: OutcomeType,
        feedback_stage: Optional[FeedbackStage] = None,
        reasons_cited: Optional[List[str]] = None,
        skills_tested: Optional[List[str]] = None,
        skills_passed: Optional[List[str]] = None,
        skills_failed: Optional[List[str]] = None,
        difficulty: Optional[DifficultyRating] = None,
        experience: Optional[ExperienceRating] = None,
        salary_offered: Optional[float] = None,
        interviewer_feedback: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ApplicationOutcomeFeedback:
        app = db.query(TrackedApplication).filter(TrackedApplication.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found")

        now = datetime.now(timezone.utc)
        prev_status = app.status

        # 1. Update TrackedApplication status & dates
        if outcome_type in (OutcomeType.OFFER_RECEIVED, OutcomeType.OFFER_ACCEPTED, OutcomeType.OFFER_DECLINED):
            app.status = ApplicationStatus.OFFER.value
            if not app.offer_date:
                app.offer_date = now
        elif outcome_type in (
            OutcomeType.REJECTED_AFTER_RESUME,
            OutcomeType.REJECTED_AFTER_SCREEN,
            OutcomeType.REJECTED_AFTER_TECHNICAL,
            OutcomeType.REJECTED_AFTER_FINAL,
        ):
            app.status = ApplicationStatus.REJECTED.value
            if not app.rejection_date:
                app.rejection_date = now
        elif outcome_type == OutcomeType.WITHDRAWN:
            app.status = ApplicationStatus.WITHDRAWN.value
            if not app.withdrawal_date:
                app.withdrawal_date = now
        elif outcome_type == OutcomeType.GHOSTED:
            app.status = ApplicationStatus.ARCHIVED.value

        app.last_status_update = now

        # 2. Record Status History
        if prev_status != app.status:
            history = ApplicationStatusHistory(
                application_id=app.id,
                from_status=prev_status,
                to_status=app.status,
                timestamp=now,
                note=f"Outcome recorded: {outcome_type.value}"
            )
            db.add(history)

        # 3. Record Timeline Event
        event_desc = f"Application outcome recorded: {outcome_type.value}"
        if feedback_stage:
            event_desc += f" at stage {feedback_stage.value}"
        timeline_event = ApplicationTimelineEvent(
            application_id=app.id,
            event_type="OUTCOME_RECORDED",
            description=event_desc,
            event_metadata=json.dumps({
                "outcome_type": outcome_type.value,
                "feedback_stage": feedback_stage.value if feedback_stage else None,
                "reasons_cited": reasons_cited or [],
                "skills_failed": skills_failed or []
            }),
            timestamp=now
        )
        db.add(timeline_event)
        db.commit()

        # 4. Persist Outcome Feedback
        feedback = FeedbackRepository.create_outcome_feedback(
            db=db,
            application_id=app.id,
            company=app.company,
            role=app.role,
            outcome_type=outcome_type,
            profile_id=app.profile_id,
            feedback_stage=feedback_stage,
            reasons_cited=reasons_cited,
            skills_tested=skills_tested,
            skills_passed=skills_passed,
            skills_failed=skills_failed,
            difficulty=difficulty,
            experience=experience,
            salary_offered=salary_offered,
            interviewer_feedback=interviewer_feedback,
            notes=notes,
        )

        # 5. Refresh learning signals
        cls.extract_learning_signals(db, profile_id=app.profile_id)

        return feedback

    @classmethod
    def extract_learning_signals(cls, db: Session, profile_id: Optional[int] = None) -> List[FeedbackLearningSignal]:
        """
        Analyzes all feedback records to discover recurring skill gaps, company rejection patterns,
        and high-converting resume strategies.
        """
        # Clear existing dynamic signals to recalculate fresh insights
        FeedbackRepository.clear_learning_signals(db, profile_id=profile_id)

        all_feedback = FeedbackRepository.list_outcome_feedback(db, profile_id=profile_id, limit=500)
        signals: List[FeedbackLearningSignal] = []

        # A. Detect Recurring Skill Gaps
        failed_skills: List[str] = []
        for fb in all_feedback:
            if fb.skills_failed_json:
                try:
                    skills = json.loads(fb.skills_failed_json)
                    failed_skills.extend([s.strip().title() for s in skills if s.strip()])
                except Exception:
                    pass

        skill_counts = Counter(failed_skills)
        for skill, count in skill_counts.items():
            if count >= 2:
                sig = FeedbackRepository.create_learning_signal(
                    db=db,
                    signal_type=SignalType.SKILL_GAP_IDENTIFIED,
                    title=f"Recurring Skill Gap: {skill}",
                    description=f"{skill} was identified as a gap in {count} separate application/interview outcomes.",
                    confidence_score=min(95, 70 + count * 10),
                    affected_skill=skill,
                    recommended_action=f"Focus on upskilling and building a portfolio project showcasing {skill}.",
                    profile_id=profile_id,
                    metadata={"occurrence_count": count, "skill": skill}
                )
                signals.append(sig)

        # B. Detect Company Rejection Clusters
        company_rejections: List[str] = []
        for fb in all_feedback:
            if "REJECTED" in fb.outcome_type:
                company_rejections.append(fb.company.strip())

        company_counts = Counter(company_rejections)
        for company, count in company_counts.items():
            if count >= 2:
                sig = FeedbackRepository.create_learning_signal(
                    db=db,
                    signal_type=SignalType.COMPANY_REJECTION_CLUSTER,
                    title=f"Rejection Pattern at {company}",
                    description=f"You have encountered {count} rejections from {company}. Resume tailoring or prerequisite adjustment recommended.",
                    confidence_score=min(90, 65 + count * 10),
                    affected_company=company,
                    recommended_action=f"Re-evaluate qualifications, obtain an employee referral, or revise resume focus for {company}.",
                    profile_id=profile_id,
                    metadata={"rejection_count": count, "company": company}
                )
                signals.append(sig)

        return signals
