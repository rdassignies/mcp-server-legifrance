"""
Configuration module for the Legifrance MCP server
-------------------------------------------------
Provides structured configuration management using dataclasses.

This module centralizes all configuration parameters used by the server,
ensuring type safety and maintainability.
"""

import os
import logging
from dataclasses import dataclass, field, fields
from typing import Dict
from dotenv import load_dotenv
from tenacity import wait_fixed, stop_after_attempt


@dataclass
class APIConfig:
    """LegiFrance API connection configuration."""
    key: str
    url: str
    headers: Dict[str, str] = field(default_factory=lambda: {
        "accept": "*/*",
        "Content-Type": "application/json"
    })
    timeout: int = 30


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: int = logging.INFO
    name: str = "legifrance_mcp"


@dataclass
class EndpointConfig:
    """API endpoint mappings."""
    rechercher_dans_texte_legal: str = "loda"
    rechercher_code: str = "code"
    rechercher_jurisprudence_judiciaire: str = "juri"

    def get_endpoint(self, tool_name: str) -> str:
        """Get the endpoint for a given tool name."""
        if hasattr(self, tool_name):
            return getattr(self, tool_name)
        raise ValueError(f"Endpoint not found for tool: {tool_name}")

    def validate_tool_name(self, tool_name: str) -> bool:
        """
        Validate if a tool name is supported.

        Args:
            tool_name (str): The name of the tool to validate

        Returns:
            bool: True if the tool name is valid

        Raises:
            ValueError: If the tool name is not valid
        """
        valid_tools = [_field.name for _field in fields(self)]
        if tool_name not in valid_tools:
            raise ValueError(f"Outil inconnu: {tool_name}")
        return True


@dataclass
class RetryConfig:
    """Retry configuration for API calls."""
    wait_seconds: int = 1
    max_attempts: int = 5

    @property
    def wait(self):
        """Get the wait strategy for tenacity."""
        return wait_fixed(self.wait_seconds)

    @property
    def stop(self):
        """Get the stop strategy for tenacity."""
        return stop_after_attempt(self.max_attempts)


@dataclass
class ServerConfig:
    """Main server configuration."""
    api: APIConfig
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    endpoints: EndpointConfig = field(default_factory=EndpointConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)


def load_config() -> ServerConfig:
    """
    Load configuration from environment variables.

    Returns:
        ServerConfig: The server configuration object

    Raises:
        ValueError: If required environment variables are missing
    """
    # Load environment variables
    load_dotenv()

    # Get API configuration
    api_key = os.getenv('DASSIGNIES_API_KEY')
    api_url = os.getenv('DASSIGNIES_API_URL')

    # Validate required configuration
    if not api_key or not api_url:
        raise ValueError("Les variables d'environnement LAB_DASSIGNIES_API_KEY et LEGAL_API_URL doivent être définies")

    # Create and return the configuration
    return ServerConfig(
        api=APIConfig(
            key=api_key,
            url=api_url
        )
    )


# Initialize configuration
config = load_config()

# Configure logging
logging.basicConfig(level=config.logging.level)
logger = logging.getLogger(config.logging.name)
