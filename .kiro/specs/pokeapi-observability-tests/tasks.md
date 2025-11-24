# Implementation Plan

> **Note:** Each top-level task represents a main phase and should have a corresponding GitHub issue opened.

## Phase 1: 🏗️ Project Foundation & Infrastructure

- [x] 1. 📦 Set up project structure and dependencies
  - ✅ Create project directory structure (tests/, locust/, config/, docker/)
  - ✅ Create requirements.txt with core dependencies (pytest, httpx, pydantic, prometheus-client, psycopg2, tenacity, python-dotenv)
  - ✅ Create requirements-dev.txt with dev dependencies (pytest plugins, hypothesis, black, ruff, mypy, truffleHog)
  - ✅ Create pyproject.toml for project configuration
  - ✅ Create .gitignore for Python projects
  - ✅ Create .dockerignore for Docker builds
  - ✅ Create .env.example with placeholder credentials
  - ✅ Create README.md with project overview and setup instructions
  - _Requirements: 1.1, 2.1, 16.4, 20.1_
  - **GitHub Issue: "Project Foundation Setup"**

- [ ] 2. 🐳 Create Docker Compose infrastructure
  - Create docker-compose.yml with all service definitions
  - Configure test-runner service with Python 3.11, volume mounts, port 8000, and health check
  - Create Dockerfile for test-runner with multi-stage build
  - Configure postgres service with persistent volume, initialization scripts, and health check
  - Configure reportportal services (ui, api, analyzer, postgres) with health checks
  - Configure prometheus service with scrape configuration and health check
  - Configure grafana service with provisioned datasources and health check
  - Configure loki service with persistent volume and health check
  - Configure promtail service with log collection configuration
  - Configure locust service with port 8089 and volume mounts
  - Configure locust-exporter service with port 9646
  - Configure pgadmin service with port 5050
  - Create docker-compose.override.yml.example for local customization
  - Add restart policies for all services
  - _Requirements: 1.1-1.10, 20.2, 20.3, 20.4, 20.5_
  - **GitHub Issue: "Docker Compose Infrastructure"**

- [ ] 3. 🗄️ Create PostgreSQL database schema
  - Create docker/postgres/init.sql with database initialization
  - Create api_responses table with indexes
  - Create schema_versions table with indexes
  - Create schema_changes table with indexes
  - Create performance_baselines table with indexes
  - Create flaky_tests table with indexes
  - _Requirements: 1.4, 5.1-5.3, 17.2, 18.1_

- [ ]* 3.1 🧪 Write property test for database schema initialization
  - **Property 3: API responses are stored in database**
  - **Validates: Requirements 5.1, 5.2, 5.3**

## Phase 2: 🔧 Core API Testing Framework

- [ ] 4. 📋 Implement Pydantic models for API validation
  - Create tests/models/__init__.py
  - Create tests/models/pokemon.py with Pokemon, PokemonType, PokemonAbility, PokemonStat, PokemonSprite models
  - Create tests/models/type.py with Type, TypePokemon models
  - Create tests/models/ability.py with Ability, EffectEntry models
  - Configure all models with extra="allow" for forward compatibility
  - Add comprehensive field validation and type hints
  - _Requirements: 2.2, 3.1-3.5_

- [ ]* 4.1 🧪 Write property test for Pydantic required fields validation
  - **Property 1: Pydantic schema validation enforces required fields**
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.5**

- [ ]* 4.2 🧪 Write property test for Pydantic extra fields handling
  - **Property 2: Pydantic models allow extra fields**
  - **Validates: Requirements 3.4**

- [ ] 5. 🌐 Implement HTTPX API client with resilience patterns
  - Create tests/api/__init__.py
  - Create tests/api/endpoints.py with endpoint URL constants
  - Create tests/api/client.py with PokeAPIClient class
  - Implement async methods: get_pokemon(), get_type(), get_ability()
  - Add timeout configuration (default 10s)
  - Add retry logic with exponential backoff using tenacity library (max 3 retries)
  - Add jitter to retry delays (random 0-1s)
  - Handle 429 rate limit responses with Retry-After header respect
  - Add error handling for network errors and HTTP errors
  - Integrate with MetricsCollector for request tracking
  - _Requirements: 2.1, 7.1, 7.2, 14.1, 14.3_

