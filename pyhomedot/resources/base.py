"""Base resource interface."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod


def noninteractive_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Return the current environment with NONINTERACTIVE=1 and any extra vars merged in."""
    env = os.environ.copy()
    env["NONINTERACTIVE"] = "1"
    if extra is not None:
        env.update(extra)
    return env


class Resource(ABC):
    """Abstract base class for all pyhomedot resources."""

    @abstractmethod
    def generate(self, *, dry_run: bool = False, show_diff: bool = False) -> None:
        """Generate/apply this resource.

        Args:
            dry_run: If True, print what would happen without making changes.
            show_diff: If True, show diffs for conflicting files.
        """
