-- ============================================================================
-- Chain of Verification (CoVe) Project - Seed Data
-- ============================================================================

USE DATABASE COVE_PROJECT_DB;

-- ============================================================================
-- RAW_DATA - Sample Data
-- ============================================================================

USE SCHEMA RAW_DATA;

-- Insert Products
INSERT INTO PRODUCTS (PRODUCT_ID, NAME, DESCRIPTION, CATEGORY, SUBCATEGORY, PRICE, COST, STOCK_QUANTITY) VALUES
('PROD-001', 'MacBook Pro 16"', 'Apple MacBook Pro 16-inch with M3 Pro chip, 18GB RAM, 512GB SSD', 'Electronics', 'Laptops', 2499.00, 1800.00, 150),
('PROD-002', 'iPhone 15 Pro', 'Apple iPhone 15 Pro with A17 Pro chip, 256GB', 'Electronics', 'Smartphones', 1199.00, 850.00, 500),
('PROD-003', 'Samsung Galaxy S24', 'Samsung Galaxy S24 Ultra with AI features, 512GB', 'Electronics', 'Smartphones', 1299.00, 900.00, 300),
('PROD-004', 'Dell XPS 15', 'Dell XPS 15 with Intel i7, 32GB RAM, 1TB SSD', 'Electronics', 'Laptops', 1899.00, 1400.00, 200),
('PROD-005', 'Sony WH-1000XM5', 'Sony Premium Noise Cancelling Wireless Headphones', 'Electronics', 'Audio', 349.00, 180.00, 800),
('PROD-006', 'Ergonomic Office Chair', 'Premium ergonomic office chair with lumbar support', 'Furniture', 'Chairs', 599.00, 250.00, 120),
('PROD-007', 'Standing Desk Pro', 'Electric height-adjustable standing desk, 60x30 inches', 'Furniture', 'Desks', 799.00, 350.00, 80),
('PROD-008', 'Cloud Storage Plan - Annual', 'Enterprise cloud storage plan, 10TB, annual subscription', 'Software', 'Storage', 1200.00, 200.00, 9999),
('PROD-009', 'CRM Software License', 'Enterprise CRM software annual license per seat', 'Software', 'Business Apps', 600.00, 100.00, 9999),
('PROD-010', 'Security Suite Enterprise', 'Comprehensive cybersecurity suite for enterprise', 'Software', 'Security', 2500.00, 500.00, 9999);

-- Insert Customers
INSERT INTO CUSTOMERS (CUSTOMER_ID, NAME, EMAIL, PHONE, SEGMENT, REGION, COUNTRY, LIFETIME_VALUE) VALUES
('CUST-001', 'Acme Corporation', 'procurement@acme.com', '+1-555-0101', 'Enterprise', 'North America', 'USA', 250000.00),
('CUST-002', 'TechStart Inc', 'billing@techstart.io', '+1-555-0102', 'SMB', 'North America', 'USA', 45000.00),
('CUST-003', 'Global Industries Ltd', 'accounts@globalind.co.uk', '+44-20-5550103', 'Enterprise', 'Europe', 'UK', 380000.00),
('CUST-004', 'Smith & Associates', 'office@smithassoc.com', '+1-555-0104', 'SMB', 'North America', 'Canada', 28000.00),
('CUST-005', 'Pacific Trading Co', 'finance@pacifictrading.com.au', '+61-2-5550105', 'Enterprise', 'Asia Pacific', 'Australia', 195000.00),
('CUST-006', 'Innovate Labs', 'admin@innovatelabs.de', '+49-30-5550106', 'SMB', 'Europe', 'Germany', 62000.00),
('CUST-007', 'MegaCorp International', 'purchasing@megacorp.com', '+1-555-0107', 'Enterprise', 'North America', 'USA', 520000.00),
('CUST-008', 'StartupXYZ', 'hello@startupxyz.com', '+1-555-0108', 'Consumer', 'North America', 'USA', 5200.00),
('CUST-009', 'European Solutions GmbH', 'einkauf@eurosolutions.de', '+49-89-5550109', 'Enterprise', 'Europe', 'Germany', 175000.00),
('CUST-010', 'Digital Dynamics', 'accounts@digitaldynamics.sg', '+65-5550110', 'SMB', 'Asia Pacific', 'Singapore', 89000.00);

