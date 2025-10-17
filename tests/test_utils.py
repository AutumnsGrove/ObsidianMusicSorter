import unittest
from src.utils import (
    format_obsidian_link,
    sanitize_filename,
    parse_date,
    merge_genres,
    extract_mbid_from_frontmatter,
)


class TestUtilsFunctions(unittest.TestCase):
    def test_format_obsidian_link(self):
        self.assertEqual(format_obsidian_link("Jay-Z"), "[[Jay-Z]]")
        with self.assertRaises(ValueError):
            format_obsidian_link("")

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("Beyoncé / Singles"), "Beyonce-Singles")
        self.assertEqual(
            sanitize_filename("File with: invalid ? characters"),
            "File-with-invalid-characters",
        )
        with self.assertRaises(ValueError):
            sanitize_filename("")

    def test_parse_date(self):
        self.assertEqual(parse_date("2020"), "2020-01-01")
        self.assertEqual(parse_date("2020-05"), "2020-05-01")
        self.assertEqual(parse_date("2020-05-15"), "2020-05-15")
        self.assertIsNone(parse_date("Invalid Date"))

    def test_merge_genres(self):
        self.assertEqual(
            merge_genres(["Rock", "Jazz"], ["Jazz", "Blues"]), ["Rock", "Jazz", "Blues"]
        )
        self.assertEqual(merge_genres([], ["Pop", "Electronic"]), ["Pop", "Electronic"])

    def test_extract_mbid_from_frontmatter(self):
        self.assertEqual(
            extract_mbid_from_frontmatter({"musicbrainz_id": "abc123"}), "abc123"
        )
        self.assertEqual(extract_mbid_from_frontmatter({"mbid": "def456"}), "def456")
        self.assertIsNone(extract_mbid_from_frontmatter({}))


if __name__ == "__main__":
    unittest.main()
