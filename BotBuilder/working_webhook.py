#!/usr/bin/env python3
"""
Standalone working webhook for the bot - bypasses all Flask routing issues
"""
import os
import json
import requests
from flask import Flask, request
from openai import OpenAI

# Create a simple Flask app just for the webhook
webhook_app = Flask(__name__)

@webhook_app.route('/working', methods=['POST', 'GET'])
def telegram_webhook():
    """Working Telegram webhook that bypasses all service issues"""
    
    if request.method == 'GET':
        return 'Bot webhook is working!', 200
    
    try:
        # Parse Telegram update
        data = request.get_json(force=True) or {}
        msg = data.get('message', {})
        text = msg.get('text', '')
        chat = msg.get('chat', {})
        chat_id = chat.get('id')
        
        if text and chat_id:
            # Get environment variables
            api_key = os.environ.get("OPENAI_API_KEY")
            bot_token = "8301717846:AAFhv9n1qlizTvYytBWVeRZFCAgVqTgGflM"
            
            if api_key:
                try:
                    # Generate AI response
                    client = OpenAI(api_key=api_key)
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a helpful AI assistant for a home services business. You help customers with mounting TVs, installing soundbars, and other home tech services. Be friendly, professional, and helpful. Provide pricing when asked: Standard TV mounting is $99, Large TV mounting is $149, Soundbar mounting is $40."},
                            {"role": "user", "content": text}
                        ],
                        max_tokens=400,
                        temperature=0.7
                    )
                    
                    response_text = response.choices[0].message.content
                    
                except Exception as ai_error:
                    response_text = f"Hello! I'm your AI assistant for home services. I can help with TV mounting ($99 standard, $149 large), soundbar installation ($40), and more. (AI temporarily unavailable: {str(ai_error)[:50]})"
            else:
                response_text = "Hello! I'm your AI assistant for home services. I can help with TV mounting ($99 standard, $149 large), soundbar installation ($40), and more. Please configure OpenAI API key for intelligent responses."
            
            # Send response via Telegram API
            telegram_api = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": response_text,
                "parse_mode": "Markdown"
            }
            
            requests.post(telegram_api, json=payload, timeout=10)
            
        return 'OK', 200
        
    except Exception as e:
        # Always return OK to prevent webhook retry storms
        print(f"Webhook error: {e}")
        return 'OK', 200

@webhook_app.route('/health')
def health():
    """Health check endpoint"""
    return 'Healthy', 200

if __name__ == '__main__':
    # Run on port 8080 to avoid conflicts
    webhook_app.run(host='0.0.0.0', port=8080, debug=True)