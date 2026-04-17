"""
Rate Limiting Module

Implements sliding window rate limiting to prevent API abuse.
Default: 20 requests/minute per user
"""

import logging
from collections import defaultdict, deque
from time import time
from typing import Dict

from fastapi import HTTPException

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Sliding window counter rate limiter.
    
    Tracks request timestamps per user and enforces limit.
    """
    
    def __init__(self, limit_per_minute: int = 20, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            limit_per_minute: Max requests allowed per minute
            window_seconds: Time window in seconds (default 60)
        """
        self.limit = limit_per_minute
        self.window = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def check(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit.
        
        Removes timestamps older than window, then:
        - If count < limit: adds current time, returns True (allowed)
        - If count >= limit: returns False (blocked)
        
        Args:
            user_id: User identifier
        
        Returns:
            bool: True if request allowed, False if blocked
        
        Raises:
            HTTPException: 429 Too Many Requests if rate limit exceeded
        """
        now = time()
        window_start = now - self.window
        
        # Get or create request queue for user
        user_requests = self.requests[user_id]
        
        # Remove timestamps outside the window
        while user_requests and user_requests[0] < window_start:
            user_requests.popleft()
        
        # Check if limit exceeded
        if len(user_requests) >= self.limit:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            # Calculate retry-after time
            oldest = user_requests[0]
            retry_after = int(oldest + self.window - now) + 1
            
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: max {self.limit} requests per minute",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Add current request
        user_requests.append(now)
        return True
    
    def get_remaining(self, user_id: str) -> int:
        """
        Get remaining requests for user in current window.
        
        Args:
            user_id: User identifier
        
        Returns:
            int: Number of requests remaining
        """
        now = time()
        window_start = now - self.window
        
        user_requests = self.requests[user_id]
        
        # Count valid requests in window
        valid_count = sum(1 for ts in user_requests if ts >= window_start)
        return max(0, self.limit - valid_count)
    
    def reset_user(self, user_id: str) -> None:
        """
        Clear rate limit history for a user (admin operation).
        
        Args:
            user_id: User identifier
        """
        if user_id in self.requests:
            self.requests[user_id].clear()
            logger.info(f"Rate limit reset for user {user_id}")


# Global instance
_limiter: RateLimiter = None


def get_rate_limiter(limit_per_minute: int = 20) -> RateLimiter:
    """
    Get or initialize global rate limiter instance.
    
    Args:
        limit_per_minute: Max requests per minute
    
    Returns:
        RateLimiter: Global instance
    """
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter(limit_per_minute)
    return _limiter
