# Chain of Verification (CoVe) with Snowflake Cortex Agents

A production-ready implementation of the **Chain-of-Verification (CoVe)** methodology using **Snowflake Cortex Agents** to reduce hallucinations in Large Language Model responses.

[![Paper](https://img.shields.io/badge/arXiv-2309.11495-b31b1b.svg)](https://arxiv.org/abs/2309.11495)
[![Snowflake](https://img.shields.io/badge/Snowflake-Cortex%20Agents-29B5E8.svg)](https://www.snowflake.com/en/data-cloud/cortex/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B.svg)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docs.docker.com/compose/)

---

## 📄 Based On

This project implements the methodology described in:

> **Chain-of-Verification Reduces Hallucination in Large Language Models**  
> Shehzaad Dhuliawala, Mojtaba Komeili, Jing Xu, Roberta Raileanu, Xian Li, Asli Celikyilmaz, Jason Weston  
> Meta AI Research, 2023  
> [arXiv:2309.11495](https://arxiv.org/abs/2309.11495)

### Key Concepts from the Paper

1. **Baseline Response**: Generate an initial response using the LLM
2. **Plan Verifications**: Identify factual claims that can be verified
3. **Execute Verifications**: Answer each verification question independently
4. **Generate Final Response**: Produce a corrected response incorporating verification results

The paper introduces **Factored Verification** - verifying each claim independently to prevent the model from repeating hallucinated information due to attention on its own prior outputs.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Streamlit Application                           │
│                           (app_agent.py)                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Cortex Agent REST API Client                       │
│                        (src/cortex/agent.py)                            │
│                                                                         │
│  • SSE (Server-Sent Events) parsing                                     │
│  • Tool call extraction (SQL, Search results)                           │
│  • Thinking/reasoning capture                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Snowflake Cortex Agent                               │
│                  (COVE_BUSINESS_AGENT)                                  │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ BusinessAnalyst │  │ KnowledgeSearch │  │  ProductSearch  │         │
│  │ (Cortex Analyst)│  │ (Cortex Search) │  │ (Cortex Search) │         │
│  │   Text-to-SQL   │  │   RAG Search    │  │  Product RAG    │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
│           │                    │                    │                   │
│           ▼                    ▼                    ▼                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  Semantic View  │  │ Knowledge Base  │  │ Product Catalog │         │
│  │  (Sales Data)   │  │   (Policies)    │  │   (Products)    │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 CoVe Workflow

The application implements the 4-step CoVe process:

### Step 1: Initial Agent Response
Query the Cortex Agent with the user's question. The agent orchestrates between Cortex Analyst (for structured data queries) and Cortex Search (for unstructured knowledge retrieval).

### Step 2: Claim Extraction
Extract all verifiable factual claims from the initial response, categorizing each by verification source (analyst for numbers/data, search for policies/knowledge).

### Step 3: Independent Verification (Factored)
**Critical**: Each claim is verified through an **independent** query to the agent. This prevents the model from being biased by its own prior outputs - the key innovation from the CoVe paper.

### Step 4: Comparison & Correction
Compare original claims with verified information, identify inconsistencies, and generate a corrected final response if needed.

---

## 📋 Prerequisites

- **Snowflake Account** with the following features enabled:
  - Cortex Agents
  - Cortex Analyst
  - Cortex Search
  - Semantic Views
- **Warehouse**: A running warehouse (e.g., `COMPUTE_WH`)
- **PAT (Programmatic Access Token)**: For REST API authentication
- **Docker & Docker Compose** (for containerized deployment)

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/curious-bigcat/snowflake-cove-agents-cortex-ai.git
cd snowflake-cove-agents-cortex-ai
```

### 2. Set Up Snowflake Objects

Run the SQL scripts in order to create the required Snowflake objects:

```bash
# Connect to Snowflake and run each script
snowsql -f sql/01_create_database.sql
snowsql -f sql/02_create_tables.sql
snowsql -f sql/03_create_cortex_search.sql
snowsql -f sql/04_create_cortex_agent.sql
snowsql -f sql/05_seed_data.sql
snowsql -f sql/06_create_semantic_view.sql
```

Or run them directly in Snowflake Worksheets/Snowsight.

#### SQL Scripts Overview:

| Script | Description |
|--------|-------------|
| `01_create_database.sql` | Creates `COVE_PROJECT_DB` database and `CORTEX_SERVICES` schema |
| `02_create_tables.sql` | Creates tables: `CUSTOMERS`, `PRODUCTS`, `SALES_TRANSACTIONS`, `KNOWLEDGE_BASE` |
| `03_create_cortex_search.sql` | Creates Cortex Search services: `KNOWLEDGE_SEARCH`, `PRODUCT_SEARCH` |
| `04_create_cortex_agent.sql` | Creates the Cortex Agent with Analyst + Search tools |
| `05_seed_data.sql` | Populates tables with sample data |
| `06_create_semantic_view.sql` | Creates the Semantic View for Cortex Analyst |

### 3. Configure Snowflake Credentials

Create or update your Snowflake config file with your PAT:

```bash
# ~/.snowflake/config.toml
[connections.default]
account = "YOUR_ACCOUNT"      # e.g., "ORGNAME-ACCOUNTNAME"
user = "YOUR_USERNAME"
password = "YOUR_PAT_TOKEN"   # Programmatic Access Token goes here
warehouse = "COMPUTE_WH"
database = "COVE_PROJECT_DB"
schema = "CORTEX_SERVICES"
```

#### How to Generate a PAT:
1. Go to Snowsight → User Menu → Profile
2. Click "Programmatic Access Tokens"
3. Generate a new token with appropriate permissions
4. Copy the token to your `config.toml` password field

### 4. Run with Docker Compose

```bash
# Build and start the container
docker-compose up --build -d

# View logs
docker logs -f cove-streamlit

# Access the app
open http://localhost:8503
```

### 5. Run Locally (Alternative)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Streamlit
streamlit run app_agent.py --server.port 8503
```

---

## 📁 Project Structure

```
snowflake-cove-agents-cortex-ai/
├── app_agent.py                 # Main Streamlit application
├── src/
│   ├── __init__.py
│   ├── config.py                # Configuration utilities
│   ├── snowflake_client.py      # Snowflake connection helper
│   └── cortex/
│       ├── __init__.py
│       └── agent.py             # Cortex Agent REST API client
├── sql/
│   ├── 01_create_database.sql   # Database and schema setup
│   ├── 02_create_tables.sql     # Table definitions
│   ├── 03_create_cortex_search.sql  # Cortex Search services
│   ├── 04_create_cortex_agent.sql   # Cortex Agent definition
│   ├── 05_seed_data.sql         # Sample data
│   └── 06_create_semantic_view.sql  # Semantic View for Analyst
├── semantic_models/
│   └── cove_business_model.yaml # Semantic model definition
├── Dockerfile                   # Container definition
├── docker-compose.yml           # Container orchestration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SNOWFLAKE_PAT` | Programmatic Access Token | Read from config.toml |
| `STREAMLIT_SERVER_PORT` | Streamlit server port | 8503 |

### Cortex Agent Configuration

The agent is configured with three tools in `sql/04_create_cortex_agent.sql`:

```yaml
tools:
  - BusinessAnalyst    # Cortex Analyst (Text-to-SQL)
  - KnowledgeSearch    # Cortex Search (Policies/Docs)
  - ProductSearch      # Cortex Search (Product Catalog)
```

---

## 💡 Usage Examples

### Example 1: Revenue Query (Uses Analyst)
```
Query: "What was total revenue in Q4 2024?"

→ Agent uses BusinessAnalyst tool
→ Generates SQL query against SALES_TRANSACTIONS
→ Returns verified revenue figure
```

### Example 2: Policy Query (Uses Search)
```
Query: "What is our return policy for electronics?"

→ Agent uses KnowledgeSearch tool
→ Searches KNOWLEDGE_BASE for return policy
→ Returns policy details
```

### Example 3: Mixed Query (Uses Both)
```
Query: "What was Enterprise revenue in Q4 2024 and what products do we sell?"

→ Agent uses BusinessAnalyst for revenue data
→ Agent uses ProductSearch for product catalog
→ CoVe verifies both claims independently
```

---

## 🔍 How Verification Works

```
User Query: "What was total revenue in Q4 2024?"
                    │
                    ▼
┌─────────────────────────────────────┐
│ STEP 1: Initial Response            │
│ "Total revenue in Q4 2024 was       │
│  $1,843,733"                        │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│ STEP 2: Extract Claims              │
│ Claim: "Q4 2024 revenue = $1,843,733│
│ Source: analyst                     │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│ STEP 3: Independent Verification    │
│ New query: "What was total revenue  │
│            in Q4 2024?"             │
│ Result: $1,843,733 ✓ CONSISTENT     │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│ STEP 4: Final Response              │
│ Original response verified ✓        │
│ No corrections needed               │
└─────────────────────────────────────┘
```

---

## 📊 Sample Data

The project includes sample data for demonstration:

- **Customers**: 5 customers across Enterprise, SMB, and Startup segments
- **Products**: 10 products across Electronics, Software, and Services categories
- **Sales Transactions**: 20 transactions from 2024
- **Knowledge Base**: 8 policy documents (returns, warranties, shipping, etc.)

---

## 🐳 Docker Commands

```bash
# Build and run
docker-compose up --build -d

# View logs
docker logs -f cove-streamlit

# Stop
docker-compose down

# Rebuild after changes
docker-compose up --build -d --force-recreate
```

---

## 🔒 Security Notes

- **PAT Token**: Store securely in `~/.snowflake/config.toml` with restricted permissions
- **Config File**: The config.toml is mounted read-only in Docker
- **Network**: The container runs on a dedicated Docker network

---

## 📚 References

- [Chain-of-Verification Paper (arXiv:2309.11495)](https://arxiv.org/abs/2309.11495)
- [Snowflake Cortex Agents Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Snowflake Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 👤 Author

Built with [Snowflake Cortex Code](https://docs.snowflake.com/user-guide/snowflake-cortex/cortex-agents)
