# Obsidian Music Metadata Enricher

## Overview
Brief description of what this tool does - enriches Obsidian markdown files for music artists and albums with MusicBrainz metadata while preserving existing content.

## Features
- Scans Obsidian vault for artist and album markdown files
- Fetches metadata from MusicBrainz API
- Updates YAML frontmatter while preserving existing notes
- Rate-limited API calls (2 seconds between requests)
- Dry-run mode for safe testing
- Rich progress bars and logging

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ObsidianMusicSorter.git
cd ObsidianMusicSorter

# Install dependencies using UV
uv sync
```

## Usage

```bash
# Coming in Phase 4 - CLI implementation
uv run python -m src.cli enrich --vault-path ~/Obsidian/Vault
```

## Configuration
Environment variables:
- `MUSIC_SORTER_VAULT_PATH`: Path to Obsidian vault
- `MUSIC_SORTER_RATE_LIMIT_SECONDS`: API rate limit (default: 2.0)
- `MUSIC_SORTER_DRY_RUN`: Enable dry-run mode (default: false)
- `MUSIC_SORTER_LOG_LEVEL`: Logging level (default: INFO)

## Project Status
🚧 **Phase 1 Complete**: Core infrastructure (scanner, config, logging)
🔄 **Phase 2 In Progress**: API integration
⏳ **Phase 3 Pending**: Metadata writing
⏳ **Phase 4 Pending**: CLI orchestrator

## Development

Run tests:
```bash
uv run pytest
```

## License
MIT License

## Contributing
Contributions welcome! Please open an issue or PR.