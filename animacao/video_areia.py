#!/usr/bin/env python3
"""
"A Areia da Vó" — todo mundo tem uma ampulheta em cima da cabeça; a areia só para quando a pessoa ri.

Efeitos: ampulheta animada acima de cada personagem (areia escorrendo em fio, grãos caindo),
areia congelando no ar quando a vó ri, montagem do Caio palhaço (peruca, nariz, dentadura),
chamada de vídeo, contador de anos e o último grão em câmera lenta.

    python3 animacao/video_areia.py --narracao narr.wav --transcricao transcricao.json --fonte Poppins.ttf
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
from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_video as g  # noqa: E402
import video_carta as vc  # noqa: E402
import video_corsa as vco  # noqa: E402
import video_estatua as ve  # noqa: E402
import video_sono as vs  # noqa: E402
import video_milhao as vm  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, gradiente, brilho,
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(505)

CAIO = dict(pele=(222, 170, 128), cabelo=(60, 40, 28), camisa=(70, 150, 220), calca=(50, 60, 90),
            sapato=(240, 240, 240), tipo="menino")
NENA = dict(pele=(214, 160, 120), cabelo=(228, 228, 232), camisa=(240, 170, 150), calca=(0, 0, 0),
            sapato=(140, 90, 80), tipo="vovo", vestido=(240, 170, 150))
MAE = dict(pele=(222, 170, 128), cabelo=(70, 45, 30), camisa=(200, 90, 120), calca=(0, 0, 0),
           sapato=(120, 60, 80), tipo="moca", vestido=(200, 90, 120))
SOGRA = dict(pele=(232, 186, 150), cabelo=(200, 200, 205), camisa=(130, 80, 160), calca=(0, 0, 0),
             sapato=(90, 60, 100), tipo="vovo", vestido=(130, 80, 160))
CHEFE = dict(pele=(232, 186, 150), cabelo=(70, 60, 55), camisa=(45, 50, 70), calca=(40, 45, 60),
             sapato=(30, 30, 30), tipo="pai", bigode=False, gravata=(200, 40, 40))
NAMORADO = dict(pele=(196, 140, 100), cabelo=(30, 25, 25), camisa=(90, 170, 120), calca=(60, 70, 110),
                sapato=(60, 60, 60), tipo="pai", bigode=False)
NAMORADA = dict(pele=(235, 190, 150), cabelo=(150, 60, 40), camisa=(230, 110, 170), calca=(0, 0, 0),
                sapato=(200, 60, 120), tipo="moca", vestido=(230, 110, 170))
AMIGOS = ve.POVO
AREIA = (235, 195, 110)
vc.DESTAQUE_VERMELHO = set()


# --------------------------------------------------------------------------
# Ampulheta
# --------------------------------------------------------------------------
_CACHE = {}


def ampulheta(cima, baixo, w=200):
    """cima/baixo: fração de areia (0–1) em cada bulbo."""
    k = (round(cima, 2), round(baixo, 2), w)
    if k in _CACHE:
        return _CACHE[k]
    h = int(w * 1.55)
    p = Pincel(w, h)
    c = w / 2
    m = h / 2
    p.ret((0, 0, w, h * 0.09), (150, 100, 60), r=10)
    p.ret((0, h * 0.91, w, h), (150, 100, 60), r=10)
    vidro = (215, 235, 250)
    p.poli([(w * 0.1, h * 0.09), (w * 0.9, h * 0.09), (c + 12, m), (c - 12, m)], vidro, ow=5)
    p.poli([(c - 12, m), (c + 12, m), (w * 0.9, h * 0.91), (w * 0.1, h * 0.91)], vidro, ow=5)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    # areia de cima (triângulo invertido que encolhe para o gargalo)
    if cima > 0.005:
        yt = m - (m - h * 0.09) * cima
        frac = (m - yt) / (m - h * 0.09)
        half = 12 + (w * 0.4 - 12) * frac
        d.polygon([(c - half, yt), (c + half, yt), (c + 10, m - 3), (c - 10, m - 3)], fill=AREIA)
    # areia de baixo (montinho)
    if baixo > 0.005:
        yb = h * 0.91 - (h * 0.91 - m) * baixo
        frac = (h * 0.91 - yb) / (h * 0.91 - m)
        half = w * 0.4 - (w * 0.4 - 12) * frac
        d.polygon([(c - w * 0.4 + 4, h * 0.91 - 4), (c + w * 0.4 - 4, h * 0.91 - 4), (c + half * 0.6, yb),
                   (c, yb - 8), (c - half * 0.6, yb)], fill=AREIA)
    d.line((w * 0.25, h * 0.15, w * 0.35, h * 0.35), fill=(255, 255, 255), width=5)     # reflexo
    _CACHE[k] = img
    return img


def fio_de_areia(m, x, y_top, y_bot, t, parado=False, w=6):
    """Fio de areia saindo do gargalo; se parado, grãos suspensos no ar."""
    d = ImageDraw.Draw(m)
    if not parado:
        d.line((x, y_top, x, y_bot), fill=AREIA, width=w)
        for i in range(4):
            yy = y_top + ((t * 300 + i * 30) % max(1, (y_bot - y_top)))
            d.ellipse((x - w, yy - w, x + w, yy + w), fill=AREIA)
    else:
        for i in range(5):
            yy = y_top + (i + 0.5) * (y_bot - y_top) / 5
            d.ellipse((x - w * 0.8, yy - w * 0.8, x + w * 0.8, yy + w * 0.8), fill=AREIA)


def com_ampulheta(m, pers, t, cx, by, e, cima, baixo, expr="neutro", pose="idle", parado=False, escala_amp=1.0,
                  **kw):
    pers(m, t, cx, by, e, expr=expr, pose=pose, **kw)
    w = int(150 * e * escala_amp)
    amp = ampulheta(cima, baixo, w)
    bob = getattr(pers.a, "ultimo_bob", 4 * math.sin(t * 2 * math.pi * 0.9))
    x0 = cx - amp.width / 2
    y0 = by - bob - 650 * e - amp.height - 10
    m.alpha_composite(amp, (int(x0), int(y0)))
    if cima > 0.005:
        hh = amp.height
        fio_de_areia(m, cx, y0 + hh / 2, y0 + hh * 0.91 - (hh * 0.41) * baixo - 6, t, parado, w=max(3, int(4 * e)))


# --------------------------------------------------------------------------
# Objetos e cenários
# --------------------------------------------------------------------------
def cozinha():
    base = gradiente(WW, WH, (250, 230, 200), (235, 210, 175))
    p = Pincel(WW, WH)
    for y in range(400, 1100, 90):
        for x in range(0, WW, 90):
            p.ret((x + 4, y + 4, x + 86, y + 86), (245, 240, 225), r=6, ow=0)
    p.ret((640, 200, 960, 520), (170, 215, 240), r=10, ow=10)
    p.ret((-20, 1450, WW + 20, WH + 20), (170, 120, 90), r=0)
    base.alpha_composite(p.pronto())
    return base


def mesa_cafe():
    p = Pincel(WW, 520)
    p.ret((60, 60, WW - 60, 150), (190, 120, 80), r=16)
    p.ret((100, 150, 140, 520), (160, 100, 70), r=10)
    p.ret((WW - 140, 150, WW - 100, 520), (160, 100, 70), r=10)
    p.ret((420, 0, 500, 64), (250, 250, 250), r=10)              # xícara
    p.elipse((620, 20, 760, 70), (250, 250, 250))
    return p.pronto()


def sala():
    base = gradiente(WW, WH, (240, 220, 190), (225, 205, 175))
    p = Pincel(WW, WH)
    p.ret((60, 200, 300, 420), (200, 180, 150), r=8, ow=8)
    p.ret((-20, 1450, WW + 20, WH + 20), (160, 120, 90), r=0)
    p.ret((120, 1300, 960, 1460), (150, 90, 160), r=30)                       # sofá
    p.ret((120, 1120, 960, 1320), (130, 80, 140), r=30)
    base.alpha_composite(p.pronto())
    return base


def palco():
    base = gradiente(WW, WH, (60, 30, 50), (35, 20, 35))
    p = Pincel(WW, WH)
    for lado in (0, 1):
        x0 = -40 if lado == 0 else WW - 260
        p.ret((x0, -20, x0 + 300, 1500), (190, 40, 60), r=20)
    p.ret((-20, 1350, WW + 20, WH + 20), (150, 100, 60), r=0)
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((900, 1300), (255, 240, 200), 550, 0.55), (90, 300))
    return base


def quarto_cama(noite=False):
    base = gradiente(WW, WH, (60, 60, 95) if noite else (230, 215, 200), (80, 75, 110) if noite else (215, 200, 185))
    p = Pincel(WW, WH)
    p.ret((640, 260, 960, 620), (25, 30, 60) if noite else (190, 220, 240), r=10, ow=10)
    if noite:
        p.elipse((760, 330, 840, 410), (240, 235, 210), ow=0)
    p.ret((-20, 1450, WW + 20, WH + 20), (120, 100, 90), r=0)
    p.ret((80, 1150, 1000, 1450), (150, 170, 210), r=30)
    p.ret((80, 1050, 360, 1200), (245, 245, 250), r=30)
    base.alpha_composite(p.pronto())
    return base


def restaurante():
    base = gradiente(WW, WH, (90, 50, 60), (60, 35, 45))
    p = Pincel(WW, WH)
    p.ret((-20, 1450, WW + 20, WH + 20), (100, 70, 60), r=0)
    p.ret((200, 1350, 880, 1420), (250, 250, 250), r=10)
    p.ret((520, 1240, 560, 1350), (250, 240, 200), r=6)
    p.elipse((515, 1200, 565, 1250), (255, 200, 80), ow=0)
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((500, 500), (255, 200, 120), 250, 0.6), (290, 970))
    return base


def escritorio():
    base = gradiente(WW, WH, (215, 220, 230), (195, 200, 210))
    p = Pincel(WW, WH)
    p.ret((-20, 1400, WW + 20, WH + 20), (150, 145, 140), r=0)
    p.ret((100, 1150, 980, 1230), (150, 110, 80), r=10)
    base.alpha_composite(p.pronto())
    return base


def peruca_nariz(f_spr, e):
    """Acessórios de palhaço por cima de um sprite já colado (desenha num overlay)."""
    p = Pincel(340, 640)
    for x in range(-2, 3):
        p.elipse((170 + x * 46 - 50, 20, 170 + x * 46 + 50, 120), (240, 90, 60), ow=0)
    p.elipse((150, 230, 190, 270), (230, 40, 40), ow=4)
    return p.pronto()


def dentadura():
    p = Pincel(200, 120)
    p.chord((10, 10, 190, 110), 0, 180, (240, 140, 150))
    for x in range(30, 180, 26):
        p.ret((x, 40, x + 22, 80), (255, 255, 255), r=4, ow=3)
    return p.pronto()


def livro_piadas(fc):
    p = Pincel(400, 500)
    p.ret((10, 10, 390, 490), (240, 200, 60), r=12)
    p.ret((40, 40, 360, 460), (250, 230, 120), r=6, ow=4)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    for i, l in enumerate(("1001", "PIADAS", "RUINS")):
        f = vc.fonte(fc, 60 if i else 80)
        d.text((200 - f.getlength(l) / 2, 120 + i * 90), l, font=f, fill=(150, 60, 40))
    return img


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeAreia(ve.FilmeEstatua):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.caio, self.nena, self.mae = P_(CAIO), P_(NENA), P_(MAE)
        self.sogra, self.chefe, self.nam1, self.nam2 = P_(SOGRA), P_(CHEFE), P_(NAMORADO), P_(NAMORADA)
        self.amigos = [P_(c) for c in AMIGOS]
        self.blur = {}
        self.rua = vco.rua(fc)
        self.coz, self.sala_img, self.palco_img = cozinha(), sala(), palco()
        self.q_dia, self.q_noite = quarto_cama(), quarto_cama(True)
        self.rest, self.escr = restaurante(), escritorio()
        self.mesa = mesa_cafe()
        self.palhaco = peruca_nariz(None, 1)
        self.dent = dentadura()
        self.livro = livro_piadas(fc)
        self.cel_video = vs.celular(fc, "VÍDEO", [("VÓ NENA", 60, (40, 40, 55))], cor=(40, 160, 90))
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.FALA_MAE = [(60.22, 61.9)]
        self.FALA_NENA = [(88.12, 88.95)]
        self.FALA_CAIO = [(89.30, 91.4)]

        P = [
            (0.00, self.p_hook, "", "corte"),
            (4.28, self.p_olha, "", "corte"),
            (8.06, self.p_sogra, "", "whip"),
            (10.98, self.p_chefe, "", "corte"),
            (13.32, self.p_encontro, "", "whip"),
            (18.24, self.p_detalhe, "", "zoom"),
            (23.28, self.p_caio, "quente", "dissolve"),
            (26.74, self.p_quase_vazia, "", "zoom"),
            (31.86, self.p_noite, "frio", "dissolve"),
            (35.42, self.p_leite, "quente", "whip"),
            (41.14, self.p_entendeu, "", "corte"),
            (43.68, self.p_aprende, "", "whip"),
            (48.90, self.p_imita, "", "corte"),
            (52.58, self.p_fantasia, "", "corte"),
            (56.66, self.p_amigos, "", "corte"),
            (59.20, self.p_mae, "", "corte"),
            (62.14, self.p_nao_caia, "quente", "corte"),
            (63.92, self.p_show, "", "whip"),
            (68.10, self.p_faculdade, "", "whip"),
            (73.60, self.p_ruim, "quente", "corte"),
            (78.56, self.p_11, "", "zoom"),
            (84.42, self.p_ultimo, "", "dissolve"),
            (89.30, self.p_piada, "", "corte"),
            (91.90, self.p_riu, "quente", "corte"),
            (93.84, self.p_grao, "", "corte"),
            (96.06, self.p_rindo, "quente", "corte"),
            (97.54, self.p_voce, "", "dissolve"),
            (103.44, self.p_final, "quente", "dissolve"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))
        self.p_preto = None

    def cam(self, m, cx, cy, z):
        return camera(m, cx, cy, z)

    # ---------- planos ----------
    def p_hook(self, t, d):
        m = self.rua.copy()
        for i, (p, x, cima) in enumerate(zip(self.amigos[:4], (150, 410, 670, 930), (0.8, 0.5, 0.65, 0.3))):
            pose = "anda1" if int(t * 2.4 + i) % 2 else "anda2"
            com_ampulheta(m, p, t + i, x, 1760, 0.8, cima, 1 - cima, expr="neutro", pose=pose)
        f = self.cam(m, 540, 1200, 1.1 - 0.05 * ease_io(t / d))
        return f

    def p_olha(self, t, d):
        m = self.rua.copy()
        com_ampulheta(m, self.nam1, t, 330, 1780, 1.15, 0.6, 0.4, expr="neutro")
        com_ampulheta(m, self.nam2, t, 760, 1780, 1.1, 0.7, 0.3, expr="feliz")
        f = self.cam(m, 540, 1150, 1.1)
        return f

    def p_sogra(self, t, d):
        m = self.coz.copy()
        com_ampulheta(m, self.sogra, t, 540, 1850, 1.0, 0.95, 0.05, expr="bravo", escala_amp=3.6)
        self.caio(m, t, 900, 1850, 0.7, expr="surpreso")
        f = self.cam(m, 540, 1000, 1.0)
        texto_pop(f, "A SOGRA", self.fc, t, OUT_W / 2, OUT_H * 0.84, 70, (255, 255, 255))
        return f

    def p_chefe(self, t, d):
        m = self.escr.copy()
        com_ampulheta(m, self.chefe, t, 540, 1760, 1.25, 0.98, 0.02, expr="bravo", parado=True)
        f = self.cam(m, 540, 1100, 1.1)
        texto_pop(f, "NEM SE MEXE", self.fc, t, OUT_W / 2, OUT_H * 0.14, 70, (255, 255, 255))
        return f

    def p_encontro(self, t, d):
        m = self.rest.copy()
        com_ampulheta(m, self.nam1, t, 300, 1480, 0.95, 0.1, 0.9, expr="triste", escala_amp=0.55)
        com_ampulheta(m, self.nam2, t, 780, 1480, 0.95, 0.1, 0.9, expr="triste", escala_amp=0.55)
        f = self.cam(m, 540, 1150, 1.1)
        if self.T > 16.6:
            texto_pop(f, "SEM SOBREMESA", self.fc, self.T - 16.6, OUT_W / 2, OUT_H * 0.14, 64, (255, 120, 120))
        return f

    def p_detalhe(self, t, d):
        m = gradiente(WW, WH, (50, 45, 70), (25, 22, 40))
        rindo = self.T > 21.80
        com_ampulheta(m, self.amigos[1], t, 540, 1700, 1.3, 0.5, 0.5, expr="ri" if rindo else "neutro",
                      parado=rindo, escala_amp=1.3)
        f = self.cam(m, 540, 1050, 1.05)
        texto_pop(f, "SÓ TEM UM DETALHE", self.fc, t, OUT_W / 2, OUT_H * 0.1, 60, (255, 214, 40))
        if rindo:
            texto_pop(f, "QUANDO RI, PARA", self.fc, self.T - 21.80, OUT_W / 2, OUT_H * 0.8, 60, (255, 255, 255))
        return f

    def p_caio(self, t, d):
        m = self.coz.copy()
        com_ampulheta(m, self.nena, t, 720, 1760, 1.1, 0.03, 0.97, expr="feliz", pose="entrega")
        x = -100 + 400 * min(1, t / 2.0)
        self.caio(m, t, x, 1800, 1.05, expr="feliz", pose="anda1" if int(t * 3) % 2 and t < 2 else "idle")
        f = self.cam(m, 540, 1150, 1.1)
        if self.T > 25.56:
            texto_pop(f, "VÓ NENA", self.fc, self.T - 25.56, OUT_W * 0.66, OUT_H * 0.1, 64, (255, 214, 40))
        return f

    def p_quase_vazia(self, t, d):
        m = gradiente(WW, WH, (60, 50, 60), (35, 30, 40))
        amp = ampulheta(0.03, 0.97, 600)
        m.alpha_composite(amp, (240, 500))
        fio_de_areia(m, 540, 500 + amp.height / 2, 500 + amp.height * 0.91 - amp.height * 0.4 - 6, t, w=8)
        f = self.cam(m, 540, 950, 1.0 + 0.2 * ease_io(t / d))
        if self.T > 29.52:
            texto_pop(f, "QUASE VAZIA", self.fc, self.T - 29.52, OUT_W / 2, OUT_H * 0.1, 76, (255, 120, 100))
        return f

    def p_noite(self, t, d):
        m = self.q_noite.copy()
        spr = self.caio.spr("triste", "idle").rotate(90, expand=True)
        g.colar(m, spr, 520, 1260, 0.9)
        return self.cam(m, 540, 1100, 1.15)

    def p_leite(self, t, d):
        m = self.coz.copy()
        T = self.T
        rindo = T > 39.16
        com_ampulheta(m, self.nena, t, 760, 1600, 1.0, 0.03, 0.97, expr="ri" if rindo else "neutro", parado=rindo)
        self.caio(m, t, 300, 1640, 1.0, expr="ri" if T > 37.8 else "neutro", pose="bate2" if 36.5 < T < 37.3 else "idle")
        m.alpha_composite(self.mesa, (0, 1350))
        if T > 36.6:                 # leite derramado
            k = min(1, (T - 36.6) / 0.6)
            p = Pincel(WW, 300)
            p.elipse((380, 40, 380 + 320 * k, 110), (250, 250, 250), ow=0)
            m.alpha_composite(p.pronto(), (0, 1350))
        f = self.cam(m, 540, 1250, 1.1)
        if T > 40.10:
            texto_pop(f, "A AREIA PAROU", self.fc, T - 40.10, OUT_W / 2, OUT_H * 0.12, 70, (255, 214, 40))
        return f

    def p_entendeu(self, t, d):
        m = self.fundo_blur("coz", self.coz)
        self.caio(m, t, 540, 2350, 2.5, expr="bravo" if t > 1.0 else "surpreso")
        return self.cam(m, 540, 950, 1.05 + 0.1 * ease_out(t / d))

    def p_aprende(self, t, d):
        T = self.T
        m = self.sala_img.copy()
        if T < 44.94:
            self.caio(m, t, 380, 1780, 1.2, expr="ri", pose="entrega")
            hx, hy = self.mao(380, 1780, 1.2, t)
            self.segura(m, self.livro, hx + 80, hy - 40, 260)
            txt, t0 = "PIADA", 43.68
        elif T < 46.34:
            self.caio(m, t, 540, 1780, 1.2, expr="bravo", pose="aponta")
            txt, t0 = "IMITAÇÃO", 44.94
        else:
            k = ease_out(min(1, (T - 46.84) / 0.5))
            p = Pincel(WW, WH)
            p.ret((600, 1400, 800, 1460), (140, 90, 60), r=8)
            m.alpha_composite(p.pronto())
            self.caio(m, t, 700 - 200 * k, 1780 + 40 * k, 1.2, expr="surpreso" if k < 1 else "ri", rot=-70 * k)
            txt, t0 = "CAIR DA CADEIRA", 46.34
        f = self.cam(m, 540, 1250, 1.1)
        texto_pop(f, txt, self.fc, T - t0, OUT_W / 2, OUT_H * 0.12, 70, (255, 214, 40))
        return f

    def p_imita(self, t, d):
        T = self.T
        m = self.palco_img.copy()
        if T < 50.02:
            fig = dict(CAIO, camisa=(40, 40, 45), calca=(40, 40, 45))
            txt, t0 = "O PADRE", 48.90
        elif T < 51.18:
            fig = dict(CAIO, camisa=(240, 190, 60), chapeu=(90, 140, 60))
            txt, t0 = "O VIZINHO", 50.02
        else:
            fig = dict(CAIO, camisa=NENA["camisa"], cabelo=NENA["cabelo"])
            txt, t0 = "A VÓ", 51.18
        ator = g.Ator(fig)
        ator.desenhar(m, t, 540, 1700, escala=1.3, expr="ri" if int(t * 4) % 2 else "fala")
        f = self.cam(m, 540, 1150, 1.1)
        texto_pop(f, txt, self.fc, T - t0, OUT_W / 2, OUT_H * 0.12, 80, (255, 255, 255))
        return f

    def p_fantasia(self, t, d):
        T = self.T
        m = self.palco_img.copy()
        self.caio(m, t, 540, 2300, 2.4, expr="ri")
        if T > 52.84:
            g.colar(m, self.palhaco, 540, 2300, 2.4)
        if T > 55.02:
            self.segura(m, self.dent, 540, 2300 - (640 - 253) * 2.4, 230)
        f = self.cam(m, 540, 950, 1.05)
        vm.confete(f, t, 30)
        return f

    def p_amigos(self, t, d):
        m = self.rua.copy()
        for i, (p, x) in enumerate(zip(self.amigos[:3], (200, 540, 880))):
            p(m, t + i, x, 1760, 0.95, expr="surpreso")
        f = self.cam(m, 540, 1250, 1.1)
        for i, x in enumerate((0.2, 0.5, 0.8)):
            texto_pop(f, "?", self.fc, max(0, t - i * 0.25), OUT_W * x, OUT_H * 0.28, 110, (255, 214, 40))
        return f

    def p_mae(self, t, d):
        m = self.fundo_blur("sala", self.sala_img)
        self.mae(m, t, 540, 2350, 2.5, expr="bravo", fala=self.FALA_MAE)
        return self.cam(m, 540, 950, 1.05)

    def p_nao_caia(self, t, d):
        m = self.sala_img.copy()
        com_ampulheta(m, self.nena, t, 540, 1700, 1.3, 0.03, 0.97, expr="ri", parado=True, escala_amp=1.5)
        f = self.cam(m, 540, 1050, 1.15)
        return f

    def p_show(self, t, d):
        m = self.sala_img.copy()
        p = Pincel(WW, 600)
        for lado in (0, 1):
            x0 = -40 if lado == 0 else WW - 200
            p.ret((x0, 0, x0 + 240, 600), (190, 40, 60), r=12)
        m.alpha_composite(p.pronto(), (0, 400))
        rindo = int(t * 4) % 2
        com_ampulheta(m, self.nena, t, 760, 1450, 0.9, 0.03, 0.97, expr="ri" if rindo else "feliz", parado=True)
        self.caio(m, t, 300, 1800, 1.1, expr="ri", pose="acena" if rindo else "aponta", pulo=20 * rindo)
        f = self.cam(m, 540, 1250, 1.1)
        T = self.T
        texto_pop(f, "SHOW DE DOMINGO" if T < 65.98 else "SHOW DUPLO", self.fc, (T - 63.92) if T < 65.98 else T - 65.98,
                  OUT_W / 2, OUT_H * 0.12, 64, (255, 214, 40))
        return f

    def p_faculdade(self, t, d):
        m = gradiente(WW, WH, (60, 70, 100), (35, 40, 60))
        tel = self.cel_video.copy()
        mini = Image.new("RGBA", (500, 520), (240, 225, 200, 255))
        a = g.Ator(NENA)
        a.desenhar(mini, t, 250, 900, escala=1.3, expr="ri" if int(t * 4) % 2 else "feliz")
        tel.alpha_composite(mini, (60, 330))
        self.segura(m, tel, 540, 960, 700)
        f = self.cam(m, 540, 960, 1.05)
        if self.T > 72.70:
            texto_pop(f, "1 PIADA POR DIA", self.fc, self.T - 72.70, OUT_W / 2, OUT_H * 0.1, 64, (255, 214, 40))
        return f

    def p_ruim(self, t, d):
        m = self.sala_img.copy()
        rindo = self.T > 76.84
        com_ampulheta(m, self.nena, t, 760, 1450, 0.9, 0.03, 0.97, expr="ri" if rindo else "neutro", parado=True)
        self.caio(m, t, 300, 1800, 1.1, expr="feliz", pose="aponta")
        f = self.cam(m, 540, 1250, 1.1)
        if not rindo:
            texto_pop(f, "…cri cri…", self.fc, t, OUT_W * 0.3, OUT_H * 0.28, 50, (200, 200, 210))
        else:
            texto_pop(f, "HAHAHA!", self.fc, self.T - 76.84, OUT_W * 0.7, OUT_H * 0.22, 80, (255, 214, 40))
        return f

    def p_11(self, t, d):
        m = gradiente(WW, WH, (250, 220, 170), (235, 190, 140))
        amp = ampulheta(0.03, 0.97, 520)
        m.alpha_composite(amp, (280, 520))
        fio_de_areia(m, 540, 520 + amp.height / 2, 520 + amp.height * 0.91 - amp.height * 0.4 - 6, t, parado=True,
                     w=8)
        f = self.cam(m, 540, 950, 1.05)
        anos = min(11, int(1 + 11 * ease_io(min(1, t / 3.0))))
        self.painel(f, "ANOS", str(anos), t, y=0.06)
        return f

    def p_ultimo(self, t, d):
        m = self.q_dia.copy()
        spr = self.nena.spr("feliz", "idle").rotate(90, expand=True)
        g.colar(m, spr, 560, 1300, 0.85)
        amp = ampulheta(0.01, 0.99, 160)
        m.alpha_composite(amp, (480, 830))
        self.caio(m, t, 820, 1780, 1.05, expr="neutro", pose="entrega")
        f = self.cam(m, 600, 1200, 1.12)
        return f

    def p_piada(self, t, d):
        m = self.fundo_blur("q_dia", self.q_dia)
        self.caio(m, t, 540, 2350, 2.5, expr="feliz", fala=self.FALA_CAIO)
        return self.cam(m, 540, 950, 1.05)

    def p_riu(self, t, d):
        m = self.fundo_blur("q_dia", self.q_dia)
        m.alpha_composite(brilho((1000, 1000), (255, 230, 170), 500, 0.6), (40, 300))
        self.nena(m, t, 540, 2350, 2.5, expr="chora" if int(t * 3) % 2 else "ri")
        f = self.cam(m, 540, 950, 1.05)
        particulas(f, t, 30, (255, 230, 160), semente=3)
        return f

    def p_grao(self, t, d):
        m = gradiente(WW, WH, (250, 220, 170), (235, 190, 140))
        amp = ampulheta(0.0, 1.0, 560)
        m.alpha_composite(amp, (260, 480))
        k = ease_io(min(1, t / (d * 0.85)))                       # o último grão, em câmera lenta
        y = 480 + amp.height / 2 + (amp.height * 0.4 - 30) * k
        dd = ImageDraw.Draw(m)
        dd.ellipse((540 - 20, y - 20, 540 + 20, y + 20), fill=AREIA, outline=(200, 160, 80), width=4)
        m.alpha_composite(brilho((300, 300), (255, 230, 150), 150, 0.6), (390, int(y - 150)))
        return self.cam(m, 540, 950, 1.1 + 0.15 * k)

    def p_rindo(self, t, d):
        m = self.fundo_blur("q_dia", self.q_dia)
        m.alpha_composite(brilho((1080, 1080), (255, 230, 170), 540, 0.8), (0, 300))
        self.nena(m, t, 540, 2350, 2.5, expr="ri", piscar=False)
        f = self.cam(m, 540, 950, 1.05)
        particulas(f, t, 40, (255, 230, 160), semente=4)
        return f

    def p_voce(self, t, d):
        m = gradiente(WW, WH, (20, 20, 30), (8, 8, 14))
        a = 0.25 + 0.15 * math.sin(t * 2)
        amp = ampulheta(0.5, 0.5, 420)
        amp.putalpha(amp.getchannel("A").point(lambda v: int(v * a)))
        m.alpha_composite(amp, (330, 520))
        f = self.cam(m, 540, 950, 1.05 + 0.08 * ease_io(t / d))
        if self.T > 98.74:
            texto_pop(f, "?", self.fc, self.T - 98.74, OUT_W / 2, OUT_H * 0.7, 140, (255, 214, 40))
        return f

    def p_final(self, t, d):
        m = self.sala_img.copy()
        m.alpha_composite(brilho((1080, 1080), (255, 230, 170), 540, 0.6), (0, 300))
        self.nena(m, t, 720, 1450, 0.9, expr="ri")
        self.caio(m, t, 330, 1800, 1.05, expr="ri", pose="acena")
        f = self.cam(m, 540, 1250, 1.1)
        texto_pop(f, "FAZ ESSA PESSOA RIR HOJE", self.fc, t, OUT_W / 2, OUT_H * 0.12, 50, (255, 214, 40))
        if t > d - 0.6:
            f = ImageEnhance.Brightness(f).enhance(max(0, 1 - (t - (d - 0.6)) / 0.6))
        return f

    # ---------- montagem ----------
    def frame(self, n):
        t = n / FPS
        self.T = t
        g.CAM_T = t
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if t < ini + d or i == len(self.planos) - 1:
                tl = t - ini
                f = self.gradear(fn(tl, d), clima)
                T_ = 0.2
                if i > 0 and tl < T_ and tr != "corte":
                    pi, pd, pfn, pcl, _ = self.planos[i - 1]
                    self.T = pi + pd - 0.001
                    prev = self.gradear(pfn(pd - 0.001, pd), pcl)
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
                f = g.vinheta(f, 0.3)
                self.legenda(f, t)
                return f

    @staticmethod
    def gradear(f, clima):
        if clima == "frio":
            return ve.tom_frio(f, 0.5)
        return vc.gradear(f, clima)

    def eventos_sfx(self):
        ev = []
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if i and tr in ("whip", "zoom"):
                ev.append(("whoosh", ini - 0.08))
            elif i and tr == "corte":
                ev.append(("pop", ini))
        return ev


def mixar(filme, narracao, saida):
    SR = g.SR
    voz = vc.ler_wav_mono(narracao)
    n = int(filme.dur_total * SR)
    mix = np.zeros(n, np.float32)
    mix[:min(n, len(voz))] += voz[:n]
    mus = g.trilha(filme.dur_total)
    mus = mus / max(1e-6, np.abs(mus).max()) * 0.12
    tt = np.arange(len(mus)) / SR
    env = np.ones_like(tt)
    env[(tt > 93.6) & (tt < 97.5)] = 0.3
    mix[:len(mus)] += (mus * env)[:n]
    ev = filme.eventos_sfx()
    ev += [("brilho", 40.10), ("brilho", 62.14), ("brilho", 94.80), ("toc", 36.62), ("toc", 46.9)]
    ev += [("pop", 52.84), ("pop", 53.62), ("pop", 55.02)]
    for tipo, t0 in ev:
        s = g.sfx(tipo) * (0.3 if tipo in ("whoosh", "pop") else 1.0)
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
    pal = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            pal.append(dict(w=w["w"], s=w["s"], e=w["e"]))
    out = []
    i = 0
    while i < len(pal):
        w = pal[i]
        if w["w"] == "é" and i + 2 < len(pal) and pal[i + 1]["w"] == "um" and pal[i + 2]["w"] == "pulheta":
            out.append(dict(w="Ampulheta", s=w["s"], e=pal[i + 2]["e"]))
            i += 3
            continue
        txt = {"vonena": "vó Nena", "nena": "Nena", "acham": "achavam", "15": "quinze", "11": "Onze"}.get(w["w"], w["w"])
        out.append(dict(w=txt, s=w["s"], e=w["e"]))
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_areia_da_vo.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    ap.add_argument("--de", type=float, default=None)
    ap.add_argument("--ate", type=float, default=None)
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeAreia(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.2, a.narracao)
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

    tmp = tempfile.mkdtemp(prefix="areia_")
    wav = os.path.join(tmp, "mix.wav")
    mixar(filme, a.narracao, wav)
    n0 = int((a.de or 0) * FPS)
    n1 = int(a.ate * FPS) if a.ate else total
    if a.de or a.ate:
        tr = os.path.join(tmp, "trecho.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.de or 0), "-t", str((n1 - n0) / FPS),
                        "-i", wav, tr], check=True)
        wav = tr
    print(f"• renderizando {total} frames ({filme.dur_total:.1f}s)…", flush=True)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}",
         "-r", str(FPS), "-i", "-", "-i", wav, "-vf", "scale=1080:1920:flags=lanczos",
         "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-maxrate", "6M", "-bufsize", "12M",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.saida],
        stdin=subprocess.PIPE)
    for n in range(n0, n1):
        proc.stdin.write(filme.frame(n).tobytes())
        if n % 150 == 0:
            print(f"  {n}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("✔ vídeo salvo em", a.saida)


if __name__ == "__main__":
    main()
