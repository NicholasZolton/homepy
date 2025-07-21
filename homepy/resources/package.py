from home import HomeResource
from typing import Literal
import subprocess


class PackageResource(HomeResource):
    """A resource for managing Python packages. Does not handle uninstalling packages, only ensuring they are installed."""

    def __init__(self, package: str) -> None:
        self.package: str = package
        self.manager: Literal["apt", "brew", "nix", "pip", "snap"] = "apt"
        self.installed: bool = True

    def generate(self, verbose: bool = False) -> None:
        """Generate the package."""

        if self.installed:
            if self.manager == "apt":
                self._apt_install(verbose)

            elif self.manager == "brew":
                self._brew_install(verbose)

            elif self.manager == "nix":
                self._nix_env_install(verbose)
        else:

    def _apt_install(self, verbose: bool = False) -> None:
        """Install the package using apt."""
        result = subprocess.run(
            ["apt", "install", self.package], check=True, capture_output=True, text=True
        )
        print(f"Installed {self.package} using apt.")
        if verbose:
            print(result.stdout)
            if result.stderr:
                print(result.stderr)

    def _brew_install(self, verbose: bool = False) -> None:
        """Install the package using brew."""
        result = subprocess.run(
            ["brew", "install", self.package],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"Installed {self.package} using brew.")
        if verbose:
            print(result.stdout)
            if result.stderr:
                print(result.stderr)

    def _nix_env_install(self, verbose: bool = False) -> None:
        """Install the package using nix-env."""
        result = subprocess.run(
            ["nix-env", "-iA", self.package], check=True, capture_output=True, text=True
        )
        print(f"Installed {self.package} using nix-env.")
        if verbose:
            print(result.stdout)
            if result.stderr:
                print(result.stderr)

    def _apt_uninstall(self, verbose: bool = False) -> None:
        """Uninstall the package using apt."""
        result = subprocess.run(
            ["apt", "remove", self.package], check=True, capture_output=True, text=True
        )
        print(f"Uninstalled {self.package} using apt.")
        if verbose:
            print(result.stdout)
            if result.stderr:
                print(result.stderr)

    def _brew_uninstall(self, verbose: bool = False) -> None:
        """Uninstall the package using brew."""
        result = subprocess.run(
            ["brew", "uninstall", self.package],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"Uninstalled {self.package} using brew.")
        if verbose:
            print(result.stdout)
            if result.stderr:
                print(result.stderr)

    def _nix_env_uninstall(self, verbose: bool = False) -> None:
        """Uninstall the package using nix-env."""
        result = subprocess.run(
            ["nix-env", "-e", self.package], check=True, capture_output=True, text=True
        )
        print(f"Uninstalled {self.package} using nix-env.")
        if verbose:
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
