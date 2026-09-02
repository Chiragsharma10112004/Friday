try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass
from fastapi import FastAPI

from app.profile.api import router as profile_router
from app.profile.models import UserProfile
from app.api.job_applications import router as job_applications_router
from app.api.jobs import router as jobs_router
from app.api.system import router as system_router
from app.api.chat import router as chat_router
from app.api.applications import router as applications_router
from app.api.application_assets import router as application_assets_router
from app.api.application_automation import router as application_automation_router
from app.api.job_discovery import router as job_discovery_router
from app.api.opportunities import router as opportunities_router
from app.api.career_intelligence import router as career_intelligence_router
from app.api.autonomous_workflow import router as autonomous_workflow_router
from app.api.application_feedback import router as application_feedback_router

from app.memory.database import Base, engine

# Import models so SQLAlchemy registers their tables
from app.memory import models
from app.applications.models import JobApplication
from app.job_discovery.models import DiscoveredOpportunity
from app.application_pipeline.models import (
    TrackedApplication,
    ApplicationTimelineEvent,
    ApplicationInterview,
    ApplicationStatusHistory,
)
from app.career_intelligence.models import CareerRecommendation
from app.autonomous_workflow.models import (
    AutonomousWorkflow,
    WorkflowStep,
    WorkflowApproval,
    WorkflowActionLog,
    WorkflowRetry,
)
from app.application_feedback.models import (
    ApplicationOutcomeFeedback,
    ApplicationAssetVersion,
    ApplicationFieldIssue,
    FeedbackLearningSignal,
)


app = FastAPI(
    title="FRIDAY API",
    version="0.1.0"
)


# Create database tables
Base.metadata.create_all(bind=engine)


# Include routers
app.include_router(system_router)
app.include_router(chat_router)
app.include_router(jobs_router)
app.include_router(applications_router)
app.include_router(job_applications_router)
app.include_router(profile_router)
app.include_router(application_assets_router)
app.include_router(application_automation_router)
app.include_router(job_discovery_router)
app.include_router(opportunities_router)
app.include_router(career_intelligence_router)
app.include_router(autonomous_workflow_router)
app.include_router(application_feedback_router)

@app.get("/")
def root():
    return {
        "message": "Backend running successfully"
    }