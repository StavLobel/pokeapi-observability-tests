-- PostgreSQL Database Initialization Script
-- This script creates the schema for storing PokéAPI test data, schema versions, and performance metrics

-- Enable UUID extension for potential future use
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- API Responses Table
-- Stores complete API responses for historical comparison
-- ============================================================================
CREATE TABLE api_responses (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    resource_id INTEGER NOT NULL,
    response_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(endpoint, resource_id, created_at)
);

-- Indexes for efficient querying
CREATE INDEX idx_endpoint_resource ON api_responses(endpoint, resource_id);
CREATE INDEX idx_created_at ON api_responses(created_at DESC);

-- Add comment for documentation
COMMENT ON TABLE api_responses IS 'Stores complete API responses from PokéAPI for historical data comparison';
COMMENT ON COLUMN api_responses.endpoint IS 'API endpoint name (e.g., pokemon, type, ability)';
COMMENT ON COLUMN api_responses.resource_id IS 'Resource identifier (e.g., pokemon ID)';
COMMENT ON COLUMN api_responses.response_data IS 'Complete JSON response from API';

-- ============================================================================
-- Schema Versions Table
-- Tracks API schema structure changes over time
-- ============================================================================
CREATE TABLE schema_versions (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    schema_structure JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for retrieving latest schema by endpoint
CREATE INDEX idx_schema_endpoint ON schema_versions(endpoint, created_at DESC);

-- Add comment for documentation
COMMENT ON TABLE schema_versions IS 'Tracks API schema structure versions for change detection';
COMMENT ON COLUMN schema_versions.endpoint IS 'API endpoint name';
COMMENT ON COLUMN schema_versions.schema_structure IS 'JSON representation of the schema structure';

-- ============================================================================
-- Schema Changes Table
-- Records specific field-level changes detected in API schemas
-- ============================================================================
CREATE TABLE schema_changes (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    change_type VARCHAR(50) NOT NULL,  -- 'field_added', 'field_removed', 'type_changed'
    field_path VARCHAR(255) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for querying changes by endpoint and time
CREATE INDEX idx_changes_endpoint ON schema_changes(endpoint, detected_at DESC);
CREATE INDEX idx_changes_type ON schema_changes(change_type);

-- Add comment for documentation
COMMENT ON TABLE schema_changes IS 'Records specific field-level changes detected in API schemas';
COMMENT ON COLUMN schema_changes.change_type IS 'Type of change: field_added, field_removed, or type_changed';
COMMENT ON COLUMN schema_changes.field_path IS 'JSON path to the changed field (e.g., types[0].slot)';

-- ============================================================================
-- Performance Baselines Table
-- Stores performance baseline metrics for regression detection
-- ============================================================================
CREATE TABLE performance_baselines (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,  -- 'p50', 'p95', 'p99'
    baseline_value FLOAT NOT NULL,
    sample_size INTEGER NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    UNIQUE(endpoint, metric_name, valid_from)
);

-- Index for retrieving active baselines
CREATE INDEX idx_baselines_endpoint ON performance_baselines(endpoint, valid_from DESC);
CREATE INDEX idx_baselines_active ON performance_baselines(endpoint, metric_name, valid_from, valid_until);

-- Add comment for documentation
COMMENT ON TABLE performance_baselines IS 'Stores performance baseline metrics (P50, P95, P99) for regression detection';
COMMENT ON COLUMN performance_baselines.metric_name IS 'Percentile metric: p50, p95, or p99';
COMMENT ON COLUMN performance_baselines.baseline_value IS 'Baseline latency value in seconds';
COMMENT ON COLUMN performance_baselines.sample_size IS 'Number of samples used to calculate baseline';
COMMENT ON COLUMN performance_baselines.valid_from IS 'Start of baseline validity period';
COMMENT ON COLUMN performance_baselines.valid_until IS 'End of baseline validity period (NULL for current baseline)';

-- ============================================================================
-- Flaky Tests Table
-- Tracks test flakiness for reliability monitoring
-- ============================================================================
CREATE TABLE flaky_tests (
    id SERIAL PRIMARY KEY,
    test_name VARCHAR(255) NOT NULL,
    total_runs INTEGER DEFAULT 0,
    flaky_runs INTEGER DEFAULT 0,
    last_flaky_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(test_name)
);

-- Index for querying flaky tests
CREATE INDEX idx_flaky_tests_name ON flaky_tests(test_name);
CREATE INDEX idx_flaky_tests_rate ON flaky_tests(flaky_runs DESC, total_runs DESC);

-- Add comment for documentation
COMMENT ON TABLE flaky_tests IS 'Tracks test flakiness metrics for reliability monitoring';
COMMENT ON COLUMN flaky_tests.test_name IS 'Full test name including module path';
COMMENT ON COLUMN flaky_tests.total_runs IS 'Total number of times test has been executed';
COMMENT ON COLUMN flaky_tests.flaky_runs IS 'Number of times test passed after retry';
COMMENT ON COLUMN flaky_tests.last_flaky_at IS 'Timestamp of most recent flaky occurrence';

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to get the latest schema for an endpoint
CREATE OR REPLACE FUNCTION get_latest_schema(p_endpoint VARCHAR)
RETURNS JSONB AS $$
DECLARE
    latest_schema JSONB;
BEGIN
    SELECT schema_structure INTO latest_schema
    FROM schema_versions
    WHERE endpoint = p_endpoint
    ORDER BY created_at DESC
    LIMIT 1;
    
    RETURN latest_schema;
END;
$$ LANGUAGE plpgsql;

-- Function to get the latest response for a resource
CREATE OR REPLACE FUNCTION get_latest_response(p_endpoint VARCHAR, p_resource_id INTEGER)
RETURNS JSONB AS $$
DECLARE
    latest_response JSONB;
BEGIN
    SELECT response_data INTO latest_response
    FROM api_responses
    WHERE endpoint = p_endpoint AND resource_id = p_resource_id
    ORDER BY created_at DESC
    LIMIT 1;
    
    RETURN latest_response;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate flakiness rate
CREATE OR REPLACE FUNCTION calculate_flakiness_rate(p_test_name VARCHAR)
RETURNS FLOAT AS $$
DECLARE
    flaky_rate FLOAT;
BEGIN
    SELECT 
        CASE 
            WHEN total_runs > 0 THEN (flaky_runs::FLOAT / total_runs::FLOAT)
            ELSE 0.0
        END INTO flaky_rate
    FROM flaky_tests
    WHERE test_name = p_test_name;
    
    RETURN COALESCE(flaky_rate, 0.0);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Initial Data / Seed Data
-- ============================================================================

-- No seed data required for this schema
-- Tables will be populated by test execution

-- ============================================================================
-- Grants and Permissions
-- ============================================================================

-- Grant permissions to the postgres user (default user in docker-compose)
-- In production, you would create specific users with limited permissions

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- ============================================================================
-- Schema Validation
-- ============================================================================

-- Verify all tables were created successfully
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('api_responses', 'schema_versions', 'schema_changes', 'performance_baselines', 'flaky_tests');
    
    IF table_count = 5 THEN
        RAISE NOTICE 'Database schema initialized successfully. All 5 tables created.';
    ELSE
        RAISE EXCEPTION 'Database schema initialization failed. Expected 5 tables, found %', table_count;
    END IF;
END $$;
