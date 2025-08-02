#!/usr/bin/env python3
"""
Debug the exact error location in the webhook
"""
import requests
import json
import traceback

def debug_webhook():
    webhook_url = "https://bot-builder-k.replit.app/webhook/telegram/3"
    
    # Test with a more detailed error trace
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
            "text": "What are your TV mounting prices?"
        }
    }
    
    print("=== DETAILED WEBHOOK DEBUG ===")
    try:
        response = requests.post(
            webhook_url,
            json=sample_update,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Full Response Text: {response.text}")
        
        if response.status_code == 500:
            print("\n🔍 This is a server error - checking logs...")
            
    except Exception as e:
        print(f"Request Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_webhook()