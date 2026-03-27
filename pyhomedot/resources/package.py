"""PackageResource - installs/uninstalls packages via package managers."""

from __future__ import annotations

import subprocess

from pyhomedot.resources.base import Resource

VALID_PROVIDERS = {"apt", "brew", "mise"}


class PackageResource(Resource):
    """Installs or uninstalls packages using supported providers (apt, brew, mise)."""

    def __init__(self, name: str, provider: str, installed: bool = True, version: str | None = None) -> None:
        if provider not in VALID_PROVIDERS:
            raise ValueError(f"Invalid provider '{provider}'. Must be one of: {', '.join(sorted(VALID_PROVIDERS))}")
        self.name = name
        self.provider = provider
        self.installed = installed
        self.version = version

    def _package_spec(self) -> str:
        """Build the package specifier with optional version."""
        if self.version is None:
            return self.name
        if self.provider == "apt":
            return f"{self.name}={self.version}"
        else:
            # brew and mise use name@version format
            return f"{self.name}@{self.version}"

    def _build_command(self) -> list[str]:
        spec = self._package_spec()
        if self.provider == "apt":
            if self.installed:
                return ["apt-get", "install", "-y", spec]
            else:
                return ["apt-get", "remove", "-y", self.name]
        elif self.provider == "brew":
            if self.installed:
                return ["brew", "install", spec]
            else:
                return ["brew", "uninstall", self.name]
        elif self.provider == "mise":
            if self.installed:
                return ["mise", "use", "-g", spec]
            else:
                return ["mise", "uninstall", self.name]
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def generate(self, *, dry_run: bool = False, show_diff: bool = False) -> None:
        cmd = self._build_command()
        if dry_run:
            action = "install" if self.installed else "uninstall"
            print(f"[dry-run] Would {action} package '{self.name}' via {self.provider}: {' '.join(cmd)}")
            return

        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            action = "install" if self.installed else "uninstall"
            print(f"Warning: Failed to {action} package '{self.name}' via {self.provider} (exit code {result.returncode})")
