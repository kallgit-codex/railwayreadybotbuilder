"""
Configuration module for LLM Bot Builder
Handles environment variables and application settings
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Security Configuration
    CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///bots.db')
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": int(os.environ.get('DB_POOL_RECYCLE', '300')),
        "pool_pre_ping": True,
    }
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_FILE_SIZE', '16777216'))  # 16MB default
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
    MESSAGES_PER_MINUTE = int(os.environ.get('MESSAGES_PER_MINUTE', '60'))
    MESSAGES_PER_SECOND = int(os.environ.get('MESSAGES_PER_SECOND', '2'))
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    LOG_ROTATION = os.environ.get('LOG_ROTATION', 'daily')  # daily, weekly
    
    # Webhook Configuration
    WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'default-webhook-secret')
    BASE_WEBHOOK_URL = os.environ.get('BASE_WEBHOOK_URL', 'https://your-domain.com')
    
    # Health Check Configuration
    HEALTH_CHECK_ENABLED = os.environ.get('HEALTH_CHECK_ENABLED', 'True').lower() == 'true'
    
    @classmethod
    def validate_required_vars(cls):
        """Validate that required environment variables are set"""
        required_vars = ['OPENAI_API_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

# Development Configuration
class DevelopmentConfig(Config):
    DEBUG = True
    
# Production Configuration  
class ProductionConfig(Config):
    DEBUG = False
    # Force secure session cookies in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Additional production-specific settings

# Configuration mapping
config_mapping = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config_mapping.get(env, DevelopmentConfig)