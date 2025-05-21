import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

from langchain_core.language_models import BaseChatModel
# Update import for deepseek integration
try:
    from langchain_deepseek import DeepseekChat as ChatDeepseek
except ImportError:
    # Fallback if langchain_deepseek is not available or API has changed
    ChatDeepseek = None
    logging.warning("Could not import DeepseekChat. LLM-based classification will be disabled.")

from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ..modules.validators import is_in_scope, extract_intent, IntentType
from ..modules.tools import AsyncCatalogClient, AsyncDocsClient, IntentClassificationTool, CartTool, OrderStatusTool
from ..simple_langchain_tools import (
    SimpleProductLookupTool,
    SimpleCompatibilityTool, 
    SimpleInstallationGuideTool,
    SimpleErrorDiagnosisTool
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PartSelectAgent:
    """
    Agent for handling appliance part queries using LangChain tools.
    Orchestrates intent detection and tool selection based on user input.
    """
    
    def __init__(self, 
                catalog_client: Optional[AsyncCatalogClient] = None,
                docs_client: Optional[AsyncDocsClient] = None,
                deepseek_api_key: Optional[str] = None,
                mongodb_uri: str = "mongodb://localhost:27017",
                redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize the PartSelect agent with clients and tools.
        
        Args:
            catalog_client: Optional AsyncCatalogClient instance
            docs_client: Optional AsyncDocsClient instance
            deepseek_api_key: API key for Deepseek LLM
            mongodb_uri: MongoDB connection string for creating clients if not provided
            redis_url: Redis connection string for CartTool
        """
        # Use provided clients or create new ones with mock data
        self.catalog_client = catalog_client or AsyncCatalogClient(mongodb_uri=mongodb_uri, use_mock=True)
        self.docs_client = docs_client or AsyncDocsClient(mongodb_uri=mongodb_uri, use_mock=True)
        
        # Store Redis URL for cart tool
        self.redis_url = redis_url
        
        # Get Deepseek API key
        self.deepseek_api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.deepseek_api_key:
            logger.warning("No Deepseek API key found. LLM-based intent classification will not work.")
        
        # Initialize tools
        self._init_tools()
        
        # Create LLM for agent reasoning (if API key is available and ChatDeepseek is importable)
        self.llm = self._create_llm() if self.deepseek_api_key and ChatDeepseek else None
        if not self.llm and self.deepseek_api_key:
            logger.warning("ChatDeepseek could not be imported. LLM-based classification will not work.")
            
        # Add conversation context tracking
        self.conversation_context = {
            "last_intent": None,
            "last_part_number": None,
            "last_part_name": None,
            "last_model_number": None,
            "last_appliance_type": None
        }
        
        logger.info("PartSelectAgent initialized with all tools")
    
    def _init_tools(self):
        """Initialize all the LangChain-compatible tools."""
        # Create the intent classification tool
        self.intent_classification_tool = IntentClassificationTool(
            deepseek_api_key=self.deepseek_api_key
        ) if self.deepseek_api_key else None
        
        # Create the main tools for handling different intents
        self.product_lookup_tool = SimpleProductLookupTool(catalog_client=self.catalog_client)
        self.compatibility_tool = SimpleCompatibilityTool(catalog_client=self.catalog_client)
        self.installation_guide_tool = SimpleInstallationGuideTool(docs_client=self.docs_client)
        self.error_diagnosis_tool = SimpleErrorDiagnosisTool(
            docs_client=self.docs_client,
            catalog_client=self.catalog_client
        )
        
        # Add new tools for cart management and order status
        self.cart_tool = CartTool(redis_url=self.redis_url)
        self.order_status_tool = OrderStatusTool(api_base_url="https://api.partselect.com/v1")
        
        # Map intents to tools
        self.intent_tool_map = {
            "lookup": self.product_lookup_tool,
            "compatibility": self.compatibility_tool,
            "install": self.installation_guide_tool,
            "diagnose": self.error_diagnosis_tool,
            "cart": self.cart_tool,
            "order": self.order_status_tool
        }
    
    def _create_llm(self) -> Optional[BaseChatModel]:
        """Create the Deepseek LLM for agent reasoning."""
        if not ChatDeepseek:
            return None
            
        try:
            return ChatDeepseek(
                api_key=self.deepseek_api_key,
                model="deepseek-chat",
                temperature=0.1,  # Low temperature for more deterministic outputs
                max_tokens=1024
            )
        except Exception as e:
            logger.error(f"Error creating Deepseek LLM: {e}")
            return None
    
    async def process_query(self, user_input: str) -> Dict[str, Any]:
        """
        Process a user query through the agent pipeline.
        
        Args:
            user_input: The user's query text
            
        Returns:
            Dictionary with tool name, result, and optional follow-up
        """
        # Check for context-dependent queries
        if self._is_context_dependent_query(user_input):
            logger.info(f"Handling context-dependent query: {user_input}")
            intent, enhanced_query = self._enhance_query_with_context(user_input)
            if intent and enhanced_query:
                logger.info(f"Enhanced query: {enhanced_query} with intent: {intent}")
                return await self._run_tool_for_intent(intent, enhanced_query)
        
        # Normal query processing flow
        # Step 1: Check if query is in scope
        if not is_in_scope(user_input):
            logger.info(f"Query out of scope: {user_input}")
            return {
                "tool_name": "out_of_scope",
                "result": "I'm sorry, but I can only help with questions about refrigerator and dishwasher parts.",
                "follow_up": None
            }
        
        # Step 2: Extract intent using rule-based system
        initial_intent = extract_intent(user_input)
        
        # Special handling for common issues in intent detection
        input_lower = user_input.lower()
        # Likely diagnose intents that might be misclassified
        if ("not working" in input_lower or "not cooling" in input_lower or 
            "leaking" in input_lower or "strange" in input_lower or 
            "noise" in input_lower or "broken" in input_lower or
            "doesn't work" in input_lower or "isn't working" in input_lower or
            "problem" in input_lower or "issue" in input_lower or
            "doesn't" in input_lower or "doesn't" in input_lower):
            intent = "diagnose"
            logger.info(f"Overriding intent to diagnose based on problem indicators in: {user_input}")
        else:
            intent = initial_intent
        
        # If intent is out_of_scope but query is in scope, use LLM-based classification
        if intent == "out_of_scope" and self.intent_classification_tool:
            logger.info(f"Rule-based intent unclear, using LLM classification for: {user_input}")
            try:
                intent = self.intent_classification_tool._run(user_input)
                logger.info(f"LLM classified intent: {intent}")
            except Exception as e:
                logger.error(f"Error using intent classification tool: {e}")
                # Keep the original out_of_scope intent if LLM classification fails
        
        # If still out_of_scope, reply with fallback
        if intent == "out_of_scope":
            return {
                "tool_name": "out_of_scope",
                "result": "I understand your question is about appliance parts, but I'm not sure how to help specifically. Could you please rephrase your question about refrigerator or dishwasher parts?",
                "follow_up": "Try asking about finding a specific part, checking compatibility, installation instructions, or diagnosing a problem."
            }
        
        # Step 3: Map intent to tool and run it
        result = await self._run_tool_for_intent(intent, user_input)
        
        # Step 4: Update conversation context with this query
        self._update_conversation_context(intent, user_input, result)
        
        return result
    
    async def _run_tool_for_intent(self, intent: IntentType, user_input: str) -> Dict[str, Any]:
        """
        Run the appropriate tool based on the detected intent.
        
        Args:
            intent: The detected intent type
            user_input: The original user query
            
        Returns:
            Dictionary with tool name, result, and optional follow-up
        """
        # Skip if intent not in our map
        if intent not in self.intent_tool_map:
            logger.warning(f"No tool mapped for intent: {intent}")
            return {
                "tool_name": "unknown_intent",
                "result": "I'm not sure how to process that request.",
                "follow_up": None
            }
        
        tool = self.intent_tool_map[intent]
        logger.info(f"Running tool {tool.name} for intent: {intent}")
        
        # Extract parameters from user input based on intent
        params = self._extract_parameters(intent, user_input)
        
        try:
            # Call the appropriate async method based on intent
            if intent == "lookup":
                # For lookup, we need to extract a part number
                part_number = params.get("part_number", "")
                result = await self._async_run_tool(tool, part_number)
                
                # Generate a follow-up for successful lookups
                follow_up = self._generate_follow_up(intent, result)
                
                return {
                    "tool_name": tool.name,
                    "result": result,
                    "follow_up": follow_up
                }
                
            elif intent == "compatibility":
                # For compatibility, format as part_number:model_number
                query = f"{params.get('part_number', '')}:{params.get('model_number', '')}"
                result = await self._async_run_tool(tool, query)
                
                return {
                    "tool_name": tool.name,
                    "result": result,
                    "follow_up": "Would you like to see installation instructions for this part?"
                }
                
            elif intent == "install":
                # For installation, format as part_name:appliance_type
                query = f"{params.get('part_name', '')}"
                if params.get('appliance_type'):
                    query += f":{params.get('appliance_type')}"
                    
                result = await self._async_run_tool(tool, query)
                
                return {
                    "tool_name": tool.name,
                    "result": result,
                    "follow_up": "Do you need help finding this part?"
                }
                
            elif intent == "diagnose":
                # For diagnosis, format as problem:appliance_type
                query = f"{params.get('problem', '')}"
                if params.get('appliance_type'):
                    query += f":{params.get('appliance_type')}"
                    
                result = await self._async_run_tool(tool, query)
                
                return {
                    "tool_name": tool.name,
                    "result": result,
                    "follow_up": "Would you like me to help you find any of these parts?"
                }
                
            elif intent == "cart":
                # For cart operations, we need action and possibly part number
                params = self._extract_parameters(intent, user_input)
                action = params.get("action", "view")
                
                if action == "add" and "part_number" in params:
                    part_number = params["part_number"]
                    quantity = params.get("quantity", "1")
                    query = f"add:{part_number}:{quantity}"
                elif action == "remove" and "part_number" in params:
                    part_number = params["part_number"]
                    query = f"remove:{part_number}"
                elif action == "clear":
                    query = "clear"
                else:
                    # Default to view
                    query = "view"
                
                result = await self._async_run_tool(tool, query)
                
                # Generate appropriate follow-up based on action
                if action == "add":
                    follow_up = "Would you like to view your cart or continue shopping?"
                elif action == "view":
                    follow_up = "Would you like to checkout or continue shopping?"
                else:
                    follow_up = "Is there anything else you'd like to do with your cart?"
                
                return {
                    "tool_name": tool.name,
                    "result": result,
                    "follow_up": follow_up
                }
                
            elif intent == "order":
                # For order status, format as order_number:email or just one of them
                params = self._extract_parameters(intent, user_input)
                
                if "order_number" in params and "email" in params:
                    query = f"{params['order_number']}:{params['email']}"
                elif "order_number" in params:
                    query = params["order_number"]
                elif "email" in params:
                    query = f"email:{params['email']}"
                else:
                    # Generic query for order status
                    query = "status"
                
                result = await self._async_run_tool(tool, query)
                
                return {
                    "tool_name": tool.name,
                    "result": result,
                    "follow_up": "Would you like to check another order or continue shopping?"
                }
                
            else:
                # Generic fallback
                result = await self._async_run_tool(tool, user_input)
                
                return {
                    "tool_name": tool.name,
                    "result": result,
                    "follow_up": None
                }
                
        except Exception as e:
            logger.error(f"Error running tool {tool.name}: {e}")
            return {
                "tool_name": "error",
                "result": f"I encountered an error while processing your request: {str(e)}",
                "follow_up": "Could you try rephrasing your question?"
            }
    
    async def _async_run_tool(self, tool, query: str) -> str:
        """Run a tool asynchronously."""
        # Access the _arun method for our simple tools
        if hasattr(tool, '_arun'):
            return await tool._arun(query)
        # Fall back to run for non-async tools
        elif hasattr(tool, 'run'):
            return tool.run(query)
        else:
            raise ValueError(f"Tool {tool.name} has no run or _arun method")
    
    def _extract_parameters(self, intent: IntentType, user_input: str) -> Dict[str, str]:
        """
        Extract relevant parameters from user input based on intent.
        
        Args:
            intent: The detected intent type
            user_input: The user's query
            
        Returns:
            Dictionary of extracted parameters
        """
        # This is a simplified parameter extraction
        # In a real system, you might use regex patterns or NER to extract entities
        params = {}
        
        # Convert to lowercase for case-insensitive matching
        input_lower = user_input.lower()
        
        if intent == "lookup":
            # Look for part numbers (simplified)
            import re
            # Look for patterns like "W10295370A" or "67003753"
            part_match = re.search(r'([a-zA-Z]{0,3}\d{4,10}[a-zA-Z0-9]{0,5})', user_input)
            if part_match:
                params["part_number"] = part_match.group(0)
            elif "water filter" in input_lower:
                # Default water filter part for demo purposes
                params["part_number"] = "W10295370A"
                params["part_name"] = "water filter"
            elif "ice maker" in input_lower:
                params["part_number"] = "W10190961"
                params["part_name"] = "ice maker"
            elif "control board" in input_lower:
                params["part_number"] = "WPW10503278"
                params["part_name"] = "control board"
            elif "heating element" in input_lower or "heater" in input_lower:
                params["part_number"] = "WPW10518394"
                params["part_name"] = "heating element" 
            elif "drain pump" in input_lower:
                params["part_number"] = "W10348269"
                params["part_name"] = "drain pump"
            elif "door gasket" in input_lower or "seal" in input_lower:
                params["part_number"] = "WPW10438677"
                params["part_name"] = "door gasket"
            else:
                # Extract part names if no specific part number
                for part in ["water filter", "ice maker", "control board", "heating element", 
                            "drain pump", "door gasket"]:
                    if part in input_lower:
                        params["part_name"] = part
                        break
        
        elif intent == "compatibility":
            # Look for part number and model number
            import re
            # Look for patterns like "W10295370A" or "67003753"
            part_match = re.search(r'([a-zA-Z]{0,3}\d{4,10}[a-zA-Z0-9]{0,5})', user_input)
            if part_match:
                params["part_number"] = part_match.group(0)
            
            # Look for model numbers (usually alphanumeric)
            model_match = re.search(r'([a-zA-Z]{2,5}\d{3,7}[a-zA-Z0-9]{0,5})', user_input)
            if model_match and model_match.group(0) != params.get("part_number", ""):
                params["model_number"] = model_match.group(0)
            
            # If we found a model but no part, and "water filter" is mentioned
            if "model_number" in params and "part_number" not in params and "water filter" in input_lower:
                params["part_number"] = "W10295370A"
                params["part_name"] = "water filter"
        
        elif intent in ["install", "diagnose"]:
            # Detect appliance type
            if "refrigerator" in input_lower or "fridge" in input_lower:
                params["appliance_type"] = "refrigerator"
            elif "dishwasher" in input_lower or "dish washer" in input_lower:
                params["appliance_type"] = "dishwasher"
            
            # For install intent, look for part names
            if intent == "install":
                for part in ["water filter", "ice maker", "control board", "heating element", 
                            "drain pump", "door gasket"]:
                    if part in input_lower:
                        params["part_name"] = part
                        break
            
            # For diagnose intent, look for problems
            elif intent == "diagnose":
                problems = [
                    "not cooling", "no water", "leaking", "not draining", 
                    "making noise", "not working", "ice maker", "no ice",
                    "water dispenser", "not running", "door", "light", "strange taste"
                ]
                
                for problem in problems:
                    if problem in input_lower:
                        params["problem"] = problem
                        break
                
                # Special case for "water tastes strange"
                if "water" in input_lower and ("taste" in input_lower or "strange" in input_lower or "bad" in input_lower):
                    params["problem"] = "water filter"
                    params["part_name"] = "water filter"
        
        elif intent == "cart":
            # Extract parameters for cart operations
            import re
            
            # Look for part numbers
            part_match = re.search(r'([a-zA-Z]{0,3}\d{4,10}[a-zA-Z0-9]{0,5})', user_input)
            if part_match:
                params["part_number"] = part_match.group(0)
                
            # Extract quantities if mentioned
            quantity_match = re.search(r'(\d+)\s+(pcs|pieces|units|quantity)', input_lower)
            if quantity_match:
                params["quantity"] = quantity_match.group(1)
            else:
                # Default quantity
                params["quantity"] = "1"
                
            # Determine cart operation
            if "add" in input_lower or "put" in input_lower:
                params["action"] = "add"
            elif "remove" in input_lower or "delete" in input_lower:
                params["action"] = "remove"
            elif "view" in input_lower or "show" in input_lower or "what" in input_lower:
                params["action"] = "view"
            elif "clear" in input_lower or "empty" in input_lower:
                params["action"] = "clear"
            else:
                params["action"] = "view"  # Default action
        
        elif intent == "order":
            # Extract parameters for order status
            import re
            
            # Look for order numbers (typically 6-10 digits)
            order_match = re.search(r'order\s+(?:number\s+)?#?(\d{6,10})', input_lower)
            if order_match:
                params["order_number"] = order_match.group(1)
                
            # Look for email addresses
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_input)
            if email_match:
                params["email"] = email_match.group(0)
        
        logger.debug(f"Extracted parameters for {intent}: {params}")
        return params
    
    def _generate_follow_up(self, intent: IntentType, result: str) -> Optional[str]:
        """
        Generate a contextual follow-up suggestion based on intent and result.
        
        Args:
            intent: The original intent
            result: The tool result
            
        Returns:
            A follow-up suggestion or None
        """
        if intent == "lookup":
            try:
                # Try to parse the result as JSON
                result_data = json.loads(result)
                
                # If this is an error response, don't give a follow-up
                if "error" in result_data:
                    return None
                
                # Generate follow-up based on part details
                part_name = result_data.get("name", "")
                if part_name:
                    return f"Would you like installation instructions for the {part_name}?"
            except:
                # If we can't parse the JSON, provide a generic follow-up
                return "Would you like to check compatibility or get installation instructions?"
        
        # For other intents, follow-ups are created in _run_tool_for_intent
        return None 
    
    def _is_context_dependent_query(self, query: str) -> bool:
        """
        Check if a query is likely to be referring to previous context.
        For example, "How do I install it?" after asking about a part.
        
        Args:
            query: The user query
            
        Returns:
            True if query is context-dependent
        """
        query_lower = query.lower().strip()
        
        # Check for pronouns without specific parts
        pronouns = ["it", "this", "that", "them", "these", "those"]
        
        # Common follow-up patterns
        follow_up_patterns = [
            "how do i",
            "how to",
            "install",
            "compatible",
            "will it work",
            "is it compatible",
            "where does it go",
            "how much",
            "what about",
            "add to cart",
            "remove from cart",
            "check order"
        ]
        
        # If query is very short, likely follows up on previous context
        if len(query_lower.split()) <= 5:
            for pronoun in pronouns:
                if pronoun in query_lower.split():
                    return True
                    
            for pattern in follow_up_patterns:
                if query_lower.startswith(pattern):
                    return True
        
        # Handle cart-related follow-up queries
        elif "cart" in query_lower or "add" in query_lower or "basket" in query_lower:
            if self.conversation_context["last_part_number"]:
                intent = "cart"
                action = "add" if "add" in query_lower else "view"
                
                if action == "add":
                    return True
                else:
                    return True
        
        # Handle order status follow-up queries
        elif "order" in query_lower or "status" in query_lower or "track" in query_lower:
            intent = "order"
            return True
        
        return False
    
    def _enhance_query_with_context(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Enhance a context-dependent query using conversation context.
        
        Args:
            query: The original query
            
        Returns:
            Tuple of (intent, enhanced_query) or (None, None) if can't enhance
        """
        query_lower = query.lower().strip()
        
        # No context to use
        if not self.conversation_context["last_intent"]:
            return None, None
            
        # Handle installation follow-up queries
        if ("how" in query_lower and "install" in query_lower) or "installation" in query_lower:
            # If there was a previous part, formulate an installation query
            if self.conversation_context["last_part_name"]:
                intent = "install"
                part_name = self.conversation_context["last_part_name"]
                appliance = self.conversation_context["last_appliance_type"] or "refrigerator"
                return intent, f"How do I install a {part_name} in my {appliance}?"
                
        # Handle compatibility follow-up queries
        elif "compatible" in query_lower or "work with" in query_lower:
            if self.conversation_context["last_part_number"] and self.conversation_context["last_model_number"]:
                intent = "compatibility"
                return intent, f"Is part {self.conversation_context['last_part_number']} compatible with {self.conversation_context['last_model_number']}?"
                
        # Handle lookup follow-up queries
        elif "where" in query_lower or "find" in query_lower or "get" in query_lower:
            if self.conversation_context["last_part_name"]:
                intent = "lookup"
                return intent, f"I need a {self.conversation_context['last_part_name']} for my {self.conversation_context['last_appliance_type'] or 'refrigerator'}"
        
        # If previous intent was lookup or compatibility and user asks about installation
        if self.conversation_context["last_intent"] in ["lookup", "compatibility"]:
            if "install" in query_lower or "how" in query_lower:
                intent = "install"
                part_name = self.conversation_context["last_part_name"] or "part"
                appliance = self.conversation_context["last_appliance_type"] or "refrigerator"
                return intent, f"How do I install a {part_name} in my {appliance}?"
        
        # Handle cart-related follow-up queries
        elif "cart" in query_lower or "add" in query_lower or "basket" in query_lower:
            if self.conversation_context["last_part_number"]:
                intent = "cart"
                action = "add" if "add" in query_lower else "view"
                
                if action == "add":
                    return intent, f"Add part {self.conversation_context['last_part_number']} to my cart"
                else:
                    return intent, "View my cart"
        
        # Handle order status follow-up queries
        elif "order" in query_lower or "status" in query_lower or "track" in query_lower:
            intent = "order"
            return intent, "Check my order status"
        
        return None, None
    
    def _update_conversation_context(self, intent: str, query: str, result: Dict[str, Any]) -> None:
        """
        Update the conversation context with information from the current query and result.
        
        Args:
            intent: The intent of the current query
            query: The user's query
            result: The result returned by the agent
        """
        # Update last intent
        self.conversation_context["last_intent"] = intent
        
        # Extract parameters to store in context
        params = self._extract_parameters(intent, query)
        
        # Update context with extracted parameters
        if "part_number" in params:
            self.conversation_context["last_part_number"] = params["part_number"]
        if "part_name" in params:
            self.conversation_context["last_part_name"] = params["part_name"]
        if "model_number" in params:
            self.conversation_context["last_model_number"] = params["model_number"]
        if "appliance_type" in params:
            self.conversation_context["last_appliance_type"] = params["appliance_type"] 