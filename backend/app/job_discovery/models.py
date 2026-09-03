import json
from datetime import datetime, timezone
from typing import Dict, Any, List

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func

from app.memory.database import Base
from app.job_discovery.schemas import DiscoveredJob, PipelineStatus, JobRecommendation


class DiscoveredOpportunity(Base):
    __tablename__ = "discovered_opportunities"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), nullable=True, index=True)
    provider = Column(String(50), nullable=False, index=True)
    source_url = Column(String(1000), nullable=False, index=True)
    application_url = Column(String(1000), nullable=True)

    company = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    is_remote = Column(Boolean, nullable=True, default=False)

    description = Column(Text, nullable=False)
    employment_type = Column(String(100), nullable=True)
    experience_level = Column(String(100), nullable=True)
    posted_at = Column(String(100), nullable=True)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())

    status = Column(String(50), nullable=False, default="DISCOVERED", index=True)

    match_score = Column(Integer, nullable=True, index=True)
    recommendation = Column(String(50), nullable=True)
    ranking_explanation = Column(Text, nullable=True)

    matched_skills = Column(Text, nullable=True)  # JSON list
    missing_skills = Column(Text, nullable=True)  # JSON list
    key_strengths = Column(Text, nullable=True)   # JSON list
    key_concerns = Column(Text, nullable=True)    # JSON list
    extra_metadata = Column(Text, nullable=True)  # JSON dict

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_schema(self) -> DiscoveredJob:
        matched = json.loads(self.matched_skills) if self.matched_skills else []
        missing = json.loads(self.missing_skills) if self.missing_skills else []
        strengths = json.loads(self.key_strengths) if self.key_strengths else []
        concerns = json.loads(self.key_concerns) if self.key_concerns else []
        meta = json.loads(self.extra_metadata) if self.extra_metadata else {}

        rec = None
        if self.recommendation:
            try:
                rec = JobRecommendation(self.recommendation)
            except ValueError:
                pass

        stat = PipelineStatus.DISCOVERED
        if self.status:
            try:
                stat = PipelineStatus(self.status)
            except ValueError:
                pass

        return DiscoveredJob(
            id=self.id,
            external_id=self.external_id,
            provider=self.provider,
            source_url=self.source_url,
            application_url=self.application_url,
            company=self.company,
            title=self.title,
            location=self.location,
            is_remote=self.is_remote,
            description=self.description,
            employment_type=self.employment_type,
            experience_level=self.experience_level,
            posted_at=self.posted_at,
            discovered_at=self.discovered_at,
            status=stat,
            match_score=self.match_score,
            recommendation=rec,
            ranking_explanation=self.ranking_explanation,
            matched_skills=matched,
            missing_skills=missing,
            key_strengths=strengths,
            key_concerns=concerns,
            metadata=meta,
        )
