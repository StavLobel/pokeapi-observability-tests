# PokéAPI Observability Tests

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![pytest](https://img.shields.io/badge/pytest-7.4.3-green.svg)](https://docs.pytest.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg?logo=docker)](https://docs.docker.com/compose/)
[![Prometheus](https://img.shields.io/badge/metrics-prometheus-E6522C.svg?logo=prometheus)](https://prometheus.io/)
[![Grafana](https://img.shields.io/badge/dashboards-grafana-F46800.svg?logo=grafana)](https://grafana.com/)
[![ReportPortal](https://img.shields.io/badge/reporting-reportportal-039BE5.svg)](https://reportportal.io/)
[![Locust](https://img.shields.io/badge/load%20testing-locust-00C853.svg)](https://locust.io/)
[![Hypothesis](https://img.shields.io/badge/property%20testing-hypothesis-4B8BBE.svg)](https://hypothesis.readthedocs.io/)

A comprehensive QA automation infrastructure for testing the public PokéAPI (https://pokeapi.co) with full observability, metrics, logging, and historical data comparison capabilities.

## 🎯 Overview

This project provides:
- **Functional API Testing**: pytest-based tests using HTTPX with Pydantic validation
- **Load Testing**: Locust-based performance and stress testing
- **Observability**: Prometheus metrics, Grafana dashboards, and Loki log aggregation
- **Historical Comparison**: PostgreSQL-backed response caching for regression detection
- **Test Reporting**: ReportPortal integration with auto-analysis
- **CI/CD Integration**: GitHub Actions workflow for automated execution

## 🏗️ Architecture

The system runs entirely on Docker Compose with the following components:

- **Test Runner**: Python 3.11 + pytest + HTTPX
- **Locust**: Load testing with web UI
- **PostgreSQL**: Response cache and schema tracking
- **ReportPortal**: Test management and reporting
- **Prometheus**: Metrics storage and querying
- **Grafana**: Visualization dashboards
- **Loki + Promtail**: Log aggregation and shipping
- **pgAdmin**: Database management UI

## 📋 Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+ (for local development)
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/pokeapi-observability-tests.git
cd pokeapi-observability-tests
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Infrastructure

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps
```

### 4. Run Tests

```bash
# Run all tests
docker-compose exec test-runner pytest

# Run smoke tests only
docker-compose exec test-runner pytest -m smoke

# Run with coverage
docker-compose exec test-runner pytest --cov=tests --cov-report=html
```

## 📊 Accessing Services

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Grafana | http://localhost:3000 | admin / admin |
| ReportPortal | http://localhost:8080 | superadmin / erebus |
| Prometheus | http://localhost:9090 | - |
| Locust | http://localhost:8089 | - |
| pgAdmin | http://localhost:5050 | admin@example.com / admin |
| Metrics | http://localhost:8000/metrics | - |

## 🧪 Test Organization

Tests are organized by type using pytest marks:

```bash
# Smoke tests - Quick validation of core endpoints
pytest -m smoke

# Regression tests - Comprehensive functional tests
pytest -m regression

# Property tests - Property-based tests using Hypothesis
pytest -m property

# Load tests - Performance and stress tests
pytest -m load

# Integration tests - Full stack integration tests
pytest -m integration
```

## 📁 Project Structure

```
.
├── tests/                      # Test suites
│   ├── smoke/                  # Smoke tests
│   ├── regression/             # Regression tests
│   ├── load/                   # Load tests
│   ├── unit/                   # Unit tests
│   ├── property/               # Property-based tests
│   ├── integration/            # Integration tests
│   └── conftest.py             # Pytest fixtures
├── locust/                     # Locust load test scripts
│   ├── locustfile.py           # Main locust configuration
│   ├── tasks/                  # Load test tasks
│   └── config/                 # Load test profiles
├── config/                     # Configuration files
│   ├── prometheus/             # Prometheus config
│   ├── grafana/                # Grafana dashboards
│   └── loki/                   # Loki config
├── docker/                     # Docker-related files
├── requirements.txt            # Core dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml              # Project configuration
├── docker-compose.yml          # Docker Compose services
└── README.md                   # This file
```

## 🔧 Local Development

### Setup Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt
```

### Run Tests Locally

```bash
# Ensure services are running
docker-compose up -d postgres reportportal-api prometheus

# Run tests
pytest

# Run with specific markers
pytest -m smoke
pytest -m "smoke or regression"

# Run with coverage
pytest --cov=tests --cov-report=html
open htmlcov/index.html
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy tests/

# Run all quality checks
make lint  # If Makefile is created
```

## 📈 Metrics and Observability

### Custom Prometheus Metrics

- `pokeapi_requests_total`: Total API requests by endpoint
- `pokeapi_request_duration_seconds`: Request latency histogram
- `pokeapi_failures_total`: Failed requests by endpoint and type
- `pokeapi_schema_changes_total`: Schema changes detected
- `pokeapi_test_flakiness_total`: Flaky test occurrences

### Grafana Dashboards

Pre-configured dashboards available at http://localhost:3000:

1. **API Performance**: Response times, request rates, error rates
2. **Test Execution**: Pass/fail rates, test trends, failure analysis
3. **Locust Load Tests**: Virtual users, throughput, latency percentiles
4. **Performance Baselines**: Historical comparison and regression detection

### Structured Logging

Logs are collected by Promtail and shipped to Loki with metadata:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "test_name": "test_get_pokemon",
  "endpoint": "/pokemon/1",
  "status_code": 200,
  "message": "API request successful"
}
```

Query logs in Grafana using LogQL:
```
{container_name="test-runner"} |= "test_get_pokemon"
```

## 🔄 CI/CD Integration

### GitHub Actions

The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:

1. Runs on every push and pull request
2. Executes linting and type checking
3. Runs all test suites
4. Publishes results to ReportPortal
5. Uploads test artifacts
6. Supports manual triggers with test suite selection

### Running in CI

Tests automatically run in CI with:
- Docker Compose for service orchestration
- GitHub Secrets for sensitive credentials
- Artifact uploads for test reports and logs

## 🔐 Secrets Management

### Local Development

Use `.env` file (never commit):
```bash
cp .env.example .env
# Edit .env with real credentials
```

### CI/CD

Configure GitHub Secrets:
- `REPORTPORTAL_API_TOKEN`
- `POSTGRES_PASSWORD`
- `GRAFANA_ADMIN_PASSWORD`

### Secrets Scanning

Pre-commit hooks scan for leaked credentials:
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

## 🐛 Troubleshooting

### Services Not Starting

```bash
# Check service logs
docker-compose logs test-runner
docker-compose logs postgres

# Restart services
docker-compose restart

# Rebuild containers
docker-compose up -d --build
```

### Database Connection Issues

```bash
# Check PostgreSQL is healthy
docker-compose exec postgres pg_isready

# Connect to database
docker-compose exec postgres psql -U postgres -d pokeapi_cache
```

### ReportPortal Not Receiving Results

1. Verify ReportPortal is running: http://localhost:8080
2. Check API token in `.env` matches ReportPortal
3. Verify project name matches in `pytest.ini`
4. Check test-runner logs for connection errors

### Tests Failing Due to Rate Limits

PokéAPI has rate limits. The framework includes:
- Rate limiter (100 req/min default)
- Exponential backoff with jitter
- Circuit breaker pattern

Adjust in `.env`:
```bash
MAX_REQUESTS_PER_MINUTE=50
CIRCUIT_BREAKER_ENABLED=true
```

## 📚 Additional Resources

- [PokéAPI Documentation](https://pokeapi.co/docs/v2)
- [pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)
- [ReportPortal Documentation](https://reportportal.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- QA Team - Initial work

## 🙏 Acknowledgments

- PokéAPI team for providing the public API
- Open source community for the amazing tools
