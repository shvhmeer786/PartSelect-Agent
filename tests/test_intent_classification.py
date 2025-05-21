#!/usr/bin/env python3
"""
Test script for DeepSeek intent classification.
This script tests the intent classification of the DeepSeekIntentClassifier
class by sending sample queries and comparing the results with expected intents.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Add parent directory to path to import DeepseekIntentClassifier
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the DeepseekIntentClassifier
try:
    from src.server.ws_server_simple import DeepseekIntentClassifier
    logger.info("Successfully imported DeepseekIntentClassifier")
except ImportError as e:
    logger.error(f"Error importing DeepseekIntentClassifier: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

def test_intent_classification():
    """Test the DeepSeek intent classification with sample queries."""
    # Create the intent classifier
    intent_classifier = DeepseekIntentClassifier()
    
    # Sample queries and expected intents
    test_cases = [
        # Basic queries
        ("I need a water filter for my refrigerator", "lookup"),
        ("How do I install a water filter?", "install"),
        ("Is this part compatible with my Samsung fridge?", "compatibility"),
        ("My ice maker isn't working properly, what could be wrong?", "diagnose"),
        ("Add this water filter to my cart", "cart"),
        ("What's the status of my order number ORD12345?", "order"),
        ("What's the weather like today?", "out_of_scope"),
        
        # More complex queries
        ("I have a Whirlpool refrigerator model WRF535SWHZ and need a replacement water filter", "lookup"),
        ("Can you show me detailed steps to replace the ice maker in my LG refrigerator?", "install"),
        ("Will the GE MWF water filter work with my GE GSS25GSHSS refrigerator?", "compatibility"),
        ("My dishwasher isn't draining properly after the cycle completes", "diagnose"),
        ("I'd like to purchase the water filter we discussed earlier", "cart"),
        ("I placed an order yesterday, can you tell me when it will arrive?", "order"),
        ("Who won the baseball game last night?", "out_of_scope"),
    ]
    
    # Test each query
    results = []
    for query, expected_intent in test_cases:
        logger.info(f"Testing query: '{query}'")
        logger.info(f"Expected intent: {expected_intent}")
        
        # Get the classified intent
        actual_intent = intent_classifier.classify_intent(query)
        
        # Check if the intent matches the expected intent
        match = actual_intent == expected_intent
        if match:
            logger.info(f"✅ Correct! Classified as: {actual_intent}")
        else:
            logger.warning(f"❌ Incorrect. Classified as: {actual_intent}, Expected: {expected_intent}")
        
        # Store the result
        results.append({
            "query": query,
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "match": match
        })
        
        # Add a separator for readability
        logger.info("-" * 80)
    
    # Print summary
    total = len(results)
    correct = sum(1 for r in results if r["match"])
    accuracy = (correct / total) * 100 if total > 0 else 0
    
    logger.info(f"\nTEST SUMMARY:")
    logger.info(f"Total test cases: {total}")
    logger.info(f"Correct classifications: {correct}")
    logger.info(f"Accuracy: {accuracy:.2f}%")
    
    if accuracy < 70:
        logger.warning("⚠️ Low accuracy. DeepSeek API key may be missing or invalid.")
        logger.warning("Using rule-based fallback classification.")
    
    return results

if __name__ == "__main__":
    logger.info("Starting DeepSeek intent classification test")
    test_intent_classification()
    logger.info("Test complete") 