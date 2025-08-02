#!/usr/bin/env python3
"""
Final bot registration with emergency webhook
"""
import requests
import time

def test_and_register():
    """Test emergency webhook and register with Telegram"""
    
    bot_token = "8301717846:AAFhv9n1qlizTvYytBWVeRZFCAgVqTgGflM"
    webhook_url = "https://bot-builder-k.replit.app/emergency/bot"
    
    print("Testing emergency webhook...")
    
    # Test GET
    try:
        get_response = requests.get(webhook_url, timeout=15)
        print(f"GET test: {get_response.status_code} - {get_response.text}")
        
        if get_response.status_code == 200:
            print("✅ GET works! Testing POST...")
            
            # Test POST
            test_data = {
                "message": {
                    "text": "test message",
                    "chat": {"id": 12345},
                    "from": {"id": 12345}
                }
            }
            
            post_response = requests.post(webhook_url, json=test_data, timeout=15)
            print(f"POST test: {post_response.status_code} - {post_response.text}")
            
            if post_response.status_code == 200:
                print("✅ POST works! Registering with Telegram...")
                
                # Delete existing webhook
                delete_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
                requests.post(delete_url)
                print("Deleted old webhook")
                
                time.sleep(3)
                
                # Register new webhook
                set_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
                webhook_data = {
                    "url": webhook_url,
                    "max_connections": 40,
                    "allowed_updates": ["message"]
                }
                
                response = requests.post(set_url, json=webhook_data)
                result = response.json()
                
                print(f"Registration result: {result}")
                
                if result.get('ok'):
                    print("🎉 BOT IS NOW WORKING!")
                    print(f"Webhook registered: {webhook_url}")
                    
                    # Get webhook info
                    info_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
                    info = requests.get(info_url).json()
                    print(f"Webhook info: {info}")
                    
                    print("\n✅ You can now message @test2_512_bot on Telegram!")
                    return True
                else:
                    print(f"❌ Registration failed: {result}")
            else:
                print("❌ POST failed")
        else:
            print("❌ GET failed")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    test_and_register()