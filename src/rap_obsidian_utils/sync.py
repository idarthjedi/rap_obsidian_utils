#!/usr/bin/env python3
"""
Obsidian Sync Utility

A CLI tool to synchronize markdown files between directories,
copying only files that have changed.
"""

import hashlib
import shutil
import sys
from enum import Enum, auto
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


# Initialize Rich console
console = Console()
error_console = Console(stderr=True)

# Constants
CHUNK_SIZE = 8192  # 8KB chunks for hashing
MTIME_TOLERANCE = 1.0  # 1 second tolerance for mtime comparison


class SyncReason(Enum):
    """Reason why a file was marked for sync."""
    NEW_FILE = auto()
    MTIME_NEWER = auto()
    CONTENT_CHANGED = auto()


class SyncCandidate(NamedTuple):
    """A file that should be synced."""
    source_path: Path
    dest_path: Path
    relative_path: Path
    reason: SyncReason


class SyncResult(NamedTuple):
    """Result of a sync operation."""
    synced_files: List[SyncCandidate]
    skipped_files: List[Path]
    errors: List[Tuple[Path, str]]


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Uses chunked reading for memory efficiency with large files.
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(CHUNK_SIZE):
            sha256.update(chunk)
    return sha256.hexdigest()


def should_sync_file(source: Path, dest: Path) -> Tuple[bool, Optional[SyncReason]]:
    """
    Determine if a file should be synced based on mtime and hash.

    Returns:
        Tuple of (should_sync, reason) where reason is None if should_sync is False.
    """
    # If destination doesn't exist, definitely sync
    if not dest.exists():
        return (True, SyncReason.NEW_FILE)

    source_mtime = source.stat().st_mtime
    dest_mtime = dest.stat().st_mtime

    # If source is newer, sync
    if source_mtime > dest_mtime + MTIME_TOLERANCE:
        return (True, SyncReason.MTIME_NEWER)

    # If mtimes are approximately equal, compare hashes
    if abs(source_mtime - dest_mtime) <= MTIME_TOLERANCE:
        source_hash = compute_file_hash(source)
        dest_hash = compute_file_hash(dest)
        if source_hash != dest_hash:
            return (True, SyncReason.CONTENT_CHANGED)

    # Destination is newer or content is identical
    return (False, None)


def find_markdown_files(source_dir: Path) -> List[Path]:
    """
    Recursively find all markdown files in a directory.

    Returns list of absolute paths to .md files.
    """
    return sorted(source_dir.rglob("*.md"))


def build_sync_plan(
    source_dir: Path,
    dest_dir: Path
) -> Tuple[List[SyncCandidate], List[Path]]:
    """
    Build list of files that need syncing.

    Returns:
        Tuple of (candidates_to_sync, skipped_files)
    """
    candidates = []
    skipped = []

    for source_path in find_markdown_files(source_dir):
        # Skip symlinks
        if source_path.is_symlink():
            continue

        # Compute relative path and destination
        relative_path = source_path.relative_to(source_dir)
        dest_path = dest_dir / relative_path

        should_sync, reason = should_sync_file(source_path, dest_path)

        if should_sync and reason is not None:
            candidates.append(SyncCandidate(
                source_path=source_path,
                dest_path=dest_path,
                relative_path=relative_path,
                reason=reason
            ))
        else:
            skipped.append(relative_path)

    return candidates, skipped


def execute_sync(
    candidates: List[SyncCandidate],
    dry_run: bool = False
) -> SyncResult:
    """
    Execute the sync operation.

    Creates destination directories as needed and copies files.
    Uses shutil.copy2() to preserve file metadata.
    """
    synced = []
    errors = []

    for candidate in candidates:
        if dry_run:
            synced.append(candidate)
            continue

        try:
            # Create destination directory if needed
            candidate.dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file with metadata
            shutil.copy2(candidate.source_path, candidate.dest_path)
            synced.append(candidate)

        except Exception as e:
            errors.append((candidate.source_path, str(e)))

    return SyncResult(
        synced_files=synced,
        skipped_files=[],  # Already tracked in build_sync_plan
        errors=errors
    )


