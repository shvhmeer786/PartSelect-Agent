"""
Health endpoint for the FastAPI server.
This module provides a simple health check endpoint that can be used by Docker and other services.
"""

from fastapi import APIRouter, HTTPException, Depends
import os
import redis
from pymongo import MongoClient
import requests
import logging

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health():
    """
    Health check endpoint.
    Checks the health of all dependencies (MongoDB, Redis, Pinecone).
    When running locally, some services may not be available and that's ok.
    """
    status = {
        "status": "healthy",
        "dependencies": {},
        "mode": os.getenv("DEPLOYMENT_MODE", "development")
    }
    
    # Check MongoDB
    try:
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://partselect:password@mongodb:27017/")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        status["dependencies"]["mongodb"] = "healthy"
    except Exception as e:
        msg = f"MongoDB unhealthy: {str(e)}"
        logger.warning(msg)
        status["dependencies"]["mongodb"] = "unhealthy (using mock data)"
        if status["mode"] == "production":
            status["status"] = "degraded"
    
    # Check Redis
    try:
        redis_uri = os.getenv("REDIS_URI", "redis://redis:6379/0")
        r = redis.from_url(redis_uri)
        r.ping()
        status["dependencies"]["redis"] = "healthy"
    except Exception as e:
        msg = f"Redis unhealthy: {str(e)}"
        logger.warning(msg)
        status["dependencies"]["redis"] = "unhealthy (not required in development)"
        if status["mode"] == "production":
            status["status"] = "degraded"
    
    # Check Pinecone (or emulator)
    try:
        pinecone_api_key = os.getenv("PINECONE_API_KEY", "")
        if pinecone_api_key:
            # If real Pinecone is configured
            status["dependencies"]["pinecone"] = "configured"
        else:
            # Try to check the emulator if in production mode
            if status["mode"] == "production":
                try:
                    response = requests.get("http://pinecone:8080/health", timeout=2)
                    if response.status_code == 200:
                        status["dependencies"]["pinecone_emulator"] = "healthy"
                    else:
                        status["dependencies"]["pinecone_emulator"] = f"unhealthy: status {response.status_code}"
                        status["status"] = "degraded"
                except Exception as e:
                    status["dependencies"]["pinecone_emulator"] = f"unhealthy: {str(e)}"
                    status["status"] = "degraded"
            else:
                status["dependencies"]["pinecone"] = "using mock data (development mode)"
    except Exception as e:
        logger.warning(f"Pinecone check error: {str(e)}")
        status["dependencies"]["pinecone"] = "using mock data"
    
    # Check DeepSeek API key
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if deepseek_api_key:
        status["dependencies"]["deepseek"] = "configured"
    else:
        status["dependencies"]["deepseek"] = "not configured (fallback enabled)"
    
    return status 