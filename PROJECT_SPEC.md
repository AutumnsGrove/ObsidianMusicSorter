# Obsidian Music Metadata Enricher - Project Specification

## Executive Summary

Build a Python script that recursively processes markdown files in an Obsidian vault's music collection, enriches them with metadata from the MusicBrainz API, and adds structured YAML frontmatter while preserving all existing content.

---

## Project Goals

1. **Automate metadata enrichment** for ~200 music-related markdown files (artists and albums)
2. **Preserve all existing content** including links, notes, and formatting
3. **Add structured YAML frontmatter** to enable Dataview queries in Obsidian
4. **Respect API rate limits** (2-second delay between requests)
5. **Provide excellent UX** with progress indicators and detailed logging
6. **Safe execution** with dry-run mode and backup capabilities

---

## Technical Requirements

### Core Technologies
- **Language**: Python 3.8+
- **Dependencies**:
  - `musicbrainzngs` - Official MusicBrainz API client (handles rate limiting, authentication)
  - `PyYAML` - YAML parsing and generation
  - `pathlib` - File system operations
  - `rich` or `tqdm` - Progress bars and beautiful console output
  - `python-frontmatter` - Parse/modify markdown frontmatter
  - Standard library: `logging`, `time`, `json`, `argparse`

### Environment
- Cross-platform (Mac/Linux/Windows)
- No external database required
- Local file system operations only

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Orchestrator                        │
│  - CLI argument parsing                                     │
│  - Progress tracking                                        │
│  - Orchestrate workflow                                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
      ┌────────────┼────────────┐
      │            │            │
      ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│  File    │ │   API    │ │ Metadata │
│ Scanner  │ │ Client   │ │ Writer   │
└──────────┘ └──────────┘ └──────────┘
      │            │            │
      └────────────┴────────────┘
                   │
                   ▼
        ┌──────────────────┐
        │   Logger &       │
        │   Reporter       │
        └──────────────────┘
```

---

## File Structure

```
obsidian-music-enricher/
├── enricher.py              # Main entry point
├── config.py                # Configuration and constants
├── models.py                # Data models (MusicFile, Metadata)
├── scanner.py               # File discovery and classification
├── api_client.py            # MusicBrainz API wrapper
├── metadata_writer.py       # Frontmatter injection
├── logger_setup.py          # Logging configuration
├── utils.py                 # Helper functions
├── requirements.txt         # Python dependencies
├── README.md                # User documentation
└── tests/                   # Unit tests (optional but recommended)
    ├── test_scanner.py
    ├── test_api_client.py
    └── test_metadata_writer.py
```

---

## Detailed Component Specifications

### 1. Main Entry Point (`enricher.py`)

**Purpose**: CLI interface and workflow orchestration

**Arguments**:
```bash
python enricher.py \
    --vault-path /path/to/vault \
    --music-folder music \
    [--dry-run] \
    [--backup] \
    [--force-update] \
    [--log-level INFO] \
    [--output-log results.json]
```

**Workflow**:
1. Parse CLI arguments
2. Initialize logging
3. Scan for music files
4. Classify files (artist vs album)
5. Process files with progress bar
6. Generate summary report
7. Save results log

**Key Features**:
- Dry-run mode (preview changes without writing)
- Optional backup before modification
- Resume capability (skip already-processed files unless --force-update)
- Rich console output with progress bars

---

### 2. Configuration (`config.py`)

**Constants**:
```python
# API Configuration
MUSICBRAINZ_APP_NAME = "ObsidianMusicEnricher"
MUSICBRAINZ_VERSION = "1.0.0"
MUSICBRAINZ_CONTACT = "user@example.com"  # User should update this
RATE_LIMIT_SECONDS = 2.0

# File Processing
ARTIST_FOLDER = "artist"
ALBUM_FOLDER = "album"
MUSIC_BASE_FOLDER = "music"

# Metadata Fields
ALBUM_FIELDS = [
    "type", "musicbrainz_id", "title", "artist", "artist_mbid",
    "release_date", "country", "label", "barcode", "track_count",
    "genres", "status"
]

