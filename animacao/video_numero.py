#!/usr/bin/env python3
"""
"O Número do Meu Pai" — mundo onde todos carregam na cabeça quantas vezes já erraram.

Marca registrada do formato: o contador ❌ + número em cima da cabeça de cada personagem,
que sobe ao vivo (+1, +1…) quando a pessoa erra.

    python3 animacao/video_numero.py --narracao narr.wav --transcricao transcricao.json --fonte Poppins.ttf
"""
import argparse
import json
import math
import os
import random
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_video as g  # noqa: E402
import video_carta as vc  # noqa: E402
import video_corsa as vco  # noqa: E402
import video_sono as vs  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, Ator, gradiente, brilho,
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(77)

LIVIA = dict(pele=(214, 160, 120), cabelo=(70, 45, 30), camisa=(60, 150, 110), calca=(0, 0, 0),
             sapato=(220, 70, 90), tipo="moca", vestido=(60, 150, 110), tranca=True)
LIVIA_CASA = dict(LIVIA, camisa=(240, 180, 200), vestido=(240, 180, 200))
SOFIA = dict(pele=(240, 200, 170), cabelo=(240, 200, 90), camisa=(130, 80, 180), calca=(0, 0, 0),
             sapato=(60, 40, 80), tipo="moca", vestido=(130, 80, 180))
PAI = dict(pele=(200, 145, 105), cabelo=(50, 38, 30), camisa=(90, 110, 140), calca=(60, 65, 80),
           sapato=(60, 50, 45), tipo="pai")
MAE = dict(pele=(214, 160, 120), cabelo=(70, 45, 30), camisa=(240, 150, 120), calca=(0, 0, 0),
           sapato=(150, 80, 70), tipo="moca", vestido=(240, 150, 120))
COLEGAS = [dict(pele=(150, 100, 70), cabelo=(30, 25, 25), camisa=(60, 150, 110), calca=(40, 50, 80),
                sapato=(220, 220, 220), tipo="menino"),
           dict(pele=(235, 190, 150), cabelo=(150, 70, 40), camisa=(60, 150, 110), calca=(0, 0, 0),
                sapato=(200, 60, 120), tipo="moca", vestido=(60, 150, 110)),
           dict(pele=(190, 130, 90), cabelo=(60, 40, 30), camisa=(60, 150, 110), calca=(40, 50, 80),
                sapato=(60, 60, 60), tipo="menino"),
           dict(pele=(176, 120, 85), cabelo=(25, 20, 20), camisa=(60, 150, 110), calca=(0, 0, 0),
                sapato=(240, 200, 60), tipo="moca", vestido=(60, 150, 110))]

vc.DESTAQUE_VERMELHO = {"errou", "fracassado", "ria.", "não", "ruim.", "desistiu"}


def fmt(n):
    return f"{int(n):,}".replace(",", ".")


# --------------------------------------------------------------------------
# O contador em cima da cabeça
# --------------------------------------------------------------------------
_CACHE_BADGE = {}


def badge(fc, numero, ouro=False):
    k = (numero, ouro)
    if k in _CACHE_BADGE:
        return _CACHE_BADGE[k]
    txt = fmt(numero)
    f = vc.fonte(fc, 60)
    w = int(f.getlength(txt) + 130)
    p = Pincel(w, 110)
    p.ret((6, 6, w - 6, 104), (255, 236, 160) if ouro else (245, 244, 248), r=26, ow=7)
    p.elipse((18, 18, 92, 92), (225, 50, 50), ow=5)
    p.linha([(38, 38), (72, 72)], fill=(255, 255, 255), w=10)
    p.linha([(72, 38), (38, 72)], fill=(255, 255, 255), w=10)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    d.text((106, 14), txt, font=f, fill=(150, 110, 20) if ouro else (40, 40, 50))
    _CACHE_BADGE[k] = img
    return img


def por_badge(m, fc, numero, cx, by, e, t=0.0, ouro=False, mais=0.0, pulo=0.0):
    """Cola o contador acima da cabeça de um personagem colado em (cx, by) com escala e."""
    b = badge(fc, numero, ouro)
    s = e * 0.62 * (1 + 0.12 * max(0, 1 - mais / 0.15) if mais < 0.15 else 1)
    b = b.resize((max(1, int(b.width * s)), max(1, int(b.height * s))), Image.BICUBIC)
    bob = 4 * math.sin(t * 2 * math.pi * 0.9) + pulo
    y = by - bob - 600 * e - b.height
    m.alpha_composite(b, (int(cx - b.width / 2), int(y)))
    return cx, y


