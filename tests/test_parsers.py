from pathlib import Path
import unittest

from magic_sorter_x.parsers import parse_text


class ParserTests(unittest.TestCase):
    def test_relaxed_json_comments_and_trailing_comma(self) -> None:
        doc = parse_text('{// comment\n"answer": 42,}', Path("x.jsonc"))
        self.assertEqual(doc.kind, "json")
        self.assertEqual(doc.data, {"answer": 42})

    def test_csv(self) -> None:
        doc = parse_text("name,score\nAda,10\n", Path("x.csv"))
        self.assertEqual(doc.kind, "csv")
        self.assertEqual(doc.data, [{"name": "Ada", "score": "10"}])

    def test_plain_text(self) -> None:
        doc = parse_text("hello", Path("x.txt"))
        self.assertEqual(doc.kind, "text")
        self.assertEqual(doc.data, "hello")

    def test_yaml(self) -> None:
        doc = parse_text("name: Magic\nitems:\n  - one\n  - two\n", Path("x.yaml"))
        self.assertEqual(doc.kind, "yaml")
        self.assertEqual(doc.data, {"name": "Magic", "items": ["one", "two"]})

    def test_toml(self) -> None:
        doc = parse_text('name = "Magic"\n[stats]\nversion = 2\n', Path("x.toml"))
        self.assertEqual(doc.kind, "toml")
        self.assertEqual(doc.data["stats"]["version"], 2)
