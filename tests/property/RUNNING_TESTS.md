# Running Property Test 3.1: Database Schema Initialization

This guide explains how to run the property-based test for database schema initialization.

## Test Overview

**Test:** `test_property_3_responses_stored_in_database`  
**File:** `tests/property/test_properties_storage.py`  
**Property:** API responses are stored in database  
**Validates:** Requirements 5.1, 5.2, 5.3

## Prerequisites

### 1. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Start Docker Services

```bash
# Start PostgreSQL database
docker-compose up -d postgres

# Verify PostgreSQL is running
docker-compose ps postgres

# Check logs if needed
docker-compose logs postgres
```

### 3. Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# The default values should work for local development:
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=pokeapi_cache
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=postgres
```

### 4. Verify Database Schema

```bash
# Connect to database and verify tables exist
docker-compose exec postgres psql -U postgres -d pokeapi_cache

# In psql, run:
\dt

# You should see 5 tables:
# - api_responses
# - schema_versions
# - schema_changes
# - performance_baselines
# - flaky_tests

# Exit psql
\q
```

## Running the Test

### Option 1: Using the Helper Script (Recommended)

```bash
# Run all property tests
./scripts/run-property-tests.sh

# Run with verbose output
./scripts/run-property-tests.sh -vv

# Run with Hypothesis statistics
./scripts/run-property-tests.sh --hypothesis-show-statistics
```

### Option 2: Using pytest Directly

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=pokeapi_cache
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres

# Run the specific property test
pytest tests/property/test_properties_storage.py::test_property_3_responses_stored_in_database -v

# Run all property tests
pytest tests/property/ -m property -v

# Run with Hypothesis statistics
pytest tests/property/ -m property --hypothesis-show-statistics
```

### Option 3: Using Docker Test Runner

```bash
# Build and run tests in Docker
docker-compose run --rm test-runner pytest tests/property/test_properties_storage.py::test_property_3_responses_stored_in_database -v
```

## Expected Output

### Successful Test Run

```
tests/property/test_properties_storage.py::test_property_3_responses_stored_in_database PASSED [100%]

============================== Hypothesis Statistics ===============================

test_property_3_responses_stored_in_database:
  - during generate phase (0.50 seconds):
    - Typical runtimes: 1-5 ms, ~ 50% in data generation
    - 100 passing examples, 0 failing examples, 0 invalid examples
  - Stopped because settings.max_examples=100

================================ 1 passed in 5.23s =================================
```

### Test Failure

If the test fails, Hypothesis will provide a counterexample:

```
Falsifying example: test_property_3_responses_stored_in_database(
    clean_db=<ResponseRepository object>,
    endpoint='pokemon',
    resource_id=42,
    response_data={'id': 42, 'name': 'test', ...}
)
```

This counterexample can be used to reproduce and debug the failure.

## Troubleshooting

### Database Connection Errors

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**
1. Verify PostgreSQL is running: `docker-compose ps postgres`
2. Check if port 5432 is available: `lsof -i :5432`
3. Verify environment variables are set correctly
4. Check Docker logs: `docker-compose logs postgres`

### Schema Not Initialized

**Error:** `relation "api_responses" does not exist`

**Solutions:**
1. Restart PostgreSQL to trigger init script:
   ```bash
   docker-compose down postgres
   docker-compose up -d postgres
   ```

2. Manually run init script:
   ```bash
   docker-compose exec postgres psql -U postgres -d pokeapi_cache -f /docker-entrypoint-initdb.d/init.sql
   ```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'hypothesis'`

**Solution:**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Permission Errors

**Error:** `permission denied while trying to connect to the Docker daemon socket`

**Solution:**
```bash
# Add your user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo (not recommended)
sudo docker-compose up -d postgres
```

## Test Configuration

The test is configured in `pyproject.toml`:

```toml
[tool.hypothesis]
max_examples = 100        # Number of test cases to generate
deadline = 5000           # Maximum time per test case (ms)
derandomize = false       # Allow randomization

[tool.pytest.ini_options]
markers = [
    "property: Property-based tests using Hypothesis",
]
```

You can override these settings in the test using the `@settings` decorator.

## Debugging Tips

### 1. Run with Specific Seed

To reproduce a specific test run:

```bash
pytest tests/property/test_properties_storage.py --hypothesis-seed=12345
```

### 2. Increase Verbosity

```bash
pytest tests/property/test_properties_storage.py -vv --hypothesis-verbosity=verbose
```

### 3. Check Database State

```bash
# Count stored responses
docker-compose exec postgres psql -U postgres -d pokeapi_cache -c "SELECT COUNT(*) FROM api_responses;"

# View recent responses
docker-compose exec postgres psql -U postgres -d pokeapi_cache -c "SELECT endpoint, resource_id, created_at FROM api_responses ORDER BY created_at DESC LIMIT 10;"

# Clear test data
docker-compose exec postgres psql -U postgres -d pokeapi_cache -c "DELETE FROM api_responses;"
```

### 4. Run with Python Debugger

```python
# Add breakpoint in test
import pdb; pdb.set_trace()

# Run pytest with -s flag
pytest tests/property/test_properties_storage.py -s
```

## Next Steps

After this test passes:

1. ✅ Property 3 is validated
2. Move to next task: Implement Pydantic models (Task 4)
3. Continue with remaining property tests (Properties 4-10)

## References

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
