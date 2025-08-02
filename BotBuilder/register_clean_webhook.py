import requests

bot_token = "8301717846:AAFhv9n1qlizTvYytBWVeRZFCAgVqTgGflM"
webhook_url = "https://bot-builder-k.replit.app/webhook/telegram/3"

response = requests.post(
    f"https://api.telegram.org/bot{bot_token}/setWebhook",
    json={"url": webhook_url}
)

result = response.json()
if result.get('ok'):
    print(f"✅ Clean webhook registered: {webhook_url}")
else:
    print(f"❌ Webhook error: {result}")