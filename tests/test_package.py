"""Tests for PackageResource."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from pyhomedot.resources import PackageResource


class TestPackageResource:
    """Test PackageResource with various providers."""

    def test_invalid_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="provider"):
            PackageResource("htop", "yum")

    def test_apt_install(self) -> None:
        r = PackageResource("htop", "apt")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            mock_run.assert_called_once()
            args = mock_run.call_args
            cmd = args[0][0]
            assert "apt" in cmd[0] or "apt-get" in cmd[0] or "apt" in " ".join(cmd)
            assert "install" in cmd
            assert "htop" in cmd

    def test_apt_uninstall(self) -> None:
        r = PackageResource("htop", "apt", installed=False)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "remove" in cmd or "uninstall" in cmd

    def test_brew_install(self) -> None:
        r = PackageResource("htop", "brew")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "brew" in cmd
            assert "install" in cmd
            assert "htop" in cmd

    def test_brew_uninstall(self) -> None:
        r = PackageResource("htop", "brew", installed=False)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "brew" in cmd
            assert "uninstall" in cmd

    def test_mise_install(self) -> None:
        r = PackageResource("node", "mise")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "mise" in cmd
            assert "use" in cmd
            assert "-g" in cmd
            assert "node" in cmd

    def test_mise_uninstall(self) -> None:
        r = PackageResource("node", "mise", installed=False)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "mise" in cmd
            assert "uninstall" in cmd or "remove" in cmd

    def test_dry_run_does_not_execute(self) -> None:
        r = PackageResource("htop", "apt")
        with patch("subprocess.run") as mock_run:
            r.generate(dry_run=True)
            mock_run.assert_not_called()

    def test_dry_run_prints_action(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = PackageResource("htop", "brew")
        r.generate(dry_run=True)
        captured = capsys.readouterr()
        assert "htop" in captured.out
        assert "install" in captured.out.lower() or "brew" in captured.out.lower()

    def test_dry_run_uninstall_prints(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = PackageResource("htop", "brew", installed=False)
        r.generate(dry_run=True)
        captured = capsys.readouterr()
        assert "htop" in captured.out
        assert "uninstall" in captured.out.lower() or "remove" in captured.out.lower()

    def test_installed_defaults_true(self) -> None:
        r = PackageResource("htop", "apt")
        assert r.installed is True

    def test_version_defaults_none(self) -> None:
        r = PackageResource("htop", "apt")
        assert r.version is None

    def test_apt_install_with_version(self) -> None:
        r = PackageResource("htop", "apt", version="3.2.1")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            cmd = mock_run.call_args[0][0]
            assert "htop=3.2.1" in cmd

    def test_brew_install_with_version(self) -> None:
        r = PackageResource("node", "brew", version="20")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            cmd = mock_run.call_args[0][0]
            assert "node@20" in cmd

    def test_mise_install_with_version(self) -> None:
        r = PackageResource("node", "mise", version="20")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            cmd = mock_run.call_args[0][0]
            assert "node@20" in cmd

    def test_cask_defaults_false(self) -> None:
        r = PackageResource("htop", "brew")
        assert r.cask is False

    def test_cask_with_non_brew_raises(self) -> None:
        with pytest.raises(ValueError, match="cask"):
            PackageResource("htop", "apt", cask=True)

    def test_brew_cask_install(self) -> None:
        r = PackageResource("claude-code", "brew", cask=True)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            cmd = mock_run.call_args[0][0]
            assert cmd == ["brew", "install", "--cask", "claude-code"]

    def test_brew_cask_uninstall(self) -> None:
        r = PackageResource("claude-code", "brew", installed=False, cask=True)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            cmd = mock_run.call_args[0][0]
            assert cmd == ["brew", "uninstall", "--cask", "claude-code"]

    def test_brew_cask_install_with_version(self) -> None:
        r = PackageResource("claude-code", "brew", cask=True, version="1.0")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            cmd = mock_run.call_args[0][0]
            assert cmd == ["brew", "install", "--cask", "claude-code@1.0"]

    def test_brew_cask_dry_run(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = PackageResource("claude-code", "brew", cask=True)
        r.generate(dry_run=True)
        captured = capsys.readouterr()
        assert "--cask" in captured.out
        assert "claude-code" in captured.out

    def test_apt_sets_noninteractive_env(self) -> None:
        r = PackageResource("htop", "apt")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            env = mock_run.call_args[1]["env"]
            assert env["DEBIAN_FRONTEND"] == "noninteractive"
            assert env["NONINTERACTIVE"] == "1"

    def test_brew_sets_noninteractive_env(self) -> None:
        r = PackageResource("htop", "brew")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            env = mock_run.call_args[1]["env"]
            assert env["HOMEBREW_NO_AUTO_UPDATE"] == "1"
            assert env["NONINTERACTIVE"] == "1"

    def test_mise_sets_noninteractive_env(self) -> None:
        r = PackageResource("node", "mise")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            env = mock_run.call_args[1]["env"]
            assert env["MISE_YES"] == "1"
            assert env["NONINTERACTIVE"] == "1"

    def test_interactive_skips_noninteractive_env(self) -> None:
        r = PackageResource("htop", "apt", interactive=True)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            r.generate()
            env = mock_run.call_args[1]["env"]
            assert env is None

    def test_dry_run_with_version(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = PackageResource("node", "brew", version="20")
        r.generate(dry_run=True)
        captured = capsys.readouterr()
        assert "node@20" in captured.out or "20" in captured.out
