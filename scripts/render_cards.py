#!/usr/bin/env python3
"""
Render the profile cards into cards/<name>-dark.svg and cards/<name>-light.svg.

Look: a terminal UI in three colours, black, white and baby blue. Every card is a pane with
its title cut into the border, set in JetBrains Mono, with art drawn from ASCII glyphs:
greys for structure, baby blue (weak / normal / strong) for anything alive.

GitHub shows the cards through <img>: CSS animations run, scripts and external files
do not, so each card embeds a woff2 subset of just the glyphs it uses. Every element
rests on its finished frame and animates *from* somewhere else, so with reduced motion
(or STATIC=1) a card simply shows its final state.

Inputs: data/content.json (copy), data/profile.json (scripts/fetch_data.py).

    python scripts/render_cards.py
    STATIC=1 python scripts/render_cards.py      # no animation, for previews
"""
import base64
import calendar
import datetime
import io
import json
import math
import os
from collections import defaultdict
from html import escape

import numpy as np
from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")
CONTENT = json.load(open(os.path.join(ROOT, "data", "content.json")))
DATA = json.load(open(os.path.join(ROOT, "data", "profile.json")))
STATIC = bool(os.environ.get("STATIC"))

W = 880        # the README column at width="100%"
TOP = 8        # room above a pane for the title sitting in its border
GAP = 14       # space under each pane, baked into the canvas
R = 10         # pane corner radius
ADV = 0.6      # JetBrains Mono advance width, in em (every glyph we use)

FONT_FILES = {400: "JetBrainsMono-Regular.woff2", 500: "JetBrainsMono-Medium.woff2",
              700: "JetBrainsMono-Bold.woff2", 800: "JetBrainsMono-ExtraBold.woff2"}
FAMILY = "J,'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# Black, white and baby blue (#89cff0) only. accent_lo / accent_hi are the weak and strong
# ends of the blue scale *against that theme's background*, so they swap between dark and
# light. On white, baby blue itself is too faint for text (1.7:1), so light mode writes in
# a deeper blue of the same hue (#2a74a3, 5.1:1) and keeps baby blue for fills.
THEMES = {
    "dark": dict(
        pane="#000000", screen="#0a0a0a", frame="#2e2e2e",
        ink="#f5f5f5", soft="#a3a3a3", dim="#6b6b6b", faint="#222222",
        accent="#89cff0", accent_lo="#1f4e6b", accent_hi="#c6e8fa", hot="#ffffff",
        logo=["#ffffff", "#d6efff", "#89cff0", "#6bbbe6"], halo="#1f4e6b",
        heat=["#2a2a2a", "#1f4e6b", "#3d86b5", "#89cff0", "#d6efff"], peak="#ffffff",
    ),
    "light": dict(
        pane="#ffffff", screen="#f7f7f7", frame="#d4d4d4",
        ink="#0a0a0a", soft="#525252", dim="#8a8a8a", faint="#e5e5e5",
        accent="#2a74a3", accent_lo="#c6e8fa", accent_hi="#1d4f72", hot="#000000",
        logo=["#000000", "#1d4f72", "#2a74a3", "#5aa9d6"], halo="#c6e8fa",
        heat=["#d4d4d4", "#c6e8fa", "#89cff0", "#3a8dc0", "#1d4f72"], peak="#000000",
    ),
}

# shared motion; per-card keyframes are added by the scenes
BASE_CSS = (
    ".in{animation:fade .45s ease-out backwards}@keyframes fade{from{opacity:0}}"
    ".ty{animation:ty .01s linear backwards}@keyframes ty{from{fill-opacity:0}}"
    ".blink{animation:blink 1.1s steps(1,end) infinite}@keyframes blink{50%{fill-opacity:0}}"
    ".pulse{animation:pulse 2.4s ease-in-out infinite}@keyframes pulse{50%{fill-opacity:.3}}"
)
REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


# ------------------------------------------------------------------ colour + text helpers
def rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def mix(a, b, t):
    """a at t=0, b at t=1."""
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(rgb(a), rgb(b)))


def ramp(colors, t):
    t = min(max(t, 0.0), 1.0) * (len(colors) - 1)
    i = min(int(t), len(colors) - 2)
    return mix(colors[i], colors[i + 1], t - i)


def cw(size):
    return size * ADV


def tw(s, size):
    return len(s) * size * ADV


def fit(s, n):
    return s if len(s) <= n else s[:max(n - 1, 0)].rstrip(" ,·;:") + "…"


def wrap(s, n):
    lines, line = [], ""
    for word in s.split():
        if line and len(line) + 1 + len(word) > n:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + ([line] if line else [])


def esc(s):
    return escape(s, quote=True)


def month_day(d):
    return f"{calendar.month_abbr[d.month].lower()} {d.day}"


# ------------------------------------------------------------------ fonts
_ttf = {}
_subsets = {}


def ttf_bytes(weight):
    """woff2 -> plain TrueType, for Pillow (the ASCII logo is traced from a real glyph)."""
    if weight not in _ttf:
        f = TTFont(os.path.join(FONTS, FONT_FILES[weight]))
        f.flavor = None
        buf = io.BytesIO()
        f.save(buf)
        _ttf[weight] = buf.getvalue()
    return _ttf[weight]


