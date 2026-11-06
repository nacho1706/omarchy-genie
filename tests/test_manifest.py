"""Contracts enforced by Omarchy's capability-scoped plugin host."""
import json
from pathlib import Path
import unittest

class ManifestTests(unittest.TestCase):
    def test_dock_launcher_declares_the_required_menu_capability(self):
        root = Path(__file__).parents[1]
        manifest = json.loads((root / "manifest.json").read_text())
        # Omarchy's createScopedPluginShell grants appLibrary only to menus.
        self.assertIn("menu", manifest["kinds"])
        self.assertTrue((root / manifest["entryPoints"]["menu"]).is_file())
        self.assertIn("service", manifest["kinds"])
        self.assertNotIn("bar-widget", manifest["kinds"])
