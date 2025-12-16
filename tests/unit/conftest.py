from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_settings():
    """Create a mock settings object for unit tests."""
    mock = Mock()
    mock.APP_NAME = "Demo-App Service"
    mock.APP_VERSION = "v1"
    return mock
