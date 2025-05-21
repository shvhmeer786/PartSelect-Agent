#!/usr/bin/env python3
"""
Test script for the enhanced MockDataProvider with additional parts and documentation.
"""

import sys
import os
from pprint import pprint

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'server'))

from modules.mock_data import MockDataProvider

def test_part_catalog():
    """Test the part catalog functionality of the MockDataProvider."""
    provider = MockDataProvider()
    
    print("\n===== TESTING PART CATALOG =====")
    
    # Test getting all parts
    all_parts = provider.get_all_parts()
    print(f"Total parts in catalog: {len(all_parts)}")
    
    # Test getting part by number
    part = provider.get_part_by_number("PS11743427")  # Dishwasher Drain Pump
    print("\nFound part by number:")
    if part:
        print(f"  Part: {part['name']} ({part['partNumber']})")
        print(f"  Price: ${part['price']}")
        print(f"  Compatible with {len(part['compatibleModels'])} models")
    else:
        print("  Part not found!")
    
    # Test searching parts
    search_results = provider.search_parts("water filter", appliance_type="refrigerator", limit=3)
    print("\nSearch results for 'water filter' (refrigerator):")
    for part in search_results:
        print(f"  {part['name']} (${part['price']})")
    
    # Test finding compatible parts
    compatible_parts = provider.find_compatible_parts("WDT750SAHZ", limit=5)  # Dishwasher model
    print("\nParts compatible with WDT750SAHZ dishwasher:")
    for part in compatible_parts:
        print(f"  {part['name']} ({part['partNumber']})")
    
    # Test part compatibility check
    is_compatible = provider.is_part_compatible("PS11743427", "WDT750SAHZ")
    print(f"\nIs Dishwasher Drain Pump compatible with WDT750SAHZ? {is_compatible}")
    
    # Test getting popular parts
    popular_fridge_parts = provider.get_popular_parts("refrigerator", limit=3)
    print("\nPopular refrigerator parts:")
    for part in popular_fridge_parts:
        print(f"  {part['name']} (${part['price']})")

def test_documentation():
    """Test the documentation functionality of the MockDataProvider."""
    provider = MockDataProvider()
    
    print("\n===== TESTING DOCUMENTATION =====")
    
    # Test getting doc by title
    doc = provider.get_doc_by_title("How to Replace a Refrigerator Water Filter")
    print("\nFound document by title:")
    if doc:
        print(f"  Title: {doc['title']}")
        print(f"  Type: {doc['type']}")
        print(f"  Appliance: {doc['applianceType']}")
        print(f"  Content length: {len(doc['content'])} characters")
    else:
        print("  Document not found!")
    
    # Test searching docs
    search_results = provider.search_docs("ice maker", doc_type="troubleshooting", limit=2)
    print("\nSearch results for 'ice maker' (troubleshooting):")
    for doc in search_results:
        print(f"  {doc['title']} ({doc['applianceType']})")
    
    # Test getting installation docs
    installation_docs = provider.get_installation_docs(part_name="door seal", appliance_type="dishwasher")
    print("\nInstallation docs for 'door seal' (dishwasher):")
    for doc in installation_docs:
        print(f"  {doc['title']}")
    
    # Test getting troubleshooting docs
    troubleshooting_docs = provider.get_troubleshooting_docs(problem="draining", appliance_type="dishwasher")
    print("\nTroubleshooting docs for 'draining' (dishwasher):")
    for doc in troubleshooting_docs:
        print(f"  {doc['title']}")
    
    # Test getting repair steps
    repair_steps = provider.get_repair_steps("Heating Element", "dishwasher")
    print("\nRepair steps for Dishwasher Heating Element:")
    for step in repair_steps[:5]:  # Show first 5 steps
        print(f"  {step}")
    
    # Test getting safety notes
    safety_notes = provider.get_safety_notes()
    print("\nSafety notes for appliance repair:")
    for note in safety_notes:
        print(f"  {note}")

if __name__ == "__main__":
    test_part_catalog()
    test_documentation()
    print("\nAll tests completed successfully!") 