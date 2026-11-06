# Local verification — 2026-11-06

Environment: Omarchy 4.5.0-3, Hyprland 0.56.2, two monitors at scale 1.

Passed:

- Official `omarchy plugin validate` with service + barWidget entry points.
- Both GPU shaders compiled with Qt's qsb.
- Quickshell loading and graphical settings open/close without plugin QML errors.
- Five adapter tests: address injection rejection, tiled-window rejection,
  recovery metadata ordering, original-workspace restoration, last-window order.
- Captured a disposable Foot window and visually inspected its snapshot.
- Visually inspected a screenshot during GPU deformation of that snapshot.
- Minimized and restored a disposable Foot window through the installed plugin's
  IPC, checking `special:minimized` and original workspace 4 via `hyprctl clients`.
- Persisted duration 600 ms through plugin settings, read it back through IPC,
  then restored the default 520 ms and read it back.
- Plugin enabled in the live shell; `hyprctl configerrors` is empty.

Not yet verified: all four edges, mixed DPI/rotated monitors, hot unplug,
large window counts, shell restart while windows are minimized, and uninstall
end-to-end. The shader is snapshot-based; this is an experimental release,
not a claim of native/live Genie equivalence or marketplace approval.

## 0.2.0 — integration correction

- Removed the independent window dock; settings remain a separate on-demand panel.
- Extended the installed Omarchy dock source, retaining its app grid, pins, menu,
  rendering, and grouping. Stock service is disabled to prevent duplicate docks.
- Both the no-argument default command and explicit-address titlebar command
  minimized a disposable Foot window to `special:minimized`.
- The shader used the actual dock icon rectangle: x=1247, y=1027, w=42, h=42
  in the tested theme. This comes from the live slot, not a computed dock model.
- Invoked the dock's real `bringForward` path via `activateDock` and verified
  animated restoration to workspace 4, with no plugin error reported.
- `hyprctl configerrors` remains empty.

## 0.2.1 — competing minimize animation

The adapter moved the real window to the hidden workspace with native animation
still enabled. Added a regression test that failed on that path, then temporarily
suppressed `no_anim` for Genie-managed windows. The override is owned by a tag
and released after restoration; existing no-animation rules are preserved.
Each capture now gets a fresh ScreencopyView rather than reusing recording state.

Passed eight adapter tests. Three consecutive minimize/restore cycles through
the titlebar command reported `phase=minimize, animated=true`, the real window's
`no_anim` property was true while hidden and false after restore, and no adapter
error was reported.

## 0.2.2 — actual titlebar click and widget removal

Reproduced with a real virtual-pointer click on the test window's minus button.
Before the fix it created only `omarchy-minimized-from-*` tags and never updated
Genie's animation report. Omarchy's `default/hypr/envs.lua` prepends its bin
directory inside the compositor, bypassing the local wrapper despite terminal
PATH checks. The managed Lua block now prepends the plugin tools directory.
Two real pointer clicks then produced `phase=minimize, animated=true` and Genie
recovery tags, with restoration through the dock between them.

Removed the bar-widget kind and entry point. Migrated settings into the plugins
service list while removing all Genie entries from bar sections. The manifest
validates as service-only and `hyprctl configerrors` is empty.

## Pointer preservation

Reproduced pointer movement when restoring through the dock: cursor position
changed from (1282, 1048) to (1407, 93). Move/focus dispatches now temporarily
suppress cursor warping within a synchronous compositor request, restoring the
previous `cursor.no_warps` value even if the dispatch raises a Lua error.

The same restore path then preserved (1268, 1048) exactly, kept the test window
focused for keyboard input, and left the global option false as before.
Eleven regression tests pass. Marketplace submission remains pending.

## 0.2.3 — maximized floating windows

Reproduced rejection of maximized windows: Hyprland reports maximized as
`fullscreen=1`, which the QML entry and adapter incorrectly rejected as true
fullscreen. Both now reject only modes 2 and 3.

Added regression coverage for accepting mode 1 and still excluding true
fullscreen. Thirteen tests pass. A real pointer click on a maximized test
window's minus button minimized it with Genie. Clicking its actual dock icon
restored it to workspace 4, still maximized at 1920x1020. The cursor did not
move during restoration.
