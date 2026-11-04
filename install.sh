#!/bin/sh
# Installs jbl-quantum-battery for the current user. The udev rule needs sudo once.
set -e
cd "$(dirname "$0")"

install -Dm755 jbl-quantum-battery "$HOME/.local/bin/jbl-quantum-battery"
install -Dm644 jbl-quantum-battery.service "$HOME/.config/systemd/user/jbl-quantum-battery.service"

if [ ! -f /etc/udev/rules.d/70-jbl-quantum-battery.rules ]; then
    echo "Installing the udev rule (needs sudo)..."
    sudo install -m644 70-jbl-quantum-battery.rules /etc/udev/rules.d/
    sudo udevadm control --reload
    sudo udevadm trigger --action=change --subsystem-match=hidraw
fi

systemctl --user daemon-reload
systemctl --user enable --now jbl-quantum-battery.service
echo "Done. The icon shows up while the headset is on."
