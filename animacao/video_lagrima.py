#!/usr/bin/env python3
"""
"A Lágrima Vermelha" — numa cidade em que as lágrimas têm cor (azul = saudade, vermelha = culpa, preta = ódio),
o narrador chora vermelho no velório do irmão. Por quê?

Velório de óculos escuros, mão vermelha, família se afastando, perícia, abraço da mãe e a confissão final.
Rig articulado + cortes a cada ~2 s.

    python3 animacao/video_lagrima.py --narracao narr.mp3 --transcricao transcricao.json --fonte Poppins.ttf
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
import video_azar as vz  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(2323)

PRETO = (32, 32, 40)
NARR = dict(pele=(222, 170, 128), cabelo=(70, 48, 36), camisa=PRETO, calca=PRETO, sapato=(20, 20, 24),
            tipo="pai", bigode=False)
NARR_C = dict(NARR, camisa=(110, 150, 110), calca=(80, 80, 100))
RAFAEL = dict(pele=(226, 176, 134), cabelo=(60, 44, 34), camisa=(150, 190, 235), calca=(70, 80, 110),
              sapato=(60, 50, 50), tipo="pai", bigode=False)
RAFAEL_F = dict(RAFAEL, camisa=(30, 30, 40), calca=(30, 30, 40))
MAE = dict(pele=(222, 170, 128), cabelo=(130, 110, 100), camisa=(30, 30, 40), calca=(0, 0, 0),
           sapato=(20, 20, 24), tipo="moca", vestido=PRETO)
MAE_C = dict(MAE, camisa=(215, 140, 170), vestido=(215, 140, 170))
PAI = dict(pele=(214, 160, 120), cabelo=(190, 190, 195), camisa=PRETO, calca=PRETO, sapato=(20, 20, 24), tipo="pai")
PAI_C = dict(PAI, camisa=(150, 60, 60), calca=(80, 80, 90))
TIO = dict(pele=(196, 140, 100), cabelo=(60, 50, 50), camisa=PRETO, calca=PRETO, sapato=(20, 20, 24), tipo="pai")
TIA = dict(pele=(235, 190, 150), cabelo=(150, 70, 50), camisa=PRETO, calca=(0, 0, 0), sapato=(20, 20, 24),
           tipo="moca", vestido=PRETO)
VIUVA = dict(pele=(214, 160, 120), cabelo=(225, 225, 232), camisa=PRETO, calca=(0, 0, 0), sapato=(20, 20, 24),
             tipo="vovo", vestido=PRETO)
PRIMA = dict(pele=(222, 170, 128), cabelo=(60, 40, 30), camisa=PRETO, calca=(0, 0, 0), sapato=(20, 20, 24),
             tipo="moca", vestido=PRETO)
PERITO = dict(pele=(196, 140, 100), cabelo=(40, 36, 36), camisa=(40, 70, 130), calca=(40, 60, 100),
              sapato=(30, 30, 34), tipo="pai", chapeu=(30, 50, 100))
POVO_PRETO = [dict(ve.POVO[i], camisa=PRETO, calca=PRETO, vestido=PRETO) for i in range(5)]
POVO_COR = [dict(ve.POVO[i]) for i in range(5)]
AZUL, VERMELHO, ROXO = (90, 170, 255), (235, 50, 60), (30, 28, 34)
vc.DESTAQUE_VERMELHO = set()
_C = {}


# --------------------------------------------------------------------------
# Objetos
# --------------------------------------------------------------------------
def gota(cor, w=120):
    k = ("gota", cor, w)
    if k not in _C:
        p = Pincel(120, 160)
        p.poli([(60, 8), (104, 96), (60, 148), (16, 96)], cor, ow=7)
        p.elipse((16, 70, 104, 150), cor, ow=0)
        p.elipse((40, 90, 62, 120), (255, 255, 255), ow=0)
        img = p.pronto()
        _C[k] = img if w == 120 else img.resize((w, int(160 * w / 120)), Image.BICUBIC)
    return _C[k]


def coroa():
    p = Pincel(240, 240)
    p.elipse((10, 10, 230, 230), (60, 110, 70), ow=8)
    p.elipse((50, 50, 190, 190), (0, 0, 0, 0), ow=0)
    for i in range(10):
        a = math.radians(i * 36)
        x, y = 120 + 90 * math.cos(a), 120 + 90 * math.sin(a)
        p.elipse((x - 22, y - 22, x + 22, y + 22), [(250, 250, 250), (255, 200, 210), (240, 230, 130)][i % 3], ow=5)
    img = p.pronto()
    d = Pincel(240, 240)
    d.elipse((60, 60, 180, 180), (0, 0, 0, 0), ow=0)
    return img


def caixao(w=700):
    k = ("cx", w)
    if k not in _C:
        p = Pincel(700, 260)
        p.ret((20, 80, 680, 240), (84, 56, 44), r=24)
        p.ret((60, 40, 640, 120), (110, 74, 56), r=22)
        p.ret((90, 52, 610, 100), (240, 235, 225), r=14, ow=0)
        p.ret((320, 56, 380, 96), (210, 170, 70), r=6, ow=0)
        for x in (40, 640):
            p.ret((x, 120, x + 20, 220), (210, 170, 70), r=4, ow=4)
        img = p.pronto()
        _C[k] = img if w == 700 else img.resize((w, int(260 * w / 700)), Image.BICUBIC)
    return _C[k]


def moto(w=560, destruida=False):
    k = ("moto", w, destruida)
    if k not in _C:
        p = Pincel(560, 340)
        for cx in (120, 440):
            p.elipse((cx - 90, 160, cx + 90, 330), (35, 35, 42), ow=0)
            p.elipse((cx - 55, 195, cx + 55, 295), (200, 205, 215), ow=5)
            p.elipse((cx - 14, 238, cx + 14, 266), (120, 125, 135), ow=4)
        p.linha([(120, 245), (230, 130), (370, 130), (440, 245)], fill=(215, 60, 60), w=22)
        p.linha([(230, 130), (260, 245), (120, 245)], fill=(215, 60, 60), w=18)
        p.ret((230, 90, 380, 140), (215, 60, 60), r=22)
        p.ret((220, 150, 340, 250), (60, 62, 72), r=14)
        p.ret((100, 260, 320, 285), (160, 165, 175), r=10)
        p.ret((200, 70, 300, 100), (50, 50, 60), r=14)
        p.linha([(440, 245), (420, 110), (470, 90)], fill=(80, 80, 92), w=12)
        p.elipse((480, 120, 530, 170), (255, 235, 160), ow=5)
        img = p.pronto()
        if destruida:
            img = img.rotate(-18, expand=True, resample=Image.BICUBIC)
            d = ImageDraw.Draw(img)
            d.line((60, 80, 200, 40), fill=(60, 60, 70, 255), width=14)
        _C[k] = img if w == 560 else img.resize((w, int(img.height * w / img.width)), Image.BICUBIC)
    return _C[k]


def caminhao(w=640):
    p = Pincel(640, 320)
    p.ret((10, 40, 420, 240), (235, 235, 240), r=14)
    p.ret((420, 90, 620, 240), (240, 150, 50), r=24)
    p.ret((460, 110, 590, 180), (170, 215, 240), r=12, ow=5)
    for cx in (110, 330, 540):
        p.elipse((cx - 50, 200, cx + 50, 300), (30, 30, 36), ow=0)
        p.elipse((cx - 22, 228, cx + 22, 272), (180, 185, 195), ow=4)
    img = p.pronto()
    return img if w == 640 else img.resize((w, int(320 * w / 640)), Image.BICUBIC)


def freio_gasto(w=500):
    p = Pincel(500, 500)
    p.elipse((40, 40, 460, 460), (190, 195, 205), ow=10)
    p.elipse((120, 120, 380, 380), (140, 145, 158), ow=6)
    p.elipse((210, 210, 290, 290), (60, 60, 70), ow=5)
    p.ret((330, 140, 410, 360), (90, 70, 60), r=16)
    p.ret((345, 160, 395, 340), (50, 40, 36), r=10, ow=0)
    img = p.pronto()
    return img if w == 500 else img.resize((w, w), Image.BICUBIC)


def celular(fc, titulo, msg, w=620):
    p = Pincel(500, 900)
    p.ret((10, 10, 490, 890), (28, 30, 40), r=60, ow=8)
    p.ret((36, 70, 464, 850), (235, 235, 240), r=30, ow=0)
    p.ret((36, 70, 464, 150), (120, 70, 150), r=0, ow=0)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f1, f2 = vc.fonte(fc, 36), vc.fonte(fc, 34)
    d.text((62, 90), titulo, font=f1, fill=(255, 255, 255))
    d.rounded_rectangle((60, 300, 440, 420), radius=24, fill=(255, 255, 255), outline=(190, 190, 200), width=3)
    d.text((82, 332), msg, font=f2, fill=(40, 40, 50))
    return img if w == 500 else img.resize((w, int(900 * w / 500)), Image.BICUBIC)


def oculos(m, cx, by, e, bob=0.0):
    """Óculos escuros por cima da cabeça do personagem (colado em coordenadas do mundo)."""
    y = by - bob - 447 * e
    p = Pincel(int(260 * e) + 40, int(90 * e) + 40)
    w, h = int(260 * e) + 40, int(90 * e) + 40
    c = w / 2
    for sx in (-1, 1):
        x0 = c + sx * 46 * e - 40 * e
        p.ret((x0, 20, x0 + 80 * e, 20 + 62 * e), (14, 14, 20), r=int(22 * e))
    p.linha([(c - 8 * e, 40), (c + 8 * e, 40)], fill=(14, 14, 20), w=max(3, int(6 * e)))
    img = p.pronto()
    m.alpha_composite(img, (int(cx - w / 2), int(y - 36 * e)))


def lagrima(m, cx, by, e, cor, t, bob=0.0, lados=(-1, 1), tam=1.0):
    ey = by - bob - 447 * e
    for sx in lados:
        for k in range(2):
            ph = (t * 0.7 + k * 0.5 + (0.13 if sx > 0 else 0)) % 1
            x = cx + sx * 46 * e + 4 * math.sin(ph * 6)
            y = ey + 28 * e + ph * 190 * e
            w = max(6, int(34 * e * tam * (1 - 0.3 * ph)))
            gi = gota(cor, w)
            a = gi.getchannel("A").point(lambda v: int(v * min(1, (1 - ph) * 2.2)))
            gi = gi.copy()
            gi.putalpha(a)
            m.alpha_composite(gi, (int(x - gi.width / 2), int(y - gi.height / 2)))


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def capela_velorio(fc):
    base = gradiente(WW, WH, (232, 222, 200), (212, 200, 176))
    p = Pincel(WW, WH)
    p.ret((-20, 1450, WW + 20, WH + 20), (140, 110, 85), r=0)
    for x in (130, 540, 950):
        p.elipse((x - 105, 400, x + 105, 610), (60, 110, 70), ow=8)
        p.elipse((x - 60, 445, x + 60, 565), (232, 222, 200), ow=0)
        for i in range(9):
            a = math.radians(i * 40)
            p.elipse((x + 85 * math.cos(a) - 20, 505 + 85 * math.sin(a) - 20, x + 85 * math.cos(a) + 20,
                      505 + 85 * math.sin(a) + 20), [(250, 250, 250), (255, 200, 210)][i % 2], ow=4)
    p.ret((120, 1180, 960, 1300), (130, 95, 70), r=10)                              # mesa do caixão
    for x in (100, 980):
        p.ret((x - 12, 1000, x + 12, 1200), (210, 200, 180), r=4)
        p.elipse((x - 12, 960, x + 12, 1010), (255, 190, 60), ow=0)
    base.alpha_composite(p.pronto())
    base.alpha_composite(caixao(760), (160, 1000))
    for x in (100, 980):
        base.alpha_composite(brilho((300, 300), (255, 210, 120), 140, 0.5), (x - 150, 900))
    return base


def casa_parede(fc):
    base = gradiente(WW, WH, (235, 225, 205), (218, 205, 182))
    p = Pincel(WW, WH)
    p.ret((-20, 1480, WW + 20, WH + 20), (150, 115, 85), r=0)
    base.alpha_composite(p.pronto())
    return base


def quadros(base, fc, narr_ausente=True):
    """Parede de retratos: só o Rafael (diplomas, medalhas)."""
    p = Pincel(WW, WH)
    pos = ((120, 300), (460, 260), (800, 300), (260, 640), (640, 620))
    for x, y in pos:
        p.ret((x, y, x + 200, y + 260), (150, 105, 70), r=8, ow=6)
        p.ret((x + 16, y + 16, x + 184, y + 244), (205, 225, 245), r=4, ow=0)
        cab = g.desenhar_personagem(RAFAEL, "feliz", "idle", so_cabeca=True).crop((20, 20, 320, 300)).resize((140, 130),
                                                                                                           Image.BICUBIC)
    base.alpha_composite(p.pronto())
    ch = g.desenhar_personagem(RAFAEL, "feliz", "idle", so_cabeca=True).crop((20, 20, 320, 300)).resize((140, 130),
                                                                                                       Image.BICUBIC)
    for x, y in pos:
        base.alpha_composite(ch, (x + 30, y + 60))
    return base


def borracharia(fc):
    base = gradiente(WW, WH, (150, 155, 165), (120, 124, 134))
    p = Pincel(WW, WH)
    p.ret((-20, 1450, WW + 20, WH + 20), (95, 98, 108), r=0)
    p.ret((60, 300, 1020, 460), (240, 190, 50), r=12, ow=8)
    for i in range(4):
        p.elipse((60 + i * 40, 1100 - i * 120, 280 + i * 40, 1300 - i * 120), (40, 40, 46), ow=6)
    p.ret((700, 980, 960, 1450), (110, 114, 126), r=6)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 70)
    d.text((540 - f.getlength("BORRACHARIA") / 2, 330), "BORRACHARIA", font=f, fill=(60, 40, 20))
    base.alpha_composite(Image.new("RGBA", (WW, WH), (20, 30, 60, 60)))
    return base


def ponte_chuva():
    base = gradiente(WW, WH, (70, 85, 95), (110, 125, 135))
    p = Pincel(WW, WH)
    p.ret((-20, 1000, WW + 20, 1380), (60, 100, 150), r=0, ow=0)                     # rio
    p.ret((-20, 1380, WW + 20, 1560), (110, 112, 120), r=0, ow=0)                    # ponte
    for x in range(-20, WW + 40, 120):
        p.ret((x, 1250, x + 20, 1380), (150, 150, 160), r=4, ow=0)
    p.ret((-20, 1240, WW + 20, 1270), (170, 170, 180), r=4)
    p.ret((-20, 1560, WW + 20, WH + 20), (60, 62, 72), r=0)
    for x in range(0, WW, 200):
        p.ret((x + 30, 1730, x + 150, 1752), (200, 190, 130), r=6, ow=0)
    p.poli([(-20, 800), (250, 650), (520, 800)], (70, 100, 80))
    p.poli([(380, 800), (700, 620), (1020, 800)], (60, 92, 74))
    base.alpha_composite(p.pronto())
    return base


def galpao(fc):
    base = gradiente(WW, WH, (175, 185, 195), (150, 158, 168))
    p = Pincel(WW, WH)
    p.ret((-20, 1450, WW + 20, WH + 20), (120, 124, 132), r=0)
    for x in range(-20, WW + 40, 60):
        p.ret((x, 820, x + 8, 1450), (110, 114, 122), r=0, ow=0)
    p.ret((-20, 820, WW + 20, 840), (110, 114, 122), r=0, ow=0)
    p.ret((300, 520, 780, 680), (40, 70, 130), r=10, ow=6)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 54)
    d.text((540 - f.getlength("PÁTIO - POLÍCIA") / 2, 560), "PÁTIO - POLÍCIA", font=f, fill=(255, 255, 255))
    return base


def quarto_rafael():
    base = gradiente(WW, WH, (95, 115, 165), (70, 88, 135))
    p = Pincel(WW, WH)
    p.ret((-20, 1480, WW + 20, WH + 20), (80, 70, 90), r=0)
    p.ret((60, 360, 420, 1250), (140, 100, 70), r=8)
    for k in range(5):
        y = 400 + k * 170
        p.ret((60, y + 130, 420, y + 150), (110, 75, 50), r=0, ow=0)
        for j in range(5):
            p.ret((80 + j * 66, y + 20, 130 + j * 66, y + 130), [(200, 70, 70), (70, 120, 200), (230, 200, 70),
                                                              (90, 170, 100), (170, 90, 190)][(j + k) % 5], r=4)
    p.ret((680, 300, 960, 560), (225, 235, 245), r=8, ow=8)
    p.ret((640, 1300, 1060, 1480), (150, 170, 215), r=24)
    base.alpha_composite(p.pronto())
    return base


def garagem():
    base = gradiente(WW, WH, (225, 215, 195), (205, 195, 172))
    p = Pincel(WW, WH)
    p.ret((-20, 1480, WW + 20, WH + 20), (120, 118, 118), r=0)
    p.ret((200, 620, 880, 1480), (150, 155, 165), r=10, ow=8)
    for y in range(660, 1480, 70):
        p.ret((210, y, 870, y + 8), (120, 125, 135), r=0, ow=0)
    base.alpha_composite(p.pronto())
    return base


def casa_noite():
    base = gradiente(WW, WH, (40, 45, 90), (70, 70, 120))
    p = Pincel(WW, WH)
    p.ret((-20, 1450, WW + 20, WH + 20), (60, 60, 80), r=0)
    p.ret((180, 760, 900, 1450), (215, 190, 160), r=8)
    p.poli([(140, 770), (540, 520), (940, 770)], (120, 70, 70))
    for x in (260, 640):
        p.ret((x, 900, x + 150, 1080), (255, 215, 140), r=8, ow=7)
    p.ret((440, 1160, 540, 1450), (100, 70, 55), r=8)
    base.alpha_composite(p.pronto())
    for x in (260, 640):
        base.alpha_composite(brilho((380, 380), (255, 200, 120), 190, 0.55), (x - 115, 800))
    return base


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeLagrima(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.narr, self.narr_c = P_(NARR), P_(NARR_C)
        self.raf, self.raf_f = P_(RAFAEL), P_(RAFAEL_F)
        self.mae, self.mae_c, self.pai, self.pai_c = P_(MAE), P_(MAE_C), P_(PAI), P_(PAI_C)
        self.tio, self.tia, self.viuva, self.prima = P_(TIO), P_(TIA), P_(VIUVA), P_(PRIMA)
        self.perito = P_(PERITO)
        self.povo = [P_(c) for c in POVO_PRETO]
        self.povoc = [P_(c) for c in POVO_COR]
        self.blur = {}
        self.cap = capela_velorio(fc)
        self.parede = quadros(casa_parede(fc), fc)
        self.casa = casa_parede(fc)
        self.borr = borracharia(fc)
        self.ponte = ponte_chuva()
        self.galp = galpao(fc)
        self.qrt = quarto_rafael()
        self.gar = garagem()
        self.casan = casa_noite()
        self.rua = vz.ponto_dia()
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        P = [
            (0.00, self.p_hook, "triste", "corte"),
            (2.74, self.p_azul, "", "corte"),
            (4.32, self.p_verm, "", "corte"),
            (5.80, self.p_preta, "", "corte"),
            (7.30, self.p_viuva, "triste", "whip"),
            (12.16, self.p_ninguem, "", "whip"),
            (14.66, self.p_oculos, "triste", "whip"),
            (18.66, self.p_rafael, "", "whip"),
            (21.12, self.p_perfeito, "", "corte"),
            (24.72, self.p_domingo, "", "whip"),
            (27.58, self.p_sempre, "", "corte"),
            (32.02, self.p_nunca_liguei, "", "corte"),
            (33.30, self.p_borracharia, "frio", "dissolve"),
            (37.82, self.p_pediu, "frio", "corte"),
            (41.32, self.p_chave, "frio", "corte"),
            (42.44, self.p_boa, "frio", "corte"),
            (45.08, self.p_ponte, "frio", "whip"),
            (49.40, self.p_nao_resistiu, "triste", "dissolve"),
            (51.08, self.p_velorio, "triste", "dissolve"),
            (53.52, self.p_mae_chora, "triste", "corte"),
            (59.28, self.p_aguentei, "triste", "corte"),
            (60.64, self.p_fechar, "triste", "corte"),
            (62.60, self.p_tirei, "triste", "corte"),
            (65.88, self.p_mao, "", "zoom"),
            (67.04, self.p_respiracao, "triste", "corte"),
            (69.46, self.p_tia, "triste", "corte"),
            (71.20, self.p_pai, "triste", "corte"),
            (75.18, self.p_dias, "frio", "dissolve"),
            (78.00, self.p_prima, "frio", "corte"),
            (81.76, self.p_garagem, "frio", "whip"),
            (87.06, self.p_nao_dormi, "frio", "dissolve"),
            (90.24, self.p_freios, "frio", "corte"),
            (92.52, self.p_sabia, "frio", "corte"),
            (95.42, self.p_falei, "frio", "corte"),
            (97.24, self.p_galpao, "", "whip"),
            (100.80, self.p_perito, "", "corte"),
            (103.44, self.p_examinou, "", "corte"),
            (105.34, self.p_gastos, "", "corte"),
            (107.14, self.p_coracao, "", "zoom"),
            (108.10, self.p_mas_nao, "", "corte"),
            (109.88, self.p_caminhao, "frio", "whip"),
            (113.04, self.p_quatro, "frio", "corte"),
            (116.82, self.p_igual, "", "whip"),
            (119.20, self.p_nao_culpa, "", "corte"),
            (121.94, self.p_confuso, "triste", "corte"),
            (126.30, self.p_voltei, "frio", "whip"),
            (128.46, self.p_mae_quarto, "triste", "whip"),
            (132.84, self.p_largou, "triste", "corte"),
            (135.60, self.p_abraco, "triste", "corte"),
            (139.48, self.p_so_voce, "triste", "corte"),
            (141.56, self.p_parado, "triste", "corte"),
            (142.50, self.p_sentir, "triste", "dissolve"),
            (145.84, self.p_primeira, "", "zoom"),
            (148.06, self.p_olhava, "", "corte"),
            (151.16, self.p_pensou, "triste", "dissolve"),
            (155.60, self.p_lagrima, "", "corte"),
            (157.36, self.p_ombro, "", "corte"),
            (159.34, self.p_vermelha, "", "zoom"),
            (160.06, self.p_nao_foi, "", "corte"),
            (161.98, self.p_chorei, "triste", "dissolve"),
            (166.92, self.p_alivio, "", "zoom"),
            (168.92, self.p_mancha, "triste", "corte"),
            (171.58, self.p_forte, "triste", "corte"),
            (173.38, self.p_30anos, "", "dissolve"),
            (176.06, self.p_agora, "", "corte"),
            (177.02, self.p_final, "triste", "dissolve"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))
        self.p_preto = None

    # ---------- utilidades ----------
    def A(self, m, p, t, cx, by, e, expr="neutro", pose="idle", oc=False, lag=None, **kw):
        p(m, t, cx, by, e, expr=expr, pose=pose, **kw)
        bob = getattr(p.a, "ultimo_bob", 0.0)
        if oc:
            oculos(m, cx, by, e, bob)
        if lag:
            lagrima(m, cx, by, e, lag, t, bob)

    def txt(self, f, s, t0, y=0.1, tam=60, cor=(255, 255, 255)):
        if self.T >= t0:
            texto_pop(f, s, self.fc, self.T - t0, OUT_W / 2, OUT_H * y, tam, cor)

    def balao_t(self, f, txt, x, y, t0):
        if self.T >= t0:
            self.balao(f, txt, x, y, self.T - t0)

    def velorio(self, t, quem=None, oc=True, mae_chora=False, z=1.1, cx=540, cy=1250):
        m = self.cap.copy()
        for i, (p, x) in enumerate(zip(self.povo, (120, 330, 760, 960, 540))):
            self.A(m, p, t + i, x, 1800 - (i % 2) * 20, 0.95, expr="triste", oc=oc)
        if quem:
            quem(m)
        return self.cam(m, cx, cy, z)

    def close_a(self, p, t, bg, nome, expr="neutro", z=1.05, oc=False, lag=None, by=2350, e=2.5, cor=None):
        m = self.fundo_blur(nome, bg)
        self.A(m, p, t, 540, by, e, expr=expr, oc=oc, lag=lag)
        return self.cam(m, 540, 950, z)

    # ---------- planos ----------
    def p_hook(self, t, d):
        f = self.velorio(t, z=1.12 - 0.05 * ease_io(t / d))
        self.txt(f, "AQUI, LÁGRIMA TEM COR", 0.3, 0.1, 50, (255, 255, 255))
        return f

    def gota_cena(self, t, cor, rotulo, bg=(24, 24, 34)):
        m = gradiente(WW, WH, bg, (10, 10, 16))
        gi = gota(cor, 520 + int(40 * math.sin(t * 4)))
        m.alpha_composite(brilho((900, 900), cor, 420, 0.35), (90, 500))
        m.alpha_composite(gi, (540 - gi.width // 2, 880))
        f = self.cam(m, 540, 1000, 1.0 + 0.1 * ease_io(min(1, t / 1.5)))
        return f

    def p_azul(self, t, d):
        f = self.gota_cena(t, AZUL, "SAUDADE")
        self.txt(f, "AZUL = SAUDADE", 2.74, 0.12, 56, AZUL)
        return f

    def p_verm(self, t, d):
        f = self.gota_cena(t, VERMELHO, "CULPA")
        self.txt(f, "VERMELHA = CULPA", 4.32, 0.12, 52, (255, 110, 120))
        return f

    def p_preta(self, t, d):
        f = self.gota_cena(t, ROXO, "ÓDIO", bg=(60, 60, 78))
        self.txt(f, "PRETA = ÓDIO", 5.8, 0.12, 56, (230, 230, 240))
        return f

    def p_viuva(self, t, d):
        m = self.cap.copy()
        for i, (p, x) in enumerate(zip(self.povo[:3], (140, 900, 960))):
            self.A(m, p, t + i, x, 1800, 0.95, expr="surpreso", oc=True)
        self.A(m, self.viuva, t, 540, 1800, 1.3, expr="chora", lag=ROXO)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "SEU OSVALDO", 7.38, 0.1, 64, (255, 255, 255))
        self.txt(f, "CHOROU PRETO", 9.4, 0.18, 54, (210, 210, 225))
        return f

    def p_ninguem(self, t, d):
        m = self.rua.copy()
        for i, p in enumerate(self.povoc[:4]):
            x = 160 + i * 250 + 30 * math.sin(t * 1.5 + i)
            self.A(m, p, t + i, x, 1800, 0.95, expr="neutro", pose="anda")
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "NINGUÉM CHORA EM PÚBLICO", 12.16, 0.1, 40, (255, 255, 255))
        return f

    def p_oculos(self, t, d):
        f = self.velorio(t, z=1.15)
        self.txt(f, "ÓCULOS ESCUROS", 15.96, 0.1, 62, (255, 255, 255))
        self.txt(f, "É EDUCAÇÃO", 17.64, 0.18, 54, (255, 214, 40))
        return f

    def p_rafael(self, t, d):
        m = self.casa.copy()
        self.A(m, self.raf, t, 540, 1800, 1.4, expr="feliz", pose="acena")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "RAFAEL", 20.24, 0.1, 90, (255, 214, 40))
        return f

    def p_perfeito(self, t, d):
        m = self.casa.copy()
        self.A(m, self.raf, t, 540, 1800, 1.35, expr="feliz", pose="entrega")
        hx, hy = self.raf.a.maos_mundo[1]
        m.alpha_composite(__import__("video_abracos").diploma(), (int(hx - 120), int(hy - 40)))
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "O FILHO PERFEITO", 21.12, 0.1, 52, (255, 255, 255))
        self.txt(f, "ENGENHARIA", 22.7, 0.18, 62, (255, 214, 40))
        return f

    def p_domingo(self, t, d):
        m = self.casa.copy()
        p = Pincel(WW, WH)
        p.ret((100, 1300, 980, 1380), (150, 105, 70), r=10)
        p.ret((150, 1380, 180, 1700), (120, 85, 55), r=4)
        p.ret((900, 1380, 930, 1700), (120, 85, 55), r=4)
        m.alpha_composite(p.pronto())
        self.A(m, self.raf, t, 220, 1760, 1.1, expr="feliz", pose="acena")
        for i, (p_, x) in enumerate(zip((self.mae_c, self.pai_c), (520, 800))):
            self.A(m, p_, t + i, x, 1780, 1.0, expr="neutro")
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "ALMOÇO DE DOMINGO", 25.04, 0.1, 52, (255, 255, 255))
        return f

    def p_sempre(self, t, d):
        m = self.parede.copy()
        self.A(m, self.narr_c, t, 900, 1850, 0.9, expr="neutro")
        f = self.cam(m, 540, 1100, 1.1)
        self.txt(f, "TINHA O RAFAEL", 29.4, 0.1, 56, (255, 255, 255))
        self.txt(f, "E O IRMÃO DO RAFAEL", 30.96, 0.17, 44, (255, 160, 140))
        return f

    def p_nunca_liguei(self, t, d):
        f = self.close_a(self.narr_c, t, self.casa, "casa", expr="neutro", z=1.05)
        return f

    def p_borracharia(self, t, d):
        m = self.borr.copy()
        mo = moto(520)
        m.alpha_composite(mo, (200, 1300))
        self.A(m, self.raf, t, 800, 1800, 1.2, expr="neutro", pose="bolso")
        f = self.cam(m, 540, 1250, 1.12)
        self.chuva_f(f, t, 60)
        self.txt(f, "MOTO NA BORRACHARIA", 36.06, 0.1, 44, (255, 255, 255))
        return f

    def chuva_f(self, f, t, n=100, seed=4):
        d = ImageDraw.Draw(f, "RGBA")
        rng = random.Random(seed)
        for _ in range(n):
            x = rng.uniform(0, OUT_W)
            y = (rng.uniform(0, OUT_H) + t * rng.uniform(900, 1400)) % OUT_H
            d.line((x, y, x - 5, y + 30), fill=(200, 215, 245, 190), width=3)

    def p_pediu(self, t, d):
        m = self.casa.copy()
        self.A(m, self.raf, t, 340, 1800, 1.25, expr="feliz", pose="entrega")
        self.A(m, self.narr_c, t, 760, 1800, 1.25, expr="neutro")
        f = self.cam(m, 540, 1250, 1.12)
        self.balao_t(f, "Me empresta sua moto?", OUT_W * 0.35, OUT_H * 0.14, 38.46)
        self.txt(f, "SANTA RITA", 40.48, 0.22, 56, (255, 214, 40))
        return f

    def p_chave(self, t, d):
        m = self.casa.copy()
        self.A(m, self.narr_c, t, 330, 1800, 1.3, expr="neutro", pose="entrega")
        self.A(m, self.raf, t, 760, 1800, 1.3, expr="feliz", pose="entrega")
        f = self.cam(m, 540, 1250, 1.15)
        self.txt(f, "ENTREGUEI A CHAVE", 41.4, 0.12, 52, (255, 255, 255))
        return f

    def p_boa(self, t, d):
        m = self.casa.copy()
        self.A(m, self.raf, t, 340, 1800, 1.3, expr="neutro")
        self.A(m, self.narr_c, t, 760, 1800, 1.3, expr="neutro")
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "A moto tá boa?", OUT_W * 0.35, OUT_H * 0.14, 42.56)
        self.balao_t(f, "Tá tranquila.", OUT_W * 0.66, OUT_H * 0.22, 44.32)
        return f

    def p_ponte(self, t, d):
        m = self.ponte.copy()
        T = self.T
        k = min(1, t / d)
        if T < 46.6:
            x = -100 + 800 * ease_in_(min(1, (T - 45.08) / 1.5)) / 1.0
            m.alpha_composite(moto(420), (int(x), 1330))
        else:
            kk = min(1, (T - 46.6) / 2.6)
            mo = moto(420).rotate(-60 * kk, expand=True, resample=Image.BICUBIC)
            m.alpha_composite(mo, (int(700 + 260 * kk), int(1250 + 520 * kk)))
        f = self.cam(m, 540 + 60 * k, 1300, 1.15)
        self.chuva_f(f, t, 140)
        self.txt(f, "ESCORREGOU", 46.48, 0.12, 70, (255, 130, 110))
        return f

    def p_nao_resistiu(self, t, d):
        m = gradiente(WW, WH, (28, 28, 38), (12, 12, 20))
        self.A(m, self.raf_f, t, 540, 1800, 1.4, expr="neutro", alpha=0.55)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "O RAFAEL NÃO RESISTIU", 49.4, 0.12, 48, (255, 255, 255))
        return f

    def p_velorio(self, t, d):
        f = self.velorio(t, z=1.12)
        self.txt(f, "TODO MUNDO DE ÓCULOS ESCUROS", 51.82, 0.1, 38, (255, 255, 255))
        return f

    def p_mae_chora(self, t, d):
        m = self.cap.copy()
        self.A(m, self.mae, t, 640, 1800, 1.5, expr="chora", pose="idle", lag=AZUL)
        f = self.cam(m, 600, 1250, 1.12)
        self.txt(f, "MENOS A MINHA MÃE", 53.52, 0.1, 48, (255, 255, 255))
        self.txt(f, "CHOROU AZUL", 55.88, 0.18, 60, AZUL)
        return f

    def p_aguentei(self, t, d):
        m = self.cap.copy()
        self.A(m, self.narr, t, 540, 1800, 1.5, expr="neutro", oc=True)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "EU AGUENTEI ATÉ O FIM", 59.38, 0.1, 44, (255, 255, 255))
        return f

    def p_fechar(self, t, d):
        m = self.cap.copy()
        T = self.T
        p = Pincel(WW, WH)
        k = ease_io(min(1, t / d))
        p.ret((160, 1000, 920, 1060 + int(60 * k)), (165, 115, 80), r=10, ow=8)
        m.alpha_composite(p.pronto())
        self.A(m, self.narr, t, 540, 1850, 1.4, expr="triste", oc=True)
        f = self.cam(m, 540, 1250, 1.15)
        self.txt(f, "NA HORA DE FECHAR", 60.76, 0.1, 54, (255, 255, 255))
        return f

    def p_tirei(self, t, d):
        m = self.cap.copy()
        T = self.T
        self.A(m, self.narr, t, 540, 1800, 1.5, expr="chora", pose="entrega", oc=T < 63.0)
        hx, hy = self.narr.a.maos_mundo[1]
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "TIREI OS ÓCULOS", 62.84, 0.1, 54, (255, 255, 255))
        return f

    def p_mao(self, t, d):
        m = gradiente(WW, WH, (24, 22, 30), (10, 10, 16))
        p = Pincel(WW, WH)
        p.ret((290, 700, 790, 1400), (222, 170, 128), r=170)
        for i in range(4):
            p.ret((290 + i * 120, 440 - (i % 2) * 40 - (i == 3) * 60, 380 + i * 120, 800), (222, 170, 128), r=44)
        p.ret((130, 900, 330, 1040), (222, 170, 128), r=60)
        m.alpha_composite(p.pronto())
        q = Pincel(WW, WH)
        for x, y, r in ((520, 1000, 50), (610, 1120, 36), (440, 1160, 30), (580, 900, 24)):
            q.elipse((x - r, y - r, x + r, y + r), VERMELHO, ow=0)
        m.alpha_composite(q.pronto())
        f = self.cam(m, 540, 1000, 1.0 + 0.15 * ease_io(t / d))
        self.txt(f, "ESTAVA VERMELHA.", 65.88, 0.1, 62, (255, 110, 120))
        return f

    def p_respiracao(self, t, d):
        m = self.cap.copy()
        for i, (p, x) in enumerate(zip(self.povo[:4], (140, 400, 700, 940))):
            self.A(m, p, t + i, x, 1800, 1.1, expr="surpreso", oc=True)
        self.A(m, self.narr, t, 540, 1830, 0.85, expr="triste")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "ALGUÉM PRENDEU A RESPIRAÇÃO", 67.26, 0.1, 36, (255, 255, 255))
        return f

    def p_tia(self, t, d):
        m = self.cap.copy()
        self.A(m, self.tia, t, 340, 1800, 1.3, expr="surpreso", pose="bate", oc=True)
        self.A(m, self.tio, t, 740, 1800, 1.3, expr="surpreso", oc=True)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "A TIA CUTUCOU O TIO", 69.64, 0.1, 44, (255, 255, 255))
        return f

    def p_pai(self, t, d):
        m = self.cap.copy()
        T = self.T
        virou = T > 73.9
        self.A(m, self.pai, t, 540, 1800, 1.5, expr="triste" if not virou else "neutro", sx=-1 if virou else 1)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "MEU PAI VIROU DE COSTAS", 72.7, 0.1, 40, (255, 255, 255))
        return f

    def p_dias(self, t, d):
        m = self.casan.copy()
        self.A(m, self.narr, t, 540, 1800, 1.3, expr="triste")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "NINGUÉM LIGOU", 76.42, 0.1, 62, (255, 255, 255))
        return f

    def p_prima(self, t, d):
        m = gradiente(WW, WH, (30, 30, 44), (14, 14, 24))
        c = celular(self.fc, "Prima Bia", "O que você fez?", 760)
        m.alpha_composite(c, (540 - c.width // 2, 600))
        f = self.cam(m, 540, 1100, 1.0 + 0.1 * ease_io(t / d))
        self.txt(f, "UMA MENSAGEM SÓ", 78.7, 0.1, 52, (255, 255, 255))
        return f

    def p_garagem(self, t, d):
        m = self.gar.copy()
        T = self.T
        self.A(m, self.pai_c, t, 740, 1800, 1.4, expr="triste", sx=-1)
        self.A(m, self.narr_c, t, 300, 1830, 1.1, expr="triste")
        f = self.cam(m, 540, 1250, 1.12)
        self.balao_t(f, "A moto era sua.", OUT_W * 0.62, OUT_H * 0.14, 85.86)
        self.txt(f, "SEM ME OLHAR", 85.0, 0.22, 52, (255, 255, 255)) if T < 85.86 else None
        return f

    def p_nao_dormi(self, t, d):
        m = self.casan.copy()
        m.alpha_composite(Image.new("RGBA", (WW, WH), (10, 10, 30, 90)))
        self.A(m, self.narr, t, 540, 1800, 1.3, expr="triste", pose="bolso")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "NÃO DORMI MAIS", 87.28, 0.1, 62, (255, 255, 255))
        return f

    def p_freios(self, t, d):
        m = gradiente(WW, WH, (50, 50, 62), (22, 22, 30))
        fr = freio_gasto(720)
        m.alpha_composite(fr, (540 - fr.width // 2, 700))
        f = self.cam(m, 540, 1000, 1.0 + 0.12 * ease_io(t / d))
        self.txt(f, "FREIOS GASTOS", 90.38, 0.1, 62, (255, 130, 110))
        return f

    def p_sabia(self, t, d):
        f = self.close_a(self.narr_c, t, self.casa, "casa", expr="triste", z=1.05)
        self.txt(f, "EU SABIA", 92.6, 0.1, 80, (255, 130, 110))
        if self.T > 94.3:
            self.txt(f, "ADIANDO HÁ MESES", 94.3, 0.2, 48, (255, 255, 255))
        return f

    def p_falei(self, t, d):
        m = self.casa.copy()
        self.A(m, self.narr_c, t, 540, 1800, 1.4, expr="neutro")
        f = self.cam(m, 540, 1250, 1.12)
        self.balao_t(f, "Tá tranquila.", OUT_W * 0.5, OUT_H * 0.14, 95.42)
        return f

    def p_galpao(self, t, d):
        m = self.galp.copy()
        m.alpha_composite(moto(640, True), (300, 1340))
        self.A(m, self.narr_c, t, 220, 1800, 1.2, expr="triste")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "O QUE SOBROU DA MOTO", 98.96, 0.1, 44, (255, 255, 255))
        return f

    def p_perito(self, t, d):
        m = self.galp.copy()
        m.alpha_composite(moto(520, True), (480, 1400))
        self.A(m, self.perito, t, 300, 1800, 1.3, expr="neutro", pose="aponta")
        self.A(m, self.narr_c, t, 820, 1830, 1.1, expr="neutro")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "O PERITO", 101.16, 0.1, 62, (255, 214, 40))
        return f

    def p_examinou(self, t, d):
        m = self.galp.copy()
        m.alpha_composite(moto(640, True), (320, 1400))
        self.A(m, self.perito, t, 240, 1800, 1.3, expr="neutro", pose="bate")
        f = self.cam(m, 540, 1300, 1.15)
        return f

    def p_gastos(self, t, d):
        f = self.close_a(self.perito, t, self.galp, "galp", expr="neutro", z=1.05)
        self.balao_t(f, "Os freios estavam gastos.", OUT_W / 2, OUT_H * 0.16, 105.48)
        return f

    def p_coracao(self, t, d):
        m = gradiente(WW, WH, (30, 22, 30), (10, 8, 14))
        s = 1 + 0.22 * abs(math.sin(t * 9))
        p = Pincel(WW, WH)
        p.elipse((540 - 140 * s, 960 - 130 * s, 540 + 140 * s, 960 + 130 * s), (230, 50, 70), ow=0)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 1000, 1.0)
        self.txt(f, "MEU CORAÇÃO PAROU", 107.28, 0.12, 50, (255, 255, 255))
        return f

    def p_mas_nao(self, t, d):
        f = self.close_a(self.perito, t, self.galp, "galp", expr="neutro", z=1.05)
        self.balao_t(f, "Sim, mas não foi isso.", OUT_W / 2, OUT_H * 0.16, 108.1)
        return f

    def p_caminhao(self, t, d):
        m = self.ponte.copy()
        x = -500 + 1500 * ease_io(min(1, t / d))
        m.alpha_composite(caminhao(640), (int(x), 1270))
        q = Pincel(WW, WH)
        for k in range(8):
            ox = x + 120 - k * 80
            q.elipse((ox - 70, 1655, ox + 70, 1690), (20, 20, 26, 230), ow=0)
        m.alpha_composite(q.pronto())
        f = self.cam(m, 540, 1350, 1.1)
        self.chuva_f(f, t, 120)
        self.txt(f, "ÓLEO NA PONTE", 111.42, 0.1, 62, (255, 214, 40))
        return f

    def p_quatro(self, t, d):
        m = self.ponte.copy()
        T = self.T
        for i in range(4):
            tt = T - 113.04 - i * 0.7
            if tt < 0:
                continue
            kk = min(1, tt / 1.2)
            mo = moto(300).rotate(-50 * kk, expand=True, resample=Image.BICUBIC)
            m.alpha_composite(mo, (int(120 + i * 250 - 80 * kk), int(1380 + 100 * kk)))
        f = self.cam(m, 540, 1350, 1.1)
        self.chuva_f(f, t, 120)
        self.txt(f, "4 VEÍCULOS", 113.36, 0.1, 74, (255, 214, 40))
        self.txt(f, "NO MESMO PONTO", 114.72, 0.18, 48, (255, 255, 255))
        return f

    def p_igual(self, t, d):
        m = self.galp.copy()
        self.A(m, self.perito, t, 340, 1800, 1.3, expr="neutro", pose="aponta")
        self.A(m, self.narr_c, t, 800, 1830, 1.1, expr="surpreso")
        f = self.cam(m, 540, 1250, 1.12)
        self.balao_t(f, "Com freio novo, igual.", OUT_W / 2, OUT_H * 0.16, 117.28)
        return f

    def p_nao_culpa(self, t, d):
        m = self.galp.copy()
        x = 540 + 220 * ease_io(min(1, t / d))
        self.A(m, self.narr_c, t, x, 1800, 1.3, expr="neutro", pose="anda")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "NÃO ERA CULPA MINHA", 119.2, 0.1, 46, (255, 255, 255))
        return f

    def p_confuso(self, t, d):
        m = self.fundo_blur("galp", self.galp)
        self.A(m, self.narr_c, t, 540, 2350, 2.5, expr="surpreso")
        f = self.cam(m, 540, 950, 1.05)
        self.txt(f, "ENTÃO POR QUE", 123.0, 0.1, 54, (255, 255, 255))
        self.txt(f, "CHOREI VERMELHO?", 124.44, 0.18, 62, (255, 110, 120))
        return f

    def p_voltei(self, t, d):
        m = self.casan.copy()
        x = -100 + 600 * ease_io(min(1, t / d))
        self.A(m, self.narr_c, t, x, 1800, 1.2, expr="triste", pose="anda")
        return self.cam(m, 540, 1250, 1.12)

    def p_mae_quarto(self, t, d):
        m = self.qrt.copy()
        cx = Pincel(500, 300)
        cx.ret((20, 90, 480, 280), (190, 140, 90), r=10)
        m.alpha_composite(cx.pronto(), (400, 1560))
        self.A(m, self.mae_c, t, 620, 1780, 1.3, expr="triste", pose="entrega")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "O QUARTO DO RAFAEL", 128.46, 0.1, 48, (255, 255, 255))
        return f

    def p_largou(self, t, d):
        m = self.qrt.copy()
        x = 760 - 280 * ease_io(min(1, t / d))
        self.A(m, self.mae_c, t, x, 1780, 1.3, expr="surpreso", pose="anda", sx=-1)
        self.A(m, self.narr_c, t, 260, 1800, 1.2, expr="triste")
        return self.cam(m, 540, 1250, 1.12)

    def p_abraco(self, t, d):
        m = self.qrt.copy()
        self.A(m, self.mae_c, t, 440, 1780, 1.35, expr="chora", pose="abraca_d")
        self.A(m, self.narr_c, t, 660, 1800, 1.3, expr="surpreso", pose="abraca_e")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "ME ABRAÇOU FORTE", 135.84, 0.1, 52, (255, 255, 255))
        return f

    def p_so_voce(self, t, d):
        f = self.close_a(self.mae_c, t, self.qrt, "qrt", expr="chora", z=1.05)
        self.balao_t(f, "Agora eu só tenho você, filho.", OUT_W / 2, OUT_H * 0.14, 139.48)
        return f

    def p_parado(self, t, d):
        f = self.close_a(self.narr_c, t, self.qrt, "qrt", expr="surpreso", z=1.05)
        return f

    def p_sentir(self, t, d):
        m = self.fundo_blur("qrt", self.qrt)
        self.A(m, self.narr_c, t, 540, 2350, 2.5, expr="neutro")
        f = self.cam(m, 540, 950, 1.05)
        self.txt(f, "ALGO QUE NUNCA SENTI", 143.0, 0.1, 44, (255, 255, 255))
        return f

    def p_primeira(self, t, d):
        m = self.parede.copy()
        m.alpha_composite(brilho((900, 900), (255, 235, 180), 420, 0.5), (90, 700))
        self.A(m, self.narr_c, t, 540, 1850, 1.35, expr="neutro")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "PELA PRIMEIRA VEZ,", 145.92, 0.1, 50, (255, 255, 255))
        self.txt(f, "ERA EU", 147.32, 0.18, 90, (255, 214, 40))
        return f

    def p_olhava(self, t, d):
        m = self.qrt.copy()
        m.alpha_composite(brilho((900, 900), (255, 235, 180), 420, 0.35), (90, 700))
        self.A(m, self.mae_c, t, 380, 1780, 1.3, expr="feliz", pose="aponta")
        self.A(m, self.narr_c, t, 760, 1800, 1.3, expr="surpreso")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "O FILHO QUE ELA OLHAVA", 149.42, 0.1, 44, (255, 214, 40))
        return f

    def p_pensou(self, t, d):
        m = self.fundo_blur("qrt", self.qrt)
        self.A(m, self.narr_c, t, 540, 2350, 2.5, expr="triste")
        f = self.cam(m, 540, 950, 1.05)
        self.txt(f, "E UMA PARTE DE MIM", 151.38, 0.1, 44, (255, 255, 255))
        self.txt(f, "\"FINALMENTE.\"", 154.5, 0.18, 70, (255, 110, 120))
        return f

    def p_lagrima(self, t, d):
        m = self.fundo_blur("qrt", self.qrt)
        self.A(m, self.narr_c, t, 540, 2350, 2.5, expr="chora", lag=VERMELHO)
        f = self.cam(m, 540, 950, 1.1)
        self.txt(f, "SENTI UMA LÁGRIMA", 155.96, 0.1, 50, (255, 255, 255))
        return f

    def p_ombro(self, t, d):
        m = self.qrt.copy()
        self.A(m, self.mae_c, t, 560, 1800, 1.6, expr="neutro", pose="idle")
        f = self.cam(m, 480, 1150, 1.25)
        T = self.T
        k = ease_out(min(1, max(0, (T - 158.0) / 0.5)))
        d_ = ImageDraw.Draw(f, "RGBA")
        r = int(34 * k)
        d_.ellipse((OUT_W * 0.50 - r, OUT_H * 0.62 - r, OUT_W * 0.50 + r, OUT_H * 0.62 + r), fill=VERMELHO + (255,))
        gi = gota(VERMELHO, 60)
        f.paste(gi, (int(OUT_W * 0.5 - 30), int(OUT_H * 0.5 + 200 * min(1, (T - 157.36) / 0.6))), gi)
        self.txt(f, "CAIU NO OMBRO DELA", 157.36, 0.1, 50, (255, 255, 255))
        return f

    def p_vermelha(self, t, d):
        m = gradiente(WW, WH, (190, 90, 150), (150, 60, 110))
        p = Pincel(WW, WH)
        p.elipse((380, 820, 700, 1060), VERMELHO, ow=0)
        p.elipse((470, 1040, 600, 1180), VERMELHO, ow=0)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 1000, 1.0 + 0.1 * ease_io(t / d))
        self.txt(f, "VERMELHA.", 159.34, 0.12, 100, (255, 255, 255))
        return f

    def p_nao_foi(self, t, d):
        m = gradiente(WW, WH, (50, 50, 62), (22, 22, 30))
        T = self.T
        fr = freio_gasto(420)
        m.alpha_composite(fr, (110, 800))
        m.alpha_composite(caminhao(420), (540, 840))
        p = Pincel(WW, WH)
        if T > 160.2:
            p.linha([(100, 780), (560, 1260)], fill=VERMELHO, w=30)
            p.linha([(560, 780), (100, 1260)], fill=VERMELHO, w=30)
        if T > 161.22:
            p.linha([(560, 780), (1000, 1260)], fill=VERMELHO, w=30)
            p.linha([(1000, 780), (560, 1260)], fill=VERMELHO, w=30)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 1000, 1.0)
        self.txt(f, "NÃO FOI O FREIO", 160.2, 0.1, 52, (255, 255, 255))
        self.txt(f, "NÃO FOI A PONTE", 161.22, 0.17, 52, (255, 255, 255))
        return f

    def p_chorei(self, t, d):
        m = self.cap.copy()
        self.A(m, self.narr, t, 540, 1800, 1.5, expr="chora", lag=VERMELHO)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "CHOREI VERMELHO", 162.36, 0.1, 60, (255, 110, 120))
        self.txt(f, "NO VELÓRIO DO MEU IRMÃO", 163.4, 0.17, 40, (255, 255, 255))
        return f

    def p_alivio(self, t, d):
        m = self.fundo_blur("cap", self.cap)
        self.A(m, self.narr, t, 540, 2350, 2.5, expr="triste")
        f = self.cam(m, 540, 950, 1.05)
        self.txt(f, "ALÍVIO", 167.74, 0.12, 100, (255, 214, 40))
        return f

    def p_mancha(self, t, d):
        m = self.qrt.copy()
        self.A(m, self.mae_c, t, 560, 1800, 1.5, expr="neutro")
        f = self.cam(m, 480, 1150, 1.2)
        d_ = ImageDraw.Draw(f, "RGBA")
        d_.ellipse((OUT_W * 0.47, OUT_H * 0.6, OUT_W * 0.53, OUT_H * 0.635), fill=VERMELHO + (255,))
        self.txt(f, "ELA OLHOU A MANCHA", 169.08, 0.1, 46, (255, 255, 255))
        return f

    def p_forte(self, t, d):
        m = self.qrt.copy()
        self.A(m, self.mae_c, t, 440, 1780, 1.35, expr="triste", pose="abraca_d")
        self.A(m, self.narr_c, t, 660, 1800, 1.3, expr="chora", pose="abraca_e", lag=VERMELHO)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "ME ABRAÇOU MAIS FORTE", 171.72, 0.1, 44, (255, 255, 255))
        return f

    def p_30anos(self, t, d):
        m = self.parede.copy()
        self.A(m, self.narr_c, t, 540, 1850, 1.3, expr="neutro")
        f = self.cam(m, 540, 1250, 1.12)
        n = int(30 * ease_out(min(1, (self.T - 173.38) / 1.0)))
        self.txt(f, f"{n} ANOS", 173.38, 0.1, 90, (255, 214, 40))
        self.txt(f, "QUERENDO SER O PREFERIDO", 174.56, 0.18, 36, (255, 255, 255))
        return f

    def p_agora(self, t, d):
        m = self.qrt.copy()
        m.alpha_composite(brilho((900, 900), (255, 235, 180), 420, 0.5), (90, 700))
        self.A(m, self.narr_c, t, 540, 1850, 1.4, expr="feliz")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "AGORA EU SOU.", 176.06, 0.1, 70, (255, 214, 40))
        return f

    def p_final(self, t, d):
        m = self.qrt.copy()
        self.A(m, self.mae_c, t, 440, 1780, 1.35, expr="feliz", pose="abraca_d")
        self.A(m, self.narr_c, t, 660, 1800, 1.3, expr="chora", pose="abraca_e", lag=VERMELHO)
        f = self.cam(m, 540, 1250, 1.1 + 0.1 * ease_io(t / d))
        self.txt(f, "E TODA VEZ QUE ELA ME ABRAÇA,", 177.08, 0.1, 34, (255, 255, 255))
        self.txt(f, "EU CHORO VERMELHO.", 178.84, 0.17, 56, (255, 110, 120))
        k = max(0, (t - (d - 1.4)) / 1.4)
        if k > 0:
            f = Image.blend(f, Image.new("RGB", f.size, (0, 0, 0)), min(1, k))
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
    mus = mus / max(1e-6, np.abs(mus).max()) * 0.11
    mix[:len(mus)] += mus[:n]
    rng = np.random.default_rng(13)
    chuva = np.convolve(rng.standard_normal(n).astype(np.float32), np.ones(40, np.float32) / 40, mode="same") * 0.05
    for a, b in ((33.3, 49.4), (97.0, 100.0), (109.88, 119.2)):
        pass
    mask = np.zeros(n, np.float32)
    for a, b in ((33.3, 37.8), (45.08, 49.4), (109.88, 119.2)):
        mask[int(a * SR):int(b * SR)] = 1
    mix += chuva * mask
    ev = filme.eventos_sfx()
    ev += [("brilho", 2.74), ("brilho", 4.32), ("brilho", 5.8), ("toc", 46.48), ("toc", 49.4), ("brilho", 65.88),
           ("toc", 107.28), ("brilho", 155.96), ("brilho", 159.34), ("brilho", 177.1)]
    for tipo, t0 in ev:
        s = g.sfx(tipo) * (0.3 if tipo in ("whoosh", "pop") else 0.8)
        a = int(max(0, t0) * SR)
        b = min(n, a + len(s))
        mix[a:b] += s[: b - a]
    fade = int(SR * 1.2)
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
            t = {"30": "Trinta", "Caio": "Caiu"}.get(w["w"], w["w"])
            out.append(dict(w=t, s=w["s"], e=w["e"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_lagrima_vermelha.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeLagrima(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.4, a.narracao)
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

    tmp = tempfile.mkdtemp(prefix="lagrima_")
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
