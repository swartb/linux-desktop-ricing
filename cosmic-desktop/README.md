# COSMIC Desktop

This folder contains COSMIC Desktop customizations.

## COSMIC Shortcuts Overlay

A searchable QuickShell overlay for COSMIC keyboard shortcuts.

It reads shortcuts from:

- `/usr/share/cosmic/com.system76.CosmicSettings.Shortcuts/v1/defaults`
- `~/.config/cosmic/com.system76.CosmicSettings.Shortcuts/v1/custom`

Custom shortcuts override defaults, and disabled shortcuts are omitted.

### Requirements

- COSMIC Desktop
- QuickShell
- Python 3

### Files

- `shell.qml` — QuickShell overlay UI
- `shortcuts.py` — parses and categorizes COSMIC shortcuts
- `install.sh` — installs the overlay to `~/.config/quickshell-shortcuts`
- `screenshots/` — screenshots for documentation

### Run manually

```bash
quickshell -p ~/.config/quickshell-shortcuts
```

A COSMIC custom shortcut can then be assigned to launch that command, for example `Super+K`.
