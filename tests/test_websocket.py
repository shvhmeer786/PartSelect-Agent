#!/usr/bin/env python3
"""
Test client for WebSocket chat server with DeepSeek integration.
"""

import asyncio
import json
import sys
import logging
from websockets.client import connect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def test_client():
    """Run the test client to connect to the WebSocket server."""
    logger.info("Starting WebSocket test client...")
    
    uri = "ws://localhost:9000/chat"
    async with connect(uri) as websocket:
        logger.info(f"Connected to {uri}")
        
        # Test messages for different intents
        test_messages = [
            "I need a water filter for my refrigerator", # lookup intent
            "How do I install the water filter?", # install intent
            "Is this filter compatible with my Samsung fridge?", # compatibility intent
            "My ice maker isn't working properly", # diagnose intent
            "My dishwasher isn't draining properly", # diagnose intent (different problem)
            "Add the water filter to my cart", # cart intent (add)
            "Show me what's in my cart", # cart intent (view)
            "What's the status of my order ORD123456?", # order intent
            "What's the weather like today?", # out_of_scope intent
        ]
        
        for msg in test_messages:
            # Send message
            logger.info(f"Sending: {msg}")
            await websocket.send(msg)
            
            # Receive and process response
            response = await websocket.recv()
            logger.info(f"Received response: {response}")
            
            # Parse JSON response
            try:
                parsed = json.loads(response)
                
                # Print formatted response details
                print(f"\n{'='*60}")
                print(f"QUERY: {msg}")
                print(f"INTENT DETECTED: {parsed.get('tool_used', 'unknown')}")
                
                # Process response data based on intent
                data = parsed.get('data', {})
                if parsed.get('tool_used') == 'product_lookup_tool':
                    print(f"PRODUCT FOUND:")
                    print(f"  Name: {data.get('name')}")
                    print(f"  Part Number: {data.get('partNumber')}")
                    print(f"  Price: ${data.get('price')}")
                    print(f"  Image URL: {data.get('imageUrl')}")
                
                elif parsed.get('tool_used') == 'installation_guide_tool':
                    print(f"INSTALLATION GUIDE:")
                    print(f"  {parsed.get('message')}")
                
                elif parsed.get('tool_used') == 'compatibility_tool':
                    print(f"COMPATIBILITY INFORMATION:")
                    print(f"  Part: {data.get('name')} ({data.get('part_number')})")
                    print(f"  Compatible with:")
                    for model in data.get('compatible_models', []):
                        print(f"    - {model}")
                    print(f"  Not compatible with:")
                    for model in data.get('not_compatible', []):
                        print(f"    - {model}")
                
                elif parsed.get('tool_used') == 'diagnose_tool':
                    print(f"DIAGNOSTIC INFORMATION:")
                    print(f"  Problem: {data.get('problem')}")
                    print(f"  Possible causes:")
                    for cause in data.get('possible_causes', []):
                        print(f"    - {cause}")
                    print(f"  Recommended parts:")
                    for part in data.get('recommended_parts', []):
                        print(f"    - {part.get('name')} (${part.get('price')}, PN: {part.get('part_number')})")
                
                elif parsed.get('tool_used') == 'cart_tool':
                    print(f"CART OPERATION:")
                    print(f"  Status: {data.get('status')}")
                    print(f"  Message: {data.get('message')}")
                    
                    if 'items' in data:
                        print(f"  Items in cart: {len(data.get('items', []))}")
                        if data.get('items'):
                            for i, item in enumerate(data.get('items', []), 1):
                                print(f"    {i}. {item.get('name')} - ${item.get('price'):.2f} x {item.get('quantity')}")
                        print(f"  Total price: ${data.get('total_price', 0):.2f}")
                    elif 'part' in data:
                        print(f"  Added: {data.get('part', {}).get('name')}")
                        print(f"  Price: ${data.get('part', {}).get('price', 0):.2f}")
                
                elif parsed.get('tool_used') == 'order_status_tool':
                    print(f"ORDER STATUS:")
                    print(f"  Order Number: {data.get('order_number')}")
                    print(f"  Date: {data.get('date')}")
                    print(f"  Status: {data.get('status')}")
                    if 'tracking_number' in data:
                        print(f"  Tracking: {data.get('tracking_number')} ({data.get('carrier')})")
                        print(f"  Est. Delivery: {data.get('estimated_delivery')}")
                
                elif parsed.get('tool_used') == 'out_of_scope':
                    print(f"OUT OF SCOPE QUERY")
                    print(f"  Response: {parsed.get('message')}")
                
                # Print suggested actions
                suggested = parsed.get('suggested_actions', [])
                if suggested:
                    print("\nSUGGESTED ACTIONS:")
                    for i, action in enumerate(suggested, 1):
                        print(f"  {i}. {action}")
                
                print(f"{'='*60}\n")
            
            except json.JSONDecodeError:
                logger.error(f"Failed to parse response as JSON: {response}")
            
            # Brief pause between messages
            await asyncio.sleep(2)

if __name__ == "__main__":
    # Run the test client
    asyncio.run(test_client()) 