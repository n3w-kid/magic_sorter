import xml.etree.ElementTree as ET

from magic_sorter_x.parsers import parse_text
from magic_sorter_x.serialize import serialize


def test_xml_round_trip() -> None:
    document = parse_text('<root lang="fr"><title>Bonjour</title><item>A</item><item>B</item></root>')
    assert document.kind == "xml"
    output = serialize("xml", document.data)
    root = ET.fromstring(output)
    assert root.tag == "root"
    assert root.attrib == {"lang": "fr"}
    assert root.findtext("title") == "Bonjour"
    assert [node.text for node in root.findall("item")] == ["A", "B"]
