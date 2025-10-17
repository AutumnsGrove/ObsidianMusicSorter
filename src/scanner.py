"""
Scanner module for processing markdown files in an Obsidian vault.

This module provides functionality to scan a directory for markdown files
with artist and album metadata, extracting and categorizing them.
"""

from pathlib import Path
from typing import Dict, List, Optional
import frontmatter
import logging

from .logger_setup import get_logger

logger = get_logger(__name__)


def scan_vault(vault_path: str) -> Dict[str, List[Path]]:
    """
    Scan vault directory for artist and album markdown files.

    Args:
        vault_path (str): Path to the Obsidian vault directory

    Returns:
        Dict with 'artists' and 'albums' keys, each containing list of file paths

    Raises:
        ValueError: If vault_path is not a valid directory
    """
    vault_dir = Path(vault_path)

    if not vault_dir.is_dir():
        raise ValueError(f"Invalid vault path: {vault_path}")

    results: Dict[str, List[Path]] = {"artists": [], "albums": []}

    # Recursively find all markdown files
    for md_file in vault_dir.rglob("*.md"):
        try:
            # Read the file's frontmatter
            with open(md_file, "r", encoding="utf-8") as f:
                parsed_file = frontmatter.load(f)

            # Check if frontmatter contains type
            file_type = parsed_file.get("type")

            if not file_type:
                logger.warning(f"No type found in {md_file}. Skipping.")
                continue

            # Categorize based on type
            if file_type == "artist":
                results["artists"].append(md_file)
            elif file_type == "album":
                results["albums"].append(md_file)
            else:
                logger.warning(f"Unknown type '{file_type}' in {md_file}. Skipping.")

        except (IOError, OSError) as e:
            logger.error(f"Error reading {md_file}: {e}")
        except frontmatter.ParseException as e:
            logger.error(f"Invalid YAML frontmatter in {md_file}: {e}")

    logger.info(
        f"Scan complete. Found {len(results['artists'])} artists and {len(results['albums'])} albums."
    )

    return results


def get_file_type(file_path: Path) -> Optional[str]:
    """
    Retrieve the type of a markdown file from its frontmatter.

    Args:
        file_path (Path): Path to the markdown file

    Returns:
        Optional[str]: The type of the file ('artist', 'album', or None)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            parsed_file = frontmatter.load(f)
            return parsed_file.get("type")
    except (IOError, frontmatter.ParseException) as e:
        logger.error(f"Error parsing {file_path}: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
        results = scan_vault(vault_path)
        print("Artists:", [f.name for f in results["artists"]])
        print("Albums:", [f.name for f in results["albums"]])
    else:
        print("Please provide a vault path as an argument.")
