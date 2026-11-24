#!/usr/bin/env python3
"""
"A Vaquinha de R$ 13" — vídeo no formato notícia/opinião com dados.

Estilo diferente dos outros:
  * legenda em CAIXA ALTA com fundo escuro (sem karaokê), palavras-chave coloridas
  * etiquetas no topo da tela ("A META", "DETALHE"…)
  * muitos números, gráfico de barras, celular com Pix e enquete no final

    python3 animacao/video_vaquinha.py --narracao narr.wav --transcricao transcricao.json --fonte Poppins.ttf
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
import video_milhao as vm  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, Ator, gradiente, brilho,
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(66)

POLITICO = dict(pele=(222, 175, 140), cabelo=(200, 200, 205), camisa=(45, 50, 70), calca=(40, 45, 60),
                sapato=(30, 30, 30), tipo="pai", barba=True, faixa_pres=True, gravata=(200, 40, 40))
COORD = dict(pele=(232, 190, 160), cabelo=(190, 190, 195), camisa=(80, 85, 100), calca=(60, 65, 80),
             sapato=(30, 30, 30), tipo="vovo_h", gravata=(200, 40, 40))
CIDADAO = dict(pele=(214, 160, 120), cabelo=(40, 30, 25), camisa=(60, 140, 220), calca=(50, 60, 90),
               sapato=(240, 240, 240), tipo="pai", bigode=False)

VERMELHO = (235, 60, 50)
VERDE = (60, 200, 100)
AMARELO = (255, 214, 40)
CORES_PALAVRA = {"DÍVIDAS": VERMELHO, "DEVENDO.": VERMELHO, "FALTOU?": VERMELHO, "IMPOSTOS.": VERMELHO,
                 "TROCO": VERMELHO, "PAU?": VERMELHO, "IMPOSTO.": VERMELHO, "NEM": VERMELHO, "UM": None,
                 "DOAVA": VERDE, "LULA.": AMARELO, "PIX": AMARELO, "TSE,": AMARELO, "TSE.": AMARELO}


# --------------------------------------------------------------------------
# Objetos
# --------------------------------------------------------------------------
def vaca(cofre=True, w=560):
    p = Pincel(w, w * 0.75)
    p.ret((80, 120, 470, 330), (250, 250, 250), r=90)
    for (x, y, r) in ((170, 170, 50), (330, 230, 60), (250, 140, 34), (400, 160, 30)):
        p.elipse((x - r, y - r * 0.8, x + r, y + r * 0.8), (30, 30, 35), ow=0)
    for x in (130, 200, 360, 430):
        p.capsula((x, 300), (x, 400), 34, (250, 250, 250))
        p.elipse((x - 22, 385, x + 22, 415), (30, 30, 35), ow=0)
    p.elipse((420, 70, 560, 210), (250, 250, 250))
    p.elipse((450, 150, 560, 220), (245, 170, 180))
    for x in (480, 525):
        p.elipse((x - 6, 175, x + 6, 189), (120, 60, 70), ow=0)
    p.elipse((455, 100, 475, 122), OUTLINE, ow=0)
    p.elipse((505, 100, 525, 122), OUTLINE, ow=0)
    p.poli([(430, 70), (420, 30), (460, 60)], (230, 220, 200))
    p.poli([(530, 60), (560, 25), (555, 75)], (230, 220, 200))
    if cofre:
        p.ret((220, 100, 330, 122), (40, 40, 45), r=6, ow=0)
    return p.pronto()


def lanche(w=360):
    p = Pincel(w, w * 0.85)
    p.chord((20, 20, w - 20, 200), 180, 360, (230, 160, 70))
    p.ret((20, 105, w - 20, 130), (100, 190, 80), r=8)
    p.ret((30, 130, w - 30, 175), (140, 70, 40), r=14)
    p.ret((25, 172, w - 25, 192), (250, 200, 50), r=6)
    p.chord((20, 160, w - 20, 290), 0, 180, (230, 160, 70))
    for x in (110, 170, 230):
        p.elipse((x - 6, 60, x + 6, 70), (250, 240, 200), ow=0)
    return p.pronto()


def documento(fc, w=560):
    h = int(w * 1.3)
    p = Pincel(w, h)
    p.ret((10, 10, w - 10, h - 10), (250, 250, 250), r=10)
    for i in range(12):
        y = 200 + i * 40
        p.linha([(60, y), (w - 60 - (i % 3) * 60, y)], fill=(170, 170, 180), w=6)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 40)
    d.text((w / 2 - f.getlength("CAMPANHA") / 2, 80), "CAMPANHA", font=f, fill=(40, 40, 50))
    d.text((w / 2 - f.getlength("FUNDO ELEITORAL") / 2, 130), "FUNDO ELEITORAL", font=vc.fonte(fc, 34),
           fill=(200, 40, 40))
    return img


def lupa(w=380):
    p = Pincel(w, w)
    p.capsula((250, 250), (360, 360), 44, (70, 50, 40))
    p.elipse((20, 20, 280, 280), (210, 230, 245), ow=14)
    p.elipse((60, 60, 120, 120), (250, 250, 255), ow=0)
    img = p.pronto()
    a = img.getchannel("A").point(lambda v: v)
    return img


def guia_imposto(fc, w=420):
    p = Pincel(w, 300)
    p.ret((10, 10, w - 10, 290), (250, 250, 250), r=8)
    p.ret((10, 10, w - 10, 70), (220, 50, 50), r=8)
    for x in range(40, w - 40, 14):
        p.ret((x, 180, x + (6 if x % 28 else 10), 260), (30, 30, 30), r=0, ow=0)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 36)
    d.text((w / 2 - f.getlength("IMPOSTO") / 2, 20), "IMPOSTO", font=f, fill=(255, 255, 255))
    return img


def tse(fc):
    base = gradiente(WW, WH, (140, 195, 240), (220, 238, 250))
    p = Pincel(WW, WH)
    vc.nuvem(p, 120, 260, 0.8)
    vc.nuvem(p, 760, 360, 0.6)
    p.ret((-20, 1300, WW + 20, WH + 20), (110, 180, 90), r=0)
    p.ret((-20, 1300, WW + 20, 1360), (110, 170, 220), r=0, ow=0)
    p.ret((60, 900, 740, 1300), (235, 238, 245), r=10)
    p.ret((40, 860, 760, 920), (200, 205, 215), r=10)
    for y in range(960, 1280, 70):
        for x in range(100, 720, 60):
            p.ret((x, y, x + 40, y + 36), (90, 130, 190), r=4, ow=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 56)
    d.text((400 - f.getlength("TSE") / 2, 790), "TSE", font=f, fill=(40, 40, 50))
    return base


def palco(fc):
    base = gradiente(WW, WH, (30, 50, 120), (15, 25, 70))
    p = Pincel(WW, WH)
    p.ret((140, 160, 940, 620), (20, 30, 70), r=20, ow=12)
    for i in range(6):
        h = 80 + (i * 53) % 220
        p.ret((220 + i * 110, 560 - h, 290 + i * 110, 560), (60, 110, 200), r=6, ow=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (40, 40, 60), r=0)
    for x in (120, 380, 700, 960):                     # bandeirinhas do Brasil
        p.ret((x - 4, 1380, x + 4, 1520), (90, 90, 95), r=2, ow=0)
        p.ret((x, 1380, x + 110, 1450), (40, 150, 70), r=0, ow=4)
        p.poli([(x + 10, 1415), (x + 55, 1388), (x + 100, 1415), (x + 55, 1442)], (250, 210, 40), ow=0)
        p.elipse((x + 40, 1400, x + 70, 1430), (40, 80, 170), ow=0)
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((1000, 1200), (120, 160, 255), 500, 0.35), (40, 500))
    return base


def cozinha_cidadao():
    base = gradiente(WW, WH, (245, 225, 195), (230, 205, 170))
    p = Pincel(WW, WH)
    p.ret((680, 220, 960, 520), (170, 215, 240), r=8, ow=10)
    p.linha([(820, 220), (820, 520)], w=8)
    p.ret((-20, 1000, WW + 20, 1300), (200, 150, 110), r=0)
    for x in range(40, WW, 200):
        p.ret((x, 1040, x + 170, 1270), (215, 165, 125), r=8, ow=5)
    p.ret((-20, 1450, WW + 20, WH + 20), (180, 140, 110), r=0)
    base.alpha_composite(p.pronto())
    return base


def campo(fc):
    base = gradiente(WW, WH, (140, 200, 245), (225, 240, 250))
    p = Pincel(WW, WH)
    vc.nuvem(p, 100, 280, 0.9)
    vc.nuvem(p, 720, 400, 0.7)
    p.ret((-20, 1250, WW + 20, WH + 20), (120, 190, 90), r=0)
    p.ret((-20, 1240, WW + 20, 1270), (110, 170, 220), r=0, ow=0)
    base.alpha_composite(p.pronto())
    return base


def calendario_dia(fc, dia, w=300):
    p = Pincel(w, w * 1.1)
    p.ret((10, 30, w - 10, w * 1.08), (250, 250, 250), r=16)
    p.ret((10, 30, w - 10, 100), (220, 50, 50), r=16)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f1, f2 = vc.fonte(fc, 30), vc.fonte(fc, 140)
    d.text((w / 2 - f1.getlength("NOVEMBRO") / 2, 45), "NOVEMBRO", font=f1, fill=(255, 255, 255))
    d.text((w / 2 - f2.getlength(str(dia)) / 2, 110), str(dia), font=f2, fill=(40, 40, 50))
    return img


def relogio(t, w=360):
    p = Pincel(w, w)
    c = w / 2
    p.elipse((10, 10, w - 10, w - 10), (250, 250, 250), ow=12)
    for k in range(12):
        a = math.radians(k * 30)
        p.linha([(c + 140 * math.cos(a), c + 140 * math.sin(a)), (c + 160 * math.cos(a), c + 160 * math.sin(a))], w=6)
    a1 = math.radians(-90 + t * 360)
    a2 = math.radians(-90 + t * 30)
    p.linha([(c, c), (c + 130 * math.cos(a1), c + 130 * math.sin(a1))], fill=(220, 40, 40), w=8)
    p.linha([(c, c), (c + 90 * math.cos(a2), c + 90 * math.sin(a2))], w=12)
    return p.pronto()


def balanca(ang):
    p = Pincel(WW, 900)
    c = 540
    p.ret((c - 20, 200, c + 20, 760), (250, 200, 40), r=8)
    p.ret((c - 180, 740, c + 180, 800), (250, 200, 40), r=14)
    a = math.radians(ang)
    L = 340
    x1, y1 = c - L * math.cos(a), 220 - L * math.sin(a)
    x2, y2 = c + L * math.cos(a), 220 + L * math.sin(a)
    p.linha([(x1, y1), (x2, y2)], fill=(250, 200, 40), w=20)
    for (x, y) in ((x1, y1), (x2, y2)):
        p.linha([(x, y), (x - 110, y + 220)], fill=(220, 170, 30), w=6)
        p.linha([(x, y), (x + 110, y + 220)], fill=(220, 170, 30), w=6)
        p.chord((x - 150, y + 150, x + 150, y + 300), 0, 180, (250, 200, 40))
    return p.pronto(), (x1, y1 + 220), (x2, y2 + 220)


def cadeado(w=200):
    p = Pincel(w, w * 1.2)
    p.arco((40, 10, w - 40, 150), 180, 360, w=26)
    p.arco((40, 10, w - 40, 150), 180, 360, fill=(200, 200, 205), w=14)
    p.ret((20, 90, w - 20, w * 1.15), (250, 200, 40), r=20)
    p.elipse((w / 2 - 18, 140, w / 2 + 18, 176), OUTLINE, ow=0)
    return p.pronto()


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeVaquinha(vc.Filme):
    def __init__(self, palavras, fc, dur_total):
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.pol, self.coord, self.cid = Ator(POLITICO), Ator(COORD), Ator(CIDADAO)
        self.palco_img = palco(fc)
        self.tse_img = tse(fc)
        self.cozinha = cozinha_cidadao()
        self.campo = campo(fc)
        self.vaca = vaca()
        self.lanche = lanche()
        self.doc = documento(fc)
        self.lupa = lupa()
        self.guia = guia_imposto(fc)
        self.cal5, self.cal14 = calendario_dia(fc, 5), calendario_dia(fc, 14)
        self.cadeado = cadeado()
        self.dinheiro = vco.dinheiro(5)
        self.pix13 = vs.celular(fc, "PIX", [("Para", 36, (130, 130, 145)), ("PT", 70, (40, 40, 55)),
                                            ("R$ 13,00", 84, (40, 170, 100))], botao="PAGAR", cor=(50, 190, 170))
        self.pix_troco = vs.celular(fc, "PIX", [("Para", 36, (130, 130, 145)), ("PT", 70, (40, 40, 55)),
                                                ("TROCO?", 84, VERMELHO)], botao="PAGAR", cor=(50, 190, 170))
        self.f_leg = vc.fonte(fc, 54)
        self.f_tag = vc.fonte(fc, 40)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        P = [
            (0.00, self.p_palco, "corte"),
            (3.18, self.p_pix, "corte"),
            (5.08, self.p_pois_e, "corte"),
            (6.96, self.p_ganhou, "corte"),
            (9.28, self.p_dia5, "whip"),
            (14.42, self.p_meta, "corte"),
            (16.78, self.p_sugerido, "corte"),
            (18.86, self.p_coord, "whip"),
            (23.34, self.p_seu_lanche, "corte"),
            (26.18, self.p_detalhe, "zoom"),
            (28.50, self.p_tse, "whip"),
            (35.64, self.p_impostos, "corte"),
            (37.52, self.p_grafico, "whip"),
            (43.80, self.p_segundo_turno, "corte"),
            (47.36, self.p_relogio, "whip"),
            (52.84, self.p_imposto_pix, "corte"),
            (57.80, self.p_pergunto, "zoom"),
            (59.24, self.p_balanca, "corte"),
            (63.32, self.p_doava, "corte"),
            (66.30, self.p_nem_um_real, "corte"),
            (68.90, self.p_comenta, "corte"),
        ]
        self.planos = []
        for i, (ini, fn, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, "", tr))

    # ---------- legenda estilo notícia ----------
    @staticmethod
    def _blocos(pal):
        blocos, cur = [], []
        for w in pal:
            cur.append(w)
            if len(cur) >= 3 or w["w"][-1] in ",.!?":
                blocos.append(cur)
                cur = []
        if cur:
            blocos.append(cur)
        return blocos

    def legenda(self, img, t):
        bloco = None
        for i, b in enumerate(self.blocos):
            fim = self.blocos[i + 1][0]["s"] if i + 1 < len(self.blocos) else b[-1]["e"] + 0.5
            if b[0]["s"] - 0.05 <= t < fim:
                bloco = b
                break
        if not bloco:
            return
        f = self.f_leg
        palavras = [w["w"].upper() for w in bloco]
        esp = f.getlength(" ")
        larg = sum(f.getlength(w) for w in palavras) + esp * (len(palavras) - 1)
        cam = Image.new("RGBA", (int(larg + 50), 100), (0, 0, 0, 0))
        dc = ImageDraw.Draw(cam)
        dc.rounded_rectangle((0, 8, cam.width, 92), radius=10, fill=(20, 22, 30, 215))
        x = 25
        for i, w in enumerate(palavras):
            cor = CORES_PALAVRA.get(w) or (255, 255, 255)
            if w == "UM" and i > 0 and palavras[i - 1] == "NEM":
                cor = VERMELHO
            if w.startswith("REAL") and i > 1 and palavras[i - 1] == "UM" and palavras[i - 2] == "NEM":
                cor = VERMELHO
            dc.text((x, 18), w, font=f, fill=cor)
            x += f.getlength(w) + esp
        esc = min(1.0, (OUT_W - 40) / cam.width)
        if esc < 1:
            cam = cam.resize((int(cam.width * esc), int(cam.height * esc)), Image.BICUBIC)
        img.paste(cam, (int(OUT_W / 2 - cam.width / 2), int(OUT_H * 0.8 - cam.height / 2)), cam)

    def etiqueta(self, f, txt, t, y=0.1, cor=(250, 240, 220), fundo=(30, 30, 40), linha=0):
        if t < 0:
            return
        s = 0.6 + 0.4 * ease_out(t / 0.15)
        ft = self.f_tag
        w = ft.getlength(txt) + 36
        cam = Image.new("RGBA", (int(w), 64), (0, 0, 0, 0))
        dc = ImageDraw.Draw(cam)
        dc.rectangle((0, 0, w, 64), fill=fundo + (255,))
        dc.text((18, 8), txt, font=ft, fill=cor)
        cam = cam.resize((int(cam.width * s), int(cam.height * s)), Image.BICUBIC)
        f.paste(cam, (int(OUT_W / 2 - cam.width / 2), int(OUT_H * y + linha * 70)), cam)

    def numero(self, f, txt, t, y=0.22, cor=VERDE, tam=96):
        if t >= 0:
            texto_pop(f, txt, self.fc, t, OUT_W / 2, OUT_H * y, tam, cor)

    def fundo_escuro(self):
        return gradiente(WW, WH, (40, 44, 58), (22, 24, 32))

    # ---------- planos ----------
    def p_palco(self, t, d):
        m = self.palco_img.copy()
        self.pol.desenhar(m, t, 540, 1700, escala=1.45, expr="ri" if int(t * 4) % 2 else "feliz", pose="acena")
        f = camera(m, 540, 1150, 1.1)
        vm.confete(f, t, 50)
        self.etiqueta(f, "O CARA", t, y=0.12)
        self.etiqueta(f, "TIRAR TODO MUNDO DA POBREZA", t - 1.0, y=0.12, linha=1, cor=(255, 214, 40))
        return f

    def p_pix(self, t, d):
        m = self.fundo_escuro()
        self.segura(m, self.pix13, 540, 900, 700)
        f = camera(m, 540, 950, 1.05 + 0.08 * ease_out(t / d))
        self.etiqueta(f, "TÁ PEDINDO PIX", t, y=0.07, fundo=(250, 250, 250), cor=(30, 30, 40))
        return f

    def p_pois_e(self, t, d):
        m = self.cozinha.copy()
        self.cid.desenhar(m, t, 540, 1760, escala=1.6, expr="surpreso", pose="acena")
        return camera(m, 540, 1150, 1.15)

    def p_ganhou(self, t, d):
        m = self.palco_img.copy()
        dev = t > 8.32 - 6.96
        self.pol.desenhar(m, t, 540, 1700, escala=1.45, expr="triste" if dev else "ri", pose="idle" if dev else "acena")
        f = camera(m, 540, 1150, 1.1 + (0.2 * ease_out((t - 1.36) / 0.3) if dev else 0))
        self.etiqueta(f, "GANHOU A ELEIÇÃO", t, y=0.12, cor=(255, 214, 40))
        if dev:
            self.etiqueta(f, "FICOU DEVENDO", t - 1.36, y=0.12, linha=1, fundo=VERMELHO, cor=(255, 255, 255))
        return f

    def p_dia5(self, t, d):
        m = self.campo.copy()
        self.pol.desenhar(m, t, 760, 1700, escala=1.2, expr="feliz")
        self.segura(m, self.cal5, 250, 700, 300)
        tv = 11.36 - 9.28
        if t > tv:
            k = ease_out(min(1, (t - tv) / 0.4))
            self.segura(m, self.vaca, 380, 1380, 560 * k + 1)
            for i in range(3):        # moedas caindo no cofrinho
                y = 930 + ((t * 500 + i * 140) % 300)
                self.segura(m, vco.moeda(), 380, y, 60)
        f = camera(m, 540, 1150, 1.08)
        self.etiqueta(f, "NO DIA 5", t, y=0.07)
        self.etiqueta(f, "O PT ABRIU", t - (10.72 - 9.28), y=0.07, linha=1, fundo=VERMELHO, cor=(255, 255, 255))
        self.etiqueta(f, "VAQUINHA", t - tv, y=0.07, linha=2, fundo=(250, 214, 40), cor=(30, 30, 40))
        self.etiqueta(f, "DÍVIDAS DA CAMPANHA", t - (12.82 - 9.28), y=0.07, linha=3, fundo=VERMELHO, cor=(255, 255, 255))
        return f

    def p_meta(self, t, d):
        m = self.fundo_escuro()
        self.segura(m, self.vaca, 540, 1250, 640)
        f = camera(m, 540, 1000, 1.05)
        self.etiqueta(f, "A META", t, y=0.08, fundo=(250, 250, 250), cor=(30, 30, 40))
        self.numero(f, "R$ 7 MILHÕES", t - 0.7, y=0.25, tam=100)
        vm.FilmeMilhao.chuva_dinheiro(self, f, t, 12) if t > 0.7 else None
        return f

    def p_sugerido(self, t, d):
        m = self.fundo_escuro()
        self.segura(m, self.vaca, 540, 1300, 560)
        f = camera(m, 540, 1000, 1.05)
        self.etiqueta(f, "VALOR SUGERIDO", t, y=0.08, fundo=(250, 214, 40), cor=(30, 30, 40))
        self.numero(f, "R$ 13", t - (17.90 - 16.78), y=0.25, tam=150)
        return f

    def p_coord(self, t, d):
        m = self.palco_img.copy()
        ap = t > 1.0
        self.coord.desenhar(m, t, 400, 1700, escala=1.4, expr="feliz", pose="aponta" if ap else "idle")
        tl = 22.86 - 18.86
        if t > tl - 1.2:
            k = ease_out(min(1, (t - (tl - 1.2)) / 0.3))
            self.segura(m, self.lanche, 800, 950, 330 * k + 1)
        f = camera(m, 540, 1150, 1.1)
        self.etiqueta(f, "COORDENADOR FINANCEIRO", t, y=0.07)
        if t > tl - 1.2:
            texto_pop(f, "R$ 13", self.fc, t - (tl - 1.2), OUT_W * 0.78, OUT_H * 0.48, 60, (255, 255, 255))
        self.etiqueta(f, "MENOS QUE UM LANCHE", t - (22.32 - 18.86), y=0.07, linha=1, fundo=(250, 214, 40),
                      cor=(30, 30, 40))
        return f

    def p_seu_lanche(self, t, d):
        m = self.cozinha.copy()
        self.cid.desenhar(m, t, 360, 1760, escala=1.4, expr="triste", pose="entrega")
        hx, hy = self.mao(360, 1760, 1.4, t)
        k = ease_io(min(1, max(0, t - 0.9) / 0.9))
        x = hx + 50 + (820 - hx - 50) * k
        y = hy - 30 - 250 * math.sin(k * math.pi) + (1500 - hy) * k
        self.segura(m, self.vaca, 840, 1700, 380)
        if k < 1:
            self.segura(m, self.lanche, x, y, 200)
        f = camera(m, 540, 1200, 1.1)
        self.etiqueta(f, "O SEU LANCHE", t, y=0.1, fundo=(250, 250, 250), cor=(30, 30, 40))
        return f

    def p_detalhe(self, t, d):
        m = self.fundo_escuro()
        self.segura(m, self.doc, 540, 960, 620, rot=-4)
        x = 470 + 80 * math.sin(t * 2)
        self.segura(m, self.lupa, x, 900, 340)
        f = camera(m, 540, 960, 1.05 + 0.1 * ease_io(t / d))
        self.etiqueta(f, "DETALHE", t, y=0.08, fundo=(250, 214, 40), cor=(30, 30, 40))
        self.etiqueta(f, "QUASE NINGUÉM CONTA", t - 1.0, y=0.08, linha=1)
        return f

    def p_tse(self, t, d):
        m = self.tse_img.copy()
        n = 1 + min(7, int(t / 0.7))
        for i in range(n):
            self.segura(m, self.dinheiro, 900, 1250 - i * 70, 300)
        f = camera(m, 540, 1050, 1.0 + 0.1 * ease_io(t / d))
        self.etiqueta(f, "ENVIADOS AO TSE", t, y=0.07)
        self.numero(f, "R$ 123 MILHÕES", t - (32.32 - 28.50), y=0.2, tam=80)
        self.etiqueta(f, "FUNDO ELEITORAL", t - (34.66 - 28.50), y=0.27, fundo=(250, 214, 40), cor=(30, 30, 40))
        return f

    def p_impostos(self, t, d):
        m = self.cozinha.copy()
        self.cid.desenhar(m, t, 460, 1760, escala=1.5, expr="bravo", pose="entrega")
        hx, hy = self.mao(460, 1760, 1.5, t)
        self.segura(m, self.guia, hx + 70, hy - 80, 320, rot=-8)
        f = camera(m, 540, 1150, 1.15)
        texto_pop(f, "SEUS IMPOSTOS", self.fc, t, OUT_W * 0.5, OUT_H * 0.62, 70, VERMELHO)
        return f

    def p_grafico(self, t, d):
        m = self.fundo_escuro()
        p = Pincel(WW, WH)
        base_y = 1400
        k1 = ease_out(min(1, t / 0.6))
        k2 = ease_out(min(1, max(0, t - 0.6) / 0.8))
        h1, h2 = 820 * k1, 820 * 93 / 123 * k2
        p.ret((200, base_y - h1, 460, base_y), (40, 190, 90), r=6)
        p.ret((620, base_y - h2, 880, base_y), (220, 50, 50), r=6)
        p.linha([(140, base_y), (940, base_y)], fill=(200, 200, 210), w=6)
        sobra = t > 40.90 - 37.52
        if sobra:
            p.ret((620, base_y - 820, 880, base_y - h2), (0, 0, 0, 0), r=6, ow=6, outline=(60, 220, 110))
        m.alpha_composite(p.pronto())
        f = camera(m, 540, 960, 1.05)
        d_ = ImageDraw.Draw(f)
        fl = vc.fonte(self.fc, 30)
        for (x, txt) in ((330, "RECEBEU"), (750, "GASTOU")):
            X = (x - 540) / (WW / 1.05) * OUT_W + OUT_W / 2
            d_.text((X - fl.getlength(txt) / 2, OUT_H * 0.73), txt, font=fl, fill=(230, 230, 235))
        fv = vc.fonte(self.fc, 40)
        for (x, h, txt) in ((330, h1, "R$ 123 MI"), (750, h2, "R$ 93 MI")):
            X = (x - 540) / (WW / 1.05) * OUT_W + OUT_W / 2
            Y = ((base_y - h) - (960 - WH / 2.1)) / (WH / 1.05) * OUT_H - 60
            if h > 10:
                d_.text((X - fv.getlength(txt) / 2, Y), txt, font=fv, fill=(255, 255, 255))
        self.etiqueta(f, "DECLAROU", t, y=0.06)
        if sobra:
            self.etiqueta(f, "SOBROU", t - (40.90 - 37.52), y=0.06, linha=1, fundo=(60, 200, 100), cor=(255, 255, 255))
        if t > 42.42 - 37.52:
            texto_pop(f, "FALTOU?", self.fc, t - (42.42 - 37.52), OUT_W * 0.5, OUT_H * 0.2, 110, VERMELHO)
        return f

    def p_segundo_turno(self, t, d):
        m = self.fundo_escuro()
        rng = random.Random(4)
        for i in range(min(9, 1 + int(t / 0.35))):
            pp = Pincel(300, 380)
            pp.ret((10, 10, 290, 370), (250, 250, 250), r=6)
            for j in range(6):
                pp.linha([(40, 60 + j * 45), (250, 60 + j * 45)], fill=(170, 170, 180), w=5)
            self.segura(m, pp.pronto(), 540 + rng.uniform(-200, 200), 1150 - i * 25, 300, rot=rng.uniform(-20, 20))
        f = camera(m, 540, 1000, 1.05)
        self.etiqueta(f, "O PT DISSE", t, y=0.08, fundo=VERMELHO, cor=(255, 255, 255))
        self.etiqueta(f, "GASTOS DO SEGUNDO TURNO", t - (45.86 - 43.80), y=0.08, linha=1, fundo=(250, 214, 40),
                      cor=(30, 30, 40))
        return f

    def p_relogio(self, t, d):
        m = self.tse_img.copy()
        self.segura(m, relogio(t * 1.5), 260, 560, 300)
        if t > 50.56 - 47.36:
            k = ease_out(min(1, (t - (50.56 - 47.36)) / 0.3))
            self.segura(m, self.cal14, 820, 560, 280 * k + 1)
        f = camera(m, 540, 950, 1.05)
        self.etiqueta(f, "CONTRA O RELÓGIO", t, y=0.06, fundo=VERMELHO, cor=(255, 255, 255))
        self.etiqueta(f, "PRAZO DO TSE", t - (51.54 - 47.36), y=0.62, fundo=(250, 214, 40), cor=(30, 30, 40))
        return f

    def p_imposto_pix(self, t, d):
        m = self.cozinha.copy()
        self.cid.desenhar(m, t, 540, 1760, escala=1.5, expr="bravo")
        k1 = ease_out(min(1, t / 0.3))
        self.segura(m, self.guia, 230, 1000, 300 * k1 + 1, rot=-8)
        tp = 55.24 - 52.84
        if t > tp:
            k2 = ease_out(min(1, (t - tp) / 0.3))
            self.segura(m, self.pix_troco, 860, 1050, 260 * k2 + 1, rot=6)
        f = camera(m, 540, 1150, 1.1)
        self.etiqueta(f, "PRIMEIRO O IMPOSTO", t, y=0.07, fundo=VERMELHO, cor=(255, 255, 255))
        self.etiqueta(f, "DEPOIS O PIX", t - tp, y=0.07, linha=1, fundo=(50, 190, 170), cor=(255, 255, 255))
        return f

    def p_pergunto(self, t, d):
        m = gradiente(WW, WH, (90, 10, 15), (40, 5, 8))
        k = 0.5 + 0.5 * math.sin(t * 10)
        m.alpha_composite(brilho((900, 900), (255, 60, 50), 450, 0.9 * k), (90, 300))
        p = Pincel(WW, WH)
        p.chord((390, 600, 690, 900), 180, 360, (240, 50, 40))
        p.ret((370, 750, 710, 800), (60, 60, 65), r=10)
        m.alpha_composite(p.pronto())
        f = camera(m, 540, 900, 1.05)
        texto_pop(f, "EU TE PERGUNTO", self.fc, t, OUT_W * 0.5, OUT_H * 0.55, 80, (255, 255, 255))
        return f

    def p_balanca(self, t, d):
        m = self.fundo_escuro()
        ang = 12 * math.sin(t * 1.6)
        img, (lx, ly), (rx, ry) = balanca(ang)
        m.alpha_composite(img, (0, 600))
        self.segura(m, self.vaca, 540, 640, 300)
        f = camera(m, 540, 1000, 1.0)
        X = lambda x: x / WW * OUT_W  # noqa: E731
        Y = lambda y: (y + 600 - 40) / WH * OUT_H  # noqa: E731
        fl = vc.fonte(self.fc, 26)
        d_ = ImageDraw.Draw(f)
        for (x, y, txt, cor) in ((lx, ly, "PARTICIPAÇÃO", (60, 120, 230)), (rx, ry, "CARA DE PAU", VERMELHO)):
            w = fl.getlength(txt) + 20
            d_.rectangle((X(x) - w / 2, Y(y) - 70, X(x) + w / 2, Y(y) - 34), fill=cor)
            d_.text((X(x) - w / 2 + 10, Y(y) - 68), txt, font=fl, fill=(255, 255, 255))
        return f

    def p_doava(self, t, d):
        m = gradiente(WW, WH, (25, 40, 80), (15, 25, 55))
        self.segura(m, self.pix13, 540, 1000, 600)
        f = camera(m, 540, 1000, 1.05)
        texto_pop(f, "DOAVA", self.fc, t, OUT_W * 0.5, OUT_H * 0.1, 120, VERDE)
        return f

    def p_nem_um_real(self, t, d):
        m = self.cozinha.copy()
        self.cid.desenhar(m, t, 540, 1760, escala=1.6, expr="feliz")
        self.segura(m, self.cadeado, 860, 1000 + 10 * math.sin(t * 6), 170)
        f = camera(m, 540, 1150, 1.12)
        texto_pop(f, "NEM UM REAL", self.fc, t, OUT_W * 0.5, OUT_H * 0.1, 90, VERMELHO)
        return f

    def p_comenta(self, t, d):
        m = gradiente(WW, WH, (25, 40, 80), (15, 25, 55))
        f = camera(m, 540, 960, 1.0)
        texto_pop(f, "COMENTA AÍ", self.fc, t, OUT_W * 0.5, OUT_H * 0.3, 96, (255, 255, 255))
        d_ = ImageDraw.Draw(f)
        fb = vc.fonte(self.fc, 54)
        for i, (txt, cor) in enumerate((("DOAVA", (40, 170, 90)), ("NEM UM REAL", (210, 50, 45)))):
            k = ease_out(min(1, max(0, t - 0.25 - i * 0.2) / 0.25))
            if k <= 0:
                continue
            w, h = 520 * k, 110 * k
            cx, cy = OUT_W / 2, OUT_H * (0.45 + i * 0.12)
            d_.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=16, fill=cor)
            if k > 0.9:
                d_.text((cx - fb.getlength(txt) / 2, cy - 36), txt, font=fb, fill=(255, 255, 255))
        if t > d - 0.4:
            f = ImageEnhance.Brightness(f).enhance(max(0, 1 - (t - (d - 0.4)) / 0.4))
        return f

    # ---------- montagem: legenda própria, sem vinheta forte ----------
    def frame(self, n):
        t = n / FPS
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if t < ini + d or i == len(self.planos) - 1:
                tl = t - ini
                f = fn(tl, d)
                if i > 0 and tl < 0.2 and tr in ("whip", "zoom"):
                    pi, pd, pfn, _, _ = self.planos[i - 1]
                    prev = pfn(pd - 0.001, pd)
                    x = tl / 0.2
                    if tr == "whip":
                        off = int(OUT_W * ease_io(x))
                        comp = Image.new("RGB", (OUT_W, OUT_H))
                        comp.paste(prev, (-off, 0))
                        comp.paste(f, (OUT_W - off, 0))
                        f = g.motion_blur_h(comp, 60 * math.sin(math.pi * x))
                    else:
                        f = g.zoom_blur(Image.blend(prev, f, ease_io(x)), 0.4 * math.sin(math.pi * x))
                f = g.vinheta(f, 0.35)
                if fn != self.p_comenta:
                    self.legenda(f, t)
                return f

    def eventos_sfx(self):
        ev = []
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if i and tr in ("whip", "zoom"):
                ev.append(("whoosh", ini - 0.08))
            elif i:
                ev.append(("pop", ini))
        ev += [("brilho", 3.18), ("brilho", 15.16), ("brilho", 32.32), ("toc", 42.42), ("brilho", 63.32)]
        ev += [("toc", 11.36 + 0.4 + i * 0.3) for i in range(4)]
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
        if w["w"] == "R" and i + 2 < len(pal) and pal[i + 1]["w"] == "$":
            valor = pal[i + 2]["w"]
            j = i + 3
            if j < len(pal) and pal[j]["w"].startswith(","):
                valor += pal[j]["w"]
                j += 1
            out.append(dict(w="R$ " + valor, s=w["s"], e=pal[j - 1]["e"]))
            i = j
            continue
        if w["w"] == "do" and i + 1 < len(pal) and pal[i + 1]["w"] == "AVA":
            out.append(dict(w="DOAVA", s=w["s"], e=pal[i + 1]["e"]))
            i += 2
            continue
        out.append(dict(w={"fungo": "fundo"}.get(w["w"], w["w"]), s=w["s"], e=w["e"]))
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_vaquinha.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeVaquinha(carregar_palavras(a.transcricao), a.fonte, voz_dur + 2.2)
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

    tmp = tempfile.mkdtemp(prefix="vaquinha_")
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
