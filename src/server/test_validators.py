#!/usr/bin/env python3
"""
Test script for validator functions in validators.py
"""

import sys
import os
from typing import List, Tuple, Dict

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from modules.validators import is_in_scope, extract_intent

def test_is_in_scope():
    """Test the is_in_scope function with various queries."""
    # Format: (query, expected_result)
    test_cases: List[Tuple[str, bool]] = [
        # In-scope queries (refrigerator)
        ("I need a new water filter for my refrigerator", True),
        ("My fridge isn't cooling properly", True),
        ("Where can I find a replacement ice maker for GE Profile?", True),
        ("How do I replace the compressor in my Samsung fridge?", True),
        ("Whirlpool freezer door gasket", True),
        
        # In-scope queries (dishwasher)
        ("My Bosch dishwasher isn't draining", True),
        ("I need a new spray arm for my KitchenAid", True),
        ("How do I replace the heating element in a dishwasher?", True),
        ("My dishwasher detergent dispenser is broken", True),
        ("Maytag MDB4949SDZ parts", True),
        
        # Out-of-scope queries
        ("I need a new heating element for my oven", False),
        ("My washing machine is making a weird noise", False),
        ("How do I replace the filter in my vacuum cleaner?", False),
        ("My microwave stopped working", False),
        ("I need a replacement part for my air conditioner", False),
        
        # Edge cases
        ("GDF520PGJWW", True),  # Just a model number for a dishwasher
        ("I need a part", False),  # Too vague
        ("Whirlpool appliance", True),  # Brand but vague appliance
        ("My LG isn't working", False),  # Brand but no appliance type
        ("Ice maker not working in my refrigerator but also my oven is broken", True)  # Mixed but has in-scope
    ]
    
    results = []
    for query, expected in test_cases:
        actual = is_in_scope(query)
        passed = actual == expected
        results.append((query, expected, actual, passed))
        
    # Print results
    print("\n===== TESTING is_in_scope() =====")
    print(f"Passed: {sum(1 for _, _, _, passed in results if passed)}/{len(results)}")
    
    # Print failures for debugging
    failures = [(query, expected, actual) for query, expected, actual, passed in results if not passed]
    if failures:
        print("\nFailures:")
        for query, expected, actual in failures:
            print(f"Query: '{query}'")
            print(f"  Expected: {expected}, Got: {actual}")
            print(f"  Query lowercase: '{query.lower()}'") # Print lowercase version for exact matching
    
    return results

def test_extract_intent():
    """Test the extract_intent function with various queries."""
    # Format: (query, expected_intent)
    test_cases: List[Tuple[str, str]] = [
        # Lookup intent
        ("I need a water filter for my Samsung refrigerator", "lookup"),
        ("Where can I find a door gasket for my Whirlpool fridge?", "lookup"),
        ("Show me dishwasher spray arms", "lookup"),
        ("What's the price of a GE ice maker?", "lookup"),
        
        # Compatibility intent
        ("Will this water filter fit my LG refrigerator?", "compatibility"),
        ("Is this drain pump compatible with Maytag MDB4949SDZ?", "compatibility"),
        ("Does this ice maker work with my GE Profile?", "compatibility"),
        ("Need a door gasket that fits Whirlpool WRF535SWHZ", "compatibility"),
        
        # Install intent
        ("How do I install a new water filter?", "install"),
        ("Instructions for replacing dishwasher heating element", "install"),
        ("Step by step guide to replace refrigerator door gasket", "install"),
        ("Need help installing ice maker in my GE fridge", "install"),
        
        # Diagnose intent
        ("My refrigerator isn't cooling properly", "diagnose"),
        ("Dishwasher not draining - how to fix?", "diagnose"),
        ("Ice maker stopped working in my Samsung", "diagnose"),
        ("Troubleshooting guide for Bosch dishwasher that won't start", "diagnose"),
        
        # Order intent
        ("I want to order a water filter for my fridge", "order"),
        ("Add dishwasher heating element to my cart", "order"),
        ("Purchase replacement ice maker", "order"),
        ("Shipping options for refrigerator parts", "order"),
        
        # Status intent
        ("Where is my order for the refrigerator water filter?", "status"),
        ("Track my dishwasher part order", "status"),
        ("When will my ice maker be delivered?", "status"),
        ("Order status for my Whirlpool part", "status"),
        
        # Out of scope intent
        ("How do I fix my microwave?", "out_of_scope"),
        ("Need parts for my washing machine", "out_of_scope"),
        ("Air conditioner installation guide", "out_of_scope"),
        ("My oven isn't heating up", "out_of_scope"),
        
        # Mixed/ambiguous intents (should pick the one with more keyword matches)
        ("I need to find and install a water filter", "lookup"),  # Both lookup and install, but more lookup keywords
        ("Is this part compatible and how do I install it?", "install"),  # Both compatibility and install
        ("My dishwasher isn't working, I need to buy a new pump", "diagnose"),  # Both diagnose and order
    ]
    
    results = []
    for query, expected in test_cases:
        actual = extract_intent(query)
        passed = actual == expected
        results.append((query, expected, actual, passed))
        
    # Print results
    print("\n===== TESTING extract_intent() =====")
    print(f"Passed: {sum(1 for _, _, _, passed in results if passed)}/{len(results)}")
    
    # Print failures for debugging
    failures = [(query, expected, actual) for query, expected, actual, passed in results if not passed]
    if failures:
        print("\nFailures:")
        for query, expected, actual in failures:
            print(f"Query: '{query}'")
            print(f"  Expected: {expected}, Got: {actual}")
            print(f"  Query lowercase: '{query.lower()}'") # Print lowercase version for exact matching
    
    return results

if __name__ == "__main__":
    scope_results = test_is_in_scope()
    intent_results = test_extract_intent()
    
    # Overall summary
    total_tests = len(scope_results) + len(intent_results)
    total_passed = (sum(1 for _, _, _, passed in scope_results if passed) + 
                    sum(1 for _, _, _, passed in intent_results if passed))
    
    print(f"\n===== OVERALL RESULTS =====")
    print(f"Total: {total_passed}/{total_tests} tests passed ({total_passed/total_tests:.1%})")
    
    # Exit with appropriate status code
    sys.exit(0 if total_passed == total_tests else 1) 