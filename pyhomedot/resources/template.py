"""TemplateResource - renders variables into config files before writing."""

from __future__ import annotations

import re
from pathlib import Path

from pyhomedot.resources.base import Resource


class TemplateResource(Resource):
    """Renders variables into config files before writing them.

    Uses {{ variable }} (Jinja2-style) syntax for template substitution.
    """

    def __init__(
        self,
        source: str,
        target: str,
        *,
        variables: dict[str, str],
        force: bool = False,
        source_root: Path | None = None,
        home_dir: Path | None = None,
    ) -> None:
        self.source = source
        self.target = target
        self.variables = variables
        self.force = force
        self._source_root = source_root or Path.cwd()
        self._home_dir = home_dir or Path.home()

    def _resolve_source(self) -> Path:
        return (self._source_root / self.source).resolve()

    def _resolve_target(self) -> Path:
        return self._home_dir / self.target

    def _render(self, template_content: str) -> str:
        def replace_var(match: re.Match[str]) -> str:
            key = match.group(1)
            return self.variables[key]

        return re.sub(r"\{\{\s*(\w+)\s*\}\}", replace_var, template_content)

    def generate(self, *, dry_run: bool = False) -> None:
        source = self._resolve_source()
        target = self._resolve_target()
        template_content = source.read_text()
        rendered = self._render(template_content)

        if dry_run:
            print(f"[dry-run] Would render template {source} -> {target}")
            return

        # Create parent directories
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists():
            if self.force:
                target.unlink()
            else:
                print(f"Warning: {target} already exists, skipping (use force=True to overwrite)")
                return

        target.write_text(rendered)
