from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.memory.database import SessionLocal

from app.profile.schemas import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
)

from app.profile.service import (
    get_user_profile,
    create_user_profile,
    update_user_profile,
)


router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.get(
    "",
    response_model=UserProfileResponse
)
def get_profile_endpoint(
    db: Session = Depends(get_db)
):
    return get_user_profile(db)


@router.post(
    "",
    response_model=UserProfileResponse
)
def create_profile_endpoint(
    profile_data: UserProfileCreate,
    db: Session = Depends(get_db)
):
    return create_user_profile(
        db,
        profile_data
    )


@router.patch(
    "",
    response_model=UserProfileResponse
)
def update_profile_endpoint(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    return update_user_profile(
        db,
        profile_data
    )