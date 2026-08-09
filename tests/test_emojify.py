from pathlib import Path
import unittest

from magic_sorter_x.emojify import emojified_name, emoji_for


class EmojifyTests(unittest.TestCase):
    def test_known_extension(self) -> None:
        path = Path("data.json")
        self.assertEqual(emoji_for(path), "🧩")
        self.assertEqual(emojified_name(path), "🧩 data.json")

    def test_does_not_double_prefix(self) -> None:
        self.assertEqual(emojified_name(Path("🐍 app.py")), "🐍 app.py")