def font_subset(weight, chars):
    key = (weight, chars)
    if key not in _subsets:
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = []      # no ligatures: "->" and "==" must stay two glyphs
        opts.hinting = False
        font = TTFont(os.path.join(FONTS, FONT_FILES[weight]), recalcTimestamp=False)   # stable bytes
        cmap, hmtx = font.getBestCmap(), font["hmtx"].metrics
        missing = [c for c in chars if ord(c) not in cmap]
        odd = [c for c in chars if ord(c) in cmap and hmtx[cmap[ord(c)]][0] != 600]
        if missing or odd:
            raise SystemExit(f"font {weight}: missing {missing!r}, not monospaced {odd!r}")
        sub = subset.Subsetter(opts)
        sub.populate(text=chars)
        sub.subset(font)
        buf = io.BytesIO()
        subset.save_font(font, buf, opts)
        _subsets[key] = base64.b64encode(buf.getvalue()).decode()
    return _subsets[key]


# ------------------------------------------------------------------ the card canvas
class Card:
    def __init__(self, name, h, mode, label):
        self.name, self.h, self.mode, self.label = name, h, mode, label
        self.th = THEMES[mode]
        self.body, self.defs, self.css = [], [], []
        self.used = defaultdict(set)

    def c(self, k):
        return self.th.get(k, k)

    def add(self, *parts):
        self.body.extend(parts)

    def text(self, x, y, s, size=13, fill="ink", w=400, anchor=None, cls=None, style=None, op=None):
        self.used[w].update(s)
        a = f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{self.c(fill)}"'
        if w != 400:
            a += f' font-weight="{w}"'
        if anchor:
            a += f' text-anchor="{anchor}"'
        if op is not None:
            a += f' opacity="{op:.2f}"'
        if cls:
            a += f' class="{cls}"'
        if style:
            a += f' style="{style}"'
        return a + f' xml:space="preserve">{esc(s)}</text>'

    def line(self, x, y, parts, size=13, w=400, cls=None, style=None, end=False):
        """One line of differently coloured runs, placed by monospace advance.
        parts: (text, colour[, weight[, extra tspan attributes]])."""
        adv = cw(size)
        cx = x - sum(len(p[0]) for p in parts) * adv if end else x
        spans = []
        for p in parts:
            s, col = p[0], p[1]
            ww = p[2] if len(p) > 2 and p[2] else w
            extra = p[3] if len(p) > 3 else ""
            lead = len(s) - len(s.lstrip(" "))
            body = s.strip(" ")
            if body:
                self.used[ww].update(body)
                fw = f' font-weight="{ww}"' if ww != w else ""
                spans.append(f'<tspan x="{cx + lead * adv:.1f}" fill="{self.c(col)}"{fw}{extra}>{esc(body)}</tspan>')
            cx += len(s) * adv
        a = f'<text y="{y:.1f}" font-size="{size}"'
        if w != 400:
            a += f' font-weight="{w}"'
        if cls:
            a += f' class="{cls}"'
        if style:
            a += f' style="{style}"'
        return a + f' xml:space="preserve">{"".join(spans)}</text>'

    def svg(self):
        faces = "".join(
            '@font-face{font-family:J;font-weight:%d;src:url(data:font/woff2;base64,%s) format("woff2")}'
            % (w, font_subset(w, "".join(sorted(set(chars) | {" "}))))
            for w, chars in sorted(self.used.items()))
        css = faces + "text{font-family:%s;font-variant-ligatures:none;font-kerning:none}" % FAMILY
        if not STATIC:
            css += BASE_CSS + "".join(self.css) + REDUCED
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{self.h}" '
                f'viewBox="0 0 {W} {self.h}" role="img" aria-label="{esc(self.label)}">'
                f"<title>{esc(self.label)}</title><style>{css}</style>{defs}{''.join(self.body)}</svg>")

    def save(self):
        path = os.path.join(OUT, f"{self.name}-{self.mode}.svg")
        with open(path, "w") as f:
            f.write(self.svg())
        return os.path.getsize(path)


# ------------------------------------------------------------------ shared pieces
def pane(card, title, accent, right=None, foot=None):
    """A rounded TUI pane over the canvas, labels cut into its border."""
    x, y, w, h, r = 0.5, TOP + 0.5, W - 1, card.h - TOP - GAP, R
    size, adv = 12, cw(12)
    top_gaps, bot_gaps, labels = [], [], []

    def put(parts, ly, gaps, at_right):
        width = sum(len(p[0]) for p in parts) * adv
        lx = x + w - 18 - width if at_right else x + 18
        gaps.append((lx - 6, lx + width + 6))
        labels.append(card.line(lx, ly + 4, parts, size))

    put([("[ ", "dim"), (title, accent, 700), (" ]", "dim")], y, top_gaps, False)
    if right:
        put(right, y, top_gaps, True)
    if foot:
        put(foot, y + h, bot_gaps, True)

    def edge(ey, gaps):
        out, cur = "", x + r
        for g0, g1 in sorted(gaps):
            out += f"M{cur:.1f},{ey}H{g0:.1f}"
            cur = g1
        return out + f"M{cur:.1f},{ey}H{x + w - r:.1f}"

    d = (edge(y, top_gaps) + edge(y + h, bot_gaps)
         + f"M{x + w - r},{y}A{r},{r} 0 0 1 {x + w},{y + r}V{y + h - r}A{r},{r} 0 0 1 {x + w - r},{y + h}"
         + f"M{x + r},{y + h}A{r},{r} 0 0 1 {x},{y + h - r}V{y + r}A{r},{r} 0 0 1 {x + r},{y}")
    # Each label also gets a tab of pane colour behind it. The README swaps artwork by the sun, not
    # by the visitor's theme, so a white card can sit on a dark GitHub page (and vice versa): the
    # tab keeps the half of the label that sticks out past the border readable. On a page of the
    # same colour it simply disappears.
    fill = card.c("pane")
    tabs = [f'<rect x="{g0:.1f}" y="0.5" width="{g1 - g0:.1f}" height="{y + 5.5:.1f}" rx="4" fill="{fill}"/>'
            for g0, g1 in top_gaps]
    tabs += [f'<rect x="{g0:.1f}" y="{y + h - 6:.1f}" width="{g1 - g0:.1f}" height="{GAP - 1.5 + 6:.1f}" rx="4" fill="{fill}"/>'
             for g0, g1 in bot_gaps]
    card.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>', *tabs,
             f'<path d="{d}" fill="none" stroke="{card.c("frame")}" stroke-width="1"/>', *labels)


