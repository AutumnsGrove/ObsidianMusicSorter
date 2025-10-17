"""Command-line interface for Obsidian Music Metadata Enricher.

This module provides a comprehensive CLI for scanning, enriching,
and validating music metadata in an Obsidian vault.
"""

import logging
import sys
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from src.config import Config
from src.enricher import MusicEnricher
from src.scanner import scan_vault
from src.logger_setup import setup_logger


def setup_rich_logging(log_level: str) -> None:
    """Configure logging with rich console output.

    Args:
        log_level (str): Logging level as string ('DEBUG', 'INFO', etc.)
    """
    log_level = getattr(logging, log_level)
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


@click.group()
def cli() -> None:
    """Obsidian Music Metadata Enricher

    A tool to enrich and validate music metadata in Obsidian vaults.
    """
    pass


@cli.command()
@click.argument('vault_path', type=click.Path(exists=True))
@click.option(
    "--dry-run",
    is_flag=True,
    help="Run without making changes, preview potential enrichments",
)
@click.option(
    "--refresh-all",
    is_flag=True,
    help="Re-process all files, ignoring existing metadata completeness",
)
@click.option(
    "--rate-limit",
    type=float,
    default=2.0,
    help="Seconds between API calls to prevent rate limiting",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Set the logging verbosity",
)
def enrich(vault_path: str, dry_run: bool, refresh_all: bool, rate_limit: float, log_level: str) -> None:
    """Enrich music metadata in Obsidian vault at VAULT_PATH.

    Scans the vault, retrieves additional music metadata, and updates notes.

    Args:
        vault_path (str): Path to the Obsidian vault
        dry_run (bool): Preview changes without applying them
        refresh_all (bool): Re-process all files regardless of existing metadata
        rate_limit (float): Time between API calls
        log_level (str): Logging verbosity level
    """
    console = Console()
    setup_rich_logging(log_level)
    logger = logging.getLogger(__name__)

    try:
        config = Config(
            vault_path=vault_path,
            dry_run=dry_run,
            refresh_all=refresh_all,
            rate_limit_seconds=rate_limit
        )
        enricher = MusicEnricher(config)

        results = enricher.enrich_vault()

        # Display results in a rich table
        table = Table(title="Enrichment Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="magenta")

        table.add_row("Total Files Found", str(results['total_files']))
        table.add_row("Files Processed", str(results['processed_files']))
        table.add_row("Files Enriched", str(results['enriched_files']))
        table.add_row("Files Skipped", str(results['skipped_files']))
        table.add_row("Errors", str(results['error_files']))

        console.print(table)

        if results['error_files'] > 0:
            logger.warning(
                f"Encountered {results['error_files']} errors during enrichment"
            )
            sys.exit(1)

    except Exception as e:
        logger.error(f"Enrichment failed: {e}")
        sys.exit(1)

    console.print("[green]✓ Enrichment Complete![/green]")


@cli.command()
@click.argument('vault_path', type=click.Path(exists=True))
def scan(vault_path: str) -> None:
    """Scan vault at VAULT_PATH and show files that would be processed.

    Provides a preview of files that could be enriched without making changes.

    Args:
        vault_path (str): Path to the Obsidian vault
    """
    console = Console()

    try:
        scan_results = scan_vault(vault_path)

        if not scan_results:
            console.print("[yellow]No processable files found.[/yellow]")
            return

        table = Table(title="Potential Music Files")
        table.add_column("File Path", style="cyan")
        table.add_column("Status", style="magenta")

        for file_path in scan_results:
            table.add_row(file_path, "Eligible for Enrichment")

        console.print(table)
        console.print(f"[green]Total Eligible Files: {len(scan_results)}[/green]")

    except Exception as e:
        console.print(f"[red]Scan failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('vault_path', type=click.Path(exists=True))
def validate(vault_path: str) -> None:
    """Validate existing metadata completeness in VAULT_PATH.

    Checks music files for missing or incomplete metadata.

    Args:
        vault_path (str): Path to the Obsidian vault
    """
    # TODO: Implement validation logic
    click.echo("Validation not yet implemented.")


if __name__ == "__main__":
    cli()