- [ ] 5.1 🛡️ Implement rate limiter
  - Create tests/utils/__init__.py
  - Create tests/utils/rate_limiter.py with RateLimiter class
  - Implement token bucket algorithm for rate limiting
  - Configure max requests per time window (default: 100 req/min)
  - Add async acquire() method to wait when limit exceeded
  - Integrate with PokeAPIClient
  - _Requirements: 14.4_

- [ ] 5.2 🔌 Implement circuit breaker pattern
  - Create tests/utils/circuit_breaker.py with CircuitBreaker class
  - Track failure rate per endpoint (5-minute sliding window)
  - Open circuit after 50% failure rate over 10 requests
  - Half-open after 30 seconds to test recovery
  - Close circuit after 3 consecutive successes
  - Expose circuit state as Prometheus gauge metric
  - _Requirements: 14.2, 14.5_

- [ ] 6. 💾 Implement database repository layer
  - Create tests/utils/database.py with ResponseRepository class
  - Implement store_response() method with UPSERT logic
  - Implement get_latest_response() method for historical comparison
  - Implement store_schema_version() method
  - Implement get_latest_schema() method
  - Add connection pooling and error handling
  - _Requirements: 5.1-5.3_

- [ ] 7. 🔍 Implement schema tracking functionality
  - Create tests/utils/schema_tracker.py with SchemaTracker class
  - Implement extract_schema_structure() to extract schema from JSON
  - Implement compare_schemas() to detect added/removed/modified fields
  - Return SchemaDiff object with change details
  - _Requirements: 4.1, 4.2_

- [ ]* 7.1 🧪 Write property test for schema change detection
  - **Property 4: Schema comparison detects changes**
  - **Validates: Requirements 4.1, 4.2**

- [ ]* 7.2 🧪 Write property test for schema persistence
  - **Property 5: Schema changes are persisted**
  - **Validates: Requirements 4.3**

- [ ]* 7.3 🧪 Write property test for unchanged schema handling
  - **Property 7: Unchanged schemas skip extra logging**
  - **Validates: Requirements 4.5**

## Phase 3: 📊 Observability & Metrics

- [ ] 8. 📈 Implement Prometheus metrics collection
  - Create tests/utils/metrics.py with MetricsCollector class
  - Define counter metric: pokeapi_requests_total with endpoint label
  - Define histogram metric: pokeapi_request_duration_seconds with endpoint label
  - Define counter metric: pokeapi_failures_total with endpoint and failure_type labels
  - Define counter metric: pokeapi_schema_changes_total with endpoint label
  - Define gauge metric: pokeapi_circuit_breaker_state with endpoint label
  - Implement methods: increment_request_counter(), record_latency(), increment_failure_counter(), increment_schema_change_counter()
  - Create simple Flask/FastAPI app to expose metrics on /metrics endpoint (port 8000)
  - _Requirements: 1.2, 7.1-7.5_

- [ ]* 8.1 🧪 Write property test for request metrics
  - **Property 11: Request metrics are incremented**
  - **Validates: Requirements 7.1**

- [ ]* 8.2 🧪 Write property test for latency metrics
  - **Property 12: Latency metrics are recorded**
  - **Validates: Requirements 7.2**

- [ ]* 8.3 🧪 Write property test for failure metrics
  - **Property 13: Failure metrics are incremented**
  - **Validates: Requirements 7.3**

- [ ]* 8.4 🧪 Write property test for schema change metrics
  - **Property 14: Schema change metrics are incremented**
  - **Validates: Requirements 7.4**

- [ ]* 8.5 🧪 Write property test for metrics exposure
  - **Property 15: All metrics are exposed**
  - **Validates: Requirements 7.5**

