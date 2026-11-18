#!/usr/bin/env python3
"""
"A Chuva que Sobe" — cidade onde a chuva cai pra cima… porque a cidade é uma gota caindo.

Animação: chuva subindo/descendo em partículas, nuvens no chão, guarda-chuva no pé, poça no teto,
o Lago do Céu crescendo, a Bia subindo dentro do guarda-chuva, a revelação da gota-cidade caindo
sobre o mar, mil guarda-chuvas abrindo, a gota freando e pousando numa flor, e o céu cheio de
gotas-cidades.

    python3 animacao/video_chuva.py --narracao narr.wav --transcricao transcricao.json --fonte Poppins.ttf
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
import video_estatua as ve  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, gradiente, brilho,
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(202)

BIA = dict(pele=(196, 140, 100), cabelo=(40, 28, 22), camisa=(150, 90, 200), calca=(0, 0, 0),
           sapato=(250, 200, 60), tipo="moca", vestido=(150, 90, 200))
DALVA = dict(pele=(222, 175, 140), cabelo=(225, 225, 230), camisa=(250, 210, 50), calca=(0, 0, 0),
             sapato=(60, 110, 200), tipo="vovo", vestido=(250, 210, 50))
DALVA_SEM = dict(DALVA, camisa=(240, 140, 160), vestido=(240, 140, 160))
LAURO = dict(pele=(196, 140, 100), cabelo=(60, 45, 35), camisa=(90, 150, 90), calca=(90, 80, 70),
             sapato=(60, 50, 45), tipo="pai", chapeu=(200, 180, 120))
PREFEITO = dict(pele=(232, 186, 150), cabelo=(70, 60, 55), camisa=(45, 50, 70), calca=(40, 45, 60),
                sapato=(30, 30, 30), tipo="pai", bigode=False, gravata=(200, 40, 40))
POVO = ve.POVO
AZUL = (110, 190, 255)
vc.DESTAQUE_VERMELHO = set()


# --------------------------------------------------------------------------
# Objetos
# --------------------------------------------------------------------------
_CACHE = {}


def guarda_chuva(cor=(220, 60, 60), w=420):
    k = ("gc", cor, w)
    if k in _CACHE:
        return _CACHE[k]
    p = Pincel(w, w * 1.05)
    c = w / 2
    p.chord((10, 30, w - 10, w * 0.62), 180, 360, cor)
    for i in range(1, 4):
        x = 10 + i * (w - 20) / 4
        p.linha([(c, 40), (x, w * 0.31)], fill=tuple(max(0, v - 50) for v in cor), w=5)
    for i in range(4):
        x0 = 10 + i * (w - 20) / 4
        p.chord((x0, w * 0.26, x0 + (w - 20) / 4, w * 0.36), 0, 180, cor, ow=5)
    p.linha([(c, w * 0.31), (c, w * 0.95)], w=10)
    p.arco((c - 50, w * 0.88, c + 4, w * 1.02), 0, 180, w=10)
    img = p.pronto()
    _CACHE[k] = img
    return img


def nuvem_chao(w=700):
    p = Pincel(w, w * 0.5)
    for dx, dy, r in ((0.2, 0.62, 0.17), (0.38, 0.45, 0.22), (0.6, 0.5, 0.2), (0.8, 0.62, 0.16), (0.5, 0.7, 0.2)):
        p.elipse((w * (dx - r), w * 0.5 * dy - w * r * 0.9, w * (dx + r), w * 0.5 * dy + w * r * 0.9),
                 (250, 250, 255), ow=0)
    return p.pronto()


def peixe(w=260):
    p = Pincel(w, w * 0.6)
    p.elipse((40, 20, w - 30, w * 0.55), (240, 140, 60))
    p.poli([(50, w * 0.3), (0, 10), (0, w * 0.55)], (240, 140, 60))
    p.elipse((w - 90, 50, w - 66, 74), OUTLINE, ow=0)
    return p.pronto()


def pipa(w=320, camera_=True):
    p = Pincel(w, w * 1.6)
    c = w / 2
    p.poli([(c, 10), (w - 20, w * 0.45), (c, w * 0.95), (20, w * 0.45)], (240, 90, 80))
    p.linha([(c, 10), (c, w * 0.95)], fill=(180, 60, 50), w=5)
    p.linha([(20, w * 0.45), (w - 20, w * 0.45)], fill=(180, 60, 50), w=5)
    for i in range(4):
        y = w * 0.95 + i * 70
        p.linha([(c, y), (c + (20 if i % 2 else -20), y + 70)], fill=(80, 80, 80), w=4)
        p.elipse((c - 18, y + 30, c + 18, y + 60), (250, 210, 60), ow=3)
    if camera_:
        p.ret((c - 50, w * 0.35, c + 50, w * 0.55), (40, 40, 45), r=10)
        p.elipse((c - 20, w * 0.39, c + 20, w * 0.51), (120, 170, 220), ow=4)
    return p.pronto()


def xicara(w=160):
    p = Pincel(w, w)
    p.ret((20, 40, w - 50, w - 30), (250, 250, 250), r=16)
    p.arco((w - 80, 60, w - 20, 120), -90, 90, w=10)
    p.ret((0, w - 30, w - 30, w - 14), (250, 250, 250), r=6)
    return p.pronto()


def flor(w=900):
    k = ("flor", w)
    if k in _CACHE:
        return _CACHE[k]
    p = Pincel(w, w * 1.2)
    c = w / 2
    p.capsula((c, w * 0.5), (c, w * 1.18), 40, (90, 170, 80))
    for i in range(8):
        a = math.radians(i * 45)
        x, y = c + w * 0.27 * math.cos(a), w * 0.42 + w * 0.2 * math.sin(a)
        p.elipse((x - w * 0.16, y - w * 0.1, x + w * 0.16, y + w * 0.1), (250, 150, 190))
    p.elipse((c - w * 0.12, w * 0.32, c + w * 0.12, w * 0.52), (250, 210, 60))
    img = p.pronto()
    _CACHE[k] = img
    return img


def gota_cidade(w=500, gc=0, errado=True, cor_gc=(220, 60, 60)):
    """Gota transparente com uma cidadezinha dentro (de cabeça pra baixo) e guarda-chuvas."""
    k = ("gota", w, gc, errado)
    if k in _CACHE:
        return _CACHE[k]
    h = int(w * 1.3)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    p = Pincel(w, h)
    c = w / 2
    cy = h * 0.6
    r = w * 0.45
    p.poli([(c, 6), (c + r * 0.55, cy - r * 0.8), (c - r * 0.55, cy - r * 0.8)], (170, 215, 255, 255), ow=6)
    p.elipse((c - r, cy - r, c + r, cy + r), (170, 215, 255), ow=6)
    # cidade de cabeça pra baixo (pendurada no "chão", que fica em cima)
    cores = g.CORES_CASAS
    for i in range(5):
        x = c - r * 0.75 + i * r * 0.36
        hh = r * (0.35 + 0.15 * (i % 2))
        p.ret((x, cy - r * 0.15, x + r * 0.3, cy - r * 0.15 + hh), cores[i % 6], r=4, ow=4)
    p.ret((c - r * 0.85, cy - r * 0.25, c + r * 0.85, cy - r * 0.12), (120, 160, 110), r=4, ow=4)
    img.alpha_composite(p.pronto())
    # brilho
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse((c - r * 0.6, cy - r * 0.75, c - r * 0.2, cy - r * 0.4), fill=(255, 255, 255, 170))
    if gc:
        gu = guarda_chuva(cor_gc, int(w * 0.16))
        if errado:
            gu = gu.rotate(180, expand=True)
        for i in range(gc):
            a = math.radians(200 + i * (140 / max(1, gc - 1)))
            x, y = c + r * 0.95 * math.cos(a), cy + r * 0.95 * math.sin(a)
            img.alpha_composite(gu, (int(x - gu.width / 2), int(y - gu.height / 2)))
    _CACHE[k] = img
    return img


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def cidade(fc, noite=False, nuvens=True, lago=1.0):
    base = gradiente(WW, WH, (30, 40, 80) if noite else (140, 190, 235),
                     (70, 70, 110) if noite else (215, 230, 245))
    if lago > 0:     # o Lago do Céu (brilho azul no alto)
        r = int(220 * lago)
        base.alpha_composite(brilho((r * 4, r * 4), (120, 200, 255), r * 2, 0.95), (540 - r * 2, -r * 2 + 120))
        p0 = Pincel(WW, WH)
        p0.elipse((540 - r, 140 - r * 0.5, 540 + r, 140 + r * 0.5), (50, 130, 230), ow=6)
        p0.elipse((540 - r * 0.7, 140 - r * 0.3, 540 + r * 0.7, 140 + r * 0.3), (90, 170, 245), ow=0)
        for k in range(3):
            p0.arco((540 - r * 0.5 + k * 40, 120, 540 - r * 0.1 + k * 40, 160), 200, 340, fill=(220, 240, 255), w=6)
        base.alpha_composite(p0.pronto())
    p = Pincel(WW, WH)
    cores = g.CORES_CASAS
    for i, x in enumerate((-40, 250, 540, 830)):
        top = 760 + (i % 2) * 70
        p.ret((x, top, x + 280, 1420), cores[i % 6], r=6)
        p.poli([(x - 15, top + 4), (x + 140, top - 150), (x + 295, top + 4)], (160, 85, 75))
        p.ret((x + 50, top + 90, x + 130, top + 200), (255, 240, 200) if not noite else (250, 210, 120), r=8, ow=6)
        p.ret((x + 160, top + 90, x + 240, top + 200), (255, 240, 200) if not noite else (250, 210, 120), r=8, ow=6)
    p.ret((-20, 1410, WW + 20, 1500), (200, 190, 175), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (90, 90, 100), r=0)
    base.alpha_composite(p.pronto())
    if nuvens:
        n = nuvem_chao(520)
        for x in (-120, 380, 820):
            base.alpha_composite(n, (x, 1600))
    return base


def sala(noite=False):
    base = gradiente(WW, WH, (60, 60, 95) if noite else (240, 225, 200), (80, 75, 110) if noite else (225, 210, 185))
    p = Pincel(WW, WH)
    p.ret((-20, -20, WW + 20, 260), (200, 190, 175) if not noite else (90, 85, 110), r=0)
    p.elipse((260, 160, 820, 300), (110, 180, 240), ow=6)                      # poça no teto
    p.ret((-20, 1420, WW + 20, WH + 20), (170, 130, 100) if not noite else (90, 75, 80), r=0)
    p.ret((200, 1300, 880, 1360), (150, 100, 70), r=10)
    p.ret((240, 1360, 280, 1600), (130, 85, 60), r=6)
    p.ret((800, 1360, 840, 1600), (130, 85, 60), r=6)
    base.alpha_composite(p.pronto())
    return base


def ceu_aberto(mar=0.0, noite=False):
    """Céu de verdade, com o mar embaixo (cresce com 'mar')."""
    base = gradiente(WW, WH, (20, 25, 60) if noite else (120, 180, 240), (60, 80, 140) if noite else (200, 225, 250))
    p = Pincel(WW, WH)
    if not noite:
        vc.nuvem(p, 120, 300, 1.0)
        vc.nuvem(p, 700, 520, 0.8)
    h = int(300 + 900 * mar)
    p.ret((-20, WH - h, WW + 20, WH + 20), (40, 110, 190), r=0, ow=0)
    for y in range(WH - h + 30, WH, 70):
        p.linha([(80, y), (380, y)], fill=(110, 170, 230), w=6)
        p.linha([(600, y + 30), (980, y + 30)], fill=(110, 170, 230), w=6)
    base.alpha_composite(p.pronto())
    return base


def praia(noite=False):
    base = gradiente(WW, WH, (25, 30, 70) if noite else (140, 195, 245), (70, 70, 120) if noite else (230, 240, 250))
    p = Pincel(WW, WH)
    if noite:
        rng = random.Random(5)
        for _ in range(60):
            x, y = rng.uniform(0, WW), rng.uniform(0, 900)
            p.elipse((x - 3, y - 3, x + 3, y + 3), (255, 255, 230), ow=0)
    p.ret((-20, 1200, WW + 20, 1500), (40, 110, 190), r=0, ow=0)
    p.ret((-20, 1480, WW + 20, WH + 20), (240, 215, 160), r=0)
    base.alpha_composite(p.pronto())
    return base


def chuva(f, t, dirc=-1, n=70, cor=(200, 230, 255), vel=1400, seed=7):
    """Gotas como riscos: dirc=-1 sobem, +1 descem."""
    d = ImageDraw.Draw(f, "RGBA")
    rng = random.Random(seed)
    for _ in range(n):
        x = rng.uniform(0, OUT_W)
        y0 = rng.uniform(0, OUT_H)
        y = (y0 + dirc * t * vel * rng.uniform(0.6, 1.0)) % OUT_H
        d.line((x, y, x + 3, y + 26 * dirc * -1), fill=cor + (200,), width=4)


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeChuva(ve.FilmeEstatua):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.bia, self.dalva, self.dalva_sem = P_(BIA), P_(DALVA), P_(DALVA_SEM)
        self.lauro, self.pref = P_(LAURO), P_(PREFEITO)
        self.povo = [P_(c) for c in POVO]
        self.blur = {}
        self.cid = {k: cidade(fc, lago=k) for k in (1.0, 1.25, 1.5)}
        self.cid_noite = cidade(fc, noite=True, lago=1.2)
        self.sala_d, self.sala_n = sala(), sala(True)
        self.gc_vermelho, self.gc_amarelo, self.gc_azul = (guarda_chuva((220, 60, 60)), guarda_chuva((250, 200, 50)),
                                                           guarda_chuva((70, 130, 220)))
        self.peixe, self.pipa_img, self.xic = peixe(), pipa(), xicara()
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.FALA_DALVA = [(48.40, 52.4), (57.88, 59.2)]
        self.FALA_BIA = [(103.18, 105.3)]
        self.TREMORES = [(53.9, 10), (54.24, 12), (84.86, 6), (115.28, 5)]

        P = [
            (0.00, self.p_hook, "", "corte"),
            (2.74, self.p_nuvens, "", "whip"),
            (7.42, self.p_guarda_pe, "", "corte"),
            (11.40, self.p_poca, "", "corte"),
            (13.26, self.p_cabelo, "", "corte"),
            (16.48, self.p_lauro, "", "whip"),
            (22.66, self.p_lago, "", "zoom"),
            (31.62, self.p_bia, "", "whip"),
            (38.40, self.p_pipa, "", "corte"),
            (41.64, self.p_foto, "", "corte"),
            (44.94, self.p_vo, "", "whip"),
            (53.06, self.p_tremor, "", "dissolve"),
            (57.88, self.p_mergulharam, "", "corte"),
            (59.38, self.p_lago_maior, "", "zoom"),
            (63.40, self.p_sabado, "", "whip"),
            (69.60, self.p_sobe, "", "corte"),
            (77.46, self.p_olha, "", "corte"),
            (80.18, self.p_mar, "", "zoom"),
            (84.86, self.p_gota, "", "zoom"),
            (87.94, self.p_por_isso, "", "corte"),
            (91.10, self.p_chegando, "", "corte"),
            (93.50, self.p_vento, "", "corte"),
            (95.16, self.p_oceano, "", "corte"),
            (98.92, self.p_desce, "", "whip"),
            (103.18, self.p_abram, "", "corte"),
            (105.86, self.p_abrem, "", "corte"),
            (110.46, self.p_mil, "", "corte"),
            (115.28, self.p_freia, "", "zoom"),
            (117.72, self.p_pousa, "", "corte"),
            (122.70, self.p_sem_estourar, "quente", "corte"),
            (123.90, self.p_chuva_baixo, "quente", "whip"),
            (127.88, self.p_vo_capa, "quente", "corte"),
            (132.28, self.p_lauro_volta, "quente", "corte"),
            (136.18, self.p_noite_flor, "", "dissolve"),
            (140.34, self.p_gotas_cidades, "", "zoom"),
            (145.96, self.p_erradas, "", "corte"),
            (148.32, self.p_bilhete, "", "corte"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))
        self.p_preto = None

    # ---------- utilidades ----------
    def cam(self, m, cx, cy, z):
        dx = dy = 0.0
        for tg, a in self.TREMORES:
            dt = self.T - tg
            if 0 <= dt < 0.6:
                k = a * (1 - dt / 0.6)
                dx, dy = k * math.sin(self.T * 90), k * math.cos(self.T * 70)
        return camera(m, cx + dx, cy + dy, z)

    def lago_k(self):
        """O Lago do Céu cresce ao longo da história."""
        T = self.T
        return 1.0 if T < 59 else (1.25 if T < 70 else 1.5)

    def cid_img(self):
        return self.cid[self.lago_k()].copy()

    # ------------------------- planos -------------------------
    def p_hook(self, t, d):
        m = self.cid_img()
        for i, (p, x) in enumerate(zip(self.povo[:3], (220, 540, 860))):
            p(m, t + i, x, 1780, 1.0, expr="surpreso")
        f = self.cam(m, 540, 1150, 1.1 - 0.05 * ease_io(t / d))
        chuva(f, t, -1, 90)
        texto_pop(f, "A CHUVA CAI PRA CIMA", self.fc, t, OUT_W / 2, OUT_H * 0.12, 58, AZUL)
        return f

    def p_nuvens(self, t, d):
        m = self.cid_img()
        m.alpha_composite(nuvem_chao(900), (90, 1450))
        f = self.cam(m, 540, 1500, 1.4 - 0.25 * ease_io(t / d))
        chuva(f, t, -1, 70)
        if t > 2.0:
            texto_pop(f, "NUVEM NO CHÃO", self.fc, t - 2.0, OUT_W / 2, OUT_H * 0.12, 64, (255, 255, 255))
        return f

    def p_guarda_pe(self, t, d):
        m = self.cid_img()
        gu = self.gc_vermelho.rotate(180, expand=True)
        m.alpha_composite(gu.resize((380, 400)), (350, 1500))
        self.povo[1](m, t, 540, 1560, 1.0, expr="feliz")
        f = self.cam(m, 540, 1300, 1.25)
        chuva(f, t, -1, 60)
        texto_pop(f, "NO PÉ", self.fc, t, OUT_W * 0.75, OUT_H * 0.7, 70, (255, 214, 40))
        return f

    def p_poca(self, t, d):
        m = self.sala_d.copy()
        self.povo[2](m, t, 540, 1780, 1.1, expr="surpreso", pose="aponta")
        f = self.cam(m, 540, 900, 1.15)
        dr = ImageDraw.Draw(f)
        for i in range(6):                     # gotas subindo do chão até a poça do teto
            k = (t * 1.2 + i / 6) % 1.0
            x = OUT_W * (0.3 + 0.08 * i)
            y = OUT_H * (0.9 - 0.75 * k)
            dr.ellipse((x - 8, y - 12, x + 8, y + 12), fill=AZUL)
        return f

    def p_cabelo(self, t, d):
        m = self.sala_d.copy()
        spr = self.povo[3].spr("ri", "idle").rotate(90, expand=True)
        g.colar(m, spr, 540, 1700, 1.0)
        f = self.cam(m, 540, 1400, 1.3)
        chuva(f, t, -1, 40, seed=3)
        dr = ImageDraw.Draw(f, "RGBA")
        for i in range(8):                     # espuminha
            x = OUT_W * 0.3 + 30 * math.sin(t * 3 + i) + i * 12
            y = OUT_H * 0.62 - (t * 80 + i * 30) % 160
            dr.ellipse((x - 14, y - 14, x + 14, y + 14), outline=(255, 255, 255, 220), width=4)
        return f

    def p_lauro(self, t, d):
        m = self.cid_img()
        sobe = ease_io(min(1, max(0, t - 2.8) / 2.6))
        y = 1780 - 1200 * sobe
        self.lauro(m, t, 540, y, 1.0, expr="surpreso" if sobe > 0 else "feliz", pose="entrega" if sobe == 0 else "acena")
        fy = 1000 - 1200 * sobe if sobe > 0 else 1000 - 300 * ease_out(t / 2.8)
        self.segura(m, self.peixe, 700, fy, 220, rot=20 * math.sin(t * 6))
        p = Pincel(WW, WH)
        p.linha([(620, y - 380), (700, fy)], fill=(60, 60, 60), w=4)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, max(700, y - 450), 1.15)
        chuva(f, t, -1, 60)
        if t > 4.4:
            texto_pop(f, "TCHAU!", self.fc, t - 4.4, OUT_W * 0.7, OUT_H * 0.2, 60, (255, 255, 255))
        return f

    def p_lago(self, t, d):
        m = self.cid_img()
        f = self.cam(m, 540, 700 - 300 * ease_io(t / d), 1.0 + 0.4 * ease_io(t / d))
        chuva(f, t, -1, 80)
        if self.T > 28.88:
            texto_pop(f, "O LAGO DO CÉU", self.fc, self.T - 28.88, OUT_W / 2, OUT_H * 0.45, 80, (255, 255, 255))
        if self.T > 30.12:
            texto_pop(f, "?", self.fc, self.T - 30.12, OUT_W / 2, OUT_H * 0.56, 140, (255, 214, 40))
        return f

    def p_bia(self, t, d):
        m = self.fundo_blur("cid", self.cid[1.0])
        if self.T > 35.4:
            n = nuvem_chao(700)
            m.alpha_composite(n, (190, 1080 + int(10 * math.sin(t * 2))))
        self.bia(m, t, 540, 2350, 2.5, expr="feliz" if self.T < 37.9 else "neutro")
        f = self.cam(m, 540, 950, 1.05)
        texto_pop(f, "BIA, 10 ANOS", self.fc, t, OUT_W / 2, OUT_H * 0.1, 64, (255, 214, 40))
        if self.T > 35.48:
            texto_pop(f, "LITERALMENTE", self.fc, self.T - 35.48, OUT_W / 2, OUT_H * 0.18, 50, (255, 255, 255))
        return f

    def p_pipa(self, t, d):
        m = self.cid_img()
        k = ease_out(min(1, t / d))
        self.bia(m, t, 300, 1800, 1.1, expr="feliz", pose="acena")
        px, py = 300 + 400 * k, 1100 - 900 * k
        p = Pincel(WW, WH)
        p.linha([(360, 1180), (px, py + 150)], fill=(80, 80, 80), w=3)
        m.alpha_composite(p.pronto())
        self.segura(m, self.pipa_img, px, py, 220, rot=10 * math.sin(t * 3))
        f = self.cam(m, 500, 1100 - 300 * k, 1.1)
        chuva(f, t, -1, 40)
        return f

    def p_foto(self, t, d):
        m = gradiente(WW, WH, (60, 60, 80), (35, 35, 50))
        p = Pincel(WW, WH)
        p.ret((190, 520, 890, 1380), (250, 250, 250), r=12)
        p.ret((240, 570, 840, 1170), (110, 190, 250), r=4, ow=0)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 950, 1.05 + 0.1 * ease_io(t / d))
        texto_pop(f, "MAIS AZUL", self.fc, t, OUT_W / 2, OUT_H * 0.68, 60, (60, 60, 80))
        return f

    def p_vo(self, t, d):
        m = self.cid_img()
        self.dalva(m, t, 380, 1780, 1.2, expr="feliz", pose="aponta", fala=self.FALA_DALVA)
        self.bia(m, t, 760, 1800, 1.0, expr="surpreso")
        f = self.cam(m, 540, 1250, 1.12)
        chuva(f, t, -1, 40)
        if self.T > 49.2:
            texto_pop(f, "PISCINA DOS ANJOS", self.fc, self.T - 49.2, OUT_W / 2, OUT_H * 0.12, 56, (255, 255, 255))
        return f

    def p_tremor(self, t, d):
        m = self.sala_n.copy()
        for i, x in enumerate((320, 540, 760)):
            dx = 8 * math.sin(self.T * 60 + i) if 53.9 < self.T < 55.2 else 0
            self.segura(m, self.xic, x + dx, 1250, 150, rot=dx)
        f = self.cam(m, 540, 900, 1.1)
        dr = ImageDraw.Draw(f)
        if self.T > 55.4:                       # poças pingando pro lado
            for i in range(6):
                k = ((t - 2.3) * 1.5 + i / 6) % 1.0
                dr.ellipse((OUT_W * (0.35 + 0.5 * k) - 8, OUT_H * (0.2 + 0.02 * i) - 12,
                            OUT_W * (0.35 + 0.5 * k) + 8, OUT_H * (0.2 + 0.02 * i) + 12), fill=AZUL)
        return f

    def p_mergulharam(self, t, d):
        return self.close(self.dalva, t, self.cid[1.0], "cid", expr="feliz", fala=self.FALA_DALVA)

    def p_lago_maior(self, t, d):
        m = self.cid_img()
        f = self.cam(m, 540, 600, 1.4)
        chuva(f, t, -1, 60)
        texto_pop(f, "MAIOR", self.fc, t, OUT_W / 2, OUT_H * 0.55, 90, (255, 214, 40))
        if self.T > 61.34:
            texto_pop(f, "TODO DIA", self.fc, self.T - 61.34, OUT_W / 2, OUT_H * 0.64, 60, (255, 255, 255))
        return f

    def p_sabado(self, t, d):
        m = self.cid_img()
        aberto = self.T > 65.6
        self.bia(m, t, 540, 1800, 1.15, expr="bravo" if aberto else "neutro", pose="acena" if aberto else "idle")
        if aberto:
            m.alpha_composite(self.gc_amarelo.rotate(180, expand=True).resize((380, 400)), (380, 960))
        f = self.cam(m, 540, 1250, 1.12)
        chuva(f, t, -1, 150, vel=2200)
        if self.T > 68.3:
            ImageDraw.Draw(f, "RGBA").ellipse((OUT_W * 0.33, OUT_H * 0.3, OUT_W * 0.67, OUT_H * 0.36),
                                               fill=(120, 190, 250, 200))
        return f

    def p_sobe(self, t, d):
        k = ease_io(min(1, t / d))
        m = gradiente(WW, WH, (140, 190, 235), (215, 230, 245))
        # cidade lá embaixo encolhendo até virar uma bolinha
        esc = 1.0 - 0.85 * k
        cid = self.cid[1.5].resize((int(WW * esc), int(WH * esc)))
        if k > 0.6:
            msk = Image.new("L", cid.size, 0)
            ImageDraw.Draw(msk).ellipse((0, 0, cid.width, cid.height), fill=255)
            cid.putalpha(msk)
        m.alpha_composite(cid, (int(540 - cid.width / 2), int(WH - cid.height * (0.7 + 0.3 * k))))
        gu = self.gc_amarelo.rotate(180, expand=True).resize((300, 316))
        m.alpha_composite(gu, (390, 520))
        self.bia(m, t, 540, 600, 0.6, expr="ri" if k < 0.7 else "surpreso", pose="acena")
        f = self.cam(m, 540, 900, 1.05)
        chuva(f, t, -1, 60)
        if 72.96 < self.T < 73.6:
            texto_pop(f, "DADOS", self.fc, self.T - 72.96, OUT_W / 2, OUT_H * 0.82, 60, (255, 255, 255))
        elif self.T > 75.4:
            texto_pop(f, "BOLINHA", self.fc, self.T - 75.4, OUT_W / 2, OUT_H * 0.82, 60, (255, 255, 255))
        return f

    def p_olha(self, t, d):
        m = gradiente(WW, WH, (140, 190, 235), (215, 230, 245))
        self.bia(m, t, 540, 2350, 2.5, expr="surpreso", piscar=False)
        return self.cam(m, 540, 950, 1.05 + 0.2 * ease_out(t / 0.4))

    def p_mar(self, t, d):
        T = self.T
        mar = 0.4 if T < 82.38 else 0.4 + 0.3 * ease_out((T - 82.38) / 1.0)
        m = ceu_aberto(mar)
        f = self.cam(m, 540, 1100, 1.05)
        if T < 81.76:
            texto_pop(f, "SEM PISCINA", self.fc, t, OUT_W / 2, OUT_H * 0.14, 60, (255, 255, 255))
        if T > 81.36:
            texto_pop(f, "SEM ANJO", self.fc, T - 81.36, OUT_W / 2, OUT_H * 0.22, 60, (255, 255, 255))
        if T > 83.36:
            texto_pop(f, "ERA O MAR", self.fc, T - 83.36, OUT_W / 2, OUT_H * 0.4, 100, (255, 214, 40))
        return f

    def p_gota(self, t, d):
        m = ceu_aberto(0.75)
        gy = 600 + 140 * t
        self.segura(m, gota_cidade(500), 540, gy, 420, rot=4 * math.sin(t * 2))
        f = self.cam(m, 540, 1000, 1.0)
        texto_pop(f, "A CIDADE ERA UMA GOTA", self.fc, t, OUT_W / 2, OUT_H * 0.1, 48, (255, 255, 255))
        if self.T > 87.2:
            texto_pop(f, "CAINDO", self.fc, self.T - 87.2, OUT_W / 2, OUT_H * 0.17, 80, (255, 120, 100))
        return f

    def p_por_isso(self, t, d):
        m = ceu_aberto(0.75)
        self.segura(m, gota_cidade(500), 540, 900 + 60 * t, 520)
        f = self.cam(m, 540, 1000, 1.1)
        chuva(f, t, -1, 30, seed=11)
        dr = ImageDraw.Draw(f)
        for i in range(3):                       # setas: a gota desce
            y = OUT_H * (0.55 + 0.08 * ((t * 1.2 + i * 0.33) % 1.0))
            dr.polygon([(OUT_W * 0.82, y), (OUT_W * 0.9, y), (OUT_W * 0.86, y + 40)], fill=(255, 214, 40))
        return f

    def p_chegando(self, t, d):
        m = ceu_aberto(0.75 + 0.25 * ease_io(t / d))
        self.segura(m, gota_cidade(500), 540, 700, 380)
        f = self.cam(m, 540, 1000, 1.0 + 0.1 * ease_io(t / d))
        if self.T > 92.18:
            texto_pop(f, "ERA A GENTE CHEGANDO", self.fc, self.T - 92.18, OUT_W / 2, OUT_H * 0.12, 52, (255, 214, 40))
        return f

    def p_vento(self, t, d):
        m = ceu_aberto(0.8)
        self.segura(m, gota_cidade(500), 540 + 60 * math.sin(t * 5), 800, 420, rot=10 * math.sin(t * 5))
        f = self.cam(m, 540, 1000, 1.05)
        dr = ImageDraw.Draw(f, "RGBA")
        for i in range(6):
            y = OUT_H * (0.25 + 0.1 * i)
            x = (t * 900 + i * 140) % (OUT_W + 300) - 200
            dr.arc((x, y, x + 260, y + 60), 200, 340, fill=(255, 255, 255, 200), width=6)
        texto_pop(f, "VENTO", self.fc, t, OUT_W / 2, OUT_H * 0.12, 80, (255, 255, 255))
        return f

    def p_oceano(self, t, d):
        m = ceu_aberto(1.0)
        k = min(1, t / 1.6)
        y = 600 + 900 * ease_io(k)
        if k < 1:
            self.segura(m, gota_cidade(500), 540, y, 380)
        f = self.cam(m, 540, 1100, 1.05)
        if k >= 1:                              # respingo (o que poderia acontecer)
            dr = ImageDraw.Draw(f, "RGBA")
            kk = min(1, (t - 1.6) / 0.6)
            for i in range(12):
                a = math.radians(180 + i * 15)
                r = 200 * kk
                x, yy = OUT_W / 2 + r * math.cos(a), OUT_H * 0.8 + r * math.sin(a) * 1.4
                dr.ellipse((x - 16, yy - 16, x + 16, yy + 16), fill=(170, 215, 255, 230))
            f = vc.gradear(f, "triste")
            texto_pop(f, "VIRAR OCEANO", self.fc, t - 1.6, OUT_W / 2, OUT_H * 0.14, 70, (255, 120, 100))
        return f

    def p_desce(self, t, d):
        k = ease_io(min(1, t / 3.0))
        m = self.cid[1.5].copy()
        y = 300 + 1450 * k
        self.bia(m, t, 540, y, 1.1, expr="ri" if k < 1 else "surpreso", rot=20 * (1 - k))
        f = self.cam(m, 540, max(900, y - 450), 1.1)
        chuva(f, t, -1, 90)
        if k >= 1:
            texto_pop(f, "TUM!", self.fc, t - 3.0, OUT_W / 2, OUT_H * 0.2, 90, (255, 255, 255))
        return f

    def p_abram(self, t, d):
        return self.close(self.bia, t, self.cid[1.5], "cid15", expr="bravo", fala=self.FALA_BIA)

    def abre_gcs(self, m, t, n=14, ini=0.0, cor=None):
        rng = random.Random(3)
        cores = [(220, 60, 60), (250, 200, 50), (70, 130, 220), (90, 180, 100), (230, 120, 200)]
        for i in range(n):
            ti = ini + i * 0.12
            if t < ti:
                continue
            k = ease_out(min(1, (t - ti) / 0.3))
            x = rng.uniform(60, 1020)
            y = rng.uniform(900, 1700)
            gu = guarda_chuva(cor or cores[i % 5], 200)
            sz = max(1, int(200 * k))
            m.alpha_composite(gu.resize((sz, sz)), (int(x - sz / 2), int(y - sz / 2)))

    def p_abrem(self, t, d):
        m = self.cid[1.5].copy()
        for i, (p, x) in enumerate(zip(self.povo, (140, 340, 540, 740, 940))):
            p(m, t + i, x, 1780, 0.85, expr="feliz", pose="acena")
        self.abre_gcs(m, t, 20, 0.3)
        f = self.cam(m, 540, 1250, 1.05)
        texto_pop(f, "DO JEITO CERTO!", self.fc, t, OUT_W / 2, OUT_H * 0.12, 64, (255, 214, 40))
        return f

    def p_mil(self, t, d):
        m = self.cid[1.5].copy()
        self.abre_gcs(m, 9, 30, 0)
        self.dalva(m, t, 300, 1780, 1.1, expr="ri", pose="acena")
        m.alpha_composite(self.gc_azul.resize((220, 230)), (60, 900))
        m.alpha_composite(self.gc_vermelho.resize((220, 230)), (330, 900))
        self.pref(m, t, 780, 1790, 1.1, expr="bravo" if self.T > 113.4 else "neutro", pose="acena")
        f = self.cam(m, 540, 1250, 1.1)
        self.painel(f, "GUARDA-CHUVAS", "1.000", t)
        return f

    def p_freia(self, t, d):
        m = ceu_aberto(0.9)
        rot = 25 * math.sin(t * 2.4)
        x = 540 + 160 * math.sin(t * 1.2)
        self.segura(m, gota_cidade(500, gc=9, errado=False), x, 700 + 60 * t, 460, rot=rot)
        f = self.cam(m, 540, 1000, 1.05)
        texto_pop(f, "FREOU", self.fc, t, OUT_W / 2, OUT_H * 0.12, 80, (255, 255, 255))
        return f

    def p_pousa(self, t, d):
        m = praia()
        fl = flor(800)
        m.alpha_composite(fl, (140, 900))
        k = ease_io(min(1, t / (d * 0.85)))
        self.segura(m, gota_cidade(500, gc=9, errado=False), 540, 200 + 1000 * k, 360, rot=12 * math.sin(t * 2) * (1 - k))
        return self.cam(m, 540, 1150 - 100 * k, 1.05)

    def p_sem_estourar(self, t, d):
        m = praia()
        m.alpha_composite(flor(800), (140, 900))
        self.segura(m, gota_cidade(500, gc=9, errado=False), 540, 1200, 360)
        f = self.cam(m, 540, 1100, 1.4)
        particulas(f, t, 40, (255, 255, 255), semente=6)
        texto_pop(f, "SEM ESTOURAR", self.fc, t, OUT_W / 2, OUT_H * 0.14, 70, (255, 255, 255))
        return f

    def p_chuva_baixo(self, t, d):
        m = cidade(self.fc, lago=0)
        for i, (p, x) in enumerate(zip(self.povo, (140, 340, 540, 740, 940))):
            p(m, t + i, x, 1780, 0.85, expr="ri" if int(t * 3 + i) % 2 else "surpreso", pose="acena")
        f = self.cam(m, 540, 1250, 1.05)
        chuva(f, t, +1, 110)
        texto_pop(f, "PRA BAIXO!", self.fc, t, OUT_W / 2, OUT_H * 0.12, 90, (255, 214, 40))
        return f

    def p_vo_capa(self, t, d):
        m = cidade(self.fc, lago=0)
        tirou = self.T > 128.6
        (self.dalva_sem if tirou else self.dalva)(m, t, 540, 1780, 1.3, expr="surpreso" if self.T > 130.0 else "feliz")
        if tirou:
            k = ease_out(min(1, (self.T - 128.6) / 0.8))
            p = Pincel(320, 300)
            p.ret((20, 20, 300, 280), (250, 210, 50), r=40)
            m.alpha_composite(p.pronto(), (int(700 + 200 * k), int(1300 + 200 * k)))
        f = self.cam(m, 540, 1250, 1.15)
        if self.T > 130.0:
            chuva(f, t, +1, 120)
        return f

    def p_lauro_volta(self, t, d):
        m = cidade(self.fc, lago=0)
        k = ease_io(min(1, t / (d * 0.8)))
        y = -200 + 1980 * k
        if k < 1:
            p = Pincel(700, 900)
            p.elipse((40, 100, 660, 860), (170, 215, 255), ow=6)
            bolha = p.pronto()
            bolha.putalpha(bolha.getchannel("A").point(lambda v: int(v * 0.5)))
            m.alpha_composite(bolha, (190, int(y - 800)))
        self.lauro(m, t, 540, y, 1.0, expr="ri", pose="entrega")
        hx, hy = self.mao(540, y, 1.0, t)
        self.segura(m, self.peixe, hx + 60, hy, 200)
        f = self.cam(m, 540, max(800, min(1250, y - 400)), 1.1)
        chuva(f, t, +1, 60)
        return f

    def p_noite_flor(self, t, d):
        m = praia(noite=True)
        m.alpha_composite(flor(900), (90, 800))
        self.bia(m, t, 540, 1170, 0.55, expr="surpreso")
        return self.cam(m, 540, 1000 - 200 * ease_io(t / d), 1.15)

    def p_gotas_cidades(self, t, d):
        m = praia(noite=True)
        rng = random.Random(9)
        for i in range(14):
            x = rng.uniform(60, 1020)
            v = rng.uniform(40, 90)
            y = (rng.uniform(-400, 1200) + t * v) % 1600 - 300
            w = int(rng.uniform(110, 220))
            self.segura(m, gota_cidade(500, gc=5, errado=True), x, y, w)
        m.alpha_composite(flor(900), (90, 1300))
        f = self.cam(m, 540, 1000, 1.0)
        if self.T > 143.92:
            texto_pop(f, "CADA UMA COM UMA CIDADE", self.fc, self.T - 143.92, OUT_W / 2, OUT_H * 0.1, 46,
                      (255, 255, 255))
        return f

    def p_erradas(self, t, d):
        m = praia(noite=True)
        self.segura(m, gota_cidade(500, gc=7, errado=True), 540, 900 + 30 * t, 760)
        f = self.cam(m, 540, 950, 1.1)
        texto_pop(f, "DO LADO ERRADO", self.fc, t, OUT_W / 2, OUT_H * 0.12, 64, (255, 120, 100))
        return f

    def p_bilhete(self, t, d):
        m = praia(noite=True)
        m.alpha_composite(flor(900), (90, 800))
        self.bia(m, t, 400, 1170, 0.6, expr="feliz", pose="entrega")
        self.segura(m, self.pipa_img, 680, 900 - 120 * t, 200, rot=10 * math.sin(t * 3))
        f = self.cam(m, 540, 1000, 1.2)
        if t > 1.2:
            texto_pop(f, "\"ABRAM DO JEITO CERTO!\"", self.fc, t - 1.2, OUT_W / 2, OUT_H * 0.14, 46, (255, 214, 40))
        if t > d - 0.7:
            f = ImageEnhance.Brightness(f).enhance(max(0, 1 - (t - (d - 0.7)) / 0.7))
        return f

    # ---------- montagem ----------
    def frame(self, n):
        t = n / FPS
        self.T = t
        g.CAM_T = t
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
                f = g.vinheta(f, 0.3)
                self.legenda(f, t)
                return f

    def eventos_sfx(self):
        ev = []
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if i and tr in ("whip", "zoom"):
                ev.append(("whoosh", ini - 0.08))
            elif i and tr == "corte":
                ev.append(("pop", ini))
        return ev


def ruido_chuva(dur):
    SR = g.SR
    rng = np.random.default_rng(4)
    x = rng.standard_normal(int(SR * dur))
    x = np.convolve(x, np.ones(6) / 6, "same")
    x = x - np.convolve(x, np.ones(200) / 200, "same")         # tira o grave: chiado de chuva
    return x * 0.06


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
    env[(tt > 83.9) & (tt < 84.9)] = 0.2
    env[(tt > 121.8) & (tt < 122.7)] = 0.2
    mix[:len(mus)] += (mus * env)[:n]
    ch = ruido_chuva(filme.dur_total)
    cenv = np.zeros_like(tt)
    for a, b, v in ((0, 22.6, 1.0), (63.4, 77.4, 1.6), (98.9, 103.2, 1.0), (123.9, 136.2, 1.2)):
        cenv[(tt >= a) & (tt < b)] = v
    cenv = np.convolve(cenv, np.ones(SR // 2) / (SR // 2), "same")
    mix[:len(ch)] += (ch * cenv)[:n]
    ev = filme.eventos_sfx()
    ev += [("brilho", 28.88), ("brilho", 84.86), ("brilho", 122.70), ("toc", 102.0)]
    ev += [("pop", 106.16 + i * 0.12) for i in range(20)]
    from video_sono import sfx as sfx_sono
    ev += [("impacto", 54.24)]
    for tipo, t0 in ev:
        s = sfx_sono("impacto") * 0.6 if tipo == "impacto" else g.sfx(tipo)
        if tipo in ("whoosh", "pop"):
            s = s * 0.3
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
            if (w["w"].startswith("-") or w["w"].startswith("'")) and pal:
                pal[-1]["w"] += w["w"]
                pal[-1]["e"] = w["e"]
                continue
            pal.append(dict(w=w["w"], s=w["s"], e=w["e"]))
    out = []
    i = 0
    while i < len(pal):
        w = pal[i]
        nxt = pal[i + 1]["w"] if i + 1 < len(pal) else ""
        if w["w"] == "da" and nxt == "alva":
            out.append(dict(w="Dalva", s=w["s"], e=pal[i + 1]["e"]))
            i += 2
            continue
        if w["w"] == "ele" and nxt == "começou" and out and out[-1]["w"] == "que":
            i += 1
            continue
        txt = {"Possa": "Poça", "lauro.": "Lauro.", "10": "dez"}.get(w["w"], w["w"])
        out.append(dict(w=txt, s=w["s"], e=w["e"]))
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_chuva_que_sobe.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeChuva(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.2, a.narracao)
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

    tmp = tempfile.mkdtemp(prefix="chuva_")
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
