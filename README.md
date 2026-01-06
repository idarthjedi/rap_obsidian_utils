# RAP Obsidian Utils

A CLI tool to extract metadata from markdown files and add/update YAML front matter with Obsidian-compatible wiki-links.

---

## Why RAP Obsidian Utils?

When processing academic papers through RAP, the generated markdown needs proper front matter for Obsidian:

- Extract title, authors, publication, and date from markdown content
- Format as Obsidian wiki-links (`[[Author Name]]`, `[[Publication]]`)
- Preserve existing front matter fields (like `sourcehash`)

---

## Quick Start

**Requirements:** Python 3.12+, [UV](https://docs.astral.sh/uv/)

```bash
# Clone and install
git clone https://github.com/idarthjedi/rap_obsidian_utils.git
cd rap_obsidian_utils
uv sync

# Process a markdown file
uv run obsidian-frontmatter -o ./output paper.md
```

---

## Usage

```bash
# Process file to output directory
uv run obsidian-frontmatter -o <output_dir> <file.md>

# Dry run (preview without writing)
uv run obsidian-frontmatter -o <output_dir> -n <file.md>

# Verbose output
uv run obsidian-frontmatter -o <output_dir> -v <file.md>
```

---

## Key Features

- **Metadata extraction** — Title from H1, authors, publication, date
- **Wiki-link formatting** — Obsidian-compatible `[[...]]` syntax
- **Smart author parsing** — Splits on `,`, `;`, `&`, or `and`
- **Date normalization** — Handles ranges, seasons, quarters
- **Front matter preservation** — Keeps existing fields intact

---

## Documentation

**Full documentation is available in the [RAP Framework Wiki](https://github.com/idarthjedi/rap_framework/wiki):**

| Topic | Wiki Page |
|-------|-----------|
| Overview | [Obsidian Utils Overview](https://github.com/idarthjedi/rap_framework/wiki/Obsidian-Utils-Overview) |
| Metadata Parsing | [Metadata Extraction](https://github.com/idarthjedi/rap_framework/wiki/Metadata-Extraction) |
| Output Format | [Front Matter Format](https://github.com/idarthjedi/rap_framework/wiki/Front-Matter-Format) |
| CLI Reference | [CLI Reference](https://github.com/idarthjedi/rap_framework/wiki/CLI-Reference) |

**For developers:** See `CLAUDE.md` for implementation details.

---

## License

AGPL-3.0 - See [LICENSE](LICENSE) for details.
