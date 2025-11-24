# PokéAPI Client

HTTPX-based async API client for PokéAPI with comprehensive resilience patterns.

## Features

- ✅ Async/await support with HTTPX
- ✅ Configurable timeout (default 10s)
- ✅ Retry with exponential backoff and jitter
- ✅ Rate limiting with token bucket algorithm
- ✅ Circuit breaker pattern per endpoint
- ✅ 429 rate limit handling with Retry-After header
- ✅ Comprehensive error handling
- ✅ Metrics collection integration
- ✅ Context manager support

## Quick Start

### Basic Usage

```python
import asyncio
from tests.api.client import PokeAPIClient

async def main():
    async with PokeAPIClient() as client:
        # Get Pokemon data
        pokemon = await client.get_pokemon(1)
        print(f"Pokemon: {pokemon['name']}")
        
        # Get Type data
        type_data = await client.get_type(1)
        print(f"Type: {type_data['name']}")
        
        # Get Ability data
        ability = await client.get_ability(1)
        print(f"Ability: {ability['name']}")

asyncio.run(main())
```

### With Rate Limiting

```python
from tests.api.client import PokeAPIClient
from tests.utils.rate_limiter import RateLimiter

async def main():
    # Limit to 100 requests per minute
    rate_limiter = RateLimiter(max_requests=100, time_window=60)
    
    async with PokeAPIClient(rate_limiter=rate_limiter) as client:
        # Make requests - automatically rate limited
        for i in range(1, 151):
            pokemon = await client.get_pokemon(i)
            print(f"Got {pokemon['name']}")

asyncio.run(main())
```

### With Metrics Collection

```python
from tests.api.client import PokeAPIClient
from tests.utils.metrics import MetricsCollector  # To be implemented in Task 8

async def main():
    metrics = MetricsCollector()
    
    async with PokeAPIClient(metrics_collector=metrics) as client:
        # Metrics are automatically collected
        pokemon = await client.get_pokemon(1)
        
        # Metrics include:
        # - Request count per endpoint
        # - Latency per endpoint
        # - Failure count per endpoint and type

asyncio.run(main())
```

### Custom Configuration

```python
from tests.api.client import PokeAPIClient

async def main():
    client = PokeAPIClient(
        base_url="https://pokeapi.co/api/v2",
        timeout=15.0,  # 15 second timeout
        max_retries=5,  # 5 retry attempts
    )
    
    try:
        pokemon = await client.get_pokemon(1)
    finally:
        await client.close()

asyncio.run(main())
```

## API Methods

### `get_pokemon(pokemon_id: int) -> Dict[str, Any]`

Get Pokemon data by ID.

```python
pokemon = await client.get_pokemon(1)  # Bulbasaur
```

### `get_type(type_id: int) -> Dict[str, Any]`

Get Type data by ID.

```python
type_data = await client.get_type(1)  # Normal
```

### `get_ability(ability_id: int) -> Dict[str, Any]`

Get Ability data by ID.

```python
ability = await client.get_ability(1)  # Stench
```

### `get_circuit_breaker_state(endpoint: str) -> int`

Get circuit breaker state for an endpoint.

```python
state = client.get_circuit_breaker_state('pokemon')
# 0 = CLOSED, 1 = OPEN, 2 = HALF_OPEN
```

## Resilience Patterns

### Rate Limiting

The client supports optional rate limiting using a token bucket algorithm:

```python
from tests.utils.rate_limiter import RateLimiter

# 100 requests per minute
rate_limiter = RateLimiter(max_requests=100, time_window=60)
client = PokeAPIClient(rate_limiter=rate_limiter)
```

**Features:**
- Burst capacity up to max_requests
- Automatic token refill over time
- Async waiting when limit exceeded

### Circuit Breaker

Each endpoint has its own circuit breaker that:
- Tracks failure rate over 5-minute sliding window
- Opens after 50% failure rate over 10 requests
- Enters half-open state after 30 seconds
- Closes after 3 consecutive successes

