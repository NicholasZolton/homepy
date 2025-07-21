from pathlib import Path
import os
import shutil
from typing import Tuple
from ..home import HomeResource


class SymlinkResource(HomeResource):
    """
    Represents a symbolic link resource.

    This class encapsulates the details of a symbolic link, including its
    source path, target path, and whether to overwrite existing files or
    directories when creating the symlink. It provides the necessary data
    for managing symbolic links in a structured way.

    Attributes:
        source (Path): The source path of the symbolic link.
        target (Path): The target path where the symbolic link will be created (relative to the home directory).
        force (bool): A flag indicating whether to overwrite existing files or
            directories at the target path if they exist.
    """

    def __init__(self, source: Path, target: Path, force: bool = False) -> None:
        self.source: Path = Path(source)
        self.target: Path = Path(target)
        self.force: bool = force

    def generate(self, verbose: bool = False) -> None:
        """Generate the symbolic link according to simplified rules."""
        resolved_source, resolved_target = self._resolve_paths()
        if not self._validate_source(resolved_source, verbose):
            return
        self._ensure_parent_directories(resolved_target)
        symlink_source = str(resolved_source)

        # Case 1: Target exists and is a symlink to source
        if resolved_target.is_symlink():
            existing_link = Path(os.readlink(resolved_target))
            if self._symlink_points_to_source(
                existing_link, resolved_target, resolved_source
            ):
                if verbose:
                    print(
                        f"Target is already a symlink to source, skipping: {resolved_target}"
                    )
                return
            # Not a symlink to source
            if not self.force:
                print(
                    f"Warning: Target exists and is a symlink to a different source, not changed (either delete the link or use force to change): {resolved_target}"
                )
                return
            else:
                if verbose:
                    print(
                        f"Target is a symlink to a different source, overwriting: {resolved_target}"
                    )
                self._create_symlink(
                    symlink_source,
                    resolved_target,
                    resolved_source,
                    verbose,
                    replace=True,
                )
                return

        # Case 2: Target does not exist
        if not resolved_target.exists():
            self._create_symlink(
                symlink_source, resolved_target, resolved_source, verbose
            )
            print(f"Created symlink: {symlink_source} -> {resolved_target}")
            return

        # Case 3: Target exists and is not a symlink
        if not self.force:
            print(
                f"Warning: Target exists and is not a symlink, not changed: {resolved_target}"
            )
            return
        else:
            if verbose:
                print(
                    f"Target exists and is not a symlink, overwriting: {resolved_target}"
                )
            self._create_symlink(
                symlink_source, resolved_target, resolved_source, verbose, replace=True
            )
            return

    def _resolve_paths(self) -> Tuple[Path, Path]:
        """Resolve source and target paths to absolute paths."""
        resolved_source = self.source
        if not self.source.is_absolute():
            resolved_source = Path(os.getcwd()) / self.source

        resolved_target = self.target
        if not self.target.is_absolute():
            resolved_target = Path.home() / self.target

        return resolved_source, resolved_target

    def _validate_source(self, resolved_source: Path, verbose: bool) -> bool:
        """Check if source exists."""
        if not resolved_source.exists():
            if verbose:
                print(f"Source path does not exist, skipping: {resolved_source}")
            return False
        return True

    def _ensure_parent_directories(self, resolved_target: Path) -> None:
        """Create parent directories for the target if they don't exist."""
        resolved_target.parent.mkdir(parents=True, exist_ok=True)

    def _symlink_points_to_source(
        self, existing_link: Path, resolved_target: Path, resolved_source: Path
    ) -> bool:
        """Check if existing symlink points to the correct source."""
        if existing_link.is_absolute():
            return str(existing_link) == str(resolved_source)
        else:
            existing_resolved = (resolved_target.parent / existing_link).resolve()
            return str(existing_resolved) == str(resolved_source)

    def _create_symlink(
        self,
        symlink_source: str,
        resolved_target: Path,
        resolved_source: Path,
        verbose: bool,
        replace: bool = False,
    ) -> None:
        """Create the symbolic link, optionally replacing existing target."""
        if replace:
            self._remove_target(resolved_target)

        os.symlink(
            symlink_source,
            resolved_target,
            target_is_directory=resolved_source.is_dir(),
        )

    def _remove_target(self, resolved_target: Path) -> None:
        """Remove existing target (file, symlink, or directory)."""
        # Always use unlink for symlinks, even if they are directories
        if resolved_target.is_symlink():
            resolved_target.unlink()
        elif resolved_target.is_file():
            resolved_target.unlink()
        elif resolved_target.is_dir():
            if any(resolved_target.iterdir()):
                shutil.rmtree(resolved_target)
            else:
                resolved_target.rmdir()
