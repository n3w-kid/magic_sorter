import unittest

from magic_sorter_x.cli import build_parser


class CliTests(unittest.TestCase):
    def test_view_command(self) -> None:
        args = build_parser().parse_args(["view", "file.json", "--summary", "--no-tui"])
        self.assertEqual(args.command, "view")
        self.assertTrue(args.summary)
        self.assertFalse(args.tui)

    def test_wizard_flag(self) -> None:
        args = build_parser().parse_args(["--wizard"])
        self.assertTrue(args.wizard)


    def test_godot_export_command(self) -> None:
        args = build_parser().parse_args(["godot-export", "questtext.gd", "-o", "questtext.msx.txt"])
        self.assertEqual(args.command, "godot-export")
        self.assertEqual(args.path, "questtext.gd")

    def test_godot_patch_command(self) -> None:
        args = build_parser().parse_args([
            "godot-patch", "game.pck", "questtext.gd",
            "--dest", "res://scripts/questtext.gd",
        ])
        self.assertEqual(args.dest, "res://scripts/questtext.gd")