def reason_to_string(reason: SyncReason) -> str:
    """Convert SyncReason to human-readable string."""
    return {
        SyncReason.NEW_FILE: "new",
        SyncReason.MTIME_NEWER: "modified",
        SyncReason.CONTENT_CHANGED: "content changed",
    }.get(reason, "unknown")


def display_sync_plan(candidates: List[SyncCandidate], verbose: bool) -> None:
    """Display the sync plan in a table."""
    if not candidates:
        console.print("[dim]No files to sync.[/dim]")
        return

    table = Table(
        title=f"Files to Sync ({len(candidates)})",
        show_header=True,
        header_style="bold cyan"
    )
    table.add_column("File", style="green")
    table.add_column("Reason", style="yellow", width=15)

    for candidate in candidates:
        table.add_row(
            str(candidate.relative_path),
            reason_to_string(candidate.reason)
        )

    console.print(table)


def display_sync_summary(
    result: SyncResult,
    skipped_count: int,
    dry_run: bool
) -> None:
    """Display a summary of the sync operation."""
    action = "Would sync" if dry_run else "Synced"

    summary_parts = [
        f"[green]{action}: {len(result.synced_files)} file(s)[/green]",
        f"[dim]Skipped: {skipped_count} file(s)[/dim]",
    ]

    if result.errors:
        summary_parts.append(f"[red]Errors: {len(result.errors)}[/red]")

    console.print(Panel(
        "\n".join(summary_parts),
        title="Sync Summary",
        border_style="cyan"
    ))

    # Display errors if any
    if result.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for path, error in result.errors:
            console.print(f"  [red]{path}:[/red] {error}")


@click.command()
@click.argument('source_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('dest_dir', type=click.Path(file_okay=False, dir_okay=True))
@click.option('--dry-run', '-n', is_flag=True,
              help="Preview changes without copying files")
@click.option('--verbose', '-v', is_flag=True,
              help="Show detailed output including file list")
@click.option('--quiet', '-q', is_flag=True,
              help="Suppress output except errors")
def sync_main(
    source_dir: str,
    dest_dir: str,
    dry_run: bool,
    verbose: bool,
    quiet: bool
) -> None:
    """
    Obsidian Sync Utility

    Synchronizes markdown files from SOURCE_DIR to DEST_DIR,
    copying only files that have changed.

    \b
    CHANGE DETECTION:
      1. New files (don't exist in destination) are copied
      2. Files with newer mtime in source are copied
      3. If mtimes match, content hash is compared

    \b
    NOTES:
      - Only .md files are synced
      - Directory structure is preserved
      - Files are never deleted from destination

    \b
    EXAMPLES:
      obsidian-sync ~/notes ~/backup
      obsidian-sync -n ~/notes ~/backup   # dry run
      obsidian-sync -v ~/notes ~/backup   # verbose
    """
    # Expand user paths (handle ~)
    source_path = Path(source_dir).expanduser().resolve()
    dest_path = Path(dest_dir).expanduser().resolve()

    if not quiet:
        console.print(f"[bold]Source:[/bold] {source_path}")
        console.print(f"[bold]Destination:[/bold] {dest_path}")
        if dry_run:
            console.print("[yellow]Dry run mode - no files will be copied[/yellow]")
        console.print()

    # Build sync plan
    try:
        candidates, skipped = build_sync_plan(source_path, dest_path)
    except Exception as e:
        error_console.print(f"[bold red]Error scanning files:[/bold red] {e}")
        sys.exit(1)

    # Show what will be synced
    if verbose or dry_run:
        display_sync_plan(candidates, verbose)
        if candidates:
            console.print()

    # Execute sync
    if not candidates:
        if not quiet:
            console.print("[green]All files are up to date.[/green]")
        return

    result = execute_sync(candidates, dry_run)

    # Display summary
    if not quiet:
        display_sync_summary(result, len(skipped), dry_run)

    # Exit with error code if there were errors
    if result.errors:
        sys.exit(1)


if __name__ == "__main__":
    sync_main()
