from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.profile.repository import (
    get_profile,
    create_profile,
    update_profile,
)

from app.profile.schemas import (
    UserProfileCreate,
    UserProfileUpdate,
)


def get_user_profile(db: Session):
    profile = get_profile(db)

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="User profile not created yet"
        )

    return profile


def create_user_profile(
    db: Session,
    profile_data: UserProfileCreate
):
    existing_profile = get_profile(db)

    if existing_profile:
        raise HTTPException(
            status_code=400,
            detail="A master profile already exists. Use PATCH to update it."
        )

    return create_profile(db, profile_data)


def update_user_profile(
    db: Session,
    profile_data: UserProfileUpdate
):
    profile = get_profile(db)

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="User profile not found. Create it first."
        )

    return update_profile(
        db,
        profile,
        profile_data
    )