# --------------------------------------------------------------------------
# Objetos e cenários
# --------------------------------------------------------------------------
_CACHE_BONECA = {}


def boneca(w=600, tranca=0.0):
    k = (w, round(tranca * 8))
    if k not in _CACHE_BONECA:
        _CACHE_BONECA[k] = _boneca(w, k[1] / 8)
    return _CACHE_BONECA[k]


def _boneca(w=600, tranca=0.0):
    p = Pincel(w, w * 1.2)
    c = w / 2
    p.elipse((c - 190, 60, c + 190, 440), (240, 200, 170))
    p.chord((c - 210, 30, c + 210, 330), 180, 360, (200, 150, 70))
    for x in (c - 70, c + 70):
        p.elipse((x - 22, 220, x + 22, 270), OUTLINE, ow=0)
    p.arco((c - 50, 300, c + 50, 360), 20, 160, w=7)
    # cabelo comprido / trança (progresso 0→1)
    n = int(8 * tranca)
    for k in range(8):
        y = 260 + k * 52
        if k < n:
            x = c + 230 + (12 if k % 2 else -12)
            p.elipse((x - 40, y - 34, x + 40, y + 34), (200, 150, 70), ow=5)
        else:
            p.linha([(c + 200, y - 30), (c + 230 + 30 * math.sin(k), y + 30)], fill=(200, 150, 70), w=26)
    p.ret((c - 150, 440, c + 150, 700), (230, 120, 150), r=40)
    return p.pronto()


def mao(w=200, cor=PAI["pele"]):
    p = Pincel(w, w)
    p.elipse((20, 20, w - 20, w - 20), cor)
    return p.pronto()


def portao(fc):
    base = gradiente(WW, WH, (150, 200, 240), (225, 238, 250))
    p = Pincel(WW, WH)
    vc.nuvem(p, 120, 240, 0.8)
    p.ret((40, 520, 1040, 1420), (240, 210, 140), r=8)
    for y in range(600, 1000, 130):
        for x in range(90, 1000, 170):
            p.ret((x, y, x + 120, y + 90), (170, 210, 240), r=8, ow=6)
    p.ret((260, 1050, 820, 1420), (60, 60, 70), r=8)
    for x in range(280, 820, 50):
        p.ret((x, 1060, x + 16, 1420), (220, 140, 40), r=6, ow=4)
    p.ret((200, 450, 880, 560), (40, 110, 200), r=12)
    p.ret((-20, 1410, WW + 20, 1500), (200, 190, 175), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (90, 90, 100), r=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 64)
    d.text((540 - f.getlength("ESCOLA") / 2, 470), "ESCOLA", font=f, fill=(255, 255, 255))
    return base


def sala(fc):
    base = gradiente(WW, WH, (240, 230, 205), (225, 210, 185))
    p = Pincel(WW, WH)
    p.ret((100, 260, 640, 640), (50, 100, 80), r=10, ow=12)
    p.ret((700, 230, 1000, 700), (240, 200, 120), r=10, ow=8)           # quadro de honra
    for i in range(3):
        for j in range(2):
            p.ret((730 + j * 135, 300 + i * 125, 840 + j * 135, 400 + i * 125), (250, 250, 250), r=6, ow=4)
    p.ret((-20, 1400, WW + 20, WH + 20), (180, 140, 100), r=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    d.text((725, 245), "QUADRO DE HONRA", font=vc.fonte(fc, 24), fill=(80, 50, 20))
    return base


def cozinha_noite():
    base = gradiente(WW, WH, (40, 45, 75), (55, 55, 85))
    p = Pincel(WW, WH)
    p.ret((640, 260, 960, 620), (20, 25, 50), r=10, ow=10)
    p.elipse((760, 320, 840, 400), (230, 230, 245), ow=0)
    p.ret((-20, 1400, WW + 20, WH + 20), (70, 60, 70), r=0)
    p.ret((60, 1250, 1020, 1330), (150, 100, 70), r=10)
    p.ret((100, 1330, 140, 1700), (130, 85, 60), r=10)
    p.ret((940, 1330, 980, 1700), (130, 85, 60), r=10)
    p.ret((500, 900, 520, 1000), (80, 80, 90), r=4, ow=0)
    p.chord((420, 980, 600, 1100), 180, 360, (250, 210, 120))
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((1000, 1000), (255, 210, 130), 500, 0.6), (10, 650))
    return base


