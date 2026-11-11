# flow: an animated full-stack request diagram.
# Requests travel right on the upper wires, responses come back on the lower ones.
# Boxes flash when a packet lands; a soft field glow sits under each box.

import numpy as np
from asciianim import *

#          wire       cyan       mint       white      dim        pink       violet     star
PALETTE = ["#484f58", "#22d3ee", "#5eead4", "#effcff", "#8b949e", "#ff5fa2", "#8b5cf6", "#c9d1d9",
           "#41b883", "#4f9cf0", "#336791", "#00a3e0", "#47a248"]
WIRE, CYAN, MINT, WHITE, DIM, PINK, VIOLET, STAR, VUE, TS, PG, MY, MONGO = range(13)

LOOP = 6.0
CONFIG = dict(width=960, height=240, cell=(7, 12), font_px=12, fps=12, duration=LOOP,
              palette=PALETTE, trail=0.35, bloom=[(4, 4, 0.6), (8, 18, 0.4)])

SPACING = 16          # cells between packets
GAP = 12              # cells between boxes
#        name       height width lines                                        accent
BOXES = [("client",   7, 17, ["browser", "", "you are here"],                 DIM),
         ("front",    7, 21, ["frontend", "", "vue · vuetify", "tailwind · ts"], VUE),
         ("api",      7, 19, ["api", "", "rest · auth", "js · ts"],             VIOLET),
         ("db",       7, 21, ["database", "", "postgres · mysql", "mongodb"],   MONGO)]
TOP = 7


def layout(cols):
    total = sum(b[2] for b in BOXES) + GAP * (len(BOXES) - 1)
    c = (cols - total) // 2
    out = {}
    for name, h, w, lines, accent in BOXES:
        out[name] = (TOP, c, h, w, lines, accent)
        c += w + GAP
    return out


def edges(B):
    """(waypoints, kind, cycles-per-loop, phase, target box)."""
    names = [b[0] for b in BOXES]
    out = []
    for i, (a, b) in enumerate(zip(names, names[1:])):
        A, Bb = B[a], B[b]
        out.append(([(TOP + 2, A[1] + A[3]), (TOP + 2, Bb[1] - 1)], "req", 3, 0.15 * i, b))
        out.append(([(TOP + 4, Bb[1] - 1), (TOP + 4, A[1] + A[3])], "res", 3, 0.5 + 0.15 * i, a))
    return out


def setup(g):
    B = g.cache["boxes"] = layout(g.cols)
    g.cache["edges"] = edges(B)
    halos = {}
    for name, (r, c, h, w, _, _) in B.items():
        cy, cx = r + h / 2, c + w / 2
        d = np.hypot((g.R - cy) / (h * 0.9), (g.C - cx) / (w * 0.65))
        halos[name] = np.exp(-d ** 2)
    g.cache["halos"] = halos


def frame(t, g):
    L = g.layer()
    B = g.cache["boxes"]
    flash = {k: 0.0 for k in B}

    # 1. wires + packets (wires first so packets sit on top)
    paths = []
    for pts, kind, cycles, phase, target in g.cache["edges"]:
        path = wire(L, pts, lum=0.9, tag=WIRE)
        paths.append((path, kind, cycles, phase, target))
    for path, kind, cycles, phase, target in paths:
        speed = SPACING * cycles / LOOP
        heads = packets(L, path, t, speed=speed, spacing=SPACING, tail=6, lum=1.25,
                        tag=CYAN if kind == "req" else MINT, tail_tag=VIOLET if kind == "req" else MINT,
                        head="●" if kind == "req" else "•", phase=phase)
        n = len(path)
        for h in heads:
            flash[target] = max(flash[target], float(np.exp(-max(n - 1 - h, 0) / 1.5)))

    # 2. a soft glow field under each box that swells when a packet lands
    for name, halo in g.cache["halos"].items():
        e = halo * (0.25 + 0.75 * flash[name])
        m = (L.char == 0) & (g.rnd < e * 0.55) & (e > 0.12)
        L.put(m, np.where(g.rnd < 0.12, ch(":"), ch("·")), 0.2 + 0.5 * e, B[name][5])

    # 3. boxes on top
    for name, (r, c, h, w, lines, accent) in B.items():
        f = flash[name]
        box(L, r, c, h, w, lum=0.5 + 0.7 * f, tag=accent if f > 0.2 else WIRE, fill=(" ", 0, 0))
        r0 = r + (h - len(lines)) // 2
        for i, line in enumerate(lines):
            L.text(r0 + i, c + (w - len(line)) // 2, line, (1.05 if i == 0 else 0.65) + 0.3 * f,
                   (accent if accent != DIM else WHITE) if i == 0 else DIM)

    # 4. captions
    e = L.text(2, B["client"][1], "$ trace ", 0.6, MINT)
    L.text(2, e, "GET /api/projects", 0.85, WHITE)
    left = B["client"][1]
    L.text(TOP + 10, left, "● request", 0.75, CYAN)
    L.text(TOP + 10, left + 12, "• response", 0.75, MINT)
    right = B["db"][1] + B["db"][3]
    L.text(TOP + 10, right - 22, "200 OK  ·  p50 12 ms", 0.55, DIM)
    stars(g, L, t, density=0.002, tag=STAR, lum=0.3)
    return L