- [ ] 9. 📝 Implement structured logging with secrets masking
  - Create tests/utils/logger.py with structured logging configuration
  - Configure python-json-logger for JSON output
  - Add log fields: timestamp, level, test_name, message, endpoint, status_code
  - Implement mask_sensitive_data() function to mask tokens, passwords, secrets
  - Implement context manager for test-specific logging
  - Configure log levels (DEBUG, INFO, WARNING, ERROR)
  - _Requirements: 9.1-9.3, 16.2_

- [ ]* 9.1 🧪 Write property test for structured log format
  - **Property 16: Structured logs contain required fields**
  - **Validates: Requirements 9.1**

- [ ]* 9.2 🧪 Write property test for API request logging
  - **Property 17: API request logs contain details**
  - **Validates: Requirements 9.2**

- [ ]* 9.3 🧪 Write property test for failure logging
  - **Property 18: Failure logs contain details**
  - **Validates: Requirements 9.3**

- [ ] 10. ⚙️ Configure Prometheus scraping
  - Create config/prometheus/prometheus.yml with scrape configurations
  - Add scrape job for test-runner:8000/metrics
  - Add scrape job for locust-exporter:9646/metrics
  - Configure scrape interval (15s)
  - Configure retention period (15 days)
  - _Requirements: 1.5, 7.5_

- [ ] 11. 📋 Configure Loki and Promtail
  - Create config/loki/loki-config.yml for Loki configuration
  - Create config/promtail/promtail-config.yml for log collection
  - Configure Promtail to collect test-runner container logs
  - Add labels: container_name, service, environment
  - Configure log retention (7 days)
  - _Requirements: 1.7, 1.8, 9.4_

- [ ]* 11.1 🧪 Write property test for log shipping
  - **Property 19: Logs are shipped with metadata**
  - **Validates: Requirements 9.4**

- [ ] 11.2 🔐 Implement secrets management
  - Create tests/utils/config.py for centralized configuration management
  - Load environment variables from .env file using python-dotenv
  - Validate required environment variables on startup
  - Provide default values for optional configuration
  - _Requirements: 16.1, 16.2, 16.4_

- [ ] 11.3 🔍 Implement secrets scanning
  - Create .pre-commit-config.yaml with secrets scanning
  - Add truffleHog to pre-commit hooks
  - Configure truffleHog to fail on detected secrets
  - _Requirements: 16.5_

- [ ] 11.4 📊 Implement performance baseline tracking
  - Create tests/utils/performance_tracker.py with PerformanceTracker class
  - Implement calculate_baseline() to compute P50, P95, P99 from last 7 days
  - Implement check_regression() to compare current vs baseline (20% threshold)
  - Implement store_baseline() to save baseline versions
  - Store performance metrics in performance_baselines table
  - Log performance regression warnings
  - _Requirements: 18.1, 18.2, 18.3, 18.5_

- [ ] 11.5 🎯 Implement flakiness detection
  - Create tests/utils/flakiness_tracker.py with FlakinessTracker class
  - Track flaky test occurrences in flaky_tests table
  - Expose flakiness metrics to Prometheus
  - Implement pytest hook to detect and record flaky tests
  - _Requirements: 17.1, 17.2, 17.3, 17.4_

## Phase 4: 📊 Grafana Dashboards

- [ ] 12. 🎨 Create Grafana dashboard configurations
  - Create config/grafana/provisioning/datasources/datasources.yml
  - Configure Prometheus datasource with URL http://prometheus:9090
  - Configure Loki datasource with URL http://loki:3100
  - _Requirements: 1.6_
  - **GitHub Issue: "Grafana Dashboards & Visualization"**

- [ ] 13. 🚀 Create API Performance dashboard
  - Create config/grafana/dashboards/api-performance.json
  - Add panel: Response latency by endpoint (line graph from histogram)
  - Add panel: Request rate by endpoint (rate of counter)
  - Add panel: Error rate percentage (gauge)
  - Add panel: P95 latency by endpoint (stat)
  - _Requirements: 8.1_

- [ ] 14. ✅ Create Test Execution dashboard
  - Create config/grafana/dashboards/test-execution.json
  - Add panel: Test pass/fail rate (pie chart)
  - Add panel: Tests executed over time (line graph)
  - Add panel: Failure types distribution (bar chart)
  - Add panel: Schema changes timeline (table)
  - _Requirements: 8.2, 8.5_