def prompt_parts():
    return [(CONTENT["prompt"], "accent", 700), (":", "dim"), ("~", "ink", 700), ("$ ", "dim")]


def prompt(card, x, y, cmd, size=13, t0=0.3, per=0.04):
    """user@host:~$ then the command, typed one character at a time. Returns when typing ends."""
    pre = prompt_parts()
    card.add(card.line(x, y, pre, size))
    cx = x + sum(len(p[0]) for p in pre) * cw(size)
    card.used[400].update(cmd.replace(" ", ""))
    spans = "".join(
        f'<tspan x="{cx + i * cw(size):.1f}" class="ty" style="animation-delay:{t0 + i * per:.2f}s">{esc(ch)}</tspan>'
        for i, ch in enumerate(cmd) if ch != " ")
    card.add(f'<text y="{y:.1f}" font-size="{size}" fill="{card.c("ink")}" xml:space="preserve">{spans}</text>')
    return t0 + len(cmd) * per


def sweep_mask(card, mid, y0, y1, delay, dur, beam=True):
    """A mask that wipes in from the left, plus a thin light beam riding its edge."""
    soft = 70
    span = W + soft
    card.defs.append(
        f'<linearGradient id="{mid}g" x1="0" x2="1"><stop offset="0" stop-color="#fff"/>'
        f'<stop offset="{(span - soft) / span:.3f}" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{card.h}">'
        f'<rect class="{mid}s" x="0" y="{y0}" width="{span}" height="{y1 - y0}" fill="url(#{mid}g)"/></mask>')
    card.css.append(f".{mid}s{{animation:{mid}k {dur}s cubic-bezier(.5,0,.3,1) {delay}s backwards}}"
                    f"@keyframes {mid}k{{from{{transform:translateX(-{span}px)}}}}")
    if beam:
        hot = card.c("hot")
        card.defs.append(f'<linearGradient id="{mid}b" x1="0" x2="1"><stop offset="0" stop-color="{hot}" stop-opacity="0"/>'
                         f'<stop offset=".8" stop-color="{hot}" stop-opacity=".22"/><stop offset="1" stop-color="{hot}" stop-opacity="0"/></linearGradient>')
        # at rest the beam is parked just past the right edge, out of the viewBox
        card.add(f'<rect class="{mid}s" x="{W + 4}" y="{y0}" width="60" height="{y1 - y0}" fill="url(#{mid}b)"/>')


def kf_window(name, a, b=96.0):
    """Keyframes: hidden until a%, shown until b%, hidden again (for looping scripted scenes)."""
    return (f"@keyframes {name}{{0%,{a:.1f}%{{fill-opacity:0}}{a + 0.2:.1f}%,{b:.1f}%{{fill-opacity:1}}"
            f"{min(b + 1.5, 100):.1f}%,100%{{fill-opacity:0}}}}")


# ------------------------------------------------------------------ stats from the calendar
def stats():
    days = [(datetime.date.fromisoformat(d), c, lv) for d, c, lv in DATA["days"]]
    today = days[-1][0]
    best = max(days, key=lambda d: d[1])
    longest = run = 0
    for _, c, _ in days:
        run = run + 1 if c else 0
        longest = max(longest, run)
    # heat levels from this profile's own spread (quartiles of the active days), not GitHub's
    # max-relative quartiles, where one 250-commit day flattens everything else into level 1
    nz = sorted(c for _, c, _ in days if c)
    cuts = [nz[int(len(nz) * q)] for q in (0.5, 0.75, 0.9)] if nz else [1, 1, 1]
    days = [(d, c, 0 if not c else 1 + sum(c > k for k in cuts)) for d, c, _ in days]
    months = defaultdict(int)
    for d, c, _ in days:
        months[(d.year, d.month)] += c
    keys, y, m = [], today.year, today.month
    for _ in range(12):
        keys.append((y, m))
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    keys.reverse()
    return dict(days=days, today=today, total=DATA["total"], best=best, longest=longest,
                months=[(k, months.get(k, 0)) for k in keys], active=sum(1 for d in days if d[1]))


