import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.application_feedback.models import (
    ApplicationOutcomeFeedback,
    ApplicationAssetVersion,
    ApplicationFieldIssue,
    FeedbackLearningSignal,
)
from app.application_feedback.schemas import (
    OutcomeType,
    FeedbackStage,
    DifficultyRating,
    ExperienceRating,
    FieldIssueType,
    SignalType,
)


class FeedbackRepository:
    """Repository layer for persisting application outcomes, asset versions, field issues, and learning signals."""

    # ==========================================
    # OUTCOME FEEDBACK CRUD
    # ==========================================

    @classmethod
    def create_outcome_feedback(
        cls,
        db: Session,
        application_id: int,
        company: str,
        role: str,
        outcome_type: OutcomeType,
        profile_id: Optional[int] = None,
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
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ApplicationOutcomeFeedback:
        now = datetime.now(timezone.utc)
        record = ApplicationOutcomeFeedback(
            application_id=application_id,
            profile_id=profile_id,
            company=company,
            role=role,
            outcome_type=outcome_type.value if isinstance(outcome_type, OutcomeType) else str(outcome_type),
            feedback_stage=feedback_stage.value if isinstance(feedback_stage, FeedbackStage) else (str(feedback_stage) if feedback_stage else None),
            reasons_cited_json=json.dumps(reasons_cited) if reasons_cited else None,
            skills_tested_json=json.dumps(skills_tested) if skills_tested else None,
            skills_passed_json=json.dumps(skills_passed) if skills_passed else None,
            skills_failed_json=json.dumps(skills_failed) if skills_failed else None,
            difficulty_rating=difficulty.value if isinstance(difficulty, DifficultyRating) else (str(difficulty) if difficulty else None),
            overall_experience=experience.value if isinstance(experience, ExperienceRating) else (str(experience) if experience else None),
            salary_offered=salary_offered,
            interviewer_feedback=interviewer_feedback,
            notes=notes,
            metadata_json=json.dumps(metadata) if metadata else None,
            created_at=now,
            updated_at=now,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def get_outcome_feedback(cls, db: Session, feedback_id: int) -> Optional[ApplicationOutcomeFeedback]:
        return db.query(ApplicationOutcomeFeedback).filter(ApplicationOutcomeFeedback.id == feedback_id).first()

    @classmethod
    def list_outcome_feedback(
        cls,
        db: Session,
        application_id: Optional[int] = None,
        profile_id: Optional[int] = None,
        company: Optional[str] = None,
        outcome_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[ApplicationOutcomeFeedback]:
        query = db.query(ApplicationOutcomeFeedback)
        if application_id:
            query = query.filter(ApplicationOutcomeFeedback.application_id == application_id)
        if profile_id:
            query = query.filter(ApplicationOutcomeFeedback.profile_id == profile_id)
        if company:
            query = query.filter(ApplicationOutcomeFeedback.company.ilike(f"%{company}%"))
        if outcome_type:
            query = query.filter(ApplicationOutcomeFeedback.outcome_type == outcome_type)
        return query.order_by(desc(ApplicationOutcomeFeedback.created_at)).limit(limit).all()

    # ==========================================
    # ASSET VERSION CRUD
    # ==========================================

    @classmethod
    def create_asset_version(
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
        record = ApplicationAssetVersion(
            application_id=application_id,
            workflow_id=workflow_id,
            resume_summary=resume_summary,
            resume_bullets_json=json.dumps(resume_bullets) if resume_bullets else None,
            cover_letter_text=cover_letter_text,
            customizations_applied_json=json.dumps(customizations_applied) if customizations_applied else None,
            asset_score_at_application=asset_score_at_application,
            created_at=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def get_asset_versions_by_application(cls, db: Session, application_id: int) -> List[ApplicationAssetVersion]:
        return db.query(ApplicationAssetVersion).filter(
            ApplicationAssetVersion.application_id == application_id
        ).order_by(desc(ApplicationAssetVersion.created_at)).all()

    @classmethod
    def list_all_asset_versions(cls, db: Session, limit: int = 200) -> List[ApplicationAssetVersion]:
        return db.query(ApplicationAssetVersion).order_by(desc(ApplicationAssetVersion.created_at)).limit(limit).all()

    # ==========================================
    # FIELD ISSUE CRUD
    # ==========================================

    @classmethod
    def create_field_issue(
        cls,
        db: Session,
        field_name: str,
        platform: str = "generic",
        application_id: Optional[int] = None,
        workflow_id: Optional[int] = None,
        field_label: Optional[str] = None,
        field_type: Optional[str] = None,
        issue_type: FieldIssueType = FieldIssueType.UNRECOGNIZED_FIELD,
        error_message: Optional[str] = None,
    ) -> ApplicationFieldIssue:
        record = ApplicationFieldIssue(
            application_id=application_id,
            workflow_id=workflow_id,
            platform=platform,
            field_name=field_name,
            field_label=field_label,
            field_type=field_type,
            issue_type=issue_type.value if isinstance(issue_type, FieldIssueType) else str(issue_type),
            error_message=error_message,
            resolved=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def get_field_issue(cls, db: Session, issue_id: int) -> Optional[ApplicationFieldIssue]:
        return db.query(ApplicationFieldIssue).filter(ApplicationFieldIssue.id == issue_id).first()

    @classmethod
    def list_field_issues(
        cls,
        db: Session,
        application_id: Optional[int] = None,
        platform: Optional[str] = None,
        issue_type: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 100,
    ) -> List[ApplicationFieldIssue]:
        query = db.query(ApplicationFieldIssue)
        if application_id:
            query = query.filter(ApplicationFieldIssue.application_id == application_id)
        if platform:
            query = query.filter(ApplicationFieldIssue.platform == platform)
        if issue_type:
            query = query.filter(ApplicationFieldIssue.issue_type == issue_type)
        if resolved is not None:
            query = query.filter(ApplicationFieldIssue.resolved == resolved)
        return query.order_by(desc(ApplicationFieldIssue.created_at)).limit(limit).all()

    @classmethod
    def resolve_field_issue(cls, db: Session, issue_id: int) -> Optional[ApplicationFieldIssue]:
        record = cls.get_field_issue(db, issue_id)
        if record:
            record.resolved = True
            record.resolved_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(record)
        return record

    # ==========================================
    # LEARNING SIGNAL CRUD
    # ==========================================

    @classmethod
    def create_learning_signal(
        cls,
        db: Session,
        signal_type: SignalType,
        title: str,
        description: str,
        confidence_score: int,
        recommended_action: str,
        profile_id: Optional[int] = None,
        affected_company: Optional[str] = None,
        affected_skill: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FeedbackLearningSignal:
        record = FeedbackLearningSignal(
            profile_id=profile_id,
            signal_type=signal_type.value if isinstance(signal_type, SignalType) else str(signal_type),
            title=title,
            description=description,
            confidence_score=confidence_score,
            affected_company=affected_company,
            affected_skill=affected_skill,
            recommended_action=recommended_action,
            metadata_json=json.dumps(metadata) if metadata else None,
            created_at=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def list_learning_signals(cls, db: Session, profile_id: Optional[int] = None, limit: int = 50) -> List[FeedbackLearningSignal]:
        query = db.query(FeedbackLearningSignal)
        if profile_id:
            query = query.filter(FeedbackLearningSignal.profile_id == profile_id)
        return query.order_by(desc(FeedbackLearningSignal.created_at)).limit(limit).all()

    @classmethod
    def clear_learning_signals(cls, db: Session, profile_id: Optional[int] = None):
        query = db.query(FeedbackLearningSignal)
        if profile_id:
            query = query.filter(FeedbackLearningSignal.profile_id == profile_id)
        query.delete()
        db.commit()
