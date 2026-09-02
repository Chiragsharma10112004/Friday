import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.memory.database import Base
from app.application_feedback.schemas import (
    OutcomeType,
    FeedbackStage,
    DifficultyRating,
    ExperienceRating,
    FieldIssueType,
    SignalType,
    OutcomeFeedbackResponse,
    AssetVersionResponse,
    FieldIssueResponse,
    FeedbackSignalResponse,
)


class ApplicationOutcomeFeedback(Base):
    __tablename__ = "application_outcome_feedback"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("tracked_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(Integer, nullable=True, index=True)

    company = Column(String(255), nullable=False, index=True)
    role = Column(String(255), nullable=False, index=True)

    outcome_type = Column(String(50), nullable=False, index=True)
    feedback_stage = Column(String(50), nullable=True)

    reasons_cited_json = Column(Text, nullable=True)
    skills_tested_json = Column(Text, nullable=True)
    skills_passed_json = Column(Text, nullable=True)
    skills_failed_json = Column(Text, nullable=True)

    difficulty_rating = Column(String(50), nullable=True)
    overall_experience = Column(String(50), nullable=True)

    salary_offered = Column(Float, nullable=True)
    interviewer_feedback = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_schema(self) -> OutcomeFeedbackResponse:
        reasons = json.loads(self.reasons_cited_json) if self.reasons_cited_json else []
        tested = json.loads(self.skills_tested_json) if self.skills_tested_json else []
        passed = json.loads(self.skills_passed_json) if self.skills_passed_json else []
        failed = json.loads(self.skills_failed_json) if self.skills_failed_json else []
        meta = json.loads(self.metadata_json) if self.metadata_json else {}

        try:
            o_type = OutcomeType(self.outcome_type)
        except ValueError:
            o_type = OutcomeType.REJECTED_AFTER_RESUME

        f_stage = None
        if self.feedback_stage:
            try:
                f_stage = FeedbackStage(self.feedback_stage)
            except ValueError:
                f_stage = None

        diff = None
        if self.difficulty_rating:
            try:
                diff = DifficultyRating(self.difficulty_rating)
            except ValueError:
                diff = None

        exp = None
        if self.overall_experience:
            try:
                exp = ExperienceRating(self.overall_experience)
            except ValueError:
                exp = None

        return OutcomeFeedbackResponse(
            id=self.id,
            application_id=self.application_id,
            profile_id=self.profile_id,
            company=self.company,
            role=self.role,
            outcome_type=o_type,
            feedback_stage=f_stage,
            reasons_cited=reasons,
            skills_tested=tested,
            skills_passed=passed,
            skills_failed=failed,
            difficulty=diff,
            experience=exp,
            salary_offered=self.salary_offered,
            interviewer_feedback=self.interviewer_feedback,
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=meta,
        )


class ApplicationAssetVersion(Base):
    __tablename__ = "application_asset_versions"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("tracked_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id = Column(Integer, nullable=True, index=True)

    resume_summary = Column(Text, nullable=True)
    resume_bullets_json = Column(Text, nullable=True)
    cover_letter_text = Column(Text, nullable=True)
    customizations_applied_json = Column(Text, nullable=True)
    asset_score_at_application = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_schema(self) -> AssetVersionResponse:
        bullets = json.loads(self.resume_bullets_json) if self.resume_bullets_json else []
        customizations = json.loads(self.customizations_applied_json) if self.customizations_applied_json else []

        return AssetVersionResponse(
            id=self.id,
            application_id=self.application_id,
            workflow_id=self.workflow_id,
            resume_summary=self.resume_summary,
            resume_bullets=bullets,
            cover_letter_text=self.cover_letter_text,
            customizations_applied=customizations,
            asset_score_at_application=self.asset_score_at_application,
            created_at=self.created_at,
        )


class ApplicationFieldIssue(Base):
    __tablename__ = "application_field_issues"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, nullable=True, index=True)
    workflow_id = Column(Integer, nullable=True, index=True)

    platform = Column(String(100), nullable=False, default="generic", index=True)
    field_name = Column(String(255), nullable=False)
    field_label = Column(String(255), nullable=True)
    field_type = Column(String(100), nullable=True)

    issue_type = Column(String(50), nullable=False, default=FieldIssueType.UNRECOGNIZED_FIELD.value, index=True)
    error_message = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def to_schema(self) -> FieldIssueResponse:
        try:
            i_type = FieldIssueType(self.issue_type)
        except ValueError:
            i_type = FieldIssueType.UNRECOGNIZED_FIELD

        return FieldIssueResponse(
            id=self.id,
            application_id=self.application_id,
            workflow_id=self.workflow_id,
            platform=self.platform,
            field_name=self.field_name,
            field_label=self.field_label,
            field_type=self.field_type,
            issue_type=i_type,
            error_message=self.error_message,
            resolved=self.resolved,
            created_at=self.created_at,
            resolved_at=self.resolved_at,
        )


class FeedbackLearningSignal(Base):
    __tablename__ = "feedback_learning_signals"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, nullable=True, index=True)

    signal_type = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    confidence_score = Column(Integer, nullable=False, default=80)

    affected_company = Column(String(255), nullable=True, index=True)
    affected_skill = Column(String(255), nullable=True, index=True)
    recommended_action = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_schema(self) -> FeedbackSignalResponse:
        meta = json.loads(self.metadata_json) if self.metadata_json else {}

        try:
            s_type = SignalType(self.signal_type)
        except ValueError:
            s_type = SignalType.SKILL_GAP_IDENTIFIED

        return FeedbackSignalResponse(
            id=self.id,
            signal_type=s_type,
            title=self.title,
            description=self.description,
            confidence_score=self.confidence_score,
            affected_company=self.affected_company,
            affected_skill=self.affected_skill,
            recommended_action=self.recommended_action,
            created_at=self.created_at,
            metadata=meta,
        )
