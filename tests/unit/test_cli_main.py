from unittest.mock import MagicMock, patch

import pytest
from pytest import CaptureFixture

from src.cli import main


def test_cli_help(capsys: CaptureFixture[str]) -> None:
    with patch("sys.argv", ["EmailHarvester.py"]):
        with pytest.raises(SystemExit):
            main()
    captured = capsys.readouterr()
    assert "A tool to retrieve Domain email addresses from Search Engines" in captured.out


def test_cli_list_plugins(capsys: CaptureFixture[str]) -> None:
    with patch("sys.argv", ["EmailHarvester.py", "-p"]):
        with pytest.raises(SystemExit):
            main()
    captured = capsys.readouterr()
    assert "[+] Available plugins" in captured.out


@patch("src.cli.EmailHarvester")
def test_cli_minimal_run(mock_harvester: MagicMock, capsys: CaptureFixture[str]) -> None:
    # Setup mocks
    mock_app_instance = MagicMock()
    mock_app_instance.get_plugins.return_value = {"google": {"search": MagicMock()}}
    mock_harvester.return_value = mock_app_instance

    # Mock ThreadPoolExecutor and as_completed
    mock_result = (["found@example.com"], "SUCCESS")
    mock_future = MagicMock()
    mock_future.result.return_value = mock_result

    with patch("src.cli.ThreadPoolExecutor") as mock_executor:
        mock_exec_instance = mock_executor.return_value.__enter__.return_value
        mock_exec_instance.submit.return_value = mock_future

        with patch("src.cli.as_completed") as mock_as_completed:
            mock_as_completed.return_value = [mock_future]

            with patch("sys.argv", ["EmailHarvester.py", "-d", "example.com", "-e", "google", "--noprint"]):
                main()

    captured = capsys.readouterr()
    assert "Total unique emails found: 1" in captured.out
