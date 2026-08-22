from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.job_discovery.schemas import (
    JobSearchQuery,
    JobSearchResponse,
    ManualDiscoveryRequest,
    ManualDiscoveryResponse,
)
from app.job_discovery.errors import DiscoveryErrorCode, DiscoveryException
from app.job_discovery.service import default_discovery_service

router = APIRouter(
    prefix="/job-discovery",
    tags=["Job Discovery"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/search",
    response_model=JobSearchResponse,
    summary="Search configured job providers and return ranked opportunities"
)
def search_jobs_endpoint(
    query: JobSearchQuery,
    db: Session = Depends(get_db)
):
    try:
        return default_discovery_service.search_and_discover(query, db)
    except DiscoveryException as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if e.code == DiscoveryErrorCode.PROFILE_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif e.code == DiscoveryErrorCode.PROVIDER_UNSUPPORTED:
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

        raise HTTPException(
            status_code=status_code,
            detail={
                "code": e.code.value,
                "message": e.message,
                "provider": e.provider
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DISCOVERY_INTERNAL_ERROR",
                "message": f"Job discovery search failed: {str(e)}"
            }
        )


@router.post(
    "/manual",
    response_model=ManualDiscoveryResponse,
    summary="Ingest manually supplied job URLs and evaluate against profile"
)
def manual_discovery_endpoint(
    request: ManualDiscoveryRequest,
    db: Session = Depends(get_db)
):
    try:
        return default_discovery_service.ingest_manual_urls(request, db)
    except DiscoveryException as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if e.code == DiscoveryErrorCode.PROFILE_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND

        raise HTTPException(
            status_code=status_code,
            detail={
                "code": e.code.value,
                "message": e.message,
                "provider": e.provider
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "MANUAL_DISCOVERY_ERROR",
                "message": f"Manual job discovery failed: {str(e)}"
            }
        )
