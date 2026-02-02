"""
Snowflake client for database connections and query execution.
Uses snowflake-connector-python for compatibility.
"""

import logging
import os
import toml
from contextlib import contextmanager
from typing import Any, Generator, Optional

import snowflake.connector
from snowflake.connector import DictCursor

from .config import Config, config as default_config

logger = logging.getLogger(__name__)


class SnowflakeClient:
    """Client for Snowflake database operations."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the Snowflake client.
        
        Args:
            config: Configuration object. Uses default if not provided.
        """
        self.config = config or default_config
        self._connection: Optional[snowflake.connector.SnowflakeConnection] = None
    
    def _get_connection_from_toml(self) -> dict:
        """Get connection parameters from Snowflake CLI config."""
        config_path = os.path.expanduser("~/.snowflake/config.toml")
        
        if not os.path.exists(config_path):
            return {}
        
        try:
            with open(config_path, "r") as f:
                toml_config = toml.load(f)
            
            connection_name = self.config.snowflake.connection_name or "default"
            
            # Handle both 'connections.default' and 'default' formats
            if "connections" in toml_config:
                conn_config = toml_config.get("connections", {}).get(connection_name, {})
            else:
                conn_config = toml_config.get(connection_name, {})
            
            return conn_config
        except Exception as e:
            logger.warning(f"Failed to read config.toml: {e}")
            return {}
    
    def _create_connection(self) -> snowflake.connector.SnowflakeConnection:
        """Create a new Snowflake connection."""
        sf_config = self.config.snowflake
        
        # Try to get connection params from CLI config first
        conn_params = self._get_connection_from_toml()
        
        # Override with explicit config if provided
        if sf_config.account:
            conn_params["account"] = sf_config.account
        if sf_config.user:
            conn_params["user"] = sf_config.user
        if sf_config.password:
            conn_params["password"] = sf_config.password
        if sf_config.role:
            conn_params["role"] = sf_config.role
        if sf_config.warehouse:
            conn_params["warehouse"] = sf_config.warehouse
        if sf_config.database:
            conn_params["database"] = sf_config.database
        if sf_config.schema:
            conn_params["schema"] = sf_config.schema
        
        # Handle authenticator
        if "authenticator" not in conn_params:
            # Check for environment variable
            auth = os.getenv("SNOWFLAKE_AUTHENTICATOR")
            if auth:
                conn_params["authenticator"] = auth
        
        # Filter out None/empty values
        conn_params = {k: v for k, v in conn_params.items() if v}
        
        logger.info(f"Connecting to Snowflake account: {conn_params.get('account', 'unknown')}")
        
        connection = snowflake.connector.connect(**conn_params)
        logger.info("Connected to Snowflake successfully")
        
        # Set default warehouse and database
        cursor = connection.cursor()
        try:
            cursor.execute("USE WAREHOUSE COMPUTE_WH")
            cursor.execute("USE DATABASE COVE_PROJECT_DB")
        except Exception as e:
            logger.warning(f"Failed to set default context: {e}")
        finally:
            cursor.close()
        
        return connection
    
    @property
    def connection(self) -> snowflake.connector.SnowflakeConnection:
        """Get or create the Snowflake connection."""
        if self._connection is None or self._connection.is_closed():
            self._connection = self._create_connection()
        return self._connection
    
    def close(self) -> None:
        """Close the Snowflake connection."""
        if self._connection is not None and not self._connection.is_closed():
            self._connection.close()
            self._connection = None
            logger.info("Snowflake connection closed")
    
    @contextmanager
    def get_cursor(self) -> Generator[DictCursor, None, None]:
        """Context manager for cursor."""
        cursor = self.connection.cursor(DictCursor)
        try:
            yield cursor
        finally:
            cursor.close()
    
    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        """
        Execute a SQL query and return results as a list of dicts.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            List of dictionaries representing rows
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql)
                results = cursor.fetchall()
                return list(results) if results else []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_query_scalar(self, sql: str) -> Any:
        """
        Execute a query and return a single scalar value.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Single value from the first column of the first row
        """
        results = self.execute_query(sql)
        if results and len(results) > 0:
            first_row = results[0]
            if first_row:
                return list(first_row.values())[0]
        return None
    
    def execute_ddl(self, sql: str) -> None:
        """
        Execute a DDL statement (CREATE, ALTER, DROP, etc.).
        
        Args:
            sql: DDL statement to execute
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql)
            logger.info("DDL executed successfully")
        except Exception as e:
            logger.error(f"DDL execution failed: {e}")
            raise


# Global client instance
_client: Optional[SnowflakeClient] = None


def get_client(config: Optional[Config] = None) -> SnowflakeClient:
    """Get or create the global Snowflake client."""
    global _client
    if _client is None:
        _client = SnowflakeClient(config)
    return _client


def close_client() -> None:
    """Close the global Snowflake client."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
