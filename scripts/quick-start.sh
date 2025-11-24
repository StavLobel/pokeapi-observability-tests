#!/bin/bash
# Quick start script for PokéAPI Observability Tests

set -e

echo "🚀 PokéAPI Observability Tests - Quick Start"
echo "=============================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it and try again."
    exit 1
fi

echo "✅ docker-compose is available"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please review and update it with your credentials."
    echo ""
    echo "⚠️  Important: Update the following in .env:"
    echo "   - POSTGRES_PASSWORD"
    echo "   - REPORTPORTAL_API_TOKEN (after ReportPortal setup)"
    echo "   - GRAFANA_ADMIN_PASSWORD"
    echo ""
    read -p "Press Enter to continue after reviewing .env file..."
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🐳 Starting Docker Compose services..."
echo "This may take a few minutes on first run..."
echo ""

# Pull images first
docker-compose pull

# Start services
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🎉 Services started successfully!"
echo ""
echo "📍 Access Points:"
echo "   - Grafana:       http://localhost:3000 (admin/admin)"
echo "   - ReportPortal:  http://localhost:8080 (superadmin/erebus)"
echo "   - Prometheus:    http://localhost:9090"
echo "   - Locust:        http://localhost:8089"
echo "   - pgAdmin:       http://localhost:5050"
echo "   - Metrics:       http://localhost:8000/metrics"
echo ""
echo "🧪 Run Tests:"
echo "   docker-compose exec test-runner pytest -m smoke"
echo "   docker-compose exec test-runner pytest --cov=tests"
echo ""
echo "📝 View Logs:"
echo "   docker-compose logs -f test-runner"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop Services:"
echo "   docker-compose down"
echo ""
echo "📚 For more information, see README.md"
