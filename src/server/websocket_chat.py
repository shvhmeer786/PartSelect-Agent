#!/usr/bin/env python3
"""
WebSocket chat server for PartSelect Agent.
"""

import logging
import json
import asyncio
import os
import sys
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add the parent directory to the path so we can use absolute imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import the PartSelectAgent with absolute imports
from src.server.agents.part_agent import PartSelectAgent
from src.server.modules.tools import AsyncCatalogClient, AsyncDocsClient

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="PartSelect Chat API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create PartSelectAgent instance
agent = PartSelectAgent(
    deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
    mongodb_uri=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

# Connection manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_sessions: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Assign a unique session ID
        self.user_sessions[websocket] = f"user_{len(self.active_connections)}"
        logger.info(f"Client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.user_sessions:
            del self.user_sessions[websocket]
        logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# Create connection manager instance
manager = ConnectionManager()

# Define WebSocket endpoint
@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            logger.info(f"Received message: {message}")

            try:
                # Process with PartSelectAgent
                result = await agent.process_query(message)
                
                # Format response for the client
                tool_name = result.get("tool_name", "unknown")
                result_content = result.get("result", "")
                follow_up = result.get("follow_up")
                
                # Try to parse result content if it's a JSON string
                try:
                    result_data = json.loads(result_content) if isinstance(result_content, str) else result_content
                except json.JSONDecodeError:
                    result_data = {"text": result_content}
                
                # Create suggested actions from follow-up
                suggested_actions = []
                if follow_up:
                    suggested_actions.append(follow_up)
                
                # Add default actions based on intent
                if tool_name == "product_lookup_tool":
                    suggested_actions.extend([
                        "Is this compatible with my refrigerator?",
                        "How do I install this?",
                        "Add to cart"
                    ])
                elif tool_name == "error_diagnosis_tool":
                    suggested_actions.extend([
                        "Find replacement parts",
                        "Installation instructions"
                    ])
                elif tool_name == "cart_tool":
                    suggested_actions.extend([
                        "Continue shopping",
                        "Checkout",
                        "Clear cart"
                    ])
                elif tool_name == "out_of_scope":
                    suggested_actions = [
                        "I need a water filter for my refrigerator",
                        "Installation Help",
                        "Order Status"
                    ]
                
                # Create client-friendly response format
                response = {
                    "message": result_content,
                    "tool_used": tool_name,
                    "data": result_data if isinstance(result_data, dict) else {},
                    "suggested_actions": suggested_actions
                }
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Fallback response
                response = {
                    "message": "I'm sorry, I encountered an error processing your request. Please try again.",
                    "tool_used": "error",
                    "data": {},
                    "suggested_actions": [
                        "I need a water filter for my refrigerator",
                        "Installation Help",
                        "Order Status"
                    ]
                }
            
            # Send response back to client
            await manager.send_message(json.dumps(response), websocket)
            
    except WebSocketDisconnect:
        logger.info("Client disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Run the server if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("websocket_chat:app", host="0.0.0.0", port=9000, reload=True) 