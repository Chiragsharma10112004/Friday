import re
from typing import List, Optional
from sqlalchemy.orm import Query

from app.job_discovery.schemas import DiscoveredJob, JobSearchQuery, OpportunityFilterParams, PipelineStatus
from app.job_discovery.models import DiscoveredOpportunity


class JobFilterEngine:
    """
    Applies search criteria and database query filters for job opportunities.
    """

    @classmethod
    def matches_query(cls, job: DiscoveredJob, query: JobSearchQuery) -> bool:
        title_lower = job.title.lower()
        desc_lower = job.description.lower()
        loc_lower = (job.location or "").lower()

        # 1. Role Filter
        if query.roles:
            role_match = any(role.lower() in title_lower for role in query.roles)
            if not role_match:
                return False

        # 2. Keyword Filter
        if query.keywords:
            kw_match = any(
                kw.lower() in title_lower or kw.lower() in desc_lower
                for kw in query.keywords
            )
            if not kw_match:
                return False

        # 3. Location Filter
        if query.locations:
            loc_match = any(
                loc.lower() in loc_lower or (loc.lower() == "remote" and (job.is_remote or "remote" in loc_lower))
                for loc in query.locations
            )
            if not loc_match:
                return False

        # 4. Remote Only Filter
        if query.remote_only:
            if not job.is_remote and "remote" not in loc_lower:
                return False

        # 5. Employment Type Filter
        if query.employment_types and job.employment_type:
            emp_match = any(et.lower() in job.employment_type.lower() for et in query.employment_types)
            if not emp_match:
                return False

        # 6. Experience Level Filter
        if query.experience_levels:
            exp_match = any(
                el.lower() in title_lower or (job.experience_level and el.lower() in job.experience_level.lower())
                for el in query.experience_levels
            )
            if not exp_match:
                return False

        return True

    @classmethod
    def filter_jobs(cls, jobs: List[DiscoveredJob], query: JobSearchQuery) -> List[DiscoveredJob]:
        filtered = [j for j in jobs if cls.matches_query(j, query)]
        return filtered[:query.max_results]

    @classmethod
    def apply_db_filters(cls, db_query: Query, params: OpportunityFilterParams) -> Query:
        if params.min_match_score is not None:
            db_query = db_query.filter(DiscoveredOpportunity.match_score >= params.min_match_score)

        if params.company:
            db_query = db_query.filter(DiscoveredOpportunity.company.ilike(f"%{params.company}%"))

        if params.title:
            db_query = db_query.filter(DiscoveredOpportunity.title.ilike(f"%{params.title}%"))

        if params.provider:
            db_query = db_query.filter(DiscoveredOpportunity.provider == params.provider.lower())

        if params.location:
            db_query = db_query.filter(DiscoveredOpportunity.location.ilike(f"%{params.location}%"))

        if params.is_remote is not None:
            db_query = db_query.filter(DiscoveredOpportunity.is_remote == params.is_remote)

        if params.status:
            db_query = db_query.filter(DiscoveredOpportunity.status == params.status.value)

        # Sorting
        if params.sort_by == "newest":
            db_query = db_query.order_by(
                DiscoveredOpportunity.discovered_at.desc() if params.sort_order == "desc"
                else DiscoveredOpportunity.discovered_at.asc()
            )
        elif params.sort_by == "company":
            db_query = db_query.order_by(
                DiscoveredOpportunity.company.desc() if params.sort_order == "desc"
                else DiscoveredOpportunity.company.asc()
            )
        elif params.sort_by == "title":
            db_query = db_query.order_by(
                DiscoveredOpportunity.title.desc() if params.sort_order == "desc"
                else DiscoveredOpportunity.title.asc()
            )
        else:  # Default: match_score
            db_query = db_query.order_by(
                DiscoveredOpportunity.match_score.desc().nullslast() if params.sort_order == "desc"
                else DiscoveredOpportunity.match_score.asc().nullslast()
            )

        return db_query
