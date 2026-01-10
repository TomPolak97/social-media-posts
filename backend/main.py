"""
Main FastAPI application entry point.

This module initializes the FastAPI application, sets up database tables,
imports CSV data, and starts the server.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

# Configure logging for the entire application FIRST, before any other imports that use logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True  # Override any existing configuration
)

from db import create_tables
from import_csv import import_csv
from utils.main_utils import configure_application, should_use_reload, start_server

# Configure module-level logger
_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application startup and shutdown.
    
    Handles:
    - Database table creation
    - CSV data import
    - Application startup/shutdown logging
    
    Yields:
        Control to the application runtime
        
    Logs:
        INFO: Startup and shutdown events
        ERROR: Startup failures
    """
    _logger.info("=" * 50)
    _logger.info("Application starting up...")
    _logger.info("=" * 50)
    
    try:
        # Initialize database tables
        _logger.info("Initializing database tables...")
        create_tables()
        _logger.info("Database tables initialized successfully")
        
        # Import CSV data if available
        _logger.info("Checking for CSV data import...")
        import_csv()
        _logger.info("CSV import process completed")
        
        _logger.info("=" * 50)
        _logger.info("Startup complete. Application is ready to serve requests.")
        _logger.info("=" * 50)
        
    except Exception as e:
        _logger.error(f"Error during application startup: {e}", exc_info=True)
        raise
    
    # Yield control to the application
    yield
    
    # Shutdown handling
    _logger.info("=" * 50)
    _logger.info("Application shutting down...")
    _logger.info("=" * 50)


# Create FastAPI application instance
_logger.debug("Initializing FastAPI application...")
app = FastAPI(
    title="Social Media Posts API",
    description="API for managing social media posts with filtering, pagination, and CRUD operations",
    version="1.0.0",
    lifespan=lifespan
)

# Configure application (middleware and routes)
configure_application(app)


def main() -> None:
    """
    Main entry point for running the application server.

    Determines reload mode and starts the uvicorn server.
    This function is called when the script is executed directly.

    Logs:
        INFO: Server configuration and startup
    """
    use_reload = should_use_reload()
    start_server(app, use_reload)


# Run the server if this file is executed directly
if __name__ == "__main__":
    main()
