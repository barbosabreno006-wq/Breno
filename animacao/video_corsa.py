#!/usr/bin/env python3
"""
"O Corsa do Murillo" — história emocional de superação, sincronizada com a narração.

    python3 animacao/remover_silencios.py narracao.mp3 narr.wav
    (faster-whisper -> transcricao.json)
    python3 animacao/video_corsa.py --narracao narr.wav --transcricao transcricao.json --fonte Poppins.ttf
"""
import argparse
import json
import math
import os
import random
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_video as g  # noqa: E402
import video_carta as vc  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, Ator, gradiente, brilho,
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(44)

MURILLO = dict(pele=(222, 170, 128), cabelo=(45, 32, 28), camisa=(210, 50, 50), calca=(40, 45, 60),
               sapato=(240, 240, 240), tipo="pai", bigode=False, chapeu=(200, 40, 40))
MURILLO_MEC = dict(MURILLO, camisa=(70, 95, 140), calca=(70, 95, 140), chapeu=None, sapato=(60, 50, 45))
FERNANDO = dict(pele=(232, 186, 150), cabelo=(30, 25, 25), camisa=(245, 245, 245), calca=(40, 40, 45),
                sapato=(30, 30, 30), tipo="pai", chapeu=(250, 250, 250))
ZE = dict(pele=(196, 140, 100), cabelo=(185, 185, 190), camisa=(60, 95, 160), calca=(60, 95, 160),
          sapato=(70, 55, 45), tipo="pai")
RISOS = [dict(pele=(150, 100, 70), cabelo=(30, 25, 25), camisa=(240, 190, 60), calca=(60, 70, 120),
              sapato=(200, 60, 60), tipo="pai", bigode=False),
         dict(pele=(235, 190, 150), cabelo=(200, 140, 60), camisa=(150, 110, 200), calca=(0, 0, 0),
              sapato=(120, 60, 120), tipo="moca", vestido=(170, 130, 220)),
         dict(pele=(190, 130, 90), cabelo=(60, 40, 30), camisa=(90, 170, 110), calca=(80, 70, 60),
              sapato=(60, 60, 60), tipo="pai", bigode=False)]

PRATA = (200, 205, 212)
vc.DESTAQUE_VERMELHO = {"nada,", "Murillo.", "falta.", "inútil.", "chorando.", "fundido.", "Fernando."}


# --------------------------------------------------------------------------
# Veículos
# --------------------------------------------------------------------------
def roda(r=72):
    p = Pincel(r * 2 + 20, r * 2 + 20)
    c = r + 10
    p.elipse((c - r, c - r, c + r, c + r), (35, 35, 40))
    p.elipse((c - r * 0.6, c - r * 0.6, c + r * 0.6, c + r * 0.6), (190, 195, 200), ow=5)
    for a in range(0, 360, 72):
        x, y = c + r * 0.5 * math.cos(math.radians(a)), c + r * 0.5 * math.sin(math.radians(a))
        p.linha([(c, c), (x, y)], fill=(120, 125, 130), w=8)
    p.elipse((c - 12, c - 12, c + 12, c + 12), (120, 125, 130), ow=4)
    return p.pronto()


def corsa(cor=PRATA, vidro=(40, 45, 60), w=900, h=420):
    """Sedã 3 volumes estilo 'Classic', visto de lado (frente à direita). Sem rodas."""
    p = Pincel(w, h)
    p.poli([(250, 210), (330, 110), (590, 105), (690, 210)], cor)                       # cabine
    p.poli([(275, 205), (345, 125), (455, 122), (455, 205)], vidro, ow=6)
    p.poli([(475, 205), (475, 122), (580, 120), (660, 205)], vidro, ow=6)
    p.ret((40, 200, 870, 330), cor, r=40)                                                # carroceria
    p.poli([(40, 215), (70, 185), (250, 195), (250, 230)], cor, ow=0)                    # porta-malas
    p.linha([(470, 210), (470, 320)], w=5)
    p.linha([(60, 255), (860, 255)], fill=(170, 175, 182), w=5)
    p.ret((400, 230, 440, 242), (120, 125, 130), r=5, ow=3)
    p.ret((600, 230, 640, 242), (120, 125, 130), r=5, ow=3)
    p.elipse((820, 220, 875, 255), (255, 235, 150), ow=5)                                # farol
    p.ret((35, 220, 65, 260), (220, 50, 50), r=6, ow=5)                                  # lanterna
    p.ret((30, 300, 880, 335), (60, 60, 65), r=14, ow=5)                                 # para-choque
    for x in (210, 700):                                                                  # caixas de roda
        p.elipse((x - 90, 250, x + 90, 420), (25, 25, 30), ow=0)
    # brilho no vidro
    p.poli([(360, 200), (420, 128), (445, 128), (385, 200)], (110, 120, 140), ow=0)
    return p.pronto()


class Carro:
    def __init__(self, cor=PRATA, vidro=(40, 45, 60)):
        self.corpo = corsa(cor, vidro)
        self.roda = roda()

    def desenhar(self, base, cx, by, escala=1.0, giro=0.0, pulo=0.0, espelhar=False):
        corpo = self.corpo
        w, h = int(corpo.width * escala), int(corpo.height * escala)
        c = corpo.resize((w, h), Image.BICUBIC)
        if espelhar:
            c = c.transpose(Image.FLIP_LEFT_RIGHT)
        x0, y0 = int(cx - w / 2), int(by - h - pulo)
        r = self.roda.rotate(-giro, resample=Image.BICUBIC).resize((int(164 * escala), int(164 * escala)))
        base.alpha_composite(c, (x0, y0))
        for rx in (210, 700):
            xx = (900 - rx) if espelhar else rx
            base.alpha_composite(r, (int(x0 + (xx - 82) * escala), int(y0 + (338 - 82) * escala + pulo)))


def ferrari():
    p = Pincel(900, 360)
    p.poli([(40, 240), (120, 190), (330, 170), (430, 110), (620, 110), (760, 190), (880, 215), (880, 280),
            (40, 290)], (220, 30, 30))
    p.poli([(440, 175), (470, 125), (600, 125), (690, 180)], (40, 45, 60), ow=5)
    for x in (220, 720):
        p.elipse((x - 66, 220, x + 66, 352), (30, 30, 35))
        p.elipse((x - 34, 252, x + 34, 320), (230, 200, 60), ow=4)
    return p.pronto()


def moto():
    p = Pincel(700, 420)
    for x in (150, 560):
        p.elipse((x - 110, 200, x + 110, 420), (30, 30, 35))
        p.elipse((x - 60, 250, x + 60, 370), (200, 200, 205), ow=4)
    p.poli([(150, 310), (300, 200), (480, 200), (560, 310), (420, 300)], (40, 110, 200))
    p.ret((260, 160, 420, 210), (30, 30, 35), r=20)
    p.linha([(480, 200), (540, 110)], w=14)
    p.linha([(520, 110), (580, 110)], w=12)
    return p.pronto()


