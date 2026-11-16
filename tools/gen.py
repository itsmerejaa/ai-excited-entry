#!/usr/bin/env python3
"""Generate the "excited AI" 1024x1024 artwork with Pillow only (no numpy).

Layout of the image, from the inside out:
  * radial gradient background: white -> yellow -> orange -> magenta -> purple -> black
  * ~80 translucent light rays (polygons) radiating from the centre
  * concentric ring waves with a sinusoidal intensity ripple
  * small warm particles plus a handful of star-shaped sparks
  * a hot white core that is added on top additively

Everything is deterministic: the only randomness comes from
``random.Random(SEED)`` and there is no use of time, os.urandom or any other
non-reproducible source.

Usage:
    /data/home/venv/bin/python tools/gen.py [output.png]
"""

from __future__ import annotations

import math
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

SIZE = 1024
SEED = 20261116
LUT_STEPS = 1024
RAY_COUNT = 80
RING_COUNT = 16
PARTICLE_COUNT = 1100
SPARK_COUNT = 26

# Palette stops: (position along the radius, RGB).  White in the centre, black
# at the rim, with yellow / orange / magenta / purple in between.
STOPS = (
    (0.00, (255, 255, 255)),
    (0.06, (255, 252, 222)),
    (0.14, (255, 232, 96)),
    (0.26, (255, 196, 0)),
    (0.38, (255, 122, 0)),
    (0.50, (255, 46, 92)),
    (0.60, (255, 0, 148)),
    (0.72, (168, 0, 214)),
    (0.84, (68, 0, 116)),
    (0.93, (16, 0, 30)),
    (1.00, (0, 0, 0)),
)

# 4x4 ordered dither, keeps the long smooth gradient free of banding.
BAYER4 = (
    0.0 / 16, 8.0 / 16, 2.0 / 16, 10.0 / 16,
    12.0 / 16, 4.0 / 16, 14.0 / 16, 6.0 / 16,
    3.0 / 16, 11.0 / 16, 1.0 / 16, 9.0 / 16,
    15.0 / 16, 7.0 / 16, 13.0 / 16, 5.0 / 16,
)


def smoothstep(x: float) -> float:
    return x * x * (3.0 - 2.0 * x)


def build_palette(steps: int = LUT_STEPS):
    """Interpolate STOPS into a list of ``steps`` RGB tuples."""
    lut = []
    last = len(STOPS) - 1
    for i in range(steps):
        t = i / (steps - 1)
        for j in range(last):
            p0, c0 = STOPS[j]
            p1, c1 = STOPS[j + 1]
            if t <= p1 or j == last - 1:
                span = p1 - p0 if p1 > p0 else 1.0
                f = smoothstep(min(max((t - p0) / span, 0.0), 1.0))
                lut.append(tuple(int(round(c0[k] + (c1[k] - c0[k]) * f)) for k in range(3)))
                break
    return lut


def sample(palette, t: float):
    """Nearest palette entry for a normalized radius ``t``."""
    i = int(min(max(t, 0.0), 1.0) * (len(palette) - 1))
    return palette[i]


def make_gradient(size: int, palette, max_r: float) -> Image.Image:
    """Radial gradient, computed on one quadrant and mirrored 2x2."""
    half = size // 2
    n = len(palette)
    scale = (n - 1) / max_r
    cx = cy = (size - 1) / 2.0

    quad = bytearray(half * half * 3)
    p = 0
    for y in range(half):
        dy2 = (cy - y) ** 2
        row_dither = (y & 3) * 4
        for x in range(half):
            dx = cx - x
            t = math.sqrt(dx * dx + dy2) * scale + BAYER4[row_dither + (x & 3)]
            i = int(t)
            if i >= n - 1:
                i = n - 1
            elif i < 0:
                i = 0
            r, g, b = palette[i]
            quad[p] = r
            quad[p + 1] = g
            quad[p + 2] = b
            p += 3

    tile = Image.frombytes("RGB", (half, half), bytes(quad))
    img = Image.new("RGB", (size, size))
    img.paste(tile, (0, 0))
    img.paste(tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (half, 0))
    img.paste(tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM), (0, half))
    img.paste(tile.transpose(Image.Transpose.ROTATE_180), (half, half))
    return img