-- Insert Orders (Q3 and Q4 2024)
INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE, AMOUNT, DISCOUNT_PERCENT, ORDER_DATE, STATUS, QUARTER) VALUES
-- Q3 2024 Orders
('ORD-001', 'CUST-001', 'PROD-001', 50, 2499.00, 124950.00, 0, '2024-07-15', 'completed', 'Q3-2024'),
('ORD-002', 'CUST-001', 'PROD-008', 100, 1200.00, 120000.00, 0, '2024-07-20', 'completed', 'Q3-2024'),
('ORD-003', 'CUST-002', 'PROD-002', 20, 1199.00, 23980.00, 0, '2024-08-01', 'completed', 'Q3-2024'),
('ORD-004', 'CUST-003', 'PROD-010', 25, 2500.00, 62500.00, 0, '2024-08-10', 'completed', 'Q3-2024'),
('ORD-005', 'CUST-004', 'PROD-006', 15, 599.00, 8985.00, 0, '2024-08-15', 'completed', 'Q3-2024'),
('ORD-006', 'CUST-005', 'PROD-001', 30, 2499.00, 74970.00, 0, '2024-09-01', 'completed', 'Q3-2024'),
('ORD-007', 'CUST-006', 'PROD-009', 50, 600.00, 30000.00, 0, '2024-09-10', 'completed', 'Q3-2024'),
('ORD-008', 'CUST-007', 'PROD-003', 100, 1299.00, 129900.00, 0, '2024-09-20', 'completed', 'Q3-2024'),
-- Q4 2024 Orders
('ORD-009', 'CUST-001', 'PROD-001', 75, 2499.00, 187425.00, 0, '2024-10-05', 'completed', 'Q4-2024'),
('ORD-010', 'CUST-001', 'PROD-010', 50, 2500.00, 125000.00, 0, '2024-10-15', 'completed', 'Q4-2024'),
('ORD-011', 'CUST-002', 'PROD-004', 10, 1899.00, 18990.00, 0, '2024-10-20', 'completed', 'Q4-2024'),
('ORD-012', 'CUST-003', 'PROD-002', 200, 1199.00, 239800.00, 0, '2024-10-25', 'completed', 'Q4-2024'),
('ORD-013', 'CUST-003', 'PROD-008', 500, 1200.00, 600000.00, 0, '2024-11-01', 'completed', 'Q4-2024'),
('ORD-014', 'CUST-005', 'PROD-003', 80, 1299.00, 103920.00, 0, '2024-11-10', 'completed', 'Q4-2024'),
('ORD-015', 'CUST-006', 'PROD-005', 100, 349.00, 34900.00, 0, '2024-11-15', 'completed', 'Q4-2024'),
('ORD-016', 'CUST-007', 'PROD-001', 100, 2499.00, 249900.00, 0, '2024-11-20', 'completed', 'Q4-2024'),
('ORD-017', 'CUST-007', 'PROD-009', 200, 600.00, 120000.00, 0, '2024-11-25', 'completed', 'Q4-2024'),
('ORD-018', 'CUST-009', 'PROD-010', 30, 2500.00, 75000.00, 0, '2024-12-01', 'completed', 'Q4-2024'),
('ORD-019', 'CUST-010', 'PROD-002', 50, 1199.00, 59950.00, 0, '2024-12-10', 'completed', 'Q4-2024'),
('ORD-020', 'CUST-001', 'PROD-007', 20, 799.00, 15980.00, 0, '2024-12-15', 'completed', 'Q4-2024'),
('ORD-021', 'CUST-004', 'PROD-005', 30, 349.00, 10470.00, 0, '2024-12-18', 'completed', 'Q4-2024'),
('ORD-022', 'CUST-008', 'PROD-002', 2, 1199.00, 2398.00, 0, '2024-12-20', 'completed', 'Q4-2024');

