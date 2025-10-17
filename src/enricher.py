"""
Obsidian Music Sorter: Metadata Enrichment Orchestration Module

This module provides the core orchestration logic for enriching music metadata
in an Obsidian vault using MusicBrainz API.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List

import logging
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

        self.api_client = MusicBrainzClient(config)
        self.metadata_writer = MetadataWriter(config)

        # Enrichment statistics
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'enriched_files': 0,
            'skipped_files': 0,
            'error_files': 0
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
        files = scan_vault(self.config.vault_path)
        artist_files = [f for f in files if 'example_artist_' in str(f)]
        album_files = [f for f in files if 'example_album_' in str(f)]

        self.stats['total_files'] = len(files)

        # Use Rich Progress for beautiful progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn()
        ) as progress:
            # Process artist files first
            artist_task = progress.add_task("[cyan]Processing Artists", total=len(artist_files))
            for artist_file in artist_files:
                try:
                    if self._should_process_file(artist_file):
                        success = self._process_artist_file(artist_file)
                        if success:
                            self.stats['enriched_files'] += 1
                        else:
                            self.stats['skipped_files'] += 1
                    else:
                        self.stats['skipped_files'] += 1

                    self.stats['processed_files'] += 1
                    progress.update(artist_task, advance=1)
                except Exception as e:
                    self.logger.error(f"Error processing artist file {artist_file}: {e}")
                    self.stats['error_files'] += 1
                    progress.update(artist_task, advance=1)

            # Then process album files
            album_task = progress.add_task("[magenta]Processing Albums", total=len(album_files))
            for album_file in album_files:
                try:
                    if self._should_process_file(album_file):
                        success = self._process_album_file(album_file)
                        if success:
                            self.stats['enriched_files'] += 1
                        else:
                            self.stats['skipped_files'] += 1
                    else:
                        self.stats['skipped_files'] += 1

                    self.stats['processed_files'] += 1
                    progress.update(album_task, advance=1)
                except Exception as e:
                    self.logger.error(f"Error processing album file {album_file}: {e}")
                    self.stats['error_files'] += 1
                    progress.update(album_task, advance=1)

        # Log final statistics
        self.logger.info(f"Vault Enrichment Complete: {self.stats}")

        # Optional progress callback
        if progress_callback:
            progress_callback(self.stats)

        return self.stats

    def _process_artist_file(self, file_path: Path) -> bool:
        """
        Process a single artist markdown file for metadata enrichment.

        Args:
            file_path (Path): Path to the artist markdown file

        Returns:
            bool: True if successfully processed, False otherwise
        """
        mbid = extract_mbid_from_frontmatter(file_path)
        if not mbid:
            self.logger.warning(f"No MBID found in artist file: {file_path}")
            return False

        try:
            # Fetch artist metadata from MusicBrainz
            artist_metadata = self.api_client.get_artist_metadata(mbid)

            # Write enriched metadata
            if not self.config.dry_run:
                self.metadata_writer.update_artist_file(file_path, artist_metadata)

            return True
        except Exception as e:
            self.logger.error(f"Error enriching artist {mbid}: {e}")
            return False

    def _process_album_file(self, file_path: Path) -> bool:
        """
        Process a single album markdown file for metadata enrichment.

        Args:
            file_path (Path): Path to the album markdown file

        Returns:
            bool: True if successfully processed, False otherwise
        """
        mbid = extract_mbid_from_frontmatter(file_path)
        if not mbid:
            self.logger.warning(f"No MBID found in album file: {file_path}")
            return False

        try:
            # Fetch album metadata from MusicBrainz
            album_metadata = self.api_client.get_album_metadata(mbid)

            # Ensure artist is in Obsidian link format
            if 'artist' in album_metadata:
                album_metadata['artist'] = f"[[{album_metadata['artist']}]]"

            # Write enriched metadata
            if not self.config.dry_run:
                self.metadata_writer.update_album_file(file_path, album_metadata)

            return True
        except Exception as e:
            self.logger.error(f"Error enriching album {mbid}: {e}")
            return False

    def _should_process_file(self, file_path: Path) -> bool:
        """
        Determine if a file needs processing based on metadata completeness.

        Args:
            file_path (Path): Path to the markdown file

        Returns:
            bool: True if file needs processing, False otherwise
        """
        # Check if file has a valid MBID
        mbid = extract_mbid_from_frontmatter(file_path)
        if not mbid:
            return False

        # Add more sophisticated checks if needed, e.g.:
        # - Check if existing metadata is complete
        # - Respect config settings for forced re-processing
        return True