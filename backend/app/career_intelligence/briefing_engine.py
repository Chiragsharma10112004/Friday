from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.application_pipeline.models import (
    TrackedApplication,
    ApplicationTimelineEvent,
    ApplicationInterview,
    ApplicationStatusHistory,
)
from app.application_pipeline.schemas import ApplicationStatus, ReferralStatus, FollowUpStatus
from app.job_discovery.models import DiscoveredOpportunity
from app.career_intelligence.schemas import (
    DailyBriefingResponse,
    WeeklyBriefingResponse,
    HealthCategory,
    ActionItemResponse,
)
from app.career_intelligence.priority_engine import ApplicationPriorityEngine
from app.career_intelligence.health_engine import ApplicationHealthEngine
from app.career_intelligence.models import CareerRecommendation


class CareerBriefingEngine:
    """
    Deterministic daily and weekly career briefing generator for personal career intelligence.
    """

    @classmethod
    def generate_daily_briefing(
        cls,
        db: Session,
        active_actions: List[ActionItemResponse],
        now: Optional[datetime] = None
    ) -> DailyBriefingResponse:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        date_str = now.strftime("%Y-%m-%d")

        # Query active applications
        active_apps = (
            db.query(TrackedApplication)
            .filter(TrackedApplication.status.notin_([ApplicationStatus.CLOSED.value, ApplicationStatus.WITHDRAWN.value]))
            .all()
        )

        overdue_fu = 0
        due_today = 0
        upcoming_interviews = 0
        pending_referrals = 0
        stale_apps = 0

        top_priority_apps: List[Dict[str, Any]] = []

        for app in active_apps:
            prio_res = ApplicationPriorityEngine.calculate_priority_score(app, now=now)
            health_res = ApplicationHealthEngine.evaluate_health(app, now=now)

            if app.follow_up_status == FollowUpStatus.OVERDUE.value:
                overdue_fu += 1
            elif app.follow_up_status == FollowUpStatus.DUE.value:
                due_today += 1

            if app.interview_date:
                int_date = app.interview_date
                if int_date.tzinfo is None:
                    int_date = int_date.replace(tzinfo=timezone.utc)
                else:
                    int_date = int_date.astimezone(timezone.utc)
                time_diff = (int_date - now).total_seconds()
                if 0 < time_diff <= 7 * 86400:
                    upcoming_interviews += 1

            if app.referral_status in (ReferralStatus.REQUESTED.value, ReferralStatus.REFERRAL_PENDING.value):
                pending_referrals += 1

            if health_res.health == HealthCategory.STALE:
                stale_apps += 1

            top_priority_apps.append({
                "id": app.id,
                "company": app.company,
                "role": app.role,
                "status": app.status,
                "priority": app.priority,
                "match_score": app.match_score,
                "priority_score": prio_res.total_score,
                "health": health_res.health.value,
                "recommended_action": health_res.recommended_action,
            })

        top_priority_apps.sort(key=lambda x: x["priority_score"], reverse=True)
        top_priority_apps = top_priority_apps[:5]

        # Top Opportunities from Phase 5
        top_opps_raw = (
            db.query(DiscoveredOpportunity)
            .filter(
                DiscoveredOpportunity.match_score >= 80,
                DiscoveredOpportunity.status.notin_(["ARCHIVED", "REJECTED", "APPLIED"])
            )
            .order_by(desc(DiscoveredOpportunity.match_score))
            .limit(5)
            .all()
        )
        top_opportunities = [
            {
                "id": o.id,
                "company": o.company,
                "title": o.title,
                "match_score": o.match_score,
                "provider": o.provider,
                "location": o.location,
            }
            for o in top_opps_raw
        ]

        total_actions = len(active_actions)
        urgent_count = sum(1 for a in active_actions if a.priority == "URGENT")
        high_count = sum(1 for a in active_actions if a.priority == "HIGH")

        # Deterministic summary
        if total_actions == 0:
            summary = "Your career pipeline is in good shape. No urgent actions required today."
        elif urgent_count > 0:
            summary = f"You have {urgent_count} urgent action(s) and {high_count} high-priority item(s) requiring attention today."
        else:
            summary = f"You have {total_actions} active recommendation(s) across your applications."

        return DailyBriefingResponse(
            date=date_str,
            summary=summary,
            applications_requiring_action=total_actions,
            overdue_follow_ups=overdue_fu,
            due_today=due_today,
            upcoming_interviews=upcoming_interviews,
            pending_referrals=pending_referrals,
            stale_applications=stale_apps,
            top_priority_applications=top_priority_apps,
            top_opportunities=top_opportunities,
            recommended_next_actions=active_actions[:5],
        )

    @classmethod
    def generate_weekly_briefing(
        cls,
        db: Session,
        now: Optional[datetime] = None
    ) -> WeeklyBriefingResponse:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        one_week_ago = now - timedelta(days=7)

        total_apps = db.query(func.count(TrackedApplication.id)).scalar() or 0

        created_this_week = (
            db.query(func.count(TrackedApplication.id))
            .filter(TrackedApplication.created_at >= one_week_ago)
            .scalar() or 0
        )

        applied_this_week = (
            db.query(func.count(TrackedApplication.id))
            .filter(
                TrackedApplication.date_applied >= one_week_ago,
                TrackedApplication.status == ApplicationStatus.APPLIED.value
            )
            .scalar() or 0
        )

        interviewing_count = (
            db.query(func.count(TrackedApplication.id))
            .filter(TrackedApplication.status == ApplicationStatus.INTERVIEWING.value)
            .scalar() or 0
        )

        offers_count = (
            db.query(func.count(TrackedApplication.id))
            .filter(TrackedApplication.status == ApplicationStatus.OFFER.value)
            .scalar() or 0
        )

        rejections_count = (
            db.query(func.count(TrackedApplication.id))
            .filter(TrackedApplication.status == ApplicationStatus.REJECTED.value)
            .scalar() or 0
        )

        withdrawals_count = (
            db.query(func.count(TrackedApplication.id))
            .filter(TrackedApplication.status == ApplicationStatus.WITHDRAWN.value)
            .scalar() or 0
        )

        follow_ups_completed = (
            db.query(func.count(TrackedApplication.id))
            .filter(TrackedApplication.follow_up_status == FollowUpStatus.COMPLETED.value)
            .scalar() or 0
        )

        overdue_follow_ups = (
            db.query(func.count(TrackedApplication.id))
            .filter(TrackedApplication.follow_up_status == FollowUpStatus.OVERDUE.value)
            .scalar() or 0
        )

        avg_score = db.query(func.avg(TrackedApplication.match_score)).filter(TrackedApplication.match_score.isnot(None)).scalar()
        avg_score_val = round(float(avg_score), 2) if avg_score is not None else None

        # Distributions
        status_raw = db.query(TrackedApplication.status, func.count(TrackedApplication.id)).group_by(TrackedApplication.status).all()
        status_dist = {s: c for s, c in status_raw}

        prio_raw = db.query(TrackedApplication.priority, func.count(TrackedApplication.id)).group_by(TrackedApplication.priority).all()
        prio_dist = {p: c for p, c in prio_raw}

        ref_raw = db.query(TrackedApplication.referral_status, func.count(TrackedApplication.id)).group_by(TrackedApplication.referral_status).all()
        ref_dist = {r: c for r, c in ref_raw}

        comp_raw = (
            db.query(TrackedApplication.company, func.count(TrackedApplication.id))
            .group_by(TrackedApplication.company)
            .order_by(desc(func.count(TrackedApplication.id)))
            .limit(5)
            .all()
        )
        top_companies = {comp: count for comp, count in comp_raw}

        # Recommended focus items
        focus: List[str] = []
        if overdue_follow_ups > 0:
            focus.append(f"Clear {overdue_follow_ups} overdue recruiter follow-up(s).")
        if interviewing_count > 0:
            focus.append(f"Prepare in-depth system design & technical walkthroughs for {interviewing_count} active interview pipeline(s).")
        if applied_this_week < 3:
            focus.append("Increase outreach velocity by targeting >= 80% match score opportunities.")
        else:
            focus.append("Maintain high application quality and monitor interview responses.")

        return WeeklyBriefingResponse(
            date=now.strftime("%Y-%m-%d"),
            total_applications=total_apps,
            applications_created_this_week=created_this_week,
            applications_applied_this_week=applied_this_week,
            applications_currently_interviewing=interviewing_count,
            new_offers=offers_count,
            rejections=rejections_count,
            withdrawals=withdrawals_count,
            follow_ups_completed=follow_ups_completed,
            overdue_follow_ups=overdue_follow_ups,
            average_match_score=avg_score_val,
            top_companies=top_companies,
            status_distribution=status_dist,
            priority_distribution=prio_dist,
            referral_distribution=ref_dist,
            recommended_focus_next_week=focus,
        )
