# Test Configuration
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Test fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_database():
    """Mock database connection for testing."""
    return Mock()

@pytest.fixture
def mock_whatsapp_api():
    """Mock WhatsApp API for testing."""
    return Mock()

@pytest.fixture
def mock_gemini_api():
    """Mock Gemini API for testing."""
    return Mock()

@pytest.fixture
def test_client():
    """Create test client for API testing."""
    # This will be implemented when we have the main app
    pass
