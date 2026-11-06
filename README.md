# Genie for Omarchy

A Genie-style minimize and restore animation for **Omarchy's floating workspaces**, integrated with the existing Omarchy application dock.

Press the **− button in a window's titlebar** or **Super+M**: the window bends and contracts into its application icon. Click that application in the dock to bring it back with the reverse animation.

**Status:** experimental · **Plugin ID:** `chato.genie` · **Tested on:** Omarchy `4.5.0-3`, Hyprland `0.56.2`.

## Features

- Uses the actual dock icon position, including theme scale and app ordering.
- Keeps Omarchy's dock appearance, pinned apps, application grid, menus, and dragging.
- Adds no extra dock or button to the top bar.
- Supports normal and maximized floating windows (true fullscreen is excluded).
- Supports configurable duration and intensity, and respects Omarchy's global animation toggle.
- Restores windows to their original workspace without moving the mouse pointer.
- Keeps the restored window ready for keyboard input.
- Starts automatically with the Omarchy shell after installation.
- Requires no native Hyprland plugin, compilation, sudo, or network access at runtime.

## Requirements

Run installation **inside your Omarchy graphical session**. You need:

- Omarchy's Quickshell-based shell and Lua-based Hyprland configuration.
- Quickshell with `ScreencopyView`, Qt Quick Controls, and GPU shader support.
- Python 3, Git, and the standard Omarchy/Hyprland commands.
- A workspace using Omarchy's **floating** mode. Switch using Omarchy's layout controls.

The tested versions above are the compatibility baseline, not a guarantee for every Omarchy release. This plugin extends a snapshot of Omarchy's dock implementation; upstream dock changes may require an update.

## Install

Use Omarchy's plugin manager:

```sh
omarchy plugin add https://github.com/nacho1706/omarchy-genie.git --enable
```

`omarchy plugin install` is an alias for `omarchy plugin add`; this is equivalent:

```sh
omarchy plugin install https://github.com/nacho1706/omarchy-genie.git --enable
```

Run **one** of those commands, not both. Omarchy clones and validates the repository and enables its background service and app-menu integration. Review the code when prompted.

### Required: connect the window titlebar buttons

**The plugin manager does not run custom setup scripts.** After adding the plugin (including through the marketplace), run this once:

```sh
cd ~/.config/omarchy/plugins/chato.genie
python3 tools/manage.py install
omarchy restart shell
```

This additional step connects the window's **− button** and **Super+M** to Genie. Without it, enabling the shell service alone does not replace Omarchy's minimization command. Do not run setup with `sudo`.

Already installed? Do not run `plugin add` again: use the update instructions below. The setup supports running directly from the installed plugin directory without modifying its Git checkout.

### Alternative: install from a development checkout

If you want a separate source checkout instead of an installation managed by Omarchy:

```sh
git clone https://github.com/nacho1706/omarchy-genie.git
cd omarchy-genie
python3 tools/manage.py install
omarchy restart shell
```

This copies the plugin files without their Git history. Use the development-checkout update instructions for this method.

### What installation changes

The installer:

1. Validates and installs the plugin under `~/.config/omarchy/plugins/chato.genie` (or `$XDG_CONFIG_HOME`).
2. Enables its background service and replaces the stock dock service with the extended version, preserving dock settings.
3. Backs up `hypr/bindings.lua`, then adds a marked `chato.genie` block for the shortcuts and titlebar command path.
4. Installs a small minimizer wrapper under `~/.local/bin`. Hyprland also gets the plugin's tools directory before Omarchy's command directory in its launch `PATH`, so the titlebar button reaches Genie.
5. Migrates settings from earlier versions and removes their old top-bar widget.

It does **not** edit `/usr/share/omarchy` or `/usr/bin`. Backups remain beside the configuration files. An unrelated custom minimizer wrapper or occupied restore shortcut prevents installation.

## Usage

| Action | Control |
| --- | --- |
| Minimize a floating window | **−** in its Omarchy titlebar, or **Super+M** |
| Restore a window | Click its application in the Omarchy dock |
| Restore the last minimized window | **Super+Ctrl+M** |
| Open animation settings | `omarchy-shell chato.genie settings` |

The supported titlebar is **Omarchy's floating-window decoration** with minimize, maximize, and close controls. Application-owned Wayland minimize requests outside Omarchy's command route are not intercepted.

