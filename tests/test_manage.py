import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("manage", Path(__file__).parents[1] / "tools/manage.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class MigrationTests(unittest.TestCase):
    def test_removes_widget_but_preserves_settings_and_other_plugins(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp)
            (config / "omarchy").mkdir()
            path = config / "omarchy/shell.json"
            path.write_text(json.dumps({"plugins": [{"id":"other"}], "bar":{"layout":{"right":[{"id":"chato.genie","duration":640},{"id":"omarchy.clock"}]}}}))
            with patch.object(m,"CONFIG",config): m.migrate_service_settings()
            data = json.loads(path.read_text())
            self.assertEqual(data["bar"]["layout"]["right"], [{"id":"omarchy.clock"}])
            self.assertEqual(data["plugins"], [{"id":"other"},{"id":"chato.genie","duration":640}])
            with patch.object(m,"CONFIG",config): m.migrate_service_settings()
            self.assertEqual(json.loads(path.read_text()), data)

    def test_marketplace_install_can_run_in_place_without_empty_folders(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "plugin"
            (root / "tools").mkdir(parents=True)
            (root / "tools/omarchy-hyprland-window-minimize").write_text("#!/bin/sh\n# chato.genie\n")
            bindings = Path(tmp) / "bindings.lua"
            bindings.write_text(m.START + "\n" + m.END)
            wrapper = Path(tmp) / "bin/omarchy-hyprland-window-minimize"
            catalog = json.dumps([{"id":"chato.genie", "kinds":["service"]}])
            with patch.multiple(m, ROOT=root, DEST=root, BINDINGS=bindings, WRAPPER=wrapper), patch.object(m,"call") as call, patch.object(m,"migrate_service_settings"), patch.object(m,"edit_bindings"), patch.object(m.subprocess,"check_output",return_value=catalog), contextlib.redirect_stdout(io.StringIO()):
                m.main("install")
            self.assertTrue(wrapper.exists())
            call.assert_any_call("omarchy", "plugin", "enable", "chato.genie")
            self.assertFalse((root / "i18n").exists())
