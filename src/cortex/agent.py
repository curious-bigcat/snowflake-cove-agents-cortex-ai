"""
Cortex Agent REST API client for interacting with Snowflake Cortex Agents.
"""

import json
import logging
import os
import requests
import toml
from dataclasses import dataclass, field
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Response from Cortex Agent."""
    request_id: str
    texts: list[str] = field(default_factory=list)
    citations: list[dict] = field(default_factory=list)
    sql_queries: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    thinking: list[str] = field(default_factory=list)
    status_messages: list[str] = field(default_factory=list)
    final_response: Optional[dict] = None
    raw_events: list[dict] = field(default_factory=list)  # Store all raw events
    
    @property
    def text(self) -> str:
        """Get combined text response."""
        return "".join(self.texts)
    
    @property
    def thinking_text(self) -> str:
        """Get combined thinking text."""
        return "".join(self.thinking)
    
    def get_tool_results(self) -> list[dict]:
        """Get results from tool calls."""
        return self.tool_results


class CortexAgentClient:
    """Client for Snowflake Cortex Agent REST API."""
    
    def __init__(
        self,
        account: Optional[str] = None,
        database: str = "COVE_PROJECT_DB",
        schema: str = "CORTEX_SERVICES",
        agent_name: str = "COVE_BUSINESS_AGENT",
        pat: Optional[str] = None,
    ):
        """
        Initialize the Cortex Agent client.
        
        Args:
            account: Snowflake account identifier
            database: Database containing the agent
            schema: Schema containing the agent
            agent_name: Name of the agent
            pat: Programmatic Access Token for authentication
        """
        self.database = database
        self.schema = schema
        self.agent_name = agent_name
        
        # Get account and credentials from config
        config = self._load_config()
        self.account = account or config.get("account", "").replace(".snowflakecomputing.com", "")
        # PAT can be in env var, passed directly, or stored as 'password' in config.toml
        self.pat = pat or os.getenv("SNOWFLAKE_PAT") or config.get("password") or config.get("pat")
        
        # Build base URL
        if "." not in self.account:
            self.base_url = f"https://{self.account}.snowflakecomputing.com"
        else:
            self.base_url = f"https://{self.account}"
    
    def _load_config(self) -> dict:
        """Load Snowflake configuration from config.toml."""
        config_path = os.path.expanduser("~/.snowflake/config.toml")
        
        if not os.path.exists(config_path):
            return {}
        
        try:
            with open(config_path, "r") as f:
                toml_config = toml.load(f)
            
            # Get default connection
            if "connections" in toml_config:
                conn = toml_config.get("connections", {}).get("default", {})
            else:
                conn = toml_config.get("default", {})
            
            return conn
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
            return {}
    
    def _get_headers(self, accept: str = "application/json") -> dict:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.pat}",
            "Content-Type": "application/json",
            "Accept": accept,
        }
    
    def _agents_url(self) -> str:
        """Get the agents API URL."""
        return f"{self.base_url}/api/v2/databases/{self.database}/schemas/{self.schema}/agents"
    
    def _iter_sse(self, response) -> Generator[tuple[str, str], None, None]:
        """Parse Server-Sent Events stream."""
        event = None
        buf = []
        
        for raw in response.iter_lines():
            if raw is None:
                continue
            
            line = raw.decode("utf-8", errors="ignore")
            
            # Skip keep-alive comments
            if line.startswith(": keep-alive"):
                continue
            
            if line.startswith("event:"):
                event = line.split("event:", 1)[1].strip()
            elif line.startswith("data:"):
                buf.append(line.split("data:", 1)[1].strip())
            elif line.strip() == "":
                if event is not None:
                    data = "\n".join(buf).strip()
                    yield event, data
                event, buf = None, []
        
        # Handle final event
        if event is not None:
            data = "\n".join(buf).strip()
            yield event, data
    
    def run(
        self,
        message: str,
        thread_id: Optional[int] = None,
        parent_message_id: int = 0,
        tool_choice: Optional[dict] = None,
        timeout: int = 300,
    ) -> AgentResponse:
        """
        Run the agent with a message.
        
        Args:
            message: User message/question
            thread_id: Optional thread ID for conversation context
            parent_message_id: Parent message ID (0 for new conversation)
            tool_choice: Optional tool choice configuration
            timeout: Request timeout in seconds
            
        Returns:
            AgentResponse with the agent's response
        """
        url = f"{self._agents_url()}/{self.agent_name}:run"
        
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": message
                        }
                    ]
                }
            ]
        }
        
        if thread_id is not None:
            body["thread_id"] = thread_id
            body["parent_message_id"] = parent_message_id
        
        if tool_choice:
            body["tool_choice"] = tool_choice
        
        logger.info(f"Sending request to agent: {message[:50]}...")
        
        try:
            with requests.post(
                url,
                headers=self._get_headers(accept="text/event-stream"),
                json=body,
                stream=True,
                timeout=timeout
            ) as response:
                response.raise_for_status()
                
                request_id = response.headers.get("X-Snowflake-Request-Id", "")
                
                result = AgentResponse(request_id=request_id)
                current_tool_use = {}
                
                for event, data_str in self._iter_sse(response):
                    # Store raw event for debugging
                    try:
                        parsed_data = json.loads(data_str) if data_str and data_str != "[DONE]" else {}
                    except json.JSONDecodeError:
                        parsed_data = {"raw": data_str}
                    
                    result.raw_events.append({
                        "event": event,
                        "data": parsed_data
                    })
                    
                    try:
                        # Handle different event types
                        if event == "response.text":
                            d = json.loads(data_str) if data_str else {}
                            if isinstance(d.get("text"), str):
                                result.texts.append(d["text"])
                        
                        elif event == "response.text.delta":
                            d = json.loads(data_str) if data_str else {}
                            if isinstance(d.get("text"), str):
                                result.texts.append(d["text"])
                        
                        elif event == "message.delta":
                            d = json.loads(data_str) if data_str else {}
                            delta = d.get("delta", {})
                            for c in delta.get("content", []):
                                if c.get("type") == "text" and isinstance(c.get("text"), str):
                                    result.texts.append(c["text"])
                        
                        elif event == "response.thinking.delta":
                            d = json.loads(data_str) if data_str else {}
                            if isinstance(d.get("text"), str):
                                result.thinking.append(d["text"])
                        
                        elif event == "response.thinking":
                            d = json.loads(data_str) if data_str else {}
                            if isinstance(d.get("text"), str):
                                # Full thinking text, don't duplicate
                                pass
                        
                        elif event == "response.status":
                            d = json.loads(data_str) if data_str else {}
                            msg = d.get("message", "")
                            status = d.get("status", "")
                            if msg:
                                result.status_messages.append(f"{status}: {msg}")
                        
                        elif event == "response.tool_use":
                            d = json.loads(data_str) if data_str else {}
                            tool_info = {
                                "name": d.get("name"),
                                "type": d.get("type"),
                                "input": d.get("input"),
                                "tool_use_id": d.get("tool_use_id"),
                                "status": "started"
                            }
                            result.tool_calls.append(tool_info)
                            current_tool_use[d.get("tool_use_id")] = tool_info
                        
                        elif event == "response.tool_result":
                            d = json.loads(data_str) if data_str else {}
                            tool_use_id = d.get("tool_use_id")
                            tool_result = {
                                "tool_use_id": tool_use_id,
                                "content": d.get("content"),
                                "is_error": d.get("is_error", False)
                            }
                            result.tool_results.append(tool_result)
                            
                            # Extract SQL from tool result - content can be a list or dict
                            content = d.get("content", [])
                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict):
                                        json_data = item.get("json", {})
                                        if isinstance(json_data, dict):
                                            sql = json_data.get("sql")
                                            if sql:
                                                result.sql_queries.append(sql)
                            elif isinstance(content, dict):
                                sql = content.get("sql")
                                if sql:
                                    result.sql_queries.append(sql)
                            
                            # Update tool call with result
                            if tool_use_id in current_tool_use:
                                current_tool_use[tool_use_id]["result"] = tool_result
                                current_tool_use[tool_use_id]["status"] = "completed"
                        
                        elif event == "response.tool_result.status":
                            d = json.loads(data_str) if data_str else {}
                            msg = d.get("message", "")
                            status = d.get("status", "")
                            tool_type = d.get("tool_type", "")
                            if msg:
                                result.status_messages.append(f"Tool {tool_type} - {status}: {msg}")
                        
                        elif event == "citation":
                            d = json.loads(data_str) if data_str else {}
                            result.citations.append(d)
                        
                        elif event == "response":
                            d = json.loads(data_str) if data_str else {}
                            result.final_response = d
                            # Extract final text from response if not already captured
                            if not result.texts and "message" in d:
                                msg = d.get("message", {})
                                for c in msg.get("content", []):
                                    if c.get("type") == "text":
                                        result.texts.append(c.get("text", ""))
                        
                        elif event == "error":
                            d = json.loads(data_str) if data_str else {}
                            error_msg = d.get("message", "Unknown error")
                            raise RuntimeError(f"Agent error: {error_msg}")
                        
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse event data: {data_str[:100]}")
                    except RuntimeError:
                        raise
                    except Exception as e:
                        logger.warning(f"Error processing event {event}: {e}")
                
                return result
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error calling agent: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling agent: {e}")
            raise
    
    def create_thread(self, origin_application: str = "cove_demo") -> int:
        """
        Create a new conversation thread.
        
        Args:
            origin_application: Application identifier
            
        Returns:
            Thread ID
        """
        url = f"{self.base_url}/api/v2/cortex/threads"
        
        response = requests.post(
            url,
            headers=self._get_headers(),
            json={"origin_application": origin_application},
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("thread_id")
    
    def describe_agent(self) -> dict:
        """Get agent configuration details."""
        url = f"{self._agents_url()}/{self.agent_name}"
        
        response = requests.get(
            url,
            headers=self._get_headers(),
            timeout=30
        )
        response.raise_for_status()
        
        return response.json()


def run_agent(
    message: str,
    agent_name: str = "COVE_BUSINESS_AGENT",
    database: str = "COVE_PROJECT_DB",
    schema: str = "CORTEX_SERVICES",
) -> AgentResponse:
    """
    Convenience function to run an agent query.
    
    Args:
        message: User question
        agent_name: Name of the agent
        database: Database containing agent
        schema: Schema containing agent
        
    Returns:
        AgentResponse
    """
    client = CortexAgentClient(
        database=database,
        schema=schema,
        agent_name=agent_name,
    )
    return client.run(message)
