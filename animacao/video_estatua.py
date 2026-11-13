#!/usr/bin/env python3
"""
"Estátua" — mundo onde quem ouve "estátua" congela de verdade.

Versão caprichada, com:
  * onda de congelamento (anel de choque + cor fria) e onda de descongelar (cor volta)
  * personagens congelados com tom de gelo e sem respiração/piscada (vivos continuam se mexendo)
  * boca sincronizada com o volume da voz nas falas (lip-sync por amplitude)
  * caminhada com perna alternada, pose ajoelhada no pedido
  * fundo desfocado nos closes (profundidade), câmera tremendo nos gritos
  * fita VHS em câmera lenta (linhas, ruído, cor deslocada, "PLAY")
  * contadores grandes na tela e silêncio total antes do "ESTÁTUA!" final

    python3 animacao/video_estatua.py --narracao narr.wav --transcricao transcricao.json --fonte Poppins.ttf
"""
import argparse
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_video as g  # noqa: E402
import video_carta as vc  # noqa: E402
import video_corsa as vco  # noqa: E402
import video_milhao as vm  # noqa: E402
import video_controle as vct  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, Ator, gradiente, brilho,
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(99)

# --------------------------------------------------------------------------
# Elenco
# --------------------------------------------------------------------------
NINA = dict(pele=(190, 130, 95), cabelo=(40, 28, 22), camisa=(250, 200, 60), calca=(0, 0, 0),
            sapato=(220, 70, 90), tipo="moca", vestido=(250, 200, 60))
ANTONIO = dict(pele=(214, 165, 128), cabelo=(220, 220, 225), camisa=(200, 185, 150), calca=(110, 90, 70),
               sapato=(80, 60, 50), tipo="vovo_h")
ANTONIO_JOVEM = dict(pele=(214, 165, 128), cabelo=(50, 36, 28), camisa=(200, 70, 60), calca=(60, 80, 130),
                     sapato=(80, 60, 50), tipo="pai")
LURDES = dict(pele=(222, 175, 140), cabelo=(70, 45, 30), camisa=(240, 120, 150), calca=(0, 0, 0),
              sapato=(150, 70, 90), tipo="moca", vestido=(240, 120, 150), tranca=True)
LURDES_NOIVA = dict(LURDES, camisa=(250, 250, 250), vestido=(250, 250, 250))
MILHO = dict(pele=(196, 140, 100), cabelo=(40, 30, 25), camisa=(60, 110, 190), calca=(70, 60, 50),
             sapato=(60, 50, 45), tipo="pai")
NOIVA = dict(pele=(235, 190, 150), cabelo=(150, 70, 40), camisa=(250, 250, 250), calca=(0, 0, 0),
             sapato=(240, 240, 240), tipo="moca", vestido=(250, 250, 250))
PADRE = dict(pele=(225, 180, 145), cabelo=(170, 170, 175), camisa=(40, 40, 45), calca=(40, 40, 45),
             sapato=(25, 25, 25), tipo="pai", bigode=False)
ZEFA = dict(pele=(176, 120, 85), cabelo=(220, 220, 225), camisa=(210, 130, 60), calca=(0, 0, 0),
            sapato=(110, 80, 60), tipo="vovo", vestido=(210, 130, 60))
DONO = dict(pele=(206, 150, 110), cabelo=(60, 45, 35), camisa=(90, 150, 110), calca=(60, 65, 80),
            sapato=(60, 50, 45), tipo="pai")
POVO = [dict(pele=(150, 100, 70), cabelo=(30, 25, 25), camisa=(240, 190, 60), calca=(60, 70, 120),
             sapato=(200, 60, 60), tipo="pai", bigode=False),
        dict(pele=(235, 190, 150), cabelo=(150, 60, 40), camisa=(220, 90, 150), calca=(0, 0, 0),
             sapato=(200, 60, 120), tipo="moca", vestido=(230, 110, 170)),
        dict(pele=(190, 130, 90), cabelo=(60, 40, 30), camisa=(120, 90, 200), calca=(80, 70, 60),
             sapato=(60, 60, 60), tipo="pai"),
        dict(pele=(176, 120, 85), cabelo=(25, 20, 20), camisa=(90, 180, 200), calca=(0, 0, 0),
             sapato=(240, 200, 60), tipo="moca", vestido=(110, 190, 210)),
        dict(pele=(230, 185, 150), cabelo=(200, 150, 60), camisa=(120, 190, 110), calca=(50, 60, 80),
             sapato=(220, 220, 220), tipo="menino")]

GRITOS = [1.94, 29.62, 62.96, 100.28, 138.62, 169.88]
DESTAQUES = {"Estátua.": (90, 180, 255), "congela.": (90, 180, 255), "congelou.": (90, 180, 255),
             "gritou.": (230, 60, 60), "papagaio,": (60, 200, 100), "problemas.": (230, 60, 60),
             "velho?": (255, 140, 40)}


# --------------------------------------------------------------------------
# Efeitos de gelo
# --------------------------------------------------------------------------
_CACHE_GELO = {}


def gelo(spr):
    k = id(spr)
    if k not in _CACHE_GELO:
        rgb = spr.convert("RGB")
        rgb = ImageEnhance.Color(rgb).enhance(0.45)
        az = Image.new("RGB", spr.size, (175, 215, 250))
        rgb = Image.blend(rgb, az, 0.38)
        out = rgb.convert("RGBA")
        out.putalpha(spr.getchannel("A"))
        p = ImageDraw.Draw(out)
        rng = random.Random(k % 9973)
        a = np.asarray(spr.getchannel("A"))
        ys, xs = np.nonzero(a > 200)
        for _ in range(40):
            if len(xs) == 0:
                break
            i = rng.randrange(len(xs))
            x, y = xs[i], ys[i]
            p.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 255, 255, 200))
        _CACHE_GELO[k] = out
    return _CACHE_GELO[k]


def tom_frio(f, k=1.0):
    a = np.asarray(f, np.float32)
    cinza = a.mean(2, keepdims=True)
    a = a * (1 - 0.45 * k) + cinza * 0.45 * k
    a = a * np.array([1 - 0.12 * k, 1 - 0.02 * k, 1 + 0.12 * k])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def onda(antes, depois, t, cx, cy, cor=(220, 240, 255), dur=0.7):
    """Transição circular: a imagem 'depois' cresce a partir de (cx, cy) com um anel de choque."""
    k = ease_out(min(1, max(0, t / dur)))
    r = k * 1500
    mask = Image.new("L", (OUT_W, OUT_H), 0)
    ImageDraw.Draw(mask).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(18))
    f = Image.composite(depois, antes, mask)
    if k < 1:
        d = ImageDraw.Draw(f, "RGBA")
        for i, w in enumerate((26, 12)):
            rr = r - i * 30
            if rr > 0:
                d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=cor + (int(200 * (1 - k)),), width=w)
    return f


def tremor(T):
    for tg in GRITOS:
        dt = T - tg
        if 0 <= dt < 0.6:
            a = 14 * (1 - dt / 0.6)
            return a * math.sin(T * 90), a * math.cos(T * 70)
    return 0.0, 0.0


def vhs(f, t, fc):
    a = np.asarray(f, np.float32)
    a[..., 0] = np.roll(a[..., 0], 4, axis=1)
    a[..., 2] = np.roll(a[..., 2], -4, axis=1)
    rng = np.random.default_rng(int(t * 30))
    a += rng.normal(0, 10, a.shape[:2])[..., None]
    a[::3] *= 0.82
    y0 = int((t * 160) % OUT_H)
    a[y0:y0 + 24] = a[y0:y0 + 24] * 0.6 + 90
    a = a * np.array([1.05, 0.98, 0.9])
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    fnt = vc.fonte(fc, 40)
    d.polygon([(40, 52), (40, 92), (72, 72)], fill=(255, 255, 255))
    d.text((84, 48), "PLAY  0,25x", font=fnt, fill=(255, 255, 255))
    d.text((40, OUT_H - 120), "JUN 24 1986", font=fnt, fill=(255, 255, 255))
    return img


# --------------------------------------------------------------------------
# Papagaio
# --------------------------------------------------------------------------
_CACHE_PAP = {}


