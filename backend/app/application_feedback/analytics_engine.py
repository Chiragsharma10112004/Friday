from collections import defaultdict
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.application_pipeline.models import TrackedApplication
from app.application_pipeline.schemas import ApplicationStatus
from app.job_discovery.models import DiscoveredOpportunity
from app.application_feedback.models import (
    ApplicationOutcomeFeedback,
    ApplicationFieldIssue,
    FeedbackLearningSignal,
)
from app.application_feedback.schemas import (
    AnalyticsSummaryResponse,
    ConversionFunnelResponse,
    PlatformPerformanceResponse,
    OutcomeType,
)
from app.application_feedback.repository import FeedbackRepository


class AnalyticsEngine:
    """
    Computes pipeline conversion funnels, stage drop-offs, platform success rates,
    and correlation between match scores and interview success.
    """

    @classmethod
    def calculate_funnel(cls, db: Session) -> ConversionFunnelResponse:
        total_discovered = db.query(DiscoveredOpportunity).count()
        apps = db.query(TrackedApplication).all()
        outcomes = FeedbackRepository.list_outcome_feedback(db)

        saved = len(apps)
        applied = sum(1 for a in apps if a.date_applied is not None or a.status not in (ApplicationStatus.DISCOVERED.value, ApplicationStatus.SAVED.value))

        screen = 0
        technical = 0
        final_round = 0
        offers = 0
        accepted = 0
        rejected = 0

        for a in apps:
            if a.status in (ApplicationStatus.INTERVIEWING.value, ApplicationStatus.OFFER.value):
                screen += 1
            if a.status == ApplicationStatus.OFFER.value:
                offers += 1
            if a.status == ApplicationStatus.REJECTED.value:
                rejected += 1

        for o in outcomes:
            if o.outcome_type in (OutcomeType.REJECTED_AFTER_TECHNICAL.value, OutcomeType.REJECTED_AFTER_FINAL.value, OutcomeType.OFFER_RECEIVED.value):
                technical += 1
            if o.outcome_type in (OutcomeType.REJECTED_AFTER_FINAL.value, OutcomeType.OFFER_RECEIVED.value):
                final_round += 1

        # Calculate conversion rates
        conv_rates: Dict[str, float] = {}
        conv_rates["discovered_to_applied"] = round((applied / total_discovered * 100.0) if total_discovered > 0 else 0.0, 2)
        conv_rates["applied_to_interview"] = round((screen / applied * 100.0) if applied > 0 else 0.0, 2)
        conv_rates["interview_to_offer"] = round((offers / screen * 100.0) if screen > 0 else 0.0, 2)
        conv_rates["applied_to_offer"] = round((offers / applied * 100.0) if applied > 0 else 0.0, 2)

        return ConversionFunnelResponse(
            discovered=total_discovered,
            saved=saved,
            applied=applied,
            screen=screen,
            technical=technical,
            final_round=final_round,
            offers=offers,
            accepted=accepted,
            rejected=rejected,
            conversion_rates=conv_rates,
        )

    @classmethod
    def calculate_platform_metrics(cls, db: Session) -> List[PlatformPerformanceResponse]:
        apps = db.query(TrackedApplication).all()
        outcomes = FeedbackRepository.list_outcome_feedback(db)
        issues = FeedbackRepository.list_field_issues(db)

        platform_apps = defaultdict(list)
        for a in apps:
            plat = (a.source_platform or "generic").lower()
            platform_apps[plat].append(a)

        issue_counts = defaultdict(int)
        for i in issues:
            plat = (i.platform or "generic").lower()
            issue_counts[plat] += 1

        results: List[PlatformPerformanceResponse] = []
        for plat, p_apps in platform_apps.items():
            total = len(p_apps)
            if total == 0:
                continue

            screens = 0
            offers = 0
            rejections = 0

            for a in p_apps:
                if a.status in (ApplicationStatus.INTERVIEWING.value, ApplicationStatus.OFFER.value):
                    screens += 1
                if a.status == ApplicationStatus.OFFER.value:
                    offers += 1
                if a.status == ApplicationStatus.REJECTED.value:
                    rejections += 1

            results.append(
                PlatformPerformanceResponse(
                    platform=plat,
                    total_applications=total,
                    screen_rate=round((screens / total) * 100.0, 2),
                    offer_rate=round((offers / total) * 100.0, 2),
                    rejection_rate=round((rejections / total) * 100.0, 2),
                    field_issue_count=issue_counts[plat],
                )
            )

        return results

    @classmethod
    def calculate_summary(cls, db: Session) -> AnalyticsSummaryResponse:
        apps = db.query(TrackedApplication).all()
        signals = FeedbackRepository.list_learning_signals(db)

        funnel = cls.calculate_funnel(db)
        platform_metrics = cls.calculate_platform_metrics(db)

        total_tracked = len(apps)
        total_applied = funnel.applied
        total_interviews = funnel.screen
        total_offers = funnel.offers
        total_rejections = funnel.rejected

        overall_conv = round((total_offers / total_applied * 100.0) if total_applied > 0 else 0.0, 2)

        # Match score correlation
        interview_scores: List[int] = []
        rejected_scores: List[int] = []

        for a in apps:
            if a.match_score is not None:
                if a.status in (ApplicationStatus.INTERVIEWING.value, ApplicationStatus.OFFER.value):
                    interview_scores.append(a.match_score)
                elif a.status == ApplicationStatus.REJECTED.value:
                    rejected_scores.append(a.match_score)

        avg_interview_score = round(sum(interview_scores) / len(interview_scores), 2) if interview_scores else 0.0
        avg_rejected_score = round(sum(rejected_scores) / len(rejected_scores), 2) if rejected_scores else 0.0

        return AnalyticsSummaryResponse(
            total_tracked=total_tracked,
            total_applied=total_applied,
            total_interviews=total_interviews,
            total_offers=total_offers,
            total_rejections=total_rejections,
            overall_conversion_rate=overall_conv,
            average_match_score_interviewed=avg_interview_score,
            average_match_score_rejected=avg_rejected_score,
            funnel=funnel,
            platform_metrics=platform_metrics,
            active_signals_count=len(signals),
        )
