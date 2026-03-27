"""Home - the core orchestrator for pyhomedot."""

from __future__ import annotations

import sys

from pyhomedot.color import BOLD, CYAN, DIM, GREEN, RED, YELLOW, color
from pyhomedot.resources.base import Resource

_SENTINEL: object = object()

_DRY_RUN_LEGEND = f"""  {color('Legend:', BOLD)}
    {color('OK', GREEN)}       — symlink already correct (no-op)
    {color('CREATE', GREEN)}   — target missing, will create symlink
    {color('IDENTICAL', CYAN)} — existing file/dir with same content (safe to replace)
    {color('REPLACE', YELLOW)}  — existing file/dir will be replaced with symlink
    {color('RELINK', YELLOW)}   — symlink exists but points to wrong target
    {color('CONFLICT', RED)} — existing file/dir, will skip (force=False)
    {color('MISSING', RED)}  — source file not found in repo
"""


class Home:
    """Core orchestrator that manages and generates resources."""

    def __init__(self) -> None:
        self.resources: list[Resource] = []

    def add(self, *resources: Resource) -> Home:
        """Add one or more resources. Returns self for chaining."""
        self.resources.extend(resources)
        return self

    def generate(self, *, dry_run: bool | object = _SENTINEL) -> None:
        """Generate all registered resources.

        If dry_run is not explicitly passed, checks for --dry-run in sys.argv.

        Args:
            dry_run: If True, print what would happen without making changes.
                     If not provided, checks sys.argv for --dry-run flag.
        """
        if dry_run is _SENTINEL:
            resolved_dry_run = "--dry-run" in sys.argv
        else:
            resolved_dry_run = bool(dry_run)

        if resolved_dry_run:
            print(_DRY_RUN_LEGEND)

        for resource in self.resources:
            resource.generate(dry_run=resolved_dry_run)

        total = len(self.resources)
        if resolved_dry_run:
            print(f"\n  {color(f'{total} resources checked (dry run — no changes made)', DIM)}")
        else:
            print(f"\n  {color(f'{total} resources processed', DIM)}")
