#!/bin/sh
set -eu

mkdir -p "$HOME/JagX"
cat > "$HOME/Desktop/JagX-OS-README.txt" <<'EOF'
JagX OS

This is the free Debian-based JagX OS foundation.
It boots as a live environment and does not change Windows boot settings automatically.

Place a JagX application build in ~/JagX when extending this image.
EOF

# If a bundled JagX launcher is present, run it; otherwise show the OS foundation notice.
if [ -x "$HOME/JagX/jagx-launcher" ]; then
  exec "$HOME/JagX/jagx-launcher"
fi

xfce4-terminal --title="JagX OS" --command="sh -c 'printf \"JagX OS is ready. Install or bundle the JagX assistant to launch it here.\\n\\n\"; exec bash'" >/dev/null 2>&1 || true
