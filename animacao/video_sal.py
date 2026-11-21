#!/usr/bin/env python3
"""
"O Sal do Seu Honório" — num mundo todo de açúcar, o sal é dinheiro. Bento descobre, por um poço com escada,
um mundo cinza onde o sal é lixo e o açúcar é sonho… e o esquema do único homem rico da cidade.

Abre num mundo de açúcar rosado (cenário novo). Rig articulado + cortes a cada ~2 s.

    python3 animacao/video_sal.py --narracao narr.mp3 --transcricao transcricao.json --fonte Poppins.ttf
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
import video_estatua as ve  # noqa: E402
import video_areia as va  # noqa: E402
import video_abracos as vb  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(1919)

BENTO = dict(pele=(222, 170, 128), cabelo=(70, 45, 30), camisa=(100, 160, 225), calca=(110, 80, 70),
             sapato=(240, 240, 245), tipo="menino")
BENTO_POBRE = dict(BENTO, camisa=(150, 150, 160), calca=(90, 80, 75), sapato=(120, 100, 90))
BENTO_RICO = dict(BENTO, camisa=(250, 200, 70), calca=(70, 60, 110), sapato=(230, 90, 80))
HONORIO = dict(pele=(232, 186, 150), cabelo=(40, 30, 30), camisa=(110, 60, 150), calca=(60, 40, 90),
               sapato=(30, 30, 34), tipo="pai", chapeu=(50, 30, 80))
AVO = dict(pele=(214, 160, 120), cabelo=(228, 228, 232), camisa=(220, 110, 130), calca=(130, 70, 100),
           sapato=(120, 80, 80), tipo="vovo", vestido=(220, 110, 130))
FEIRA = dict(pele=(196, 140, 100), cabelo=(35, 28, 26), camisa=(255, 180, 40), calca=(70, 80, 110),
             sapato=(40, 40, 45), tipo="pai", bigode=False, chapeu=(255, 150, 30))
MENINO2 = dict(pele=(196, 140, 100), cabelo=(35, 28, 26), camisa=(120, 200, 140), calca=(110, 80, 70),
               sapato=(230, 230, 235), tipo="menino")
CINZAS = [dict(pele=(185, 185, 190), cabelo=(70, 70, 76), camisa=(120, 120, 130), calca=(80, 80, 92),
               sapato=(50, 50, 56), tipo=t, bigode=False) for t in ("pai", "menino", "pai", "menino")]
ACUC = [dict(ve.POVO[i % len(ve.POVO)], camisa=c) for i, c in enumerate(
    ((255, 170, 200), (255, 210, 140), (170, 220, 255), (200, 170, 255), (255, 190, 160)))]
vc.DESTAQUE_VERMELHO = set()
_C = {}
ROSA, CREME = (255, 200, 220), (255, 240, 235)


# --------------------------------------------------------------------------
# Ícones
# --------------------------------------------------------------------------
def icone(kind, w=300):
    k = (kind, w)
    if k in _C:
        return _C[k]
    p = Pincel(300, 300)
    if kind == "saco":
        p.poli([(70, 60), (230, 60), (250, 270), (50, 270)], (250, 250, 252), ow=7)
        p.ret((70, 40, 230, 80), (225, 225, 232), r=8)
        p.ret((100, 130, 200, 210), (80, 130, 200), r=10, ow=0)
    elif kind == "pitada":
        p.elipse((60, 190, 240, 270), (250, 250, 252), ow=6)
        for x, y in ((120, 150), (150, 120), (170, 160), (140, 170), (110, 190)):
            p.elipse((x - 8, y - 8, x + 8, y + 8), (255, 255, 255), ow=3)
    elif kind == "pirulito":
        p.ret((140, 150, 160, 290), (240, 240, 235), r=4)
        p.elipse((60, 20, 240, 200), (255, 120, 170), ow=8)
        p.arco((95, 55, 205, 165), 0, 270, fill=(255, 255, 255), w=14)
        p.arco((125, 85, 175, 135), 90, 360, fill=(255, 255, 255), w=12)
    elif kind == "colher":
        p.linha([(70, 270), (210, 90)], fill=(200, 205, 215), w=22)
        p.elipse((170, 30, 270, 140), (215, 220, 230), ow=7)
    elif kind == "panela":
        p.ret((50, 130, 250, 250), (150, 150, 160), r=18)
        p.ret((35, 110, 265, 140), (190, 190, 200), r=10)
        p.ret((250, 150, 295, 170), (110, 110, 120), r=6)
        p.elipse((60, 100, 240, 150), (240, 170, 80), ow=5)
    elif kind == "carrinho":
        p.poli([(30, 60), (270, 60), (240, 190), (70, 190)], (190, 195, 205), ow=7)
        for i in range(3):
            p.poli([(80 + i * 60, 20), (130 + i * 60, 20), (135 + i * 60, 62), (75 + i * 60, 62)],
                   (250, 250, 252), ow=5)
        p.elipse((70, 200, 120, 250), (50, 50, 60))
        p.elipse((200, 200, 250, 250), (50, 50, 60))
    elif kind == "casa":
        p.ret((50, 120, 250, 270), (235, 200, 160), r=6)
        p.poli([(30, 130), (150, 30), (270, 130)], (190, 90, 80))
        p.ret((125, 190, 175, 270), (120, 80, 55), r=6)
    elif kind == "cama":
        p.ret((20, 140, 280, 230), (255, 205, 225), r=20)
        p.ret((20, 100, 90, 230), (245, 185, 210), r=14)
        p.ret((30, 230, 55, 270), (210, 160, 180), r=4)
        p.ret((245, 230, 270, 270), (210, 160, 180), r=4)
    elif kind == "dente":
        p.poli([(60, 60), (240, 60), (230, 170), (200, 270), (165, 170), (135, 170), (100, 270), (70, 170)],
               (255, 255, 255), ow=8)
        p.elipse((140, 90, 190, 140), (70, 60, 60), ow=0)
    elif kind == "bolo":
        p.ret((40, 150, 260, 260), (255, 190, 210), r=16)
        p.ret((40, 110, 260, 170), (255, 235, 240), r=16)
        for x in (100, 150, 200):
            p.ret((x - 5, 60, x + 5, 115), (250, 245, 220), r=3, ow=4)
            p.elipse((x - 8, 40, x + 8, 66), (255, 170, 40), ow=0)
    elif kind == "porta":
        p.ret((80, 30, 220, 280), (255, 215, 230), r=10)
        p.elipse((190, 150, 206, 166), (255, 255, 255), ow=4)
    elif kind == "janela":
        p.ret((50, 50, 250, 250), (255, 230, 240), r=8)
        p.linha([(150, 50), (150, 250)], fill=OUTLINE, w=7)
        p.linha([(50, 150), (250, 150)], fill=OUTLINE, w=7)
    elif kind == "vaso":
        p.ret((80, 40, 220, 140), (255, 235, 245), r=12)
        p.elipse((60, 120, 240, 250), (255, 240, 248), ow=7)
        p.elipse((100, 150, 200, 200), (235, 215, 225), ow=4)
    elif kind == "pote":
        p.ret((70, 90, 230, 270), (255, 240, 245), r=26)
        p.ret((60, 60, 240, 100), (255, 170, 200), r=14)
        for x, y in ((120, 160), (170, 190), (150, 130)):
            p.elipse((x - 9, y - 9, x + 9, y + 9), (255, 255, 255), ow=3)
    elif kind == "montanha_sal":
        p.poli([(10, 280), (150, 40), (290, 280)], (250, 250, 252), ow=8)
        p.poli([(90, 280), (180, 110), (260, 280)], (232, 232, 240), ow=0)
    img = p.pronto()
    _C[k] = img if w == 300 else img.resize((w, w), Image.BICUBIC)
    return _C[k]


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def brilhos_acucar(base, seed=2, n=70):
    rng = random.Random(seed)
    d = ImageDraw.Draw(base)
    for _ in range(n):
        x, y = rng.randint(0, WW), rng.randint(0, WH)
        r = rng.choice((3, 4, 6))
        d.line((x - r * 2, y, x + r * 2, y), fill=(255, 255, 255, 230), width=2)
        d.line((x, y - r * 2, x, y + r * 2), fill=(255, 255, 255, 230), width=2)


def mundo_acucar():
    base = gradiente(WW, WH, (255, 190, 215), (255, 238, 232))
    p = Pincel(WW, WH)
    p.elipse((700, 140, 920, 360), (255, 245, 200), ow=0)
    for i, x in enumerate((-50, 260, 570, 880)):
        top = 760 + (i % 2) * 90
        cor = [(255, 210, 225), (255, 235, 200), (215, 235, 255), (235, 215, 255)][i]
        p.ret((x, top, x + 300, 1420), cor, r=14)
        p.poli([(x - 14, top + 6), (x + 150, top - 150), (x + 314, top + 6)], (255, 160, 190))
        p.ret((x + 40, top + 90, x + 120, top + 200), (255, 250, 245), r=8, ow=6)
        p.ret((x + 180, top + 200, x + 250, 1420), (255, 245, 245), r=8, ow=6)
    p.ret((-20, 1410, WW + 20, 1500), (255, 250, 250), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (250, 235, 242), r=0)
    for x in range(0, WW, 200):
        p.ret((x + 40, 1700, x + 150, 1722), (255, 190, 215), r=6, ow=0)
    base.alpha_composite(p.pronto())
    brilhos_acucar(base)
    return base


def salina(fc, noite=False):
    base = mundo_acucar() if not noite else gradiente(WW, WH, (50, 40, 90), (95, 70, 120))
    if noite:
        p0 = Pincel(WW, WH)
        p0.ret((-20, 1410, WW + 20, 1500), (190, 170, 200), r=0)
        p0.ret((-20, 1500, WW + 20, WH + 20), (160, 140, 175), r=0)
        base.alpha_composite(p0.pronto())
    p = Pincel(WW, WH)
    p.ret((200, 640, 880, 1420), (235, 235, 245), r=12)
    p.poli([(170, 650), (540, 470), (910, 650)], (100, 80, 150))
    p.ret((260, 1000, 820, 1200), (60, 40, 70), r=10, ow=10)                       # janelinha
    p.ret((240, 1200, 840, 1250), (140, 100, 70), r=6)
    p.ret((620, 1250, 760, 1420), (110, 70, 55), r=8)
    p.ret((300, 700, 780, 800), (60, 50, 100), r=10, ow=6)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 56)
    d.text((540 - f.getlength("SALINA") / 2, 722), "SALINA", font=f, fill=(255, 255, 255))
    if noite:
        base.alpha_composite(brilho((600, 400), (255, 220, 150), 220, 0.7), (240, 900))
    return base


def mundo_cinza(fc):
    base = gradiente(WW, WH, (110, 112, 125), (170, 172, 182))
    p = Pincel(WW, WH)
    rng = random.Random(6)
    for i in range(7):
        x = i * 170 - 40
        top = rng.randint(620, 960)
        p.ret((x, top, x + 160, 1400), rng.choice([(95, 98, 112), (105, 108, 122), (85, 88, 100)]), r=4, ow=0)
        for yy in range(top + 30, 1380, 80):
            p.ret((x + 40, yy, x + 80, yy + 44), (140, 144, 160), r=3, ow=0)
    p.ret((-20, 1400, WW + 20, 1500), (130, 132, 146), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (98, 100, 114), r=0)
    for x in range(0, WW, 220):
        p.ret((x + 40, 1710, x + 150, 1730), (160, 162, 175), r=6, ow=0)
    for x in (110, 900):
        p.ret((x - 8, 1000, x + 8, 1410), (70, 72, 84), r=4)
        p.elipse((x - 28, 960, x + 28, 1016), (230, 230, 235), ow=4)
    base.alpha_composite(p.pronto())
    return base


def mercado_sal(fc):
    base = gradiente(WW, WH, (245, 248, 250), (225, 230, 235))
    p = Pincel(WW, WH)
    for col in range(2):
        x0 = 20 + col * 570
        for k in range(5):
            y = 360 + k * 200
            p.ret((x0, y + 150, x0 + 490, y + 172), (170, 175, 185), r=4)
            for j in range(6):
                p.ret((x0 + 15 + j * 77, y + 40, x0 + 82 + j * 77, y + 150), (250, 250, 255), r=6, ow=5)
                p.ret((x0 + 28 + j * 77, y + 70, x0 + 70 + j * 77, y + 110), (80, 130, 200), r=4, ow=0)
    p.ret((-20, 110, WW + 20, 200), (60, 130, 200), r=0)
    p.ret((-20, 1480, WW + 20, WH + 20), (200, 205, 212), r=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 60)
    d.text((540 - f.getlength("CORREDOR DO SAL") / 2, 125), "CORREDOR DO SAL", font=f, fill=(255, 255, 255))
    return base


def poco_escada(fc):
    """Poço vertical: topo de açúcar rosado → pedra cinza lá embaixo, com escada."""
    base = gradiente(WW, WH, (255, 190, 215), (70, 72, 85))
    p = Pincel(WW, WH)
    for y in range(0, WH, 110):
        for x in range(-60 + (y // 110 % 2) * 80, WW, 160):
            alfa = y / WH
            cor = (int(255 - 150 * alfa), int(205 - 100 * alfa), int(225 - 120 * alfa))
            p.ret((x, y, x + 150, y + 100), cor, r=8, ow=4)
    p.ret((330, -20, 750, WH + 20), (28, 26, 36), r=0, ow=0)
    for x in (360, 690):
        p.ret((x - 10, -20, x + 10, WH + 20), (200, 160, 90), r=4)
    for y in range(40, WH, 90):
        p.ret((360, y, 700, y + 16), (210, 170, 100), r=4)
    base.alpha_composite(p.pronto())
    return base


def cozinha_noite():
    base = va.cozinha()
    base.alpha_composite(Image.new("RGBA", (WW, WH), (30, 20, 70, 110)))
    base.alpha_composite(brilho((900, 900), (255, 220, 150), 420, 0.45), (90, 700))
    return base


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeSal(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.bento, self.bpobre, self.brico = P_(BENTO), P_(BENTO_POBRE), P_(BENTO_RICO)
        self.hon, self.avo, self.feira, self.m2 = P_(HONORIO), P_(AVO), P_(FEIRA), P_(MENINO2)
        self.cinzas = [P_(c) for c in CINZAS]
        self.acuc = [P_(c) for c in ACUC]
        self.blur = {}
        self.mundo = mundo_acucar()
        self.sal_dia, self.sal_noite = salina(fc), salina(fc, True)
        self.cinza = mundo_cinza(fc)
        self.merc = mercado_sal(fc)
        self.poco = poco_escada(fc)
        self.coz = cozinha_noite()
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        P = [
            (0.00, self.p_hook, "", "corte"),
            (2.58, self.p_sal_dinheiro, "", "whip"),
            (4.22, self.p_pitada, "", "corte"),
            (7.70, self.p_bento_rico, "", "whip"),
            (11.62, self.p_ja_pobre, "", "corte"),
            (14.82, self.p_calcada, "", "whip"),
            (21.24, self.p_pobre_come, "", "corte"),
            (25.42, self.p_enjoa, "", "corte"),
            (27.24, self.p_um_homem, "", "whip"),
            (31.72, self.p_fabrica, "", "zoom"),
            (33.74, self.p_trabalham, "", "corte"),
            (36.84, self.p_tempera, "", "corte"),
            (39.34, self.p_ninguem, "frio", "dissolve"),
            (41.60, self.p_sopa, "frio", "dissolve"),
            (45.64, self.p_avo_pede, "frio", "corte"),
            (49.80, self.p_corri, "frio", "whip"),
            (51.16, self.p_empresta, "frio", "whip"),
            (52.86, self.p_paga_com, "frio", "corte"),
            (55.26, self.p_com_acucar, "frio", "corte"),
            (56.24, self.p_calcada_hon, "frio", "corte"),
            (59.10, self.p_fechou, "frio", "whip"),
            (61.00, self.p_esperei, "frio", "corte"),
            (64.10, self.p_lamber, "frio", "whip"),
            (68.66, self.p_dentro, "frio", "dissolve"),
            (74.30, self.p_de_onde, "frio", "zoom"),
            (78.36, self.p_desceu, "", "whip"),
            (82.12, self.p_tampa, "", "corte"),
            (85.42, self.p_cinza, "", "whip"),
            (87.76, self.p_nada_acucar, "", "corte"),
            (90.02, self.p_sal_lixo, "", "corte"),
            (95.34, self.p_homem_feira, "", "whip"),
            (100.16, self.p_paga_hora, "", "corte"),
            (101.32, self.p_ninguem_ligava, "", "corte"),
            (105.24, self.p_troquei, "", "whip"),
            (107.26, self.p_mercado, "", "whip"),
            (112.14, self.p_entao, "", "zoom"),
            (113.20, self.p_esquema, "", "dissolve"),
            (119.08, self.p_muito_sal, "", "corte"),
            (122.76, self.p_esquisito, "", "zoom"),
            (127.28, self.p_isso, "", "corte"),
            (128.86, self.p_carrinho, "", "whip"),
            (130.78, self.p_vo_espera, "quente", "whip"),
            (133.46, self.p_sabor, "quente", "corte"),
            (134.98, self.p_salva, "quente", "corte"),
            (136.04, self.p_colher, "", "whip"),
            (141.40, self.p_la_embaixo, "", "whip"),
            (144.04, self.p_vendia, "", "corte"),
            (147.36, self.p_bolo, "", "whip"),
            (152.66, self.p_rico, "", "dissolve"),
            (156.58, self.p_bateu, "", "whip"),
            (159.34, self.p_pede, "", "corte"),
            (162.56, self.p_paga_com2, "", "corte"),
            (164.16, self.p_com_acucar2, "", "corte"),
            (165.82, self.p_eu_ri, "", "corte"),
            (169.12, self.p_se_aceito, "", "zoom"),
            (173.00, self.p_entendi, "", "dissolve"),
            (174.96, self.p_janela, "", "corte"),
            (178.10, self.p_chover, "frio", "corte"),
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

    def txt(self, f, s, t0, y=0.1, tam=64, cor=(255, 214, 40)):
        if self.T >= t0:
            texto_pop(f, s, self.fc, self.T - t0, OUT_W / 2, OUT_H * y, tam, cor)

    def ic(self, m, kind, x, y, w):
        im = icone(kind, int(w))
        m.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))

    def chuva_f(self, f, t, n=130, seed=5):
        d = ImageDraw.Draw(f, "RGBA")
        rng = random.Random(seed)
        for _ in range(n):
            x = rng.uniform(0, OUT_W)
            y = (rng.uniform(0, OUT_H) + t * rng.uniform(900, 1400)) % OUT_H
            d.line((x, y, x - 5, y + 30), fill=(190, 210, 255, 200), width=3)

    def cena(self, bg, t, fn, cx=540, cy=1250, z=1.12):
        m = bg.copy()
        fn(m)
        return self.cam(m, cx, cy, z)

    def fundo_noite(self, c1=(60, 50, 100), c2=(30, 26, 56)):
        return gradiente(WW, WH, c1, c2)

    def close_bg(self, pers, t, bg, nome, expr, z=1.05, **kw):
        return self.close(pers, t, bg, nome, expr=expr, z=z, **kw)

    # ---------- planos ----------
    def p_hook(self, t, d):
        m = self.mundo.copy()
        self.bento(m, t, 540, 1780, 1.2, expr="surpreso", pose="bracos_abertos")
        for i, (p, x) in enumerate(zip(self.acuc[:2], (200, 900))):
            p(m, t + i, x, 1780, 0.9, expr="feliz", pose="anda")
        f = self.cam(m, 540, 1200, 1.12 - 0.05 * ease_io(t / d))
        self.txt(f, "TUDO É DE AÇÚCAR", 0.2, 0.08, 62)
        return f

    def p_sal_dinheiro(self, t, d):
        m = gradiente(WW, WH, (255, 190, 215), (255, 238, 232))
        self.ic(m, "pitada", 540, 1000, 700)
        f = self.cam(m, 540, 1000, 1.0 + 0.1 * ease_io(t / d))
        particulas(f, t, 30, cor=(255, 255, 255), semente=3)
        self.txt(f, "SAL = DINHEIRO", 2.7, 0.12, 64, (255, 255, 255))
        return f

    def p_pitada(self, t, d):
        m = gradiente(WW, WH, (255, 190, 215), (255, 238, 232))
        T = self.T
        self.ic(m, "pitada", 280, 900, 420)
        if T > 5.7:
            self.ic(m, "saco", 300, 1380, 480)
            self.ic(m, "casa", 780, 1380, 480)
        f = self.cam(m, 540, 1150, 1.05)
        self.txt(f, "UMA PITADA = 100", 4.5, 0.1, 56)
        self.txt(f, "UM SACO = UMA CASA", 6.4, 0.2, 52, (255, 255, 255))
        return f

    def p_bento_rico(self, t, d):
        m = self.mundo.copy()
        self.brico(m, t, 540, 1800, 1.4, expr="feliz", pose="bracos_abertos")
        for x in (180, 900):
            self.ic(m, "saco", x, 1700, 340)
        f = self.cam(m, 540, 1250, 1.1)
        self.txt(f, "BENTO", 8.0, 0.1, 80)
        self.txt(f, "O MENINO MAIS RICO", 9.6, 0.2, 48, (255, 255, 255))
        return f

    def p_ja_pobre(self, t, d):
        m = self.mundo.copy()
        self.bpobre(m, t, 540, 1800, 1.4, expr="triste", pose="idle")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "JÁ FUI POBRE", 11.8, 0.1, 68, (255, 255, 255))
        return f

    def p_calcada(self, t, d):
        m = gradiente(WW, WH, (255, 190, 215), (255, 238, 232))
        T = self.T
        for i, (k, ts, lab) in enumerate((("casa", 15.9, "CALÇADA"), ("porta", 18.2, "MURO"), ("cama", 19.9, "CAMA"))):
            if T > ts:
                s = ease_out(min(1, (T - ts) / 0.3))
                self.ic(m, k, 200 + i * 340, 1100 + 120 * (i % 2), 330 * s + 1)
        f = self.cam(m, 540, 1150, 1.0)
        self.txt(f, "AÇÚCAR AÇÚCAR AÇÚCAR", 14.82, 0.1, 48)
        return f

    def p_pobre_come(self, t, d):
        m = self.mundo.copy()
        self.bpobre(m, t, 540, 1800, 1.35, expr="neutro", pose="entrega")
        hx, hy = self.bpobre.a.maos_mundo[1]
        self.ic(m, "pote", hx, hy - 80, 220)
        f = self.cam(m, 540, 1250, 1.12)
        T = self.T
        for lab, ts, y in (("CAFÉ", 22.3, 0.1), ("ALMOÇO", 23.24, 0.17), ("JANTA", 24.46, 0.24)):
            self.txt(f, lab + " DE AÇÚCAR", ts, y, 46, (255, 255, 255))
        return f

    def p_enjoa(self, t, d):
        m = self.mundo.copy()
        self.bpobre(m, t, 450, 1800, 1.35, expr="chora", pose="bolso")
        self.ic(m, "dente", 800, 1500, 360 + 20 * math.sin(t * 5))
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "ENJOA E DÁ CÁRIE", 25.4, 0.1, 50, (255, 255, 255))
        return f

    def p_um_homem(self, t, d):
        m = self.sal_dia.copy()
        self.hon(m, t, 540, 1800, 1.4, expr="feliz", pose="bracos_abertos")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "SEU HONÓRIO", 29.14, 0.1, 74)
        return f

    def p_fabrica(self, t, d):
        m = self.sal_dia.copy()
        f = self.cam(m, 540, 1000, 1.0 + 0.15 * ease_io(t / d))
        self.txt(f, "FABRICA DINHEIRO", 32.4, 0.1, 56)
        return f

    def p_trabalham(self, t, d):
        m = self.sal_dia.copy()
        for i, p in enumerate(self.acuc[:4]):
            x = 160 + i * 250 + 40 * math.sin(t * 2 + i)
            p(m, t + i, x, 1800, 0.95, expr="neutro", pose="anda")
            self.ic(m, "saco", x + 30, 1500, 160)
        return self.cam(m, 540, 1250, 1.12)

    def p_tempera(self, t, d):
        m = self.fundo_noite((120, 70, 150), (60, 40, 90))
        self.hon(m, t, 540, 1800, 1.4, expr="ri", pose="aponta")
        for i in range(8):
            x = 700 + 60 * math.sin(t * 6 + i)
            y = 700 + ((t * 300 + i * 90) % 500)
            m.alpha_composite(brilho((20, 20), (255, 255, 255), 9, 1), (int(x + i * 10), int(y)))
        f = self.cam(m, 540, 1200, 1.1)
        self.txt(f, "SÓ PORQUE PODE", 38.4, 0.12, 60, (255, 255, 255))
        return f

    def p_ninguem(self, t, d):
        m = self.sal_noite.copy()
        p = Pincel(WW, WH)
        p.ret((580, 1230, 800, 1330), (230, 80, 80), r=10, ow=6)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 1100, 1.1 + 0.15 * ease_io(t / d))
        self.txt(f, "NINGUÉM ENTROU", 39.58, 0.1, 62, (255, 255, 255))
        return f

    def p_sopa(self, t, d):
        m = self.coz.copy()
        self.avo(m, t, 540, 1780, 1.3, expr="neutro", pose="idle")
        self.ic(m, "panela", 800, 1480, 420)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "SOPA SEM SAL", 43.9, 0.1, 64, (255, 255, 255))
        return f

    def p_avo_pede(self, t, d):
        m = self.coz.copy()
        self.avo(m, t, 640, 1780, 1.3, expr="bravo", pose="aponta")
        self.bento(m, t, 260, 1800, 1.1, expr="surpreso")
        f = self.cam(m, 540, 1250, 1.12)
        self.balao_t(f, "Açúcar de novo não!", OUT_W * 0.58, OUT_H * 0.16, 46.3)
        return f

    def p_corri(self, t, d):
        m = self.sal_noite.copy()
        x = -100 + 800 * ease_io(t / d)
        self.bento(m, t, x, 1800, 1.2, expr="neutro", pose="corre")
        return self.cam(m, 540 + 40 * math.sin(t * 8), 1250, 1.12)

    def janela_cena(self, t, bento_expr, hon_expr, bento_pose="idle", hon_pose="idle", fechada=0.0):
        m = self.sal_noite.copy()
        self.hon(m, t, 540, 1450, 1.15, expr=hon_expr, pose=hon_pose)
        p = Pincel(WW, WH)
        p.ret((240, 1200, 840, 1250), (140, 100, 70), r=6)
        p.ret((200, 640, 880, 1010), (235, 235, 245), r=0, ow=0)
        p.ret((200, 1250, 880, 1420), (235, 235, 245), r=0, ow=0)
        m.alpha_composite(p.pronto())
        if fechada > 0:
            q = Pincel(WW, WH)
            q.ret((260, 1000, 820, 1000 + int(200 * fechada)), (150, 110, 80), r=6, ow=6)
            m.alpha_composite(q.pronto())
        self.bento(m, t, 300, 1850, 1.2, expr=bento_expr, pose=bento_pose)
        return m

    def p_empresta(self, t, d):
        m = self.janela_cena(t, "neutro", "neutro", bento_pose="entrega")
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Me empresta uma pitada?", OUT_W * 0.5, OUT_H * 0.14, 52.0)
        return f

    def p_paga_com(self, t, d):
        m = self.janela_cena(t, "triste", "bravo", hon_pose="aponta")
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Me paga com o quê?", OUT_W * 0.55, OUT_H * 0.14, 53.8)
        return f

    def p_com_acucar(self, t, d):
        m = self.janela_cena(t, "feliz", "surpreso", bento_pose="entrega")
        hx, hy = self.bento.a.maos_mundo[1]
        self.ic(m, "pote", hx, hy - 60, 200)
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Com açúcar.", OUT_W * 0.3, OUT_H * 0.16, 55.26)
        return f

    def p_calcada_hon(self, t, d):
        m = self.janela_cena(t, "triste", "ri", hon_pose="bracos_abertos")
        f = self.cam(m, 540, 1250, 1.18)
        self.balao_t(f, "Açúcar é pra calçada!", OUT_W * 0.5, OUT_H * 0.14, 56.94)
        return f

    def p_fechou(self, t, d):
        k = ease_out(min(1, t / 0.4))
        m = self.janela_cena(t, "surpreso", "bravo", fechada=k)
        f = self.cam(m, 540, 1250, 1.15)
        self.txt(f, "BAM!", 59.1, 0.12, 120, (255, 120, 100))
        return f

    def p_esperei(self, t, d):
        m = self.sal_noite.copy()
        self.hon(m, t, 120 + 900 * ease_in_(min(1, t / d)), 1800, 1.2, expr="neutro", pose="anda", sx=-1)
        self.bento(m, t, 760, 1830, 1.1, expr="neutro", pose="idle")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "FIZ UMA COISA FEIA", 62.62, 0.12, 54, (255, 120, 120))
        return f

    def p_lamber(self, t, d):
        m = self.sal_noite.copy()
        self.bento(m, t, 360, 1830, 1.3, expr="ri", pose="idle", rot=4 * math.sin(t * 8))
        k = ease_out(min(1, max(0, (self.T - 66.58) / 1.4)))
        q = Pincel(WW, WH)
        q.elipse((560 - 90 * k, 1300 - 120 * k, 560 + 90 * k, 1300 + 120 * k), (20, 14, 30), ow=6)
        m.alpha_composite(q.pronto())
        f = self.cam(m, 540, 1250, 1.15)
        self.txt(f, "LAMBER O MURO", 66.66, 0.12, 60, (255, 255, 255))
        return f

    def p_dentro(self, t, d):
        m = self.fundo_noite((60, 55, 80), (30, 28, 44))
        p = Pincel(WW, WH)
        p.elipse((300, 1500, 780, 1620), (14, 12, 20), ow=0)
        p.ret((330, 1400, 750, 1560), (28, 26, 36), r=0, ow=0)
        m.alpha_composite(p.pronto())
        for i, x in enumerate((140, 900, 220)):
            self.ic(m, "saco", x, 1640 + 30 * (i % 2), 240)
        self.bento(m, t, 540, 1500, 1.1, expr="surpreso")
        f = self.cam(m, 540, 1200, 1.12)
        self.txt(f, "NENHUMA SALINA", 69.56, 0.12, 60, (255, 255, 255))
        return f

    def p_de_onde(self, t, d):
        m = self.poco.copy()
        f = self.cam(m, 540, 200 + 400 * ease_io(t / d), 1.3)
        self.txt(f, "DE ONDE VEM O SAL?", 76.24, 0.12, 56, (255, 214, 40))
        return f

    def p_desceu(self, t, d):
        m = self.poco.copy()
        k = ease_io(t / d)
        by = 500 + 1000 * k
        self.bento(m, t, 540, by, 0.9, expr="surpreso", pose="idle")
        f = self.cam(m, 540, by - 100, 1.5)
        self.txt(f, "A PRIMEIRA PEDRA DA MINHA VIDA", 80.38, 0.12, 36, (255, 255, 255))
        return f

    def p_tampa(self, t, d):
        m = self.fundo_noite((30, 30, 44), (60, 62, 80))
        p = Pincel(WW, WH)
        p.ret((300, 1300, 780, 1360), (110, 112, 125), r=6)
        m.alpha_composite(p.pronto())
        T = self.T
        k = ease_out(min(1, max(0, (T - 84.5) / 0.6)))
        q = Pincel(WW, WH)
        q.elipse((340, 520 + 300 * k, 740, 620 + 300 * k), (140, 144, 158), ow=8)
        m.alpha_composite(q.pronto())
        self.bento(m, t, 540, 1300, 1.0, expr="surpreso", pose="aponta")
        if T > 84.5:
            m.alpha_composite(brilho((900, 900), (255, 255, 255), 420, 0.3 + 0.5 * k), (90, 200))
        return self.cam(m, 540, 1000, 1.15)

    def p_cinza(self, t, d):
        m = self.cinza.copy()
        self.bento(m, t, 540, 1800, 1.3, expr="surpreso", pose="bracos_abertos")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "UM MUNDO CINZA", 86.58, 0.1, 64, (255, 255, 255))
        return f

    def p_nada_acucar(self, t, d):
        m = self.cinza.copy()
        self.bento(m, t, 540, 1800, 1.2, expr="surpreso", pose="idle")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "TUDO DE PEDRA", 87.76, 0.1, 62, (255, 255, 255))
        self.txt(f, "NADA DE AÇÚCAR", 88.8, 0.18, 50, (255, 160, 190))
        return f

    def p_sal_lixo(self, t, d):
        m = self.cinza.copy()
        for x, y, w in ((200, 1760, 260), (620, 1800, 220), (900, 1700, 200), (400, 1500, 160), (80, 1500, 180)):
            self.ic(m, "saco", x, y, w)
        p = Pincel(WW, WH)
        p.ret((800, 1400, 920, 1560), (70, 72, 84), r=10)
        m.alpha_composite(p.pronto())
        self.ic(m, "saco", 860, 1380, 140)
        self.bento(m, t, 480, 1830, 1.1, expr="surpreso", pose="aponta")
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "SAL NO LIXO", 90.56, 0.1, 62, (255, 255, 255))
        self.txt(f, "DINHEIRO FORA!", 93.72, 0.18, 54, (255, 214, 40))
        return f

    def p_homem_feira(self, t, d):
        m = self.cinza.copy()
        self.feira(m, t, 760, 1800, 1.3, expr="surpreso", pose="aponta")
        self.bento(m, t, 280, 1830, 1.0, expr="surpreso")
        hx, hy = self.bento.a.maos_mundo[1]
        self.ic(m, "pirulito", 300, 1450, 220)
        f = self.cam(m, 540, 1250, 1.12)
        self.balao_t(f, "Esse pirulito é de açúcar?", OUT_W * 0.55, OUT_H * 0.14, 97.88)
        return f

    def p_paga_hora(self, t, d):
        m = self.cinza.copy()
        self.feira(m, t, 760, 1800, 1.3, expr="feliz", pose="entrega")
        self.bento(m, t, 280, 1830, 1.0, expr="feliz", pose="entrega")
        f = self.cam(m, 540, 1250, 1.12)
        self.balao_t(f, "Pago na hora!", OUT_W * 0.6, OUT_H * 0.16, 100.28)
        return f

    def p_ninguem_ligava(self, t, d):
        m = self.cinza.copy()
        for i, p in enumerate(self.cinzas):
            x = 150 + i * 260
            p(m, t + i, x, 1800, 1.0, expr="neutro", pose="anda")
            self.ic(m, "saco", x + 30, 1700 + 40 * abs(math.sin(t * 2 + i)), 100)
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "NINGUÉM LIGAVA PRA SAL", 102.16, 0.1, 44, (255, 255, 255))
        self.txt(f, "TODO MUNDO QUERIA AÇÚCAR", 103.8, 0.18, 40, (255, 160, 190))
        return f

    def p_troquei(self, t, d):
        m = self.cinza.copy()
        self.feira(m, t, 780, 1800, 1.2, expr="feliz", pose="entrega")
        self.bento(m, t, 300, 1830, 1.1, expr="feliz", pose="entrega")
        self.ic(m, "saco", 540, 1550, 260)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "TROCA!", 105.7, 0.12, 100, (255, 214, 40))
        return f

    def p_mercado(self, t, d):
        m = self.merc.copy()
        self.bento(m, t, 540, 1850, 1.2, expr="surpreso", pose="bracos_abertos")
        f = self.cam(m, 540, 1200, 1.1)
        self.txt(f, "12 KG POR R$ 19,90", 109.62, 0.1, 54, (255, 214, 40))
        return f

    def p_entao(self, t, d):
        f = self.close(self.bento, t, self.merc, "merc", expr="surpreso", z=1.05)
        self.txt(f, "ENTÃO ERA ISSO", 112.14, 0.1, 64, (255, 255, 255))
        return f

    def p_esquema(self, t, d):
        m = self.fundo_noite((40, 36, 70), (22, 20, 40))
        T = self.T
        itens = (("pote", 113.88, 200, "AÇÚCAR"), ("saco", 115.56, 540, "SAL"), ("casa", 116.64, 880, "UM POUQUINHO"))
        for k, ts, x, lab in itens:
            if T > ts:
                s = ease_out(min(1, (T - ts) / 0.3))
                self.ic(m, k, x, 1000, 300 * s + 1)
        d_ = ImageDraw.Draw(m)
        for ts, x in ((114.6, 370), (116.2, 710)):
            if T > ts:
                d_.polygon([(x - 40, 990), (x + 40, 990), (x + 40, 960), (x + 100, 1010), (x + 40, 1060), (x + 40, 1030),
                            (x - 40, 1030)], fill=(255, 214, 40, 255))
        f = self.cam(m, 540, 1000, 1.0)
        self.txt(f, "VENDE AÇÚCAR", 113.88, 0.12, 54)
        self.txt(f, "COMPRA SAL", 115.56, 0.2, 54, (255, 255, 255))
        self.txt(f, "DE PROPÓSITO", 118.2, 0.28, 54, (255, 160, 160))
        return f

    def p_muito_sal(self, t, d):
        m = self.fundo_noite((50, 44, 80), (26, 22, 44))
        T = self.T
        k = ease_out(min(1, max(0, (T - 119.94) / 1.2)))
        self.ic(m, "montanha_sal", 540, 1150, 360 + 700 * k)
        f = self.cam(m, 540, 1050, 1.0)
        self.txt(f, "MUITO SAL", 119.46, 0.12, 64)
        self.txt(f, "VALE NADA", 121.52, 0.2, 80, (255, 120, 100))
        return f

    def p_esquisito(self, t, d):
        m = self.cinza.copy()
        self.bento(m, t, 540, 1830, 1.4, expr="neutro", pose="aponta")
        f = self.cam(m, 540, 1250, 1.12 + 0.08 * ease_io(t / d))
        self.txt(f, "SAL É LIXO", 124.16, 0.1, 64, (255, 255, 255))
        self.txt(f, "AÇÚCAR É SONHO", 125.26, 0.18, 54, (255, 160, 190))
        return f

    def p_isso(self, t, d):
        f = self.close(self.bento, t, self.cinza, "cinza", expr="feliz", z=1.15)
        self.txt(f, "VOCÊ AÍ", 128.1, 0.12, 100, (255, 214, 40))
        return f

    def p_carrinho(self, t, d):
        m = self.mundo.copy()
        x = -150 + 800 * ease_out(min(1, t / d))
        self.bento(m, t, x, 1800, 1.3, expr="feliz", pose="anda")
        self.ic(m, "carrinho", x + 220, 1700, 420)
        for k in range(3):
            self.ic(m, "saco", x + 160 + k * 70, 1540, 120)
        return self.cam(m, 540, 1300, 1.12)

    def p_vo_espera(self, t, d):
        m = self.coz.copy()
        self.avo(m, t, 540, 1780, 1.3, expr="triste", pose="idle")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "3 HORAS", 131.98, 0.1, 90)
        return f

    def p_sabor(self, t, d):
        m = self.coz.copy()
        self.avo(m, t, 540, 1780, 1.35, expr="ri", pose="entrega")
        self.ic(m, "panela", 800, 1480, 420)
        f = self.cam(m, 540, 1250, 1.12)
        self.balao_t(f, "Ai, que sabor!", OUT_W * 0.5, OUT_H * 0.16, 134.08)
        return f

    def p_salva(self, t, d):
        m = self.coz.copy()
        self.avo(m, t, 420, 1780, 1.3, expr="chora", pose="abraca_d")
        self.bento(m, t, 660, 1800, 1.15, expr="ri", pose="abraca_e")
        f = self.cam(m, 540, 1250, 1.12)
        vb.coracoes(m, t, 540, 1000, 5) if False else None
        self.txt(f, "A VÓ FOI SALVA", 135.3, 0.12, 62)
        return f

    def p_colher(self, t, d):
        m = self.mundo.copy()
        self.brico(m, t, 380, 1800, 1.3, expr="ri", pose="entrega")
        hx, hy = self.brico.a.maos_mundo[1]
        self.ic(m, "colher", hx + 20, hy - 60 + 25 * math.sin(t * 8), 240)
        q = Pincel(WW, WH)
        q.elipse((560, 1760, 900, 1840), (14, 12, 20), ow=0)
        m.alpha_composite(q.pronto())
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "BURACO COM COLHER", 140.42, 0.1, 52, (255, 255, 255))
        return f

    def p_la_embaixo(self, t, d):
        m = self.cinza.copy()
        for i, p in enumerate(self.cinzas):
            p(m, t + i, 140 + i * 260, 1800, 1.0, expr="feliz", pose="bracos_abertos")
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "TODO MUNDO QUERIA", 141.5, 0.1, 50, (255, 255, 255))
        self.txt(f, "O MEU AÇÚCAR", 143.0, 0.18, 62, (255, 160, 190))
        return f

    def p_vendia(self, t, d):
        m = self.cinza.copy()
        self.brico(m, t, 300, 1830, 1.15, expr="ri", pose="bracos_abertos")
        T = self.T
        for k, ts, x in (("porta", 144.66, 560), ("janela", 145.3, 760), ("vaso", 146.6, 940)):
            if T > ts:
                s = ease_out(min(1, (T - ts) / 0.3))
                self.ic(m, k, x, 1650, 260 * s + 1)
        f = self.cam(m, 540, 1300, 1.12)
        return f

    def p_bolo(self, t, d):
        m = self.fundo_noite((255, 190, 215), (255, 238, 232))
        self.ic(m, "bolo", 540, 1050, 640)
        f = self.cam(m, 540, 1050, 1.0 + 0.12 * ease_io(t / d))
        particulas(f, t, 30, cor=(255, 255, 255), semente=5)
        self.txt(f, "DE ONDE VEIO O AÇÚCAR?", 150.52, 0.1, 44, (255, 255, 255))
        return f

    def p_rico(self, t, d):
        m = self.sal_dia.copy()
        self.brico(m, t, 540, 1800, 1.4, expr="feliz", pose="bracos_abertos")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "A MINHA SALINA", 155.04, 0.1, 62)
        return f

    def p_bateu(self, t, d):
        m = self.janela_cena(t, "neutro", "neutro")
        m = self.sal_noite.copy()
        self.brico(m, t, 540, 1450, 1.15, expr="surpreso")
        p = Pincel(WW, WH)
        p.ret((240, 1200, 840, 1250), (140, 100, 70), r=6)
        m.alpha_composite(p.pronto())
        self.m2(m, t, 300, 1850, 1.2, expr="neutro", pose="bate")
        f = self.cam(m, 540, 1250, 1.15)
        self.txt(f, "TOC TOC", 157.58, 0.12, 90, (255, 255, 255))
        return f

    def p_pede(self, t, d):
        m = self.sal_noite.copy()
        self.brico(m, t, 540, 1450, 1.15, expr="neutro")
        self.m2(m, t, 300, 1850, 1.2, expr="triste", pose="entrega")
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Me empresta uma pitada?", OUT_W * 0.5, OUT_H * 0.14, 159.88)
        self.balao_t(f, "Minha vó fez sopa.", OUT_W * 0.45, OUT_H * 0.22, 161.5)
        return f

    def p_paga_com2(self, t, d):
        m = self.sal_noite.copy()
        self.brico(m, t, 540, 1450, 1.15, expr="bravo", pose="aponta")
        self.m2(m, t, 300, 1850, 1.2, expr="neutro")
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Me paga com o quê?", OUT_W * 0.55, OUT_H * 0.14, 162.84)
        return f

    def p_com_acucar2(self, t, d):
        m = self.sal_noite.copy()
        self.brico(m, t, 540, 1450, 1.15, expr="surpreso")
        self.m2(m, t, 300, 1850, 1.2, expr="feliz", pose="entrega")
        hx, hy = self.m2.a.maos_mundo[1]
        self.ic(m, "pote", hx, hy - 60, 200)
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Com açúcar?", OUT_W * 0.3, OUT_H * 0.16, 164.3)
        return f

    def p_eu_ri(self, t, d):
        m = self.sal_noite.copy()
        self.brico(m, t, 540, 1450, 1.15, expr="ri", pose="bracos_abertos")
        self.m2(m, t, 300, 1850, 1.2, expr="surpreso")
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Açúcar é pra calçada!", OUT_W * 0.5, OUT_H * 0.14, 166.9)
        return f

    def p_se_aceito(self, t, d):
        m = self.fundo_noite((60, 50, 100), (30, 26, 56))
        self.brico(m, t, 540, 2200, 2.3, expr="neutro")
        f = self.cam(m, 540, 950, 1.05)
        self.txt(f, "SE EU ACEITO AÇÚCAR…", 169.12, 0.1, 48, (255, 255, 255))
        self.txt(f, "ELE DESCOBRE QUE VALE", 171.14, 0.18, 44, (255, 214, 40))
        return f

    def p_entendi(self, t, d):
        m = self.fundo_noite((60, 50, 100), (30, 26, 56))
        self.brico(m, t, 380, 1800, 1.3, expr="surpreso")
        self.hon(m, t, 800, 1800, 1.0, expr="ri", alpha=0.45)
        f = self.cam(m, 540, 1250, 1.1)
        self.txt(f, "AGORA EU ENTENDI", 173.0, 0.1, 54, (255, 255, 255))
        self.txt(f, "O SEU HONÓRIO", 174.0, 0.18, 62, (255, 214, 40))
        return f

    def p_janela(self, t, d):
        m = gradiente(WW, WH, (255, 190, 215), (255, 238, 232))
        self.ic(m, "janela", 540, 1000, 700)
        f = self.cam(m, 540, 1000, 1.0 + 0.1 * ease_io(t / d))
        self.txt(f, "A MINHA JANELA TAMBÉM", 175.96, 0.1, 44, (255, 255, 255))
        self.txt(f, "É DE AÇÚCAR", 177.0, 0.18, 62, (255, 160, 190))
        return f

    def p_chover(self, t, d):
        m = gradiente(WW, WH, (70, 80, 120), (110, 120, 150))
        k = min(1, t / d)
        sc = 1 - 0.55 * k
        im = icone("janela", int(700 * sc))
        m.alpha_composite(im, (540 - im.width // 2, int(1000 + 220 * k - im.height / 2)))
        p = Pincel(WW, WH)
        p.ret((200, 1400, 880, 1480), (255, 215, 230), r=40, ow=0)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 1050, 1.0)
        self.chuva_f(f, t, 160)
        self.txt(f, "E COMEÇOU A CHOVER", 178.16, 0.12, 54, (190, 215, 255))
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
    rng = np.random.default_rng(3)
    chuva = np.convolve(rng.standard_normal(n).astype(np.float32), np.ones(40, np.float32) / 40, mode="same") * 0.05
    chuva[: int(178.0 * SR)] = 0
    mix += chuva
    ev = filme.eventos_sfx()
    ev += [("brilho", 0.2), ("pop", 2.72), ("toc", 59.1), ("brilho", 85.42), ("pop", 105.7), ("brilho", 112.14),
           ("brilho", 128.1), ("brilho", 134.08), ("toc", 157.58), ("brilho", 173.0), ("brilho", 178.16)]
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
    troca = {"onório": "Honório", "onório,": "Honório,", "onório.": "Honório.", "Injoa": "Enjoa", "Em": "Enjoa",
             "joa,": "", "cari,": "cárie,", "da": "da", "arranjo": "arranja", "notado": "lotado", "abriu": "abri"}
    out = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            out.append(dict(w=w["w"], s=w["s"], e=w["e"]))
    res, i = [], 0
    while i < len(out):
        w = out[i]
        if w["w"] == "Em" and i + 1 < len(out) and out[i + 1]["w"] == "joa,":
            res.append(dict(w="Enjoa,", s=w["s"], e=out[i + 1]["e"]))
            i += 2
            continue
        if w["w"] == "R" and i + 2 < len(out):
            res.append(dict(w="R$19,90.", s=w["s"], e=out[i + 2]["e"]))
            i += 3
            continue
        t = w["w"]
        t = {"onório": "Honório", "onório,": "Honório,", "onório.": "Honório.", "cari,": "cárie,",
             "arranjo": "arranja", "notado": "lotado"}.get(t, t)
        if t == "abri" or t == "abriu":
            pass
        res.append(dict(w=t, s=w["s"], e=w["e"]))
        i += 1
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_sal_do_seu_honorio.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeSal(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.4, a.narracao)
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

    tmp = tempfile.mkdtemp(prefix="sal_")
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
