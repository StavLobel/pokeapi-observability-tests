#!/bin/bash
# Script to validate that the test environment is properly set up

set -e

echo "🔍 Validating Test Setup for Property Test 3.1"
echo "=============================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Check 1: Python version
echo "1️⃣  Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 11 ]; then
        echo -e "${GREEN}✅ Python $PYTHON_VERSION found (>= 3.11 required)${NC}"
    else
        echo -e "${RED}❌ Python $PYTHON_VERSION found, but 3.11+ required${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 2: Docker
echo "2️⃣  Checking Docker..."
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        echo -e "${GREEN}✅ Docker is installed and running${NC}"
    else
        echo -e "${RED}❌ Docker is installed but not running${NC}"
        echo "   Please start Docker Desktop"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}❌ Docker not found${NC}"
    echo "   Please install Docker: https://docs.docker.com/get-docker/"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 3: Docker Compose
echo "3️⃣  Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f4 | tr -d ',')
    echo -e "${GREEN}✅ Docker Compose $COMPOSE_VERSION found${NC}"
else
    echo -e "${RED}❌ Docker Compose not found${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 4: Required files
echo "4️⃣  Checking required files..."
FILES=(
    "docker-compose.yml"
    "docker/postgres/init.sql"
    "requirements.txt"
    "tests/utils/database.py"
    "tests/property/test_properties_storage.py"
    "tests/conftest.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file not found${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Check 5: Environment file
echo "5️⃣  Checking environment configuration..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
else
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "   Will use .env.example as template"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check 6: Python dependencies (if venv exists)
echo "6️⃣  Checking Python dependencies..."
if [ -d "venv" ]; then
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        if python3 -c "import pytest, hypothesis, psycopg2" 2>/dev/null; then
            echo -e "${GREEN}✅ Required Python packages installed in venv${NC}"
        else
            echo -e "${YELLOW}⚠️  Some Python packages missing in venv${NC}"
            echo "   Run: pip install -r requirements.txt"
            WARNINGS=$((WARNINGS + 1))
        fi
        deactivate
    fi
else
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo "   Recommended: python3 -m venv venv && source venv/bin/activate"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check 7: PostgreSQL container
echo "7️⃣  Checking PostgreSQL container..."
if docker info &> /dev/null; then
    if docker-compose ps postgres 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}✅ PostgreSQL container is running${NC}"
        
        # Check if database is accessible
        if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
            echo -e "${GREEN}✅ PostgreSQL is accepting connections${NC}"
            
            # Check if schema is initialized
            TABLE_COUNT=$(docker-compose exec -T postgres psql -U postgres -d pokeapi_cache -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('api_responses', 'schema_versions', 'schema_changes', 'performance_baselines', 'flaky_tests');" 2>/dev/null | tr -d ' ')
            
            if [ "$TABLE_COUNT" = "5" ]; then
                echo -e "${GREEN}✅ Database schema initialized (5 tables)${NC}"
            else
                echo -e "${YELLOW}⚠️  Database schema incomplete (found $TABLE_COUNT/5 tables)${NC}"
                echo "   Run: docker-compose down postgres && docker-compose up -d postgres"
                WARNINGS=$((WARNINGS + 1))
            fi
        else
            echo -e "${YELLOW}⚠️  PostgreSQL not ready yet${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo -e "${YELLOW}⚠️  PostgreSQL container not running${NC}"
        echo "   Run: docker-compose up -d postgres"
        WARNINGS=$((WARNINGS + 1))
    fi
fi
echo ""

# Summary
echo "=============================================="
echo "📊 Validation Summary"
echo "=============================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to run tests.${NC}"
    echo ""
    echo "To run the property test:"
    echo "  ./scripts/run-property-tests.sh"
    echo ""
    echo "Or manually:"
    echo "  source venv/bin/activate"
    echo "  pytest tests/property/test_properties_storage.py::test_property_3_responses_stored_in_database -v"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warning(s) found${NC}"
    echo "Tests may run, but some features might not work correctly."
    exit 0
else
    echo -e "${RED}❌ $ERRORS error(s) and $WARNINGS warning(s) found${NC}"
    echo "Please fix the errors above before running tests."
    exit 1
fi
