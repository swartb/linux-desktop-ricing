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

    parts = [part.strip() for part in shortcut.split(" + ") if part.strip()]
    if not parts:
        raise ValueError("empty shortcut")

    modifier_names = {
        "super": "logo",
        "logo": "logo",
        "win": "logo",
        "ctrl": "ctrl",
        "control": "ctrl",
        "shift": "shift",
        "alt": "alt",
        "altgr": "altgr",
        "capslock": "capslock",
    }

    key_names = {
        "Enter": "Return",
        "Space": "space",
        "Esc": "Escape",
    }

    modifiers = []
    for modifier in parts[:-1]:
        mapped = modifier_names.get(modifier.lower())
        if not mapped:
            raise ValueError(f"unsupported modifier: {modifier}")
        modifiers.append(mapped)

    key = key_names.get(parts[-1], parts[-1])

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
