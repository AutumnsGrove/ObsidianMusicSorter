# Claude Code Implementation Prompt

Implement the Obsidian Music Metadata Enricher following the PROJECT_SPEC.md exactly.

## Critical Instructions

**DELEGATION STRATEGY**: Use subagents extensively. Delegate ALL coding and testing work to the **haiku coder subagent** - it's very fast and should be your primary worker for:
- Writing all Python modules (scanner.py, api_client.py, metadata_writer.py, etc.)
- Creating test files
- Implementing utility functions
- Any file creation or code modification
- Running tests and debugging

**YOUR ROLE**: You are the architect and coordinator. Plan, delegate, review, and integrate.

## Implementation Workflow

### Phase 1: Setup & Core Infrastructure
1. Create project structure (delegate to haiku):
   - All Python module files from spec
   - requirements.txt
   - README.md
   - tests/ directory

2. Implement scanner.py (delegate to haiku):
   - File discovery with pathlib
   - Artist/album classification based on /artist/ and /album/ folders
   - Frontmatter parsing with python-frontmatter
   - Link extraction from content

3. Implement logger_setup.py (delegate to haiku):
   - Configure Python logging
   - Rich console output setup
   - JSON results writer

### Phase 2: API Integration
4. Implement config.py (delegate to haiku):
   - All constants from spec
   - 2-second rate limiting
   - MusicBrainz configuration

5. Implement models.py (delegate to haiku):
   - All dataclasses: MusicFile, AlbumMetadata, ArtistMetadata, ProcessingResult
   - Use exact field specifications from spec

6. Implement api_client.py (delegate to haiku):
   - MusicBrainzClient class
   - Use musicbrainzngs library
   - search_artist() and search_album() methods
   - Rate limiting enforcement (2 seconds)
   - Error handling with retries
   - Prefer "Official" releases

### Phase 3: Metadata Writing
7. Implement metadata_writer.py (delegate to haiku):
   - update_file_with_metadata()
   - merge_frontmatter() with preservation logic
   - Use python-frontmatter for safe writing
   - Artist links formatted as [[Artist Name]]

8. Implement utils.py (delegate to haiku):
   - Helper functions as needed
   - Filename sanitization
   - Link extraction utilities

### Phase 4: Main Orchestrator
9. Implement enricher.py (delegate to haiku):
   - CLI with argparse (all arguments from spec)
   - Workflow orchestration following spec's "Processing Workflow" section
   - Rich progress bars
   - Summary statistics
   - Dry-run mode support
   - Backup functionality

### Phase 5: Testing & Polish
10. Create tests (delegate to haiku):
    - test_scanner.py
    - test_api_client.py
    - test_metadata_writer.py

11. Create documentation (delegate to haiku):
    - README.md with installation and usage
    - Example command-line invocations

## Specific Requirements

**Rate Limiting**: MUST enforce 2-second delays between MusicBrainz API calls
**Content Preservation**: MUST preserve all existing markdown content - test this thoroughly
**Folder Structure**: Files in /artist/ = artists, /album/ = albums (no ambiguity)
**Frontmatter Format**: Use exact YAML schemas from spec (AlbumMetadata and ArtistMetadata)
**Error Handling**: Graceful failures - log and continue, never crash on single file
**Progress Indication**: Use rich library for beautiful progress bars
**Idempotent**: Safe to run multiple times (skip files with musicbrainz_id unless --force-update)

## Testing Strategy

Delegate all testing to haiku coder:
1. Unit test each module independently
2. Integration test with sample markdown files
3. Test dry-run mode doesn't modify files
4. Test frontmatter preservation
5. Verify YAML output is valid

## Delegation Pattern

For EVERY implementation task:
```
You: "I need scanner.py implemented per the spec. Here are the requirements: [summarize from spec]"
↓
Haiku Coder: [implements the module]
↓
You: [review, test, integrate]
```

Do NOT write code yourself. Always delegate to haiku coder subagent.

## Success Criteria

- [ ] All modules from spec are implemented
- [ ] CLI accepts all arguments from spec
- [ ] Dry-run mode works correctly
- [ ] Real run successfully updates files with frontmatter
- [ ] All existing content is preserved
- [ ] Rate limiting is enforced (2 sec between API calls)
- [ ] Progress bars show real-time status
- [ ] Summary report is generated
- [ ] Tests pass
- [ ] README documents usage clearly

## Final Deliverable

Working Python application that:
- Takes `--vault-path` and `--music-folder` arguments
- Scans for .md files in /artist/ and /album/ subfolders
- Enriches them with MusicBrainz metadata
- Preserves all existing content
- Shows beautiful progress bars
- Generates detailed logs and summary
- Handles ~200 files in ~7-10 minutes

## Key Reminder

**USE SUBAGENTS**: Delegate ALL coding to haiku coder. It's fast and efficient. You orchestrate, review, and integrate. Follow the spec exactly - it contains all the details you need.