- [ ] 15. 📉 Create Locust Load Test dashboard
  - Create config/grafana/dashboards/locust-load-tests.json
  - Add panel: Virtual users over time (area graph)
  - Add panel: Request duration percentiles (line graph)
  - Add panel: Requests per second (line graph)
  - Add panel: Failed requests (stat)
  - Add panel: Response time distribution (histogram)
  - _Requirements: 8.4_

- [ ] 15.1 📈 Create Performance Baseline dashboard
  - Create config/grafana/dashboards/performance-baselines.json
  - Add panel: Current vs baseline latency comparison (line graph)
  - Add panel: Performance regression alerts (table)
  - Add panel: Baseline history over time (line graph)
  - Add panel: Deviation from baseline percentage (gauge)
  - _Requirements: 18.4_

- [ ] 15.2 🚨 Configure Prometheus alerting rules
  - Create config/prometheus/alerting_rules.yml
  - Add alert: HighAPILatency (P95 > 500ms for 5 min)
  - Add alert: HighTestFailureRate (>10% failures for 10 min)
  - Add alert: SchemaChangeDetected (any schema change)
  - Add alert: CircuitBreakerOpen (circuit open for 2 min)
  - Configure alert labels and annotations
  - Update prometheus.yml to include alerting_rules.yml
  - _Requirements: 15.1, 15.2, 15.3, 15.5_

- [ ]* 15.3 🔔 Configure Grafana alerting
  - Configure Grafana to use Prometheus alert rules
  - Set up alert notification channels (email, optional Slack)
  - Configure notification policies
  - Document alert setup in README
  - _Requirements: 15.4_

## Phase 5: 📋 ReportPortal Integration

- [ ] 16. 🔗 Configure ReportPortal integration
  - Update pytest.ini with reportportal configuration (already has basic config)
  - Configure RP endpoint, project name, API token from environment variables
  - Configure launch name, description, and tags
  - _Requirements: 2.3, 10.1-10.5, 19.1-19.5_
  - **GitHub Issue: "ReportPortal Integration"**

- [ ]* 16.1 📚 Create ReportPortal setup guide
  - Add ReportPortal setup section to README.md
  - Document how to start ReportPortal services
  - Document default credentials and first login
  - Document project creation steps
  - Document API token generation
  - Document auto-analysis configuration
  - Add troubleshooting section
  - _Requirements: 19.2, 19.3, 19.4_

- [ ] 17. 🔧 Implement pytest fixtures for ReportPortal
  - Create tests/conftest.py with pytest fixtures
  - Add fixture for database connection
  - Add fixture for API client
  - Add fixture for metrics collector
  - Add fixture for attaching response payloads to ReportPortal
  - Add fixture for attaching logs to ReportPortal
  - Add fixture for launch metadata
  - _Requirements: 2.3, 10.3_

- [ ]* 17.1 🧪 Write property test for ReportPortal test reporting
  - **Property 21: Test results are sent to ReportPortal**
  - **Validates: Requirements 2.3, 10.2**

- [ ]* 17.2 🧪 Write property test for ReportPortal launch creation
  - **Property 22: ReportPortal launches have metadata**
  - **Validates: Requirements 10.1**

- [ ]* 17.3 🧪 Write property test for ReportPortal launch tagging
  - **Property 23: ReportPortal launches are tagged by suite**
  - **Validates: Requirements 10.3**

- [ ]* 17.4 🧪 Write property test for ReportPortal attachments
  - **Property 24: Attachments are uploaded to ReportPortal**
  - **Validates: Requirements 10.5**

## Phase 6: 🧪 Test Implementation

- [ ] 18. ✅ Implement smoke tests
  - Create tests/smoke/test_basic_endpoints.py
  - Test GET /pokemon/1 (Bulbasaur) with schema validation
  - Test GET /type/1 (Normal) with schema validation
  - Test GET /ability/1 (Stench) with schema validation
  - Mark tests with @pytest.mark.smoke
  - Add response storage and metrics collection
  - _Requirements: 13.1-13.3_
  - **GitHub Issue: "Initial Test Suite Implementation"**

