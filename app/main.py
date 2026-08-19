from fastapi import FastAPI

from app.api.job_applications import router as job_applications_router
from app.api.jobs import router as jobs_router
from app.api.system import router as system_router
from app.api.chat import router as chat_router
from app.api.applications import router as applications_router

from app.memory.database import Base, engine

# Import models so SQLAlchemy registers their tables
from app.memory import models
from app.applications.models import JobApplication


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

@app.get("/")
def root():
    return {
        "message": "Backend running successfully"
    }