-- Insert Support Tickets
INSERT INTO SUPPORT_TICKETS (TICKET_ID, CUSTOMER_ID, ISSUE, ISSUE_CATEGORY, PRIORITY, RESOLUTION, STATUS, RESOLVED_AT, SATISFACTION_SCORE) VALUES
('TKT-001', 'CUST-001', 'Unable to access cloud storage dashboard after password reset', 'Access Issues', 'high', 'Reset authentication tokens and cleared cache. User can now access dashboard.', 'resolved', '2024-10-06 14:30:00', 5),
('TKT-002', 'CUST-002', 'Invoice discrepancy for order ORD-003', 'Billing', 'medium', 'Corrected invoice sent. Discount applied for inconvenience.', 'resolved', '2024-08-05 09:15:00', 4),
('TKT-003', 'CUST-003', 'Request for bulk license pricing', 'Sales Inquiry', 'low', 'Forwarded to sales team. Enterprise pricing sent.', 'closed', '2024-08-12 11:00:00', 5),
('TKT-004', 'CUST-005', 'MacBook delivery delayed by 2 weeks', 'Shipping', 'high', 'Expedited shipping arranged. 10% credit applied to account.', 'resolved', '2024-09-05 16:45:00', 3),
('TKT-005', 'CUST-007', 'CRM software integration failing with existing ERP', 'Technical', 'critical', 'Engineering team identified API version mismatch. Patch deployed.', 'resolved', '2024-11-22 10:30:00', 5),
('TKT-006', 'CUST-006', 'Need to add users to security suite license', 'License Management', 'medium', 'License expanded. Additional seats activated.', 'resolved', '2024-11-18 13:00:00', 5);

-- Insert Knowledge Base Articles
INSERT INTO KNOWLEDGE_BASE (DOC_ID, TITLE, CONTENT, CATEGORY, SUBCATEGORY, TAGS, SOURCE) VALUES
('KB-001', 'Return Policy', 'Our return policy allows returns within 30 days of purchase for most products. Electronics must be returned within 14 days in original packaging. Software licenses are non-refundable once activated. Enterprise customers may have custom return terms specified in their contracts. To initiate a return, contact support with your order number.', 'Policies', 'Returns', ARRAY_CONSTRUCT('returns', 'refund', 'policy'), 'policy'),
('KB-002', 'Enterprise Pricing Tiers', 'Enterprise pricing is available for orders exceeding $50,000 annually or 100+ licenses. Tier 1 (100-499 licenses): 15% discount. Tier 2 (500-999 licenses): 25% discount. Tier 3 (1000+ licenses): Custom pricing with dedicated account manager. Volume discounts are applied automatically at checkout for eligible customers.', 'Sales', 'Pricing', ARRAY_CONSTRUCT('enterprise', 'pricing', 'discount', 'volume'), 'manual'),
('KB-003', 'Cloud Storage Technical Specifications', 'Our enterprise cloud storage solution offers: 99.99% uptime SLA, AES-256 encryption at rest and in transit, automatic geo-redundancy across 3 regions, real-time sync with conflict resolution, API rate limits of 10,000 requests per minute for enterprise tier, and compliance certifications including SOC 2 Type II, ISO 27001, and HIPAA.', 'Products', 'Cloud Storage', ARRAY_CONSTRUCT('cloud', 'storage', 'specifications', 'technical'), 'api_docs'),
('KB-004', 'CRM Integration Guide', 'To integrate our CRM with external systems: 1) Generate API keys from Settings > Integrations. 2) Use OAuth 2.0 for authentication. 3) Available endpoints: /contacts, /deals, /activities, /reports. 4) Webhook support for real-time event notifications. 5) Pre-built connectors available for Salesforce, SAP, and Oracle. Rate limits: 1000 API calls per hour for standard, unlimited for enterprise.', 'Products', 'CRM', ARRAY_CONSTRUCT('crm', 'integration', 'api', 'guide'), 'api_docs'),
('KB-005', 'Shipping and Delivery Times', 'Standard shipping: 5-7 business days (free for orders over $500). Express shipping: 2-3 business days ($25 flat rate). Next-day delivery: Available in select metro areas ($50). International shipping: 7-14 business days, duties and taxes may apply. Enterprise customers with annual contracts receive free express shipping on all orders.', 'Policies', 'Shipping', ARRAY_CONSTRUCT('shipping', 'delivery', 'logistics'), 'policy'),
('KB-006', 'Security Suite Features', 'Enterprise Security Suite includes: Advanced threat detection with ML-based anomaly detection, endpoint protection for up to 10,000 devices per license, network monitoring and intrusion prevention, email security with anti-phishing, data loss prevention (DLP), security information and event management (SIEM) integration, 24/7 SOC support for critical incidents.', 'Products', 'Security', ARRAY_CONSTRUCT('security', 'enterprise', 'features'), 'manual'),
('KB-007', 'Customer Segment Definitions', 'Customer segments are defined as follows: Enterprise - Annual spend > $100,000 or 500+ employees, dedicated account manager, custom SLAs. SMB (Small-Medium Business) - Annual spend $10,000-$100,000 or 50-499 employees, priority support. Consumer - Individual purchasers or businesses with <50 employees, standard support.', 'Internal', 'Definitions', ARRAY_CONSTRUCT('segments', 'customers', 'definitions'), 'manual'),
('KB-008', 'Q4 2024 Promotion Terms', 'Q4 2024 Holiday Promotion: Valid October 1 - December 31, 2024. 20% off all software licenses for new customers. Free upgrade to next storage tier for existing cloud customers. Bundle discount: Purchase laptop + accessories for additional 10% off. Enterprise customers: Contact sales for custom year-end pricing. Promotion codes cannot be combined with other offers.', 'Sales', 'Promotions', ARRAY_CONSTRUCT('promotion', 'q4', '2024', 'discount'), 'manual');

