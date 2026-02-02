"""
Streamlit app for Chain of Verification (CoVe) with Cortex Agents.

Shows the full CoVe workflow with streaming results:
1. Initial Agent Response
2. Verification of each claim (streamed as they complete)
3. Comparison and final result
"""

import streamlit as st
import sys
import os
import json
import toml
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cortex.agent import CortexAgentClient, AgentResponse
from dataclasses import dataclass, field
from typing import Optional, Any


def get_pat_from_config() -> str:
    """Get PAT from config.toml or environment variable."""
    pat = os.getenv("SNOWFLAKE_PAT")
    if pat:
        return pat
    
    config_path = os.path.expanduser("~/.snowflake/config.toml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                toml_config = toml.load(f)
            conn = toml_config.get("connections", {}).get("default", {})
            return conn.get("password", "")
        except Exception:
            pass
    return ""


st.set_page_config(
    page_title="CoVe - Chain of Verification",
    page_icon="🔍",
    layout="wide"
)

st.markdown("""
<style>
    .step-header {
        background: linear-gradient(90deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 20px 0 10px 0;
    }
    .consistent { background-color: #1b4332; border-left: 4px solid #40916c; padding: 10px; margin: 5px 0; }
    .inconsistent { background-color: #3d1e1e; border-left: 4px solid #d62828; padding: 10px; margin: 5px 0; }
    .unverified { background-color: #3d3d1e; border-left: 4px solid #f4a261; padding: 10px; margin: 5px 0; }
    .claim-box { border: 1px solid #444; border-radius: 8px; padding: 15px; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if "cove_running" not in st.session_state:
        st.session_state.cove_running = False
    if "selected_query" not in st.session_state:
        st.session_state.selected_query = ""


@dataclass
class ClaimVerification:
    """Verification result for a single claim."""
    claim: str
    verification_question: str
    source: str
    verification_response: AgentResponse
    comparison_response: AgentResponse
    is_consistent: Optional[bool] = None
    explanation: str = ""


def display_agent_response(response: AgentResponse, title: str, container=None):
    """Display an agent response with all details."""
    target = container if container else st
    
    target.markdown(f"**{title}**")
    
    # Main text
    target.info(response.text if response.text else "No text response")
    
    # Tool calls
    if response.tool_calls:
        with target.expander(f"🔧 Tool Calls ({len(response.tool_calls)})", expanded=False):
            for tc in response.tool_calls:
                st.markdown(f"**Tool:** `{tc.get('name')}` ({tc.get('type')})")
                if tc.get('input'):
                    st.json(tc.get('input'))
    
    # SQL Queries
    if response.sql_queries:
        with target.expander(f"📝 SQL Queries ({len(response.sql_queries)})", expanded=True):
            for sql in response.sql_queries:
                st.code(sql, language="sql")
    
    # Tool Results
    if response.tool_results:
        with target.expander(f"📊 Tool Results ({len(response.tool_results)})", expanded=False):
            for tr in response.tool_results:
                content = tr.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "json" in item:
                            json_data = item["json"]
                            if "result_set" in json_data:
                                result_set = json_data["result_set"]
                                if "data" in result_set and "resultSetMetaData" in result_set:
                                    meta = result_set["resultSetMetaData"]
                                    columns = [col["name"] for col in meta.get("rowType", [])]
                                    data = result_set.get("data", [])
                                    if columns and data:
                                        import pandas as pd
                                        df = pd.DataFrame(data, columns=columns)
                                        st.dataframe(df, use_container_width=True)
                            # Show search results
                            if "results" in json_data:
                                st.json(json_data["results"][:3] if len(json_data.get("results", [])) > 3 else json_data["results"])
    
    # Thinking
    if response.thinking_text:
        with target.expander("🧠 Agent Thinking", expanded=False):
            st.text(response.thinking_text)


def extract_claims(client: CortexAgentClient, query: str, response_text: str) -> tuple[list[dict], AgentResponse]:
    """Extract claims from the response."""
    extraction_prompt = f"""Analyze this response and list all specific factual claims that can be verified.

Original Question: {query}

Response to Analyze:
{response_text}

For each claim, provide:
1. The exact claim made
2. A verification question to check it
3. Whether to use "analyst" (for data/numbers) or "search" (for policies/knowledge/products)

List each claim in this format:
CLAIM: [the claim]
QUESTION: [verification question]
SOURCE: [analyst or search]
---"""

    extract_response = client.run(extraction_prompt)
    
    # Parse claims
    claims = []
    current_claim = {}
    
    for line in extract_response.text.split('\n'):
        line = line.strip()
        if line.startswith('CLAIM:'):
            if current_claim.get('claim'):
                claims.append(current_claim)
            current_claim = {'claim': line[6:].strip()}
        elif line.startswith('QUESTION:'):
            current_claim['verification_question'] = line[9:].strip()
        elif line.startswith('SOURCE:'):
            source = line[7:].strip().lower()
            current_claim['source'] = 'analyst' if 'analyst' in source else 'search'
        elif line == '---' and current_claim.get('claim'):
            claims.append(current_claim)
            current_claim = {}
    
    if current_claim.get('claim'):
        claims.append(current_claim)
    
    # Ensure all claims have required fields
    for claim in claims:
        if 'verification_question' not in claim:
            claim['verification_question'] = f"Verify: {claim['claim']}"
        if 'source' not in claim:
            claim['source'] = 'analyst'
    
    return claims, extract_response


def verify_claim(client: CortexAgentClient, claim: dict) -> ClaimVerification:
    """Verify a single claim independently."""
    question = claim.get('verification_question', '')
    
    # Query agent independently (factored verification)
    verification_response = client.run(question)
    
    # Compare original claim with verification
    comparison_prompt = f"""Compare these two statements and determine if they are consistent.

ORIGINAL CLAIM:
{claim.get('claim', '')}

VERIFIED INFORMATION:
{verification_response.text}

Respond with exactly one of these first, then explain:
- CONSISTENT: if the claim matches the verified information
- INCONSISTENT: if the claim contradicts the verified information  
- UNVERIFIED: if you cannot determine from the information

Your response:"""

    comparison_response = client.run(comparison_prompt)
    
    # Parse consistency
    response_upper = comparison_response.text.upper()
    is_consistent = None
    if 'CONSISTENT' in response_upper and 'INCONSISTENT' not in response_upper:
        is_consistent = True
    elif 'INCONSISTENT' in response_upper:
        is_consistent = False
    
    return ClaimVerification(
        claim=claim.get('claim', ''),
        verification_question=question,
        source=claim.get('source', 'analyst'),
        verification_response=verification_response,
        comparison_response=comparison_response,
        is_consistent=is_consistent,
        explanation=comparison_response.text
    )


def display_verification_result(v: ClaimVerification, index: int, container):
    """Display a single verification result."""
    if v.is_consistent is True:
        status_icon = "✅"
        status_text = "CONSISTENT"
    elif v.is_consistent is False:
        status_icon = "❌"
        status_text = "INCONSISTENT"
    else:
        status_icon = "⚠️"
        status_text = "UNVERIFIED"
    
    with container.expander(f"{status_icon} Claim {index}: {v.claim[:60]}... [{status_text}]", expanded=v.is_consistent is False):
        st.markdown(f"**Original Claim:** {v.claim}")
        st.markdown(f"**Verification Question:** {v.verification_question}")
        st.markdown(f"**Source:** `{v.source.upper()}`")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔎 Verification Query")
            display_agent_response(v.verification_response, "Independent Verification Result:")
        
        with col2:
            st.markdown("### ⚖️ Comparison")
            st.markdown("**Comparison Analysis:**")
            
            if v.is_consistent is True:
                st.success(v.explanation)
            elif v.is_consistent is False:
                st.error(v.explanation)
            else:
                st.warning(v.explanation)


def main():
    init_session_state()
    
    st.title("🔍 Chain of Verification (CoVe)")
    st.markdown("**Verify Cortex Agent responses using Cortex Analyst, Knowledge Search, and Product Search**")
    
    # Check PAT
    pat = get_pat_from_config()
    if not pat:
        st.error("No PAT found. Configure in ~/.snowflake/config.toml or set SNOWFLAKE_PAT env var.")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("📝 Sample Questions")
        
        sample_questions = [
            "What was total revenue in Q4 2024?",
            "What is our return policy for electronics?",
            "Tell me about the SmartWatch Pro product",
            "Which customer segment had highest revenue?",
            "What was Enterprise revenue in Q4 2024 and what products do we have?",
        ]
        
        for q in sample_questions:
            if st.button(q[:40] + "..." if len(q) > 40 else q, key=f"sample_{hash(q)}", use_container_width=True):
                st.session_state.selected_query = q
                st.rerun()
    
    # Main query area
    query = st.text_input(
        "Enter your question:",
        value=st.session_state.selected_query,
        placeholder="e.g., What was total revenue in Q4 2024?"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        run_button = st.button("🚀 Run CoVe Verification", type="primary", use_container_width=True)
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.selected_query = ""
            st.rerun()
    
    # Run CoVe with streaming output
    if run_button and query:
        start_time = time.time()
        client = CortexAgentClient()
        
        # ========== STEP 1: Initial Agent Response ==========
        st.markdown('<div class="step-header"><h2>📤 STEP 1: Initial Agent Response</h2></div>', unsafe_allow_html=True)
        
        step1_status = st.empty()
        step1_status.info("⏳ Querying Cortex Agent...")
        
        initial_response = client.run(query)
        
        step1_status.success("✅ Initial response received!")
        
        st.markdown(f"**Query:** {query}")
        display_agent_response(initial_response, "Agent Response:")
        
        # Extract claims
        st.markdown("---")
        claims_status = st.empty()
        claims_status.info("⏳ Extracting claims from response...")
        
        claims, extraction_response = extract_claims(client, query, initial_response.text)
        
        claims_status.success(f"✅ Extracted {len(claims)} claims for verification")
        
        st.markdown("**Extracted Claims:**")
        for i, claim in enumerate(claims, 1):
            st.markdown(f"{i}. **{claim.get('claim', '')}** (Source: `{claim.get('source', 'unknown')}`)")
        
        # ========== STEP 2: Verification Results (Streaming) ==========
        st.markdown('<div class="step-header"><h2>🔍 STEP 2: Independent Verification (Streaming)</h2></div>', unsafe_allow_html=True)
        
        # Create container for streaming results
        verification_container = st.container()
        
        # Track results
        verifications = []
        consistent_count = 0
        inconsistent_count = 0
        unverified_count = 0
        
        # Progress tracking
        progress_bar = st.progress(0)
        progress_text = st.empty()
        
        # Verify each claim and display immediately
        for i, claim in enumerate(claims, 1):
            progress_text.info(f"⏳ Verifying claim {i}/{len(claims)}: {claim.get('claim', '')[:50]}...")
            
            # Verify this claim
            verification = verify_claim(client, claim)
            verifications.append(verification)
            
            # Update counts
            if verification.is_consistent is True:
                consistent_count += 1
            elif verification.is_consistent is False:
                inconsistent_count += 1
            else:
                unverified_count += 1
            
            # Display immediately in the container
            display_verification_result(verification, i, verification_container)
            
            # Update progress
            progress_bar.progress(i / len(claims))
        
        progress_text.success(f"✅ All {len(claims)} claims verified!")
        progress_bar.empty()
        
        # ========== STEP 3: Comparison & Final Result ==========
        st.markdown('<div class="step-header"><h2>📊 STEP 3: Comparison & Final Result</h2></div>', unsafe_allow_html=True)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Claims", len(verifications))
        col2.metric("✅ Consistent", consistent_count)
        col3.metric("❌ Inconsistent", inconsistent_count)
        col4.metric("⚠️ Unverified", unverified_count)
        
        # Comparison table
        st.markdown("### Verification Summary Table")
        import pandas as pd
        comparison_data = []
        for i, v in enumerate(verifications, 1):
            status = "✅ Consistent" if v.is_consistent else ("❌ Inconsistent" if v.is_consistent is False else "⚠️ Unverified")
            comparison_data.append({
                "#": i,
                "Claim": v.claim[:50] + "..." if len(v.claim) > 50 else v.claim,
                "Source": v.source.upper(),
                "Status": status,
                "Verified Value": v.verification_response.text[:100] + "..." if len(v.verification_response.text) > 100 else v.verification_response.text
            })
        
        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
        
        # Generate corrected response if needed
        final_response = None
        if inconsistent_count > 0:
            st.markdown("### 🔄 Generating Corrected Response...")
            
            correction_parts = []
            for v in verifications:
                status = "CONSISTENT" if v.is_consistent else ("INCONSISTENT" if v.is_consistent is False else "UNVERIFIED")
                correction_parts.append(f"- Claim: {v.claim}\n  Status: {status}")
                if v.is_consistent is False:
                    correction_parts.append(f"  Correct Info: {v.verification_response.text[:200]}")
            
            correction_prompt = f"""Generate a corrected response based on verification results.

ORIGINAL QUESTION: {query}

ORIGINAL RESPONSE: {initial_response.text}

VERIFICATION RESULTS:
{chr(10).join(correction_parts)}

Generate a revised response that corrects any INCONSISTENT claims using the verified information.

Corrected Response:"""
            
            final_response = client.run(correction_prompt)
        
        # Side by side comparison
        st.markdown("### Response Comparison")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Original Agent Response:**")
            st.info(initial_response.text)
        
        with col2:
            st.markdown("**Final Verified Response:**")
            if final_response:
                st.success(final_response.text)
                display_agent_response(final_response, "Correction Details:")
            elif inconsistent_count == 0:
                st.success(initial_response.text + "\n\n✅ *All claims verified - no corrections needed*")
            else:
                st.warning("No corrected response generated")
        
        # Execution time
        execution_time = time.time() - start_time
        st.sidebar.metric("⏱️ Total Time", f"{execution_time:.1f}s")
        st.sidebar.metric("📊 Verification Score", f"{consistent_count}/{len(verifications)}")
        
        # Export
        st.divider()
        export_data = {
            "query": query,
            "initial_response": initial_response.text,
            "initial_response_sql": initial_response.sql_queries,
            "claims": claims,
            "verifications": [
                {
                    "claim": v.claim,
                    "verification_question": v.verification_question,
                    "source": v.source,
                    "verification_response": v.verification_response.text,
                    "verification_sql": v.verification_response.sql_queries,
                    "is_consistent": v.is_consistent,
                    "explanation": v.explanation,
                }
                for v in verifications
            ],
            "final_response": final_response.text if final_response else None,
            "summary": {
                "consistent": consistent_count,
                "inconsistent": inconsistent_count,
                "unverified": unverified_count,
                "execution_time": execution_time
            }
        }
        
        st.download_button(
            "📥 Export Full CoVe Results (JSON)",
            data=json.dumps(export_data, indent=2, default=str),
            file_name="cove_full_results.json",
            mime="application/json"
        )


if __name__ == "__main__":
    main()
