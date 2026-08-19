from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.schemas.applications import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationUpdate,
)
from app.services.application_service import (
    create_application,
    delete_application,
    get_application,
    get_applications,
    get_application_dashboard,
    update_application,
)


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "",
    response_model=JobApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application_endpoint(
    application: JobApplicationCreate,
    db: Session = Depends(get_db),
):
    return create_application(
        db,
        application,
    )


@router.get(
    "",
    response_model=list[JobApplicationResponse],
)
def get_applications_endpoint(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return get_applications(
        db,
        status,
    )

@router.get("/dashboard")
def get_application_dashboard_endpoint(
    db: Session = Depends(get_db),
):
    return get_application_dashboard(db)

@router.get(
    "/{application_id}",
    response_model=JobApplicationResponse,
)
def get_application_endpoint(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = get_application(
        db,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return application


@router.patch(
    "/{application_id}",
    response_model=JobApplicationResponse,
)
def update_application_endpoint(
    application_id: int,
    application: JobApplicationUpdate,
    db: Session = Depends(get_db),
):
    updated_application = update_application(
        db,
        application_id,
        application,
    )

    if not updated_application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return updated_application


@router.delete(
    "/{application_id}",
)
def delete_application_endpoint(
    application_id: int,
    db: Session = Depends(get_db),
):
    deleted = delete_application(
        db,
        application_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return {
        "message": "Application deleted successfully"
    }