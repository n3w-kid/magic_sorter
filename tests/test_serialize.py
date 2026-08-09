import tomllib
import unittest
import xml.etree.ElementTree as ET

from magic_sorter_x.parsers import parse_text
from magic_sorter_x.serialize import serialize


class SerializeTests(unittest.TestCase):
    def test_xml_round_trip(self) -> None:
        document = parse_text('<root lang="fr"><title>Bonjour</title><item>A</item><item>B</item></root>')
        self.assertEqual(document.kind, "xml")
        output = serialize("xml", document.data)
        root = ET.fromstring(output)
        self.assertEqual(root.tag, "root")
        self.assertEqual(root.attrib, {"lang": "fr"})
        self.assertEqual(root.findtext("title"), "Bonjour")
        self.assertEqual([node.text for node in root.findall("item")], ["A", "B"])

    def test_yaml_round_trip(self) -> None:
        value = {"name": "Magic", "items": ["one", "two"], "enabled": True}
        output = serialize("yaml", value)
        parsed = parse_text(output)
        self.assertEqual(parsed.data, value)

    def test_toml_round_trip(self) -> None:
        value = {"name": "Magic", "stats": {"version": 2, "enabled": True}}
        output = serialize("toml", value)
        self.assertEqual(tomllib.loads(output), value)
