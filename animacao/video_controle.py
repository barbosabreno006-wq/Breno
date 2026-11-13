#!/usr/bin/env python3
"""
"O Controle do Meu Pai" — mundo onde todos têm um controle que pula as partes chatas da vida.

Marcas do formato: o controle com botão ⏩ e contador "TEMPO PULADO", o "olho cinza" de quem
pulou (corpo no automático) e o efeito de avanço rápido com falha de imagem.

    python3 animacao/video_controle.py --narracao narr.wav --transcricao transcricao.json --fonte Poppins.ttf
"""
import argparse
import json
import math
import os
import random
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_video as g  # noqa: E402
import video_carta as vc  # noqa: E402
import video_corsa as vco  # noqa: E402
import video_sono as vs  # noqa: E402
import video_milhao as vm  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, Ator, gradiente, brilho,
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(88)

MIGUEL = dict(pele=(226, 178, 138), cabelo=(70, 48, 32), camisa=(240, 240, 245), calca=(60, 80, 130),
              sapato=(220, 70, 60), tipo="menino")
MIGUEL_ADULTO = dict(MIGUEL, tipo="pai", bigode=False, camisa=(80, 110, 150), calca=(50, 55, 70),
                     sapato=(50, 45, 40))
PAI = dict(pele=(206, 150, 110), cabelo=(60, 45, 35), camisa=(90, 120, 80), calca=(70, 75, 90),
           sapato=(60, 50, 45), tipo="pai")
PAI_VELHO = dict(PAI, cabelo=(200, 200, 205))
MAE = dict(pele=(220, 170, 130), cabelo=(215, 215, 220), camisa=(180, 120, 160), calca=(0, 0, 0),
           sapato=(120, 80, 70), tipo="vovo", vestido=(180, 120, 160))
FILHA = dict(pele=(226, 178, 138), cabelo=(90, 60, 35), camisa=(250, 200, 80), calca=(0, 0, 0),
             sapato=(220, 70, 90), tipo="moca", vestido=(250, 200, 80))
ESPOSA = dict(pele=(176, 120, 85), cabelo=(30, 25, 25), camisa=(90, 170, 190), calca=(0, 0, 0),
              sapato=(60, 60, 60), tipo="moca", vestido=(90, 170, 190))
GENTE = [dict(pele=(150, 100, 70), cabelo=(30, 25, 25), camisa=(240, 190, 60), calca=(60, 70, 120),
              sapato=(200, 60, 60), tipo="pai", bigode=False),
         dict(pele=(235, 190, 150), cabelo=(150, 60, 40), camisa=(220, 90, 150), calca=(0, 0, 0),
              sapato=(200, 60, 120), tipo="moca", vestido=(230, 110, 170)),
         dict(pele=(190, 130, 90), cabelo=(60, 40, 30), camisa=(120, 90, 200), calca=(80, 70, 60),
              sapato=(60, 60, 60), tipo="pai")]

vc.DESTAQUE_VERMELHO = {"voltar.", "pulou.", "Pulou.", "medo.", "morreu", "cinza.", "despedida.", "zero."}


# --------------------------------------------------------------------------
# Objetos
# --------------------------------------------------------------------------
def controle(fc, numero="", aperto=0.0, w=420, caixa=False):
    h = int(w * 1.7)
    p = Pincel(w, h)
    if caixa:   # embalagem
        p.ret((0, 0, w, h), (220, 50, 50), r=24)
        p.ret((24, 120, w - 24, h - 24), (235, 240, 245), r=18, ow=5)
    x0 = 50 if caixa else 20
    y0 = 150 if caixa else 20
    ww, hh = w - 2 * x0, h - y0 - (50 if caixa else 20)
    p.ret((x0, y0, x0 + ww, y0 + hh), (60, 62, 72), r=50)
    p.ret((x0 + 40, y0 + 50, x0 + ww - 40, y0 + 180), (120, 190, 110), r=14, ow=6)     # visor
    cx, cy = x0 + ww / 2, y0 + hh * 0.62
    r = ww * 0.32 * (1 - 0.08 * aperto)
    p.elipse((cx - r - 12, cy - r - 12, cx + r + 12, cy + r + 12), (40, 40, 48), ow=6)
    p.elipse((cx - r, cy - r, cx + r, cy + r), (220, 40, 40) if aperto < 0.5 else (180, 25, 25), ow=6)
    for dx in (-26, 18):    # ⏩
        p.poli([(cx + dx - 18, cy - 34), (cx + dx + 26, cy), (cx + dx - 18, cy + 34)], (255, 255, 255), ow=0)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f1, f2 = vc.fonte(fc, 22), vc.fonte(fc, 60)
    d.text((cx - f1.getlength("TEMPO PULADO") / 2, y0 + 60), "TEMPO PULADO", font=f1, fill=(30, 60, 30))
    d.text((cx - f2.getlength(numero) / 2, y0 + 88), numero, font=f2, fill=(30, 60, 30))
    if caixa:
        f3 = vc.fonte(fc, 50)
        d.text((w / 2 - f3.getlength("CONTROLE") / 2, 40), "CONTROLE", font=f3, fill=(255, 255, 255))
    return img


