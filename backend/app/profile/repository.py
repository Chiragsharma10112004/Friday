from sqlalchemy.orm import Session

from app.profile.models import UserProfile
from app.profile.schemas import UserProfileCreate, UserProfileUpdate


def get_profile(db: Session):
    return db.query(UserProfile).first()


def create_profile(
    db: Session,
    profile_data: UserProfileCreate
):
    profile = UserProfile(**profile_data.model_dump())

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


def update_profile(
    db: Session,
    profile: UserProfile,
    profile_data: UserProfileUpdate
):
    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile