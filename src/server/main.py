#!/usr/bin/env python3
"""
Main server application for PartSelect Agent.
Provides API endpoints for interacting with appliance parts and documentation.
"""

import os
import logging
import json
import asyncio
from typing import Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from modules.tools import AsyncCatalogClient, AsyncDocsClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    app_name: str = Field(default="PartSelect Agent API", env="APP_NAME")
    mongodb_uri: str = Field(default="mongodb://localhost:27017", env="MONGODB_URI")
    database_name: str = Field(default="partselect", env="DATABASE_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Additional settings from existing .env
    mongodb_database: Optional[str] = None
    mongodb_collection: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    log_level: Optional[str] = None
    rate_limit_delay: Optional[int] = 2  # Default value of 2 seconds
    
    # Use field_validator instead of validator
    @field_validator('rate_limit_delay', mode='before')
    @classmethod  # Add classmethod decorator to make it a proper class method
    def parse_rate_limit_delay(cls, v):
        if v is None:
            return 2  # Default to 2 seconds
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            # Extract the first part before any comment or whitespace
            try:
                # Strip any comments (text after #)
                clean_value = v.split('#')[0].strip()
                return int(clean_value)
            except ValueError:
                logger.warning(f"Could not parse rate_limit_delay: {v}")
                return 2  # Default value
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create settings instance
try:
    settings = Settings()
    logger.info(f"Loaded settings for {settings.app_name}")
except Exception as e:
    logger.error(f"Error loading settings: {e}")
    # Use defaults if .env is not available
    settings = Settings(
        app_name="PartSelect Agent API (Default)",
        mongodb_uri="mongodb://localhost:27017",
        database_name="partselect",
        debug=True
    )
    logger.warning("Using default settings")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="API for accessing appliance parts and documentation",
    version="1.0.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Client dependency functions
def get_catalog_client():
    """Get an instance of the AsyncCatalogClient."""
    return AsyncCatalogClient(
        mongodb_uri=settings.mongodb_uri,
        database_name=settings.database_name,
        collection_name="parts",
        use_mock=True  # Using mock data for now
    )

def get_docs_client():
    """Get an instance of the AsyncDocsClient."""
    return AsyncDocsClient(
        mongodb_uri=settings.mongodb_uri,
        database_name=settings.database_name,
        collection_name="docs",
        use_mock=True  # Using mock data for now
    )

# Connection manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# Create connection manager instance
manager = ConnectionManager()

# WebSocket chat endpoint
@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            logger.info(f"Received message: {message}")

            # Simulate agent response (replace with actual agent call)
            response = {
                "message": f"You said: {message}",
                "suggested_actions": [
                    "Tell me more about refrigerator parts",
                    "How do I install this?",
                    "Check compatibility"
                ]
            }
            
            # Delay to simulate processing
            await asyncio.sleep(1)
            
            # Send response back to client
            await manager.send_message(json.dumps(response), websocket)
            
    except WebSocketDisconnect:
        logger.info("Client disconnected")
        manager.disconnect(websocket)

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify API is running.
    
    Returns:
        Dictionary with status information
    """
    return {"status": "ok"}

@app.get("/api/parts/{part_number}")
async def get_part(
    part_number: str,
    catalog_client: AsyncCatalogClient = Depends(get_catalog_client)
):
    """
    Get details for a specific part by part number.
    
    Args:
        part_number: The part number to look up
        
    Returns:
        Part details or 404 if not found
    """
    part = await catalog_client.get_part(part_number)
    
    if not part:
        raise HTTPException(status_code=404, detail=f"Part {part_number} not found")
        
    return part

@app.get("/api/parts/model/{model_number}")
async def find_parts_by_model(
    model_number: str,
    limit: int = Query(10, ge=1, le=50),
    catalog_client: AsyncCatalogClient = Depends(get_catalog_client)
):
    """
    Find parts compatible with a specific model number.
    
    Args:
        model_number: The model number to find compatible parts for
        limit: Maximum number of results to return
        
    Returns:
        List of compatible parts
    """
    parts = await catalog_client.find_by_model(model_number, limit)
    return parts

@app.get("/api/parts/search")
async def search_parts(
    query: str,
    appliance_type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    catalog_client: AsyncCatalogClient = Depends(get_catalog_client)
):
    """
    Search for parts based on a query string.
    
    Args:
        query: Search term
        appliance_type: Optional filter for refrigerator or dishwasher
        limit: Maximum number of results to return
        
    Returns:
        List of matching parts
    """
    parts = await catalog_client.search_parts(query, appliance_type, limit)
    return parts

@app.get("/api/parts/compatibility")
async def check_compatibility(
    part_number: str,
    model_number: str,
    catalog_client: AsyncCatalogClient = Depends(get_catalog_client)
):
    """
    Check if a part is compatible with a specific model.
    
    Args:
        part_number: Part number to check
        model_number: Model number to check compatibility with
        
    Returns:
        Compatibility status
    """
    is_compatible = await catalog_client.check_compatibility(part_number, model_number)
    return {"part_number": part_number, "model_number": model_number, "is_compatible": is_compatible}

@app.get("/api/docs/installation")
async def get_installation_docs(
    part_number: Optional[str] = None,
    part_name: Optional[str] = None,
    appliance_type: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    docs_client: AsyncDocsClient = Depends(get_docs_client)
):
    """
    Get installation documentation.
    
    Args:
        part_number: Optional part number to find installation docs for
        part_name: Optional part name to find installation docs for
        appliance_type: Optional appliance type filter
        limit: Maximum number of results to return
        
    Returns:
        List of installation docs
    """
    docs = await docs_client.get_installation_docs(part_number, part_name, appliance_type, limit)
    return docs

@app.get("/api/docs/troubleshooting")
async def get_troubleshooting_docs(
    problem: str,
    appliance_type: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    docs_client: AsyncDocsClient = Depends(get_docs_client)
):
    """
    Get troubleshooting documentation.
    
    Args:
        problem: Problem or symptom to find troubleshooting docs for
        appliance_type: Optional appliance type filter
        limit: Maximum number of results to return
        
    Returns:
        List of troubleshooting docs
    """
    docs = await docs_client.get_troubleshooting_docs(problem=problem, appliance_type=appliance_type, limit=limit)
    return docs

@app.get("/api/docs/search")
async def search_docs(
    query: str,
    doc_type: Optional[str] = None,
    appliance_type: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    docs_client: AsyncDocsClient = Depends(get_docs_client)
):
    """
    Search for documentation.
    
    Args:
        query: Search term
        doc_type: Optional filter for documentation type
        appliance_type: Optional filter for appliance type
        limit: Maximum number of results to return
        
    Returns:
        List of matching docs
    """
    docs = await docs_client.search_docs(query, doc_type, appliance_type, limit)
    return docs

@app.get("/api/docs/repair-steps")
async def get_repair_steps(
    part_name: str,
    appliance_type: Optional[str] = None,
    docs_client: AsyncDocsClient = Depends(get_docs_client)
):
    """
    Get step-by-step repair instructions.
    
    Args:
        part_name: Name of the part to find repair steps for
        appliance_type: Optional appliance type for more specific results
        
    Returns:
        List of repair steps
    """
    steps = await docs_client.get_repair_steps(part_name, appliance_type)
    
    if not steps:
        return {"message": f"No repair steps found for {part_name}", "steps": []}
        
    return {"part_name": part_name, "appliance_type": appliance_type, "steps": steps}

@app.get("/api/docs/safety-notes")
async def get_safety_notes(
    appliance_type: Optional[str] = None,
    docs_client: AsyncDocsClient = Depends(get_docs_client)
):
    """
    Get safety notes for appliance repair.
    
    Args:
        appliance_type: Optional appliance type for more specific safety notes
        
    Returns:
        List of safety notes
    """
    notes = await docs_client.get_safety_notes(appliance_type)
    return {"appliance_type": appliance_type, "notes": notes}

# Run the server if executed as script
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        reload=settings.debug
    )
