"""SymlinkResource - creates symlinks from source to target."""

from __future__ import annotations

import difflib
import filecmp
import os
import shutil
from pathlib import Path

from pyhomedot.color import BOLD, CYAN, DIM, GREEN, RED, YELLOW, color
from pyhomedot.resources.base import Resource

_FORCE_SENTINEL: object = object()


def _contents_match(a: Path, b: Path) -> bool:
    """Check if two paths have identical content (works for files and directories)."""
    if a.is_file() and b.is_file():
        return filecmp.cmp(a, b, shallow=False)
    if a.is_dir() and b.is_dir():
        dcmp = filecmp.dircmp(a, b, ignore=[".git", ".jj", ".DS_Store", "node_modules", "__pycache__"])
        if dcmp.left_only or dcmp.right_only or dcmp.diff_files:
            return False
        return all(_contents_match(a / sub, b / sub) for sub in dcmp.common_dirs)
    return False


def _read_text_safe(path: Path) -> str | None:
    """Read file as text, return None if binary or unreadable."""
    try:
        return path.read_text(encoding="utf-8", errors="strict")
    except (UnicodeDecodeError, OSError):
        return None


def _show_file_diff(existing: Path, source: Path, label: str) -> None:
    """Show a unified diff between existing file and source file."""
    existing_text = _read_text_safe(existing)
    source_text = _read_text_safe(source)

    if existing_text is None or source_text is None:
        print(f"    {color('(binary or unreadable — cannot show diff)', DIM)}")
        return

    diff = list(
        difflib.unified_diff(
            existing_text.splitlines(keepends=True),
            source_text.splitlines(keepends=True),
            fromfile=f"current: ~/{label}",
            tofile=f"repo: {source}",
        )
    )
    if not diff:
        print(f"    {color('(files are identical)', DIM)}")
        return

    for line in diff:
        line = line.rstrip("\n")
        if line.startswith("+++") or line.startswith("---"):
            print(f"    {color(line, BOLD)}")
        elif line.startswith("+"):
            print(f"    {color(line, GREEN)}")
        elif line.startswith("-"):
            print(f"    {color(line, RED)}")
        elif line.startswith("@@"):
            print(f"    {color(line, CYAN)}")
        else:
            print(f"    {line}")


def _show_dir_diff(existing: Path, source: Path) -> None:
    """Show a summary and file-level diffs for two directories."""
    ignore = {".git", ".jj", ".DS_Store", "node_modules", "__pycache__"}
    existing_files = {
        p.relative_to(existing)
        for p in existing.rglob("*")
        if p.is_file() and not (set(p.parts) & ignore)
    }
    source_files = {
        p.relative_to(source)
        for p in source.rglob("*")
        if p.is_file() and not (set(p.parts) & ignore)
    }

    only_existing = sorted(existing_files - source_files)
    only_source = sorted(source_files - existing_files)
    common = sorted(existing_files & source_files)

    if only_existing:
        print(f"    {color('Only in current:', YELLOW)}")
        for f in only_existing:
            print(f"      {f}")
    if only_source:
        print(f"    {color('Only in repo:', GREEN)}")
        for f in only_source:
            print(f"      {f}")

    differing = [f for f in common if not filecmp.cmp(existing / f, source / f, shallow=False)]
    if differing:
        print(f"    {color('Files with differences:', CYAN)}")
        for f in differing:
            print(f"      {color(str(f), BOLD)}:")
            _show_file_diff(existing / f, source / f, str(f))

    if not only_existing and not only_source and not differing:
        print(f"    {color('(directories are identical)', DIM)}")


class SymlinkResource(Resource):
    """Creates symlinks from source files/directories to target locations relative to $HOME."""

    def __init__(
        self,
        source: str,
        target: str,
        *,
        force: bool | object = _FORCE_SENTINEL,
        source_root: Path | None = None,
        home_dir: Path | None = None,
    ) -> None:
        self.source = source
        self.target = target
        self._force_explicit = force is not _FORCE_SENTINEL
        self.force = bool(force) if force is not _FORCE_SENTINEL else False
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

    def _apply_cli_force(self, cli_force: bool) -> None:
        """Apply CLI --force flag if force wasn't explicitly set in code."""
        if not self._force_explicit and cli_force:
            self.force = True

    def generate(self, *, dry_run: bool = False, show_diff: bool = False) -> None:
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
                identical = _contents_match(target, source)
                if dry_run:
                    if identical:
                        print(f"  {color('IDENTICAL', CYAN)} {label} {color(f'(existing {kind}, same content — safe to replace)', DIM)}")
                    elif self.force:
                        print(f"  {color('REPLACE', YELLOW)}  {label} {color(f'(existing {kind} -> symlink)', DIM)}")
                    else:
                        print(f"  {color('CONFLICT', RED)} {label} {color(f'(existing {kind}, would skip)', DIM)}")
                    if show_diff and not identical:
                        if target.is_dir():
                            _show_dir_diff(target, source)
                        else:
                            _show_file_diff(target, source, self.target)
                    return
                if self.force or identical:
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
