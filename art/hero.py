# hero: the name ignites under a scan beam, holds, then burns off into embers.
# Rendered with the ascii-animation skill:  python asciianim.py hero.py --gif hero.gif

import numpy as np
from asciianim import *

NAME = "YOLOOO"
PROMPT = "yolooo332@github:~$ "
CMD = "./hello --render"
SUB = "ml systems  ·  self-hosted infra  ·  linux  ·  security  ·  bucharest, ro"

#          indigo     violet     cyan       mint       white      dim        pink       star
PALETTE = ["#4338ca", "#8b5cf6", "#22d3ee", "#5eead4", "#effcff", "#6e7681", "#ff5fa2", "#c9d1d9"]
INDIGO, VIOLET, CYAN, MINT, WHITE, DIM, PINK, STAR = range(8)

CONFIG = dict(width=960, height=320, cell=(7, 12), font_px=12, fps=12, duration=8.0,
              palette=PALETTE, trail=0.42, bloom=[(4, 5, 0.65), (8, 24, 0.45)])

IGNITE = (0.7, 2.5)     # scan beam crosses, letters light behind it
TYPE = (2.3, 4.0)       # subtitle types out
BURN = (6.5, 7.75)      # second pass burns everything off


def setup(g):
    M = text_field(g, NAME, height=0.5, center=(0.0, -0.1), font="monobold")
    soft = blur_field(M, 0.9)
    gy, gx = np.gradient(soft)
    rows = np.flatnonzero(M.max(axis=1) > 0.3)
    cols = np.flatnonzero(M.max(axis=0) > 0.3)
    g.cache.update(
        M=M,
        halo=text_field(g, NAME, height=0.5, center=(0.0, -0.1), font="monobold", blur=14),
        edge=(M > 0.1) & (M < 0.7) & (np.hypot(gx, gy) > 0.02),
        edge_char=tangent(-gy, gx),
        under=rows.max() + 2,
        c0=cols.min() - 2, c1=cols.max() + 3,
    )


def sweep(g, t, a, b):
    A = g.aspect
    return -A / 2 - 0.2 + (A + 0.4) * ramp(t, a, b)


def frame(t, g):
    c = g.cache
    X, Y, M = g.X, g.Y, c["M"]
    L = g.layer()

    s1, s2 = sweep(g, t, *IGNITE), sweep(g, t, *BURN)
    lit = smooth((s1 - X) / 0.1)
    gone = smooth((s2 - X) / 0.06)
    alive = lit * (1 - gone)
    beam_on = window(t, IGNITE[0], IGNITE[1], 0.15)
    front = gauss(X - s1, 0.035) * beam_on

    # 1. soft halo behind the letters: sparse dots, indigo/violet
    halo = c["halo"] * alive * (0.75 + 0.25 * np.sin(1.3 * t + 6 * X))
    hmask = (halo > 0.12) & (M < 0.05) & (g.rnd < halo * 0.9)
    L.put(hmask, np.where(g.rnd < 0.15, ch(":"), ch(".")), 0.25 + 0.5 * halo, np.where(halo > 0.35, VIOLET, INDIGO))

    # 2. the letters: liquid interior, drifting glyphs
    flow = noise(X * 1.3, Y * 2.4, t * 0.9)
    bands = np.sin(9 * (0.55 * X + Y) - 2.2 * t)
    sheen = gauss(fract((X * 0.5 - Y * 0.6) / 1.1 - (t - IGNITE[1]) / 1.9) - 0.5, 0.05) * window(t, IGNITE[1] + 0.3, BURN[0], 0.3)
    heat = M * alive * (0.5 + 0.22 * flow + 0.12 * bands + 0.55 * sheen) + M * front * 1.3
    inside = (M > 0.45) & (heat > 0.05)
    L.put(inside, shade(heat, g.hsh, X * 7 + Y * 3 - t * 2.5), 0.5 + 0.75 * heat,
          levels(heat, [0.3, 0.5, 0.72, 1.0]))

    # 3. contour: glyphs that follow the outline
    em = c["edge"] & (alive > 0.3)
    L.put(em, c["edge_char"], 0.7 + 0.4 * alive + front, np.where(front > 0.3, WHITE, CYAN))

    # 4. the scan beam itself
    beam = (np.abs(X - s1) < 0.011) & (beam_on > 0.05)
    L.put(beam & (M < 0.3), ch("│"), 0.55 * beam_on, VIOLET)
    L.put(beam & (M >= 0.3), ch("█"), 1.3, WHITE)

    # 5. burn-off embers drifting up behind the second front
    behind = s2 - X
    ember_zone = (behind > 0) & (behind < 0.45) & (c["halo"] > 0.05)
    rise = (g.R + (t * 9 + g.rnd * 40).astype(int)) % 7 == 0
    ember = ember_zone & rise & (g.rnd < 0.5 * c["halo"] + 0.05)
    L.put(ember, np.where(g.rnd < 0.3, ch("*"), ch("·")), 0.9 * np.exp(-behind / 0.18), np.where(behind < 0.12, WHITE, PINK))
    L.put(gauss(X - s2, 0.012) * (M > 0.3) * window(t, *BURN, 0.1) > 0.4, ch("▓"), 1.2, PINK)

    # 6. underline rail with a comet running along it while the name holds
    r, c0, c1 = c["under"], c["c0"], c["c1"]
    col = np.arange(c0, c1)
    xcol = ((col + 0.5) / g.cols - 0.5) * g.aspect
    rail = smooth((s1 - xcol) / 0.1) * (1 - smooth((s2 - xcol) / 0.06))
    hold = window(t, IGNITE[1], BURN[0], 0.3)
    head = c0 + (c1 - c0) * fract((t - IGNITE[1]) / 1.35)
    d = head - col
    comet = np.where(d >= 0, np.exp(-d / 9), np.exp(d / 0.8)) * hold
    lum_r = 0.22 * rail + 1.1 * comet
    L.char[r, c0:c1] = np.where(rail > 0.05, np.where(np.abs(d) < 0.6, ch("•"), ch("─")), 0)
    L.lum[r, c0:c1] = lum_r
    L.tag[r, c0:c1] = np.where(comet > 0.5, WHITE, np.where(comet > 0.12, CYAN, VIOLET))

    # 7. subtitle types out, cursor blinks, burn erases it
    k = (len(SUB) + 1) * ramp(t, *TYPE) if t < BURN[0] else len(SUB)
    sc = (g.cols - len(SUB) - 2) // 2
    end = L.text(r + 2, sc, "> ", 0.9, PINK)
    end = L.text(r + 2, end, SUB, 0.75, DIM, reveal=k)
    if TYPE[0] - 0.4 < t < BURN[0] and int(t * 2.4) % 2 == 0:
        L.text(r + 2, end, "█", 0.85, PINK, skip_spaces=False)
    L.put((g.R == r + 2) & (gone > 0.5), 0, 0, 0)

    # 8. terminal prompt in the corner (constant, so the loop is seamless)
    typed = len(CMD) * ramp(t, 0.05, 0.6)
    e = L.text(1, 2, PROMPT, 0.6, MINT)
    e = L.text(1, e, CMD, 0.8, WHITE, reveal=typed)
    if int(t * 2.4) % 2 == 0:
        L.text(1, e, "_", 0.7, WHITE)
    L.text(1, g.cols - 13, "[ README.md ]", 0.45, DIM)

    glitch_rows(L, g, t, [(5.05, 0.14, 7, 11), (5.9, 0.07, 12, 15), (6.25, 0.07, 4, 6)])
    stars(g, L, t, density=0.004, tag=STAR, lum=0.45)
    return L
