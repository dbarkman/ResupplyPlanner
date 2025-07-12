import pytest
from app.config import get_config


def test_get_config_success(monkeypatch):
    """
    Tests that get_config successfully retrieves an existing environment variable.
    """
    monkeypatch.setenv("EXISTING_KEY", "test_value")
    assert get_config("EXISTING_KEY") == "test_value"


def test_get_config_failure_raises_value_error(monkeypatch):
    """
    Tests that get_config raises a ValueError for a missing environment variable.

    This test ensures the application will not run with incomplete configuration,
    adhering to the strict config policy.
    """
    # Ensure the key does not exist
    monkeypatch.delenv("MISSING_KEY", raising=False)
    with pytest.raises(ValueError) as excinfo:
        get_config("MISSING_KEY")
    assert "Error: Configuration key 'MISSING_KEY' not found" in str(excinfo.value) 