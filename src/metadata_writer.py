import frontmatter
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from src.models import ArtistMetadata, AlbumMetadata
from src.logger_setup import setup_logger
from src.utils import format_obsidian_link

class MetadataWriter:
    """
    Writes and updates enriched metadata to Obsidian markdown files.

    Ensures preservation of existing user content while updating MusicBrainz metadata.
    Supports writing metadata for both artists and albums with intelligent merging.
    """

    def __init__(self):
        """
        Initialize MetadataWriter with a logger.

        Uses the setup_logger to create a context-specific logger for tracking operations.
        """
        self.logger = setup_logger(__name__)

    def write_artist_metadata(
        self,
        file_path: Path,
        metadata: ArtistMetadata,
        dry_run: bool = False
    ) -> bool:
        """
        Write artist metadata to an existing markdown file.

        Reads the existing file, merges new metadata, and writes back while preserving
        original content and user-added fields.

        Args:
            file_path (Path): Path to the markdown file to update
            metadata (ArtistMetadata): New metadata to merge into the file
            dry_run (bool, optional): If True, only logs changes without writing. Defaults to False.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate file exists
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return False

            # Read existing file
            post = frontmatter.load(file_path)
            existing_metadata = dict(post.metadata)

            # Merge metadata intelligently
            merged_metadata = self._merge_frontmatter(existing_metadata, metadata.model_dump())

            # Prepare updated post
            post.metadata = merged_metadata

            # Dry run - just log what would be written
            if dry_run:
                self.logger.info(f"Dry run: Would update {file_path}")
                self.logger.info(f"Merged metadata: {merged_metadata}")
                return True

            # Write updated file
            with open(file_path, 'wb') as f:
                frontmatter.dump(post, f)

            self.logger.info(f"Successfully updated artist metadata in {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating artist metadata in {file_path}: {e}")
            return False

    def write_album_metadata(
        self,
        file_path: Path,
        metadata: AlbumMetadata,
        dry_run: bool = False
    ) -> bool:
        """
        Write album metadata to an existing markdown file.

        Similar to write_artist_metadata, but with special handling for artist field
        to ensure it's an Obsidian link.

        Args:
            file_path (Path): Path to the markdown file to update
            metadata (AlbumMetadata): New metadata to merge into the file
            dry_run (bool, optional): If True, only logs changes without writing. Defaults to False.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate file exists
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return False

            # Read existing file
            post = frontmatter.load(file_path)
            existing_metadata = dict(post.metadata)

            # Prepare metadata, converting artist to Obsidian link if needed
            metadata_dict = metadata.model_dump()
            if 'artist' in metadata_dict:
                metadata_dict['artist'] = format_obsidian_link(metadata_dict['artist'])

            # Merge metadata intelligently
            merged_metadata = self._merge_frontmatter(existing_metadata, metadata_dict)

            # Prepare updated post
            post.metadata = merged_metadata

            # Dry run - just log what would be written
            if dry_run:
                self.logger.info(f"Dry run: Would update {file_path}")
                self.logger.info(f"Merged metadata: {merged_metadata}")
                return True

            # Write updated file
            with open(file_path, 'wb') as f:
                frontmatter.dump(post, f)

            self.logger.info(f"Successfully updated album metadata in {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating album metadata in {file_path}: {e}")
            return False

    def _merge_frontmatter(
        self,
        existing: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Intelligently merge frontmatter, preserving user content and handling special cases.

        Args:
            existing (Dict[str, Any]): Existing frontmatter dictionary
            new_data (Dict[str, Any]): New metadata to merge

        Returns:
            Dict[str, Any]: Merged frontmatter dictionary
        """
        # Create a copy to avoid modifying the original
        merged = existing.copy()

        # Special handling for genres: merge and remove duplicates
        if 'genres' in new_data and new_data['genres']:
            existing_genres = set(merged.get('genres', []))
            new_genres = set(new_data['genres'])
            merged['genres'] = list(existing_genres.union(new_genres))

        # Merge other fields, preserving existing if more specific
        for key, value in new_data.items():
            if key == 'genres':
                continue  # Already handled above

            # Only update if new value is not None/empty and either
            # the key doesn't exist or the existing value is empty/None
            if value is not None and (
                key not in merged or
                not merged[key] or
                (isinstance(merged[key], list) and len(merged[key]) == 0)
            ):
                merged[key] = value

        return merged