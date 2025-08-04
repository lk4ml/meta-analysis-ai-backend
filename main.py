from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

from database import get_db, engine
from models import Base
from routers import research_questions, pubmed_search, screening, extraction, reports
from services.ai_service import AIService
from utils.logging_config import setup_logging
from utils.error_handlers import setup_exception_handlers

load_dotenv()

# Setup logging
logger = setup_logging()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Meta-Analysis AI Backend",
    description="Backend API for automated meta-analysis research",
    version="1.0.0"
)

# Setup exception handlers
setup_exception_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(research_questions.router, prefix="/api", tags=["Research Questions"])
app.include_router(pubmed_search.router, prefix="/api", tags=["PubMed Search"])
app.include_router(screening.router, prefix="/api", tags=["Paper Screening"])
app.include_router(extraction.router, prefix="/api", tags=["Data Extraction"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Meta-Analysis AI Backend API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy", "timestamp": str(datetime.utcnow())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)