def x_vermelho(img):
    d = ImageDraw.Draw(img)
    w, h = img.size
    for a, b in (((40, 40), (w - 40, h - 40)), ((w - 40, 40), (40, h - 40))):
        d.line((a, b), fill=(20, 20, 26), width=46)
        d.line((a, b), fill=(230, 40, 40), width=30)
    return img


def guincho(carro_corpo):
    p = Pincel(1300, 560)
    p.ret((20, 330, 1000, 410), (230, 170, 40), r=10)                 # plataforma
    p.ret((960, 160, 1260, 440), (230, 170, 40), r=30)               # cabine
    p.ret((1050, 190, 1230, 300), (60, 70, 90), r=14, ow=6)
    p.ret((960, 400, 1280, 450), (60, 60, 65), r=10)
    p.elipse((1250, 330, 1290, 370), (255, 235, 150), ow=5)
    p.ret((1100, 130, 1160, 165), (240, 120, 30), r=8)                # giroflex
    img = p.pronto()
    r = roda().resize((150, 150))
    for x in (120, 760, 1090):
        img.alpha_composite(r, (x, 400))
    c = carro_corpo.resize((800, 373))
    img.alpha_composite(c, (90, 0))
    return img


# --------------------------------------------------------------------------
# Objetos
# --------------------------------------------------------------------------
def pizza(fatias=8, w=700):
    p = Pincel(w, w)
    c = w / 2
    p.elipse((10, 10, w - 10, w - 10), (225, 165, 90))
    p.elipse((50, 50, w - 50, w - 50), (205, 60, 45), ow=0)
    p.elipse((70, 70, w - 70, w - 70), (250, 210, 100), ow=0)
    rng = random.Random(3)
    for _ in range(12):
        a, rr = rng.uniform(0, 6.28), rng.uniform(40, w / 2 - 120)
        x, y = c + rr * math.cos(a), c + rr * math.sin(a)
        p.elipse((x - 34, y - 34, x + 34, y + 34), (190, 50, 45), ow=4)
    for k in range(fatias):
        a = math.radians(k * 45)
        p.linha([(c, c), (c + (w / 2 - 12) * math.cos(a), c + (w / 2 - 12) * math.sin(a))], w=6)
    return p.pronto()


def cortador():
    p = Pincel(420, 420)
    p.capsula((200, 200), (390, 390), 40, (60, 60, 70))
    p.elipse((60, 60, 260, 260), (215, 220, 228), ow=7)
    p.elipse((140, 140, 180, 180), (90, 90, 100), ow=4)
    return p.pronto()


def pote(aberto=False, moedas=0):
    p = Pincel(520, 460)
    p.ret((60, 140, 460, 440), (250, 225, 90), r=40)
    p.ret((60, 230, 460, 330), (250, 250, 250), r=0, ow=0)
    if aberto:
        p.elipse((60, 100, 460, 180), (90, 70, 50))
        rng = random.Random(5)
        for _ in range(min(40, moedas)):
            x, y = rng.uniform(110, 410), rng.uniform(95, 165)
            p.elipse((x - 26, y - 14, x + 26, y + 14), (235, 195, 70), ow=4)
    else:
        p.ret((40, 90, 480, 150), (240, 210, 70), r=20)
    img = p.pronto()
    return img


def moeda():
    p = Pincel(90, 90)
    p.elipse((6, 6, 84, 84), (235, 195, 70), ow=6)
    p.elipse((24, 24, 66, 66), (250, 215, 100), ow=0)
    return p.pronto()


def bicicleta():
    p = Pincel(900, 520)
    for x, murcho in ((200, True), (700, False)):
        if murcho:
            p.chord((x - 150, 270, x + 150, 560), 180, 360, (35, 35, 40))
            p.ret((x - 160, 400, x + 160, 440), (35, 35, 40), r=16)
        else:
            p.elipse((x - 150, 210, x + 150, 510), (35, 35, 40))
            p.elipse((x - 125, 235, x + 125, 485), (235, 235, 240), ow=0)
    p.linha([(200, 380), (420, 380), (700, 360), (560, 180), (330, 180), (200, 380)], fill=(40, 120, 200), w=20)
    p.linha([(330, 180), (420, 380)], fill=(40, 120, 200), w=20)
    p.ret((290, 140, 400, 175), (30, 30, 35), r=12)
    p.linha([(560, 180), (600, 100), (660, 100)], w=12)
    return p.pronto()


def dinheiro(maços=5):
    p = Pincel(800, 520)
    for i in range(maços):
        x, y = 60 + (i % 3) * 230, 280 - (i // 3) * 140 + (i % 2) * 20
        p.ret((x, y, x + 260, y + 120), (110, 190, 140), r=10)
        p.ret((x + 100, y, x + 150, y + 120), (240, 240, 240), r=0, ow=0)
        p.elipse((x + 20, y + 30, x + 80, y + 90), (80, 160, 110), ow=4)
    return p.pronto()


def chave_carro():
    p = Pincel(420, 300)
    p.ret((30, 60, 190, 240), (40, 40, 45), r=50)
    p.elipse((80, 110, 140, 170), (200, 40, 40), ow=4)
    p.ret((180, 130, 400, 170), (210, 210, 215), r=8)
    for x in (300, 350):
        p.ret((x, 165, x + 22, 200), (210, 210, 215), r=3, ow=4)
    return p.pronto()


def pernas_debaixo():
    p = Pincel(500, 200)
    for y in (40, 120):
        p.capsula((20, y + 20), (360, y + 20), 54, ZE["calca"])
        p.elipse((350, y - 14, 470, y + 54), ZE["sapato"])
    return p.pronto()


def chave_inglesa():
    p = Pincel(500, 160)
    p.ret((80, 60, 440, 100), (180, 185, 195), r=16)
    p.elipse((10, 20, 130, 140), (180, 185, 195))
    p.ret((0, 60, 60, 100), (120, 120, 130), r=0, ow=0)
    return p.pronto()


def motor():
    p = Pincel(800, 600)
    p.ret((100, 160, 700, 520), (90, 95, 105), r=30)
    p.ret((160, 80, 640, 200), (120, 125, 135), r=20)
    for x in (220, 340, 460, 580):
        p.elipse((x - 30, 100, x + 30, 160), (60, 60, 70), ow=5)
    p.ret((60, 260, 140, 420), (60, 65, 75), r=16)
    p.ret((680, 260, 760, 420), (60, 65, 75), r=16)
    p.elipse((300, 300, 500, 500), (140, 140, 150), ow=8)
    p.elipse((360, 360, 440, 440), (70, 70, 80), ow=5)
    return p.pronto()


def galao_oleo():
    p = Pincel(400, 500)
    p.ret((60, 120, 340, 480), (230, 170, 30), r=30)
    p.ret((240, 40, 320, 140), (230, 170, 30), r=14)
    p.ret((100, 240, 300, 340), (40, 40, 50), r=10, ow=0)
    return p.pronto()


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def pizzaria(fc):
    base = gradiente(WW, WH, (180, 90, 60), (150, 70, 45))
    p = Pincel(WW, WH)
    for row, y in enumerate(range(0, 1300, 70)):           # tijolos
        for x in range(-((row % 2) * 70), WW, 140):
            p.ret((x + 4, y + 4, x + 136, y + 66), (190, 100, 70), r=6, ow=0)
    # forno a lenha
    p.chord((560, 380, 1060, 1100), 180, 360, (170, 160, 150))
    p.ret((560, 730, 1060, 1300), (170, 160, 150), r=10)
    p.chord((680, 700, 940, 1000), 180, 360, (30, 20, 20))
    p.ret((680, 840, 940, 1000), (30, 20, 20), r=0, ow=0)
    p.ret((-20, 1300, WW + 20, WH + 20), (120, 80, 60), r=0)
    p.ret((60, 120, 500, 260), (40, 90, 50), r=16)
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((700, 700), (255, 150, 50), 350, 0.8), (460, 550))
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 64)
    d.text((280 - f.getlength("PIZZARIA") / 2, 150), "PIZZARIA", font=f, fill=(250, 240, 210))
    return base


