from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from pathlib import Path


class ArtistMetadata(BaseModel):
    """
    Metadata for a music artist from MusicBrainz.

    Represents comprehensive information about a musical artist, including
    identification, personal details, and genre information.

    Example:
        artist = ArtistMetadata(
            musicbrainz_id="5b11f4ce-a62d-471e-81fc-a69b8a9d0b98",
            name="Jay-Z",
            sort_name="Jay-Z",
            country="US",
            artist_type="person",
            genres=["hip hop", "rap"]
        )
    """

    musicbrainz_id: str = Field(
        ..., description="Unique MusicBrainz identifier for the artist"
    )
    name: str = Field(..., description="Primary name of the artist")
    sort_name: str = Field(..., description="Name used for alphabetical sorting")
    country: Optional[str] = Field(None, description="Country of artist's origin")
    formed: Optional[str] = Field(
        None, description="Year or date the artist/band was formed"
    )
    artist_type: Optional[str] = Field(
        None, description="Type of artist (e.g., 'person', 'group')"
    )
    genres: List[str] = Field(
        default_factory=list,
        description="List of musical genres associated with the artist",
    )
    disambiguation: Optional[str] = Field(
        None,
        description="Additional context to distinguish between artists with similar names",
    )


class AlbumMetadata(BaseModel):
    """
    Metadata for a music album from MusicBrainz.

    Captures comprehensive details about a musical release, including
    identification, artist information, and album characteristics.

    Example:
        album = AlbumMetadata(
            musicbrainz_id="380b56f9-0e16-4f80-9ae6-55f4a654dba9",
            title="4:44",
            artist="[[Jay-Z]]",
            artist_mbid="5b11f4ce-a62d-471e-81fc-a69b8a9d0b98",
            release_date="2017-06-30",
            genres=["hip hop"],
            track_count=10
        )
    """

    musicbrainz_id: str = Field(
        ..., description="Unique MusicBrainz identifier for the album"
    )
    title: str = Field(..., description="Title of the album")
    artist: str = Field(..., description="Artist name, formatted for Obsidian link")
    artist_mbid: str = Field(
        ..., description="MusicBrainz identifier for the album's artist"
    )
    release_date: Optional[str] = Field(None, description="Date of album release")
    country: Optional[str] = Field(None, description="Country of album release")
    label: Optional[str] = Field(
        None, description="Record label that released the album"
    )
    barcode: Optional[str] = Field(
        None, description="Album's unique barcode identifier"
    )
    track_count: Optional[int] = Field(
        None, description="Total number of tracks on the album"
    )
    genres: List[str] = Field(
        default_factory=list,
        description="List of musical genres associated with the album",
    )
    status: Optional[str] = Field(
        None, description="Release status (e.g., 'official', 'promotional')"
    )


class FileMetadata(BaseModel):
    """
    Metadata for files processed in the Obsidian Music Sorter.

    Tracks file path, type, existing metadata, and enrichment status.

    Example:
        file_meta = FileMetadata(
            file_path=Path("/path/to/artist/Jay-Z.md"),
            file_type="artist",
            existing_frontmatter={},
            needs_enrichment=True
        )
    """

    file_path: Path = Field(..., description="Absolute path to the file")
    file_type: str = Field(..., description="Type of file ('artist' or 'album')")
    existing_frontmatter: Dict[str, Any] = Field(
        default_factory=dict, description="Existing metadata in the file's frontmatter"
    )
    needs_enrichment: bool = Field(
        default=True,
        description="Flag indicating if the file requires additional metadata",
    )
