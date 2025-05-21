#!/usr/bin/env python3
import asyncio
import json
import os
import sys
from dotenv import load_dotenv
from modules.tools import AsyncCatalogClient, AsyncDocsClient
from simple_langchain_tools import (
    SimpleProductLookupTool,
    SimpleCompatibilityTool,
    SimpleInstallationGuideTool,
    SimpleErrorDiagnosisTool
)

# Load environment variables
load_dotenv()

# Test the SimpleProductLookupTool
async def test_product_lookup_tool():
    print("\n===== Testing SimpleProductLookupTool =====")
    
    # Create async clients with mock data
    catalog_client = AsyncCatalogClient(mongodb_uri="mongodb://localhost:27017", use_mock=True)
    
    # Create the tool
    lookup_tool = SimpleProductLookupTool(catalog_client=catalog_client)
    
    # Test with a valid part number
    part_number = "PS11743427"  # Water Filter
    print(f"Looking up part: {part_number}")
    result = await lookup_tool._arun(part_number)
    
    # Parse and pretty print the result
    try:
        part_data = json.loads(result)
        print(f"Part found: {part_data.get('name')} - ${part_data.get('price')}")
        print(f"Description: {part_data.get('description')[:100]}...")
    except json.JSONDecodeError:
        print(f"Error parsing result: {result}")
    
    # Test with an invalid part number
    invalid_part = "NOTREAL123"
    print(f"\nLooking up invalid part: {invalid_part}")
    result = await lookup_tool._arun(invalid_part)
    print(f"Result: {result}")

# Test the SimpleCompatibilityTool
async def test_compatibility_tool():
    print("\n===== Testing SimpleCompatibilityTool =====")
    
    # Create async clients with mock data
    catalog_client = AsyncCatalogClient(mongodb_uri="mongodb://localhost:27017", use_mock=True)
    
    # Create the tool
    compat_tool = SimpleCompatibilityTool(catalog_client=catalog_client)
    
    # Test with a compatible part and model
    query = "PS11743427:WRS555SIHZ"  # Test valid compatibility
    print(f"Checking compatibility: {query}")
    result = await compat_tool._arun(query)
    print(f"Result: {result}")
    
    # Test with an incompatible part and model
    query = "PS11743427:UNKNOWN_MODEL"  # Test invalid compatibility
    print(f"\nChecking compatibility: {query}")
    result = await compat_tool._arun(query)
    print(f"Result: {result}")
    
    # Test with invalid query format
    query = "invalid_format"
    print(f"\nChecking with invalid format: {query}")
    result = await compat_tool._arun(query)
    print(f"Result: {result}")

# Test the SimpleInstallationGuideTool
async def test_installation_guide_tool():
    print("\n===== Testing SimpleInstallationGuideTool =====")
    
    # Create async clients with mock data
    docs_client = AsyncDocsClient(mongodb_uri="mongodb://localhost:27017", use_mock=True)
    
    # Create the tool
    install_tool = SimpleInstallationGuideTool(docs_client=docs_client)
    
    # Test with a valid part name and appliance type
    query = "Water Filter:refrigerator"
    print(f"Getting installation guide for: {query}")
    result = await install_tool._arun(query)
    print(f"Result preview (first 200 chars):\n{result[:200]}...\n")
    
    # Test with just a part name
    query = "Heating Element"
    print(f"Getting installation guide for: {query}")
    result = await install_tool._arun(query)
    print(f"Result preview (first 200 chars):\n{result[:200]}...\n")
    
    # Test with an invalid part name
    query = "NonExistentPart:dishwasher"
    print(f"Getting installation guide for: {query}")
    result = await install_tool._arun(query)
    print(f"Result: {result}")

# Test the SimpleErrorDiagnosisTool
async def test_error_diagnosis_tool():
    print("\n===== Testing SimpleErrorDiagnosisTool =====")
    
    # Create async clients with mock data
    catalog_client = AsyncCatalogClient(mongodb_uri="mongodb://localhost:27017", use_mock=True)
    docs_client = AsyncDocsClient(mongodb_uri="mongodb://localhost:27017", use_mock=True)
    
    # Create the tool
    diagnosis_tool = SimpleErrorDiagnosisTool(docs_client=docs_client, catalog_client=catalog_client)
    
    # Test with a valid problem and appliance type
    query = "not making ice:refrigerator"
    print(f"Diagnosing problem: {query}")
    result = await diagnosis_tool._arun(query)
    print(f"Result preview (first 200 chars):\n{result[:200]}...\n")
    
    # Test with just a problem
    query = "not draining"
    print(f"Diagnosing problem: {query}")
    result = await diagnosis_tool._arun(query)
    print(f"Result preview (first 200 chars):\n{result[:200]}...\n")
    
    # Test with an invalid problem
    query = "quantum flux capacitor malfunction:refrigerator"
    print(f"Diagnosing problem: {query}")
    result = await diagnosis_tool._arun(query)
    print(f"Result: {result}")

# Main test function
async def run_tests():
    print("Testing Simplified LangChain-Compatible Tools")
    print("============================================")
    
    # Run all tests
    await test_product_lookup_tool()
    await test_compatibility_tool()
    await test_installation_guide_tool()
    await test_error_diagnosis_tool()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_tests()) 