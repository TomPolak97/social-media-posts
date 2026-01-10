"""
Utility functions for FastAPI application configuration and server management.

This module provides helper functions for configuring the FastAPI application,
including CORS setup, route registration, and server startup logic.
"""

import logging
import sys
import os
from typing import List
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path to allow importing posts_routes
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from posts_routes import router as posts_router

# Configure module-level logger
_logger = logging.getLogger(__name__)

# Configuration constants
HOST = "0.0.0.0"
PORT = 8000
CORS_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]


def configure_application(app: FastAPI) -> None:
    """
    Configure the FastAPI application with middleware and routes.
    
    Configures:
    - CORS middleware for cross-origin requests
    - Health check endpoint
    - Posts API routes
    
    Args:
        app: FastAPI application instance
        
    Logs:
        DEBUG: Configuration details
    """
    _logger.debug("Configuring application middleware and routes...")
    
    # Configure CORS
    configure_cors(app)
    
    # Register routes
    register_routes(app)
    
    _logger.debug("Application configuration completed successfully")


def configure_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the FastAPI application.
    
    Allows requests from frontend development servers and enables
    credentials for cross-origin requests.
    
    Args:
        app: FastAPI application instance
        
    Logs:
        DEBUG: CORS configuration details
    """
    _logger.debug(f"Configuring CORS with allowed origins: {CORS_ORIGINS}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    _logger.debug("CORS middleware configured successfully")


def register_routes(app: FastAPI) -> None:
    """
    Register all API routes with the FastAPI application.
    
    Args:
        app: FastAPI application instance
        
    Logs:
        DEBUG: Route registration details
    """
    # Health check endpoint
    @app.get("/health")
    def health_check():
        """
        Health check endpoint.
        
        Returns:
            Dictionary with application status
        """
        return {"status": "ok", "service": "social-media-posts-api"}
    
    # Register posts router (no prefix to maintain backward compatibility)
    app.include_router(posts_router)
    
    _logger.debug("Routes registered successfully")


def should_use_reload() -> bool:
    """
    Determine if uvicorn should use reload mode.
    
    Reload is disabled when:
    - Running in PyCharm debugger (detected by 'pydevd' in sys.modules)
    - Explicitly disabled with --no-reload flag
    
    Returns:
        True if reload should be enabled, False otherwise
        
    Logs:
        DEBUG: Reload mode decision and reason
    """
    # Check if running in debugger
    in_debugger = "pydevd" in sys.modules
    
    # Check for explicit --no-reload flag
    no_reload_flag = "--no-reload" in sys.argv
    
    if in_debugger:
        _logger.debug("Detected debugger environment, disabling reload mode")
        return False
    
    if no_reload_flag:
        _logger.debug("Reload mode explicitly disabled via --no-reload flag")
        return False
    
    _logger.debug("Enabling reload mode for development")
    return True


def start_server(app: FastAPI, use_reload: bool) -> None:
    """
    Start the uvicorn server.
    
    Args:
        app: FastAPI application instance
        use_reload: Whether to enable auto-reload for development
        
    Logs:
        INFO: Server startup information
    """
    if use_reload:
        _logger.info(f"Starting server with reload enabled on {HOST}:{PORT}")
        # Use import string format for reload to work correctly
        uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
    else:
        _logger.info(f"Starting server without reload on {HOST}:{PORT}")
        # Direct app object when not using reload (works better with debuggers)
        uvicorn.run(app, host=HOST, port=PORT, reload=False)


def get_cors_origins() -> List[str]:
    """
    Get the list of allowed CORS origins.
    
    Returns:
        List of allowed origin URLs
    """
    return CORS_ORIGINS.copy()


def get_server_host() -> str:
    """
    Get the server host address.
    
    Returns:
        Server host address
    """
    return HOST


def get_server_port() -> int:
    """
    Get the server port number.
    
    Returns:
        Server port number
    """
    return PORT
