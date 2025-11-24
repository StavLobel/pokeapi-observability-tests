"""
Rate limiter implementation using token bucket algorithm.

Provides async rate limiting to prevent overwhelming the PokéAPI service.
"""

import asyncio
import time
from typing import Optional


class RateLimiter:
    """
    Token bucket rate limiter for controlling API request rates.
    
    The token bucket algorithm allows bursts up to the bucket capacity
    while maintaining an average rate over time.
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        time_window: float = 60.0
    ):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the time window
            time_window: Time window in seconds (default: 60s = 1 minute)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.tokens = float(max_requests)
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
        
        # Calculate token refill rate (tokens per second)
        self.refill_rate = max_requests / time_window
    
    async def acquire(self) -> None:
        """
        Acquire a token to make a request.
        
        If no tokens are available, this method will wait until a token
        becomes available through the refill process.
        """
        async with self.lock:
            while True:
                now = time.monotonic()
                time_passed = now - self.last_update
                
                # Refill tokens based on time passed
                self.tokens = min(
                    self.max_requests,
                    self.tokens + time_passed * self.refill_rate
                )
                self.last_update = now
                
                # If we have tokens available, consume one and return
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                
                # Calculate wait time until next token is available
                wait_time = (1.0 - self.tokens) / self.refill_rate
                
                # Release lock while waiting to allow other operations
                # Wait for the calculated time
                await asyncio.sleep(wait_time)
    
    def reset(self) -> None:
        """
        Reset the rate limiter to full capacity.
        
        Useful for testing or when starting a new rate limit period.
        """
        self.tokens = float(self.max_requests)
        self.last_update = time.monotonic()
    
    def get_available_tokens(self) -> float:
        """
        Get the current number of available tokens.
        
        Returns:
            Number of tokens currently available (may be fractional)
        """
        now = time.monotonic()
        time_passed = now - self.last_update
        
        return min(
            self.max_requests,
            self.tokens + time_passed * self.refill_rate
        )
