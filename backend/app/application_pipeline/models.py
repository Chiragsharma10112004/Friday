import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.memory.database import Base
from app.application_pipeline.schemas import (
    ApplicationStatus,
    ApplicationPriority,
    ReferralStatus,
    FollowUpStatus,
    InterviewStage,
    InterviewMode,
    InterviewStatus,
    ApplicationResponse,
    ApplicationTimelineEventResponse,
    InterviewResponse,
    ApplicationStatusHistoryResponse,
)


class TrackedApplication(Base):
    __tablename__ = "tracked_applications"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, nullable=True, index=True)
    opportunity_id = Column(Integer, nullable=True, index=True)

    company = Column(String(255), nullable=False, index=True)
    role = Column(String(255), nullable=False, index=True)

    source_url = Column(String(1000), nullable=True)
    source_platform = Column(String(100), nullable=True, default="manual")
    job_id = Column(String(255), nullable=True, index=True)
    job_description = Column(Text, nullable=True)

    location = Column(String(255), nullable=True)
    workplace_type = Column(String(100), nullable=True)
    employment_type = Column(String(100), nullable=True)

    status = Column(String(50), nullable=False, default=ApplicationStatus.DISCOVERED.value, index=True)
    priority = Column(String(20), nullable=False, default=ApplicationPriority.MEDIUM.value, index=True)

    match_score = Column(Integer, nullable=True, index=True)
    recommendation = Column(String(50), nullable=True)

    date_discovered = Column(DateTime(timezone=True), nullable=True)
    date_saved = Column(DateTime(timezone=True), nullable=True)
    date_assets_generated = Column(DateTime(timezone=True), nullable=True)
    date_applied = Column(DateTime(timezone=True), nullable=True)
    last_status_update = Column(DateTime(timezone=True), nullable=True)

    next_follow_up_date = Column(DateTime(timezone=True), nullable=True, index=True)
    follow_up_status = Column(String(50), nullable=False, default=FollowUpStatus.NONE.value, index=True)

    referral_status = Column(String(50), nullable=False, default=ReferralStatus.NOT_REQUESTED.value, index=True)
    referral_contact_name = Column(String(255), nullable=True)
    referral_contact_identifier = Column(String(255), nullable=True)
    referral_requested_date = Column(DateTime(timezone=True), nullable=True)
    referral_referred_date = Column(DateTime(timezone=True), nullable=True)
    referral_notes = Column(Text, nullable=True)

    interview_stage = Column(String(50), nullable=True)
    interview_date = Column(DateTime(timezone=True), nullable=True)

    offer_date = Column(DateTime(timezone=True), nullable=True)
    rejection_date = Column(DateTime(timezone=True), nullable=True)
    withdrawal_date = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_schema(self) -> ApplicationResponse:
        return ApplicationResponse(
            id=self.id,
            profile_id=self.profile_id,
            opportunity_id=self.opportunity_id,
            company=self.company,
            role=self.role,
            source_url=self.source_url,
            source_platform=self.source_platform,
            job_id=self.job_id,
            job_description=self.job_description,
            location=self.location,
            workplace_type=self.workplace_type,
            employment_type=self.employment_type,
            status=ApplicationStatus(self.status) if self.status in ApplicationStatus.__members__ or self.status in [s.value for s in ApplicationStatus] else ApplicationStatus.DISCOVERED,
            priority=ApplicationPriority(self.priority) if self.priority in ApplicationPriority.__members__ or self.priority in [p.value for p in ApplicationPriority] else ApplicationPriority.MEDIUM,
            match_score=self.match_score,
            recommendation=self.recommendation,
            date_discovered=self.date_discovered,
            date_saved=self.date_saved,
            date_assets_generated=self.date_assets_generated,
            date_applied=self.date_applied,
            last_status_update=self.last_status_update,
            next_follow_up_date=self.next_follow_up_date,
            follow_up_status=FollowUpStatus(self.follow_up_status) if self.follow_up_status in FollowUpStatus.__members__ or self.follow_up_status in [f.value for f in FollowUpStatus] else FollowUpStatus.NONE,
            referral_status=ReferralStatus(self.referral_status) if self.referral_status in ReferralStatus.__members__ or self.referral_status in [r.value for r in ReferralStatus] else ReferralStatus.NOT_REQUESTED,
            referral_contact_name=self.referral_contact_name,
            referral_contact_identifier=self.referral_contact_identifier,
            referral_requested_date=self.referral_requested_date,
            referral_referred_date=self.referral_referred_date,
            referral_notes=self.referral_notes,
            interview_stage=self.interview_stage,
            interview_date=self.interview_date,
            offer_date=self.offer_date,
            rejection_date=self.rejection_date,
            withdrawal_date=self.withdrawal_date,
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class ApplicationTimelineEvent(Base):
    __tablename__ = "application_timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(Text, nullable=False)
    event_metadata = Column(Text, nullable=True)  # JSON serialized dict
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_schema(self) -> ApplicationTimelineEventResponse:
        meta = json.loads(self.event_metadata) if self.event_metadata else {}
        return ApplicationTimelineEventResponse(
            id=self.id,
            application_id=self.application_id,
            event_type=self.event_type,
            timestamp=self.timestamp,
            description=self.description,
            metadata=meta,
            created_at=self.created_at,
        )


class ApplicationInterview(Base):
    __tablename__ = "application_interviews"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, nullable=False, index=True)
    stage = Column(String(50), nullable=False, default=InterviewStage.TECHNICAL_ROUND.value)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=60)
    mode = Column(String(50), nullable=False, default=InterviewMode.ONLINE.value)
    meeting_url = Column(String(1000), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default=InterviewStatus.SCHEDULED.value)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_schema(self) -> InterviewResponse:
        return InterviewResponse(
            id=self.id,
            application_id=self.application_id,
            stage=InterviewStage(self.stage) if self.stage in InterviewStage.__members__ or self.stage in [s.value for s in InterviewStage] else InterviewStage.OTHER,
            scheduled_at=self.scheduled_at,
            duration_minutes=self.duration_minutes,
            mode=InterviewMode(self.mode) if self.mode in InterviewMode.__members__ or self.mode in [m.value for m in InterviewMode] else InterviewMode.ONLINE,
            meeting_url=self.meeting_url,
            notes=self.notes,
            status=InterviewStatus(self.status) if self.status in InterviewStatus.__members__ or self.status in [s.value for s in InterviewStatus] else InterviewStatus.SCHEDULED,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, nullable=False, index=True)
    from_status = Column(String(50), nullable=False)
    to_status = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    note = Column(Text, nullable=True)

    def to_schema(self) -> ApplicationStatusHistoryResponse:
        return ApplicationStatusHistoryResponse(
            id=self.id,
            application_id=self.application_id,
            from_status=self.from_status,
            to_status=self.to_status,
            timestamp=self.timestamp,
            note=self.note,
        )

