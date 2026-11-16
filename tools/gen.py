#!/usr/bin/env python
"""
gen.py -- deterministic 1024x1024 "explosion" poster generator.

Idea: the smallest thing at the heart of the loudest bang.
A pitch-black chess PAWN, dead-centre, standing upright against a white-hot
radial blast.  A cream rim light keeps the silhouette readable at thumbnail
size.  Everything is drawn with Pillow only -- no numpy.

Usage:  /data/home/venv/bin/python tools/gen.py entry.png
"""

import math
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------- constants
W = H = 1024
CX = CY = 512.0
SEED = 115959

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BAND_Y = int(0.79 * H)                       # dark caption band: 808

# white-hot core -> yellow -> orange -> magenta -> violet -> black
RAMP = [
    (0.00, (255, 255, 255)),
    (0.05, (255, 253, 228)),
    (0.14, (255, 240, 142)),
    (0.30, (255, 190, 48)),
    (0.45, (255, 118, 20)),
    (0.58, (242, 42, 92)),
    (0.72, (188, 20, 134)),
    (0.85, (95, 10, 122)),
    (0.94, (36, 6, 60)),
    (1.00, (4, 2, 8)),
]

RAYS = 80                                    # radiating thin polygons
WAVES = 5                                    # shockwave ellipses
PAWN_H = int(0.50 * H)                       # 512 px = 50% of frame height


def lerp(a, b, t):
    return a + (b - a) * t


def ramp_color(t):
    """Piecewise-linear lookup on RAMP, t in [0, 1]."""
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    for i in range(len(RAMP) - 1):
        p0, c0 = RAMP[i]
        p1, c1 = RAMP[i + 1]
        if p0 <= t <= p1:
            k = (t - p0) / (p1 - p0)
            k = k ** 0.85                    # tight hot core, wide halo
            return (int(round(lerp(c0[0], c1[0], k))),
                    int(round(lerp(c0[1], c1[1], k))),
                    int(round(lerp(c0[2], c1[2], k))))
    return RAMP[-1][1]


# ------------------------------------------------- 1. radial gradient field
def light_add(img, layer, amount):
    """img + layer*amount, clamped. Keeps the gradient from blowing out."""
    return ImageChops.add(img, Image.eval(layer, lambda v: int(v * amount)))


def radial(t_expr):
    """Build a full-res RGB field from a low-res pass + bicubic upscale."""
    S = 256
    small = Image.new("RGB", (S, S))
    px = small.load()
    half = S / 2.0
    diag = math.hypot(half, half)
    for y in range(S):
        dy = (y + 0.5) - half
        for x in range(S):
            dx = (x + 0.5) - half
            px[x, y] = t_expr(math.hypot(dx, dy) / diag)
    return small.resize((W, H), Image.Resampling.BICUBIC)


def build_background():
    # Pure, smooth euclidean radial ramp: white-hot centre -> ... -> black.
    # t = (r/rmax)**1.4 keeps the blast bright well past the silhouette while
    # the corners (r -> 1) land on the black end of the ramp.
    return radial(lambda r: ramp_color(r ** 1.4))


def vignette(img):
    """Darken the frame's rim with a superellipse mask.

    d = 1.0 at any edge midpoint, ~1.17 at the corners.  Light is untouched
    out to d = 0.86 -- deliberate: (512,60), the bright band above the pawn's
    head, sits at d = 0.883 and must stay hot.  From there it rolls off to a
    dim plum at the edges and near-black in the corners, which is what
    actually rings the explosion in darkness.
    """
    S, half = 256, 128.0
    small = Image.new("L", (S, S))
    px = small.load()
    for y in range(S):
        dy = (y + 0.5) - half
        for x in range(S):
            dx = (x + 0.5) - half
            d = ((abs(dx / half) ** 4 + abs(dy / half) ** 4)) ** 0.25
            if d <= 0.86:
                v = 1.0
            elif d <= 1.0:
                v = 1.0 - 0.55 * ((d - 0.86) / 0.14) ** 1.5
            else:
                v = 0.45 * max(0.0, 1.0 - (d - 1.0) / 0.30 * 0.75)
            px[x, y] = int(round(255 * v))
    mask = small.resize((W, H), Image.Resampling.BICUBIC)
    return ImageChops.multiply(img, Image.merge("RGB", (mask, mask, mask)))


def falloff(exp):
    """Soft radial attenuation mask (RGB) used to kill light at the corners."""
    def f(r):
        g = int(round(255 * max(0.0, 1.0 - r ** exp)))
        return (g, g, g)
    return radial(f)


# ------------------------------------------------- 2. rays (~80 polygons)
def draw_rays(img, n=RAYS):
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = random.Random(SEED)
    reach = 1.30 * W                          # pokes past the corners
    for i in range(n):
        ang = 2.0 * math.pi * i / n + rng.uniform(-0.007, 0.007)
        hw = math.radians(rng.uniform(0.28, 1.00))     # angular half-width
        if i % 7 == 3:
            col = (255, 244, 206)                      # a few near-white blades
        else:
            clear = rng.random()
            col = (255, int(lerp(252, 150, clear)), int(lerp(232, 118, clear)))
        r0 = rng.uniform(64.0, 150.0)                  # keep the eye clean
        tip = reach * rng.uniform(0.58, 1.0)
        a, b = ang - hw, ang + hw
        d.polygon([(CX + r0 * math.cos(a), CY + r0 * math.sin(a)),
                   (CX + tip * math.cos(a), CY + tip * math.sin(a)),
                   (CX + tip * math.cos(b), CY + tip * math.sin(b)),
                   (CX + r0 * math.cos(b), CY + r0 * math.sin(b))], fill=col)
    layer = layer.filter(ImageFilter.GaussianBlur(2.4))
    layer = ImageChops.multiply(layer, falloff(1.6))   # rays die out with r
    return light_add(img, layer, 0.60)


