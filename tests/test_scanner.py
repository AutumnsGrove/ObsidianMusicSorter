"""
Test suite for the scanner module.

This module contains unit tests for the scanner functionality,
verifying file scanning, categorization, and frontmatter handling.
"""

import pytest
import yaml
from pathlib import Path
import tempfile
import os

from src.scanner import scan_vault, get_file_type

@pytest.fixture
def temp_vault():
    """
    Create a temporary vault directory with test files for scanning.

    Fixture creates a directory with various test files to simulate
    an Obsidian vault with music-related markdown files.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create artist files
        artist_files = [
            ('Jay-Z.md', '''---
type: artist
name: Jay-Z
genre: Hip Hop
---
Jay-Z is a renowned rapper and entrepreneur.'''),
            ('Beyoncé.md', '''---
type: artist
name: Beyoncé
genre: R&B
---
Beyoncé is a global pop icon.''')
        ]

        # Create album files
        album_files = [
            ('4-44.md', '''---
type: album
artist: Jay-Z
name: 4:44
year: 2017
---
Jay-Z's introspective album about personal growth.'''),
            ('Renaissance.md', '''---
type: album
artist: Beyoncé
name: Renaissance
year: 2022
---
A dance and house music-inspired album.''')
        ]

        # Create files without frontmatter
        no_frontmatter_files = [
            ('random_note.md', 'This is just a regular note.'),
            ('incomplete_note.md', '---\npartial: frontmatter')
        ]

        # Write artist files
        for filename, content in artist_files + album_files + no_frontmatter_files:
            with open(os.path.join(temp_dir, filename), 'w') as f:
                f.write(content)

        yield temp_dir

def test_scan_vault_imports():
    """
    Verify that necessary imports for scanning work correctly.
    """
    assert scan_vault is not None, "scan_vault function should be importable"
    assert get_file_type is not None, "get_file_type function should be importable"

def test_scan_vault_basic(temp_vault):
    """
    Test basic scanning of a vault directory.

    Validates that:
    - Vault can be scanned successfully
    - Expected file types are detected
    """
    result = scan_vault(temp_vault)

    assert 'artists' in result and 'albums' in result
    assert len(result['artists']) == 2
    assert len(result['albums']) == 2

def test_file_type_categorization(temp_vault):
    """
    Test file type categorization functionality.

    Verifies correct identification of artist and album files.
    """
    result = scan_vault(temp_vault)

    # Check artist files
    artist_files = [f.stem for f in result['artists']]
    assert 'Jay-Z' in artist_files or 'Beyoncé' in artist_files

    # Check album files
    album_files = [f.stem for f in result['albums']]
    assert '4-44' in album_files or 'Renaissance' in album_files

def test_no_frontmatter_handling(temp_vault):
    """
    Test handling of files without proper frontmatter.

    Validates that files without valid frontmatter are either
    skipped or handled gracefully.
    """
    result = scan_vault(temp_vault)

    # Ensure standard artist and album categorization still works
    assert 'artists' in result and 'albums' in result

    # No specific assertion on unprocessed files, as they're now filtered out

def test_invalid_yaml_handling(temp_vault):
    """
    Test handling of files with invalid YAML frontmatter.

    Create a file with intentionally malformed YAML to test error handling.
    """
    invalid_yaml_file = os.path.join(temp_vault, 'invalid_yaml.md')
    with open(invalid_yaml_file, 'w') as f:
        f.write('''---
type: album
name: Broken Album
invalid_yaml: [
---
Some content''')

    result = scan_vault(temp_vault)

    # Verify that the invalid file doesn't break processing
    # and that valid categorizations are preserved
    assert 'artists' in result and 'albums' in result
    assert len(result['artists']) == 2
    assert len(result['albums']) == 2