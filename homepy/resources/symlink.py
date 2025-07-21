from pathlib import Path
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

        # handle the case where the target does not exist
        if not self.target.is_symlink() and not self.target.exists():
            # create the symlink if the target doesn't exist
            os.symlink(
                self.source, self.target, target_is_directory=self.source.is_dir()
            )
            print(f"Created symlink: {self.source} -> {self.target}")
            return

        # handle the case where the target is a symlink
        if (
            self.target.exists()
            and self.target.is_symlink()
            and str(Path(os.readlink(self.target))) == str(self.source)
        ):
            print(f"Target already exists, skipping: {self.target}")
            return
        elif self.target.exists() and self.target.is_symlink():
            if not self.force:
                print(
                    f"Target is a symlink but points to the wrong source, skipping: {self.target}"
                )
                return
            else:
                print(
                    f"Target is a symlink but points to the wrong source, overwriting: {self.target}"
                )
                self.target.unlink()
                os.symlink(
                    self.source, self.target, target_is_directory=self.source.is_dir()
                )
                print(f"Created symlink: {self.source} -> {self.target}")
                return

        # now make sure that the target and source are the same type
        if self.target.is_file() != self.source.is_file():
            if not self.force:
                print(
                    f"Target and source are not the same type, skipping: {self.target}"
                )
                return
            else:
                print(
                    f"Target and source are the same type, overwriting: {self.target}"
                )
                # guarantee removal of existing target
                if self.target.is_file() or self.target.is_symlink():
                    self.target.unlink()
                elif self.target.is_dir():
                    self.target.rmdir()
                os.symlink(
                    self.source, self.target, target_is_directory=self.source.is_dir()
                )
                print(f"Created symlink: {self.source} -> {self.target}")
                return

        # now handle the case where the target and source are files
        if self.target.is_file() and self.source.is_file():
            if self.target.read_text() == self.source.read_text():
                print(
                    f"Target and source are the same, making target a symlink: {self.target}"
                )
                os.symlink(
                    self.source,
                    self.target,
                    target_is_directory=self.source.is_dir(),
                )
                print(f"Created symlink: {self.source} -> {self.target}")
                return
            else:
                if not self.force:
                    print(
                        f"Target and source are not the same, skipping: {self.target}"
                    )
                    return
                else:
                    print(f"Target and source are the same, overwriting: {self.target}")
                    self.target.unlink()
                    os.symlink(
                        self.source,
                        self.target,
                        target_is_directory=self.source.is_dir(),
                    )
                    print(f"Created symlink: {self.source} -> {self.target}")
                    return

        # now handle the case where the target and source are directories
        if self.target.is_dir() and self.source.is_dir():
            # check if everything is identical
            if all(
                (self.source / item).read_text() == (self.target / item).read_text()
                for item in self.source.iterdir()
                if (self.source / item).is_file()
            ):
                print(
                    f"Target and source are identical, making target a symlink: {self.target}"
                )
                self.target.rmdir()
                os.symlink(
                    self.source,
                    self.target,
                    target_is_directory=self.source.is_dir(),
                )
                print(f"Created symlink: {self.source} -> {self.target}")
                return
            else:
                if not self.force:
                    print(
                        f"Target and source are not identical, skipping: {self.target}"
                    )
                    return
                else:
                    print(
                        f"Target and source are identical, overwriting: {self.target}"
                    )
                    self.target.rmdir()
                    os.symlink(
                        self.source,
                        self.target,
                        target_is_directory=self.source.is_dir(),
                    )
                    print(f"Created symlink: {self.source} -> {self.target}")
                    return
