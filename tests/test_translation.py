import unittest

from magic_sorter_x.translation import translate_value, translate_xml_value


class FakeTranslator:
    name = "fake"

    def translate(self, text: str) -> str:
        return f"EN({text})"


class CountingTranslator:
    name = "counting"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def translate(self, text: str) -> str:
        self.calls.append(text)
        return text.upper()


class TranslationTests(unittest.TestCase):
    def test_recursive_translation_preserves_non_strings(self) -> None:
        value = {"title": "bonjour", "count": 3, "items": ["hola", True]}
        self.assertEqual(
            translate_value(value, FakeTranslator()),
            {"title": "EN(bonjour)", "count": 3, "items": ["EN(hola)", True]},
        )

    def test_translate_keys(self) -> None:
        self.assertEqual(
            translate_value({"titre": "bonjour"}, FakeTranslator(), True),
            {"EN(titre)": "EN(bonjour)"},
        )

    def test_duplicate_strings_are_cached(self) -> None:
        translator = CountingTranslator()
        result = translate_value(["hola", "hola"], translator)
        self.assertEqual(result, ["HOLA", "HOLA"])
        self.assertEqual(translator.calls, ["hola"])

    def test_xml_translation_preserves_attributes(self) -> None:
        value = {"root": {"@attributes": {"lang": "fr", "id": "bonjour"}, "title": "bonjour"}}
        self.assertEqual(
            translate_xml_value(value, FakeTranslator()),
            {"root": {"@attributes": {"lang": "fr", "id": "bonjour"}, "title": "EN(bonjour)"}},
        )
