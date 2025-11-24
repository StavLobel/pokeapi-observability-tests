# Docker Infrastructure Documentation

## Overview

The PokéAPI Observability Tests project uses Docker Compose to orchestrate a complete testing and observability infrastructure. This document provides detailed information about the Docker setup, services, networking, and troubleshooting.

## Architecture

### Service Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Docker Network: pokeapi-network              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Test Runner  │───▶│  PostgreSQL  │    │   pgAdmin    │      │
│  │ Python+pytest│    │ Response DB  │◀───│  DB Viewer   │      │
│  │ Port: 8000   │    │ Port: 5432   │    │ Port: 5050   │      │
│  └──────┬───────┘    └──────────────┘    └──────────────┘      │
│         │                                                         │
│         │            ┌──────────────┐    ┌──────────────┐      │
│         ├───────────▶│  Prometheus  │───▶│   Grafana    │      │
│         │            │   Metrics    │    │ Dashboards   │      │
│         │            │ Port: 9090   │    │ Port: 3000   │      │
│         │            └──────────────┘    └──────┬───────┘      │
│         │                                        │               │
│         │            ┌──────────────┐           │               │
│         └───────────▶│     Loki     │◀──────────┘              │
│                      │ Log Storage  │                           │
│                      │ Port: 3100   │                           │
│                      └──────▲───────┘                           │
│                             │                                    │
│                      ┌──────┴───────┐                           │
│                      │   Promtail   │                           │
│                      │ Log Shipper  │                           │
│                      └──────────────┘                           │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │    Locust    │───▶│   Locust     │───▶│  Prometheus  │      │
│  │ Load Testing │    │  Exporter    │    │              │      │
│  │ Port: 8089   │    │ Port: 9646   │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ ReportPortal │    │ ReportPortal │    │ ReportPortal │      │
│  │     UI       │───▶│     API      │───▶│  PostgreSQL  │      │
│  │ Port: 8080   │    │              │    │              │      │
│  └──────────────┘    └──────┬───────┘    └──────────────┘      │
│                             │                                    │
│                      ┌──────┴───────┐                           │
│                      │ ReportPortal │                           │
│                      │   Analyzer   │                           │
│                      └──────────────┘                           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Services

### Test Runner

**Image**: Custom (built from Dockerfile)  
**Container Name**: `pokeapi-test-runner`  
**Ports**: 8000 (metrics endpoint)  
**Purpose**: Execute pytest tests, expose Prometheus metrics

**Key Features**:
- Multi-stage Docker build for optimized image size
- Python 3.11 with all test dependencies
- HTTPX for async HTTP requests
- Pydantic for response validation
- Health check endpoint on port 8000

**Environment Variables**:
- `POKEAPI_BASE_URL`: PokéAPI base URL
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Database connection
- `REPORTPORTAL_ENDPOINT`, `REPORTPORTAL_PROJECT`, `REPORTPORTAL_API_TOKEN`: ReportPortal configuration
- `PROMETHEUS_PORT`: Metrics port

**Volumes**:
- `./tests:/app/tests`: Test code
- `./locust:/app/locust`: Locust scripts
- `./config:/app/config`: Configuration files
- `./.env:/app/.env`: Environment variables

**Health Check**:
```bash
curl -f http://localhost:8000/health
```

### PostgreSQL (Response Cache)

**Image**: `postgres:15-alpine`  
**Container Name**: `pokeapi-postgres`  
**Ports**: 5432  
**Purpose**: Store API responses, schema versions, performance baselines

**Key Features**:
- Persistent volume for data retention
- Initialization script creates schema on first run
- Health check using `pg_isready`

**Volumes**:
- `postgres-data:/var/lib/postgresql/data`: Persistent data
- `./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql`: Schema initialization

**Tables Created**:
- `api_responses`: Complete API response cache
- `schema_versions`: API schema tracking
- `schema_changes`: Field-level change detection
- `performance_baselines`: Performance regression tracking
- `flaky_tests`: Test flakiness monitoring

### pgAdmin

**Image**: `dpage/pgadmin4:latest`  
**Container Name**: `pokeapi-pgadmin`  
**Ports**: 5050  
**Purpose**: Web-based PostgreSQL management

