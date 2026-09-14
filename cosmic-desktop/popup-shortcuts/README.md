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

Execution supports wtype 0.4 (including Fedora's `wtype-0.4-11.fc44`).
Modifiers are pressed with `-M`, the key is sent with `-k`, and modifiers are
released in reverse order with `-m`. For example, `Super + Shift + F` becomes:

```bash
wtype -M logo -M shift -k f -m shift -m logo
```

**Super is called `logo` in wtype 0.4**; `-M super` is not accepted by that
version. See the [upstream 0.4 modifier names and argument parser](https://github.com/atx/wtype/blob/v0.4/main.c).
Supported modifiers include Super/Logo/Win/Meta/Mod4, Ctrl/Control, Shift,
Alt/Mod1, AltGr/ISO_Level3_Shift, and CapsLock. Names are case-insensitive;
spaces around `+` are optional. Duplicate modifiers are pressed only once.

Letters are normalized to lowercase; use an explicit Shift modifier when needed.
Common key aliases include Enter, Esc, Space, Backspace, Delete/Del,
Insert/Ins, arrows, Home/End, PageUp/PgUp, PageDown/PgDn, PrintScreen, and F1–F35.
XKB names such as `XF86AudioMute` and `KP_Enter` also work. Punctuation is
translated to XKB names; a plus key can be written as `Ctrl + plus` or `Ctrl++`.
Unknown modifiers and malformed combinations are rejected before execution;
wtype validates other XKB key names.

Run the execution regression tests from this directory:

```bash
python3 -m unittest -v test_shortcuts.py
```