def dedao(w=260):
    p = Pincel(w, w * 2.2)
    p.ret((40, 60, w - 40, w * 2.2), (226, 178, 138), r=90)
    p.ret((70, 70, w - 70, 220), (245, 215, 195), r=60, ow=0)
    return p.pronto()


def lona(w=1000):
    p = Pincel(w, 520)
    p.poli([(30, 500), (80, 160), (260, 60), (720, 50), (900, 180), (970, 500)], (150, 155, 165))
    for x in (250, 500, 750):
        p.linha([(x, 80), (x - 40, 480)], fill=(120, 125, 135), w=6)
    return p.pronto()


def bolo(fc, txt="60", w=520):
    p = Pincel(w, 520)
    p.ret((60, 260, w - 60, 480), (240, 180, 200), r=20)
    p.ret((60, 260, w - 60, 320), (250, 250, 250), r=20)
    for i, x in enumerate(range(150, w - 120, 90)):
        p.ret((x, 160, x + 20, 260), (120, 170, 230), r=6)
        p.elipse((x - 4, 120, x + 24, 165), (255, 180, 50), ow=0)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 70)
    d.text((w / 2 - f.getlength(txt) / 2, 350), txt, font=f, fill=(150, 60, 90))
    return img


def arvore_natal(w=560):
    p = Pincel(w, 760)
    for k in range(3):
        y = 120 + k * 170
        p.poli([(w / 2, y - 60), (w / 2 + 120 + k * 60, y + 200), (w / 2 - 120 - k * 60, y + 200)], (50, 140, 70))
    p.ret((w / 2 - 40, 640, w / 2 + 40, 740), (120, 80, 50), r=8)
    p.poli([(w / 2, 20), (w / 2 + 30, 80), (w / 2 - 30, 80)], (250, 210, 40))
    rng = random.Random(2)
    for _ in range(14):
        x, y = rng.uniform(w / 2 - 160, w / 2 + 160), rng.uniform(160, 600)
        p.elipse((x - 14, y - 14, x + 14, y + 14), rng.choice([(220, 50, 50), (250, 210, 40), (80, 150, 230)]), ow=3)
    return p.pronto()


def caixao():
    p = Pincel(900, 400)
    p.poli([(40, 200), (160, 80), (740, 80), (860, 200), (740, 320), (160, 320)], (110, 80, 60))
    for x in (250, 450, 650):
        p.elipse((x - 60, 30, x + 60, 120), (240, 240, 240), ow=4)
    return p.pronto()


def radio(t):
    p = Pincel(800, 400)
    p.ret((20, 40, 780, 380), (60, 55, 50), r=30)
    p.ret((70, 90, 450, 330), (25, 25, 30), r=16)
    for i in range(10):
        h = 40 + 80 * abs(math.sin(t * 6 + i * 0.7))
        p.ret((100 + i * 34, 300 - h, 120 + i * 34, 300), (120, 220, 120), r=4, ow=0)
    p.ret((500, 120, 740, 220), (200, 190, 170), r=12)
    for x in (560, 680):
        p.elipse((x - 30, 140, x + 30, 200), (70, 60, 50), ow=4)
    p.elipse((520, 250, 600, 330), (90, 85, 80))
    p.elipse((640, 250, 720, 330), (90, 85, 80))
    return p.pronto()


def garagem():
    base = gradiente(WW, WH, (200, 185, 160), (170, 155, 135))
    p = Pincel(WW, WH)
    p.ret((60, 260, 560, 640), (120, 90, 60), r=10)
    for i, x in enumerate(range(100, 540, 80)):
        p.ret((x, 300 + (i % 2) * 40, x + 22, 460 + (i % 2) * 40), (90, 95, 105), r=8, ow=5)
    p.ret((700, 220, 1000, 560), (230, 230, 220), r=8, ow=8)                 # calendário de parede
    p.ret((700, 220, 1000, 300), (220, 60, 50), r=8)
    p.ret((-20, 1350, WW + 20, WH + 20), (120, 115, 110), r=0)
    p.elipse((300, 1520, 760, 1620), (90, 85, 85), ow=0)
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((900, 900), (255, 220, 150), 450, 0.4), (90, 400))
    return base


