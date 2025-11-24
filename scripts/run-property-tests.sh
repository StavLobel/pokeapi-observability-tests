#!/bin/bash
# Script to run property-based tests with proper setup

set -e

echo "🚀 Starting Property-Based Tests"
echo "================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker and try again"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "📝 Please review and update credentials in .env if needed"
fi

# Start PostgreSQL if not running
echo ""
echo "🐘 Checking PostgreSQL status..."
if ! docker-compose ps postgres | grep -q "Up"; then
    echo "Starting PostgreSQL..."
    docker-compose up -d postgres
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 5
    
    # Wait for health check
    for i in {1..30}; do
        if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
            echo "✅ PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ PostgreSQL failed to start"
            docker-compose logs postgres
            exit 1
        fi
        sleep 1
    done
else
    echo "✅ PostgreSQL is already running"
fi

# Verify database schema
echo ""
echo "🔍 Verifying database schema..."
TABLE_COUNT=$(docker-compose exec -T postgres psql -U postgres -d pokeapi_cache -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('api_responses', 'schema_versions', 'schema_changes', 'performance_baselines', 'flaky_tests');" | tr -d ' ')

if [ "$TABLE_COUNT" -eq "5" ]; then
    echo "✅ Database schema is initialized (5 tables found)"
else
    echo "⚠️  Warning: Expected 5 tables, found $TABLE_COUNT"
    echo "Database may need reinitialization"
fi

# Run property tests
echo ""
echo "🧪 Running Property-Based Tests..."
echo "================================"

# Export environment variables for pytest
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=pokeapi_cache
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres

# Run the tests
pytest tests/property/ -m property -v --hypothesis-show-statistics "$@"

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All property tests passed!"
else
    echo "❌ Some property tests failed (exit code: $TEST_EXIT_CODE)"
    echo ""
    echo "Troubleshooting tips:"
    echo "  1. Check database logs: docker-compose logs postgres"
    echo "  2. Verify database connection: docker-compose exec postgres psql -U postgres -d pokeapi_cache"
    echo "  3. Review test output above for specific failures"
fi

exit $TEST_EXIT_CODE
