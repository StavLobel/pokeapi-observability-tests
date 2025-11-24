"""
HTTPX-based API client for PokéAPI with resilience patterns.

Provides async HTTP client with:
- Timeout configuration
- Retry logic with exponential backoff and jitter
- Rate limiting (429 handling)
- Circuit breaker pattern
- Metrics collection
- Error handling
"""

import asyncio
import random
import logging
from typing import Dict, Any, Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from tests.api.endpoints import get_pokemon_url, get_type_url, get_ability_url
from tests.utils.rate_limiter import RateLimiter
from tests.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

# Configure logger
logger = logging.getLogger(__name__)


class PokeAPIClient:
    """
    Async HTTP client for PokéAPI with resilience patterns.
    
    Features:
    - HTTPX async client for efficient concurrent requests
    - Configurable timeout (default 10s)
    - Retry with exponential backoff (max 3 retries)
    - Jitter to prevent thundering herd
    - 429 rate limit handling with Retry-After header
    - Circuit breaker per endpoint
    - Rate limiting
    - Metrics collection integration
    """
    
    def __init__(
        self,
        base_url: str = "https://pokeapi.co/api/v2",
        timeout: float = 10.0,
        rate_limiter: Optional[RateLimiter] = None,
        metrics_collector: Optional[Any] = None,
        max_retries: int = 3,
    ):
        """
        Initialize the PokéAPI client.
        
        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            rate_limiter: Optional RateLimiter instance
            metrics_collector: Optional MetricsCollector instance
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limiter = rate_limiter
        self.metrics_collector = metrics_collector
        
        # Create HTTPX async client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )
        
        # Circuit breakers per endpoint
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            'pokemon': CircuitBreaker(),
            'type': CircuitBreaker(),
            'ability': CircuitBreaker(),
        }
    
    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    def _add_jitter(self, delay: float) -> float:
        """
        Add random jitter to delay to prevent thundering herd.
        
        Args:
            delay: Base delay in seconds
            
        Returns:
            Delay with added jitter (0-1 second)
        """
        return delay + random.uniform(0, 1)
    
    async def _handle_rate_limit(self, response: httpx.Response) -> None:
        """
        Handle 429 rate limit response by waiting for Retry-After duration.
        
        Args:
            response: HTTP response with 429 status
        """
        retry_after = response.headers.get('Retry-After')
        
        if retry_after:
            try:
                wait_time = float(retry_after)
            except ValueError:
                # If Retry-After is not a number, use default
                wait_time = 1.0
        else:
            # No Retry-After header, use exponential backoff
            wait_time = 1.0
        
        # Add jitter to prevent synchronized retries
        wait_time = self._add_jitter(wait_time)
        
        logger.warning(
            f"Rate limited (429). Waiting {wait_time:.2f}s before retry"
        )
        await asyncio.sleep(wait_time)
    
    async def _make_request(
        self,
        url: str,
        endpoint_name: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with error handling and retries.
        
        Args:
            url: Full URL to request
            endpoint_name: Endpoint name for metrics/circuit breaker
            retry_count: Current retry attempt number
            
        Returns:
            JSON response as dictionary
            
        Raises:
            httpx.HTTPError: For HTTP errors
            httpx.RequestError: For network errors
            CircuitBreakerOpenError: If circuit breaker is open
        """
        import time
        
        # Acquire rate limiter token if configured
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        # Get circuit breaker for this endpoint
        circuit_breaker = self.circuit_breakers.get(endpoint_name)
        
        # Check if circuit is open
        if circuit_breaker and circuit_breaker.is_open():
            if self.metrics_collector:
                self.metrics_collector.increment_failure_counter(
                    endpoint_name,
                    'circuit_open'
                )
            raise CircuitBreakerOpenError(
                f"Circuit breaker is open for endpoint: {endpoint_name}"
            )
        
        start_time = time.time()
        
        try:
            # Make the HTTP request
            response = await self.client.get(url)
            
            # Handle rate limiting
            if response.status_code == 429:
                if retry_count < self.max_retries:
                    await self._handle_rate_limit(response)
                    return await self._make_request(url, endpoint_name, retry_count + 1)
                else:
                    if self.metrics_collector:
                        self.metrics_collector.increment_failure_counter(
                            endpoint_name,
                            'rate_limit_exceeded'
                        )
                    response.raise_for_status()
            
            # Raise for other HTTP errors
            response.raise_for_status()
            
            # Record success metrics
            duration = time.time() - start_time
            if self.metrics_collector:
                self.metrics_collector.increment_request_counter(endpoint_name)
                self.metrics_collector.record_latency(endpoint_name, duration)
            
            # Record success in circuit breaker
            if circuit_breaker:
                await circuit_breaker.record_success()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            # HTTP error (4xx, 5xx)
            duration = time.time() - start_time
            
            if self.metrics_collector:
                self.metrics_collector.increment_failure_counter(
                    endpoint_name,
                    f'http_{e.response.status_code}'
                )
                self.metrics_collector.record_latency(endpoint_name, duration)
            
            # Record failure in circuit breaker
            if circuit_breaker:
                await circuit_breaker.record_failure()
            
            logger.error(
                f"HTTP error for {endpoint_name}: {e.response.status_code} - {e}"
            )
            raise
            
        except httpx.RequestError as e:
            # Network error (timeout, connection error, etc.)
            duration = time.time() - start_time
            
            if self.metrics_collector:
                self.metrics_collector.increment_failure_counter(
                    endpoint_name,
                    'network_error'
                )
                self.metrics_collector.record_latency(endpoint_name, duration)
            
            # Record failure in circuit breaker
            if circuit_breaker:
                await circuit_breaker.record_failure()
            
            logger.error(f"Network error for {endpoint_name}: {e}")
            raise
    
    async def _request_with_retry(
        self,
        url: str,
        endpoint_name: str
    ) -> Dict[str, Any]:
        """
        Make request with exponential backoff retry logic.
        
        Args:
            url: Full URL to request
            endpoint_name: Endpoint name for metrics
            
        Returns:
            JSON response as dictionary
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await self._make_request(url, endpoint_name)
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_exception = e
                
                # Don't retry on client errors (except 429 which is handled separately)
                if isinstance(e, httpx.HTTPStatusError):
                    if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                        raise
                
                # Don't retry if this was the last attempt
                if attempt >= self.max_retries:
                    break
                
                # Calculate exponential backoff with jitter
                # 2^attempt seconds: 1s, 2s, 4s
                wait_time = 2 ** attempt
                wait_time = self._add_jitter(wait_time)
                
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries + 1}). "
                    f"Retrying in {wait_time:.2f}s..."
                )
                
                await asyncio.sleep(wait_time)
        
        # All retries exhausted
        if last_exception:
            raise last_exception
    
    async def get_pokemon(self, pokemon_id: int) -> Dict[str, Any]:
        """
        Get Pokemon data by ID.
        
        Args:
            pokemon_id: Pokemon ID (e.g., 1 for Bulbasaur)
            
        Returns:
            Pokemon data as dictionary
            
        Raises:
            httpx.HTTPError: For HTTP errors
            httpx.RequestError: For network errors
            CircuitBreakerOpenError: If circuit breaker is open
        """
        url = get_pokemon_url(pokemon_id)
        return await self._request_with_retry(url, 'pokemon')
    
    async def get_type(self, type_id: int) -> Dict[str, Any]:
        """
        Get Type data by ID.
        
        Args:
            type_id: Type ID (e.g., 1 for Normal)
            
        Returns:
            Type data as dictionary
            
        Raises:
            httpx.HTTPError: For HTTP errors
            httpx.RequestError: For network errors
            CircuitBreakerOpenError: If circuit breaker is open
        """
        url = get_type_url(type_id)
        return await self._request_with_retry(url, 'type')
    
    async def get_ability(self, ability_id: int) -> Dict[str, Any]:
        """
        Get Ability data by ID.
        
        Args:
            ability_id: Ability ID (e.g., 1 for Stench)
            
        Returns:
            Ability data as dictionary
            
        Raises:
            httpx.HTTPError: For HTTP errors
            httpx.RequestError: For network errors
            CircuitBreakerOpenError: If circuit breaker is open
        """
        url = get_ability_url(ability_id)
        return await self._request_with_retry(url, 'ability')
    
    def get_circuit_breaker_state(self, endpoint: str) -> int:
        """
        Get the circuit breaker state for an endpoint.
        
        Args:
            endpoint: Endpoint name ('pokemon', 'type', 'ability')
            
        Returns:
            Circuit state value (0=CLOSED, 1=OPEN, 2=HALF_OPEN)
        """
        circuit_breaker = self.circuit_breakers.get(endpoint)
        if circuit_breaker:
            return circuit_breaker.get_state_value()
        return 0
