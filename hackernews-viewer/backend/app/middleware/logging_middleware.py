"""Middleware for logging API requests and responses."""
import time
import logging
from logging.handlers import RotatingFileHandler
import json
from pathlib import Path
from typing import Callable, Dict, Any, Optional

from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings

logs_dir = Path(settings.DATA_DIR) / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

api_log_file = logs_dir / "api.log"

logger = logging.getLogger("api")
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(
    api_log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,  # Keep 5 backup files
    encoding="utf-8"
)

log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)


class APILoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all API requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process a request and log the details."""
        request_id = str(int(time.time() * 1000))
        
        await self._log_request(request, request_id)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            process_time = time.time() - start_time
            
            self._log_response(request, response, process_time, request_id)
            
            return response
        except Exception as exc:
            process_time = time.time() - start_time
            
            self._log_error(request, exc, process_time, request_id)
            
            raise

    async def _log_request(self, request: Request, request_id: str) -> None:
        """Log the request details."""
        client_host = request.client.host if request.client else "unknown"
        
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                await request._receive()
                try:
                    body = json.loads(body_bytes.decode())
                except:
                    body = body_bytes.decode()[:1000]
            except Exception:
                body = "Error reading body"
        
        log_dict = {
            "request_id": request_id,
            "client_ip": client_host,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "headers": dict(request.headers),
            "body": body,
            "type": "request"
        }
        
        logger.info(f"Request: {json.dumps(log_dict)}")

    def _log_response(self, request: Request, response: Response, 
                     process_time: float, request_id: str) -> None:
        """Log the response details."""
        log_dict = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2),
            "headers": dict(response.headers),
            "type": "response"
        }
        
        if 400 <= response.status_code < 600:
            logger.error(f"Response (Error): {json.dumps(log_dict)}")
        else:
            logger.info(f"Response: {json.dumps(log_dict)}")

    def _log_error(self, request: Request, exc: Exception, 
                  process_time: float, request_id: str) -> None:
        """Log exceptions that occur during request processing."""
        log_dict = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "error": str(exc),
            "error_type": type(exc).__name__,
            "process_time_ms": round(process_time * 1000, 2),
            "type": "error"
        }
        
        logger.error(f"Exception during request: {json.dumps(log_dict)}")
