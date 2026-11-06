# Third-party notices

## Omarchy application dock

The files in `dock/` are derived from the dock shipped with Omarchy 4.5.0-3:

- `Dock.qml`
- `DockWindow.qml`
- `DockModel.js`
- `AppGrid.qml`

Upstream project: https://github.com/omacom/omarchy

Copyright (c) David Heinemeier Hansson. The upstream permission notice is retained in [dock/LICENSE](dock/LICENSE).

Local modifications add a reference to the Genie controller, route managed minimized-window activation through the restore effect, and expose the rendered application icon rectangle. The dock's appearance and other behavior come from Omarchy.

No code from Hyprglass or Nothing Liquid is included. Apple does not sponsor or endorse this project; “Genie-style” describes the visual inspiration.
