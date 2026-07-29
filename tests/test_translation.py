from magic_sorter_x.translation import translate_value, translate_xml_value


class FakeTranslator:
    name = "fake"

    def translate(self, text: str) -> str:
        return f"EN({text})"


def test_recursive_translation_preserves_non_strings() -> None:
    value = {"title": "bonjour", "count": 3, "items": ["hola", True]}
    assert translate_value(value, FakeTranslator()) == {
        "title": "EN(bonjour)",
        "count": 3,
        "items": ["EN(hola)", True],
    }


def test_translate_keys() -> None:
    assert translate_value({"titre": "bonjour"}, FakeTranslator(), True) == {
        "EN(titre)": "EN(bonjour)"
    }

class CountingTranslator:
    name = "counting"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def translate(self, text: str) -> str:
        self.calls.append(text)
        return text.upper()


def test_duplicate_strings_are_cached() -> None:
    translator = CountingTranslator()
    result = translate_value(["hola", "hola"], translator)
    assert result == ["HOLA", "HOLA"]
    assert translator.calls == ["hola"]


def test_xml_translation_preserves_attributes() -> None:
    value = {
        "root": {
            "@attributes": {"lang": "fr", "id": "bonjour"},
            "title": "bonjour",
        }
    }
    assert translate_xml_value(value, FakeTranslator()) == {
        "root": {
            "@attributes": {"lang": "fr", "id": "bonjour"},
            "title": "EN(bonjour)",
        }
    }