**States:**
- `CLOSED (0)`: Normal operation
- `OPEN (1)`: Fast-fail, requests blocked
- `HALF_OPEN (2)`: Testing recovery

### Retry Logic

Automatic retry with exponential backoff:
- Max 3 retry attempts
- Wait times: 1s, 2s, 4s
- Random jitter (0-1s) added to each delay
- No retry on 4xx errors (except 429)

### 429 Rate Limit Handling

Special handling for rate limit responses:
- Respects `Retry-After` header
- Falls back to exponential backoff if header missing
- Adds jitter to prevent thundering herd

## Error Handling

### Network Errors

```python
import httpx

try:
    pokemon = await client.get_pokemon(1)
except httpx.RequestError as e:
    # Timeout, connection error, DNS error, etc.
    print(f"Network error: {e}")
```

### HTTP Errors

```python
try:
    pokemon = await client.get_pokemon(99999)
except httpx.HTTPStatusError as e:
    # 404, 500, etc.
    print(f"HTTP {e.response.status_code}: {e}")
```

### Circuit Breaker Open

```python
from tests.utils.circuit_breaker import CircuitBreakerOpenError

try:
    pokemon = await client.get_pokemon(1)
except CircuitBreakerOpenError as e:
    # Circuit is open, request blocked
    print(f"Circuit breaker open: {e}")
```

## Testing

The client includes comprehensive unit tests in `tests/unit/test_api_client.py`:

```bash
pytest tests/unit/test_api_client.py -v
```

## Integration with Other Components

### Pydantic Models (Task 4)

```python
from tests.models.pokemon import Pokemon

async def main():
    async with PokeAPIClient() as client:
        data = await client.get_pokemon(1)
        pokemon = Pokemon(**data)  # Validate with Pydantic
        print(f"Validated: {pokemon.name}")
```

### Database Storage (Task 6)

```python
from tests.utils.database import ResponseRepository

async def main():
    db = ResponseRepository()
    
    async with PokeAPIClient() as client:
        data = await client.get_pokemon(1)
        db.store_response('pokemon', 1, data)
```

### Metrics Collection (Task 8)

```python
from tests.utils.metrics import MetricsCollector

async def main():
    metrics = MetricsCollector()
    
    async with PokeAPIClient(metrics_collector=metrics) as client:
        await client.get_pokemon(1)
        # Metrics automatically recorded
```

## Configuration

### Environment Variables

```bash
# Base URL (optional, defaults to https://pokeapi.co/api/v2)
export POKEAPI_BASE_URL=https://pokeapi.co/api/v2
```

### Client Parameters

```python
PokeAPIClient(
    base_url: str = "https://pokeapi.co/api/v2",
    timeout: float = 10.0,
    rate_limiter: Optional[RateLimiter] = None,
    metrics_collector: Optional[Any] = None,
    max_retries: int = 3,
)
```

## Best Practices

1. **Always use context manager** for automatic cleanup:
   ```python
   async with PokeAPIClient() as client:
       # Use client
   ```

2. **Configure rate limiting** to be respectful of the API:
   ```python
   rate_limiter = RateLimiter(max_requests=100, time_window=60)
   ```

3. **Handle errors appropriately**:
   ```python
   try:
       data = await client.get_pokemon(id)
   except httpx.HTTPStatusError as e:
       if e.response.status_code == 404:
           # Handle not found
       else:
           # Handle other errors
   ```

4. **Monitor circuit breaker states**:
   ```python
   if client.get_circuit_breaker_state('pokemon') == 1:
       # Circuit is open, wait before retrying
   ```

## Performance

- **Async/await**: Non-blocking I/O for concurrent requests
- **Connection pooling**: HTTPX manages connection pool automatically
- **Efficient rate limiting**: Token bucket with minimal overhead
- **Smart retries**: Exponential backoff prevents overwhelming the API

## Dependencies

- `httpx>=0.25.2` - Async HTTP client
- `tenacity>=8.2.3` - Retry utilities (for reference)
- Python 3.11+ - Async/await support