Change the dock's edge, pins, or appearance using **Omarchy's own dock settings**. Genie follows those settings.

### Animation settings

Use the settings panel or the command line:

```sh
omarchy-shell chato.genie configure '{"duration":520,"intensity":1.5}'
```

| Setting | Default | Range |
| --- | --- | --- |
| Duration | 520 ms | 100–1200 ms |
| Intensity | 1.5 | 0.2–4.0 |

Settings persist in the `chato.genie` service entry in `shell.json`.

## Update

If you installed with `omarchy plugin add` / `install` or through the marketplace:

```sh
omarchy plugin update chato.genie
cd ~/.config/omarchy/plugins/chato.genie
python3 tools/manage.py install
omarchy restart shell
```

The plugin manager updates the Git-managed checkout. Running setup again refreshes the keyboard/titlebar integration and retains animation settings.

If you installed from a separate development checkout instead, update that original checkout:

```sh
cd /path/to/omarchy-genie
git pull --ff-only
python3 tools/manage.py install
omarchy restart shell
```

Review compatibility before updating Omarchy or Hyprland. Restarting the shell clears animation snapshots; windows remain recoverable through the dock.

## Uninstall

From either your checkout or the installed plugin directory:

```sh
python3 tools/manage.py uninstall
omarchy restart shell
```

The uninstaller restores hidden Genie windows, enables the stock Omarchy dock, removes the marked shortcut block and Genie-owned wrapper, and removes the installed plugin. Backups and unrelated configuration remain in place.

Omarchy also provides `omarchy plugin remove chato.genie`, but that command alone does not undo this plugin's additional keyboard/titlebar setup. Use the custom uninstaller above for complete removal.

**Restore windows before manually deleting or disabling the plugin.** If the shell is unavailable, run this repeatedly until all Genie windows are back:

```sh
python3 tools/windows.py restore-last
```

Window tags store the original workspace and minimization order, allowing recovery without the shell's in-memory state.

## Troubleshooting

```sh
omarchy-shell chato.genie status
omarchy plugin list
hyprctl configerrors
```

`status` reports application-launch capability and the number of available apps, along with the most recent animation direction, whether it ran, its fallback reason when applicable, and the actual dock icon rectangle.

- **The − button uses the old effect:** rerun the installer, then restart the shell. A terminal's `PATH` can differ from the command path inside Hyprland; copying a wrapper alone is insufficient.
- **Nothing happens:** check that the window is floating, not in true fullscreen or pinned, and that its workspace uses Omarchy's floating mode.
- **A window restores without an effect after restarting the shell:** its snapshot is no longer available; restoration still works.
- **Two docks appear:** check that `chato.genie` is enabled and `omarchy.dock` is disabled. The installer sets this up.

## How it works and current limits

Quickshell captures the window. A GPU mesh deforms that snapshot toward the dock icon while the real window waits on `special:minimized`. Hyprland's native animation is suppressed for that window to avoid competing effects, and the temporary override is released after restoration.

This is a **snapshot-based effect**, not a live deformation: video and changing content freeze during the animation. Server-side decorations and popups may not be captured. Capture failure falls back to functional minimization. A shell restart loses snapshots; a compositor restart normally terminates Wayland clients.

Mixed DPI, rotated displays, monitor removal, dock autohide during animation, and large numbers of windows still need wider testing. See [local verification notes](VERIFICATION.md) for what has actually been checked.

## Development

```sh
omarchy plugin validate .
python3 -m unittest discover -s tests -v
```

Compiled Qt shaders are included, so users do not need a shader compiler. To rebuild them:

```sh
/usr/lib/qt6/bin/qsb --glsl '100 es,120,150' --hlsl 50 --msl 12 -o shaders/genie.vert.qsb shaders/genie.vert
/usr/lib/qt6/bin/qsb --glsl '100 es,120,150' --hlsl 50 --msl 12 -o shaders/genie.frag.qsb shaders/genie.frag
```

## Marketplace submission

This repository provides the root manifest, source, README, licenses, and installation/removal instructions required for a submission. **It has not been accepted into the marketplace.** See [submission details](docs/MARKETPLACE.md) and the [official publishing guide](https://plugins.omarchy.org/publish.html).

## License and credits

Original Genie code is available under the [MIT license](LICENSE). The extended Omarchy dock retains its [upstream license](dock/LICENSE). See [third-party notices](THIRD_PARTY_NOTICES.md) for attribution and the changes made to those files.
