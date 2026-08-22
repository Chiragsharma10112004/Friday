import json
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.job_discovery.models import DiscoveredOpportunity
from app.job_discovery.schemas import DiscoveredJob, PipelineStatus, OpportunityFilterParams
from app.job_discovery.errors import DiscoveryErrorCode, DiscoveryException
from app.job_discovery.filters import JobFilterEngine


class OpportunityRepository:
    """
    Persistence and query management for Discovered Opportunities.
    """

    ALLOWED_TRANSITIONS = {
        PipelineStatus.DISCOVERED: {PipelineStatus.SAVED, PipelineStatus.ANALYZED, PipelineStatus.REJECTED, PipelineStatus.ARCHIVED},
        PipelineStatus.SAVED: {PipelineStatus.ANALYZED, PipelineStatus.REJECTED, PipelineStatus.ARCHIVED, PipelineStatus.READY_TO_APPLY},
        PipelineStatus.ANALYZED: {PipelineStatus.ASSETS_GENERATED, PipelineStatus.READY_TO_APPLY, PipelineStatus.SAVED, PipelineStatus.REJECTED, PipelineStatus.ARCHIVED},
        PipelineStatus.ASSETS_GENERATED: {PipelineStatus.READY_TO_APPLY, PipelineStatus.SAVED, PipelineStatus.REJECTED, PipelineStatus.ARCHIVED},
        PipelineStatus.READY_TO_APPLY: {PipelineStatus.APPLIED, PipelineStatus.SAVED, PipelineStatus.REJECTED, PipelineStatus.ARCHIVED},
        PipelineStatus.APPLIED: {PipelineStatus.REJECTED, PipelineStatus.ARCHIVED},
        PipelineStatus.REJECTED: {PipelineStatus.ARCHIVED, PipelineStatus.SAVED},
        PipelineStatus.ARCHIVED: {PipelineStatus.SAVED},
    }

    @classmethod
    def validate_transition(cls, current_status: PipelineStatus, target_status: PipelineStatus):
        if current_status == target_status:
            return

        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise DiscoveryException(
                code=DiscoveryErrorCode.INVALID_STATUS_TRANSITION,
                message=f"Cannot transition opportunity from {current_status.value} to {target_status.value}."
            )

    @classmethod
    def save_opportunity(cls, db: Session, job: DiscoveredJob) -> DiscoveredOpportunity:
        existing = db.query(DiscoveredOpportunity).filter(
            DiscoveredOpportunity.source_url == job.source_url
        ).first()

        matched_json = json.dumps(job.matched_skills) if job.matched_skills else None
        missing_json = json.dumps(job.missing_skills) if job.missing_skills else None
        strengths_json = json.dumps(job.key_strengths) if job.key_strengths else None
        concerns_json = json.dumps(job.key_concerns) if job.key_concerns else None
        meta_json = json.dumps(job.metadata) if job.metadata else None

        rec_str = job.recommendation.value if job.recommendation else None
        status_str = job.status.value if job.status else PipelineStatus.DISCOVERED.value

        if existing:
            existing.company = job.company
            existing.title = job.title
            existing.location = job.location
            existing.is_remote = job.is_remote
            existing.description = job.description
            existing.employment_type = job.employment_type
            existing.match_score = job.match_score
            existing.recommendation = rec_str
            existing.ranking_explanation = job.ranking_explanation
            existing.matched_skills = matched_json
            existing.missing_skills = missing_json
            existing.key_strengths = strengths_json
            existing.key_concerns = concerns_json
            existing.extra_metadata = meta_json
            db.commit()
            db.refresh(existing)
            return existing

        new_opp = DiscoveredOpportunity(
            external_id=job.external_id,
            provider=job.provider,
            source_url=job.source_url,
            application_url=job.application_url,
            company=job.company,
            title=job.title,
            location=job.location,
            is_remote=job.is_remote,
            description=job.description,
            employment_type=job.employment_type,
            experience_level=job.experience_level,
            posted_at=job.posted_at,
            status=status_str,
            match_score=job.match_score,
            recommendation=rec_str,
            ranking_explanation=job.ranking_explanation,
            matched_skills=matched_json,
            missing_skills=missing_json,
            key_strengths=strengths_json,
            key_concerns=concerns_json,
            extra_metadata=meta_json,
        )

        db.add(new_opp)
        db.commit()
        db.refresh(new_opp)
        return new_opp

    @classmethod
    def get_opportunity(cls, db: Session, opp_id: int) -> Optional[DiscoveredOpportunity]:
        return db.query(DiscoveredOpportunity).filter(DiscoveredOpportunity.id == opp_id).first()

    @classmethod
    def list_opportunities(
        cls,
        db: Session,
        params: OpportunityFilterParams
    ) -> Tuple[List[DiscoveredOpportunity], int]:
        query = db.query(DiscoveredOpportunity)
        query = JobFilterEngine.apply_db_filters(query, params)

        total = query.count()
        offset = (params.page - 1) * params.page_size
        items = query.offset(offset).limit(params.page_size).all()

        return items, total

    @classmethod
    def update_opportunity_status(
        cls,
        db: Session,
        opp_id: int,
        target_status: PipelineStatus
    ) -> DiscoveredOpportunity:
        opp = cls.get_opportunity(db, opp_id)
        if not opp:
            raise DiscoveryException(
                code=DiscoveryErrorCode.OPPORTUNITY_NOT_FOUND,
                message=f"Opportunity with ID {opp_id} not found."
            )

        current = PipelineStatus(opp.status)
        cls.validate_transition(current, target_status)

        opp.status = target_status.value
        db.commit()
        db.refresh(opp)
        return opp

    @classmethod
    def delete_opportunity(cls, db: Session, opp_id: int) -> bool:
        opp = cls.get_opportunity(db, opp_id)
        if not opp:
            return False
        db.delete(opp)
        db.commit()
        return True
