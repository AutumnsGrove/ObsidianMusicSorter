import frontmatter
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

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
        notable_albums: Optional[List[Dict[str, Any]]] = None,
        dry_run: bool = False
    ) -> bool:
        """
        Write artist metadata to an existing markdown file.

        Reads the existing file, merges new metadata, and writes back while preserving
        original content and user-added fields. Appends body content if file has no content.

        Args:
            file_path (Path): Path to the markdown file to update
            metadata (ArtistMetadata): New metadata to merge into the file
            notable_albums (Optional[List[Dict[str, Any]]]): List of notable album dicts
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

            # Add type field for artist
            merged_metadata["type"] = "artist"

            # Prepare updated post
            post.metadata = merged_metadata

            # APPEND ONLY: Add body content if there's no existing content
            if not post.content or not post.content.strip():
                body_content = self._generate_artist_body_content(metadata, notable_albums)
                post.content = body_content
                self.logger.info(f"Generated body content for {file_path.name}")
            else:
                self.logger.info(f"Preserving existing body content in {file_path.name}")

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
        track_names: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> bool:
        """
        Write album metadata to an existing markdown file.

        Similar to write_artist_metadata, but with special handling for artist field
        to ensure it's an Obsidian link. Appends body content if file has no content.

        Args:
            file_path (Path): Path to the markdown file to update
            metadata (AlbumMetadata): New metadata to merge into the file
            track_names (Optional[List[str]]): List of track names for body content
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

            # Add type field for album
            merged_metadata["type"] = "album"

            # Prepare updated post
            post.metadata = merged_metadata

            # APPEND ONLY: Add body content if there's no existing content
            if not post.content or not post.content.strip():
                body_content = self._generate_album_body_content(metadata, track_names)
                post.content = body_content
                self.logger.info(f"Generated body content for {file_path.name}")
            else:
                self.logger.info(f"Preserving existing body content in {file_path.name}")

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

    def _generate_artist_body_content(
        self,
        metadata: ArtistMetadata,
        notable_albums: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Generate body content for an artist markdown file.

        Args:
            metadata (ArtistMetadata): Artist metadata
            notable_albums (Optional[List[Dict[str, Any]]]): List of notable album dicts

        Returns:
            str: Formatted markdown content for the body
        """
        content_parts = []

        # Genre Summary
        if metadata.genres:
            content_parts.append("## Genres")
            genres_str = ", ".join(metadata.genres[:5])  # Limit to top 5 genres
            content_parts.append(f"{genres_str}")
            content_parts.append("")

        # Notable Albums (as Obsidian links)
        if notable_albums:
            content_parts.append("## Notable Albums")
            for album in notable_albums[:10]:  # Limit to 10 albums
                album_title = album.get('title', '')
                # Create Obsidian link
                album_link = f"- [[{album_title}]]"
                if album.get('date'):
                    album_link += f" ({album['date'][:4]})"  # Show year only
                content_parts.append(album_link)
            content_parts.append("")

        # External Links
        content_parts.append("## Links")
        content_parts.append(f"- [MusicBrainz](https://musicbrainz.org/artist/{metadata.musicbrainz_id})")
        content_parts.append("")

        return "\n".join(content_parts)

    def _generate_album_body_content(
        self,
        metadata: AlbumMetadata,
        track_names: Optional[List[str]] = None
    ) -> str:
        """
        Generate body content for an album markdown file.

        Args:
            metadata (AlbumMetadata): Album metadata
            track_names (Optional[List[str]]): List of track names

        Returns:
            str: Formatted markdown content for the body
        """
        content_parts = []

        # Artist Link
        content_parts.append("## Artist")
        # Extract artist name from Obsidian link format
        artist_display = metadata.artist.replace("[[", "").replace("]]", "")
        if "|" in artist_display:
            artist_display = artist_display.split("|")[-1].strip()
        elif "/" in artist_display:
            artist_display = artist_display.split("/")[-1].strip()
        content_parts.append(f"**{artist_display}**")
        content_parts.append("")

        # Album Info
        content_parts.append("## Album Information")
        if metadata.release_date:
            content_parts.append(f"- **Released**: {metadata.release_date}")
        if metadata.country:
            content_parts.append(f"- **Country**: {metadata.country}")
        if metadata.track_count:
            content_parts.append(f"- **Tracks**: {metadata.track_count}")
        content_parts.append("")

        # Genre Summary
        if metadata.genres:
            content_parts.append("## Genres")
            genres_str = ", ".join(metadata.genres[:5])
            content_parts.append(f"{genres_str}")
            content_parts.append("")

        # Track Listing
        if track_names:
            content_parts.append("## Track Listing")
            for idx, track in enumerate(track_names, 1):
                content_parts.append(f"{idx}. {track}")
            content_parts.append("")

        # Cover Art Reference
        if metadata.cover:
            content_parts.append("## Cover Art")
            content_parts.append(f"![Album Cover]({metadata.cover})")
            content_parts.append("")

        # External Links
        content_parts.append("## Links")
        content_parts.append(f"- [MusicBrainz](https://musicbrainz.org/release/{metadata.musicbrainz_id})")
        content_parts.append("")

        return "\n".join(content_parts)

    def update_artist_file(
        self,
        file_path: Path,
        metadata: Dict[str, Any],
        notable_albums: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Update an artist file with metadata from MusicBrainz.

        Args:
            file_path (Path): Path to the artist markdown file
            metadata (Dict[str, Any]): Metadata dictionary from MusicBrainz
            notable_albums (Optional[List[Dict[str, Any]]]): List of notable album dicts

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert dict to ArtistMetadata model
            artist_metadata = ArtistMetadata(**metadata)
            return self.write_artist_metadata(
                file_path, artist_metadata, notable_albums=notable_albums, dry_run=False
            )
        except Exception as e:
            self.logger.error(f"Error updating artist file {file_path}: {e}")
            return False

    def update_album_file(
        self,
        file_path: Path,
        metadata: Dict[str, Any],
        track_names: Optional[List[str]] = None
    ) -> bool:
        """
        Update an album file with metadata from MusicBrainz.

        Args:
            file_path (Path): Path to the album markdown file
            metadata (Dict[str, Any]): Metadata dictionary from MusicBrainz
            track_names (Optional[List[str]]): List of track names

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert dict to AlbumMetadata model
            album_metadata = AlbumMetadata(**metadata)
            return self.write_album_metadata(
                file_path, album_metadata, track_names=track_names, dry_run=False
            )
        except Exception as e:
            self.logger.error(f"Error updating album file {file_path}: {e}")
            return False