# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

rap_obsidian_utils is a collection of utilities for working with Obsidian markdown files. The primary tool extracts metadata from markdown content and adds/updates YAML front matter with Obsidian-compatible wiki-links (`[[...]]` format).

## Commands

```bash
# Install dependencies
uv pip install -e .

# Run the CLI utility
uv run obsidian-frontmatter -o <output_dir> <file.md>
uv run obsidian-frontmatter -o <output_dir> -n <file.md>  # dry run (preview only)
uv run obsidian-frontmatter -o <output_dir> -v <file.md>  # verbose output
```

## Architecture

### Core Data Flow

1. **Extract**: `extract_metadata_from_markdown(content)` → `MarkdownMetadata`
   - Parses H1 heading as title
   - Parses `**Author(s):**`, `**Publication:**`, `**Date:**` lines
   - Splits authors on `,`, `;`, `&`, or ` and `

2. **Transform**: `add_title_to_frontmatter(content, metadata)` → modified content
   - Adds Title, Authors (as wiki-links), Book (as wiki-link), Date to YAML front matter
   - Preserves existing front matter fields (e.g., `sourcehash`)

3. **Validate**: `validate_frontmatter(content, metadata)` → `ValidationResult`
   - Verifies all fields were correctly added
   - Returns errors (blocking) and warnings (informational)

### Key Functions

- `clean_to_ascii()`: Replaces non-ASCII dashes/spaces with ASCII equivalents before stripping
- `normalize_date()`: Handles various date formats (month ranges, seasons, quarters, numeric)

### Expected Input Format

```markdown
---
sourcehash: ...
---
# Document Title

**Author(s):** Author Name
**Publication:** Publication Name
**Date:** Date String
```

### Output Format

```yaml
---
Title: "Document Title"
Authors:
  - "[[Author Name]]"
Book: "[[Publication Name]]"
Date: "Date String"
sourcehash: ...
---
```

## Dependencies

- **click**: CLI framework
- **rich**: Terminal formatting (tables, panels, syntax highlighting)
