# rap_obsidian_utils

A CLI tool to extract metadata from markdown files and add/update YAML front matter with Obsidian-compatible wiki-links.

## Installation

Requires Python 3.12+

```bash
# Clone the repository
git clone git@github.com:idarthjedi/rap_obsidian_utils.git
cd rap_obsidian_utils

# Install with uv
uv pip install -e .
```

## Usage

```bash
# Process a markdown file (output to specified directory)
uv run obsidian-frontmatter -o <output_dir> <file.md>

# Preview changes without writing (dry run)
uv run obsidian-frontmatter -o <output_dir> -n <file.md>

# Verbose output with metadata table
uv run obsidian-frontmatter -o <output_dir> -v <file.md>
```

The `-o/--output-dir` parameter is required. The processed file is written to the output directory with the same filename as the input file. The output directory is created if it doesn't exist.

## Expected Input Format

The tool expects markdown files with this structure:

```markdown
---
sourcehash: ...
---
# Document Title

**Author(s):** Author Name, Another Author
**Publication:** Publication Name
**Date:** March-April 2023
```

## Output Format

The tool adds Obsidian-compatible front matter:

```yaml
---
Title: "Document Title"
Authors:
  - "[[Author Name]]"
  - "[[Another Author]]"
Book: "[[Publication Name]]"
Date: "March-April 2023"
sourcehash: ...
---
```

## Features

- Extracts title from H1 heading
- Parses multiple authors (splits on `,`, `;`, `&`, or `and`)
- Formats authors and publication as Obsidian wiki-links (`[[...]]`)
- Normalizes date formats (month ranges, seasons, quarters, various formats)
- Preserves existing front matter fields
- Validates output before writing
- Rich terminal output with syntax highlighting

## Dependencies

- [click](https://click.palletsprojects.com/) - CLI framework
- [rich](https://rich.readthedocs.io/) - Terminal formatting

## License

AGPL-3.0 - See [LICENSE](LICENSE) for details.
