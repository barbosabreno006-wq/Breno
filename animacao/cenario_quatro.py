#!/usr/bin/env python3
"""Props de "De Quatro no Quarto": aliança, gaveta, foto do casal, feixe de lanterna, quarto com cama."""
import math

from PIL import Image, ImageDraw

import cenario_escola as cs
from gerar_video import WW, WH, Pincel, gradiente, brilho

_C = {}


def alianca(w=300, brilho_=0.0):
    k = ("alianca", w, round(brilho_, 1))
    if k not in _C:
        p = Pincel(300, 300)
        p.elipse((40, 60, 260, 260), (252, 208, 72), ow=10)
        p.elipse((86, 106, 214, 214), (60, 50, 60, 0), ow=8)
        im = p.pronto()
        d = ImageDraw.Draw(im)
        d.ellipse((92, 112, 208, 208), fill=(0, 0, 0, 0))
        d.ellipse((70, 76, 120, 108), fill=(255, 250, 200, 220))
        im = im.resize((w, w), Image.BICUBIC)
        if brilho_ > 0:
            g_ = brilho((w * 2, w * 2), (255, 240, 160), w * 0.9, 0.5 * brilho_)
            g_.alpha_composite(im, (w // 2, w // 2))
            im = g_
        _C[k] = im
    return _C[k]


def gaveta(fc, aberta=True, w=800):
    k = ("gaveta", aberta, w)
    if k not in _C:
        p = Pincel(800, 520)
        p.ret((10, 90, 790, 510), (150, 100, 62), r=14)
        p.ret((60, 140, 740, 470), (110, 72, 44) if aberta else (170, 120, 80), r=8)
        p.ret((340, 110, 460, 140), (220, 190, 110), r=10)
        if aberta:
            p.ret((60, 140, 740, 220), (60, 40, 30), r=6, ow=0)
        _C[k] = p.pronto().resize((w, int(520 * w / 800)), Image.BICUBIC)
    return _C[k]


def foto_casal(fc, pal_h, pal_m, w=700):
    p = Pincel(360, 300)
    p.ret((0, 0, 360, 300), (236, 214, 190), r=0, ow=0)
    im = p.pronto()
    for pal, x in ((pal_h, 110), (pal_m, 250)):
        f_ = cs._fig(pal, "feliz", 0.5)
        im.alpha_composite(f_, (x - f_.width // 2, 300 - f_.height + 10))
    return cs.polaroid(fc, im, "38 ANOS JUNTOS", w)


def feixe(m, x, y, ang=-70, comp=520, larg=140):
    """Feixe de lanterna saindo de (x, y)."""
    ov = Image.new("RGBA", m.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    a = math.radians(ang)
    a1, a2 = a - math.radians(14), a + math.radians(14)
    d.polygon([(x, y), (x + comp * math.cos(a1), y + comp * math.sin(a1)), (x + comp * math.cos(a2), y + comp * math.sin(a2))],
              fill=(255, 240, 170, 110))
    m.alpha_composite(ov)
