#!/usr/bin/env python3
"""
Test the new fresh webhook endpoint
"""
import requests
import json

def test_fresh_webhook():
    """Test the fresh webhook endpoint"""
    
    webhook_url = "https://bot-builder-k.replit.app/fresh/webhook"
    
    print("Testing fresh webhook...")
    
    # Test GET
    try:
        get_response = requests.get(webhook_url, timeout=15)
        print(f"GET test: {get_response.status_code} - {get_response.text}")
        
        if get_response.status_code == 200:
            print("✅ GET works!")
            
            # Test POST with actual Telegram message format
            test_message = {
                "message": {
                    "message_id": 1,
                    "from": {
                        "id": 123456789,
                        "is_bot": False,
                        "first_name": "Test"
                    },
                    "chat": {
                        "id": 123456789,
                        "type": "private"
                    },
                    "date": 1640995200,
                    "text": "Hello, how much does TV mounting cost?"
                }
            }
            
            post_response = requests.post(webhook_url, json=test_message, timeout=15)
            print(f"POST test: {post_response.status_code} - {post_response.text}")
            
            if post_response.status_code == 200:
                print("✅ POST works! Bot should be functioning now!")
                
                # Check webhook status with Telegram
                bot_token = "8301717846:AAFhv9n1qlizTvYytBWVeRZFCAgVqTgGflM"
                info_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
                info_response = requests.get(info_url)
                webhook_info = info_response.json()
                
                print(f"Telegram webhook status: {json.dumps(webhook_info, indent=2)}")
                
                return True
            else:
                print("❌ POST failed")
        else:
            print("❌ GET failed")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    if test_fresh_webhook():
        print("\n🎉 BOT IS WORKING!")
        print("You can now message @test2_512_bot on Telegram!")
    else:
        print("\n❌ Bot test failed")