# ------------------------------------------------------------------ hero: a neofetch for the profile
def logo_cells(text, cols, rows, adv, lh, th, seed=11):
    """Trace the name from the real ExtraBold glyphs into a grid of coloured characters."""
    S = 4
    wp, hp = round(cols * adv * S), round(rows * lh * S)
    img = Image.new("L", (wp, hp), 0)
    draw = ImageDraw.Draw(img)
    fs = int(min(0.82 * hp / 0.73, 0.96 * wp / (len(text) * ADV)))
    font = ImageFont.truetype(io.BytesIO(ttf_bytes(800)), fs)
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    draw.text(((wp - (r - l)) / 2 - l, (hp - (b - t)) / 2 - t), text, font=font, fill=255)

    def cells(im):
        return np.asarray(im.resize((cols, rows), Image.BOX), dtype=float) / 255

    cov = cells(img)
    soft = cells(img.filter(ImageFilter.GaussianBlur(S * 3)))
    halo = cells(img.filter(ImageFilter.GaussianBlur(S * 10)))
    gy, gx = np.gradient(soft)
    gx, gy = gx / adv, gy / lh                                 # per pixel, so slopes match the screen
    rnd = np.random.default_rng(seed).random((rows, cols))
    lit = np.flatnonzero(cov.max(axis=0) > 0.3)
    c0, c1 = lit.min(), lit.max()
    pool = "+*#%@"
    out = {}
    for r_ in range(rows):
        for c in range(cols):
            v = cov[r_, c]
            tx = round(min(max((c - c0) / (c1 - c0), 0), 1) * 14) / 14
            base = ramp(th["logo"], tx)
            if v >= 0.55:
                n = 0.5 + 0.5 * math.sin(c * 0.42 + r_ * 1.25) * math.cos(c * 0.11 - r_ * 0.63)
                heat = min(0.999, 0.5 * v + 0.5 * n)
                ch = pool[int(heat * len(pool))]
                out[(r_, c)] = (ch, mix(base, th["hot"], 0.28 if heat > 0.82 else 0.0), None)
            elif v >= 0.13:
                ang = (math.degrees(math.atan2(gy[r_, c], gx[r_, c])) + 90) % 180   # tangent of the outline
                ch = "-" if ang < 22.5 or ang >= 157.5 else "\\" if ang < 67.5 else "|" if ang < 112.5 else "/"
                out[(r_, c)] = (ch, mix(base, th["hot"], 0.12), None)
            elif halo[r_, c] > 0.06 and rnd[r_, c] < halo[r_, c] * 1.5:
                out[(r_, c)] = (":" if rnd[r_, c] < halo[r_, c] * 0.3 else ".", th["halo"],
                                0.8 if halo[r_, c] > 0.2 else 0.5)
    return out


def card_hero(mode, st):
    card = Card("hero", 362, mode, "yolooo332: the name YOLOOO drawn in coloured ASCII, a list of current "
                "projects and a short neofetch-style summary")
    th = card.th
    when = "day" if mode == "light" else "night"            # README swaps these at sunrise / sunset
    pane(card, "README.md", "accent", right=[("[ ", "dim"), ("tty1 · ", "soft"), (when, "accent"), (" ]", "dim")])
    t = prompt(card, 28, 44, "./hello --fetch")

    # the logo, wiped in by a scan beam, a few glyphs flickering afterwards
    size, lh, cols, rows, x0, y0 = 11, 11, 88, 13, 28, 56
    adv = cw(size)
    cells = logo_cells(CONTENT["logo"], cols, rows, adv, lh, th)
    rng = np.random.default_rng(5)
    solid = [k for k, v in cells.items() if v[1] != th["halo"]]
    flick = {solid[i] for i in rng.choice(len(solid), size=min(42, len(solid)), replace=False)}
    sweep_mask(card, "lm", y0 - 4, y0 + rows * lh + 6, t + 0.05, 1.5)
    rows_svg = []
    for r_ in range(rows):
        spans, c = [], 0
        while c < cols:
            k = (r_, c)
            if k not in cells:
                c += 1
                continue
            ch, col, op = cells[k]
            if k in flick:
                dur, delay = rng.uniform(2.6, 5.5), rng.uniform(-5, 0)
                spans.append(f'<tspan x="{x0 + c * adv:.1f}" fill="{col}" class="fl" '
                             f'style="animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s">{esc(ch)}</tspan>')
                card.used[400].add(ch)
                c += 1
                continue
            run = ch
            c2 = c + 1
            while c2 < cols and (r_, c2) in cells and (r_, c2) not in flick and cells[(r_, c2)][1:] == (col, op):
                run += cells[(r_, c2)][0]
                c2 += 1
            card.used[400].update(run)
            o = f' fill-opacity="{op}"' if op else ""
            spans.append(f'<tspan x="{x0 + c * adv:.1f}" fill="{col}"{o}>{esc(run)}</tspan>')
            c = c2
        if spans:
            rows_svg.append(f'<text y="{y0 + r_ * lh + 9:.1f}" font-size="{size}" xml:space="preserve">{"".join(spans)}</text>')
    card.add(f'<g mask="url(#lm)">{"".join(rows_svg)}</g>')
    card.css.append(".fl{animation:fl 4s steps(1,end) infinite}"
                    "@keyframes fl{0%,100%{fill-opacity:1}46%{fill-opacity:.15}52%{fill-opacity:1}78%{fill-opacity:.4}82%{fill-opacity:1}}")

    # right column: what's running
    rx0, rx1 = 646, 852
    card.add(card.line(rx0, 80, [("~/projects", "dim")], 12, cls="in", style=f"animation-delay:{t + 0.6:.2f}s"))
    card.add(f'<line x1="{rx0}" x2="{rx1}" y1="90.5" y2="90.5" stroke="{card.c("faint")}" class="in" '
             f'style="animation-delay:{t + 0.6:.2f}s"/>')
    for i, p in enumerate(CONTENT["projects"]):
        state, word = p["status"]
        dot = ("○", "dim") if state == "queued" else ("●", p.get("accent", "accent"))
        y = 112 + i * 24
        d = t + 0.7 + i * 0.15
        pulse = ' class="pulse"' if state == "live" else ""
        card.add(card.line(rx0, y, [(dot[0] + " ", dot[1], None, pulse), (p["short"], "ink")], 12.5,
                           cls="in", style=f"animation-delay:{d:.2f}s"))
        card.add(card.line(rx1, y, [(word, "soft" if state != "queued" else "dim")], 12, end=True, cls="in",
                           style=f"animation-delay:{d:.2f}s"))

    # neofetch block
    t2 = t + 1.2
    card.add(f'<line x1="28" x2="852" y1="216.5" y2="216.5" stroke="{card.c("faint")}" class="in" '
             f'style="animation-delay:{t2:.2f}s"/>')
    info = [(k, v.replace("{total}", f"{st['total']:,}")) for k, v in CONTENT["info"]]
    half = (len(info) + 1) // 2
    for i, (k, v) in enumerate(info):
        col, row = divmod(i, half)
        x = 28 + col * 424
        y = 242 + row * 21
        card.add(card.line(x, y, [(k.ljust(8), "accent", 700), (fit(v, 45), "ink")], 13, cls="in",
                           style=f"animation-delay:{t2 + 0.1 + row * 0.09 + col * 0.04:.2f}s"))

    # final prompt with a live cursor, palette swatches on the right
    t3 = t2 + 0.6
    y = 330
    pre = prompt_parts()
    card.add(card.line(28, y, pre, 13, cls="in", style=f"animation-delay:{t3:.2f}s"))
    cx = 28 + sum(len(p[0]) for p in pre) * cw(13)
    card.add(card.text(cx, y, "█", 13, "ink", cls="cur", style=f"animation-delay:{t3:.2f}s,{t3:.2f}s"))
    card.css.append(".cur{animation:fade .01s backwards,blink 1.1s steps(1,end) infinite}")
    sw = ["faint", "frame", "dim", "soft", "ink", "accent_lo", "accent", "accent_hi"]
    sx = 852 - len(sw) * 3 * cw(13)
    for i, k in enumerate(sw):
        card.add(card.text(sx + i * 3 * cw(13), y, "███", 13, k, cls="in", style=f"animation-delay:{t3 + 0.05 * i:.2f}s"))
    return card


