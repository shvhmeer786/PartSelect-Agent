#!/usr/bin/env python3
import asyncio
import json
import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to the Python path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import the agent
try:
    from server.agents.part_agent import PartSelectAgent
except ImportError as e:
    logger.error(f"Error importing PartSelectAgent: {e}")
    logger.info("Make sure the agents directory is properly set up")
    sys.exit(1)

# Test the agent with various queries
async def test_part_agent():
    """Test the PartSelectAgent with various queries."""
    print("\n===== TESTING PARTSELECT AGENT =====\n")
    
    # Check for Deepseek API key
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        print("WARNING: No Deepseek API key found in environment variables.")
        print("LLM-based intent classification will not work.")
    
    # Create the agent
    try:
        agent = PartSelectAgent(deepseek_api_key=deepseek_api_key)
    except Exception as e:
        print(f"ERROR: Failed to initialize PartSelectAgent: {e}")
        return
    
    # Define test cases with expected intents
    test_cases = [
        # Lookup intent
        ("I need a water filter for my refrigerator", "lookup"),
        ("Do you have part number W10295370A?", "lookup"),
        
        # Compatibility intent
        ("Will part 67003753 work with my GD5SHAAXNQ00 dishwasher?", "compatibility"),
        ("Is this water filter compatible with Whirlpool WRS325FDAM04?", "compatibility"),
        
        # Installation intent
        ("How do I install a new water filter in my refrigerator?", "install"),
        ("Instructions for replacing ice maker", "install"),
        
        # Diagnosis intent
        ("My refrigerator is not cooling, what could be wrong?", "diagnose"),
        ("Dishwasher making loud noise during wash cycle", "diagnose"),
        
        # Out of scope or ambiguous queries
        ("What's the weather like today?", "out_of_scope"),
        ("I have a problem with my kitchen appliance", "out_of_scope"),
        
        # Ambiguous query that might need LLM classification
        ("The water tastes strange from my refrigerator", "diagnose")
    ]
    
    # Process each test case
    for query, expected_intent in test_cases:
        print(f"\n--- Test Case ---")
        print(f"Query: '{query}'")
        print(f"Expected intent: {expected_intent}")
        
        try:
            # Process the query
            result = await agent.process_query(query)
            
            # Print result
            print(f"Result tool: {result['tool_name']}")
            print(f"Result: {result['result'][:100]}..." if len(result['result']) > 100 else f"Result: {result['result']}")
            
            if result.get('follow_up'):
                print(f"Follow-up: {result['follow_up']}")
                
        except Exception as e:
            print(f"Error processing query: {e}")
    
    print("\n===== TESTING COMPLETE =====\n")

# Additional test to simulate a full conversation
async def test_conversation_flow():
    """Test a simulated conversation flow with the agent."""
    print("\n===== TESTING CONVERSATION FLOW =====\n")
    
    # Check for Deepseek API key
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    
    # Create the agent
    try:
        agent = PartSelectAgent(deepseek_api_key=deepseek_api_key)
    except Exception as e:
        print(f"ERROR: Failed to initialize PartSelectAgent: {e}")
        return
    
    # Simulate a conversation
    conversation = [
        "I need a new water filter for my refrigerator",
        "Is W10295370A compatible with my Whirlpool WRS325FDAM04?",
        "How do I install it?",
        "My ice maker isn't working after I installed the filter"
    ]
    
    for i, message in enumerate(conversation):
        print(f"\n--- User Message {i+1} ---")
        print(f"User: {message}")
        
        try:
            # Process the message
            result = await agent.process_query(message)
            
            # Print agent response
            print(f"Agent: {result['result'][:150]}..." if len(result['result']) > 150 else f"Agent: {result['result']}")
            
            if result.get('follow_up'):
                print(f"Agent suggestion: {result['follow_up']}")
                
        except Exception as e:
            print(f"Error in conversation: {e}")
    
    print("\n===== CONVERSATION TEST COMPLETE =====\n")

if __name__ == "__main__":
    # Run the test
    try:
        asyncio.run(test_part_agent())
        asyncio.run(test_conversation_flow())
    except Exception as e:
        print(f"Error running tests: {e}") 