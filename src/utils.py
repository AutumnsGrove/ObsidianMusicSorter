from typing import List, Dict, Optional, Union
import re
import unidecode
from datetime import datetime


def format_obsidian_link(artist_name: str) -> str:
    """
    Convert an artist name to an Obsidian wiki-link format.

    Args:
        artist_name (str): The name of the artist to convert.

    Returns:
        str: Obsidian wiki-link formatted artist name.

    Examples:
        >>> format_obsidian_link("Jay-Z")
        '[[Jay-Z]]'
        >>> format_obsidian_link("The Beatles")
        '[[The Beatles]]'
    """
    if not artist_name:
        raise ValueError("Artist name cannot be empty")
    return f"[[{artist_name}]]"


def sanitize_filename(name: str, replacement: str = "-") -> str:
    """
    Sanitize a filename by removing invalid characters and replacing spaces.

    Args:
        name (str): The original filename or name to sanitize.
        replacement (str, optional): Character to replace spaces with. Defaults to '-'.

    Returns:
        str: A sanitized filename safe for most filesystems.

    Examples:
        >>> sanitize_filename("Beyoncé / Singles")
        'Beyonce-Singles'
        >>> sanitize_filename("File with: invalid ? characters")
        'File-with-invalid-characters'
    """
    if not name:
        raise ValueError("Name cannot be empty")

    # Remove or replace invalid filename characters
    # Includes characters invalid in most filesystems
    sanitized = re.sub(r'[<>:"/\\|?*]', "", name)

    # Replace special characters and multiple spaces
    sanitized = re.sub(r"\s+", replacement, sanitized.strip())

    # Replace Unicode characters (like accented letters)
    sanitized = unidecode.unidecode(sanitized)

    # Ensure the filename is not empty after sanitization
    if not sanitized:
        raise ValueError("Sanitization resulted in an empty filename")

    return sanitized


def parse_date(date_str: str) -> Optional[str]:
    """
    Parse various date formats from MusicBrainz into a standardized YYYY-MM-DD format.

    Args:
        date_str (str): Date string to parse.

    Returns:
        Optional[str]: Standardized date string or None if parsing fails.

    Examples:
        >>> parse_date('2020')
        '2020-01-01'
        >>> parse_date('2020-05')
        '2020-05-01'
        >>> parse_date('2020-05-15')
        '2020-05-15'
        >>> parse_date('Invalid Date')
        None
    """
    if not date_str or not isinstance(date_str, str):
        return None

    # Trim any whitespace
    date_str = date_str.strip()

    # Possible date formats
    date_formats = [
        "%Y-%m-%d",  # Full date
        "%Y-%m",  # Year and month
        "%Y",  # Just year
    ]

    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)

            # For partial dates, default to first of the month/year
            if fmt == "%Y":
                return parsed_date.strftime("%Y-01-01")
            elif fmt == "%Y-%m":
                return parsed_date.strftime("%Y-%m-01")

            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def merge_genres(existing: List[str], new: List[str]) -> List[str]:
    """
    Merge two genre lists, removing duplicates while preserving existing order.

    Args:
        existing (List[str]): The original list of genres.
        new (List[str]): The new list of genres to merge.

    Returns:
        List[str]: A merged list of genres without duplicates.

    Examples:
        >>> merge_genres(['Rock', 'Jazz'], ['Jazz', 'Blues'])
        ['Rock', 'Jazz', 'Blues']
        >>> merge_genres([], ['Pop', 'Electronic'])
        ['Pop', 'Electronic']
    """
    if not existing:
        return list(new)

    if not new:
        return list(existing)

    # Use a set to track unique genres while preserving order
    seen = set(existing)
    merged = existing.copy()

    for genre in new:
        if genre not in seen:
            merged.append(genre)
            seen.add(genre)

    return merged


def extract_mbid_from_frontmatter(frontmatter: Dict) -> Optional[str]:
    """
    Extract MusicBrainz ID from existing frontmatter.

    Args:
        frontmatter (Dict): A dictionary representing the frontmatter.

    Returns:
        Optional[str]: The extracted MusicBrainz ID or None if not found.

    Examples:
        >>> extract_mbid_from_frontmatter({'musicbrainz_id': 'abc123'})
        'abc123'
        >>> extract_mbid_from_frontmatter({'mbid': 'def456'})
        'def456'
        >>> extract_mbid_from_frontmatter({})
        None
    """
    # Common keys for MusicBrainz ID in frontmatter
    mbid_keys = ["musicbrainz_id", "mbid", "musicbrainz", "id"]

    for key in mbid_keys:
        if key in frontmatter and frontmatter[key]:
            return str(frontmatter[key])

    return None
