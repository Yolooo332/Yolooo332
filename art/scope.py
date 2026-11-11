# scope: a phosphor oscilloscope drawing a closed-loop step response.
# Two tuning passes per loop: the first rings, the second settles.

import numpy as np
from asciianim import *

#          dark       mid        phosphor   hot        dim        pink       amber      grid
PALETTE = ["#0f3d2e", "#1f9d63", "#39ff88", "#e2fff0", "#6e7681", "#ff5fa2", "#ffb347", "#2b4a3c"]
DARK, MID, PHOS, HOT, DIM, PINK, AMBER, GRID = range(8)

LOOP = 8.0
CONFIG = dict(width=960, height=264, cell=(7, 12), font_px=12, fps=12, duration=LOOP,
              palette=PALETTE, trail=0.3, bloom=[(4, 4, 0.75), (8, 18, 0.5)])

#        start  sweep  zeta  wn   label
PASSES = [(0.2, 3.0, 0.16, 1.0, "tune #1   Kp 2.40   Ki 0.80"),
          (4.2, 3.0, 0.72, 1.0, "tune #2   Kp 0.90   Ki 0.35")]
TSPAN = 16.0                     # seconds of plant time across the screen
YMIN, YMAX = -0.12, 1.75


def step_response(tau, z, wn):
    wd = wn * np.sqrt(1 - z * z)
    phi = np.arccos(z)
    return 1 - np.exp(-z * wn * tau) / np.sqrt(1 - z * z) * np.sin(wd * tau + phi)


def setup(g):
    top, bot = 3, g.rows - 4
    left, right = 4, g.cols - 5
    g.cache.update(top=top, bot=bot, left=left, right=right)


def yrow(c, y):
    return c["bot"] - (y - YMIN) / (YMAX - YMIN) * (c["bot"] - c["top"])


def frame(t, g):
    c = g.cache
    L = g.layer()
    top, bot, left, right = c["top"], c["bot"], c["left"], c["right"]
    R, C = g.R, g.C

    # graticule: border, dotted divisions, centre ticks
    inside = (R > top) & (R < bot) & (C > left) & (C < right)
    L.put(inside & ((C - left) % 12 == 0) & ((R - top) % 3 == 0), ch("·"), 0.5, GRID)
    L.put(((R == top) | (R == bot)) & (C >= left) & (C <= right), ch("-"), 0.35, GRID)
    L.put(((C == left) | (C == right)) & (R >= top) & (R <= bot), ch("|"), 0.35, GRID)
    for rr in (top, bot):
        L.text(rr, left, "+", 0.5, GRID)
        L.text(rr, right, "+", 0.5, GRID)

    # setpoint r(t) = 1
    rs = int(round(yrow(c, 1.0)))
    L.put((R == rs) & inside & (C % 3 != 0), ch("-"), 0.35, PINK)
    L.text(rs, right + 1, "r", 0.6, PINK)
    r0 = int(round(yrow(c, 0.0)))
    L.text(r0, left - 3, "0", 0.4, DIM)
    L.text(rs, left - 3, "1", 0.4, DIM)

    cols = np.arange(left + 1, right)
    tau = (cols - left - 1) / (right - left - 2) * TSPAN
    active = None
    for start, dur, z, wn, label in PASSES:
        k = (t - start) / dur                                # 0..1 while the beam sweeps
        if t < start - 0.1 or t > start + dur + 1.0:
            continue
        fade = 1 - ramp(t, start + dur + 0.25, start + dur + 0.95)
        head = left + 1 + np.clip(k, 0, 1) * (right - left - 2)
        y = step_response(tau, z, wn)
        fr = yrow(c, y)
        rows_i = np.floor(fr).astype(int)
        frac = fr - rows_i
        drow = np.gradient(fr)
        glyph = np.where(np.abs(drow) < 0.35, np.where(frac > 0.5, ch("_"), ch("-")),
                         np.where(drow < 0, ch("/"), ch("\\")))
        behind = head - cols
        lum = np.where(behind >= 0, 0.8 + 0.5 * np.exp(-behind / 6), 0.0) * fade
        tag = np.where(behind < 2, HOT, np.where(behind < 30, PHOS, MID))
        for i, cc in enumerate(cols):
            if lum[i] <= 0:
                continue
            r1 = rows_i[i]
            if i + 1 < len(cols):                            # steep: fill the vertical run
                r2 = rows_i[i + 1]
                lo, hi = sorted((r1, r2))
                for rr in range(lo + 1, hi):
                    if top < rr < bot:
                        L.text(rr, cc, "|", lum[i] * 0.9, tag[i])
            if top < r1 < bot:
                L.text(r1, cc, CHARS[glyph[i]], lum[i], tag[i])
        if 0 <= k <= 1:
            hc = int(head)
            hr = rows_i[min(max(hc - left - 1, 0), len(cols) - 1)]
            L.put((C == hc) & inside & (L.char == 0), ch("│"), 0.25, MID)
            if top < hr < bot:
                L.text(hr, hc, "●", 1.4, HOT)

        # overshoot marker once the beam has passed the peak
        peak = int(np.argmax(y))
        if head > cols[peak] + 1:
            ov = (y[peak] - 1) * 100
            pr = rows_i[peak] - 1
            mark = f"^ {ov:02.0f}%" if ov > 1 else "settled"
            L.text(pr, int(cols[peak]) - 1, mark, 0.9 * fade, AMBER if ov > 15 else PHOS)
        active = (label, z, fade, k)

    # read-outs
    L.text(1, left, "CH1  step response   G(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)", 0.55, MID)
    if active:
        label, z, fade, k = active
        L.text(1, right - 34, label, 0.8 * fade, PHOS)
        verdict = "rings  x" if z < 0.4 else "stable ok"
        if k > 0.55:
            L.text(bot + 1, right - 9, verdict, 0.9 * fade, PINK if z < 0.4 else PHOS)
    msg = "// currently: getting sharper at C"
    e = L.text(bot + 2, left, msg, 0.6, DIM)
    if int(t * 2.4) % 2 == 0:
        L.text(bot + 2, e + 1, "█", 0.7, PINK)
    return L
