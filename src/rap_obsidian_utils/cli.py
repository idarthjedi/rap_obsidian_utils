#!/usr/bin/env python3
"""
Obsidian Front Matter Utility

A CLI tool to extract metadata from markdown files and add/update
YAML front matter with Obsidian-compatible wiki-links.
"""

import re
import sys
import calendar
from pathlib import Path
from typing import List, NamedTuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


# Initialize Rich console
console = Console()
error_console = Console(stderr=True)


class MarkdownMetadata(NamedTuple):
    """Container for extracted markdown metadata."""
    title: str
    authors: List[str]
    book: str
    publication_date: str


def clean_to_ascii(text: str) -> str:
    """
    Remove non-ASCII characters from a string, but first replace
    common non-ASCII punctuation with ASCII equivalents.
    """
    # Replace common non-ASCII characters with ASCII equivalents
    replacements = {
        # Dashes
        '\u2013': '-',  # en-dash
        '\u2014': '-',  # em-dash
        '\u2010': '-',  # hyphen
        '\u2011': '-',  # non-breaking hyphen
        '\u2012': '-',  # figure dash
        '\u2015': '-',  # horizontal bar
        '\u00ad': '',   # soft hyphen (remove)
        # Spaces
        '\u00a0': ' ',  # non-breaking space
        '\u2002': ' ',  # en space
        '\u2003': ' ',  # em space
        '\u2009': ' ',  # thin space
        '\u200a': ' ',  # hair space
        '\u200b': '',   # zero-width space (remove)
        '\u202f': ' ',  # narrow no-break space
        '\u205f': ' ',  # medium mathematical space
        '\u3000': ' ',  # ideographic space
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    return ''.join(char for char in text if ord(char) < 128)


def normalize_date(date_str: str) -> str:
    """
    Attempts to normalize a date string into a consistent format.
    Returns the original string if it can't be parsed (e.g., "not specified").

    Handles formats like:
        - "May 2015", "March-April 2023", "Jan 2020"
        - "2015", "2023"
        - "05/2015", "5/2015", "2015-05"
        - "May 1, 2015", "1 May 2015"
        - "Spring 2023", "Q1 2023"
        - "not specified", "unknown", etc.
    """
    if not date_str:
        return ""

    # Clean and normalize whitespace
    cleaned = clean_to_ascii(date_str).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)

    # Check for non-date indicators
    non_date_patterns = ['not specified', 'unknown', 'n/a', 'none', 'tbd', 'undated']
    if cleaned.lower() in non_date_patterns or not cleaned:
        return cleaned

    # Month name mappings (handles abbreviations)
    month_names = {
        'jan': 'January', 'january': 'January',
        'feb': 'February', 'february': 'February',
        'mar': 'March', 'march': 'March',
        'apr': 'April', 'april': 'April',
        'may': 'May',
        'jun': 'June', 'june': 'June',
        'jul': 'July', 'july': 'July',
        'aug': 'August', 'august': 'August',
        'sep': 'September', 'sept': 'September', 'september': 'September',
        'oct': 'October', 'october': 'October',
        'nov': 'November', 'november': 'November',
        'dec': 'December', 'december': 'December'
    }

    # Season/quarter mappings
    season_map = {
        'spring': 'Spring', 'summer': 'Summer',
        'fall': 'Fall', 'autumn': 'Fall', 'winter': 'Winter',
        'q1': 'Q1', 'q2': 'Q2', 'q3': 'Q3', 'q4': 'Q4'
    }

    # Try to extract year (4 digits)
    year_match = re.search(r'\b(19|20)\d{2}\b', cleaned)
    year = year_match.group(0) if year_match else None

    if not year:
        return cleaned

    # Check for month range (e.g., "March-April 2023", "Jan/Feb 2020")
    range_pattern = r'([A-Za-z]+)\s*[-/]\s*([A-Za-z]+)\s*(\d{4})?'
    range_match = re.search(range_pattern, cleaned, re.IGNORECASE)
    if range_match:
        month1_raw = range_match.group(1).lower()
        month2_raw = range_match.group(2).lower()
        if month1_raw in month_names and month2_raw in month_names:
            month1 = month_names[month1_raw]
            month2 = month_names[month2_raw]
            return f"{month1}-{month2} {year}"

    # Check for season/quarter + year
    for season_key, season_name in season_map.items():
        if season_key in cleaned.lower():
            return f"{season_name} {year}"

    # Check for "Month Year" format
    month_year_pattern = r'([A-Za-z]+)\s*,?\s*(\d{4})'
    month_year_match = re.search(month_year_pattern, cleaned)
    if month_year_match:
        month_raw = month_year_match.group(1).lower()
        if month_raw in month_names:
            return f"{month_names[month_raw]} {year}"

    # Check for "Month Day, Year" or "Day Month Year" format
    full_date_patterns = [
        r'([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})',
        r'(\d{1,2})\s+([A-Za-z]+)\s*,?\s*(\d{4})',
    ]
    for pattern in full_date_patterns:
        match = re.search(pattern, cleaned)
        if match:
            groups = match.groups()
            for g in groups:
                if g.lower() in month_names:
                    return f"{month_names[g.lower()]} {year}"

    # Check for numeric formats: MM/YYYY, YYYY-MM, MM-YYYY
    numeric_patterns = [
        (r'(\d{1,2})[/-](\d{4})', 1),
        (r'(\d{4})[/-](\d{1,2})', 2),
    ]
    for pattern, month_group in numeric_patterns:
        match = re.search(pattern, cleaned)
        if match:
            month_num = int(match.group(month_group))
            if 1 <= month_num <= 12:
                month_name = calendar.month_name[month_num]
                return f"{month_name} {year}"

    # If only year found, return just the year
    if re.fullmatch(r'\s*(19|20)\d{2}\s*', cleaned):
        return year

    return cleaned


