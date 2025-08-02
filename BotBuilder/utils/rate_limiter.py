"""
Rate limiting utility for LLM Bot Builder
Prevents abuse and controls API usage per bot
"""
import time
from collections import defaultdict, deque
from config import get_config

config = get_config()

class RateLimiter:
    """Simple rate limiter implementation"""
    
    def __init__(self):
        self.config = config
        self.request_history = defaultdict(deque)
        self.enabled = self.config.RATE_LIMIT_ENABLED
    
    def is_allowed(self, bot_id, current_time=None):
        """Check if request is allowed for given bot"""
        if not self.enabled:
            return True, None
        
        if current_time is None:
            current_time = time.time()
        
        # Clean old requests
        self._cleanup_old_requests(bot_id, current_time)
        
        # Check per-second limit
        recent_requests = [t for t in self.request_history[bot_id] 
                          if current_time - t <= 1]
        if len(recent_requests) >= self.config.MESSAGES_PER_SECOND:
            return False, f"Rate limit exceeded: {self.config.MESSAGES_PER_SECOND} messages per second"
        
        # Check per-minute limit
        minute_requests = [t for t in self.request_history[bot_id] 
                          if current_time - t <= 60]
        if len(minute_requests) >= self.config.MESSAGES_PER_MINUTE:
            return False, f"Rate limit exceeded: {self.config.MESSAGES_PER_MINUTE} messages per minute"
        
        # Record this request
        self.request_history[bot_id].append(current_time)
        
        return True, None
    
    def _cleanup_old_requests(self, bot_id, current_time):
        """Remove requests older than 1 minute"""
        cutoff_time = current_time - 60
        while (self.request_history[bot_id] and 
               self.request_history[bot_id][0] < cutoff_time):
            self.request_history[bot_id].popleft()
    
    def get_stats(self, bot_id):
        """Get current rate limiting stats for a bot"""
        current_time = time.time()
        self._cleanup_old_requests(bot_id, current_time)
        
        recent_requests = [t for t in self.request_history[bot_id] 
                          if current_time - t <= 1]
        minute_requests = [t for t in self.request_history[bot_id] 
                          if current_time - t <= 60]
        
        return {
            'requests_last_second': len(recent_requests),
            'requests_last_minute': len(minute_requests),
            'limit_per_second': self.config.MESSAGES_PER_SECOND,
            'limit_per_minute': self.config.MESSAGES_PER_MINUTE,
            'enabled': self.enabled
        }

# Global rate limiter instance
rate_limiter = RateLimiter()