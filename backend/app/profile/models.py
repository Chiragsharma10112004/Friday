from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.memory.database import Base


class UserProfile(Base):
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, index=True)

    # Personal
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)

    # Professional
    headline = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    current_status = Column(String(100), nullable=True)

    # Education
    university = Column(String(255), nullable=True)
    degree = Column(String(255), nullable=True)
    branch = Column(String(255), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    cgpa = Column(String(20), nullable=True)

    # Skills and experience
    skills = Column(Text, nullable=True)
    projects = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)

    # Job preferences
    target_roles = Column(Text, nullable=True)
    preferred_locations = Column(Text, nullable=True)
    remote_preference = Column(String(100), nullable=True)
    job_type_preference = Column(String(100), nullable=True)

    # Common application information
    work_authorization = Column(String(255), nullable=True)
    sponsorship_required = Column(String(50), nullable=True)

    # Resume/documents
    resume_path = Column(String(500), nullable=True)
    portfolio_path = Column(String(500), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now()
    )