-- ============================================================================
-- Create Semantic View for Cortex Analyst in Cortex Agents
-- ============================================================================

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE COMPUTE_WH;
USE DATABASE COVE_PROJECT_DB;
USE SCHEMA CORTEX_SERVICES;

-- Create Semantic View for business data
-- This allows Cortex Analyst to understand the data model and generate accurate SQL
CREATE OR REPLACE SEMANTIC VIEW BUSINESS_SEMANTIC_VIEW
  COMMENT = 'Semantic view for business analytics - orders, customers, and products'
AS
  -- Orders fact table
  SELECT
    o.ORDER_ID,
    o.CUSTOMER_ID,
    o.PRODUCT_ID,
    o.QUANTITY,
    o.AMOUNT,
    o.ORDER_DATE,
    o.QUARTER,
    o.STATUS,
    -- Customer dimensions
    c.NAME AS CUSTOMER_NAME,
    c.SEGMENT AS CUSTOMER_SEGMENT,
    c.REGION AS CUSTOMER_REGION,
    c.COUNTRY AS CUSTOMER_COUNTRY,
    -- Product dimensions
    p.NAME AS PRODUCT_NAME,
    p.CATEGORY AS PRODUCT_CATEGORY,
    p.PRICE AS PRODUCT_PRICE
  FROM COVE_PROJECT_DB.RAW_DATA.ORDERS o
  JOIN COVE_PROJECT_DB.RAW_DATA.CUSTOMERS c ON o.CUSTOMER_ID = c.CUSTOMER_ID
  JOIN COVE_PROJECT_DB.RAW_DATA.PRODUCTS p ON o.PRODUCT_ID = p.PRODUCT_ID
WITH SEMANTIC MODEL (
  DESCRIPTION = 'Business analytics model for sales, customers, and products'
  
  ENTITIES = (
    ORDER_ID DESCRIPTION 'Unique order identifier' PRIMARY KEY,
    CUSTOMER_ID DESCRIPTION 'Customer identifier' REFERENCES CUSTOMER_NAME,
    PRODUCT_ID DESCRIPTION 'Product identifier' REFERENCES PRODUCT_NAME
  )
  
  DIMENSIONS = (
    CUSTOMER_NAME DESCRIPTION 'Name of the customer',
    CUSTOMER_SEGMENT DESCRIPTION 'Customer segment: Enterprise, SMB, or Consumer',
    CUSTOMER_REGION DESCRIPTION 'Geographic region: North America, EMEA, APAC, LATAM',
    CUSTOMER_COUNTRY DESCRIPTION 'Country of the customer',
    PRODUCT_NAME DESCRIPTION 'Name of the product',
    PRODUCT_CATEGORY DESCRIPTION 'Product category: Software, Hardware, or Services',
    QUARTER DESCRIPTION 'Fiscal quarter in format Q1-2024, Q2-2024, etc.',
    STATUS DESCRIPTION 'Order status: Completed, Pending, or Cancelled',
    ORDER_DATE DESCRIPTION 'Date when the order was placed'
  )
  
  MEASURES = (
    AMOUNT DESCRIPTION 'Order amount in USD' AGGREGATION SUM,
    QUANTITY DESCRIPTION 'Number of units ordered' AGGREGATION SUM,
    PRODUCT_PRICE DESCRIPTION 'Unit price of the product' AGGREGATION AVG
  )
  
  TIME_DIMENSIONS = (
    ORDER_DATE DESCRIPTION 'Order date for time-based analysis'
  )
  
  METRICS = (
    TOTAL_REVENUE DESCRIPTION 'Total revenue' EXPRESSION 'SUM(AMOUNT)',
    ORDER_COUNT DESCRIPTION 'Number of orders' EXPRESSION 'COUNT(DISTINCT ORDER_ID)',
    AVG_ORDER_VALUE DESCRIPTION 'Average order value' EXPRESSION 'AVG(AMOUNT)',
    TOTAL_UNITS DESCRIPTION 'Total units sold' EXPRESSION 'SUM(QUANTITY)'
  )
  
  SAMPLE_QUESTIONS = (
    'What was the total revenue in Q4 2024?',
    'Which customer segment had the highest revenue?',
    'What are the top selling product categories?',
    'How many orders did Enterprise customers place?',
    'What is the average order value by region?'
  )
);

-- Verify the semantic view was created
DESCRIBE SEMANTIC VIEW BUSINESS_SEMANTIC_VIEW;
