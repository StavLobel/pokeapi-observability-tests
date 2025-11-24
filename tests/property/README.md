# Property-Based Tests

This directory contains property-based tests using the Hypothesis library.

## Running Property Tests

### Prerequisites

1. **Start Docker services:**
   ```bash
   docker-compose up -d postgres
   ```

2. **Verify database is ready:**
   ```bash
   docker-compose ps postgres
   ```

### Run All Property Tests

```bash
pytest tests/property/ -m property -v
```

### Run Specific Property Test

```bash
pytest tests/property/test_properties_storage.py::test_property_3_responses_stored_in_database -v
```

### Run with More Examples

```bash
pytest tests/property/ -m property --hypothesis-show-statistics
```

## Property Test: Database Schema Initialization (Property 3)

**File:** `test_properties_storage.py::test_property_3_responses_stored_in_database`

**Property:** For any successful API response from pokemon, type, or ability endpoints, the complete JSON response shall be stored in PostgreSQL with endpoint name, resource ID, and timestamp.

**Validates:** Requirements 5.1, 5.2, 5.3

**Test Strategy:**
- Generates random endpoint names (pokemon, type, ability)
- Generates random resource IDs (1-1000)
- Generates random response structures matching each endpoint type
- Stores each response in the database
- Verifies the response can be retrieved with all fields intact
- Runs 100 examples by default (configurable via Hypothesis settings)

**Expected Behavior:**
- All responses should be stored successfully
- Retrieved responses should match stored data exactly
- Timestamps should be automatically added
- No data loss or corruption should occur

## Troubleshooting

### Database Connection Errors

If you see connection errors:

1. Check if PostgreSQL is running:
   ```bash
   docker-compose ps postgres
   ```

2. Check database logs:
   ```bash
   docker-compose logs postgres
   ```

3. Verify environment variables:
   ```bash
   cat .env
   ```

4. Test connection manually:
   ```bash
   docker-compose exec postgres psql -U postgres -d pokeapi_cache -c "SELECT 1;"
   ```

### Property Test Failures

If property tests fail:

1. Check the counterexample provided by Hypothesis
2. Run with `--hypothesis-show-statistics` to see test distribution
3. Use `--hypothesis-seed=<seed>` to reproduce a specific failure
4. Check database state after failure:
   ```bash
   docker-compose exec postgres psql -U postgres -d pokeapi_cache -c "SELECT COUNT(*) FROM api_responses;"
   ```

## Configuration

Property test configuration is in `pyproject.toml`:

```toml
[tool.hypothesis]
max_examples = 100
deadline = 5000
derandomize = false
```

You can override these settings per-test using the `@settings` decorator.
