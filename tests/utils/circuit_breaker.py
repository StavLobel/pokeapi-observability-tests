"""
Circuit breaker pattern implementation for resilient API calls.

Prevents cascading failures by opening the circuit after repeated failures
and allowing time for the service to recover.
"""

import asyncio
import time
from typing import Callable, Any, Optional
from collections import deque
from enum import Enum


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = 0  # Normal operation, requests pass through
    OPEN = 1    # Circuit is open, requests fail fast
    HALF_OPEN = 2  # Testing if service has recovered


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.
    
    Tracks failure rates per endpoint and opens the circuit when
    failures exceed the threshold. After a timeout period, the circuit
    enters half-open state to test recovery.
    """
    
    def __init__(
        self,
        failure_threshold: float = 0.5,
        timeout: float = 30.0,
        window_size: int = 10,
        window_duration: float = 300.0,
        success_threshold: int = 3
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            failure_threshold: Failure rate (0.0-1.0) that triggers circuit opening
            timeout: Seconds to wait before entering half-open state
            window_size: Minimum number of requests before evaluating failure rate
            window_duration: Time window in seconds for tracking failures (5 minutes)
            success_threshold: Consecutive successes needed to close circuit from half-open
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.window_size = window_size
        self.window_duration = window_duration
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.opened_at: Optional[float] = None
        
        # Sliding window for tracking request outcomes (timestamp, success)
        self.request_history: deque = deque()
        
        self.lock = asyncio.Lock()
    
    def _clean_old_requests(self) -> None:
        """Remove requests outside the sliding window."""
        now = time.monotonic()
        cutoff = now - self.window_duration
        
        while self.request_history and self.request_history[0][0] < cutoff:
            self.request_history.popleft()
    
    def _calculate_failure_rate(self) -> float:
        """
        Calculate the current failure rate within the sliding window.
        
        Returns:
            Failure rate as a float between 0.0 and 1.0
        """
        self._clean_old_requests()
        
        if len(self.request_history) < self.window_size:
            return 0.0
        
        failures = sum(1 for _, success in self.request_history if not success)
        return failures / len(self.request_history)
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception raised by the function
        """
        async with self.lock:
            # Check if we should transition from OPEN to HALF_OPEN
            if self.state == CircuitState.OPEN:
                if self.opened_at and (time.monotonic() - self.opened_at) >= self.timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is open. Opened at {self.opened_at}"
                    )
            
            # In HALF_OPEN state, only allow limited requests through
            if self.state == CircuitState.HALF_OPEN:
                pass  # Allow the request to proceed
        
        # Execute the function outside the lock to avoid blocking
        try:
            result = await func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure()
            raise
    
    async def record_success(self) -> None:
        """Record a successful request."""
        async with self.lock:
            now = time.monotonic()
            self.request_history.append((now, True))
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    # Close the circuit after enough consecutive successes
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.opened_at = None
    
    async def record_failure(self) -> None:
        """Record a failed request and potentially open the circuit."""
        async with self.lock:
            now = time.monotonic()
            self.request_history.append((now, False))
            self.last_failure_time = now
            
            if self.state == CircuitState.HALF_OPEN:
                # Failure in half-open state reopens the circuit
                self.state = CircuitState.OPEN
                self.opened_at = now
                self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                # Check if we should open the circuit
                failure_rate = self._calculate_failure_rate()
                
                if (len(self.request_history) >= self.window_size and 
                    failure_rate >= self.failure_threshold):
                    self.state = CircuitState.OPEN
                    self.opened_at = now
    
    def is_open(self) -> bool:
        """
        Check if the circuit is currently open.
        
        Returns:
            True if circuit is open, False otherwise
        """
        return self.state == CircuitState.OPEN
    
    def get_state(self) -> CircuitState:
        """
        Get the current circuit state.
        
        Returns:
            Current CircuitState
        """
        return self.state
    
    def get_state_value(self) -> int:
        """
        Get the numeric value of the current state for Prometheus metrics.
        
        Returns:
            0 for CLOSED, 1 for OPEN, 2 for HALF_OPEN
        """
        return self.state.value
    
    def reset(self) -> None:
        """
        Reset the circuit breaker to closed state.
        
        Useful for testing or manual intervention.
        """
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_at = None
        self.request_history.clear()


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass
