"""SymlinkResource - creates symlinks from source to target."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from pyhomedot.color import BOLD, CYAN, DIM, GREEN, RED, YELLOW, color
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

    def _short_target(self) -> str:
        """Return ~/relative target path for display."""
        return f"~/{self.target}"

    def generate(self, *, dry_run: bool = False) -> None:
        source = self._resolve_source()
        target = self._resolve_target()
        label = self._short_target()

        if not source.exists():
            if dry_run:
                print(f"  {color('MISSING', RED)}  source does not exist: {source}")
                return
            raise FileNotFoundError(f"Source does not exist: {source}")

        # Check current state of target
        if target.exists() or target.is_symlink():
            if target.is_symlink():
                existing_target = Path(os.readlink(str(target))).resolve()
                if existing_target == source:
                    # Already correct symlink
                    if dry_run:
                        print(f"  {color('OK', GREEN)}       {color(label, DIM)}")
                    return

                # Symlink pointing elsewhere
                if dry_run:
                    print(f"  {color('RELINK', YELLOW)}   {label} {color(f'(currently -> {existing_target})', DIM)}")
                    if not self.force:
                        print(f"           {color('^ would skip (force=False)', DIM)}")
                    return
                if self.force:
                    target.unlink()
                else:
                    print(f"{color('Warning:', YELLOW)} {target} is already a symlink to {existing_target}, skipping (use force=True to overwrite)")
                    return
            else:
                # Regular file or directory
                kind = "directory" if target.is_dir() else "file"
                if dry_run:
                    if self.force:
                        print(f"  {color('REPLACE', YELLOW)}  {label} {color(f'(existing {kind} -> symlink)', DIM)}")
                    else:
                        print(f"  {color('CONFLICT', RED)} {label} {color(f'(existing {kind}, would skip)', DIM)}")
                    return
                if self.force:
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                else:
                    print(f"{color('Warning:', YELLOW)} {target} already exists and is not a symlink, skipping (use force=True to overwrite)")
                    return
        else:
            # Target doesn't exist — will create
            if dry_run:
                print(f"  {color('CREATE', GREEN)}   {color(label, BOLD)} -> {source}")
                return

        # Create parent directories and symlink
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source)