ARTIST_FIELDS = [
    "type", "musicbrainz_id", "name", "sort_name", "country",
    "formed", "disbanded", "artist_type", "genres", "disambiguation"
]

# Processing
MAX_RETRIES = 3
SEARCH_LIMIT = 5  # Max results to fetch when searching
```

---

### 3. Data Models (`models.py`)

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

@dataclass
class MusicFile:
    """Represents a music-related markdown file."""
    path: Path
    filename: str
    file_type: str  # "artist" or "album"
    name: str  # Extracted from filename (without .md)
    existing_frontmatter: Optional[Dict[str, Any]]
    existing_content: str
    has_musicbrainz_id: bool  # Already processed?
    linked_files: List[str]  # [[links]] found in content

@dataclass
class AlbumMetadata:
    """Structured album metadata from MusicBrainz."""
    type: str = "album"
    musicbrainz_id: str
    title: str
    artist: str  # Formatted as [[Artist Name]]
    artist_mbid: str
    release_date: Optional[str] = None
    country: Optional[str] = None
    label: Optional[str] = None
    barcode: Optional[str] = None
    track_count: Optional[int] = None
    genres: Optional[List[str]] = None
    status: Optional[str] = None

@dataclass
class ArtistMetadata:
    """Structured artist metadata from MusicBrainz."""
    type: str = "artist"
    musicbrainz_id: str
    name: str
    sort_name: str
    country: Optional[str] = None
    formed: Optional[str] = None
    disbanded: Optional[str] = None
    artist_type: Optional[str] = None
    genres: Optional[List[str]] = None
    disambiguation: Optional[str] = None

@dataclass
class ProcessingResult:
    """Result of processing a single file."""
    file_path: Path
    success: bool
    action: str  # "updated", "skipped", "failed"
    message: str
    metadata: Optional[Dict[str, Any]] = None
```

---

### 4. File Scanner (`scanner.py`)

**Purpose**: Discover and classify music files

**Key Functions**:

```python
def scan_music_folder(vault_path: Path, music_folder: str) -> List[MusicFile]:
    """
    Recursively scan music folder for markdown files.
    
    Returns:
        List of MusicFile objects with classification
    """
    pass

def classify_file(file_path: Path, music_base: Path) -> str:
    """
    Determine if file is an artist or album based on folder structure.
    
    Logic:
    - If in /artist/ subfolder -> "artist"
    - If in /album/ subfolder -> "album"
    - Otherwise -> raise error (unknown type)
    
    Returns:
        "artist" or "album"
    """
    pass

def parse_existing_file(file_path: Path) -> MusicFile:
    """
    Parse markdown file to extract:
    - Existing frontmatter (if any)
    - Content (preserve everything)
    - Links ([[Artist]] or [[Album]])
    - Whether it already has musicbrainz_id
    
    Returns:
        MusicFile object
    """
    pass

def extract_links(content: str) -> List[str]:
    """
    Extract all [[wiki-style links]] from content.
    
    Returns:
        List of link names (without brackets)
    """
    pass
```

**Logic Details**:
- Use `pathlib` for cross-platform path handling
- Filter for `.md` files only
- Skip hidden files (starting with `.`)
- Detect existing `musicbrainz_id` in frontmatter to avoid re-processing

---

### 5. API Client (`api_client.py`)

**Purpose**: Wrapper around MusicBrainz API with smart error handling

**Key Functions**:

```python
class MusicBrainzClient:
    """Wrapper for MusicBrainz API with rate limiting and error handling."""
    
    def __init__(self, rate_limit: float = 2.0):
        """Initialize client with rate limiting."""
        pass
    
    def search_artist(self, artist_name: str) -> Optional[ArtistMetadata]:
        """
        Search for artist by name and return best match.
        
        Steps:
        1. Search MusicBrainz for artist
        2. Fetch detailed info for top result
        3. Transform to ArtistMetadata
        4. Handle errors gracefully
        
        Returns:
            ArtistMetadata or None if not found
        """
        pass
    
    def search_album(self, album_name: str, artist_name: Optional[str] = None) -> Optional[AlbumMetadata]:
        """
        Search for album/release by name (optionally with artist).
        
        Steps:
        1. Search MusicBrainz for release
        2. Prefer "Official" status releases
        3. Fetch detailed info including artist
        4. Fetch artist details for genres
        5. Transform to AlbumMetadata
        6. Format artist as [[Artist Name]] for Obsidian
        
        Returns:
            AlbumMetadata or None if not found
        """
        pass
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        pass
```

