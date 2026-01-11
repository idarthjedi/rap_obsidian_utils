"""
rap_obsidian_utils - Utilities for Obsidian markdown front matter management.
"""

from rap_obsidian_utils.cli import (
    main,
    MarkdownMetadata,
    ValidationResult,
    extract_metadata_from_markdown,
    add_title_to_frontmatter,
    validate_frontmatter,
    clean_to_ascii,
    normalize_date,
)

from rap_obsidian_utils.sync import (
    sync_main,
)

__version__ = "0.1.0"

__all__ = [
    # Frontmatter utility
    "main",
    "MarkdownMetadata",
    "ValidationResult",
    "extract_metadata_from_markdown",
    "add_title_to_frontmatter",
    "validate_frontmatter",
    "clean_to_ascii",
    "normalize_date",
    # Sync utility
    "sync_main",
]
