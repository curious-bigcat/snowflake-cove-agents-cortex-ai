# Chain of Verification (CoVe) with Cortex Agents

A Streamlit application that implements Chain of Verification (CoVe) using Snowflake Cortex Agents to reduce LLM hallucinations.

## How It Works

1. **Initial Response**: Query the Cortex Agent (with Analyst + Search tools)
2. **Claim Extraction**: Extract verifiable claims from the response
3. **Independent Verification**: Verify each claim independently (factored verification)
4. **Comparison**: Compare original claims with verified information
5. **Correction**: Generate corrected response if inconsistencies found

## Prerequisites

- Snowflake account with Cortex Agents enabled
- PAT (Programmatic Access Token) in `~/.snowflake/config.toml`
- Docker and Docker Compose

## Quick Start

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:8503
```

## Configuration

The app reads Snowflake credentials from `~/.snowflake/config.toml`:

```toml
[connections.default]
account = "your-account"
user = "your-user"
password = "your-pat-token"  # PAT goes here
```

## Project Structure

```
CoVe/
├── app_agent.py          # Main Streamlit application
├── src/
│   └── cortex/
│       └── agent.py      # Cortex Agent REST API client
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Cortex Agent

The app uses a pre-configured Cortex Agent with:
- **BusinessAnalyst**: Cortex Analyst for SQL queries
- **KnowledgeSearch**: Knowledge base search
- **ProductSearch**: Product catalog search
