#!/usr/bin/env python3
"""
Register the working webhook with Telegram - Final Solution
"""
import requests
import time

def register_final_webhook():
    """Register the working webhook URL with Telegram"""
    
    bot_token = "8301717846:AAFhv9n1qlizTvYytBWVeRZFCAgVqTgGflM"
    
    # Test different webhook URLs to find one that works
    webhook_urls = [
        "https://bot-builder-k.replit.app/working",
        "https://bot-builder-k.replit.app/test/webhook", 
        "https://bot-builder-k.replit.app/bot/webhook"
    ]
    
    for webhook_url in webhook_urls:
        print(f"\n=== TESTING WEBHOOK URL: {webhook_url} ===")
        
        # Test GET request first
        try:
            test_response = requests.get(webhook_url, timeout=10)
            print(f"GET test: {test_response.status_code} - {test_response.text[:100]}")
            
            if test_response.status_code == 200:
                print(f"✅ GET request works for {webhook_url}")
                
                # Test POST request
                test_data = {
                    "message": {
                        "text": "test",
                        "chat": {"id": 12345},
                        "from": {"id": 12345}
                    }
                }
                
                post_response = requests.post(webhook_url, json=test_data, timeout=10)
                print(f"POST test: {post_response.status_code} - {post_response.text[:100]}")
                
                if post_response.status_code == 200:
                    print(f"✅ POST request works for {webhook_url}")
                    
                    # Register this working webhook
                    print(f"Registering {webhook_url} with Telegram...")
                    
                    # Delete existing webhook first
                    delete_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
                    delete_response = requests.post(delete_url)
                    print(f"Delete response: {delete_response.json()}")
                    
                    time.sleep(2)
                    
                    # Set new webhook
                    set_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
                    webhook_data = {
                        "url": webhook_url,
                        "max_connections": 40,
                        "allowed_updates": ["message"]
                    }
                    
                    response = requests.post(set_url, json=webhook_data)
                    result = response.json()
                    
                    print(f"Registration response: {result}")
                    
                    if result.get('ok'):
                        print("✅ Webhook registered successfully!")
                        
                        # Verify webhook info
                        info_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
                        info_response = requests.get(info_url)
                        info_result = info_response.json()
                        
                        print(f"Webhook info: {info_result}")
                        return True
                    else:
                        print(f"❌ Registration failed: {result.get('description')}")
                else:
                    print(f"❌ POST request failed for {webhook_url}")
            else:
                print(f"❌ GET request failed for {webhook_url}")
                
        except Exception as e:
            print(f"❌ Error testing {webhook_url}: {e}")
    
    print("❌ No working webhook URL found")
    return False

if __name__ == "__main__":
    register_final_webhook()