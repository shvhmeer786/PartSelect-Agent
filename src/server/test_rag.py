#!/usr/bin/env python3
"""
Test script for the PineconeRetriever implementation.
Tests both installation guide retrieval and error diagnosis capabilities.
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv
from modules.pinecone_retriever import PineconeRetriever

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_installation_guide_retrieval():
    """Test retrieving installation guides for various appliance parts."""
    logger.info("Testing installation guide retrieval...")
    
    # Initialize the PineconeRetriever
    retriever = PineconeRetriever(
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-west1-gcp",
        index_name="partselect"
    )
    
    # Test queries for installation guides
    test_queries = [
        "How do I install a water filter in my Samsung refrigerator?",
        "Steps to install an ice maker",
        "Installation instructions for dishwasher control board"
    ]
    
    for query in test_queries:
        logger.info(f"Testing query: '{query}'")
        
        # Try with and without appliance type
        appliance_type = None
        if "refrigerator" in query.lower() or "fridge" in query.lower():
            appliance_type = "refrigerator"
        elif "dishwasher" in query.lower():
            appliance_type = "dishwasher"
        
        result = await retriever.retrieve_and_format_for_llm(
            query=query,
            doc_type="installation",
            appliance_type=appliance_type,
            top_k=2
        )
        
        logger.info(f"Query: '{query}'\nAppliance Type: {appliance_type}\n")
        logger.info(f"Result:\n{result}\n{'-' * 80}\n")

async def test_error_diagnosis():
    """Test diagnosing errors for various appliance problems."""
    logger.info("Testing error diagnosis retrieval...")
    
    # Initialize the PineconeRetriever
    retriever = PineconeRetriever(
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-west1-gcp",
        index_name="partselect"
    )
    
    # Test queries for error diagnosis
    test_queries = [
        "My refrigerator ice maker is not working",
        "Dishwasher not draining water properly",
        "Refrigerator is making loud noises"
    ]
    
    for query in test_queries:
        logger.info(f"Testing query: '{query}'")
        
        # Try with and without appliance type
        appliance_type = None
        if "refrigerator" in query.lower() or "fridge" in query.lower():
            appliance_type = "refrigerator"
        elif "dishwasher" in query.lower():
            appliance_type = "dishwasher"
        
        result = await retriever.retrieve_and_format_for_llm(
            query=query,
            doc_type="troubleshooting",
            appliance_type=appliance_type,
            top_k=2
        )
        
        logger.info(f"Query: '{query}'\nAppliance Type: {appliance_type}\n")
        logger.info(f"Result:\n{result}\n{'-' * 80}\n")

async def main():
    """Run all tests."""
    logger.info("Starting PineconeRetriever tests...")
    
    # Test if the PINECONE_API_KEY is present
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        logger.warning("No PINECONE_API_KEY found in environment. Tests will use mock data.")
    else:
        logger.info("PINECONE_API_KEY found. Tests will use real Pinecone database if available.")
    
    # Run the tests
    await test_installation_guide_retrieval()
    await test_error_diagnosis()
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 