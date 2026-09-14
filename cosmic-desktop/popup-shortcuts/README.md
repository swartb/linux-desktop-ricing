# COSMIC Shortcuts Overlay

A searchable QuickShell overlay for COSMIC keyboard shortcuts.

It reads shortcuts from:

- `/usr/share/cosmic/com.system76.CosmicSettings.Shortcuts/v1/defaults`
- `~/.config/cosmic/com.system76.CosmicSettings.Shortcuts/v1/custom`

Custom shortcuts override defaults, and disabled shortcuts are omitted.

The overlay is also interactive:

- the first matching shortcut is selected automatically
- `Up` / `Down` moves through the visible shortcuts
- `Enter` executes the selected shortcut
- clicking a shortcut executes it
- `Esc` closes the overlay
- typing filters by shortcut, description, or category

### Requirements

- COSMIC Desktop
- QuickShell
- Python 3
- `wtype` for executing selected shortcuts

`wtype` is used to replay the selected key combination after the overlay closes. It uses Wayland's virtual-keyboard protocol.

### Files

- `shell.qml` — QuickShell overlay UI and keyboard navigation
- `shortcuts.py` — parses, categorizes, and executes COSMIC shortcuts
- `install.sh` — installs the overlay to `~/.config/quickshell-shortcuts`
- `screenshots/` — screenshots for documentation

### Run manually

```bash
quickshell -p ~/.config/quickshell-shortcuts
```

A COSMIC custom shortcut can then be assigned to launch that command, for example `Super+K`.

### Execution

When a shortcut is selected, the overlay starts `shortcuts.py --run`, closes, waits briefly, and then uses `wtype` to send the selected key combination to COSMIC. This makes the launcher work for normal COSMIC actions such as window management, workspace switching, and application shortcuts without maintaining a second set of commands.
