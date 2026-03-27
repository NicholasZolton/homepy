"""Integration tests exercising the full Home workflow."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pyhomedot import Home
from pyhomedot.resources import (
    SymlinkResource,
    PackageResource,
    TemplateResource,
    ShellResource,
)


class TestFullWorkflow:
    """End-to-end tests combining multiple resource types."""

    def test_generate_multiple_resource_types(self, tmp_path: Path) -> None:
        """Home.generate() processes symlinks, templates, and packages together."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        # Create source files
        (source_dir / "bashrc").write_text("# bashrc")
        (source_dir / "gitconfig.tmpl").write_text("[user]\n    name = {{ username }}")

        home = Home()
        home.add(
            SymlinkResource("bashrc", ".bashrc", source_root=source_dir, home_dir=home_dir),
            TemplateResource(
                "gitconfig.tmpl",
                ".gitconfig",
                variables={"username": "TestUser"},
                source_root=source_dir,
                home_dir=home_dir,
            ),
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            home.add(PackageResource("git", "apt"))
            home.generate()

        # Verify symlink
        bashrc = home_dir / ".bashrc"
        assert bashrc.is_symlink()
        assert bashrc.read_text() == "# bashrc"

        # Verify template
        gitconfig = home_dir / ".gitconfig"
        assert gitconfig.exists()
        assert "TestUser" in gitconfig.read_text()
        assert "{{ username }}" not in gitconfig.read_text()

        # Verify package install was called
        mock_run.assert_called_once()

    def test_dry_run_full_workflow(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Dry run across all resource types prints but doesn't change anything."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        (source_dir / "file.txt").write_text("content")
        (source_dir / "tmpl.txt").write_text("val = {{ x }}")

        home = Home()
        home.add(
            SymlinkResource("file.txt", "file.txt", source_root=source_dir, home_dir=home_dir),
            TemplateResource("tmpl.txt", "out.txt", variables={"x": "1"}, source_root=source_dir, home_dir=home_dir),
            PackageResource("curl", "apt"),
            ShellResource("echo test"),
        )

        with patch("subprocess.run") as mock_run:
            home.generate(dry_run=True)
            mock_run.assert_not_called()

        # Nothing should be created
        assert not (home_dir / "file.txt").exists()
        assert not (home_dir / "out.txt").exists()

        captured = capsys.readouterr()
        assert "dry-run" in captured.out.lower()

    def test_chaining_add(self, tmp_path: Path) -> None:
        """Home.add() supports chaining."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        (source_dir / "a.txt").write_text("a")
        (source_dir / "b.txt").write_text("b")

        home = Home()
        home.add(
            SymlinkResource("a.txt", "a.txt", source_root=source_dir, home_dir=home_dir),
        ).add(
            SymlinkResource("b.txt", "b.txt", source_root=source_dir, home_dir=home_dir),
        )

        home.generate()

        assert (home_dir / "a.txt").is_symlink()
        assert (home_dir / "b.txt").is_symlink()

    def test_dry_run_flag_from_argv(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """--dry-run flag from sys.argv works end-to-end."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        (source_dir / "file.txt").write_text("content")

        home = Home()
        home.add(
            SymlinkResource("file.txt", "file.txt", source_root=source_dir, home_dir=home_dir),
        )

        with patch("sys.argv", ["main.py", "--dry-run"]):
            home.generate()

        assert not (home_dir / "file.txt").exists()
        captured = capsys.readouterr()
        assert "dry-run" in captured.out.lower()

    def test_package_with_version(self) -> None:
        """PackageResource with version works in full workflow."""
        home = Home()
        home.add(
            PackageResource("node", "mise", version="20"),
            PackageResource("python", "brew", version="3.12"),
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            home.generate()

            calls = mock_run.call_args_list
            assert len(calls) == 2
            assert "node@20" in calls[0][0][0]
            assert "python@3.12" in calls[1][0][0]

    def test_shell_resource_in_workflow(self) -> None:
        """ShellResource integrates with Home.generate()."""
        home = Home()
        home.add(ShellResource("echo hello", cwd="/tmp"))

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            home.generate()
            mock_run.assert_called_once()
            assert mock_run.call_args[1]["cwd"] == "/tmp"

    def test_template_with_jinja_syntax_in_workflow(self, tmp_path: Path) -> None:
        """Jinja2-style templates work end-to-end."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        (source_dir / "config.tmpl").write_text("host = {{ hostname }}\nport = {{ port }}")

        home = Home()
        home.add(
            TemplateResource(
                "config.tmpl",
                ".config/app/config",
                variables={"hostname": "prod.example.com", "port": "8080"},
                source_root=source_dir,
                home_dir=home_dir,
            ),
        )
        home.generate()

        target = home_dir / ".config" / "app" / "config"
        content = target.read_text()
        assert "prod.example.com" in content
        assert "8080" in content
        assert "{{ hostname }}" not in content
        assert "{{ port }}" not in content
