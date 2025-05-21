#!/usr/bin/env python3
"""
CLI script to crawl PartSelect.ca documentation pages and store them in MongoDB.
Takes a list of doc URLs or patterns and crawls them to extract documentation content.
"""

import argparse
import os
import sys
import logging
import json
from typing import List
from dotenv import load_dotenv

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server.modules.tools import DocScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def read_urls_from_file(file_path: str) -> List[str]:
    """
    Read URLs from a file, one per line.
    
    Args:
        file_path: Path to the file containing URLs
        
    Returns:
        List of URLs
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return []
    
    try:
        with open(file_path, 'r') as file:
            # Strip whitespace and filter out empty lines and comments
            urls = [line.strip() for line in file if line.strip() and not line.strip().startswith('#')]
        
        logger.info(f"Read {len(urls)} URLs from {file_path}")
        return urls
    
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

def get_predefined_patterns() -> List[str]:
    """
    Get a list of predefined URL patterns for common documentation sections.
    
    Returns:
        List of URL patterns
    """
    return [
        # Installation guides
        "https://www.partselect.ca/installation/",
        "https://www.partselect.ca/repair-guide/",
        "https://www.partselect.ca/DIY/",
        
        # Troubleshooting guides
        "https://www.partselect.ca/troubleshooting/",
        "https://www.partselect.ca/repair-help/",
        "https://www.partselect.ca/symptom/",
        
        # Maintenance guides
        "https://www.partselect.ca/maintenance/",
        "https://www.partselect.ca/care-guide/"
    ]

def main():
    """
    Main entry point for the script.
    """
    # Load environment variables
    load_dotenv()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Crawl PartSelect.ca documentation and store in MongoDB")
    parser.add_argument(
        "-f", "--file", 
        help="Path to file containing URLs (one per line)"
    )
    parser.add_argument(
        "-u", "--urls",
        nargs='+',
        help="One or more URLs to process"
    )
    parser.add_argument(
        "--predefined",
        action="store_true",
        help="Use predefined URL patterns for common documentation sections"
    )
    parser.add_argument(
        "-m", "--max-per-url", 
        type=int,
        default=20,
        help="Maximum number of documents to process per URL pattern"
    )
    parser.add_argument(
        "--mongodb-uri", 
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
        default=os.environ.get("MONGODB_COLLECTION", "docs"),
        help="MongoDB collection name"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set log level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Collect URLs to process
    urls_to_process = []
    
    if args.file:
        urls_to_process.extend(read_urls_from_file(args.file))
    
    if args.urls:
        urls_to_process.extend(args.urls)
    
    if args.predefined:
        urls_to_process.extend(get_predefined_patterns())
    
    if not urls_to_process:
        logger.error("No URLs provided. Use --file, --urls, or --predefined to specify URLs to process.")
        parser.print_help()
        sys.exit(1)
    
    # Initialize the scraper
    try:
        scraper = DocScraper(
            mongodb_uri=args.mongodb_uri,
            database_name=args.database,
            collection_name=args.collection
        )
    except Exception as e:
        logger.error(f"Failed to initialize scraper: {e}")
        sys.exit(1)
    
    # Process URLs
    logger.info(f"Starting crawl of {len(urls_to_process)} URL patterns (max {args.max_per_url} docs per pattern)...")
    results = scraper.bulk_process_urls(urls_to_process, args.max_per_url)
    
    # Report results
    logger.info("Crawl completed:")
    logger.info(f"  Successfully processed: {results['success']}")
    logger.info(f"  Failed to process: {results['failure']}")
    logger.info(f"  Skipped (already visited): {results['skipped']}")
    
    if results['success'] == 0 and results['failure'] > 0:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main() 