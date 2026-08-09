import unittest

from magic_sorter_x.tui import all_container_paths, format_path, visible_nodes


class TuiTests(unittest.TestCase):
    def test_visible_nodes_and_search(self) -> None:
        data = {"project": {"name": "Magic", "count": 2}, "other": "hello"}
        expanded = {(), ("project",)}
        nodes = visible_nodes(data, expanded)
        self.assertEqual([node.label for node in nodes], ["document", "project", "name", "count", "other"])
        matches = visible_nodes(data, expanded, "magic")
        self.assertEqual([node.label for node in matches], ["document", "project", "name"])

    def test_container_paths_and_json_path(self) -> None:
        data = {"items": [{"name": "x"}]}
        self.assertEqual(all_container_paths(data), {(), ("items",), ("items", 0)})
        self.assertEqual(format_path(("items", 0, "name")), "$.items[0].name")
