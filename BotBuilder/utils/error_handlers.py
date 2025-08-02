"""
Centralized error handling for LLM Bot Builder
Provides consistent error responses and logging
"""
from flask import jsonify
from utils.logging_manager import logging_manager

class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def handle_api_error(error, context=None):
        """Handle API errors with consistent response format"""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Log the error
        logging_manager.log_error(error_type, error_message, context)
        
        # Determine status code based on error type
        status_code = ErrorHandler._get_status_code(error)
        
        response = {
            'error': True,
            'message': error_message,
            'type': error_type
        }
        
        if context:
            response['context'] = context
        
        return jsonify(response), status_code
    
    @staticmethod
    def handle_validation_error(field, message):
        """Handle validation errors"""
        response = {
            'error': True,
            'message': f"Validation error: {message}",
            'type': 'ValidationError',
            'field': field
        }
        
        logging_manager.log_error('ValidationError', message, {'field': field})
        
        return jsonify(response), 400
    
    @staticmethod
    def handle_rate_limit_error(bot_id, limit_message):
        """Handle rate limiting errors"""
        response = {
            'error': True,
            'message': limit_message,
            'type': 'RateLimitError',
            'bot_id': bot_id
        }
        
        logging_manager.log_error('RateLimitError', limit_message, {'bot_id': bot_id})
        
        return jsonify(response), 429
    
    @staticmethod
    def _get_status_code(error):
        """Determine appropriate HTTP status code for error"""
        error_mappings = {
            'ValidationError': 400,
            'ValueError': 400,
            'FileNotFoundError': 404,
            'PermissionError': 403,
            'ConnectionError': 503,
            'TimeoutError': 504,
            'KeyError': 400,
            'AttributeError': 500,
            'TypeError': 500,
        }
        
        error_type = type(error).__name__
        return error_mappings.get(error_type, 500)
    
    @staticmethod
    def success_response(data=None, message="Success"):
        """Create consistent success response"""
        response = {
            'error': False,
            'message': message
        }
        
        if data is not None:
            response['data'] = data
        
        return jsonify(response)

# Decorator for wrapping Flask routes with error handling
def handle_errors(f):
    """Decorator to wrap Flask routes with error handling"""
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            return ErrorHandler.handle_api_error(e, {
                'function': f.__name__,
                'args': str(args),
                'kwargs': str(kwargs)
            })
    
    wrapper.__name__ = f.__name__
    return wrapper