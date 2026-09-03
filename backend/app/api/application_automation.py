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
    try:
        return default_automation_service.inspect_form(request, db)
    except AutomationException as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if e.code == AutomationErrorCode.SESSION_NOT_FOUND or e.code == AutomationErrorCode.APPLICATION_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif e.code == AutomationErrorCode.SESSION_EXPIRED or e.code == AutomationErrorCode.PAGE_STATE_CHANGED or e.code == AutomationErrorCode.STAGE_TRANSITION_INVALID:
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
    "/inspect/{session_id}/refresh",
    response_model=InspectApplicationResponse,
    summary="Re-inspect application form after completing browser authentication"
)
def refresh_inspection_endpoint(
    session_id: str,
    db: Session = Depends(get_db)
):
    try:
        return default_automation_service.refresh_inspection(session_id, db)
    except AutomationException as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if e.code == AutomationErrorCode.SESSION_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif e.code == AutomationErrorCode.SESSION_EXPIRED:
            status_code = status.HTTP_409_CONFLICT

        raise HTTPException(
            status_code=status_code,
            detail={
                "code": e.code.value,
                "message": e.message,
                "platform": e.platform
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
    try:
        return default_automation_service.fill_form(request)
    except AutomationException as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if e.code == AutomationErrorCode.SESSION_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif e.code == AutomationErrorCode.SESSION_EXPIRED or e.code == AutomationErrorCode.STAGE_TRANSITION_INVALID:
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