**Access**: http://localhost:5050  
**Default Credentials**: admin@pokeapi.local / admin

### ReportPortal

**Components**:
1. **ReportPortal UI** (`reportportal/service-ui:5.10.0`)
   - Port: 8080
   - Web interface for test results
   
2. **ReportPortal API** (`reportportal/service-api:5.10.0`)
   - Backend API service
   - Connects to ReportPortal PostgreSQL
   
3. **ReportPortal Analyzer** (`reportportal/service-auto-analyzer:5.10.0`)
   - Auto-analysis of test failures
   - Pattern recognition
   
4. **ReportPortal PostgreSQL** (`postgres:15-alpine`)
   - Dedicated database for ReportPortal data
   
5. **RabbitMQ** (`rabbitmq:3.12-management-alpine`)
   - Message queue for ReportPortal services

**Access**: http://localhost:8080  
**Default Credentials**: superadmin / erebus

**Setup Steps**:
1. Access UI at http://localhost:8080
2. Login with default credentials
3. Create project: `pokeapi-tests`
4. Generate API token: User Profile → API Keys
5. Update `.env` with `REPORTPORTAL_API_TOKEN`

### Prometheus

**Image**: `prom/prometheus:latest`  
**Container Name**: `pokeapi-prometheus`  
**Ports**: 9090  
**Purpose**: Metrics storage and querying

**Key Features**:
- 15-day retention period
- Scrapes test-runner metrics every 15s
- Scrapes Locust metrics via exporter
- Alerting rules configured

**Configuration Files**:
- `config/prometheus/prometheus.yml`: Main configuration
- `config/prometheus/alerting_rules.yml`: Alert definitions

**Scrape Targets**:
- `test-runner:8000/metrics`: Test execution metrics
- `locust-exporter:9646/metrics`: Load test metrics

**Access**: http://localhost:9090

### Grafana

**Image**: `grafana/grafana:latest`  
**Container Name**: `pokeapi-grafana`  
**Ports**: 3000  
**Purpose**: Visualization and dashboards

**Key Features**:
- Pre-configured Prometheus datasource
- Pre-configured Loki datasource
- Dashboard provisioning support

**Configuration**:
- `config/grafana/provisioning/datasources/datasources.yml`: Datasource configuration
- `config/grafana/dashboards/`: Dashboard JSON files (created in later tasks)

**Access**: http://localhost:3000  
**Default Credentials**: admin / admin

### Loki

**Image**: `grafana/loki:latest`  
**Container Name**: `pokeapi-loki`  
**Ports**: 3100  
**Purpose**: Log aggregation and storage

**Key Features**:
- 7-day log retention
- Filesystem storage
- Compression and indexing

**Configuration**: `config/loki/loki-config.yml`

**Storage**:
- Volume: `loki-data:/loki`
- Chunks, indexes, and rules stored persistently

### Promtail

**Image**: `grafana/promtail:latest`  
**Container Name**: `pokeapi-promtail`  
**Purpose**: Log collection and shipping to Loki

**Key Features**:
- Collects logs from Docker containers
- Adds metadata labels (container_name, service, environment)
- JSON log parsing
- Ships to Loki

**Configuration**: `config/promtail/promtail-config.yml`

**Volumes**:
- `/var/lib/docker/containers:/var/lib/docker/containers:ro`: Container logs
- `/var/run/docker.sock:/var/run/docker.sock`: Docker socket

### Locust

**Image**: Custom (built from Dockerfile)  
**Container Name**: `pokeapi-locust`  
**Ports**: 8089 (web UI)  
**Purpose**: Load testing and performance testing

**Key Features**:
- Web UI for test control
- Configurable user count and spawn rate
- Reuses test code (Pydantic models, API client)

**Volumes**:
- `./locust:/app/locust`: Locust scripts
- `./tests/models:/app/tests/models`: Shared Pydantic models
- `./tests/api:/app/tests/api`: Shared API client

**Access**: http://localhost:8089

### Locust Exporter

