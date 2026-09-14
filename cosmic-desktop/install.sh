#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$HOME/.config/quickshell-shortcuts"

mkdir -p "$TARGET_DIR"
cp "$SOURCE_DIR/shell.qml" "$TARGET_DIR/shell.qml"
cp "$SOURCE_DIR/shortcuts.py" "$TARGET_DIR/shortcuts.py"
chmod +x "$TARGET_DIR/shortcuts.py"

printf 'Installed COSMIC shortcuts overlay to %s\n' "$TARGET_DIR"
printf 'Run with: quickshell -p %s\n' "$TARGET_DIR"