def casa_porta():
    base = gradiente(WW, WH, (150, 200, 240), (225, 238, 250))
    p = Pincel(WW, WH)
    p.ret((80, 500, 1000, 1420), (240, 220, 180), r=8)
    p.poli([(40, 510), (540, 260), (1040, 510)], (170, 80, 70))
    p.ret((380, 900, 700, 1420), (120, 80, 60), r=10)
    p.ret((150, 650, 330, 830), (170, 210, 240), r=8, ow=8)
    p.ret((750, 650, 930, 830), (170, 210, 240), r=8, ow=8)
    p.ret((-20, 1410, WW + 20, WH + 20), (120, 180, 100), r=0)
    base.alpha_composite(p.pronto())
    return base


def escritorio():
    base = gradiente(WW, WH, (215, 220, 230), (195, 200, 210))
    p = Pincel(WW, WH)
    p.ret((-20, 1400, WW + 20, WH + 20), (150, 145, 140), r=0)
    p.ret((100, 1150, 980, 1230), (150, 110, 80), r=10)
    p.ret((560, 960, 820, 1150), (40, 40, 50), r=10)
    base.alpha_composite(p.pronto())
    return base


def avanco(f, t, forca=1.0, fc=None):
    """Efeito de 'pular': falha de imagem + linhas + ⏩ x16."""
    f = vs.glitch(f, t, 0.8 * forca)
    d = ImageDraw.Draw(f, "RGBA")
    rng = random.Random(int(t * 30))
    for _ in range(int(10 * forca)):
        y = rng.uniform(0, OUT_H)
        d.line((0, y, OUT_W, y), fill=(255, 255, 255, 60), width=rng.randint(2, 6))
    if fc:
        fx = vc.fonte(fc, 70)
        d.text((OUT_W - 220, 60), ">> x16", font=fx, fill=(255, 255, 255, 230))
    return f


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeControle(vc.Filme):
    def __init__(self, palavras, fc, dur_total):
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.mig, self.mig_ad = Ator(MIGUEL), Ator(MIGUEL_ADULTO)
        self.pai, self.pai_v, self.mae = Ator(PAI), Ator(PAI_VELHO), Ator(MAE)
        self.filha, self.esposa = Ator(FILHA), Ator(ESPOSA)
        self.gente = [Ator(c) for c in GENTE]
        self.chev = vco.Carro((200, 40, 40))
        self.chev_velho = vco.Carro((140, 95, 90), (60, 60, 65))
        self.garagem = garagem()
        self.rua = vco.rua(fc)
        self.porta = casa_porta()
        self.escr = escritorio()
        self.ctrl = {k: controle(fc, k) for k in ("12H", "3 ANOS", "21 ANOS")}
        self.ctrl_ap = controle(fc, "12H", aperto=1)
        self.ctrl_caixa = controle(fc, "0", caixa=True)
        self.dedao = dedao()
        self.lona = lona()
        self.bolo10 = bolo(fc, "10")
        self.bolo60 = bolo(fc, "PAI 60")
        self.arvore = arvore_natal()
        self.caixao = caixao()
        self.lixeira = vm.lixeira()
        self.cel_pai = vs.celular(fc, "LIGANDO", [("PAI", 90, (40, 40, 55))], botao="RECUSAR", cor=(40, 160, 90))
        self.cel_feed = vs.celular(fc, "FEED", [("…", 60, (40, 40, 55))], cor=(40, 40, 50))
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        P = [
            (0.00, self.p_mundo, "", "corte"),
            (4.38, self.p_aperta, "", "corte"),
            (9.14, self.p_olho_cinza, "", "corte"),
            (13.58, self.p_segunda, "", "whip"),
            (16.02, self.p_familia, "", "corte"),
            (18.54, self.p_sem_voltar, "", "zoom"),
            (22.18, self.p_aniversario, "quente", "whip"),
            (25.94, self.p_pai_chama, "", "corte"),
            (28.36, self.p_chevette_velho, "", "corte"),
            (31.94, self.p_aperta_menino, "", "corte"),
            (34.28, self.p_pai_fala, "", "corte"),
            (38.52, self.p_domingos, "", "whip"),
            (44.02, self.p_pulou_todos, "", "corte"),
            (45.62, self.p_resto, "", "corte"),
            (48.98, self.p_sozinho, "", "zoom"),
            (53.38, self.p_ligacao, "", "corte"),
            (54.90, self.p_bolo_pai, "", "corte"),
            (56.50, self.p_natal, "", "corte"),
            (58.10, self.p_pisca, "", "corte"),
            (60.84, self.p_familia_adulto, "", "corte"),
            (64.04, self.p_festa_filha, "quente", "whip"),
            (68.44, self.p_medo, "", "corte"),
            (70.70, self.p_lixo, "", "corte"),
            (72.84, self.p_porta, "", "whip"),
            (77.58, self.p_mae, "triste", "corte"),
            (81.38, self.p_velorio, "triste", "zoom"),
            (85.46, self.p_lona, "quente", "dissolve"),
            (90.30, self.p_portaluvas, "quente", "corte"),
            (93.32, self.p_zero, "quente", "corte"),
            (94.84, self.p_chave, "", "corte"),
            (96.14, self.p_pegou, "quente", "corte"),
            (97.54, self.p_radio, "quente", "corte"),
            (100.08, self.p_fita_pai, "sepia", "dissolve"),
            (105.70, self.p_trinta_anos, "sepia", "corte"),
            (111.12, self.p_hoje, "quente", "dissolve"),
            (115.36, self.p_filha_de_novo, "quente", "corte"),
            (117.06, self.p_fica, "quente", "corte"),
            (120.52, self.p_voce, "", "zoom"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))

    def fundo(self, c1=(240, 225, 200), c2=(220, 200, 175)):
        return gradiente(WW, WH, c1, c2)

    def segura_ctrl(self, m, cx, cy, larg, num="12H", aperto=False, rot=0):
        img = self.ctrl_ap if aperto else self.ctrl.get(num) or self.ctrl["12H"]
        self.segura(m, img, cx, cy, larg, rot=rot)

    def aperto_close(self, t, d, num="12H", t_ap=0.6):
        m = self.fundo((60, 60, 75), (35, 35, 45))
        ap = t > t_ap
        self.segura_ctrl(m, 540, 1000, 600, num, aperto=ap)
        y = 1300 - (180 if ap else 80 * ease_out(t / t_ap))
        self.segura(m, self.dedao, 560, y + 300, 230)
        f = camera(m, 540, 1000, 1.05)
        if ap:
            f = avanco(f, t, 0.6 if t - t_ap > 0.4 else 1.2, self.fc)
        return f

    # ------------------------- planos -------------------------
    def p_mundo(self, t, d):
        m = self.rua.copy()
        for i, (a, x) in enumerate(zip(self.gente, (220, 540, 860))):
            a.desenhar(m, t + i, x, 1760, escala=1.0, expr="feliz", pose="entrega")
            hx, hy = self.mao(x, 1760, 1.0, t + i)
            self.segura_ctrl(m, hx + 30, hy - 30, 90)
        return camera(m, 540, 1250, 1.1 + 0.08 * ease_io(t / d))

    def p_aperta(self, t, d):
        return self.aperto_close(t, d, t_ap=1.4)

    def p_olho_cinza(self, t, d):
        m = self.fundo((190, 195, 205), (160, 165, 175))
        self.gente[0].desenhar(m, t, 540, 2350, escala=2.5, expr="cinza", piscar=False)
        f = camera(m, 540, 950, 1.05 + 0.1 * ease_io(t / d))
        if t > 2.6:
            texto_pop(f, "MAS VOCÊ NÃO TÁ", self.fc, t - 2.6, OUT_W / 2, OUT_H * 0.12, 64, (230, 50, 50))
        return vs.glitch(f, t, 0.3)

    def p_segunda(self, t, d):
        m = self.escr.copy()
        self.gente[2].desenhar(m, t, 380, 1700, escala=1.3, expr="cinza", piscar=False)
        f = camera(m, 540, 1200, 1.1)
        dias = ["SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA!"]
        k = min(4, int(t / (d / 5)))
        texto_pop(f, dias[k], self.fc, (t % (d / 5)), OUT_W / 2, OUT_H * 0.14, 90,
                  (255, 214, 40) if k == 4 else (255, 255, 255))
        return avanco(f, t, 0.5) if k < 4 else f

    def p_familia(self, t, d):
        m = self.fundo((240, 215, 180), (220, 190, 150))
        p = Pincel(WW, WH)
        p.ret((60, 1300, 1020, 1380), (180, 110, 70), r=10)
        m.alpha_composite(p.pronto())
        for i, (a, x) in enumerate(zip(self.gente + [self.mae], (150, 400, 680, 930))):
            a.desenhar(m, t + i, x, 1640, escala=0.85, expr="cinza", piscar=False)
        f = camera(m, 540, 1200, 1.1)
        return avanco(f, t, 0.4)

    def p_sem_voltar(self, t, d):
        m = self.fundo((40, 40, 55), (20, 20, 30))
        self.segura_ctrl(m, 540, 1000, 560)
        f = camera(m, 540, 1000, 1.0 + 0.1 * ease_io(t / d))
        if t > 1.2:
            texto_pop(f, "SEM BOTÃO DE VOLTAR", self.fc, t - 1.2, OUT_W / 2, OUT_H * 0.12, 58, (230, 50, 50))
        return f

    def p_aniversario(self, t, d):
        m = self.fundo((255, 220, 180), (245, 190, 150))
        self.mig.desenhar(m, t, 540, 1760, escala=1.4, expr="ri", pose="entrega")
        hx, hy = self.mao(540, 1760, 1.4, t)
        self.segura_ctrl(m, hx + 30, hy - 40, 140)
        self.segura(m, self.bolo10, 220, 1450, 300)
        f = camera(m, 540, 1250, 1.1)
        vm.confete(f, t, 50)
        return f

    def p_pai_chama(self, t, d):
        m = self.garagem.copy()
        self.chev_velho.desenhar(m, 620, 1560, escala=0.9)
        self.pai.desenhar(m, t, 220, 1740, escala=1.2, expr="feliz", pose="acena")
        return camera(m, 540, 1200, 1.1)

    def p_chevette_velho(self, t, d):
        m = self.garagem.copy()
        self.chev_velho.desenhar(m, 540, 1560, escala=1.0)
        f = camera(m, 540, 1300, 1.3 - 0.1 * ease_io(t / d))
        texto_pop(f, "CHEVETTE DO VÔ", self.fc, t, OUT_W / 2, OUT_H * 0.14, 70, (255, 214, 40))
        if t > 1.6:
            texto_pop(f, "20 ANOS PARADO", self.fc, t - 1.6, OUT_W / 2, OUT_H * 0.22, 54)
        return f

    def p_aperta_menino(self, t, d):
        return self.aperto_close(t, d, t_ap=1.6)

    def p_pai_fala(self, t, d):
        m = self.garagem.copy()
        self.chev_velho.desenhar(m, 760, 1560, escala=0.75)
        self.pai.desenhar(m, t, 300, 1740, escala=1.25, expr="ri" if int(t * 4) % 2 else "feliz", pose="aponta")
        self.mig.desenhar(m, t, 620, 1780, escala=1.0, expr="cinza", piscar=False)
        f = camera(m, 540, 1220, 1.12)
        return vs.glitch(f, t, 0.25)

    def p_domingos(self, t, d):
        m = self.garagem.copy()
        cena = int(t / (d / 3))
        self.chev_velho.desenhar(m, 560, 1560, escala=0.95, pulo=4 * math.sin(t * 30) if cena == 2 else 0)
        self.pai.desenhar(m, t, 220, 1740, escala=1.15, expr="neutro", pose="bate" if int(t * 5) % 2 else "bate2")
        f = camera(m, 540, 1250, 1.15)
        nomes = ["GRAXA", "CHAVE DE BOCA", "NÃO PEGOU…"]
        texto_pop(f, nomes[min(2, cena)], self.fc, t % (d / 3), OUT_W / 2, OUT_H * 0.14, 70,
                  (230, 50, 50) if cena == 2 else (255, 255, 255))
        return f

    def p_pulou_todos(self, t, d):
        m = self.fundo((60, 60, 75), (35, 35, 45))
        rng = random.Random(3)
        for i in range(8):
            k = (t * 2 + i * 0.15) % 1.2
            pp = Pincel(260, 280)
            pp.ret((10, 10, 250, 270), (250, 250, 250), r=12)
            pp.ret((10, 10, 250, 70), (220, 50, 50), r=12)
            self.segura(m, pp.pronto(), 200 + rng.uniform(0, 700) + k * 400, 1600 - k * 1200, 220, rot=k * 200)
        f = camera(m, 540, 960, 1.0)
        texto_pop(f, "DOMINGO", self.fc, t, OUT_W / 2, OUT_H * 0.45, 100, (255, 255, 255))
        return avanco(f, t, 1.0, self.fc)

    def p_resto(self, t, d):
        k = min(2, int(t / (d / 3)))
        m = [self.escr, self.rua, self.escr][k].copy()
        e = 1.0 + 0.1 * k
        ator = self.mig if k == 0 else self.mig_ad
        ator.desenhar(m, t, 540, 1760, escala=1.2 * e, expr="cinza", piscar=False)
        f = camera(m, 540, 1200, 1.1)
        texto_pop(f, ["PROVA", "FILA", "TRABALHO"][k], self.fc, t % (d / 3), OUT_W / 2, OUT_H * 0.14, 80)
        return avanco(f, t, 0.8, self.fc)

    def p_sozinho(self, t, d):
        m = self.fundo((40, 15, 20), (20, 5, 10))
        k = 0.5 + 0.5 * math.sin(t * 10)
        m.alpha_composite(brilho((900, 900), (255, 40, 40), 450, 0.7 * k), (90, 550))
        ap = int(t * 3) % 2 == 0
        self.segura_ctrl(m, 540, 1000, 600, "3 ANOS", aperto=ap)
        f = camera(m, 540, 1000, 1.05)
        texto_pop(f, "APERTANDO SOZINHO", self.fc, t, OUT_W / 2, OUT_H * 0.12, 58, (230, 50, 50))
        return avanco(f, t, 0.5) if ap else f

    def pulou(self, f, t, t_pulo):
        if t > t_pulo:
            f = avanco(f, t, 1.4, self.fc)
            texto_pop(f, "PULOU", self.fc, t - t_pulo, OUT_W / 2, OUT_H * 0.5, 130, (230, 50, 50))
        return f

    def p_ligacao(self, t, d):
        m = self.fundo((60, 60, 75), (35, 35, 45))
        self.segura(m, self.cel_pai, 540, 950, 620, rot=4 * math.sin(t * 40) if t < 0.9 else 0)
        f = camera(m, 540, 960, 1.05)
        return self.pulou(f, t, 54.34 - 53.38)

    def p_bolo_pai(self, t, d):
        m = self.fundo((255, 220, 180), (245, 190, 150))
        self.segura(m, self.bolo60, 540, 1000, 700)
        f = camera(m, 540, 960, 1.05)
        return self.pulou(f, t, 55.72 - 54.90)

    def p_natal(self, t, d):
        m = self.fundo((40, 50, 80), (25, 30, 50))
        self.segura(m, self.arvore, 540, 980, 640)
        f = camera(m, 540, 960, 1.05)
        particulas(f, t, 40, (255, 255, 255), semente=5)
        return self.pulou(f, t, 57.60 - 56.50)

    def p_pisca(self, t, d):
        m = self.fundo((210, 215, 225), (180, 185, 195))
        olho = "cinza" if t < 0.7 else ("surpreso" if t < 1.6 else "neutro")
        self.mig_ad.desenhar(m, t, 540, 2350, escala=2.5, expr=olho, piscar=False)
        f = camera(m, 540, 950, 1.05)
        if t > 0.9:
            texto_pop(f, "40 ANOS", self.fc, t - 0.9, OUT_W / 2, OUT_H * 0.12, 100, (255, 214, 40))
        return f

    def p_familia_adulto(self, t, d):
        m = self.porta.copy()
        self.esposa.desenhar(m, t, 260, 1760, escala=1.15, expr="feliz")
        self.mig_ad.desenhar(m, t, 560, 1760, escala=1.25, expr="neutro")
        self.filha.desenhar(m, t, 820, 1780, escala=0.85, expr="feliz")
        f = camera(m, 540, 1250, 1.1)
        if t > 2.0:
            texto_pop(f, "QUASE NENHUMA LEMBRANÇA", self.fc, t - 2.0, OUT_W / 2, OUT_H * 0.12, 50, (230, 50, 50))
        return f

    def p_festa_filha(self, t, d):
        m = self.fundo((255, 220, 180), (245, 190, 150))
        self.mig_ad.desenhar(m, t, 260, 1760, escala=1.2, expr="feliz" if t < 3.3 else "surpreso")
        self.filha.desenhar(m, t, 720, 1800, escala=1.1, expr="ri", pose="entrega")
        self.segura(m, self.bolo10, 480, 1500, 260)
        if t > 3.3:
            hx, hy = self.mao(720, 1800, 1.1, t)
            self.segura_ctrl(m, hx + 30, hy - 40, 130)
        f = camera(m, 540, 1250, 1.1)
        vm.confete(f, t, 40)
        return f

    def p_medo(self, t, d):
        m = self.fundo((60, 60, 80), (35, 35, 50))
        self.mig_ad.desenhar(m, t, 540, 2350, escala=2.5, expr="surpreso", piscar=False)
        f = camera(m, 540, 950, 1.05 + 0.25 * ease_out(t / 0.4))
        return f

    def p_lixo(self, t, d):
        m = self.rua.copy()
        self.segura(m, self.lixeira, 760, 1600, 300)
        k = ease_out(min(1, t / 0.8))
        x = 300 + 460 * k
        y = 1100 + 400 * k - 300 * math.sin(k * math.pi)
        if k < 1:
            self.segura_ctrl(m, x, y, 120, rot=k * 540)
        self.mig_ad.desenhar(m, t, 260, 1760, escala=1.2, expr="bravo", pose="aponta" if t < 0.6 else "idle")
        return camera(m, 540, 1250, 1.12)

    def p_porta(self, t, d):
        m = self.porta.copy()
        aberta = t > 74.88 - 72.84
        if aberta:
            p = Pincel(WW, WH)
            p.ret((380, 900, 700, 1420), (40, 30, 30), r=10, ow=0)
            m.alpha_composite(p.pronto())
            self.mae.desenhar(m, t, 540, 1430, escala=0.85, expr="triste")
        self.mig_ad.desenhar(m, t, 260, 1760, escala=1.2, expr="ri" if not aberta else "surpreso", pose="acena")
        return camera(m, 520, 1200, 1.1)

    def p_mae(self, t, d):
        m = self.fundo((200, 195, 195), (170, 165, 165))
        self.mae.desenhar(m, t, 540, 2350, escala=2.5, expr="chora", piscar=False)
        return camera(m, 540, 950, 1.05 + 0.08 * ease_io(t / d))

    def p_velorio(self, t, d):
        m = self.fundo((120, 120, 130), (90, 90, 100))
        self.segura(m, self.caixao, 540, 1400, 760)
        for i, x in enumerate((180, 900)):
            self.gente[i].desenhar(m, t, x, 1700, escala=0.9, expr="triste")
        self.mig_ad.desenhar(m, t, 540, 1820, escala=1.1, expr="cinza", piscar=False)
        f = camera(m, 540, 1250, 1.1 + 0.15 * ease_io(t / d))
        return vs.glitch(f, t, 0.3)

    def p_lona(self, t, d):
        m = self.garagem.copy()
        self.chev.desenhar(m, 540, 1560, escala=1.0)
        k = ease_io(min(1, max(0, t - 1.4) / 0.8))
        if k < 1:
            self.segura(m, self.lona, 540 + 900 * k, 1300 - 200 * k, 1000, rot=-20 * k)
        if k > 0.5:
            m.alpha_composite(brilho((1000, 700), (255, 240, 180), 500, 0.6 * k), (40, 1000))
        f = camera(m, 540, 1300, 1.15)
        if k >= 1:
            particulas(f, t, 40, semente=31)
        return f

    def p_portaluvas(self, t, d):
        m = self.fundo((60, 55, 50), (40, 35, 32))
        p = Pincel(WW, WH)
        p.ret((140, 700, 940, 1300), (90, 80, 70), r=30)
        p.ret((200, 760, 880, 1240), (30, 28, 25), r=20, ow=0)
        m.alpha_composite(p.pronto())
        self.segura(m, self.ctrl_caixa, 540, 1000, 360, rot=-6)
        f = camera(m, 540, 1000, 1.05 + 0.15 * ease_io(t / d))
        return f

    def p_zero(self, t, d):
        m = self.fundo((255, 225, 170), (240, 190, 130))
        m.alpha_composite(brilho((1000, 1000), (255, 245, 200), 500, 0.8), (40, 300))
        self.segura(m, self.ctrl_caixa, 540, 1000, 560)
        f = camera(m, 540, 900, 1.25 + 0.3 * ease_out(t / 0.5))
        return f

    def p_chave(self, t, d):
        m = self.fundo((40, 40, 50), (25, 25, 30))
        p = Pincel(WW, WH)
        p.elipse((240, 560, 840, 1160), (50, 50, 60), ow=10)
        p.elipse((440, 760, 640, 960), (120, 125, 135), ow=8)
        m.alpha_composite(p.pronto())
        ang = -70 * ease_out(min(1, max(0, t - 0.3) / 0.3))
        self.segura(m, vco.chave_carro().rotate(ang, expand=True, resample=Image.BICUBIC), 600, 860, 420)
        return camera(m, 540, 900, 1.1)

    def p_pegou(self, t, d):
        m = self.garagem.copy()
        self.chev.desenhar(m, 540, 1560, escala=1.0, pulo=4 * math.sin(t * 60))
        f = camera(m, 540, 1300, 1.15)
        d_ = ImageDraw.Draw(f, "RGBA")
        for i in range(4):
            tt = (t * 1.5 + i * 0.25) % 1.0
            x, y = OUT_W * 0.12 - tt * 120, OUT_H * 0.68 - tt * 40
            r = 12 + tt * 30
            d_.ellipse((x - r, y - r, x + r, y + r), fill=(220, 220, 225, int(170 * (1 - tt))))
        texto_pop(f, "PEGOU!", self.fc, t, OUT_W / 2, OUT_H * 0.14, 110, (255, 214, 40))
        return f

    def p_radio(self, t, d):
        m = self.fundo((60, 50, 45), (40, 32, 28))
        m.alpha_composite(brilho((900, 700), (255, 210, 130), 450, 0.6), (90, 600))
        self.segura(m, radio(t), 540, 960, 860)
        f = camera(m, 540, 960, 1.05 + 0.1 * ease_io(t / d))
        return f

    def p_fita_pai(self, t, d):
        m = self.garagem.copy()
        self.chev.desenhar(m, 760, 1560, escala=0.75)
        self.pai_v.desenhar(m, t, 360, 1740, escala=1.35, expr="feliz" if t < 3.2 else "ri", pose="acena")
        f = camera(m, 480, 1220, 1.15)
        return f

    def p_trinta_anos(self, t, d):
        m = self.garagem.copy()
        anos = int(t / d * 30)
        velho = anos > 15
        self.chev_velho.desenhar(m, 760, 1560, escala=0.75)
        (self.pai_v if velho else self.pai).desenhar(m, t, 300, 1740, escala=1.25, expr="feliz", pose="aponta")
        (self.mig_ad if anos > 8 else self.mig).desenhar(m, t, 620, 1780, escala=1.05 if anos > 8 else 0.95,
                                                        expr="cinza", piscar=False)
        f = camera(m, 540, 1220, 1.12)
        texto_pop(f, f"{anos} ANOS", self.fc, 0.5, OUT_W / 2, OUT_H * 0.12, 90, (255, 255, 255))
        return f

    def p_hoje(self, t, d):
        m = self.rua.copy()
        self.chev.desenhar(m, 620, 1600, escala=0.85)
        self.mig_ad.desenhar(m, t, 220, 1760, escala=1.2, expr="feliz", pose="acena")
        f = camera(m, 540, 1230, 1.12)
        particulas(f, t, 30, semente=40)
        return f

    def p_filha_de_novo(self, t, d):
        m = self.fundo((255, 215, 165), (245, 185, 130))
        self.filha.desenhar(m, t, 540, 2350, escala=2.5, expr="neutro", pose="entrega", piscar=False)
        return camera(m, 540, 950, 1.05)

    def p_fica(self, t, d):
        m = self.rua.copy()
        self.chev.desenhar(m, 540, 1600, escala=1.0)
        self.mig_ad.desenhar(m, t, 300, 1780, escala=1.1, expr="feliz")
        self.filha.desenhar(m, t, 760, 1790, escala=0.85, expr="cinza", piscar=False)
        f = camera(m, 540, 1250, 1.12 + 0.08 * ease_io(t / d))
        particulas(f, t, 40, semente=41)
        return f

    def p_voce(self, t, d):
        m = self.fundo((20, 22, 30), (10, 10, 15))
        m.alpha_composite(brilho((900, 900), (120, 160, 255), 450, 0.5), (90, 500))
        self.segura(m, self.cel_feed, 540, 950, 600)
        f = camera(m, 540, 960, 1.05 + 0.1 * ease_io(t / d))
        d_ = ImageDraw.Draw(f)
        rng = random.Random(int(t * 4))
        for i in range(5):     # feed rolando
            y = OUT_H * 0.35 + ((i * 120 - t * 600) % 600)
            d_.rounded_rectangle((OUT_W * 0.32, y, OUT_W * 0.68, y + 90), radius=10,
                                 fill=rng.choice([(200, 210, 230), (230, 200, 210), (210, 230, 200)]))
        if t > d - 0.6:
            f = ImageEnhance.Brightness(f).enhance(max(0, 1 - (t - (d - 0.6)) / 0.6))
        return f

    def eventos_sfx(self):
        ev = []
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if i and tr in ("whip", "zoom"):
                ev.append(("whoosh", ini - 0.08))
            elif i and tr == "corte":
                ev.append(("pop", ini))
        ev += [("toc", 4.38 + 1.4), ("toc", 31.94 + 1.6)]
        ev += [("whoosh", x) for x in (54.34, 55.72, 57.60)]
        ev += [("brilho", 85.46 + 1.8), ("brilho", 93.32), ("toc", 95.2), ("toc", 95.35), ("toc", 95.5)]
        return ev


def carregar_palavras(caminho):
    pal = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            if (w["w"].startswith("-") or w["w"].startswith("'")) and pal:
                pal[-1]["w"] += w["w"]
                pal[-1]["e"] = w["e"]
                continue
            pal.append(dict(w=w["w"], s=w["s"], e=w["e"]))
    troca = {"voo,": "vô,", "10": "dez", "20": "vinte", "40": "quarenta", "3": "três", "30": "Trinta"}
    out = []
    for w in pal:
        txt = troca.get(w["w"], w["w"])
        if txt == "dele" and out and out[-1]["w"] == "Jogou":
            txt = "o dele"
        out.append(dict(w=txt, s=w["s"], e=w["e"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_controle_do_meu_pai.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeControle(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.2)
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

    tmp = tempfile.mkdtemp(prefix="controle_")
    wav = os.path.join(tmp, "mix.wav")
    vc.mixar(filme, a.narracao, wav)
    print(f"• renderizando {total} frames ({filme.dur_total:.1f}s)…", flush=True)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}",
         "-r", str(FPS), "-i", "-", "-i", wav, "-vf", "scale=1080:1920:flags=lanczos",
         "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
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