-- ============================================================================
-- ANALYTICS - Aggregated Data
-- ============================================================================

USE SCHEMA ANALYTICS;

-- Populate Daily Sales Metrics (sample for Q4 2024)
INSERT INTO DAILY_SALES_METRICS (DATE, TOTAL_REVENUE, ORDER_COUNT, AVG_ORDER_VALUE, UNIQUE_CUSTOMERS, UNITS_SOLD, REFUND_AMOUNT, NET_REVENUE)
SELECT 
    ORDER_DATE,
    SUM(AMOUNT) as TOTAL_REVENUE,
    COUNT(DISTINCT ORDER_ID) as ORDER_COUNT,
    AVG(AMOUNT) as AVG_ORDER_VALUE,
    COUNT(DISTINCT CUSTOMER_ID) as UNIQUE_CUSTOMERS,
    SUM(QUANTITY) as UNITS_SOLD,
    0 as REFUND_AMOUNT,
    SUM(AMOUNT) as NET_REVENUE
FROM RAW_DATA.ORDERS
GROUP BY ORDER_DATE;

-- Populate Customer Segments
INSERT INTO CUSTOMER_SEGMENTS (SEGMENT_ID, SEGMENT_NAME, CUSTOMER_COUNT, TOTAL_LTV, AVG_LTV, TOTAL_ORDERS, AVG_ORDER_VALUE)
SELECT 
    'SEG-' || ROW_NUMBER() OVER (ORDER BY c.SEGMENT) as SEGMENT_ID,
    c.SEGMENT as SEGMENT_NAME,
    COUNT(DISTINCT c.CUSTOMER_ID) as CUSTOMER_COUNT,
    SUM(c.LIFETIME_VALUE) as TOTAL_LTV,
    AVG(c.LIFETIME_VALUE) as AVG_LTV,
    COUNT(DISTINCT o.ORDER_ID) as TOTAL_ORDERS,
    AVG(o.AMOUNT) as AVG_ORDER_VALUE
FROM RAW_DATA.CUSTOMERS c
LEFT JOIN RAW_DATA.ORDERS o ON c.CUSTOMER_ID = o.CUSTOMER_ID
GROUP BY c.SEGMENT;

-- Populate Product Performance (Q4 2024)
INSERT INTO PRODUCT_PERFORMANCE (PRODUCT_ID, PRODUCT_NAME, CATEGORY, UNITS_SOLD, REVENUE, RETURN_RATE, AVG_RATING, REVIEW_COUNT, PERIOD, PERIOD_VALUE)
SELECT 
    p.PRODUCT_ID,
    p.NAME as PRODUCT_NAME,
    p.CATEGORY,
    COALESCE(SUM(o.QUANTITY), 0) as UNITS_SOLD,
    COALESCE(SUM(o.AMOUNT), 0) as REVENUE,
    0 as RETURN_RATE,
    4.5 as AVG_RATING,
    FLOOR(RANDOM() * 100 + 10) as REVIEW_COUNT,
    'quarterly' as PERIOD,
    'Q4-2024' as PERIOD_VALUE
FROM RAW_DATA.PRODUCTS p
LEFT JOIN RAW_DATA.ORDERS o ON p.PRODUCT_ID = o.PRODUCT_ID AND o.QUARTER = 'Q4-2024'
GROUP BY p.PRODUCT_ID, p.NAME, p.CATEGORY;