# ------------------------------------------------------------------ contributions as ASCII heat
def card_activity(mode, st):
    card = Card("activity", 262, mode, f"{st['total']:,} contributions in the last 12 months, drawn as a grid "
                "of ASCII characters, one per day")
    th = card.th
    right = [("[ ", "dim"), ("last 12 months", "soft"), (" ]", "dim")]
    foot = [("[ ", "dim"), ("updated " + DATA["fetched"][:10], "dim"), (" ]", "dim")]
    pane(card, "activity", "accent", right=right, foot=foot)
    t = prompt(card, 28, 44, 'git log --since="1 year ago" | heat', t0=0.2, per=0.03)

    days = st["days"]
    lead = (days[0][0].weekday() + 1) % 7                 # GitHub weeks start on Sunday
    ncol = (lead + len(days) + 6) // 7
    gx0, gx1, gy0, rh = 70, 852, 76, 15
    cwid = (gx1 - gx0) / ncol
    glyphs = "·-+*#"
    peak = st["best"][0]

    def pos(i):
        k = lead + i
        return gx0 + (k // 7 + 0.5) * cwid, gy0 + (k % 7) * rh

    for r_, name in ((1, "mon"), (3, "wed"), (5, "fri")):
        card.add(card.text(28, gy0 + r_ * rh, name, 11, "dim"))

    sweep_mask(card, "am", gy0 - 14, gy0 + 7 * rh, t + 0.05, 1.7)
    rows = defaultdict(list)
    today_svg = ""
    for i, (d, c, lv) in enumerate(days):
        x, y = pos(i)
        ch, col = (("@", th["peak"]) if d == peak and c else (glyphs[lv], th["heat"][lv]))
        if d == st["today"]:
            card.used[400].add(ch)
            today_svg = (f'<text x="{x:.1f}" y="{y:.1f}" font-size="13" fill="{col}" text-anchor="middle" '
                         f'class="pulse">{esc(ch)}</text>')
            continue
        rows[y].append((x, ch, col))
    out = []
    for y, cells in sorted(rows.items()):
        spans = "".join(f'<tspan x="{x:.1f}" fill="{col}">{esc(ch)}</tspan>' for x, ch, col in cells)
        card.used[400].update(ch for _, ch, _ in cells)
        out.append(f'<text y="{y:.1f}" font-size="13" text-anchor="middle" xml:space="preserve">{spans}</text>')
    card.add(f'<g mask="url(#am)">{"".join(out)}{today_svg}</g>')

    # month labels where a month's first week starts
    last = -9
    for k in range(ncol):
        i = k * 7 - lead
        if 0 <= i < len(days) and days[i][0].day <= 7 and k - last >= 3:
            card.add(card.text(gx0 + k * cwid + 1, gy0 + 7 * rh + 10, calendar.month_abbr[days[i][0].month].lower(),
                               11, "dim"))
            last = k

    # one line of numbers, then a 12-month sparkline
    bd, bc, _ = st["best"]
    parts = [(f"{st['total']:,}", "ink", 700), (" total", "soft"), ("  │  ", "faint"),
             ("best day ", "dim"), (f"{month_day(bd)} · {bc}", "ink"), ("  │  ", "faint"),
             ("longest streak ", "dim"), (f"{st['longest']}d", "ink"), ("  │  ", "faint"),
             (f"{st['active']}", "ink"), (" active days", "dim")]
    y = 228
    card.add(card.line(28, y, parts, 12.5, cls="in", style=f"animation-delay:{t + 1.4:.2f}s"))
    top = max(v for _, v in st["months"]) or 1
    bars = "▁▂▃▄▅▆▇█"
    spark = []
    for (yy, mm), v in st["months"]:
        lvl = 0 if not v else 1 + min(3, int(4 * v / top))
        spark.append((bars[min(7, int(round(7 * v / top)))], th["heat"][lvl] if v else th["faint"]))
    sx = 852 - len(spark) * cw(12.5)
    card.add(card.line(sx - tw("12mo ", 12.5), y, [("12mo ", "dim")] + spark, 12.5, cls="in",
                       style=f"animation-delay:{t + 1.5:.2f}s"))
    return card


# ------------------------------------------------------------------ project scenes
def screen(card, x, y, w, h):
    card.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{card.c("screen")}" '
             f'stroke="{card.c("faint")}"/>')


