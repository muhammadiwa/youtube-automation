"""Test notification API endpoints.

Usage:
    cd backend
    venv\Scripts\activate
    python -m scripts.test_notification_api
"""

import asyncio
import httpx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_notification_api():
    """Test notification API endpoints."""
    
    print("\n" + "=" * 60)
    print("Testing Notification API Endpoints")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Get notifications
        print("\n1. GET /notifications")
        try:
            response = await client.get(f"{base_url}/notifications", timeout=10.0)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Total: {data.get('total', 0)}")
                print(f"   Unread: {data.get('unread_count', 0)}")
                print(f"   Items: {len(data.get('items', []))}")
                if data.get('items'):
                    print(f"   First item: {data['items'][0].get('title', 'N/A')}")
            else:
                print(f"   Response: {response.text[:200]}")
        except httpx.ConnectError:
            print("   ❌ Cannot connect to backend. Make sure it's running.")
            return
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 2: Get unread count
        print("\n2. GET /notifications/unread/count")
        try:
            response = await client.get(f"{base_url}/notifications/unread/count", timeout=10.0)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Count: {data.get('count', 0)}")
            else:
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_notification_api())
