# Music Metadata Enhancer

## Overview
A powerful tool that enriches Obsidian markdown files for music artists and albums with MusicBrainz metadata while preserving existing content.

## Features
- Scans Obsidian vault for artist and album markdown files
- Fetches metadata from MusicBrainz API
- Updates YAML frontmatter while preserving existing notes
- Rate-limited API calls
- Dry-run mode for safe testing
- Rich progress bars and logging

## Installation

### As a UV Tool (Recommended)
Install globally with UV:
```bash
uv tool install music-metadata-enhancer
```

### From Source
```bash
git clone https://github.com/AutumnsGrove/ObsidianMusicSorter.git
cd ObsidianMusicSorter
uv sync
```

## Usage

### Quick Start
```bash
# Scan your vault to see what would be processed
music-metadata-enhancer scan ~/Obsidian/Vault

# Or use the short alias
mme scan ~/Obsidian/Vault

# Dry run to see what would change
mme enrich ~/Obsidian/Vault --dry-run

# Enrich your vault for real
mme enrich ~/Obsidian/Vault
```

### Options
```bash
# Custom rate limiting (default: 2.0 seconds)
mme enrich ~/Obsidian/Vault --rate-limit 3.0

# Debug logging
mme enrich ~/Obsidian/Vault --log-level DEBUG

# Dry run mode
mme enrich ~/Obsidian/Vault --dry-run
```

## How It Works
1. Scan the Obsidian vault for markdown files related to artists and albums
2. Use MusicBrainz API to fetch additional metadata
3. Intelligently update YAML frontmatter without overwriting existing notes
4. Provide detailed logging and optional dry-run mode for safety

## Configuration
Environment variables:
- `MUSIC_SORTER_VAULT_PATH`: Path to Obsidian vault
- `MUSIC_SORTER_RATE_LIMIT_SECONDS`: API rate limit (default: 2.0)
- `MUSIC_SORTER_DRY_RUN`: Enable dry-run mode (default: false)
- `MUSIC_SORTER_LOG_LEVEL`: Logging level (default: INFO)

## Project Status
**Status**: Complete and Ready for Use
- ✅ Core infrastructure
- ✅ API integration
- ✅ Metadata writing
- ✅ CLI orchestrator

## Development

Run tests:
```bash
uv run pytest
```

## License
MIT License

## Contributing
Contributions welcome! Please open an issue or PR.