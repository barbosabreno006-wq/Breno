#!/usr/bin/env python3
"""
"O Taxista Que Não Cobrava" — nunca cobrou corrida pra maternidade: 31 anos atrás um velho de Fusca
amarelo o levou de graça ao hospital ("me paga quando ela fizer 18 anos"). A neta dele entra no táxi…

Abre DENTRO do táxi, à noite, na chuva (cenários novos em cenarios.py / aqui) + cortes a cada ~2 s.

    python3 animacao/video_taxista.py --narracao narr.mp3 --transcricao transcricao.json --fonte Poppins.ttf
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
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(1414)

TAXISTA = dict(pele=(214, 160, 120), cabelo=(185, 185, 190), camisa=(70, 110, 160), calca=(60, 62, 80),
               sapato=(40, 40, 45), tipo="pai")
TAXISTA_J = dict(TAXISTA, cabelo=(45, 32, 28), camisa=(150, 90, 70))
ESPOSA = dict(pele=(226, 176, 136), cabelo=(60, 38, 30), camisa=(230, 130, 150), calca=(0, 0, 0),
              sapato=(150, 70, 90), tipo="moca", vestido=(230, 130, 150))
GRAVIDA = dict(pele=(222, 170, 128), cabelo=(90, 55, 40), camisa=(130, 190, 150), calca=(0, 0, 0),
               sapato=(80, 110, 90), tipo="moca", vestido=(130, 190, 150))
PAI_ANSIOSO = dict(pele=(232, 186, 150), cabelo=(60, 45, 35), camisa=(215, 120, 60), calca=(60, 70, 100),
                   sapato=(50, 50, 55), tipo="pai", bigode=False)
VELHO = dict(pele=(222, 170, 128), cabelo=(238, 238, 242), camisa=(90, 130, 90), calca=(95, 85, 70),
             sapato=(70, 55, 45), tipo="vovo_h")
COLEGA1 = dict(pele=(196, 140, 100), cabelo=(35, 28, 26), camisa=(235, 235, 240), calca=(60, 62, 80),
               sapato=(40, 40, 45), tipo="pai", bigode=False)
COLEGA2 = dict(pele=(232, 186, 150), cabelo=(110, 70, 40), camisa=(240, 200, 80), calca=(60, 62, 80),
               sapato=(40, 40, 45), tipo="pai")
AMARELO = (250, 210, 40)
vc.DESTAQUE_VERMELHO = set()
_C = {}


# --------------------------------------------------------------------------
# Objetos
# --------------------------------------------------------------------------
def fusca(cor=AMARELO, w=820, h=420):
    k = ("fusca", cor)
    if k in _C:
        return _C[k]
    p = Pincel(w, h)
    p.ret((60, 190, 790, 330), cor, r=60)                                        # carroceria
    p.chord((200, 70, 700, 330), 180, 360, cor)                                  # cúpula
    p.poli([(300, 195), (340, 110), (440, 98), (450, 195)], (60, 75, 100), ow=6)  # vidros
    p.poli([(470, 195), (470, 98), (570, 112), (620, 195)], (60, 75, 100), ow=6)
    p.poli([(335, 190), (360, 125), (385, 122), (362, 190)], (120, 140, 170), ow=0)
    p.elipse((690, 215, 770, 280), (255, 245, 190), ow=6)                         # farol
    p.ret((56, 235, 92, 275), (210, 50, 50), r=8, ow=5)
    p.ret((70, 305, 780, 338), (190, 190, 195), r=14, ow=5)                       # para-choque
    p.linha([(470, 200), (470, 310)], w=5)
    p.ret((430, 235, 465, 247), (120, 100, 40), r=5, ow=3)
    for x in (230, 640):
        p.elipse((x - 88, 255, x + 88, 420), (25, 25, 30), ow=0)
    _C[k] = p.pronto()
    return _C[k]


class Fusca:
    def __init__(self, cor=AMARELO):
        self.corpo = fusca(cor)
        self.roda = vco.roda()

    def desenhar(self, base, cx, by, escala=1.0, giro=0.0, pulo=0.0, espelhar=False, farol=False):
        c0 = self.corpo
        w, h = int(c0.width * escala), int(c0.height * escala)
        c = c0.resize((w, h), Image.BICUBIC)
        if espelhar:
            c = c.transpose(Image.FLIP_LEFT_RIGHT)
        x0, y0 = int(cx - w / 2), int(by - h - pulo)
        r = self.roda.rotate(-giro, resample=Image.BICUBIC).resize((int(164 * escala), int(164 * escala)))
        if farol:
            fx = (w * 0.12) if espelhar else (w * 0.9)
            base.alpha_composite(brilho((int(520 * escala), int(300 * escala)), (255, 240, 170),
                                        int(240 * escala), 0.7),
                                 (int(x0 + fx - 260 * escala * (0.3 if espelhar else 0.7) - (330 * escala if espelhar else 0)),
                                  int(y0 + h * 0.6 - 150 * escala)))
        base.alpha_composite(c, (x0, y0))
        for rx in (230, 640):
            xx = (820 - rx) if espelhar else rx
            base.alpha_composite(r, (int(x0 + (xx - 82) * escala), int(y0 + (338 - 82) * escala + pulo)))


class Taxi(vco.Carro):
    def __init__(self):
        super().__init__((245, 245, 248), (45, 55, 80))
        p = Pincel(900, 420)
        p.ret((390, 70, 540, 112), (250, 220, 60), r=8)
        p.ret((410, 82, 520, 98), (200, 120, 20), r=4, ow=0)
        spr = self.corpo.copy()
        spr.alpha_composite(p.pronto())
        pp = Pincel(900, 420)
        pp.ret((60, 255, 860, 278), (220, 60, 60), r=6, ow=0)           # faixa vermelha
        spr.alpha_composite(pp.pronto())
        self.corpo = spr


def adesivo(fc):
    p = Pincel(560, 210)
    p.ret((8, 8, 552, 202), (250, 245, 225), r=24, ow=8)
    p.ret((26, 26, 534, 184), (240, 90, 100), r=16, ow=0)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f1, f2 = vc.fonte(fc, 44), vc.fonte(fc, 64)
    for txt, f, y, cor in (("PRA MATERNIDADE", f1, 40, (255, 255, 255)), ("É DE GRAÇA", f2, 92, (255, 235, 120))):
        d.text((280 - f.getlength(txt) / 2, y), txt, font=f, fill=cor)
    return img


def envelope(fc=None):
    p = Pincel(420, 280)
    p.ret((10, 10, 410, 270), (245, 235, 205), r=14)
    p.poli([(10, 14), (210, 150), (410, 14)], (230, 215, 175), ow=6)
    p.linha([(10, 266), (160, 140)], fill=(210, 195, 155), w=4)
    p.linha([(410, 266), (260, 140)], fill=(210, 195, 155), w=4)
    p.elipse((190, 120, 230, 160), (200, 50, 50), ow=4)
    return p.pronto()


def maco_dinheiro(w=300):
    p = Pincel(300, 160)
    p.ret((20, 30, 280, 140), (100, 170, 100), r=10)
    p.ret((110, 20, 190, 150), (230, 220, 170), r=4, ow=5)
    p.elipse((130, 60, 170, 110), (250, 240, 200), ow=4)
    img = p.pronto()
    return img if w == 300 else img.resize((w, int(160 * w / 300)), Image.BICUBIC)


def polaroid(fc):
    p = Pincel(520, 620)
    p.ret((10, 10, 510, 610), (250, 247, 238), r=10, ow=8)
    p.ret((40, 40, 480, 470), (150, 200, 235), r=4, ow=5)
    p.ret((40, 380, 480, 470), (120, 170, 100), r=0, ow=0)
    img = p.pronto()
    f = fusca().resize((360, 184), Image.BICUBIC)
    img.alpha_composite(f, (70, 250))
    cab = g.desenhar_personagem(VELHO, "feliz", "idle", so_cabeca=True).crop((0, 0, 340, 310)).resize((170, 155),
                                                                                                    Image.BICUBIC)
    img.alpha_composite(cab, (300, 100))
    d = ImageDraw.Draw(img)
    f1 = vc.fonte(fc, 34)
    d.text((260 - f1.getlength("meu avô") / 2, 520), "meu avô", font=f1, fill=(90, 70, 60))
    return img


def barriga(m, cx, by, e, cor, t=0.0):
    k = 1 + 0.03 * math.sin(t * 5)
    p = Pincel(260, 220)
    p.elipse((20, 20, 240, 200), cor)
    img = p.pronto()
    w = int(260 * e * 0.62 * k)
    h = int(220 * e * 0.62 * k)
    img = img.resize((w, h), Image.BICUBIC)
    m.alpha_composite(img, (int(cx + 6 * e - w / 2), int(by - 292 * e - h / 2 + 90 * e)))


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def luzes_bokeh(base, n=26, seed=4, y0=300, y1=1000):
    rng = random.Random(seed)
    for _ in range(n):
        x, y = rng.randint(0, WW), rng.randint(y0, y1)
        cor = rng.choice([(255, 200, 120), (255, 120, 120), (140, 190, 255), (255, 240, 180)])
        r = rng.randint(30, 80)
        base.alpha_composite(brilho((r * 2, r * 2), cor, r, 0.55), (x - r, y - r))


def taxi_bg():
    base = gradiente(WW, WH, (18, 22, 50), (40, 36, 70))
    luzes_bokeh(base)
    p = Pincel(WW, WH)
    p.ret((-20, 1020, WW + 20, 1400), (30, 32, 50), r=0, ow=0)                 # asfalto distante
    base.alpha_composite(p.pronto())
    for x in (130, 500, 860):
        base.alpha_composite(brilho((400, 200), (255, 150, 120), 150, 0.35), (x - 200, 1050))
    return base


def taxi_fg(fc, t):
    """Painel do táxi (por cima dos personagens): volante, taxímetro e adesivo."""
    p = Pincel(WW, WH)
    p.ret((-20, 1420, WW + 20, WH + 20), (48, 50, 64), r=0)
    p.ret((-20, 1380, WW + 20, 1470), (70, 74, 92), r=30)
    p.elipse((330, 1500, 750, 1920), (30, 30, 38), ow=10)
    p.elipse((400, 1570, 680, 1850), (48, 50, 64), ow=8)
    p.ret((60, 1260, 320, 1390), (25, 28, 36), r=14)                           # taxímetro
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 56)
    d.text((190 - f.getlength("0,00") / 2, 1290), "0,00", font=f, fill=(255, 90, 80))
    return img


def limpador(f, t, fc):
    """Para-brisa com chuva e limpador."""
    d = ImageDraw.Draw(f, "RGBA")
    ang = -35 + 70 * (0.5 + 0.5 * math.sin(t * 2.4))
    cx, cy = OUT_W * 0.5, OUT_H * 0.84
    for L, a in ((330, ang), ):
        x = cx + L * math.sin(math.radians(a))
        y = cy - L * math.cos(math.radians(a))
        d.line((cx, cy, x, y), fill=(15, 15, 20, 230), width=7)
    vco.gotas(f, t, 50, (200, 215, 245))


def avenida_noite():
    base = gradiente(WW, WH, (16, 20, 46), (46, 40, 78))
    p = Pincel(WW, WH)
    rng = random.Random(21)
    for i in range(7):
        x = i * 170 - 40
        top = rng.randint(520, 900)
        p.ret((x, top, x + 160, 1400), rng.choice([(34, 38, 70), (40, 44, 80), (30, 34, 62)]), r=4, ow=0)
        for yy in range(top + 30, 1380, 70):
            for xx in (x + 25, x + 90):
                if rng.random() < 0.5:
                    p.ret((xx, yy, xx + 34, yy + 38), (255, 214, 120), r=3, ow=0)
    p.ret((-20, 1400, WW + 20, 1500), (70, 72, 90), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (44, 46, 60), r=0)
    for x in range(0, WW, 220):
        p.ret((x + 40, 1710, x + 150, 1730), (200, 190, 130), r=6, ow=0)
    for x in (80, 560):
        p.ret((x - 8, 1000, x + 8, 1410), (60, 60, 80), r=4)
        p.elipse((x - 30, 960, x + 30, 1020), (255, 235, 170), ow=4)
    base.alpha_composite(p.pronto())
    for x in (80, 560):
        base.alpha_composite(brilho((500, 500), (255, 220, 150), 250, 0.45), (x - 250, 730))
    for x in (160, 500, 840):                                                      # reflexos no asfalto
        base.alpha_composite(brilho((300, 700), (255, 200, 140), 140, 0.22), (x - 150, 1500))
    return base


def casa_noite():
    base = avenida_noite()
    p = Pincel(WW, WH)
    p.ret((60, 960, 560, 1410), (170, 130, 105), r=6)
    p.poli([(30, 970), (310, 760), (590, 970)], (110, 70, 70))
    p.ret((130, 1080, 230, 1210), (255, 214, 120), r=6, ow=6)
    p.ret((380, 1160, 470, 1410), (90, 60, 50), r=8)
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((380, 380), (255, 200, 120), 190, 0.5), (90, 1000))
    return base


def hospital_fachada(fc):
    base = gradiente(WW, WH, (16, 20, 46), (40, 44, 80))
    p = Pincel(WW, WH)
    p.ret((80, 520, 1000, 1420), (240, 240, 245), r=8)
    for r_ in range(3):
        for c in range(5):
            x, y = 130 + c * 180, 600 + r_ * 150
            p.ret((x, y, x + 100, y + 90), (255, 220, 140) if (r_ + c) % 3 else (60, 70, 110), r=6, ow=5)
    p.ret((400, 1130, 680, 1420), (200, 230, 250), r=10, ow=8)
    p.linha([(540, 1130), (540, 1420)], w=6)
    p.ret((300, 420, 780, 540), (220, 60, 70), r=12, ow=6)
    p.ret((508, 340, 572, 470), (255, 255, 255), r=4, ow=0)
    p.ret((470, 380, 610, 440), (255, 255, 255), r=4, ow=0)
    p.ret((-20, 1420, WW + 20, 1500), (110, 112, 128), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (50, 52, 68), r=0)
    base.alpha_composite(p.pronto())
    img = base
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 56)
    d.text((540 - f.getlength("MATERNIDADE") / 2, 450), "MATERNIDADE", font=f, fill=(255, 255, 255))
    base.alpha_composite(brilho((900, 700), (255, 230, 170), 420, 0.35), (90, 1000))
    return base


def ponto_taxi(fc):
    base = avenida_noite()
    p = Pincel(WW, WH)
    p.ret((470, 1000, 500, 1420), (120, 120, 135), r=4)
    p.ret((260, 930, 710, 1030), (250, 215, 60), r=12, ow=6)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 46)
    d.text((485 - f.getlength("PONTO DE TÁXI") / 2, 950), "PONTO DE TÁXI", font=f, fill=(40, 30, 20))
    return base


def porta_luvas_cena(fc, aberto=0.0):
    base = gradiente(WW, WH, (34, 34, 46), (22, 22, 32))
    p = Pincel(WW, WH)
    p.ret((60, 560, 1020, 1500), (62, 64, 82), r=40, ow=10)
    p.ret((110, 620, 970, 1440), (44, 46, 60), r=26, ow=6)
    base.alpha_composite(p.pronto())
    return base


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeTaxista(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.tx, self.txj = P_(TAXISTA), P_(TAXISTA_J)
        self.esp, self.grav, self.pai = P_(ESPOSA), P_(GRAVIDA), P_(PAI_ANSIOSO)
        self.velho = P_(VELHO)
        self.col1, self.col2 = P_(COLEGA1), P_(COLEGA2)
        self.blur = {}
        self.bg_taxi = taxi_bg()
        self.fg_taxi = taxi_fg(fc, 0)
        self.av = avenida_noite()
        self.casa = casa_noite()
        self.hosp = hospital_fachada(fc)
        self.ponto = ponto_taxi(fc)
        self.luvas = porta_luvas_cena(fc)
        self.taxi, self.fusca = Taxi(), Fusca()
        self.adesivo, self.env_img, self.dinheiro = adesivo(fc), envelope(), maco_dinheiro(240)
        self.foto = polaroid(fc)
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        P = [
            (0.00, self.p_hook, "", "corte"),
            (5.14, self.p_nenhuma, "", "corte"),
            (6.08, self.p_milduzentas, "", "zoom"),
            (8.14, self.p_banco_tras, "", "whip"),
            (13.56, self.p_pagar, "", "whip"),
            (16.04, self.p_adesivo, "", "corte"),
            (20.00, self.p_ponto, "", "whip"),
            (22.40, self.p_tres_carros, "", "corte"),
            (26.00, self.p_motivo, "", "zoom"),
            (27.94, self.p_31anos, "sepia", "dissolve"),
            (33.24, self.p_sem_carro, "sepia", "corte"),
            (34.64, self.p_acenando, "sepia", "whip"),
            (37.52, self.p_passou, "sepia", "corte"),
            (40.96, self.p_sete, "sepia", "corte"),
            (42.88, self.p_fusca_chega, "sepia", "whip"),
            (45.82, self.p_velho, "sepia", "corte"),
            (49.42, self.p_corre, "sepia", "whip"),
            (53.68, self.p_empurra, "sepia", "corte"),
            (59.94, self.p_embora, "sepia", "corte"),
            (61.02, self.p_procurei, "triste", "dissolve"),
            (64.32, self.p_envelope, "", "dissolve"),
            (69.22, self.p_3h, "", "whip"),
            (72.18, self.p_moca_entra, "", "corte"),
            (75.28, self.p_tenta_pagar, "", "whip"),
            (78.00, self.p_adesivo2, "", "corte"),
            (79.30, self.p_chora, "", "corte"),
            (82.90, self.p_foto, "quente", "zoom"),
            (84.80, self.p_abre, "", "corte"),
            (86.42, self.p_final, "quente", "dissolve"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))
        self.p_preto = None

    # ---------- utilidades ----------
    def dentro(self, t, quem, expr="neutro", pose="idle", x=540, by=1760, e=1.45, bg=None, vidro=True):
        m = (bg or self.bg_taxi).copy()
        quem(m, t, x, by, e, expr=expr, pose=pose)
        m.alpha_composite(self.fg_taxi)
        f = self.cam(m, 540, 1150, 1.1)
        if vidro:
            limpador(f, t, self.fc)
        return f

    def chuva_f(self, f, t, n=70, seed=7):
        d = ImageDraw.Draw(f, "RGBA")
        rng = random.Random(seed)
        for _ in range(n):
            x = rng.uniform(0, OUT_W)
            y = (rng.uniform(0, OUT_H) + t * rng.uniform(900, 1400)) % OUT_H
            d.line((x, y, x - 5, y + 30), fill=(200, 215, 245, 170), width=3)

    def legenda_balao(self, f, txt, x, y, t0):
        if self.T >= t0:
            self.balao(f, txt, x, y, self.T - t0)

    # ---------- planos ----------
    def p_hook(self, t, d):
        f = self.dentro(t, self.tx, expr="neutro", pose="idle")
        if self.T > 1.66:
            texto_pop(f, "30 ANOS DE TÁXI", self.fc, self.T - 1.66, OUT_W / 2, OUT_H * 0.12, 62, (255, 214, 40))
        return f

    def p_nenhuma(self, t, d):
        f = self.dentro(t, self.tx, expr="bravo" if t < 0.9 else "neutro", pose="aponta" if t > 0.4 else "idle")
        texto_pop(f, "NENHUMA.", self.fc, t, OUT_W / 2, OUT_H * 0.13, 100, (255, 120, 100))
        return f

    def p_milduzentas(self, t, d):
        m = self.bg_taxi.copy()
        m.alpha_composite(self.fg_taxi)
        f = self.cam(m, 200, 1330, 1.8 + 0.2 * ease_io(t / d))
        n = int(1200 * ease_out(min(1, t / 1.6)))
        texto_pop(f, f"{n:,}".replace(",", "."), self.fc, 0.3, OUT_W / 2, OUT_H * 0.35, 150, (255, 214, 40))
        texto_pop(f, "CORRIDAS GRÁTIS", self.fc, max(0, t - 0.5), OUT_W / 2, OUT_H * 0.5, 56, (255, 255, 255))
        return f

    def p_banco_tras(self, t, d):
        m = self.bg_taxi.copy()
        sh = 8 * math.sin(t * 22)
        self.pai(m, t, 330, 1760, 1.15, expr="surpreso", pose="bracos_abertos")
        self.grav(m, t, 760, 1760 + sh * 0.5, 1.2, expr="chora", pose="idle", rot=sh * 0.3)
        barriga(m, 760, 1760, 1.2, GRAVIDA["vestido"], t)
        m.alpha_composite(self.fg_taxi)
        f = self.cam(m, 540, 1150, 1.1)
        limpador(f, t, self.fc)
        if self.T > 12.9:
            texto_pop(f, "NA AVENIDA!", self.fc, self.T - 12.9, OUT_W / 2, OUT_H * 0.12, 70, (255, 120, 120))
        return f

    def p_pagar(self, t, d):
        m = self.hosp.copy()
        m.alpha_composite(self.fg_taxi.crop((0, 0, 1, 1)).resize((1, 1)), (0, 0))
        self.taxi.desenhar(m, 250, 1780, 0.75)
        self.pai(m, t, 700, 1780, 1.1, expr="feliz", pose="entrega")
        hx, hy = self.pai.a.maos_mundo[1]
        self.segura(m, self.dinheiro, hx + 40, hy - 20, 180, rot=-10)
        self.tx(m, t, 900, 1780, 1.05, expr="neutro", pose="idle")
        f = self.cam(m, 600, 1250, 1.12)
        self.chuva_f(f, t, 40)
        return f

    def p_adesivo(self, t, d):
        m = self.bg_taxi.copy()
        m.alpha_composite(self.fg_taxi)
        self.segura(m, self.adesivo, 560, 1330, 680 + 40 * ease_io(t / d))
        f = self.cam(m, 540, 1250, 1.1 + 0.3 * ease_io(t / d))
        return f

    def p_ponto(self, t, d):
        m = self.ponto.copy()
        ri = int(t * 8) % 2
        self.col1(m, t, 280, 1780, 1.1, expr="ri", pose="idle")
        self.col2(m, t + 1, 700, 1780, 1.1, expr="ri", pose="bate" if int(t * 3) % 2 else "idle")
        self.tx(m, t, 940, 1800, 1.0, expr="triste")
        self.taxi.desenhar(m, 200, 1500, 0.5)
        f = self.cam(m, 540, 1250, 1.12)
        self.chuva_f(f, t, 40)
        if self.T > 21.8:
            texto_pop(f, "\"LOUCO!\"", self.fc, self.T - 21.8, OUT_W / 2, OUT_H * 0.14, 80, (255, 255, 255))
        return f

    def p_tres_carros(self, t, d):
        m = gradiente(WW, WH, (40, 38, 66), (22, 20, 40))
        for i in range(3):
            tt = t - i * 0.35
            if tt < 0:
                continue
            k = ease_out(min(1, tt / 0.3))
            self.taxi.desenhar(m, 540, 760 + i * 380, 0.8 * k + 0.01, pulo=0)
        f = self.cam(m, 540, 1050, 1.05)
        texto_pop(f, "= 3 CARROS", self.fc, max(0, t - 0.4), OUT_W / 2, OUT_H * 0.1, 80, (255, 214, 40))
        return f

    def p_motivo(self, t, d):
        f = self.dentro(t, self.tx, expr="neutro", pose="idle", e=1.7)
        if self.T > 26.14:
            texto_pop(f, "?", self.fc, self.T - 26.14, OUT_W / 2, OUT_H * 0.14, 150, (255, 214, 40))
        return f

    def p_31anos(self, t, d):
        m = self.casa.copy()
        self.esp(m, t, 640, 1780, 1.15, expr="chora", pose="idle")
        barriga(m, 640, 1780, 1.15, ESPOSA["vestido"], t)
        self.txj(m, t, 900, 1780, 1.1, expr="surpreso", pose="bracos_abertos")
        f = self.cam(m, 600, 1250, 1.12)
        self.chuva_f(f, t, 80)
        texto_pop(f, "31 ANOS ATRÁS", self.fc, t, OUT_W / 2, OUT_H * 0.1, 78, (255, 214, 40))
        return f

    def p_sem_carro(self, t, d):
        m = self.casa.copy()
        self.txj(m, t, 360, 1800, 1.25, expr="triste", pose="bolso")
        self.esp(m, t, 720, 1800, 1.2, expr="chora")
        barriga(m, 720, 1800, 1.2, ESPOSA["vestido"], t)
        f = self.cam(m, 540, 1250, 1.12)
        self.chuva_f(f, t, 80)
        if self.T > 34.0:
            texto_pop(f, "SEM CARRO", self.fc, self.T - 34.0, OUT_W / 2, OUT_H * 0.12, 80, (255, 120, 120))
        return f

    def p_acenando(self, t, d):
        m = self.av.copy()
        self.txj(m, t, 540, 1800, 1.3, expr="surpreso", pose="acena")
        f = self.cam(m, 540, 1250, 1.15)
        self.chuva_f(f, t, 110)
        return f

    def taxis_passando(self, t, qtd, ini=0.0):
        m = self.av.copy()
        for i in range(qtd):
            x = 1500 - ((t - ini - i * 0.55) * 2300)
            if x < -700 or x > 1700:
                continue
            self.taxi.desenhar(m, x, 1760, 0.85, giro=t * 900, espelhar=True)
        return m

    def p_passou(self, t, d):
        T = self.T
        m = self.taxis_passando(t, 2, 0.15)
        self.txj(m, t, 200, 1800, 1.2, expr="surpreso" if (T % 1.6) < 0.8 else "triste", pose="acena")
        f = self.cam(m, 540, 1250, 1.1)
        self.chuva_f(f, t, 100)
        if T > 38.5:
            texto_pop(f, "NÃO PAROU", self.fc, T - 38.5, OUT_W / 2, OUT_H * 0.12, 72, (255, 140, 120))
        return f

    def p_sete(self, t, d):
        m = self.av.copy()
        for i in range(7):
            k = ease_out(min(1, max(0, (t - i * 0.2) / 0.3)))
            if k > 0:
                self.taxi.desenhar(m, 140 + (i % 4) * 280 + (110 if i > 3 else 0), 1560 + (i // 4) * 220, 0.36 * k,
                                   espelhar=True)
        self.txj(m, t, 540, 1830, 1.0, expr="triste", pose="idle")
        f = self.cam(m, 540, 1250, 1.1)
        self.chuva_f(f, t, 100)
        texto_pop(f, "7 TÁXIS", self.fc, max(0, t - 0.3), OUT_W / 2, OUT_H * 0.1, 90, (255, 214, 40))
        return f

    def p_fusca_chega(self, t, d):
        m = self.av.copy()
        x = 1500 - 1000 * ease_out(min(1, t / 1.7))
        self.txj(m, t, 210, 1800, 1.2, expr="surpreso" if t > 1.0 else "triste", pose="acena")
        self.fusca.desenhar(m, x, 1760, 0.95, giro=-t * 500 * (1 - min(1, t / 1.9)), espelhar=True, farol=True)
        f = self.cam(m, 600, 1250, 1.1)
        self.chuva_f(f, t, 100)
        return f

    def p_velho(self, t, d):
        m = self.av.copy()
        self.fusca.desenhar(m, 380, 1780, 1.25, espelhar=True, farol=False)
        self.velho(m, t, 860, 1800, 1.15, expr="feliz", pose="acena")
        f = self.cam(m, 600, 1300, 1.15)
        self.chuva_f(f, t, 70)
        self.legenda_balao(f, "Entra, filho.", OUT_W * 0.6, OUT_H * 0.2, 48.62)
        return f

    def p_corre(self, t, d):
        m = self.av.copy()
        for i in range(8):                                  # linhas de velocidade
            y = 1450 + i * 45
            xx = (-(t * 1800) + i * 330) % 1600 - 300
            ImageDraw.Draw(m).line((xx, y, xx + 240, y), fill=(255, 255, 255, 120), width=6)
        self.fusca.desenhar(m, 540, 1760, 1.2, giro=t * 1400, espelhar=True, pulo=5 * abs(math.sin(t * 30)))
        f = self.cam(m, 540 + 25 * math.sin(t * 20), 1300, 1.2)
        self.chuva_f(f, t, 110)
        if self.T > 51.34:
            texto_pop(f, "10 MINUTOS", self.fc, self.T - 51.34, OUT_W / 2, OUT_H * 0.12, 80, (255, 214, 40))
        return f

    def p_empurra(self, t, d):
        m = self.hosp.copy()
        self.fusca.desenhar(m, 190, 1780, 0.75, espelhar=True)
        self.velho(m, t, 520, 1780, 1.1, expr="feliz", pose="entrega")
        self.txj(m, t, 860, 1780, 1.1, expr="triste", pose="entrega")
        hx, hy = self.txj.a.maos_mundo[1]
        self.segura(m, self.dinheiro, hx - 60, hy - 20, 150, rot=10)
        f = self.cam(m, 560, 1250, 1.15)
        self.chuva_f(f, t, 60)
        self.legenda_balao(f, "Me paga quando ela", OUT_W * 0.58, OUT_H * 0.16, 57.6)
        if self.T > 58.46:
            texto_pop(f, "FIZER 18 ANOS", self.fc, self.T - 58.46, OUT_W / 2, OUT_H * 0.1, 66, (255, 214, 40))
        return f

    def p_embora(self, t, d):
        m = self.av.copy()
        x = 380 + 1300 * ease_in(t / d) if False else 380 + 1300 * ((t / d) ** 2)
        self.fusca.desenhar(m, x, 1760, 0.95, giro=t * 1200)
        self.txj(m, t, 240, 1800, 1.1, expr="triste", pose="acena")
        f = self.cam(m, 540, 1250, 1.1)
        self.chuva_f(f, t, 80)
        return f

    def p_procurei(self, t, d):
        m = self.av.copy()
        self.tx(m, t, 540 + 200 * math.sin(t * 0.9), 1800, 1.25, expr="triste", pose="anda")
        f = self.cam(m, 540, 1250, 1.12)
        self.chuva_f(f, t, 60)
        if self.T > 61.0:
            texto_pop(f, "PROCUREI POR ANOS", self.fc, self.T - 61.0, OUT_W / 2, OUT_H * 0.12, 60, (255, 255, 255))
        return f

    def p_envelope(self, t, d):
        m = self.luvas.copy()
        T = self.T
        k = ease_out(min(1, max(0, (T - 66.12) / 0.5)))
        self.segura(m, self.env_img, 540, 1120 + (1 - k) * 300, 620 * (0.4 + 0.6 * k))
        f = self.cam(m, 540, 1050, 1.0 + 0.25 * ease_io(t / d))
        if T > 66.12:
            texto_pop(f, "O ENVELOPE", self.fc, T - 66.12, OUT_W / 2, OUT_H * 0.14, 78, (255, 214, 40))
        return f

    def p_3h(self, t, d):
        m = self.av.copy()
        self.taxi.desenhar(m, 300 + 260 * ease_out(t / d), 1760, 0.9, giro=t * 700)
        f = self.cam(m, 540, 1250, 1.1)
        self.chuva_f(f, t, 110)
        texto_pop(f, "03:00", self.fc, t, OUT_W / 2, OUT_H * 0.13, 130, (120, 235, 255))
        return f

    def p_moca_entra(self, t, d):
        m = self.bg_taxi.copy()
        sh = 7 * math.sin(t * 22)
        self.tx(m, t, 330, 1760, 1.2, expr="surpreso", pose="idle")
        self.grav(m, t, 780, 1760 + sh * 0.4, 1.2, expr="chora", rot=sh * 0.3)
        barriga(m, 780, 1760, 1.2, GRAVIDA["vestido"], t)
        m.alpha_composite(self.fg_taxi)
        f = self.cam(m, 540, 1150, 1.1)
        limpador(f, t, self.fc)
        return f

    def p_tenta_pagar(self, t, d):
        m = self.hosp.copy()
        self.taxi.desenhar(m, 230, 1780, 0.7)
        self.tx(m, t, 600, 1780, 1.15, expr="feliz", pose="aponta")
        self.grav(m, t, 900, 1780, 1.1, expr="neutro", pose="entrega")
        barriga(m, 900, 1780, 1.1, GRAVIDA["vestido"], t)
        f = self.cam(m, 620, 1250, 1.12)
        self.chuva_f(f, t, 50)
        return f

    def p_adesivo2(self, t, d):
        return self.p_adesivo(t, d)

    def p_chora(self, t, d):
        return self.close(self.grav, t, self.hosp, "hosp", expr="chora", z=1.05)

    def p_foto(self, t, d):
        m = gradiente(WW, WH, (70, 55, 60), (35, 28, 34))
        T = self.T
        k = ease_out(min(1, max(0, (T - 82.9) / 0.4)))
        rot = 6 * math.sin(t * 1.5)
        im = self.foto.rotate(rot, expand=True, resample=Image.BICUBIC)
        w = int((880 * k) + 1)
        im = im.resize((w, int(im.height * w / im.width) + 1), Image.BICUBIC)
        m.alpha_composite(im, (540 - im.width // 2, 980 - im.height // 2))
        f = self.cam(m, 540, 1000, 1.0 + 0.1 * ease_io(t / d))
        self.balao(f, "Ele tinha um Fusca amarelo.", OUT_W / 2, OUT_H * 0.12, max(0, T - 82.9)) if T > 82.9 else None
        return f

    def p_abre(self, t, d):
        m = self.luvas.copy()
        T = self.T
        k = ease_out(min(1, max(0, (T - 85.2) / 0.5)))
        m.alpha_composite(brilho((900, 900), (255, 235, 160), 420, 0.6 * k), (90, 620))
        self.segura(m, self.env_img, 540, 1100, 640)
        f = self.cam(m, 540, 1050, 1.1 + 0.25 * ease_io(t / d))
        particulas(f, t, 40, cor=(255, 235, 160), semente=3)
        return f

    def p_final(self, t, d):
        m = gradiente(WW, WH, (255, 190, 130), (250, 225, 190))
        p = Pincel(WW, WH)
        p.elipse((380, 820, 700, 1140), (255, 235, 150), ow=0)
        p.ret((-20, 1500, WW + 20, WH + 20), (200, 185, 170), r=0)
        m.alpha_composite(p.pronto())
        T = self.T
        k = ease_out(min(1, t / 1.0))
        self.tx(m, t, 360, 1800, 1.25, expr="chora" if T > 88.8 else "feliz", pose="entrega")
        hx, hy = self.tx.a.maos_mundo[1]
        self.segura(m, self.env_img, hx + 50, hy - 10, 250 * k + 1, rot=-12)
        self.grav(m, t, 780, 1800, 1.2, expr="chora" if T < 89.5 else "feliz", pose="idle")
        barriga(m, 780, 1800, 1.2, GRAVIDA["vestido"], t)
        f = self.cam(m, 560, 1250, 1.1 + 0.08 * ease_io(t / d))
        particulas(f, t, 50, cor=(255, 240, 200), semente=6)
        if T > 90.14:
            texto_pop(f, "CORRIDA PAGA.", self.fc, T - 90.14, OUT_W / 2, OUT_H * 0.12, 74, (255, 255, 255))
        return f


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
    # chuva constante (ruído suave filtrado)
    rng = np.random.default_rng(5)
    ruido = rng.standard_normal(n).astype(np.float32)
    k = np.ones(40, np.float32) / 40
    chuva = np.convolve(ruido, k, mode="same") * 0.05
    chuva[int(61.0 * SR):int(64.3 * SR)] *= 0.3
    chuva[int(84.8 * SR):] *= 0.15
    mix += chuva
    ev = filme.eventos_sfx()
    ev += [("toc", 5.14), ("brilho", 6.08), ("pop", 16.04), ("brilho", 26.14), ("whoosh", 37.7), ("whoosh", 39.3),
           ("pop", 41.4), ("brilho", 42.88), ("brilho", 66.12), ("toc", 78.0), ("brilho", 82.9),
           ("brilho", 85.2), ("brilho", 90.14)]
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
    pal = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            pal.append(dict(w=w["w"], s=w["s"], e=w["e"]))
    out, i = [], 0
    while i < len(pal):
        w = pal[i]
        if w["w"] == "1" and i + 1 < len(pal) and pal[i + 1]["w"] == ".200":
            out.append(dict(w="1.200", s=w["s"], e=pal[i + 1]["e"]))
            i += 2
            continue
        if w["w"] == "porta" and i + 1 < len(pal) and pal[i + 1]["w"].startswith("-luvas"):
            out.append(dict(w="porta-luvas" + pal[i + 1]["w"][6:], s=w["s"], e=pal[i + 1]["e"]))
            i += 2
            continue
        txt = {"grave": "grávida", "taxis": "táxis", "fusca": "Fusca"}.get(w["w"], w["w"])
        out.append(dict(w=txt, s=w["s"], e=w["e"]))
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_taxista.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeTaxista(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.4, a.narracao)
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

    tmp = tempfile.mkdtemp(prefix="taxista_")
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
