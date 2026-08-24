import math
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.profile.models import UserProfile
from app.job_discovery.models import DiscoveredOpportunity
from app.application_pipeline.models import TrackedApplication
from app.application_pipeline.schemas import (
    ApplicationStatus,
    ApplicationPriority,
    ReferralStatus,
    FollowUpStatus,
    CreateApplicationRequest,
    UpdateApplicationRequest,
    ApplicationStatusTransitionRequest,
    MarkAppliedRequest,
    AddNoteRequest,
    ReferralRequest,
    FollowUpRequest,
    InterviewCreateRequest,
    InterviewUpdateRequest,
    ApplicationFilterParams,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationTimelineEventResponse,
    InterviewResponse,
    FollowUpCategoryResponse,
    PipelineSummaryResponse,
)
from app.application_pipeline.errors import PipelineErrorCode, PipelineException
from app.application_pipeline.repository import ApplicationRepository
from app.application_pipeline.timeline import TimelineService
from app.application_pipeline.reminders import FollowUpManager

logger = logging.getLogger("friday.application_pipeline.service")


class ApplicationPipelineService:
    """
    Core service orchestrating application lifecycle tracking, referrals, interviews,
    timeline logs, and Phase 5 opportunity conversions.
    """

    @classmethod
    def _get_profile_id(cls, db: Session) -> Optional[int]:
        profile = db.query(UserProfile).first()
        return profile.id if profile else None

    @classmethod
    def create_application(
        cls,
        request: CreateApplicationRequest,
        db: Session
    ) -> ApplicationResponse:
        profile_id = cls._get_profile_id(db)
        app_record = ApplicationRepository.create_application(
            db=db,
            request=request,
            profile_id=profile_id
        )
        return app_record.to_schema()

    @classmethod
    def create_from_opportunity(
        cls,
        opportunity_id: int,
        db: Session
    ) -> ApplicationResponse:
        opp = db.query(DiscoveredOpportunity).filter(DiscoveredOpportunity.id == opportunity_id).first()
        if not opp:
            raise PipelineException(
                code=PipelineErrorCode.OPPORTUNITY_NOT_FOUND,
                message=f"Opportunity with ID {opportunity_id} not found.",
                opportunity_id=opportunity_id
            )

        profile_id = cls._get_profile_id(db)

        create_req = CreateApplicationRequest(
            company=opp.company,
            role=opp.title,
            source_url=opp.source_url,
            source_platform=opp.provider,
            job_id=opp.external_id,
            job_description=opp.description,
            location=opp.location,
            workplace_type="Remote" if opp.is_remote else None,
            employment_type=opp.employment_type,
            status=ApplicationStatus.SAVED,
            priority=ApplicationPriority.MEDIUM,
            match_score=opp.match_score,
            recommendation=opp.recommendation,
            notes=f"Converted from Phase 5 discovered opportunity #{opp.id} ({opp.provider})."
        )

        app_record = ApplicationRepository.create_application(
            db=db,
            request=create_req,
            profile_id=profile_id,
            opportunity_id=opp.id
        )
        return app_record.to_schema()

    @classmethod
    def get_application(
        cls,
        application_id: int,
        db: Session
    ) -> ApplicationResponse:
        app_record = ApplicationRepository.get_application(db, application_id)
        return app_record.to_schema()

    @classmethod
    def list_applications(
        cls,
        params: ApplicationFilterParams,
        db: Session
    ) -> ApplicationListResponse:
        items, total = ApplicationRepository.list_applications(db, params)
        total_pages = math.ceil(total / params.page_size) if params.page_size > 0 else 1

        return ApplicationListResponse(
            items=[item.to_schema() for item in items],
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )

    @classmethod
    def update_application(
        cls,
        application_id: int,
        request: UpdateApplicationRequest,
        db: Session
    ) -> ApplicationResponse:
        app_record = ApplicationRepository.update_application(db, application_id, request)
        return app_record.to_schema()

    @classmethod
    def transition_status(
        cls,
        application_id: int,
        request: ApplicationStatusTransitionRequest,
        db: Session
    ) -> ApplicationResponse:
        app_record = ApplicationRepository.transition_status(
            db=db,
            application_id=application_id,
            to_status=request.status,
            note=request.note
        )
        return app_record.to_schema()

    @classmethod
    def mark_applied(
        cls,
        application_id: int,
        request: MarkAppliedRequest,
        db: Session
    ) -> ApplicationResponse:
        app_record = ApplicationRepository.get_application(db, application_id)
        curr_status = ApplicationStatus(app_record.status) if app_record.status in [s.value for s in ApplicationStatus] else ApplicationStatus.DISCOVERED

        if curr_status == ApplicationStatus.APPLIED:
            if request.applied_at and not app_record.date_applied:
                app_record.date_applied = request.applied_at
                db.commit()
                db.refresh(app_record)
            return app_record.to_schema()

        app_record = ApplicationRepository.transition_status(
            db=db,
            application_id=application_id,
            to_status=ApplicationStatus.APPLIED,
            note=request.note
        )
        if request.applied_at:
            app_record.date_applied = request.applied_at
            db.commit()
            db.refresh(app_record)

        return app_record.to_schema()

    @classmethod
    def get_timeline(
        cls,
        application_id: int,
        db: Session
    ) -> List[ApplicationTimelineEventResponse]:
        ApplicationRepository.get_application(db, application_id)
        return TimelineService.get_events(db, application_id)

    @classmethod
    def add_note(
        cls,
        application_id: int,
        request: AddNoteRequest,
        db: Session
    ) -> ApplicationResponse:
        app_record = ApplicationRepository.add_note(db, application_id, request.note)
        return app_record.to_schema()

    @classmethod
    def update_referral(
        cls,
        application_id: int,
        request: ReferralRequest,
        db: Session
    ) -> ApplicationResponse:
        app_record = ApplicationRepository.update_referral(
            db=db,
            application_id=application_id,
            status=request.status,
            contact_name=request.contact_name,
            contact_identifier=request.contact_identifier,
            requested_date=request.requested_date,
            referred_date=request.referred_date,
            notes=request.notes
        )
        return app_record.to_schema()

    @classmethod
    def schedule_follow_up(
        cls,
        application_id: int,
        request: FollowUpRequest,
        db: Session
    ) -> ApplicationResponse:
        app_record = ApplicationRepository.schedule_follow_up(
            db=db,
            application_id=application_id,
            next_follow_up_date=request.next_follow_up_date,
            notes=request.notes
        )
        return app_record.to_schema()

    @classmethod
    def complete_follow_up(
        cls,
        application_id: int,
        db: Session
    ) -> ApplicationResponse:
        app_record = ApplicationRepository.complete_follow_up(db, application_id)
        return app_record.to_schema()

    @classmethod
    def create_interview(
        cls,
        application_id: int,
        request: InterviewCreateRequest,
        db: Session
    ) -> InterviewResponse:
        interview = ApplicationRepository.create_interview(db, application_id, request)
        return interview.to_schema()

    @classmethod
    def list_interviews(
        cls,
        application_id: int,
        db: Session
    ) -> List[InterviewResponse]:
        interviews = ApplicationRepository.list_interviews(db, application_id)
        return [i.to_schema() for i in interviews]

    @classmethod
    def update_interview(
        cls,
        application_id: int,
        interview_id: int,
        request: InterviewUpdateRequest,
        db: Session
    ) -> InterviewResponse:
        interview = ApplicationRepository.update_interview(db, application_id, interview_id, request)
        return interview.to_schema()

    @classmethod
    def get_follow_ups(cls, db: Session) -> FollowUpCategoryResponse:
        apps = db.query(TrackedApplication).filter(
            TrackedApplication.next_follow_up_date.isnot(None),
            TrackedApplication.status.notin_([ApplicationStatus.CLOSED.value, ApplicationStatus.WITHDRAWN.value])
        ).all()

        scheduled: List[ApplicationResponse] = []
        due: List[ApplicationResponse] = []
        overdue: List[ApplicationResponse] = []

        for a in apps:
            cal_status = FollowUpManager.calculate_follow_up_status(
                a.next_follow_up_date,
                FollowUpStatus(a.follow_up_status) if a.follow_up_status in [f.value for f in FollowUpStatus] else None
            )
            schema_resp = a.to_schema()
            schema_resp.follow_up_status = cal_status

            if cal_status == FollowUpStatus.SCHEDULED:
                scheduled.append(schema_resp)
            elif cal_status == FollowUpStatus.DUE:
                due.append(schema_resp)
            elif cal_status == FollowUpStatus.OVERDUE:
                overdue.append(schema_resp)

        return FollowUpCategoryResponse(
            scheduled=scheduled,
            due=due,
            overdue=overdue
        )

    @classmethod
    def get_summary(cls, db: Session) -> PipelineSummaryResponse:
        return ApplicationRepository.get_summary(db)


default_pipeline_service = ApplicationPipelineService()

