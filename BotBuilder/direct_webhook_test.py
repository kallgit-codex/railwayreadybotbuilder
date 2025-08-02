import requests
import json

def test_webhook_directly():
    """Test the webhook directly without any local code"""
    
    url = "https://bot-builder-k.replit.app/webhook/telegram/3"
    
    test_data = {
        "message": {
            "text": "Hello bot",
            "chat": {"id": 12345},
            "from": {"id": 12345, "first_name": "Test User"}
        }
    }
    
    print("=== TESTING DIRECT WEBHOOK ===")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook working!")
        else:
            print("❌ Webhook failed")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_webhook_directly()