**Image**: `containersol/locust_exporter:latest`  
**Container Name**: `pokeapi-locust-exporter`  
**Ports**: 9646  
**Purpose**: Export Locust metrics to Prometheus

**Configuration**:
- `LOCUST_EXPORTER_URI=http://locust:8089`

## Networking

All services are connected via a custom bridge network: `pokeapi-network`

**Benefits**:
- Service discovery by container name
- Isolated from other Docker networks
- Secure inter-service communication

**Service Communication**:
- Test Runner → PostgreSQL: `postgres:5432`
- Test Runner → ReportPortal API: `reportportal-api:8080`
- Test Runner → Prometheus: Prometheus scrapes `test-runner:8000`
- Promtail → Loki: `loki:3100`
- Grafana → Prometheus: `prometheus:9090`
- Grafana → Loki: `loki:3100`

## Volumes

Persistent volumes ensure data survives container restarts:

| Volume Name | Purpose | Size (typical) |
|-------------|---------|----------------|
| `postgres-data` | API response cache | 1-5 GB |
| `pgadmin-data` | pgAdmin configuration | < 100 MB |
| `reportportal-postgres-data` | ReportPortal data | 1-10 GB |
| `prometheus-data` | Metrics (15 days) | 1-5 GB |
| `grafana-data` | Dashboards and config | < 500 MB |
| `loki-data` | Logs (7 days) | 1-10 GB |

**Volume Management**:
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect pokeapi-observability-tests_postgres-data

# Remove all volumes (WARNING: deletes all data)
docker-compose down -v

# Backup volume
docker run --rm -v pokeapi-observability-tests_postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz /data
```

## Health Checks

All critical services have health checks configured:

| Service | Health Check | Interval | Timeout | Retries |
|---------|--------------|----------|---------|---------|
| test-runner | `curl http://localhost:8000/health` | 30s | 10s | 3 |
| postgres | `pg_isready -U postgres` | 10s | 5s | 5 |
| reportportal-postgres | `pg_isready -U rpuser` | 10s | 5s | 5 |
| reportportal-api | `curl http://localhost:8080/health` | 30s | 10s | 5 |
| reportportal-ui | `curl http://localhost:8080` | 30s | 10s | 3 |
| prometheus | `wget http://localhost:9090/-/healthy` | 30s | 10s | 3 |
| grafana | `curl http://localhost:3000/api/health` | 30s | 10s | 3 |
| loki | `wget http://localhost:3100/ready` | 30s | 10s | 3 |
| rabbitmq | `rabbitmq-diagnostics ping` | 30s | 10s | 5 |

**Check Service Health**:
```bash
docker-compose ps
```

## Resource Limits

Default resource limits can be customized in `docker-compose.override.yml`:

```yaml
services:
  test-runner:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

**Recommended Minimum Resources**:
- Total CPU: 4 cores
- Total RAM: 8 GB
- Disk Space: 20 GB

## Common Operations

### Start All Services
```bash
docker-compose up -d
```

### Start Specific Services
```bash
docker-compose up -d postgres prometheus grafana
```

### Stop All Services
```bash
docker-compose down
```

### Stop and Remove Volumes
```bash
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f test-runner

# Last 100 lines
docker-compose logs --tail=100 test-runner
```

### Restart Service
```bash
docker-compose restart test-runner
```

### Rebuild Service
```bash
docker-compose up -d --build test-runner
```

### Execute Command in Container
```bash
# Run tests
docker-compose exec test-runner pytest -m smoke

# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d pokeapi_cache

