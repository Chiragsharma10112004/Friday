from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.applications.models import JobApplication
from app.schemas.applications import (
    JobApplicationCreate,
    JobApplicationUpdate,
)


def create_application(
    db: Session,
    application: JobApplicationCreate,
):
    data = application.model_dump()

    if data["status"] == "APPLIED":
        data["applied_at"] = datetime.now(timezone.utc)

    db_application = JobApplication(**data)

    db.add(db_application)
    db.commit()
    db.refresh(db_application)

    return db_application


def get_applications(
    db: Session,
    status: str | None = None,
):
    query = db.query(JobApplication)

    if status:
        query = query.filter(
            JobApplication.status == status
        )

    return query.order_by(
        JobApplication.created_at.desc()
    ).all()


def get_application(
    db: Session,
    application_id: int,
):
    return (
        db.query(JobApplication)
        .filter(JobApplication.id == application_id)
        .first()
    )


def update_application(
    db: Session,
    application_id: int,
    application: JobApplicationUpdate,
):
    db_application = get_application(
        db,
        application_id,
    )

    if not db_application:
        return None

    update_data = application.model_dump(
        exclude_unset=True
    )

    if (
        update_data.get("status") == "APPLIED"
        and db_application.applied_at is None
    ):
        update_data["applied_at"] = datetime.now(
            timezone.utc
        )

    for field, value in update_data.items():
        setattr(db_application, field, value)

    db.commit()
    db.refresh(db_application)

    return db_application


def delete_application(
    db: Session,
    application_id: int,
):
    db_application = get_application(
        db,
        application_id,
    )

    if not db_application:
        return False

    db.delete(db_application)
    db.commit()

    return True

from sqlalchemy import func


def get_application_dashboard(db: Session):
    total_applications = db.query(
        func.count(JobApplication.id)
    ).scalar() or 0

    status_counts = (
        db.query(
            JobApplication.status,
            func.count(JobApplication.id)
        )
        .group_by(JobApplication.status)
        .all()
    )

    by_status = {
        status: count
        for status, count in status_counts
    }

    average_match_score = db.query(
        func.avg(JobApplication.match_score)
    ).scalar()

    strongest_applications = (
        db.query(JobApplication)
        .filter(
            JobApplication.match_score.isnot(None)
        )
        .order_by(
            JobApplication.match_score.desc()
        )
        .limit(5)
        .all()
    )

    return {
        "total_applications": total_applications,
        "by_status": by_status,
        "average_match_score": (
            round(float(average_match_score), 2)
            if average_match_score is not None
            else None
        ),
        "strongest_applications": [
            {
                "id": application.id,
                "company": application.company,
                "role": application.role,
                "match_score": application.match_score,
                "status": application.status,
                "recommendation": application.recommendation,
            }
            for application in strongest_applications
        ],
    }