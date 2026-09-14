#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
trap 'printf "Installatie gestopt op regel %s. Reeds gemaakte backups blijven bewaard.\n" "$LINENO" >&2' ERR
# Run as the desktop user so systemctl --user addresses the correct session.
if (( EUID == 0 )); then
  echo 'Start dit script zonder sudo vanuit je COSMIC-terminal; het vraagt zelf sudo waar nodig.' >&2
  exit 1
fi
user_name=$(id -un)
user_home=$(getent passwd "$(id -u)" | cut -d: -f6)
[[ -n "$user_home" && "$user_home" == /* && -d "$user_home" ]] || exit 1
export HOME="$user_home"
[[ -f /etc/fedora-release && ! -e /run/ostree-booted ]] || {
  echo 'Dit script is voor reguliere Fedora met DNF, niet voor Atomic/OSTree.' >&2; exit 1;
}
[[ -n "${WAYLAND_DISPLAY:-}" && -n "${XDG_RUNTIME_DIR:-}" ]] || {
  echo 'Start vanuit een ingelogde COSMIC Wayland-sessie.' >&2; exit 1;
}
systemctl --user show-environment >/dev/null
sudo -v
sudo dnf copr enable alternateved/keyd
sudo dnf install keyd curl python3
stage=$(mktemp -d)
trap 'rm -rf -- "$stage"' EXIT
stamp=$(date +%Y%m%d-%H%M%S)-$$
backup="$HOME/.local/state/keyd-super-clipboard/backups/$stamp"
mkdir -p "$backup"
printf 'Gebruiker: %s\nHome: %s\nBackups: %s\n' "$user_name" "$HOME" "$backup"
# Download first; never pipe remote code into a shell.
url=https://raw.githubusercontent.com/rvaiya/keyd/master/scripts/keyd-application-mapper
curl --fail --show-error --location --proto '=https' --proto-redir '=https' \
  --connect-timeout 20 --max-time 120 "$url" -o "$stage/mapper"
python3 - "$stage/mapper" <<'PY'
import ast, pathlib, sys
s = pathlib.Path(sys.argv[1]).read_text()
ast.parse(s)
if 'class Cosmic' not in s or 'keyd' not in s:
    raise SystemExit('Onverwachte upstream mapper; installatie afgebroken.')
PY
printf '%s\n' "$url" > "$backup/mapper-source.txt"
sha256sum "$stage/mapper" > "$backup/mapper-sha256.txt"
# Back up all existing global config before installing our default.
if sudo test -e /etc/keyd; then sudo cp -a /etc/keyd "$backup/etc-keyd"; fi
if sudo test -e /usr/bin/keyd-application-mapper; then
  sudo cp -a /usr/bin/keyd-application-mapper "/usr/bin/keyd-application-mapper.bak-$stamp"
  printf '%s\n' "/usr/bin/keyd-application-mapper.bak-$stamp" > "$backup/mapper-backup-path.txt"
fi
for rel in .config/keyd/app.conf .config/systemd/user/keyd-application-mapper.service; do
  file="$HOME/$rel"
  if [[ -e "$file" || -L "$file" ]]; then
    [[ ! -d "$file" ]] || { echo "Onverwachte directory: $file" >&2; exit 1; }
    mkdir -p "$backup/$(dirname "$rel")"
    cp -a -- "$file" "$backup/$rel"
    # Also preserve symlink target contents for manual recovery.
    if [[ -L "$file" && -f "$file" ]]; then cp -L -- "$file" "$backup/$rel.target"; fi
  fi
done
cat > "$stage/default.conf" <<'EOF'
[ids]
*

[meta]
a = C-a
c = C-insert
v = S-insert
x = C-x
EOF
cat > "$stage/app.conf" <<'EOF'
[com-system76-cosmicterm]
meta.c = C-S-c
meta.v = C-S-v

[kitty]
meta.c = C-S-c
meta.v = C-S-v

[foot]
meta.c = C-S-c
meta.v = C-S-v

[alacritty]
meta.c = C-S-c
meta.v = C-S-v
EOF
cat > "$stage/mapper.service" <<'EOF'
[Unit]
Description=keyd application mapper
After=graphical-session.target

[Service]
ExecStart=/usr/bin/keyd-application-mapper
Restart=on-failure

[Install]
WantedBy=default.target
EOF
sudo install -d -m 0755 /etc/keyd
# Remove backed-up symlinks instead of following them during replacement.
sudo rm -f /etc/keyd/default.conf
sudo install -m 0644 "$stage/default.conf" /etc/keyd/default.conf
sudo rm -f /usr/bin/keyd-application-mapper
sudo install -m 0755 "$stage/mapper" /usr/bin/keyd-application-mapper
if command -v restorecon >/dev/null; then
  sudo restorecon /etc/keyd/default.conf /usr/bin/keyd-application-mapper
fi
mkdir -p "$HOME/.config/keyd" "$HOME/.config/systemd/user"
rm -f "$HOME/.config/keyd/app.conf" "$HOME/.config/systemd/user/keyd-application-mapper.service"
install -m 0644 "$stage/app.conf" "$HOME/.config/keyd/app.conf"
install -m 0644 "$stage/mapper.service" "$HOME/.config/systemd/user/keyd-application-mapper.service"
getent group keyd >/dev/null || sudo groupadd --system keyd
sudo usermod -aG keyd "$user_name"
sudo systemctl enable --now keyd.service
sudo systemctl restart keyd.service
systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_RUNTIME_DIR
systemctl --user daemon-reload
if systemctl --user enable --now keyd-application-mapper.service; then
  systemctl --user restart keyd-application-mapper.service || echo 'Herstart mapper na opnieuw inloggen.'
else
  echo 'Mapper kon nog niet starten. Log volledig uit en weer in en herstart de service.' >&2
fi
printf '\nBestanden geïnstalleerd. Backups: %s\n' "$backup"
echo 'BELANGRIJK: log volledig uit en weer in (of reboot) voor de nieuwe keyd-groeprechten.'
echo 'Controleer daarna: systemctl --user status keyd-application-mapper.service --no-pager'
echo 'Test Super+C/V in een gewone app en in COSMIC Terminal; wissel eerst van venster.'
