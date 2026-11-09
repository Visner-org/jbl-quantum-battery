#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Watch the jbl-quantum-battery tray icon and check it does what it should.

Every 10 s it reads the headset level, link and cable straight from the dongle, works out on its
own whether the bolt should show (plugged in, below 100%, and a 5% step within the last 30 min),
then reads the real tray icon over D-Bus (is it shown, is there a yellow bolt in its pixels) and
compares. Changes and mismatches go to ~/jbl-monitor.log (and the screen). Read-only.

Usage: tools/monitor.py [--log FILE] [--interval SECONDS]
"""
import argparse, importlib.machinery, importlib.util, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
STALL = 30 * 60
GRACE = 30  # seconds a mismatch may last before it is reported (icon updates every 10 s)


def load_app():
    path = os.path.join(HERE, '..', 'jbl-quantum-battery')
    loader = importlib.machinery.SourceFileLoader('jblq', path)
    spec = importlib.util.spec_from_loader('jblq', loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def busctl(*args):
    r = subprocess.run(['busctl', '--user', '--json=short', *args], capture_output=True, text=True, timeout=5)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def find_tray_item():
    """Bus name of the tray icon whose Id is jbl-quantum-battery, or None."""
    items = busctl('get-property', 'org.kde.StatusNotifierWatcher', '/StatusNotifierWatcher',
                   'org.kde.StatusNotifierWatcher', 'RegisteredStatusNotifierItems')
    for item in (items or {}).get('data', []):
        name, _, path = item.partition('/')
        r = busctl('get-property', name, '/' + path, 'org.kde.StatusNotifierItem', 'Id')
        if r and r.get('data') == 'jbl-quantum-battery':
            return name, '/' + path
    return None


def read_icon(item):
    """(shown, bolt visible) from the tray icon, or (None, None) if it can't be read."""
    if not item:
        return False, False
    name, path = item
    st = busctl('get-property', name, path, 'org.kde.StatusNotifierItem', 'Status')
    px = busctl('get-property', name, path, 'org.kde.StatusNotifierItem', 'IconPixmap')
    if not st or not px:
        return None, None
    best = max(px['data'], key=lambda i: i[0] * i[1], default=None)
    if not best:
        return st['data'] != 'Passive', False
    # ARGB32 bytes; the bolt is #fdd835 (opaque yellow) and nothing else in the icon is
    data = bytes(best[2])
    bolt = sum(1 for i in range(0, len(data) - 3, 4)  # bytes are A, R, G, B
               if data[i] > 200 and data[i + 1] > 230 and data[i + 2] > 180 and data[i + 3] < 110) > 40
    return st['data'] != 'Passive', bolt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', default=os.path.expanduser('~/jbl-monitor.log'))
    ap.add_argument('--interval', type=int, default=10)
    a = ap.parse_args()
    app = load_app()
    logf = open(a.log, 'a', buffering=1)

    def log(msg):
        line = time.strftime('%Y-%m-%d %H:%M:%S ') + msg
        print(line, flush=True)
        logf.write(line + '\n')

    fd = None
    plugged_prev, level_prev, last_rise, bad_since, prev_key = False, None, 0.0, None, None
    log('monitor started')
    while True:
        now = time.monotonic()
        on = level = cable = None
        try:
            if fd is None:
                d = app.find_dongle()
                if d:
                    fd = os.open(d[0], os.O_RDWR | os.O_NONBLOCK)
                    dongle = d
            if fd is not None:
                on, level = app.read_state(fd)
                cable = app.usb_present(app.VENDOR, dongle[2])
        except OSError:
            if fd is not None:
                os.close(fd)
            fd = None

        # expected bolt, worked out separately from the app
        if not on or level is None:
            expect_shown, expect_bolt = False, False
            plugged_prev, level_prev = False, None
        else:
            if not cable:
                plugged_prev = False
            elif not plugged_prev or (level_prev is not None and level > level_prev):
                last_rise = now
                plugged_prev = True
            level_prev = level
            expect_shown = True
            expect_bolt = bool(cable) and level < 100 and now - last_rise < STALL

        shown, bolt = read_icon(find_tray_item())
        since = int(now - last_rise) if plugged_prev else None
        key = (on, level, cable, expect_bolt, shown, bolt)
        if key != prev_key:
            log(f'headset={"on" if on else "off"} level={level} cable={cable} '
                f'since_rise={since}s | expected: shown={expect_shown} bolt={expect_bolt} | '
                f'icon: shown={shown} bolt={bolt}')
            prev_key = key
        ok = shown is None or (shown == expect_shown and (not expect_shown or bolt == expect_bolt))
        if ok:
            if bad_since is not None:
                log('OK again')
            bad_since = None
        else:
            bad_since = bad_since or now
            if now - bad_since >= GRACE and now - bad_since < GRACE + a.interval:
                log(f'MISMATCH for {int(now - bad_since)}s: expected shown={expect_shown} bolt={expect_bolt}, '
                    f'icon shown={shown} bolt={bolt}')
        time.sleep(a.interval)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
