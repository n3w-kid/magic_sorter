from pathlib import Path

from magic_sorter_x.emojify import emojified_name, emoji_for


def test_known_extension() -> None:
    path = Path("data.json")
    assert emoji_for(path) == "🧩"
    assert emojified_name(path) == "🧩 data.json"


def test_does_not_double_prefix() -> None:
    assert emojified_name(Path("🐍 app.py")) == "🐍 app.py"
