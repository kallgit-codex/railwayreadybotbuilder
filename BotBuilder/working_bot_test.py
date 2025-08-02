#!/usr/bin/env python3
"""
Direct bot test to verify functionality outside the main app
"""
import requests
import json

def test_working_bot():
    """Test the Telegram bot directly using API calls"""
    
    # Bot token for @test2_512_bot
    bot_token = "8301717846:AAFhv9n1qlizTvYytBWVeRZFCAgVqTgGflM"
    
    # Test message
    test_message = {
        "update_id": 123456,
        "message": {
            "message_id": 789,
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
            "text": "Hello bot, how are you?"
        }
    }
    
    # Send to WORKING webhook
    webhook_url = "https://bot-builder-k.replit.app/bot/webhook"
    
    print("=== TESTING BOT WITH REAL MESSAGE ===")
    print(f"URL: {webhook_url}")
    print(f"Message: {test_message['message']['text']}")
    
    try:
        response = requests.post(
            webhook_url,
            json=test_message,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Bot webhook is working!")
        else:
            print("❌ Bot webhook failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_working_bot()