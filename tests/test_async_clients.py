#!/usr/bin/env python3
"""
Test script for the asynchronous MongoDB clients.
"""

import sys
import os
import asyncio
from pprint import pprint

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'server'))

from modules.tools import AsyncCatalogClient, AsyncDocsClient

async def test_catalog_client():
    """Test the functionality of the AsyncCatalogClient using mock data."""
    # Initialize client with mock data
    client = AsyncCatalogClient("mongodb://localhost:27017", use_mock=True)
    
    print("\n===== TESTING ASYNC CATALOG CLIENT =====")
    
    # Test getting part by number
    part = await client.get_part("PS11743427")  # Dishwasher Drain Pump
    print("\nFound part by number:")
    if part:
        print(f"  Part: {part['name']} ({part['partNumber']})")
        print(f"  Price: ${part['price']}")
        print(f"  Compatible with {len(part['compatibleModels'])} models")
    else:
        print("  Part not found!")
    
    # Test searching parts with filters
    search_results = await client.search_parts("water", appliance_type="refrigerator", limit=3)
    print("\nSearch results for 'water' (refrigerator only):")
    for part in search_results:
        print(f"  {part['name']} (${part['price']})")
    
    # Test finding parts by model
    model_parts = await client.find_by_model("WDT750SAHZ", limit=3)
    print("\nParts compatible with WDT750SAHZ dishwasher (limited to 3):")
    for part in model_parts:
        print(f"  {part['name']} ({part['partNumber']})")
    
    # Test compatibility check
    is_compatible = await client.check_compatibility("PS11743427", "WDT750SAHZ")
    print(f"\nIs Dishwasher Drain Pump compatible with WDT750SAHZ? {is_compatible}")
    
    # Test getting popular parts
    popular_parts = await client.get_popular_parts("dishwasher", 3)
    print("\nPopular dishwasher parts:")
    for part in popular_parts:
        print(f"  {part['name']} (${part['price']})")

async def test_docs_client():
    """Test the functionality of the AsyncDocsClient using mock data."""
    # Initialize client with mock data
    client = AsyncDocsClient("mongodb://localhost:27017", use_mock=True)
    
    print("\n===== TESTING ASYNC DOCS CLIENT =====")
    
    # Test getting document by title
    doc = await client.get_doc_by_title("How to Replace a Dishwasher Door Seal")
    print("\nFound document by title:")
    if doc:
        print(f"  Title: {doc['title']}")
        print(f"  Type: {doc['type']}")
        print(f"  Appliance: {doc['applianceType']}")
    else:
        print("  Document not found!")
    
    # Test searching docs with filters
    search_results = await client.search_docs("temperature", doc_type="troubleshooting", appliance_type="refrigerator")
    print("\nSearch results for 'temperature' (refrigerator troubleshooting):")
    for doc in search_results:
        print(f"  {doc['title']}")
    
    # Test getting installation docs
    installation_docs = await client.get_installation_docs(part_name="heating element", appliance_type="dishwasher")
    print("\nInstallation docs for 'heating element' (dishwasher):")
    for doc in installation_docs:
        print(f"  {doc['title']}")
    
    # Test getting troubleshooting docs
    troubleshooting_docs = await client.get_troubleshooting_docs(problem="ice maker", appliance_type="refrigerator")
    print("\nTroubleshooting docs for 'ice maker' (refrigerator):")
    for doc in troubleshooting_docs:
        print(f"  {doc['title']}")
    
    # Test getting repair steps
    repair_steps = await client.get_repair_steps("Ice Maker", "refrigerator")
    print("\nRepair steps for Refrigerator Ice Maker:")
    for step in repair_steps[:5]:  # Show first 5 steps
        print(f"  {step}")
    
    # Test getting safety notes
    safety_notes = await client.get_safety_notes()
    print("\nSafety notes for appliance repair:")
    for note in safety_notes[:3]:  # Show first 3 notes
        print(f"  {note}")

async def main():
    """Run all tests."""
    await test_catalog_client()
    await test_docs_client()
    print("\nAll async client tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 