# Chain of Verification (CoVe) with Snowflake Cortex

## Project Overview

This project implements a **Chain of Verification (CoVe)** system to reduce hallucination in LLM responses using Snowflake Cortex AI services. The system leverages Cortex Analyst for semantic data queries, Cortex Search for retrieval-augmented generation, and Cortex Agents for orchestration—all integrated with LangGraph for the CoVe workflow.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER QUERY                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LANGGRAPH CoVe WORKFLOW                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   STEP 1     │  │   STEP 2     │  │   STEP 3     │  │   STEP 4     │     │
│  │  Generate    │─▶│    Plan      │─▶│   Execute    │─▶│   Final      │     │
│  │  Baseline    │  │ Verification │  │ Verification │  │  Response    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
         │                   │                  │                  │
         ▼                   ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SNOWFLAKE CORTEX SERVICES                             │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │  CORTEX LLM     │  │  CORTEX SEARCH  │  │  CORTEX ANALYST │              │
│  │  (COMPLETE)     │  │  (RAG Service)  │  │  (Semantic SQL) │              │
│  │                 │  │                 │  │                 │              │
│  │  - claude-3.5   │  │  - Vector       │  │  - Natural      │              │
│  │  - llama3.1-70b │  │    Search       │  │    Language     │              │
│  │  - mistral-large│  │  - Hybrid       │  │    to SQL       │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                    CORTEX FUNCTIONS                          │            │
│  │  SNOWFLAKE.CORTEX.COMPLETE()  - LLM inference               │            │
│  │  SNOWFLAKE.CORTEX.EMBED_TEXT_768() - Text embeddings        │            │
│  │  SNOWFLAKE.CORTEX.SENTIMENT() - Sentiment analysis          │            │
│  │  SNOWFLAKE.CORTEX.EXTRACT_ANSWER() - QA extraction          │            │
│  └─────────────────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SNOWFLAKE DATABASE                                   │
│                                                                              │
│  Database: COVE_PROJECT_DB                                                   │
│  ├── Schema: RAW_DATA          (Source data tables)                         │
│  ├── Schema: ANALYTICS         (Processed/aggregated data)                  │
│  ├── Schema: CORTEX_SERVICES   (Search services, semantic views)            │
│  └── Schema: COVE_LOGS         (Verification audit trail)                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Snowflake Database Structure

#### Database: `COVE_PROJECT_DB`

| Schema | Purpose |
|--------|---------|
| `RAW_DATA` | Source tables for business data |
| `ANALYTICS` | Aggregated metrics and KPIs |
| `CORTEX_SERVICES` | Cortex Search services and semantic views |
| `COVE_LOGS` | CoVe execution logs and audit trail |

#### Tables

**RAW_DATA Schema:**

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `PRODUCTS` | Product catalog | product_id, name, description, category, price |
| `CUSTOMERS` | Customer information | customer_id, name, email, segment, region |
| `ORDERS` | Transaction records | order_id, customer_id, product_id, amount, order_date |
| `SUPPORT_TICKETS` | Customer support data | ticket_id, customer_id, issue, resolution, created_at |
| `KNOWLEDGE_BASE` | Documentation/FAQs | doc_id, title, content, category, embedding |

**ANALYTICS Schema:**

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `DAILY_SALES_METRICS` | Daily aggregated sales | date, total_revenue, order_count, avg_order_value |
| `CUSTOMER_SEGMENTS` | Customer segmentation | segment_id, segment_name, customer_count, total_ltv |
| `PRODUCT_PERFORMANCE` | Product analytics | product_id, units_sold, revenue, return_rate |

**COVE_LOGS Schema:**

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `VERIFICATION_RUNS` | CoVe execution logs | run_id, query, baseline_response, verified_response, timestamp |
| `VERIFICATION_QUESTIONS` | Generated VQs per run | vq_id, run_id, fact_claim, verification_question, answer, is_consistent |

---

### 2. Cortex Analyst Setup

**Purpose:** Enable natural language queries over business data with SQL generation.

#### Semantic View Definition

