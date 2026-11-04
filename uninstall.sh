#!/bin/sh
# Removes jbl-quantum-battery for the current user, and the udev rule (sudo).
systemctl --user disable --now jbl-quantum-battery.service 2>/dev/null
rm -f "$HOME/.local/bin/jbl-quantum-battery" "$HOME/.config/systemd/user/jbl-quantum-battery.service"
systemctl --user daemon-reload
if [ -f /etc/udev/rules.d/70-jbl-quantum-battery.rules ]; then
    sudo rm /etc/udev/rules.d/70-jbl-quantum-battery.rules && sudo udevadm control --reload
fi
echo "Removed."