**API Integration Details**:

Using `musicbrainzngs` library:

```python
import musicbrainzngs

# Setup (do once at initialization)
musicbrainzngs.set_useragent(APP_NAME, VERSION, CONTACT)
musicbrainzngs.set_hostname("musicbrainz.org", use_https=True)

# Search for artist
result = musicbrainzngs.search_artists(artist=name, limit=5)
artists = result.get('artist-list', [])

# Get detailed artist info
artist = musicbrainzngs.get_artist_by_id(
    mbid,
    includes=['genres', 'tags']
)['artist']

# Search for album/release
result = musicbrainzngs.search_releases(
    release=album_name,
    artist=artist_name,  # optional
    limit=5
)
releases = result.get('release-list', [])

# Get detailed release info
release = musicbrainzngs.get_release_by_id(
    mbid,
    includes=['artists', 'labels', 'recordings', 'release-groups', 'genres']
)['release']
```

**Error Handling**:
- Catch `musicbrainzngs.WebServiceError`
- Retry logic (up to MAX_RETRIES)
- Exponential backoff on 503 errors
- Log all API errors with context

**Smart Matching**:
- Prefer releases with `status: "Official"`
- Filter out bootlegs and promotional releases
- Handle fuzzy name matching (strip "The", case-insensitive)
- Log match confidence score

---

### 6. Metadata Writer (`metadata_writer.py`)

**Purpose**: Inject/update YAML frontmatter while preserving content

**Key Functions**:

```python
def update_file_with_metadata(
    music_file: MusicFile,
    metadata: Union[AlbumMetadata, ArtistMetadata],
    dry_run: bool = False
) -> ProcessingResult:
    """
    Update markdown file with metadata frontmatter.
    
    Steps:
    1. Parse existing file (using python-frontmatter)
    2. Merge new metadata with existing frontmatter
    3. Preserve all existing content
    4. Write back to file (if not dry-run)
    5. Return ProcessingResult
    
    Behavior:
    - If no frontmatter exists: add it
    - If frontmatter exists: merge (new fields override)
    - Always preserve content after frontmatter
    - Maintain existing formatting
    """
    pass

def merge_frontmatter(
    existing: Dict[str, Any],
    new: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Intelligently merge frontmatter, preserving user additions.
    
    Rules:
    - New metadata fields override existing
    - User-added fields (not in our schema) are preserved
    - Empty/None values don't override existing values
    """
    pass

def format_frontmatter(metadata: Union[AlbumMetadata, ArtistMetadata]) -> Dict[str, Any]:
    """Convert dataclass to dict, removing None values."""
    pass
```

**Implementation with `python-frontmatter`**:

```python
import frontmatter

# Read file
with open(file_path) as f:
    post = frontmatter.load(f)

# post.metadata = existing frontmatter dict
# post.content = content after frontmatter

# Update metadata
post.metadata.update(new_metadata)

# Write back
with open(file_path, 'w') as f:
    f.write(frontmatter.dumps(post))
```

**Special Formatting**:
- Artist links in album frontmatter: `artist: "[[Artist Name]]"`
- Lists in YAML: use list format, not inline
- Dates: Keep as strings in ISO format (YYYY-MM-DD)
- Sort frontmatter keys in a logical order (type first, ID second, etc.)

---

### 7. Logging & Reporting (`logger_setup.py`)

**Logging Levels**:
- **DEBUG**: API requests/responses, file parsing details
- **INFO**: File processing, successful updates
- **WARNING**: Skipped files, ambiguous matches
- **ERROR**: API errors, file write failures

**Output Formats**:

