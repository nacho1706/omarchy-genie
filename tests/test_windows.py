import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("windows", Path(__file__).parents[1] / "tools/windows.py")
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

class AdapterTests(unittest.TestCase):
    def client(self, **kwargs):
        return dict(address="0xab", workspace={"id":3,"name":"3"}, floating=True, fullscreen=0, tags=[], **kwargs)

    def test_rejects_injected_address(self):
        with patch.object(w,"query",return_value=[]), self.assertRaises(ValueError):
            w.main("restore", '0xab"; os.execute("bad")')

    def test_rejects_tiled_window(self):
        c = self.client(); c["floating"] = False
        with patch.object(w,"query",return_value=[c]), patch.object(w,"dispatch") as d, self.assertRaises(ValueError):
            w.main("minimize", "0xab")
        d.assert_not_called()

    def test_minimize_records_recovery_before_moving(self):
        c = self.client(); c["tags"] = ["genie-workspace-9", "genie-order-1"]
        with patch.object(w,"query",return_value=[c]), patch.object(w,"run",return_value="floating"), patch.object(w,"dispatch") as d:
            w.main("minimize", "0xab")
        calls = [x.args[0] for x in d.call_args_list]
        self.assertIn('tag = "+genie-workspace-3"', calls[2])
        move = next(i for i, call in enumerate(calls) if "window.move" in call)
        self.assertIn('workspace = "special:minimized"', calls[move])
        self.assertIn('workspace = "3"', calls[move + 1])

    def test_restore_original_workspace(self):
        c = self.client(); c["workspace"] = {"id":-99,"name":"special:minimized"}; c["tags"] = ["genie-workspace-7", "genie-order-9"]
        with patch.object(w,"query",return_value=[c]), patch.object(w,"dispatch") as d:
            w.main("restore", "0xab")
        self.assertIn('workspace = "7"',d.call_args_list[0].args[0])

    def test_minimize_suppresses_compositor_animation_during_move(self):
        with patch.object(w, "query", return_value=[self.client()]), patch.object(w, "run", return_value="floating"), patch.object(w, "dispatch") as d:
            w.main("minimize", "0xab")
        calls = [x.args[0] for x in d.call_args_list]
        move = next(i for i, call in enumerate(calls) if "window.move" in call)
        self.assertTrue(any('prop = "no_anim", value = "1"' in call for call in calls[:move]),
                        "Moving the real window still triggers Hyprland's animation behind Genie")

    def test_restore_releases_only_genie_animation_override(self):
        c = self.client(); c["tags"] = ["genie-workspace-3", "genie-noanim-owned"]
        with patch.object(w, "query", return_value=[c]), patch.object(w, "dispatch") as d, patch.object(w.time, "sleep"):
            w.main("restore", "0xab")
        calls = [call.args[0] for call in d.call_args_list]
        self.assertIn('prop = "no_anim", value = "unset"', calls[-2])
        self.assertIn('-genie-noanim-owned', calls[-1])

    def test_minimize_preserves_existing_no_animation_rule(self):
        with patch.object(w, "query", return_value=[self.client()]), patch.object(w, "run", side_effect=["floating", "true"]), patch.object(w, "dispatch") as d:
            w.main("minimize", "0xab")
        self.assertFalse(any("set_prop" in call.args[0] for call in d.call_args_list))

    def test_restore_last_uses_order_not_client_list(self):
        first = self.client(); first["tags"] = ["genie-workspace-3", "genie-order-20"]; first["workspace"]["name"] = "special:minimized"
        second = dict(first,address="0xcd",tags=["genie-workspace-3","genie-order-10"])
        with patch.object(w,"query",return_value=[first,second]), patch.object(w,"dispatch") as d:
            result = w.main("restore-last")
        self.assertEqual(result["address"],"0xab")

if __name__ == "__main__": unittest.main()
