#!/usr/bin/env python3
"""
Test script for Deepseek LLM-based intent classification without LangChain.
"""

import sys
import os
import requests
import json
import argparse
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the Deepseek API key from environment
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    print("Error: DEEPSEEK_API_KEY environment variable not set. Please set it in your .env file.")
    sys.exit(1)

def create_classification_prompt(query: str) -> str:
    """
    Create a detailed prompt for the intent classification task.
    
    Args:
        query: User's raw query
        
    Returns:
        A formatted prompt for Deepseek LLM
    """
    return f"""You are an intent classification system for a refrigerator and dishwasher parts assistant.
Your task is to classify the user's query into one of the following intents:
- lookup: User is looking for a part or information about a part
- compatibility: User is asking if a part is compatible with their appliance
- install: User is asking how to install or replace a part
- diagnose: User is asking about troubleshooting a problem
- order: User is trying to order/purchase a part
- status: User is asking about the status of an order
- out_of_scope: Query is not related to refrigerator or dishwasher parts

IMPORTANT: The assistant ONLY handles refrigerator and dishwasher parts.
Queries about other appliances (ovens, washing machines, microwaves, etc.) should be classified as 'out_of_scope'.

Here are some examples:
- "I need a water filter for my Samsung refrigerator" -> lookup
- "Will this ice maker work with my GE Profile fridge?" -> compatibility
- "How do I replace the heating element in my dishwasher?" -> install
- "My refrigerator isn't cooling properly" -> diagnose
- "I want to order a door gasket for my Whirlpool" -> order
- "Where is my order for the water filter?" -> status
- "How do I fix my microwave?" -> out_of_scope
- "I need parts for my washing machine" -> out_of_scope
- "Can you recommend a good dryer?" -> out_of_scope

Be strict about the out_of_scope category. If it's not clearly about refrigerator or dishwasher parts, classify it as out_of_scope.

User query: {query}

Based on the information above, classify this query into exactly one of these intents: lookup, compatibility, install, diagnose, order, status, out_of_scope.
Respond with ONLY the classified intent. No explanations or additional text.
"""

def call_deepseek_api(prompt: str) -> Dict[str, Any]:
    """
    Call the Deepseek API with the classification prompt.
    
    Args:
        prompt: The formatted prompt
        
    Returns:
        The API response as a dictionary
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,  # Low temperature for more deterministic outputs
        "max_tokens": 10     # We only need a single word response
    }
    
    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        print(f"Error calling Deepseek API: {response.status_code} - {response.text}")
        return {}
    
    return response.json()

def extract_intent_from_response(response: Dict[str, Any]) -> str:
    """
    Extract the intent from the Deepseek API response.
    
    Args:
        response: Deepseek API response
        
    Returns:
        The classified intent
    """
    try:
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Clean and validate the response
        content = content.strip().lower()
        
        # Map of valid intents
        valid_intents = {
            "lookup": "lookup",
            "compatibility": "compatibility",
            "install": "install",
            "diagnose": "diagnose",
            "order": "order", 
            "status": "status",
            "out_of_scope": "out_of_scope"
        }
        
        # Check if the response is a valid intent
        for intent_keyword in valid_intents:
            if intent_keyword in content:
                return valid_intents[intent_keyword]
        
        # If no valid intent is found, return the raw response
        return f"Unknown intent: {content}"
        
    except Exception as e:
        return f"Error extracting intent: {e}"

def classify_intent(query: str) -> str:
    """
    Classify user intent using Deepseek LLM.
    
    Args:
        query: User query text
        
    Returns:
        The classified intent
    """
    prompt = create_classification_prompt(query)
    response = call_deepseek_api(prompt)
    
    if not response:
        return "Error calling Deepseek API"
    
    return extract_intent_from_response(response)

def run_test_cases() -> None:
    """Run a set of predefined test cases to showcase the intent classification."""
    # Define test cases that might be ambiguous for rule-based classifier
    test_cases = [
        # Edge cases
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
        intent = classify_intent(case)
        print(f"\nQuery: '{case}'")
        print(f"Deepseek intent classification: {intent}")
        print("-" * 50)

def main():
    """Run the intent classification test based on command line arguments."""
    parser = argparse.ArgumentParser(description="Test Deepseek LLM intent classification")
    parser.add_argument("--query", "-q", type=str, help="Query to classify")
    parser.add_argument("--run-tests", "-t", action="store_true", help="Run predefined test cases")
    
    args = parser.parse_args()
    
    if args.run_tests:
        run_test_cases()
    elif args.query:
        intent = classify_intent(args.query)
        print(f"\nQuery: '{args.query}'")
        print(f"Deepseek intent classification: {intent}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 