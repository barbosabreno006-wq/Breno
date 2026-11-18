#!/usr/bin/env python3
"""
"A Cor da Dona Cida" — bairro onde quem fica sozinho vai ficando transparente.

Efeito principal: personagens com transparência real (o fundo aparece através deles) e um
contador de % de transparência. Final interativo seguro (só pede comentário).

    python3 animacao/video_cor.py --narracao narr.wav --transcricao transcricao.json --fonte Poppins.ttf
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
import video_controle as vct  # noqa: E402
import video_estatua as ve  # noqa: E402
import video_sono as vs  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, gradiente, brilho,
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(303)

CIDA = dict(pele=(214, 160, 120), cabelo=(225, 225, 230), camisa=(180, 130, 200), calca=(0, 0, 0),
            sapato=(120, 80, 70), tipo="vovo", vestido=(180, 130, 200))
VALTER = dict(pele=(232, 186, 150), cabelo=(40, 35, 30), camisa=(45, 50, 70), calca=(40, 45, 60),
              sapato=(25, 25, 25), tipo="pai", gravata=(240, 190, 40))
LUCAS = dict(pele=(176, 120, 85), cabelo=(30, 22, 18), camisa=(60, 150, 220), calca=(60, 70, 110),
             sapato=(240, 240, 240), tipo="menino")
SOZINHO = dict(pele=(206, 150, 110), cabelo=(150, 150, 155), camisa=(150, 120, 90), calca=(80, 75, 70),
               sapato=(60, 50, 45), tipo="pai")
FILHOS = ve.POVO
vc.DESTAQUE_VERMELHO = set()
LARANJA = (255, 170, 80)


def alfa_de(pct):
    """% de transparência -> opacidade visível (mantém um 'fantasma' visível até 99%)."""
    return max(0.0, 0.14 + 0.86 * (1 - pct / 100) ** 0.8) if pct < 100 else 0.0


# --------------------------------------------------------------------------
# Objetos e cenários
# --------------------------------------------------------------------------
def placa_vende(fc, w=340, nome=None):
    h = int(w * 0.7)
    p = Pincel(w, h + 160)
    p.ret((w / 2 - 10, h - 10, w / 2 + 10, h + 160), (120, 90, 60), r=4)
    p.ret((10, 10, w - 10, h), (230, 50, 50), r=14, ow=6)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, int(w * 0.18))
    d.text((w / 2 - f.getlength("VENDE-SE") / 2, h * 0.28), "VENDE-SE", font=f, fill=(255, 255, 255))
    if nome:
        f2 = vc.fonte(fc, int(w * 0.09))
        d.text((w / 2 - f2.getlength(nome) / 2, h * 0.62), nome, font=f2, fill=(255, 230, 200))
    return img


def casa_interior(papel=True):
    base = gradiente(WW, WH, (235, 215, 190), (220, 195, 170))
    p = Pincel(WW, WH)
    if papel:     # papel de parede listrado/florido: aparece através da dona Cida
        for x in range(0, WW, 90):
            p.ret((x, 0, x + 45, 1400), (225, 200, 175), r=0, ow=0)
        rng = random.Random(2)
        for _ in range(40):
            x, y = rng.uniform(0, WW), rng.uniform(0, 1350)
            p.elipse((x - 18, y - 18, x + 18, y + 18), (210, 150, 160), ow=0)
            p.elipse((x - 7, y - 7, x + 7, y + 7), (240, 210, 120), ow=0)
    p.ret((680, 260, 980, 600), (170, 215, 240), r=10, ow=10)
    p.ret((80, 300, 360, 520), (200, 180, 150), r=8, ow=8)                     # quadro de família
    for i in range(5):
        p.elipse((105 + i * 50, 380, 145 + i * 50, 420), (230, 190, 160), ow=4)
    p.ret((-20, 1400, WW + 20, WH + 20), (160, 120, 90), r=0)
    base.alpha_composite(p.pronto())
    return base


def mesa_seis(fc):
    p = Pincel(WW, 700)
    p.ret((60, 200, 1020, 300), (180, 110, 70), r=16)
    p.ret((60, 160, 1020, 220), (250, 250, 250), r=10)
    for x in (140, 1000):
        p.ret((x - 20, 300, x + 20, 650), (150, 90, 60), r=8)
    for i in range(6):
        x = 150 + i * 156
        p.elipse((x - 55, 150, x + 55, 200), (250, 250, 250), ow=5)
        p.ret((x - 50, 0, x + 50, 150), (140, 90, 60), r=12)                    # cadeira (encosto)
    return p.pronto()


def rua_bairro(fc, cinza=0.0):
    base = vco.rua(fc)
    if cinza > 0:
        base = ImageEnhance.Color(base.convert("RGB")).enhance(1 - cinza).convert("RGBA")
    return base


def imobiliaria(fc):
    base = gradiente(WW, WH, (150, 200, 240), (225, 238, 250))
    p = Pincel(WW, WH)
    p.ret((80, 560, 1000, 1420), (240, 240, 235), r=8)
    p.ret((60, 520, 1020, 680), (40, 120, 90), r=10)
    p.ret((150, 800, 930, 1150), (180, 215, 240), r=8, ow=8)
    p.ret((-20, 1410, WW + 20, WH + 20), (190, 185, 175), r=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 50)
    t = "IMOBILIÁRIA LAR DOCE LAR"
    d.text((540 - f.getlength(t) / 2, 572), t, font=f, fill=(255, 255, 255))
    return base


def bilhete(fc, w=700):
    h = int(w * 0.75)
    p = Pincel(w, h)
    p.ret((10, 10, w - 10, h - 10), (252, 246, 220), r=6)
    for i in range(5):
        p.linha([(40, 120 + i * 80), (w - 40, 120 + i * 80)], fill=(200, 210, 235), w=3)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 48)
    for i, l in enumerate(["Dona Cida,", "alguém vai lembrar", "da senhora.", "", "        — Lucas"]):
        d.text((50, 60 + i * 80), l, font=f, fill=(40, 60, 140))
    return img


def kit_tinta(w=300):
    p = Pincel(w, w * 0.6)
    p.ret((10, 40, w - 10, w * 0.58), (240, 240, 240), r=12)
    for i, c in enumerate(((230, 60, 60), (250, 200, 50), (60, 140, 230), (90, 190, 90), (230, 120, 200))):
        x = 40 + i * (w - 80) / 4.5
        p.elipse((x, 60, x + 44, 104), c, ow=4)
    return p.pronto()


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeCor(ve.FilmeEstatua):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.cida, self.valter, self.lucas, self.soz = P_(CIDA), P_(VALTER), P_(LUCAS), P_(SOZINHO)
        self.filhos = [P_(c) for c in FILHOS]
        self.blur = {}
        self.rua = rua_bairro(fc)
        self.rua_c = rua_bairro(fc, 0.5)
        self.casa = casa_interior()
        self.imob = imobiliaria(fc)
        self.mesa = mesa_seis(fc)
        self.porta = vct.casa_porta()
        self.vende = placa_vende(fc)
        self.bilh = bilhete(fc)
        self.kit = kit_tinta()
        self.cel_ring = vs.celular(fc, "LIGANDO", [("FILHO", 80, (40, 40, 55))], botao="ATENDER", cor=(40, 160, 90))
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.FALA_VALTER = [(28.16, 32.5)]

        P = [
            (0.00, self.p_hook, "", "corte"),
            (3.80, self.p_tudo_bem, "", "corte"),
            (8.24, self.p_apagado, "", "corte"),
            (10.76, self.p_natal, "frio", "whip"),
            (14.74, self.p_some, "frio", "corte"),
            (17.98, self.p_imob, "", "whip"),
            (21.96, self.p_pega_casa, "", "corte"),
            (24.62, self.p_placas, "", "corte"),
            (28.16, self.p_valter, "", "corte"),
            (32.76, self.p_cida, "quente", "dissolve"),
            (37.42, self.p_filhos, "sepia", "dissolve"),
            (39.56, self.p_telefone, "", "corte"),
            (44.72, self.p_97, "", "zoom"),
            (48.58, self.p_parede, "", "corte"),
            (50.44, self.p_mesa, "", "corte"),
            (53.20, self.p_lucas, "", "whip"),
            (57.50, self.p_pinta, "", "corte"),
            (62.42, self.p_nunca, "triste", "corte"),
            (63.62, self.p_regra, "", "zoom"),
            (69.94, self.p_voce, "", "corte"),
            (71.76, self.p_comentarios, "quente", "corte"),
            (77.44, self.p_prazo, "", "whip"),
            (83.20, self.p_placa_portao, "", "corte"),
            (86.36, self.p_bilhete, "quente", "corte"),
            (90.28, self.p_bilhete_close, "quente", "corte"),
            (92.82, self.p_rua_final, "frio", "dissolve"),
            (96.60, self.p_mao, "", "zoom"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))
        self.p_preto = None

    # ---------- utilidades ----------
    def cam(self, m, cx, cy, z):
        return camera(m, cx, cy, z)

    def fantasma(self, pers, m, t, x, by, e, pct, expr="neutro", pose="idle", **kw):
        a = alfa_de(pct)
        if a <= 0:
            return
        if pct > 50:   # brilho fraquinho em volta de quem está sumindo
            m.alpha_composite(brilho((int(500 * e), int(800 * e)), (255, 255, 255), int(260 * e), 0.25 * a),
                              (int(x - 250 * e), int(by - 700 * e)))
        pers(m, t, x, by, e, expr=expr, pose=pose, alpha=a, **kw)

    def pct(self, f, valor, t, y=0.06, titulo="TRANSPARENTE", cor=(200, 220, 255)):
        self.painel(f, titulo, f"{int(valor)}%", t, y=y, cor=cor)

    # ------------------------- planos -------------------------
    def p_hook(self, t, d):
        m = self.rua.copy()
        pct = min(90, 90 * ease_io(t / d))
        x = 300 + 120 * t
        pose = "anda1" if int(t * 2.4) % 2 else "anda2"
        self.fantasma(self.soz, m, t, x, 1780, 1.15, pct, expr="triste", pose=pose)
        f = self.cam(m, 540, 1250, 1.1)
        self.pct(f, pct, t)
        return f

    def p_tudo_bem(self, t, d):
        m = self.rua.copy()
        for i, (p, x) in enumerate(zip(self.filhos[:3], (150, 900, 700))):
            pose = "anda1" if int(t * 2.4 + i) % 2 else "anda2"
            p(m, t, x - 80 * t * (1 if i % 2 else -1), 1700 + i * 30, 0.8, expr="neutro", pose=pose)
        pct = 40 + 1 * int(t / 1.2)
        self.fantasma(self.soz, m, t, 480, 1800, 1.1, pct, expr="triste")
        f = self.cam(m, 540, 1250, 1.1)
        self.balao(f, "TUDO BEM?", OUT_W * 0.65, OUT_H * 0.22, t - 1.6, cor=(230, 230, 235))
        dr = ImageDraw.Draw(f)
        if t > 1.6:
            dr.line((OUT_W * 0.45, OUT_H * 0.23, OUT_W * 0.85, OUT_H * 0.3), fill=(230, 60, 60), width=10)
        texto_pop(f, "-1%", self.fc, (t % 1.2), OUT_W * 0.25, OUT_H * 0.35, 60, (255, 120, 100))
        self.pct(f, pct, 1)
        return f

    def p_apagado(self, t, d):
        m = self.casa.copy()
        self.fantasma(self.soz, m, t, 540, 1760, 1.3, 45, expr="neutro")
        f = self.cam(m, 540, 1200, 1.15)
        self.pct(f, 45, t)
        return f

    def p_natal(self, t, d):
        m = self.casa.copy()
        m.alpha_composite(vct.arvore_natal().resize((360, 490)), (700, 900))
        m.alpha_composite(self.mesa.resize((900, 583)), (90, 1320))
        pct = 45 if t < 1.4 else 55
        self.fantasma(self.soz, m, t, 300, 1560, 1.0, pct, expr="triste")
        f = self.cam(m, 540, 1250, 1.1)
        if t > 1.4:
            texto_pop(f, "-10%", self.fc, t - 1.4, OUT_W / 2, OUT_H * 0.3, 110, (255, 100, 90))
        self.pct(f, pct, t if t < 1.4 else t - 1.4)
        return f

    def p_some(self, t, d):
        m = self.rua_c.copy()
        pct = min(100, 95 + 5 * ease_io(min(1, max(0, t - 0.9) / 0.9)))
        self.fantasma(self.soz, m, t, 540, 1780, 1.3, pct, expr="triste")
        f = self.cam(m, 540, 1200, 1.15)
        if pct >= 100:
            particulas(f, t, 50, (255, 255, 255), semente=4)
            texto_pop(f, "SUMIU", self.fc, t - 1.8, OUT_W / 2, OUT_H * 0.35, 110, (255, 255, 255))
        self.pct(f, pct, t)
        return f

    def p_imob(self, t, d):
        m = self.imob.copy()
        self.valter(m, t, 540, 1760, 1.25, expr="ri" if int(t * 3) % 2 else "feliz", pose="acena")
        return self.cam(m, 540, 1150, 1.05 + 0.08 * ease_io(t / d))

    def p_pega_casa(self, t, d):
        m = self.porta.copy()
        k = ease_out(min(1, t / 0.6))
        self.segura(m, self.vende, 820, 1500 + 300 * (1 - k), 280)
        self.valter(m, t, 360, 1760, 1.2, expr="ri", pose="bate2" if int(t * 6) % 2 else "bate")
        f = self.cam(m, 540, 1200, 1.1)
        vm_dinheiro = vco.dinheiro(3).resize((240, 156))
        f2 = f.convert("RGBA")
        f2.alpha_composite(vm_dinheiro, (int(OUT_W * 0.15), int(OUT_H * 0.2 - 40 * math.sin(t * 4))))
        return f2.convert("RGB")

    def p_placas(self, t, d):
        m = gradiente(WW, WH, (200, 190, 180), (170, 160, 150))
        nomes = ["CASA 12", "CASA 31", "CASA 7", "CASA 48", "CASA 22", "CASA 15", "CASA 9", "CASA 40", "CASA 3"]
        for i, n in enumerate(nomes):
            if t > i * 0.25:
                x, y = 200 + (i % 3) * 340, 500 + (i // 3) * 420
                self.segura(m, placa_vende(self.fc, 300, n), x, y, 280, rot=(i % 3 - 1) * 5)
        return self.cam(m, 540, 950, 1.05)

    def p_valter(self, t, d):
        m = self.fundo_blur("imob", self.imob)
        self.valter(m, t, 540, 2350, 2.5, expr="ri", fala=self.FALA_VALTER)
        f = self.cam(m, 540, 950, 1.05 + 0.1 * ease_io(t / d))
        return f

    def p_cida(self, t, d):
        m = self.casa.copy()
        self.fantasma(self.cida, m, t, 540, 1760, 1.35, 97, expr="neutro")
        f = self.cam(m, 540, 1150, 1.1)
        texto_pop(f, "DONA CIDA, 82", self.fc, t, OUT_W / 2, OUT_H * 0.25, 70, (255, 214, 40))
        if self.T > 35.24:
            texto_pop(f, "5 FILHOS", self.fc, self.T - 35.24, OUT_W / 2, OUT_H * 0.33, 60, (255, 255, 255))
        return f

    def p_filhos(self, t, d):
        m = self.porta.copy()
        self.cida(m, t, 300, 1760, 1.1, expr="feliz", pose="acena")
        for i, p in enumerate(self.filhos):
            x = 560 + i * 120 + 400 * ease_io(t / d)
            pose = "anda1" if int(t * 3 + i) % 2 else "anda2"
            p(m, t, x, 1780, 0.75, expr="feliz", pose=pose)
        return self.cam(m, 540, 1250, 1.1)

    def p_telefone(self, t, d):
        T = self.T
        fase = 0 if T < 41.52 else (1 if T < 42.68 else 2)
        m = self.casa.copy()
        pct = [20, 55, 85][fase]
        self.fantasma(self.cida, m, t, 360, 1760, 1.15, pct, expr=["ri", "neutro", "triste"][fase])
        tremor = 6 * math.sin(t * 50) if fase == 0 else (3 * math.sin(t * 50) if fase == 1 and int(t * 2) % 2 else 0)
        if fase < 2:
            self.segura(m, self.cel_ring, 760 + tremor, 1100, 300)
        else:
            m.alpha_composite(vct.bolo(self.fc, "82").resize((360, 360)), (580, 1100))
        f = self.cam(m, 540, 1200, 1.1)
        txt = ["TODO DOMINGO", "DE VEZ EM QUANDO", "SÓ NO ANIVERSÁRIO"][fase]
        t0 = [39.56, 41.52, 42.68][fase]
        texto_pop(f, txt, self.fc, T - t0, OUT_W / 2, OUT_H * 0.2, 64, (255, 255, 255))
        self.pct(f, pct, T - t0)
        return f

    def p_97(self, t, d):
        m = self.casa.copy()
        self.fantasma(self.cida, m, t, 540, 1760, 1.4, 97, expr="triste")
        f = self.cam(m, 540, 1150, 1.1 + 0.15 * ease_io(t / d))
        self.painel(f, "TRANSPARENTE", "97%", t, y=0.1, cor=(255, 120, 100))
        return f

    def p_parede(self, t, d):
        m = self.casa.copy()
        self.fantasma(self.cida, m, t, 540, 2350, 2.5, 97, expr="neutro")
        return self.cam(m, 540, 950, 1.05 + 0.05 * ease_io(t / d))

    def p_mesa(self, t, d):
        m = self.casa.copy()
        self.fantasma(self.cida, m, t, 540, 1330, 1.1, 97, expr="feliz")
        m.alpha_composite(self.mesa, (0, 1250))
        f = self.cam(m, 540, 1250, 1.05)
        texto_pop(f, "MESA PRA 6", self.fc, t, OUT_W / 2, OUT_H * 0.2, 70, (255, 255, 255))
        return f

    def p_lucas(self, t, d):
        m = self.rua.copy()
        x = 1000 - 500 * min(1, t / 3.0)
        pose = "anda1" if int(t * 3) % 2 and t < 3 else ("anda2" if t < 3 else "acena")
        self.lucas(m, t, x, 1780, 1.15, expr="feliz", pose=pose)
        self.segura(m, self.kit, x + 120, 1500, 180)
        f = self.cam(m, 540, 1250, 1.1)
        if self.T > 54.6:
            texto_pop(f, "LUCAS, 9", self.fc, self.T - 54.6, OUT_W / 2, OUT_H * 0.2, 70, (255, 214, 40))
        return f

    def p_pinta(self, t, d):
        m = self.casa.copy()
        self.fantasma(self.cida, m, t, 680, 1760, 1.2, 97, expr="feliz")
        self.lucas(m, t, 330, 1800, 1.05, expr="feliz", pose="bate" if int(t * 4) % 2 else "bate2")
        f = self.cam(m, 540, 1250, 1.1)
        dr = ImageDraw.Draw(f, "RGBA")
        rng = random.Random(7)
        cores = [(230, 60, 60), (250, 200, 50), (60, 140, 230), (90, 190, 90)]
        for i in range(10):                       # tinta atravessa e escorre até o chão
            x = OUT_W * 0.58 + rng.uniform(-60, 60)
            k = ((t * 0.7 + i / 10) % 1.0)
            y = OUT_H * (0.45 + 0.35 * k)
            dr.ellipse((x - 12, y - 16, x + 12, y + 16), fill=cores[i % 4] + (220,))
        dr.ellipse((OUT_W * 0.45, OUT_H * 0.84, OUT_W * 0.75, OUT_H * 0.88), fill=(150, 120, 180, 200))
        return f

    def p_nunca(self, t, d):
        m = self.fundo_blur("casa", self.casa)
        self.lucas(m, t, 540, 2350, 2.5, expr="triste")
        return self.cam(m, 540, 950, 1.05)

    def p_regra(self, t, d):
        m = gradiente(WW, WH, (30, 25, 45), (15, 12, 25))
        m.alpha_composite(brilho((900, 900), LARANJA, 450, 0.5 + 0.2 * math.sin(t * 2)), (90, 500))
        self.fantasma(self.cida, m, t, 540, 1700, 1.3, 97, expr="neutro")
        f = self.cam(m, 540, 1100, 1.05)
        if self.T > 66.30:
            texto_pop(f, "ALGUÉM DE FORA", self.fc, self.T - 66.30, OUT_W / 2, OUT_H * 0.14, 70, LARANJA)
        return f

    def p_voce(self, t, d):
        m = self.fundo_blur("casa", self.casa)
        self.fantasma(self.cida, m, t, 540, 2350, 2.5, 97, expr="surpreso")
        f = self.cam(m, 540, 950, 1.05 + 0.3 * ease_out(t / 0.6))
        texto_pop(f, "VOCÊ", self.fc, max(0, self.T - 70.84), OUT_W / 2, OUT_H * 0.2, 140, (255, 214, 40))
        return f

    def p_comentarios(self, t, d):
        m = self.casa.copy()
        pct = 97 - 4 * ease_io(t / d)
        self.fantasma(self.cida, m, t, 540, 1760, 1.25, pct, expr="feliz" if t > 2 else "neutro")
        f = self.cam(m, 540, 1150, 1.1)
        dr = ImageDraw.Draw(f, "RGBA")
        fn = vc.fonte(self.fc, 30)
        nomes = ["@ana", "@pedro_s", "@vovo_lu", "@carlos", "@bia.m", "@joao23", "@marta", "@leo"]
        for i in range(6):                         # comentários subindo
            k = (t * 0.6 + i / 6) % 1.0
            y = OUT_H * (0.75 - 0.55 * k)
            a = int(255 * min(1, k * 4) * min(1, (1 - k) * 4))
            dr.rounded_rectangle((40, y, OUT_W - 40, y + 70), radius=20, fill=(255, 255, 255, int(a * 0.9)))
            dr.text((60, y + 18), nomes[i % len(nomes)] + ": tô aqui, dona Cida", font=fn, fill=(40, 40, 50, a))
        self.pct(f, pct, t)
        return f

    def p_prazo(self, t, d):
        m = gradiente(WW, WH, (40, 40, 55), (20, 20, 30))
        p = Pincel(WW, WH)
        p.elipse((240, 560, 840, 1160), (255, 255, 255), ow=16)
        for k in range(12):
            a = math.radians(k * 30)
            p.linha([(540 + 250 * math.cos(a), 860 + 250 * math.sin(a)),
                     (540 + 280 * math.cos(a), 860 + 280 * math.sin(a))], w=8)
        a = math.radians(-90 + 360 * (t / d) * 2)
        p.linha([(540, 860), (540 + 230 * math.cos(a), 860 + 230 * math.sin(a))], fill=(230, 60, 60), w=10)
        p.linha([(540, 860), (540 + 150 * math.cos(math.radians(120)), 860 + 150 * math.sin(math.radians(120)))], w=18)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 960, 1.05)
        texto_pop(f, "7:00", self.fc, t, OUT_W / 2, OUT_H * 0.14, 110, (255, 120, 100))
        if self.T > 82.16:
            self.painel(f, "AMANHÃ", "100%", self.T - 82.16, y=0.78, cor=(255, 120, 100))
        return f

    def p_placa_portao(self, t, d):
        m = self.porta.copy()
        k = ease_out(min(1, t / 0.6))
        self.segura(m, self.vende, 760, 1500 + 300 * (1 - k), 300)
        self.valter(m, t, 320, 1760, 1.2, expr="ri", pose="bate2" if int(t * 5) % 2 else "bate")
        return self.cam(m, 540, 1200, 1.1)

    def p_bilhete(self, t, d):
        m = self.casa.copy()
        m.alpha_composite(self.mesa, (0, 1250))
        self.lucas(m, t, 820, 1780, 1.0, expr="triste", pose="entrega")
        k = ease_out(min(1, t / 1.0))
        self.segura(m, self.bilh, 600 + 100 * (1 - k), 1300 - 150 * (1 - k), 180)
        return self.cam(m, 540, 1250, 1.1)

    def p_bilhete_close(self, t, d):
        m = gradiente(WW, WH, (200, 170, 140), (180, 150, 120))
        self.segura(m, self.bilh, 540, 950, 900, rot=-2)
        return self.cam(m, 540, 950, 1.05 + 0.1 * ease_io(t / d))

    def p_rua_final(self, t, d):
        m = self.rua_c.copy()
        for i, (p, x, pc) in enumerate(zip(self.filhos + [self.soz], (120, 320, 540, 760, 960, 640),
                                           (60, 80, 30, 90, 70, 95))):
            self.fantasma(p, m, t, x, 1760 - (i % 2) * 40, 0.85, pc, expr="triste")
        return self.cam(m, 540, 1250, 1.05 + 0.08 * ease_io(t / d))

    def p_mao(self, t, d):
        m = self.fundo_blur("casa", self.casa)
        m.alpha_composite(brilho((1000, 1000), LARANJA, 500, 0.4 + 0.2 * math.sin(t * 2)), (40, 300))
        self.fantasma(self.cida, m, t, 540, 2350, 2.5, 96, expr="neutro")
        f = self.cam(m, 540, 950, 1.05 + 0.08 * ease_io(t / d))
        if t > 0.8:
            texto_pop(f, "COMENTE:", self.fc, t - 0.8, OUT_W / 2, OUT_H * 0.1, 50, (255, 255, 255))
            texto_pop(f, "\"TÔ AQUI, DONA CIDA\"", self.fc, t - 0.8, OUT_W / 2, OUT_H * 0.17, 54, LARANJA)
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
                f = g.vinheta(f, 0.35)
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
    mix[:len(mus)] += mus[:n]
    ev = filme.eventos_sfx()
    ev += [("brilho", 16.34), ("brilho", 71.76), ("toc", 22.2), ("toc", 22.5), ("toc", 83.5), ("toc", 83.8)]
    ev += [("ding", 39.7), ("ding", 40.4), ("ding", 41.6)]
    ev += [("pop", 71.9 + i * 0.8) for i in range(7)]
    from video_sono import sfx as sfx_sono
    for tipo, t0 in ev:
        s = sfx_sono(tipo) if tipo == "ding" else g.sfx(tipo)
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
            if (w["w"].startswith("-") or w["w"] == "%") and pal:
                pal[-1]["w"] += w["w"]
                pal[-1]["e"] = w["e"]
                continue
            pal.append(dict(w=w["w"], s=w["s"], e=w["e"]))
    troca = {"6,": "seis,", "6.": "seis.", "5": "cinco", "9": "nove", "7": "sete"}
    for w in pal:
        w["w"] = troca.get(w["w"], w["w"])
    return pal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_cor_da_dona_cida.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeCor(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.2, a.narracao)
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

    tmp = tempfile.mkdtemp(prefix="cor_")
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
