from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from sqlalchemy.orm import Session

from app.application_pipeline.models import TrackedApplication
from app.application_pipeline.schemas import ApplicationStatus, ReferralStatus, FollowUpStatus
from app.job_discovery.models import DiscoveredOpportunity
from app.career_intelligence.models import CareerRecommendation
from app.career_intelligence.schemas import (
    RecommendationType,
    RecommendationStatus,
    ActionPriority,
    HealthCategory,
)
from app.career_intelligence.priority_engine import ApplicationPriorityEngine
from app.career_intelligence.health_engine import ApplicationHealthEngine


class RecommendationCandidate:
    def __init__(
        self,
        recommendation_type: RecommendationType,
        priority: ActionPriority,
        title: str,
        description: str,
        reason: str,
        recommended_action: str,
        score: int,
        application_id: Optional[int] = None,
        opportunity_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.recommendation_type = recommendation_type
        self.priority = priority
        self.title = title
        self.description = description
        self.reason = reason
        self.recommended_action = recommended_action
        self.score = score
        self.application_id = application_id
        self.opportunity_id = opportunity_id
        self.metadata = metadata or {}

    @property
    def key(self) -> Tuple[str, Optional[int], Optional[int]]:
        return (self.recommendation_type.value, self.application_id, self.opportunity_id)


class RecommendationEngine:
    """
    Deterministic rule engine that analyzes application pipeline and discovered opportunities
    to generate, update, and expire actionable career intelligence recommendations.
    """

    COOLDOWN_DAYS = 7

    @classmethod
    def evaluate_candidates(
        cls,
        db: Session,
        now: Optional[datetime] = None
    ) -> List[RecommendationCandidate]:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        candidates: List[RecommendationCandidate] = []

        # 1. Inspect Tracked Applications (active only)
        active_apps = (
            db.query(TrackedApplication)
            .filter(TrackedApplication.status.notin_([ApplicationStatus.CLOSED.value, ApplicationStatus.WITHDRAWN.value]))
            .all()
        )

        for app in active_apps:
            prio_res = ApplicationPriorityEngine.calculate_priority_score(app, now=now)
            health_res = ApplicationHealthEngine.evaluate_health(app, now=now)

            # Rule 1: Follow-up Overdue
            if app.follow_up_status == FollowUpStatus.OVERDUE.value:
                candidates.append(
                    RecommendationCandidate(
                        recommendation_type=RecommendationType.FOLLOW_UP_OVERDUE,
                        priority=ActionPriority.URGENT,
                        title=f"Follow-up Overdue: {app.company}",
                        description=f"Your scheduled follow-up for {app.role} at {app.company} is overdue.",
                        reason=f"Follow-up date {app.next_follow_up_date.strftime('%Y-%m-%d') if app.next_follow_up_date else ''} has passed without completion.",
                        recommended_action=f"Contact the recruiter or recruiter contact for {app.company} today.",
                        score=max(prio_res.total_score, 95),
                        application_id=app.id,
                        metadata={"company": app.company, "role": app.role, "status": app.status}
                    )
                )

            # Rule 2: Follow-up Due Today
            elif app.follow_up_status == FollowUpStatus.DUE.value:
                candidates.append(
                    RecommendationCandidate(
                        recommendation_type=RecommendationType.FOLLOW_UP_DUE,
                        priority=ActionPriority.HIGH,
                        title=f"Follow-up Due Today: {app.company}",
                        description=f"You have a follow-up scheduled today for {app.role} at {app.company}.",
                        reason="Follow-up date is today.",
                        recommended_action="Execute your planned follow-up message and update the record.",
                        score=max(prio_res.total_score, 85),
                        application_id=app.id,
                        metadata={"company": app.company, "role": app.role, "status": app.status}
                    )
                )

            # Rule 3: Upcoming Interview
            if app.interview_date:
                int_date = app.interview_date
                if int_date.tzinfo is None:
                    int_date = int_date.replace(tzinfo=timezone.utc)
                else:
                    int_date = int_date.astimezone(timezone.utc)

                time_diff = (int_date - now).total_seconds()
                if 0 < time_diff <= 86400:
                    candidates.append(
                        RecommendationCandidate(
                            recommendation_type=RecommendationType.INTERVIEW_PREPARATION,
                            priority=ActionPriority.URGENT,
                            title=f"Interview within 24h: {app.company}",
                            description=f"{app.interview_stage or 'Interview'} round scheduled for {app.role} at {app.company}.",
                            reason=f"Interview starts in {int(time_diff / 3600)} hours.",
                            recommended_action="Review key skills, project stories, and prepare questions for the interview panel.",
                            score=98,
                            application_id=app.id,
                            metadata={"interview_stage": app.interview_stage, "interview_date": int_date.isoformat()}
                        )
                    )
                elif 0 < time_diff <= 3 * 86400:
                    candidates.append(
                        RecommendationCandidate(
                            recommendation_type=RecommendationType.INTERVIEW_PREPARATION,
                            priority=ActionPriority.HIGH,
                            title=f"Interview in {int(time_diff / 86400) + 1} days: {app.company}",
                            description=f"{app.interview_stage or 'Interview'} round scheduled for {app.role} at {app.company}.",
                            reason="Interview scheduled in upcoming 3 days.",
                            recommended_action="Prepare tailored architecture walkthroughs and system design examples.",
                            score=88,
                            application_id=app.id,
                            metadata={"interview_stage": app.interview_stage, "interview_date": int_date.isoformat()}
                        )
                    )

            # Rule 4: Ready to Apply with high match score
            if app.status == ApplicationStatus.READY_TO_APPLY.value and (app.match_score or 0) >= 80:
                candidates.append(
                    RecommendationCandidate(
                        recommendation_type=RecommendationType.APPLY_NOW,
                        priority=ActionPriority.HIGH,
                        title=f"Apply Now: {app.role} at {app.company}",
                        description=f"Your tailored application package is ready with a high match score ({app.match_score}%).",
                        reason="Assets are generated and application form is ready for manual submission.",
                        recommended_action="Open the job application portal and complete submission.",
                        score=max(prio_res.total_score, 88),
                        application_id=app.id,
                        metadata={"match_score": app.match_score}
                    )
                )

            # Rule 5: Saved or Discovered with high match but no assets
            if app.status in (ApplicationStatus.SAVED.value, ApplicationStatus.DISCOVERED.value) and (app.match_score or 0) >= 70 and not app.date_assets_generated:
                candidates.append(
                    RecommendationCandidate(
                        recommendation_type=RecommendationType.GENERATE_ASSETS,
                        priority=ActionPriority.MEDIUM,
                        title=f"Generate Tailored Assets: {app.company}",
                        description=f"Generate tailored resume and cover letter for {app.role} at {app.company}.",
                        reason=f"Strong fit score ({app.match_score}%) warrants customized application assets.",
                        recommended_action="Run Phase 3 asset generation to produce resume and outreach materials.",
                        score=prio_res.total_score,
                        application_id=app.id,
                        metadata={"match_score": app.match_score}
                    )
                )

            # Rule 6: High match score, not yet applied, no referral requested
            if (
                app.status in (ApplicationStatus.DISCOVERED.value, ApplicationStatus.SAVED.value, ApplicationStatus.ASSETS_READY.value)
                and (app.match_score or 0) >= 75
                and app.referral_status == ReferralStatus.NOT_REQUESTED.value
            ):
                candidates.append(
                    RecommendationCandidate(
                        recommendation_type=RecommendationType.REQUEST_REFERRAL,
                        priority=ActionPriority.MEDIUM,
                        title=f"Request Referral: {app.company}",
                        description=f"Identify connections or alumni at {app.company} for {app.role}.",
                        reason="Employee referrals increase interview conversion rates significantly.",
                        recommended_action="Reach out to professional network contacts at the company before submitting.",
                        score=prio_res.total_score,
                        application_id=app.id,
                        metadata={"match_score": app.match_score}
                    )
                )

            # Rule 7: Stale Application
            if health_res.health == HealthCategory.STALE:
                candidates.append(
                    RecommendationCandidate(
                        recommendation_type=RecommendationType.STALE_APPLICATION,
                        priority=ActionPriority.MEDIUM,
                        title=f"Stale Application Review: {app.company}",
                        description=f"Application for {app.role} at {app.company} has had no activity.",
                        reason=" ".join(health_res.reasons),
                        recommended_action=health_res.recommended_action,
                        score=prio_res.total_score,
                        application_id=app.id,
                        metadata={"health_score": health_res.score}
                    )
                )

            # Rule 8: Attention Needed
            elif health_res.health == HealthCategory.ATTENTION_NEEDED and app.follow_up_status != FollowUpStatus.DUE.value:
                candidates.append(
                    RecommendationCandidate(
                        recommendation_type=RecommendationType.APPLICATION_STATUS_REVIEW,
                        priority=ActionPriority.MEDIUM,
                        title=f"Status Review Needed: {app.company}",
                        description=f"Check progress on {app.role} at {app.company}.",
                        reason=" ".join(health_res.reasons),
                        recommended_action=health_res.recommended_action,
                        score=prio_res.total_score,
                        application_id=app.id,
                        metadata={"health_score": health_res.score}
                    )
                )

        # 2. Inspect Phase 5 Discovered Opportunities
        tracked_opp_ids = {a.opportunity_id for a in active_apps if a.opportunity_id is not None}
        high_match_opps = (
            db.query(DiscoveredOpportunity)
            .filter(
                DiscoveredOpportunity.match_score >= 80,
                DiscoveredOpportunity.status.notin_(["ARCHIVED", "REJECTED", "APPLIED"])
            )
            .all()
        )

        for opp in high_match_opps:
            if opp.id not in tracked_opp_ids:
                candidates.append(
                    RecommendationCandidate(
                        recommendation_type=RecommendationType.PRIORITY_APPLICATION,
                        priority=ActionPriority.HIGH,
                        title=f"Top Opportunity: {opp.title} at {opp.company}",
                        description=f"Discovered a high-match ({opp.match_score}%) role at {opp.company}.",
                        reason=f"Candidate profile scored {opp.match_score}% fit for this discovered opening.",
                        recommended_action="Convert this opportunity into a tracked application and prepare assets.",
                        score=85,
                        opportunity_id=opp.id,
                        metadata={"company": opp.company, "title": opp.title, "match_score": opp.match_score}
                    )
                )

        return candidates