def fogo(t):
    p = Pincel(260, 200)
    for i in range(5):
        x = 30 + i * 45
        h = 90 + 40 * math.sin(t * 9 + i * 1.7)
        p.elipse((x, 190 - h, x + 60, 195), (255, 140, 30), ow=0)
        p.elipse((x + 12, 190 - h * 0.6, x + 48, 195), (255, 220, 90), ow=0)
    return p.pronto()


def balcao():
    p = Pincel(WW, 600)
    p.ret((20, 30, WW - 20, 110), (90, 60, 40), r=12)
    p.ret((50, 100, WW - 50, 600), (160, 40, 40), r=10)
    for x in range(110, WW - 100, 160):
        p.ret((x, 160, x + 100, 560), (190, 60, 50), r=10, ow=0)
    return p.pronto()


def oficina(fc):
    base = gradiente(WW, WH, (175, 180, 185), (150, 155, 160))
    p = Pincel(WW, WH)
    p.ret((60, 220, 660, 700), (120, 90, 60), r=10)                  # painel de ferramentas
    for i, x in enumerate(range(110, 640, 90)):
        p.ret((x, 280 + (i % 2) * 40, x + 26, 470 + (i % 2) * 40), (90, 95, 105), r=8, ow=5)
        p.elipse((x - 14, 260 + (i % 2) * 40, x + 40, 310 + (i % 2) * 40), (200, 60, 50), ow=5)
    for k in range(4):                                                # pneus empilhados
        p.elipse((780, 1100 - k * 90, 1040, 1220 - k * 90), (40, 40, 45))
        p.elipse((850, 1130 - k * 90, 970, 1190 - k * 90), (90, 90, 95), ow=4)
    p.ret((-20, 1300, WW + 20, WH + 20), (110, 110, 115), r=0)
    p.elipse((300, 1500, 700, 1600), (80, 80, 85), ow=0)              # mancha de óleo
    base.alpha_composite(p.pronto())
    return base


def fachada_oficina(fc):
    base = gradiente(WW, WH, (150, 200, 240), (220, 235, 245))
    p = Pincel(WW, WH)
    vc.nuvem(p, 120, 240, 0.9)
    p.ret((60, 520, 1020, 1420), (230, 200, 120), r=8)
    p.ret((100, 560, 980, 700), (60, 95, 160), r=12)
    p.ret((180, 780, 900, 1420), (60, 60, 70), r=10)                  # portão aberto
    for y in range(800, 1000, 40):
        p.linha([(180, y), (900, y)], fill=(100, 100, 110), w=6)
    p.ret((-20, 1410, WW + 20, 1500), (190, 185, 175), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (90, 90, 100), r=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 64)
    t = "OFICINA DO ZÉ"
    d.text((540 - f.getlength(t) / 2, 595), t, font=f, fill=(250, 240, 200))
    return base


def rua(fc, sol=False, chuva=False):
    base = gradiente(WW, WH, (250, 180, 120) if sol else ((120, 125, 140) if chuva else (150, 200, 240)),
                     (255, 220, 170) if sol else ((150, 150, 160) if chuva else (225, 240, 250)))
    p = Pincel(WW, WH)
    if sol:
        p.elipse((380, 620, 700, 940), (255, 220, 120), ow=0)
    for i, x in enumerate((-60, 250, 560, 870)):
        top = 760 + (i % 2) * 60
        p.ret((x, top, x + 290, 1420), g.CORES_CASAS[i], r=6)
        p.poli([(x - 15, top + 4), (x + 145, top - 140), (x + 305, top + 4)], (160, 85, 75))
        p.ret((x + 40, top + 80, x + 120, top + 190), (255, 240, 200), r=8, ow=6)
    p.ret((-20, 1410, WW + 20, 1500), (200, 190, 175), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (90, 90, 100), r=0)
    for x in range(0, WW, 220):
        p.ret((x + 40, 1700, x + 150, 1722), (230, 220, 150), r=6, ow=0)
    base.alpha_composite(p.pronto())
    return base


def quarto():
    base = gradiente(WW, WH, (200, 210, 230), (180, 190, 215))
    p = Pincel(WW, WH)
    p.ret((-20, 1450, WW + 20, WH + 20), (160, 125, 100), r=0)
    p.ret((80, 1000, 1000, 1300), (90, 120, 180), r=30)
    p.ret((80, 920, 360, 1060), (240, 240, 245), r=30)
    p.ret((60, 900, 110, 1460), (130, 90, 60), r=12)
    p.ret((970, 1000, 1020, 1460), (130, 90, 60), r=12)
    p.ret((110, 1290, 970, 1460), (40, 40, 50), r=0, ow=0)          # vão embaixo da cama
    base.alpha_composite(p.pronto())
    return base


