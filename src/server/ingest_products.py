#!/usr/bin/env python3
"""
CLI script to ingest product data from PartSelect.ca into MongoDB.
Reads a list of part numbers from a file and scrapes details for each part.
"""

import argparse
import os
import sys
import logging
from typing import List
from dotenv import load_dotenv

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server.modules.tools import PartSelectScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def read_part_numbers(file_path: str) -> List[str]:
    """
    Read part numbers from a file, one per line.
    
    Args:
        file_path: Path to the file containing part numbers
        
    Returns:
        List of part numbers
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return []
    
    try:
        with open(file_path, 'r') as file:
            # Strip whitespace and filter out empty lines
            part_numbers = [line.strip() for line in file if line.strip()]
        
        logger.info(f"Read {len(part_numbers)} part numbers from {file_path}")
        return part_numbers
    
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

def main():
    """
    Main entry point for the script.
    """
    # Load environment variables
    load_dotenv()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Ingest PartSelect.ca product data into MongoDB")
    parser.add_argument(
        "-f", "--file", 
        required=True, 
        help="Path to file containing part numbers (one per line)"
    )
    parser.add_argument(
        "-m", "--mongodb-uri", 
        default=os.environ.get("MONGODB_URI", "mongodb://localhost:27017"),
        help="MongoDB connection URI"
    )
    parser.add_argument(
        "-d", "--database", 
        default=os.environ.get("MONGODB_DATABASE", "partselect"),
        help="MongoDB database name"
    )
    parser.add_argument(
        "-c", "--collection", 
        default=os.environ.get("MONGODB_COLLECTION", "parts"),
        help="MongoDB collection name"
    )
    
    args = parser.parse_args()
    
    # Read part numbers from file
    part_numbers = read_part_numbers(args.file)
    
    if not part_numbers:
        logger.error("No part numbers found. Exiting.")
        sys.exit(1)
    
    # Initialize the scraper
    try:
        scraper = PartSelectScraper(
            mongodb_uri=args.mongodb_uri,
            database_name=args.database,
            collection_name=args.collection
        )
    except Exception as e:
        logger.error(f"Failed to initialize scraper: {e}")
        sys.exit(1)
    
    # Scrape and ingest part data
    logger.info(f"Starting ingestion of {len(part_numbers)} parts...")
    results = scraper.bulk_upsert_parts(part_numbers)
    
    # Report results
    logger.info("Ingestion completed:")
    logger.info(f"  Successfully processed: {results['success']}")
    logger.info(f"  Failed to process: {results['failure']}")
    
    if results['failure'] > 0:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main() 