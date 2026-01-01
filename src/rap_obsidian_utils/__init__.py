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

__version__ = "0.1.0"

__all__ = [
    "main",
    "MarkdownMetadata",
    "ValidationResult",
    "extract_metadata_from_markdown",
    "add_title_to_frontmatter",
    "validate_frontmatter",
    "clean_to_ascii",
    "normalize_date",
]
