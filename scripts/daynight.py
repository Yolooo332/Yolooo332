#!/usr/bin/env python3
"""Point the README at the white or the black artwork, depending on whether the sun is up.

A README can't run code and CSS has no "time of day", so .github/workflows/profile.yml runs
this every ten minutes around sunrise and sunset and commits when the answer flips. It swaps
every card (cards/<name>-light.svg <-> -dark.svg), the stack animation
(assets/stack-light.gif <-> -dark.gif) and the badge colours. The page around them still
follows each visitor's own GitHub theme; only the artwork follows the sun.

The place is "daylight" in data/content.json. Sun position: the standard low-precision
solar formulas (good to about 0.01 degrees); the sun counts as up above -0.833 degrees,
the usual sunrise/sunset altitude once refraction and the sun's radius are allowed for.
Standard library only, so the frequent check needs no installs.

    python scripts/daynight.py             # rewrite README.md for right now
    python scripts/daynight.py --check     # print today's sunrise/sunset and the mode, change nothing
    python scripts/daynight.py --mode dark # force a mode
"""
import argparse
import datetime as dt
import json
import math
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
README = os.path.join(ROOT, "README.md")
PLACE = json.load(open(os.path.join(ROOT, "data", "content.json")))["daylight"]
HORIZON = -0.833

# badge background and logo colour per mode (the badge text colour shields picks itself)
BADGES = {"dark": ("000000", "89cff0"), "light": ("ffffff", "2a74a3")}


def sun_elevation(when, lat, lon):
    """Solar elevation in degrees at a UTC datetime."""
    n = (when - dt.datetime(2000, 1, 1, 12, tzinfo=dt.timezone.utc)).total_seconds() / 86400
    mean_lon = math.radians((280.460 + 0.9856474 * n) % 360)
    anomaly = math.radians((357.528 + 0.9856003 * n) % 360)
    ecl_lon = mean_lon + math.radians(1.915 * math.sin(anomaly) + 0.020 * math.sin(2 * anomaly))
    tilt = math.radians(23.439 - 0.0000004 * n)
    ra = math.atan2(math.cos(tilt) * math.sin(ecl_lon), math.cos(ecl_lon))
    dec = math.asin(math.sin(tilt) * math.sin(ecl_lon))
    sidereal = math.radians((280.46061837 + 360.98564736629 * n + lon) % 360)
    hour = sidereal - ra
    phi = math.radians(lat)
    return math.degrees(math.asin(math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(hour)))


def mode_at(when):
    return "light" if sun_elevation(when, PLACE["lat"], PLACE["lon"]) > HORIZON else "dark"


def crossings(day):
    """Sunrise and sunset (UTC) on a date, to the minute."""
    start = dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc)
    out, prev = [], mode_at(start)
    for m in range(1, 24 * 60 + 1):
        t = start + dt.timedelta(minutes=m)
        cur = mode_at(t)
        if cur != prev:
            out.append(("sunrise" if cur == "light" else "sunset", t))
        prev = cur
    return out


def apply(md, mode):
    md = re.sub(r"(\./cards/[\w-]+)-(?:dark|light)\.svg", rf"\1-{mode}.svg", md)
    md = re.sub(r"(assets/[\w-]+)-(?:dark|light)\.gif", rf"\1-{mode}.gif", md)
    bg, logo = BADGES[mode]
    return re.sub(r"(img\.shields\.io/badge/[^\"?]*)-[0-9a-f]{6}\?style=flat-square&logo=([\w.-]+)&logoColor=[0-9a-f]{6}",
                  rf"\1-{bg}?style=flat-square&logo=\2&logoColor={logo}", md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["light", "dark"])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    mode = a.mode or mode_at(now)
    if a.check:
        times = ", ".join(f"{k} {t:%H:%M} UTC" for k, t in crossings(now.date()))
        print(f"{PLACE['place']}: {times}; now {now:%H:%M} UTC, sun at "
              f"{sun_elevation(now, PLACE['lat'], PLACE['lon']):.1f}°, mode {mode}")
        return
    md = open(README).read()
    new = apply(md, mode)
    if new != md:
        open(README, "w").write(new)
        print(f"daynight: switched README to {mode}")
    else:
        print(f"daynight: already {mode}")


if __name__ == "__main__":
    main()
