#!/usr/bin/env python3

import requests
import random

def test_access():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }

    r = requests.get('https://www.partselect.ca', headers=headers)
    print(f'Status code: {r.status_code}')
    
    if r.status_code == 200:
        print("Success! We can access the website.")
        # Print a small part of the content to verify
        print(r.text[:500])
    else:
        print(f"Failed to access the website. Response: {r.text[:200]}")

if __name__ == "__main__":
    test_access() 