def papagaio(velho=False, aberto=False, asas=False, w=420):
    k = (velho, aberto, asas, w)
    if k in _CACHE_PAP:
        return _CACHE_PAP[k]
    p = Pincel(w, w * 1.3)
    verde, verde2 = (60, 170, 80), (40, 130, 60)
    if asas:
        p.poli([(150, 240), (10, 120), (40, 330), (160, 360)], verde2)
        p.poli([(270, 240), (410, 120), (380, 330), (260, 360)], verde2)
        for x0, s in ((10, 1), (410, -1)):
            p.poli([(x0, 120), (x0 + 30 * s, 110), (x0 + 50 * s, 200), (x0 + 20 * s, 210)], (220, 50, 50), ow=4)
    p.poli([(180, 420), (160, 540), (210, 520), (250, 540), (240, 420)], (40, 90, 200))   # rabo
    p.elipse((120, 190, 300, 450), verde)                                                    # corpo
    p.elipse((160, 260, 260, 430), (250, 210, 60), ow=0)                                     # peito
    if not asas:
        p.chord((110, 220, 230, 420), 90, 270, verde2)
    p.elipse((140, 70, 300, 230), verde)                                                     # cabeça
    if velho:
        p.elipse((175, 70, 265, 130), (235, 175, 170), ow=4)                                  # careca
        for x in (160, 180):
            p.linha([(x, 80), (x - 10, 50)], fill=verde, w=6)
    p.elipse((170, 115, 214, 159), (255, 255, 255), ow=5)
    p.elipse((184, 126, 206, 148), OUTLINE, ow=0)
    if velho:
        p.arco((166, 108, 218, 140), 200, 340, fill=OUTLINE, w=6)                              # pálpebra caída
    # bico
    if aberto:
        p.poli([(255, 130), (330, 140), (300, 175), (262, 160)], (240, 200, 90))
        p.poli([(258, 175), (300, 190), (290, 220), (262, 200)], (220, 180, 70))
        p.elipse((268, 165, 300, 190), (150, 40, 50), ow=0)
    else:
        p.poli([(255, 130), (330, 150), (300, 205), (262, 180)], (240, 200, 90))
    for x in (180, 240):                                                                     # pés
        p.linha([(x, 440), (x, 480)], fill=(120, 120, 120), w=10)
        p.linha([(x - 16, 480), (x + 16, 480)], fill=(120, 120, 120), w=10)
    img = p.pronto()
    _CACHE_PAP[k] = img
    return img


# --------------------------------------------------------------------------
# Objetos
# --------------------------------------------------------------------------
def milho(w=110):
    p = Pincel(w, w * 2.4)
    p.elipse((10, 10, w - 10, w * 2.2), (250, 210, 60))
    for y in range(30, int(w * 2.1), 22):
        p.linha([(20, y), (w - 20, y)], fill=(220, 170, 40), w=4)
    p.poli([(10, w * 1.6), (-10, w * 2.4), (w / 2, w * 2.0)], (110, 170, 70), ow=4)
    return p.pronto()


def biscoito(w=160):
    p = Pincel(w, w)
    p.elipse((8, 8, w - 8, w - 8), (210, 150, 80))
    for (x, y) in ((50, 50), (100, 60), (70, 100), (110, 105)):
        p.elipse((x - 9, y - 9, x + 9, y + 9), (110, 70, 40), ow=0)
    return p.pronto()


def placa(fc, linhas, cor=(220, 50, 50), w=600):
    h = 120 + 70 * len(linhas)
    p = Pincel(w, h + 220)
    p.ret((w / 2 - 14, h, w / 2 + 14, h + 220), (110, 110, 115), r=6)
    p.ret((10, 10, w - 10, h), (250, 250, 250), r=22, ow=8)
    p.ret((30, 30, w - 30, 110), cor, r=14, ow=0)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f1, f2 = vc.fonte(fc, 50), vc.fonte(fc, 44)
    d.text((w / 2 - f1.getlength("PROIBIDO") / 2, 40), "PROIBIDO", font=f1, fill=(255, 255, 255))
    for i, l in enumerate(linhas):
        d.text((w / 2 - f2.getlength(l) / 2, 130 + i * 66), l, font=f2, fill=(40, 40, 50))
    return img


def fita_vhs(fc, w=520):
    p = Pincel(w, w * 0.6)
    p.ret((10, 10, w - 10, w * 0.58), (30, 30, 35), r=14)
    p.ret((60, 40, w - 60, 140), (240, 235, 210), r=8, ow=4)
    for x in (150, w - 150):
        p.elipse((x - 55, 160, x + 55, 270), (240, 240, 240), ow=5)
        p.elipse((x - 22, 193, x + 22, 237), (60, 60, 65), ow=0)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    d.text((80, 60), "FESTA 1986", font=vc.fonte(fc, 44), fill=(40, 40, 60))
    return img


def tv(w=760):
    p = Pincel(w, w * 0.9)
    p.ret((10, 10, w - 10, w * 0.78), (110, 80, 60), r=40)
    p.ret((50, 50, w - 170, w * 0.72), (25, 30, 35), r=30)
    for y in (120, 220):
        p.elipse((w - 130, y, w - 60, y + 70), (200, 190, 170), ow=5)
    p.ret((150, w * 0.78, 200, w * 0.88), (80, 60, 45), r=6)
    p.ret((w - 200, w * 0.78, w - 150, w * 0.88), (80, 60, 45), r=6)
    return p.pronto()


def gaiola(w=300):
    p = Pincel(w, w * 1.3)
    p.chord((20, 20, w - 20, 200), 180, 360, (210, 180, 90), ow=6)
    for x in range(30, w - 20, 34):
        p.linha([(x, 110), (x, w * 1.2)], fill=(210, 180, 90), w=6)
    p.ret((10, w * 1.18, w - 10, w * 1.28), (170, 140, 60), r=8)
    return p.pronto()


def coroa_flores(w=700):
    p = Pincel(w, w * 1.1)
    p.arco((40, 40, w - 40, w * 1.4), 180, 360, fill=(120, 170, 90), w=40)
    rng = random.Random(4)
    for i in range(16):
        a = math.radians(180 + i * 11.5)
        x = w / 2 + (w / 2 - 60) * math.cos(a)
        y = w * 0.72 + (w * 0.7 - 40) * math.sin(a)
        c = rng.choice([(250, 250, 250), (250, 180, 200), (250, 220, 120)])
        p.elipse((x - 34, y - 34, x + 34, y + 34), c, ow=4)
    return p.pronto()


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def festa(fc, ano=1986):
    novo = ano == 1986
    base = gradiente(WW, WH, (25, 30, 75) if novo else (60, 62, 80), (70, 50, 100) if novo else (95, 90, 105))
    p = Pincel(WW, WH)
    rng = random.Random(1)
    for _ in range(50):
        x, y = rng.uniform(0, WW), rng.uniform(0, 650)
        p.elipse((x - 3, y - 3, x + 3, y + 3), (255, 255, 230), ow=0)
    p.elipse((800, 130, 920, 250), (250, 240, 200), ow=0)
    # barracas
    for x0, nome, cor in ((-40, "QUENTÃO", (200, 60, 50)), (720, "MILHO", (240, 170, 40))):
        cor = cor if novo else tuple(int(c * 0.6 + 60) for c in cor)
        p.ret((x0, 900, x0 + 400, 1350), (170, 120, 80) if novo else (130, 110, 95), r=8)
        p.poli([(x0 - 20, 905), (x0 + 200, 760), (x0 + 420, 905)], cor)
        p.ret((x0 + 60, 930, x0 + 340, 1010), (250, 240, 210), r=10, ow=6)
    # fogueira
    for i in range(6):
        a = math.radians(20 + i * 28)
        p.linha([(540 - 110 * math.cos(a), 1330), (540 + 40 * math.cos(a), 1180)], fill=(110, 70, 40), w=26)
    p.ret((-20, 1340, WW + 20, WH + 20), (150, 110, 70) if novo else (120, 105, 95), r=0)
    # bandeirinhas
    cores = [(230, 60, 60), (250, 210, 50), (60, 160, 230), (90, 190, 90), (230, 120, 200)]
    for fio in range(4):
        y0 = 300 + fio * 140
        p.linha([(-20, y0), (540, y0 + 80), (WW + 20, y0)], fill=(60, 60, 60), w=4)
        for i, x in enumerate(range(10, WW, 70)):
            if not novo and (i + fio) % 3 == 0:
                continue
            y = y0 + 80 * (1 - abs(x - 540) / 560)
            c = cores[(i + fio) % 5] if novo else tuple(int(v * 0.5 + 70) for v in cores[(i + fio) % 5])
            p.poli([(x, y), (x + 54, y), (x + 27, y + 62)], c, ow=3)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 50)
    for x0, nome in ((-40, "QUENTÃO"), (720, "MILHO")):
        d.text((x0 + 200 - f.getlength(nome) / 2, 945), nome, font=f, fill=(90, 50, 30))
    if novo:
        base.alpha_composite(brilho((700, 700), (255, 170, 60), 350, 0.6), (190, 900))
    return base


