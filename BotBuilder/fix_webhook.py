#!/usr/bin/env python3
"""
Quick script to manually register the webhook with Telegram
"""
import requests
import json

def register_webhook():
    bot_token = "8102074391:AAEGVBqoqQtftjysd7B1BtFq0J1mTr2C9Ro"
    webhook_url = "https://bot-builder-k.replit.app/webhook/telegram/3"
    
    print(f"Registering webhook...")
    print(f"Bot Token: {bot_token[:10]}...")
    print(f"Webhook URL: {webhook_url}")
    
    # Register webhook
    url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    data = {"url": webhook_url}
    
    response = requests.post(url, json=data)
    result = response.json()
    
    print("\n=== WEBHOOK REGISTRATION RESULT ===")
    print(f"Success: {result.get('ok', False)}")
    print(f"Description: {result.get('description', 'N/A')}")
    
    if not result.get('ok'):
        print(f"Error Code: {result.get('error_code', 'N/A')}")
        return False
    
    # Verify webhook
    print("\n=== VERIFYING WEBHOOK ===")
    verify_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    verify_response = requests.get(verify_url)
    verify_result = verify_response.json()
    
    if verify_result.get('ok'):
        webhook_info = verify_result.get('result', {})
        current_url = webhook_info.get('url', 'None')
        pending_updates = webhook_info.get('pending_update_count', 0)
        
        print(f"Current Webhook URL: {current_url}")
        print(f"Pending Updates: {pending_updates}")
        
        if current_url == webhook_url:
            print("✅ SUCCESS: Webhook registered correctly!")
            
            if pending_updates > 0:
                print(f"📩 There are {pending_updates} pending messages that will be delivered")
                
            return True
        else:
            print("❌ MISMATCH: Webhook URL doesn't match")
            return False
    else:
        print("❌ VERIFICATION FAILED")
        return False

if __name__ == "__main__":
    register_webhook()