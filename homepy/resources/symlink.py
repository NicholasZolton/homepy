from pathlib import Path
import os
import shutil
from typing import Tuple, Optional
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
        """Generate the symbolic link."""
        resolved_source, resolved_target = self._resolve_paths()
        
        if not self._validate_source(resolved_source, verbose):
            return
            
        self._ensure_parent_directories(resolved_target)
        symlink_source = self._calculate_relative_path(resolved_source, resolved_target)
        
        if resolved_target.is_symlink():
            if self._handle_existing_symlink(resolved_target, resolved_source, symlink_source, verbose):
                return
        elif not resolved_target.exists():
            self._create_symlink(symlink_source, resolved_target, resolved_source, verbose)
            return
        else:
            if self._handle_existing_file_or_directory(resolved_target, resolved_source, symlink_source, verbose):
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

    def _calculate_relative_path(self, resolved_source: Path, resolved_target: Path) -> str:
        """Calculate the relative path from target to source for the symlink."""
        try:
            return os.path.relpath(resolved_source, resolved_target.parent)
        except ValueError:
            # If relative path calculation fails (e.g., different drives on Windows), use absolute path
            return str(resolved_source)

    def _handle_existing_symlink(self, resolved_target: Path, resolved_source: Path, 
                                symlink_source: str, verbose: bool) -> bool:
        """Handle case where target is already a symlink. Returns True if handled (should return from generate)."""
        existing_link = Path(os.readlink(resolved_target))
        source_matches = self._symlink_points_to_source(existing_link, resolved_target, resolved_source)
        format_matches = str(existing_link) == symlink_source
        
        if source_matches and format_matches:
            if verbose:
                print(f"Target already exists, skipping: {resolved_target}")
            return True
        elif source_matches and not format_matches:
            if verbose:
                print(f"Target symlink has correct source but wrong format, updating: {resolved_target}")
            self._create_symlink(symlink_source, resolved_target, resolved_source, verbose, replace=True)
            return True
        else:
            return self._handle_wrong_symlink(resolved_target, resolved_source, symlink_source, verbose)

    def _symlink_points_to_source(self, existing_link: Path, resolved_target: Path, resolved_source: Path) -> bool:
        """Check if existing symlink points to the correct source."""
        if existing_link.is_absolute():
            return str(existing_link) == str(resolved_source)
        else:
            existing_resolved = (resolved_target.parent / existing_link).resolve()
            return str(existing_resolved) == str(resolved_source)

    def _handle_wrong_symlink(self, resolved_target: Path, resolved_source: Path, 
                             symlink_source: str, verbose: bool) -> bool:
        """Handle symlink that points to wrong source. Returns True if handled."""
        if not self.force:
            if verbose:
                print(f"Target is a symlink but points to the wrong source, skipping: {resolved_target}")
            return True
        else:
            if verbose:
                print(f"Target is a symlink but points to the wrong source, overwriting: {resolved_target}")
            self._create_symlink(symlink_source, resolved_target, resolved_source, verbose, replace=True)
            return True

    def _handle_existing_file_or_directory(self, resolved_target: Path, resolved_source: Path, 
                                         symlink_source: str, verbose: bool) -> bool:
        """Handle case where target exists but is not a symlink. Returns True if handled."""
        if self._different_types(resolved_target, resolved_source):
            return self._handle_type_mismatch(resolved_target, resolved_source, symlink_source, verbose)
        elif resolved_target.is_file() and resolved_source.is_file():
            return self._handle_existing_file(resolved_target, resolved_source, symlink_source, verbose)
        elif resolved_target.is_dir() and resolved_source.is_dir():
            return self._handle_existing_directory(resolved_target, resolved_source, symlink_source, verbose)
        else:
            return self._handle_unhandled_case(resolved_target, resolved_source, symlink_source, verbose)

    def _different_types(self, resolved_target: Path, resolved_source: Path) -> bool:
        """Check if target and source are different types (file vs directory)."""
        return resolved_target.is_file() != resolved_source.is_file()

    def _handle_type_mismatch(self, resolved_target: Path, resolved_source: Path, 
                             symlink_source: str, verbose: bool) -> bool:
        """Handle case where target and source are different types."""
        if not self.force:
            if verbose:
                print(f"Target and source are not the same type, skipping: {resolved_target}")
            return True
        else:
            if verbose:
                print(f"Target and source are different types, overwriting: {resolved_target}")
            self._create_symlink(symlink_source, resolved_target, resolved_source, verbose, replace=True)
            return True

    def _handle_existing_file(self, resolved_target: Path, resolved_source: Path, 
                             symlink_source: str, verbose: bool) -> bool:
        """Handle case where both target and source are files."""
        if self._files_identical(resolved_target, resolved_source):
            if verbose:
                print(f"Target and source are the same, making target a symlink: {resolved_target}")
            self._create_symlink(symlink_source, resolved_target, resolved_source, verbose, replace=True)
            return True
        else:
            return self._handle_different_files(resolved_target, resolved_source, symlink_source, verbose)

    def _files_identical(self, resolved_target: Path, resolved_source: Path) -> bool:
        """Check if two files have identical content."""
        try:
            return resolved_target.read_text() == resolved_source.read_text()
        except (OSError, UnicodeDecodeError):
            return False

    def _handle_different_files(self, resolved_target: Path, resolved_source: Path, 
                               symlink_source: str, verbose: bool) -> bool:
        """Handle case where target and source files have different content."""
        if not self.force:
            if verbose:
                print(f"Target and source are not the same, skipping: {resolved_target}")
            return True
        else:
            if verbose:
                print(f"Target and source are different, overwriting: {resolved_target}")
            self._create_symlink(symlink_source, resolved_target, resolved_source, verbose, replace=True)
            return True

    def _handle_existing_directory(self, resolved_target: Path, resolved_source: Path, 
                                  symlink_source: str, verbose: bool) -> bool:
        """Handle case where both target and source are directories."""
        if self._directories_identical(resolved_target, resolved_source):
            if verbose:
                print(f"Target and source are identical, making target a symlink: {resolved_target}")
            self._create_symlink(symlink_source, resolved_target, resolved_source, verbose, replace=True)
            return True
        else:
            return self._handle_different_directories(resolved_target, resolved_source, symlink_source, verbose)

    def _directories_identical(self, resolved_target: Path, resolved_source: Path) -> bool:
        """Check if two directories have identical content."""
        try:
            return all(
                (resolved_source / item).read_text() == (resolved_target / item).read_text()
                for item in resolved_source.iterdir()
                if (resolved_source / item).is_file()
            )
        except (OSError, UnicodeDecodeError):
            return False

    def _handle_different_directories(self, resolved_target: Path, resolved_source: Path, 
                                     symlink_source: str, verbose: bool) -> bool:
        """Handle case where target and source directories have different content."""
        if not self.force:
            if verbose:
                print(f"Target and source are not identical, skipping: {resolved_target}")
            return True
        else:
            if verbose:
                print(f"Target and source are different, overwriting: {resolved_target}")
            self._create_symlink(symlink_source, resolved_target, resolved_source, verbose, replace=True)
            return True

    def _handle_unhandled_case(self, resolved_target: Path, resolved_source: Path, 
                              symlink_source: str, verbose: bool) -> bool:
        """Handle any remaining unhandled cases."""
        if not self.force:
            if verbose:
                print(f"Target exists but cannot be handled, skipping: {resolved_target}")
            return True
        else:
            if verbose:
                print(f"Target exists, forcing overwrite: {resolved_target}")
            self._create_symlink(symlink_source, resolved_target, resolved_source, verbose, replace=True)
            return True

    def _create_symlink(self, symlink_source: str, resolved_target: Path, resolved_source: Path, 
                       verbose: bool, replace: bool = False) -> None:
        """Create the symbolic link, optionally replacing existing target."""
        if replace:
            self._remove_target(resolved_target)
            
        os.symlink(symlink_source, resolved_target, target_is_directory=resolved_source.is_dir())
        
        if verbose:
            print(f"Created symlink: {symlink_source} -> {resolved_target}")

    def _remove_target(self, resolved_target: Path) -> None:
        """Remove existing target (file, symlink, or directory)."""
        if resolved_target.is_file() or resolved_target.is_symlink():
            resolved_target.unlink()
        elif resolved_target.is_dir():
            if any(resolved_target.iterdir()):
                shutil.rmtree(resolved_target)
            else:
                resolved_target.rmdir()
