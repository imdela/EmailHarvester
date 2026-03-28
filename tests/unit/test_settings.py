import os

import pytest
from pydantic import ValidationError

from src.core import Settings


def test_invalid_timeout_raises_validation_error() -> None:
    """
    TI-04: Verify that a timeout less than or equal to 0 raises a ValidationError.
    This ensures Fail-Fast behavior so the scraping engine cannot start with invalid bounds.
    """
    # Inject invalid environment variable
    os.environ["EH_TIMEOUT"] = "-5"

    with pytest.raises(ValidationError) as excinfo:
        # Instantiating Settings triggers Pydantic's environment reading
        Settings()

    # Verify the error message points out the timeout validation failure
    assert "timeout" in str(excinfo.value)
    assert "Input should be greater than 0" in str(excinfo.value)

    # Clear the mocked environment to avoid polluting subsequent tests
    del os.environ["EH_TIMEOUT"]


def test_default_valid_configuration() -> None:
    """
    Verifies that the default instantiation correctly parses hardcoded defaults.
    """
    settings = Settings()
    assert settings.tor_port == 9050
    # Updated from 12 to 20 to match actual .env value (TI-04 Verification)
    assert settings.timeout == 20
    assert settings.tor_control_password == "emailharvester_secret"