def scene_ecg(card, x, y, w, h, acc, p):
    """A patient monitor: an ECG trace in glyphs, swept by a bright head that erases ahead of itself."""
    size, lh = 11, 12
    adv = cw(size)
    card.add(card.text(x + 12, y + 18, "ecg · lead II", 10.5, "dim"),
             card.text(x + w - 12, y + 18, "25 mm/s", 10.5, "dim", anchor="end"))
    cols, rows = int((w - 20) / adv), int((h - 36) / lh)
    ox, oy = x + (w - cols * adv) / 2, y + 28
    for r_ in range(1, rows, 3):                                    # monitor grid
        card.add(card.text(ox, oy + r_ * lh + 9, "".join("·" if c % 4 == 0 else " " for c in range(cols)),
                           size, "faint"))

    def g(u, m, s):
        return math.exp(-((u - m) / s) ** 2)

    def v(u):
        u %= 1
        return (0.12 * g(u, .16, .035) - 0.08 * g(u, .355, .012) + g(u, .39, .013)
                - 0.17 * g(u, .425, .014) + 0.24 * g(u, .64, .05))

    beats, base = 2.6, rows - 2.6
    amp = base - 0.3
    dur = 3.4
    hot, col = card.c("hot"), card.c(acc)
    card.css.append(f".ew{{animation:ew {dur}s linear infinite}}"
                    f"@keyframes ew{{0%{{opacity:1;fill:{hot}}}6%{{fill:{col}}}78%{{opacity:.3}}90%,100%{{opacity:0}}}}")
    for c in range(cols):
        ys = np.array([base - amp * v(u) for u in np.linspace(c / cols, (c + 1) / cols, 14) * beats])
        r0, r1 = int(round(ys.min())), int(round(ys.max()))
        peaked = ys.min() < min(ys[0], ys[-1]) - 0.6 or ys.max() > max(ys[0], ys[-1]) + 0.6
        if r0 == r1:
            chars = {r0: "─"}
        elif r1 - r0 == 1 and not peaked:
            ch = "/" if ys[-1] < ys[0] else "\\"
            chars = {r0: ch, r1: ch}
        else:
            chars = {rr: "│" for rr in range(r0, r1 + 1)}
        texts = "".join(card.text(ox + c * adv, oy + rr * lh + 9, ch, size, col) for rr, ch in chars.items())
        card.add(f'<g class="ew" style="animation-delay:{-(1 - c / cols) * dur:.2f}s">{texts}</g>')


