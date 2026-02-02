-- ============================================================================
-- Chain of Verification (CoVe) Project - Database Setup
-- ============================================================================

-- Create Database
CREATE DATABASE IF NOT EXISTS COVE_PROJECT_DB
    COMMENT = 'Chain of Verification project database for hallucination reduction';

USE DATABASE COVE_PROJECT_DB;

-- Create Schemas
CREATE SCHEMA IF NOT EXISTS RAW_DATA
    COMMENT = 'Source tables for business data';

CREATE SCHEMA IF NOT EXISTS ANALYTICS
    COMMENT = 'Aggregated metrics and KPIs';

CREATE SCHEMA IF NOT EXISTS CORTEX_SERVICES
    COMMENT = 'Cortex Search services and semantic views';

CREATE SCHEMA IF NOT EXISTS COVE_LOGS
    COMMENT = 'CoVe execution logs and audit trail';

-- Create Warehouse for Cortex Operations
CREATE WAREHOUSE IF NOT EXISTS COVE_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    COMMENT = 'Warehouse for CoVe Cortex operations';

-- Grant usage
GRANT USAGE ON DATABASE COVE_PROJECT_DB TO ROLE PUBLIC;
GRANT USAGE ON ALL SCHEMAS IN DATABASE COVE_PROJECT_DB TO ROLE PUBLIC;
GRANT USAGE ON WAREHOUSE COVE_WH TO ROLE PUBLIC;
