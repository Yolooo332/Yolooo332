#!/usr/bin/env python3
"""asciianim: a field-based animated ASCII renderer.

Every cell of a character grid asks one question per frame ("how much
energy is here?"). The answer picks a glyph from a density-ranked pool, a
palette colour and a brightness. Frames are rasterised from a glyph atlas,
faded into a trail buffer and bloomed, then exported.

Only numpy and Pillow are required. ffmpeg (optional) gives much better GIFs
and enables MP4 output.

    python asciianim.py SCENE.py --gif out.gif
    python asciianim.py SCENE.py --sheet sheet.png --n 8     # contact sheet of stills
    python asciianim.py SCENE.py --still 3.2 --png frame.png
    python asciianim.py SCENE.py --term                      # play in the terminal
    python asciianim.py SCENE.py --mp4 out.mp4

A scene is a Python file that defines:

    CONFIG = dict(width=960, height=320, ...)     # see DEFAULTS below
    def setup(g): ...                             # optional, precompute into g.cache
    def frame(t, g) -> Layer                      # required
    def hud(t, g) -> list[(text, (x, y), rgb)]    # optional pixel-space overlay text

Scenes import helpers with `from asciianim import *`.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

__all__ = [
    "TAU", "CHARS", "AT", "ch", "POOLS", "Grid", "Layer",
    "smooth", "ramp", "window", "gauss", "ripple", "noise", "fract", "hexrgb",
    "shade", "tangent", "levels", "text_field", "blur_field", "find_font",
    "stars", "glitch_rows", "polyline_splat",
    "box", "wire", "packets",
]

TAU = 2 * np.pi

# ── glyphs ──────────────────────────────────────────────────────────────────
# All printable ASCII plus a few box/shade glyphs, so scenes can place literal
# text anywhere in the grid. Index 0 is always the space (= empty cell).
CHARS = "".join(chr(i) for i in range(32, 127)) + "·•●○◦░▒▓█─│╱╲═▲▼◆►◄┌┐└┘├┤┬┴┼╭╮╰╯━┃"
AT = {c: i for i, c in enumerate(CHARS)}


def ch(c: str) -> int:
    """Glyph index of a single character."""
    return AT[c]


# Density pools, dark -> bright. Glyphs inside one pool have similar ink
# coverage, so swapping between them reads as texture, not as flicker.
POOLS = [
    ".,'`:",
    ";!il1|+~",
    "rtfjcvxz=*<>",
    "aeoun0{}[]%",
    "08B$#&@QM",
]


def _fill_table(pools):
    width = 12
    return np.array([[AT[p[k % len(p)]] for k in range(width)] for p in pools])


_FILL_CACHE: dict = {}


# ── easing / signal helpers ─────────────────────────────────────────────────
def smooth(x):
    """Smoothstep on [0, 1], clamped."""
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def ramp(t, a, b):
    """0 before a, 1 after b, smooth in between. The workhorse for timelines."""
    return smooth((t - a) / (b - a))


def window(t, a, b, fade=0.4):
    """1 inside [a, b], soft edges of length `fade`."""
    return ramp(t, a - fade, a) * (1 - ramp(t, b, b + fade))


def gauss(x, w=1.0):
    return np.exp(-(np.asarray(x) / w) ** 2)


def fract(x):
    return x - np.floor(x)


def ripple(a, b, t):
    """Three nested sines: organic, slow, cheap. Range about [-1, 1]."""
    return (np.sin(a + 0.9 * np.sin(b + 1.3 * t)) * 0.5
            + np.sin(2.3 * a - b + 0.7 * t) * 0.3
            + np.sin(4.1 * a + 1.7 * b - 1.1 * t) * 0.2)


def noise(x, y, t=0.0, octaves=4, seed=0.0):
    """Sum of rotated sine waves: a smooth fbm-like field in about [-1, 1]."""
    out = np.zeros(np.broadcast(x, y).shape, dtype=np.float64)
    amp, freq, norm = 1.0, 1.0, 0.0
    for k in range(octaves):
        a = 1.7 * k + seed
        u = x * math.cos(a) + y * math.sin(a)
        v = -x * math.sin(a) + y * math.cos(a)
        out += amp * np.sin(freq * u * 6.1 + 1.3 * np.sin(freq * v * 4.3 + t * (0.6 + 0.2 * k)) + t * 0.4 + k)
        norm += amp
        amp *= 0.55
        freq *= 2.03
    return out / norm


def hexrgb(h: str):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


# ── grid + layer ────────────────────────────────────────────────────────────
class Grid:
    """Normalised cell coordinates. Frame height = 1, y grows downward,
    x spans [-aspect/2, aspect/2] so circles stay round despite tall cells."""

    def __init__(self, cols, rows, cw, chh, seed=7):
        self.cols, self.rows, self.cw, self.ch = cols, rows, cw, chh
        self.aspect = (cols * cw) / (rows * chh)
        x = ((np.arange(cols) + 0.5) / cols - 0.5) * self.aspect
        y = (np.arange(rows) + 0.5) / rows - 0.5
        self.X, self.Y = np.meshgrid(x, y)
        self.r = np.hypot(self.X, self.Y)
        self.ang = np.arctan2(self.Y, self.X)
        self.C, self.R = np.meshgrid(np.arange(cols), np.arange(rows))
        rng = np.random.default_rng(seed)
        self.rnd = rng.random((rows, cols))          # stable per-cell randomness
        self.hsh = rng.integers(0, 1 << 16, (rows, cols))
        self.cache: dict = {}

    @property
    def shape(self):
        return (self.rows, self.cols)

    def layer(self):
        return Layer(self.shape)

    def to_cell(self, x, y):
        """Normalised coords -> (col, row) integer arrays."""
        c = np.floor((np.asarray(x) / self.aspect + 0.5) * self.cols).astype(int)
        r = np.floor((np.asarray(y) + 0.5) * self.rows).astype(int)
        return c, r


class Layer:
    """char = glyph index into CHARS, lum = brightness (0..~1.3),
    tag = palette index. Everything is painted with `put` / `text`."""

    def __init__(self, shape):
        self.char = np.zeros(shape, dtype=np.int32)
        self.lum = np.zeros(shape, dtype=np.float32)
        self.tag = np.zeros(shape, dtype=np.int32)
        self.info: dict = {}

    def put(self, mask, char, lum, tag):
        """Paint cells where mask is True. Arguments may be scalars or arrays."""
        mask = np.asarray(mask, dtype=bool)
        self.char = np.where(mask, char, self.char)
        self.lum = np.where(mask, lum, self.lum).astype(np.float32)
        self.tag = np.where(mask, tag, self.tag)
        return self

    def over(self, mask, char, lum, tag):
        """Like put, but only where the new cell is brighter (depth-free max blend)."""
        mask = np.asarray(mask, dtype=bool) & (np.asarray(lum) >= self.lum)
        return self.put(mask, char, lum, tag)

    def text(self, row, col, s, lum=1.0, tag=0, reveal=None, skip_spaces=True):
        """Write literal text. col='center' centres it. reveal=k shows only the
        first k characters (typewriter). Returns the column after the text."""
        rows, cols = self.char.shape
        if col == "center":
            col = (cols - len(s)) // 2
        if reveal is not None:
            s = s[: max(0, int(reveal))]
        if not 0 <= row < rows:
            return col + len(s)
        for i, c in enumerate(s):
            x = col + i
            if 0 <= x < cols and (c != " " or not skip_spaces):
                self.char[row, x] = AT.get(c, AT["?"])
                self.lum[row, x] = lum
                self.tag[row, x] = tag
        return col + len(s)

    def count(self):
        return int((self.char != 0).sum())


# ── glyph selection ─────────────────────────────────────────────────────────
def shade(heat, jitter, flow=0.0, pools=POOLS, gain=None):
    """Map heat (0..1) to a glyph from the density pools.

    jitter: per-cell integers (g.hsh) so neighbours differ.
    flow:   a slowly varying field; changing it makes letters *drift*
            through the pool instead of flickering randomly each frame.
    """
    key = tuple(pools)
    if key not in _FILL_CACHE:
        _FILL_CACHE[key] = _fill_table(pools)
    fill = _FILL_CACHE[key]
    n = len(pools)
    gain = n if gain is None else gain
    level = np.clip((np.asarray(heat) * gain).astype(int), 0, n - 1)
    idx = (jitter + np.asarray(flow * 1.0).astype(int)) % fill.shape[1]
    return fill[level, idx]


def tangent(dx, dy):
    """Glyph that follows a direction (screen y down): - / | \\"""
    s = np.degrees(np.arctan2(-np.asarray(dy), np.asarray(dx))) % 180
    out = np.full(np.shape(s), AT["\\"])
    out = np.where((s < 22.5) | (s >= 157.5), AT["-"], out)
    out = np.where((s >= 22.5) & (s < 67.5), AT["/"], out)
    out = np.where((s >= 67.5) & (s < 112.5), AT["|"], out)
    return out


def levels(heat, cuts):
    """Palette tag from heat thresholds: levels(h, [0.1, 0.3, 0.6]) -> 0..3."""
    return np.digitize(heat, cuts)


# ── fonts + text masks ──────────────────────────────────────────────────────
_FONT_HINTS = {
    "mono": ["JetBrainsMono-Regular", "DejaVuSansMono.ttf", "Menlo", "Consolas",
             "NotoSansMono-Regular", "LiberationMono-Regular", "SourceCodePro-Regular"],
    "bold": ["Montserrat-ExtraBold", "Montserrat-Bold", "DejaVuSans-Bold.ttf",
             "NotoSans-Bold", "LiberationSans-Bold", "Arial Bold", "Helvetica-Bold"],
    "monobold": ["JetBrainsMono-ExtraBold", "JetBrainsMono-Bold", "DejaVuSansMono-Bold",
                 "SourceCodePro-Bold", "NotoSansMono-Bold"],
}
_FONT_DIRS = ["/usr/share/fonts", "/usr/local/share/fonts", str(Path.home() / ".local/share/fonts"),
              str(Path.home() / ".fonts"), "/Library/Fonts", "/System/Library/Fonts",
              str(Path.home() / "Library/Fonts"), "C:/Windows/Fonts"]


def find_font(kind="mono"):
    """Best-effort path to a font. kind: mono | bold | monobold | a path."""
    if kind and Path(kind).is_file():
        return kind
    hints = _FONT_HINTS.get(kind, [kind])
    for hint in hints:
        for d in _FONT_DIRS:
            p = Path(d)
            if not p.is_dir():
                continue
            for f in p.rglob("*"):
                if f.suffix.lower() in (".ttf", ".otf") and f.stem.lower() == Path(hint).stem.lower():
                    return str(f)
    if shutil.which("fc-match"):
        pat = {"mono": "monospace", "bold": "sans:bold", "monobold": "monospace:bold"}.get(kind, kind)
        out = subprocess.run(["fc-match", "-f", "%{file}", pat], capture_output=True, text=True).stdout
        if out and Path(out).is_file():
            return out
    return None


def _load_font(path, px):
    if path:
        return ImageFont.truetype(path, px)
    try:
        return ImageFont.load_default(px)
    except TypeError:
        return ImageFont.load_default()


def text_field(g, text, height=0.5, center=(0.0, 0.0), font="bold", spacing=0.0, blur=0.0):
    """Rasterise text into a per-cell coverage field in [0, 1].

    height: cap height as a fraction of frame height.
    center: (x, y) in normalised coords.
    blur:   gaussian radius in *pixels* applied before sampling (soft halos).
    Rendering happens at pixel resolution and is box-averaged into cells, so
    letters keep their true proportions on tall cells.
    """
    W, H = g.cols * g.cw, g.rows * g.ch
    fpath = find_font(font)
    px = max(8, int(height * H * 1.35))
    f = _load_font(fpath, px)
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    cx = (center[0] / g.aspect + 0.5) * W
    cy = (center[1] + 0.5) * H
    if spacing:
        widths = [d.textlength(c, font=f) for c in text]
        total = sum(widths) + spacing * px * (len(text) - 1)
        x = cx - total / 2
        for c, w in zip(text, widths):
            d.text((x, cy), c, font=f, fill=255, anchor="lm")
            x += w + spacing * px
    else:
        d.text((cx, cy), text, font=f, fill=255, anchor="mm")
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(img, dtype=np.float32) / 255
    return a.reshape(g.rows, g.ch, g.cols, g.cw).mean(axis=(1, 3))


def blur_field(field, radius):
    """Gaussian blur of a cell field (radius in cells)."""
    a = np.asarray(field, dtype=np.float32)
    lo, hi = float(a.min()), float(a.max())
    span = hi - lo if hi > lo else 1.0
    img = Image.fromarray(((a - lo) / span * 255).astype(np.uint8))
    b = np.asarray(img.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255
    return b * span + lo


# ── common decorations ──────────────────────────────────────────────────────
def stars(g, layer, t, density=0.003, tag=0, lum=0.7, twinkle=0.8):
    """A sparse, stable, gently twinkling starfield in empty cells."""
    empty = layer.char == 0
    s = empty & (g.rnd < density)
    c = np.where(g.rnd < density * 0.2, AT["+"], np.where(g.rnd < density * 0.5, AT["*"], AT["."]))
    tw = lum * (0.75 + 0.25 * np.sin(twinkle * t + g.rnd * 9000))
    return layer.put(s, c, tw, tag)


def glitch_rows(layer, g, t, events, max_shift=4):
    """Short horizontal row tears. events = [(time, duration, row0, row1), ...]."""
    for (t0, dur, r0, r1) in events:
        if t0 <= t < t0 + dur:
            k = int(1 + (t * 97) % max_shift) * (1 if int(t * 31) % 2 else -1)
            for arr in (layer.char, layer.lum, layer.tag):
                arr[r0:r1] = np.roll(arr[r0:r1], k, axis=1)
    return layer


def polyline_splat(g, layer, xs, ys, lum, tag, zs=None, char=None, zbuf=None):
    """Splat sampled curve points (normalised coords) into the grid.

    Points become tangent glyphs (from neighbour differences) unless `char`
    is given. zs + zbuf give simple depth sorting (larger z = nearer).
    Returns the z-buffer so several curves can share one.
    """
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    lum = np.broadcast_to(np.asarray(lum, float), xs.shape)
    tag = np.broadcast_to(np.asarray(tag), xs.shape)
    zs = np.zeros_like(xs) if zs is None else np.asarray(zs, float)
    if zbuf is None:
        zbuf = np.full(g.shape, -np.inf)
    if char is None:
        dx = np.gradient(xs) * g.cols / g.aspect
        dy = np.gradient(ys) * g.rows
        glyph = tangent(dx, dy)
    else:
        glyph = np.broadcast_to(np.asarray(char), xs.shape)
    c, r = g.to_cell(xs, ys)
    ok = (c >= 0) & (c < g.cols) & (r >= 0) & (r < g.rows) & (lum > 0.02)
    order = np.argsort(zs[ok])                       # far first, near overwrites
    for i in np.flatnonzero(ok)[order]:
        rr, cc = r[i], c[i]
        if zs[i] >= zbuf[rr, cc] or lum[i] > layer.lum[rr, cc] * 1.5:
            zbuf[rr, cc] = zs[i]
            layer.char[rr, cc] = glyph[i]
            layer.lum[rr, cc] = max(lum[i], 0.0)
            layer.tag[rr, cc] = tag[i]
    return zbuf


# ── diagram primitives ──────────────────────────────────────────────────────
# Cell-space (row, col) helpers for animated ASCII diagrams: boxes, routed
# wires and packets that travel along them. Combine freely with fields.

def box(layer, r, c, h, w, title=None, lum=0.6, tag=0, title_lum=None, title_tag=None,
        rounded=True, fill=None):
    """Draw a box with its top-left corner at (r, c), h rows x w cols.
    title is centred inside; a list of strings gives several centred lines.
    fill=(char, lum, tag) paints the interior first."""
    tl, tr, bl, br = "╭╮╰╯" if rounded else "┌┐└┘"
    if fill:
        fc, fl, ft = fill
        layer.char[r + 1:r + h - 1, c + 1:c + w - 1] = AT[fc] if isinstance(fc, str) else fc
        layer.lum[r + 1:r + h - 1, c + 1:c + w - 1] = fl
        layer.tag[r + 1:r + h - 1, c + 1:c + w - 1] = ft
    layer.text(r, c, tl + "─" * (w - 2) + tr, lum, tag)
    layer.text(r + h - 1, c, bl + "─" * (w - 2) + br, lum, tag)
    for rr in range(r + 1, r + h - 1):
        layer.text(rr, c, "│", lum, tag)
        layer.text(rr, c + w - 1, "│", lum, tag)
    if title is not None:
        lines = [title] if isinstance(title, str) else list(title)
        r0 = r + (h - len(lines)) // 2
        for i, line in enumerate(lines):
            layer.text(r0 + i, c + (w - len(line)) // 2, line,
                       lum if title_lum is None else title_lum,
                       tag if title_tag is None else title_tag)
    return (r, c, h, w)


_CORNER = {((0, 1), (1, 0)): "╮", ((0, 1), (-1, 0)): "╯", ((0, -1), (1, 0)): "╭", ((0, -1), (-1, 0)): "╰",
           ((1, 0), (0, 1)): "╰", ((1, 0), (0, -1)): "╯", ((-1, 0), (0, 1)): "╭", ((-1, 0), (0, -1)): "╮"}
_HEAD = {(0, 1): "►", (0, -1): "◄", (1, 0): "▼", (-1, 0): "▲"}


def wire(layer, points, lum=0.35, tag=0, arrow=True, draw=True):
    """Orthogonal wire through (row, col) waypoints. Returns the list of cells
    along it (for `packets`). Consecutive waypoints must share a row or col."""
    path = []
    for (r1, c1), (r2, c2) in zip(points, points[1:]):
        dr, dc = int(np.sign(r2 - r1)), int(np.sign(c2 - c1))
        n = max(abs(r2 - r1), abs(c2 - c1))
        seg = [(r1 + dr * k, c1 + dc * k) for k in range(n + 1)]
        path += seg if not path else seg[1:]
    if draw:
        for i, (r, c) in enumerate(path):
            d_in = (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]) if i else None
            d_out = (path[i + 1][0] - r, path[i + 1][1] - c) if i + 1 < len(path) else None
            if d_in and d_out and d_in != d_out:
                g = _CORNER.get((d_in, d_out), "+")
            elif i + 1 == len(path) and arrow and d_in:
                g = _HEAD[d_in]
            else:
                d = d_out or d_in or (0, 1)
                g = "─" if d[0] == 0 else "│"
            layer.text(r, c, g, lum, tag)
    return path


def packets(layer, path, t, speed=18.0, spacing=14, tail=5, lum=1.2, tag=0, tail_tag=None,
            head="●", phase=0.0, count=None):
    """Bright packets flowing along a wire path (cells/second). Loops cleanly
    when len(path) / speed divides the scene duration, or use `count` with
    spacing = len(path) / count for an exact cycle."""
    n = len(path)
    if n == 0:
        return []
    if count:
        spacing = n / count
    heads = []
    pos0 = (t * speed + phase * spacing) % spacing
    k = pos0
    while k < n:
        heads.append(k)
        k += spacing
    for hpos in heads:
        hi = int(hpos)
        for j in range(tail, 0, -1):
            if hi - j >= 0:
                r, c = path[hi - j]
                f = (1 - j / (tail + 1)) * lum * 0.7
                if layer.lum[r, c] < f:
                    layer.lum[r, c] = f
                    layer.tag[r, c] = tag if tail_tag is None else tail_tag
        r, c = path[hi]
        layer.text(r, c, head, lum, tag)
    return heads


# ── renderer ────────────────────────────────────────────────────────────────
DEFAULTS = dict(
    width=960, height=320,      # output pixels
    cell=(7, 12),               # glyph cell (w, h) in pixels
    font_px=12,                 # glyph size inside the cell
    font="mono",                # path or mono | monobold
    fps=15, duration=8.0,
    palette=["#ffffff"],        # tag -> colour
    bg="#0d1117",               # GitHub dark background, so GIFs blend in
    trail=0.45,                 # 0 = no persistence, 0.8 = long smears
    bloom=[(4, 5, 0.7), (8, 22, 0.4)],   # (downscale, radius px, amount)
    loop=True,                  # warm the trail with the end of the loop so frame 0 matches
    warm=1.5,                   # seconds of warm-up for stills / loops
    seed=7,
)


class Renderer:
    def __init__(self, scene):
        cfg = dict(DEFAULTS)
        cfg.update(getattr(scene, "CONFIG", {}))
        self.cfg, self.scene = cfg, scene
        self.W, self.H = cfg["width"], cfg["height"]
        self.cw, self.chh = cfg["cell"]
        self.cols, self.rows = self.W // self.cw, self.H // self.chh
        self.ox = (self.W - self.cols * self.cw) // 2
        self.oy = (self.H - self.rows * self.chh) // 2
        self.g = Grid(self.cols, self.rows, self.cw, self.chh, cfg["seed"])
        self.pal = np.array([hexrgb(c) if isinstance(c, str) else c for c in cfg["palette"]], np.float32) / 255
        self.bg = np.array(hexrgb(cfg["bg"]) if isinstance(cfg["bg"], str) else cfg["bg"], np.float32) / 255
        self.font_path = find_font(cfg["font"])
        self.atlas = self._atlas()
        self.trail = np.zeros((self.rows * self.chh, self.cols * self.cw, 3), np.float32)
        hud_px = cfg.get("hud_px", 13)
        self.hud_font = _load_font(find_font("mono"), hud_px)
        if hasattr(scene, "setup"):
            scene.setup(self.g)

    def _atlas(self):
        f = _load_font(self.font_path, self.cfg["font_px"])
        out = []
        for c in CHARS:
            im = Image.new("L", (self.cw, self.chh), 0)
            ImageDraw.Draw(im).text((self.cw / 2, self.chh / 2), c, font=f, fill=255, anchor="mm")
            out.append(np.asarray(im, np.float32) / 255)
        return np.stack(out)

    def reset(self):
        self.trail[:] = 0

    def step(self, t):
        """Advance the trail by one frame at time t. Returns the Layer."""
        layer = self.scene.frame(t, self.g)
        rows, cols = self.rows, self.cols
        mask = self.atlas[np.clip(layer.char, 0, len(CHARS) - 1)]           # rows, cols, ch, cw
        mask = mask.transpose(0, 2, 1, 3).reshape(rows * self.chh, cols * self.cw)
        tag = np.clip(layer.tag, 0, len(self.pal) - 1)
        col = self.pal[tag] * np.clip(layer.lum, 0, 1.6)[..., None]
        col = np.repeat(np.repeat(col, self.chh, 0), self.cw, 1)
        img = mask[..., None] * col
        tr = self.cfg["trail"]
        self.trail = np.maximum(self.trail * tr, img) if tr > 0 else img
        return layer

    def image(self, t=0.0, layer=None):
        """Compose trail + bloom + background + HUD into a PIL image."""
        art = np.zeros((self.H, self.W, 3), np.float32)
        art[self.oy:self.oy + self.rows * self.chh, self.ox:self.ox + self.cols * self.cw] = self.trail
        out = art.copy()
        base = Image.fromarray((np.clip(art, 0, 1) * 255).astype(np.uint8))
        for k, radius, amount in self.cfg["bloom"]:
            small = base.resize((max(1, self.W // k), max(1, self.H // k)), Image.BILINEAR)
            small = small.filter(ImageFilter.GaussianBlur(max(0.5, radius / k)))
            big = np.asarray(small.resize((self.W, self.H), Image.BILINEAR), np.float32) / 255
            out += amount * big
        out = self.bg + out * (1 - self.bg * 0.5)
        im = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
        if hasattr(self.scene, "hud"):
            d = ImageDraw.Draw(im)
            for item in self.scene.hud(t, self.g) or []:
                text, (x, y), rgb = item[:3]
                anchor = item[3] if len(item) > 3 else "la"
                rgb = tuple(hexrgb(rgb)) if isinstance(rgb, str) else tuple(rgb)
                d.text((x, y), text, font=self.hud_font, fill=rgb, anchor=anchor)
        return im

    def frames(self):
        """Yield (t, PIL.Image) for one full loop."""
        fps, dur = self.cfg["fps"], self.cfg["duration"]
        n = int(round(fps * dur))
        self.reset()
        if self.cfg["loop"]:
            for i in range(int(self.cfg["warm"] * fps), 0, -1):
                self.step(dur - i / fps)
        for i in range(n):
            t = i / fps
            layer = self.step(t)
            yield t, self.image(t, layer)

    def still(self, t):
        fps = self.cfg["fps"]
        self.reset()
        t0 = t - self.cfg["warm"]
        k = max(1, int(self.cfg["warm"] * fps))
        layer = None
        for i in range(k + 1):
            tt = t0 + i * (t - t0) / k
            if tt < 0:
                tt = (tt % self.cfg["duration"]) if self.cfg["loop"] else 0.0
            layer = self.step(tt)
        return self.image(t, layer)


# ── outputs ─────────────────────────────────────────────────────────────────
def write_gif(r: Renderer, path, colors=40, dither="none", scale=1.0):
    fps = r.cfg["fps"]
    W, H = r.W, r.H
    ow, oh = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
    if shutil.which("ffmpeg"):
        vf = f"scale={ow}:{oh}:flags=lanczos," if scale != 1.0 else ""
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
               "-filter_complex",
               f"[0:v]{vf}split[a][b];[a]palettegen=max_colors={colors}:stats_mode=full[p];"
               f"[b][p]paletteuse=dither={dither}:diff_mode=rectangle",
               "-loop", "0", str(path)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for _, im in r.frames():
            p.stdin.write(im.tobytes())
        p.stdin.close()
        p.wait()
    else:
        ims = [im.resize((ow, oh), Image.LANCZOS) if scale != 1.0 else im for _, im in r.frames()]
        pal = ims[len(ims) // 2].quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
        q = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in ims]
        q[0].save(path, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0, optimize=True)


def write_mp4(r: Renderer, path, crf=18):
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is required for --mp4")
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{r.W}x{r.H}", "-r", str(r.cfg["fps"]), "-i", "-",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), str(path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for _, im in r.frames():
        p.stdin.write(im.tobytes())
    p.stdin.close()
    p.wait()


def contact_sheet(r: Renderer, path, n=8, cols=2):
    dur = r.cfg["duration"]
    times = [dur * (i + 0.5) / n for i in range(n)]
    ims = [r.still(t) for t in times]
    w, h = ims[0].size
    rows = math.ceil(n / cols)
    pad = 24
    sheet = Image.new("RGB", (cols * w, rows * (h + pad)), (20, 20, 24))
    d = ImageDraw.Draw(sheet)
    for i, (t, im) in enumerate(zip(times, ims)):
        x, y = (i % cols) * w, (i // cols) * (h + pad)
        d.text((x + 8, y + 5), f"t = {t:.2f}s", fill=(200, 200, 210), font=r.hud_font)
        sheet.paste(im, (x, y + pad))
    sheet.save(path)


def play_terminal(r: Renderer, seconds=None):
    """Truecolor ANSI playback straight from the layer (no atlas / bloom)."""
    fps, dur = r.cfg["fps"], r.cfg["duration"]
    pal = (r.pal * 255).astype(int)
    sys.stdout.write("\x1b[2J\x1b[?25l")
    t0, t = time.time(), 0.0
    try:
        while seconds is None or t < seconds:
            t = time.time() - t0
            layer = r.scene.frame(t % dur, r.g)
            lines = []
            for row in range(r.rows):
                parts = []
                for c in range(r.cols):
                    k = layer.char[row, c]
                    if k == 0:
                        parts.append(" ")
                        continue
                    rgb = np.clip(pal[min(layer.tag[row, c], len(pal) - 1)] * min(layer.lum[row, c], 1.3), 0, 255).astype(int)
                    parts.append(f"\x1b[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{CHARS[k]}")
                lines.append("".join(parts) + "\x1b[0m")
            sys.stdout.write("\x1b[H" + "\n".join(lines))
            sys.stdout.flush()
            time.sleep(max(0.0, 1 / fps - (time.time() - t0 - t)))
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h\n")


def load_scene(path):
    path = Path(path).resolve()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.modules.setdefault("asciianim", sys.modules[__name__])
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scene")
    ap.add_argument("--gif"), ap.add_argument("--mp4"), ap.add_argument("--png")
    ap.add_argument("--sheet"), ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--still", type=float, default=None, help="time for --png")
    ap.add_argument("--term", action="store_true", help="play in the terminal (truecolor ANSI)")
    ap.add_argument("--seconds", type=float, default=None, help="stop --term playback after N seconds")
    ap.add_argument("--colors", type=int, default=40, help="GIF palette size (32-64 is plenty for glyph art)")
    ap.add_argument("--dither", default="none", help="ffmpeg paletteuse dither (none compresses best)")
    ap.add_argument("--scale", type=float, default=1.0, help="GIF output scale")
    ap.add_argument("--fps", type=float), ap.add_argument("--duration", type=float)
    a = ap.parse_args(argv)

    scene = load_scene(a.scene)
    cfg = getattr(scene, "CONFIG", {})
    if a.fps:
        cfg["fps"] = a.fps
    if a.duration:
        cfg["duration"] = a.duration
    scene.CONFIG = cfg
    r = Renderer(scene)
    print(f"[asciianim] {Path(a.scene).name}: {r.cols}x{r.rows} cells, {r.W}x{r.H}px, "
          f"{r.cfg['fps']}fps x {r.cfg['duration']}s, font={r.font_path}", file=sys.stderr)
    did = False
    if a.png:
        r.still(a.still if a.still is not None else r.cfg["duration"] / 2).save(a.png)
        did = True
    if a.sheet:
        contact_sheet(r, a.sheet, a.n)
        did = True
    if a.gif:
        t = time.time()
        write_gif(r, a.gif, a.colors, a.dither, a.scale)
        kb = Path(a.gif).stat().st_size / 1024
        print(f"[asciianim] wrote {a.gif} ({kb:,.0f} KB) in {time.time() - t:.1f}s", file=sys.stderr)
        did = True
    if a.mp4:
        write_mp4(r, a.mp4)
        did = True
    if a.term or not did:
        play_terminal(r, a.seconds)


if __name__ == "__main__":
    main()
