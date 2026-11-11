# stack: an orrery of the languages I write, orbiting a shaded core.
# Technique mix: per-cell field (the core, the pulse rings) + point splats
# with a depth buffer (orbits, comets, labels).

import numpy as np
from asciianim import *

PALETTE = ["#4338ca", "#8b5cf6", "#22d3ee", "#5eead4", "#effcff", "#6e7681", "#ff5fa2", "#c9d1d9",
           "#a8b9cc", "#f34b7d", "#41b883", "#4f9cf0", "#f7df1e", "#8a94ff", "#f89820", "#e34c26"]
INDIGO, VIOLET, CYAN, MINT, WHITE, DIM, PINK, STAR = range(8)
C_, CPP, VUE, TSX, JS, LUA, JAVA, HTML = range(8, 16)

LOOP = 8.0
CONFIG = dict(width=960, height=360, cell=(7, 12), font_px=12, fps=12, duration=LOOP,
              palette=PALETTE, trail=0.22, bloom=[(4, 5, 0.6), (8, 22, 0.4)])

R0 = 0.15                        # core radius
LIGHT = np.array([-0.55, -0.6, 0.58]) / np.linalg.norm([-0.55, -0.6, 0.58])

# An atom: two steep crossed orbits for the systems languages, one wide
# equator for the web. stretch widens an orbit to use the wide canvas.
#          radius incline roll stretch turns ring tag  labels (name, colour, start angle)
ORBITS = [(0.30,  74,     57,  1.30,   2,    VIOLET,   [(".c", C_, 0.3), (".cpp", CPP, 3.4)]),
          (0.30,  74,    -57,  1.30,  -1,    VIOLET,   [(".lua", LUA, 1.0), (".java", JAVA, 4.1)]),
          (0.40,  72,      0,  2.55,   1,    INDIGO,   [(".vue", VUE, 0.4), (".tsx", TSX, 1.65), (".js", JS, 2.9),
                                                         (".html", HTML, 4.15), (".css", TSX, 5.4)])]


def orbit_xyz(a, inc, roll, stretch, th):
    """3D circle -> screen (x, y) plus depth z (z > 0 is in front of the core)."""
    inc, roll = np.radians(inc), np.radians(roll)
    x = a * np.cos(th) * stretch
    y = a * np.sin(th) * np.cos(inc)
    z = a * np.sin(th) * np.sin(inc)
    xr = x * np.cos(roll) - y * np.sin(roll)
    yr = x * np.sin(roll) + y * np.cos(roll)
    return xr, yr, z


def hidden(x, y, z):
    return (z < 0) & (np.hypot(x, y) < R0 * 1.05)


def frame(t, g):
    X, Y, r = g.X, g.Y, g.r
    L = g.layer()
    zbuf = np.full(g.shape, -np.inf)
    beat = fract(t / 2.0)                               # the core beats every 2 s (4 per loop)

    # 1. pulse rings leaving the core, drawn along their own tangent
    for k in range(2):
        f = fract(beat + k * 0.5)
        front = R0 + f * 0.75
        ring = gauss(r - front, 0.008) * (1 - f) ** 1.6
        L.put(ring > 0.25, tangent(-np.sin(g.ang), np.cos(g.ang)), 0.55 * ring, VIOLET)

    # 2. orbit paths: faint, brighter on the near side
    th = np.linspace(0, TAU, 900, endpoint=False)
    for a, inc, roll, st, turns, rtag, labels in ORBITS:
        x, y, z = orbit_xyz(a, inc, roll, st, th)
        lum = np.where(hidden(x, y, z), 0.0, 0.3 + 0.35 * (z / a + 1) / 2)
        lum = np.where(np.hypot(x, y) < R0, lum * 0.45, lum)        # don't scribble over the core
        zbuf = polyline_splat(g, L, x, y, lum, rtag, zs=z, zbuf=zbuf)

    # 3. the core: a lit sphere whose glyphs drift with its spin
    inside = r < R0
    zc = np.sqrt(np.clip(R0 ** 2 - r ** 2, 0, None)) / R0
    n = np.stack([X / R0, Y / R0, zc])
    lam = np.clip(np.tensordot(LIGHT, n, axes=1), 0, 1)
    lon = np.arctan2(X / R0, zc) + TAU * t / LOOP
    grid_line = gauss(fract(lon * 6 / TAU) - 0.5, 0.06) + gauss(fract((Y / R0) * 2.5) - 0.5, 0.05)
    heat = 1.05 * lam ** 1.4 + 0.22 * grid_line * lam + 0.35 * gauss(beat, 0.08)
    lit = inside & (heat > 0.1)                          # the night side stays empty: a crescent
    L.put(lit, shade(heat, g.hsh, lon * 5), 0.3 + 0.8 * heat, levels(heat, [0.3, 0.55, 0.8, 1.0]))
    rim = inside & ~lit & (r > R0 * 0.82)
    L.put(rim, tangent(-np.sin(g.ang), np.cos(g.ang)), 0.35, INDIGO)
    zbuf = np.where(inside, 0.0, zbuf)
    cr = g.rows // 2
    L.text(cr, "center", "</>", 1.3, WHITE)

    # 4. labels riding the orbits, each with a comet tail
    for a, inc, roll, st, turns, rtag, labels in ORBITS:
        w = TAU * turns / LOOP
        for name, tag, start in labels:
            ang = start + w * t
            back = ang - np.sign(turns) * np.linspace(0, 1.1, 70)
            x, y, z = orbit_xyz(a, inc, roll, st, back)
            depth = 0.55 + 0.45 * (z / a + 1) / 2
            fade = np.exp(-np.linspace(0, 1.1, 70) / 0.35) * depth
            fade = np.where(hidden(x, y, z), 0.0, fade)
            zbuf = polyline_splat(g, L, x, y, fade, tag, zs=z + 0.001, zbuf=zbuf)
            if hidden(x[0], y[0], z[0]):
                continue
            c, rr = g.to_cell(x[0], y[0])
            lum = 0.6 + 0.6 * float(depth[0])
            L.text(int(rr), int(c), "●", lum * 1.1, tag)
            L.text(int(rr), int(c) + 2, name, lum, tag)

    # 5. frame text
    L.text(1, 2, "$ ls ~/stack --orbit", 0.6, MINT)
    L.text(g.rows - 2, 2, "langs 09  ·  orbits 03  ·  loop 08s", 0.4, DIM)
    L.text(g.rows - 2, g.cols - 23, "front-end <-> systems", 0.4, DIM)
    stars(g, L, t, density=0.004, tag=STAR, lum=0.4)
    return L
