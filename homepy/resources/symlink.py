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
        # Resolve source and target paths to absolute paths for existence checks and operations
        resolved_source = self.source
        if not self.source.is_absolute():
            resolved_source = Path(os.getcwd()) / self.source

        resolved_target = self.target
        # Resolve target path relative to home directory (unless it's already absolute)
        if not self.target.is_absolute():
            resolved_target = Path.home() / self.target

        # Ensure source exists
        if not resolved_source.exists():
            print(f"Source path does not exist, skipping: {resolved_source}")
            return

        # Create parent directories for the target if they don't exist
        resolved_target.parent.mkdir(parents=True, exist_ok=True)

        # Calculate the relative path from target to source for the symlink
        try:
            symlink_source = os.path.relpath(resolved_source, resolved_target.parent)
        except ValueError:
            # If relative path calculation fails (e.g., different drives on Windows), use absolute path
            symlink_source = str(resolved_source)

        # handle the case where the target is a symlink (check this first since broken symlinks return False for exists())
        if resolved_target.is_symlink():
            existing_link = Path(os.readlink(resolved_target))
            # Check if existing symlink points to the same resolved source
            if existing_link.is_absolute():
                source_matches = str(existing_link) == str(resolved_source)
            else:
                # Resolve the existing relative symlink to compare
                existing_resolved = (resolved_target.parent / existing_link).resolve()
                source_matches = str(existing_resolved) == str(resolved_source)
            
            # Also check if the symlink format matches what we want to create
            format_matches = str(existing_link) == symlink_source
                
            if source_matches and format_matches:
                print(f"Target already exists, skipping: {resolved_target}")
                return
            elif source_matches and not format_matches:
                # Source is correct but format is wrong (e.g., absolute vs relative) - update it
                print(f"Target symlink has correct source but wrong format, updating: {resolved_target}")
                resolved_target.unlink()
                os.symlink(
                    symlink_source, resolved_target, target_is_directory=resolved_source.is_dir()
                )
                print(f"Created symlink: {symlink_source} -> {resolved_target}")
                return
            else:
                # Source is wrong
                if not self.force:
                    print(
                        f"Target is a symlink but points to the wrong source, skipping: {resolved_target}"
                    )
                    return
                else:
                    print(
                        f"Target is a symlink but points to the wrong source, overwriting: {resolved_target}"
                    )
                    resolved_target.unlink()
                    os.symlink(
                        symlink_source, resolved_target, target_is_directory=resolved_source.is_dir()
                    )
                    print(f"Created symlink: {symlink_source} -> {resolved_target}")
                    return

        # handle the case where the target does not exist
        if not resolved_target.exists():
            # create the symlink if the target doesn't exist
            os.symlink(
                symlink_source, resolved_target, target_is_directory=resolved_source.is_dir()
            )
            print(f"Created symlink: {symlink_source} -> {resolved_target}")
            return

        # now make sure that the target and source are the same type
        if resolved_target.is_file() != resolved_source.is_file():
            if not self.force:
                print(
                    f"Target and source are not the same type, skipping: {resolved_target}"
                )
                return
            else:
                print(
                    f"Target and source are the same type, overwriting: {resolved_target}"
                )
                # guarantee removal of existing target
                if resolved_target.is_file() or resolved_target.is_symlink():
                    resolved_target.unlink()
                elif resolved_target.is_dir():
                    resolved_target.rmdir()
                os.symlink(
                    symlink_source, resolved_target, target_is_directory=resolved_source.is_dir()
                )
                print(f"Created symlink: {symlink_source} -> {resolved_target}")
                return

        # now handle the case where the target and source are files
        if resolved_target.is_file() and resolved_source.is_file():
            if resolved_target.read_text() == resolved_source.read_text():
                print(
                    f"Target and source are the same, making target a symlink: {resolved_target}"
                )
                resolved_target.unlink()
                os.symlink(
                    symlink_source,
                    resolved_target,
                    target_is_directory=resolved_source.is_dir(),
                )
                print(f"Created symlink: {symlink_source} -> {resolved_target}")
                return
            else:
                if not self.force:
                    print(
                        f"Target and source are not the same, skipping: {resolved_target}"
                    )
                    return
                else:
                    print(f"Target and source are the same, overwriting: {resolved_target}")
                    resolved_target.unlink()
                    os.symlink(
                        symlink_source,
                        resolved_target,
                        target_is_directory=resolved_source.is_dir(),
                    )
                    print(f"Created symlink: {symlink_source} -> {resolved_target}")
                    return

        # now handle the case where the target and source are directories
        if resolved_target.is_dir() and resolved_source.is_dir():
            # check if everything is identical
            if all(
                (resolved_source / item).read_text() == (resolved_target / item).read_text()
                for item in resolved_source.iterdir()
                if (resolved_source / item).is_file()
            ):
                print(
                    f"Target and source are identical, making target a symlink: {resolved_target}"
                )
                resolved_target.rmdir()
                os.symlink(
                    symlink_source,
                    resolved_target,
                    target_is_directory=resolved_source.is_dir(),
                )
                print(f"Created symlink: {symlink_source} -> {resolved_target}")
                return
            else:
                if not self.force:
                    print(
                        f"Target and source are not identical, skipping: {resolved_target}"
                    )
                    return
                else:
                    print(
                        f"Target and source are identical, overwriting: {resolved_target}"
                    )
                    resolved_target.rmdir()
                    os.symlink(
                        symlink_source,
                        resolved_target,
                        target_is_directory=resolved_source.is_dir(),
                    )
                    print(f"Created symlink: {symlink_source} -> {resolved_target}")
                    return

        # If we reach here, target exists but doesn't match any handled cases
        if resolved_target.exists():
            if not self.force:
                print(f"Target exists but cannot be handled, skipping: {resolved_target}")
                return
            else:
                print(f"Target exists, forcing overwrite: {resolved_target}")
                if resolved_target.is_file() or resolved_target.is_symlink():
                    resolved_target.unlink()
                elif resolved_target.is_dir():
                    import shutil
                    shutil.rmtree(resolved_target)
                os.symlink(
                    symlink_source,
                    resolved_target,
                    target_is_directory=resolved_source.is_dir(),
                )
                print(f"Created symlink: {symlink_source} -> {resolved_target}")
                return

        # Create parent directories for the target if they don't exist
        self.target.parent.mkdir(parents=True, exist_ok=True)

        # handle the case where the target is a symlink (check this first since broken symlinks return False for exists())
        if self.target.is_symlink():
            if str(Path(os.readlink(self.target))) == str(self.source):
                print(f"Target already exists, skipping: {self.target}")
                return
            else:
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

        # handle the case where the target does not exist
        if not self.target.exists():
            # create the symlink if the target doesn't exist
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
                self.target.unlink()
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

        # If we reach here, target exists but doesn't match any handled cases
        if self.target.exists():
            if not self.force:
                print(f"Target exists but cannot be handled, skipping: {self.target}")
                return
            else:
                print(f"Target exists, forcing overwrite: {self.target}")
                if self.target.is_file() or self.target.is_symlink():
                    self.target.unlink()
                elif self.target.is_dir():
                    import shutil
                    shutil.rmtree(self.target)
                os.symlink(
                    self.source,
                    self.target,
                    target_is_directory=self.source.is_dir(),
                )
                print(f"Created symlink: {self.source} -> {self.target}")
                return