def gotas(f, t, n=60, cor=(200, 210, 230)):
    d = ImageDraw.Draw(f)
    rng = random.Random(9)
    for _ in range(n):
        x = rng.uniform(0, OUT_W)
        y = (rng.uniform(0, OUT_H) + t * 900) % OUT_H
        d.line((x, y, x - 6, y + 30), fill=cor, width=3)


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeCorsa(vc.Filme):
    def __init__(self, palavras, fc, dur_total):
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.mu, self.mu_mec = Ator(MURILLO), Ator(MURILLO_MEC)
        self.fer, self.ze = Ator(FERNANDO), Ator(ZE)
        self.risos = [Ator(c) for c in RISOS]
        self.corsa = Carro()
        self.carro_fer = Carro((70, 110, 80), (40, 45, 60))
        self.ferrari = x_vermelho(ferrari())
        self.moto = x_vermelho(moto())
        self.guincho = guincho(self.carro_fer.corpo)
        self.pizzaria = pizzaria(fc)
        self.balcao = balcao()
        self.pizza = [pizza(k) for k in range(9)]
        self.cort = cortador()
        self.pote_f, self.pote_a = pote(False), pote(True, 40)
        self.moeda = moeda()
        self.bike = bicicleta()
        self.dinheiro = dinheiro(5)
        self.chave = chave_carro()
        self.pernas = pernas_debaixo()
        self.inglesa = chave_inglesa()
        self.motor = motor()
        self.galao = galao_oleo()
        self.oficina = oficina(fc)
        self.fachada = fachada_oficina(fc)
        self.rua, self.rua_sol, self.rua_chuva = rua(fc), rua(fc, sol=True), rua(fc, chuva=True)
        self.quarto = quarto()
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        P = [
            (0.00, self.p_riem, "", "corte"),
            (2.74, self.p_ferrari, "", "whip"),
            (3.90, self.p_moto, "", "corte"),
            (4.86, self.p_corsa_reveal, "quente", "zoom"),
            (6.46, self.p_prata, "quente", "corte"),
            (7.10, self.p_vidro, "quente", "corte"),
            (8.40, self.p_pizzaria, "", "whip"),
            (11.32, self.p_corta, "", "corte"),
            (13.96, self.p_forno, "", "corte"),
            (16.98, self.p_oito, "", "corte"),
            (19.46, self.p_chefe, "", "whip"),
            (23.86, self.p_grita, "", "corte"),
            (25.98, self.p_mu_triste, "triste", "corte"),
            (27.22, self.p_pote, "", "dissolve"),
            (30.80, self.p_cama, "", "corte"),
            (32.38, self.p_atraso, "", "whip"),
            (35.08, self.p_bike, "", "corte"),
            (37.00, self.p_arranca, "", "whip"),
            (40.34, self.p_vai_embora, "", "corte"),
            (42.60, self.p_ninguem, "triste", "corte"),
            (44.18, self.p_volta_pe, "triste", "dissolve"),
            (46.46, self.p_fachada, "", "dissolve"),
            (48.60, self.p_debaixo, "", "corte"),
            (52.42, self.p_ze_olha, "", "corte"),
            (53.74, self.p_ze_close, "quente", "corte"),
            (55.38, self.p_ze_nome, "quente", "corte"),
            (56.14, self.p_ajudante, "", "whip"),
            (57.80, self.p_oleo, "", "corte"),
            (59.14, self.p_motor, "", "corte"),
            (60.30, self.p_ouvir, "", "corte"),
            (63.20, self.p_riem_juntos, "quente", "corte"),
            (64.88, self.p_meu_mecanico, "quente", "corte"),
            (67.18, self.p_dois_anos, "", "zoom"),
            (68.40, self.p_abre_pote, "quente", "corte"),
            (70.04, self.p_conta, "quente", "corte"),
            (71.08, self.p_valor, "quente", "corte"),
            (72.94, self.p_compra, "quente", "whip"),
            (76.40, self.p_com_corsa, "quente", "corte"),
            (78.04, self.p_guincho, "", "whip"),
            (81.02, self.p_fumaca, "", "corte"),
            (82.50, self.p_dono, "", "corte"),
            (84.98, self.p_reconhece, "triste", "corte"),
            (88.02, self.p_conserta, "", "whip"),
            (89.44, self.p_nao_cobra, "quente", "corte"),
            (90.50, self.p_ombro, "quente", "dissolve"),
            (94.82, self.p_flash_pizza, "sepia", "zoom"),
            (96.96, self.p_orgulho, "quente", "zoom"),
            (99.72, self.p_liga, "quente", "whip"),
            (102.28, self.p_final, "quente", "corte"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))

    def fundo(self, c1=(250, 220, 180), c2=(235, 190, 150)):
        return gradiente(WW, WH, c1, c2)

    # ------------------------- planos -------------------------
    def p_riem(self, t, d):
        m = self.rua.copy()
        for i, (a, x) in enumerate(zip(self.risos, (170, 900, 360))):
            rindo = int(t * 5 + i) % 2
            a.desenhar(m, t + i, x, 1700 if i < 2 else 1800, escala=0.95,
                       expr="ri" if rindo else "feliz", pulo=6 * rindo)
        self.mu.desenhar(m, t, 620, 1760, escala=1.15, expr="neutro")
        return camera(m, 540, 1250, 1.15)

    def p_ferrari(self, t, d):
        m = self.fundo((230, 230, 235), (200, 200, 210))
        self.segura(m, self.ferrari, 540, 960, 900)
        return camera(m, 540, 960, 1.05 + 0.05 * ease_io(t / d))

    def p_moto(self, t, d):
        m = self.fundo((230, 230, 235), (200, 200, 210))
        self.segura(m, self.moto, 540, 960, 760)
        return camera(m, 540, 960, 1.05 + 0.05 * ease_io(t / d))

    def p_corsa_reveal(self, t, d):
        m = self.fundo((255, 225, 160), (240, 180, 120))
        m.alpha_composite(brilho((1080, 1080), (255, 245, 200), 540, 0.9), (0, 420))
        p = Pincel(WW, WH)
        p.ret((-20, 1240, WW + 20, WH + 20), (210, 170, 130), r=0, ow=0)
        m.alpha_composite(p.pronto())
        self.corsa.desenhar(m, 540, 1300, escala=1.05)
        f = camera(m, 540, 1000, 1.0 + 0.12 * ease_io(t / d))
        particulas(f, t, 40, semente=4)
        return f

    def p_prata(self, t, d):
        m = self.fundo((255, 225, 160), (240, 180, 120))
        self.corsa.desenhar(m, 540, 1300, escala=1.05)
        f = camera(m, 330, 1150, 2.0)
        # reflexo passando na lataria
        dr = ImageDraw.Draw(f, "RGBA")
        x = -200 + (OUT_W + 400) * (t / d)
        dr.polygon([(x, 0), (x + 90, 0), (x - 160, OUT_H), (x - 250, OUT_H)], fill=(255, 255, 255, 90))
        return f

    def p_vidro(self, t, d):
        m = self.fundo((255, 225, 160), (240, 180, 120))
        self.corsa.desenhar(m, 540, 1300, escala=1.05)
        f = camera(m, 520, 1050, 2.2 + 0.1 * ease_io(t / d))
        if t > 0.5:
            k = math.sin(min(1, (t - 0.5) / 0.5) * math.pi)
            fb = brilho((260, 260), (255, 255, 255), 130, k)
            f2 = f.convert("RGBA")
            f2.alpha_composite(fb, (int(OUT_W * 0.35 - 130), int(OUT_H * 0.32 - 130)))
            f = f2.convert("RGB")
        return f

    def cena_pizzaria(self, t, fogo_on=True):
        m = self.pizzaria.copy()
        if fogo_on:
            m.alpha_composite(fogo(t), (680, 800))
        return m

    def p_pizzaria(self, t, d):
        m = self.cena_pizzaria(t)
        self.mu.desenhar(m, t, 360, 1620, escala=1.2, expr="neutro", pose="entrega")
        m.alpha_composite(self.balcao, (0, 1350))
        self.segura(m, self.pizza[8], 640, 1360, 300)
        f = camera(m, 540, 1150, 1.1)
        if t > 0.26:
            texto_pop(f, "18 ANOS", self.fc, t - 0.26, OUT_W / 2, OUT_H * 0.12, 100, (255, 214, 40))
        return f

    def p_corta(self, t, d):
        m = self.fundo((120, 80, 60), (90, 60, 45))
        k = min(8, int(t / (d / 8)) + 1)
        self.segura(m, self.pizza[k], 540, 960, 900)
        a = math.radians((k - 1) * 45)
        fr = (t % (d / 8)) / (d / 8)
        cx = 540 + math.cos(a) * 380 * fr
        cy = 960 + math.sin(a) * 380 * fr
        cort = self.cort.rotate(-t * 600, resample=Image.BICUBIC)
        self.segura(m, cort, cx + 70, cy - 70, 320)
        return camera(m, 540, 960, 1.05)

    def p_forno(self, t, d):
        m = self.cena_pizzaria(t)
        self.mu.desenhar(m, t, 420, 1700, escala=1.45, expr="triste")
        f = camera(m, 560, 1150, 1.2)
        if t > 0.2:
            texto_pop(f, "8 HORAS", self.fc, t - 0.2, OUT_W * 0.5, OUT_H * 0.12, 96, (255, 214, 40))
        d_ = ImageDraw.Draw(f)
        for i in range(3):   # gotas de suor
            y = OUT_H * 0.32 + ((t * 140 + i * 60) % 120)
            d_.ellipse((OUT_W * 0.25 + i * 20, y, OUT_W * 0.25 + i * 20 + 14, y + 22), fill=(140, 200, 255))
        return f

    def p_oito(self, t, d):
        m = self.fundo((120, 80, 60), (90, 60, 45))
        for i in range(3):
            if t > i * 0.5:
                self.segura(m, self.pizza[8], 260 + (i % 2) * 560, 600 + i * 420, 480)
        f = camera(m, 540, 960, 1.0)
        if t > 0.2:
            texto_pop(f, "8", self.fc, t - 0.2, OUT_W * 0.5, OUT_H * 0.5, 240, (255, 214, 40))
        return f

    def p_chefe(self, t, d):
        m = self.cena_pizzaria(t)
        self.fer.desenhar(m, t, 760, 1600, escala=1.35, expr="bravo" if t > d * 0.5 else "neutro")
        self.mu.desenhar(m, t, 330, 1650, escala=1.2, expr="triste", pose="entrega")
        m.alpha_composite(self.balcao, (0, 1380))
        self.segura(m, self.pizza[8], 420, 1390, 280)
        f = camera(m, 540, 1150, 1.1 + 0.06 * ease_io(t / d))
        if t > 1.5:
            texto_pop(f, "SEU FERNANDO", self.fc, t - 1.5, OUT_W * 0.64, OUT_H * 0.14, 64, (255, 120, 90))
        return f

    def p_grita(self, t, d):
        m = self.fundo((190, 90, 70), (150, 60, 45))
        self.fer.desenhar(m, t, 540, 2450, escala=2.7, expr="bravo", piscar=False)
        f = camera(m, 540, 1000, 1.05 + 0.25 * ease_out(t / 0.3))
        if t < 0.6:
            f = f.transform(f.size, Image.AFFINE, (1, 0, 6 * math.sin(t * 60), 0, 1, 0))
        return f

    def p_mu_triste(self, t, d):
        m = self.fundo((210, 200, 195), (180, 170, 165))
        self.mu.desenhar(m, t, 540, 2450, escala=2.7, expr="triste", piscar=False)
        return camera(m, 540, 1000, 1.05 + 0.08 * ease_io(t / d))

    def p_pote(self, t, d):
        m = self.fundo((240, 225, 200), (215, 200, 175))
        self.segura(m, self.pote_a, 540, 1180, 640)
        for i in range(5):
            tt = t - i * 0.55
            if tt > 0:
                y = 300 + 760 * min(1, tt / 0.45)
                if tt < 0.55:
                    self.segura(m, self.moeda, 540 + (i - 2) * 30, y, 110, rot=tt * 500)
        return camera(m, 540, 1000, 1.05 + 0.05 * ease_io(t / d))

    def p_cama(self, t, d):
        m = self.quarto.copy()
        k = ease_io(min(1, t / 1.0))
        self.segura(m, self.pote_f, 1000 - 420 * k, 1390, 200)
        p = Pincel(WW, 200)
        p.ret((80, 0, 1000, 60), (90, 120, 180), r=20, ow=0)
        return camera(m, 540, 1250, 1.25)

    def p_atraso(self, t, d):
        m = self.fundo((240, 235, 230), (215, 210, 205))
        p = Pincel(WW, WH)
        p.elipse((240, 560, 840, 1160), (255, 255, 255), ow=16)
        for k in range(12):
            a = math.radians(k * 30)
            p.linha([(540 + 250 * math.cos(a), 860 + 250 * math.sin(a)),
                     (540 + 280 * math.cos(a), 860 + 280 * math.sin(a))], w=8)
        a = math.radians(-90 + 30 * (t / d))
        p.linha([(540, 860), (540 + 230 * math.cos(a), 860 + 230 * math.sin(a))], w=14)
        p.linha([(540, 860), (540 + 150 * math.cos(math.radians(-60)), 860 + 150 * math.sin(math.radians(-60)))],
                w=18)
        m.alpha_composite(p.pronto())
        f = camera(m, 540, 960, 1.05)
        if t > 0.9:
            texto_pop(f, "+5 MIN", self.fc, t - 0.9, OUT_W * 0.5, OUT_H * 0.2, 110, (230, 50, 50))
        return f

    def p_bike(self, t, d):
        m = self.rua.copy()
        self.segura(m, self.bike, 540, 1500, 900)
        f = camera(m, 540, 1300, 1.25)
        if t > 0.3:
            texto_pop(f, "PSSSS…", self.fc, t - 0.3, OUT_W * 0.3, OUT_H * 0.3, 80)
        return f

    def p_arranca(self, t, d):
        m = self.cena_pizzaria(t)
        self.fer.desenhar(m, t, 760, 1600, escala=1.35, expr="bravo", pose="entrega" if t < 1.6 else "idle")
        self.mu.desenhar(m, t, 330, 1650, escala=1.2, expr="surpreso" if t > 1.6 else "triste", pose="entrega")
        m.alpha_composite(self.balcao, (0, 1380))
        # o cortador sai da mão do Murillo e voa até o Fernando
        k = ease_out(min(1, max(0, (t - 1.5) / 0.6)))
        x = 520 + 220 * k
        y = 1240 - 200 * math.sin(k * math.pi)
        self.segura(m, self.cort.rotate(-k * 720), x, y, 180)
        return camera(m, 540, 1150, 1.15 + 0.08 * ease_io(t / d))

    def p_vai_embora(self, t, d):
        m = self.cena_pizzaria(t)
        self.fer.desenhar(m, t, 620, 1650, escala=1.6, expr="bravo", pose="aponta")
        return camera(m, 540, 1150, 1.2)

    def p_ninguem(self, t, d):
        m = self.fundo((200, 195, 195), (170, 165, 165))
        self.mu.desenhar(m, t, 540, 2450, escala=2.7, expr="chora", piscar=False)
        return camera(m, 540, 1000, 1.05 + 0.1 * ease_io(t / d))

    def p_volta_pe(self, t, d):
        off = (t * 220) % WW
        m = Image.new("RGBA", (WW, WH))
        m.alpha_composite(self.rua_chuva, (int(-off), 0))
        m.alpha_composite(self.rua_chuva, (int(WW - off), 0))
        self.mu.desenhar(m, t, 540, 1760, escala=1.3, expr="chora", rot=3 * math.sin(t * 6),
                         pulo=8 * abs(math.sin(t * 6)))
        f = camera(m, 540, 1200, 1.15)
        gotas(f, t)
        return f

    def p_fachada(self, t, d):
        m = self.fachada.copy()
        self.mu.desenhar(m, t, 230, 1760, escala=1.0, expr="triste")
        return camera(m, 560, 1100, 1.05 + 0.1 * ease_io(t / d))

    def p_debaixo(self, t, d):
        m = self.oficina.copy()
        self.carro_fer.desenhar(m, 470, 1480, escala=1.0)
        self.segura(m, self.pernas, 780 + 6 * math.sin(t * 8), 1440, 360)
        f = camera(m, 560, 1250, 1.2)
        if t > 2.3:
            texto_pop(f, "graxa", self.fc, t - 2.3, OUT_W * 0.25, OUT_H * 0.25, 60, (60, 60, 60))
        return f

    def p_ze_olha(self, t, d):
        m = self.oficina.copy()
        self.carro_fer.desenhar(m, 400, 1480, escala=1.0)
        self.ze.desenhar(m, t, 820, 1700, escala=1.3, expr="neutro")
        return camera(m, 640, 1200, 1.2)

    def p_ze_close(self, t, d):
        m = self.fundo((200, 205, 210), (170, 175, 180))
        self.ze.desenhar(m, t, 540, 2450, escala=2.7, expr="feliz", piscar=False)
        f = camera(m, 540, 1000, 1.05 + 0.08 * ease_io(t / d))
        d_ = ImageDraw.Draw(f, "RGBA")
        for (x, y) in ((0.3, 0.55), (0.66, 0.42)):   # manchas de graxa
            d_.ellipse((OUT_W * x - 20, OUT_H * y - 10, OUT_W * x + 20, OUT_H * y + 10), fill=(40, 40, 40, 140))
        return f

    def p_ze_nome(self, t, d):
        m = self.oficina.copy()
        self.ze.desenhar(m, t, 380, 1700, escala=1.35, expr="feliz", pose="acena")
        self.mu.desenhar(m, t, 760, 1700, escala=1.25, expr="surpreso")
        f = camera(m, 560, 1200, 1.15)
        texto_pop(f, "SEU ZÉ", self.fc, t, OUT_W * 0.33, OUT_H * 0.14, 90, (255, 214, 40))
        return f

    def p_ajudante(self, t, d):
        m = self.oficina.copy()
        self.ze.desenhar(m, t, 340, 1700, escala=1.3, expr="feliz")
        e = 1.25
        self.mu_mec.desenhar(m, t, 760, 1700, escala=e, expr="feliz", pose="entrega")
        hx, hy = self.mao(760, 1700, e, t)
        self.segura(m, self.inglesa, hx + 40, hy - 10, 220, rot=30)
        return camera(m, 560, 1200, 1.15)

    def p_oleo(self, t, d):
        m = self.fundo((170, 175, 180), (140, 145, 150))
        self.segura(m, self.motor, 540, 1250, 800)
        gal = self.galao.rotate(-110 * ease_out(min(1, t / 0.4)), expand=True, resample=Image.BICUBIC)
        self.segura(m, gal, 640, 640, 360)
        if t > 0.4:
            p = Pincel(WW, WH)
            p.ret((470, 720, 500, 1040), (230, 170, 30), r=14, ow=0)
            m.alpha_composite(p.pronto())
        return camera(m, 540, 960, 1.1)

    def p_motor(self, t, d):
        m = self.fundo((170, 175, 180), (140, 145, 150))
        self.segura(m, self.motor, 540, 1100, 900)
        self.segura(m, self.inglesa, 560, 1100, 480, rot=-30 * math.sin(t * 8))
        return camera(m, 540, 1050, 1.15)

    def p_ouvir(self, t, d):
        m = self.oficina.copy()
        self.carro_fer.desenhar(m, 360, 1520, escala=1.0, pulo=3 * math.sin(t * 40))
        self.mu_mec.desenhar(m, t, 820, 1700, escala=1.25, expr="neutro" if t < 1.6 else "feliz", rot=-8)
        f = camera(m, 600, 1250, 1.2)
        d_ = ImageDraw.Draw(f)
        for i in range(3):     # ondas de som
            r = 30 + ((t * 120 + i * 40) % 120)
            d_.arc((OUT_W * 0.62 - r, OUT_H * 0.55 - r, OUT_W * 0.62 + r, OUT_H * 0.55 + r), 150, 210,
                   fill=(40, 40, 50), width=6)
        if t > 1.6:
            texto_pop(f, "!", self.fc, t - 1.6, OUT_W * 0.8, OUT_H * 0.25, 140, (255, 214, 40))
        return f

    def p_riem_juntos(self, t, d):
        m = self.oficina.copy()
        r = int(t * 5) % 2
        self.ze.desenhar(m, t, 360, 1700, escala=1.3, expr="ri" if r else "feliz", pulo=6 * r)
        self.mu_mec.desenhar(m, t, 760, 1700, escala=1.25, expr="feliz" if r else "ri", pulo=6 * (1 - r))
        return camera(m, 560, 1200, 1.15)

    def p_meu_mecanico(self, t, d):
        m = self.fundo((255, 215, 160), (240, 175, 120))
        m.alpha_composite(brilho((1080, 1080), (255, 240, 190), 540, 0.6), (0, 500))
        self.ze.desenhar(m, t, 340, 1760, escala=1.4, expr="feliz", pose="entrega")
        self.mu_mec.desenhar(m, t, 740, 1760, escala=1.3, expr="ri")
        f = camera(m, 540, 1200, 1.12)
        if t > 0.9:
            texto_pop(f, "\"MEU MECÂNICO\"", self.fc, t - 0.9, OUT_W * 0.5, OUT_H * 0.14, 70, (255, 214, 40))
        particulas(f, t, 30, semente=7)
        return f

    def p_dois_anos(self, t, d):
        m = self.fundo((60, 60, 80), (30, 30, 45))
        cal = vc.calendario(None, self.fc)
        for i in range(4):
            tt = t - i * 0.2
            if tt > 0:
                self.segura(m, cal, 540, 1000 - 30 * i, 700, rot=-20 * ease_out(min(1, tt / 0.3)) * (i < 3))
        f = camera(m, 540, 960, 1.05)
        texto_pop(f, "2 ANOS DEPOIS", self.fc, t, OUT_W * 0.5, OUT_H * 0.14, 80, (255, 255, 255))
        return f

    def p_abre_pote(self, t, d):
        m = self.fundo((240, 225, 200), (215, 200, 175))
        k = ease_out(min(1, t / 0.4))
        m.alpha_composite(brilho((900, 900), (255, 230, 120), 450, 0.9 * k), (90, 500))
        self.segura(m, self.pote_a if t > 0.3 else self.pote_f, 540, 1100, 680)
        f = camera(m, 540, 1000, 1.05)
        particulas(f, t, 30, semente=17)
        return f

    def p_conta(self, t, d):
        m = self.fundo((240, 225, 200), (215, 200, 175))
        n = 1 + int(t / 0.2)
        m.alpha_composite(dinheiro(min(5, n)), (140, 700))
        return camera(m, 540, 1000, 1.1)

    def p_valor(self, t, d):
        m = self.fundo((60, 140, 90), (40, 100, 60))
        m.alpha_composite(brilho((1000, 1000), (180, 255, 190), 500, 0.6), (40, 460))
        m.alpha_composite(self.dinheiro, (140, 1050))
        f = camera(m, 540, 1000, 1.05 + 0.05 * ease_io(t / d))
        texto_pop(f, "R$ 9.400", self.fc, t, OUT_W * 0.5, OUT_H * 0.32, 150, (255, 214, 40))
        particulas(f, t, 40, semente=27)
        return f

    def p_compra(self, t, d):
        m = self.fachada.copy()
        m.alpha_composite(brilho((1080, 1080), (255, 230, 150), 540, 0.6), (0, 700))
        k = ease_out(min(1, t / 1.4))
        self.corsa.desenhar(m, -300 + 840 * k, 1580, escala=0.95, giro=-k * 900)
        f = camera(m, 540, 1180, 1.1)
        if t > 1.6:
            self.segura_tela(f, self.chave, OUT_W * 0.5, OUT_H * 0.2, 260, t - 1.6)
        particulas(f, t, 40, semente=33)
        return f

    def segura_tela(self, f, img, x, y, w, t):
        s = 0.5 + 0.5 * ease_out(t / 0.25)
        o = img.resize((int(w * s), int(img.height * w * s / img.width)), Image.BICUBIC)
        o = o.rotate(10 * math.sin(t * 6), expand=True, resample=Image.BICUBIC)
        f.paste(o, (int(x - o.width / 2), int(y - o.height / 2)), o)

    def p_com_corsa(self, t, d):
        m = self.fachada.copy()
        self.corsa.desenhar(m, 600, 1580, escala=0.95)
        self.mu_mec.desenhar(m, t, 200, 1620, escala=1.15, expr="ri" if int(t * 4) % 2 else "feliz", pose="acena")
        f = camera(m, 480, 1180, 1.12)
        particulas(f, t, 40, semente=34)
        return f

    def p_guincho(self, t, d):
        m = self.fachada.copy()
        k = ease_out(min(1, t / 2.2))
        g2 = self.guincho.resize((1100, 474))
        m.alpha_composite(g2, (int(1100 - 1050 * k), 1240))
        f = camera(m, 540, 1250, 1.1)
        if t > 0.2:
            d_ = ImageDraw.Draw(f, "RGBA")
            if int(t * 6) % 2:
                d_.ellipse((0, 0, OUT_W, OUT_H * 0.4), fill=(255, 150, 30, 30))
        return f

    def p_fumaca(self, t, d):
        m = self.fundo((170, 175, 180), (140, 145, 150))
        self.segura(m, self.motor, 540, 1150, 900)
        f = camera(m, 540, 1000, 1.1)
        dr = ImageDraw.Draw(f, "RGBA")
        rng = random.Random(2)
        for i in range(14):
            tt = (t * 0.8 + i * 0.12) % 1.4
            x = OUT_W * 0.5 + rng.uniform(-120, 120) + 40 * math.sin(tt * 4 + i)
            y = OUT_H * 0.45 - tt * 380
            r = 30 + tt * 70
            dr.ellipse((x - r, y - r, x + r, y + r), fill=(90, 90, 95, int(160 * (1 - tt / 1.4))))
        return f

    def p_dono(self, t, d):
        m = self.fachada.copy()
        m.alpha_composite(self.guincho.resize((1100, 474)), (50, 1240))
        k = ease_out(min(1, t / 0.8))
        self.fer.desenhar(m, t, 900, 1740, escala=1.25, expr="neutro", alpha=k)
        punch = t > 84.36 - 82.50
        z = 1.1 if not punch else 1.1 + 0.8 * ease_out((t - (84.36 - 82.50)) / 0.25)
        f = camera(m, 540 if not punch else 900, 1250 if not punch else 1150, z)
        if punch and t - (84.36 - 82.50) < 0.08:
            f = Image.blend(f, Image.new("RGB", f.size, (255, 255, 255)), 0.6)
        return f

    def p_reconhece(self, t, d):
        m = self.fundo((200, 195, 195), (170, 165, 165))
        k = ease_out(max(0, t - 1.5) / 0.6)
        self.fer.desenhar(m, t, 540, 2450 + 90 * k, escala=2.7, expr="triste", rot=-7 * k, piscar=False)
        return camera(m, 540, 1000, 1.05)

    def p_conserta(self, t, d):
        m = self.oficina.copy()
        self.carro_fer.desenhar(m, 420, 1500, escala=1.0)
        e = 1.25
        self.mu_mec.desenhar(m, t, 840, 1700, escala=e, expr="neutro", pose="bate2" if int(t * 6) % 2 else "bate")
        f = camera(m, 600, 1250, 1.2)
        d_ = ImageDraw.Draw(f)
        rng = random.Random(int(t * 12))
        for _ in range(8):   # faíscas
            x, y = OUT_W * 0.62 + rng.uniform(-40, 40), OUT_H * 0.55 + rng.uniform(-40, 40)
            d_.line((x, y, x + rng.uniform(-30, 30), y + rng.uniform(-30, 30)), fill=(255, 220, 90), width=4)
        return f

    def p_nao_cobra(self, t, d):
        m = self.fachada.copy()
        self.fer.desenhar(m, t, 760, 1700, escala=1.25, expr="surpreso")
        e = 1.25
        self.mu_mec.desenhar(m, t, 330, 1700, escala=e, expr="feliz", pose="entrega")
        hx, hy = self.mao(330, 1700, e, t)
        self.segura(m, self.chave, hx + 50, hy - 10, 150)
        f = camera(m, 540, 1250, 1.15)
        texto_pop(f, "R$ 0", self.fc, t, OUT_W * 0.5, OUT_H * 0.15, 110, (90, 220, 120))
        return f

    def p_ombro(self, t, d):
        m = self.fundo((255, 210, 150), (240, 170, 110))
        m.alpha_composite(brilho((1080, 1080), (255, 240, 190), 540, 0.6), (0, 500))
        self.ze.desenhar(m, t, 360, 1760, escala=1.4, expr="feliz", pose="entrega")
        self.mu_mec.desenhar(m, t, 720, 1760, escala=1.3, expr="feliz")
        f = camera(m, 540, 1200, 1.1 + 0.08 * ease_io(t / d))
        particulas(f, t, 30, semente=41)
        return f

    def p_flash_pizza(self, t, d):
        m = self.cena_pizzaria(t, fogo_on=False)
        self.mu.desenhar(m, t, 540, 1650, escala=1.3, expr="triste", pose="entrega")
        m.alpha_composite(self.balcao, (0, 1380))
        f = camera(m, 540, 1150, 1.1)
        d_ = ImageDraw.Draw(f)
        k = ease_out(min(1, max(0, t - 0.9) / 0.4))
        if k > 0:     # risco sobre a lembrança
            d_.line((60, OUT_H * 0.2, 60 + (OUT_W - 120) * k, OUT_H * 0.7), fill=(230, 50, 50), width=26)
        return f

    def p_orgulho(self, t, d):
        m = self.fundo((255, 210, 140), (245, 170, 100))
        m.alpha_composite(brilho((1080, 1080), (255, 245, 200), 540, 0.8), (0, 400))
        self.mu_mec.desenhar(m, t, 540, 2450, escala=2.7, expr="feliz", piscar=False)
        f = camera(m, 540, 1000, 1.05 + 0.1 * ease_io(t / d))
        particulas(f, t, 40, semente=47)
        return f

    def p_liga(self, t, d):
        m = self.fundo((40, 40, 50), (25, 25, 30))
        p = Pincel(WW, WH)
        p.elipse((240, 560, 840, 1160), (50, 50, 60), ow=10)       # painel / ignição
        p.elipse((440, 760, 640, 960), (120, 125, 135), ow=8)
        m.alpha_composite(p.pronto())
        ang = 0 if t < 0.8 else -70 * ease_out((t - 0.8) / 0.3)
        self.segura(m, self.chave.rotate(ang, expand=True, resample=Image.BICUBIC), 600, 860, 420)
        f = camera(m, 540, 900, 1.1)
        if t > 1.1:
            f = f.transform(f.size, Image.AFFINE, (1, 0, 0, 0, 1, 4 * math.sin(t * 70)))
            texto_pop(f, "VRUUUM!", self.fc, t - 1.1, OUT_W * 0.5, OUT_H * 0.2, 100, (255, 214, 40))
        return f

    def p_final(self, t, d):
        off = (t * 300) % WW
        m = Image.new("RGBA", (WW, WH))
        m.alpha_composite(self.rua_sol, (int(-off), 0))
        m.alpha_composite(self.rua_sol, (int(WW - off), 0))
        self.corsa.desenhar(m, 540, 1580, escala=1.0, giro=-t * 500, pulo=3 * abs(math.sin(t * 9)))
        f = camera(m, 540, 1200, 1.25 - 0.2 * ease_io(t / d))
        dr = ImageDraw.Draw(f, "RGBA")
        for i in range(4):                     # fumacinha do escapamento
            tt = (t * 1.5 + i * 0.25) % 1.0
            x = OUT_W * 0.14 - tt * 120
            y = OUT_H * 0.70 - tt * 40
            r = 12 + tt * 30
            dr.ellipse((x - r, y - r, x + r, y + r), fill=(220, 220, 225, int(170 * (1 - tt))))
        particulas(f, t, 30, semente=50)
        if t > d - 0.8:
            f = ImageEnhance.Brightness(f).enhance(1 - ease_io((t - (d - 0.8)) / 0.8))
        return f

    def eventos_sfx(self):
        ev = []
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if i and tr in ("whip", "zoom"):
                ev.append(("whoosh", ini - 0.08))
            elif i and tr == "corte":
                ev.append(("pop", ini))
        ev += [("brilho", 4.86), ("brilho", 71.08), ("brilho", 72.94 + 1.6), ("brilho", 96.96)]
        ev += [("toc", 27.22 + i * 0.55 + 0.45) for i in range(5)]       # moedas caindo
        ev += [("toc", 100.6), ("toc", 100.75), ("toc", 100.9)]            # motor pegando
        return ev


