#!/usr/bin/env python3
"""Cenários de "A Porta do Porão": corredor com a porta, porão, mesa posta, rádio, fita cassete, caminhão, retrato,
máquina de lavar, notas musicais e vapor."""
import math

from PIL import Image, ImageDraw

import video_carta as vc
import cenario_escola as cs
from gerar_video import WW, WH, Pincel, gradiente, brilho

_C = {}


def _p_piso(p, y=1500, cor=(150, 112, 80)):
    p.ret((-20, y, WW + 20, WH + 20), cor, r=0, ow=0)


def corredor_porta(fc, luz=False, chave=True):
    """Parede com a porta de madeira do porão (chave pendurada na fechadura); luz = brilho por baixo da porta."""
    k = ("porta", luz, chave)
    if k in _C:
        return _C[k]
    base = gradiente(WW, WH, (232, 206, 150), (206, 176, 120))
    p = Pincel(WW, WH)
    _p_piso(p, 1540, (140, 96, 70))
    p.ret((300, 420, 780, 1540), (120, 78, 52), r=14, ow=10)
    p.ret((340, 470, 740, 900), (138, 94, 64), r=8, ow=6)
    p.ret((340, 960, 740, 1490), (138, 94, 64), r=8, ow=6)
    p.elipse((690, 1010, 730, 1050), (230, 190, 70))                                   # maçaneta
    p.ret((680, 1060, 740, 1110), (200, 160, 50), r=6)                                 # fechadura
    p.ret((60, 520, 240, 800), (176, 216, 240), r=6, ow=8)                             # janelinha
    p.ret((830, 460, 1000, 640), (200, 120, 90), r=6, ow=6)                            # quadro
    base.alpha_composite(p.pronto())
    if luz:
        base.alpha_composite(brilho((520, 200), (255, 226, 140), 240, 0.8), (280, 1470))
    if chave:
        d = ImageDraw.Draw(base)
        d.ellipse((704, 1100, 734, 1130), outline=(40, 30, 20, 255), width=6, fill=(230, 190, 70, 255))
    _C[k] = base
    return base


def porao(fc):
    if "porao" in _C:
        return _C["porao"]
    base = gradiente(WW, WH, (52, 40, 40), (22, 16, 20))
    p = Pincel(WW, WH)
    _p_piso(p, 1480, (62, 48, 44))
    for i in range(7):                                                                  # escada à esquerda
        p.ret((20 + i * 70, 300 + i * 120, 140 + i * 70, 340 + i * 120), (120, 90, 64), r=0)
    p.ret((560, 180, 600, 420), (70, 60, 56), r=0, ow=4)
    p.elipse((520, 380, 640, 470), (250, 224, 140), ow=6)                              # lâmpada
    p.ret((700, 700, 1000, 1000), (92, 80, 74), r=6, ow=6)                             # prateleira
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((900, 900), (255, 214, 120), 380, 0.55), (90, 340))
    _C["porao"] = base
    return base


def mesa_posta(fc, n=2):
    """Mesa de toalha xadrez com n pratos; devolve fundo + posições dos pratos (x)."""
    k = ("mesa", n)
    if k in _C:
        return _C[k]
    base = porao(fc).copy()
    p = Pincel(WW, WH)
    p.ret((120, 1180, 960, 1250), (226, 90, 80), r=10)                                  # toalha
    for x in range(140, 940, 60):
        p.ret((x, 1180, x + 30, 1250), (250, 220, 210), r=0, ow=0)
    p.ret((200, 1250, 250, 1520), (96, 68, 50), r=4)
    p.ret((830, 1250, 880, 1520), (96, 68, 50), r=4)
    xs = [320, 760] if n == 2 else [220, 540, 860]
    for x in xs:
        p.elipse((x - 90, 1120, x + 90, 1200), (250, 250, 252))
        p.elipse((x - 54, 1136, x + 54, 1184), (236, 200, 140), ow=0)
    for x in xs:                                                                        # cadeiras
        p.ret((x - 70, 1000, x + 70, 1030), (150, 106, 70), r=6)
        p.ret((x - 60, 1030, x - 40, 1260), (120, 84, 56), r=2)
        p.ret((x + 40, 1030, x + 60, 1260), (120, 84, 56), r=2)
    base.alpha_composite(p.pronto())
    out = (base, xs)
    _C[k] = out
    return out


def vapor(m, t, x, y, n=5):
    d = ImageDraw.Draw(m, "RGBA")
    for i in range(n):
        ph = (t * 0.6 + i / n) % 1.0
        xx = x + math.sin(ph * 7 + i) * 18
        yy = y - ph * 160
        r = 14 + ph * 22
        a = int(160 * (1 - ph))
        d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=(255, 255, 255, a))


