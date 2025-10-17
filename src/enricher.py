"""
Obsidian Music Sorter: Metadata Enrichment Orchestration Module

This module provides the core orchestration logic for enriching music metadata
in an Obsidian vault using MusicBrainz API.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List

import logging
import frontmatter
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from src.config import Config
from src.scanner import scan_vault
from src.api_client import MusicBrainzClient
from src.metadata_writer import MetadataWriter
from src.logger_setup import setup_logger
from src.utils import extract_mbid_from_frontmatter


class MusicEnricher:
    """
    Main orchestrator for enriching music files in an Obsidian vault.

    Responsibilities:
    - Scan vault for music-related markdown files
    - Process artists and albums with MusicBrainz metadata
    - Track and report enrichment progress and statistics
    """

    def __init__(self, config: Config):
        """
        Initialize the MusicEnricher with necessary components.

        Args:
            config (Config): Configuration object with vault and enrichment settings
        """
        self.config = config
        self.logger = setup_logger(__name__)

        self.api_client = MusicBrainzClient(rate_limit_seconds=config.rate_limit_seconds)
        self.metadata_writer = MetadataWriter()

        # Enrichment statistics
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "enriched_files": 0,
            "skipped_files": 0,
            "error_files": 0,
        }

    def enrich_vault(self, progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Orchestrate the metadata enrichment process for the entire vault.

        Args:
            progress_callback (Optional[callable]): Optional callback for progress updates

        Returns:
            Dict[str, Any]: Enrichment statistics and summary
        """
        self.logger.info("Starting vault enrichment process")

        # Find markdown files to process
        scan_results = scan_vault(self.config.vault_path)
        artist_files = scan_results["artists"]
        album_files = scan_results["albums"]

        self.stats["total_files"] = len(artist_files) + len(album_files)

        # Use Rich Progress for beautiful progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            # Process artist files first
            artist_task = progress.add_task("[cyan]Processing Artists", total=len(artist_files))
            for idx, artist_file in enumerate(artist_files, start=1):
                try:
                    if self._should_process_file(artist_file):
                        success = self._process_artist_file(
                            artist_file, current=idx, total=len(artist_files)
                        )
                        if success:
                            self.stats["enriched_files"] += 1
                        else:
                            self.stats["skipped_files"] += 1
                    else:
                        self.stats["skipped_files"] += 1

                    self.stats["processed_files"] += 1
                    progress.update(artist_task, advance=1)
                except Exception as e:
                    self.logger.error(f"Error processing artist file {artist_file}: {e}")
                    self.stats["error_files"] += 1
                    progress.update(artist_task, advance=1)

            # Then process album files
            album_task = progress.add_task("[magenta]Processing Albums", total=len(album_files))
            for idx, album_file in enumerate(album_files, start=1):
                try:
                    if self._should_process_file(album_file):
                        success = self._process_album_file(
                            album_file, current=idx, total=len(album_files)
                        )
                        if success:
                            self.stats["enriched_files"] += 1
                        else:
                            self.stats["skipped_files"] += 1
                    else:
                        self.stats["skipped_files"] += 1

                    self.stats["processed_files"] += 1
                    progress.update(album_task, advance=1)
                except Exception as e:
                    self.logger.error(f"Error processing album file {album_file}: {e}")
                    self.stats["error_files"] += 1
                    progress.update(album_task, advance=1)

        # Log final statistics
        self.logger.info(f"Vault Enrichment Complete: {self.stats}")

        # Optional progress callback
        if progress_callback:
            progress_callback(self.stats)

        return self.stats

    def _process_artist_file(self, file_path: Path, current: int = 0, total: int = 0) -> bool:
        """
        Process a single artist markdown file for metadata enrichment.

        Args:
            file_path (Path): Path to the artist markdown file
            current (int): Current artist being processed (for logging)
            total (int): Total number of artists to be processed (for logging)

        Returns:
            bool: True if successfully processed, False otherwise
        """
        try:
            # Read the file's frontmatter
            with open(file_path, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)

            # Check if MBID already exists
            mbid = post.get("musicbrainz_id") or post.get("mbid")

            # If no MBID, search by name
            if not mbid:
                # Use name from frontmatter, or fallback to filename without extension
                artist_name = post.get("name")
                if not artist_name:
                    artist_name = file_path.stem  # filename without .md extension
                    self.logger.debug(f"Using filename as artist name: {artist_name}")

                # Log progress with current index and artist name
                if total > 0:
                    self.logger.info(f"Processing artist {current} of {total}: {artist_name}")
                else:
                    self.logger.info(f"Processing artist: {artist_name}")

                self.logger.info(f"Searching for artist: {artist_name}")
                search_results = self.api_client.search_artist(artist_name, limit=1)

                if not search_results:
                    self.logger.warning(f"No MusicBrainz results found for artist: {artist_name}")
                    # Log search failure with progress
                    if total > 0:
                        self.logger.warning(
                            f"Search failed for artist {current} of {total}: {artist_name}"
                        )
                    return False

                # Use the first search result
                mbid = search_results[0]["mbid"]
                self.logger.info(f"Found MBID {mbid} for artist: {artist_name}")

            # Fetch full artist metadata from MusicBrainz
            artist_metadata = self.api_client.get_artist_by_mbid(mbid)

            if not artist_metadata:
                # Log metadata fetch failure with progress
                if total > 0:
                    self.logger.warning(
                        f"Failed to fetch metadata for artist {current} of {total}: {mbid}"
                    )
                else:
                    self.logger.warning(f"Failed to fetch metadata for artist MBID: {mbid}")
                return False

            # Write enriched metadata
            if not self.config.dry_run:
                self.metadata_writer.update_artist_file(file_path, artist_metadata.model_dump())

            # Log successful processing with progress
            if total > 0:
                self.logger.info(
                    f"Successfully processed artist {current} of {total}: {artist_metadata.name}"
                )
            else:
                self.logger.info(f"Successfully processed artist: {artist_metadata.name}")

            return True
        except Exception as e:
            # Log error with progress context
            if total > 0:
                self.logger.error(
                    f"Error processing artist {current} of {total} file {file_path}: {e}"
                )
            else:
                self.logger.error(f"Error enriching artist file {file_path}: {e}")
            return False

    def _process_album_file(self, file_path: Path, current: int = 0, total: int = 0) -> bool:
        """
        Process a single album markdown file for metadata enrichment.

        Args:
            file_path (Path): Path to the album markdown file
            current (int): Current album being processed (for logging)
            total (int): Total number of albums to be processed (for logging)

        Returns:
            bool: True if successfully processed, False otherwise
        """
        try:
            # Read the file's frontmatter
            with open(file_path, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)

            # Check if MBID already exists
            mbid = post.get("musicbrainz_id") or post.get("mbid")

            # If no MBID, search by name
            if not mbid:
                # Use name from frontmatter, or fallback to filename without extension
                album_name = post.get("name")
                if not album_name:
                    album_name = file_path.stem  # filename without .md extension
                    self.logger.debug(f"Using filename as album name: {album_name}")

                # Get artist name if available for better search accuracy
                artist_name = post.get("artist")
                if artist_name:
                    # Remove Obsidian link formatting if present
                    artist_name = artist_name.replace("[[", "").replace("]]", "")
                    # If pipe exists, take the display name (after pipe)
                    if "|" in artist_name:
                        artist_name = artist_name.split("|")[-1].strip()
                    # If path exists, take the last part
                    elif "/" in artist_name:
                        artist_name = artist_name.split("/")[-1].strip()

                # Log progress with current index and album name
                if total > 0:
                    self.logger.info(f"Processing album {current} of {total}: {album_name}")
                else:
                    self.logger.info(f"Processing album: {album_name}")

                self.logger.info(
                    f"Searching for album: {album_name}"
                    + (f" by {artist_name}" if artist_name else "")
                )
                search_results = self.api_client.search_album(
                    album_name, artist=artist_name, limit=1
                )

                if not search_results:
                    self.logger.warning(f"No MusicBrainz results found for album: {album_name}")
                    # Log search failure with progress
                    if total > 0:
                        self.logger.warning(
                            f"Search failed for album {current} of {total}: {album_name}"
                        )
                    return False

                # Use the first search result
                mbid = search_results[0]["mbid"]
                self.logger.info(f"Found MBID {mbid} for album: {album_name}")

            # Fetch full album metadata from MusicBrainz
            album_metadata = self.api_client.get_album_by_mbid(mbid)

            if not album_metadata:
                # Log metadata fetch failure with progress
                if total > 0:
                    self.logger.warning(
                        f"Failed to fetch metadata for album {current} of {total}: {mbid}"
                    )
                else:
                    self.logger.warning(f"Failed to fetch metadata for album MBID: {mbid}")
                return False

            # Convert to dict for metadata processing
            album_dict = album_metadata.model_dump()

            # Write enriched metadata
            if not self.config.dry_run:
                self.metadata_writer.update_album_file(file_path, album_dict)

            # Log successful processing with progress
            if total > 0:
                self.logger.info(
                    f"Successfully processed album {current} of {total}: {album_dict.get('title', album_dict.get('name', 'Unknown'))}"
                )
            else:
                self.logger.info(f"Successfully processed album: {album_dict.get('title', album_dict.get('name', 'Unknown'))}")

            return True
        except Exception as e:
            # Log error with progress context
            if total > 0:
                self.logger.error(
                    f"Error processing album {current} of {total} file {file_path}: {e}"
                )
            else:
                self.logger.error(f"Error enriching album file {file_path}: {e}")
            return False

    def _should_process_file(self, file_path: Path) -> bool:
        """
        Determine if a file needs processing based on metadata completeness.

        Args:
            file_path (Path): Path to the markdown file

        Returns:
            bool: True if file needs processing, False otherwise
        """
        try:
            # Read the file's frontmatter
            with open(file_path, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)

            # Must have a name/title (use filename as fallback)
            name = post.get("name") or post.get("title") or file_path.stem
            if not name:
                return False

            # Check if file already has complete metadata
            mbid = post.get("musicbrainz_id") or post.get("mbid")
            genres = post.get("genres", [])

            # Skip if already complete (has MBID and genres)
            if mbid and genres and len(genres) > 0:
                self.logger.info(f"Skipping {file_path.name} - already enriched")
                return False

            return True
        except Exception as e:
            self.logger.error(f"Error checking file {file_path}: {e}")
            return False
