#!/usr/bin/env python3
"""
"O Contador de Abraços" — todo mundo nasce com um número no pulso: quantos abraços ainda vai dar.
O pai do narrador tinha só 3… porque doou todos os outros para o filho, que nasceu com zero.

Usa o rig articulado (boneco.py) e cortes automáticos a cada ~2 s (gerar_video.subcortes).

    python3 animacao/video_abracos.py --narracao narr.mp3 --transcricao transcricao.json --fonte Poppins.ttf
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
import video_milhao as vm  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(808)

PAI = dict(pele=(226, 172, 130), cabelo=(55, 40, 32), camisa=(90, 110, 145), calca=(55, 60, 75),
           sapato=(60, 45, 40), tipo="pai")
PAI_VELHO = dict(PAI, cabelo=(195, 195, 200))
PAI_HOSP = dict(PAI_VELHO, camisa=(170, 205, 225))
DAVI = dict(pele=(232, 180, 136), cabelo=(70, 45, 30), camisa=(245, 170, 60), calca=(60, 90, 150),
            sapato=(230, 80, 70), tipo="menino")
DAVI_AD = dict(pele=(232, 180, 136), cabelo=(70, 45, 30), camisa=(90, 170, 120), calca=(60, 70, 100),
               sapato=(70, 50, 40), tipo="pai", bigode=False)
DAVI_FORM = dict(DAVI_AD, camisa=(40, 42, 62))
DAVI_NOIVO = dict(DAVI_AD, camisa=(45, 50, 70), gravata=(240, 240, 245))
MAE = dict(pele=(222, 170, 128), cabelo=(110, 60, 40), camisa=(200, 100, 130), calca=(0, 0, 0),
           sapato=(140, 70, 90), tipo="moca", vestido=(200, 100, 130))
MAE_VELHA = dict(MAE, cabelo=(210, 210, 215), tipo="vovo")
VIZINHO = dict(pele=(200, 145, 105), cabelo=(40, 30, 28), camisa=(235, 110, 80), calca=(70, 80, 110),
               sapato=(50, 50, 50), tipo="pai")
CARTEIRO = dict(pele=(232, 186, 150), cabelo=(90, 60, 40), camisa=(250, 210, 70), calca=(60, 80, 140),
                sapato=(60, 60, 60), tipo="pai", bigode=False, chapeu=(60, 90, 170), bolsa=True)
MEDICO = dict(pele=(232, 186, 150), cabelo=(150, 150, 155), camisa=(245, 246, 250), calca=(120, 140, 170),
              sapato=(240, 240, 240), tipo="pai", bigode=False, gravata=(80, 150, 210))
MEDICA = dict(pele=(196, 140, 100), cabelo=(40, 30, 28), camisa=(245, 246, 250), calca=(0, 0, 0),
              sapato=(240, 240, 240), tipo="moca", vestido=(245, 246, 250))
FILHO = dict(pele=(232, 180, 136), cabelo=(70, 45, 30), camisa=(110, 190, 240), calca=(60, 80, 130),
             sapato=(240, 240, 240), tipo="menino")
PAIS_ESC = [dict(ve.POVO[0], tipo="pai"), dict(MAE, vestido=(120, 170, 220), camisa=(120, 170, 220))]
CIANO = (120, 235, 255)
vc.DESTAQUE_VERMELHO = set()


def num(n):
    return f"{int(n):,}".replace(",", ".")


# --------------------------------------------------------------------------
# Objetos
# --------------------------------------------------------------------------
_CACHE = {}


def texto_glow(txt, fc, tam, cor=CIANO, raio=14):
    k = ("tg", txt, tam, cor)
    if k in _CACHE:
        return _CACHE[k]
    f = vc.fonte(fc, tam)
    w, h = int(f.getlength(txt) + raio * 4), int(tam * 1.4 + raio * 4)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((raio * 2, raio * 2), txt, font=f, fill=cor + (255,))
    glow = img.filter(ImageFilter.GaussianBlur(raio))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for _ in range(2):
        out.alpha_composite(glow)
    d2 = ImageDraw.Draw(out)
    d2.text((raio * 2, raio * 2), txt, font=f, fill=(255, 255, 255, 255))
    out.alpha_composite(img, (0, 0)) if False else None
    tint = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(tint).text((raio * 2 + 2, raio * 2 + 2), txt, font=f, fill=cor + (120,))
    out.alpha_composite(tint)
    _CACHE[k] = out
    return out


def pulso(pele, manga, w=1080):
    """Antebraço na horizontal, visto de perto (o número vai em cima)."""
    k = ("pulso", pele, manga)
    if k in _CACHE:
        return _CACHE[k]
    p = Pincel(w, 620)
    p.capsula((300, 310), (790, 310), 200, pele)
    p.elipse((760, 190, 1010, 430), pele)                       # mão fechada
    for i in range(4):
        p.elipse((930, 200 + i * 52, 1040, 262 + i * 52), pele, ow=6)
    p.capsula((800, 210), (900, 170), 60, pele, ow=6)          # polegar
    p.ret((-40, 180, 330, 440), manga, r=40)
    p.arco((520, 230, 760, 390), 250, 290, fill=tuple(max(0, c - 40) for c in pele), w=5)
    img = p.pronto()
    _CACHE[k] = img
    return img


def bebe(w=300):
    k = ("bebe", w)
    if k in _CACHE:
        return _CACHE[k]
    p = Pincel(300, 300)
    p.elipse((40, 120, 260, 290), (250, 235, 200))              # mantinha
    p.elipse((80, 20, 220, 160), (236, 186, 150))               # cabeça
    p.arco((110, 70, 140, 100), 200, 340, w=5)
    p.arco((160, 70, 190, 100), 200, 340, w=5)
    p.elipse((138, 115, 162, 132), (220, 110, 120), ow=4)
    p.arco((140, 18, 170, 48), 180, 330, fill=(120, 80, 60), w=6)   # topete
    p.elipse((95, 98, 115, 112), (245, 150, 150), ow=0)
    p.elipse((185, 98, 205, 112), (245, 150, 150), ow=0)
    img = p.pronto()
    if w != 300:
        img = img.resize((w, w), Image.BICUBIC)
    _CACHE[k] = img
    return img


def coracao(t, x, y, s, alpha=255):
    p = Pincel(120, 120)
    p.elipse((10, 10, 64, 64), (240, 80, 110), ow=5)
    p.elipse((56, 10, 110, 64), (240, 80, 110), ow=5)
    p.poli([(14, 50), (106, 50), (60, 108)], (240, 80, 110), ow=5)
    p.elipse((16, 16, 60, 60), (240, 80, 110), ow=0)
    p.elipse((60, 16, 104, 60), (240, 80, 110), ow=0)
    img = p.pronto()
    return img


CORACAO = None


def coracoes(m, t, x, y, n=6, esc=1.0):
    global CORACAO
    if CORACAO is None:
        CORACAO = coracao(0, 0, 0, 1)
    rng = random.Random(int(x) + int(y))
    for i in range(n):
        ph = (t * 0.6 + rng.random()) % 1
        xx = x + rng.uniform(-120, 120) * esc + 20 * math.sin(t * 3 + i)
        yy = y - ph * 300 * esc
        s = (0.4 + 0.5 * rng.random()) * esc * (1 - ph * 0.3)
        h = CORACAO.resize((max(1, int(120 * s)), max(1, int(120 * s))), Image.BICUBIC)
        a = h.getchannel("A").point(lambda v: int(v * min(1, (1 - ph) * 2)))
        h.putalpha(a)
        m.alpha_composite(h, (int(xx - h.width / 2), int(yy - h.height / 2)))


def bicicleta():
    p = Pincel(520, 320)
    for cx in (110, 410):
        p.elipse((cx - 95, 125, cx + 95, 315), (60, 60, 70), ow=6)
        p.elipse((cx - 75, 145, cx + 75, 295), (0, 0, 0, 0), ow=0)
        p.elipse((cx - 12, 208, cx + 12, 232), (180, 180, 190), ow=4)
    p.linha([(110, 220), (230, 110), (360, 110), (410, 220)], fill=(220, 60, 60), w=16)
    p.linha([(230, 110), (260, 220), (110, 220)], fill=(220, 60, 60), w=16)
    p.linha([(260, 220), (360, 110)], fill=(220, 60, 60), w=16)
    p.ret((200, 80, 270, 100), (40, 40, 40), r=8, ow=4)
    p.linha([(360, 110), (380, 60), (420, 55)], fill=(80, 80, 90), w=10)
    return p.pronto()


def porta_rachada(w=380, h=820):
    p = Pincel(w, h)
    p.ret((0, 0, w, h), (250, 220, 150), r=6, ow=10)
    return p.pronto()


def capelo():
    p = Pincel(300, 160)
    p.poli([(10, 60), (150, 10), (290, 60), (150, 110)], (35, 35, 45), ow=6)
    p.ret((90, 70, 210, 140), (35, 35, 45), r=10)
    p.linha([(150, 60), (250, 80), (255, 140)], fill=(250, 200, 60), w=8)
    return p.pronto()


def aliancas():
    p = Pincel(260, 200)
    p.elipse((20, 40, 150, 170), (0, 0, 0, 0), ow=0)
    p.arco((20, 40, 150, 170), 0, 360, fill=(240, 200, 60), w=22)
    p.arco((110, 30, 240, 160), 0, 360, fill=(250, 215, 90), w=22)
    return p.pronto()


def diploma():
    p = Pincel(240, 80)
    p.ret((10, 10, 230, 70), (250, 245, 230), r=30, ow=6)
    p.ret((100, 8, 140, 72), (200, 40, 50), r=4, ow=0)
    return p.pronto()


def monitor(t, plano=False, w=300):
    p = Pincel(w, 230)
    p.ret((10, 10, w - 10, 200), (40, 50, 60), r=16)
    p.ret((26, 26, w - 26, 184), (15, 25, 30), r=8, ow=0)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(60):
        x = 30 + i * (w - 60) / 59
        ph = (i / 59 * 2 + t * 1.2) % 1
        y = 105
        if not plano and 0.42 < ph < 0.5:
            y = 105 - 60 * math.sin((ph - 0.42) / 0.08 * math.pi)
        elif not plano and 0.5 < ph < 0.55:
            y = 105 + 25 * math.sin((ph - 0.5) / 0.05 * math.pi)
        pts.append((x, y))
    d.line(pts, fill=(90, 240, 140), width=5)
    return img


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def auditorio():
    base = gradiente(WW, WH, (90, 60, 90), (60, 40, 60))
    p = Pincel(WW, WH)
    p.ret((-20, 1100, WW + 20, WH + 20), (150, 105, 70), r=0)
    for x in range(-40, WW + 40, 120):                 # bandeirinhas
        p.poli([(x, 140), (x + 100, 140), (x + 50, 230)], random.choice(
            [(240, 90, 90), (250, 210, 70), (90, 180, 240), (120, 210, 120)]), ow=4)
    p.linha([(-20, 140), (WW + 20, 140)], w=6)
    p.ret((80, 280, 1000, 520), (250, 245, 230), r=16, ow=8)
    base.alpha_composite(p.pronto())
    f = vc.fonte(None, 10) if False else None
    return base


def plateia():
    base = gradiente(WW, WH, (70, 50, 70), (45, 30, 50))
    p = Pincel(WW, WH)
    p.ret((-20, 1350, WW + 20, WH + 20), (120, 85, 60), r=0)
    for fila, y in enumerate((1500, 1700, 1900)):
        for x in range(-60, WW + 60, 170):
            xx = x + (85 if fila % 2 else 0)
            p.ret((xx, y - 160, xx + 140, y), (170, 50, 60), r=24)
    return base, p.pronto()


def hospital(noite=False):
    base = gradiente(WW, WH, (40, 55, 80) if noite else (205, 225, 235), (30, 40, 60) if noite else (185, 205, 220))
    p = Pincel(WW, WH)
    p.ret((680, 260, 980, 640), (20, 30, 60) if noite else (200, 230, 250), r=10, ow=10)
    if noite:
        p.elipse((800, 330, 870, 400), (240, 235, 210), ow=0)
    p.ret((-20, 1450, WW + 20, WH + 20), (130, 150, 160) if not noite else (60, 70, 85), r=0)
    p.ret((60, 900, 90, 1450), (170, 180, 190), r=8)              # suporte de soro
    p.ret((30, 860, 120, 990), (230, 240, 250), r=20, ow=6)
    base.alpha_composite(p.pronto())
    return base


def cama_hosp(noite=False):
    p = Pincel(WW, 700)
    lencol = (225, 235, 245) if not noite else (120, 135, 160)
    p.ret((120, 120, 980, 300), lencol, r=40)
    p.ret((140, 300, 960, 360), (150, 160, 175), r=10)
    for x in (170, 920):
        p.ret((x - 12, 340, x + 12, 600), (150, 160, 175), r=6)
    p.ret((80, 40, 140, 360), (170, 180, 195), r=14)
    return p.pronto()


def quarto_menino(noite=True):
    base = gradiente(WW, WH, (50, 55, 95) if noite else (220, 210, 200), (70, 70, 110) if noite else (200, 190, 180))
    p = Pincel(WW, WH)
    p.ret((640, 260, 960, 620), (25, 30, 60), r=10, ow=10)
    p.elipse((760, 330, 840, 410), (240, 235, 210), ow=0)
    p.ret((120, 420, 380, 680), (230, 200, 150), r=10, ow=10)     # porta-retrato do cachorro
    p.ret((140, 440, 360, 660), (150, 190, 220), r=6, ow=0)
    p.elipse((190, 500, 310, 640), (190, 140, 90), ow=6)           # cachorro
    p.elipse((170, 500, 215, 580), (140, 95, 60), ow=5)
    p.elipse((285, 500, 330, 580), (140, 95, 60), ow=5)
    p.elipse((225, 545, 245, 565), OUTLINE, ow=0)
    p.elipse((255, 545, 275, 565), OUTLINE, ow=0)
    p.elipse((240, 585, 262, 602), OUTLINE, ow=0)
    p.ret((-20, 1450, WW + 20, WH + 20), (100, 90, 90), r=0)
    base.alpha_composite(p.pronto())
    return base


def cama_menino():
    p = Pincel(WW, 600)
    p.ret((60, 100, 1020, 330), (120, 150, 210), r=36)
    p.ret((60, 300, 1020, 380), (160, 110, 80), r=10)
    return p.pronto()


def corredor_porta(noite=True):
    base = gradiente(WW, WH, (40, 45, 80), (55, 55, 90))
    p = Pincel(WW, WH)
    p.ret((300, 520, 780, 1500), (255, 225, 160), r=6, ow=12)      # porta aberta com luz
    p.ret((-20, 1480, WW + 20, WH + 20), (90, 80, 85), r=0)
    p.poli([(300, 1500), (780, 1500), (1000, WH + 20), (80, WH + 20)], (150, 130, 110), ow=0)
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((900, 1300), (255, 220, 150), 600, 0.45), (90, 380))
    return base


def maternidade():
    base = gradiente(WW, WH, (240, 225, 235), (225, 210, 225))
    p = Pincel(WW, WH)
    p.ret((-20, 1450, WW + 20, WH + 20), (200, 190, 200), r=0)
    p.ret((640, 260, 960, 620), (200, 230, 250), r=10, ow=10)
    base.alpha_composite(p.pronto())
    return base


def parque_por_do_sol():
    base = gradiente(WW, WH, (250, 170, 110), (250, 215, 160))
    p = Pincel(WW, WH)
    p.elipse((380, 620, 700, 940), (255, 230, 150), ow=0)
    p.elipse((-200, 1200, 600, 1700), (110, 170, 100), ow=0)
    p.elipse((400, 1150, 1300, 1700), (120, 180, 105), ow=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (130, 190, 110), r=0)
    for x in (120, 920):
        p.ret((x - 20, 980, x + 20, 1500), (120, 80, 60), r=8)
        p.elipse((x - 150, 760, x + 150, 1060), (90, 150, 90))
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((900, 900), (255, 220, 160), 450, 0.6), (90, 330))
    return base


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeAbracos(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.pai, self.pai_v, self.pai_h = P_(PAI), P_(PAI_VELHO), P_(PAI_HOSP)
        self.davi, self.davi_ad, self.davi_f, self.davi_n = P_(DAVI), P_(DAVI_AD), P_(DAVI_FORM), P_(DAVI_NOIVO)
        self.mae, self.mae_v = P_(MAE), P_(MAE_VELHA)
        self.viz, self.cart = P_(VIZINHO), P_(CARTEIRO)
        self.med, self.medica, self.filho = P_(MEDICO), P_(MEDICA), P_(FILHO)
        self.noiva = P_(ve.NOIVA)
        self.povo = [P_(c) for c in ve.POVO]
        self.pais_esc = [P_(c) for c in PAIS_ESC]
        self.criancas = [P_(dict(DAVI, camisa=c, cabelo=h)) for c, h in
                         (((120, 200, 120), (40, 30, 25)), ((230, 120, 170), (150, 70, 40)))]
        self.blur = {}
        self.rua = vco.rua(fc)
        self.coz, self.sala_img = va.cozinha(), va.sala()
        self.audit = auditorio()
        self.plat, self.cadeiras = plateia()
        self.hosp, self.hosp_n = hospital(), hospital(True)
        self.cama, self.cama_n = cama_hosp(), cama_hosp(True)
        self.quarto, self.cama_m = quarto_menino(), cama_menino()
        self.corredor = corredor_porta()
        self.matern = maternidade()
        self.berco = ve.berco()
        self.capela = ve.capela(fc)
        self.parque = parque_por_do_sol()
        self.bike, self.capelo, self.alianca, self.dipl = bicicleta(), capelo(), aliancas(), diploma()
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.f_leg = vc.fonte(fc, 50)
        self.FALA_DAVI = [(54.20, 56.40)]
        self.FALA_PAI = [(58.60, 61.60)]

        P = [
            (0.00, self.p_hook, "", "corte"),
            (5.82, self.p_maioria, "", "zoom"),
            (8.44, self.p_mae, "", "whip"),
            (10.20, self.p_vizinho, "", "whip"),
            (13.84, self.p_pai, "", "zoom"),
            (15.54, self.p_so3, "", "corte"),
            (16.64, self.p_nunca, "", "corte"),
            (18.86, self.p_bike, "", "whip"),
            (23.46, self.p_escola, "", "whip"),
            (27.20, self.p_fundo, "", "corte"),
            (29.28, self.p_cachorro, "frio", "dissolve"),
            (32.40, self.p_porta, "frio", "corte"),
            (36.14, self.p_cresci, "triste", "dissolve"),
            (38.48, self.p_formatura, "", "whip"),
            (41.64, self.p_pulso2, "", "zoom"),
            (43.58, self.p_casamento, "", "whip"),
            (46.26, self.p_pulso1, "", "zoom"),
            (47.12, self.p_hospital, "", "dissolve"),
            (50.06, self.p_senta, "", "corte"),
            (54.20, self.p_pergunta, "", "corte"),
            (56.86, self.p_sorri, "quente", "corte"),
            (61.86, self.p_mae_conta, "", "corte"),
            (63.32, self.p_bebe, "sepia", "dissolve"),
            (66.10, self.p_medicos, "sepia", "corte"),
            (70.34, self.p_doar, "", "zoom"),
            (76.08, self.p_pai_doa, "sepia", "dissolve"),
            (80.30, self.p_guardou, "quente", "dissolve"),
            (85.28, self.p_noite, "", "dissolve"),
            (88.32, self.p_zero, "", "corte"),
            (89.96, self.p_hoje, "quente", "dissolve"),
            (93.10, self.p_final, "quente", "corte"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))
        self.p_preto = None

    # ---------- utilidades ----------
    def cont(self, m, pers, txt, e, cor=CIANO, lado=0, dy=0):
        """Contador brilhando no pulso do personagem."""
        maos = getattr(pers.a, "maos_mundo", None)
        if not maos:
            return
        x, y = maos[lado]
        tam = max(18, int(46 * e))
        img = texto_glow(txt, self.fc, tam, cor, raio=max(4, int(10 * e)))
        m.alpha_composite(img, (int(x - img.width / 2), int(y - 44 * e - img.height / 2 + dy)))

    def pulso_cena(self, t, pele, manga, valor, cor=CIANO, bg=((25, 30, 50), (10, 12, 25)), z0=1.0, z1=1.15,
                   tremer=0.0):
        m = gradiente(WW, WH, *bg)
        img = pulso(pele, manga)
        m.alpha_composite(img, (0, 680))
        if valor is not None:
            tam = 170 if len(valor) < 4 else 130
            tg = texto_glow(valor, self.fc, tam, cor, raio=22)
            dx = tremer * math.sin(t * 60)
            m.alpha_composite(tg, (int(560 - tg.width / 2 + dx), int(990 - tg.height / 2)))
            m.alpha_composite(brilho((600, 400), cor, 300, 0.25), (260, 790))
        return self.cam(m, 600, 990, 0.45 + z0 + (z1 - z0) * ease_io(t / 2.5))

    def troca_num(self, t, a, b, t0):
        """Número que 'glitcha' de a para b no instante t0."""
        if t < t0:
            return a, 0.0
        x = t - t0
        if x < 0.25:
            return (a if int(x * 40) % 2 else b), 8.0
        return b, 0.0

    def de_pe(self, pers, t, m, x, by, e, **kw):
        pers(m, t, x, by, e, **kw)

    # ---------- planos ----------
    def p_hook(self, t, d):
        m = self.rua.copy()
        valores = ("10.214", "9.870", "11.032", "8.455")
        for i, (p, x) in enumerate(zip(self.povo[:4], (170, 420, 680, 930))):
            xx = x + 40 * math.sin(t * 0.5 + i)
            p(m, t + i, xx, 1760 - (i % 2) * 40, 0.85, expr="feliz" if i % 2 else "neutro", pose="anda")
            self.cont(m, p, valores[i], 0.85)
        f = self.cam(m, 540, 1250, 1.12 - 0.06 * ease_io(t / d))
        if self.T > 3.56:
            texto_pop(f, "ABRAÇOS QUE AINDA VAI DAR", self.fc, self.T - 3.56, OUT_W / 2, OUT_H * 0.12, 46,
                      (255, 214, 40))
        return f

    def p_maioria(self, t, d):
        v = min(10000, int(10000 * ease_out(t / 1.6)))
        f = self.pulso_cena(t, (214, 160, 120), (120, 170, 220), num(v))
        if t > 1.5:
            texto_pop(f, "10 MIL", self.fc, t - 1.5, OUT_W / 2, OUT_H * 0.15, 90, (255, 255, 255))
        return f

    def p_mae(self, t, d):
        m = self.coz.copy()
        self.mae(m, t, 540, 1780, 1.25, expr="feliz", pose="acena")
        self.cont(m, self.mae, "8.000", 1.25)
        f = self.cam(m, 540, 1150, 1.1)
        texto_pop(f, "MINHA MÃE", self.fc, t, OUT_W / 2, OUT_H * 0.1, 64, (255, 214, 40))
        return f

    def p_vizinho(self, t, d):
        m = self.rua.copy()
        T = self.T
        abraco = T > 11.94
        if not abraco:
            x = 900 - 260 * ease_out(t / 1.5)
            self.cart(m, t, x, 1780, 1.05, expr="surpreso" if t > 1.2 else "neutro", pose="anda" if t < 1.5 else "idle")
            self.viz(m, t, 300, 1780, 1.1, expr="feliz", pose="bracos_abertos" if t > 0.8 else "idle")
            self.cont(m, self.viz, "12.000", 1.1)
        else:
            self.viz(m, t, 390, 1780, 1.1, expr="ri", pose="abraca_d")
            self.cart(m, t, 630, 1780, 1.05, expr="surpreso", pose="abraca_e")
            self.cont(m, self.viz, "11.999" if T > 12.2 else "12.000", 1.1, lado=0)
            coracoes(m, T - 11.94, 510, 1050, 6)
        f = self.cam(m, 520, 1250, 1.15)
        if T > 12.5:
            texto_pop(f, "ATÉ O CARTEIRO", self.fc, T - 12.5, OUT_W / 2, OUT_H * 0.12, 64, (255, 255, 255))
        return f

    def p_pai(self, t, d):
        m = self.sala_img.copy()
        self.pai(m, t, 540, 1800, 1.35, expr="neutro", pose="bolso" if t < 0.4 else "idle", piscar=True)
        self.cont(m, self.pai, "3", 1.35, cor=(255, 120, 100))
        f = self.cam(m, 540, 1200, 1.1 + 0.15 * ease_io(t / d))
        if self.T > 14.68:
            texto_pop(f, "3", self.fc, self.T - 14.68, OUT_W / 2, OUT_H * 0.14, 150, (255, 120, 100))
        return f

    def p_so3(self, t, d):
        return self.pulso_cena(t, PAI["pele"], PAI["camisa"], "3", cor=(255, 120, 100), z0=1.1, z1=1.4,
                               bg=((40, 20, 25), (15, 8, 12)))

    def p_nunca(self, t, d):
        m = self.sala_img.copy()
        x = 860 - 220 * ease_out(t / 0.9)
        self.davi(m, t, x, 1800, 0.85, expr="feliz" if t < 1.1 else "triste",
                  pose="anda" if t < 0.9 else ("bracos_abertos" if t < 1.3 else "idle"))
        self.pai(m, t, 330, 1800, 1.3, expr="neutro", pose="bolso")
        self.cont(m, self.pai, "3", 1.3, cor=(255, 120, 100), lado=0, dy=-40)
        return self.cam(m, 540, 1250, 1.12)

    def p_bike(self, t, d):
        m = self.rua.copy()
        T = self.T
        bk = self.bike.rotate(-12, expand=True, resample=Image.BICUBIC)
        m.alpha_composite(bk, (560, 1500))
        self.davi(m, t, 460, 1800, 1.0, expr="chora")
        self.pai(m, t, 820, 1760, 1.25, expr="neutro", pose="bolso")
        if T > 20.22:   # gesso no braço
            pass
        f = self.cam(m, 600, 1250, 1.15)
        if T > 22.7:
            self.balao(f, "Vai passar.", OUT_W * 0.66, OUT_H * 0.16, T - 22.7)
        return f

    def p_escola(self, t, d):
        m = self.audit.copy()
        T = self.T
        abr = T > 25.74
        pares = ((self.pais_esc[0], self.criancas[0], 230), (self.pais_esc[1], self.criancas[1], 760))
        for adulto, crianca, x in pares:
            if abr:
                adulto(m, t, x - 60, 1780, 1.05, expr="ri", pose="abraca_d")
                crianca(m, t, x + 110, 1780, 0.8, expr="ri", pose="abraca_e")
                coracoes(m, T - 25.74, x + 20, 1150, 4, 0.8)
            else:
                adulto(m, t, x - 90, 1780, 1.05, expr="feliz", pose="palmas")
                crianca(m, t, x + 120, 1780, 0.8, expr="feliz", pose="acena")
        f = self.cam(m, 540, 1250, 1.08)
        return f

    def p_fundo(self, t, d):
        m = self.plat.copy()
        self.pai(m, t, 540, 1360, 0.7, expr="neutro", pose="palmas")
        m.alpha_composite(self.cadeiras)
        z = 1.05 + 0.5 * ease_io(t / d)
        return self.cam(m, 540, 1150, z)

    def p_cachorro(self, t, d):
        m = self.quarto.copy()
        self.davi(m, t, 640, 1560, 1.0, expr="chora")
        m.alpha_composite(self.cama_m, (0, 1180))
        return self.cam(m, 520, 1100, 1.1)

    def p_porta(self, t, d):
        m = self.corredor.copy()
        self.pai(m, t, 540, 1520, 1.05, expr="triste", pose="bolso")
        f = self.cam(m, 540, 1100, 1.12 + 0.1 * ease_io(t / d))
        return f

    def p_cresci(self, t, d):
        m = self.rua.copy()
        k = ease_io(min(1, t / (d * 0.7)))
        x = 200 + 500 * t / d
        if k < 0.5:
            a = 1 - k * 2
            self.davi(m, t, x, 1780, 0.85 + 0.2 * k, expr="triste", pose="anda", alpha=max(0.05, a))
        if k > 0.3:
            self.davi_ad(m, t, x, 1780, 1.0 + 0.1 * k, expr="triste", pose="anda", alpha=min(1, (k - 0.3) / 0.4))
        f = self.cam(m, 540, 1250, 1.1)
        if self.T > 37.58:
            texto_pop(f, "NÃO ME AMAVA", self.fc, self.T - 37.58, OUT_W / 2, OUT_H * 0.12, 70, (255, 140, 140))
        return f

    def chapeu(self, m, pers, x, by, e):
        y = by - pers.a.ultimo_bob - (640 - 70) * e
        g.colar(m, self.capelo, x, y + 60 * e, e * 0.9)

    def p_formatura(self, t, d):
        m = self.audit.copy()
        T = self.T
        if T < 39.84:
            xp = 1000 - 380 * ease_out(min(1, t / 1.2))
            self.davi_f(m, t, 380, 1800, 1.15, expr="feliz", pose="entrega")
            hx, hy = self.davi_f.a.maos_mundo[1]
            self.segura(m, self.dipl, hx, hy, 200, rot=20)
            self.chapeu(m, self.davi_f, 380, 1800, 1.15)
            self.pai_v(m, t, xp, 1800, 1.2, expr="neutro", pose="anda" if t < 1.2 else "idle")
        else:
            self.pai_v(m, t, 430, 1800, 1.2, expr="feliz", pose="abraca_d")
            self.davi_f(m, t, 640, 1800, 1.15, expr="chora" if T > 40.6 else "surpreso", pose="abraca_e")
            self.chapeu(m, self.davi_f, 640, 1800, 1.15)
            coracoes(m, T - 39.84, 540, 1000, 5)
        f = self.cam(m, 540, 1200, 1.1)
        if T > 40.5:
            texto_pop(f, "PRIMEIRA VEZ", self.fc, T - 40.5, OUT_W / 2, OUT_H * 0.12, 70, (255, 214, 40))
        return f

    def p_pulso2(self, t, d):
        v, tr = self.troca_num(self.T, "3", "2", 42.86)
        return self.pulso_cena(t, PAI["pele"], PAI["camisa"], v, cor=(255, 150, 100), tremer=tr, z0=1.15, z1=1.35)

    def p_casamento(self, t, d):
        m = self.capela.copy()
        T = self.T
        self.noiva(m, t, 840, 1800, 1.05, expr="feliz")
        if T < 44.92:
            self.davi_n(m, t, 600, 1800, 1.15, expr="feliz", pose="idle")
            self.pai_v(m, t, 260, 1800, 1.15, expr="neutro", pose="anda" if T < 44.4 else "idle")
        else:
            self.pai_v(m, t, 400, 1800, 1.15, expr="feliz", pose="abraca_d")
            self.davi_n(m, t, 600, 1800, 1.15, expr="chora", pose="abraca_e")
            coracoes(m, T - 44.92, 500, 1000, 5)
        vm.confete(m, t, 40) if False else None
        f = self.cam(m, 540, 1250, 1.1)
        particulas(f, t, 30, cor=(255, 240, 200), semente=4)
        return f

    def p_pulso1(self, t, d):
        v, tr = self.troca_num(self.T, "2", "1", 46.66)
        return self.pulso_cena(t, PAI["pele"], (110, 110, 120), v, cor=(255, 110, 90), tremer=tr, z0=1.2, z1=1.5,
                               bg=((40, 20, 25), (15, 8, 12)))

    def leito(self, m, t, noite=False, expr="neutro", fala=None, x=560, pose="idle"):
        self.pai_h(m, t, x, 1620, 1.0, expr=expr, fala=fala, pose=pose)
        m.alpha_composite(self.cama_n if noite else self.cama, (0, 1240))
        self.cont(m, self.pai_h, "1", 1.0, cor=(255, 110, 90), lado=1, dy=-160) if False else None

    def p_hospital(self, t, d):
        m = self.hosp.copy()
        m.alpha_composite(monitor(t), (780, 980))
        self.leito(m, t, expr="triste")
        return self.cam(m, 540, 1150, 1.12 - 0.05 * ease_io(t / d))

    def p_senta(self, t, d):
        m = self.hosp.copy()
        m.alpha_composite(monitor(t), (780, 980))
        self.leito(m, t, expr="neutro", x=640)
        x = -100 + 340 * ease_out(min(1, t / 1.2))
        self.davi_ad(m, t, x, 1880, 1.25, expr="triste", pose="anda" if t < 1.2 else "idle")
        return self.cam(m, 480, 1250, 1.12)

    def p_pergunta(self, t, d):
        return self.close(self.davi_ad, t, self.hosp, "hosp", expr="triste", fala=self.FALA_DAVI, z=1.05)

    def p_sorri(self, t, d):
        f = self.close(self.pai_h, t, self.hosp, "hosp", expr="feliz", fala=self.FALA_PAI, z=1.05 + 0.08 * t / d,
                       glow=(255, 220, 150))
        if self.T > 60.84:
            tg = texto_glow("9.000", self.fc, 120, (255, 214, 60), raio=16)
            s = 0.5 + 0.5 * ease_out((self.T - 60.84) / 0.25)
            tg = tg.resize((int(tg.width * s), int(tg.height * s)), Image.BICUBIC)
            f.paste(tg, (int(OUT_W / 2 - tg.width / 2), int(OUT_H * 0.1)), tg)
        return f

    def p_mae_conta(self, t, d):
        m = self.hosp.copy()
        self.mae_v(m, t, 360, 1800, 1.2, expr="triste", pose="entrega" if t > 0.3 else "idle")
        self.davi_ad(m, t, 760, 1800, 1.2, expr="surpreso")
        return self.cam(m, 560, 1200, 1.12)

    def p_bebe(self, t, d):
        m = self.matern.copy()
        T = self.T
        bb = bebe(280)
        m.alpha_composite(self.berco, (90, 1000))
        m.alpha_composite(bb, (400, 1120))
        if T > 65.46:
            pisca = (int((T - 65.46) * 4) % 2) == 0
            tg = texto_glow("0", self.fc, 120, (255, 80, 80) if pisca else (255, 140, 140), raio=16)
            m.alpha_composite(tg, (int(540 - tg.width / 2), 870))
        z = 1.1 + 0.6 * ease_io(t / d)
        f = self.cam(m, 540, 1150 - 100 * ease_io(t / d), z)
        if T > 65.46:
            texto_pop(f, "ZERO", self.fc, T - 65.46, OUT_W / 2, OUT_H * 0.12, 90, (255, 90, 90))
        return f

    def p_medicos(self, t, d):
        m = self.matern.copy()
        sh = 6 * math.sin(t * 7)
        self.med(m, t, 330, 1800, 1.15, expr="triste", rot=sh * 0.5)
        self.medica(m, t, 760, 1800, 1.1, expr="triste", rot=-sh * 0.5)
        f = self.cam(m, 540, 1200, 1.1)
        if self.T > 68.62:
            texto_pop(f, "NEM UMA SEMANA", self.fc, self.T - 68.62, OUT_W / 2, OUT_H * 0.12, 64, (255, 120, 120))
        return f

    def fluxo(self, m, t, a, b, n=26, cor=CIANO):
        """Números saindo de um pulso e entrando no outro."""
        f = vc.fonte(self.fc, 44)
        d = ImageDraw.Draw(m)
        rng = random.Random(9)
        for i in range(n):
            ph = (t * 0.7 + i / n) % 1
            cx = a[0] + (b[0] - a[0]) * ph + 120 * math.sin(ph * math.pi) * (1 if i % 2 else -1)
            cy = a[1] + (b[1] - a[1]) * ph - 80 * math.sin(ph * math.pi)
            dg = str(rng.randint(0, 9))
            d.text((cx, cy), dg, font=f, fill=cor)

    def p_doar(self, t, d):
        m = gradiente(WW, WH, (25, 30, 50), (10, 12, 25))
        big = pulso(PAI["pele"], PAI["camisa"])
        small = pulso((236, 186, 150), (250, 235, 200)).resize((760, 436), Image.BICUBIC)
        m.alpha_composite(big, (0, 420))
        m.alpha_composite(small.transpose(Image.FLIP_LEFT_RIGHT), (320, 1180))
        self.fluxo(m, t, (560, 720), (720, 1390))
        m.alpha_composite(brilho((700, 700), CIANO, 350, 0.25), (300, 700))
        f = self.cam(m, 540, 1050, 1.0 + 0.1 * ease_io(t / d))
        if self.T > 71.34:
            texto_pop(f, "DOAR ABRAÇOS", self.fc, self.T - 71.34, OUT_W / 2, OUT_H * 0.1, 72, (255, 214, 40))
        return f

    def p_pai_doa(self, t, d):
        m = self.matern.copy()
        T = self.T
        k = ease_io(min(1, max(0, (T - 76.6) / 2.6)))
        self.pai(m, t, 470, 1800, 1.3, expr="triste" if T > 78.2 else "feliz", pose="entrega")
        hx, hy = self.pai.a.maos_mundo[1]
        bb = bebe(220)
        m.alpha_composite(bb, (int(hx - 110), int(hy - 150)))
        self.cont(m, self.pai, num(9000 - 8997 * k), 1.3, cor=(255, 214, 60))
        tg = texto_glow(num(8997 * k), self.fc, 54, CIANO, raio=10)
        m.alpha_composite(tg, (int(hx - tg.width / 2), int(hy - 230)))
        if 0.02 < k < 0.98:
            self.fluxo(m, t * 2, (hx - 300, hy + 40), (hx + 20, hy - 180), n=14)
        f = self.cam(m, 560, 1250, 1.15)
        if T > 78.88:
            texto_pop(f, "FICOU SÓ COM 3", self.fc, T - 78.88, OUT_W / 2, OUT_H * 0.12, 70, (255, 214, 40))
        return f

    def p_guardou(self, t, d):
        m = gradiente(WW, WH, (60, 45, 60), (30, 22, 35))
        T = self.T
        self.pai(m, t, 540, 2250, 2.2, expr="neutro" if T < 82.78 else "feliz", pose="idle")
        f = self.cam(m, 540, 950, 1.05)
        if T > 82.78:
            icones = (self.capelo, self.alianca, None)
            for i, ic in enumerate(icones):
                tt = T - 82.78 - i * 0.35
                if tt < 0:
                    continue
                s = ease_out(min(1, tt / 0.25))
                x = OUT_W * (0.2 + 0.3 * i)
                y = OUT_H * 0.3
                if ic is None:
                    global CORACAO
                    if CORACAO is None:
                        CORACAO = coracao(0, 0, 0, 1)
                    ic = CORACAO
                w = int(140 * s) + 1
                im = ic.resize((w, int(ic.height * w / ic.width) + 1), Image.BICUBIC)
                f.paste(im, (int(x - im.width / 2), int(y - im.height / 2)), im)
            texto_pop(f, "3 DIAS", self.fc, T - 82.78, OUT_W / 2, OUT_H * 0.14, 90, (255, 214, 40))
        return f

    def p_noite(self, t, d):
        m = self.hosp_n.copy()
        m.alpha_composite(brilho((900, 900), (255, 200, 140), 450, 0.5), (90, 700))
        T = self.T
        if T < 86.56:
            self.pai_h(m, t, 380, 1640, 1.05, expr="feliz")
            self.davi_ad(m, t, 700, 1700, 1.1, expr="triste")
        else:
            self.pai_h(m, t, 470, 1640, 1.05, expr="feliz", pose="abraca_d")
            self.davi_ad(m, t, 650, 1700, 1.1, expr="chora", pose="abraca_e")
            coracoes(m, T - 86.56, 560, 980, 5)
        m.alpha_composite(self.cama_n, (0, 1300))
        return self.cam(m, 540, 1200, 1.12 + 0.12 * ease_io(t / d))

    def p_zero(self, t, d):
        v, tr = self.troca_num(self.T, "1", "0", 89.32)
        f = self.pulso_cena(t, PAI["pele"], PAI_HOSP["camisa"], v, cor=(255, 214, 120) if v == "1" else (200, 200, 210),
                            tremer=tr, z0=1.25, z1=1.4, bg=((40, 35, 45), (15, 12, 18)))
        particulas(f, t, 40, cor=(255, 230, 170), semente=8)
        return f

    def p_hoje(self, t, d):
        m = self.parque.copy()
        T = self.T
        self.davi_ad(m, t, 380, 1820, 1.25, expr="feliz", pose="idle" if T < 91.0 else "bracos_abertos")
        self.cont(m, self.davi_ad, "8.000", 1.25, cor=(255, 214, 60))
        x = 1100 - 360 * ease_out(min(1, t / 2.6))
        self.filho(m, t, x, 1820, 0.8, expr="ri", pose="corre" if t < 2.6 else "bracos_abertos", sx=-1)
        f = self.cam(m, 560, 1250, 1.12)
        particulas(f, t, 30, cor=(255, 230, 170), semente=2)
        return f

    def p_final(self, t, d):
        m = self.parque.copy()
        T = self.T
        self.davi_ad(m, t, 440, 1820, 1.25, expr="ri", pose="abraca_d")
        self.filho(m, t, 640, 1820, 0.85, expr="ri", pose="abraca_e")
        self.cont(m, self.davi_ad, "7.999" if T > 93.6 else "8.000", 1.25, cor=(255, 214, 60))
        coracoes(m, t, 540, 1120, 7)
        f = self.cam(m, 540, 1250, 1.1 + 0.1 * ease_io(t / d))
        particulas(f, t, 40, cor=(255, 230, 170), semente=5)
        if T > 94.54:
            texto_pop(f, "OBRIGADO, PAI.", self.fc, T - 94.54, OUT_W / 2, OUT_H * 0.12, 70, (255, 255, 255))
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
    ev += [("brilho", 7.5), ("brilho", 14.68), ("brilho", 42.86), ("brilho", 46.66), ("brilho", 60.84),
           ("toc", 19.3), ("toc", 65.46), ("brilho", 78.88), ("brilho", 82.78), ("brilho", 94.54)]
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
    troca = {"3.": "três.", "3,": "três,", "3": "três", "2.": "dois.", "1.": "um.", "0.": "zero.",
             "10": "dez", "8": "oito", "12": "doze", "9": "nove", "nenhuma": "nem uma"}
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            out.append(dict(w=troca.get(w["w"], w["w"]), s=w["s"], e=w["e"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_contador_de_abracos.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeAbracos(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.4, a.narracao)
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

    tmp = tempfile.mkdtemp(prefix="abracos_")
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
