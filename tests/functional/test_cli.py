import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def script_path() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "EmailHarvester.py",
    )


def test_invalid_engine_parsing_fails_gracefully(script_path: str) -> None:
    result = subprocess.run(
        [sys.executable, script_path, "-d", "example.com", "-e", "notexist"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3
    assert "[-] Search engine plugin not found: notexist" in result.stdout


def test_comma_separated_engines_invalid_mix_fails(script_path: str) -> None:
    result = subprocess.run(
        [
            sys.executable,
            script_path,
            "-d",
            "example.com",
            "-e",
            "ask,notexist",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3
    assert "[-] Search engine plugin not found: notexist" in result.stdout


def test_run_thread_returns_tuple() -> None:
    """
    US-09/11: Verifies thread workers return the required tuple structure (emails, status).
    """
    from src.cli import run_engine_thread

    with patch("src.cli.EmailHarvester") as mock_app:
        # Setup mock search engine
        mock_plugin = {"search": MagicMock(return_value=["test@domain.com"])}
        mock_app.return_value.get_plugins.return_value = {"bing": mock_plugin}
        mock_app.return_value.status = "SUCCESS"

        mock_progress = MagicMock()

        result, status = run_engine_thread("bing", "domain.com", 1, "UA", None, False, mock_progress)

        assert result == ["test@domain.com"]
        assert status == "SUCCESS"
