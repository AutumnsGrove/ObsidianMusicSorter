# Phase 2 - Next Steps

## What Was Accomplished in Phase 1

✅ **73 out of 106 files successfully enriched** (69% success rate!)
- Artists: Automatically matched by filename
- Albums: Many matched, some need manual correction
- All enriched with MusicBrainz IDs, genres, countries, release dates, etc.

✅ **Tool Improvements:**
- Auto-detect file type from directory structure (Artists/Albums folders)
- Use filename as fallback when `name` field is missing
- Made `sort_name` optional in metadata model

## Issues to Address Before Phase 2

### 0. Write Type Field During Enrichment
**Problem:** The `type` field (artist/album) is inferred during scanning but not written to files

**Solution Needed:**
- In `metadata_writer.py`, ensure we write the `type` field
- For artist files: set `type: artist`
- For album files: set `type: album`

**Fix in `src/metadata_writer.py`:**
```python
# In update_artist_file():
post["type"] = "artist"

# In update_album_file():
post["type"] = "album"
```

### 1. Obsidian Link Aliases
**Problem:** Obsidian uses pipe syntax for link aliases:
```markdown
artist: '[[Mac Miller|Mac Miller]]'
```

**Solution Needed:**
- Update parser to handle `[[Path/To/File|Display Name]]` format
- Extract just the artist name part (after the pipe) when searching MusicBrainz
- Or strip the path entirely and use display name

### 2. Skip Already-Complete Files
**Problem:** Re-running will ping API for files that already have all metadata

**Solution Needed:**
- Check if file has:
  - `musicbrainz_id` (required)
  - `name` or `title` (required)
  - `genres` (should have at least 1)
  - For albums: `artist`, `artist_mbid`, `release_date`
- Skip API call if all required fields are present and non-empty
- Only enrich files missing data

### 3. Manual Corrections Needed
**Files to Review:**
- **IGOR.md** - Wrong artist (got "Purveyors of the Irregular" instead of Tyler, the Creator)
- **27 error files** - No MusicBrainz matches found or validation errors
- Check albums with generic names that might have matched incorrectly

## Phase 2 Implementation Plan

### Step 1: Update Artist Link Parser
**File:** `src/enricher.py` (lines ~249-251)

```python
# Current code:
artist_name = post.get("artist")
if artist_name:
    artist_name = artist_name.replace("[[", "").replace("]]", "")

# Needs to handle:
# - [[Mac Miller]] → Mac Miller
# - [[Knowledge/Music/Artists/Mac Miller|Mac Miller]] → Mac Miller
# - [[Knowledge/Music/Artists/Mac Miller]] → Mac Miller
```

**Fix:**
```python
artist_name = post.get("artist")
if artist_name:
    # Remove [[ and ]]
    artist_name = artist_name.replace("[[", "").replace("]]", "")
    # If pipe exists, take the display name (after pipe)
    if "|" in artist_name:
        artist_name = artist_name.split("|")[-1].strip()
    # If path exists, take the last part
    elif "/" in artist_name:
        artist_name = artist_name.split("/")[-1].strip()
```

### Step 2: Add Smart Skipping Logic
**File:** `src/enricher.py` - Update `_should_process_file()` method (line ~318)

**Current logic:** Only checks if `name` exists

**New logic needed:**
```python
def _should_process_file(self, file_path: Path) -> bool:
    """Check if file needs processing based on metadata completeness."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Must have a name/title
        name = post.get("name") or post.get("title") or file_path.stem
        if not name:
            return False

        # If has MusicBrainz ID and genres, consider it complete
        mbid = post.get("musicbrainz_id") or post.get("mbid")
        genres = post.get("genres", [])

        # Skip if already complete
        if mbid and genres and len(genres) > 0:
            self.logger.info(f"Skipping {file_path.name} - already enriched")
            return False

        return True
    except Exception as e:
        self.logger.error(f"Error checking file {file_path}: {e}")
        return False
```

### Step 3: Run Phase 2 Enrichment

After manual corrections are complete:

```bash
cd /Users/autumn/Documents/Projects/ObsidianMusicSorter
uv run python -m src.cli enrich "/Users/autumn/AutumnsGarden/Knowledge/Music" --log-level INFO
```

**Expected Results:**
- Skip ~73 already-enriched files
- Process ~27 error files that were manually fixed
- Fill in missing metadata for incomplete files
- Use corrected artist links for better album matching

## Backup Location

Backup created before Phase 1:
```
/Users/autumn/AutumnsGarden/Knowledge/Music_backup_20251017_112119
```

Keep this backup until Phase 2 is complete and verified!

## Testing Recommendations

Before full Phase 2 run, test on a few files:

1. Create test directory:
   ```bash
   mkdir -p /tmp/phase2_test/Artists /tmp/phase2_test/Albums
   ```

2. Copy a few corrected files:
   ```bash
   cp "/Users/autumn/AutumnsGarden/Knowledge/Music/Albums/IGOR.md" /tmp/phase2_test/Albums/
   cp "/Users/autumn/AutumnsGarden/Knowledge/Music/Artists/Tyler, the Creator.md" /tmp/phase2_test/Artists/
   ```

3. Run enrichment:
   ```bash
   uv run python -m src.cli enrich /tmp/phase2_test --log-level INFO
   ```

4. Verify:
   - Already-complete files are skipped
   - Obsidian links are parsed correctly
   - No unnecessary API calls

## Summary Stats from Phase 1

```
Total Files Found: 106
Files Processed:   106
Files Enriched:    73 (69%)
Files Skipped:     6
Errors:            27
```

**Artists enriched:** 51 files
**Albums enriched:** ~22 files (many had no artist context, causing wrong matches)

## Questions to Consider

1. Should we add a `--force` flag to re-enrich already-complete files?
2. Should we add album genres from artist genres as fallback?
3. Should we log a report of files that need manual review?
4. Should we add validation for common wrong matches (e.g., country: XW)?

---

**Next conversation:** After manual corrections, we'll implement the fixes above and run Phase 2!
