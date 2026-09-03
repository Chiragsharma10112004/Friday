from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserProfileBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None

    headline: Optional[str] = None
    summary: Optional[str] = None
    current_status: Optional[str] = None

    university: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None
    cgpa: Optional[str] = None

    skills: Optional[str] = None
    projects: Optional[str] = None
    experience: Optional[str] = None

    target_roles: Optional[str] = None
    preferred_locations: Optional[str] = None
    remote_preference: Optional[str] = None
    job_type_preference: Optional[str] = None

    work_authorization: Optional[str] = None
    sponsorship_required: Optional[str] = None

    resume_path: Optional[str] = None
    portfolio_path: Optional[str] = None


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(UserProfileBase):
    id: int

    model_config = ConfigDict(from_attributes=True)