"""Tests for CLI argument parsing (--dry-run flag)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pyhomedot import Home
from pyhomedot.resources.base import Resource


class TestDryRunFlag:
    """Test that Home.generate() supports --dry-run from sys.argv."""

    def test_generate_parses_dry_run_flag(self) -> None:
        """When --dry-run is in sys.argv, generate runs in dry-run mode."""
        home = Home()
        r = MagicMock(spec=Resource)
        home.resources.append(r)

        with patch("sys.argv", ["main.py", "--dry-run"]):
            home.generate()

        r.generate.assert_called_once_with(dry_run=True, show_diff=False)

    def test_generate_no_dry_run_flag(self) -> None:
        """Without --dry-run in sys.argv, generate runs normally."""
        home = Home()
        r = MagicMock(spec=Resource)
        home.resources.append(r)

        with patch("sys.argv", ["main.py"]):
            home.generate()

        r.generate.assert_called_once_with(dry_run=False, show_diff=False)

    def test_explicit_dry_run_overrides_argv(self) -> None:
        """Explicit dry_run=True overrides sys.argv (no flag needed)."""
        home = Home()
        r = MagicMock(spec=Resource)
        home.resources.append(r)

        with patch("sys.argv", ["main.py"]):
            home.generate(dry_run=True)

        r.generate.assert_called_once_with(dry_run=True, show_diff=False)

    def test_explicit_dry_run_false_overrides_argv(self) -> None:
        """Explicit dry_run=False overrides --dry-run in sys.argv."""
        home = Home()
        r = MagicMock(spec=Resource)
        home.resources.append(r)

        with patch("sys.argv", ["main.py", "--dry-run"]):
            home.generate(dry_run=False)

        r.generate.assert_called_once_with(dry_run=False, show_diff=False)
