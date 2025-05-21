#!/usr/bin/env python3
"""
Simplified WebSocket chat server for PartSelect Agent.
This version mocks the cart and order functionality without complex imports.
"""

import logging
import json
import asyncio
import os
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests
from modules.pinecone_retriever import PineconeRetriever

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="PartSelect Chat API")

# Add CORS middleware with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize the PineconeRetriever
pinecone_retriever = PineconeRetriever(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment="us-west1-gcp",
    index_name="partselect"
)

# DeepSeek LLM Integration
class DeepseekIntentClassifier:
    """
    Intent classifier using the DeepSeek LLM API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with an API key for DeepSeek."""
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            logger.warning("No DeepSeek API key provided. LLM intent classification will not work.")
            
    def classify_intent(self, query: str) -> str:
        """Classify the intent of a user query."""
        if not self.api_key:
            logger.warning("No DeepSeek API key. Defaulting to rule-based classification.")
            return self._rule_based_classification(query)
        
        try:
            prompt = self._create_prompt(query)
            response = self._call_deepseek_api(prompt)
            intent = self._extract_intent_from_response(response)
            logger.info(f"DeepSeek classified intent for '{query}': {intent}")
            return intent
        except Exception as e:
            logger.error(f"Error classifying intent with DeepSeek: {e}")
            # Default to rule-based classification when DeepSeek fails
            return self._rule_based_classification(query)
    
    def _create_prompt(self, query: str) -> str:
        """Create a prompt for the DeepSeek API."""
        return f"""
        You are a specialized intent classifier for an appliance parts system.
        Your task is to categorize user queries related to refrigerator and dishwasher parts.
        
        The possible intents are:
        - lookup: User wants to find or identify a specific part
        - compatibility: User wants to check if a part is compatible with their appliance
        - install: User needs installation instructions for a part
        - diagnose: User has an issue and needs to diagnose which part may be causing it
        - cart: User wants to add, view, or modify their shopping cart
        - order: User wants to check the status of an order
        - out_of_scope: Query is not related to refrigerator or dishwasher parts
        
        Analyze the following query and respond with only one of the intent labels above:
        
        User query: "{query}"
        
        Intent:
        """
    
    def _call_deepseek_api(self, prompt: str) -> str:
        """Call the DeepSeek API with the given prompt."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 50
        }
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"DeepSeek API error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _extract_intent_from_response(self, response: str) -> str:
        """Extract the intent from the API response."""
        # Lower case and strip whitespace
        response = response.lower().strip()
        
        # Map of valid intents
        valid_intents = {
            "lookup", "compatibility", "install", "diagnose", 
            "cart", "order", "out_of_scope"
        }
        
        # Check if response is one of the valid intents
        for intent in valid_intents:
            if intent in response:
                return intent
        
        # Default to out_of_scope if no match
        return "out_of_scope"
    
    def _rule_based_classification(self, query: str) -> str:
        """Fallback rule-based classification when DeepSeek is unavailable."""
        query_lower = query.lower()
        
        if any(term in query_lower for term in ["find", "part number", "need part", "find part", "water filter", "refrigerator part"]):
            return "lookup"
        elif any(term in query_lower for term in ["compatible", "work with", "fit", "fits"]):
            return "compatibility"
        elif any(term in query_lower for term in ["install", "installation", "how to", "steps"]):
            return "install"
        elif any(term in query_lower for term in ["not working", "broken", "issue", "problem", "diagnose", "fix"]):
            return "diagnose"
        elif any(term in query_lower for term in ["cart", "add", "shopping", "checkout", "buy"]):
            return "cart"
        elif any(term in query_lower for term in ["order", "status", "track", "delivery", "shipped"]):
            return "order"
        elif any(term in query_lower for term in ["weather", "news", "sports", "price", "sale"]):
            return "out_of_scope"
        else:
            return "out_of_scope"

# Initialize DeepSeek classifier
intent_classifier = DeepseekIntentClassifier()

# Mock cart store - simple dictionary to store user carts
cart_store = {}

# Mock order data
mock_orders = {
    "ORD123456": {
        "order_number": "ORD123456",
        "date": "2025-05-15",
        "customer_email": "john.doe@example.com",
        "status": "Shipped",
        "tracking_number": "1ZW23X4Y5678901234",
        "carrier": "UPS",
        "estimated_delivery": "2025-05-22",
        "items": [
            {
                "part_number": "DA29-00020B",
                "name": "Samsung Refrigerator Water Filter",
                "quantity": 2,
                "price": 49.99
            }
        ],
        "total": 99.98
    },
    "ORD789012": {
        "order_number": "ORD789012",
        "date": "2025-05-18",
        "customer_email": "john.doe@example.com",
        "status": "Processing",
        "items": [
            {
                "part_number": "DA97-07365G",
                "name": "Samsung Ice Maker Assembly",
                "quantity": 1,
                "price": 129.99
            }
        ],
        "total": 129.99
    }
}

# Mock installation guides
installation_guides = {
    "water_filter": "# Installation Guide for Water Filter\n\n## Step-by-Step Instructions:\n1. Turn off the water supply\n2. Remove the old filter by turning counterclockwise\n3. Insert the new filter and turn clockwise until it locks\n4. Run water for 5 minutes to clear the system",
    "ice_maker": "# Installation Guide for Ice Maker\n\n## Step-by-Step Instructions:\n1. Disconnect power to the refrigerator\n2. Remove the freezer shelves for access\n3. Disconnect the wiring harness\n4. Remove mounting screws and old ice maker\n5. Install new ice maker and reattach mounting screws\n6. Connect wiring harness\n7. Restore power and test operation",
    "dishwasher_control_board": "# Installation Guide for Dishwasher Control Board\n\n## Step-by-Step Instructions:\n1. Disconnect power\n2. Remove the outer door panel\n3. Locate the control board at the top of the door\n4. Disconnect all wire harnesses (take a photo first)\n5. Remove mounting screws\n6. Install new board and reconnect wires\n7. Reinstall door and test"
}

# Mock compatibility information
compatibility_info = {
    "samsung_filter": {
        "part_number": "DA29-00020B",
        "name": "Samsung Refrigerator Water Filter",
        "compatible_models": [
            "RF28R7351SG",
            "RF23M8070SG",
            "RF22N9781SG",
            "RF28K9070SG",
            "And 40+ more Samsung refrigerator models"
        ],
        "not_compatible": [
            "Models produced before 2010",
            "Side-by-side models with filter in the grille"
        ]
    }
}

# Mock diagnostic information
diagnostic_info = {
    "ice_maker": {
        "problem": "Ice maker not working or not producing ice",
        "possible_causes": [
            "Water supply issue - check water line is not frozen or kinked",
            "Water filter needs replacement - replace if older than 6 months",
            "Ice maker assembly failure - may need replacement",
            "Control board issue - check for error codes"
        ],
        "recommended_parts": [
            {
                "part_number": "DA97-07365G",
                "name": "Samsung Ice Maker Assembly",
                "price": 129.99
            },
            {
                "part_number": "DA29-00020B",
                "name": "Samsung Water Filter",
                "price": 49.99
            }
        ]
    },
    "dishwasher_not_draining": {
        "problem": "Dishwasher not draining properly",
        "possible_causes": [
            "Clogged drain filter - clean or replace",
            "Drain pump failure - check for obstructions or replace",
            "Drain hose kinked or blocked - inspect and clear",
            "Check valve clogged - clean or replace"
        ],
        "recommended_parts": [
            {
                "part_number": "WPW10348269",
                "name": "Dishwasher Drain Pump",
                "price": 86.49
            },
            {
                "part_number": "W10195677",
                "name": "Dishwasher Check Valve",
                "price": 15.99
            }
        ]
    }
}

# Connection manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_sessions: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Assign a unique session ID
        session_id = f"user_{len(self.active_connections)}"
        self.user_sessions[websocket] = session_id
        # Initialize empty cart for new user
        cart_store[session_id] = []
        logger.info(f"Client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.user_sessions:
            session_id = self.user_sessions[websocket]
            # Clean up user's cart when they disconnect
            if session_id in cart_store:
                del cart_store[session_id]
            del self.user_sessions[websocket]
        logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

# Create connection manager instance
manager = ConnectionManager()

# Helper function to process user messages
async def process_message(message: str, session_id: str) -> Dict:
    """
    Process user messages and detect intent.
    
    Args:
        message: User message
        session_id: User session ID
        
    Returns:
        Response dict with tool, result, and follow-up
    """
    message_lower = message.lower()
    
    # Use DeepSeek intent classification if available
    intent = intent_classifier.classify_intent(message)
    logger.info(f"Classified intent for message '{message}': {intent}")
    
    # Extract appliance type if mentioned
    appliance_type = None
    if "refrigerator" in message_lower or "fridge" in message_lower:
        appliance_type = "refrigerator"
    elif "dishwasher" in message_lower:
        appliance_type = "dishwasher"
    elif "washer" in message_lower or "washing machine" in message_lower:
        appliance_type = "washer"
    elif "dryer" in message_lower:
        appliance_type = "dryer"
    
    # Handle installation intent with Pinecone RAG
    if "how do i install" in message_lower or "installation" in message_lower or intent == "install":
        try:
            # Extract part name for installation
            part_name = "water filter"  # default
            if "ice maker" in message_lower or "icemaker" in message_lower:
                part_name = "ice maker"
            elif "control board" in message_lower:
                part_name = "control board"
            elif "water filter" in message_lower or "filter" in message_lower:
                part_name = "water filter"
            
            # Use Pinecone retriever to get installation guide
            installation_guide = await pinecone_retriever.retrieve_and_format_for_llm(
                query=message,
                doc_type="installation",
                appliance_type=appliance_type,
                top_k=3
            )
            
            # Format the retrieved information into an installation guide
            if installation_guide and "No relevant documentation found" not in installation_guide:
                # Use the retrieved information
                guide = installation_guide
            else:
                # Fall back to mock guides if no relevant docs found
                guide = installation_guides.get(part_name.replace(" ", "_"), installation_guides["water_filter"])
            
            return {
                "tool_name": "installation_guide_tool",
                "result": guide,
                "follow_up": "Do you need help finding this part?"
            }
        except Exception as e:
            logger.error(f"Error retrieving installation guide: {e}")
            # Fall back to mock guides
            guide = installation_guides["water_filter"]
            if "ice maker" in message_lower or "icemaker" in message_lower:
                guide = installation_guides["ice_maker"]
            elif "control board" in message_lower or "dishwasher" in message_lower:
                guide = installation_guides["dishwasher_control_board"]
                
            return {
                "tool_name": "installation_guide_tool",
                "result": guide,
                "follow_up": "Do you need help finding this part?"
            }
    elif intent == "lookup" or (("water filter" in message_lower or "refrigerator part" in message_lower) and "cart" not in message_lower and "order" not in message_lower):
        # Product lookup intent
        return {
            "tool_name": "product_lookup_tool",
            "result": json.dumps({
                "name": "Samsung Refrigerator Water Filter",
                "partNumber": "DA29-00020B",
                "price": 49.99,
                "imageUrl": "https://m.media-amazon.com/images/I/71iuYmN8QIL._AC_UF894,1000_QL80_.jpg",
                "description": "Genuine Samsung refrigerator water filter. Reduces contaminants for cleaner, better tasting water and ice."
            }),
            "follow_up": "Would you like installation instructions for the water filter?"
        }
    elif intent == "compatibility":
        # Compatibility intent
        return {
            "tool_name": "compatibility_tool",
            "result": json.dumps(compatibility_info["samsung_filter"]),
            "follow_up": "Would you like to add this compatible filter to your cart?"
        }
    elif intent == "diagnose":
        try:
            # Extract problem for diagnosis
            problem = "ice maker not working"  # default
            if "dishwasher" in message_lower and "drain" in message_lower:
                problem = "dishwasher not draining"
            elif "ice" in message_lower:
                problem = "ice maker not working"
            elif "water" in message_lower and "leak" in message_lower:
                problem = "water leaking"
            elif "not cooling" in message_lower:
                problem = "refrigerator not cooling"
            
            # Use Pinecone retriever to get diagnostic information
            diagnostic_info_text = await pinecone_retriever.retrieve_and_format_for_llm(
                query=message,
                doc_type="troubleshooting",
                appliance_type=appliance_type,
                top_k=3
            )
            
            # Format the retrieved information into a diagnosis
            if diagnostic_info_text and "No relevant documentation found" not in diagnostic_info_text:
                # Use the retrieved information as a markdown formatted diagnosis
                return {
                    "tool_name": "diagnose_tool",
                    "result": diagnostic_info_text,
                    "follow_up": "Would you like to see any replacement parts for this issue?"
                }
            else:
                # Fall back to mock diagnostics if no relevant docs found
                diagnostic_data = diagnostic_info["ice_maker"]
                if "dishwasher" in message_lower and "drain" in message_lower:
                    diagnostic_data = diagnostic_info["dishwasher_not_draining"]
                
                return {
                    "tool_name": "diagnose_tool",
                    "result": json.dumps(diagnostic_data),
                    "follow_up": "Would you like to see any of these replacement parts?"
                }
        except Exception as e:
            logger.error(f"Error retrieving diagnostic information: {e}")
            # Fall back to mock diagnostics
            diagnostic_data = diagnostic_info["ice_maker"]
            if "dishwasher" in message_lower and "drain" in message_lower:
                diagnostic_data = diagnostic_info["dishwasher_not_draining"]
            
            return {
                "tool_name": "diagnose_tool",
                "result": json.dumps(diagnostic_data),
                "follow_up": "Would you like to see any of these replacement parts?"
            }
    elif intent == "cart" or ("add" in message_lower and ("cart" in message_lower or "basket" in message_lower)):
        # Cart add intent - new feature
        user_cart = cart_store.get(session_id, [])
        user_cart.append({
            "part_number": "DA29-00020B",
            "name": "Samsung Refrigerator Water Filter",
            "quantity": 1,
            "price": 49.99
        })
        cart_store[session_id] = user_cart
        
        return {
            "tool_name": "cart_tool",
            "result": json.dumps({
                "status": "success",
                "message": "Added Samsung Refrigerator Water Filter to cart",
                "part": {
                    "name": "Samsung Refrigerator Water Filter",
                    "partNumber": "DA29-00020B",
                    "price": 49.99
                },
                "quantity": 1
            }),
            "follow_up": "Would you like to view your cart or continue shopping?"
        }
    elif intent == "cart" or (("show" in message_lower or "view" in message_lower) and "cart" in message_lower):
        # Cart view intent - new feature
        user_cart = cart_store.get(session_id, [])
        total_price = sum(item["price"] * item["quantity"] for item in user_cart)
        
        return {
            "tool_name": "cart_tool",
            "result": json.dumps({
                "status": "success",
                "message": f"Cart contains {len(user_cart)} items",
                "items": user_cart,
                "total_price": total_price
            }),
            "follow_up": "Would you like to checkout or continue shopping?"
        }
    elif intent == "order" or ("order" in message_lower and "status" in message_lower):
        # Order status intent - new feature
        order_id = "ORD123456"
        if "789012" in message_lower:
            order_id = "ORD789012"
            
        return {
            "tool_name": "order_status_tool",
            "result": json.dumps(mock_orders.get(order_id, {"error": "Order not found"})),
            "follow_up": "Would you like to check another order or continue shopping?"
        }
    elif intent == "out_of_scope" or "weather" in message_lower or "forecast" in message_lower:
        # Out of scope intent
        return {
            "tool_name": "out_of_scope",
            "result": "I'm sorry, but I can only help with questions about refrigerator and dishwasher parts.",
            "follow_up": None
        }
    else:
        # Generic response for other messages
        return {
            "tool_name": "unknown",
            "result": "How can I help you with your appliance parts today?",
            "follow_up": "Try asking about finding a specific part, checking compatibility, installation instructions, or diagnosing a problem."
        }

# Define WebSocket endpoint
@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            logger.info(f"Received message: {message}")
            
            # Get session ID for this user
            session_id = manager.user_sessions.get(websocket, "unknown")
            
            try:
                # Process the message
                result = await process_message(message, session_id)
                
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
                elif tool_name == "installation_guide_tool":
                    suggested_actions.extend([
                        "Find replacement parts",
                        "Add to cart"
                    ])
                elif tool_name == "compatibility_tool":
                    suggested_actions.extend([
                        "How do I install this?",
                        "Add to cart",
                        "Find a different part"
                    ])
                elif tool_name == "diagnose_tool":
                    suggested_actions.extend([
                        "Find a replacement part",
                        "Show installation instructions",
                        "Contact customer support"
                    ])
                elif tool_name == "cart_tool":
                    suggested_actions.extend([
                        "Continue shopping",
                        "Checkout",
                        "Check order status"
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
            
            # Delay to simulate processing
            await asyncio.sleep(1)
            
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
    uvicorn.run("ws_server_simple:app", host="0.0.0.0", port=9000, reload=True) 