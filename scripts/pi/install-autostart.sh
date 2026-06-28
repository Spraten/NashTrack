#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AUTOSTART_DIR="${HOME}/.config/autostart"
DESKTOP_FILE="${AUTOSTART_DIR}/nashtrack.desktop"

mkdir -p "${AUTOSTART_DIR}"

cat > "${DESKTOP_FILE}" <<EOF
[Desktop Entry]
Type=Application
Name=NashTrack
Comment=Launch NashTrack sports dashboard
Exec=python3 ${ROOT_DIR}/main.py
Path=${ROOT_DIR}
Terminal=false
StartupNotify=false
X-GNOME-Autostart-enabled=true
EOF

chmod +x "${DESKTOP_FILE}"
echo "NashTrack autostart installed at ${DESKTOP_FILE}"
