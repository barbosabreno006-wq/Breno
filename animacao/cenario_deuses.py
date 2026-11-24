#!/usr/bin/env python3
"""Cenários de "Os Quatro Deuses": montanha sagrada, mesa dos deuses, auras e símbolos (sol, lua, trevo, ampulheta)."""
import math

from PIL import Image, ImageDraw

import video_carta as vc
from gerar_video import WW, WH, Pincel, gradiente, brilho

_C = {}

COR = {"sol": (255, 200, 60), "lua": (150, 170, 255), "trevo": (90, 210, 120), "fim": (190, 190, 205)}


def simbolo(tipo, w=200):
    """Símbolo de cada deus: sol, lua, trevo ou ampulheta (fim)."""
    k = ("simb", tipo, w)
    if k in _C:
        return _C[k]
    p = Pincel(240, 240)
    if tipo == "sol":
        for a in range(0, 360, 30):
            r = math.radians(a)
            p.linha([(120 + 64 * math.cos(r), 120 + 64 * math.sin(r)), (120 + 106 * math.cos(r), 120 + 106 * math.sin(r))],
                    fill=(250, 190, 40), w=12)
        p.elipse((60, 60, 180, 180), (255, 214, 70))
    elif tipo == "lua":
        p.elipse((50, 40, 200, 190), (214, 220, 255))
        p.elipse((100, 20, 220, 150), (30, 36, 80), ow=0)
    elif tipo == "trevo":
        for dx, dy in ((-34, -34), (34, -34), (-34, 34), (34, 34)):
            p.elipse((120 + dx - 40, 120 + dy - 40, 120 + dx + 40, 120 + dy + 40), (80, 200, 110))
        p.linha([(120, 130), (140, 220)], fill=(40, 120, 70), w=10)
    else:
        p.poli([(60, 30), (180, 30), (120, 120)], (230, 226, 240))
        p.poli([(60, 210), (180, 210), (120, 120)], (230, 226, 240))
        p.ret((50, 20, 190, 40), (120, 110, 130), r=4)
        p.ret((50, 200, 190, 220), (120, 110, 130), r=4)
        p.poli([(90, 190), (150, 190), (120, 160)], (190, 150, 90), ow=0)
    im = p.pronto()
    _C[k] = im if w == 240 else im.resize((w, w), Image.BICUBIC)
    return _C[k]


def aura(m, x, y, tipo, raio=380, forca=0.55):
    m.alpha_composite(brilho((raio * 2, raio * 2), COR[tipo], raio, forca), (int(x - raio), int(y - raio)))


def montanha(fc, hora="dia"):
    """Topo da montanha sagrada: céu, picos, chão de pedra, mesa de pedra redonda ao fundo."""
    k = ("mont", hora)
    if k in _C:
        return _C[k]
    topo, base_ = ((120, 170, 240), (255, 226, 180)) if hora == "dia" else ((40, 36, 90), (150, 90, 130))
    if hora == "poente":
        topo, base_ = ((240, 150, 110), (255, 220, 160))
    img = gradiente(WW, WH, topo, base_)
    p = Pincel(WW, WH)
    p.poli([(-20, 1200), (260, 760), (480, 1100), (760, 640), (1100, 1180), (1100, 1500), (-20, 1500)], (120, 126, 150))
    p.poli([(260, 760), (330, 880), (220, 880)], (250, 250, 255), ow=4)
    p.poli([(760, 640), (850, 800), (680, 800)], (250, 250, 255), ow=4)
    p.ret((-20, 1480, WW + 20, WH + 20), (150, 150, 168), r=0, ow=0)
    p.elipse((160, 1340, 920, 1560), (170, 172, 190))                              # mesa de pedra
    p.ret((460, 1480, 620, 1620), (140, 142, 160), r=6)
    img.alpha_composite(p.pronto())
    _C[k] = img
    return img


def aldeia(fc):
    k = "aldeia"
    if k in _C:
        return _C[k]
    img = gradiente(WW, WH, (150, 200, 245), (255, 236, 200))
    p = Pincel(WW, WH)
    p.ret((-20, 1480, WW + 20, WH + 20), (150, 200, 120), r=0, ow=0)
    for x, c in ((60, (230, 170, 120)), (380, (200, 140, 160)), (700, (170, 190, 230))):
        p.ret((x, 1000, x + 300, 1480), c, r=8)
        p.poli([(x - 20, 1010), (x + 150, 840), (x + 320, 1010)], (190, 90, 80))
        p.ret((x + 110, 1260, x + 190, 1480), (120, 80, 60), r=6)
    img.alpha_composite(p.pronto())
    _C[k] = img
    return img


def estrelas(m, t, n=40, seed=3):
    import random
    rng = random.Random(seed)
    d = ImageDraw.Draw(m, "RGBA")
    for _ in range(n):
        x, y = rng.uniform(0, WW), rng.uniform(0, WH * 0.55)
        a = int(120 + 120 * math.sin(t * 2 + x))
        r = rng.uniform(2, 5)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 230, max(40, a)))


def correntes(m, x, y, quebrada=0.0):
    """Elos de corrente em volta do peito (quebram com quebrada 0-1)."""
    d = ImageDraw.Draw(m, "RGBA")
    for i in range(7):
        dx = (i - 3) * 38
        off = quebrada * (40 + 30 * (i % 2)) * (1 if dx >= 0 else -1)
        d.ellipse((x + dx - 18 + off, y - 12 + abs(dx) * 0.2 - quebrada * 60, x + dx + 18 + off,
                   y + 12 + abs(dx) * 0.2 - quebrada * 60), outline=(70, 70, 82, 255), width=7)
