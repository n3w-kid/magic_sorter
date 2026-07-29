from pathlib import Path

from magic_sorter_x.parsers import parse_text


def test_relaxed_json_comments_and_trailing_comma() -> None:
    doc = parse_text('{// comment\n"answer": 42,}', Path("x.jsonc"))
    assert doc.kind == "json"
    assert doc.data == {"answer": 42}


def test_csv() -> None:
    doc = parse_text("name,score\nAda,10\n", Path("x.csv"))
    assert doc.kind == "csv"
    assert doc.data == [{"name": "Ada", "score": "10"}]


def test_plain_text() -> None:
    doc = parse_text("hello", Path("x.txt"))
    assert doc.kind == "text"
    assert doc.data == "hello"