def extract_metadata_from_markdown(content: str) -> MarkdownMetadata:
    """
    Extracts title, authors, book/publication name, and date from markdown content.

    Expected format:
        ---
        sourcehash: ...
        ---
        # Title Here

        **Author(s):** Author1, Author2
        **Publication:** Book or Publication Name
        **Date:** Date String
    """
    # Extract title from first H1 heading (# Title)
    title_match = re.search(r'^#\s+(.+?)(?:\s*$|\s*\n)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""

    # Extract authors from **Author(s):** line
    authors_match = re.search(r'\*\*Author\(s\):\*\*\s*(.+?)(?:\s*$|\s*\n)', content, re.MULTILINE)
    authors_str = authors_match.group(1).strip() if authors_match else ""
    # Split authors by comma, semicolon, ampersand, or " and " and clean up
    authors = [a.strip() for a in re.split(r'[,;&]|\s+and\s+', authors_str) if a.strip()]

    # Extract publication/book from **Publication:** line
    pub_match = re.search(r'\*\*Publication:\*\*\s*(.+?)(?:\s*$|\s*\n)', content, re.MULTILINE)
    book = pub_match.group(1).strip() if pub_match else ""

    # Extract date from **Date:** line, clean to ASCII, and normalize
    date_match = re.search(r'\*\*Date:\*\*\s*(.+?)(?:\s*$|\s*\n)', content, re.MULTILINE)
    raw_date = date_match.group(1).strip() if date_match else ""
    publication_date = normalize_date(raw_date)

    return MarkdownMetadata(
        title=title,
        authors=authors,
        book=book,
        publication_date=publication_date
    )


def add_title_to_frontmatter(content: str, metadata: MarkdownMetadata) -> str:
    """
    Adds metadata fields to the YAML front matter of markdown content.
    Preserves any existing front matter content.
    """
    # Regex to match YAML front matter between --- delimiters at the start
    frontmatter_pattern = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
    match = frontmatter_pattern.match(content)

    # Build the new front matter fields
    # Format authors as Obsidian wiki-links
    authors_yaml = "\n".join(f'  - "[[{author}]]"' for author in metadata.authors)

    new_fields = f'''Title: "{metadata.title}"
Authors:
{authors_yaml}
Book: "[[{metadata.book}]]"
Date: "{metadata.publication_date}"'''

    if match:
        # Get existing front matter content
        existing_yaml = match.group(1).strip()

        # Combine new fields with existing content
        combined_yaml = f"{new_fields}\n{existing_yaml}"

        # Rebuild the content with updated front matter
        new_content = f"---\n{combined_yaml}\n---{content[match.end():]}"
        return new_content
    else:
        # No front matter found, create new one
        new_frontmatter = f"---\n{new_fields}\n---\n"
        return new_frontmatter + content


class ValidationResult(NamedTuple):
    """Result of front matter validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


def validate_frontmatter(content: str, metadata: MarkdownMetadata) -> ValidationResult:
    """
    Validates that the front matter was correctly added to the content.

    Checks:
    - Front matter delimiters exist
    - Title field is present and matches
    - Authors field is present with correct wiki-link format
    - Book field is present with correct wiki-link format
    - Date field is present and matches
    """
    errors = []
    warnings = []

    # Check for front matter delimiters
    frontmatter_pattern = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
    match = frontmatter_pattern.match(content)

    if not match:
        errors.append("Front matter delimiters (---) not found at start of file")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    frontmatter = match.group(1)

    # Check Title
    title_match = re.search(r'^Title:\s*"(.+?)"', frontmatter, re.MULTILINE)
    if not title_match:
        errors.append("Title field not found in front matter")
    elif title_match.group(1) != metadata.title:
        errors.append(f"Title mismatch: expected '{metadata.title}', found '{title_match.group(1)}'")

    # Check Authors
    if 'Authors:' not in frontmatter:
        errors.append("Authors field not found in front matter")
    else:
        for author in metadata.authors:
            expected_author = f'"[[{author}]]"'
            if expected_author not in frontmatter:
                errors.append(f"Author '{author}' not found in expected format {expected_author}")

    # Check Book
    expected_book = f'Book: "[[{metadata.book}]]"'
    if expected_book not in frontmatter:
        book_match = re.search(r'^Book:\s*(.+?)$', frontmatter, re.MULTILINE)
        if not book_match:
            errors.append("Book field not found in front matter")
        else:
            errors.append(f"Book field format incorrect: expected '{expected_book}'")

    # Check Date
    date_match = re.search(r'^Date:\s*"(.+?)"', frontmatter, re.MULTILINE)
    if not date_match:
        errors.append("Date field not found in front matter")
    elif date_match.group(1) != metadata.publication_date:
        warnings.append(f"Date value: '{date_match.group(1)}' (normalized from original)")

    # Warnings for potential issues
    if not metadata.title:
        warnings.append("Title is empty - could not extract from markdown")
    if not metadata.authors:
        warnings.append("No authors found - could not extract from markdown")
    if not metadata.book:
        warnings.append("Book/Publication is empty - could not extract from markdown")
    if not metadata.publication_date:
        warnings.append("Date is empty - could not extract from markdown")

    is_valid = len(errors) == 0
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def display_metadata_table(metadata: MarkdownMetadata) -> None:
    """Display extracted metadata in a formatted table."""
    table = Table(title="Extracted Metadata", show_header=True, header_style="bold cyan")
    table.add_column("Field", style="dim", width=12)
    table.add_column("Value", style="green")

    table.add_row("Title", metadata.title or "[dim italic]empty[/]")
    table.add_row("Authors", ", ".join(metadata.authors) if metadata.authors else "[dim italic]empty[/]")
    table.add_row("Book", metadata.book or "[dim italic]empty[/]")
    table.add_row("Date", metadata.publication_date or "[dim italic]empty[/]")

    console.print(table)


def display_frontmatter_preview(content: str) -> None:
    """Display a preview of the front matter."""
    frontmatter_pattern = re.compile(r'^(---\n.*?\n---)', re.DOTALL)
    match = frontmatter_pattern.match(content)

    if match:
        frontmatter = match.group(1)
        syntax = Syntax(frontmatter, "yaml", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Front Matter Preview", border_style="green"))


def display_validation_result(result: ValidationResult) -> None:
    """Display validation results with appropriate styling."""
    if result.is_valid:
        console.print("[bold green]Validation passed.[/bold green]")
    else:
        console.print("[bold red]Validation failed![/bold red]")

    if result.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in result.errors:
            console.print(f"  [red]{error}[/red]")

    if result.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in result.warnings:
            console.print(f"  [yellow]{warning}[/yellow]")


@click.command()
@click.argument('filename', type=click.Path(exists=True), required=False)
@click.option('--output-dir', '-o', type=click.Path(), required=True,
              help="Output directory for processed files")
@click.option('--dry-run', '-n', is_flag=True, help="Preview changes without writing to file")
@click.option('--verbose', '-v', is_flag=True, help="Show detailed output")
@click.option('--quiet', '-q', is_flag=True, help="Suppress output except errors")
def main(filename: str, output_dir: str, dry_run: bool, verbose: bool, quiet: bool) -> None:
    """
    Obsidian Front Matter Utility

    Extracts metadata from markdown files and adds/updates YAML front matter
    with Obsidian-compatible wiki-links. Writes output to a separate directory.

    \b
    USAGE:
        obsidian-frontmatter -o <output_dir> <filename>
        obsidian-frontmatter -o <output_dir> -n <filename>  # dry run
        obsidian-frontmatter -o <output_dir> -v <filename>  # verbose

    \b
    EXPECTED MARKDOWN FORMAT:
        ---
        sourcehash: ...
        ---
        # Document Title

        **Author(s):** Author Name
        **Publication:** Publication Name
        **Date:** Date String

    \b
    OUTPUT FORMAT:
        ---
        Title: "Document Title"
        Authors:
          - "[[Author Name]]"
        Book: "[[Publication Name]]"
        Date: "Date String"
        sourcehash: ...
        ---
    """
    # Show help if no filename provided
    if not filename:
        console.print(Panel.fit(
            "[bold cyan]Obsidian Front Matter Utility[/bold cyan]\n\n"
            "Extract metadata from markdown files and add/update\n"
            "YAML front matter with Obsidian-compatible wiki-links.\n\n"
            "[dim]Run with --help for full usage information.[/dim]",
            title="Welcome",
            border_style="cyan"
        ))

        # Show quick usage examples
        console.print("\n[bold]Quick Start:[/bold]")
        console.print("  [cyan]obsidian-frontmatter[/cyan] [yellow]-o <output_dir>[/yellow] [green]<file.md>[/green]")
        console.print("  [cyan]obsidian-frontmatter[/cyan] [yellow]-o <output_dir> -n[/yellow] [green]<file.md>[/green]  [dim]# dry run[/dim]")
        console.print("  [cyan]obsidian-frontmatter[/cyan] [yellow]--help[/yellow]")
        console.print()
        sys.exit(0)

    file_path = Path(filename)
    output_path = Path(output_dir)

    # Create output directory if it doesn't exist
    if not dry_run:
        output_path.mkdir(parents=True, exist_ok=True)

    # Determine output file path (same filename in output directory)
    output_file = output_path / file_path.name

    if not quiet:
        console.print(f"[bold]Processing:[/bold] {file_path.name}")

    # Read the file
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        error_console.print(f"[bold red]Error reading file:[/bold red] {e}")
        sys.exit(1)

    # Extract metadata
    metadata = extract_metadata_from_markdown(content)

    if verbose:
        display_metadata_table(metadata)
        console.print()

    # Add front matter
    modified_content = add_title_to_frontmatter(content, metadata)

    # Validate the result
    validation = validate_frontmatter(modified_content, metadata)

    if verbose or not validation.is_valid:
        display_validation_result(validation)
        console.print()

    if not validation.is_valid:
        error_console.print("[bold red]Aborting due to validation errors.[/bold red]")
        sys.exit(1)

    # Show preview
    if verbose or dry_run:
        display_frontmatter_preview(modified_content)

    # Write the file (unless dry run)
    if dry_run:
        if not quiet:
            console.print(f"[yellow]Dry run - would write to:[/yellow] {output_file}")
    else:
        try:
            output_file.write_text(modified_content, encoding="utf-8")
            if not quiet:
                console.print(f"[bold green]Written to:[/bold green] {output_file}")
        except Exception as e:
            error_console.print(f"[bold red]Error writing file:[/bold red] {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
