#!/usr/bin/env python3
"""Write preview.html: the day (white) and night (black) artwork side by side, each on both
GitHub page colours, since the page follows the visitor's theme and the artwork follows the sun.

    STATIC=1 python scripts/render_cards.py   # finished frames (drop STATIC to watch the motion)
    python scripts/preview.py && open preview.html
"""
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
md = open(os.path.join(ROOT, "README.md")).read()
cards = re.findall(r'src="\./cards/([\w-]+)-(?:dark|light)\.svg"', md)


def column(mode, page, label):
    imgs = "".join(f'<img src="cards/{c}-{mode}.svg" width="100%">' for c in cards)
    imgs += f'<img src="assets/stack-{mode}.gif" width="100%">'
    return f'<div style="background:{page}"><p>{label}</p>{imgs}</div>'


html = ("<!doctype html><meta charset='utf-8'><title>cards preview</title>"
        "<style>body{margin:0;display:flex;gap:24px;padding:24px;background:#6e7681;font:13px ui-monospace,monospace}"
        "div{width:880px;padding:16px}img{display:block}p{margin:0 0 12px;color:#8a8a8a}</style>"
        + column("light", "#ffffff", "day · light GitHub theme")
        + column("dark", "#0d1117", "night · dark GitHub theme"))
open(os.path.join(ROOT, "preview.html"), "w").write(html)
print(f"wrote preview.html ({len(cards)} cards)")
