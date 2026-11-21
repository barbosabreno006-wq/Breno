#!/usr/bin/env python3
"""
"O Papel do Seu Valdomiro" — num mundo todo de ouro, o papel é dinheiro. Tiago descobre, por um poço com escada,
um mundo cinza onde o papel é lixo e o ouro é sonho… e o esquema do único homem rico da cidade.

Reaproveita o motor de video_sal.py (poço, mundo cinza, janela, rig articulado) com arte e roteiro novos.

    python3 animacao/video_papel.py --narracao narr.mp3 --transcricao transcricao.json --fonte Poppins.ttf
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
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_video as g  # noqa: E402
import video_carta as vc  # noqa: E402
import video_estatua as ve  # noqa: E402
import video_areia as va  # noqa: E402
import video_sal as vs_  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io, particulas, texto_pop)

random.seed(2024)
OURO = (250, 205, 70)
OURO_ESC = (214, 160, 40)
_C = {}


# --------------------------------------------------------------------------
# Ícones
# --------------------------------------------------------------------------
def icone(kind, w=300):
    k = (kind, w)
    if k in _C:
        return _C[k]
    if kind in ("colher", "carrinho", "montanha_sal", "casa"):
        img = vs_.icone(kind, w)
        if kind == "montanha_sal":
            img = vs_.icone("montanha_sal", w)
        _C[k] = img
        return img
    p = Pincel(300, 300)
    if kind == "folha":
        p.ret((60, 30, 240, 270), (252, 252, 255), r=8)
        for y in (80, 120, 160, 200):
            p.linha([(90, y), (210, y)], fill=(170, 180, 205), w=6)
    elif kind == "bloco":
        for i in range(5):
            p.ret((50 + i * 6, 70 - i * 8 + 30, 250 + i * 6, 250 - i * 8 + 10), (250 - i * 4, 250 - i * 4, 255), r=8)
        p.ret((70, 130, 230, 190), (80, 130, 200), r=8, ow=0)
    elif kind == "ouro":
        p.poli([(40, 230), (80, 120), (230, 120), (270, 230)], OURO, ow=8)
        p.poli([(80, 120), (110, 80), (200, 80), (230, 120)], (255, 232, 140), ow=8)
    elif kind == "corrente":
        for i in range(9):
            a = math.radians(200 + i * 17.5)
            x, y = 150 + 110 * math.cos(a), 220 + 110 * math.sin(a)
            p.elipse((x - 22, y - 16, x + 22, y + 16), OURO, ow=6)
        p.elipse((126, 262, 174, 300 - 4), OURO, ow=6)
    elif kind == "sacolinha":
        p.poli([(90, 70), (210, 70), (240, 270), (60, 270)], (240, 240, 245), ow=6)
        p.linha([(110, 70), (130, 20)], fill=(210, 210, 220), w=10)
        p.linha([(190, 70), (170, 20)], fill=(210, 210, 220), w=10)
    elif kind == "cama":
        p.ret((20, 140, 280, 230), OURO, r=20)
        p.ret((20, 100, 90, 230), OURO_ESC, r=14)
        p.ret((30, 230, 55, 270), OURO_ESC, r=4)
        p.ret((245, 230, 270, 270), OURO_ESC, r=4)
    elif kind == "porta":
        p.ret((80, 30, 220, 280), OURO, r=10)
        p.elipse((190, 150, 206, 166), (255, 240, 180), ow=4)
    elif kind == "janela":
        p.ret((50, 50, 250, 250), (255, 225, 120), r=8)
        p.linha([(150, 50), (150, 250)], w=7)
        p.linha([(50, 150), (250, 150)], w=7)
    elif kind == "vaso":
        p.ret((80, 40, 220, 140), (255, 225, 120), r=12)
        p.elipse((60, 120, 240, 250), OURO, ow=7)
        p.elipse((100, 150, 200, 200), OURO_ESC, ow=4)
    elif kind == "pote":
        p.ret((70, 90, 230, 270), (255, 245, 210), r=26)
        p.ret((60, 60, 240, 100), OURO, r=14)
        for x, y in ((120, 160), (170, 190), (150, 130)):
            p.elipse((x - 9, y - 9, x + 9, y + 9), OURO_ESC, ow=3)
    elif kind == "dente":
        p.poli([(60, 60), (240, 60), (230, 170), (200, 270), (165, 170), (135, 170), (100, 270), (70, 170)],
               (255, 255, 255), ow=8)
    else:
        p.ret((60, 60, 240, 240), (200, 200, 200), r=10)
    img = p.pronto()
    _C[k] = img if w == 300 else img.resize((w, w), Image.BICUBIC)
    return _C[k]


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def brilhos_ouro(base, seed=2, n=70):
    rng = random.Random(seed)
    d = ImageDraw.Draw(base)
    for _ in range(n):
        x, y = rng.randint(0, WW), rng.randint(0, WH)
        r = rng.choice((3, 4, 6))
        d.line((x - r * 2, y, x + r * 2, y), fill=(255, 255, 255, 235), width=2)
        d.line((x, y - r * 2, x, y + r * 2), fill=(255, 255, 255, 235), width=2)


def mundo_ouro():
    base = gradiente(WW, WH, (255, 205, 95), (255, 240, 180))
    p = Pincel(WW, WH)
    p.elipse((700, 140, 920, 360), (255, 250, 220), ow=0)
    for i, x in enumerate((-50, 260, 570, 880)):
        top = 760 + (i % 2) * 90
        cor = [(255, 215, 110), (240, 190, 70), (255, 225, 140), (230, 175, 60)][i]
        p.ret((x, top, x + 300, 1420), cor, r=14)
        p.poli([(x - 14, top + 6), (x + 150, top - 150), (x + 314, top + 6)], (214, 150, 40))
        p.ret((x + 40, top + 90, x + 120, top + 200), (255, 245, 200), r=8, ow=6)
        p.ret((x + 180, top + 200, x + 250, 1420), (255, 235, 150), r=8, ow=6)
    p.ret((-20, 1410, WW + 20, 1500), (255, 235, 150), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (240, 200, 90), r=0)
    for x in range(0, WW, 200):
        p.ret((x + 40, 1700, x + 150, 1722), (255, 245, 190), r=6, ow=0)
    base.alpha_composite(p.pronto())
    brilhos_ouro(base)
    return base


def fabrica(fc, noite=False):
    base = mundo_ouro() if not noite else gradiente(WW, WH, (50, 40, 90), (95, 70, 120))
    if noite:
        p0 = Pincel(WW, WH)
        p0.ret((-20, 1410, WW + 20, 1500), (190, 160, 90), r=0)
        p0.ret((-20, 1500, WW + 20, WH + 20), (160, 130, 70), r=0)
        base.alpha_composite(p0.pronto())
    p = Pincel(WW, WH)
    p.ret((160, 640, 920, 1420), (232, 232, 240), r=12)
    p.ret((260, 500, 440, 650), (210, 210, 220), r=8)                                # chaminé
    p.elipse((500, 470, 700, 650), (250, 250, 255), ow=7)                           # rolo de papel gigante
    p.elipse((565, 535, 635, 605), (190, 190, 205), ow=5)
    p.ret((240, 1000, 840, 1200), (60, 40, 70), r=10, ow=10)                        # janelinha
    p.ret((220, 1200, 860, 1250), (140, 100, 70), r=6)
    p.ret((660, 1250, 800, 1420), (110, 70, 55), r=8)
    p.ret((200, 690, 880, 800), (60, 50, 100), r=10, ow=6)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 46)
    d.text((540 - f.getlength("FÁBRICA DE PAPEL") / 2, 722), "FÁBRICA DE PAPEL", font=f, fill=(255, 255, 255))
    if noite:
        base.alpha_composite(brilho((600, 400), (255, 220, 150), 220, 0.7), (220, 900))
    return base


def mercado_papel(fc):
    base = vs_.mercado_sal(fc)
    p = Pincel(WW, 120)
    p.ret((-20, 0, WW + 20, 100), (60, 130, 200), r=0, ow=0)
    base.alpha_composite(p.pronto(), (0, 108))
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 56)
    d.text((540 - f.getlength("CORREDOR DO PAPEL") / 2, 125), "CORREDOR DO PAPEL", font=f, fill=(255, 255, 255))
    return base


def poco_ouro():
    base = gradiente(WW, WH, (255, 210, 100), (70, 72, 85))
    p = Pincel(WW, WH)
    for y in range(0, WH, 110):
        for x in range(-60 + (y // 110 % 2) * 80, WW, 160):
            alfa = y / WH
            cor = (int(255 - 150 * alfa), int(205 - 95 * alfa), int(100 + 10 * alfa))
            p.ret((x, y, x + 150, y + 100), cor, r=8, ow=4)
    p.ret((330, -20, 750, WH + 20), (28, 26, 36), r=0, ow=0)
    for x in (360, 690):
        p.ret((x - 10, -20, x + 10, WH + 20), (200, 160, 90), r=4)
    for y in range(40, WH, 90):
        p.ret((360, y, 700, y + 16), (210, 170, 100), r=4)
    base.alpha_composite(p.pronto())
    return base


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmePapel(vs_.FilmeSal):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.bento, self.bpobre, self.brico = P_(vs_.BENTO), P_(vs_.BENTO_POBRE), P_(vs_.BENTO_RICO)
        self.hon, self.avo, self.feira, self.m2 = P_(vs_.HONORIO), P_(vs_.AVO), P_(vs_.FEIRA), P_(vs_.MENINO2)
        self.cinzas = [P_(c) for c in vs_.CINZAS]
        self.acuc = [P_(c) for c in vs_.ACUC]
        self.blur = {}
        self.mundo = mundo_ouro()
        self.sal_dia, self.sal_noite = fabrica(fc), fabrica(fc, True)
        self.cinza = vs_.mundo_cinza(fc)
        self.merc = mercado_papel(fc)
        self.poco = poco_ouro()
        self.coz = vs_.cozinha_noite()
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        P = [
            (0.00, self.p_hook, "", "corte"),
            (2.46, self.p_papel_dinheiro, "", "whip"),
            (4.06, self.p_folha, "", "corte"),
            (7.50, self.p_tiago_rico, "", "whip"),
            (11.64, self.p_ja_pobre, "", "corte"),
            (15.30, self.p_ouro_comum, "", "whip"),
            (18.52, self.p_crianca, "", "corte"),
            (20.24, self.p_assoar, "", "corte"),
            (25.08, self.p_um_homem, "", "whip"),
            (30.46, self.p_fabrica, "", "zoom"),
            (32.48, self.p_trabalham, "", "corte"),
            (35.20, self.p_tempera, "", "corte"),
            (40.78, self.p_ninguem, "frio", "dissolve"),
            (42.66, self.p_sacolinha, "frio", "corte"),
            (47.26, self.p_resfriado, "frio", "dissolve"),
            (51.08, self.p_avo_pede, "frio", "corte"),
            (54.86, self.p_sem_folha, "frio", "corte"),
            (57.42, self.p_corri, "frio", "whip"),
            (58.78, self.p_empresta, "frio", "whip"),
            (60.70, self.p_paga_com, "frio", "corte"),
            (62.70, self.p_com_ouro, "frio", "corte"),
            (63.40, self.p_calcar, "frio", "corte"),
            (65.98, self.p_fechou, "frio", "whip"),
            (68.02, self.p_esperei, "frio", "corte"),
            (71.00, self.p_amassar, "frio", "whip"),
            (75.78, self.p_dentro, "frio", "dissolve"),
            (81.46, self.p_nao_fabricava, "frio", "zoom"),
            (87.02, self.p_subi, "", "whip"),
            (92.38, self.p_tampa, "", "corte"),
            (95.76, self.p_cinza, "", "whip"),
            (97.70, self.p_nada_ouro, "", "corte"),
            (99.96, self.p_papel_lixo, "", "corte"),
            (105.74, self.p_colete, "", "whip"),
            (110.18, self.p_paga_hora, "", "corte"),
            (111.14, self.p_ninguem_ligava, "", "corte"),
            (115.44, self.p_troquei, "", "whip"),
            (117.88, self.p_mercado, "", "whip"),
            (123.92, self.p_entao, "", "zoom"),
            (125.22, self.p_esquema, "", "dissolve"),
            (131.58, self.p_muito_papel, "", "corte"),
            (135.20, self.p_esquisito, "", "zoom"),
            (139.36, self.p_isso, "", "corte"),
            (141.48, self.p_carrinho, "", "whip"),
            (143.30, self.p_vo_espera, "quente", "whip"),
            (147.18, self.p_alivio, "quente", "corte"),
            (149.08, self.p_salva, "quente", "corte"),
            (150.36, self.p_colher, "", "whip"),
            (155.90, self.p_la_cima, "", "whip"),
            (159.80, self.p_vendia, "", "corte"),
            (163.34, self.p_alianca, "", "whip"),
            (167.80, self.p_rico, "", "dissolve"),
            (172.46, self.p_bateu, "", "whip"),
            (175.38, self.p_pede, "", "corte"),
            (178.56, self.p_paga_com2, "", "corte"),
            (179.90, self.p_com_ouro2, "", "corte"),
            (180.62, self.p_eu_ri, "", "corte"),
            (183.98, self.p_se_aceito, "", "zoom"),
            (187.94, self.p_entendi, "", "dissolve"),
            (190.46, self.p_janela, "", "corte"),
            (193.50, self.p_mole, "", "corte"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))
        self.p_preto = None

    def ic(self, m, kind, x, y, w):
        im = icone(kind, int(w))
        m.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))

    # ---------- planos ----------
    def p_hook(self, t, d):
        m = self.mundo.copy()
        self.bento(m, t, 540, 1780, 1.2, expr="surpreso", pose="bracos_abertos")
        for i, (p, x) in enumerate(zip(self.acuc[:2], (200, 900))):
            p(m, t + i, x, 1780, 0.9, expr="feliz", pose="anda")
            self.ic(m, "folha", x + 60, 1500 - 20 * abs(math.sin(t * 2 + i)), 150)
        f = self.cam(m, 540, 1200, 1.12 - 0.05 * ease_io(t / d))
        self.txt(f, "TUDO É DE OURO", 0.2, 0.08, 62)
        return f

    def p_papel_dinheiro(self, t, d):
        m = gradiente(WW, WH, (255, 205, 95), (255, 240, 180))
        self.ic(m, "folha", 540, 1000, 700)
        f = self.cam(m, 540, 1000, 1.0 + 0.1 * ease_io(t / d))
        particulas(f, t, 30, cor=(255, 255, 255), semente=3)
        self.txt(f, "PAPEL = DINHEIRO", 2.58, 0.12, 60, (255, 255, 255))
        return f

    def p_folha(self, t, d):
        m = gradiente(WW, WH, (255, 205, 95), (255, 240, 180))
        T = self.T
        self.ic(m, "folha", 280, 900, 420)
        if T > 5.54:
            self.ic(m, "bloco", 300, 1380, 480)
            self.ic(m, "casa", 780, 1380, 480)
        f = self.cam(m, 540, 1150, 1.05)
        self.txt(f, "UMA FOLHA = 100", 4.26, 0.1, 56)
        self.txt(f, "UM BLOCO = UMA CASA", 5.74, 0.2, 50, (255, 255, 255))
        return f

    def p_tiago_rico(self, t, d):
        m = self.mundo.copy()
        self.brico(m, t, 540, 1800, 1.4, expr="feliz", pose="bracos_abertos")
        for x in (180, 900):
            self.ic(m, "bloco", x, 1700, 340)
        f = self.cam(m, 540, 1250, 1.1)
        self.txt(f, "TIAGO", 7.9, 0.1, 80)
        self.txt(f, "O MENINO MAIS RICO", 9.62, 0.2, 48, (255, 255, 255))
        return f

    def p_ja_pobre(self, t, d):
        m = self.mundo.copy()
        self.bpobre(m, t, 540, 1800, 1.4, expr="triste")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "JÁ FUI POBRE", 11.96, 0.1, 68, (255, 255, 255))
        self.txt(f, "E CHEIO DE OURO", 14.06, 0.18, 50)
        return f

    def p_ouro_comum(self, t, d):
        m = gradiente(WW, WH, (255, 205, 95), (255, 240, 180))
        T = self.T
        for i, (k, ts) in enumerate((("ouro", 15.54), ("casa", 16.24), ("porta", 17.22))):
            if T > ts:
                s = ease_out(min(1, (T - ts) / 0.3))
                self.ic(m, k, 200 + i * 340, 1100 + 120 * (i % 2), 330 * s + 1)
        f = self.cam(m, 540, 1150, 1.0)
        self.txt(f, "OURO NÃO VALE NADA", 15.54, 0.1, 50)
        self.txt(f, "É TÃO COMUM QUE É MOLE", 17.22, 0.17, 40, (255, 255, 255))
        return f

    def p_crianca(self, t, d):
        m = self.mundo.copy()
        self.bpobre(m, t, 540, 1800, 1.3, expr="ri", pose="entrega")
        hx, hy = self.bpobre.a.maos_mundo[1]
        s = 1 - 0.55 * ease_out(min(1, max(0, (self.T - 19.12) / 0.5)))
        self.ic(m, "ouro", hx, hy - 80, 260 * s + 40)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "CRIANÇA AMASSA COM A MÃO", 18.72, 0.1, 40, (255, 255, 255))
        return f

    def p_assoar(self, t, d):
        m = self.mundo.copy()
        T = self.T
        self.bpobre(m, t, 540, 1800, 1.4, expr="chora" if T > 23.7 else "neutro", pose="entrega")
        hx, hy = self.bpobre.a.maos_mundo[1]
        self.ic(m, "ouro", hx - 30, hy - 160, 220)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "ASSOAR O NARIZ", 20.92, 0.1, 54, (255, 255, 255))
        self.txt(f, "FRIA E ARRANHA", 23.74, 0.18, 54, (255, 130, 110))
        return f

    def p_um_homem(self, t, d):
        m = self.sal_dia.copy()
        self.hon(m, t, 540, 1800, 1.4, expr="feliz", pose="bracos_abertos")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "SEU VALDOMIRO", 27.22, 0.1, 62)
        return f

    def p_fabrica(self, t, d):
        m = self.sal_dia.copy()
        f = self.cam(m, 540, 1000, 1.0 + 0.15 * ease_io(t / d))
        self.txt(f, "FABRICA DINHEIRO", 31.2, 0.1, 56)
        return f

    def p_trabalham(self, t, d):
        m = self.sal_dia.copy()
        for i, p in enumerate(self.acuc[:4]):
            x = 160 + i * 250 + 40 * math.sin(t * 2 + i)
            p(m, t + i, x, 1800, 0.95, expr="neutro", pose="anda")
            self.ic(m, "bloco", x + 30, 1500, 160)
        return self.cam(m, 540, 1250, 1.12)

    def p_tempera(self, t, d):
        m = self.fundo_noite((255, 205, 95), (200, 150, 60))
        T = self.T
        self.hon(m, t, 540, 1800, 1.4, expr="ri", pose="aponta")
        self.ic(m, "folha", 760, 1300 + 20 * math.sin(t * 5), 260)
        f = self.cam(m, 540, 1200, 1.1)
        self.txt(f, "LIMPA A MESA", 35.38, 0.1, 50, (255, 255, 255))
        self.txt(f, "EMBRULHA O PÃO", 36.46, 0.17, 50, (255, 255, 255))
        self.txt(f, "SÓ PORQUE PODE", 39.7, 0.24, 54, (255, 130, 110))
        return f

    def p_ninguem(self, t, d):
        m = self.sal_noite.copy()
        p = Pincel(WW, WH)
        p.ret((580, 1230, 800, 1330), (230, 80, 80), r=10, ow=6)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 1100, 1.1 + 0.15 * ease_io(t / d))
        self.txt(f, "NINGUÉM ENTROU", 41.0, 0.1, 62, (255, 255, 255))
        return f

    def p_sacolinha(self, t, d):
        m = gradiente(WW, WH, (255, 205, 95), (255, 240, 180))
        self.ic(m, "sacolinha", 540, 1000, 560)
        f = self.cam(m, 540, 1000, 1.0 + 0.1 * ease_io(t / d))
        self.txt(f, "UMA SACOLINHA", 43.3, 0.1, 56, (255, 255, 255))
        self.txt(f, "A ÚNICA COISA QUE NÃO É DE OURO", 44.72, 0.17, 34)
        return f

    def p_resfriado(self, t, d):
        m = self.coz.copy()
        self.avo(m, t, 540, 1780, 1.3, expr="triste", pose="idle")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "RESFRIADO DAQUELES", 49.2, 0.1, 50, (255, 255, 255))
        return f

    def p_avo_pede(self, t, d):
        m = self.coz.copy()
        self.avo(m, t, 640, 1780, 1.3, expr="bravo", pose="aponta")
        self.bento(m, t, 260, 1800, 1.1, expr="surpreso")
        f = self.cam(m, 540, 1250, 1.12)
        self.balao_t(f, "Ouro de novo não!", OUT_W * 0.58, OUT_H * 0.16, 51.98)
        return f

    def p_sem_folha(self, t, d):
        m = self.mundo.copy()
        for i, p in enumerate(self.acuc[:3]):
            p(m, t + i, 200 + i * 340, 1800, 1.0, expr="triste", pose="bracos_abertos")
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "NINGUÉM TINHA UMA FOLHA", 55.0, 0.1, 38, (255, 255, 255))
        return f

    def p_empresta(self, t, d):
        m = self.janela_cena(t, "neutro", "neutro", bento_pose="entrega")
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Me empresta uma folha?", OUT_W * 0.5, OUT_H * 0.14, 59.56)
        return f

    def p_paga_com(self, t, d):
        m = self.janela_cena(t, "triste", "bravo", hon_pose="aponta")
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Me paga com o quê?", OUT_W * 0.55, OUT_H * 0.14, 61.34)
        return f

    def p_com_ouro(self, t, d):
        m = self.janela_cena(t, "feliz", "surpreso", bento_pose="entrega")
        hx, hy = self.bento.a.maos_mundo[1]
        self.ic(m, "ouro", hx, hy - 60, 200)
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Com ouro.", OUT_W * 0.3, OUT_H * 0.16, 62.7)
        return f

    def p_calcar(self, t, d):
        m = self.janela_cena(t, "triste", "ri", hon_pose="bracos_abertos")
        f = self.cam(m, 540, 1250, 1.18)
        self.balao_t(f, "Ouro é pra calçar mesa!", OUT_W * 0.5, OUT_H * 0.14, 63.94)
        return f

    def p_fechou(self, t, d):
        k = ease_out(min(1, t / 0.4))
        m = self.janela_cena(t, "surpreso", "bravo", fechada=k)
        f = self.cam(m, 540, 1250, 1.15)
        self.txt(f, "BAM!", 66.06, 0.12, 120, (255, 120, 100))
        return f

    def p_esperei(self, t, d):
        m = self.sal_noite.copy()
        self.hon(m, t, 120 + 900 * (min(1, t / d) ** 2), 1800, 1.2, expr="neutro", pose="anda", sx=-1)
        self.bento(m, t, 760, 1830, 1.1)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "FIZ UMA COISA FEIA", 69.5, 0.12, 54, (255, 120, 120))
        return f

    def p_amassar(self, t, d):
        m = self.sal_noite.copy()
        self.bento(m, t, 360, 1830, 1.3, expr="ri", pose="idle", rot=4 * math.sin(t * 8))
        k = ease_out(min(1, max(0, (self.T - 73.74) / 1.4)))
        q = Pincel(WW, WH)
        q.elipse((560 - 90 * k, 1300 - 120 * k, 560 + 90 * k, 1300 + 120 * k), (20, 14, 30), ow=6)
        m.alpha_composite(q.pronto())
        f = self.cam(m, 540, 1250, 1.15)
        self.txt(f, "O MURO ERA DE OURO", 71.14, 0.1, 50, (255, 255, 255))
        self.txt(f, "E OURO É MOLE", 72.64, 0.17, 60)
        return f

    def p_dentro(self, t, d):
        m = self.fundo_noite((60, 55, 80), (30, 28, 44))
        p = Pincel(WW, WH)
        p.elipse((300, 1500, 780, 1620), (14, 12, 20), ow=0)
        p.ret((330, 1400, 750, 1560), (28, 26, 36), r=0, ow=0)
        m.alpha_composite(p.pronto())
        for i, x in enumerate((140, 900, 220)):
            self.ic(m, "sacolinha", x, 1640 + 30 * (i % 2), 240)
        self.bento(m, t, 540, 1500, 1.1, expr="surpreso")
        f = self.cam(m, 540, 1200, 1.12)
        self.txt(f, "NENHUMA MÁQUINA", 76.6, 0.12, 60, (255, 255, 255))
        return f

    def p_nao_fabricava(self, t, d):
        m = self.poco.copy()
        f = self.cam(m, 540, 200 + 400 * ease_io(t / d), 1.3)
        self.txt(f, "NÃO FABRICAVA PAPEL", 82.54, 0.12, 48)
        self.txt(f, "DE ONDE VEM O PAPEL?", 85.08, 0.2, 42, (255, 255, 255))
        return f

    def p_subi(self, t, d):
        m = self.poco.copy()
        k = ease_io(t / d)
        by = 500 + 1000 * k
        self.bento(m, t, 540, by, 0.9, expr="surpreso")
        f = self.cam(m, 540, by - 100, 1.5)
        self.txt(f, "A PRIMEIRA PEDRA DA MINHA VIDA", 90.26, 0.12, 36, (255, 255, 255))
        return f

    def p_tampa(self, t, d):
        m = self.fundo_noite((30, 30, 44), (60, 62, 80))
        p = Pincel(WW, WH)
        p.ret((300, 1300, 780, 1360), (110, 112, 125), r=6)
        m.alpha_composite(p.pronto())
        T = self.T
        k = ease_out(min(1, max(0, (T - 94.66) / 0.6)))
        q = Pincel(WW, WH)
        q.elipse((340, 520 + 300 * k, 740, 620 + 300 * k), (140, 144, 158), ow=8)
        m.alpha_composite(q.pronto())
        self.bento(m, t, 540, 1300, 1.0, expr="surpreso", pose="aponta")
        if T > 94.66:
            m.alpha_composite(brilho((900, 900), (255, 255, 255), 420, 0.3 + 0.5 * k), (90, 200))
        return self.cam(m, 540, 1000, 1.15)

    def p_cinza(self, t, d):
        m = self.cinza.copy()
        self.bento(m, t, 540, 1800, 1.3, expr="surpreso", pose="bracos_abertos")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "UM MUNDO CINZA", 96.38, 0.1, 64, (255, 255, 255))
        return f

    def p_nada_ouro(self, t, d):
        m = self.cinza.copy()
        self.bento(m, t, 540, 1800, 1.2, expr="surpreso")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "TUDO DE PEDRA", 97.7, 0.1, 62, (255, 255, 255))
        self.txt(f, "NADA DE OURO", 98.82, 0.18, 54)
        return f

    def p_papel_lixo(self, t, d):
        m = self.cinza.copy()
        for x, y, w in ((200, 1760, 240), (620, 1800, 200), (900, 1700, 180), (400, 1500, 150), (80, 1500, 170)):
            self.ic(m, "folha", x, y, w)
        p = Pincel(WW, WH)
        p.ret((800, 1400, 920, 1560), (70, 72, 84), r=10)
        m.alpha_composite(p.pronto())
        self.ic(m, "folha", 860, 1380, 130)
        self.bento(m, t, 480, 1830, 1.1, expr="surpreso", pose="aponta")
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "PAPEL NO LIXO", 100.32, 0.1, 62, (255, 255, 255))
        self.txt(f, "DINHEIRO FORA!", 103.74, 0.18, 54)
        return f

    def p_colete(self, t, d):
        m = self.cinza.copy()
        self.feira(m, t, 760, 1800, 1.3, expr="surpreso", pose="aponta")
        self.bento(m, t, 280, 1830, 1.0, expr="surpreso")
        self.ic(m, "corrente", 300, 1450, 240)
        f = self.cam(m, 540, 1250, 1.12)
        self.balao_t(f, "Essa corrente é de ouro?", OUT_W * 0.55, OUT_H * 0.14, 108.76)
        return f

    def p_paga_hora(self, t, d):
        m = self.cinza.copy()
        self.feira(m, t, 760, 1800, 1.3, expr="feliz", pose="entrega")
        self.bento(m, t, 280, 1830, 1.0, expr="feliz", pose="entrega")
        f = self.cam(m, 540, 1250, 1.12)
        self.balao_t(f, "Pago na hora!", OUT_W * 0.6, OUT_H * 0.16, 110.3)
        return f

    def p_ninguem_ligava(self, t, d):
        m = self.cinza.copy()
        for i, p in enumerate(self.cinzas):
            x = 150 + i * 260
            p(m, t + i, x, 1800, 1.0, expr="neutro", pose="anda")
            self.ic(m, "folha", x + 30, 1700 + 40 * abs(math.sin(t * 2 + i)), 100)
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "NINGUÉM LIGAVA PRA PAPEL", 112.32, 0.1, 40, (255, 255, 255))
        self.txt(f, "TODO MUNDO QUERIA OURO", 113.96, 0.18, 40)
        return f

    def p_troquei(self, t, d):
        m = self.cinza.copy()
        self.feira(m, t, 780, 1800, 1.2, expr="feliz", pose="entrega")
        self.bento(m, t, 300, 1830, 1.1, expr="feliz", pose="entrega")
        self.ic(m, "bloco", 540, 1550, 260)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "TROCA!", 115.9, 0.12, 100)
        return f

    def p_mercado(self, t, d):
        m = self.merc.copy()
        self.bento(m, t, 540, 1850, 1.2, expr="surpreso", pose="bracos_abertos")
        f = self.cam(m, 540, 1200, 1.1)
        self.txt(f, "500 FOLHAS POR R$ 24,90", 121.0, 0.1, 44)
        return f

    def p_entao(self, t, d):
        f = self.close(self.bento, t, self.merc, "merc", expr="surpreso", z=1.05)
        self.txt(f, "ENTÃO ERA ISSO", 123.92, 0.1, 64, (255, 255, 255))
        return f

    def p_esquema(self, t, d):
        m = self.fundo_noite((40, 36, 70), (22, 20, 40))
        T = self.T
        for k, ts, x in (("ouro", 126.14, 200), ("bloco", 127.9, 540), ("casa", 129.12, 880)):
            if T > ts:
                s = ease_out(min(1, (T - ts) / 0.3))
                self.ic(m, k, x, 1000, 300 * s + 1)
        d_ = ImageDraw.Draw(m)
        for ts, x in ((126.9, 370), (128.5, 710)):
            if T > ts:
                d_.polygon([(x - 40, 990), (x + 40, 990), (x + 40, 960), (x + 100, 1010), (x + 40, 1060), (x + 40, 1030),
                            (x - 40, 1030)], fill=(255, 214, 40, 255))
        f = self.cam(m, 540, 1000, 1.0)
        self.txt(f, "VENDE OURO", 126.14, 0.12, 54)
        self.txt(f, "COMPRA PAPEL", 127.9, 0.2, 54, (255, 255, 255))
        self.txt(f, "DE PROPÓSITO", 130.34, 0.28, 54, (255, 160, 160))
        return f

    def p_muito_papel(self, t, d):
        m = self.fundo_noite((50, 44, 80), (26, 22, 44))
        k = ease_out(min(1, max(0, (self.T - 132.4) / 1.2)))
        self.ic(m, "montanha_sal", 540, 1150, 360 + 700 * k)
        f = self.cam(m, 540, 1050, 1.0)
        self.txt(f, "MUITO PAPEL", 131.96, 0.12, 64)
        self.txt(f, "VALE NADA", 134.04, 0.2, 80, (255, 120, 100))
        return f

    def p_esquisito(self, t, d):
        m = self.cinza.copy()
        self.bento(m, t, 540, 1830, 1.4, expr="neutro", pose="aponta")
        f = self.cam(m, 540, 1250, 1.12 + 0.08 * ease_io(t / d))
        self.txt(f, "PAPEL É LIXO", 136.66, 0.1, 64, (255, 255, 255))
        self.txt(f, "OURO É SONHO", 138.0, 0.18, 54)
        return f

    def p_isso(self, t, d):
        f = self.close(self.bento, t, self.cinza, "cinza", expr="feliz", z=1.15)
        self.txt(f, "VOCÊ AÍ", 140.44, 0.12, 100)
        return f

    def p_carrinho(self, t, d):
        m = self.mundo.copy()
        x = -150 + 800 * ease_out(min(1, t / d))
        self.bento(m, t, x, 1800, 1.3, expr="feliz", pose="anda")
        self.ic(m, "carrinho", x + 220, 1700, 420)
        return self.cam(m, 540, 1300, 1.12)

    def p_vo_espera(self, t, d):
        m = self.coz.copy()
        self.avo(m, t, 540, 1780, 1.3, expr="triste", pose="idle")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "3 HORAS", 144.92, 0.1, 90, (255, 255, 255))
        return f

    def p_alivio(self, t, d):
        m = self.coz.copy()
        self.avo(m, t, 540, 1780, 1.35, expr="ri", pose="entrega")
        self.ic(m, "folha", 800, 1480, 300)
        f = self.cam(m, 540, 1250, 1.12)
        self.balao_t(f, "Ai, que alívio!", OUT_W * 0.5, OUT_H * 0.16, 147.94)
        return f

    def p_salva(self, t, d):
        m = self.coz.copy()
        self.avo(m, t, 420, 1780, 1.3, expr="chora", pose="abraca_d")
        self.bento(m, t, 660, 1800, 1.15, expr="ri", pose="abraca_e")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "A VÓ FOI SALVA", 149.38, 0.12, 62)
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
        self.txt(f, "BURACO COM COLHER", 153.72, 0.1, 52, (255, 255, 255))
        return f

    def p_la_cima(self, t, d):
        m = self.cinza.copy()
        for i, p in enumerate(self.cinzas):
            p(m, t + i, 140 + i * 260, 1800, 1.0, expr="feliz", pose="bracos_abertos")
            self.ic(m, "folha", 170 + i * 260, 1500, 110)
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "TODO MUNDO FAZIA FILA", 156.68, 0.1, 44, (255, 255, 255))
        self.txt(f, "PELO MEU OURO", 158.92, 0.18, 62)
        return f

    def p_vendia(self, t, d):
        m = self.cinza.copy()
        self.brico(m, t, 300, 1830, 1.15, expr="ri", pose="bracos_abertos")
        T = self.T
        for k, ts, x in (("porta", 160.38, 560), ("janela", 161.14, 760), ("vaso", 162.52, 940)):
            if T > ts:
                s = ease_out(min(1, (T - ts) / 0.3))
                self.ic(m, k, x, 1650, 260 * s + 1)
        return self.cam(m, 540, 1300, 1.12)

    def p_alianca(self, t, d):
        m = self.fundo_noite((255, 205, 95), (255, 240, 180))
        p = Pincel(WW, WH)
        p.elipse((320, 700, 760, 1140), (0, 0, 0, 0), ow=0)
        p.arco((320, 700, 760, 1140), 0, 360, fill=OURO_ESC, w=70)
        p.arco((340, 720, 740, 1120), 0, 360, fill=OURO, w=40)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 1000, 1.0 + 0.12 * ease_io(t / d))
        particulas(f, t, 30, cor=(255, 255, 255), semente=5)
        self.txt(f, "SUA ALIANÇA É DE OURO?", 164.3, 0.1, 44, (255, 255, 255))
        self.txt(f, "NEM PERGUNTE DE ONDE VEIO", 166.36, 0.17, 36, (60, 40, 20))
        return f

    def p_rico(self, t, d):
        m = self.sal_dia.copy()
        self.brico(m, t, 540, 1800, 1.4, expr="feliz", pose="bracos_abertos")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "A MINHA FÁBRICA DE PAPEL", 170.56, 0.1, 40)
        return f

    def p_bateu(self, t, d):
        m = self.sal_noite.copy()
        self.brico(m, t, 540, 1450, 1.15, expr="surpreso")
        p = Pincel(WW, WH)
        p.ret((240, 1200, 840, 1250), (140, 100, 70), r=6)
        m.alpha_composite(p.pronto())
        self.m2(m, t, 300, 1850, 1.2, expr="neutro", pose="bate")
        f = self.cam(m, 540, 1250, 1.15)
        self.txt(f, "TOC TOC", 173.46, 0.12, 90, (255, 255, 255))
        return f

    def p_pede(self, t, d):
        m = self.sal_noite.copy()
        self.brico(m, t, 540, 1450, 1.15, expr="neutro")
        self.m2(m, t, 300, 1850, 1.2, expr="triste", pose="entrega")
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Me empresta uma folha?", OUT_W * 0.5, OUT_H * 0.14, 176.04)
        self.balao_t(f, "Minha vó está resfriada.", OUT_W * 0.45, OUT_H * 0.22, 177.12)
        return f

    def p_paga_com2(self, t, d):
        m = self.sal_noite.copy()
        self.brico(m, t, 540, 1450, 1.15, expr="bravo", pose="aponta")
        self.m2(m, t, 300, 1850, 1.2)
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Me paga com o quê?", OUT_W * 0.55, OUT_H * 0.14, 178.84)
        return f

    def p_com_ouro2(self, t, d):
        m = self.sal_noite.copy()
        self.brico(m, t, 540, 1450, 1.15, expr="surpreso")
        self.m2(m, t, 300, 1850, 1.2, expr="feliz", pose="entrega")
        hx, hy = self.m2.a.maos_mundo[1]
        self.ic(m, "ouro", hx, hy - 60, 200)
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Com ouro?", OUT_W * 0.3, OUT_H * 0.16, 180.08)
        return f

    def p_eu_ri(self, t, d):
        m = self.sal_noite.copy()
        self.brico(m, t, 540, 1450, 1.15, expr="ri", pose="bracos_abertos")
        self.m2(m, t, 300, 1850, 1.2, expr="surpreso")
        f = self.cam(m, 540, 1250, 1.15)
        self.balao_t(f, "Ouro é pra calçar mesa!", OUT_W * 0.5, OUT_H * 0.14, 182.46)
        return f

    def p_se_aceito(self, t, d):
        m = self.fundo_noite((60, 50, 100), (30, 26, 56))
        self.brico(m, t, 540, 2200, 2.3, expr="neutro")
        f = self.cam(m, 540, 950, 1.05)
        self.txt(f, "SE EU ACEITO OURO…", 183.98, 0.1, 48, (255, 255, 255))
        self.txt(f, "ELE DESCOBRE QUE VALE", 186.06, 0.18, 44)
        return f

    def p_entendi(self, t, d):
        m = self.fundo_noite((60, 50, 100), (30, 26, 56))
        self.brico(m, t, 380, 1800, 1.3, expr="surpreso")
        self.hon(m, t, 800, 1800, 1.0, expr="ri", alpha=0.45)
        f = self.cam(m, 540, 1250, 1.1)
        self.txt(f, "AGORA EU ENTENDI", 187.94, 0.1, 54, (255, 255, 255))
        self.txt(f, "O SEU VALDOMIRO", 189.26, 0.18, 56)
        return f

    def p_janela(self, t, d):
        m = gradiente(WW, WH, (255, 205, 95), (255, 240, 180))
        self.ic(m, "janela", 540, 1000, 700)
        f = self.cam(m, 540, 1000, 1.0 + 0.1 * ease_io(t / d))
        self.txt(f, "A MINHA JANELA TAMBÉM", 191.54, 0.1, 44, (60, 40, 20))
        self.txt(f, "É DE OURO", 192.82, 0.18, 62, (255, 255, 255))
        return f

    def p_mole(self, t, d):
        m = gradiente(WW, WH, (255, 205, 95), (255, 240, 180))
        k = min(1, t / d)
        im = icone("janela", 700)
        sx, sy = 1 + 0.6 * k, 1 - 0.6 * k
        im = im.resize((int(im.width * sx), max(10, int(im.height * sy))), Image.BICUBIC)
        m.alpha_composite(im, (540 - im.width // 2, int(1250 - im.height)))
        f = self.cam(m, 540, 1000, 1.0)
        self.txt(f, "E OURO É MOLE.", 193.66, 0.12, 70, (60, 40, 20))
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
    ev = filme.eventos_sfx()
    ev += [("brilho", 0.2), ("pop", 2.7), ("toc", 66.06), ("brilho", 95.76), ("pop", 115.9), ("brilho", 123.92),
           ("brilho", 140.44), ("brilho", 147.94), ("toc", 173.46), ("brilho", 187.94), ("toc", 193.66)]
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
            out.append(dict(w=w["w"], s=w["s"], e=w["e"]))
    res, i = [], 0
    troca = {"voz": "vó", "Arrange": "Arranja", "assou": "assoa", "massa": "amassa", "Thiago,": "Tiago,",
             "Muleque,": "Moleque,", "amacei": "amassei", "calçar": "calçar"}
    while i < len(out):
        w = out[i]
        if w["w"] == "24" and i + 1 < len(out) and out[i + 1]["w"].startswith(",90"):
            res.append(dict(w="R$24,90.", s=w["s"], e=out[i + 1]["e"]))
            i += 2
            continue
        t = troca.get(w["w"], w["w"])
        if w["w"] == "voz" and i > 0 and out[i - 1]["w"] in ("minha", "A"):
            t = "vó"
        res.append(dict(w=t, s=w["s"], e=w["e"]))
        i += 1
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_papel_do_seu_valdomiro.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmePapel(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.4, a.narracao)
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

    tmp = tempfile.mkdtemp(prefix="papel_")
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
