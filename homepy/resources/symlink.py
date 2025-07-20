from pathlib import Path
import shutil
import os
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
        # Resolve source and target paths
        if not self.source.is_absolute():
            self.source = Path(os.getcwd()) / self.source

        # Resolve target path relative to home directory (unless it's already absolute)
        if not self.target.is_absolute():
            self.target = Path.home() / self.target

        # Ensure source exists
        if not self.source.exists():
            print(f"Source path does not exist, skipping: {self.source}")
            return

        # Create parent directories for the target if they don't exist
        self.target.parent.mkdir(parents=True, exist_ok=True)

        # Handle force logic if the target exists
        if not (self.target.exists() or self.target.is_symlink()):
            # Create the symbolic link if the target doesn't exist
            os.symlink(
                self.source, self.target, target_is_directory=self.source.is_dir()
            )
            print(f"Created symlink: {self.source} -> {self.target}")
            return

        # Check if the existing symlink points to the source
        if self.target.is_symlink() and str(Path(os.readlink(self.target))) == str(
            self.source
        ):
            return

        # Handle cases where the target is a file
        if self.target.is_file():
            if (
                self.source.is_file()
                and self.target.read_text() == self.source.read_text()
            ):
                if verbose:
                    print(
                        f"Replacing identical file with symlink to source: {self.target}"
                    )
                self.target.unlink()
            elif self.force:
                print(f"Target file exists, overwriting with force: {self.target}")
                self.target.unlink()
            else:
                print(f"Target file exists, skipping: {self.target}")
                return

        # Handle cases where the target is a directory
        elif self.target.is_dir():
            if self.source.is_dir() and all(
                (self.source / item).read_text() == (self.target / item).read_text()
                for item in self.source.iterdir()
                if (self.source / item).is_file()
            ):
                print(
                    f"Replacing directory with symlink (identical contents): {self.target}"
                )
                shutil.rmtree(self.target)
            elif self.force:
                print(f"Target directory exists, overwriting with force: {self.target}")
                if verbose:
                    print(f"Replacing directory: {self.target}")
                shutil.rmtree(self.target)
            else:
                print(f"Target directory exists, skipping: {self.target}")
                return

        # Final check: only create symlink if target does not exist
        if self.target.exists() or self.target.is_symlink():
            print(
                f"Final check: Target still exists, not creating symlink: {self.target}"
            )
            return

        os.symlink(self.source, self.target, target_is_directory=self.source.is_dir())
        print(f"Created symlink: {self.source} -> {self.target}")
