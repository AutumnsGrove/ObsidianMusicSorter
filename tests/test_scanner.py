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
    - Expected number of files are detected
    """
    result = scan_vault(temp_vault)

    assert len(result) == 4, f"Expected 4 files, found {len(result)}"

    # Verify file types are correctly identified
    artist_files = [f for f in result if f.get('type') == 'artist']
    album_files = [f for f in result if f.get('type') == 'album']

    assert len(artist_files) == 2, "Should find 2 artist files"
    assert len(album_files) == 2, "Should find 2 album files"

def test_file_type_categorization(temp_vault):
    """
    Test file type categorization functionality.

    Verifies correct identification of artist and album files.
    """
    result = scan_vault(temp_vault)

    # Check artist files
    jay_z_file = next((f for f in result if f.get('name') == 'Jay-Z'), None)
    assert jay_z_file is not None, "Should find Jay-Z artist file"
    assert jay_z_file.get('type') == 'artist', "Jay-Z file should be categorized as artist"

    # Check album files
    renaissance_file = next((f for f in result if f.get('name') == 'Renaissance'), None)
    assert renaissance_file is not None, "Should find Renaissance album file"
    assert renaissance_file.get('type') == 'album', "Renaissance file should be categorized as album"

def test_no_frontmatter_handling(temp_vault):
    """
    Test handling of files without proper frontmatter.

    Validates that files without valid frontmatter are either
    skipped or handled gracefully.
    """
    result = scan_vault(temp_vault)

    # Count files with no type (i.e., skipped or unrecognized)
    no_type_files = [f for f in result if 'type' not in f]

    assert len(no_type_files) <= 2, "Should handle or skip files without complete frontmatter"

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

    # Verify that an invalid YAML file doesn't break the entire scanning process
    valid_files = [f for f in result if 'type' in f]

    assert len(valid_files) >= 4, "Should still process valid files even with an invalid YAML file"