- [ ] 19. 📄 Implement regression tests for pagination
  - Create tests/regression/test_pagination.py
  - Test GET /pokemon?limit=20&offset=0
  - Test GET /pokemon?limit=50&offset=100
  - Validate pagination fields (count, next, previous, results)
  - Mark tests with @pytest.mark.regression
  - _Requirements: 13.4_

- [ ] 20. ❌ Implement regression tests for error handling
  - Create tests/regression/test_error_handling.py
  - Test GET /pokemon/0 (invalid ID) expects 404
  - Test GET /pokemon/-1 (negative ID) expects 404
  - Test GET /pokemon/999999 (non-existent) expects 404
  - Test GET /type/999 (non-existent) expects 404
  - Mark tests with @pytest.mark.regression
  - _Requirements: 13.5_

- [ ] 20.1 🧪 Write property test for invalid resource IDs
  - **Property 32: Invalid resource IDs return errors**
  - **Validates: Requirements 13.5**

- [ ] 21. 🔄 Implement data comparison tests
  - Create tests/regression/test_data_comparison.py
  - Test historical data comparison for pokemon endpoint
  - Test detection of changed field values
  - Test logging of field diffs
  - Mark tests with @pytest.mark.regression
  - _Requirements: 5.4-5.6_

- [ ] 21.1 🧪 Write property test for data difference detection
  - **Property 8: Data differences are identified**
  - **Validates: Requirements 5.4**

- [ ] 21.2 🧪 Write property test for data difference logging
  - **Property 9: Data differences are logged**
  - **Validates: Requirements 5.5**

- [ ] 21.3 🧪 Write property test for data difference reporting
  - **Property 10: Data differences are reported**
  - **Validates: Requirements 5.6**

- [ ] 22. ✔️ Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 7: 🦗 Load Testing with Locust