def notas(m, t, x, y, n=4, cor=(255, 230, 120)):
    d = ImageDraw.Draw(m, "RGBA")
    for i in range(n):
        ph = (t * 0.4 + i / n) % 1.0
        xx = x + math.sin(ph * 6 + i * 2) * 50 + (i - n / 2) * 60
        yy = y - ph * 220
        a = int(255 * min(1, ph * 5, (1 - ph) * 2.5))
        d.ellipse((xx - 14, yy - 10, xx + 10, yy + 10), fill=cor + (a,))
        d.line((xx + 9, yy, xx + 9, yy - 50), fill=cor + (a,), width=5)
        d.line((xx + 9, yy - 50, xx + 28, yy - 38), fill=cor + (a,), width=5)


def radio(w=520):
    if ("radio", w) not in _C:
        p = Pincel(520, 340)
        p.ret((10, 30, 510, 330), (160, 100, 60), r=34)
        p.ret((40, 70, 330, 290), (226, 196, 140), r=18)
        for i in range(8):
            p.linha([(60, 100 + i * 24), (310, 100 + i * 24)], fill=(120, 90, 50), w=4)
        p.elipse((360, 90, 450, 180), (230, 200, 120))
        p.elipse((360, 200, 450, 290), (230, 200, 120))
        p.linha([(405, 100), (405, 140)], w=5)
        p.linha([(150, 30), (260, 0)], w=5)
        _C[("radio", w)] = p.pronto().resize((w, int(340 * w / 520)), Image.BICUBIC)
    return _C[("radio", w)]


def fita(w=520, giro=0.0):
    p = Pincel(520, 340)
    p.ret((10, 20, 510, 320), (60, 60, 72), r=20)
    p.ret((60, 60, 460, 200), (226, 220, 200), r=10)
    for cx in (160, 360):
        p.elipse((cx - 44, 90, cx + 44, 178), (250, 250, 250))
    p.ret((130, 240, 390, 300), (90, 90, 104), r=10)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    for cx in (160, 360):
        for a in range(3):
            ang = giro + a * 2.094
            d.line((cx, 134, cx + 30 * math.cos(ang), 134 + 30 * math.sin(ang)), fill=(40, 40, 50, 255), width=6)
    return im if w == 520 else im.resize((w, int(340 * w / 520)), Image.BICUBIC)


def caminhao(w=900):
    if ("cam", w) not in _C:
        p = Pincel(900, 460)
        p.ret((20, 100, 560, 360), (70, 120, 190), r=14)
        p.ret((560, 170, 860, 360), (230, 90, 70), r=30)
        p.ret((620, 190, 780, 280), (176, 216, 240), r=12)
        p.elipse((100, 310, 230, 440), (36, 36, 44))
        p.elipse((330, 310, 460, 440), (36, 36, 44))
        p.elipse((640, 310, 770, 440), (36, 36, 44))
        _C[("cam", w)] = p.pronto().resize((w, int(460 * w / 900)), Image.BICUBIC)
    return _C[("cam", w)]


def retrato(fc, pal, w=520):
    """Retrato emoldurado do avô."""
    p = Pincel(520, 640)
    p.ret((10, 10, 510, 630), (150, 100, 56), r=14, ow=8)
    p.ret((50, 50, 470, 590), (236, 224, 196), r=6, ow=4)
    im = p.pronto()
    fig = cs._fig(pal, "feliz", 0.7)
    fig = fig.resize((int(fig.width * 0.8), int(fig.height * 0.8)), Image.BICUBIC)
    im.alpha_composite(fig, (260 - fig.width // 2, 590 - fig.height))
    return im if w == 520 else im.resize((w, int(640 * w / 520)), Image.BICUBIC)


def maquina_lavar(w=520):
    if ("lav", w) not in _C:
        p = Pincel(520, 640)
        p.ret((10, 10, 510, 630), (240, 244, 248), r=24)
        p.elipse((110, 150, 410, 450), (176, 196, 220))
        p.elipse((150, 190, 370, 410), (120, 150, 190), ow=6)
        p.ret((50, 40, 470, 100), (200, 210, 224), r=10)
        p.elipse((80, 56, 112, 88), (230, 80, 70), ow=3)
        _C[("lav", w)] = p.pronto().resize((w, int(640 * w / 520)), Image.BICUBIC)
    return _C[("lav", w)]


def panela(w=300):
    p = Pincel(300, 220)
    p.ret((30, 70, 250, 190), (190, 190, 200), r=14)
    p.ret((10, 90, 40, 110), (60, 60, 70), r=4)
    p.ret((260, 90, 290, 110), (60, 60, 70), r=4)
    p.ret((60, 40, 220, 80), (210, 210, 220), r=10)
    return p.pronto() if w == 300 else p.pronto().resize((w, int(220 * w / 300)), Image.BICUBIC)


def relogio_parede(fc, hh=6, mm=0, w=400):
    from cenario_apagador import relogio_torre
    return relogio_torre(fc, hh, mm, w)


def sepia(img, k=0.6):
    """Tom de lembrança (sépia) em uma imagem RGB."""
    from PIL import ImageOps
    g = ImageOps.colorize(img.convert("L"), (40, 24, 12), (255, 232, 190))
    return Image.blend(img.convert("RGB"), g, k)
