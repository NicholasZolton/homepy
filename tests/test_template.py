"""Tests for TemplateResource."""

from __future__ import annotations

from pathlib import Path

import pytest

from homepy.resources import TemplateResource


class TestTemplateResource:
    """Test TemplateResource rendering and writing."""

    def test_renders_variables_and_writes(self, tmp_path: Path) -> None:
        """Renders template with variables and writes to target."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        template = source_dir / "gitconfig.tmpl"
        template.write_text("[user]\n    name = {{ username }}\n    email = {{ email }}\n")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        r = TemplateResource(
            "gitconfig.tmpl",
            ".gitconfig",
            variables={"username": "John", "email": "john@example.com"},
            source_root=source_dir,
            home_dir=home_dir,
        )
        r.generate()

        target = home_dir / ".gitconfig"
        assert target.exists()
        assert not target.is_symlink()
        content = target.read_text()
        assert "John" in content
        assert "john@example.com" in content
        assert "{{ username }}" not in content
        assert "{{ email }}" not in content

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        template = source_dir / "config.tmpl"
        template.write_text("host = {{ host }}")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        r = TemplateResource(
            "config.tmpl",
            ".config/app/config",
            variables={"host": "localhost"},
            source_root=source_dir,
            home_dir=home_dir,
        )
        r.generate()

        target = home_dir / ".config" / "app" / "config"
        assert target.exists()
        assert "localhost" in target.read_text()

    def test_warns_on_existing_file_without_force(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        template = source_dir / "config.tmpl"
        template.write_text("value = {{ val }}")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        target = home_dir / "config"
        target.write_text("old content")

        r = TemplateResource(
            "config.tmpl",
            "config",
            variables={"val": "new"},
            source_root=source_dir,
            home_dir=home_dir,
        )
        r.generate()

        captured = capsys.readouterr()
        assert "warning" in captured.out.lower() or "Warning" in captured.out
        assert target.read_text() == "old content"

    def test_force_overwrites_existing(self, tmp_path: Path) -> None:
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        template = source_dir / "config.tmpl"
        template.write_text("value = {{ val }}")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        target = home_dir / "config"
        target.write_text("old content")

        r = TemplateResource(
            "config.tmpl",
            "config",
            variables={"val": "new"},
            source_root=source_dir,
            home_dir=home_dir,
            force=True,
        )
        r.generate()

        assert "new" in target.read_text()
        assert "old content" not in target.read_text()

    def test_dry_run_does_not_write(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        template = source_dir / "config.tmpl"
        template.write_text("value = {{ val }}")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        r = TemplateResource(
            "config.tmpl",
            "config",
            variables={"val": "test"},
            source_root=source_dir,
            home_dir=home_dir,
        )
        r.generate(dry_run=True)

        target = home_dir / "config"
        assert not target.exists()

        captured = capsys.readouterr()
        assert "config" in captured.out.lower() or "template" in captured.out.lower()

    def test_empty_variables(self, tmp_path: Path) -> None:
        """Template with no variables is written as-is."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        template = source_dir / "static.txt"
        template.write_text("no variables here")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        r = TemplateResource(
            "static.txt",
            "static.txt",
            variables={},
            source_root=source_dir,
            home_dir=home_dir,
        )
        r.generate()

        target = home_dir / "static.txt"
        assert target.read_text() == "no variables here"

    def test_jinja_style_variables(self, tmp_path: Path) -> None:
        """Renders {{ variable }} syntax."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        template = source_dir / "config.tmpl"
        template.write_text("name = {{ username }}\nhost = {{ host }}")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        r = TemplateResource(
            "config.tmpl",
            "config",
            variables={"username": "Alice", "host": "myhost"},
            source_root=source_dir,
            home_dir=home_dir,
        )
        r.generate()

        target = home_dir / "config"
        content = target.read_text()
        assert "Alice" in content
        assert "myhost" in content
        assert "{{ username }}" not in content
        assert "{{ host }}" not in content

    def test_source_not_found_raises(self, tmp_path: Path) -> None:
        """Raises FileNotFoundError if template source does not exist."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        r = TemplateResource(
            "nonexistent.tmpl",
            "config",
            variables={},
            source_root=source_dir,
            home_dir=home_dir,
        )
        with pytest.raises(FileNotFoundError):
            r.generate()

    def test_preserves_non_variable_text(self, tmp_path: Path) -> None:
        """Text without {{ }} is preserved as-is, including dollar signs."""
        source_dir = tmp_path / "project"
        source_dir.mkdir()
        template = source_dir / "config.tmpl"
        template.write_text("price = $100\nname = {{ name }}")

        home_dir = tmp_path / "home"
        home_dir.mkdir()

        r = TemplateResource(
            "config.tmpl",
            "config",
            variables={"name": "Alice"},
            source_root=source_dir,
            home_dir=home_dir,
        )
        r.generate()

        target = home_dir / "config"
        content = target.read_text()
        assert "$100" in content
        assert "Alice" in content
