-- ============================================================================
-- Chain of Verification (CoVe) Project - Cortex Agent Setup
-- ============================================================================

USE DATABASE COVE_PROJECT_DB;
USE SCHEMA CORTEX_SERVICES;

-- ============================================================================
-- Create Cortex Agent for CoVe Verification
-- ============================================================================

CREATE OR REPLACE CORTEX AGENT COVE_VERIFICATION_AGENT
    WAREHOUSE = COVE_WH
    MODEL = 'claude-3-5-sonnet'
    DESCRIPTION = 'Agent for executing Chain of Verification to reduce hallucination'
    TOOLS = (
        -- Cortex Analyst Tool for structured data queries
        CORTEX_ANALYST_TOOL(
            SEMANTIC_MODEL => '@CORTEX_SERVICES.SEMANTIC_MODELS/cove_business_model.yaml',
            DESCRIPTION => 'Query business data using natural language. Use for verifying facts about revenue, orders, customers, and products.'
        ),
        -- Cortex Search Tool for knowledge base
        CORTEX_SEARCH_TOOL(
            SEARCH_SERVICE => 'CORTEX_SERVICES.KNOWLEDGE_SEARCH',
            DESCRIPTION => 'Search the knowledge base for policies, product information, and documentation. Use for verifying facts about company policies, features, and specifications.'
        ),
        -- SQL Executor Tool
        SQL_EXEC_TOOL(
            DESCRIPTION => 'Execute SQL queries directly when semantic model queries are insufficient. Use for complex analytical queries.'
        )
    )
    INSTRUCTIONS = $$
You are a verification agent designed to fact-check claims and provide accurate information.

When asked to verify a fact:
1. First determine if the fact relates to structured data (revenue, orders, customers, products) or unstructured knowledge (policies, documentation, features)
2. For structured data facts, use the cortex_analyst tool to query the business database
3. For knowledge-based facts, use the cortex_search tool to find relevant documentation
4. If neither tool provides a clear answer, use sql_exec for custom queries

Always:
- Return only factual, verified information
- Cite your source (which tool/query you used)
- Indicate confidence level (high, medium, low)
- If you cannot verify a fact, explicitly state that it could not be verified

Never:
- Make up information
- Assume facts without verification
- Provide information outside the available data sources
$$;

-- ============================================================================
-- Create Stage for Semantic Model
-- ============================================================================

CREATE STAGE IF NOT EXISTS CORTEX_SERVICES.SEMANTIC_MODELS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for storing semantic model YAML files';

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT USAGE ON CORTEX AGENT COVE_VERIFICATION_AGENT TO ROLE PUBLIC;