# ------------------------------------------------- 3. shockwaves (ellipses)
def draw_shockwaves(img, count=WAVES):
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = random.Random(SEED + 7)
    for i in range(count):
        f = (i + 1) / float(count)
        rx = lerp(160.0, 700.0, f ** 0.9)
        ry = rx * rng.uniform(0.56, 0.80)              # squashed wavefront
        wid = max(2, int(round(lerp(8.0, 1.8, f))))
        v = int(round(lerp(255, 130, f ** 0.7)))
        col = (v, int(v * 0.70), int(v * 0.52))
        d.ellipse([CX - rx, CY - ry, CX + rx, CY + ry], outline=col, width=wid)
    layer = layer.filter(ImageFilter.GaussianBlur(3.2))
    layer = ImageChops.multiply(layer, falloff(2.2))
    return light_add(img, layer, 0.55)


# ------------------------------------------------- 4. blinding white core
def draw_core(img):
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    for r, v in ((235, 40), (172, 88), (122, 152), (74, 240)):
        d.ellipse([CX - r, CY - r, CX + r, CY + r], fill=(v, v, int(v * 0.93)))
    layer = layer.filter(ImageFilter.GaussianBlur(20))
    img = light_add(img, layer, 0.85)
    ImageDraw.Draw(img).ellipse([CX - 48, CY - 48, CX + 48, CY + 48],
                                fill=(255, 255, 255))
    return img


# ------------------------------- 5. THE SUBJECT: solid black pawn (drawn last)
def pawn_shapes():
    """Classic Staunton pawn, built bottom-up as bands of the total height.

    Returns primitives in absolute pixels: ("box", x0, y0, x1, y1),
    ("ell", x0, y0, x1, y1) and ("poly", [points]).
    """
    base_y = CY + PAWN_H * 0.5                 # pawn stands on y = 768
    h = float(PAWN_H)

    def y(f):                                  # f = 0 at base, 1 at head top
        return base_y - f * h

    def box(f0, f1, hw):
        return ("box", CX - hw * h, y(f1), CX + hw * h, y(f0))

    def ell(f0, f1, hw):
        return ("ell", CX - hw * h, y(f1), CX + hw * h, y(f0))

    return [
        box(0.000, 0.072, 0.300),              # foot slab (widest)
        box(0.072, 0.104, 0.268),              # bevel
        ell(0.104, 0.166, 0.236),              # collar ring (convex)
        ("poly", [(CX - 0.200 * h, y(0.150)), (CX - 0.100 * h, y(0.618)),
                  (CX + 0.100 * h, y(0.618)), (CX + 0.200 * h, y(0.150))]),
        ell(0.598, 0.668, 0.146),              # neck flare
        ell(0.632, 1.000, 0.186),              # round head
    ]


def stamp(mask, fill=255):
    d = ImageDraw.Draw(mask)
    for s in pawn_shapes():
        if s[0] == "box":
            d.rectangle(list(s[1:]), fill=fill)
        elif s[0] == "ell":
            d.ellipse(list(s[1:]), fill=fill)
        else:
            d.polygon(s[1], fill=fill)
    return mask


def draw_pawn(img):
    """Cream rim light, then a hard-edged pitch-black silhouette on top."""
    solid = stamp(Image.new("L", (W, H), 0))

    # (a) wide soft halo so the pawn lifts off the background
    glow = solid.filter(ImageFilter.GaussianBlur(15))
    img = Image.composite(Image.new("RGB", (W, H), (255, 236, 198)), img,
                          glow.point(lambda v: int(v * 0.80)))

    # (b) tight rim light: dilate a little then blur -> thin bright outline
    rim = solid.filter(ImageFilter.MaxFilter(7))
    rim = rim.filter(ImageFilter.GaussianBlur(3))
    img = Image.composite(Image.new("RGB", (W, H), (255, 250, 234)), img,
                          rim.point(lambda v: int(v * 0.95)))

    # (c) the subject itself: pure black, no blur, hard edge
    return Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, solid)


# ------------------------------------------------- 6. caption band + type
def draw_band(img):
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(30):                        # soft lip instead of a knife cut
        a = int(238 * (1.0 - i / 30.0) ** 1.7 * 0.6)
        d.rectangle([0, BAND_Y - i - 1, W, BAND_Y - i], fill=(5, 4, 8, a))
    d.rectangle([0, BAND_Y, W, H], fill=(5, 4, 8, 238))

    big = ImageFont.truetype(FONT_BOLD, 118)
    small = ImageFont.truetype(FONT_REG, 40)
    d.text((CX, BAND_Y + 96), "11:59:59", font=big,
           fill=(255, 246, 232), anchor="mm")
    d.text((CX, BAND_Y + 182), "the last second is the loudest", font=small,
           fill=(188, 178, 198), anchor="mm")
    return img


# ---------------------------------------------------------------- driver
def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
    img = build_background()          # 1. radial gradient
    img = draw_rays(img)              # 2. ~80 rays
    img = draw_shockwaves(img)        # 3. 5 shockwave ellipses
    img = draw_core(img)              # 4. white-hot core
    img = vignette(img)               # 5. darken the frame's rim
    img = draw_pawn(img)              # 6. subject, after every light layer
    img = draw_band(img)              # 7. caption band + type
    img.convert("RGB").save(out, "PNG", optimize=True)
    print("wrote %s" % out)


if __name__ == "__main__":
    main()