```yaml
# semantic_model.yaml
name: cove_business_model
description: Business analytics semantic model for CoVe verification

tables:
  - name: ORDERS
    description: Customer order transactions
    columns:
      - name: ORDER_ID
        description: Unique order identifier
      - name: CUSTOMER_ID
        description: Reference to customer
      - name: AMOUNT
        description: Order total in USD
        synonyms: [revenue, sales, total]
      - name: ORDER_DATE
        description: Date of purchase
        
  - name: PRODUCTS
    description: Product catalog
    columns:
      - name: PRODUCT_ID
        description: Unique product identifier
      - name: NAME
        description: Product name
      - name: CATEGORY
        description: Product category
        
  - name: CUSTOMERS
    description: Customer master data
    columns:
      - name: CUSTOMER_ID
        description: Unique customer identifier
      - name: SEGMENT
        description: Customer segment (Enterprise, SMB, Consumer)
      - name: REGION
        description: Geographic region

relationships:
  - from: ORDERS.CUSTOMER_ID
    to: CUSTOMERS.CUSTOMER_ID
  - from: ORDERS.PRODUCT_ID
    to: PRODUCTS.PRODUCT_ID

metrics:
  - name: total_revenue
    expression: SUM(ORDERS.AMOUNT)
    description: Total revenue from orders
    
  - name: order_count
    expression: COUNT(DISTINCT ORDERS.ORDER_ID)
    description: Number of unique orders
    
  - name: avg_order_value
    expression: AVG(ORDERS.AMOUNT)
    description: Average order value
```

---

### 3. Cortex Search Setup

**Purpose:** Provide RAG capabilities for verification against knowledge base.

#### Search Service Configuration

| Service Name | Source Table | Searchable Columns | Use Case |
|--------------|--------------|-------------------|----------|
| `KNOWLEDGE_SEARCH` | `KNOWLEDGE_BASE` | title, content | Verify against documentation |
| `PRODUCT_SEARCH` | `PRODUCTS` | name, description | Verify product claims |
| `TICKET_SEARCH` | `SUPPORT_TICKETS` | issue, resolution | Verify support-related facts |

---

### 4. Cortex Agent Setup

**Purpose:** Orchestrate multi-tool verification workflows.

#### Agent Configuration

```yaml
# cortex_agent.yaml
name: cove_verification_agent
description: Agent for executing Chain of Verification

tools:
  - name: cortex_analyst
    type: cortex_analyst_tool
    semantic_model: cove_business_model
    description: Query business data using natural language
    
  - name: cortex_search
    type: cortex_search_tool
    service: KNOWLEDGE_SEARCH
    description: Search knowledge base for verification
    
  - name: sql_executor
    type: sql_tool
    description: Execute verified SQL queries

instructions: |
  You are a verification agent. When asked to verify a fact:
  1. Use cortex_analyst to query structured data
  2. Use cortex_search to find supporting documentation
  3. Return factual, verified information only
```

---

### 5. Chain of Verification (CoVe) Implementation

#### LangGraph Workflow

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  BASELINE   │  ◄── Cortex Complete
                    │  RESPONSE   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    PLAN     │  ◄── Cortex Complete
                    │VERIFICATION │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
            ┌───────┤   EXECUTE   │───────┐
            │       │VERIFICATION │       │
            │       └─────────────┘       │
            ▼               │             ▼
     ┌───────────┐          │      ┌───────────┐
     │  CORTEX   │          │      │  CORTEX   │
     │  ANALYST  │          │      │  SEARCH   │
     └─────┬─────┘          │      └─────┬─────┘
            │               │             │
            └───────────────┼─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   FINAL     │  ◄── Cortex Complete
                    │  RESPONSE   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    END      │
                    └─────────────┘
```

#### State Schema

```python
from typing import TypedDict, List, Optional
from pydantic import BaseModel

class VerificationQuestion(BaseModel):
    fact_claim: str
    question: str
    answer: Optional[str] = None
    source: Optional[str] = None  # "cortex_analyst" | "cortex_search" | "llm"
    is_consistent: Optional[bool] = None

class CoVeState(TypedDict):
    # Input
    user_query: str
    
    # Step 1: Baseline
    baseline_response: str
    
    # Step 2: Plan
    verification_questions: List[VerificationQuestion]
    
    # Step 3: Execute
    verification_results: List[VerificationQuestion]
    
    # Step 4: Final
    final_response: str
    
    # Metadata
    run_id: str
    model_used: str
    timestamp: str
