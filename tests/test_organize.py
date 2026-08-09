import tempfile
import unittest
from pathlib import Path

from magic_sorter_x.organize import category_for, plan_organize


class OrganizeTests(unittest.TestCase):
    def test_categories(self) -> None:
        self.assertEqual(category_for(Path("data.json")), "data")
        self.assertEqual(category_for(Path("photo.png")), "images")
        self.assertEqual(category_for(Path("unknown.xyz")), "other")

    def test_plan_organize(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data.json").write_text("{}", encoding="utf-8")
            plans = plan_organize(root)
            self.assertEqual(len(plans), 1)
            self.assertEqual(plans[0].destination.parent.name, "🧩 Data")
