#!/usr/bin/env python3
"""
"A Mala no Ponto Final" — há 15 anos existe uma mala marrom no ponto final da linha 308; o motorista
nunca deixou ninguém mexer: ela é de um menino que esperou a mãe por 3 semanas… e voltou.

Cenários novos: ponto final com nevoeiro, interior do ônibus, ônibus chegando, festa de despedida.
Rig articulado + cortes a cada ~2 s (gerar_video.subcortes).

    python3 animacao/video_mala.py --narracao narr.mp3 --transcricao transcricao.json --fonte Poppins.ttf
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
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_video as g  # noqa: E402
import video_carta as vc  # noqa: E402
import video_corsa as vco  # noqa: E402
import video_estatua as ve  # noqa: E402
import video_areia as va  # noqa: E402
import cenarios as cen  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(308)

MOTORISTA = dict(pele=(214, 160, 120), cabelo=(190, 190, 195), camisa=(60, 110, 150), calca=(55, 60, 78),
                 sapato=(40, 40, 45), tipo="pai", chapeu=(40, 70, 120))
MOTORISTA_J = dict(MOTORISTA, cabelo=(50, 38, 32))
MENINO = dict(pele=(196, 140, 100), cabelo=(35, 28, 26), camisa=(120, 150, 210), calca=(70, 80, 100),
              sapato=(230, 230, 235), tipo="menino")
HOMEM = dict(pele=(196, 140, 100), cabelo=(35, 28, 26), camisa=(40, 44, 66), calca=(40, 44, 66),
             sapato=(30, 30, 34), tipo="pai", bigode=False, gravata=(180, 50, 60))
FILHO = dict(MENINO, camisa=(250, 190, 70))
FISCAL = dict(pele=(232, 186, 150), cabelo=(80, 60, 45), camisa=(240, 170, 40), calca=(60, 62, 80),
              sapato=(40, 40, 45), tipo="pai", bigode=False, faixas=True)
COBRADOR = dict(pele=(232, 186, 150), cabelo=(90, 60, 40), camisa=(110, 170, 120), calca=(70, 80, 110),
                sapato=(50, 50, 55), tipo="pai", bigode=False)
COLEGA = dict(pele=(222, 170, 128), cabelo=(110, 70, 40), camisa=(60, 110, 150), calca=(55, 60, 78),
              sapato=(40, 40, 45), tipo="pai", chapeu=(40, 70, 120))
COLEGA_F = dict(pele=(235, 190, 150), cabelo=(150, 60, 40), camisa=(230, 130, 150), calca=(0, 0, 0),
                sapato=(150, 70, 90), tipo="moca", vestido=(230, 130, 150))
vc.DESTAQUE_VERMELHO = set()
_C = {}


# --------------------------------------------------------------------------
# Objetos
# --------------------------------------------------------------------------
def mala_img(w=360, tampa=0.0):
    """Mala marrom antiga. tampa=0 fechada; >0 abre (graus) mostrando garrafa e carta."""
    k = ("mala", w, round(tampa))
    if k in _C:
        return _C[k]
    p = Pincel(420, 360)
    if tampa > 1:
        a = math.radians(tampa)
        alt = 190 * math.sin(a) + 10
        lid = Pincel(420, 360)
        lid.ret((55, 160 - alt, 365, 175), (150, 96, 56), r=18)
        lid.ret((75, 180 - alt, 345, 170), (90, 58, 36), r=8, ow=0)
        img = lid.pronto()
        p.ret((40, 150, 380, 330), (120, 76, 44), r=18)                          # base
        p.ret((60, 170, 360, 310), (70, 44, 30), r=10, ow=0)                      # interior
        img.alpha_composite(p.pronto())
        d = Pincel(420, 360)
        d.ret((90, 120, 150, 300), (90, 150, 200), r=16)
        d.ret((92, 100, 148, 140), (230, 80, 70), r=10)
        d.poli([(190, 205), (330, 205), (330, 290), (190, 290)], (250, 245, 225), ow=5)
        d.linha([(190, 205), (260, 250), (330, 205)], w=4)
        d.elipse((254, 238, 270, 254), (200, 50, 50), ow=3)
        img.alpha_composite(d.pronto())
    else:
        p.ret((20, 70, 400, 330), (150, 96, 56), r=28)
        p.ret((20, 70, 400, 150), (170, 112, 66), r=24)
        p.ret((70, 70, 100, 330), (110, 70, 42), r=6, ow=5)
        p.ret((320, 70, 350, 330), (110, 70, 42), r=6, ow=5)
        p.ret((180, 40, 240, 78), (90, 60, 40), r=14)
        p.ret((190, 128, 230, 160), (240, 200, 80), r=6)
        p.ret((20, 190, 400, 205), (110, 70, 42), r=4, ow=0)
        p.ret((18, 300, 70, 345), (90, 60, 40), r=10)
        p.ret((350, 300, 402, 345), (90, 60, 40), r=10)
        img = p.pronto()
    if w != 420:
        img = img.resize((w, int(img.height * w / 420)), Image.BICUBIC)
    _C[k] = img
    return img


def garrafa(w=160):
    p = Pincel(120, 300)
    p.ret((14, 60, 106, 290), (90, 150, 200), r=24)
    p.ret((10, 20, 110, 80), (230, 80, 70), r=16)
    p.ret((30, 150, 90, 190), (255, 255, 255), r=6, ow=0)
    img = p.pronto()
    return img.resize((w, int(300 * w / 120)), Image.BICUBIC)


def carta_img(fc, w=640, aberta=True):
    p = Pincel(640, 440)
    p.ret((10, 10, 630, 430), (250, 244, 222), r=14, ow=8)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 44)
    for i, l in enumerate(("Obrigado", "por esperar", "comigo.")):
        d.text((320 - f.getlength(l) / 2, 80 + i * 96), l, font=f, fill=(70, 50, 120))
    return img.resize((w, int(440 * w / 640)), Image.BICUBIC) if w != 640 else img


def onibus(w=1000):
    k = ("onibus", w)
    if k in _C:
        return _C[k]
    p = Pincel(1000, 480)
    p.ret((20, 60, 980, 400), (240, 240, 245), r=44)
    p.ret((20, 320, 980, 360), (200, 60, 60), r=0, ow=0)
    for i in range(6):
        p.ret((90 + i * 130, 100, 200 + i * 130, 230), (150, 205, 235), r=14, ow=6)
    p.ret((830, 100, 960, 300), (150, 205, 235), r=16, ow=6)
    p.ret((760, 40, 960, 90), (30, 30, 40), r=8)
    p.elipse((940, 280, 990, 330), (255, 240, 180), ow=5)
    for x in (200, 760):
        p.elipse((x - 85, 320, x + 85, 470), (25, 25, 30), ow=0)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = vc.fonte(None, 40) if False else None
    _C[k] = img
    return img


class Onibus:
    def __init__(self, fc):
        self.corpo = onibus()
        d = ImageDraw.Draw(self.corpo)
        f = vc.fonte(fc, 38)
        d.text((860 - f.getlength("308") / 2, 44), "308", font=f, fill=(255, 220, 80))
        self.roda = vco.roda(78)

    def desenhar(self, base, cx, by, escala=1.0, giro=0.0, espelhar=False, farol=False, vazio=True):
        c0 = self.corpo
        w, h = int(c0.width * escala), int(c0.height * escala)
        c = c0.resize((w, h), Image.BICUBIC)
        if espelhar:
            c = c.transpose(Image.FLIP_LEFT_RIGHT)
        x0, y0 = int(cx - w / 2), int(by - h)
        r = self.roda.rotate(-giro, resample=Image.BICUBIC).resize((int(176 * escala), int(176 * escala)))
        if farol:
            fx = w * (0.02 if espelhar else 0.98)
            base.alpha_composite(brilho((int(600 * escala), int(300 * escala)), (255, 240, 170), int(280 * escala), 0.6),
                                 (int(x0 + fx - (300 * escala if not espelhar else 300 * escala)),
                                  int(y0 + h * 0.62 - 150 * escala)))
        base.alpha_composite(c, (x0, y0))
        for rx in (200, 760):
            xx = (1000 - rx) if espelhar else rx
            base.alpha_composite(r, (int(x0 + (xx - 88) * escala), int(y0 + (395 - 88) * escala)))


def banco_img():
    p = Pincel(460, 200)
    p.ret((10, 40, 450, 90), (150, 105, 70), r=8)
    p.ret((10, 100, 450, 140), (150, 105, 70), r=8)
    p.ret((40, 140, 70, 195), (60, 60, 70), r=4)
    p.ret((390, 140, 420, 195), (60, 60, 70), r=4)
    return p.pronto()


def nevoa_img():
    """Faixa de névoa sem emenda (blobs repetidos nas bordas)."""
    k = "nevoa"
    if k in _C:
        return _C[k]
    rng = random.Random(8)
    im = Image.new("RGBA", (WW, 700), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for _ in range(14):
        x, y = rng.randint(0, WW), rng.randint(120, 580)
        rx, ry = rng.randint(180, 360), rng.randint(50, 110)
        for off in (-WW, 0, WW):
            d.ellipse((x + off - rx, y - ry, x + off + rx, y + ry), fill=(225, 232, 245, 90))
    im = im.filter(ImageFilter.GaussianBlur(40))
    _C[k] = im
    return im


def nevoa(m, t, y=1180, alpha=1.0, vel=26):
    n = nevoa_img()
    dx = int(t * vel) % WW
    layer = ImageChops.offset(n, dx, 0)
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    m.alpha_composite(layer, (0, y))


def neve_f(f, t, n=60, seed=3):
    d = ImageDraw.Draw(f, "RGBA")
    rng = random.Random(seed)
    for _ in range(n):
        x = (rng.uniform(0, OUT_W) + 30 * math.sin(t * 1.3 + rng.random() * 6)) % OUT_W
        y = (rng.uniform(0, OUT_H) + t * rng.uniform(60, 160)) % OUT_H
        r = rng.choice((2, 3, 4))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(240, 245, 255, 200))


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def ponto_final(fc):
    base = gradiente(WW, WH, (14, 20, 44), (60, 70, 100))
    p = Pincel(WW, WH)
    rng = random.Random(5)
    for i in range(6):                                   # galpão/garagem ao fundo
        x = i * 190 - 30
        p.ret((x, 760 + (i % 2) * 40, x + 180, 1400), (36, 42, 70), r=4, ow=0)
        for yy in (820, 920, 1020):
            if rng.random() < 0.6:
                p.ret((x + 30, yy, x + 70, yy + 40), (255, 214, 120), r=3, ow=0)
    p.ret((-20, 1400, WW + 20, 1480), (70, 74, 96), r=0)
    p.ret((-20, 1480, WW + 20, WH + 20), (46, 50, 68), r=0)
    for x in range(0, WW, 220):
        p.ret((x + 40, 1720, x + 150, 1738), (200, 190, 130), r=6, ow=0)
    p.ret((130, 900, 150, 1420), (80, 84, 104), r=4)                              # poste
    p.elipse((90, 860, 190, 930), (255, 235, 170), ow=4)
    p.ret((780, 960, 800, 1420), (110, 112, 130), r=4)                            # placa do ponto
    p.ret((660, 860, 920, 990), (40, 90, 170), r=12, ow=6)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 36)
    d.text((790 - f.getlength("LINHA") / 2, 872), "LINHA", font=f, fill=(255, 255, 255))
    f2 = vc.fonte(fc, 56)
    d.text((790 - f2.getlength("308") / 2, 912), "308", font=f2, fill=(255, 220, 80))
    base.alpha_composite(brilho((700, 700), (255, 230, 170), 340, 0.5), (-140, 640))
    return base


def onibus_dentro_noite():
    base = cen.onibus_dentro()
    escuro = Image.new("RGBA", (WW, WH), (8, 10, 30, 150))
    base.alpha_composite(escuro)
    base.alpha_composite(brilho((900, 400), (255, 230, 170), 300, 0.4), (90, 140))
    return base


def volante_fg():
    p = Pincel(WW, WH)
    p.ret((-20, 1440, WW + 20, WH + 20), (40, 42, 56), r=0)
    p.ret((-20, 1400, WW + 20, 1480), (62, 66, 84), r=30)
    p.elipse((230, 1480, 850, 2100), (28, 28, 36), ow=10)
    p.elipse((330, 1580, 750, 2000), (40, 42, 56), ow=8)
    return p.pronto()


def festa():
    base = gradiente(WW, WH, (252, 232, 200), (238, 214, 180))
    p = Pincel(WW, WH)
    p.ret((60, 200, 1020, 360), (240, 90, 100), r=20, ow=8)                       # faixa
    for i, x in enumerate(range(100, 1000, 140)):
        p.elipse((x, 440 + (i % 2) * 60, x + 110, 590 + (i % 2) * 60),
                 [(250, 200, 60), (90, 170, 240), (240, 100, 120), (120, 210, 130)][i % 4])
        p.linha([(x + 55, 590 + (i % 2) * 60), (x + 55, 760)], fill=(120, 120, 130), w=3)
    p.ret((-20, 1480, WW + 20, WH + 20), (190, 140, 100), r=0)
    p.ret((340, 1380, 740, 1500), (150, 100, 70), r=10)                           # mesa
    p.ret((420, 1300, 660, 1390), (250, 230, 240), r=14, ow=6)                    # bolo
    p.ret((520, 1240, 560, 1305), (250, 240, 200), r=4, ow=4)
    p.elipse((518, 1205, 562, 1250), (255, 190, 60), ow=0)
    base.alpha_composite(p.pronto())
    return base


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeMala(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.mot, self.motj = P_(MOTORISTA), P_(MOTORISTA_J)
        self.men, self.hom, self.fil = P_(MENINO), P_(HOMEM), P_(FILHO)
        self.fis, self.cob = P_(FISCAL), P_(COBRADOR)
        self.col, self.colf = P_(COLEGA), P_(COLEGA_F)
        self.blur = {}
        self.ponto = ponto_final(fc)
        self.rod = ponto_final(fc)
        self.bus_in = onibus_dentro_noite()
        self.volante = volante_fg()
        self.festa_img = festa()
        self.bus = Onibus(fc)
        self.mala, self.garr, self.banco = mala_img(380), garrafa(150), banco_img()
        self.carta = carta_img(fc)
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        P = [
            (0.00, self.p_hook, "frio", "corte"),
            (5.32, self.p_ninguem, "frio", "corte"),
            (6.88, self.p_motorista, "", "whip"),
            (9.90, self.p_ultima, "", "whip"),
            (12.36, self.p_desce, "frio", "whip"),
            (16.52, self.p_sempre, "frio", "corte"),
            (17.78, self.p_fiscais, "", "whip"),
            (21.16, self.p_colegas, "", "corte"),
            (22.96, self.p_bomba, "", "corte"),
            (25.30, self.p_nao_deixei, "", "whip"),
            (27.00, self.p_sei, "triste", "zoom"),
            (30.42, self.p_15anos, "sepia", "dissolve"),
            (33.26, self.p_menino_desce, "sepia", "whip"),
            (36.12, self.p_sozinho, "sepia", "corte"),
            (37.84, self.p_perdido, "sepia", "corte"),
            (39.64, self.p_esperando, "sepia", "corte"),
            (43.36, self.p_esperei, "sepia", "dissolve"),
            (44.40, self.p_vazio, "sepia", "whip"),
            (47.08, self.p_sentou, "sepia", "corte"),
            (50.22, self.p_tres_semanas, "sepia", "whip"),
            (54.36, self.p_sopa, "sepia", "dissolve"),
            (59.12, self.p_sorrindo, "sepia", "whip"),
            (61.46, self.p_ligou, "sepia", "corte"),
            (65.00, self.p_abraco, "sepia", "dissolve"),
            (68.26, self.p_nunca_soube, "triste", "dissolve"),
            (70.48, self.p_guardei, "frio", "dissolve"),
            (71.50, self.p_todo_dia, "frio", "corte"),
            (74.90, self.p_aposentei, "quente", "dissolve"),
            (76.48, self.p_festa, "quente", "whip"),
            (78.04, self.p_homem_entra, "quente", "corte"),
            (80.68, self.p_abraca, "quente", "corte"),
            (82.68, self.p_guardou, "quente", "corte"),
            (83.68, self.p_ate_ponto, "frio", "whip"),
            (86.12, self.p_abriu, "", "zoom"),
            (87.12, self.p_garrafa, "", "corte"),
            (91.48, self.p_carta, "", "corte"),
            (96.52, self.p_final, "quente", "dissolve"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))
        self.p_preto = None

    # ---------- utilidades ----------
    def balao_t(self, f, txt, x, y, t0):
        if self.T >= t0:
            self.balao(f, txt, x, y, self.T - t0)

    def pmala(self, m, x=600, by=1780, e=1.0, tampa=0.0):
        mm = mala_img(380, tampa) if tampa else self.mala
        w = int(mm.width * e)
        im = mm.resize((w, int(mm.height * e)), Image.BICUBIC)
        m.alpha_composite(im, (int(x - w / 2), int(by - im.height)))

    def cena_ponto(self, t, neve=False, nev=0.9):
        m = self.ponto.copy()
        nevoa(m, t, 1150, nev)
        return m

    def fim_cam(self, m, cx, cy, z, t, neve=False, seed=3):
        f = self.cam(m, cx, cy, z)
        if neve:
            neve_f(f, t, 70, seed)
        return f

    # ---------- planos ----------
    def p_hook(self, t, d):
        m = self.cena_ponto(t)
        self.pmala(m, 540, 1760, 1.15)
        nevoa(m, t + 5, 1500, 0.6, 40)
        f = self.cam(m, 540, 1300, 1.25 - 0.1 * ease_io(t / d))
        if self.T > 0.2:
            texto_pop(f, "15 ANOS", self.fc, self.T - 0.2, OUT_W / 2, OUT_H * 0.12, 90, (255, 214, 40))
        if self.T > 1.78:
            texto_pop(f, "A MESMA MALA", self.fc, self.T - 1.78, OUT_W / 2, OUT_H * 0.22, 56, (255, 255, 255))
        return f

    def p_ninguem(self, t, d):
        m = gradiente(WW, WH, (22, 28, 52), (50, 56, 84))
        self.pmala(m, 540, 1500, 2.0)
        m.alpha_composite(brilho((900, 900), (255, 230, 170), 450, 0.3), (90, 700))
        f = self.cam(m, 540, 1150, 1.0 + 0.15 * ease_io(t / d))
        texto_pop(f, "?", self.fc, t, OUT_W / 2, OUT_H * 0.14, 160, (255, 214, 40))
        return f

    def p_motorista(self, t, d):
        m = self.bus_in.copy()
        self.mot(m, t, 540, 1800, 1.5, expr="neutro")
        m.alpha_composite(self.volante)
        f = self.cam(m, 540, 1150, 1.1)
        if self.T > 8.46:
            texto_pop(f, "32 ANOS", self.fc, self.T - 8.46, OUT_W / 2, OUT_H * 0.12, 90, (255, 214, 40))
        return f

    def p_ultima(self, t, d):
        m = self.cena_ponto(t)
        x = -500 + 1000 * ease_out(min(1, t / 1.8))
        self.bus.desenhar(m, x, 1760, 0.9, giro=t * 500 * (1 - ease_out(min(1, t / 1.8))), farol=True)
        f = self.cam(m, 540 + 60 * ease_io(t / d), 1300, 1.1)
        texto_pop(f, "ÚLTIMA VIAGEM", self.fc, t, OUT_W / 2, OUT_H * 0.12, 70, (255, 255, 255))
        return f

    def p_desce(self, t, d):
        m = self.cena_ponto(t)
        self.pmala(m, 800, 1760, 0.9)
        x = 180 + 380 * ease_io(min(1, t / (d * 0.85)))
        self.mot(m, t, x, 1800, 1.2, expr="neutro", pose="anda" if t < d * 0.85 else "idle")
        nevoa(m, t + 3, 1450, 0.5, 35)
        return self.cam(m, 540 + 100 * ease_io(t / d), 1300, 1.12)

    def p_sempre(self, t, d):
        m = gradiente(WW, WH, (22, 28, 52), (50, 56, 84))
        self.pmala(m, 540, 1500, 2.1)
        m.alpha_composite(brilho((900, 900), (255, 230, 170), 450, 0.45 + 0.1 * math.sin(t * 6)), (90, 700))
        f = self.cam(m, 540, 1150, 1.1)
        particulas(f, t, 30, cor=(255, 235, 170), semente=2)
        return f

    def p_fiscais(self, t, d):
        m = self.cena_ponto(t)
        self.pmala(m, 520, 1760, 1.0)
        self.fis(m, t, 180, 1800, 1.2, expr="bravo", pose="aponta")
        self.mot(m, t, 900, 1800, 1.25, expr="bravo", pose="bracos_abertos" if t > 1.0 else "idle")
        f = self.cam(m, 560, 1300, 1.12)
        if self.T > 19.84:
            texto_pop(f, "ACHADOS E PERDIDOS?", self.fc, self.T - 19.84, OUT_W / 2, OUT_H * 0.12, 52, (255, 255, 255))
        return f

    def p_colegas(self, t, d):
        m = self.cena_ponto(t)
        self.pmala(m, 540, 1760, 1.0)
        self.col(m, t, 250, 1800, 1.15, expr="surpreso", pose="aponta")
        self.colf(m, t + 1, 830, 1800, 1.15, expr="feliz", pose="idle")
        f = self.cam(m, 540, 1300, 1.12)
        if self.T > 21.96:
            texto_pop(f, "ABRIR!", self.fc, self.T - 21.96, OUT_W / 2, OUT_H * 0.12, 90, (255, 255, 255))
        return f

    def p_bomba(self, t, d):
        m = self.cena_ponto(t)
        self.pmala(m, 560, 1760, 1.0)
        self.cob(m, t, 250, 1800, 1.25, expr="surpreso", pose="bracos_abertos")
        f = self.cam(m, 480, 1300, 1.15)
        self.balao_t(f, "É BOMBA!", OUT_W * 0.35, OUT_H * 0.2, 24.6)
        return f

    def p_nao_deixei(self, t, d):
        m = self.cena_ponto(t)
        self.pmala(m, 540, 1760, 1.0)
        self.mot(m, t, 540, 1830, 1.5, expr="bravo", pose="bracos_abertos")
        f = self.cam(m, 540, 1300, 1.12 + 0.1 * ease_io(t / d))
        if self.T > 25.52:
            texto_pop(f, "NINGUÉM ENCOSTA", self.fc, self.T - 25.52, OUT_W / 2, OUT_H * 0.12, 62, (255, 120, 100))
        return f

    def p_sei(self, t, d):
        m = self.fundo_blur("ponto", self.ponto)
        self.mot(m, t, 540, 2350, 2.5, expr="triste")
        f = self.cam(m, 540, 950, 1.05)
        if self.T > 28.38:
            texto_pop(f, "ELE SABE", self.fc, self.T - 28.38, OUT_W / 2, OUT_H * 0.1, 80, (255, 214, 40))
        return f

    def p_15anos(self, t, d):
        m = self.cena_ponto(t, nev=0.7)
        self.bus.desenhar(m, 330, 1760, 0.78)
        f = self.cam(m, 540, 1300, 1.1)
        neve_f(f, t, 70)
        texto_pop(f, "15 ANOS ATRÁS", self.fc, t, OUT_W / 2, OUT_H * 0.12, 74, (255, 214, 40))
        return f

    def p_menino_desce(self, t, d):
        m = self.cena_ponto(t, nev=0.6)
        self.bus.desenhar(m, 300, 1760, 0.78, farol=False)
        x = 520 + 220 * ease_out(min(1, t / 1.5))
        self.men(m, t, x, 1800, 1.0, expr="neutro", pose="anda" if t < 1.5 else "idle")
        self.pmala(m, x + 160, 1790, 0.75)
        f = self.cam(m, 540, 1300, 1.15)
        neve_f(f, t, 70)
        return f

    def p_sozinho(self, t, d):
        m = self.cena_ponto(t, nev=0.8)
        self.men(m, t, 440, 1800, 1.1, expr="triste")
        self.pmala(m, 700, 1790, 0.85)
        f = self.cam(m, 540, 1300, 1.18 + 0.12 * ease_io(t / d))
        neve_f(f, t, 70)
        if self.T > 36.12:
            texto_pop(f, "SOZINHO", self.fc, self.T - 36.12, OUT_W / 2, OUT_H * 0.12, 80, (255, 255, 255))
        return f

    def p_perdido(self, t, d):
        m = self.cena_ponto(t, nev=0.8)
        self.motj(m, t, 250, 1800, 1.2, expr="neutro", pose="idle")
        self.men(m, t, 780, 1800, 1.0, expr="triste")
        self.pmala(m, 950, 1790, 0.7)
        f = self.cam(m, 540, 1300, 1.12)
        neve_f(f, t, 70)
        self.balao_t(f, "Tá perdido?", OUT_W * 0.3, OUT_H * 0.2, 38.0)
        return f

    def p_esperando(self, t, d):
        m = self.cena_ponto(t, nev=0.8)
        self.men(m, t, 560, 1800, 1.4, expr="neutro", pose="idle")
        self.pmala(m, 860, 1790, 0.8)
        f = self.cam(m, 540, 1300, 1.12)
        neve_f(f, t, 70)
        self.balao_t(f, "Minha mãe já vem.", OUT_W * 0.5, OUT_H * 0.16, 40.26)
        return f

    def p_esperei(self, t, d):
        m = self.cena_ponto(t, nev=0.8)
        m.alpha_composite(self.banco, (320, 1620))
        self.motj(m, t, 450, 1700, 1.05, expr="feliz")
        self.men(m, t, 650, 1700, 0.95, expr="neutro")
        m.alpha_composite(self.banco.crop((0, 70, 460, 200)), (320, 1690))
        f = self.cam(m, 540, 1300, 1.12)
        neve_f(f, t, 70)
        return f

    def p_vazio(self, t, d):
        m = self.cena_ponto(t, nev=0.8)
        x = -500 + 1050 * ease_out(min(1, t / 1.6))
        self.bus.desenhar(m, x, 1760, 0.82, giro=t * 400 * (1 - ease_out(min(1, t / 1.6))), farol=True)
        self.men(m, t, 240, 1800, 1.1, expr="surpreso" if t < 1.6 else "triste")
        f = self.cam(m, 540, 1300, 1.1)
        neve_f(f, t, 70)
        if self.T > 46.1:
            texto_pop(f, "VAZIO.", self.fc, self.T - 46.1, OUT_W / 2, OUT_H * 0.12, 100, (255, 255, 255))
        return f

    def p_sentou(self, t, d):
        m = self.cena_ponto(t, nev=0.8)
        self.men(m, t, 540, 1760, 1.35, expr="triste")
        self.pmala(m, 540, 1800, 0.75)
        f = self.cam(m, 540, 1300, 1.15 + 0.1 * ease_io(t / d))
        neve_f(f, t, 70)
        self.balao_t(f, "Ela deve ter pegado o outro.", OUT_W / 2, OUT_H * 0.17, 48.66)
        return f

    def p_tres_semanas(self, t, d):
        m = self.cena_ponto(t, nev=0.7)
        self.men(m, t, 540, 1760, 1.3, expr="triste")
        self.pmala(m, 540, 1800, 0.72)
        T = self.T
        dia = min(21, 1 + int((T - 50.22) / (d) * 21))
        f = self.cam(m, 540, 1300, 1.15)
        neve_f(f, t, 70)
        texto_pop(f, f"DIA {dia}", self.fc, 0.2, OUT_W / 2, OUT_H * 0.12, 90, (255, 214, 40))
        return f

    def vapor(self, m, t, x, y):
        for i in range(5):
            ph = (t * 0.8 + i * 0.2) % 1
            m.alpha_composite(brilho((90, 90), (255, 255, 255), 40, 0.5 * (1 - ph)),
                              (int(x + 20 * math.sin(t * 3 + i) - 45), int(y - ph * 160 - 45)))

    def p_sopa(self, t, d):
        m = self.cena_ponto(t, nev=0.7)
        self.motj(m, t, 300, 1800, 1.25, expr="feliz", pose="entrega")
        hx, hy = self.motj.a.maos_mundo[1]
        self.men(m, t, 760, 1800, 1.0, expr="feliz")
        m.alpha_composite(self.garr, (int(hx - 40), int(hy - 200)))
        self.vapor(m, t, hx + 35, hy - 210)
        f = self.cam(m, 540, 1300, 1.18)
        neve_f(f, t, 70)
        if self.T > 55.14:
            texto_pop(f, "SOPA QUENTE", self.fc, self.T - 55.14, OUT_W / 2, OUT_H * 0.12, 70, (255, 200, 120))
        return f

    def p_sorrindo(self, t, d):
        m = self.cena_ponto(t, nev=0.6)
        x = 1150 - 500 * ease_out(min(1, t / 1.4))
        self.men(m, t, x, 1800, 1.1, expr="feliz", pose="corre" if t < 1.4 else "bracos_abertos", sx=-1)
        self.motj(m, t, 250, 1800, 1.2, expr="surpreso")
        f = self.cam(m, 540, 1300, 1.12)
        neve_f(f, t, 70)
        return f

    def p_ligou(self, t, d):
        m = self.cena_ponto(t, nev=0.6)
        self.men(m, t, 560, 1800, 1.4, expr="feliz", pose="bracos_abertos")
        f = self.cam(m, 540, 1300, 1.12)
        neve_f(f, t, 70)
        self.balao_t(f, "Minha mãe vem amanhã!", OUT_W / 2, OUT_H * 0.16, 62.0)
        return f

    def p_abraco(self, t, d):
        m = self.cena_ponto(t, nev=0.6)
        T = self.T
        if T < 66.0:
            self.motj(m, t, 440, 1800, 1.25, expr="feliz", pose="abraca_d")
            self.men(m, t, 640, 1800, 1.0, expr="feliz", pose="abraca_e")
            self.pmala(m, 880, 1790, 0.8)
        else:
            x = 640 - 420 * ease_in_(min(1, (T - 66.0) / 1.7))
            self.motj(m, t, 440, 1800, 1.25, expr="triste", pose="acena")
            self.men(m, t, x + 150 if False else 640 - 380 * ease_io(min(1, (T - 66.0) / 1.7)), 1800, 1.0,
                     expr="feliz", pose="anda", sx=-1)
            self.pmala(m, 880, 1790, 0.8)
        f = self.cam(m, 600, 1300, 1.12)
        neve_f(f, t, 70)
        if T > 67.1:
            texto_pop(f, "ESQUECEU A MALA", self.fc, T - 67.1, OUT_W / 2, OUT_H * 0.12, 58, (255, 214, 40))
        return f

    def p_nunca_soube(self, t, d):
        m = self.cena_ponto(t, nev=0.8)
        self.pmala(m, 700, 1790, 1.0)
        self.mot(m, t, 340, 1800, 1.3, expr="triste", pose="idle")
        f = self.cam(m, 540, 1300, 1.15)
        return f

    def p_guardei(self, t, d):
        m = self.cena_ponto(t, nev=0.6)
        self.mot(m, t, 420, 1800, 1.3, expr="neutro", pose="entrega")
        hx, hy = self.mot.a.maos_mundo[1]
        mm = mala_img(300)
        m.alpha_composite(mm, (int(hx - 150), int(hy - 20)))
        return self.cam(m, 540, 1300, 1.18)

    def p_todo_dia(self, t, d):
        T = self.T
        k = (T - 71.5) * 1.3
        noite = 0.5 + 0.5 * math.sin(k * 2.2)
        m = self.cena_ponto(t, nev=0.6)
        self.pmala(m, 700, 1790, 1.0)
        self.mot(m, t, 340, 1800, 1.3, expr="neutro", pose="idle")
        sombra = Image.new("RGBA", (WW, WH), (255, 190, 110, int(80 * (1 - noite))))
        m.alpha_composite(sombra)
        f = self.cam(m, 540, 1300, 1.15)
        if self.T > 71.94:
            self.balao_t(f, "Um dia ele volta.", OUT_W * 0.5, OUT_H * 0.16, 72.64)
        return f

    def p_aposentei(self, t, d):
        m = gradiente(WW, WH, (255, 190, 130), (250, 225, 190))
        self.mot(m, t, 540, 1800, 1.45, expr="feliz", pose="idle")
        f = self.cam(m, 540, 1250, 1.1)
        texto_pop(f, "APOSENTADO", self.fc, t, OUT_W / 2, OUT_H * 0.12, 74, (255, 214, 40))
        return f

    def p_festa(self, t, d):
        m = self.festa_img.copy()
        self.mot(m, t, 540, 1800, 1.2, expr="ri", pose="idle")
        self.col(m, t, 220, 1800, 1.1, expr="feliz", pose="palmas")
        self.colf(m, t + 0.4, 860, 1800, 1.1, expr="feliz", pose="palmas")
        f = self.cam(m, 540, 1250, 1.1)
        particulas(f, t, 40, cor=(255, 240, 200), semente=9)
        return f

    def p_homem_entra(self, t, d):
        m = self.festa_img.copy()
        x = 1250 - 560 * ease_out(min(1, t / 1.6))
        self.mot(m, t, 260, 1800, 1.2, expr="surpreso")
        self.hom(m, t, x, 1800, 1.25, expr="neutro", pose="anda" if t < 1.6 else "idle")
        self.fil(m, t, x + 190, 1800, 0.75, expr="feliz", pose="anda" if t < 1.6 else "idle")
        return self.cam(m, 640, 1250, 1.1)

    def p_abraca(self, t, d):
        m = self.festa_img.copy()
        self.mot(m, t, 440, 1800, 1.3, expr="chora", pose="abraca_d")
        self.hom(m, t, 660, 1800, 1.3, expr="feliz", pose="abraca_e")
        self.fil(m, t, 900, 1800, 0.8, expr="feliz")
        f = self.cam(m, 560, 1250, 1.12)
        va_ = __import__("video_abracos")
        va_.coracoes(m, 0, 0, 0, 0) if False else None
        return f

    def p_guardou(self, t, d):
        return self.close(self.hom, t, self.festa_img, "festa", expr="feliz", z=1.05)

    def p_ate_ponto(self, t, d):
        m = self.cena_ponto(t, nev=0.8)
        x = 240 + 360 * ease_io(min(1, t / (d * 0.9)))
        self.mot(m, t, x, 1800, 1.25, expr="neutro", pose="anda" if t < d * 0.9 else "idle")
        self.hom(m, t, x - 230, 1800, 1.25, expr="neutro", pose="anda" if t < d * 0.9 else "idle")
        self.pmala(m, 900, 1790, 0.95)
        f = self.cam(m, 540 + 80 * ease_io(t / d), 1300, 1.12)
        return f

    def p_abriu(self, t, d):
        m = gradiente(WW, WH, (22, 28, 52), (50, 56, 84))
        T = self.T
        tampa = 100 * ease_out(min(1, max(0, (T - 86.2) / 0.8)))
        mm = mala_img(380, max(tampa, 0))
        self.pmala(m, 540, 1500, 2.1, tampa=tampa if tampa > 1 else 0.0)
        m.alpha_composite(brilho((900, 900), (255, 235, 170), 450, 0.2 + 0.5 * tampa / 100), (90, 700))
        f = self.cam(m, 540, 1150, 1.0 + 0.2 * ease_io(t / d))
        particulas(f, t, 30, cor=(255, 235, 170), semente=2)
        return f

    def p_garrafa(self, t, d):
        m = gradiente(WW, WH, (22, 28, 52), (50, 56, 84))
        gg = garrafa(380)
        m.alpha_composite(gg, (540 - gg.width // 2, 780))
        self.vapor(m, t, 540, 800)
        m.alpha_composite(brilho((900, 900), (255, 235, 170), 450, 0.35), (90, 500))
        f = self.cam(m, 540, 1000, 1.0 + 0.2 * ease_io(t / d))
        if self.T > 88.0:
            texto_pop(f, "A GARRAFA DA SOPA", self.fc, self.T - 88.0, OUT_W / 2, OUT_H * 0.12, 60, (255, 214, 40))
        return f

    def p_carta(self, t, d):
        m = gradiente(WW, WH, (40, 34, 52), (22, 20, 34))
        T = self.T
        k = ease_out(min(1, max(0, (T - 91.6) / 0.5)))
        ci = self.carta.rotate(2 * math.sin(t * 1.5), resample=Image.BICUBIC, expand=True)
        w = int(900 * (0.4 + 0.6 * k)) + 1
        ci = ci.resize((w, int(ci.height * w / ci.width)), Image.BICUBIC)
        m.alpha_composite(brilho((1000, 1000), (255, 235, 170), 480, 0.45), (40, 480))
        m.alpha_composite(ci, (540 - ci.width // 2, 1000 - ci.height // 2))
        f = self.cam(m, 540, 1000, 1.0 + 0.1 * ease_io(t / d))
        particulas(f, t, 30, cor=(255, 235, 170), semente=4)
        if T > 92.8:
            texto_pop(f, "AOS 12 ANOS", self.fc, T - 92.8, OUT_W / 2, OUT_H * 0.1, 66, (255, 214, 40))
        return f

    def p_final(self, t, d):
        m = gradiente(WW, WH, (255, 190, 130), (250, 225, 190))
        p = Pincel(WW, WH)
        p.elipse((380, 820, 700, 1140), (255, 235, 150), ow=0)
        p.ret((-20, 1500, WW + 20, WH + 20), (200, 185, 170), r=0)
        m.alpha_composite(p.pronto())
        self.mot(m, t, 440, 1800, 1.3, expr="chora", pose="abraca_d")
        self.hom(m, t, 660, 1800, 1.3, expr="chora", pose="abraca_e")
        self.fil(m, t, 900, 1800, 0.8, expr="feliz")
        f = self.cam(m, 560, 1250, 1.1 + 0.08 * ease_io(t / d))
        particulas(f, t, 50, cor=(255, 240, 200), semente=6)
        if self.T > 97.0:
            texto_pop(f, "OBRIGADO POR ESPERAR.", self.fc, self.T - 97.0, OUT_W / 2, OUT_H * 0.12, 54, (255, 255, 255))
        return f


def ease_in_(x):
    return x * x


# --------------------------------------------------------------------------
def mixar(filme, narracao, saida):
    SR = g.SR
    voz = vc.ler_wav_mono(narracao)
    n = int(filme.dur_total * SR)
    mix = np.zeros(n, np.float32)
    mix[:min(n, len(voz))] += voz[:n]
    mus = g.trilha(filme.dur_total)
    mus = mus / max(1e-6, np.abs(mus).max()) * 0.13
    mix[:len(mus)] += mus[:n]
    rng = np.random.default_rng(11)
    vento = np.convolve(rng.standard_normal(n).astype(np.float32), np.ones(900, np.float32) / 900, mode="same") * 0.9
    mix += vento * (0.5 + 0.5 * np.sin(np.arange(n) / SR * 0.4)) * 0.05
    ev = filme.eventos_sfx()
    ev += [("brilho", 0.2), ("toc", 5.32), ("brilho", 27.0), ("pop", 46.1), ("brilho", 55.14), ("toc", 65.0),
           ("brilho", 76.48), ("brilho", 86.4), ("brilho", 91.6), ("brilho", 97.0)]
    for tipo, t0 in ev:
        s = g.sfx(tipo) * (0.3 if tipo in ("whoosh", "pop") else 0.8)
        a = int(max(0, t0) * SR)
        b = min(n, a + len(s))
        mix[a:b] += s[: b - a]
    fade = int(SR * 0.8)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = mix / max(1.0, np.abs(mix).max() / 0.95)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def carregar_palavras(caminho):
    out = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            txt = {"Diz": "Disse"}.get(w["w"], w["w"])
            out.append(dict(w=txt, s=w["s"], e=w["e"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_mala_ponto_final.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeMala(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.4, a.narracao)
    total = int(filme.dur_total * FPS)

    if a.testar:
        for ini, d, *_r in filme.planos:
            for k in (0.01, 0.5, 0.99):
                filme.frame(int((ini + d * k) * FPS))
        print("todos os planos ok")
        return
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        filme.frame(0)
        ts = [c for c, _ in filme.cortes] + [filme.dur_total]
        for i, (x, y) in enumerate(zip(ts, ts[1:])):
            filme.frame(int((x + y) / 2 * FPS)).save(os.path.join(a.preview, f"take_{i:02d}.png"))
        print("preview em", a.preview, len(ts) - 1, "takes")
        return

    tmp = tempfile.mkdtemp(prefix="mala_")
    wav = os.path.join(tmp, "mix.wav")
    mixar(filme, a.narracao, wav)
    print(f"• renderizando {total} frames ({filme.dur_total:.1f}s)…", flush=True)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}",
         "-r", str(FPS), "-i", "-", "-i", wav, "-vf", "scale=1080:1920:flags=lanczos",
         "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-maxrate", "6M", "-bufsize", "12M",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.saida],
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