```

---

## Technical Specifications

### Dependencies

```
snowflake-connector-python>=3.0.0
snowflake-snowpark-python>=1.5.0
langgraph>=0.1.0
langchain>=0.2.0
langchain-community>=0.2.0
pydantic>=2.0.0
```

### Cortex Functions Used

| Function | Purpose in CoVe |
|----------|-----------------|
| `SNOWFLAKE.CORTEX.COMPLETE()` | Generate baseline, plan VQs, final response |
| `SNOWFLAKE.CORTEX.EMBED_TEXT_768()` | Create embeddings for semantic search |
| `SNOWFLAKE.CORTEX.EXTRACT_ANSWER()` | Extract specific answers from context |

### Supported Models

| Model | Use Case |
|-------|----------|
| `claude-3-5-sonnet` | Complex reasoning, final response generation |
| `llama3.1-70b` | Baseline generation, verification questions |
| `mistral-large2` | Fast verification execution |

---

## Implementation Phases

### Phase 1: Database & Table Setup
- [ ] Create database `COVE_PROJECT_DB`
- [ ] Create schemas (RAW_DATA, ANALYTICS, CORTEX_SERVICES, COVE_LOGS)
- [ ] Create and populate source tables
- [ ] Create logging tables for CoVe audit trail

### Phase 2: Cortex Services Setup
- [ ] Create Cortex Search service on KNOWLEDGE_BASE
- [ ] Define and deploy semantic model for Cortex Analyst
- [ ] Configure Cortex Agent with tools
- [ ] Test individual Cortex functions

### Phase 3: CoVe Core Implementation
- [ ] Implement LangGraph state machine
- [ ] Create baseline generation node (Step 1)
- [ ] Create verification planning node (Step 2)
- [ ] Create verification execution node (Step 3)
- [ ] Create final response node (Step 4)
- [ ] Add conditional routing for verification sources

### Phase 4: Integration & Testing
- [ ] Integrate Cortex Analyst for data verification
- [ ] Integrate Cortex Search for knowledge verification
- [ ] Implement factored verification (parallel execution)
- [ ] Add logging and audit trail
- [ ] Create evaluation metrics

### Phase 5: Deployment
- [ ] Deploy as Snowflake Streamlit app
- [ ] Create API endpoints (optional)
- [ ] Set up monitoring and alerting
- [ ] Document usage and examples

---

## Project Structure

```
cove-snowflake/
├── README.md
├── PROJECT_DEFINITION.md
├── requirements.txt
│
├── sql/
│   ├── 01_create_database.sql
│   ├── 02_create_tables.sql
│   ├── 03_create_cortex_search.sql
│   ├── 04_create_cortex_agent.sql
│   └── 05_seed_data.sql
│
├── semantic_models/
│   └── cove_business_model.yaml
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── snowflake_client.py
│   │
│   ├── cortex/
│   │   ├── __init__.py
│   │   ├── complete.py
│   │   ├── search.py
│   │   ├── analyst.py
│   │   └── agent.py
│   │
│   ├── cove/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── baseline.py
│   │   │   ├── plan_verification.py
│   │   │   ├── execute_verification.py
│   │   │   └── final_response.py
│   │   ├── graph.py
│   │   └── prompts.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── logging.py
│
├── app/
│   └── streamlit_app.py
│
└── tests/
    ├── test_cortex_services.py
    ├── test_cove_workflow.py
    └── test_integration.py
```

---

## Example Usage

### Input Query
```
"What was our total revenue from Enterprise customers in Q4 2024, 
and which product category performed best?"
```

### CoVe Execution Flow

**Step 1 - Baseline Response:**
```
"In Q4 2024, Enterprise customers generated $2.3M in revenue. 
The Electronics category performed best with $890K in sales."
```

**Step 2 - Verification Questions:**
```
1. "What was the exact total revenue from Enterprise segment in Q4 2024?"
2. "Which product category had the highest revenue in Q4 2024?"
3. "What was the revenue for the Electronics category in Q4 2024?"
```

**Step 3 - Verification Execution:**
```
VQ1 → Cortex Analyst → SQL: SELECT SUM(amount) FROM orders WHERE segment='Enterprise' AND quarter='Q4-2024'
      Result: $2,287,450 ✓ Consistent

VQ2 → Cortex Analyst → SQL: SELECT category, SUM(amount) FROM orders GROUP BY category ORDER BY 2 DESC LIMIT 1
      Result: Electronics ✓ Consistent

VQ3 → Cortex Analyst → SQL: SELECT SUM(amount) FROM orders WHERE category='Electronics' AND quarter='Q4-2024'
      Result: $912,340 ✗ Inconsistent (baseline said $890K)
```

**Step 4 - Final Verified Response:**
```
"In Q4 2024, Enterprise customers generated $2.29M in revenue. 
The Electronics category performed best with $912K in sales."
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Factual Accuracy | >95% | Manual review of verified responses |
| Hallucination Reduction | >50% | Compare baseline vs verified responses |
| Latency | <10s | End-to-end CoVe execution time |
| Verification Coverage | >80% | % of claims verified against data sources |

---

## References

- [Chain-of-Verification Paper (arXiv)](https://arxiv.org/abs/2309.11495)
- [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Cortex Analyst Guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Cortex Search Guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