# Shell access
docker-compose exec test-runner bash
```

### Scale Services
```bash
# Not applicable for this setup (single instance per service)
```

## Troubleshooting

### Service Won't Start

**Check logs**:
```bash
docker-compose logs service-name
```

**Common issues**:
- Port already in use: Change port in `docker-compose.override.yml`
- Volume permission issues: Check file ownership
- Out of memory: Increase Docker memory limit

### Database Connection Errors

**Verify PostgreSQL is running**:
```bash
docker-compose exec postgres pg_isready
```

**Check connection from test-runner**:
```bash
docker-compose exec test-runner psql -h postgres -U postgres -d pokeapi_cache
```

**Reset database**:
```bash
docker-compose down
docker volume rm pokeapi-observability-tests_postgres-data
docker-compose up -d postgres
```

### ReportPortal Not Accessible

**Check all ReportPortal services are running**:
```bash
docker-compose ps | grep reportportal
```

**Check ReportPortal API logs**:
```bash
docker-compose logs reportportal-api
```

**Restart ReportPortal stack**:
```bash
docker-compose restart reportportal-ui reportportal-api reportportal-analyzer reportportal-postgres rabbitmq
```

### Prometheus Not Scraping Metrics

**Check Prometheus targets**:
- Access http://localhost:9090/targets
- Verify test-runner target is UP

**Check test-runner metrics endpoint**:
```bash
curl http://localhost:8000/metrics
```

**Verify network connectivity**:
```bash
docker-compose exec prometheus wget -O- http://test-runner:8000/metrics
```

### Grafana Dashboards Not Loading

**Check datasources**:
- Access http://localhost:3000/datasources
- Test Prometheus and Loki connections

**Check Grafana logs**:
```bash
docker-compose logs grafana
```

### Loki Not Receiving Logs

**Check Promtail logs**:
```bash
docker-compose logs promtail
```

**Verify Loki is accessible**:
```bash
curl http://localhost:3100/ready
```

**Check Promtail can reach Loki**:
```bash
docker-compose exec promtail wget -O- http://loki:3100/ready
```

### Out of Disk Space

**Check Docker disk usage**:
```bash
docker system df
```

**Clean up**:
```bash
# Remove unused containers, networks, images
docker system prune -a

# Remove unused volumes
docker volume prune
```

**Reduce retention periods**:
- Prometheus: Edit `config/prometheus/prometheus.yml` (default: 15 days)
- Loki: Edit `config/loki/loki-config.yml` (default: 7 days)

## Security Considerations

### Secrets Management

- Never commit `.env` file
- Use strong passwords in production
- Rotate credentials regularly
- Use Docker secrets in production environments

### Network Security

- Services are isolated in custom network
- Only necessary ports are exposed to host
- Use reverse proxy (nginx) in production

### Container Security

- Images are from official sources
- Regular updates recommended
- Run containers as non-root user in production

## Performance Tuning

### PostgreSQL

```yaml
# docker-compose.override.yml
services:
  postgres:
    command:
      - "postgres"
      - "-c"
      - "max_connections=200"
      - "-c"
      - "shared_buffers=256MB"
```

### Prometheus

```yaml
# config/prometheus/prometheus.yml
global:
  scrape_interval: 30s  # Increase for less frequent scraping
```

### Loki

```yaml
# config/loki/loki-config.yml
limits_config:
  retention_period: 72h  # Reduce for less storage
```

## Backup and Restore

### Backup PostgreSQL

```bash
# Backup to file
docker-compose exec postgres pg_dump -U postgres pokeapi_cache > backup.sql

# Backup with docker
docker-compose exec postgres pg_dump -U postgres pokeapi_cache | gzip > backup.sql.gz
```

### Restore PostgreSQL

```bash
# Restore from file
docker-compose exec -T postgres psql -U postgres pokeapi_cache < backup.sql

# Restore from gzip
gunzip -c backup.sql.gz | docker-compose exec -T postgres psql -U postgres pokeapi_cache
```

### Backup Volumes

```bash
# Backup volume to tar.gz
docker run --rm -v pokeapi-observability-tests_postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-data.tar.gz /data
```

### Restore Volumes

```bash
# Restore volume from tar.gz
docker run --rm -v pokeapi-observability-tests_postgres-data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres-data.tar.gz -C /
```

## Monitoring

### Container Resource Usage

```bash
# Real-time stats
docker stats

# Specific container
docker stats pokeapi-test-runner
```

### Service Health Dashboard

Create a simple monitoring script:

```bash
#!/bin/bash
echo "Service Health Status:"
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Networking](https://docs.docker.com/network/)
- [Docker Volumes](https://docs.docker.com/storage/volumes/)
- [Health Checks](https://docs.docker.com/engine/reference/builder/#healthcheck)
