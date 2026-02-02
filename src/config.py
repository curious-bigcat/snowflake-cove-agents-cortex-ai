"""
Configuration settings for the CoVe project.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SnowflakeConfig:
    """Snowflake connection configuration."""
    account: str = field(default_factory=lambda: os.getenv("SNOWFLAKE_ACCOUNT", ""))
    user: str = field(default_factory=lambda: os.getenv("SNOWFLAKE_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("SNOWFLAKE_PASSWORD", ""))
    role: str = field(default_factory=lambda: os.getenv("SNOWFLAKE_ROLE", ""))
    warehouse: str = field(default_factory=lambda: os.getenv("SNOWFLAKE_WAREHOUSE", "COVE_WH"))
    database: str = "COVE_PROJECT_DB"
    schema: str = "RAW_DATA"
    
    # Optional: Use connection name from Snowflake CLI config
    connection_name: Optional[str] = field(
        default_factory=lambda: os.getenv("SNOWFLAKE_CONNECTION_NAME", "default")
    )


@dataclass
class CortexConfig:
    """Cortex AI service configuration."""
    # Models for different CoVe stages
    baseline_model: str = "llama3.1-70b"
    verification_model: str = "mistral-large2"
    final_model: str = "claude-3-5-sonnet"
    
    # Cortex Search services
    knowledge_search_service: str = "CORTEX_SERVICES.KNOWLEDGE_SEARCH"
    product_search_service: str = "CORTEX_SERVICES.PRODUCT_SEARCH"
    
    # Cortex Agent
    verification_agent: str = "CORTEX_SERVICES.COVE_VERIFICATION_AGENT"
    
    # Semantic model path
    semantic_model_path: str = "@CORTEX_SERVICES.SEMANTIC_MODELS/cove_business_model.yaml"
    
    # Model parameters
    temperature: float = 0.0
    max_tokens: int = 4096


@dataclass
class CoVeConfig:
    """Chain of Verification workflow configuration."""
    # Maximum verification questions to generate
    max_verification_questions: int = 10
    
    # Minimum confidence threshold for consistency
    consistency_threshold: float = 0.7
    
    # Whether to use factored (independent) verification
    use_factored_verification: bool = True
    
    # Whether to use external search for verification
    use_external_search: bool = True
    
    # Logging settings
    log_to_database: bool = True
    log_schema: str = "COVE_LOGS"
    
    # Timeout settings (seconds)
    verification_timeout: int = 30
    total_timeout: int = 120


@dataclass
class Config:
    """Main configuration container."""
    snowflake: SnowflakeConfig = field(default_factory=SnowflakeConfig)
    cortex: CortexConfig = field(default_factory=CortexConfig)
    cove: CoVeConfig = field(default_factory=CoVeConfig)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            snowflake=SnowflakeConfig(),
            cortex=CortexConfig(),
            cove=CoVeConfig()
        )


# Default configuration instance
config = Config.from_env()
