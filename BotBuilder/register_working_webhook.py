#!/usr/bin/env python3
"""
Register the working webhook with Telegram
"""
import requests

def register_working_webhook():
    """Register the new working webhook URL with Telegram"""
    
    bot_token = "8301717846:AAFhv9n1qlizTvYytBWVeRZFCAgVqTgGflM"
    webhook_url = "https://bot-builder-k.replit.app/bot/webhook"
    
    # First, delete any existing webhook
    delete_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    print("Deleting existing webhook...")
    
    delete_response = requests.post(delete_url)
    print(f"Delete response: {delete_response.json()}")
    
    # Register new webhook
    set_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    webhook_data = {
        "url": webhook_url,
        "max_connections": 40,
        "allowed_updates": ["message"]
    }
    
    print(f"Registering webhook: {webhook_url}")
    
    response = requests.post(set_url, json=webhook_data)
    result = response.json()
    
    print(f"Registration response: {result}")
    
    if result.get('ok'):
        print("✅ Webhook registered successfully!")
        
        # Test the webhook
        print("Testing webhook URL...")
        test_response = requests.get(webhook_url)
        print(f"Test response: {test_response.status_code} - {test_response.text}")
        
    else:
        print("❌ Webhook registration failed!")
        print(f"Error: {result.get('description', 'Unknown error')}")
    
    # Check webhook info
    info_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    info_response = requests.get(info_url)
    info_result = info_response.json()
    
    print(f"Webhook info: {info_result}")

if __name__ == "__main__":
    register_working_webhook()