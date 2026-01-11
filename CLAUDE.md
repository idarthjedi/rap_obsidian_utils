# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

rap_obsidian_utils is a collection of utilities for working with Obsidian markdown files:

| Utility | Purpose |
|---------|---------|
| `obsidian-frontmatter` | Extract metadata and add Obsidian-compatible YAML front matter |
| `obsidian-sync` | Sync changed markdown files between directories |

## Documentation

### Wiki (User-Facing Documentation)

The RAP Framework Wiki contains user-facing documentation for this project:
- **Location:** `~/development/anthropics/projects/rap_framework.wiki/`
- **URL:** https://github.com/idarthjedi/rap_framework/wiki

**When to update the wiki:**
- Adding or changing CLI options
- Modifying metadata extraction rules
- Changing front matter output format
- Adding new field types or wiki-link formats
- Updating installation procedures

**Wiki pages for this project:**

| Change Type | Wiki Page(s) to Update |
|-------------|------------------------|
| CLI options | `CLI-Reference.md` |
| Installation/setup | `Installation.md` |
| Metadata parsing | `Metadata-Extraction.md`, `Obsidian-Utils-Overview.md` |
| Front matter format | `Front-Matter-Format.md`, `Configuration.md` |
| Architecture changes | `System-Overview.md`, `Data-Flow.md` |

### Documentation Map

| Topic | Location | Audience |
|-------|----------|----------|
| User guide, CLI reference | [RAP Framework Wiki](https://github.com/idarthjedi/rap_framework/wiki) | Users |
| Implementation details | This file (`CLAUDE.md`) | Developers |

## Commands

```bash
# Install dependencies
uv pip install -e .

# obsidian-frontmatter: Add front matter to markdown files
uv run obsidian-frontmatter -o <output_dir> <file.md>
uv run obsidian-frontmatter -o <output_dir> -n <file.md>  # dry run (preview only)
uv run obsidian-frontmatter -o <output_dir> -v <file.md>  # verbose output

# obsidian-sync: Sync changed markdown files between directories
uv run obsidian-sync <source_dir> <dest_dir>
uv run obsidian-sync -n <source_dir> <dest_dir>  # dry run (preview only)
uv run obsidian-sync -v <source_dir> <dest_dir>  # verbose output
```

## Architecture

### obsidian-frontmatter

#### Core Data Flow

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

#### Output Format

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

### obsidian-sync

#### Sync Algorithm

1. **Discover**: `find_markdown_files(source_dir)` → list of `.md` files
   - Recursively finds all markdown files
   - Skips symlinks

2. **Plan**: `build_sync_plan(source_dir, dest_dir)` → `(candidates, skipped)`
   - For each source file, determines if sync is needed
   - Uses `should_sync_file()` for change detection

3. **Execute**: `execute_sync(candidates, dry_run)` → `SyncResult`
   - Creates destination directories as needed
   - Copies files with `shutil.copy2()` (preserves metadata)

#### Change Detection

`should_sync_file(source, dest)` returns `(should_sync, reason)`:

| Condition | Result |
|-----------|--------|
| Dest doesn't exist | `(True, NEW_FILE)` |
| Source mtime > dest mtime | `(True, MTIME_NEWER)` |
| Mtimes equal (±1s), hashes differ | `(True, CONTENT_CHANGED)` |
| Otherwise | `(False, None)` |

#### Key Functions

- `compute_file_hash()`: SHA-256 hash in 8KB chunks (memory efficient)
- `should_sync_file()`: Change detection logic
- `build_sync_plan()`: Determines what needs syncing
- `execute_sync()`: Performs the copy operations

## Dependencies

- **click**: CLI framework
- **rich**: Terminal formatting (tables, panels, syntax highlighting)
