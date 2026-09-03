from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

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
    OutcomeFeedbackCreateRequest,
    OutcomeFeedbackResponse,
    AssetVersionCreateRequest,
    AssetVersionResponse,
    FieldIssueCreateRequest,
    FieldIssueResponse,
    AnalyticsSummaryResponse,
    ConversionFunnelResponse,
    PlatformPerformanceResponse,
    AssetPerformanceResponse,
    FeedbackSignalResponse,
    FeedbackRankRequest,
    FeedbackRankResponse,
)
from app.application_feedback.repository import FeedbackRepository
from app.application_feedback.outcome_engine import OutcomeEngine
from app.application_feedback.asset_versioning import AssetVersioningEngine
from app.application_feedback.field_issue_tracker import FieldIssueTracker
from app.application_feedback.analytics_engine import AnalyticsEngine
from app.application_feedback.feedback_ranker_engine import FeedbackRankerEngine


class ApplicationFeedbackService:
    """
    Unified service facade for Phase 8 Application Feedback, Asset Versioning,
    Field Issue Diagnosis, and Career Analytics.
    """

    def record_outcome(
        self,
        db: Session,
        req: OutcomeFeedbackCreateRequest,
    ) -> OutcomeFeedbackResponse:
        record = OutcomeEngine.record_outcome_and_sync_pipeline(
            db=db,
            application_id=req.application_id,
            outcome_type=req.outcome_type,
            feedback_stage=req.feedback_stage,
            reasons_cited=req.reasons_cited,
            skills_tested=req.skills_tested,
            skills_passed=req.skills_passed,
            skills_failed=req.skills_failed,
            difficulty=req.difficulty,
            experience=req.experience,
            salary_offered=req.salary_offered,
            interviewer_feedback=req.interviewer_feedback,
            notes=req.notes,
        )
        return record.to_schema()

    def get_outcome(self, db: Session, feedback_id: int) -> Optional[OutcomeFeedbackResponse]:
        record = FeedbackRepository.get_outcome_feedback(db, feedback_id)
        return record.to_schema() if record else None

    def list_outcomes(
        self,
        db: Session,
        application_id: Optional[int] = None,
        profile_id: Optional[int] = None,
        company: Optional[str] = None,
        outcome_type: Optional[str] = None,
    ) -> List[OutcomeFeedbackResponse]:
        records = FeedbackRepository.list_outcome_feedback(
            db=db,
            application_id=application_id,
            profile_id=profile_id,
            company=company,
            outcome_type=outcome_type,
        )
        return [r.to_schema() for r in records]

    def snapshot_asset_version(
        self,
        db: Session,
        req: AssetVersionCreateRequest,
    ) -> AssetVersionResponse:
        record = AssetVersioningEngine.record_snapshot(
            db=db,
            application_id=req.application_id,
            workflow_id=req.workflow_id,
            resume_summary=req.resume_summary,
            resume_bullets=req.resume_bullets,
            cover_letter_text=req.cover_letter_text,
            customizations_applied=req.customizations_applied,
            asset_score_at_application=req.asset_score_at_application,
        )
        return record.to_schema()

    def get_asset_versions(self, db: Session, application_id: int) -> List[AssetVersionResponse]:
        records = FeedbackRepository.get_asset_versions_by_application(db, application_id)
        return [r.to_schema() for r in records]

    def log_field_issue(
        self,
        db: Session,
        req: FieldIssueCreateRequest,
    ) -> FieldIssueResponse:
        record = FieldIssueTracker.log_issue(
            db=db,
            field_name=req.field_name,
            platform=req.platform or "generic",
            application_id=req.application_id,
            workflow_id=req.workflow_id,
            field_label=req.field_label,
            field_type=req.field_type,
            issue_type=req.issue_type,
            error_message=req.error_message,
        )
        return record.to_schema()

    def resolve_field_issue(self, db: Session, issue_id: int) -> Optional[FieldIssueResponse]:
        record = FieldIssueTracker.resolve_issue(db, issue_id)
        return record.to_schema() if record else None

    def list_field_issues(
        self,
        db: Session,
        application_id: Optional[int] = None,
        platform: Optional[str] = None,
        issue_type: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> List[FieldIssueResponse]:
        records = FieldIssueTracker.list_issues(
            db=db,
            application_id=application_id,
            platform=platform,
            issue_type=issue_type,
            resolved=resolved,
        )
        return [r.to_schema() for r in records]

    def get_analytics_summary(self, db: Session) -> AnalyticsSummaryResponse:
        return AnalyticsEngine.calculate_summary(db)

    def get_funnel(self, db: Session) -> ConversionFunnelResponse:
        return AnalyticsEngine.calculate_funnel(db)

    def get_platform_metrics(self, db: Session) -> List[PlatformPerformanceResponse]:
        return AnalyticsEngine.calculate_platform_metrics(db)

    def get_asset_performance(self, db: Session) -> List[AssetPerformanceResponse]:
        return AssetVersioningEngine.analyze_asset_performance(db)

    def list_signals(self, db: Session, profile_id: Optional[int] = None) -> List[FeedbackSignalResponse]:
        records = FeedbackRepository.list_learning_signals(db, profile_id=profile_id)
        return [r.to_schema() for r in records]

    def rank_opportunity(self, db: Session, req: FeedbackRankRequest) -> FeedbackRankResponse:
        return FeedbackRankerEngine.rank_with_feedback(
            db=db,
            company=req.company,
            role=req.role,
            match_score=req.match_score,
            missing_skills=req.missing_skills,
            platform=req.platform,
        )


default_feedback_service = ApplicationFeedbackService()
