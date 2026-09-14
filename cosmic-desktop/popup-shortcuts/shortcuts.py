#!/usr/bin/env python3

import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULTS = Path("/usr/share/cosmic/com.system76.CosmicSettings.Shortcuts/v1/defaults")
CUSTOM = Path.home() / ".config/cosmic/com.system76.CosmicSettings.Shortcuts/v1/custom"


def pretty_action(action):
    translations = {
        "Terminate": "Terminate COSMIC",
        "Debug": "Debug",
        "Close": "Close window",
        "Fullscreen": "Fullscreen",
        "LastWorkspace": "Last workspace",
        "MoveToLastWorkspace": "Move window to last workspace",
        "PreviousWorkspace": "Previous workspace",
        "NextWorkspace": "Next workspace",
        "MoveToPreviousWorkspace": "Move window to previous workspace",
        "MoveToNextWorkspace": "Move window to next workspace",
    }

    if action in translations:
        return translations[action]

    m = re.fullmatch(r"Focus\((.+)\)", action)
    if m:
        return f"Focus {m.group(1).lower()}"

    m = re.fullmatch(r"Move\((.+)\)", action)
    if m:
        return f"Move window {m.group(1).lower()}"

    m = re.fullmatch(r"Workspace\((\d+)\)", action)
    if m:
        return f"Workspace {m.group(1)}"

    m = re.fullmatch(r"MoveToWorkspace\((\d+)\)", action)
    if m:
        return f"Move window to workspace {m.group(1)}"

    m = re.fullmatch(r"SwitchOutput\((.+)\)", action)
    if m:
        return f"Focus output {m.group(1).lower()}"

    m = re.fullmatch(r"MoveToOutput\((.+)\)", action)
    if m:
        return f"Move window to output {m.group(1).lower()}"

    m = re.fullmatch(r"System\((.+)\)", action)
    if m:
        names = {
            "Terminal": "Terminal",
            "LockScreen": "Lock screen",
            "LogOut": "Log out",
        }
        return names.get(m.group(1), m.group(1))

    m = re.fullmatch(r'Spawn\("(.+)"\)', action, re.S)
    if m:
        return m.group(1)

    return action


def category_for(action, description):
    text = f"{action} {description}".lower()

    if (
        action.startswith("Workspace(")
        or action.startswith("MoveToWorkspace(")
        or action in {
            "LastWorkspace",
            "MoveToLastWorkspace",
            "PreviousWorkspace",
            "NextWorkspace",
            "MoveToPreviousWorkspace",
            "MoveToNextWorkspace",
        }
    ):
        return "Workspaces"

    if (
        action.startswith("Focus(")
        or action.startswith("Move(")
        or action in {"Close", "Fullscreen"}
    ):
        return "Window Management"

    if action.startswith("SwitchOutput(") or action.startswith("MoveToOutput("):
        return "Displays"

    if action.startswith("System(") or action in {"Terminate", "Debug"}:
        return "System"

    if "screenshot" in text or "screen shot" in text:
        return "Screenshots"

    if action.startswith("Spawn("):
        return "Applications"

    return "Other"


def parse_file(path):
    if not path.exists():
        return []

    text = path.read_text()
    entries = []
    depth = 0
    start = None

    for i, ch in enumerate(text):
        if ch == "(":
            if depth == 0:
                start = i
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and start is not None:
                rest = text[i + 1:]
                m = re.match(r"\s*:\s*([^,\n}]+(?:\([^)]*\))?)", rest)
                if m:
                    entries.append((text[start:i + 1], m.group(1).strip()))
                start = None

    result = []

    for spec, action in entries:
        mods_match = re.search(r"modifiers\s*:\s*\[(.*?)\]", spec, re.S)
        key_match = re.search(r'key\s*:\s*"([^"]+)"', spec)
        desc_match = re.search(r'description\s*:\s*Some\("([^"]+)"\)', spec)

        if not key_match:
            continue

        modifiers = []
        if mods_match:
            modifiers = [x.strip() for x in mods_match.group(1).split(",") if x.strip()]

        result.append({
            "modifiers": modifiers,
            "key": key_match.group(1),
            "action": action,
            "description": desc_match.group(1) if desc_match else None,
        })

    return result


def combo_id(item):
    return tuple(item["modifiers"]), item["key"]


