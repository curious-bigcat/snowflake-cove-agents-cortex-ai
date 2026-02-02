# Eliminating LLM Hallucinations with Chain of Verification: A Snowflake Cortex Agents Implementation

*How we built a self-verifying AI system that fact-checks its own responses using Snowflake's Cortex Agents, Analyst, and Search*

---

![Chain of Verification Banner](https://images.unsplash.com/photo-1677442136019-21780ecad995?w=1200)

## The Hallucination Problem

If you've worked with Large Language Models, you've encountered it: that confident, articulate response that turns out to be completely fabricated. LLMs don't know what they don't know — they generate plausible-sounding text regardless of factual accuracy.

In enterprise settings, this isn't just annoying — it's dangerous. Imagine an AI assistant confidently reporting that Q4 revenue was $2.5 million when the actual figure was $1.8 million. Or stating that your return policy allows 90-day returns when it's actually 30 days. These hallucinations erode trust and can lead to costly business decisions.

**But what if the AI could verify its own claims before presenting them to users?**

That's exactly what Chain of Verification (CoVe) does, and in this article, I'll show you how we implemented it using Snowflake Cortex Agents.

---

## The Chain of Verification Methodology

In September 2023, researchers at Meta AI published a groundbreaking paper: [Chain-of-Verification Reduces Hallucination in Large Language Models](https://arxiv.org/abs/2309.11495). The core insight is elegantly simple:

> Instead of trusting the LLM's initial response, break it into individual claims and verify each one independently.

The methodology consists of four steps:

### 1. Generate Baseline Response
Ask the LLM your question and get an initial response. This response may contain hallucinations.

### 2. Plan Verifications
Analyze the response and extract all factual claims that can be verified. For each claim, formulate a verification question.

### 3. Execute Verifications (The Key Innovation)
Here's where it gets interesting. The paper introduces **Factored Verification** — each claim is verified through a *completely independent* query. Why? Because if you ask the model to verify claims while showing it the original response, it tends to agree with itself due to attention mechanisms.

### 4. Generate Final Verified Response
Compare the original claims with the verified information. If inconsistencies are found, generate a corrected response.

---

## Why Snowflake Cortex Agents?

To implement CoVe effectively, we need an AI system that can:

- Query structured data (databases, data warehouses)
- Search unstructured knowledge bases (documents, policies)
- Orchestrate between multiple data sources
- Provide transparent, auditable responses

**Snowflake Cortex Agents** check all these boxes. A Cortex Agent is an AI orchestrator that can use multiple tools:

- **Cortex Analyst**: Converts natural language to SQL queries against your data
- **Cortex Search**: Performs RAG (Retrieval-Augmented Generation) over document collections

This combination is perfect for CoVe — we can verify numerical claims against actual database records and policy claims against source documents.

---

## Architecture Overview

Here's the system we built:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit Application                        │
│            (Real-time streaming verification UI)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Cortex Agent REST API Client                    │
│         (SSE parsing, tool call extraction, SQL capture)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COVE_BUSINESS_AGENT                          │
│                                                                 │
│   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐    │
│   │Business       │   │Knowledge      │   │Product        │    │
│   │Analyst        │   │Search         │   │Search         │    │
│   │(Text-to-SQL)  │   │(Policy RAG)   │   │(Catalog RAG)  │    │
│   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘    │
│           │                   │                   │             │
│           ▼                   ▼                   ▼             │
│   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐    │
│   │ Semantic View │   │Knowledge Base │   │Product Catalog│    │
│   │ (Sales Data)  │   │  (Policies)   │   │  (Products)   │    │
│   └───────────────┘   └───────────────┘   └───────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

The key insight: **every verification is an independent agent call**. This implements the "Factored Verification" from the paper — the agent has no memory of the original response when verifying each claim.

---

## Implementation Deep Dive

### Setting Up the Cortex Agent

First, we create a Cortex Agent with three tools:

```sql
CREATE OR REPLACE AGENT COVE_PROJECT_DB.CORTEX_SERVICES.COVE_BUSINESS_AGENT
FROM SPECIFICATION $$
models:
  orchestration: claude-3-5-sonnet
tools:
  - tool_spec:
      type: "cortex_analyst_text_to_sql"
      name: "BusinessAnalyst"
  - tool_spec:
      type: "cortex_search"
      name: "KnowledgeSearch"
  - tool_spec:
      type: "cortex_search"
      name: "ProductSearch"
tool_resources:
  BusinessAnalyst:
    semantic_view: "COVE_PROJECT_DB.CORTEX_SERVICES.BUSINESS_SEMANTIC_VIEW"
    execution_environment:
      type: "warehouse"
      warehouse: "COMPUTE_WH"
  KnowledgeSearch:
    name: "COVE_PROJECT_DB.CORTEX_SERVICES.KNOWLEDGE_SEARCH"
    max_results: 5
  ProductSearch:
    name: "COVE_PROJECT_DB.CORTEX_SERVICES.PRODUCT_SEARCH"
    max_results: 5
$$;
```

The agent uses Claude 3.5 Sonnet for orchestration and can dynamically choose which tool to use based on the query.

### The Cortex Agent Client

We built a Python client that handles the REST API communication with full SSE (Server-Sent Events) parsing:

```python
@dataclass
class AgentResponse:
    """Structured response from Cortex Agent."""
    text: str = ""
    tool_calls: list = field(default_factory=list)
    tool_results: list = field(default_factory=list)
    sql_queries: list = field(default_factory=list)
    thinking_text: str = ""
    raw_events: list = field(default_factory=list)

class CortexAgentClient:
    def __init__(self):
        config = self._load_config()
        self.account = config.get("account", "")
        self.pat = config.get("password")  # PAT from config.toml
        
    def run(self, message: str) -> AgentResponse:
        """Execute a query against the Cortex Agent."""
        response = requests.post(
            self.api_url,
            headers={"Authorization": f"Bearer {self.pat}"},
            json={"messages": [{"role": "user", "content": message}]},
            stream=True
        )
        
        result = AgentResponse()
        for event, data in self._iter_sse(response):
            # Parse SSE events: text, tool_use, tool_result, etc.
            self._process_event(event, data, result)
        
        return result
```

The client captures everything: the agent's thinking process, tool calls, SQL queries executed, and raw results. This transparency is crucial for verification.

### The CoVe Workflow Implementation

Here's the core of our implementation:

```python
def run_cove(query: str) -> CoVeResult:
    client = CortexAgentClient()
    
    # STEP 1: Get initial response
    initial_response = client.run(query)
    
    # STEP 2: Extract claims
    claims = extract_claims(client, query, initial_response.text)
    
    # STEP 3: Verify each claim INDEPENDENTLY
    verifications = []
    for claim in claims:
        # Key: This is a NEW agent call with NO context from original response
        verification = verify_claim(client, claim)
        verifications.append(verification)
    
    # STEP 4: Compare and correct
    if any(v.is_consistent == False for v in verifications):
        final_response = generate_corrected_response(
            client, query, initial_response, verifications
        )
    else:
        final_response = initial_response
    
    return CoVeResult(
        initial_response=initial_response,
        verifications=verifications,
        final_response=final_response
    )
```

### Claim Extraction

We use the agent itself to extract verifiable claims:

```python
def extract_claims(client, query, response_text):
    extraction_prompt = f"""Analyze this response and list all factual claims.

Original Question: {query}

Response to Analyze:
{response_text}

For each claim, provide:
CLAIM: [the exact claim]
QUESTION: [verification question]
SOURCE: [analyst or search]
---"""

    extract_response = client.run(extraction_prompt)
    return parse_claims(extract_response.text)
```

The agent categorizes each claim by source:
- **analyst**: Numerical data, metrics, aggregations → verified via SQL
- **search**: Policies, procedures, product info → verified via RAG

### Independent Verification (Factored)

This is the critical piece. Each claim is verified through a **completely independent** agent call:

```python
def verify_claim(client, claim):
    # Independent query - no context from original response
    verification_response = client.run(claim['verification_question'])
    
    # Compare original claim with verification
    comparison_prompt = f"""Compare these statements:

ORIGINAL CLAIM: {claim['claim']}

VERIFIED INFORMATION: {verification_response.text}

Respond with:
- CONSISTENT: if they match
- INCONSISTENT: if they contradict
- UNVERIFIED: if you cannot determine"""

    comparison = client.run(comparison_prompt)
    
    return ClaimVerification(
        claim=claim['claim'],
        verification_response=verification_response,
        is_consistent=parse_consistency(comparison.text)
    )
```

---

## The Streamlit UI: Real-Time Verification

We built a Streamlit app that shows the verification process in real-time:

```python
def main():
    st.title("Chain of Verification (CoVe)")
    
    query = st.text_input("Enter your question:")
    
    if st.button("Run CoVe Verification"):
        # STEP 1: Show initial response immediately
        st.header("Step 1: Initial Agent Response")
        initial_response = client.run(query)
        st.info(initial_response.text)
        display_sql_queries(initial_response.sql_queries)
        
        # STEP 2: Extract and show claims
        claims = extract_claims(client, query, initial_response.text)
        st.header("Step 2: Extracted Claims")
        for claim in claims:
            st.markdown(f"• {claim['claim']}")
        
        # STEP 3: Stream verification results as they complete
        st.header("Step 3: Independent Verification")
        for i, claim in enumerate(claims):
            with st.spinner(f"Verifying claim {i+1}..."):
                verification = verify_claim(client, claim)
            
            # Display immediately after each verification
            status = "✅" if verification.is_consistent else "❌"
            st.expander(f"{status} {claim['claim'][:50]}..."):
                st.write(verification.explanation)
                display_sql_queries(verification.sql_queries)
        
        # STEP 4: Show comparison
        st.header("Step 4: Final Verified Response")
        display_comparison(initial_response, verifications)
```

The streaming approach is important — users see each verification complete in real-time rather than waiting for all verifications to finish.

---

## Real-World Example

Let's walk through a complete verification:

**Query:** "What was total revenue in Q4 2024 and what is our return policy?"

### Step 1: Initial Response
```
The total revenue in Q4 2024 was $1,843,733.00. Our return policy 
allows customers to return products within 30 days of purchase for 
a full refund, provided items are in original condition.
```

### Step 2: Extracted Claims
1. **Claim**: "Total revenue in Q4 2024 was $1,843,733.00"
   - Source: `analyst`
   - Verification Question: "What was the total revenue in Q4 2024?"

2. **Claim**: "Return policy allows 30-day returns for full refund"
   - Source: `search`
   - Verification Question: "What is the return policy duration?"

### Step 3: Independent Verification

**Verification 1** (via Cortex Analyst):
```sql
SELECT SUM(TOTAL_AMOUNT) as TOTAL_REVENUE
FROM SALES_TRANSACTIONS
WHERE TRANSACTION_DATE BETWEEN '2024-10-01' AND '2024-12-31'
```
Result: `$1,843,733.00` → **✅ CONSISTENT**

**Verification 2** (via Cortex Search):
Retrieved document: "Return Policy - Customers may return items within 30 days..."
Result: 30 days confirmed → **✅ CONSISTENT**

### Step 4: Final Response
Both claims verified! Original response is accurate — no corrections needed.

---

## What Happens When Hallucinations Are Detected?

Here's where CoVe really shines. If the initial response contained:

> "Total revenue in Q4 2024 was **$2,500,000**..."

The verification would flag this:

```
CLAIM: Q4 2024 revenue was $2,500,000
VERIFIED: Actual Q4 2024 revenue was $1,843,733.00
STATUS: ❌ INCONSISTENT

Generating corrected response...
```

The system then generates a new response incorporating the verified data:

> "Total revenue in Q4 2024 was **$1,843,733.00**..."

---

## Key Benefits

### 1. Auditable Verification
Every claim shows the SQL query or search results used for verification. You can see exactly how the system reached its conclusions.

### 2. Source-Appropriate Verification
Numbers are verified against actual database records via SQL. Policies are verified against source documents via RAG. The right tool for each claim type.

### 3. Factored Independence
By verifying each claim independently, we prevent the "agreeing with itself" problem that plagues naive verification approaches.

### 4. Real-Time Transparency
Users see the verification process unfold in real-time, building trust in the system's conclusions.

### 5. Self-Correcting
When inconsistencies are found, the system automatically generates corrected responses.

---

## Deployment

We containerized the entire solution with Docker:

```yaml
# docker-compose.yml
services:
  cove-app:
    build: .
    ports:
      - "8503:8503"
    volumes:
      - ~/.snowflake:/root/.snowflake:ro
```

```bash
docker-compose up --build -d
# Access at http://localhost:8503
```

---

## Lessons Learned

### 1. Independent Verification is Non-Negotiable
Early versions verified all claims in a single prompt. The model consistently agreed with itself. Factored verification (separate API calls) is essential.

### 2. Claim Categorization Matters
Not all claims should be verified the same way. Revenue figures need SQL; policy statements need document search. Categorizing claims by verification source dramatically improves accuracy.

### 3. Show Your Work
Displaying the SQL queries and search results builds trust. Users can verify the verification.

### 4. Stream Results
Waiting for all verifications to complete before showing anything is frustrating. Streaming results as they complete provides better UX.

---

## Future Improvements

1. **Confidence Scoring**: Weight verifications by data freshness and source reliability
2. **Verification Caching**: Cache recent verifications to reduce redundant queries
3. **Multi-Step Reasoning**: For complex claims that require joining multiple data sources
4. **Contradiction Resolution**: When multiple sources conflict, provide transparent reasoning about which to trust

---

## Conclusion

LLM hallucinations aren't going away — they're inherent to how these models work. But with Chain of Verification, we can build systems that verify their own outputs against authoritative sources before presenting them to users.

Snowflake Cortex Agents provide the perfect foundation: seamless access to both structured data (via Cortex Analyst) and unstructured knowledge (via Cortex Search), all orchestrated by an AI that can dynamically choose the right verification approach for each claim.

The result? An AI assistant that doesn't just sound confident — it actually is.

---

## Resources

- **GitHub Repository**: [snowflake-cove-agents-cortex-ai](https://github.com/curious-bigcat/snowflake-cove-agents-cortex-ai)
- **Original Paper**: [Chain-of-Verification Reduces Hallucination in Large Language Models](https://arxiv.org/abs/2309.11495)
- **Snowflake Cortex Agents**: [Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)

---

*Built with Snowflake Cortex Code*

---

**Tags**: #AI #LLM #Snowflake #Hallucination #Verification #RAG #TextToSQL #MachineLearning #DataEngineering
