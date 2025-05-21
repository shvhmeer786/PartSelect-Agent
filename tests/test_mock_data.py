#!/usr/bin/env python3

import logging
from src.server.modules.mock_data import MockDataProvider

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Initialize the mock data provider
    mock_data = MockDataProvider()
    
    # Test part lookup by part number
    part_number = "PS11752778"
    logger.info(f"Looking up part by number: {part_number}")
    part = mock_data.find_part_by_number(part_number)
    if part:
        logger.info(f"Found part: {part['name']} (${part['price']})")
    else:
        logger.info(f"Part not found: {part_number}")
    
    # Test part search by query
    search_query = "water valve"
    logger.info(f"Searching for parts with query: '{search_query}'")
    search_results = mock_data.search_parts(search_query)
    logger.info(f"Found {len(search_results)} results:")
    for i, result in enumerate(search_results):
        logger.info(f"  {i+1}. {result['partNumber']} - {result['name']} (${result['price']})")
    
    # Test compatibility check
    model_number = "WDT780SAEM1"
    logger.info(f"Checking if {part_number} is compatible with {model_number}")
    is_compatible = mock_data.check_compatibility(part_number, model_number)
    logger.info(f"Compatible: {is_compatible}")
    
    # Test documentation search
    doc_query = "ice maker"
    logger.info(f"Searching docs with query: '{doc_query}'")
    doc_results = mock_data.search_docs(doc_query)
    logger.info(f"Found {len(doc_results)} documentation entries:")
    for i, doc in enumerate(doc_results):
        logger.info(f"  {i+1}. {doc['title']} ({doc['type']})")
        
    # Test finding docs by part number
    docs_part_number = "PS11722167"
    logger.info(f"Finding docs for part number: {docs_part_number}")
    part_docs = mock_data.find_docs_by_part_number(docs_part_number)
    logger.info(f"Found {len(part_docs)} documentation entries:")
    for i, doc in enumerate(part_docs):
        logger.info(f"  {i+1}. {doc['title']} ({doc['type']})")
        if i == 0 and len(doc['content']['steps']) > 0:
            # Show some steps from the first doc
            logger.info("    Example steps:")
            for step in doc['content']['steps'][:3]:
                logger.info(f"    - {step}")

if __name__ == "__main__":
    main() 