"""Base resource interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Resource(ABC):
    """Abstract base class for all pyhomedot resources."""

    @abstractmethod
    def generate(self, *, dry_run: bool = False) -> None:
        """Generate/apply this resource.

        Args:
            dry_run: If True, print what would happen without making changes.
        """