- [ ] 23. 📝 Implement Locust load test scripts
  - Create locust/locustfile.py with PokeAPIUser class
  - Configure wait_time between requests (1-3 seconds)
  - Configure host URL (https://pokeapi.co/api/v2)
  - _Requirements: 6.1_
  - **GitHub Issue: "Locust Load Testing Implementation"**

- [ ] 24. 🎯 Implement Locust tasks
  - Create locust/tasks/pokemon_tasks.py with pokemon endpoint tasks
  - Create locust/tasks/type_tasks.py with type endpoint tasks
  - Create locust/tasks/ability_tasks.py with ability endpoint tasks
  - Configure task weights (pokemon: 3, type: 1, ability: 1)
  - Add response validation in tasks
  - _Requirements: 6.1_

- [ ] 25. 📊 Configure Locust metrics export
  - Configure locust-exporter in docker-compose.yml
  - Verify metrics exposed on port 9646
  - Test Prometheus scraping of Locust metrics
  - _Requirements: 6.3_

- [ ] 25.1 🧪 Write property test for Locust statistics
  - **Property 26: Locust generates statistics**
  - **Validates: Requirements 6.2**

- [ ] 25.2 🧪 Write property test for Locust metrics export
  - **Property 27: Locust exports metrics**
  - **Validates: Requirements 6.3**

- [ ] 25.3 🧪 Write property test for Locust summary reports
  - **Property 28: Locust generates summary reports**
  - **Validates: Requirements 6.4**

- [ ] 26. ⚙️ Create Locust load test profiles
  - Create locust/config/load_profiles.py with different load scenarios
  - Profile 1: Light load (10 users, 2 min duration)
  - Profile 2: Medium load (50 users, 5 min duration)
  - Profile 3: Heavy load (100 users, 10 min duration)
  - Document how to run each profile
  - _Requirements: 6.5_

## Phase 8: 🚀 CI/CD Pipeline

- [ ] 27. 📋 Create GitHub Actions workflow
  - Create .github/workflows/ci.yml
  - Configure workflow triggers (push, pull_request, workflow_dispatch)
  - Add manual trigger inputs for test suite selection
  - _Requirements: 11.1, 11.6_
  - **GitHub Issue: "CI/CD Pipeline Setup"**

- [ ] 28. 📦 Implement CI job for dependency installation
  - Add job step to set up Python 3.11
  - Add job step to install dependencies from requirements.txt
  - Add job step to install dev dependencies
  - Cache pip dependencies for faster builds
  - _Requirements: 11.2_

- [ ] 29. 🧹 Implement CI job for linting and type checking
  - Add job step to run ruff linter
  - Add job step to run black formatter check
  - Add job step to run mypy type checker
  - Add job step to run secrets scanning with truffleHog
  - Fail build on linting errors or detected secrets
  - _Requirements: 11.2, 16.5_

- [ ] 30. 🧪 Implement CI job for pytest execution
  - Add job step to start Docker Compose services
  - Add job step to wait for services to be healthy
  - Add job step to load secrets from GitHub Secrets to environment
  - Add job step to run pytest with coverage
  - Add job step to run smoke tests
  - Add job step to run regression tests
  - Configure pytest-reportportal with CI environment variables
  - _Requirements: 11.3, 16.3_

- [ ] 30.1 🧪 Write property test for CI test execution
  - **Property 29: CI/CD executes tests and publishes results**
  - **Validates: Requirements 11.3**

- [ ] 31. 🦗 Implement CI job for Locust load tests
  - Add job step to run Locust in headless mode
  - Configure load test parameters (users, duration)
  - Export Locust metrics to JSON
  - Upload Locust results as artifacts
  - _Requirements: 11.4_

- [ ] 31.1 🧪 Write property test for CI load test execution
  - **Property 30: CI/CD executes load tests**
  - **Validates: Requirements 11.4**

- [ ] 32. 📤 Implement CI job for artifact uploads
  - Add job step to upload pytest HTML report
  - Add job step to upload coverage report
  - Add job step to upload Locust results
  - Add job step to upload test logs
  - Configure artifact retention (30 days)
  - _Requirements: 11.5_

- [ ] 32.1 🧪 Write property test for CI artifact uploads
  - **Property 31: CI/CD uploads artifacts**
  - **Validates: Requirements 11.5**

- [ ] 33. 🏷️ Implement pytest mark filtering
  - Configure pytest.ini with custom marks
  - Test running pytest -m smoke
  - Test running pytest -m regression
  - Test running pytest -m load
  - Verify only marked tests execute
  - _Requirements: 12.1-12.6_

- [ ] 33.1 🧪 Write property test for pytest mark filtering
  - **Property 25: Pytest marks filter test execution**
  - **Validates: Requirements 2.4, 12.4, 12.5, 12.6**

## Phase 9: 📚 Documentation & Finalization

- [ ] 34. 📖 Create comprehensive documentation
  - Update README.md with architecture overview
  - Document Docker Compose setup and usage
  - Document how to run tests locally
  - Document how to access Grafana dashboards
  - Document how to access ReportPortal
  - Document how to run Locust load tests
  - Create CONTRIBUTING.md with development guidelines
  - **GitHub Issue: "Documentation & Project Finalization"**

- [ ] 35. ⚙️ Create configuration examples
  - Create .env.example with all required environment variables
  - Document ReportPortal configuration
  - Document Prometheus configuration
  - Document Grafana datasource configuration
  - Create docker-compose.override.yml.example for local customization

- [ ] 36. 🛠️ Add project quality tools
  - Create .pre-commit-config.yaml for pre-commit hooks
  - Configure ruff, black, mypy in pre-commit
  - Create Makefile with common commands (test, lint, format, docker-up, docker-down)
  - Add pytest coverage configuration in pyproject.toml

- [ ] 37. ✅ Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
  - Run full test suite (smoke, regression, property tests)
  - Verify all Docker services start successfully
  - Verify Grafana dashboards display data
  - Verify ReportPortal receives test results
  - Verify Prometheus collects metrics
  - Verify Loki receives logs
  - Run Locust load test and verify metrics
  - Run CI/CD pipeline end-to-end