def blank_layer(size: int) -> Image.Image:
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def screen_over(base: Image.Image, layer: Image.Image, strength: float = 1.0) -> Image.Image:
    """Screen-blend a light layer (RGBA, drawn on black) onto an RGB base."""
    light = Image.alpha_composite(Image.new("RGBA", base.size, (0, 0, 0, 255)), layer)
    out = ImageChops.screen(base, light.convert("RGB"))
    return Image.blend(base, out, strength) if strength < 1.0 else out


def draw_rays(size: int, rng: random.Random, palette) -> Image.Image:
    """~RAY_COUNT translucent polygons radiating from the centre."""
    layer = blank_layer(size)
    d = ImageDraw.Draw(layer, "RGBA")
    c = (size - 1) / 2.0
    step = 2.0 * math.pi / RAY_COUNT
    phase = rng.uniform(0.0, 2.0 * math.pi)

    for i in range(RAY_COUNT):
        ang = phase + i * step + rng.uniform(-0.010, 0.010)
        half_w = math.radians(rng.uniform(0.16, 0.55))
        outer = rng.uniform(0.44, 0.74) * size
        col = sample(palette, rng.uniform(0.24, 0.60))
        alpha = rng.randint(30, 78)

        p1 = (c + math.cos(ang - half_w) * outer, c + math.sin(ang - half_w) * outer)
        p2 = (c + math.cos(ang + half_w) * outer, c + math.sin(ang + half_w) * outer)
        d.polygon([(c, c), p1, p2], fill=(col[0], col[1], col[2], alpha))

        if i % 3 == 0:  # bright thin spine inside some rays
            tip = rng.uniform(0.70, 0.96) * outer
            d.line(
                [(c, c), (c + math.cos(ang) * tip, c + math.sin(ang) * tip)],
                fill=(255, 244, 214, rng.randint(18, 44)),
                width=rng.choice((1, 1, 2)),
            )

    return layer.filter(ImageFilter.GaussianBlur(0.7))


def draw_rings(size: int, rng: random.Random, palette) -> Image.Image:
    """Concentric ring waves: arcs whose alpha ripples with the angle."""
    layer = blank_layer(size)
    d = ImageDraw.Draw(layer, "RGBA")
    c = (size - 1) / 2.0
    box_cache = []
    for _ in range(RING_COUNT):
        r = rng.uniform(38.0, 0.47 * size)
        box_cache.append((r, rng.randint(2, 6)))

    for r, waves in sorted(box_cache):
        col = sample(palette, min(r / c, 1.0) * 0.55)
        base_alpha = int(rng.uniform(46, 108))
        phase = rng.uniform(0.0, 2.0 * math.pi)
        width = rng.choice((1, 1, 2, 3))
        arc = 4.0
        a = 0.0
        while a < 360.0:
            ripple = 0.5 + 0.5 * math.sin(math.radians(a) * waves + phase)
            alpha = int(base_alpha * (0.10 + 0.90 * ripple) ** 1.4)
            if alpha > 3:
                box = (c - r, c - r, c + r, c + r)
                d.arc(box, a, a + arc + 1.2, fill=(col[0], col[1], col[2], alpha), width=width)
            a += arc

    return layer.filter(ImageFilter.GaussianBlur(0.8))


