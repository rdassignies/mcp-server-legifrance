import pytest
import logging
import os
from tenacity import wait_fixed, stop_after_attempt

# Set environment variables for testing
os.environ["DASSIGNIES_API_KEY"] = "test_key"
os.environ["DASSIGNIES_API_URL"] = "http://test.url"

from src.config import (
    APIConfig,
    LoggingConfig,
    EndpointConfig,
    RetryConfig,
    ServerConfig,
    load_config,
)


def test_api_config_init():
    """Test APIConfig initialization with required parameters."""
    config = APIConfig(key="test_key", url="http://test.url")
    assert config.key == "test_key"
    assert config.url == "http://test.url"
    assert config.headers == {"accept": "*/*", "Content-Type": "application/json"}
    assert config.timeout == 30


def test_logging_config_init():
    """Test LoggingConfig initialization with default parameters."""
    config = LoggingConfig()
    assert config.level == logging.INFO
    assert config.name == "legifrance_mcp"


def test_endpoint_config_init():
    """Test EndpointConfig initialization with default parameters."""
    config = EndpointConfig()
    assert config.rechercher_dans_texte_legal == "loda"
    assert config.rechercher_code == "code"
    assert config.rechercher_jurisprudence_judiciaire == "juri"


def test_endpoint_config_get_endpoint_valid():
    """Test get_endpoint with valid tool name."""
    config = EndpointConfig()
    assert config.get_endpoint("rechercher_dans_texte_legal") == "loda"
    assert config.get_endpoint("rechercher_code") == "code"
    assert config.get_endpoint("rechercher_jurisprudence_judiciaire") == "juri"


def test_endpoint_config_get_endpoint_invalid():
    """Test get_endpoint with invalid tool name."""
    config = EndpointConfig()
    with pytest.raises(ValueError, match="Endpoint not found for tool: invalid_tool"):
        config.get_endpoint("invalid_tool")


def test_endpoint_config_validate_tool_name_valid():
    """Test validate_tool_name with valid tool name."""
    config = EndpointConfig()
    assert config.validate_tool_name("rechercher_dans_texte_legal") is True
    assert config.validate_tool_name("rechercher_code") is True
    assert config.validate_tool_name("rechercher_jurisprudence_judiciaire") is True


def test_endpoint_config_validate_tool_name_invalid():
    """Test validate_tool_name with invalid tool name."""
    config = EndpointConfig()
    with pytest.raises(ValueError, match="Outil inconnu: invalid_tool"):
        config.validate_tool_name("invalid_tool")


def test_retry_config_init():
    """Test RetryConfig initialization with default parameters."""
    config = RetryConfig()
    assert config.wait_seconds == 1
    assert config.max_attempts == 5


def test_retry_config_wait_property():
    """Test wait property returns wait_fixed with correct value."""
    config = RetryConfig(wait_seconds=2)
    wait_strategy = config.wait
    # Check that wait_strategy is an instance of wait_fixed
    assert isinstance(wait_strategy, type(wait_fixed(2)))


def test_retry_config_stop_property():
    """Test stop property returns stop_after_attempt with correct value."""
    config = RetryConfig(max_attempts=3)
    stop_strategy = config.stop
    # Check that stop_strategy is an instance of stop_after_attempt
    assert isinstance(stop_strategy, type(stop_after_attempt(3)))


def test_server_config_init():
    """Test ServerConfig initialization with required parameters."""
    api_config = APIConfig(key="test_key", url="http://test.url")
    config = ServerConfig(api=api_config)
    assert config.api == api_config
    assert isinstance(config.logging, LoggingConfig)
    assert isinstance(config.endpoints, EndpointConfig)
    assert isinstance(config.retry, RetryConfig)


def test_load_config_success(monkeypatch):
    """Test load_config with valid environment variables."""
    # Mock environment variables
    monkeypatch.setenv("DASSIGNIES_API_KEY", "test_key")
    monkeypatch.setenv("DASSIGNIES_API_URL", "http://test.url")

    # Call the function
    config = load_config()

    # Verify the result
    assert isinstance(config, ServerConfig)
    assert config.api.key == "test_key"
    assert config.api.url == "http://test.url"


def test_load_config_missing_env_vars(monkeypatch):
    """Test load_config with missing environment variables."""
    # Clear environment variables
    monkeypatch.delenv("DASSIGNIES_API_KEY", raising=False)
    monkeypatch.delenv("DASSIGNIES_API_URL", raising=False)

    # Verify that ValueError is raised
    with pytest.raises(ValueError, match="Les variables d'environnement LAB_DASSIGNIES_API_KEY et LEGAL_API_URL doivent être définies"):
        load_config()