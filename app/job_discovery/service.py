import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
import math

from app.profile.models import UserProfile
from app.job_discovery.schemas import (
    DiscoveredJob,
    JobSearchQuery,
    JobSearchResponse,
    ManualDiscoveryRequest,
    ManualDiscoveryResponse,
    OpportunityFilterParams,
    OpportunityListResponse,
    PipelineStatus,
    JobRecommendation,
)
from app.job_discovery.errors import DiscoveryErrorCode, DiscoveryException
from app.job_discovery.providers import (
    BaseJobProvider,
    GreenhouseDiscoveryProvider,
    LeverDiscoveryProvider,
    ManualUrlProvider,
)
from app.job_discovery.deduplication import JobDeduplicator
from app.job_discovery.filters import JobFilterEngine
from app.job_discovery.ranking import JobRanker
from app.job_discovery.repository import OpportunityRepository

# Reused Subsystems
from app.services.job_service import analyze_job
from app.application_assets.schemas import ApplicationAssetRequest, ApplicationAssetResponse
from app.application_assets.service import default_asset_service
from app.application_automation.schemas import InspectApplicationRequest, InspectApplicationResponse
from app.application_automation.service import default_automation_service

logger = logging.getLogger("friday.job_discovery.service")


class JobDiscoveryService:
    """
    Central orchestration service for Job Discovery, Deduplication, Ranking,
    and Opportunity Pipeline Lifecycle management.
    """

    def __init__(self):
        self.providers: Dict[str, BaseJobProvider] = {
            "greenhouse": GreenhouseDiscoveryProvider(),
            "lever": LeverDiscoveryProvider(),
            "manual": ManualUrlProvider(),
        }

    def search_and_discover(
        self,
        query: JobSearchQuery,
        db: Session
    ) -> JobSearchResponse:
        profile = db.query(UserProfile).first()
        if not profile:
            raise DiscoveryException(
                code=DiscoveryErrorCode.PROFILE_NOT_FOUND,
                message="Master candidate profile not found. Please create a profile before discovering jobs."
            )

        active_providers: List[BaseJobProvider] = []
        if query.providers:
            for p_name in query.providers:
                p_name_lower = p_name.lower().strip()
                if p_name_lower not in self.providers:
                    raise DiscoveryException(
                        code=DiscoveryErrorCode.PROVIDER_UNSUPPORTED,
                        message=f"Job provider '{p_name}' is not supported. Supported providers: {list(self.providers.keys())}"
                    )
                active_providers.append(self.providers[p_name_lower])
        else:
            active_providers = [self.providers["greenhouse"], self.providers["lever"]]

        all_discovered: List[DiscoveredJob] = []
        warnings: List[str] = []

        for prov in active_providers:
            try:
                jobs = prov.search_jobs(query)
                all_discovered.extend(jobs)
            except Exception as e:
                warnings.append(f"Provider '{prov.provider_name}' query failed: {str(e)}")

        if query.include_manual_urls:
            manual_prov = self.providers["manual"]
            manual_jobs = manual_prov.search_jobs(query)
            all_discovered.extend(manual_jobs)

        total_discovered = len(all_discovered)
        unique_jobs, dups_skipped = JobDeduplicator.deduplicate(all_discovered)
        filtered_jobs = JobFilterEngine.filter_jobs(unique_jobs, query)
        ranked_jobs = JobRanker.rank_jobs(filtered_jobs, db, profile)

        persisted_jobs: List[DiscoveredJob] = []
        for j in ranked_jobs:
            saved_record = OpportunityRepository.save_opportunity(db, j)
            persisted_jobs.append(saved_record.to_schema())

        return JobSearchResponse(
            success=True,
            total_discovered=total_discovered,
            unique_opportunities=len(persisted_jobs),
            duplicates_skipped=dups_skipped,
            opportunities=persisted_jobs,
            warnings=warnings,
            errors=[]
        )

    def ingest_manual_urls(
        self,
        request: ManualDiscoveryRequest,
        db: Session
    ) -> ManualDiscoveryResponse:
        profile = db.query(UserProfile).first()
        if not profile:
            raise DiscoveryException(
                code=DiscoveryErrorCode.PROFILE_NOT_FOUND,
                message="Master candidate profile not found. Please create a profile before discovering jobs."
            )

        manual_prov = self.providers["manual"]
        query = JobSearchQuery(include_manual_urls=request.urls)
        discovered_jobs = manual_prov.search_jobs(query)

        total_submitted = len(request.urls)
        unique_jobs, dups_skipped = JobDeduplicator.deduplicate(discovered_jobs)
        ranked_jobs = JobRanker.rank_jobs(unique_jobs, db, profile)

        persisted: List[DiscoveredJob] = []
        for j in ranked_jobs:
            saved_record = OpportunityRepository.save_opportunity(db, j)
            persisted.append(saved_record.to_schema())

        warnings = []
        if len(persisted) < total_submitted:
            warnings.append(f"{total_submitted - len(persisted)} URL(s) could not be extracted or were duplicates.")

        return ManualDiscoveryResponse(
            success=True,
            total_submitted=total_submitted,
            unique_opportunities=len(persisted),
            duplicates_skipped=dups_skipped,
            opportunities=persisted,
            warnings=warnings,
            errors=[]
        )

    def list_opportunities(
        self,
        params: OpportunityFilterParams,
        db: Session
    ) -> OpportunityListResponse:
        items, total = OpportunityRepository.list_opportunities(db, params)
        total_pages = math.ceil(total / params.page_size) if params.page_size > 0 else 1

        return OpportunityListResponse(
            items=[item.to_schema() for item in items],
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )

    def get_opportunity(
        self,
        opp_id: int,
        db: Session
    ) -> DiscoveredJob:
        opp = OpportunityRepository.get_opportunity(db, opp_id)
        if not opp:
            raise DiscoveryException(
                code=DiscoveryErrorCode.OPPORTUNITY_NOT_FOUND,
                message=f"Opportunity with ID {opp_id} not found."
            )
        return opp.to_schema()

    def update_opportunity_status(
        self,
        opp_id: int,
        status: PipelineStatus,
        db: Session
    ) -> DiscoveredJob:
        opp = OpportunityRepository.update_opportunity_status(db, opp_id, status)
        return opp.to_schema()

    def analyze_opportunity(
        self,
        opp_id: int,
        db: Session
    ) -> Dict[str, Any]:
        opp = OpportunityRepository.get_opportunity(db, opp_id)
        if not opp:
            raise DiscoveryException(
                code=DiscoveryErrorCode.OPPORTUNITY_NOT_FOUND,
                message=f"Opportunity with ID {opp_id} not found."
            )

        analysis = analyze_job(opp.description, db)

        opp.match_score = analysis.get("match_score", opp.match_score)
        opp.ranking_explanation = analysis.get("reason", opp.ranking_explanation)
        
        current_status = PipelineStatus(opp.status)
        if current_status in (PipelineStatus.DISCOVERED, PipelineStatus.SAVED):
            OpportunityRepository.update_opportunity_status(db, opp_id, PipelineStatus.ANALYZED)

        return {
            "opportunity_id": opp.id,
            "company": opp.company,
            "title": opp.title,
            "analysis": analysis,
        }

    def generate_opportunity_assets(
        self,
        opp_id: int,
        db: Session
    ) -> ApplicationAssetResponse:
        opp = OpportunityRepository.get_opportunity(db, opp_id)
        if not opp:
            raise DiscoveryException(
                code=DiscoveryErrorCode.OPPORTUNITY_NOT_FOUND,
                message=f"Opportunity with ID {opp_id} not found."
            )

        asset_request = ApplicationAssetRequest(
            job_description=opp.description,
            company=opp.company,
            role=opp.title,
        )

        asset_response = default_asset_service.generate_assets(asset_request, db)

        current_status = PipelineStatus(opp.status)
        if current_status in (PipelineStatus.DISCOVERED, PipelineStatus.SAVED, PipelineStatus.ANALYZED):
            OpportunityRepository.update_opportunity_status(db, opp_id, PipelineStatus.ASSETS_GENERATED)

        return asset_response

    def prepare_opportunity_application(
        self,
        opp_id: int,
        db: Session
    ) -> InspectApplicationResponse:
        opp = OpportunityRepository.get_opportunity(db, opp_id)
        if not opp:
            raise DiscoveryException(
                code=DiscoveryErrorCode.OPPORTUNITY_NOT_FOUND,
                message=f"Opportunity with ID {opp_id} not found."
            )

        target_url = opp.application_url or opp.source_url
        inspect_request = InspectApplicationRequest(application_url=target_url)

        inspect_response = default_automation_service.inspect_form(inspect_request, db)

        current_status = PipelineStatus(opp.status)
        if current_status in (
            PipelineStatus.DISCOVERED,
            PipelineStatus.SAVED,
            PipelineStatus.ANALYZED,
            PipelineStatus.ASSETS_GENERATED
        ):
            OpportunityRepository.update_opportunity_status(db, opp_id, PipelineStatus.READY_TO_APPLY)

        return inspect_response


default_discovery_service = JobDiscoveryService()