1. **Console Output** (using `rich` library):
   ```
   ╭─────────────────────────────────────────────╮
   │  Obsidian Music Metadata Enricher v1.0     │
   ╰─────────────────────────────────────────────╯
   
   📂 Scanning: /Users/you/vault/music
   
   Found 203 files:
     • 102 artists
     • 101 albums
   
   Processing files...
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 203/203 [02:45<00:00]
   
   ✅ Album: 4:44 by Jay-Z
   ✅ Artist: Jay-Z
   ⚠️  Album: Unknown Album (no match found)
   
   ╭──────────── Summary ────────────╮
   │  ✅ Updated: 180               │
   │  ⏭️  Skipped: 15               │
   │  ❌ Failed: 8                  │
   │  ⏱️  Duration: 2m 45s          │
   ╰──────────────────────────────────╯
   ```

2. **Log File** (`enricher.log`):
   - Standard Python logging format
   - Timestamped entries
   - Full stack traces for errors
   - API request/response details in DEBUG mode

3. **Results JSON** (`enrichment_results.json`):
   ```json
   {
     "timestamp": "2025-10-17T10:30:00Z",
     "vault_path": "/Users/you/vault",
     "total_files": 203,
     "statistics": {
       "updated": 180,
       "skipped": 15,
       "failed": 8
     },
     "results": [
       {
         "file": "music/album/4-44.md",
         "type": "album",
         "status": "updated",
         "musicbrainz_id": "e0a2eae1-3bf6-48b4-9fb8-5e2d0c4c2f42",
         "message": "Successfully enriched"
       }
     ],
     "failures": [
       {
         "file": "music/album/Unknown Album.md",
         "error": "No MusicBrainz match found"
       }
     ]
   }
   ```

---

## Processing Workflow

```
1. INITIALIZATION
   ├─ Parse CLI arguments
   ├─ Set up logging
   ├─ Initialize MusicBrainz API client
   └─ Create backup directory (if --backup)

2. FILE DISCOVERY
   ├─ Scan music folder recursively
   ├─ Filter .md files
   ├─ Classify as artist or album
   └─ Parse existing frontmatter/content

3. PROCESSING LOOP (with progress bar)
   For each file:
   ├─ Check if already processed (has musicbrainz_id)
   │  └─ Skip unless --force-update
   │
   ├─ Extract name from filename
   │  └─ Remove .md extension
   │  └─ Decode URL-encoded characters
   │
   ├─ API LOOKUP
   │  ├─ If album: search_album(name, artist_hint_from_links)
   │  └─ If artist: search_artist(name)
   │
   ├─ VALIDATE MATCH
   │  ├─ Check confidence score
   │  ├─ Log ambiguous matches
   │  └─ Allow manual review in dry-run
   │
   ├─ UPDATE FILE
   │  ├─ Merge frontmatter
   │  ├─ Preserve content
   │  └─ Write (if not dry-run)
   │
   ├─ RATE LIMIT
   │  └─ Sleep 2 seconds before next request
   │
   └─ LOG RESULT

4. COMPLETION
   ├─ Display summary statistics
   ├─ Save results.json
   └─ Exit with appropriate code
```

---

## Edge Cases & Error Handling

### File System
- **Permission errors**: Log and skip, don't crash
- **Missing folders**: Create if needed (with confirmation)
- **Unicode filenames**: Handle properly with pathlib
- **Locked files**: Skip with warning

### API Issues
- **No match found**: Log, skip, continue processing
- **Multiple matches**: Pick best (prefer Official releases), log alternatives
- **Rate limiting (503)**: Exponential backoff, retry
- **Network errors**: Retry with backoff, eventually skip
- **Malformed responses**: Catch parsing errors, log raw response

### Data Quality
- **Missing fields**: Don't add field if data unavailable (avoid `None` in frontmatter)
- **Duplicate MBIDs**: Allow (some files may legitimately reference same entity)
- **Conflicting metadata**: New data overwrites old unless --preserve-existing

### User Errors
- **Invalid vault path**: Clear error message, suggest correction
- **No music folder**: Create or exit with instruction
- **Empty results**: Friendly message, not an error

---

## Configuration Options

### CLI Arguments

