#!/usr/bin/env python3

import requests
import time
import random

def test_product_access():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/search?q=refrigerator+parts+PS11752778+partselect',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'Cookie': 'visitor_id=1234567890'  # Adding a fake cookie
    }

    # A few test URLs to try
    test_urls = [
        'https://www.partselect.ca/PS11752778-Whirlpool-WP8268383R-Dispenser-Module.htm',
        'https://www.partselect.ca/PS11746337-Whirlpool-WP2198202-Water-Inlet-Valve.htm',
        'https://www.partselect.ca/search?query=PS11746337'
    ]
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        try:
            r = requests.get(url, headers=headers, timeout=15)
            print(f'Status code: {r.status_code}')
            
            if r.status_code == 200:
                print("Success! We can access this URL.")
                # Print a small part of the content to verify
                print(r.text[:300])
            else:
                print(f"Failed to access. Response: {r.text[:200]}")
                
        except Exception as e:
            print(f"Error accessing URL: {e}")
        
        # Add a delay between requests
        time.sleep(random.uniform(2.0, 4.0))

if __name__ == "__main__":
    test_product_access() 