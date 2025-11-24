#!/bin/bash
# Validation script for Docker Compose configuration

set -e

echo "🔍 Validating Docker Compose configuration..."

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found!"
    exit 1
fi

echo "✅ docker-compose.yml found"

# Validate docker-compose syntax
echo "🔍 Validating Docker Compose syntax..."
docker-compose config > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Docker Compose syntax is valid"
else
    echo "❌ Docker Compose syntax validation failed!"
    exit 1
fi

# Check required configuration files
echo "🔍 Checking required configuration files..."

required_files=(
    "Dockerfile"
    ".dockerignore"
    ".env.example"
    "docker/postgres/init.sql"
    "config/prometheus/prometheus.yml"
    "config/prometheus/alerting_rules.yml"
    "config/grafana/provisioning/datasources/datasources.yml"
    "config/loki/loki-config.yml"
    "config/promtail/promtail-config.yml"
)

missing_files=()

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo ""
    echo "❌ Missing required files:"
    for file in "${missing_files[@]}"; do
        echo "  - $file"
    done
    exit 1
fi

echo ""
echo "✅ All required configuration files are present"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Copy .env.example to .env and configure it."
    echo "   Run: cp .env.example .env"
else
    echo "✅ .env file found"
fi

echo ""
echo "🎉 Docker Compose configuration validation complete!"
echo ""
echo "Next steps:"
echo "  1. Ensure .env file is configured (cp .env.example .env)"
echo "  2. Start services: docker-compose up -d"
echo "  3. Check service health: docker-compose ps"
echo "  4. View logs: docker-compose logs -f"
