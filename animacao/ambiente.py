#!/usr/bin/env python3
"""
Vida no cenário: elementos animados que fazem o fundo nunca ficar parado
(nuvens, pássaros, folhas, vagalumes, raios de luz, gente andando ao fundo).

Todas as funções desenham direto no "mundo" (RGBA WW x WH) e dependem só do tempo t.
"""
import math
import random

from PIL import Image, ImageDraw

from gerar_video import WW, WH, Pincel, brilho

_C = {}


def nuvens(m, t, y0=170, n=4, seed=1, vel=16, cor=(255, 255, 255), alpha=215, escala=1.0):
    rng = random.Random(seed)
    for i in range(n):
        w = rng.randint(260, 420) * escala
        y = y0 + rng.randint(-60, 140)
        x = (rng.uniform(0, WW + 500) + t * vel * rng.uniform(0.6, 1.4)) % (WW + 500) - 300
        k = ("nuvem", int(w))
        if k not in _C:
            p = Pincel(int(w) + 40, int(w * 0.5) + 40)
            p.elipse((20, w * 0.18, 20 + w * 0.5, 20 + w * 0.42), (255, 255, 255), ow=0)
            p.elipse((20 + w * 0.25, 20, 20 + w * 0.75, 20 + w * 0.46), (255, 255, 255), ow=0)
            p.elipse((20 + w * 0.5, w * 0.16, 20 + w, 20 + w * 0.42), (255, 255, 255), ow=0)
            _C[k] = p.pronto()
        img = _C[k].copy()
        if alpha < 255:
            img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha / 255)))
        if cor != (255, 255, 255):
            tint = Image.new("RGBA", img.size, cor + (0,))
            tint.putalpha(img.getchannel("A"))
            img = tint
        m.alpha_composite(img, (int(x), int(y)))


def passaros(m, t, n=4, seed=2, y0=330, vel=90):
    rng = random.Random(seed)
    d = ImageDraw.Draw(m)
    for i in range(n):
        x = (rng.uniform(0, WW + 300) + t * vel * rng.uniform(0.7, 1.2)) % (WW + 300) - 150
        y = y0 + rng.uniform(-80, 120) + 20 * math.sin(t * 1.3 + i)
        s = rng.uniform(0.8, 1.3)
        flap = math.sin(t * 9 + i * 2)
        for sx in (-1, 1):
            d.line((x, y, x + sx * 30 * s, y - (14 + 12 * flap) * s), fill=(43, 40, 58, 255), width=5)
            d.line((x + sx * 30 * s, y - (14 + 12 * flap) * s, x + sx * 52 * s, y + (4 - 6 * flap) * s),
                   fill=(43, 40, 58, 255), width=5)


def folhas(m, t, n=10, seed=3, cor=(120, 175, 80), vento=40):
    rng = random.Random(seed)
    d = ImageDraw.Draw(m)
    for i in range(n):
        x0 = rng.uniform(0, WW)
        vy = rng.uniform(90, 170)
        y = (rng.uniform(0, WH) + t * vy) % (WH + 100) - 50
        x = x0 + vento * math.sin(t * 1.1 + i) + t * 25
        x = x % (WW + 60) - 30
        a = t * 3 + i
        r = rng.randint(9, 15)
        pts = [(x + r * math.cos(a), y + r * 0.5 * math.sin(a)), (x + r * 1.7 * math.cos(a + 2), y + r * 0.6 * math.sin(a + 2)),
               (x + r * math.cos(a + 4), y + r * 0.5 * math.sin(a + 4))]
        c = tuple(max(0, min(255, int(v + rng.randint(-25, 25)))) for v in cor)
        d.polygon(pts, fill=c + (235,))


def vagalumes(m, t, n=20, seed=4, cor=(255, 240, 150)):
    rng = random.Random(seed)
    for i in range(n):
        bx, by = rng.uniform(0, WW), rng.uniform(900, 1650)
        x = bx + 70 * math.sin(t * rng.uniform(0.4, 0.9) + i)
        y = by + 50 * math.cos(t * rng.uniform(0.5, 1.0) + i * 2)
        pulso = 0.4 + 0.6 * abs(math.sin(t * rng.uniform(1.2, 2.2) + i))
        r = 22
        m.alpha_composite(brilho((r * 4, r * 4), cor, r * 2, pulso), (int(x - r * 2), int(y - r * 2)))


def raios_luz(m, t, cor=(255, 240, 190), alpha=40, n=4):
    p = Pincel(WW, WH)
    for i in range(n):
        x0 = 120 + i * 260 + 40 * math.sin(t * 0.4 + i)
        p.poli([(x0, -20), (x0 + 120, -20), (x0 + 520, 1500), (x0 + 240, 1500)], cor, ow=0)
    img = p.pronto()
    img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha / 255)))
    m.alpha_composite(img)


def gente_fundo(m, t, pers, y=1385, escala=0.36, n=3, seed=5, vel=70, filme_t=None):
    """Gente miúda andando ao fundo (profundidade e movimento).  pers: lista de Pers/Boneco chamáveis."""
    rng = random.Random(seed)
    for i in range(n):
        p = pers[i % len(pers)]
        sentido = 1 if i % 2 == 0 else -1
        x = (rng.uniform(0, WW + 400) + sentido * t * vel * rng.uniform(0.7, 1.2)) % (WW + 400) - 200
        p(m, t + i * 0.7, x, y + (i % 2) * 22, escala, expr="neutro", pose="anda", sx=sentido)