def corredor_escuro():
    base = gradiente(WW, WH, (20, 22, 40), (30, 30, 50))
    p = Pincel(WW, WH)
    p.ret((380, 600, 700, 1400), (255, 215, 140), r=6, ow=10)            # porta da cozinha acesa
    p.ret((-20, 1400, WW + 20, WH + 20), (35, 35, 50), r=0)
    p.poli([(380, 1400), (700, 1400), (900, WH), (180, WH)], (90, 80, 70), ow=0)
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((900, 1200), (255, 200, 120), 500, 0.5), (90, 400))
    return base


def esquina(fc):
    base = vco.rua(fc)
    p = Pincel(WW, WH)
    p.ret((880, 900, 900, 1420), (80, 80, 90), r=6)
    p.ret((820, 860, 1000, 920), (40, 140, 70), r=8)
    base.alpha_composite(p.pronto())
    return base


def relogio_5():
    p = Pincel(600, 600)
    p.elipse((20, 20, 580, 580), (250, 250, 250), ow=14)
    for k in range(12):
        a = math.radians(k * 30)
        p.linha([(300 + 230 * math.cos(a), 300 + 230 * math.sin(a)), (300 + 260 * math.cos(a), 300 + 260 * math.sin(a))],
                w=8)
    a = math.radians(-90 + 150)
    p.linha([(300, 300), (300 + 140 * math.cos(a), 300 + 140 * math.sin(a))], w=18)
    p.linha([(300, 300), (300, 80)], w=10)
    return p.pronto()


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeNumero(vc.Filme):
    def __init__(self, palavras, fc, dur_total):
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.livia, self.livia_c = Ator(LIVIA), Ator(LIVIA_CASA)
        self.sofia, self.pai, self.mae = Ator(SOFIA), Ator(PAI), Ator(MAE)
        self.colegas = [Ator(c) for c in COLEGAS]
        self.rua = vco.rua(fc)
        self.portao = portao(fc)
        self.sala = sala(fc)
        self.cozinha = cozinha_noite()
        self.corredor = corredor_escuro()
        self.esquina = esquina(fc)
        self.relogio = relogio_5()
        self.mao_pai = mao()
        self.nums_colegas = [1204, 3870, 912, 2455]
        self.celular_aula = vs.celular(fc, "VÍDEO", [("Como fazer", 46, (40, 40, 55)), ("trança embutida", 46, (40, 40, 55)),
                                                     ("AULA 12", 80, (220, 50, 50))], cor=(220, 50, 50))
        self.atm = vs.celular(fc, "BANCO", [("Senha", 50, (40, 40, 55)), ("INCORRETA", 76, (220, 50, 50)),
                                            ("Tentativa 5", 44, (130, 130, 145))], cor=(40, 110, 200))
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        P = [
            (0.00, self.p_mundo, "", "corte"),
            (5.06, self.p_arroz, "", "whip"),
            (6.74, self.p_senha, "", "corte"),
            (9.92, self.p_honra, "", "whip"),
            (13.26, self.p_sala, "", "corte"),
            (16.74, self.p_sofia8, "", "corte"),
            (19.16, self.p_pai_num, "", "zoom"),
            (23.02, self.p_portao, "", "whip"),
            (26.10, self.p_sofia_grita, "", "corte"),
            (31.52, self.p_riem, "", "corte"),
            (35.24, self.p_esquina, "triste", "whip"),
            (39.02, self.p_reclamou, "triste", "corte"),
            (40.00, self.p_madrugada, "", "dissolve"),
            (44.66, self.p_relogio, "", "corte"),
            (45.80, self.p_cozinha, "", "corte"),
            (49.88, self.p_sobe, "", "corte"),
            (54.26, self.p_tranca, "", "corte"),
            (59.48, self.p_celular, "", "corte"),
            (64.38, self.p_mae, "sepia", "zoom"),
            (68.18, self.p_percebe, "", "dissolve"),
            (71.22, self.p_cabelo, "quente", "corte"),
            (75.40, self.p_licao, "quente", "zoom"),
            (81.86, self.p_portao_frente, "", "whip"),
            (85.48, self.p_sofia_ri, "", "corte"),
            (86.66, self.p_mao, "quente", "corte"),
            (90.08, self.p_fala, "quente", "corte"),
            (93.10, self.p_ensina, "quente", "dissolve"),
            (95.38, self.p_42, "quente", "corte"),
            (97.48, self.p_sorri, "quente", "corte"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))

    def fundo(self, c1=(240, 225, 200), c2=(220, 200, 175)):
        return gradiente(WW, WH, c1, c2)

    def pessoa(self, m, ator, t, cx, by, e, num, expr="neutro", pose="idle", ouro=False, mais=9.0, **kw):
        ator.desenhar(m, t, cx, by, escala=e, expr=expr, pose=pose, **kw)
        return por_badge(m, self.fc, num, cx, by, e, t, ouro=ouro, mais=mais, pulo=kw.get("pulo", 0))

    def mais_um(self, f, t, x, y, n=1):
        """'+1' que sobe e some."""
        if 0 <= t < 0.6:
            k = t / 0.6
            texto_pop(f, f"+{n}", self.fc, t, x, y - 80 * k, 56, (230, 50, 50))

    # ------------------------- planos -------------------------
    def p_mundo(self, t, d):
        m = self.rua.copy()
        gente = [(self.colegas[0], 150, 1700, 0.8, 3412), (self.mae, 400, 1760, 0.95, 18230),
                 (self.pai, 680, 1760, 0.95, 52007), (self.colegas[3], 930, 1700, 0.8, 2210)]
        for i, (a, x, y, e, n) in enumerate(gente):
            self.pessoa(m, a, t + i, x, y, e, n, expr="feliz" if i % 2 else "neutro")
        return camera(m, 540, 1200, 1.05 + 0.12 * ease_io(t / d))

    def p_arroz(self, t, d):
        m = self.fundo((240, 235, 225), (215, 210, 200))
        p = Pincel(WW, WH)
        p.ret((-20, 1300, WW + 20, WH + 20), (160, 150, 140), r=0)
        p.ret((560, 1150, 1000, 1310), (60, 60, 65), r=12)                # fogão
        p.chord((640, 1040, 920, 1180), 0, 180, (40, 40, 45))              # panela
        m.alpha_composite(p.pronto())
        n = 3200 + (1 if t > 0.5 else 0)
        cx, cy = self.pessoa(m, self.colegas[1], t, 350, 1700, 1.3, n, expr="surpreso" if t > 0.5 else "neutro")
        f = camera(m, 540, 1200, 1.12)
        dr = ImageDraw.Draw(f, "RGBA")
        for i in range(5):             # fumaça
            tt = (t * 1.2 + i * 0.2) % 1.0
            x, y = OUT_W * 0.72 + 30 * math.sin(tt * 6 + i), OUT_H * 0.5 - tt * 260
            r = 20 + tt * 40
            dr.ellipse((x - r, y - r, x + r, y + r), fill=(70, 70, 70, int(180 * (1 - tt))))
        self.mais_um(f, t - 0.5, OUT_W * 0.3, OUT_H * 0.18)
        return f

    def p_senha(self, t, d):
        m = self.fundo((210, 220, 235), (185, 195, 215))
        n = 870 + min(5, int(max(0, t - 0.3) / 0.45))
        self.pessoa(m, self.colegas[2], t, 330, 1760, 1.3, n, expr="bravo" if t > 1.5 else "neutro")
        self.segura(m, self.atm, 800, 1100, 380)
        f = camera(m, 540, 1200, 1.12)
        k = int(max(0, t - 0.3) / 0.45)
        if k <= 5:
            self.mais_um(f, (t - 0.3) - k * 0.45, OUT_W * 0.3, OUT_H * 0.16)
        return f

    def p_honra(self, t, d):
        m = self.sala.copy()
        f = camera(m, 850, 470, 2.3 - 0.3 * ease_io(t / d))
        if t > 0.6:
            texto_pop(f, "MENOR = MELHOR", self.fc, t - 0.6, OUT_W * 0.5, OUT_H * 0.72, 66, (255, 214, 40))
        return f

    def p_sala(self, t, d):
        m = self.sala.copy()
        for i, (a, x, n) in enumerate(zip(self.colegas, (140, 380, 700, 940), self.nums_colegas)):
            self.pessoa(m, a, t + i, x, 1780, 0.8, n)
        self.pessoa(m, self.sofia, t, 540, 1880, 1.1, 8, expr="feliz", ouro=True)
        return camera(m, 540, 1250, 1.08)

    def p_sofia8(self, t, d):
        m = self.fundo((250, 235, 200), (240, 210, 160))
        m.alpha_composite(brilho((1000, 1000), (255, 230, 140), 500, 0.7), (40, 200))
        self.pessoa(m, self.sofia, t, 540, 2350, 2.4, 8, expr="feliz", ouro=True)
        f = camera(m, 540, 900, 1.05)
        particulas(f, t, 30, semente=3)
        return f

    def p_pai_num(self, t, d):
        m = self.fundo((220, 220, 230), (190, 190, 205))
        self.pessoa(m, self.pai, t, 540, 2350, 2.4, 140000, expr="neutro")
        f = camera(m, 540, 900, 1.05 + 0.1 * ease_out(t / 0.5))
        return f

    def p_portao(self, t, d):
        m = self.portao.copy()
        self.pessoa(m, self.pai, t, 760, 1760, 1.1, 140000, expr="feliz", pose="acena" if int(t * 2) % 2 else "idle")
        return camera(m, 560, 1200, 1.1)

    def p_sofia_grita(self, t, d):
        m = self.portao.copy()
        self.pessoa(m, self.pai, t, 860, 1760, 0.95, 140000, expr="neutro")
        rindo = int(t * 5) % 2
        self.pessoa(m, self.sofia, t, 320, 1800, 1.15, 8, expr="ri" if rindo else "feliz", pose="aponta", ouro=True)
        self.pessoa(m, self.livia, t + 2, 560, 1820, 1.0, 1204, expr="triste")
        f = camera(m, 560, 1220, 1.12)
        if t > 3.5:
            texto_pop(f, "CAMPEÃO DE ERROS!", self.fc, t - 3.5, OUT_W * 0.5, OUT_H * 0.1, 60, (230, 50, 50))
        return f

    def p_riem(self, t, d):
        m = self.portao.copy()
        for i, (a, x, n) in enumerate(zip(self.colegas, (130, 330, 750, 950), self.nums_colegas)):
            r = int(t * 5 + i) % 2
            self.pessoa(m, a, t + i, x, 1760, 0.85, n, expr="ri" if r else "feliz", pulo=6 * r)
        self.pessoa(m, self.livia, t, 540, 1820, 1.1, 1204, expr="triste", rot=-4)
        return camera(m, 540, 1220, 1.12)

    def p_esquina(self, t, d):
        m = self.esquina.copy()
        self.pessoa(m, self.pai, t, 900, 1520, 0.55, 140000, expr="neutro")
        x = 220 + 160 * (t / d)
        self.pessoa(m, self.livia, t, x, 1800, 1.1, 1204, expr="triste", pulo=6 * abs(math.sin(t * 6)))
        return camera(m, 560, 1220, 1.1)

    def p_reclamou(self, t, d):
        m = self.fundo((210, 205, 200), (180, 175, 170))
        self.pessoa(m, self.pai, t, 540, 2350, 2.4, 140000, expr="feliz")
        return camera(m, 540, 900, 1.05)

    def p_madrugada(self, t, d):
        m = self.corredor.copy()
        self.livia_c.desenhar(m, t, 540, 1900, escala=1.0, expr="surpreso" if t > 2.8 else "neutro")
        return camera(m, 540, 1150, 1.05 + 0.2 * ease_io(t / d))

    def p_relogio(self, t, d):
        m = self.fundo((40, 45, 70), (25, 28, 45))
        self.segura(m, self.relogio, 540, 900, 600)
        f = camera(m, 540, 950, 1.1)
        texto_pop(f, "5:00", self.fc, t, OUT_W * 0.5, OUT_H * 0.15, 110, (255, 230, 150))
        return f

    def num_pai_cozinha(self, T):
        """Número do pai subindo durante a cena da cozinha (tempo absoluto)."""
        if T < 49.88:
            return 140000
        if T < 54.26:
            marcos = [(51.66, 1), (52.02, 2), (52.82, 3), (53.60, 10)]
            n = 0
            for tm, v in marcos:
                if T >= tm:
                    n = v
            return 140000 + n
        return 140010 + int((T - 54.26) * 2.2)

    def p_cozinha(self, t, d):
        m = self.cozinha.copy()
        self.pessoa(m, self.pai, t, 420, 1560, 1.15, self.num_pai_cozinha(45.80 + t), expr="neutro", pose="entrega")
        self.segura(m, boneca(tranca=0.3), 760, 1100, 300)
        return camera(m, 560, 1150, 1.12 + 0.06 * ease_io(t / d))

    def p_sobe(self, t, d):
        m = self.fundo((60, 60, 90), (35, 35, 60))
        m.alpha_composite(brilho((900, 900), (255, 210, 130), 450, 0.5), (90, 300))
        T = 49.88 + t
        self.pessoa(m, self.pai, t, 540, 2350, 2.4, self.num_pai_cozinha(T), expr="triste")
        f = camera(m, 540, 900, 1.05 + 0.15 * ease_io(t / d))
        for tm, n in ((51.66, 1), (52.02, 1), (52.82, 1), (53.60, 7)):
            self.mais_um(f, T - tm, OUT_W * 0.75, OUT_H * 0.12, n)
        return f

    def p_tranca(self, t, d):
        m = self.fundo((60, 55, 80), (40, 38, 55))
        m.alpha_composite(brilho((1000, 1000), (255, 210, 130), 500, 0.6), (40, 300))
        # trança faz e desfaz
        prog = 0.6 * abs(math.sin(t * 1.4))
        self.segura(m, boneca(tranca=prog), 470, 960, 760)
        for i, ph in enumerate((0, 1.7)):
            x = 760 + 40 * math.sin(t * 7 + ph)
            y = 760 + 60 * i + 30 * math.cos(t * 7 + ph)
            self.segura(m, self.mao_pai, x, y, 150)
        f = camera(m, 540, 960, 1.1)
        self.mais_um(f, (t % 0.8), OUT_W * 0.82, OUT_H * 0.2)
        return f

    def p_celular(self, t, d):
        m = self.cozinha.copy()
        self.segura(m, self.celular_aula, 540, 980, 640)
        return camera(m, 540, 1000, 1.05 + 0.15 * ease_io(t / d))

    def p_mae(self, t, d):
        m = self.fundo((250, 225, 190), (235, 200, 160))
        self.mae.desenhar(m, t, 380, 1760, escala=1.4, expr="feliz", pose="entrega")
        self.livia_c.desenhar(m, t, 720, 1820, escala=1.05, expr="feliz")
        f = camera(m, 540, 1250, 1.12)
        return f

    def p_percebe(self, t, d):
        m = self.fundo((60, 55, 80), (40, 38, 55))
        self.livia_c.desenhar(m, t, 540, 2350, escala=2.5, expr="chora" if t > 1.2 else "triste", piscar=False)
        return camera(m, 540, 950, 1.05 + 0.08 * ease_io(t / d))

    def p_cabelo(self, t, d):
        m = self.sala.copy()
        self.pessoa(m, self.livia, t, 540, 1880, 1.4, 1204, expr="feliz")
        f = camera(m, 600, 1200, 1.2)
        particulas(f, t, 30, semente=8)
        return f

    def p_licao(self, t, d):
        m = self.fundo((255, 215, 150), (240, 175, 110))
        m.alpha_composite(brilho((1000, 1000), (255, 245, 200), 500, 0.8), (40, 300))
        ouro = t > 1.4
        self.pessoa(m, self.pai, t, 540, 2350, 2.4, 140042, expr="feliz" if ouro else "neutro", ouro=ouro)
        f = camera(m, 540, 900, 1.05 + 0.08 * ease_io(t / d))
        particulas(f, t, 40, semente=9)
        return f

    def p_portao_frente(self, t, d):
        m = self.portao.copy()
        self.pessoa(m, self.pai, t, 540, 1760, 1.2, 140042, expr="surpreso")
        return camera(m, 540, 1200, 1.1)

    def p_sofia_ri(self, t, d):
        m = self.fundo((240, 225, 200), (220, 200, 175))
        self.pessoa(m, self.sofia, t, 540, 2350, 2.4, 8, expr="ri", ouro=True)
        return camera(m, 540, 900, 1.05)

    def p_mao(self, t, d):
        m = self.portao.copy()
        self.pessoa(m, self.pai, t, 640, 1760, 1.2, 140042, expr="surpreso")
        self.pessoa(m, self.livia, t, 420, 1800, 1.1, 1204, expr="neutro", pose="entrega")
        return camera(m, 540, 1220, 1.15)

    def p_fala(self, t, d):
        m = self.portao.copy()
        self.pessoa(m, self.pai, t, 680, 1760, 1.2, 140042, expr="chora")
        self.pessoa(m, self.livia, t, 400, 1800, 1.1, 1204, expr="feliz", pose="aponta")
        self.pessoa(m, self.sofia, t, 940, 1700, 0.7, 8, expr="surpreso", ouro=True)
        f = camera(m, 540, 1220, 1.12)
        particulas(f, t, 30, semente=12)
        return f

    def p_ensina(self, t, d):
        m = self.cozinha.copy()
        self.pessoa(m, self.pai, t, 330, 1560, 1.1, 140042, expr="feliz")
        self.pessoa(m, self.livia_c, t, 740, 1580, 0.95, 1204, expr="feliz", pose="entrega")
        self.segura(m, boneca(tranca=0.5), 560, 1150, 260)
        return camera(m, 540, 1150, 1.12)

    def p_42(self, t, d):
        m = self.fundo((255, 215, 160), (240, 180, 120))
        n = 1204 + min(42, int(t / (d * 0.9) * 42))
        self.pessoa(m, self.livia_c, t, 540, 2350, 2.4, n, expr="neutro")
        f = camera(m, 540, 900, 1.05)
        self.mais_um(f, (t % 0.25) * 2.4, OUT_W * 0.78, OUT_H * 0.1)
        return f

    def p_sorri(self, t, d):
        m = self.fundo((255, 210, 140), (245, 170, 100))
        m.alpha_composite(brilho((1080, 1080), (255, 245, 200), 540, 0.9), (0, 300))
        self.pessoa(m, self.livia_c, t, 540, 2350, 2.4, 1246, expr="ri" if t > 0.6 else "feliz", ouro=True)
        f = camera(m, 540, 900, 1.05 + 0.1 * ease_io(t / d))
        particulas(f, t, 50, semente=20)
        if t > d - 0.8:
            f = ImageEnhance.Brightness(f).enhance(1 - ease_io((t - (d - 0.8)) / 0.8))
        return f

    def eventos_sfx(self):
        ev = []
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if i and tr in ("whip", "zoom"):
                ev.append(("whoosh", ini - 0.08))
            elif i and tr == "corte":
                ev.append(("pop", ini))
        ev += [("toc", 5.56)] + [("toc", 7.04 + k * 0.45) for k in range(5)]
        ev += [("toc", x) for x in (51.66, 52.02, 52.82, 53.60)]
        ev += [("brilho", 16.74), ("brilho", 76.8), ("brilho", 97.48)]
        return ev


def carregar_palavras(caminho):
    pal = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            pal.append(dict(w=w["w"], s=w["s"], e=w["e"]))
    out = []
    i = 0
    while i < len(pal):
        w = pal[i]
        if w["w"] == "Era" and i + 1 < len(pal) and pal[i + 1]["w"] == "um":
            out.append(dict(w="Eram", s=w["s"], e=pal[i + 1]["e"]))
            i += 2
            continue
        out.append(dict(w={"12.": "doze.", "42": "quarenta e duas"}.get(w["w"], w["w"]), s=w["s"], e=w["e"]))
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_numero_do_meu_pai.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeNumero(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.2)
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

    tmp = tempfile.mkdtemp(prefix="numero_")
    wav = os.path.join(tmp, "mix.wav")
    vc.mixar(filme, a.narracao, wav)
    print(f"• renderizando {total} frames ({filme.dur_total:.1f}s)…", flush=True)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}",
         "-r", str(FPS), "-i", "-", "-i", wav, "-vf", "scale=1080:1920:flags=lanczos",
         "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.saida],
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
