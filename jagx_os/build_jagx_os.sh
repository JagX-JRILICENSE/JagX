#!/usr/bin/env bash
set -euo pipefail

# JagX OS is a free Debian live environment foundation.
# It intentionally does not modify the host bootloader.

ROOT="$(cd "$(dirname "$0")" && pwd)"
BUILD="${ROOT}/build"
rm -rf "$BUILD"
mkdir -p "$BUILD"
cd "$BUILD"

# Explicit Debian mirrors are required because GitHub's Ubuntu runner can
# otherwise cause live-build to inherit Ubuntu's mirror configuration while
# the requested distribution is Debian bookworm.
lb config \
  --distribution bookworm \
  --architectures amd64 \
  --archive-areas "main contrib non-free-firmware" \
  --mirror-bootstrap "http://deb.debian.org/debian/" \
  --mirror-binary "http://deb.debian.org/debian/" \
  --mirror-binary-security "http://security.debian.org/debian-security/" \
  --debian-installer false \
  --binary-images iso-hybrid \
  --bootappend-live "boot=live components quiet splash"

mkdir -p config/package-lists config/includes.chroot/usr/local/bin config/includes.chroot/etc/xdg/autostart
cat > config/package-lists/jagx.list.chroot <<'EOF'
xfce4
xfce4-terminal
thunar
network-manager
network-manager-gnome
python3
python3-pip
python3-venv
python3-tk
git
curl
wget
ca-certificates
sudo
pciutils
usbutils
htop
EOF

install -m 0755 "${ROOT}/jagx-session.sh" config/includes.chroot/usr/local/bin/jagx-session
cat > config/includes.chroot/etc/xdg/autostart/jagx.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=JagX Command Center
Exec=/usr/local/bin/jagx-session
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

# live-build requires root for chroot/bootstrap operations.
sudo lb build
mkdir -p "${ROOT}/dist"
sudo cp live-image-amd64.hybrid.iso "${ROOT}/dist/JagX-OS-amd64.iso"
sudo chown "$(id -u):$(id -g)" "${ROOT}/dist/JagX-OS-amd64.iso"
echo "Built ${ROOT}/dist/JagX-OS-amd64.iso"