def fogo(t, congelado=False):
    p = Pincel(320, 260)
    for i in range(5):
        x = 30 + i * 55
        h = 120 + (0 if congelado else 50 * math.sin(t * 9 + i * 1.7))
        c1 = (150, 200, 240) if congelado else (255, 140, 30)
        c2 = (220, 240, 255) if congelado else (255, 220, 90)
        p.elipse((x, 250 - h, x + 70, 255), c1, ow=0)
        p.elipse((x + 14, 250 - h * 0.6, x + 56, 255), c2, ow=0)
    return p.pronto()


def berco():
    p = Pincel(900, 700)
    p.ret((60, 300, 840, 600), (250, 250, 250), r=30)
    for x in range(100, 820, 60):
        p.ret((x, 120, x + 20, 600), (240, 230, 220), r=6)
    p.ret((60, 100, 840, 140), (240, 230, 220), r=14)
    return p.pronto()


def loja_bicho(fc):
    base = gradiente(WW, WH, (235, 225, 200), (215, 200, 175))
    p = Pincel(WW, WH)
    for y in (420, 820):
        p.ret((40, y, 1040, y + 30), (150, 110, 70), r=6)
    p.ret((-20, 1400, WW + 20, WH + 20), (170, 140, 110), r=0)
    p.ret((80, 1150, 1000, 1240), (150, 110, 70), r=10)            # balcão
    p.ret((110, 1240, 970, 1420), (180, 135, 90), r=8)
    base.alpha_composite(p.pronto())
    for i, x in enumerate((90, 360, 640, 880)):
        if i != 2:
            base.alpha_composite(gaiola(200), (x, 160))
    for x in (120, 420, 760):
        base.alpha_composite(gaiola(170), (x, 600))
    return base


def fachada_loja(fc):
    base = gradiente(WW, WH, (150, 200, 240), (225, 238, 250))
    p = Pincel(WW, WH)
    vc.nuvem(p, 100, 250, 0.8)
    p.ret((80, 560, 1000, 1420), (120, 190, 160), r=8)
    p.ret((60, 520, 1020, 660), (40, 120, 90), r=10)
    p.ret((380, 950, 700, 1420), (90, 60, 45), r=10)
    p.ret((140, 760, 330, 920), (180, 215, 240), r=8, ow=8)
    p.ret((750, 760, 940, 920), (180, 215, 240), r=8, ow=8)
    p.ret((-20, 1410, WW + 20, WH + 20), (190, 185, 175), r=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 60)
    d.text((540 - f.getlength("PET SANTO AMARO") / 2, 555), "PET SANTO AMARO", font=f, fill=(255, 255, 255))
    return base


def quarto_nina():
    base = gradiente(WW, WH, (70, 60, 100), (90, 75, 120))
    p = Pincel(WW, WH)
    p.ret((-20, 1400, WW + 20, WH + 20), (110, 90, 100), r=0)
    p.ret((60, 1250, 1020, 1330), (150, 100, 70), r=10)
    base.alpha_composite(p.pronto())
    return base


def capela(fc):
    base = gradiente(WW, WH, (150, 200, 240), (225, 238, 250))
    p = Pincel(WW, WH)
    p.ret((240, 600, 840, 1420), (250, 250, 245), r=8)
    p.poli([(200, 610), (540, 330), (880, 610)], (230, 230, 225))
    p.ret((525, 200, 555, 340), (200, 170, 80), r=4)
    p.ret((480, 240, 600, 270), (200, 170, 80), r=4)
    p.chord((420, 1000, 660, 1300), 180, 360, (120, 80, 60))
    p.ret((420, 1150, 660, 1420), (120, 80, 60), r=0, ow=0)
    p.ret((-20, 1410, WW + 20, WH + 20), (120, 180, 100), r=0)
    base.alpha_composite(p.pronto())
    return base


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class Pers:
    """Personagem com: vivo (respira/pisca), congelado (gelo, imóvel) e lip-sync."""

    def __init__(self, pal, filme):
        self.a = Ator(pal)
        self.filme = filme

    def spr(self, expr, pose):
        return self.a.spr(expr, pose)

    def __call__(self, m, t, cx, by, e, expr="neutro", pose="idle", cong=False, fala=None, **kw):
        if cong:
            g.colar(m, gelo(self.a.spr(expr, pose)), cx, by, e, rot=kw.get("rot", 0.0))
            return
        if fala and self.filme.boca_aberta(fala):
            expr = "fala"
        self.a.desenhar(m, t, cx, by, escala=e, expr=expr, pose=pose, **kw)


