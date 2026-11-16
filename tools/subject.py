"""Subjek: bidak pion hitam di inti ledakan putih.

Ide: bagian terkecil di jantung ledakan terbesar -> kontras maksimum, terbaca
di 300px, dan punya "twist" (bukan ledakan stok).
"""
import math

from PIL import Image, ImageDraw

W = H = 1024
CX = CY = 512


def pawn_mask(scale=1.0, dx=0, dy=0):
    """Siluet pion: kepala bulat + badan + alas. Kembalikan mask 'L'."""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    s = scale
    x = CX + dx
    y = CY + dy
    # kepala
    r = 118 * s
    d.ellipse([x - r, y - 300 * s - r, x + r, y - 300 * s + r], fill=255)
    # leher
    d.polygon([(x - 46 * s, y - 300 * s + 40 * s), (x + 46 * s, y - 300 * s + 40 * s)],
              fill=255)
    d.rectangle([x - 52 * s, y - 300 * s + 20 * s, x + 52 * s, y - 180 * s], fill=255)
    # badan (kerucut)
    d.polygon([(x - 52 * s, y - 190 * s), (x + 52 * s, y - 190 * s),
               (x + 132 * s, y + 120 * s), (x - 132 * s, y + 120 * s)], fill=255)
    # alas
    d.rectangle([x - 160 * s, y + 110 * s, x + 160 * s, y + 168 * s], fill=255)
    d.ellipse([x - 175 * s, y + 148 * s, x + 175 * s, y + 196 * s], fill=255)
    return m


def stamp_pawn(img, mask, color=(8, 4, 12), blur=0.0):
    """Tempel siluet berwarna ke gambar lewat mask."""
    layer = Image.new("RGB", (W, H), color)
    if blur > 0:
        mask = mask.filter(__import__("PIL.ImageFilter", fromlist=["ImageFilter"])
                           .GaussianBlur(blur))
    return Image.composite(layer, img, mask)


def rim_light(img, mask, color=(255, 245, 220), width=4):
    """Garis tepi terang di siluet -> terpisah dari latar, tetap terbaca kecil."""
    from PIL import ImageChops, ImageFilter
    dil = mask.filter(ImageFilter.MaxFilter(2 * width + 1))
    ring = ImageChops.subtract(dil, mask)
    ring = ring.filter(ImageFilter.GaussianBlur(1.2))
    layer = Image.new("RGB", (W, H), color)
    return Image.composite(layer, img, ring)
