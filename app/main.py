from fastapi import FastAPI

from app.api.system import router as system_router
from app.api.chat import router as chat_router

from app.memory.database import Base, engine
from app.memory import models

app = FastAPI(
    title="FRIDAY API",
    version="0.1.0"
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(system_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {"message": "Backend running successfully"}
