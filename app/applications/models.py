from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.memory.database import Base


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)

    company = Column(String(255), nullable=False, index=True)
    role = Column(String(255), nullable=False, index=True)

    job_url = Column(String(1000), nullable=True)
    job_description = Column(Text, nullable=True)

    match_score = Column(Integer, nullable=True)
    recommendation = Column(String(20), nullable=True)

    status = Column(
        String(50),
        nullable=False,
        default="NOT_APPLIED"
    )

    applied_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )