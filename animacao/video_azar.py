#!/usr/bin/env python3
"""
"O Banco do Azar" — nessa cidade todo azar paga. A avó nunca trocou nenhuma ficha… porque cada azar já
tinha pago, com juros (e o verso de cada ficha conta como).

Abre no guichê do Banco do Azar (cenário novo). Rig articulado + cortes a cada ~2 s.

    python3 animacao/video_azar.py --narracao narr.mp3 --transcricao transcricao.json --fonte Poppins.ttf
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
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_video as g  # noqa: E402
import video_carta as vc  # noqa: E402
import video_corsa as vco  # noqa: E402
import video_estatua as ve  # noqa: E402
import video_areia as va  # noqa: E402
import video_abracos as vb  # noqa: E402
import video_taxista as vt  # noqa: E402
import cenarios as cen  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(2026)

NAIR = dict(pele=(214, 160, 120), cabelo=(225, 225, 232), camisa=(176, 120, 190), calca=(120, 90, 150),
            sapato=(110, 80, 70), tipo="vovo", vestido=(176, 120, 190))
NAIR_J = dict(pele=(220, 168, 126), cabelo=(100, 62, 40), camisa=(240, 150, 120), calca=(0, 0, 0),
              sapato=(140, 80, 70), tipo="moca", vestido=(240, 150, 120))
AVO_J = dict(pele=(226, 172, 130), cabelo=(60, 42, 32), camisa=(90, 130, 170), calca=(60, 66, 90),
             sapato=(50, 45, 45), tipo="pai", bigode=False)
NETA = dict(pele=(222, 170, 128), cabelo=(70, 45, 30), camisa=(110, 170, 220), calca=(0, 0, 0),
            sapato=(90, 90, 110), tipo="moca", vestido=(110, 170, 220))
FUNC = dict(pele=(232, 186, 150), cabelo=(80, 60, 45), camisa=(235, 235, 240), calca=(60, 62, 80),
            sapato=(40, 40, 45), tipo="pai", bigode=False, gravata=(200, 60, 60))
NOIVO = dict(AVO_J, camisa=(45, 50, 70), gravata=(240, 240, 245))
vc.DESTAQUE_VERMELHO = set()
OURO = (250, 205, 70)
_C = {}


# --------------------------------------------------------------------------
# Objetos
# --------------------------------------------------------------------------
def ficha_frente(w=300):
    k = ("ff", w)
    if k not in _C:
        p = Pincel(300, 300)
        p.elipse((10, 10, 290, 290), OURO, ow=10)
        p.elipse((40, 40, 260, 260), (250, 225, 130), ow=6)
        p.poli([(150, 70), (170, 125), (230, 130), (185, 168), (200, 225), (150, 195), (100, 225), (115, 168),
                (70, 130), (130, 125)], (230, 150, 40), ow=5)
        img = p.pronto()
        _C[k] = img if w == 300 else img.resize((w, w), Image.BICUBIC)
    return _C[k]


def cartao(fc, linhas, w=640, cor=(250, 244, 222)):
    """Verso da ficha: cartão com a frase à caneta."""
    p = Pincel(640, 320)
    p.ret((10, 10, 630, 310), cor, r=26, ow=8)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 40 if max(len(l) for l in linhas) < 26 else 34)
    y0 = 160 - len(linhas) * 28
    for i, l in enumerate(linhas):
        d.text((320 - f.getlength(l) / 2, y0 + i * 56), l, font=f, fill=(60, 50, 110))
    return img if w == 640 else img.resize((w, int(320 * w / 640)), Image.BICUBIC)


def nota(fc, txt, w=300):
    p = Pincel(300, 150)
    p.ret((8, 8, 292, 142), (110, 180, 120), r=14, ow=7)
    p.elipse((100, 25, 200, 125), (150, 215, 150), ow=5)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 34)
    d.text((150 - f.getlength(txt) / 2, 52), txt, font=f, fill=(30, 80, 40))
    return img if w == 300 else img.resize((w, int(150 * w / 300)), Image.BICUBIC)


def caixa_sapato(w=520, tampa=False, cheia=True):
    k = ("cx", w, tampa, cheia)
    if k not in _C:
        p = Pincel(520, 320)
        p.ret((20, 110, 500, 300), (200, 80, 70), r=14)
        if cheia:
            for i in range(14):
                x = 50 + (i % 7) * 62
                y = 70 + (i // 7) * 24 + (i % 3) * 6
                p.elipse((x, y, x + 64, y + 64), OURO, ow=5)
        if tampa:
            p.ret((10, 40, 510, 130), (220, 100, 90), r=14)
        else:
            p.ret((20, 190, 500, 300), (200, 80, 70), r=14)
            p.ret((10, 180, 510, 215), (225, 110, 100), r=10)
        img = p.pronto()
        _C[k] = img if w == 520 else img.resize((w, int(320 * w / 520)), Image.BICUBIC)
    return _C[k]


def ponto_dia():
    base = gradiente(WW, WH, (150, 205, 245), (225, 240, 250))
    p = Pincel(WW, WH)
    for i, x in enumerate((-60, 240, 540, 840)):
        p.ret((x, 720 + (i % 2) * 120, x + 230, 1400), [(220, 160, 140), (150, 190, 215), (230, 210, 140),
                                                           (170, 205, 160)][i], r=4)
        for yy in range(780 + (i % 2) * 120, 1360, 100):
            p.ret((x + 40, yy, x + 90, yy + 55), (255, 245, 210), r=4, ow=5)
            p.ret((x + 130, yy, x + 180, yy + 55), (255, 245, 210), r=4, ow=5)
    p.ret((-20, 1400, WW + 20, 1480), (205, 195, 180), r=0)
    p.ret((-20, 1480, WW + 20, WH + 20), (95, 95, 110), r=0)
    for x in range(0, WW, 220):
        p.ret((x + 40, 1720, x + 150, 1740), (235, 225, 150), r=6, ow=0)
    p.ret((760, 1000, 780, 1420), (110, 110, 125), r=4)
    p.ret((680, 930, 860, 1030), (230, 70, 70), r=10, ow=6)
    base.alpha_composite(p.pronto())
    return base


def banco_fachada(fc):
    base = gradiente(WW, WH, (255, 214, 160), (255, 236, 200))
    p = Pincel(WW, WH)
    p.ret((40, 300, 1040, 1440), (245, 235, 215), r=10)
    p.poli([(20, 310), (540, 160), (1060, 310)], (190, 120, 90))
    p.ret((120, 330, 960, 470), (60, 50, 110), r=14, ow=8)
    for x in (130, 330, 530, 730):
        p.ret((x, 560, x + 80, 1330), (225, 215, 195), r=8)
    p.ret((140, 880, 940, 1150), (170, 215, 240), r=10, ow=8)           # janela do guichê
    p.ret((140, 1150, 940, 1200), (150, 100, 70), r=6)
    p.ret((120, 520, 960, 800), (30, 34, 56), r=14, ow=8)               # painel de preços
    p.ret((-20, 1440, WW + 20, WH + 20), (185, 175, 160), r=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f1, f2 = vc.fonte(fc, 76), vc.fonte(fc, 44)
    d.text((540 - f1.getlength("BANCO DO AZAR") / 2, 352), "BANCO DO AZAR", font=f1, fill=(255, 220, 90))
    for i, (a, b) in enumerate((("PNEU FURADO", "R$ 20"), ("PERDEU ÔNIBUS", "R$ 10"), ("CHUVA NO CASAMENTO", "R$ 200"))):
        y = 545 + i * 80
        d.text((160, y), a, font=f2, fill=(255, 255, 255))
        d.text((930 - f2.getlength(b), y), b, font=f2, fill=(120, 235, 140))
    return base


def guarda_roupa():
    base = gradiente(WW, WH, (225, 205, 180), (205, 185, 160))
    p = Pincel(WW, WH)
    p.ret((80, 260, 1000, 1500), (140, 95, 65), r=18, ow=10)
    p.ret((130, 320, 950, 1450), (90, 60, 42), r=10, ow=6)
    p.ret((130, 880, 950, 905), (140, 95, 65), r=4)
    p.ret((130, 1160, 950, 1185), (140, 95, 65), r=4)
    for i, c in enumerate(((200, 90, 90), (90, 120, 200), (230, 200, 90), (120, 180, 120), (190, 120, 200))):
        p.ret((160 + i * 70, 340, 220 + i * 70, 870), c, r=8)
    p.ret((-20, 1500, WW + 20, WH + 20), (170, 130, 95), r=0)
    base.alpha_composite(p.pronto())
    return base


def agua(m, t, y=1640, alpha=110):
    p = Pincel(WW, WH - y + 40)
    p.ret((-20, 10, WW + 20, WH), (90, 150, 215), r=0, ow=0)
    ov = p.pronto()
    ov.putalpha(ov.getchannel("A").point(lambda v: int(v * alpha / 255)))
    d = ImageDraw.Draw(ov)
    for x in range(-40, WW + 40, 90):
        dy = 6 * math.sin(t * 3 + x * 0.05)
        d.arc((x, 0 + dy, x + 90, 24 + dy), 200, 340, fill=(230, 245, 255, 220), width=5)
    m.alpha_composite(ov, (0, y))


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeAzar(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.nair, self.nairj, self.avoj = P_(NAIR), P_(NAIR_J), P_(AVO_J)
        self.neta, self.func, self.noivo = P_(NETA), P_(FUNC), P_(NOIVO)
        self.povo = [P_(c) for c in ve.POVO]
        self.blur = {}
        self.banco = banco_fachada(fc)
        self.ponto = ponto_dia()
        self.capela = ve.capela(fc)
        self.padaria = cen.padaria()
        self.sitio = cen.sitio()
        self.sala_img = va.sala()
        self.guarda = guarda_roupa()
        self.carro = vco.Carro()
        self.onibus = __import__("video_mala").Onibus(fc)
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        P = [
            (0.00, self.p_hook, "", "corte"),
            (2.38, self.p_pneu, "", "whip"),
            (4.22, self.p_onibus, "", "corte"),
            (6.02, self.p_chuva, "", "corte"),
            (8.96, self.p_guiche, "", "whip"),
            (11.80, self.p_fila, "", "corte"),
            (13.16, self.p_avo, "", "zoom"),
            (15.96, self.p_azarada, "", "corte"),
            (18.92, self.p_onibus_mil, "", "whip"),
            (20.80, self.p_emprego, "", "corte"),
            (22.78, self.p_temporal, "", "whip"),
            (24.66, self.p_alagou, "", "whip"),
            (26.96, self.p_vizinhos, "", "whip"),
            (30.34, self.p_casinha, "", "corte"),
            (32.42, self.p_zero, "", "corte"),
            (35.36, self.p_morreu, "triste", "dissolve"),
            (37.50, self.p_guarda, "", "whip"),
            (39.34, self.p_caixa, "", "zoom"),
            (43.30, self.p_centenas, "", "corte"),
            (45.70, self.p_atras, "", "corte"),
            (48.80, self.p_f1, "quente", "whip"),
            (51.58, self.p_f2, "quente", "whip"),
            (53.74, self.p_f3, "quente", "whip"),
            (57.80, self.p_f4, "quente", "whip"),
            (61.84, self.p_f5, "quente", "whip"),
            (67.04, self.p_entendi, "", "dissolve"),
            (69.66, self.p_pagou, "", "corte"),
            (72.86, self.p_ultima, "triste", "dissolve"),
            (79.34, self.p_guiche2, "", "whip"),
            (82.96, self.p_nao_troquei, "", "corte"),
            (86.72, self.p_final, "quente", "dissolve"),
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

    def chuva_f(self, f, t, n=90, seed=7):
        d = ImageDraw.Draw(f, "RGBA")
        rng = random.Random(seed)
        for _ in range(n):
            x = rng.uniform(0, OUT_W)
            y = (rng.uniform(0, OUT_H) + t * rng.uniform(900, 1400)) % OUT_H
            d.line((x, y, x - 5, y + 30), fill=(200, 215, 245, 190), width=3)

    def card(self, f, linhas, y, t0, w=620):
        if self.T < t0:
            return
        c = cartao(self.fc, linhas, w)
        s = ease_out(min(1, (self.T - t0) / 0.25))
        c = c.resize((max(1, int(c.width * (0.6 + 0.4 * s))), max(1, int(c.height * (0.6 + 0.4 * s)))), Image.BICUBIC)
        f.paste(c, (int(OUT_W / 2 - c.width / 2), int(y)), c)

    def dinheiro_flutua(self, m, t, x, y, txt):
        n = nota(self.fc, txt, 260)
        m.alpha_composite(n, (int(x - 130), int(y - 25 * abs(math.sin(t * 3)))))

    # ---------- planos ----------
    def p_hook(self, t, d):
        m = self.banco.copy()
        for i, (p, x) in enumerate(zip(self.povo[:3], (200, 560, 900))):
            p(m, t + i, x, 1800, 1.05, expr="feliz", pose="idle")
        f = self.cam(m, 540, 1000, 1.05 + 0.1 * ease_io(t / d))
        texto_pop(f, "TODO AZAR PAGA", self.fc, t, OUT_W / 2, OUT_H * 0.08, 62, (255, 214, 40))
        return f

    def p_pneu(self, t, d):
        m = self.ponto.copy()
        self.carro.desenhar(m, 380, 1740, 0.85, giro=0)
        self.povo[1](m, t, 820, 1800, 1.2, expr="feliz", pose="entrega")
        hx, hy = self.povo[1].a.maos_mundo[1]
        self.dinheiro_flutua(m, t, hx, hy - 150, "R$ 20")
        f = self.cam(m, 560, 1300, 1.12)
        texto_pop(f, "PNEU FURADO", self.fc, t, OUT_W / 2, OUT_H * 0.12, 64, (255, 255, 255))
        return f

    def p_onibus(self, t, d):
        m = self.ponto.copy()
        self.onibus.desenhar(m, 400 + 1000 * ease_in_(min(1, t / d)), 1700, 0.8, giro=t * 400)
        self.povo[3](m, t, 700, 1800, 1.2, expr="surpreso", pose="corre")
        f = self.cam(m, 560, 1300, 1.12)
        texto_pop(f, "PERDEU O ÔNIBUS: R$ 10", self.fc, t, OUT_W / 2, OUT_H * 0.12, 40, (255, 255, 255))
        return f

    def p_chuva(self, t, d):
        m = self.capela.copy()
        self.noivo(m, t, 380, 1800, 1.2, expr="neutro", pose="bracos_abertos")
        self.nairj(m, t, 700, 1800, 1.2, expr="surpreso")
        f = self.cam(m, 540, 1250, 1.12)
        self.chuva_f(f, t, 120)
        texto_pop(f, "CHUVA NO CASAMENTO: R$ 200", self.fc, t, OUT_W / 2, OUT_H * 0.12, 36, (255, 214, 40))
        return f

    def p_guiche(self, t, d):
        m = gradiente(WW, WH, (255, 214, 160), (240, 205, 160))
        p = Pincel(WW, WH)
        p.ret((60, 700, 1020, 1300), (170, 215, 240), r=16, ow=10)
        p.ret((40, 1300, 1040, 1420), (150, 100, 70), r=10)
        p.ret((-20, 1420, WW + 20, WH + 20), (185, 175, 160), r=0)
        m.alpha_composite(p.pronto())
        self.func(m, t, 540, 1450, 1.1, expr="feliz", pose="acena")
        m.alpha_composite(p.pronto().crop((0, 1300, WW, 1420)), (0, 1300))
        f = self.cam(m, 540, 1150, 1.1)
        texto_pop(f, "BANCO DO AZAR", self.fc, max(0, self.T - 10.56), OUT_W / 2, OUT_H * 0.1, 72, (255, 214, 40)) \
            if self.T > 10.56 else None
        return f

    def p_fila(self, t, d):
        m = self.banco.copy()
        for i, p in enumerate(self.povo[:5]):
            p(m, t + i, 120 + i * 210, 1800 - (i % 2) * 20, 0.8, expr="ri" if i % 2 else "feliz",
              pose="anda" if i == 0 else "idle")
        return self.cam(m, 540, 1250, 1.1)

    def p_avo(self, t, d):
        m = self.sitio.copy()
        self.nair(m, t, 540, 1780, 1.3, expr="neutro", pose="idle")
        f = self.cam(m, 540, 1200, 1.1 + 0.12 * ease_io(t / d))
        if self.T > 14.26:
            texto_pop(f, "DONA NAIR", self.fc, self.T - 14.26, OUT_W / 2, OUT_H * 0.1, 76, (255, 214, 40))
        return f

    def p_azarada(self, t, d):
        f = self.close(self.nair, t, self.sitio, "sitio", expr="triste", z=1.05)
        if self.T > 16.5:
            texto_pop(f, "A MAIS AZARADA", self.fc, self.T - 16.5, OUT_W / 2, OUT_H * 0.1, 66, (255, 140, 120))
        return f

    def p_onibus_mil(self, t, d):
        m = self.ponto.copy()
        self.onibus.desenhar(m, 300 + 900 * ((t * 1.6) % 1), 1700, 0.8, giro=t * 500)
        self.nairj(m, t, 780, 1800, 1.2, expr="surpreso", pose="corre")
        f = self.cam(m, 560, 1300, 1.12)
        n = int(1000 * ease_out(min(1, t / 1.5)))
        texto_pop(f, f"X {n}", self.fc, 0.3, OUT_W / 2, OUT_H * 0.12, 96, (255, 214, 40))
        return f

    def p_emprego(self, t, d):
        m = self.sala_img.copy()
        self.nairj(m, t, 540, 1800, 1.3, expr="chora", pose="idle")
        f = self.cam(m, 540, 1250, 1.12)
        texto_pop(f, "SEM EMPREGO", self.fc, t, OUT_W / 2, OUT_H * 0.12, 80, (255, 120, 100))
        if self.T > 21.98:
            texto_pop(f, "2 VEZES", self.fc, self.T - 21.98, OUT_W / 2, OUT_H * 0.22, 70, (255, 255, 255))
        return f

    def p_temporal(self, t, d):
        m = self.capela.copy()
        self.noivo(m, t, 380, 1800, 1.2, expr="feliz", pose="bracos_abertos")
        self.nairj(m, t, 700, 1800, 1.2, expr="chora")
        f = self.cam(m, 540, 1250, 1.12)
        self.chuva_f(f, t, 140, seed=3)
        texto_pop(f, "TEMPORAL", self.fc, t, OUT_W / 2, OUT_H * 0.12, 84, (200, 225, 255))
        return f

    def p_alagou(self, t, d):
        m = self.ponto.copy()
        self.nairj(m, t, 540, 1800, 1.3, expr="surpreso", pose="bracos_abertos")
        agua(m, t, 1600)
        f = self.cam(m, 540, 1300, 1.12)
        if self.T > 25.68:
            texto_pop(f, "3 ANOS SEGUIDOS", self.fc, self.T - 25.68, OUT_W / 2, OUT_H * 0.12, 64, (255, 214, 40))
        return f

    def p_vizinhos(self, t, d):
        m = self.ponto.copy()
        for i, (p, x) in enumerate(zip(self.povo[:3], (230, 540, 850))):
            p(m, t + i, x, 1800, 1.1, expr="surpreso" if i == 1 else "feliz", pose="aponta" if i != 1 else "idle")
        f = self.cam(m, 540, 1300, 1.12)
        self.balao_t(f, "Deve ser milionária!", OUT_W / 2, OUT_H * 0.16, 28.38)
        return f

    def p_casinha(self, t, d):
        m = self.sitio.copy()
        self.nair(m, t, 440, 1780, 1.2, expr="feliz", pose="idle")
        f = self.cam(m, 600, 1200, 1.12)
        if self.T > 30.98:
            texto_pop(f, "CASINHA SIMPLES", self.fc, self.T - 30.98, OUT_W / 2, OUT_H * 0.1, 60, (255, 255, 255))
        return f

    def p_zero(self, t, d):
        m = gradiente(WW, WH, (60, 50, 90), (30, 26, 52))
        self.nair(m, t, 540, 1800, 1.4, expr="feliz", pose="bolso")
        f = self.cam(m, 540, 1250, 1.1)
        texto_pop(f, "R$ 0", self.fc, self.T - 32.9 if self.T > 32.9 else 0, OUT_W / 2, OUT_H * 0.12, 130,
                  (255, 120, 100))
        return f

    def p_morreu(self, t, d):
        m = self.sala_img.copy()
        self.neta(m, t, 540, 1800, 1.3, expr="triste", pose="bolso")
        m.alpha_composite(brilho((600, 600), (255, 230, 180), 250, 0.3), (240, 900))
        f = self.cam(m, 540, 1250, 1.1)
        if self.T > 36.0:
            texto_pop(f, "SEMANA PASSADA", self.fc, self.T - 36.0, OUT_W / 2, OUT_H * 0.1, 66, (255, 255, 255))
        return f

    def p_guarda(self, t, d):
        m = self.guarda.copy()
        self.neta(m, t, 300, 1800, 1.2, expr="triste", pose="entrega")
        return self.cam(m, 540, 1150, 1.12)

    def p_caixa(self, t, d):
        m = gradiente(WW, WH, (80, 60, 70), (40, 30, 40))
        cx = caixa_sapato(900, tampa=False)
        m.alpha_composite(brilho((1100, 1100), OURO, 500, 0.35), (-10, 600))
        m.alpha_composite(cx, (90, 800))
        f = self.cam(m, 540, 1000, 1.0 + 0.2 * ease_io(t / d))
        particulas(f, t, 40, cor=(255, 230, 150), semente=4)
        if self.T > 41.46:
            texto_pop(f, "FICHAS DO AZAR", self.fc, self.T - 41.46, OUT_W / 2, OUT_H * 0.12, 62, (255, 214, 40))
        return f

    def p_centenas(self, t, d):
        m = gradiente(WW, WH, (80, 60, 70), (40, 30, 40))
        rng = random.Random(4)
        ff = ficha_frente(150)
        for i in range(60):
            x, y = rng.randint(0, 930), 1000 + rng.randint(0, 800)
            m.alpha_composite(ff, (x, y)) if (t * 40) > i else None
        f = self.cam(m, 540, 1300, 1.0)
        texto_pop(f, "CENTENAS", self.fc, t, OUT_W / 2, OUT_H * 0.1, 90, (255, 214, 40))
        if self.T > 44.24:
            texto_pop(f, "NENHUMA TROCADA", self.fc, self.T - 44.24, OUT_W / 2, OUT_H * 0.2, 56, (255, 255, 255))
        return f

    def p_atras(self, t, d):
        m = gradiente(WW, WH, (80, 60, 70), (40, 30, 40))
        k = ease_io(min(1, t / 0.7))
        w = max(10, int(700 * abs(math.cos(k * math.pi))))
        ff = ficha_frente(700)
        im = ff.resize((w, 700), Image.BICUBIC)
        if k > 0.5:
            c = cartao(self.fc, ["escrito à caneta"], 700)
            im = c.resize((max(10, w), int(c.height * 700 / c.width)), Image.BICUBIC)
        m.alpha_composite(im, (540 - im.width // 2, 960 - im.height // 2))
        return self.cam(m, 540, 1000, 1.0 + 0.1 * ease_io(t / d))

    def cena_ficha(self, t, bg, linhas, t0, y_card=OUT_H * 0.1):
        f = self.cam(bg, 540, 1250, 1.12)
        self.card(f, linhas, y_card, t0)
        return f

    def p_f1(self, t, d):
        m = self.ponto.copy()
        self.nairj(m, t, 330, 1800, 1.2, expr="surpreso", pose="idle")
        self.avoj(m, t, 700 if self.T < 49.9 else 640, 1800, 1.2, expr="feliz", pose="acena")
        self.onibus.desenhar(m, 900 + 900 * ease_in_(min(1, t / 1.0)), 1700, 0.7)
        return self.cena_ficha(t, m, ["Perdi o ônibus.", "Conheci o seu avô", "no ponto."], 48.8)

    def p_f2(self, t, d):
        m = self.padaria.copy()
        self.nairj(m, t, 540, 1800, 1.3, expr="feliz", pose="bracos_abertos")
        return self.cena_ficha(t, m, ["Perdi o emprego.", "Abri a padaria."], 51.58)

    def p_f3(self, t, d):
        m = self.capela.copy()
        k = (t * 2) % 2
        self.noivo(m, t, 420, 1800, 1.2, expr="ri", pose="palmas")
        self.nairj(m, t, 680, 1800, 1.2, expr="ri", pose="bracos_abertos")
        f = self.cena_ficha(t, m, ["Choveu no casamento.", "Ninguém foi embora."], 53.74)
        self.chuva_f(f, t, 100, seed=2)
        if self.T > 55.86:
            texto_pop(f, "DANÇARAM NA CHUVA", self.fc, self.T - 55.86, OUT_W / 2, OUT_H * 0.36, 48, (255, 255, 255))
        return f

    def p_f4(self, t, d):
        m = self.ponto.copy()
        for i, (p, x) in enumerate(zip(self.povo[:3], (250, 540, 840))):
            p(m, t + i, x, 1800, 1.1, expr="feliz", pose="bate" if i % 2 else "idle")
        self.nairj(m, t, 540, 1860, 1.0, expr="feliz")
        agua(m, t, 1650)
        f = self.cena_ficha(t, m, ["A casa alagou.", "Os vizinhos viraram", "a nossa família."], 57.8)
        return f

    def p_f5(self, t, d):
        m = self.padaria.copy()
        T = self.T
        cesta = Pincel(300, 160)
        cesta.ret((10, 60, 290, 150), (190, 140, 80), r=20)
        m.alpha_composite(cesta.pronto(), (700, 1700))
        m.alpha_composite(vb.bebe(220), (740, 1590))
        self.nairj(m, t, 360, 1800, 1.3, expr="surpreso" if T < 64.5 else "feliz", pose="entrega")
        f = self.cena_ficha(t, m, ["Voltei a pé e encontrei", "a sua mãe, bebê,", "na porta da padaria."], 61.84)
        if T > 64.46:
            texto_pop(f, "SUA MÃE", self.fc, T - 64.46, OUT_W / 2, OUT_H * 0.4, 70, (255, 214, 40))
        return f

    def p_entendi(self, t, d):
        f = self.close(self.neta, t, self.sala_img, "sala", expr="chora", z=1.05)
        return f

    def p_pagou(self, t, d):
        m = gradiente(WW, WH, (80, 60, 70), (40, 30, 40))
        ff = ficha_frente(560)
        m.alpha_composite(brilho((1000, 1000), OURO, 480, 0.4 + 0.2 * math.sin(t * 6)), (40, 500))
        m.alpha_composite(ff, (260, 700 + int(14 * math.sin(t * 3))))
        f = self.cam(m, 540, 1000, 1.0 + 0.12 * ease_io(t / d))
        particulas(f, t, 50, cor=(255, 230, 150), semente=7)
        texto_pop(f, "JÁ TINHA PAGO", self.fc, max(0, self.T - 70.84), OUT_W / 2, OUT_H * 0.12, 66, (255, 214, 40)) \
            if self.T > 70.84 else None
        if self.T > 71.82:
            texto_pop(f, "COM JUROS", self.fc, self.T - 71.82, OUT_W / 2, OUT_H * 0.22, 90, (120, 235, 140))
        return f

    def p_ultima(self, t, d):
        m = self.sala_img.copy()
        self.nair(m, t, 560, 1800, 1.3, expr="triste", pose="idle")
        self.neta(m, t, 220, 1800, 1.1, expr="chora", pose="idle")
        f = self.cam(m, 540, 1250, 1.1)
        self.card(f, ["Descobri que estou doente.", "Tive tempo de me", "despedir de vocês."], OUT_H * 0.08, 75.62)
        return f

    def p_guiche2(self, t, d):
        m = gradiente(WW, WH, (255, 214, 160), (240, 205, 160))
        p = Pincel(WW, WH)
        p.ret((60, 700, 1020, 1300), (170, 215, 240), r=16, ow=10)
        p.ret((40, 1300, 1040, 1420), (150, 100, 70), r=10)
        p.ret((-20, 1420, WW + 20, WH + 20), (185, 175, 160), r=0)
        m.alpha_composite(p.pronto())
        self.func(m, t, 700, 1450, 1.1, expr="triste", pose="entrega")
        self.neta(m, t, 280, 1800, 1.3, expr="chora", pose="entrega")
        m.alpha_composite(ficha_frente(220), (480, 1140))
        return self.cam(m, 540, 1250, 1.1)

    def p_nao_troquei(self, t, d):
        m = gradiente(WW, WH, (80, 60, 70), (40, 30, 40))
        c = cartao(self.fc, ["Tive a melhor", "avó do mundo."], 900)
        m.alpha_composite(brilho((1000, 1000), OURO, 480, 0.3), (40, 500))
        m.alpha_composite(c, (540 - c.width // 2, 900))
        f = self.cam(m, 540, 1000, 1.0 + 0.12 * ease_io(t / d))
        particulas(f, t, 40, cor=(255, 230, 150), semente=9)
        texto_pop(f, "EU NÃO TROQUEI", self.fc, t, OUT_W / 2, OUT_H * 0.12, 66, (255, 255, 255))
        return f

    def p_final(self, t, d):
        m = gradiente(WW, WH, (255, 190, 130), (250, 225, 190))
        p = Pincel(WW, WH)
        p.elipse((380, 820, 700, 1140), (255, 235, 150), ow=0)
        p.ret((-20, 1500, WW + 20, WH + 20), (200, 185, 170), r=0)
        m.alpha_composite(p.pronto())
        self.neta(m, t, 540, 1800, 1.4, expr="feliz", pose="entrega")
        hx, hy = self.neta.a.maos_mundo[1]
        m.alpha_composite(ficha_frente(170), (int(hx - 85), int(hy - 200)))
        f = self.cam(m, 540, 1250, 1.1 + 0.08 * ease_io(t / d))
        particulas(f, t, 50, cor=(255, 240, 200), semente=6)
        if self.T > 88.36:
            texto_pop(f, "É SÓ LER O VERSO", self.fc, self.T - 88.36, OUT_W / 2, OUT_H * 0.12, 62, (255, 255, 255))
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
    ev = filme.eventos_sfx()
    ev += [("brilho", 0.2), ("pop", 2.38), ("pop", 4.22), ("pop", 6.02), ("toc", 32.9), ("brilho", 39.34),
           ("brilho", 43.3), ("toc", 45.7), ("brilho", 71.82), ("brilho", 83.0), ("brilho", 88.36)]
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
    troca = {"Pineufurado?": "Pneu furado?", "Chuveu": "Choveu", "lagou": "alagou", "Conjuros.": "Com juros.",
             "Perdeu": "Perdi", "Abria": "Abri"}
    out = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            out.append(dict(w=troca.get(w["w"], w["w"]), s=w["s"], e=w["e"]))
    # junta "guarda" + "-roupa"
    res, i = [], 0
    while i < len(out):
        if out[i]["w"] == "guarda" and i + 1 < len(out) and out[i + 1]["w"].startswith("-roupa"):
            res.append(dict(w="guarda-roupa" + out[i + 1]["w"][6:], s=out[i]["s"], e=out[i + 1]["e"]))
            i += 2
            continue
        res.append(out[i])
        i += 1
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_banco_do_azar.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeAzar(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.4, a.narracao)
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

    tmp = tempfile.mkdtemp(prefix="azar_")
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
