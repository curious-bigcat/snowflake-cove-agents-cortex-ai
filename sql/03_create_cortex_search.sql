-- ============================================================================
-- Chain of Verification (CoVe) Project - Cortex Search Services
-- ============================================================================

USE DATABASE COVE_PROJECT_DB;
USE SCHEMA CORTEX_SERVICES;

-- ============================================================================
-- Cortex Search Service for Knowledge Base
-- ============================================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE KNOWLEDGE_SEARCH
    ON RAW_DATA.KNOWLEDGE_BASE
    TARGET_LAG = '1 hour'
    WAREHOUSE = COVE_WH
    AS (
        SELECT 
            DOC_ID,
            TITLE,
            CONTENT,
            CATEGORY,
            SUBCATEGORY,
            ARRAY_TO_STRING(TAGS, ', ') as TAGS_STR,
            SOURCE,
            CREATED_AT
        FROM RAW_DATA.KNOWLEDGE_BASE
    )
    SEARCH_COLUMN = CONTENT
    COLUMNS = (DOC_ID, TITLE, CATEGORY, SUBCATEGORY, TAGS_STR, SOURCE);

-- ============================================================================
-- Cortex Search Service for Products
-- ============================================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE PRODUCT_SEARCH
    ON RAW_DATA.PRODUCTS
    TARGET_LAG = '1 hour'
    WAREHOUSE = COVE_WH
    AS (
        SELECT 
            PRODUCT_ID,
            NAME,
            DESCRIPTION,
            CATEGORY,
            SUBCATEGORY,
            PRICE,
            STOCK_QUANTITY
        FROM RAW_DATA.PRODUCTS
    )
    SEARCH_COLUMN = DESCRIPTION
    COLUMNS = (PRODUCT_ID, NAME, CATEGORY, SUBCATEGORY, PRICE);

-- ============================================================================
-- Cortex Search Service for Support Tickets
-- ============================================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE TICKET_SEARCH
    ON RAW_DATA.SUPPORT_TICKETS
    TARGET_LAG = '1 hour'
    WAREHOUSE = COVE_WH
    AS (
        SELECT 
            TICKET_ID,
            CUSTOMER_ID,
            ISSUE,
            ISSUE_CATEGORY,
            PRIORITY,
            RESOLUTION,
            STATUS,
            SATISFACTION_SCORE
        FROM RAW_DATA.SUPPORT_TICKETS
    )
    SEARCH_COLUMN = ISSUE
    COLUMNS = (TICKET_ID, CUSTOMER_ID, ISSUE_CATEGORY, PRIORITY, RESOLUTION, STATUS);

-- ============================================================================
-- Grant permissions for search services
-- ============================================================================

GRANT USAGE ON CORTEX SEARCH SERVICE KNOWLEDGE_SEARCH TO ROLE PUBLIC;
GRANT USAGE ON CORTEX SEARCH SERVICE PRODUCT_SEARCH TO ROLE PUBLIC;
GRANT USAGE ON CORTEX SEARCH SERVICE TICKET_SEARCH TO ROLE PUBLIC;
