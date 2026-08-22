from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.application_automation.schemas import (
    InspectApplicationRequest,
    InspectApplicationResponse,
    FillApprovedFieldsRequest,
    FillApprovedFieldsResponse,
)
from app.application_automation.errors import AutomationErrorCode, AutomationException
from app.application_automation.service import default_automation_service

router = APIRouter(
    prefix="/application-automation",
    tags=["Application Automation"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/inspect",
    response_model=InspectApplicationResponse,
    summary="Stage A: Inspect job application form and generate field preview"
)
def inspect_application_endpoint(
    request: InspectApplicationRequest,
    db: Session = Depends(get_db)
):
    """
    Open target job application form, detect platform, parse visible controls,
    map candidate profile facts, and return a preview with AUTO_FILL_READY,
    APPROVAL_REQUIRED, and MANUAL_REQUIRED classifications.
    Does NOT modify the form or submit the application.
    """
    try:
        return default_automation_service.inspect_form(request, db)
    except AutomationException as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if e.code == AutomationErrorCode.SESSION_NOT_FOUND or e.code == AutomationErrorCode.APPLICATION_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif e.code == AutomationErrorCode.SESSION_EXPIRED or e.code == AutomationErrorCode.PAGE_STATE_CHANGED:
            status_code = status.HTTP_409_CONFLICT
        elif e.code == AutomationErrorCode.SOURCE_ACCESS_RESTRICTED:
            status_code = status.HTTP_403_FORBIDDEN
        elif e.code == AutomationErrorCode.BROWSER_UNAVAILABLE or e.code == AutomationErrorCode.BROWSER_TIMEOUT:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        raise HTTPException(
            status_code=status_code,
            detail={
                "code": e.code.value,
                "message": e.message,
                "platform": e.platform
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_AUTOMATION_ERROR",
                "message": f"Form inspection failed: {str(e)}"
            }
        )


@router.post(
    "/fill",
    response_model=FillApprovedFieldsResponse,
    summary="Stage B: Fill approved fields in active form session"
)
def fill_application_endpoint(
    request: FillApprovedFieldsRequest
):
    """
    Fills ONLY the user-approved form fields in the active session.
    Leaves the browser at the completed form for final human review.
    Hard safety invariant: NEVER submits the application automatically.
    """
    try:
        return default_automation_service.fill_form(request)
    except AutomationException as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if e.code == AutomationErrorCode.SESSION_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif e.code == AutomationErrorCode.SESSION_EXPIRED:
            status_code = status.HTTP_409_CONFLICT
        elif e.code == AutomationErrorCode.SUBMISSION_BLOCKED or e.code == AutomationErrorCode.UNSAFE_FIELD:
            status_code = status.HTTP_403_FORBIDDEN

        raise HTTPException(
            status_code=status_code,
            detail={
                "code": e.code.value,
                "message": e.message,
                "platform": e.platform
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_AUTOMATION_ERROR",
                "message": f"Field filling failed: {str(e)}"
            }
        )

