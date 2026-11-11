# Section dividers: a cursive word that writes itself, framed by fading rules.
# The glyphs are shaped with HarfBuzz and stored as SVG paths, so the result
# doesn't depend on fonts on the viewer's machine.
#
#   pip install fonttools uharfbuzz
#   curl -LO https://github.com/google/fonts/raw/main/ofl/parisienne/Parisienne-Regular.ttf   (SIL OFL)
#   python dividers.py Parisienne-Regular.ttf ../assets
#   python dividers.py Parisienne-Regular.ttf ../assets --static   # final frame, no animation

import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

SECTIONS = [("description", "Description", "01"),
            ("options", "Options", "02"),
            ("pipeline", "Pipeline", "03"),
            ("files", "Files", "04"),
            ("bugs", "Bugs", "05"),
            ("see-also", "See also", "06")]

W, H = 960, 96
SIZE = 58                       # font size in px
BASE = 64                       # baseline y
GAP = 26                        # space between word and rules
COLORS = ("#8b5cf6", "#22d3ee", "#14b8a6")


def shape(font_path, text):
    blob = hb.Blob.from_file_path(font_path)
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True, "calt": True})
    return buf.glyph_infos, buf.glyph_positions, face.upem


def word_paths(font_path, text):
    tt = TTFont(font_path)
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    infos, positions, upem = shape(font_path, text)
    s = SIZE / upem
    total = sum(p.x_advance for p in positions) * s
    x0 = (W - total) / 2
    paths, pen_x = [], 0
    for info, pos in zip(infos, positions):
        pen = SVGPathPen(gs)
        # font units: y up. SVG: y down -> flip around the baseline
        tp = TransformPen(pen, (s, 0, 0, -s, x0 + (pen_x + pos.x_offset) * s, BASE - pos.y_offset * s))
        gs[order[info.codepoint]].draw(tp)
        d = pen.getCommands()
        if d:
            paths.append(d)
        pen_x += pos.x_advance
    return paths, x0, x0 + total


def svg(font_path, word, num, static=False):
    paths, left, right = word_paths(font_path, word)
    mid = BASE - 14
    lx, rx = left - GAP, right + GAP
    glyphs = "\n    ".join(f'<path pathLength="1" d="{d}"/>' for d in paths)
    anim = "" if static else """
  <style>
    .w path { stroke-dasharray: 1; stroke-dashoffset: 1; fill-opacity: 0;
              animation: draw 2.2s cubic-bezier(.6,.05,.3,1) forwards, fill .9s ease 1.6s forwards; }
    .rule { stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 1.4s ease-out .5s forwards; }
    .dot, .num { opacity: 0; animation: show .6s ease 1.7s forwards; }
    @keyframes draw { to { stroke-dashoffset: 0; } }
    @keyframes fill { to { fill-opacity: 1; } }
    @keyframes show { to { opacity: 1; } }
  </style>"""
    c1, c2, c3 = COLORS
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{word}">
  <title>{word}</title>
  <defs>
    <linearGradient id="ink" gradientUnits="userSpaceOnUse" x1="{left:.0f}" y1="0" x2="{right:.0f}" y2="0">
      <stop offset="0" stop-color="{c1}"/><stop offset=".55" stop-color="{c2}"/><stop offset="1" stop-color="{c3}"/>
    </linearGradient>
    <linearGradient id="ruleL" gradientUnits="userSpaceOnUse" x1="24" y1="0" x2="{lx:.0f}" y2="0">
      <stop offset="0" stop-color="{c1}" stop-opacity="0"/><stop offset="1" stop-color="{c1}" stop-opacity=".9"/>
    </linearGradient>
    <linearGradient id="ruleR" gradientUnits="userSpaceOnUse" x1="{rx:.0f}" y1="0" x2="{W - 24}" y2="0">
      <stop offset="0" stop-color="{c3}" stop-opacity=".9"/><stop offset="1" stop-color="{c3}" stop-opacity="0"/>
    </linearGradient>
  </defs>{anim}
  <path class="rule" pathLength="1" d="M{lx:.1f} {mid} L24 {mid}" stroke="url(#ruleL)" stroke-width="1.2" fill="none"/>
  <path class="rule" pathLength="1" d="M{rx:.1f} {mid} L{W - 24} {mid}" stroke="url(#ruleR)" stroke-width="1.2" fill="none"/>
  <circle class="dot" cx="{lx + 6:.1f}" cy="{mid}" r="2.2" fill="{c1}"/>
  <circle class="dot" cx="{rx - 6:.1f}" cy="{mid}" r="2.2" fill="{c3}"/>
  <text class="num" x="{W - 24}" y="{mid - 8}" text-anchor="end" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="11" letter-spacing="1" fill="#8b949e">{num} /</text>
  <g class="w" fill="url(#ink)" stroke="url(#ink)" stroke-width="0.9" stroke-linejoin="round">
    {glyphs}
  </g>
</svg>
"""


def main():
    font_path, out = sys.argv[1], Path(sys.argv[2])
    static = "--static" in sys.argv
    out.mkdir(parents=True, exist_ok=True)
    for slug, word, num in SECTIONS:
        p = out / f"h-{slug}{'-static' if static else ''}.svg"
        p.write_text(svg(font_path, word, num, static))
        print(p, f"{p.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
