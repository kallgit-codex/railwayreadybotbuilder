
from database import db

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    telegram_api_key = db.Column(db.String(255))
    whatsapp_api_key = db.Column(db.String(255))
    facebook_api_key = db.Column(db.String(255))
    instagram_api_key = db.Column(db.String(255))

def save_client(name, telegram_key=None, whatsapp_key=None, facebook_key=None, instagram_key=None):
    client = Client(name=name,
                    telegram_api_key=telegram_key,
                    whatsapp_api_key=whatsapp_key,
                    facebook_api_key=facebook_key,
                    instagram_api_key=instagram_key)
    db.session.add(client)
    db.session.commit()
    return client

def get_client(client_id):
    return Client.query.get(client_id)

def update_client_keys(client_id, telegram_key=None, whatsapp_key=None, facebook_key=None, instagram_key=None):
    client = Client.query.get(client_id)
    if telegram_key: client.telegram_api_key = telegram_key
    if whatsapp_key: client.whatsapp_api_key = whatsapp_key
    if facebook_key: client.facebook_api_key = facebook_key
    if instagram_key: client.instagram_api_key = instagram_key
    db.session.commit()
    return client
