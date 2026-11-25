#!/usr/bin/env python3
"""Props de "Eu Dou Uma Todo Dia": pão, tabuleiro de pães, forno, saco de farinha, envelopes, arma de brinquedo,
poste, folha com bilhete antigo, padaria ao amanhecer."""
import math

from PIL import Image, ImageDraw

import video_carta as vc
from gerar_video import WW, WH, Pincel, gradiente, brilho

_C = {}


def pao(w=300, estilo=0):
    k = ("pao", w, estilo)
    if k not in _C:
        p = Pincel(300, 220)
        cor = (226, 160, 80) if estilo == 0 else (214, 140, 66)
        p.elipse((20, 50, 280, 200), cor)
        for i in range(3):
            p.linha([(80 + i * 60, 80), (110 + i * 60, 40 + 110 * 0 + 60)], fill=(160, 100, 40), w=8)
        p.elipse((60, 70, 150, 110), (250, 210, 140), ow=0)
        _C[k] = p.pronto().resize((w, int(220 * w / 300)), Image.BICUBIC)
    return _C[k]


def tabuleiro(w=900, n=6):
    k = ("tab", w, n)
    if k not in _C:
        p = Pincel(900, 420)
        p.ret((20, 280, 880, 330), (150, 150, 162), r=10)
        p.ret((60, 330, 100, 410), (110, 110, 124), r=4)
        p.ret((800, 330, 840, 410), (110, 110, 124), r=4)
        im = p.pronto()
        for i in range(n):
            pn = pao(190, i % 2)
            im.alpha_composite(pn, (40 + i * 135, 170 - (i % 2) * 20))
        _C[k] = im.resize((w, int(420 * w / 900)), Image.BICUBIC)
    return _C[k]


def forno(fc, t=0.0, w=900):
    p = Pincel(900, 800)
    p.ret((10, 40, 890, 790), (170, 90, 60), r=24)
    p.ret((70, 140, 830, 640), (50, 30, 26), r=18)
    p.ret((110, 180, 790, 600), (255, 150, 50), r=10, ow=0)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    for i in range(4):
        x = 150 + i * 170
        d.ellipse((x, 400, x + 130, 520), fill=(226, 160, 80, 255), outline=(60, 30, 20, 255), width=6)
    d.rectangle((110, 180, 790, 260), fill=(255, 200, 80, 120))
    f = vc.fonte(fc, 44)
    d.text((450 - f.getlength("FORNO") / 2, 670), "FORNO", font=f, fill=(255, 240, 220))
    glow = brilho((1100, 900), (255, 160, 60), 480, 0.35 + 0.1 * math.sin(t * 6))
    glow.alpha_composite(im, (100, 50))
    return glow if w == 900 else glow.resize((w, int(900 * w / 900)), Image.BICUBIC)


def saco_farinha(fc, w=520):
    p = Pincel(520, 640)
    p.poli([(60, 90), (460, 90), (500, 600), (20, 600)], (246, 240, 226))
    p.ret((60, 40, 460, 110), (226, 218, 200), r=8)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    f1, f2 = vc.fonte(fc, 72), vc.fonte(fc, 44)
    d.text((260 - f1.getlength("FARINHA") / 2, 220), "FARINHA", font=f1, fill=(170, 60, 50))
    d.text((260 - f2.getlength("25 kg") / 2, 330), "25 kg", font=f2, fill=(90, 80, 70))
    return im if w == 520 else im.resize((w, int(640 * w / 520)), Image.BICUBIC)


def envelope(w=520, aberto=False):
    p = Pincel(520, 360)
    p.ret((10, 20, 510, 350), (250, 244, 226), r=14)
    p.poli([(10, 20), (260, 220), (510, 20)], (236, 226, 200))
    im = p.pronto()
    return im if w == 520 else im.resize((w, int(360 * w / 520)), Image.BICUBIC)