def draw_particles(size: int, rng: random.Random, palette) -> Image.Image:
    """Warm dust: small dots biased toward the bright middle."""
    layer = blank_layer(size)
    d = ImageDraw.Draw(layer, "RGBA")
    c = (size - 1) / 2.0
    max_r = 0.52 * size

    for _ in range(PARTICLE_COUNT):
        t = rng.random() ** 0.65
        r = t * max_r
        ang = rng.uniform(0.0, 2.0 * math.pi)
        x = c + math.cos(ang) * r
        y = c + math.sin(ang) * r
        col = sample(palette, min(t * 0.8, 1.0))
        # mix toward white so the dust reads as light, not as coloured noise
        m = rng.uniform(0.25, 0.75)
        col = tuple(int(col[k] + (255 - col[k]) * m) for k in range(3))
        alpha = int(rng.uniform(80, 210) * (1.0 - 0.35 * t))
        rad = rng.choice((0.9, 1.2, 1.6, 2.1, 2.8))
        d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=(col[0], col[1], col[2], alpha))

    for _ in range(SPARK_COUNT):  # brighter four-point sparks
        r = rng.uniform(0.10, 0.48) * size
        ang = rng.uniform(0.0, 2.0 * math.pi)
        x = c + math.cos(ang) * r
        y = c + math.sin(ang) * r
        arm = rng.uniform(3.0, 9.0)
        alpha = rng.randint(120, 225)
        d.line((x - arm, y, x + arm, y), fill=(255, 248, 226, alpha), width=1)
        d.line((x, y - arm, x, y + arm), fill=(255, 248, 226, alpha), width=1)
        d.ellipse((x - 1.4, y - 1.4, x + 1.4, y + 1.4), fill=(255, 255, 255, min(255, alpha + 20)))

    return layer.filter(ImageFilter.GaussianBlur(0.5))


def draw_core(size: int, rng: random.Random, palette) -> Image.Image:
    """Hot white core: concentric glows drawn big-to-small, then blurred."""
    layer = blank_layer(size)
    d = ImageDraw.Draw(layer, "RGBA")
    c = (size - 1) / 2.0
    outer = 0.20 * size

    radii = []
    r = outer
    while r > 1.0:
        radii.append(r)
        r *= 0.90

    for r in radii:
        # inward = whiter, alpha ramps up as the rings shrink
        f = 1.0 - (r / outer)
        col = sample(palette, max(0.0, 0.30 - 0.30 * f))
        col = tuple(int(col[k] + (255 - col[k]) * (0.45 + 0.55 * f)) for k in range(3))
        alpha = int(10 + 42 * f)
        wobble = 1.0 + 0.05 * math.sin(f * 11.0 + rng.random())
        rr = r * wobble
        d.ellipse((c - rr, c - rr, c + rr, c + rr), fill=(col[0], col[1], col[2], alpha))

    halo = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo, "RGBA")
    hr = 0.075 * size
    hd.ellipse((c - hr, c - hr, c + hr, c + hr), fill=(255, 255, 255, 235))
    halo = halo.filter(ImageFilter.GaussianBlur(9.0))

    return Image.alpha_composite(layer, halo)


def render(size: int = SIZE, seed: int = SEED) -> Image.Image:
    palette = build_palette()

    # black at the rim: normalize by half the width, so the edge midpoints hit 1.0
    base = make_gradient(size, palette, max_r=size / 2.0)

    rays = draw_rays(size, random.Random(seed + 1), palette)
    base = screen_over(base, rays, 0.95)
    base = screen_over(base, rays.filter(ImageFilter.GaussianBlur(11.0)), 0.35)

    base = screen_over(base, draw_rings(size, random.Random(seed + 2), palette), 0.9)
    base = screen_over(base, draw_particles(size, random.Random(seed + 3), palette), 1.0)

    core = draw_core(size, random.Random(seed + 4), palette)
    core_rgb = Image.alpha_composite(Image.new("RGBA", (size, size), (0, 0, 0, 255)), core).convert("RGB")
    return ImageChops.add(base, core_rgb)


def main(argv) -> int:
    out = argv[1] if len(argv) > 1 else "entry.png"
    img = render(SIZE, SEED)
    img = img.convert("RGB")
    img.save(out, "PNG", optimize=True)
    print("wrote %s (%dx%d, seed=%d)" % (out, img.width, img.height, SEED))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