```
Required:
  --vault-path PATH         Path to Obsidian vault

Optional:
  --music-folder NAME       Music folder name (default: "music")
  --dry-run                 Preview changes without modifying files
  --backup                  Create backup before processing
  --force-update            Re-process files with existing musicbrainz_id
  --skip-albums             Only process artists
  --skip-artists            Only process albums
  --log-level LEVEL         DEBUG, INFO, WARNING, ERROR (default: INFO)
  --output-log PATH         Save results JSON to file
  --contact EMAIL           Email for MusicBrainz User-Agent
  --rate-limit SECONDS      Seconds between API calls (default: 2.0)
```

### Environment Variables (Optional)

```bash
export MUSICBRAINZ_CONTACT="user@example.com"
export VAULT_PATH="/Users/you/Documents/vault"
```

---

## Success Criteria

### Functional Requirements ✅
- [ ] Successfully processes 200 files in ~7-10 minutes (2sec/file)
- [ ] Preserves all existing content and user-added frontmatter
- [ ] Adds structured YAML frontmatter matching schema
- [ ] Handles artists and albums correctly
- [ ] Respects rate limiting (2 second delays)
- [ ] Provides real-time progress indication
- [ ] Generates detailed logs and summary report
- [ ] Supports dry-run mode
- [ ] Handles errors gracefully without crashing

### Quality Requirements ✅
- [ ] Code is well-documented with docstrings
- [ ] Error messages are clear and actionable
- [ ] Console output is informative and beautiful
- [ ] API matching accuracy >90%
- [ ] Zero data loss (all content preserved)
- [ ] Idempotent (safe to run multiple times)

### User Experience ✅
- [ ] Single command execution
- [ ] Clear progress indication
- [ ] Summary shows what changed
- [ ] Easy to review results before committing
- [ ] Helpful error messages with suggested fixes

---

## Testing Strategy

### Unit Tests
- `test_scanner.py`: File discovery, classification, link extraction
- `test_api_client.py`: API responses, error handling, rate limiting
- `test_metadata_writer.py`: Frontmatter merging, content preservation

### Integration Tests
- Test with small sample vault (10 files)
- Verify dry-run doesn't modify files
- Verify actual run modifies correctly
- Test backup functionality

### Manual Testing
- Run on actual 200-file vault
- Verify Dataview queries work in Obsidian
- Check various edge cases (Unicode, special chars, etc.)

---

## Example Output Files

### Album File (After Processing)

`music/album/4-44.md`:
```markdown
---
type: album
musicbrainz_id: e0a2eae1-3bf6-48b4-9fb8-5e2d0c4c2f42
title: '4:44'
artist: '[[Jay-Z]]'
artist_mbid: f82bcf78-5b69-4622-a5ef-73800768d9ac
release_date: '2017-06-30'
country: US
label: Roc Nation
barcode: '887254822424'
track_count: 10
genres:
  - hip hop
  - east coast hip hop
  - rap
status: official
---

## My Notes

This album is incredible. The production is top-tier.

## Favorite Tracks
- The Story of O.J.
- 4:44
- Family Feud
```

### Artist File (After Processing)

`music/artist/Jay-Z.md`:
```markdown
---
type: artist
musicbrainz_id: f82bcf78-5b69-4622-a5ef-73800768d9ac
name: Jay-Z
sort_name: Jay-Z
country: US
formed: '1990'
artist_type: person
genres:
  - hip hop
  - east coast hip hop
  - rap
  - gangsta rap
  - pop rap
disambiguation: US rapper
---

## Biography

One of the greatest rappers of all time. Started his career in Brooklyn...

## Discography
- [[Reasonable Doubt]]
- [[The Blueprint]]
- [[4-44|4:44]]
```

---

## Installation & Usage

### Installation

```bash
# Clone or download the project
cd obsidian-music-enricher

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Requirements File

`requirements.txt`:
```
musicbrainzngs>=0.7.1
PyYAML>=6.0
python-frontmatter>=1.0.0
rich>=13.0.0
```

### Usage

```bash
# Dry run (preview changes)
python enricher.py --vault-path ~/Documents/vault --dry-run

# Actual run with backup
python enricher.py \
    --vault-path ~/Documents/vault \
    --backup \
    --contact your-email@example.com

