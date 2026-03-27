"""PackageResource - installs/uninstalls packages via package managers."""

from __future__ import annotations

import subprocess

from pyhomedot.resources.base import Resource, noninteractive_env

VALID_PROVIDERS = {"apt", "brew", "mise"}


class PackageResource(Resource):
    """Installs or uninstalls packages using supported providers (apt, brew, mise)."""

    def __init__(
        self,
        name: str,
        provider: str,
        installed: bool = True,
        version: str | None = None,
        cask: bool = False,
        interactive: bool = False,
    ) -> None:
        if provider not in VALID_PROVIDERS:
            raise ValueError(f"Invalid provider '{provider}'. Must be one of: {', '.join(sorted(VALID_PROVIDERS))}")
        if cask and provider != "brew":
            raise ValueError("The 'cask' option is only supported with the 'brew' provider")
        self.name = name
        self.provider = provider
        self.installed = installed
        self.version = version
        self.cask = cask
        self.interactive = interactive

    def _package_spec(self) -> str:
        """Build the package specifier with optional version."""
        if self.version is None:
            return self.name
        if self.provider == "apt":
            return f"{self.name}={self.version}"
        else:
            # brew and mise use name@version format
            return f"{self.name}@{self.version}"

    def _build_env(self) -> dict[str, str] | None:
        """Return the subprocess environment, or None to inherit the default."""
        if self.interactive:
            return None
        extra: dict[str, str] = {}
        if self.provider == "apt":
            extra["DEBIAN_FRONTEND"] = "noninteractive"
        elif self.provider == "brew":
            extra["HOMEBREW_NO_AUTO_UPDATE"] = "1"
        elif self.provider == "mise":
            extra["MISE_YES"] = "1"
        return noninteractive_env(extra)

    def _build_command(self) -> list[str]:
        spec = self._package_spec()
        if self.provider == "apt":
            if self.installed:
                return ["apt-get", "install", "-y", spec]
            else:
                return ["apt-get", "remove", "-y", self.name]
        elif self.provider == "brew":
            if self.installed:
                cmd = ["brew", "install"]
                if self.cask:
                    cmd.append("--cask")
                cmd.append(spec)
                return cmd
            else:
                cmd = ["brew", "uninstall"]
                if self.cask:
                    cmd.append("--cask")
                cmd.append(self.name)
                return cmd
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

        result = subprocess.run(cmd, check=False, env=self._build_env())
        if result.returncode != 0:
            action = "install" if self.installed else "uninstall"
            print(f"Warning: Failed to {action} package '{self.name}' via {self.provider} (exit code {result.returncode})")
