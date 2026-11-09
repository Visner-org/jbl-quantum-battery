# jbl-quantum-battery

A Linux tray icon showing the battery level of a JBL Quantum wireless headset over its 2.4 GHz USB dongle.

On Linux, the dongle doesn't report the battery in a way the system understands, so KDE, GNOME and UPower show nothing. Over Bluetooth you get a level in 10% steps; the dongle reports it in 5% steps.

The icon shows the percent with a bar under it:
- green above 30%, orange from 16 to 30%, red at 15% or below
- blue, with a yellow lightning bolt, while the headset is charging: its USB cable is plugged in, it is below 100%, and the level rose within the last 30 minutes (the bolt goes away after 30 minutes with no 5% step, and at 100%)

It hides while the headset is off. Hover for the tooltip, and right-click to quit.

## Supported headsets

| Headset | Dongle USB ID | Status |
|---|---|---|
| JBL Quantum 810 Wireless | `0ecb:2069` | tested |

Other JBL Quantum wireless headsets may speak the same protocol. If yours has a different dongle ID, run `lsusb | grep 0ecb` and open an issue with the output. You can also try adding the ID to `DONGLES` in the script and to the udev rule.

## Install

Needs Python 3 and PyQt6 (`python3-pyqt6` on Fedora, `python3-pyqt6` on Debian/Ubuntu, `python-pyqt6` on Arch).

```sh
git clone https://github.com/Visner-org/jbl-quantum-battery
cd jbl-quantum-battery
./install.sh
```

This puts the script in `~/.local/bin`, adds a systemd user service that starts it with your desktop session, and installs a udev rule (asks for sudo once). The rule lets the logged-in user read the dongle.

`jbl-quantum-battery --print` prints the level once, for scripts or status bars. Exit code 0 means it printed a level, 2 means the headset is off, and 1 means it found no dongle or lacks permission.

Remove it with `./uninstall.sh`.

## How it works

The dongle is a USB HID device with a vendor-defined interface (usage page `0xFF13`). Found by probing a Quantum 810:

| Report | Type | Meaning |
|---|---|---|
| `0x49` | feature, 1 byte | battery percent, in 5% steps. Keeps its last value while the headset is off. |
| `0x68` | feature, 1 byte | headset link: `1` = on, `0` = off (`0x69` mirrors it) |
| `0x09` | input, 1 byte | sent when the headset turns off (`00`) or on (`01`) |
| `0x08` | input, 1 byte | battery percent. Sent only in reply to the host's requests, so not useful to listen for on its own. |
| `0x47` | feature, 1 byte | `1` while a Bluetooth device is also connected |

The app reads `0x68` and `0x49` every 10 seconds. It also reacts right away to `0x09`.

When the headset's USB cable is plugged into the PC, the headset shows up as a separate device (`0ecb:206a` for the 810). It refuses these reads over the cable, so the app only uses it to show the "plugged in" color.

Not affiliated with JBL or Harman.

## License

GPL-3.0. See `LICENSE`.
