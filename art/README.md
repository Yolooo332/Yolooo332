# art/

The animations on the profile page are Python scenes drawn only with
letters, numbers and symbols. Each frame, every cell of a character grid
works out "how much light is here?", and the answer picks a glyph from a
density-ranked pool, a palette colour and a brightness. The renderer then
fades each frame into a trail, adds two blur passes for bloom and writes a GIF.

| scene | what it is | technique |
|---|---|---|
| `hero.py`  | the name ignites under a scan beam, holds, burns off | text mask field · contour glyphs · sweep fronts · glitch rows |
| `stack.py` | languages orbiting a shaded core, like an atom | lit sphere field · 3D orbits splatted with a depth buffer · comet tails |
| `flow.py`  | browser → frontend → api → database request flow | box / wire / packet diagram primitives · glow fields |
| `scope.py` | oscilloscope, two PID tuning passes | analytic step response · slope glyphs · phosphor trail |
| `dividers.py` | cursive section headings that write themselves | HarfBuzz shaping → SVG paths · stroke-dash draw-on |

## Rebuild

```sh
pip install -r requirements.txt          # ffmpeg is optional, but it makes much smaller GIFs
python asciianim.py hero.py --sheet sheet.png --n 8     # contact sheet to check the timing
python asciianim.py hero.py --gif ../assets/hero.gif    # final render
python asciianim.py flow.py --term                      # play it in the terminal
```

`asciianim.py` is the renderer engine.
The technique is inspired by the ASCII code art of JIN2 ([@jin_22ee](https://instagram.com/jin_22ee)).
All scene code here is original.

## Section dividers

`dividers.py` writes the cursive section headings (`assets/h-*.svg`). Each word
is shaped with HarfBuzz from the Parisienne font (SIL OFL), stored as SVG paths,
and drawn on with a CSS stroke animation, so it needs no web fonts.
