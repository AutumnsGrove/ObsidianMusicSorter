import time
from typing import Optional, List, Dict, Any
import musicbrainzngs as mb
from src.models import ArtistMetadata, AlbumMetadata
from src.logger_setup import setup_logger


class MusicBrainzClient:
    """
    Client for interacting with the MusicBrainz API with rate limiting and error handling.

    Attributes:
        rate_limit (float): Minimum time between API requests.
        last_request_time (float): Timestamp of the last API request.
        logger (logging.Logger): Logger for recording API interactions.
    """

    def __init__(self, rate_limit_seconds: float = 2.0):
        """
        Initialize the MusicBrainz API client.

        Args:
            rate_limit_seconds (float, optional): Minimum time between requests.
                Defaults to 2.0 seconds.
        """
        self.rate_limit = rate_limit_seconds
        self.last_request_time = 0
        self.logger = setup_logger(__name__)

        # Set user agent as required by MusicBrainz
        try:
            mb.set_useragent("ObsidianMusicEnricher", "1.0", "contact@example.com")
        except Exception as e:
            self.logger.error(f"Failed to set user agent: {e}")
            raise

    def _enforce_rate_limit(self):
        """
        Enforce rate limiting by sleeping if necessary to maintain minimum time
        between requests.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last_request
            self.logger.info(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get_artist_by_mbid(self, mbid: str) -> Optional[ArtistMetadata]:
        """
        Fetch artist data by MusicBrainz ID.

        Args:
            mbid (str): MusicBrainz ID of the artist.

        Returns:
            Optional[ArtistMetadata]: Parsed artist metadata or None if not found.
        """
        try:
            self._enforce_rate_limit()
            result = mb.get_artist_by_id(mbid, includes=["tags", "release-groups"])
            artist = result["artist"]

            return ArtistMetadata(
                musicbrainz_id=mbid,
                name=artist.get("name", ""),
                disambiguation=artist.get("disambiguation"),
                type=artist.get("type"),
                country=artist.get("country"),
                begin_date=self._format_date(artist.get("life-span", {})),
                end_date=self._format_date(artist.get("life-span", {}), end=True),
                genres=[tag["name"] for tag in artist.get("tag-list", [])],
                cover=None,
            )
        except mb.MusicBrainzError as e:
            self.logger.error(f"Error fetching artist {mbid}: {e}")
            return None

    def get_album_by_mbid(self, mbid: str) -> Optional[AlbumMetadata]:
        """
        Fetch album/release data by MusicBrainz ID.

        Args:
            mbid (str): MusicBrainz ID of the album/release.

        Returns:
            Optional[AlbumMetadata]: Parsed album metadata or None if not found.
        """
        try:
            self._enforce_rate_limit()
            result = mb.get_release_by_id(
                mbid, includes=["artists", "recordings", "tags"]
            )
            release = result["release"]

            track_names = [
                track["recording"]["title"]
                for track in release.get("medium-list", [])[0].get("track-list", [])
            ]

            return AlbumMetadata(
                musicbrainz_id=mbid,
                title=release.get("title", ""),
                artist=release["artist-credit"][0]["artist"]["name"],
                artist_mbid=release["artist-credit"][0]["artist"]["id"],
                release_date=release.get("date"),
                country=release.get("country"),
                track_count=len(track_names),
                genres=[tag["name"] for tag in release.get("tag-list", [])],
                cover=f"https://coverartarchive.org/release/{mbid}/front",
            )
        except mb.MusicBrainzError as e:
            self.logger.error(f"Error fetching album {mbid}: {e}")
            return None

    def search_artist(self, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for artists by name.

        Args:
            name (str): Name of the artist to search for.
            limit (int, optional): Maximum number of results. Defaults to 10.

        Returns:
            List[Dict[str, Any]]: List of artist search results.
        """
        try:
            self._enforce_rate_limit()
            result = mb.search_artists(artist=name, limit=limit)

            return [
                {
                    "mbid": artist["id"],
                    "name": artist["name"],
                    "type": artist.get("type"),
                    "disambiguation": artist.get("disambiguation"),
                }
                for artist in result["artist-list"]
            ]
        except mb.MusicBrainzError as e:
            self.logger.error(f"Error searching artist {name}: {e}")
            return []

    def search_album(
        self, title: str, artist: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for albums/releases.

        Args:
            title (str): Title of the album/release to search for.
            artist (Optional[str], optional): Name of the artist. Defaults to None.
            limit (int, optional): Maximum number of results. Defaults to 10.

        Returns:
            List[Dict[str, Any]]: List of album search results.
        """
        try:
            self._enforce_rate_limit()
            search_params = {"release": title}
            if artist:
                search_params["artist"] = artist

            result = mb.search_releases(**search_params, limit=limit)

            return [
                {
                    "mbid": release["id"],
                    "title": release["title"],
                    "artist_name": release["artist-credit"][0]["artist"]["name"],
                    "artist_mbid": release["artist-credit"][0]["artist"]["id"],
                    "date": release.get("date"),
                    "type": release.get("primary-type"),
                }
                for release in result["release-list"]
            ]
        except mb.MusicBrainzError as e:
            self.logger.error(f"Error searching album {title}: {e}")
            return []

    def get_artist_albums(self, mbid: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch notable albums/releases for an artist.

        Args:
            mbid (str): MusicBrainz ID of the artist.
            limit (int, optional): Maximum number of albums to return. Defaults to 10.

        Returns:
            List[Dict[str, Any]]: List of album information dictionaries.
        """
        try:
            self._enforce_rate_limit()
            result = mb.get_artist_by_id(mbid, includes=["release-groups"], limit=limit)
            artist = result["artist"]

            release_groups = artist.get("release-group-list", [])

            albums = []
            for rg in release_groups[:limit]:
                if rg.get("type") in ["Album", "EP", None]:
                    albums.append({
                        "title": rg.get("title", ""),
                        "mbid": rg.get("id", ""),
                        "type": rg.get("type", "Album"),
                        "date": rg.get("first-release-date", ""),
                    })

            return albums[:limit]
        except mb.MusicBrainzError as e:
            self.logger.error(f"Error fetching albums for artist {mbid}: {e}")
            return []

    @staticmethod
    def _format_date(life_span: Dict, end: bool = False) -> Optional[str]:
        """
        Format life span or date from MusicBrainz metadata.

        Args:
            life_span (Dict): Life span dictionary from MusicBrainz.
            end (bool, optional): Whether to get end date. Defaults to False.

        Returns:
            Optional[str]: Formatted date string.
        """
        if not life_span:
            return None

        key = "ended" if end else "begin"
        return life_span.get(f"{key}")
