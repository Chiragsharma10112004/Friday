import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.memory.database import Base
from app.career_intelligence.schemas import (
    RecommendationType,
    RecommendationStatus,
    ActionPriority,
    ActionItemResponse,
)


class CareerRecommendation(Base):
    __tablename__ = "career_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, nullable=True, index=True)
    application_id = Column(Integer, nullable=True, index=True)
    opportunity_id = Column(Integer, nullable=True, index=True)

    recommendation_type = Column(String(100), nullable=False, index=True)
    priority = Column(String(20), nullable=False, default=ActionPriority.MEDIUM.value, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)

    score = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default=RecommendationStatus.ACTIVE.value, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    dismissed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    metadata_json = Column(Text, nullable=True)

    def to_schema(self) -> ActionItemResponse:
        meta = json.loads(self.metadata_json) if self.metadata_json else {}
        
        try:
            rec_type = RecommendationType(self.recommendation_type)
        except ValueError:
            rec_type = RecommendationType.UPDATE_APPLICATION

        try:
            prio = ActionPriority(self.priority)
        except ValueError:
            prio = ActionPriority.MEDIUM

        try:
            stat = RecommendationStatus(self.status)
        except ValueError:
            stat = RecommendationStatus.ACTIVE

        return ActionItemResponse(
            id=self.id,
            type=rec_type,
            priority=prio,
            title=self.title,
            description=self.description,
            reason=self.reason,
            recommended_action=self.recommended_action,
            score=self.score,
            application_id=self.application_id,
            opportunity_id=self.opportunity_id,
            status=stat,
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=meta,
        )

