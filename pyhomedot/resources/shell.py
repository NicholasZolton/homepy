"""ShellResource - runs arbitrary shell commands during generation."""

from __future__ import annotations

import subprocess

from pyhomedot.resources.base import Resource, noninteractive_env


class ShellResource(Resource):
    """Runs arbitrary shell commands during generation."""

    def __init__(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        interactive: bool = False,
    ) -> None:
        self.command = command
        self.cwd = cwd
        self.env = env
        self.interactive = interactive

    def _build_env(self) -> dict[str, str] | None:
        """Return the subprocess environment, or None to inherit the default."""
        if self.interactive:
            return self.env
        return noninteractive_env(self.env)

    def generate(self, *, dry_run: bool = False, show_diff: bool = False) -> None:
        if dry_run:
            msg = f"[dry-run] Would run: {self.command}"
            if self.cwd:
                msg += f" (in {self.cwd})"
            print(msg)
            return

        result = subprocess.run(
            self.command,
            shell=True,
            check=False,
            cwd=self.cwd,
            env=self._build_env(),
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Shell command failed with exit code {result.returncode}: {self.command}"
            )