def wtype_command(shortcut):
    wtype = shutil.which("wtype")
    if not wtype:
        raise RuntimeError("wtype is required to execute shortcuts")

    shortcut = shortcut.strip()
    if not shortcut:
        raise ValueError("empty shortcut")

    # Keep a literal trailing '+' as the key (also accept Ctrl++).
    if shortcut == "+":
        parts = ["plus"]
    elif re.search(r"\+\s*\+$", shortcut):
        parts = re.split(r"\s*\+\s*", shortcut[:-1].rstrip())[:-1] + ["plus"]
    else:
        parts = re.split(r"\s*\+\s*", shortcut)
    if any(not part for part in parts):
        raise ValueError(f"invalid shortcut: {shortcut}")

    modifier_names = {
        "super": "logo",
        "logo": "logo",
        "win": "logo",
        "meta": "logo",
        "mod4": "logo",
        "ctrl": "ctrl",
        "control": "ctrl",
        "shift": "shift",
        "alt": "alt",
        "mod1": "alt",
        "altgr": "altgr",
        "isolevel3shift": "altgr",
        "capslock": "capslock",
    }

    key_names = {
        "enter": "Return", "return": "Return", "space": "space",
        "spacebar": "space", "esc": "Escape", "escape": "Escape",
        "tab": "Tab", "backtab": "ISO_Left_Tab", "backspace": "BackSpace",
        "delete": "Delete", "del": "Delete", "insert": "Insert", "ins": "Insert",
        "home": "Home", "end": "End", "left": "Left", "right": "Right",
        "up": "Up", "down": "Down", "pageup": "Page_Up", "pgup": "Page_Up",
        "pagedown": "Page_Down", "pgdn": "Page_Down", "pgdown": "Page_Down",
        "printscreen": "Print", "prtsc": "Print", "print": "Print",
        "pause": "Pause", "menu": "Menu", "capslock": "Caps_Lock",
        "numlock": "Num_Lock", "scrolllock": "Scroll_Lock",
    }
    punctuation = dict(zip(
        "`~!@#$%^&*()-_=+[]{}\\|;:'\",<.>/?",
        ("grave asciitilde exclam at numbersign dollar percent asciicircum "
         "ampersand asterisk parenleft parenright minus underscore equal plus "
         "bracketleft bracketright braceleft braceright backslash bar semicolon "
         "colon apostrophe quotedbl comma less period greater slash question").split(),
    ))

    modifiers = []
    for modifier in parts[:-1]:
        mapped = modifier_names.get(re.sub(r"[\s_-]", "", modifier.lower()))
        if not mapped:
            raise ValueError(f"unsupported modifier: {modifier}")
        if mapped not in modifiers:
            modifiers.append(mapped)

    raw_key = parts[-1]
    alias = re.sub(r"[\s_-]", "", raw_key.lower())
    key = key_names.get(alias, punctuation.get(raw_key, raw_key))
    if re.fullmatch(r"[A-Za-z]", key):
        # Shift is carried by the modifier, not by an uppercase keysym.
        key = key.lower()
    elif re.fullmatch(r"f(?:[1-9]|[12][0-9]|3[0-5])", key, re.I):
        key = key.upper()
    # Other XKB names (e.g. XF86AudioMute and KP_Enter) pass through to wtype.
    if not re.fullmatch(r"[A-Za-z0-9_]+", key):
        raise ValueError(f"unsupported key: {raw_key}")

    command = [wtype]
    for modifier in modifiers:
        command += ["-M", modifier]

    command += ["-k", key]

    for modifier in reversed(modifiers):
        command += ["-m", modifier]

    return command


def run_shortcut(shortcut):
    try:
        command = wtype_command(shortcut)
    except (RuntimeError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    # The overlay still owns keyboard focus while this process is started.
    # Run wtype detached after a short delay so QuickShell can close first.
    delayed_command = "sleep 0.15; exec " + shlex.join(command)

    subprocess.Popen(
        ["/bin/sh", "-c", delayed_command],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    return 0


def build_output():
    merged = {}

    for item in parse_file(DEFAULTS):
        merged[combo_id(item)] = item

    for item in parse_file(CUSTOM):
        combo = combo_id(item)
        if item["action"] == "Disable":
            merged.pop(combo, None)
        else:
            merged[combo] = item

    output = []

    for item in merged.values():
        description = item["description"] or pretty_action(item["action"])
        output.append({
            "shortcut": " + ".join(item["modifiers"] + [item["key"]]),
            "description": description,
            "action": item["action"],
            "category": category_for(item["action"], description),
        })

    category_order = {
        "Window Management": 0,
        "Workspaces": 1,
        "Applications": 2,
        "Displays": 3,
        "Screenshots": 4,
        "System": 5,
        "Other": 6,
    }

    output.sort(
        key=lambda x: (
            category_order.get(x["category"], 99),
            x["description"].lower(),
            x["shortcut"].lower(),
        )
    )

    return output


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--run":
        return run_shortcut(sys.argv[2])

    print(json.dumps(build_output(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
