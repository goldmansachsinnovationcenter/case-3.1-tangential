"""Main FastAPI application."""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlmodel import Session
import logging
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.api.endpoints import stories, users, system
from app.core.config import settings
from app.core.database import get_db, engine
from app.db.models import SQLModel
from app.middleware.logging_middleware import APILoggingMiddleware

SQLModel.metadata.create_all(bind=engine)

app = FastAPI(title="HackerNews Viewer API")

logs_dir = Path(settings.DATA_DIR) / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

app.add_middleware(APILoggingMiddleware)

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

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Log HTTP exceptions."""
    from app.middleware.logging_middleware import logger as api_logger
    
    log_dict = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "status_code": exc.status_code,
        "detail": str(exc.detail),
        "type": "http_exception"
    }
    api_logger.error(f"HTTP Exception: {json.dumps(log_dict)}")
    raise exc

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Log validation exceptions."""
    from app.middleware.logging_middleware import logger as api_logger
    
    log_dict = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "errors": str(exc),
        "type": "validation_error"
    }
    api_logger.error(f"Validation Error: {json.dumps(log_dict)}")
    raise exc

@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    SQLModel.metadata.create_all(bind=engine)
