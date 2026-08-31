from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.application_pipeline.models import TrackedApplication
from app.application_pipeline.schemas import ApplicationStatus, ApplicationPriority, ReferralStatus, FollowUpStatus
from app.career_intelligence.schemas import PriorityScoreResult


class ApplicationPriorityEngine:
    """
    Deterministic and explainable priority scoring engine for job applications.
    Calculates an action priority score from 0–100.
    """

    @classmethod
    def calculate_priority_score(
        cls,
        app: TrackedApplication,
        now: Optional[datetime] = None
    ) -> PriorityScoreResult:
        """
        Calculate the multi-factor priority score and explainable breakdown for an application.

        Args:
            app: The TrackedApplication entity to evaluate.
            now: Current timestamp (defaults to timezone.utc now).

        Returns:
            PriorityScoreResult with total_score (0-100), breakdown dict, and human-readable reasoning list.
        """
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        breakdown: Dict[str, int] = {
            "match_score": 0,
            "application_priority": 0,
            "referral": 0,
            "application_state": 0,
            "follow_up": 0,
            "interview": 0,
            "staleness": 0,
        }
        reasoning: List[str] = []

        # A. Match Score
        ms = app.match_score
        if ms is not None:
            try:
                ms_val = max(0, min(100, int(ms)))
            except (ValueError, TypeError):
                ms_val = 0
            if ms_val >= 90:
                breakdown["match_score"] = 30
                reasoning.append(f"Exceptional match score ({ms_val}%)")
            elif ms_val >= 80:
                breakdown["match_score"] = 25
                reasoning.append(f"Strong match score ({ms_val}%)")
            elif ms_val >= 70:
                breakdown["match_score"] = 20
                reasoning.append(f"Good match score ({ms_val}%)")
            elif ms_val >= 60:
                breakdown["match_score"] = 10
            else:
                breakdown["match_score"] = 0

        # B. Application Priority
        prio = app.priority
        if prio == ApplicationPriority.URGENT.value:
            breakdown["application_priority"] = 25
            reasoning.append("Urgent user priority")
        elif prio == ApplicationPriority.HIGH.value:
            breakdown["application_priority"] = 18
            reasoning.append("High user priority")
        elif prio == ApplicationPriority.MEDIUM.value:
            breakdown["application_priority"] = 10
        elif prio == ApplicationPriority.LOW.value:
            breakdown["application_priority"] = 5

        # C. Referral Advantage
        ref = app.referral_status
        if ref == ReferralStatus.REFERRED.value:
            breakdown["referral"] = 15
            reasoning.append("Active employee referral")
        elif ref == ReferralStatus.REFERRAL_PENDING.value:
            breakdown["referral"] = 10
            reasoning.append("Referral request pending")
        elif ref == ReferralStatus.REQUESTED.value:
            breakdown["referral"] = 8
            reasoning.append("Referral requested")
        elif ref == ReferralStatus.DECLINED.value:
            breakdown["referral"] = -2

        # D. Application State
        st = app.status
        if st == ApplicationStatus.READY_TO_APPLY.value:
            breakdown["application_state"] = 20
            reasoning.append("Ready to apply (assets prepared)")
        elif st == ApplicationStatus.ASSETS_READY.value:
            breakdown["application_state"] = 15
            reasoning.append("Assets ready for application")
        elif st == ApplicationStatus.SAVED.value:
            breakdown["application_state"] = 10
            reasoning.append("Saved opportunity awaiting preparation")
        elif st == ApplicationStatus.DISCOVERED.value:
            breakdown["application_state"] = 5

        # E. Follow-up Urgency
        fu = app.follow_up_status
        if fu == FollowUpStatus.OVERDUE.value:
            breakdown["follow_up"] = 25
            reasoning.append("Follow-up is overdue")
        elif fu == FollowUpStatus.DUE.value:
            breakdown["follow_up"] = 20
            reasoning.append("Follow-up is due today")
        elif fu == FollowUpStatus.SCHEDULED.value:
            breakdown["follow_up"] = 5

        # F. Interview Urgency
        if app.interview_date:
            int_date = app.interview_date
            if int_date.tzinfo is None:
                int_date = int_date.replace(tzinfo=timezone.utc)
            else:
                int_date = int_date.astimezone(timezone.utc)

            time_diff = int_date - now
            if time_diff.total_seconds() > 0:
                days_diff = time_diff.total_seconds() / 86400.0
                if days_diff <= 1.0:
                    breakdown["interview"] = 30
                    reasoning.append(f"Interview within 24 hours ({int_date.strftime('%Y-%m-%d %H:%M')})")
                elif days_diff <= 3.0:
                    breakdown["interview"] = 25
                    reasoning.append(f"Interview within 3 days ({int_date.strftime('%Y-%m-%d')})")
                elif days_diff <= 7.0:
                    breakdown["interview"] = 15
                    reasoning.append("Interview scheduled this week")
                else:
                    breakdown["interview"] = 5

        # G. Staleness
        if st in (ApplicationStatus.APPLIED.value, ApplicationStatus.INTERVIEWING.value):
            last_date = app.last_status_update or app.date_applied or app.created_at
            if last_date:
                if last_date.tzinfo is None:
                    last_date = last_date.replace(tzinfo=timezone.utc)
                else:
                    last_date = last_date.astimezone(timezone.utc)

                days_inactive = (now - last_date).total_seconds() / 86400.0
                if days_inactive >= 30:
                    breakdown["staleness"] = 20
                    reasoning.append(f"No update for {int(days_inactive)} days (stale)")
                elif days_inactive >= 21:
                    breakdown["staleness"] = 15
                    reasoning.append(f"No update for {int(days_inactive)} days")
                elif days_inactive >= 14:
                    breakdown["staleness"] = 10
                    reasoning.append(f"No update for {int(days_inactive)} days")

        raw_total = sum(breakdown.values())
        total_score = max(0, min(100, raw_total))

        return PriorityScoreResult(
            total_score=total_score,
            breakdown=breakdown,
            reasoning=reasoning
        )

