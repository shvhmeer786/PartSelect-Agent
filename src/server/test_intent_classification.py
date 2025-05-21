#!/usr/bin/env python3
"""
Test script for the IntentClassificationTool using Deepseek LLM.
"""

import sys
import os
import argparse
from typing import List, Tuple
from dotenv import load_dotenv

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Import our tools and validators
from modules.tools import IntentClassificationTool
from modules.validators import extract_intent, is_in_scope

# Load environment variables
load_dotenv()

def test_intent_classification(query: str, use_fallback: bool = False) -> str:
    """
    Test the intent classification system with a given query.
    
    Args:
        query: The user query to classify
        use_fallback: Whether to use the LLM fallback regardless of rule-based result
        
    Returns:
        The classified intent
    """
    # First, try the rule-based classifier
    intent = extract_intent(query)
    
    print(f"\nQuery: '{query}'")
    print(f"Rule-based intent: {intent}")
    
    # If the rule-based classifier returns 'out_of_scope' or fallback is forced, try the LLM
    if intent == 'out_of_scope' or use_fallback:
        # Get the Deepseek API key from environment
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not deepseek_api_key:
            print("Error: DEEPSEEK_API_KEY environment variable not set. Please set it in your .env file.")
            return intent
            
        # Create the tool
        llm_tool = IntentClassificationTool(deepseek_api_key=deepseek_api_key)
        
        try:
            # Use the LLM to classify
            llm_intent = llm_tool._run(query)
            print(f"LLM-based intent: {llm_intent}")
            
            # Return the LLM intent as the final classification
            return llm_intent
            
        except Exception as e:
            print(f"Error using LLM for classification: {e}")
            
    return intent

def run_test_cases() -> None:
    """Run a set of predefined test cases to showcase the intent classification."""
    # Define test cases that might be ambiguous for rule-based classifier
    test_cases = [
        # Edge cases where rule-based might struggle
        "Can you help me with my refrigerator?",
        "I have a question about my kitchen appliance",
        "Is the GE Profile a good refrigerator?",
        "Do you have parts for a KitchenAid refrigerator?",
        
        # Definitely out of scope cases
        "How do I fix my toaster?",
        "Looking for washing machine parts",
        "What's the weather today?",
        
        # Mixed/ambiguous cases
        "I need to replace something in my refrigerator but don't know what it is",
        "My dishwasher is making a noise, and I also need to order a part",
        "Can you tell me about the differences between refrigerator models?"
    ]
    
    for case in test_cases:
        test_intent_classification(case, use_fallback=True)
        print("-" * 50)

def main():
    """Run the intent classification test based on command line arguments."""
    parser = argparse.ArgumentParser(description="Test the intent classification system")
    parser.add_argument("--query", "-q", type=str, help="Query to classify")
    parser.add_argument("--force-llm", "-f", action="store_true", help="Force LLM usage even if rule-based succeeds")
    parser.add_argument("--run-tests", "-t", action="store_true", help="Run predefined test cases")
    
    args = parser.parse_args()
    
    if args.run_tests:
        run_test_cases()
    elif args.query:
        test_intent_classification(args.query, use_fallback=args.force_llm)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 