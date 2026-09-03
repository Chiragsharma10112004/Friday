import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.profile.models import UserProfile
from app.application_pipeline.models import TrackedApplication
from app.application_pipeline.schemas import ApplicationStatus
from app.career_intelligence.models import CareerRecommendation
from app.career_intelligence.schemas import (
    RecommendationType,
    RecommendationStatus,
    ActionPriority,
    ActionItemResponse,
    TodayActionQueueResponse,
    DashboardIntelligenceResponse,
    ApplicationHealthItem,
    ApplicationHealthListResponse,
    DailyBriefingResponse,
    WeeklyBriefingResponse,
    RefreshResponse,
)
from app.career_intelligence.errors import CareerIntelligenceErrorCode, CareerIntelligenceException
from app.career_intelligence.repository import CareerIntelligenceRepository
from app.career_intelligence.recommendation_engine import RecommendationEngine
from app.career_intelligence.briefing_engine import CareerBriefingEngine
from app.career_intelligence.priority_engine import ApplicationPriorityEngine
from app.career_intelligence.health_engine import ApplicationHealthEngine

logger = logging.getLogger("friday.career_intelligence.service")


class CareerIntelligenceService:
    """
    Core service orchestrating career intelligence evaluations, recommendation lifecycle,
    health assessments, and briefings.
    """

    @classmethod
    def _get_profile_id(cls, db: Session) -> Optional[int]:
        profile = db.query(UserProfile).first()
        return profile.id if profile else None

    @classmethod
    def refresh_recommendations(
        cls,
        db: Session,
        now: Optional[datetime] = None
    ) -> RefreshResponse:
        now = now or datetime.now(timezone.utc)
        profile_id = cls._get_profile_id(db)

        candidates = RecommendationEngine.evaluate_candidates(db, now=now)
        valid_keys = {c.key for c in candidates}

        created_count = 0
        updated_count = 0

        for candidate in candidates:
            rec, is_created = CareerIntelligenceRepository.create_or_update_recommendation(
                db=db,
                candidate_item=candidate,
                profile_id=profile_id,
                now=now
            )
            if is_created:
                created_count += 1
            else:
                updated_count += 1

        expired_count = CareerIntelligenceRepository.expire_invalid_recommendations(
            db=db,
            valid_keys=valid_keys,
            now=now
        )

        active_recs = CareerIntelligenceRepository.list_recommendations(
            db=db,
            status=RecommendationStatus.ACTIVE
        )

        return RefreshResponse(
            success=True,
            created_count=created_count,
            updated_count=updated_count,
            expired_count=expired_count,
            active_count=len(active_recs)
        )

    @classmethod
    def get_today_actions(
        cls,
        db: Session,
        now: Optional[datetime] = None
    ) -> TodayActionQueueResponse:
        now = now or datetime.now(timezone.utc)
        cls.refresh_recommendations(db, now=now)

        active_recs = CareerIntelligenceRepository.list_recommendations(
            db=db,
            status=RecommendationStatus.ACTIVE
        )

        actions = [r.to_schema() for r in active_recs]
        urgent_count = sum(1 for a in actions if a.priority == ActionPriority.URGENT)
        high_count = sum(1 for a in actions if a.priority == ActionPriority.HIGH)

        if len(actions) == 0:
            summary = "No pending actions for today. Your pipeline is up to date."
        elif urgent_count > 0:
            summary = f"You have {urgent_count} urgent action(s) and {high_count} high-priority action(s) today."
        else:
            summary = f"You have {len(actions)} active recommendation(s) to advance your job search."

        return TodayActionQueueResponse(
            success=True,
            date=now.strftime("%Y-%m-%d"),
            summary=summary,
            action_count=len(actions),
            urgent_count=urgent_count,
            high_priority_count=high_count,
            actions=actions,
        )

    @classmethod
    def get_next_actions(
        cls,
        db: Session,
        priority: Optional[ActionPriority] = None,
        recommendation_type: Optional[RecommendationType] = None,
        application_id: Optional[int] = None,
        opportunity_id: Optional[int] = None,
        status: Optional[RecommendationStatus] = RecommendationStatus.ACTIVE,
    ) -> List[ActionItemResponse]:
        recs = CareerIntelligenceRepository.list_recommendations(
            db=db,
            priority=priority,
            recommendation_type=recommendation_type,
            application_id=application_id,
            opportunity_id=opportunity_id,
            status=status
        )
        return [r.to_schema() for r in recs]

    @classmethod
    def get_dashboard(
        cls,
        db: Session,
        now: Optional[datetime] = None
    ) -> DashboardIntelligenceResponse:
        now = now or datetime.now(timezone.utc)
        cls.refresh_recommendations(db, now=now)
        return CareerIntelligenceRepository.get_dashboard_metrics(db, now=now)

    @classmethod
    def get_application_health(
        cls,
        db: Session,
        application_id: Optional[int] = None,
        now: Optional[datetime] = None
    ) -> Any:
        now = now or datetime.now(timezone.utc)

        if application_id is not None:
            app = db.query(TrackedApplication).filter(TrackedApplication.id == application_id).first()
            if not app:
                raise CareerIntelligenceException(
                    code=CareerIntelligenceErrorCode.APPLICATION_NOT_FOUND,
                    message=f"Application with ID {application_id} not found.",
                    application_id=application_id
                )

            prio_res = ApplicationPriorityEngine.calculate_priority_score(app, now=now)
            health_res = ApplicationHealthEngine.evaluate_health(app, now=now)

            return ApplicationHealthItem(
                application_id=app.id,
                company=app.company,
                role=app.role,
                status=app.status,
                health=health_res.health,
                health_score=health_res.score,
                priority_score=prio_res.total_score,
                reasons=health_res.reasons,
                recommended_action=health_res.recommended_action,
                last_status_update=app.last_status_update,
                next_follow_up_date=app.next_follow_up_date,
            )

        apps = (
            db.query(TrackedApplication)
            .filter(TrackedApplication.status.notin_([ApplicationStatus.CLOSED.value, ApplicationStatus.WITHDRAWN.value]))
            .all()
        )

        items: List[ApplicationHealthItem] = []
        for app in apps:
            prio_res = ApplicationPriorityEngine.calculate_priority_score(app, now=now)
            health_res = ApplicationHealthEngine.evaluate_health(app, now=now)

            items.append(
                ApplicationHealthItem(
                    application_id=app.id,
                    company=app.company,
                    role=app.role,
                    status=app.status,
                    health=health_res.health,
                    health_score=health_res.score,
                    priority_score=prio_res.total_score,
                    reasons=health_res.reasons,
                    recommended_action=health_res.recommended_action,
                    last_status_update=app.last_status_update,
                    next_follow_up_date=app.next_follow_up_date,
                )
            )

        items.sort(key=lambda x: x.priority_score, reverse=True)
        return ApplicationHealthListResponse(total=len(items), items=items)

    @classmethod
    def get_daily_briefing(
        cls,
        db: Session,
        now: Optional[datetime] = None
    ) -> DailyBriefingResponse:
        now = now or datetime.now(timezone.utc)
        today_queue = cls.get_today_actions(db, now=now)
        return CareerBriefingEngine.generate_daily_briefing(
            db=db,
            active_actions=today_queue.actions,
            now=now
        )

    @classmethod
    def get_weekly_briefing(
        cls,
        db: Session,
        now: Optional[datetime] = None
    ) -> WeeklyBriefingResponse:
        now = now or datetime.now(timezone.utc)
        return CareerBriefingEngine.generate_weekly_briefing(db=db, now=now)

    @classmethod
    def dismiss_recommendation(
        cls,
        recommendation_id: int,
        db: Session
    ) -> ActionItemResponse:
        rec = CareerIntelligenceRepository.dismiss_recommendation(db, recommendation_id)
        return rec.to_schema()

    @classmethod
    def complete_recommendation(
        cls,
        recommendation_id: int,
        db: Session
    ) -> ActionItemResponse:
        rec = CareerIntelligenceRepository.complete_recommendation(db, recommendation_id)
        return rec.to_schema()


default_career_intelligence_service = CareerIntelligenceService()

