"""Tests for ShellResource."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from homepy.resources import ShellResource


class TestShellResource:
    """Test ShellResource running shell commands."""

    def test_runs_command(self) -> None:
        r = ShellResource("echo hello")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0] == "echo hello"
            assert call_args[1].get("shell") is True

    def test_dry_run_does_not_execute(self) -> None:
        r = ShellResource("rm -rf /")
        with patch("subprocess.run") as mock_run:
            r.generate(dry_run=True)
            mock_run.assert_not_called()

    def test_dry_run_prints_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = ShellResource("echo hello")
        r.generate(dry_run=True)
        captured = capsys.readouterr()
        assert "echo hello" in captured.out

    def test_failed_command_raises(self) -> None:
        r = ShellResource("false")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            with pytest.raises(RuntimeError):
                r.generate()

    def test_stores_command(self) -> None:
        r = ShellResource("defaults write com.apple.dock autohide -bool true")
        assert r.command == "defaults write com.apple.dock autohide -bool true"

    def test_cwd_passed_to_subprocess(self) -> None:
        r = ShellResource("make build", cwd="/tmp")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            call_args = mock_run.call_args
            assert call_args[1].get("cwd") == "/tmp"

    def test_env_passed_to_subprocess(self) -> None:
        r = ShellResource("echo $FOO", env={"FOO": "bar"})
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            call_args = mock_run.call_args
            env = call_args[1].get("env")
            assert env is not None
            assert env["FOO"] == "bar"

    def test_cwd_defaults_none(self) -> None:
        r = ShellResource("echo hello")
        assert r.cwd is None

    def test_env_defaults_none(self) -> None:
        r = ShellResource("echo hello")
        assert r.env is None

    def test_dry_run_with_cwd(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = ShellResource("make build", cwd="/tmp")
        r.generate(dry_run=True)
        captured = capsys.readouterr()
        assert "make build" in captured.out
        assert "/tmp" in captured.out