class FilmeEstatua(vc.Filme):
    def __init__(self, palavras, fc, dur_total, narracao):
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: Pers(pal, self)  # noqa: E731
        self.nina, self.ant, self.antj = P_(NINA), P_(ANTONIO), P_(ANTONIO_JOVEM)
        self.lur, self.lur_noiva = P_(LURDES), P_(LURDES_NOIVA)
        self.milhoman, self.noiva, self.padre, self.zefa = P_(MILHO), P_(NOIVA), P_(PADRE), P_(ZEFA)
        self.dono = P_(DONO)
        self.povo = [P_(c) for c in POVO]
        self.f86, self.f26 = festa(fc, 1986), festa(fc, 2026)
        self.blur = {}
        self.rua = vco.rua(fc)
        self.loja, self.fachada = loja_bicho(fc), fachada_loja(fc)
        self.quarto = quarto_nina()
        self.capela = capela(fc)
        self.sala = __import__("video_numero").sala(fc)
        self.casa = vct.casa_porta()
        self.milho_img, self.bisc = milho(), biscoito()
        self.placa_estadio = placa(fc, ["GRITAR", "AQUELA PALAVRA"])
        self.placa_escola = placa(fc, ["BRINCAR DE", "★ ★ ★ ★ ★"], cor=(60, 120, 220))
        self.placa_papagaio = placa(fc, ["ENSINAR", "PAPAGAIO"], cor=(60, 160, 80))
        self.placa_grande = placa(fc, ["DIZER", "\"ES _ _ _ _ A\""], w=760)
        self.fita, self.tv_img = fita_vhs(fc), tv()
        self.berco = berco()
        self.radio = vct.radio
        self.coroa = coroa_flores()
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        # janelas de fala (lip-sync): (início, fim)
        self.FALA_NINA = [(69.00, 70.70)]
        self.FALA_ANT = [(71.12, 74.10), (128.40, 131.00)]
        self.FALA_LUR = [(149.80, 150.30), (152.48, 154.10)]
        self.FALA_JUCA = [(100.20, 100.95), (125.00, 126.40), (138.55, 139.30), (169.80, 170.60)]

        P = [
            (0.00, self.p_hook, "", "corte"),
            (4.90, self.p_descongela, "", "whip"),
            (9.60, self.p_nao_envelhece, "", "corte"),
            (13.56, self.p_proibida, "", "zoom"),
            (15.80, self.p_bebe, "", "corte"),
            (20.22, self.p_placas, "", "whip"),
            (24.82, self.p_1986, "", "zoom"),
            (29.34, self.p_gritou, "", "corte"),
            (32.40, self.p_40anos, "", "dissolve"),
            (35.16, self.p_milho, "", "corte"),
            (36.74, self.p_noiva, "", "corte"),
            (39.06, self.p_padre, "", "corte"),
            (40.98, self.p_ninguem, "", "corte"),
            (43.08, self.p_frase, "", "whip"),
            (48.08, self.p_banco, "", "dissolve"),
            (56.08, self.p_boca, "", "corte"),
            (57.26, self.p_pedido, "sepia", "zoom"),
            (60.90, self.p_responder, "sepia", "corte"),
            (63.70, self.p_espera, "", "dissolve"),
            (66.10, self.p_nina, "", "corte"),
            (69.00, self.p_pergunta, "", "corte"),
            (71.12, self.p_vo_responde, "", "corte"),
            (74.42, self.p_fita, "", "whip"),
            (78.52, self.p_vhs, "", "zoom"),
            (81.28, self.p_vhs_papagaio, "", "corte"),
            (84.90, self.p_vhs_voou, "", "corte"),
            (87.90, self.p_80anos, "", "whip"),
            (90.00, self.p_procura, "", "corte"),
            (92.58, self.p_loja_fora, "", "corte"),
            (95.32, self.p_juca_velho, "", "zoom"),
            (98.40, self.p_juca_grita, "", "corte"),
            (103.90, self.p_dois_problemas, "", "corte"),
            (105.86, self.p_duas_coisas, "", "whip"),
            (110.44, self.p_terceira, "", "corte"),
            (112.68, self.p_cidade_ajuda, "", "whip"),
            (114.56, self.p_radio, "", "corte"),
            (117.58, self.p_janelas, "", "corte"),
            (119.58, self.p_escola, "", "corte"),
            (121.08, self.p_tentativas, "", "whip"),
            (125.02, self.p_cade, "", "corte"),
            (126.74, self.p_paciente, "", "corte"),
            (131.30, self.p_aniversario, "", "dissolve"),
            (136.76, self.p_bico, "", "corte"),
            (138.62, self.p_desestatua, "", "corte"),
            (139.38, self.p_milho2, "", "corte"),
            (140.96, self.p_noiva2, "", "corte"),
            (142.50, self.p_padre2, "", "corte"),
            (143.72, self.p_troco, "", "whip"),
            (146.06, self.p_lurdes, "", "dissolve"),
            (149.88, self.p_sim, "quente", "corte"),
            (150.42, self.p_olhou, "quente", "corte"),
            (152.48, self.p_velho, "", "corte"),
            (154.46, self.p_chora_ri, "quente", "corte"),
            (156.76, self.p_casamento, "quente", "whip"),
            (159.02, self.p_festa_heroi, "quente", "dissolve"),
            (162.80, self.p_biscoito_novo, "quente", "corte"),
            (165.54, self.p_feliz, "quente", "corte"),
            (169.88, self.p_estatua_final, "", "corte"),
            (170.70, self.p_preto, "", "corte"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))

    # ---------- utilidades ----------
    @staticmethod
    def envelope(narracao):
        x = vc.ler_wav_mono(narracao)
        n = int(g.SR / FPS)
        k = len(x) // n
        rms = np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1))
        return rms / max(1e-6, np.percentile(rms, 95))

    def boca_aberta(self, janelas):
        T = self.T
        if not any(a <= T < b for a, b in janelas):
            return False
        i = int(T * FPS)
        return i < len(self.env) and self.env[i] > 0.28 and (i // 3) % 2 == 0 or (
            i < len(self.env) and self.env[i] > 0.7)

    def fundo_blur(self, nome, img):
        if nome not in self.blur:
            self.blur[nome] = img.filter(ImageFilter.GaussianBlur(14))
        return self.blur[nome].copy()

    def cam(self, m, cx, cy, z):
        dx, dy = tremor(self.T)
        return camera(m, cx + dx, cy + dy, z)

    def painel(self, f, titulo, valor, t, y=0.08, cor=(255, 214, 40)):
        ft, fv = vc.fonte(self.fc, 30), vc.fonte(self.fc, 80)
        w = max(ft.getlength(titulo), fv.getlength(valor)) + 60
        s = 0.7 + 0.3 * ease_out(t / 0.2)
        cam = Image.new("RGBA", (int(w), 150), (0, 0, 0, 0))
        d = ImageDraw.Draw(cam)
        d.rounded_rectangle((0, 0, w, 150), radius=20, fill=(20, 22, 32, 220))
        d.text((w / 2 - ft.getlength(titulo) / 2, 12), titulo, font=ft, fill=(220, 220, 230))
        d.text((w / 2 - fv.getlength(valor) / 2, 44), valor, font=fv, fill=cor)
        cam = cam.resize((int(cam.width * s), int(cam.height * s)), Image.BICUBIC)
        f.paste(cam, (int(OUT_W / 2 - cam.width / 2), int(OUT_H * y)), cam)

    def multidao(self, m, t, cong, ano=1986, sem=()):
        """A praça da festa com as pessoas (vivas ou congeladas)."""
        m.alpha_composite(fogo(t, cong), (380, 1090))
        gente = [(self.povo[0], 160, 1600, 0.85, "acena"), (self.povo[1], 900, 1580, 0.8, "idle"),
                 (self.zefa, 180, 1360, 0.7, "entrega"), (self.povo[3], 760, 1700, 0.9, "anda1")]
        for i, (p, x, y, e, pose) in enumerate(gente):
            p(m, t + i, x, y, e, expr="ri" if not cong else "surpreso", pose=pose, cong=cong)
        if "milho" not in sem:
            self.milhoman(m, t, 420, 1760, 1.0, expr="feliz" if not cong else "surpreso", pose="entrega", cong=cong)
            hx, hy = self.mao(420, 1760, 1.0, 0 if cong else t)
            self.segura(m, self.milho_img, hx + 10, hy - 60, 80, rot=-30)
        if "noiva" not in sem:
            pulo = 160 if cong else 160 * abs(math.sin(t * 3))
            self.noiva(m, t, 640, 1760 - pulo, 0.95, expr="ri", pose="anda2", cong=cong)

    def cena_festa(self, t, cong, ano=1986, cx=540, cy=1250, z=1.05):
        m = (self.f86 if ano == 1986 else self.f26).copy()
        self.multidao(m, t, cong, ano)
        f = self.cam(m, cx, cy, z)
        if cong:
            f = tom_frio(f, 0.6)
        else:
            particulas(f, t, 30, (255, 220, 150), semente=2)
        return f

    def close(self, pers, t, bg, nome, expr="neutro", cong=False, fala=None, z=1.05, glow=None, by=2350, e=2.5):
        m = self.fundo_blur(nome, bg)
        if glow:
            m.alpha_composite(brilho((1000, 1000), glow, 500, 0.6), (40, 300))
        pers(m, t, 540, by, e, expr=expr, cong=cong, fala=fala, piscar=not cong)
        return self.cam(m, 540, 950, z)

    # ------------------------- planos -------------------------
    def p_hook(self, t, d):
        tg = GRITOS[0] - 0.0
        if t < tg:
            return self.cena_festa(t, False, z=1.12 - 0.04 * t / tg)
        viva = self.cena_festa(t, False, z=1.08)
        cong = self.cena_festa(tg, True, z=1.08)
        f = onda(viva, cong, t - tg, OUT_W / 2, OUT_H * 0.55)
        if t - tg > 0.5:
            texto_pop(f, "ESTÁTUA!", self.fc, t - tg - 0.5, OUT_W / 2, OUT_H * 0.16, 110, (120, 200, 255))
        return f

    def p_descongela(self, t, d):
        tg = 8.34 - 4.90
        def cena(cong):
            m = self.rua.copy()
            for i, (p, x) in enumerate(zip(self.povo[:3], (200, 520, 860))):
                p(m, t, x, 1760, 1.0, expr="surpreso" if cong else "feliz", pose="anda1" if i % 2 else "anda2", cong=cong)
            self.povo[4](m, t, 540, 1500, 0.75, expr="fala" if t > tg - 0.4 else "neutro")
            return self.cam(m, 540, 1250, 1.1)
        if t < tg:
            return tom_frio(cena(True), 0.4)
        return onda(tom_frio(cena(True), 0.4), cena(False), t - tg, OUT_W / 2, OUT_H * 0.55, cor=(255, 230, 150))

    def p_nao_envelhece(self, t, d):
        m = self.fundo_blur("rua", self.rua)
        self.povo[2](m, t, 540, 2350, 2.5, expr="surpreso", cong=True)
        f = self.cam(m, 540, 950, 1.05)
        for i, (txt, ts) in enumerate((("SEM FOME", 10.60), ("SEM FRIO", 11.84), ("NÃO ENVELHECE", 12.78))):
            T = 9.60 + t
            if T > ts:
                texto_pop(f, txt, self.fc, T - ts, OUT_W / 2, OUT_H * (0.1 + i * 0.07), 58, (180, 225, 255))
        return f

    def p_proibida(self, t, d):
        m = gradiente(WW, WH, (40, 40, 55), (20, 20, 30))
        self.segura(m, self.placa_grande, 540, 1000, 900, rot=2 * math.sin(t * 2))
        return self.cam(m, 540, 980, 1.3 + 0.1 * ease_io(t / d))

    def p_bebe(self, t, d):
        m = gradiente(WW, WH, (240, 220, 235), (220, 200, 220))
        self.povo[4](m, t, 540, 1520, 0.9, expr="feliz")
        m.alpha_composite(self.berco, (90, 1000))
        f = self.cam(m, 540, 1150, 1.15)
        T = 15.80 + t
        for i, (txt, ts, cor) in enumerate((("mamãe", 16.62, (255, 255, 255)), ("papai", 17.42, (255, 255, 255)),
                                            ("não pode falar aquela palavra", 18.24, (255, 120, 120)))):
            if T > ts:
                texto_pop(f, txt, self.fc, T - ts, OUT_W / 2, OUT_H * (0.12 + i * 0.07), 48 if i < 2 else 36, cor)
        return f

    def p_placas(self, t, d):
        m = gradiente(WW, WH, (150, 200, 240), (225, 238, 250))
        p = Pincel(WW, WH)
        p.ret((-20, 1500, WW + 20, WH + 20), (120, 180, 100), r=0)
        m.alpha_composite(p.pronto())
        T = 20.22 + t
        for i, (img, ts, x) in enumerate(((self.placa_estadio, 20.22, 220), (self.placa_escola, 21.72, 540),
                                          (self.placa_papagaio, 23.00, 860))):
            if T > ts:
                k = ease_out(min(1, (T - ts) / 0.25))
                self.segura(m, img, x, 1250 + (1 - k) * 400, 330)
        if T > 23.0:
            g.colar(m, papagaio(), 860, 1560, 0.45)
        return self.cam(m, 540, 1300, 1.3)

    def p_1986(self, t, d):
        f = self.cena_festa(t, False, z=1.0 + 0.1 * ease_io(t / d))
        texto_pop(f, "1986", self.fc, t, OUT_W / 2, OUT_H * 0.12, 130, (255, 214, 40))
        if t > 2.3:
            texto_pop(f, "FESTA JUNINA DE SANTO AMARO", self.fc, t - 2.3, OUT_W / 2, OUT_H * 0.21, 40)
        return f

    def p_gritou(self, t, d):
        tg = GRITOS[1] - 29.34
        if t < tg:
            return self.cena_festa(t, False, z=1.1)
        viva = self.cena_festa(t, False, z=1.1)
        cong = self.cena_festa(tg, True, z=1.1)
        return onda(viva, cong, t - tg, OUT_W * 0.3, OUT_H * 0.45)

    def p_40anos(self, t, d):
        m = self.f26.copy()
        self.multidao(m, 0, True, 2026)
        for i, (p, x) in enumerate(((self.povo[2], 960), (self.povo[4], 120))):
            p(m, t + i, x, 1880, 1.05, expr="feliz", pose="entrega")
        f = self.cam(m, 540, 1250, 1.05 + 0.08 * ease_io(t / d))
        if int(t * 2) % 3 == 0:
            ImageDraw.Draw(f, "RGBA").rectangle((0, 0, OUT_W, OUT_H), fill=(255, 255, 255, 60))  # flash de foto
        self.painel(f, "CONGELADOS HÁ", "40 ANOS", t)
        return f

    def p_milho(self, t, d):
        m = self.fundo_blur("f26", self.f26)
        self.milhoman(m, 0, 540, 2350, 2.5, expr="surpreso", pose="entrega", cong=True)
        hx, hy = self.mao(540, 2350, 2.5, 0)
        self.segura(m, gelo(self.milho_img), hx - 120, hy - 300, 200, rot=-60)
        return self.cam(m, 540, 950, 1.05 + 0.08 * ease_io(t / d))

    def p_noiva(self, t, d):
        m = self.fundo_blur("f26", self.f26)
        self.noiva(m, 0, 540, 1700, 1.6, expr="ri", pose="anda2", cong=True)
        p = Pincel(WW, WH)
        p.elipse((360, 1760, 720, 1820), (60, 50, 50), ow=0)
        m.alpha_composite(p.pronto())
        return self.cam(m, 540, 1150, 1.15)

    def p_padre(self, t, d):
        m = self.fundo_blur("f26", self.f26)
        self.padre(m, 0, 540, 2350, 2.5, expr="fala", cong=True)
        f = self.cam(m, 540, 950, 1.05 + 0.08 * ease_io(t / d))
        texto_pop(f, "A…", self.fc, 0.5, OUT_W * 0.7, OUT_H * 0.25, 90, (200, 230, 255))
        return f

    def p_ninguem(self, t, d):
        f = self.cena_festa(0, True, ano=2026, z=1.0)
        for i, (x, y) in enumerate(((0.25, 0.3), (0.7, 0.25), (0.5, 0.18))):
            if t > i * 0.3:
                texto_pop(f, "?", self.fc, t - i * 0.3, OUT_W * x, OUT_H * y, 120, (255, 214, 40))
        return f

    def p_frase(self, t, d):
        m = self.rua.copy()
        for i, (p, x) in enumerate(zip(self.povo, (140, 340, 540, 740, 940))):
            p(m, t + i, x, 1760, 0.85, expr="neutro" if i % 2 else "fala")
        f = self.cam(m, 540, 1250, 1.1)
        if t > 0.2:
            texto_pop(f, "\"SE FOSSE ALGUÉM DAQUI,", self.fc, t - 0.2, OUT_W / 2, OUT_H * 0.1, 44)
            texto_pop(f, "JÁ TINHA CONFESSADO.\"", self.fc, t - 0.4, OUT_W / 2, OUT_H * 0.16, 44)
        return f

    def banco_cena(self, t, cong_lurdes=True, z=1.15, cy=1250, fala_ant=None):
        m = self.f26.copy()
        p = Pincel(WW, WH)
        p.ret((180, 1560, 900, 1620), (130, 90, 60), r=10)
        p.ret((200, 1620, 240, 1760), (110, 75, 50), r=6)
        p.ret((840, 1620, 880, 1760), (110, 75, 50), r=6)
        m.alpha_composite(p.pronto())
        self.lur(m, t, 680, 1700, 1.0, expr="surpreso", cong=cong_lurdes)
        self.ant(m, t, 380, 1720, 1.05, expr="neutro", pose="entrega", fala=fala_ant)
        return self.cam(m, 540, cy, z)

    def p_banco(self, t, d):
        f = self.banco_cena(t, z=1.1 + 0.08 * ease_io(t / d))
        T = 48.08 + t
        if T > 49.78:
            texto_pop(f, "80 ANOS", self.fc, T - 49.78, OUT_W * 0.28, OUT_H * 0.16, 70, (255, 255, 255))
        if T > 53.96:
            texto_pop(f, "30 ANOS", self.fc, T - 53.96, OUT_W * 0.72, OUT_H * 0.16, 70, (180, 225, 255))
        return f

    def p_boca(self, t, d):
        return self.close(self.lur, 0, self.f26, "f26", expr="surpreso", cong=True, z=1.1 + 0.1 * ease_io(t / d))

    def pedido(self, t, cong=False):
        m = self.f86.copy()
        self.multidao(m, t, cong, sem=("milho", "noiva"))
        self.antj(m, t, 360, 1760, 1.15, expr="feliz", pose="ajoelha", cong=cong)
        self.lur(m, t, 700, 1760, 1.15, expr="surpreso" if cong or t > 0.5 else "feliz", cong=cong)
        return m

    def p_pedido(self, t, d):
        f = self.cam(self.pedido(t), 540, 1250, 1.15 + 0.06 * ease_io(t / d))
        particulas(f, t, 40, (255, 200, 220), semente=9)
        return f

    def p_responder(self, t, d):
        tg = GRITOS[2] - 60.90
        if t < tg:
            return self.cam(self.pedido(t), 640, 1150, 1.3 + 0.1 * t / tg)
        viva = self.cam(self.pedido(t), 640, 1150, 1.4)
        cong = tom_frio(self.cam(self.pedido(tg, cong=True), 640, 1150, 1.4), 0.6)
        return onda(viva, cong, t - tg, OUT_W * 0.6, OUT_H * 0.4)

    def p_espera(self, t, d):
        f = self.banco_cena(t, z=1.4, cy=1300)
        ano = 1986 + int(40 * ease_io(min(1, t / (d * 0.9))))
        self.painel(f, "ESPERANDO A RESPOSTA", str(ano), t)
        return f

    def p_nina(self, t, d):
        m = self.f26.copy()
        p = Pincel(WW, WH)
        p.ret((180, 1560, 900, 1620), (130, 90, 60), r=10)
        m.alpha_composite(p.pronto())
        self.lur(m, t, 760, 1700, 0.95, expr="surpreso", cong=True)
        self.ant(m, t, 480, 1720, 1.0, expr="neutro")
        passo = "anda1" if int(t * 4) % 2 else "anda2"
        x = -100 + 340 * min(1, t / 2.0)
        self.nina(m, t, x, 1800, 0.95, expr="feliz", pose=passo if t < 2.0 else "idle")
        f = self.cam(m, 540, 1250, 1.12)
        texto_pop(f, "NINA, 10 ANOS", self.fc, t, OUT_W / 2, OUT_H * 0.12, 64, (255, 214, 40))
        return f

    def p_pergunta(self, t, d):
        return self.close(self.nina, t, self.f26, "f26", expr="neutro", fala=self.FALA_NINA)

    def p_vo_responde(self, t, d):
        return self.close(self.ant, t, self.f26, "f26", expr="neutro", fala=self.FALA_ANT)

    def p_fita(self, t, d):
        m = self.quarto.copy()
        m.alpha_composite(brilho((900, 900), (120, 160, 255), 450, 0.5), (90, 400))
        self.segura(m, self.tv_img, 560, 950, 700)
        self.nina(m, t, 300, 1760, 1.1, expr="surpreso" if t > 2 else "neutro", pose="entrega")
        k = ease_out(min(1, t / 1.0))
        hx, hy = self.mao(300, 1760, 1.1, t)
        self.segura(m, self.fita, hx + 60 + 200 * (1 - k), hy - 60, 260)
        return self.cam(m, 540, 1150, 1.1)

    def vhs_cena(self, t, cx, cy, z, voando=0.0):
        m = self.f86.copy()
        self.multidao(m, t * 0.25, False)
        if voando <= 0:
            g.colar(m, papagaio(aberto=t > 1.5), 160, 830, 0.45)
        else:
            k = ease_io(min(1, voando))
            g.colar(m, papagaio(asas=True), 160 + 900 * k, 830 - 600 * k, 0.45)
        return vhs(camera(m, cx, cy, z), t, self.fc)

    def p_vhs(self, t, d):
        k = ease_io(t / d)
        return self.vhs_cena(t, 540 - 300 * k, 1150 - 150 * k, 1.0 + 0.6 * k)

    def p_vhs_papagaio(self, t, d):
        f = self.vhs_cena(t, 200, 800, 2.6 + 0.3 * ease_io(t / d))
        d_ = ImageDraw.Draw(f)
        k = ease_out(min(1, t / 0.4))
        r = 230 * k
        cx, cy = OUT_W * 0.46, OUT_H * 0.5
        d_.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(230, 40, 40), width=12)
        if t > 1.2:
            texto_pop(f, "O JUCA", self.fc, t - 1.2, OUT_W / 2, OUT_H * 0.82, 80, (255, 214, 40))
        return f

    def p_vhs_voou(self, t, d):
        return self.vhs_cena(t, 540, 900, 1.3, voando=t / (d * 0.8))

    def p_80anos(self, t, d):
        m = gradiente(WW, WH, (60, 170, 120), (30, 110, 80))
        m.alpha_composite(brilho((900, 900), (200, 255, 200), 450, 0.4), (90, 500))
        g.colar(m, papagaio(), 540, 1500, 1.4)
        f = self.cam(m, 540, 1000, 1.05)
        self.painel(f, "PAPAGAIO VIVE", "80 ANOS", t, cor=(120, 230, 140))
        return f

    def p_procura(self, t, d):
        off = (t * 500) % WW
        m = Image.new("RGBA", (WW, WH))
        m.alpha_composite(self.rua, (int(-off), 0))
        m.alpha_composite(self.rua, (int(WW - off), 0))
        self.nina(m, t, 540, 1780, 1.15, expr="neutro", pose="anda1" if int(t * 5) % 2 else "anda2")
        f = self.cam(m, 540, 1250, 1.12)
        self.painel(f, "CASAS VISITADAS", str(min(37, 1 + int(t / d * 37))), t, cor=(255, 255, 255))
        return f

    def p_loja_fora(self, t, d):
        m = self.fachada.copy()
        self.nina(m, t, 300, 1760, 1.05, expr="feliz")
        f = self.cam(m, 540, 1150, 1.05 + 0.12 * ease_io(t / d))
        self.painel(f, "CASA", "38", t, cor=(120, 230, 140))
        return f

    def juca_close(self, t, aberto=False, asas=False, bg=None, nome="loja", z=1.05, velho=True, glow=None):
        m = self.fundo_blur(nome, bg or self.loja)
        if glow:
            m.alpha_composite(brilho((1000, 1000), glow, 500, 0.6), (40, 300))
        bob = 6 * math.sin(t * 4)
        g.colar(m, papagaio(velho=velho, aberto=aberto, asas=asas), 540, 1750 + bob, 2.3)
        return self.cam(m, 540, 1000, z)

    def p_juca_velho(self, t, d):
        f = self.juca_close(t, z=1.05 + 0.1 * ease_io(t / d))
        T = 95.32 + t
        for i, (txt, ts) in enumerate((("VELHO.", 96.52), ("CARECA.", 97.04), ("VIVO.", 97.94))):
            if T > ts:
                texto_pop(f, txt, self.fc, T - ts, OUT_W / 2, OUT_H * (0.1 + i * 0.07), 64,
                          (120, 230, 140) if i == 2 else (255, 255, 255))
        return f

    def loja_cena(self, t, cong):
        m = self.loja.copy()
        self.dono(m, t, 760, 1420, 0.9, expr="feliz" if not cong else "surpreso", pose="entrega", cong=cong)
        g.colar(m, papagaio(velho=True, aberto=not cong and 100.2 <= self.T < 101), 560, 820, 0.6)
        self.nina(m, t, 300, 1800, 1.1, expr="feliz" if not cong else "surpreso", cong=cong)
        return self.cam(m, 540, 1200, 1.08)

    def p_juca_grita(self, t, d):
        tg = GRITOS[3] - 98.40
        if t < tg:
            return self.loja_cena(t, False)
        viva = self.loja_cena(t, False)
        cong = tom_frio(self.loja_cena(tg, True), 0.5)
        f = onda(viva, cong, t - tg, OUT_W * 0.52, OUT_H * 0.35)
        if t - tg > 0.4:
            texto_pop(f, "ESTÁTUA!", self.fc, t - tg - 0.4, OUT_W / 2, OUT_H * 0.12, 110, (120, 200, 255))
        return f

    def p_dois_problemas(self, t, d):
        a = self.cena_festa(0, True, ano=2026, z=1.0).resize((OUT_W, OUT_H // 2))
        b = tom_frio(self.loja_cena(0, True), 0.5).resize((OUT_W, OUT_H // 2))
        f = Image.new("RGB", (OUT_W, OUT_H))
        f.paste(a, (0, 0))
        f.paste(b, (0, OUT_H // 2))
        ImageDraw.Draw(f).line((0, OUT_H // 2, OUT_W, OUT_H // 2), fill=(255, 255, 255), width=8)
        texto_pop(f, "2 PROBLEMAS", self.fc, t, OUT_W / 2, OUT_H * 0.5, 90, (230, 60, 60))
        return f

    def balao(self, f, txt, x, y, t, cor=(255, 255, 255)):
        if t < 0:
            return
        fnt = vc.fonte(self.fc, 44)
        w = fnt.getlength(txt) + 60
        s = 0.6 + 0.4 * ease_out(t / 0.2)
        cam = Image.new("RGBA", (int(w), 120), (0, 0, 0, 0))
        dc = ImageDraw.Draw(cam)
        dc.rounded_rectangle((0, 0, w, 96), radius=40, fill=cor, outline=OUTLINE, width=6)
        dc.polygon([(w * 0.3, 90), (w * 0.4, 90), (w * 0.28, 118)], fill=cor, outline=OUTLINE)
        dc.text((30, 20), txt, font=fnt, fill=(40, 40, 50))
        cam = cam.resize((int(cam.width * s), int(cam.height * s)), Image.BICUBIC)
        f.paste(cam, (int(x - cam.width / 2), int(y)), cam)

    def p_duas_coisas(self, t, d):
        f = self.juca_close(t, aberto=int(t * 3) % 2 == 0 and t > 2.2, z=1.1)
        T = 105.86 + t
        self.balao(f, "ESTÁTUA!", OUT_W * 0.3, OUT_H * 0.12, T - 108.22)
        self.balao(f, "CADÊ O BISCOITO?", OUT_W * 0.6, OUT_H * 0.22, T - 109.48)
        return f

    def p_terceira(self, t, d):
        f = self.juca_close(t, z=1.1)
        self.balao(f, "ESTÁTUA!", OUT_W * 0.3, OUT_H * 0.08, 1)
        self.balao(f, "CADÊ O BISCOITO?", OUT_W * 0.62, OUT_H * 0.16, 1)
        self.balao(f, "???", OUT_W * 0.5, OUT_H * 0.25, t, cor=(255, 230, 130))
        return f

    def p_cidade_ajuda(self, t, d):
        m = self.rua.copy()
        for i, p in enumerate(self.povo):
            x = 1200 - (t * 300 + i * 220) % 1500
            p(m, t + i, x, 1760 - (i % 2) * 40, 0.9, expr="feliz", pose="anda1" if int(t * 5 + i) % 2 else "anda2")
        self.nina(m, t, 540, 1820, 1.0, expr="feliz", pose="acena")
        return self.cam(m, 540, 1250, 1.1)

    def p_radio(self, t, d):
        m = gradiente(WW, WH, (250, 220, 170), (235, 190, 140))
        self.segura(m, self.radio(t), 540, 1000, 860)
        f = self.cam(m, 540, 980, 1.05)
        texto_pop(f, "DESESTÁTUA!", self.fc, (t % 1.0), OUT_W / 2, OUT_H * 0.14, 80,
                  (255, 214, 40))
        return f

    def p_janelas(self, t, d):
        m = self.casa.copy()
        for i, x in enumerate((240, 840)):
            self.povo[3 + i](m, t + i, x, 1060, 0.55, expr="fala" if int(t * 4 + i) % 2 else "feliz")
        self.nina(m, t, 540, 1760, 1.0, expr="fala" if int(t * 4) % 2 else "feliz", pose="acena")
        return self.cam(m, 540, 1200, 1.08)

    def p_escola(self, t, d):
        m = self.sala.copy()
        for i, (p, x) in enumerate(zip(self.povo, (140, 340, 540, 740, 940))):
            p(m, t + i, x, 1780, 0.8, expr="fala" if int(t * 4 + i) % 2 else "feliz")
        f = self.cam(m, 540, 1250, 1.1)
        texto_pop(f, "DESESTÁTUA!", self.fc, t % 0.7, OUT_W / 2, OUT_H * 0.12, 70, (255, 214, 40))
        return f

    def p_tentativas(self, t, d):
        f = self.juca_close(t, aberto=int(t * 4) % 2 == 0, z=1.1, nome="sala", bg=self.sala)
        T = 121.08 + t
        n = 100 if T < 122.24 else (200 if T < 123.64 else 312)
        self.painel(f, "TENTATIVAS", str(n), T - (121.08 if n == 100 else (122.24 if n == 200 else 123.64)),
                    cor=(255, 255, 255))
        return f

    def p_cade(self, t, d):
        aberto = self.boca_aberta(self.FALA_JUCA)
        f = self.juca_close(t, aberto=aberto, z=1.15 + 0.1 * ease_out(t / 0.4), nome="sala", bg=self.sala)
        self.balao(f, "CADÊ O BISCOITO?", OUT_W / 2, OUT_H * 0.12, t)
        self.painel(f, "TENTATIVAS", "312", 1, y=0.25, cor=(255, 255, 255))
        return f

    def p_paciente(self, t, d):
        return self.close(self.ant, t, self.f26, "f26", expr="feliz", fala=self.FALA_ANT, glow=(255, 220, 160))

    def praca_aniv(self, t, cong=True):
        m = self.f26.copy()
        self.multidao(m, 0, cong, 2026)
        self.lur(m, t, 930, 1700, 0.85, expr="surpreso", cong=cong)
        self.ant(m, t, 330, 1880, 1.1, expr="feliz", pose="entrega")
        hx, hy = self.mao(330, 1880, 1.1, t)
        self.segura(m, self.bisc, hx + 40, hy - 20, 100)
        g.colar(m, papagaio(velho=True, aberto=False), 560, 1880, 0.6)
        self.nina(m, t, 760, 1900, 0.9, expr="neutro")
        return m

    def p_aniversario(self, t, d):
        f = self.cam(self.praca_aniv(t), 540, 1300, 1.1 + 0.06 * ease_io(t / d))
        self.painel(f, "ÚLTIMO BISCOITO", "1", t, cor=(255, 214, 40))
        return f

    def p_bico(self, t, d):
        aberto = t > d * 0.75
        return self.juca_close(t, aberto=aberto, nome="f26", bg=self.f26, z=1.1 + 0.4 * ease_io(t / d))

    def praca_viva(self, t, sem=()):
        m = self.f86.copy()
        self.multidao(m, t, False, 1986, sem=sem)
        return m

    def p_desestatua(self, t, d):
        cong = tom_frio(self.cam(self.praca_aniv(0, True), 540, 1300, 1.1), 0.6)
        viva = self.cam(self.praca_viva(t), 540, 1300, 1.1)
        f = onda(cong, viva, t, OUT_W * 0.52, OUT_H * 0.7, cor=(255, 220, 140), dur=0.6)
        texto_pop(f, "DESESTÁTUA!", self.fc, t, OUT_W / 2, OUT_H * 0.14, 100, (255, 214, 40))
        return f

    def p_milho2(self, t, d):
        m = self.fundo_blur("f86", self.f86)
        mastiga = int(t * 6) % 2
        self.milhoman(m, t, 540, 2350, 2.5, expr="ri" if mastiga else "feliz", pose="entrega")
        return self.cam(m, 540, 950, 1.05)

    def p_noiva2(self, t, d):
        m = self.fundo_blur("f86", self.f86)
        k = ease_io(min(1, t / 0.5))
        self.noiva(m, t, 540, 1700 + 300 * k, 1.6, expr="surpreso" if k < 1 else "ri", pose="anda2" if k < 1 else "idle")
        return self.cam(m, 540, 1150, 1.15)

    def p_padre2(self, t, d):
        m = self.fundo_blur("f86", self.f86)
        self.padre(m, t, 540, 2350, 2.5, expr="bravo" if t < 0.3 else "ri")
        f = self.cam(m, 540, 950 + (12 * math.sin(t * 60) if t < 0.4 else 0), 1.05)
        texto_pop(f, "ATCHIM!", self.fc, t, OUT_W / 2, OUT_H * 0.15, 110, (255, 255, 255))
        return f

    def p_troco(self, t, d):
        m = self.loja.copy()
        self.dono(m, t, 760, 1420, 0.9, expr="feliz", pose="entrega")
        self.nina(m, t, 300, 1800, 1.1, expr="ri", pose="acena")
        f = self.cam(m, 540, 1200, 1.08)
        vm.confete(f, t, 40)
        return f

    def p_lurdes(self, t, d):
        T = 146.06 + t
        m = self.fundo_blur("f86", self.f86)
        m.alpha_composite(brilho((1000, 1000), (255, 220, 170), 500, 0.5), (40, 300))
        self.lur(m, t, 540, 2350, 2.5, expr="surpreso" if T < 148.6 else "neutro")
        return self.cam(m, 540, 950, 1.05 + 0.15 * ease_io(t / d))

    def p_sim(self, t, d):
        m = self.fundo_blur("f86", self.f86)
        m.alpha_composite(brilho((1080, 1080), (255, 230, 150), 540, 0.9), (0, 300))
        self.lur(m, t, 540, 2350, 2.5, expr="feliz", fala=self.FALA_LUR)
        f = self.cam(m, 540, 950, 1.2)
        texto_pop(f, "SIM.", self.fc, t, OUT_W / 2, OUT_H * 0.14, 130, (255, 214, 40))
        particulas(f, t, 50, (255, 230, 160), semente=12)
        return f

    def dois(self, t, expr_l="feliz", expr_a="surpreso", fala_l=None, z=1.25):
        m = self.f86.copy()
        p = Pincel(WW, WH)
        p.ret((180, 1560, 900, 1620), (130, 90, 60), r=10)
        m.alpha_composite(p.pronto())
        self.ant(m, t, 360, 1720, 1.1, expr=expr_a)
        self.lur(m, t, 720, 1720, 1.1, expr=expr_l, fala=fala_l)
        return self.cam(m, 540, 1250, z)

    def p_olhou(self, t, d):
        f = self.dois(t, z=1.2 + 0.05 * ease_io(t / d))
        particulas(f, t, 30, (255, 230, 160), semente=13)
        return f

    def p_velho(self, t, d):
        return self.close(self.lur, t, self.f86, "f86", expr="surpreso", fala=self.FALA_LUR, z=1.1)

    def p_chora_ri(self, t, d):
        r = int(t * 4) % 2
        return self.close(self.ant, t, self.f86, "f86", expr="chora" if r else "ri", glow=(255, 220, 160))

    def p_casamento(self, t, d):
        m = self.capela.copy()
        m.alpha_composite(self.coroa, (190, 860))
        self.ant(m, t, 420, 1760, 1.15, expr="ri")
        self.lur_noiva(m, t, 680, 1760, 1.15, expr="ri")
        f = self.cam(m, 540, 1250, 1.1)
        vm.confete(f, t, 70)
        return f

    def p_festa_heroi(self, t, d):
        m = self.f86.copy()
        self.multidao(m, t, False, 1986)
        p = Pincel(WW, WH)
        p.ret((400, 1500, 680, 1700), (200, 160, 60), r=10)
        m.alpha_composite(p.pronto())
        g.colar(m, papagaio(velho=True, asas=int(t * 2) % 2 == 0), 540, 1520, 0.9)
        f = self.cam(m, 540, 1250, 1.12)
        vm.confete(f, t, 60)
        texto_pop(f, "HERÓI DA CIDADE", self.fc, t, OUT_W / 2, OUT_H * 0.12, 70, (255, 214, 40))
        return f

    def p_biscoito_novo(self, t, d):
        m = self.fundo_blur("f86", self.f86)
        g.colar(m, papagaio(velho=True, aberto=t > 1.5), 700, 1700, 1.6)
        self.nina(m, t, 300, 2000, 1.6, expr="feliz", pose="entrega")
        hx, hy = self.mao(300, 2000, 1.6, t)
        self.segura(m, self.bisc, hx + 60, hy - 40, 160)
        return self.cam(m, 540, 1150, 1.1)

    def p_feliz(self, t, d):
        asas = t > (167.74 - 165.54)
        return self.juca_close(t, aberto=asas, asas=asas, nome="f86", bg=self.f86, glow=(255, 230, 150),
                               z=1.05 + 0.2 * ease_io(t / d))

    def p_estatua_final(self, t, d):
        viva = self.juca_close(t, aberto=True, asas=True, nome="f86", bg=self.f86, z=1.25)
        cong = tom_frio(viva, 0.8)
        return onda(viva, cong, t, OUT_W * 0.6, OUT_H * 0.45, dur=0.45)

    def p_preto(self, t, d):
        f = Image.new("RGB", (OUT_W, OUT_H), (8, 8, 12))
        T = 170.70 + t
        if T > 171.10:
            texto_pop(f, "TENTATIVA", self.fc, T - 171.10, OUT_W / 2, OUT_H * 0.42, 70, (200, 200, 210))
            texto_pop(f, "Nº 1", self.fc, T - 171.10, OUT_W / 2, OUT_H * 0.52, 160, (255, 255, 255))
        return f

    # ---------- legenda com cores próprias ----------
    def legenda(self, img, t):
        cor_orig = vc.DESTAQUE_VERMELHO
        vc.DESTAQUE_VERMELHO = set()
        super().legenda(img, t)
        vc.DESTAQUE_VERMELHO = cor_orig

    # ---------- montagem ----------
    def frame(self, n):
        t = n / FPS
        self.T = t
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if t < ini + d or i == len(self.planos) - 1:
                tl = t - ini
                f = vc.gradear(fn(tl, d), clima)
                T_ = 0.2
                if i > 0 and tl < T_ and tr != "corte":
                    pi, pd, pfn, pcl, _ = self.planos[i - 1]
                    self.T = pi + pd - 0.001
                    prev = vc.gradear(pfn(pd - 0.001, pd), pcl)
                    self.T = t
                    x = tl / T_
                    if tr == "whip":
                        off = int(OUT_W * ease_io(x))
                        comp = Image.new("RGB", (OUT_W, OUT_H))
                        comp.paste(prev, (-off, 0))
                        comp.paste(f, (OUT_W - off, 0))
                        f = g.motion_blur_h(comp, 60 * math.sin(math.pi * x))
                    elif tr == "dissolve":
                        f = Image.blend(prev, f, ease_io(x))
                    elif tr == "zoom":
                        f = g.zoom_blur(Image.blend(prev, f, ease_io(x)), 0.35 * math.sin(math.pi * x))
                if fn != self.p_preto:
                    f = g.vinheta(f, 0.35)
                    self.legenda(f, t)
                return f

    def eventos_sfx(self):
        ev = []
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if i and tr in ("whip", "zoom"):
                ev.append(("whoosh", ini - 0.08))
            elif i and tr == "corte" and fn not in (self.p_preto, self.p_estatua_final):
                ev.append(("pop", ini))
        return ev


# --------------------------------------------------------------------------
# Áudio: voz + trilha (some antes do grito final) + gelo/descongelar
# --------------------------------------------------------------------------
def sfx_gelo():
    SR = g.SR
    t = np.arange(int(SR * 0.9)) / SR
    rng = np.random.default_rng(7)
    crack = rng.standard_normal(len(t)) * np.exp(-t * 18)
    crack = np.diff(np.concatenate([[0], crack])) * 0.8                       # agudo
    ping = (np.sin(2 * np.pi * 2400 * t) + 0.5 * np.sin(2 * np.pi * 3600 * t)) * np.exp(-t * 5) * 0.25
    boom = np.sin(2 * np.pi * (70 - 30 * t) * t) * np.exp(-t * 4) * 0.7
    return crack + ping + boom


def sfx_degelo():
    SR = g.SR
    t = np.arange(int(SR * 1.2)) / SR
    out = np.zeros_like(t)
    for j, f in enumerate((523, 659, 784, 1047)):
        tt = t - j * 0.06
        m = tt > 0
        out[m] += np.sin(2 * np.pi * f * tt[m]) * np.exp(-tt[m] * 3) * 0.18
    return out


def mixar(filme, narracao, saida):
    SR = g.SR
    voz = vc.ler_wav_mono(narracao)
    n = int(filme.dur_total * SR)
    mix = np.zeros(n, np.float32)
    mix[:min(n, len(voz))] += voz[:n]
    mus = g.trilha(filme.dur_total)
    mus = mus / max(1e-6, np.abs(mus).max()) * 0.14
    tt = np.arange(len(mus)) / SR
    env = np.clip((169.2 - tt) / 0.8, 0, 1)                 # silêncio total antes do "ESTÁTUA!" final
    env *= np.where((tt > 149.2) & (tt < 149.9), 0.25, 1.0)  # quase silêncio antes do "Sim."
    mix[:len(mus)] += (mus * env)[:n]
    eventos = filme.eventos_sfx()
    eventos += [("gelo", x) for x in GRITOS if x != 138.62] + [("degelo", 138.62), ("degelo", 8.34),
                                                                ("brilho", 149.88)]
    for tipo, t0 in eventos:
        s = {"gelo": sfx_gelo, "degelo": sfx_degelo}.get(tipo, lambda: g.sfx(tipo))()
        if tipo in ("whoosh", "pop"):
            s = s * 0.3
        a = int(max(0, t0) * SR)
        b = min(n, a + len(s))
        mix[a:b] += s[: b - a]
    mix = mix / max(1.0, np.abs(mix).max() / 0.95)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def carregar_palavras(caminho):
    pal = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            pal.append(dict(w=w["w"], s=w["s"], e=w["e"]))
    troca = {"Beber": "Bebê", "joelhado": "ajoelhado", "Zéfa,": "Zefa,", "antonio": "Antônio",
             "Lourdes.": "Lurdes.", "Lourdes,": "Lurdes,", "38ª,": "trigésima oitava,", "1.": "um."}
    out = []
    for w in pal:
        txt = troca.get(w["w"], w["w"])
        s = round(w["s"], 2)
        if s in (100.28, 169.88):
            txt = "ESTÁTUA!"
        if s == 138.62:
            txt = "DESESTÁTUA!"
        out.append(dict(w=txt, s=w["s"], e=w["e"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_estatua.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeEstatua(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.0, a.narracao)
    total = int(filme.dur_total * FPS)

    if a.testar:
        for ini, d, *_r in filme.planos:
            for k in (0.01, 0.5, 0.99):
                filme.frame(int((ini + d * k) * FPS))
        print("todos os planos ok")
        return
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        for i, (ini, d, *_r) in enumerate(filme.planos):
            filme.frame(int((ini + d * 0.6) * FPS)).save(os.path.join(a.preview, f"plano_{i:02d}.png"))
        print("preview em", a.preview)
        return

    tmp = tempfile.mkdtemp(prefix="estatua_")
    wav = os.path.join(tmp, "mix.wav")
    mixar(filme, a.narracao, wav)
    print(f"• renderizando {total} frames ({filme.dur_total:.1f}s)…", flush=True)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}",
         "-r", str(FPS), "-i", "-", "-i", wav, "-vf", "scale=1080:1920:flags=lanczos",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.saida],
        stdin=subprocess.PIPE)
    for n in range(total):
        proc.stdin.write(filme.frame(n).tobytes())
        if n % 150 == 0:
            print(f"  {n}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("✔ vídeo salvo em", a.saida)


if __name__ == "__main__":
    main()