def carregar_palavras(caminho):
    pal = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            pal.append(dict(w=w["w"], s=w["s"], e=w["e"]))
    out = []
    i = 0
    while i < len(pal):
        w = pal[i]
        if w["w"] == "R" and i + 3 < len(pal) and pal[i + 1]["w"] == "$":
            out.append(dict(w="R$", s=w["s"], e=pal[i + 1]["e"]))
            out.append(dict(w="9.400.", s=pal[i + 2]["s"], e=pal[i + 3]["e"]))
            i += 4
            continue
        txt = {"18": "dezoito", "5": "cinco", "corsa": "Corsa", "corsa,": "Corsa,",
               "clássico.": "Classic."}.get(w["w"], w["w"])
        out.append(dict(w=txt, s=w["s"], e=w["e"]))
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_corsa_do_murillo.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true", help="renderiza início/meio/fim de cada plano (sem vídeo)")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeCorsa(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.2)
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

    tmp = tempfile.mkdtemp(prefix="corsa_")
    wav = os.path.join(tmp, "mix.wav")
    vc.mixar(filme, a.narracao, wav)
    print(f"• renderizando {total} frames ({filme.dur_total:.1f}s)…", flush=True)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}",
         "-r", str(FPS), "-i", "-", "-i", wav, "-vf", "scale=1080:1920:flags=lanczos",
         "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
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
