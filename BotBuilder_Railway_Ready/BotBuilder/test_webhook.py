#!/usr/bin/env python3
"""
Test the webhook endpoint directly to see if it's working
"""
import requests
import json

def test_webhook():
    webhook_url = "https://bot-builder-k.replit.app/webhook/telegram/3"
    
    # Test GET request first
    print("=== TESTING GET REQUEST ===")
    try:
        response = requests.get(webhook_url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"GET Error: {e}")
    
    # Test POST request with sample Telegram update
    print("\n=== TESTING POST REQUEST ===")
    sample_update = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 12345,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser"
            },
            "chat": {
                "id": 12345,
                "first_name": "Test",
                "username": "testuser",
                "type": "private"
            },
            "date": 1640995200,
            "text": "Hello bot test message"
        }
    }
    
    try:
        response = requests.post(
            webhook_url, 
            json=sample_update,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook endpoint is working!")
        else:
            print(f"❌ Webhook returned error: {response.status_code}")
            
    except Exception as e:
        print(f"POST Error: {e}")

if __name__ == "__main__":
    test_webhook()