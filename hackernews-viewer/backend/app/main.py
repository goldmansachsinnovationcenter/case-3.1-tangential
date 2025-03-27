"""Main FastAPI application."""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.endpoints import stories, users, system
from app.core.config import settings
from app.core.database import get_db, engine
from app.db.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HackerNews Viewer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(stories.router, prefix=f"{settings.API_V1_STR}/stories", tags=["stories"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(system.router, prefix=f"{settings.API_V1_STR}/system", tags=["system"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the HackerNews Viewer API"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    Base.metadata.create_all(bind=engine)
