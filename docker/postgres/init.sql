-- PostgreSQL initialization script for PokéAPI observability tests
-- This script creates the database schema for caching API responses and tracking changes

-- Create database if it doesn't exist (handled by POSTGRES_DB env var)
-- CREATE DATABASE IF NOT EXISTS pokeapi_cache;

-- Connect to the database
\c pokeapi_cache;

-- Enable UUID extension for potential future use
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- API Responses Table
-- Stores complete API responses for historical comparison
-- ============================================================================
CREATE TABLE IF NOT EXISTS api_responses (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    resource_id INTEGER NOT NULL,
    response_data JSONB NOT NULL,
    status_code INTEGER DEFAULT 200,
    response_time_ms FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_endpoint_resource_time UNIQUE(endpoint, resource_id, created_at)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_endpoint_resource ON api_responses(endpoint, resource_id);
CREATE INDEX IF NOT EXISTS idx_created_at ON api_responses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_endpoint_created ON api_responses(endpoint, created_at DESC);

-- ============================================================================
-- Schema Versions Table
-- Tracks API schema structure changes over time
-- ============================================================================
CREATE TABLE IF NOT EXISTS schema_versions (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    schema_structure JSONB NOT NULL,
    schema_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for schema tracking
CREATE INDEX IF NOT EXISTS idx_schema_endpoint ON schema_versions(endpoint, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_schema_hash ON schema_versions(schema_hash);

-- ============================================================================
-- Schema Changes Table
-- Records specific field-level changes detected in API schemas
-- ============================================================================
CREATE TABLE IF NOT EXISTS schema_changes (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    change_type VARCHAR(50) NOT NULL,  -- 'field_added', 'field_removed', 'type_changed'
    field_path VARCHAR(255) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for change tracking
CREATE INDEX IF NOT EXISTS idx_changes_endpoint ON schema_changes(endpoint, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_changes_type ON schema_changes(change_type);

-- ============================================================================
-- Performance Baselines Table
-- Stores performance baseline metrics for regression detection
-- ============================================================================
CREATE TABLE IF NOT EXISTS performance_baselines (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,  -- 'p50', 'p95', 'p99'
    baseline_value FLOAT NOT NULL,
    sample_size INTEGER NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    CONSTRAINT unique_endpoint_metric_valid UNIQUE(endpoint, metric_name, valid_from)
);

-- Indexes for baseline queries
CREATE INDEX IF NOT EXISTS idx_baselines_endpoint ON performance_baselines(endpoint, valid_from DESC);
CREATE INDEX IF NOT EXISTS idx_baselines_valid ON performance_baselines(valid_from, valid_until);

-- ============================================================================
-- Flaky Tests Table
-- Tracks test flakiness for reliability monitoring
-- ============================================================================
CREATE TABLE IF NOT EXISTS flaky_tests (
    id SERIAL PRIMARY KEY,
    test_name VARCHAR(255) NOT NULL,
    total_runs INTEGER DEFAULT 0,
    flaky_runs INTEGER DEFAULT 0,
    last_flaky_at TIMESTAMP,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_test_name UNIQUE(test_name)
);

-- Indexes for flakiness tracking
CREATE INDEX IF NOT EXISTS idx_flaky_tests_name ON flaky_tests(test_name);
CREATE INDEX IF NOT EXISTS idx_flaky_rate ON flaky_tests((flaky_runs::float / NULLIF(total_runs, 0)));

-- ============================================================================
-- Views for Common Queries
-- ============================================================================

-- View: Latest response per endpoint and resource
CREATE OR REPLACE VIEW latest_responses AS
SELECT DISTINCT ON (endpoint, resource_id)
    id,
    endpoint,
    resource_id,
    response_data,
    status_code,
    response_time_ms,
    created_at
FROM api_responses
ORDER BY endpoint, resource_id, created_at DESC;

-- View: Latest schema per endpoint
CREATE OR REPLACE VIEW latest_schemas AS
SELECT DISTINCT ON (endpoint)
    id,
    endpoint,
    schema_structure,
    schema_hash,
    created_at
FROM schema_versions
ORDER BY endpoint, created_at DESC;

-- View: Active performance baselines
CREATE OR REPLACE VIEW active_baselines AS
SELECT
    endpoint,
    metric_name,
    baseline_value,
    sample_size,
    calculated_at,
    valid_from
FROM performance_baselines
WHERE valid_until IS NULL OR valid_until > NOW()
ORDER BY endpoint, metric_name;

-- View: Flaky test statistics
CREATE OR REPLACE VIEW flaky_test_stats AS
SELECT
    test_name,
    total_runs,
    flaky_runs,
    CASE
        WHEN total_runs > 0 THEN ROUND((flaky_runs::float / total_runs * 100)::numeric, 2)
        ELSE 0
    END AS flakiness_percentage,
    last_flaky_at,
    first_seen_at
FROM flaky_tests
WHERE total_runs > 0
ORDER BY flakiness_percentage DESC, total_runs DESC;

-- ============================================================================
-- Grant Permissions
-- ============================================================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- ============================================================================
-- Insert Sample Data (Optional - for testing)
-- ============================================================================
-- Uncomment to insert sample data for development/testing

-- INSERT INTO api_responses (endpoint, resource_id, response_data, status_code, response_time_ms)
-- VALUES
--     ('pokemon', 1, '{"id": 1, "name": "bulbasaur", "types": [{"type": {"name": "grass"}}]}'::jsonb, 200, 150.5),
--     ('pokemon', 25, '{"id": 25, "name": "pikachu", "types": [{"type": {"name": "electric"}}]}'::jsonb, 200, 120.3);

-- ============================================================================
-- Database Maintenance Functions
-- ============================================================================

-- Function to clean up old responses (keep last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_responses()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM api_responses
    WHERE created_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate flakiness rate
CREATE OR REPLACE FUNCTION update_flakiness_rate(
    p_test_name VARCHAR(255),
    p_is_flaky BOOLEAN
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO flaky_tests (test_name, total_runs, flaky_runs, last_flaky_at)
    VALUES (
        p_test_name,
        1,
        CASE WHEN p_is_flaky THEN 1 ELSE 0 END,
        CASE WHEN p_is_flaky THEN NOW() ELSE NULL END
    )
    ON CONFLICT (test_name) DO UPDATE SET
        total_runs = flaky_tests.total_runs + 1,
        flaky_runs = flaky_tests.flaky_runs + CASE WHEN p_is_flaky THEN 1 ELSE 0 END,
        last_flaky_at = CASE WHEN p_is_flaky THEN NOW() ELSE flaky_tests.last_flaky_at END;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Completion Message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'PokéAPI observability database schema initialized successfully!';
    RAISE NOTICE 'Tables created: api_responses, schema_versions, schema_changes, performance_baselines, flaky_tests';
    RAISE NOTICE 'Views created: latest_responses, latest_schemas, active_baselines, flaky_test_stats';
END $$;
