"""
Global Settings Service
Manages global application settings including OpenAI API key
"""

import logging
from models import GlobalSettings
from database import db


class SettingsService:
    """Service for managing global application settings with caching and validation"""
    
    def __init__(self):
        self._cache = {}
        self._openai_key_history = []  # Keep track of key changes for rollback
        self._load_initial_settings()
    
    def _load_initial_settings(self):
        """Load settings from database into cache on startup"""
        try:
            settings = GlobalSettings.query.all()
            for setting in settings:
                self._cache[setting.key] = setting.value
            
            openai_key = self._cache.get('openai_api_key')
            if openai_key:
                logging.info("✅ Global OpenAI API key loaded from database on startup")
                self._openai_key_history.append(openai_key)
            else:
                logging.warning("⚠️ No OpenAI API key found in database. Bots cannot run until key is configured.")
                
        except Exception as e:
            logging.error(f"Error loading initial settings: {e}")
    
    def get_setting(self, key):
        """Get a setting value by key (cached)"""
        try:
            # First check cache
            if key in self._cache:
                return self._cache[key]
            
            # If not in cache, load from database
            setting = GlobalSettings.query.filter_by(key=key).first()
            value = setting.value if setting else None
            
            # Cache the value
            if value is not None:
                self._cache[key] = value
                
            return value
        except Exception as e:
            logging.error(f"Error getting setting {key}: {e}")
            return None
    
    def set_setting(self, key, value):
        """Set or update a setting value with caching"""
        try:
            old_value = self._cache.get(key)
            
            setting = GlobalSettings.query.filter_by(key=key).first()
            
            if setting:
                setting.value = value
            else:
                setting = GlobalSettings(key=key, value=value)
                db.session.add(setting)
            
            db.session.commit()
            
            # Update cache
            self._cache[key] = value
            
            # Track OpenAI key changes for rollback capability
            if key == 'openai_api_key' and old_value != value:
                if old_value:
                    self._openai_key_history.append(old_value)
                # Keep only last 3 keys for rollback
                if len(self._openai_key_history) > 3:
                    self._openai_key_history = self._openai_key_history[-3:]
                
                logging.info(f"🔑 OpenAI API key updated from {old_value[:8] + '...' if old_value else 'None'} to {value[:8] + '...'}")
            
            return {
                'success': True,
                'message': f'Setting {key} updated successfully',
                'setting': setting.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error setting {key}: {e}")
            return {
                'success': False,
                'message': f'Failed to update setting: {str(e)}'
            }
    
    def get_openai_api_key(self):
        """Get the global OpenAI API key"""
        return self.get_setting('openai_api_key')
    
    def validate_openai_key(self, api_key):
        """Validate OpenAI API key with a test call"""
        try:
            from openai import OpenAI
            test_client = OpenAI(api_key=api_key)
            
            # Test with a minimal completion call
            response = test_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            
            return {
                'valid': True,
                'message': 'API key validated successfully'
            }
        except Exception as e:
            error_msg = str(e)
            if "invalid" in error_msg.lower() or "authentication" in error_msg.lower():
                return {
                    'valid': False,
                    'message': 'Invalid API key - authentication failed'
                }
            else:
                return {
                    'valid': False,
                    'message': f'API key validation failed: {error_msg}'
                }
    
    def set_openai_api_key(self, api_key, confirmed=False):
        """Set the global OpenAI API key with validation and confirmation"""
        if not confirmed:
            return {
                'success': False,
                'message': 'Confirmation required to change OpenAI API key',
                'requires_confirmation': True
            }
        
        # Validate the new key first
        validation = self.validate_openai_key(api_key)
        if not validation['valid']:
            return {
                'success': False,
                'message': f'Invalid API key: {validation["message"]}'
            }
        
        # Store old key for potential rollback
        old_key = self.get_openai_api_key()
        
        # Set the new key
        result = self.set_setting('openai_api_key', api_key)
        
        if result['success']:
            # Notify OpenAI service to refresh
            try:
                from services.openai_service import openai_service
                openai_service.refresh_api_key()
                logging.info("🔄 OpenAI service refreshed with new API key")
            except Exception as e:
                logging.error(f"Error refreshing OpenAI service: {e}")
        
        return result
    
    def rollback_openai_key(self):
        """Rollback to the previous OpenAI API key"""
        if len(self._openai_key_history) < 2:
            return {
                'success': False,
                'message': 'No previous key available for rollback'
            }
        
        # Get the previous key (excluding current)
        previous_key = self._openai_key_history[-2]
        
        # Set it without confirmation (emergency rollback)
        result = self.set_setting('openai_api_key', previous_key)
        
        if result['success']:
            logging.warning(f"🔄 Rolled back OpenAI API key to previous version")
            try:
                from services.openai_service import openai_service
                openai_service.refresh_api_key()
            except Exception as e:
                logging.error(f"Error refreshing OpenAI service after rollback: {e}")
        
        return result
    
    def delete_setting(self, key):
        """Delete a setting"""
        try:
            setting = GlobalSettings.query.filter_by(key=key).first()
            if setting:
                db.session.delete(setting)
                db.session.commit()
                return {
                    'success': True,
                    'message': f'Setting {key} deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'message': f'Setting {key} not found'
                }
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting setting {key}: {e}")
            return {
                'success': False,
                'message': f'Failed to delete setting: {str(e)}'
            }
    
    def get_all_settings(self):
        """Get all settings as a dictionary"""
        try:
            settings = GlobalSettings.query.all()
            return {setting.key: setting.value for setting in settings}
        except Exception as e:
            logging.error(f"Error getting all settings: {e}")
            return {}


# Initialize the service
settings_service = SettingsService()