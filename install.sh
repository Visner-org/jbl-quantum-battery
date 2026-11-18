#!/bin/sh
# Installs jbl-quantum-battery for the current user. The udev rule needs sudo when it is new or changed.
set -e
cd "$(dirname "$0")"

install -Dm755 jbl-quantum-battery "$HOME/.local/bin/jbl-quantum-battery"
install -Dm644 jbl-quantum-battery.service "$HOME/.config/systemd/user/jbl-quantum-battery.service"

if ! cmp -s 70-jbl-quantum-battery.rules /etc/udev/rules.d/70-jbl-quantum-battery.rules; then
    echo "Installing the udev rule (needs sudo)..."
    sudo install -m644 70-jbl-quantum-battery.rules /etc/udev/rules.d/
    sudo udevadm control --reload
    sudo udevadm trigger --action=change --subsystem-match=hidraw
fi

systemctl --user daemon-reload
systemctl --user enable jbl-quantum-battery.service
systemctl --user restart jbl-quantum-battery.service
echo "Done. The icon shows up while the headset is on."