def scene_spectrogram(card, x, y, w, h, acc, p):
    """A spectrogram in shade blocks: a plane's falling Doppler tone and its harmonic over broadband
    noise, the 50 Hz mains hum along the bottom, read by a looping playhead."""
    lh = 12
    size = lh / 1.32                       # JetBrains Mono's block glyphs are 1.32 em tall: rows tile exactly
    adv = cw(size)
    card.add(card.text(x + 12, y + 18, "spectrogram", 10.5, "dim"),
             card.text(x + w - 12, y + 18, "doppler · enf", 10.5, "dim", anchor="end"))
    cols, rows = int((w - 20) / adv), int((h - 34) / lh)
    ox, oy = x + (w - cols * adv) / 2, y + 26
    rnd = np.random.default_rng(3).random((rows, cols))
    bottom = rows - 1
    k = (bottom - 1.6) / (2 * 1.3)
    dur = 4.8
    card.css.append(f".sp{{animation:sp {dur}s linear infinite}}"
                    f"@keyframes sp{{0%{{opacity:1}}55%{{opacity:.9}}80%,100%{{opacity:.16}}}}"
                    f".ph{{animation:ph {dur}s linear infinite}}"
                    f"@keyframes ph{{from{{transform:translateX(0)}}to{{transform:translateX({cols * adv:.1f}px)}}}}")
    cmap = [card.c("accent_lo"), card.c(acc), card.c("accent_hi"), card.c("hot")]
    for c in range(cols):
        tt = (c + 0.5) / cols
        f = 1 - 0.3 * math.tanh((tt - 0.47) / 0.12)               # the tone drops as the plane passes
        loud = 0.4 + 0.6 * math.exp(-((tt - 0.47) / 0.22) ** 2)   # loudest at closest approach
        spans = []
        for r_ in range(bottom):
            e = 0.0
            for hmul, gain in ((1, 1.0), (2, 0.85)):
                d = r_ - (bottom - 0.6 - hmul * k * f)
                e = max(e, gain * loud * math.exp(-(d / 0.45) ** 2))
            if e < 0.1:                                             # broadband rumble, heavier low down
                if rnd[r_, c] < 0.08 + 0.3 * r_ / rows:
                    spans.append((r_, "░", cmap[0], 0.45))
                continue
            ch = "░" if e < 0.3 else "▒" if e < 0.55 else "▓" if e < 0.8 else "█"
            spans.append((r_, ch, ramp(cmap, 0.15 + 0.85 * e), None))
        spans.append((bottom, "░", card.c("soft"), 0.9))           # the mains hum
        card.used[400].update(s[1] for s in spans)
        body = "".join(
            f'<tspan x="{ox + c * adv:.2f}" y="{oy + r_ * lh + 1.02 * size:.2f}" fill="{col}"'
            + (f' fill-opacity="{op}"' if op else "") + f">{ch}</tspan>"
            for r_, ch, col, op in spans)
        card.add(f'<text class="sp" font-size="{size:.3f}" style="animation-delay:{-(1 - c / cols) * dur:.2f}s">'
                 f"{body}</text>")
    card.add(f'<rect class="ph" x="{ox:.1f}" y="{oy - 1}" width="2" height="{rows * lh + 2}" '
             f'fill="{card.c("hot")}" opacity=".8"/>')


def scene_cargo(card, x, y, w, h, acc, p):
    """Placeholder: a build that runs, stalls, and says when the real work starts."""
    size, lh = 11.5, 18
    adv = cw(size)
    tx, ty = x + 14, y + 26
    dur = 9.0
    nbar, filled = 18, 8
    lines = [
        (2, [("$ ", "dim"), ("cargo build --release", "ink")]),
        (12, [("   Compiling ", "accent", 700), ("framework v0.1.0", "ink")]),
        (18, None),                                                    # the progress bar
        (60, [("$ ", "dim"), ("./fxserver +exec server.cfg", "ink")]),
        (68, [("  > ", acc), (p.get("eta", "soon"), acc)]),
    ]
    for i, (at, parts) in enumerate(lines):
        yy = ty + i * lh
        name = f"cl{i}"
        card.css.append(kf_window(name, at))
        style = f"animation:{name} {dur}s linear infinite"
        if parts is None:
            pre = [("    Building ", "accent", 700), ("[", "dim")]
            cx = tx + sum(len(q[0]) for q in pre) * adv
            track = "░" * nbar                                     # the empty track, shown with its line
            fill = []
            for b in range(filled):                                # then the blocks fill in, and stall
                bn = f"cb{b}"
                card.css.append(kf_window(bn, at + 3 + b * 4.2))
                fill.append(f'<tspan x="{cx + b * adv:.1f}" style="animation:{bn} {dur}s linear infinite">█</tspan>')
            card.used[400].update("█░")
            card.add(card.line(tx, yy, pre, size, style=style))
            card.add(f'<text x="{cx:.1f}" y="{yy:.1f}" font-size="{size}" fill="{card.c("faint")}" '
                     f'style="{style}" xml:space="preserve">{track}</text>')
            card.add(f'<text y="{yy:.1f}" font-size="{size}" fill="{card.c(acc)}" xml:space="preserve">{"".join(fill)}</text>')
            card.add(card.text(cx + nbar * adv, yy, "]", size, "dim", style=style))
            continue
        if i == len(lines) - 1:                                    # blinking cursor on the last line
            end = tx + sum(len(q[0]) for q in parts) * adv + adv * 0.5
            card.add(f'<g style="{style}">'
                     + card.line(tx, yy, parts, size)
                     + card.text(end, yy, "█", size, acc, cls="blink") + "</g>")
            card.css[-1] = card.css[-1].replace("fill-opacity", "opacity")   # a <g>: animate opacity
            continue
        card.add(card.line(tx, yy, parts, size, style=style))


SCENES = {"ecg": scene_ecg, "spectrogram": scene_spectrogram, "cargo": scene_cargo}


def project_height():
    lines = max(len(wrap(p["pitch"], 61)) for p in CONTENT["projects"])
    return round(104 + (lines - 1) * 20 + 36 + 24 + GAP)


