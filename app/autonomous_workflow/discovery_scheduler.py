import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.autonomous_workflow.models import AutonomousWorkflow
from app.autonomous_workflow.schemas import (
    WorkflowStatus,
    WorkflowPriority,
    DiscoveryRunResponse,
)
from app.autonomous_workflow.job_ranker import JobRankerEngine
from app.autonomous_workflow.repository import WorkflowRepository
from app.job_discovery.models import DiscoveredOpportunity
from app.profile.models import UserProfile

logger = logging.getLogger("friday.autonomous_workflow.discovery")


class DiscoveryScheduler:
    """
    Service abstraction for running automated job discovery cycles, ranking candidate opportunities,
    and creating queued autonomous workflows for top-tier matches.
    """

    DEFAULT_MIN_SCORE = 70

    @classmethod
    def run_discovery_cycle(
        cls,
        db: Session,
        min_score_threshold: int = DEFAULT_MIN_SCORE,
        profile_id: Optional[int] = None
    ) -> DiscoveryRunResponse:
        """
        Scans discovered opportunities, filters by score threshold, and initializes workflows.
        """
        query = db.query(DiscoveredOpportunity).filter(
            DiscoveredOpportunity.match_score >= min_score_threshold,
            DiscoveredOpportunity.status.notin_(["ARCHIVED", "REJECTED", "APPLIED"])
        )

        opportunities = query.order_by(desc(DiscoveredOpportunity.match_score)).all()

        workflows_created = 0
        workflows_queued = 0

        for opp in opportunities:
            existing_wf = WorkflowRepository.get_workflow_by_opportunity(db, opp.id)
            if existing_wf:
                continue

            ranking = JobRankerEngine.rank_job(
                match_score=opp.match_score,
                recommendation=opp.recommendation,
            )

            init_status = WorkflowStatus.QUEUED_FOR_REVIEW
            if (opp.match_score or 0) >= 85:
                init_status = WorkflowStatus.AWAITING_APPROVAL

            try:
                wf = WorkflowRepository.create_workflow(
                    db=db,
                    company=opp.company,
                    role=opp.title,
                    source_url=opp.source_url or opp.application_url,
                    source_platform=opp.provider,
                    priority=ranking.priority,
                    profile_id=profile_id,
                    opportunity_id=opp.id,
                    match_score=opp.match_score,
                    initial_status=init_status,
                    metadata={"ranking_reasons": ranking.reasons}
                )
                workflows_created += 1
                workflows_queued += 1
            except Exception as e:
                logger.warning(f"Could not auto-create workflow for opportunity {opp.id}: {e}")

        return DiscoveryRunResponse(
            success=True,
            opportunities_discovered=len(opportunities),
            workflows_created=workflows_created,
            workflows_queued=workflows_queued,
            min_score_threshold=min_score_threshold,
        )

    @classmethod
    def run_profile_discovery(
        cls,
        db: Session,
        profile_id: int,
        min_score_threshold: int = DEFAULT_MIN_SCORE
    ) -> DiscoveryRunResponse:
        return cls.run_discovery_cycle(db, min_score_threshold=min_score_threshold, profile_id=profile_id)

    @classmethod
    def run_all_active_profiles(
        cls,
        db: Session,
        min_score_threshold: int = DEFAULT_MIN_SCORE
    ) -> DiscoveryRunResponse:
        profile = db.query(UserProfile).first()
        return cls.run_discovery_cycle(db, min_score_threshold=min_score_threshold, profile_id=profile.id if profile else None)
