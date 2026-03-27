"""ANSI color helpers for terminal output."""

from __future__ import annotations

import sys

BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"


def _is_tty() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def color(text: str, code: str) -> str:
    """Wrap text in ANSI color codes if stdout is a TTY."""
    if not _is_tty():
        return text
    return f"{code}{text}{RESET}"
