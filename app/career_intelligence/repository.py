import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Set, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

from app.career_intelligence.models import CareerRecommendation
from app.career_intelligence.schemas import (
    RecommendationType,
    RecommendationStatus,
    ActionPriority,
    DashboardIntelligenceResponse,
    HealthCategory,
)
from app.career_intelligence.errors import CareerIntelligenceErrorCode, CareerIntelligenceException
from app.application_pipeline.models import TrackedApplication
from app.application_pipeline.schemas import ApplicationStatus, FollowUpStatus, ReferralStatus
from app.career_intelligence.priority_engine import ApplicationPriorityEngine
from app.career_intelligence.health_engine import ApplicationHealthEngine


class CareerIntelligenceRepository:
    """
    SQLAlchemy repository for CareerRecommendation entities and career intelligence aggregations.
    """

    @classmethod
    def find_active_recommendation(
        cls,
        db: Session,
        recommendation_type: str,
        application_id: Optional[int] = None,
        opportunity_id: Optional[int] = None,
    ) -> Optional[CareerRecommendation]:
        query = db.query(CareerRecommendation).filter(
            CareerRecommendation.recommendation_type == recommendation_type,
            CareerRecommendation.status == RecommendationStatus.ACTIVE.value,
        )
        if application_id is not None:
            query = query.filter(CareerRecommendation.application_id == application_id)
        else:
            query = query.filter(CareerRecommendation.application_id.is_(None))

        if opportunity_id is not None:
            query = query.filter(CareerRecommendation.opportunity_id == opportunity_id)
        else:
            query = query.filter(CareerRecommendation.opportunity_id.is_(None))

        return query.first()

    @classmethod
    def get_recommendation(
        cls,
        db: Session,
        recommendation_id: int
    ) -> CareerRecommendation:
        rec = db.query(CareerRecommendation).filter(CareerRecommendation.id == recommendation_id).first()
        if not rec:
            raise CareerIntelligenceException(
                code=CareerIntelligenceErrorCode.RECOMMENDATION_NOT_FOUND,
                message=f"Recommendation with ID {recommendation_id} not found.",
                recommendation_id=recommendation_id
            )
        return rec

    @classmethod
    def list_recommendations(
        cls,
        db: Session,
        priority: Optional[ActionPriority] = None,
        recommendation_type: Optional[RecommendationType] = None,
        application_id: Optional[int] = None,
        opportunity_id: Optional[int] = None,
        status: Optional[RecommendationStatus] = RecommendationStatus.ACTIVE,
    ) -> List[CareerRecommendation]:
        query = db.query(CareerRecommendation)

        if status:
            query = query.filter(CareerRecommendation.status == status.value)
        if priority:
            query = query.filter(CareerRecommendation.priority == priority.value)
        if recommendation_type:
            query = query.filter(CareerRecommendation.recommendation_type == recommendation_type.value)
        if application_id is not None:
            query = query.filter(CareerRecommendation.application_id == application_id)
        if opportunity_id is not None:
            query = query.filter(CareerRecommendation.opportunity_id == opportunity_id)

        recs = query.all()

        prio_weight = {
            ActionPriority.URGENT.value: 4,
            ActionPriority.HIGH.value: 3,
            ActionPriority.MEDIUM.value: 2,
            ActionPriority.LOW.value: 1,
        }

        recs.sort(
            key=lambda r: (
                prio_weight.get(r.priority, 0),
                r.score if r.score is not None else 0,
                r.created_at or datetime.min.replace(tzinfo=timezone.utc)
            ),
            reverse=True
        )
        return recs

    @classmethod
    def create_or_update_recommendation(
        cls,
        db: Session,
        candidate_item: Any,
        profile_id: Optional[int] = None,
        now: Optional[datetime] = None
    ) -> Tuple[CareerRecommendation, bool]:
        now = now or datetime.now(timezone.utc)
        rec_type_val = candidate_item.recommendation_type.value if hasattr(candidate_item.recommendation_type, "value") else str(candidate_item.recommendation_type)
        prio_val = candidate_item.priority.value if hasattr(candidate_item.priority, "value") else str(candidate_item.priority)
        meta_str = json.dumps(candidate_item.metadata or {}, default=str)

        # Check for existing ACTIVE recommendation
        existing = cls.find_active_recommendation(
            db=db,
            recommendation_type=rec_type_val,
            application_id=candidate_item.application_id,
            opportunity_id=candidate_item.opportunity_id
        )

        if existing:
            existing.priority = prio_val
            existing.title = candidate_item.title
            existing.description = candidate_item.description
            existing.reason = candidate_item.reason
            existing.recommended_action = candidate_item.recommended_action
            existing.score = candidate_item.score
            existing.metadata_json = meta_str
            existing.updated_at = now
            db.commit()
            db.refresh(existing)
            return existing, False

        # Check if recently dismissed with cooldown (7 days)
        seven_days_ago = now - timedelta(days=7)
        dismissed = (
            db.query(CareerRecommendation)
            .filter(
                CareerRecommendation.recommendation_type == rec_type_val,
                CareerRecommendation.application_id == candidate_item.application_id,
                CareerRecommendation.opportunity_id == candidate_item.opportunity_id,
                CareerRecommendation.status == RecommendationStatus.DISMISSED.value,
                CareerRecommendation.dismissed_at >= seven_days_ago
            )
            .first()
        )
        if dismissed:
            return dismissed, False

        # Create new recommendation
        new_rec = CareerRecommendation(
            profile_id=profile_id,
            application_id=candidate_item.application_id,
            opportunity_id=candidate_item.opportunity_id,
            recommendation_type=rec_type_val,
            priority=prio_val,
            title=candidate_item.title,
            description=candidate_item.description,
            reason=candidate_item.reason,
            recommended_action=candidate_item.recommended_action,
            score=candidate_item.score,
            status=RecommendationStatus.ACTIVE.value,
            metadata_json=meta_str,
            created_at=now,
            updated_at=now,
        )
        db.add(new_rec)
        db.commit()
        db.refresh(new_rec)
        return new_rec, True

    @classmethod
    def dismiss_recommendation(
        cls,
        db: Session,
        recommendation_id: int
    ) -> CareerRecommendation:
        rec = cls.get_recommendation(db, recommendation_id)
        if rec.status != RecommendationStatus.ACTIVE.value:
            raise CareerIntelligenceException(
                code=CareerIntelligenceErrorCode.INVALID_RECOMMENDATION_STATE,
                message=f"Only ACTIVE recommendations can be dismissed. Current status: '{rec.status}'.",
                recommendation_id=recommendation_id
            )

        now = datetime.now(timezone.utc)
        rec.status = RecommendationStatus.DISMISSED.value
        rec.dismissed_at = now
        rec.updated_at = now
        db.commit()
        db.refresh(rec)
        return rec

    @classmethod
    def complete_recommendation(
        cls,
        db: Session,
        recommendation_id: int
    ) -> CareerRecommendation:
        rec = cls.get_recommendation(db, recommendation_id)
        if rec.status != RecommendationStatus.ACTIVE.value:
            raise CareerIntelligenceException(
                code=CareerIntelligenceErrorCode.INVALID_RECOMMENDATION_STATE,
                message=f"Only ACTIVE recommendations can be completed. Current status: '{rec.status}'.",
                recommendation_id=recommendation_id
            )

        now = datetime.now(timezone.utc)
        rec.status = RecommendationStatus.COMPLETED.value
        rec.completed_at = now
        rec.updated_at = now
        db.commit()
        db.refresh(rec)
        return rec

    @classmethod
    def expire_invalid_recommendations(
        cls,
        db: Session,
        valid_keys: Set[Tuple[str, Optional[int], Optional[int]]],
        now: Optional[datetime] = None
    ) -> int:
        now = now or datetime.now(timezone.utc)
        active_recs = db.query(CareerRecommendation).filter(CareerRecommendation.status == RecommendationStatus.ACTIVE.value).all()
        expired_count = 0

        for r in active_recs:
            key = (r.recommendation_type, r.application_id, r.opportunity_id)
            if key not in valid_keys:
                r.status = RecommendationStatus.EXPIRED.value
                r.updated_at = now
                expired_count += 1

        if expired_count > 0:
            db.commit()

        return expired_count

    @classmethod
    def get_dashboard_metrics(
        cls,
        db: Session,
        now: Optional[datetime] = None
    ) -> DashboardIntelligenceResponse:
        now = now or datetime.now(timezone.utc)

        active_apps = (
            db.query(TrackedApplication)
            .filter(TrackedApplication.status.notin_([ApplicationStatus.CLOSED.value, ApplicationStatus.WITHDRAWN.value]))
            .all()
        )

        healthy_count = 0
        attention_count = 0
        stale_count = 0
        critical_count = 0
        health_scores: List[int] = []

        overdue_fu = 0
        upcoming_ints = 0
        pending_refs = 0

        top_priority_list: List[Dict[str, Any]] = []

        for app in active_apps:
            prio_res = ApplicationPriorityEngine.calculate_priority_score(app, now=now)
            health_res = ApplicationHealthEngine.evaluate_health(app, now=now)

            health_scores.append(health_res.score)

            if health_res.health in (HealthCategory.EXCELLENT, HealthCategory.HEALTHY):
                healthy_count += 1
            elif health_res.health == HealthCategory.ATTENTION_NEEDED:
                attention_count += 1
            elif health_res.health == HealthCategory.STALE:
                stale_count += 1
            elif health_res.health == HealthCategory.CRITICAL:
                critical_count += 1

            if app.follow_up_status == FollowUpStatus.OVERDUE.value:
                overdue_fu += 1

            if app.interview_date:
                int_date = app.interview_date
                if int_date.tzinfo is None:
                    int_date = int_date.replace(tzinfo=timezone.utc)
                else:
                    int_date = int_date.astimezone(timezone.utc)
                if 0 < (int_date - now).total_seconds() <= 7 * 86400:
                    upcoming_ints += 1

            if app.referral_status in (ReferralStatus.REQUESTED.value, ReferralStatus.REFERRAL_PENDING.value):
                pending_refs += 1

            top_priority_list.append({
                "id": app.id,
                "company": app.company,
                "role": app.role,
                "status": app.status,
                "priority": app.priority,
                "priority_score": prio_res.total_score,
                "health": health_res.health.value,
                "health_score": health_res.score,
                "recommended_action": health_res.recommended_action,
            })

        top_priority_list.sort(key=lambda x: x["priority_score"], reverse=True)

        avg_health = round(sum(health_scores) / len(health_scores), 1) if health_scores else 100.0

        urgent_actions = (
            db.query(func.count(CareerRecommendation.id))
            .filter(
                CareerRecommendation.status == RecommendationStatus.ACTIVE.value,
                CareerRecommendation.priority == ActionPriority.URGENT.value
            )
            .scalar() or 0
        )
        high_prio_actions = (
            db.query(func.count(CareerRecommendation.id))
            .filter(
                CareerRecommendation.status == RecommendationStatus.ACTIVE.value,
                CareerRecommendation.priority == ActionPriority.HIGH.value
            )
            .scalar() or 0
        )

        return DashboardIntelligenceResponse(
            total_active_applications=len(active_apps),
            healthy_applications=healthy_count,
            attention_needed=attention_count,
            stale=stale_count,
            critical=critical_count,
            urgent_actions=urgent_actions,
            high_priority_actions=high_prio_actions,
            overdue_follow_ups=overdue_fu,
            upcoming_interviews=upcoming_ints,
            pending_referrals=pending_refs,
            average_application_health=avg_health,
            top_priority_applications=top_priority_list[:5],
        )

