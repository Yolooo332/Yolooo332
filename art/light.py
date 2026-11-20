"""Render a scene for a white background.

    python light.py stack.py --gif ../assets/stack-light.gif

asciianim only adds light onto a dark background. For white, the scene is rendered on
black with every colour inverted, then each finished frame is inverted back: the ground
turns white, every glyph lands on its intended colour, and the bloom becomes a soft ink
bleed instead of a glow. The scene supplies PALETTE_LIGHT, the colours it should end up
with on white (same roles and order as PALETTE).
"""
import argparse
import sys
from pathlib import Path

from PIL import ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asciianim as A  # noqa: E402


def invert(hex_colour):
    h = hex_colour.lstrip("#")
    return "#" + "".join(f"{255 - int(h[i:i + 2], 16):02x}" for i in (0, 2, 4))


class Inverted:
    """Looks enough like a Renderer for write_gif / contact_sheet, with every frame inverted."""

    def __init__(self, r):
        self.r, self.cfg, self.W, self.H = r, r.cfg, r.W, r.H

    def frames(self):
        for t, im in self.r.frames():
            yield t, ImageOps.invert(im.convert("RGB"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scene")
    ap.add_argument("--gif", required=True)
    ap.add_argument("--font", help="font path, if JetBrains Mono isn't installed")
    ap.add_argument("--colors", type=int, default=40)
    a = ap.parse_args()

    scene = A.load_scene(a.scene)
    cfg = dict(getattr(scene, "CONFIG", {}))
    cfg["palette"] = [invert(c) for c in scene.PALETTE_LIGHT]
    cfg["bg"] = "#000000"
    if a.font:
        cfg["font"] = a.font
    scene.CONFIG = cfg
    A.write_gif(Inverted(A.Renderer(scene)), a.gif, a.colors, "none", 1.0)
    print(f"[light] wrote {a.gif} ({Path(a.gif).stat().st_size / 1024:,.0f} KB)", file=sys.stderr)


if __name__ == "__main__":
    main()
