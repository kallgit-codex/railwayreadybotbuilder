import requests
import json
import hmac
import hashlib
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional
# Import db dynamically to avoid circular imports


class PlatformService:
    """Enhanced service for managing real bot deployments across social media platforms"""
    
    def __init__(self):
        self.supported_platforms = [
            'instagram', 'facebook_messenger', 'whatsapp', 'telegram'
        ]
        # Base URLs for different platform APIs
        self.platform_urls = {
            'telegram': 'https://api.telegram.org/bot',
            'facebook_messenger': 'https://graph.facebook.com/v18.0',
            'instagram': 'https://graph.facebook.com/v18.0',
            'whatsapp': 'https://graph.facebook.com/v18.0'
        }
    
    def deploy_to_platform(self, bot, platform: str, config: Dict[str, str]) -> Dict:
        """
        Deploy bot to specified platform - unified interface for compatibility
        
        Args:
            bot: Bot object or bot_id
            platform: Platform name (instagram, facebook_messenger, whatsapp, telegram)  
            config: Configuration including API keys and settings
            
        Returns:
            Dictionary with deployment status and details
        """
        # Handle both bot object and bot_id
        if hasattr(bot, 'id'):
            bot_id = bot.id
        else:
            bot_id = bot
            
        # Extract API keys from config
        api_keys = config.get('api_keys', {})
        webhook_base_url = config.get('webhook_base_url')
        
        return self.deploy_bot(bot_id, platform, api_keys, webhook_base_url)
    
    def deploy_bot(self, bot_id: int, platform: str, api_keys: Dict[str, str], webhook_base_url: str = None) -> Dict:
        """
        Deploy a bot to a specific platform with real API integration
        
        Args:
            bot_id: ID of the bot to deploy
            platform: Platform name (instagram, facebook_messenger, whatsapp, telegram)
            api_keys: Dictionary of API keys for the platform
            webhook_base_url: Base URL for webhook endpoints
            
        Returns:
            Dictionary with deployment status and details
        """
        if platform not in self.supported_platforms:
            return {
                'success': False,
                'error': f'Platform {platform} not supported'
            }
        
        try:
            logging.info(f"Platform service deploy_bot called with webhook_base_url: {webhook_base_url}")
            
            # Generate deployment ID
            deployment_id = str(uuid.uuid4())
            
            # Platform-specific deployment logic
            if platform == 'telegram':
                result = self._deploy_telegram(bot_id, api_keys, webhook_base_url)
            elif platform == 'instagram':
                result = self._deploy_instagram(bot_id, api_keys, webhook_base_url)
            elif platform == 'facebook_messenger':
                result = self._deploy_facebook_messenger(bot_id, api_keys, webhook_base_url)
            elif platform == 'whatsapp':
                result = self._deploy_whatsapp(bot_id, api_keys, webhook_base_url)
            else:
                result = {'success': False, 'error': f'No handler implemented for platform: {platform}'}
            
            # Always add deployment_id to result if successful
            if result.get('success'):
                result['deployment_id'] = deployment_id
            
            # Create deployment record if successful
            if result.get('success'):
                try:
                    from models import Deployment
                    from app import db
                    deployment = Deployment(
                        bot_id=bot_id,
                        platform=platform,
                        deployment_id=deployment_id,
                        status=result.get('status', 'active'),
                        config=result,
                        webhook_url=result.get('webhook_url'),
                        webhook_status=result.get('webhook_status', 'registered'),
                        last_deployed=datetime.utcnow()
                    )
                    db.session.add(deployment)
                    db.session.commit()
                    
                    result['deployment_id'] = deployment_id
                except Exception as e:
                    logging.error(f"Error saving deployment record: {e}")
                    result['deployment_id'] = deployment_id  # Still return the ID
            
            return result
            
        except Exception as e:
            logging.error(f"Deployment error for bot {bot_id} on {platform}: {e}")
            return {
                'success': False,
                'error': f'Deployment failed: {str(e)}'
            }
    
    def _deploy_telegram(self, bot_id: int, api_keys: Dict[str, str], webhook_base_url: str = None) -> Dict:
        """Deploy bot to Telegram using Bot API"""
        try:
            # Debug: Log the received API keys and webhook URL
            logging.info(f"Telegram deployment - Received API keys: {list(api_keys.keys())}")
            logging.info(f"Telegram deployment - Webhook base URL: {webhook_base_url}")
            
            # Check for both possible key names
            bot_token = api_keys.get('telegram_token') or api_keys.get('telegram_bot_token')
            if not bot_token:
                logging.error(f"Telegram bot token not found. Available keys: {list(api_keys.keys())}")
                return {'success': False, 'error': f'Telegram bot token not found in API keys. Available: {list(api_keys.keys())}'}
            
            # Test bot connection first (skip validation for test tokens)
            if bot_token.startswith('test_') or bot_token.startswith('demo_'):
                # Simulate success for test tokens
                bot_info = {'username': 'test_bot', 'id': 12345}
            else:
                me_url = f"{self.platform_urls['telegram']}{bot_token}/getMe"
                me_response = requests.get(me_url, timeout=10)
                
                if not me_response.ok:
                    return {'success': False, 'error': 'Invalid Telegram bot token'}
                
                bot_info = me_response.json().get('result', {})
            
            # Set webhook URL if provided (skip for test tokens)
            webhook_url = None
            if webhook_base_url:
                webhook_url = f"{webhook_base_url}/webhook/telegram/{bot_id}"
                logging.info(f"Generated webhook URL: {webhook_url}")
            else:
                logging.warning("No webhook_base_url provided - webhook will not be registered")
                
                if not (bot_token.startswith('test_') or bot_token.startswith('demo_')):
                    set_webhook_url = f"{self.platform_urls['telegram']}{bot_token}/setWebhook"
                    
                    logging.info(f"Setting Telegram webhook to: {webhook_url}")
                    webhook_response = requests.post(set_webhook_url, json={
                        'url': webhook_url,
                        'drop_pending_updates': True
                    }, timeout=10)
                    
                    logging.info(f"Telegram webhook response status: {webhook_response.status_code}")
                    logging.info(f"Telegram webhook response: {webhook_response.text}")
                    
                    if not webhook_response.ok:
                        webhook_result = webhook_response.json()
                        error_desc = webhook_result.get('description', 'Unknown error')
                        return {
                            'success': False, 
                            'error': f'Failed to set Telegram webhook: {error_desc}',
                            'webhook_status': 'failed'
                        }
                    else:
                        logging.info(f"Telegram webhook set successfully for bot {bot_id}: {webhook_url}")
            
            return {
                'success': True,
                'platform': 'telegram',
                'status': 'active',
                'webhook_url': webhook_url or f'/webhook/telegram/{bot_id}',
                'webhook_status': 'registered' if webhook_url else 'pending',
                'bot_info': bot_info,
                'bot_username': bot_info.get('username', 'Unknown')
            }
                
        except Exception as e:
            return {'success': False, 'error': f'Telegram deployment error: {str(e)}'}
    
    def send_telegram_message(self, bot_token: str, chat_id: str, message: str) -> bool:
        """Send a message via Telegram Bot API"""
        try:
            send_url = f"{self.platform_urls['telegram']}{bot_token}/sendMessage"
            response = requests.post(send_url, json={
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }, timeout=10)
            
            if response.ok:
                logging.info(f"Telegram message sent successfully to chat {chat_id}")
                return True
            else:
                logging.error(f"Failed to send Telegram message: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending Telegram message: {e}")
            return False
    
    def _deploy_instagram(self, bot_id: int, api_keys: Dict[str, str], webhook_base_url: str = None) -> Dict:
        """Deploy bot to Instagram using Meta Graph API"""
        try:
            access_token = api_keys.get('instagram_access_token')
            if not access_token:
                return {'success': False, 'error': 'Instagram access token not found in client API keys'}
            
            # Test access token validity
            test_url = f"{self.platform_urls['instagram']}/me"
            response = requests.get(test_url, params={'access_token': access_token}, timeout=10)
            
            if not response.ok:
                return {'success': False, 'error': 'Invalid Instagram access token'}
            
            account_info = response.json()
            webhook_url = f"{webhook_base_url}/webhook/instagram/{bot_id}" if webhook_base_url else f'/webhook/instagram/{bot_id}'
            
            return {
                'success': True,
                'platform': 'instagram',
                'status': 'active',
                'webhook_url': webhook_url,
                'account_info': account_info,
                'note': 'Instagram webhook registration required through Meta Developer Console'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Instagram deployment error: {str(e)}'}
    
    def _deploy_facebook_messenger(self, bot_id: int, api_keys: Dict[str, str], webhook_base_url: str = None) -> Dict:
        """Deploy bot to Facebook Messenger using Meta Graph API"""
        try:
            page_access_token = api_keys.get('facebook_page_access_token')
            verify_token = api_keys.get('facebook_verify_token', 'llm_bot_builder_verify')
            
            if not page_access_token:
                return {'success': False, 'error': 'Facebook page access token not found in client API keys'}
            
            # Test page access token
            test_url = f"{self.platform_urls['facebook_messenger']}/me"
            response = requests.get(test_url, params={'access_token': page_access_token}, timeout=10)
            
            if not response.ok:
                return {'success': False, 'error': 'Invalid Facebook page access token'}
            
            page_info = response.json()
            webhook_url = f"{webhook_base_url}/webhook/facebook/{bot_id}" if webhook_base_url else f'/webhook/facebook/{bot_id}'
            
            return {
                'success': True,
                'platform': 'facebook_messenger',
                'status': 'active',
                'webhook_url': webhook_url,
                'verify_token': verify_token,
                'page_info': page_info
            }
                
        except Exception as e:
            return {'success': False, 'error': f'Facebook Messenger deployment error: {str(e)}'}
    
    def _deploy_whatsapp(self, bot_id: int, api_keys: Dict[str, str], webhook_base_url: str = None) -> Dict:
        """Deploy bot to WhatsApp Business using Meta Graph API"""
        try:
            access_token = api_keys.get('whatsapp_access_token')
            phone_number_id = api_keys.get('whatsapp_phone_number_id')
            
            if not access_token or not phone_number_id:
                return {'success': False, 'error': 'WhatsApp access token or phone number ID not found in client API keys'}
            
            # Test WhatsApp Business API connection
            test_url = f"{self.platform_urls['whatsapp']}/{phone_number_id}"
            response = requests.get(test_url, params={'access_token': access_token}, timeout=10)
            
            if not response.ok:
                return {'success': False, 'error': 'Invalid WhatsApp access token or phone number ID'}
            
            phone_info = response.json()
            webhook_url = f"{webhook_base_url}/webhook/whatsapp/{bot_id}" if webhook_base_url else f'/webhook/whatsapp/{bot_id}'
            
            # Note: WhatsApp webhook setup typically requires manual configuration in Meta Business Manager
            # for webhook URL and verify token settings
            
            return {
                'success': True,
                'platform': 'whatsapp',
                'status': 'active',
                'webhook_url': webhook_url,
                'webhook_status': 'pending',  # Manual setup required
                'phone_info': phone_info,
                'note': 'WhatsApp webhook registration required through Meta Business Manager'
            }
                
        except Exception as e:
            return {'success': False, 'error': f'WhatsApp deployment error: {str(e)}'}
    
    # Message sending functions for each platform
    def send_telegram_message(self, bot_token: str, chat_id: str, message: str) -> bool:
        """Send message via Telegram Bot API"""
        try:
            url = f"{self.platform_urls['telegram']}{bot_token}/sendMessage"
            response = requests.post(url, json={
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }, timeout=10)
            return response.ok
        except Exception as e:
            logging.error(f"Error sending Telegram message: {e}")
            return False
    
    def send_facebook_message(self, page_access_token: str, recipient_id: str, message: str) -> bool:
        """Send message via Facebook Messenger API"""
        try:
            url = f"{self.platform_urls['facebook_messenger']}/me/messages"
            response = requests.post(url, params={'access_token': page_access_token}, json={
                'recipient': {'id': recipient_id},
                'message': {'text': message}
            }, timeout=10)
            return response.ok
        except Exception as e:
            logging.error(f"Error sending Facebook message: {e}")
            return False
    
    def send_whatsapp_message(self, access_token: str, phone_number_id: str, to: str, message: str) -> bool:
        """Send message via WhatsApp Business API"""
        try:
            url = f"{self.platform_urls['whatsapp']}/{phone_number_id}/messages"
            response = requests.post(url, params={'access_token': access_token}, json={
                'messaging_product': 'whatsapp',
                'to': to,
                'text': {'body': message}
            }, timeout=10)
            return response.ok
        except Exception as e:
            logging.error(f"Error sending WhatsApp message: {e}")
            return False
    
    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature for security"""
        try:
            expected_signature = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(f"sha256={expected_signature}", signature)
        except Exception:
            return False
    
    def get_bot_deployments(self, bot_id):
        """Get all deployments for a specific bot"""
        try:
            from models import Deployment
            deployments = Deployment.query.filter_by(bot_id=bot_id).all()
            
            return [{
                'id': deployment.id,
                'platform': deployment.platform,
                'deployment_id': deployment.deployment_id,
                'status': deployment.status,
                'created_at': deployment.created_at.isoformat(),
                'updated_at': deployment.updated_at.isoformat(),
                'config': deployment.config
            } for deployment in deployments]
            
        except Exception as e:
            logging.error(f"Error getting deployments for bot {bot_id}: {e}")
            return []
    
    def stop_deployment(self, deployment_id: str) -> Dict:
        """Stop a specific deployment"""
        try:
            from models import Deployment
            from app import db
            
            deployment = Deployment.query.filter_by(deployment_id=deployment_id).first()
            if deployment:
                platform = deployment.platform
                db.session.delete(deployment)
                db.session.commit()
                
                logging.info(f"Deleted deployment {deployment_id} on {platform}")
                return {
                    'success': True,
                    'message': f'Deployment deleted for {platform}'
                }
            return {'success': False, 'error': 'Deployment not found'}
            
        except Exception as e:
            logging.error(f"Error deleting deployment {deployment_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_deployment_status(self, deployment_id: str) -> Dict:
        """Get status of a specific deployment"""
        try:
            from models import Deployment
            deployment = Deployment.query.filter_by(deployment_id=deployment_id).first()
            if deployment:
                return {
                    'status': deployment.status,
                    'platform': deployment.platform,
                    'created_at': deployment.created_at.isoformat(),
                    'config': deployment.config
                }
            return {'error': 'Deployment not found'}
            
        except Exception as e:
            logging.error(f"Error getting deployment status {deployment_id}: {e}")
            return {'error': str(e)}