def envelopes(n=8, w=900):
    k = ("envs", n, w)
    if k not in _C:
        im = Image.new("RGBA", (900, 700), (0, 0, 0, 0))
        for i in range(n):
            e = envelope(380).rotate((i * 37) % 30 - 15, expand=True, resample=Image.BICUBIC)
            im.alpha_composite(e, (60 + (i % 3) * 190, 40 + (i // 3) * 150))
        _C[k] = im.resize((w, int(700 * w / 900)), Image.BICUBIC)
    return _C[k]


def bilhete(fc, w=760, ate=1.0):
    p = Pincel(760, 560)
    p.ret((10, 10, 750, 550), (246, 236, 206), r=10)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    f = vc.fonte(fc, 52)
    linhas = ("Desculpa pelo roubo.", "Eu estava com fome.")
    n = int(sum(len(s) for s in linhas) * max(0.0, min(1.0, ate)))
    for i, s in enumerate(linhas):
        k = min(len(s), n)
        d.text((50 + (i % 2) * 10, 150 + i * 110), s[:k], font=f, fill=(60, 50, 120))
        n -= k
        if n <= 0:
            break
    f2 = vc.fonte(fc, 28)
    d.text((50, 40), "8 anos atrás", font=f2, fill=(120, 110, 90))
    return im if w == 760 else im.resize((w, int(560 * w / 760)), Image.BICUBIC)


def arma_brinquedo(w=420):
    p = Pincel(420, 300)
    p.ret((40, 60, 340, 150), (230, 70, 80), r=18)
    p.ret((120, 140, 210, 270), (210, 60, 70), r=14)
    p.ret((330, 76, 400, 120), (250, 220, 70), r=8)
    return p.pronto() if w == 420 else p.pronto().resize((w, int(300 * w / 420)), Image.BICUBIC)


def poste(w=260, h=1200):
    p = Pincel(260, h)
    p.ret((100, 100, 160, h - 10), (70, 74, 92), r=8)
    p.ret((60, 40, 200, 120), (90, 94, 112), r=14)
    return p.pronto() if w == 260 else p.pronto().resize((w, int(h * w / 260)), Image.BICUBIC)


def padaria_alvorada(fc):
    """Fachada da padaria ao amanhecer: céu rosa-laranja, janela acesa, portas abertas (cores vivas)."""
    if "alv" in _C:
        return _C["alv"]
    img = gradiente(WW, WH, (255, 150, 110), (255, 226, 160))
    p = Pincel(WW, WH)
    p.ret((-20, 1500, WW + 20, WH + 20), (120, 120, 140), r=0, ow=0)
    p.ret((60, 520, 1020, 1500), (240, 190, 120), r=8)
    p.ret((60, 400, 1020, 540), (210, 70, 60), r=8)
    p.ret((140, 700, 480, 1300), (255, 236, 150), r=10, ow=8)
    p.ret((600, 800, 940, 1500), (120, 70, 50), r=10, ow=8)
    img.alpha_composite(p.pronto())
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 74)
    d.text((540 - f.getlength("PADARIA") / 2, 424), "PADARIA", font=f, fill=(255, 255, 255))
    img.alpha_composite(brilho((600, 700), (255, 240, 160), 260, 0.6), (-10, 560))
    _C["alv"] = img
    return img


def rua_noite_poste(fc):
    if "rnp" in _C:
        return _C["rnp"]
    img = gradiente(WW, WH, (40, 40, 96), (16, 16, 44))
    p = Pincel(WW, WH)
    p.ret((-20, 1480, WW + 20, WH + 20), (50, 54, 70), r=0, ow=0)
    p.ret((80, 640, 560, 1480), (90, 80, 120), r=8)
    p.ret((620, 700, 1020, 1480), (110, 90, 130), r=8)
    for x, y in ((140, 780), (260, 780), (380, 780), (680, 840), (800, 840)):
        p.ret((x, y, x + 70, y + 90), (255, 224, 140), r=4, ow=4)
    img.alpha_composite(p.pronto())
    img.alpha_composite(brilho((600, 600), (255, 230, 150), 260, 0.55), (660, 420))
    _C["rnp"] = img
    return img


def padaria_interior(fc):
    if "pint" in _C:
        return _C["pint"]
    img = gradiente(WW, WH, (252, 230, 190), (236, 204, 158))
    pc = Pincel(WW, WH)
    pc.ret((-20, 1500, WW + 20, WH + 20), (176, 130, 96), r=0, ow=0)
    pc.ret((60, 300, 1020, 400), (200, 70, 60), r=10)
    for x in (90, 190, 290, 390, 700, 800, 900):
        pc.ret((x, 480, x + 70, 700), (240, 190, 90), r=26)
    pc.ret((60, 1180, 1020, 1500), (150, 100, 66), r=8)
    pc.ret((60, 1150, 1020, 1210), (200, 150, 100), r=8)
    img.alpha_composite(pc.pronto())
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 52)
    d.text((540 - f.getlength("PADARIA DO RAIMUNDO") / 2, 316), "PADARIA DO RAIMUNDO", font=f, fill=(255, 255, 255))
    _C["pint"] = img
    return img
