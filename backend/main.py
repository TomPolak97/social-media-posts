from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from posts_routes import router as posts_router
from db import create_tables
from import_csv import import_csv
import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Lifespan event for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Application starting up...")
    create_tables()
    import_csv()
    logging.info("Startup complete.")
    yield
    logging.info("Application shutting down...")

app = FastAPI(lifespan=lifespan)

# Enable CORS for frontend
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

# Include posts endpoints
app.include_router(posts_router)
