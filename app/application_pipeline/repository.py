import re
import math
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc, asc

from app.application_pipeline.models import (
    TrackedApplication,
    ApplicationTimelineEvent,
    ApplicationInterview,
    ApplicationStatusHistory,
)
from app.application_pipeline.schemas import (
    ApplicationStatus,
    ApplicationPriority,
    ReferralStatus,
    FollowUpStatus,
    InterviewStage,
    InterviewMode,
    InterviewStatus,
    ApplicationFilterParams,
    PipelineSummaryResponse,
    CreateApplicationRequest,
    UpdateApplicationRequest,
    InterviewCreateRequest,
    InterviewUpdateRequest,
)
from app.application_pipeline.errors import PipelineErrorCode, PipelineException
from app.application_pipeline.reminders import FollowUpManager
from app.application_pipeline.transitions import StatusTransitionEngine
from app.application_pipeline.timeline import TimelineService


class ApplicationRepository:
    """
    SQLAlchemy repository for Application Pipeline & Job Tracking records.
    """

    @staticmethod
    def normalize_text(text: Optional[str]) -> str:
        if not text:
            return ""
        cleaned = re.sub(r"\s+", " ", text.strip().lower())
        return cleaned

    @classmethod
    def check_duplicate(
        cls,
        db: Session,
        company: str,
        role: str,
        job_id: Optional[str] = None,
        source_url: Optional[str] = None,
        profile_id: Optional[int] = None,
        exclude_id: Optional[int] = None,
    ) -> Optional[TrackedApplication]:
        """
        Multi-tier duplicate detection:
        Priority 1: profile_id + company + job_id
        Priority 2: profile_id + normalized company + normalized role + normalized source_url
        """
        active_statuses = [
            s.value for s in ApplicationStatus if s not in (ApplicationStatus.WITHDRAWN, ApplicationStatus.CLOSED)
        ]

        query = db.query(TrackedApplication).filter(
            TrackedApplication.status.in_(active_statuses)
        )
        if exclude_id:
            query = query.filter(TrackedApplication.id != exclude_id)
        if profile_id is not None:
            query = query.filter(
                or_(TrackedApplication.profile_id == profile_id, TrackedApplication.profile_id.is_(None))
            )

        norm_company = cls.normalize_text(company)
        norm_role = cls.normalize_text(role)
        norm_url = cls.normalize_text(source_url)

        # Priority 1: Check by job_id if present
        if job_id and str(job_id).strip():
            target_job_id = str(job_id).strip()
            candidates = query.filter(
                func.lower(TrackedApplication.company) == norm_company,
                TrackedApplication.job_id == target_job_id
            ).first()
            if candidates:
                return candidates

        # Priority 2: Normalized company + role + source_url
        candidates = query.all()
        for cand in candidates:
            cand_company = cls.normalize_text(cand.company)
            cand_role = cls.normalize_text(cand.role)
            cand_url = cls.normalize_text(cand.source_url)

            if cand_company == norm_company:
                if norm_url and cand_url and cand_url == norm_url:
                    return cand
                if cand_role == norm_role and (not norm_url or not cand_url or cand_url == norm_url):
                    return cand

        return None

    @classmethod
    def create_application(
        cls,
        db: Session,
        request: CreateApplicationRequest,
        profile_id: Optional[int] = None,
        opportunity_id: Optional[int] = None,
    ) -> TrackedApplication:
        existing = cls.check_duplicate(
            db=db,
            company=request.company,
            role=request.role,
            job_id=request.job_id,
            source_url=request.source_url,
            profile_id=profile_id,
        )
        if existing:
            raise PipelineException(
                code=PipelineErrorCode.DUPLICATE_APPLICATION,
                message=f"An active application for '{request.role}' at '{request.company}' already exists (ID: {existing.id}).",
                application_id=existing.id
            )

        now = datetime.now(timezone.utc)
        app_record = TrackedApplication(
            profile_id=profile_id,
            opportunity_id=opportunity_id,
            company=request.company.strip(),
            role=request.role.strip(),
            source_url=request.source_url.strip() if request.source_url else None,
            source_platform=request.source_platform or "manual",
            job_id=request.job_id.strip() if request.job_id else None,
            job_description=request.job_description,
            location=request.location,
            workplace_type=request.workplace_type,
            employment_type=request.employment_type,
            status=request.status.value,
            priority=request.priority.value,
            match_score=request.match_score,
            recommendation=request.recommendation,
            notes=request.notes,
            date_discovered=now,
            last_status_update=now,
            follow_up_status=FollowUpStatus.NONE.value,
            referral_status=ReferralStatus.NOT_REQUESTED.value,
            created_at=now,
            updated_at=now,
        )

        if request.status == ApplicationStatus.SAVED:
            app_record.date_saved = now
        elif request.status == ApplicationStatus.ASSETS_READY:
            app_record.date_assets_generated = now
        elif request.status == ApplicationStatus.APPLIED:
            app_record.date_applied = now

        db.add(app_record)
        db.commit()
        db.refresh(app_record)

        TimelineService.log_event(
            db=db,
            application_id=app_record.id,
            event_type="APPLICATION_CREATED",
            description=f"Application for '{app_record.role}' at '{app_record.company}' created.",
            metadata={"status": app_record.status, "priority": app_record.priority},
            now=now
        )

        return app_record

    @classmethod
    def get_application(cls, db: Session, application_id: int) -> TrackedApplication:
        app_record = db.query(TrackedApplication).filter(TrackedApplication.id == application_id).first()
        if not app_record:
            raise PipelineException(
                code=PipelineErrorCode.APPLICATION_NOT_FOUND,
                message=f"Application with ID {application_id} not found.",
                application_id=application_id
            )

        calculated_fu = FollowUpManager.calculate_follow_up_status(
            app_record.next_follow_up_date,
            FollowUpStatus(app_record.follow_up_status) if app_record.follow_up_status in [f.value for f in FollowUpStatus] else None
        )
        if app_record.follow_up_status != calculated_fu.value and app_record.follow_up_status != FollowUpStatus.COMPLETED.value:
            app_record.follow_up_status = calculated_fu.value
            db.commit()
            db.refresh(app_record)

        return app_record

    @classmethod
    def list_applications(
        cls,
        db: Session,
        params: ApplicationFilterParams
    ) -> Tuple[List[TrackedApplication], int]:
        query = db.query(TrackedApplication)

        if params.status:
            query = query.filter(TrackedApplication.status == params.status.value)
        if params.company:
            query = query.filter(TrackedApplication.company.ilike(f"%{params.company.strip()}%"))
        if params.role:
            query = query.filter(TrackedApplication.role.ilike(f"%{params.role.strip()}%"))
        if params.priority:
            query = query.filter(TrackedApplication.priority == params.priority.value)
        if params.referral_status:
            query = query.filter(TrackedApplication.referral_status == params.referral_status.value)
        if params.follow_up_status:
            query = query.filter(TrackedApplication.follow_up_status == params.follow_up_status.value)

        total = query.count()

        sort_attr = getattr(TrackedApplication, params.sort_by, TrackedApplication.created_at)
        if params.sort_order.lower() == "asc":
            query = query.order_by(asc(sort_attr), asc(TrackedApplication.id))
        else:
            query = query.order_by(desc(sort_attr), desc(TrackedApplication.id))

        offset = (params.page - 1) * params.page_size
        items = query.offset(offset).limit(params.page_size).all()

        for item in items:
            cal_fu = FollowUpManager.calculate_follow_up_status(
                item.next_follow_up_date,
                FollowUpStatus(item.follow_up_status) if item.follow_up_status in [f.value for f in FollowUpStatus] else None
            )
            if item.follow_up_status != cal_fu.value and item.follow_up_status != FollowUpStatus.COMPLETED.value:
                item.follow_up_status = cal_fu.value

        return items, total

    @classmethod
    def update_application(
        cls,
        db: Session,
        application_id: int,
        request: UpdateApplicationRequest
    ) -> TrackedApplication:
        app_record = cls.get_application(db, application_id)

        update_dict = request.model_dump(exclude_unset=True)
        if not update_dict:
            return app_record

        new_company = update_dict.get("company", app_record.company)
        new_role = update_dict.get("role", app_record.role)
        new_job_id = update_dict.get("job_id", app_record.job_id)
        new_url = update_dict.get("source_url", app_record.source_url)

        if (
            new_company != app_record.company
            or new_role != app_record.role
            or new_job_id != app_record.job_id
            or new_url != app_record.source_url
        ):
            dup = cls.check_duplicate(
                db=db,
                company=new_company,
                role=new_role,
                job_id=new_job_id,
                source_url=new_url,
                profile_id=app_record.profile_id,
                exclude_id=application_id
            )
            if dup:
                raise PipelineException(
                    code=PipelineErrorCode.DUPLICATE_APPLICATION,
                    message=f"Update conflicts with existing application '{dup.role}' at '{dup.company}' (ID: {dup.id}).",
                    application_id=dup.id
                )

        for key, val in update_dict.items():
            if hasattr(app_record, key):
                if isinstance(val, (ApplicationStatus, ApplicationPriority, ReferralStatus, FollowUpStatus)):
                    setattr(app_record, key, val.value)
                else:
                    setattr(app_record, key, val)

        app_record.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(app_record)
        return app_record

    @classmethod
    def transition_status(
        cls,
        db: Session,
        application_id: int,
        to_status: ApplicationStatus,
        note: Optional[str] = None
    ) -> TrackedApplication:
        app_record = cls.get_application(db, application_id)
        from_status = ApplicationStatus(app_record.status) if app_record.status in [s.value for s in ApplicationStatus] else ApplicationStatus.DISCOVERED

        StatusTransitionEngine.validate_transition(from_status, to_status, application_id=application_id)

        now = datetime.now(timezone.utc)
        StatusTransitionEngine.apply_transition_timestamps(app_record, to_status, now=now)
        app_record.status = to_status.value
        app_record.updated_at = now

        db.commit()
        db.refresh(app_record)

        history = ApplicationStatusHistory(
            application_id=application_id,
            from_status=from_status.value,
            to_status=to_status.value,
            timestamp=now,
            note=note,
        )
        db.add(history)

        event_type = "STATUS_CHANGED"
        if to_status == ApplicationStatus.APPLIED:
            event_type = "APPLICATION_MARKED_APPLIED"
        elif to_status == ApplicationStatus.OFFER:
            event_type = "OFFER_RECORDED"
        elif to_status == ApplicationStatus.REJECTED:
            event_type = "APPLICATION_REJECTED"
        elif to_status == ApplicationStatus.WITHDRAWN:
            event_type = "APPLICATION_WITHDRAWN"

        desc = f"Status changed from {from_status.value} to {to_status.value}."
        if note:
            desc += f" Note: {note}"

        TimelineService.log_event(
            db=db,
            application_id=application_id,
            event_type=event_type,
            description=desc,
            metadata={"from_status": from_status.value, "to_status": to_status.value, "note": note},
            now=now
        )
        db.commit()
        return app_record

    @classmethod
    def add_note(cls, db: Session, application_id: int, note_text: str) -> TrackedApplication:
        app_record = cls.get_application(db, application_id)
        now = datetime.now(timezone.utc)

        existing_notes = app_record.notes or ""
        timestamp_prefix = f"[{now.strftime('%Y-%m-%d %H:%M UTC')}]"
        new_note_entry = f"{timestamp_prefix} {note_text.strip()}"

        if existing_notes:
            app_record.notes = f"{existing_notes}\n{new_note_entry}"
        else:
            app_record.notes = new_note_entry

        app_record.updated_at = now
        db.commit()
        db.refresh(app_record)

        TimelineService.log_event(
            db=db,
            application_id=application_id,
            event_type="NOTE_ADDED",
            description=f"Note added: {note_text.strip()}",
            metadata={"note": note_text.strip()},
            now=now
        )
        return app_record

    @classmethod
    def update_referral(
        cls,
        db: Session,
        application_id: int,
        status: ReferralStatus,
        contact_name: Optional[str] = None,
        contact_identifier: Optional[str] = None,
        requested_date: Optional[datetime] = None,
        referred_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> TrackedApplication:
        app_record = cls.get_application(db, application_id)
        now = datetime.now(timezone.utc)

        is_new_referral = (app_record.referral_status == ReferralStatus.NOT_REQUESTED.value)

        app_record.referral_status = status.value
        if contact_name is not None:
            app_record.referral_contact_name = contact_name
        if contact_identifier is not None:
            app_record.referral_contact_identifier = contact_identifier
        if requested_date is not None:
            app_record.referral_requested_date = requested_date
        elif is_new_referral and status in (ReferralStatus.REQUESTED, ReferralStatus.REFERRAL_PENDING):
            app_record.referral_requested_date = now

        if referred_date is not None:
            app_record.referral_referred_date = referred_date
        elif status == ReferralStatus.REFERRED and not app_record.referral_referred_date:
            app_record.referral_referred_date = now

        if notes is not None:
            app_record.referral_notes = notes

        app_record.updated_at = now
        db.commit()
        db.refresh(app_record)

        evt_type = "REFERRAL_ADDED" if is_new_referral else "REFERRAL_STATUS_UPDATED"
        desc = f"Referral status updated to '{status.value}'"
        if contact_name:
            desc += f" (Contact: {contact_name})"

        TimelineService.log_event(
            db=db,
            application_id=application_id,
            event_type=evt_type,
            description=desc,
            metadata={
                "referral_status": status.value,
                "contact_name": contact_name,
                "contact_identifier": contact_identifier,
                "notes": notes
            },
            now=now
        )
        return app_record

    @classmethod
    def schedule_follow_up(
        cls,
        db: Session,
        application_id: int,
        next_follow_up_date: datetime,
        notes: Optional[str] = None,
    ) -> TrackedApplication:
        app_record = cls.get_application(db, application_id)
        now = datetime.now(timezone.utc)

        app_record.next_follow_up_date = next_follow_up_date
        app_record.follow_up_status = FollowUpManager.calculate_follow_up_status(next_follow_up_date, now=now).value
        app_record.updated_at = now

        db.commit()
        db.refresh(app_record)

        TimelineService.log_event(
            db=db,
            application_id=application_id,
            event_type="FOLLOW_UP_SCHEDULED",
            description=f"Follow-up scheduled for {next_follow_up_date.strftime('%Y-%m-%d')}.",
            metadata={"next_follow_up_date": next_follow_up_date.isoformat(), "notes": notes},
            now=now
        )
        return app_record

    @classmethod
    def complete_follow_up(cls, db: Session, application_id: int) -> TrackedApplication:
        app_record = cls.get_application(db, application_id)
        now = datetime.now(timezone.utc)

        app_record.follow_up_status = FollowUpStatus.COMPLETED.value
        app_record.updated_at = now

        db.commit()
        db.refresh(app_record)

        TimelineService.log_event(
            db=db,
            application_id=application_id,
            event_type="FOLLOW_UP_COMPLETED",
            description="Follow-up task marked as completed.",
            metadata={"completed_at": now.isoformat()},
            now=now
        )
        return app_record

    @classmethod
    def create_interview(
        cls,
        db: Session,
        application_id: int,
        request: InterviewCreateRequest
    ) -> ApplicationInterview:
        app_record = cls.get_application(db, application_id)
        now = datetime.now(timezone.utc)

        interview = ApplicationInterview(
            application_id=application_id,
            stage=request.stage.value,
            scheduled_at=request.scheduled_at,
            duration_minutes=request.duration_minutes,
            mode=request.mode.value,
            meeting_url=request.meeting_url,
            notes=request.notes,
            status=InterviewStatus.SCHEDULED.value,
            created_at=now,
            updated_at=now,
        )
        db.add(interview)

        app_record.interview_stage = request.stage.value
        app_record.interview_date = request.scheduled_at
        app_record.updated_at = now

        curr_status = ApplicationStatus(app_record.status) if app_record.status in [s.value for s in ApplicationStatus] else ApplicationStatus.DISCOVERED
        if curr_status == ApplicationStatus.APPLIED:
            try:
                cls.transition_status(
                    db=db,
                    application_id=application_id,
                    to_status=ApplicationStatus.INTERVIEWING,
                    note=f"Interview round '{request.stage.value}' scheduled."
                )
            except Exception:
                pass

        db.commit()
        db.refresh(interview)

        TimelineService.log_event(
            db=db,
            application_id=application_id,
            event_type="INTERVIEW_SCHEDULED",
            description=f"Interview scheduled: {request.stage.value} ({request.mode.value}) on {request.scheduled_at.strftime('%Y-%m-%d %H:%M')}.",
            metadata={
                "interview_id": interview.id,
                "stage": request.stage.value,
                "scheduled_at": request.scheduled_at.isoformat(),
                "mode": request.mode.value,
            },
            now=now
        )
        return interview

    @classmethod
    def list_interviews(cls, db: Session, application_id: int) -> List[ApplicationInterview]:
        cls.get_application(db, application_id)
        return (
            db.query(ApplicationInterview)
            .filter(ApplicationInterview.application_id == application_id)
            .order_by(ApplicationInterview.scheduled_at.asc())
            .all()
        )

    @classmethod
    def update_interview(
        cls,
        db: Session,
        application_id: int,
        interview_id: int,
        request: InterviewUpdateRequest
    ) -> ApplicationInterview:
        cls.get_application(db, application_id)

        interview = (
            db.query(ApplicationInterview)
            .filter(
                ApplicationInterview.id == interview_id,
                ApplicationInterview.application_id == application_id
            )
            .first()
        )
        if not interview:
            raise PipelineException(
                code=PipelineErrorCode.INTERVIEW_NOT_FOUND,
                message=f"Interview with ID {interview_id} for application {application_id} not found.",
                application_id=application_id
            )

        now = datetime.now(timezone.utc)
        update_dict = request.model_dump(exclude_unset=True)

        for k, v in update_dict.items():
            if hasattr(interview, k):
                if isinstance(v, (InterviewStage, InterviewMode, InterviewStatus)):
                    setattr(interview, k, v.value)
                else:
                    setattr(interview, k, v)

        interview.updated_at = now
        db.commit()
        db.refresh(interview)

        TimelineService.log_event(
            db=db,
            application_id=application_id,
            event_type="INTERVIEW_UPDATED",
            description=f"Interview #{interview_id} updated (Stage: {interview.stage}, Status: {interview.status}).",
            metadata={"interview_id": interview_id, "status": interview.status, "stage": interview.stage},
            now=now
        )
        return interview

    @classmethod
    def get_summary(cls, db: Session) -> PipelineSummaryResponse:
        total_apps = db.query(func.count(TrackedApplication.id)).scalar() or 0

        status_counts_raw = (
            db.query(TrackedApplication.status, func.count(TrackedApplication.id))
            .group_by(TrackedApplication.status)
            .all()
        )
        status_counts = {s.value: 0 for s in ApplicationStatus}
        for st, count in status_counts_raw:
            status_counts[st] = count

        prio_counts_raw = (
            db.query(TrackedApplication.priority, func.count(TrackedApplication.id))
            .group_by(TrackedApplication.priority)
            .all()
        )
        priority_counts = {p.value: 0 for p in ApplicationPriority}
        for pr, count in prio_counts_raw:
            priority_counts[pr] = count

        company_counts_raw = (
            db.query(TrackedApplication.company, func.count(TrackedApplication.id))
            .group_by(TrackedApplication.company)
            .order_by(desc(func.count(TrackedApplication.id)))
            .all()
        )
        applications_by_company = {comp: count for comp, count in company_counts_raw}

        avg_score = db.query(func.avg(TrackedApplication.match_score)).filter(TrackedApplication.match_score.isnot(None)).scalar()
        avg_score_val = round(float(avg_score), 2) if avg_score is not None else None

        applied_count = db.query(func.count(TrackedApplication.id)).filter(TrackedApplication.status == ApplicationStatus.APPLIED.value).scalar() or 0
        interview_count = db.query(func.count(TrackedApplication.id)).filter(TrackedApplication.status == ApplicationStatus.INTERVIEWING.value).scalar() or 0
        offer_count = db.query(func.count(TrackedApplication.id)).filter(TrackedApplication.status == ApplicationStatus.OFFER.value).scalar() or 0
        rejection_count = db.query(func.count(TrackedApplication.id)).filter(TrackedApplication.status == ApplicationStatus.REJECTED.value).scalar() or 0

        all_apps = db.query(TrackedApplication).filter(TrackedApplication.next_follow_up_date.isnot(None)).all()
        now = datetime.now(timezone.utc)
        fu_due_count = 0
        fu_overdue_count = 0

        for a in all_apps:
            fu_status = FollowUpManager.calculate_follow_up_status(a.next_follow_up_date, now=now)
            if fu_status == FollowUpStatus.DUE:
                fu_due_count += 1
            elif fu_status == FollowUpStatus.OVERDUE:
                fu_overdue_count += 1

        ref_pending_count = (
            db.query(func.count(TrackedApplication.id))
            .filter(TrackedApplication.referral_status.in_([ReferralStatus.REQUESTED.value, ReferralStatus.REFERRAL_PENDING.value]))
            .scalar() or 0
        )

        return PipelineSummaryResponse(
            total_applications=total_apps,
            status_counts=status_counts,
            priority_counts=priority_counts,
            applications_by_company=applications_by_company,
            average_match_score=avg_score_val,
            applied_count=applied_count,
            interview_count=interview_count,
            offer_count=offer_count,
            rejection_count=rejection_count,
            follow_up_due_count=fu_due_count,
            follow_up_overdue_count=fu_overdue_count,
            referral_pending_count=ref_pending_count,
        )

