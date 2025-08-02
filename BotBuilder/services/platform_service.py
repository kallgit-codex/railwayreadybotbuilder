
import requests

def register_webhooks(client, bot_id, public_url):
    # Telegram
    if client.telegram_api_key:
        telegram_url = f"https://api.telegram.org/bot{client.telegram_api_key}/setWebhook"
        requests.post(telegram_url, data={"url": f"{public_url}/webhook/telegram/{bot_id}"})
    # WhatsApp / Meta would go here with Graph API calls
