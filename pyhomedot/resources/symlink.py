"""SymlinkResource - creates symlinks from source to target."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from pyhomedot.resources.base import Resource


class SymlinkResource(Resource):
    """Creates symlinks from source files/directories to target locations relative to $HOME."""

    def __init__(
        self,
        source: str,
        target: str,
        *,
        force: bool = False,
        source_root: Path | None = None,
        home_dir: Path | None = None,
    ) -> None:
        self.source = source
        self.target = target
        self.force = force
        self._source_root = source_root or Path.cwd()
        self._home_dir = home_dir or Path.home()

    def _resolve_source(self) -> Path:
        return (self._source_root / self.source).resolve()

    def _resolve_target(self) -> Path:
        # Strip trailing slash for path resolution
        target = self.target.rstrip("/")
        return self._home_dir / target

    def generate(self, *, dry_run: bool = False) -> None:
        source = self._resolve_source()
        target = self._resolve_target()

        if not source.exists():
            raise FileNotFoundError(f"Source does not exist: {source}")

        if dry_run:
            print(f"[dry-run] Would create symlink: {target} -> {source}")
            return

        # Create parent directories
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists() or target.is_symlink():
            if target.is_symlink():
                existing_target = Path(os.readlink(str(target))).resolve()
                if existing_target == source:
                    # Already correct symlink, skip
                    return
                else:
                    # Symlink to different source
                    if self.force:
                        target.unlink()
                    else:
                        print(f"Warning: {target} is already a symlink to {existing_target}, skipping (use force=True to overwrite)")
                        return
            else:
                # Regular file or directory
                if self.force:
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                else:
                    print(f"Warning: {target} already exists and is not a symlink, skipping (use force=True to overwrite)")
                    return

        target.symlink_to(source)
