"""Home - the core orchestrator for homepy."""

from __future__ import annotations

import sys

from homepy.resources.base import Resource

_SENTINEL: object = object()


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

        for resource in self.resources:
            resource.generate(dry_run=resolved_dry_run)
