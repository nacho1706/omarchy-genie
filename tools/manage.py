#!/usr/bin/env python3
"""Local installation. Marketplace users can instead enable the cloned plugin."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
DEST = CONFIG / "omarchy/plugins/chato.genie"
BINDINGS = CONFIG / "hypr/bindings.lua"
START, END = "-- BEGIN chato.genie", "-- END chato.genie"
BLOCK = '''-- BEGIN chato.genie
-- Route titlebar commands through Genie before Omarchy defaults.
local genie_config = os.getenv("XDG_CONFIG_HOME") or (os.getenv("HOME") .. "/.config")
hl.env("PATH", genie_config .. "/omarchy/plugins/chato.genie/tools:" .. (os.getenv("PATH") or "/usr/bin"))
hl.unbind("SUPER + M")
o.bind("SUPER + M", "Minimize window to Omarchy dock", "omarchy-shell chato.genie minimize")
o.bind("SUPER + CTRL + M", "Genie restore last", "omarchy-shell chato.genie restoreLast")
-- END chato.genie'''
WRAPPER = Path.home() / ".local/bin/omarchy-hyprland-window-minimize"


def call(*args):
    subprocess.run(args, check=True, timeout=15)


def edit_bindings(install):
    source = BINDINGS.read_text()
    if START in source:
        before, rest = source.split(START, 1)
        _, after = rest.split(END, 1)
        source = before.rstrip() + after
    if install:
        source = source.rstrip() + "\n\n" + BLOCK + "\n"
    backup = BINDINGS.with_name("bindings.lua.genie-backup-" + str(time.time_ns()))
    shutil.copy2(BINDINGS, backup)
    BINDINGS.write_text(source)
    call("hyprctl", "reload")
    errors = subprocess.check_output(["hyprctl", "configerrors"], text=True).strip()
    if errors:
        shutil.copy2(backup, BINDINGS)
        call("hyprctl", "reload")
        raise RuntimeError("Config validation failed; bindings restored: " + errors)


def migrate_service_settings():
    path = CONFIG / "omarchy/shell.json"
    source = path.read_text()
    data = json.loads(source)
    settings = {"id": "chato.genie"}
    for entry in data.get("plugins", []):
        if isinstance(entry, dict) and entry.get("id") == "chato.genie": settings.update(entry)
    for section, entries in data.get("bar", {}).get("layout", {}).items():
        for entry in entries:
            if isinstance(entry, dict) and entry.get("id") == "chato.genie": settings.update(entry)
        data["bar"]["layout"][section] = [e for e in entries if not (e == "chato.genie" or isinstance(e, dict) and e.get("id") == "chato.genie")]
    data["plugins"] = [e for e in data.get("plugins", []) if not (e == "chato.genie" or isinstance(e, dict) and e.get("id") == "chato.genie")] + [settings]
    path.with_name("shell.json.genie-backup-" + str(time.time_ns())).write_text(source)
    temporary = path.with_name("shell.json.genie-tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def main(action):
    if action == "install":
        call("omarchy", "plugin", "validate", str(ROOT))
        # Do not replace someone else's bindings for the chosen defaults.
        if START not in BINDINGS.read_text():
            binds = json.loads(subprocess.check_output(["hyprctl", "binds", "-j"], text=True))
            if any(b.get("key", "").lower() == "m" and b.get("modmask") == 68 for b in binds):
                raise RuntimeError("Super+Ctrl+M is occupied; choose a free restore shortcut before installing.")
        # Marketplace clones are already in DEST; installing in place must not
        # copy a file onto itself. Empty, unused folders are not tracked by Git.
        if ROOT.resolve() != DEST.resolve():
            DEST.mkdir(parents=True, exist_ok=True)
            for filename in ("manifest.json", "Service.qml", "GenieScreen.qml", "Menu.qml", "README.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
                shutil.copy2(ROOT / filename, DEST / filename)
            for directory in ("tools", "shaders", "dock"):
                shutil.copytree(ROOT / directory, DEST / directory, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
        call("omarchy-shell", "shell", "rescanPlugins")
        for attempt in range(40):
            catalog = subprocess.check_output(["omarchy-plugin-catalog"], text=True)
            if any(p.get("id") == "chato.genie" and set(p.get("kinds", [])) == {"service", "menu"} for p in json.loads(catalog)):
                break
            time.sleep(0.1)
        call("omarchy", "plugin", "enable", "chato.genie")
        migrate_service_settings()
        WRAPPER.parent.mkdir(parents=True, exist_ok=True)
        if WRAPPER.exists() and "chato.genie" not in WRAPPER.read_text():
            raise RuntimeError("A custom minimizer already exists at " + str(WRAPPER))
        shutil.copy2(ROOT / "tools/omarchy-hyprland-window-minimize", WRAPPER)
        call("omarchy", "plugin", "disable", "omarchy.dock")
        edit_bindings(True)
        print("Installed. Super+M and Omarchy's titlebar minimize use Genie; restore through the Omarchy dock.")
    elif action == "uninstall":
        # Bring every managed hidden window back before disabling its dock.
        clients = json.loads(subprocess.check_output(["python3", str(ROOT / "tools/windows.py"), "list"], text=True))["clients"]
        for c in clients:
            if c["workspace"]["name"] == "special:minimized" and any(t.startswith("genie-workspace-") for t in c.get("tags", [])):
                call("python3", str(ROOT / "tools/windows.py"), "restore", c["address"])
        call("omarchy", "plugin", "disable", "chato.genie")
        call("omarchy", "plugin", "enable", "omarchy.dock")
        edit_bindings(False)
        if WRAPPER.exists() and "chato.genie" in WRAPPER.read_text(): WRAPPER.unlink()
        if DEST.exists(): shutil.rmtree(DEST)
        call("omarchy-shell", "shell", "rescanPlugins")
    else:
        raise ValueError("Use install or uninstall")

if __name__ == "__main__": main(sys.argv[1])
