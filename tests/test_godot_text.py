import tempfile
import unittest
from pathlib import Path

from magic_sorter_x.godot_text import (
    export_editable_text,
    extract_godot_strings,
    import_edited_text,
    merge_editable_text,
    parse_editable_text,
)


SAMPLE = '''extends Node\n\nvar Greeting = "Hello\\nWorld"\nconst Quote: String = 'She said: \\"Hi\\"'\nvar Number = 42\n'''


class GodotTextTests(unittest.TestCase):
    def test_extract_string_assignments(self) -> None:
        entries = extract_godot_strings(SAMPLE)
        self.assertEqual([entry.name for entry in entries], ["Greeting", "Quote"])
        self.assertEqual(entries[0].value, "Hello\nWorld")
        self.assertEqual(entries[1].value, 'She said: "Hi"')

    def test_merge_changes_only_string_literal(self) -> None:
        edited = '''# Magic Sorter X - Godot editable text v1\n@@MSX:BEGIN 0001 Greeting\n|Hello\n|Universe\n@@MSX:END 0001\n'''
        result = merge_editable_text(SAMPLE, edited)
        self.assertEqual(result.changed_blocks, 1)
        self.assertIn('var Greeting = "Hello\\nUniverse"', result.output_text)
        self.assertIn("var Number = 42", result.output_text)

    def test_export_import_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "dialogue.gd"
            editable = root / "dialogue.msx.txt"
            output = root / "dialogue_patched.gd"
            source.write_text(SAMPLE, encoding="utf-8")
            count = export_editable_text(source, editable)
            self.assertEqual(count, 2)
            blocks = parse_editable_text(editable.read_text(encoding="utf-8"))
            self.assertEqual(len(blocks), 2)
            result = import_edited_text(source, editable, output)
            self.assertEqual(result.changed_blocks, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), SAMPLE)


if __name__ == "__main__":
    unittest.main()