# Force update all files
python enricher.py \
    --vault-path ~/Documents/vault \
    --force-update

# Only process albums
python enricher.py \
    --vault-path ~/Documents/vault \
    --skip-artists

# Custom music folder location
python enricher.py \
    --vault-path ~/Documents/vault \
    --music-folder "media/music"
```

---

## Implementation Phases

### Phase 1: Core Infrastructure ⭐ (Priority)
1. Set up project structure
2. Implement scanner.py (file discovery)
3. Implement logger_setup.py
4. Basic CLI with dry-run
5. **Deliverable**: Can scan and list files with progress bar

### Phase 2: API Integration ⭐ (Priority)
1. Implement api_client.py
2. Test with sample queries
3. Add rate limiting
4. Error handling and retries
5. **Deliverable**: Can fetch metadata from MusicBrainz

### Phase 3: Metadata Writing ⭐ (Priority)
1. Implement metadata_writer.py
2. Test frontmatter preservation
3. Test content preservation
4. Implement backup functionality
5. **Deliverable**: Can safely update files

### Phase 4: Integration & Polish
1. Connect all components in enricher.py
2. Add rich console output
3. Generate results JSON
4. Test with full vault
5. **Deliverable**: Production-ready tool

### Phase 5: Nice-to-Haves (Optional)
- Resume capability (save progress, resume on failure)
- Interactive mode (manual review of ambiguous matches)
- Cover art downloading (from Cover Art Archive)
- Support for other music APIs (Spotify, Last.fm)
- Web UI for easier use

---

## Known Limitations

1. **MusicBrainz Coverage**: Not all artists/albums are in the database
2. **Name Matching**: Ambiguous names may match wrong entities
3. **Rate Limiting**: Takes time to process large collections (2 sec/file)
4. **Manual Review**: Some matches may need human verification
5. **Network Required**: No offline mode

---

## Future Enhancements

- Add `--interactive` mode for manual match selection
- Support for additional metadata sources (Spotify, Discogs, Last.fm)
- Cover art downloading and linking
- Batch processing modes (albums-only pass, artists-only pass)
- Web UI for easier operation
- Cloud vault support (via Obsidian Sync API)
- Undo functionality
- Match confidence scoring with manual review threshold

---

## Notes for Claude Code

### Best Practices
- Use `pathlib` for all file operations (cross-platform)
- Use `rich` for beautiful console output
- Use `musicbrainzngs` library (don't reinvent API client)
- Use `python-frontmatter` for markdown parsing
- Comprehensive error handling (don't crash on single file failure)
- Preserve user data at all costs

### Testing
- Test with a small sample vault first
- Always test dry-run before actual run
- Verify frontmatter YAML is valid
- Check that Obsidian can parse the output files

### Documentation
- Add docstrings to all functions
- Include usage examples in README
- Document all CLI arguments
- Add inline comments for complex logic

### Code Style
- Follow PEP 8
- Type hints for all functions
- Descriptive variable names
- Keep functions focused and small

---

## Questions for User (if any arise during implementation)

1. Should we preserve the order of existing frontmatter fields?
2. How to handle files with ambiguous matches (multiple good results)?
3. Should we add a `last_updated` timestamp field?
4. What to do with files that already have different metadata?
5. Should we validate that [[Artist]] links actually exist as files?

---

## Deliverables

✅ **Primary Deliverable**: `enricher.py` and supporting modules  
✅ **Documentation**: README.md with usage instructions  
✅ **Dependencies**: requirements.txt  
✅ **Logs**: Detailed log file and results JSON  
✅ **Examples**: Sample output files showing the result  

---

## Contact & Support

For questions or issues during implementation, refer to:
- MusicBrainz API Docs: https://musicbrainz.org/doc/MusicBrainz_API
- musicbrainzngs Docs: https://python-musicbrainzngs.readthedocs.io/
- python-frontmatter: https://python-frontmatter.readthedocs.io/

---

**End of Specification**

This specification provides a complete blueprint for implementing the Obsidian Music Metadata Enricher. All major decisions are documented, edge cases considered, and the architecture is clearly defined.
