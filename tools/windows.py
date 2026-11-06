#!/usr/bin/env python3
"""Hyprland adapter. No shell interpolation; original workspace lives in window tags."""
import json
import re
import subprocess
import sys
import time

ADDRESS = re.compile(r"0x[0-9a-fA-F]+\Z")
PREFIX = "genie-"


def run(*args):
    p = subprocess.run(args, capture_output=True, text=True, timeout=5, check=True)
    return p.stdout.strip()


def query(what):
    return json.loads(run("hyprctl", what, "-j"))


def dispatch(code, preserve_pointer=False):
    if preserve_pointer:
        # One synchronous compositor request: no other input event can run
        # between the temporary override and its restoration, even on error.
        lua = (
            'local previous = hl.get_config("cursor.no_warps"); '
            'hl.config({ cursor = { no_warps = true } }); '
            'local ok, err = pcall(function() hl.dispatch(' + code + ') end); '
            'hl.config({ cursor = { no_warps = previous } }); '
            'if not ok then error(err) end'
        )
        result = run("hyprctl", "eval", lua)
    else:
        result = run("hyprctl", "dispatch", code)
    if result != "ok":
        raise RuntimeError(result)


def metadata(client):
    tags = client.get("tags", [])
    def number(prefix):
        return next((int(t[len(prefix):]) for t in tags
                     if re.fullmatch(re.escape(prefix) + r"\d+", t)), None)
    return number("genie-workspace-"), number("genie-order-")


def main(action, address=""):
    clients = query("clients")
    if action == "list":
        return {"clients": clients, "monitors": query("monitors"), "active": query("activewindow")}
    if action == "restore-last":
        candidates = [c for c in clients if metadata(c)[1] is not None
                      and c["workspace"]["name"] == "special:minimized"]
        if not candidates:
            return {"ok": True}
        address = max(candidates, key=lambda c: metadata(c)[1])["address"]
        action = "restore"
    if not ADDRESS.fullmatch(address):
        raise ValueError("Invalid window address")
    c = next((c for c in clients if c["address"] == address), None)
    if not c:
        raise ValueError("Window has closed")
    target = 'window = "address:' + address + '"'
    if action == "minimize":
        ws = c["workspace"]["id"]
        if not c.get("floating") or ws < 1 or c.get("fullscreen", 0) or c.get("pinned", False):
            raise ValueError("Only non-fullscreen floating windows can be minimized")
        if run("omarchy-hyprland-workspace-layout-current", str(ws)) != "floating":
            raise ValueError("Workspace must use Omarchy's floating mode")
        # Store recovery metadata before moving the window. Repeated minimization
        # removes stale tags, so restoring never selects a previous workspace.
        for tag in c.get("tags", []):
            if re.fullmatch(r"genie-(workspace|order)-\d+", tag):
                dispatch(f'hl.dsp.window.tag({{ tag = "-{tag}", {target} }})')
        for tag in (f"genie-workspace-{ws}", f"genie-order-{time.time_ns()}"):
            dispatch(f'hl.dsp.window.tag({{ tag = "+{tag}", {target} }})')
        # Keep the real hidden window still while Quickshell animates its
        # snapshot. Restore the rule-derived value only after bringing it back.
        if run("hyprctl", "getprop", "address:" + address, "no_anim") != "true":
            dispatch(f'hl.dsp.window.tag({{ tag = "+genie-noanim-owned", {target} }})')
            dispatch(f'hl.dsp.window.set_prop({{ prop = "no_anim", value = "1", {target} }})')
        dispatch(f'hl.dsp.window.move({{ workspace = "special:minimized", follow = false, {target} }})', preserve_pointer=True)
        dispatch(f'hl.dsp.focus({{ workspace = "{ws}" }})', preserve_pointer=True)
    elif action == "restore":
        ws, _ = metadata(c)
        if ws is None:
            raise ValueError("Window is not managed by Genie")
        dispatch(f'hl.dsp.window.move({{ workspace = "{ws}", follow = false, {target} }})', preserve_pointer=True)
        dispatch(f'hl.dsp.focus({{ workspace = "{ws}" }})', preserve_pointer=True)
        dispatch(f'hl.dsp.focus({{ {target} }})', preserve_pointer=True)
        if "genie-noanim-owned" in c.get("tags", []):
            # Match the stock dock's grace period: no native entrance behind
            # the final Genie frame, then release only our temporary override.
            time.sleep(0.4)
            dispatch(f'hl.dsp.window.set_prop({{ prop = "no_anim", value = "unset", {target} }})')
            dispatch(f'hl.dsp.window.tag({{ tag = "-genie-noanim-owned", {target} }})')
    else:
        raise ValueError("Unknown action")
    return {"ok": True, "address": address}


if __name__ == "__main__":
    try:
        print(json.dumps(main(*sys.argv[1:])))
    except (ValueError, RuntimeError, subprocess.SubprocessError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)
