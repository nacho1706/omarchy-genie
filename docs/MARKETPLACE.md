# Omarchy marketplace submission

Repository: https://github.com/nacho1706/omarchy-genie

Plugin ID: `chato.genie`

Name: Genie

Suggested category: Desktop

Suggested tags: animations, floating, windows, dock, hyprland

Suggested description:

> Genie-style minimize and restore for Omarchy floating windows. Windows contract into their actual application icons in the Omarchy dock, with configurable duration and intensity. Runs as a Quickshell service without adding a second dock or top-bar widget.

## Installation command

```sh
omarchy plugin add https://github.com/nacho1706/omarchy-genie.git --enable
cd ~/.config/omarchy/plugins/chato.genie
python3 tools/manage.py install
omarchy restart shell
```

`omarchy plugin install` is an alias for `omarchy plugin add`. The additional setup step is required for the titlebar buttons, whether installed by CLI or marketplace.

## Reviewer notes

- Baseline: Omarchy 4.5.0-3, Hyprland 0.56.2.
- Root `manifest.json` validates with `omarchy plugin validate .`.
- Background service plus an application-menu entry point, extending an attributed copy of the Omarchy dock. The menu kind grants the shell application-library capability needed to launch closed apps; no top-bar widget is added.
- No runtime network access, sudo, native plugin compilation, or downloaded executables.
- **Additional local setup is required** for the default keyboard and titlebar integration. Marketplace installation does not execute the installer; users must explicitly run `python3 tools/manage.py install`, then restart the shell.
- The installer changes user configuration only, with backups. It disables the stock dock to avoid duplicates; uninstall restores it and brings back managed hidden windows.
- The animation uses a window snapshot. Compatibility outside the documented baseline is not yet established.

## Submit

Use the [official submission form](https://github.com/omacom/omarchy-plugin-marketplace/issues/new?template=submit-plugin.yml), providing the repository URL and the closest available category/tags. Disclose the additional setup step above.

The marketplace's automated validation and maintainer review determine acceptance. A local manifest validation does not grant catalog approval.
