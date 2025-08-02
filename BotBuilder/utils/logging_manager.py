"""
Centralized logging manager for LLM Bot Builder
Handles API errors, messages, and deployment events
"""
import os
import logging
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from config import get_config

config = get_config()

class LoggingManager:
    """Centralized logging manager"""
    
    def __init__(self):
        self.config = config
        self.setup_logging()
    
    def setup_logging(self):
        """Set up logging configuration"""
        # Create logs directory
        os.makedirs(self.config.LOG_DIR, exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create specialized loggers
        self.setup_app_logger()
        self.setup_message_logger()
        self.setup_error_logger()
        self.setup_deployment_logger()
    
    def setup_app_logger(self):
        """Set up main application logger"""
        self.app_logger = logging.getLogger('app')
        handler = self._get_handler('app.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.app_logger.addHandler(handler)
    
    def setup_message_logger(self):
        """Set up message logger for bot conversations"""
        self.message_logger = logging.getLogger('messages')
        handler = self._get_handler('messages.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        self.message_logger.addHandler(handler)
    
    def setup_error_logger(self):
        """Set up error logger"""
        self.error_logger = logging.getLogger('errors')
        handler = self._get_handler('errors.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        ))
        self.error_logger.addHandler(handler)
    
    def setup_deployment_logger(self):
        """Set up deployment events logger"""
        self.deployment_logger = logging.getLogger('deployments')
        handler = self._get_handler('deployments.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        self.deployment_logger.addHandler(handler)
    
    def _get_handler(self, filename):
        """Get appropriate handler based on rotation configuration"""
        filepath = os.path.join(self.config.LOG_DIR, filename)
        
        if self.config.LOG_ROTATION == 'daily':
            handler = TimedRotatingFileHandler(
                filepath, when='midnight', interval=1, backupCount=30
            )
        elif self.config.LOG_ROTATION == 'weekly':
            handler = TimedRotatingFileHandler(
                filepath, when='W0', interval=1, backupCount=12
            )
        else:
            # Size-based rotation as fallback
            handler = RotatingFileHandler(
                filepath, maxBytes=10*1024*1024, backupCount=5
            )
        
        return handler
    
    def log_message(self, bot_id, client_id, session_id, message, response, token_usage):
        """Log bot message exchange"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'bot_id': bot_id,
            'client_id': client_id,
            'session_id': session_id,
            'message_length': len(message),
            'response_length': len(response),
            'token_usage': token_usage
        }
        self.message_logger.info(json.dumps(log_entry))
    
    def log_error(self, error_type, error_message, context=None):
        """Log application errors"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': error_type,
            'error_message': str(error_message),
            'context': context or {}
        }
        self.error_logger.error(json.dumps(log_entry))
    
    def log_deployment(self, action, bot_id, platform, status, details=None):
        """Log deployment events"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'bot_id': bot_id,
            'platform': platform,
            'status': status,
            'details': details or {}
        }
        self.deployment_logger.info(json.dumps(log_entry))
    
    def log_api_request(self, endpoint, method, status_code, response_time=None):
        """Log API requests"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time': response_time
        }
        self.app_logger.info(json.dumps(log_entry))

# Global logging manager instance
logging_manager = LoggingManager()