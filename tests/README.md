# Test Suite Overview

This directory contains the comprehensive test suite for the PokéAPI Observability Tests project.

## Directory Structure

```
tests/
├── conftest.py                 # Shared pytest fixtures
├── utils/                      # Test utilities and helpers
│   ├── database.py            # Database repository layer
│   └── __init__.py
├── property/                   # Property-based tests (Hypothesis)
│   ├── test_properties_storage.py
│   ├── test_database_module.py
│   ├── README.md
│   ├── RUNNING_TESTS.md
│   └── TASK_3.1_SUMMARY.md
├── unit/                       # Unit tests
├── integration/                # Integration tests
├── smoke/                      # Smoke tests
├── regression/                 # Regression tests
└── load/                       # Load tests
```

## Test Categories

### Property-Based Tests (`property/`)

Tests that verify universal properties using Hypothesis library. Each test generates 100+ random examples to verify correctness properties hold across all inputs.

**Current Tests:**
- ✅ Property 3: API responses are stored in database

**To Run:**
```bash
./scripts/run-property-tests.sh
# or
pytest tests/property/ -m property -v
```

### Unit Tests (`unit/`)

Tests for individual components in isolation.

**To Run:**
```bash
pytest tests/unit/ -v
```

### Integration Tests (`integration/`)

Tests that verify multiple components working together.

**To Run:**
```bash
pytest tests/integration/ -v
```

### Smoke Tests (`smoke/`)

Quick tests to verify basic functionality.

**To Run:**
```bash
pytest tests/smoke/ -m smoke -v
```

### Regression Tests (`regression/`)

Tests to prevent previously fixed bugs from reoccurring.

**To Run:**
```bash
pytest tests/regression/ -m regression -v
```

### Load Tests (`load/`)

Performance and stress tests using Locust.

**To Run:**
```bash
pytest tests/load/ -m load -v
```

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create environment file
cp .env.example .env
```

### 2. Start Services

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Verify services
docker-compose ps
```

### 3. Run Tests

```bash
# Validate setup
./scripts/validate-test-setup.sh

# Run all tests
pytest

# Run specific category
pytest tests/property/ -m property -v
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.smoke` - Quick smoke tests
- `@pytest.mark.regression` - Regression tests
- `@pytest.mark.load` - Load tests
- `@pytest.mark.property` - Property-based tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests

**Run tests by marker:**
```bash
pytest -m smoke
pytest -m property
pytest -m "not slow"
```

## Fixtures

Common fixtures are defined in `conftest.py`:

- `db_config` - Database configuration (session-scoped)
- `db_repository` - Database repository instance (function-scoped)
- `clean_db` - Clean database state for tests (function-scoped)

## Configuration

Test configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "smoke: Quick smoke tests",
    "regression: Regression tests",
    "load: Load tests",
    "property: Property-based tests",
]

[tool.hypothesis]
max_examples = 100
deadline = 5000
```

## Environment Variables

Required environment variables (set in `.env`):

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=pokeapi_cache
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# API
POKEAPI_BASE_URL=https://pokeapi.co/api/v2

# ReportPortal
REPORTPORTAL_ENDPOINT=http://localhost:8080
REPORTPORTAL_PROJECT=pokeapi-tests
REPORTPORTAL_API_TOKEN=your_token_here
```

## Troubleshooting

### Database Connection Errors

```bash
# Check PostgreSQL status
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Verify installation
python3 -c "import pytest, hypothesis, psycopg2"
```

### Test Failures

```bash
# Run with verbose output
pytest -vv

# Run with debugging
pytest -vv --pdb

# Run specific test
pytest tests/property/test_properties_storage.py::test_property_3_responses_stored_in_database -v
```

## Documentation

- **Property Tests**: See `tests/property/README.md`
- **Running Tests**: See `tests/property/RUNNING_TESTS.md`
- **Task 3.1 Summary**: See `tests/property/TASK_3.1_SUMMARY.md`

## Scripts

Helper scripts in `scripts/`:

- `validate-test-setup.sh` - Validate test environment
- `run-property-tests.sh` - Run property-based tests

## Contributing

When adding new tests:

1. Place tests in appropriate directory
2. Add appropriate pytest markers
3. Use existing fixtures from `conftest.py`
4. Follow naming convention: `test_*.py`
5. Add docstrings explaining what is tested
6. Update this README if adding new categories

## CI/CD Integration

Tests run automatically in CI/CD pipeline:

- Smoke tests: On every commit
- Regression tests: On every commit
- Property tests: On every commit
- Load tests: On schedule or manual trigger

Results are published to ReportPortal.

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Design Document](../.kiro/specs/pokeapi-observability-tests/design.md)
- [Requirements](../.kiro/specs/pokeapi-observability-tests/requirements.md)