def card_project(mode, p, h):
    state, word = p["status"]
    acc = p.get("accent", "accent")
    card = Card(f"project-{p['id']}", h, mode, f"{p['name']} ({word}): {p['pitch']}")
    dot = "○" if state == "queued" else "●"
    right = [("[ ", "dim"), (dot + " ", acc, None, ' class="pulse"' if state == "live" else ""), (word, acc), (" ]", "dim")]
    foot = None
    if p.get("url"):
        foot = [("[ ", "dim"), ("↗ " + p["url"].split("github.com/")[-1], "soft"), (" ]", "dim")]
    pane(card, f"~/projects/{p['id']}", acc, right=right, foot=foot)

    sx, sy, sw = 22, TOP + 22, 322
    sh = h - GAP - sy - 14
    screen(card, sx, sy, sw, sh)
    SCENES[p["scene"]](card, sx, sy, sw, sh, acc, p)

    x = 372
    card.add(card.text(x, 54, p["name"], 22, "ink", w=800))
    card.add(card.text(x, 76, p["tag"], 12, "dim"))
    lines = wrap(p["pitch"], 61)
    for i, ln in enumerate(lines):
        card.add(card.text(x, 106 + i * 20, ln, 13, "ink", op=0.92))
    cy = 106 + (len(lines) - 1) * 20 + 36
    cx = x
    for s in p["stack"]:
        wdt = tw(s, 12) + 16
        card.add(f'<rect x="{cx:.1f}" y="{cy - 15.5:.1f}" width="{wdt:.1f}" height="22" rx="4" '
                 f'fill="{mix(card.c(acc), card.c("pane"), 0.9)}" stroke="{mix(card.c(acc), card.c("pane"), 0.55)}"/>',
                 card.text(cx + 8, cy, s, 12, acc))
        cx += wdt + 8
    return card


def card_ls(mode):
    projects = CONTENT["projects"]
    card = Card("ls", 52, mode, "ls ~/projects")
    # a slim pane of its own: by day the white cards can sit on a dark GitHub page and vice versa
    card.add(f'<rect x="0.5" y="4.5" width="{W - 1}" height="34" rx="8" fill="{card.c("pane")}" '
             f'stroke="{card.c("frame")}"/>')
    t = prompt(card, 18, 26, "ls ~/projects", t0=0.1)
    counts = defaultdict(int)
    for p in projects:
        counts[p["status"][1]] += 1
    parts = [(f"{len(projects)} entries", "soft")]
    for word, n in counts.items():
        parts += [("  ·  ", "faint"), (f"{n} {word}", "dim")]
    card.add(card.line(W - 18, 26, parts, 12, end=True, cls="in", style=f"animation-delay:{t:.2f}s"))
    return card


# ------------------------------------------------------------------ the log, as a git graph
def card_log(mode):
    log = CONTENT["log"]
    h = 72 + len(log) * 24 + 8 + GAP
    card = Card("log", h, mode, "git log: projects, newest first")
    pane(card, "git log", "accent", right=[("[ ", "dim"), ("newest first", "soft"), (" ]", "dim")])
    t = prompt(card, 28, 44, "git log --graph --oneline", t0=0.2, per=0.03)
    hues = {"HEAD": "accent", "queued": "accent"}                   # only what is live or next gets the accent
    gx = 28
    ys = [74 + i * 24 for i in range(len(log))]
    for i in range(len(log) - 1):                               # rails between the nodes
        dash = ' stroke-dasharray="2 3"' if log[i][0] == "next" else ""
        card.add(f'<line x1="{gx + 3.9}" x2="{gx + 3.9}" y1="{ys[i] + 5}" y2="{ys[i + 1] - 12}" '
                 f'stroke="{card.c("faint")}" stroke-width="1.2"{dash} class="in" style="animation-delay:{t + 0.1 + i * 0.07:.2f}s"/>')
    for i, (when, name, desc, tag) in enumerate(log):
        y = ys[i]
        d = t + 0.1 + i * 0.07
        node_col = hues.get(tag, "soft")
        node = "o" if when == "next" else "*"
        extra = ' class="pulse"' if tag == "HEAD" else ""
        tag_parts = [("(", "dim"), (tag, hues.get(tag, "soft"), 700), (")", "dim")] if tag else []
        tag_w = sum(len(q[0]) for q in tag_parts) * cw(13)
        room = int((852 - 290 - tag_w - 14) / cw(13))
        card.add(card.line(gx, y, [(node, node_col, 700, extra)], 13, cls="in", style=f"animation-delay:{d:.2f}s"))
        card.add(card.line(50, y, [(when, "dim")], 13, cls="in", style=f"animation-delay:{d:.2f}s"))
        card.add(card.line(118, y, [(fit(name, 20), "ink", 700)], 13, cls="in", style=f"animation-delay:{d:.2f}s"))
        card.add(card.line(290, y, [(fit(desc, room), "soft")], 13, cls="in", style=f"animation-delay:{d:.2f}s"))
        if tag_parts:
            card.add(card.line(852, y, tag_parts, 13, end=True, cls="in", style=f"animation-delay:{d:.2f}s"))
    return card


# ------------------------------------------------------------------ main
def main():
    os.makedirs(OUT, exist_ok=True)
    st = stats()
    ph = project_height()
    sizes = {}
    for mode in THEMES:
        cards = [card_hero(mode, st), card_ls(mode), card_activity(mode, st), card_log(mode)]
        cards += [card_project(mode, p, ph) for p in CONTENT["projects"]]
        for c in cards:
            sizes[f"{c.name}-{mode}"] = c.save()
    for k, v in sorted(sizes.items()):
        print(f"  cards/{k}.svg  {v / 1024:.1f} KB")


if __name__ == "__main__":
    main()
