from datetime import datetime, timezone, timedelta
from typing import List, Optional

from app.application_pipeline.models import TrackedApplication
from app.application_pipeline.schemas import ApplicationStatus, ReferralStatus, FollowUpStatus
from app.career_intelligence.schemas import HealthCategory, ApplicationHealthResult


class ApplicationHealthEngine:
    """
    Deterministic health classification and diagnostics for job applications.
    Categories: EXCELLENT, HEALTHY, ATTENTION_NEEDED, STALE, CRITICAL
    """

    @classmethod
    def evaluate_health(
        cls,
        app: TrackedApplication,
        now: Optional[datetime] = None
    ) -> ApplicationHealthResult:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        st = app.status
        fu_status = app.follow_up_status
        ref_status = app.referral_status

        reasons: List[str] = []
        health: HealthCategory = HealthCategory.HEALTHY
        score: int = 75
        recommended_action: str = "Keep monitoring application progression."

        # Check for CRITICAL conditions
        is_critical = False
        if fu_status == FollowUpStatus.OVERDUE.value:
            is_critical = True
            reasons.append("Follow-up is overdue")
            recommended_action = "Reach out to recruiter/contact or update follow-up date."
            score = 25

        if app.interview_date:
            int_date = app.interview_date
            if int_date.tzinfo is None:
                int_date = int_date.replace(tzinfo=timezone.utc)
            else:
                int_date = int_date.astimezone(timezone.utc)

            time_to_interview = (int_date - now).total_seconds()
            if 0 < time_to_interview <= 86400:
                is_critical = True
                reasons.append("Upcoming interview in less than 24 hours")
                recommended_action = "Review company architecture, role requirements, and prepare talking points."
                score = min(score, 30)

        # Check last update staleness
        last_date = app.last_status_update or app.date_applied or app.created_at
        days_inactive = 0.0
        if last_date:
            if last_date.tzinfo is None:
                last_date = last_date.replace(tzinfo=timezone.utc)
            else:
                last_date = last_date.astimezone(timezone.utc)
            days_inactive = (now - last_date).total_seconds() / 86400.0

        if not is_critical and st in (ApplicationStatus.APPLIED.value, ApplicationStatus.INTERVIEWING.value):
            if days_inactive >= 30:
                health = HealthCategory.CRITICAL
                reasons.append(f"No update or recruiter communication for {int(days_inactive)} days")
                recommended_action = "Send polite follow-up or consider closing inactive application."
                score = 28
                is_critical = True
            elif days_inactive >= 14 and fu_status != FollowUpStatus.SCHEDULED.value:
                health = HealthCategory.STALE
                reasons.append(f"Application has been inactive for {int(days_inactive)} days without scheduled follow-up")
                recommended_action = "Schedule follow-up reminder or reach out to recruiter."
                score = 45

        if is_critical:
            health = HealthCategory.CRITICAL
            return ApplicationHealthResult(
                health=health,
                score=score,
                reasons=reasons,
                recommended_action=recommended_action
            )

        if health == HealthCategory.STALE:
            return ApplicationHealthResult(
                health=health,
                score=score,
                reasons=reasons,
                recommended_action=recommended_action
            )

        # Check ATTENTION_NEEDED conditions
        if fu_status == FollowUpStatus.DUE.value:
            health = HealthCategory.ATTENTION_NEEDED
            reasons.append("Follow-up task is due today")
            recommended_action = "Execute scheduled follow-up action today."
            score = 60
        elif st == ApplicationStatus.READY_TO_APPLY.value and days_inactive >= 3:
            health = HealthCategory.ATTENTION_NEEDED
            reasons.append(f"Application ready to submit for {int(days_inactive)} days")
            recommended_action = "Submit your application on the company portal."
            score = 65
        elif ref_status in (ReferralStatus.REQUESTED.value, ReferralStatus.REFERRAL_PENDING.value) and days_inactive >= 5:
            health = HealthCategory.ATTENTION_NEEDED
            reasons.append("Referral request pending for 5+ days")
            recommended_action = "Check in with referral contact or proceed with standard application."
            score = 62
        elif app.interview_date:
            int_date = app.interview_date
            if int_date.tzinfo is None:
                int_date = int_date.replace(tzinfo=timezone.utc)
            else:
                int_date = int_date.astimezone(timezone.utc)
            time_to_int = (int_date - now).total_seconds()
            if 0 < time_to_int <= 3 * 86400:
                health = HealthCategory.ATTENTION_NEEDED
                reasons.append("Interview coming up within 3 days")
                recommended_action = "Begin structured interview preparation."
                score = 68

        if health == HealthCategory.ATTENTION_NEEDED:
            return ApplicationHealthResult(
                health=health,
                score=score,
                reasons=reasons,
                recommended_action=recommended_action
            )

        # Check EXCELLENT conditions
        if st == ApplicationStatus.OFFER.value:
            health = HealthCategory.EXCELLENT
            reasons.append("Job offer received")
            recommended_action = "Review offer package and prepare decision or counter-offer."
            score = 98
        elif st == ApplicationStatus.APPLIED.value and ref_status == ReferralStatus.REFERRED.value and days_inactive <= 7:
            health = HealthCategory.EXCELLENT
            reasons.append("Recently applied with active employee referral")
            recommended_action = "Monitor application portal for initial interview invitation."
            score = 92
        elif st == ApplicationStatus.READY_TO_APPLY.value and (app.match_score or 0) >= 85 and days_inactive <= 2:
            health = HealthCategory.EXCELLENT
            reasons.append("High match fit application ready to submit")
            recommended_action = "Submit application to take advantage of high match alignment."
            score = 90
        else:
            health = HealthCategory.HEALTHY
            reasons.append("Application progressing normally")
            recommended_action = "Continue standard tracking."
            score = 80

        return ApplicationHealthResult(
            health=health,
            score=score,
            reasons=reasons,
            recommended_action=recommended_action
        )

