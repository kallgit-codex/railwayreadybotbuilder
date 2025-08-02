#!/usr/bin/env python3
"""
Update bot token and test webhook registration
Usage: python3 update_bot_token.py YOUR_NEW_TOKEN
"""
import sys
import requests
import json

def update_and_test_bot(new_token):
    print(f"=== TESTING NEW BOT TOKEN ===")
    
    # Test the new token
    test_url = f"https://api.telegram.org/bot{new_token}/getMe"
    try:
        response = requests.get(test_url, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            bot_info = result.get('result', {})
            username = bot_info.get('username', 'unknown')
            first_name = bot_info.get('first_name', 'unknown')
            
            print(f"✅ Bot token is valid!")
            print(f"Bot Username: @{username}")
            print(f"Bot Name: {first_name}")
            
            # Register webhook with new bot
            webhook_url = "https://bot-builder-k.replit.app/webhook/telegram/3"
            print(f"\n=== REGISTERING WEBHOOK ===")
            print(f"Webhook URL: {webhook_url}")
            
            webhook_response = requests.post(
                f"https://api.telegram.org/bot{new_token}/setWebhook",
                json={"url": webhook_url},
                timeout=10
            )
            webhook_result = webhook_response.json()
            
            if webhook_result.get('ok'):
                print("✅ Webhook registered successfully!")
                
                print(f"\n=== UPDATE INSTRUCTIONS ===")
                print(f"1. Go to: https://bot-builder-k.replit.app")
                print(f"2. Navigate to Clients section")
                print(f"3. Edit your client's API keys")
                print(f"4. Update 'telegram_bot_token' field with: {new_token}")
                print(f"5. Save changes")
                print(f"6. Test by messaging @{username}")
                
                return True
            else:
                print(f"❌ Webhook registration failed: {webhook_result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ Invalid bot token: {result.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing bot token: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 update_bot_token.py YOUR_NEW_TOKEN")
        print("Example: python3 update_bot_token.py 123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        sys.exit(1)
    
    new_token = sys.argv[1].strip()
    update_and_test_bot(new_token)