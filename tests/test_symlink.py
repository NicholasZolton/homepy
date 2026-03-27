"""Tests for SymlinkResource."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from homepy.resources import SymlinkResource


class TestSymlinkResource:
    """Test SymlinkResource creation and collision handling."""

    def test_creates_symlink(self, tmp_path: Path) -> None:
        """Creates a symlink from source to target relative to home."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        source_file = source_dir / "hello.txt"
        source_file.write_text("hello")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        r = SymlinkResource("hello.txt", "hello.txt", source_root=source_dir, home_dir=home_dir)
        r.generate()

        target = home_dir / "hello.txt"
        assert target.is_symlink()
        assert target.resolve() == source_file.resolve()

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Creates parent directories for the target if they don't exist."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        source_file = source_dir / "config.txt"
        source_file.write_text("config")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        r = SymlinkResource("config.txt", ".config/app/config.txt", source_root=source_dir, home_dir=home_dir)
        r.generate()

        target = home_dir / ".config" / "app" / "config.txt"
        assert target.is_symlink()

    def test_symlink_directory(self, tmp_path: Path) -> None:
        """Can symlink a directory."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        git_dir = source_dir / "git"
        git_dir.mkdir()
        (git_dir / "config").write_text("gitconfig")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        r = SymlinkResource("git/", ".config/git/", source_root=source_dir, home_dir=home_dir)
        r.generate()

        target = home_dir / ".config" / "git"
        assert target.is_symlink()

    def test_skip_if_already_correct_symlink(self, tmp_path: Path) -> None:
        """Skips if target is already a symlink to the correct source."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        source_file = source_dir / "hello.txt"
        source_file.write_text("hello")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        target = home_dir / "hello.txt"
        target.symlink_to(source_file)

        r = SymlinkResource("hello.txt", "hello.txt", source_root=source_dir, home_dir=home_dir)
        r.generate()  # should not raise, should skip

        assert target.is_symlink()
        assert target.resolve() == source_file.resolve()

    def test_warns_on_different_symlink(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Warns and leaves unchanged if target points to different source."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        source_file = source_dir / "hello.txt"
        source_file.write_text("hello")

        other_file = tmp_path / "other.txt"
        other_file.write_text("other")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        target = home_dir / "hello.txt"
        target.symlink_to(other_file)

        r = SymlinkResource("hello.txt", "hello.txt", source_root=source_dir, home_dir=home_dir)
        r.generate()

        captured = capsys.readouterr()
        assert "warning" in captured.out.lower() or "Warning" in captured.out
        # symlink should still point to the old target
        assert os.readlink(str(target)) == str(other_file)

    def test_force_replaces_different_symlink(self, tmp_path: Path) -> None:
        """With force=True, replaces symlink pointing to different source."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        source_file = source_dir / "hello.txt"
        source_file.write_text("hello")

        other_file = tmp_path / "other.txt"
        other_file.write_text("other")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        target = home_dir / "hello.txt"
        target.symlink_to(other_file)

        r = SymlinkResource("hello.txt", "hello.txt", source_root=source_dir, home_dir=home_dir, force=True)
        r.generate()

        assert target.is_symlink()
        assert target.resolve() == source_file.resolve()

    def test_warns_on_regular_file(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Warns and leaves unchanged if target is a regular file."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        source_file = source_dir / "hello.txt"
        source_file.write_text("hello")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        target = home_dir / "hello.txt"
        target.write_text("existing content")

        r = SymlinkResource("hello.txt", "hello.txt", source_root=source_dir, home_dir=home_dir)
        r.generate()

        captured = capsys.readouterr()
        assert "warning" in captured.out.lower() or "Warning" in captured.out
        assert not target.is_symlink()
        assert target.read_text() == "existing content"

    def test_force_replaces_regular_file(self, tmp_path: Path) -> None:
        """With force=True, removes regular file and creates symlink."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        source_file = source_dir / "hello.txt"
        source_file.write_text("hello")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        target = home_dir / "hello.txt"
        target.write_text("existing content")

        r = SymlinkResource("hello.txt", "hello.txt", source_root=source_dir, home_dir=home_dir, force=True)
        r.generate()

        assert target.is_symlink()
        assert target.resolve() == source_file.resolve()

    def test_force_replaces_directory(self, tmp_path: Path) -> None:
        """With force=True, removes existing directory and creates symlink."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        git_dir = source_dir / "git"
        git_dir.mkdir()

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        target_dir = home_dir / ".config" / "git"
        target_dir.mkdir(parents=True)
        (target_dir / "old_config").write_text("old")

        r = SymlinkResource("git/", ".config/git/", source_root=source_dir, home_dir=home_dir, force=True)
        r.generate()

        target = home_dir / ".config" / "git"
        assert target.is_symlink()

    def test_source_not_found_raises(self, tmp_path: Path) -> None:
        """Raises FileNotFoundError if source does not exist."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        r = SymlinkResource("nonexistent.txt", "target.txt", source_root=source_dir, home_dir=home_dir)
        with pytest.raises(FileNotFoundError):
            r.generate()

    def test_dry_run_does_not_create_symlink(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Dry run prints what would happen without creating symlink."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        source_file = source_dir / "hello.txt"
        source_file.write_text("hello")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        r = SymlinkResource("hello.txt", "hello.txt", source_root=source_dir, home_dir=home_dir)
        r.generate(dry_run=True)

        target = home_dir / "hello.txt"
        assert not target.exists()

        captured = capsys.readouterr()
        assert "symlink" in captured.out.lower() or "hello.txt" in captured.out
