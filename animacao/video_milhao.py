#!/usr/bin/env python3
"""
"O Milhão de Todo Mundo" — vídeo "E se…?" com lição de economia (inflação).

    python3 animacao/remover_silencios.py narracao.mp3 narr.wav
    (faster-whisper -> transcricao.json)
    python3 animacao/video_milhao.py --narracao narr.wav --transcricao transcricao.json --fonte Poppins.ttf
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

random.seed(55)

VOCE = dict(pele=(222, 170, 128), cabelo=(60, 40, 30), camisa=(60, 160, 90), calca=(50, 60, 90),
            sapato=(240, 240, 240), tipo="pai", bigode=False)
CHEFE = dict(pele=(235, 195, 160), cabelo=(70, 60, 55), camisa=(70, 75, 90), calca=(55, 60, 75),
             sapato=(30, 30, 30), tipo="pai", bigode=False)
CIDA = dict(pele=(176, 120, 85), cabelo=(225, 225, 230), camisa=(250, 250, 250), calca=(0, 0, 0),
            sapato=(120, 80, 60), tipo="vovo", vestido=(240, 150, 120))
VIZINHO = dict(pele=(200, 140, 100), cabelo=(30, 25, 25), camisa=(240, 190, 60), calca=(60, 70, 120),
               sapato=(200, 60, 60), tipo="pai")
TIA = dict(pele=(235, 190, 150), cabelo=(150, 60, 40), camisa=(220, 90, 150), calca=(0, 0, 0),
           sapato=(200, 60, 120), tipo="moca", vestido=(230, 110, 170))
POVO = [VIZINHO, TIA, VOCE,
        dict(VIZINHO, camisa=(120, 90, 200), pele=(150, 100, 70), bigode=False),
        dict(TIA, camisa=(90, 180, 200), vestido=(110, 190, 210), cabelo=(30, 25, 25), pele=(160, 110, 80))]

vc.DESTAQUE_VERMELHO = {"demissão.", "Goiás.", "velha?", "ninguém", "estranha.", "valer.", "chefe.", "faço."}
VERDE = (60, 170, 100)


# --------------------------------------------------------------------------
# Objetos
# --------------------------------------------------------------------------
def fnt(fc, t):
    return vc.fonte(fc, t)


def etiqueta(fc, preco, produto="ARROZ", w=760):
    p = Pincel(w, 520)
    p.ret((20, 20, w - 20, 500), (230, 40, 40), r=30)
    p.ret((20, 380, w - 20, 500), (250, 210, 60), r=0, ow=0)
    p.elipse((50, 60, 100, 110), (255, 255, 255), ow=5)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f1, f2 = fnt(fc, 54), fnt(fc, 130 if len(preco) < 9 else 100)
    d.text((w / 2 - f1.getlength(produto) / 2, 70), produto, font=f1, fill=(255, 255, 255))
    d.text((w / 2 - f2.getlength(preco) / 2, 170), preco, font=f2, fill=(255, 255, 255))
    return img


def lancha(w=900):
    p = Pincel(w, 380)
    p.poli([(20, 180), (w - 40, 180), (w - 140, 330), (120, 330)], (250, 250, 250))
    p.ret((20, 230, w - 80, 260), (40, 110, 200), r=6, ow=0)
    p.poli([(300, 180), (380, 80), (600, 80), (640, 180)], (230, 230, 240))
    p.poli([(400, 170), (430, 100), (580, 100), (600, 170)], (80, 150, 210), ow=5)
    p.linha([(620, 80), (660, 30)], w=8)
    return p.pronto()


def carrinho(cheio=True):
    p = Pincel(700, 600)
    p.poli([(60, 100), (640, 100), (580, 420), (140, 420)], (200, 205, 215))
    for x in range(120, 640, 70):
        p.linha([(x, 110), (x - 10 + (x - 350) * -0.05, 410)], fill=(150, 155, 165), w=6)
    p.linha([(0, 40), (70, 100)], w=12)
    p.ret((150, 420, 600, 450), (150, 155, 165), r=10)
    for x in (190, 540):
        p.elipse((x - 40, 470, x + 40, 550), (40, 40, 45))
    img = p.pronto()
    if cheio:
        notas = vco.dinheiro(5).resize((620, 403))
        img.alpha_composite(notas, (40, -120))
        img.alpha_composite(vco.dinheiro(4).resize((560, 364)), (90, -40))
    return img


def pao(w=520):
    p = Pincel(w, 300)
    p.elipse((20, 40, w - 20, 280), (220, 150, 70))
    for k in range(4):
        x = 110 + k * 90
        p.arco((x - 40, 90, x + 40, 200), 200, 340, fill=(250, 210, 140), w=12)
    return p.pronto()


def pao_queijo(w=260):
    p = Pincel(w, w)
    p.elipse((20, 30, w - 20, w - 20), (240, 200, 100))
    for (x, y) in ((80, 90), (160, 110), (110, 160), (170, 170)):
        p.elipse((x - 10, y - 8, x + 10, y + 8), (250, 225, 150), ow=0)
    return p.pronto()


def nota_trilhoes(fc, w=900):
    h = 420
    p = Pincel(w, h)
    p.ret((10, 10, w - 10, h - 10), (180, 210, 170), r=20)
    p.ret((40, 40, w - 40, h - 40), (200, 225, 190), r=10, ow=4)
    p.elipse((w - 300, 90, w - 80, 330), (160, 195, 150), ow=5)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    d.text((70, 70), "100", font=fnt(fc, 120), fill=(40, 80, 50))
    d.text((70, 210), "TRILLION", font=fnt(fc, 64), fill=(40, 80, 50))
    d.text((70, 290), "DOLLARS", font=fnt(fc, 44), fill=(40, 80, 50))
    d.text((w - 250, 180), "2008", font=fnt(fc, 50), fill=(40, 80, 50))
    return img


def placa_fechado(fc, w=520):
    p = Pincel(w, 220)
    p.linha([(w / 2, 0), (60, 60)], fill=(80, 80, 80), w=5)
    p.linha([(w / 2, 0), (w - 60, 60)], fill=(80, 80, 80), w=5)
    p.ret((20, 50, w - 20, 210), (220, 40, 40), r=20)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = fnt(fc, 72)
    d.text((w / 2 - f.getlength("FECHADO") / 2, 85), "FECHADO", font=f, fill=(255, 255, 255))
    return img


def caminhao():
    p = Pincel(1100, 520)
    p.ret((20, 60, 720, 400), (240, 240, 240), r=12)
    p.ret((720, 160, 1040, 400), (40, 110, 200), r=30)
    p.ret((800, 190, 1000, 290), (180, 215, 240), r=12, ow=6)
    p.ret((20, 390, 1060, 440), (60, 60, 65), r=10)
    img = p.pronto()
    r = vco.roda().resize((150, 150))
    for x in (100, 520, 860):
        img.alpha_composite(r, (x, 370))
    return img


def onibus():
    p = Pincel(1100, 520)
    p.ret((20, 60, 1060, 420), (250, 200, 50), r=30)
    for x in range(80, 1000, 160):
        p.ret((x, 110, x + 130, 230), (170, 210, 240), r=10, ow=6)
    p.ret((20, 300, 1060, 330), (40, 110, 200), r=0, ow=0)
    img = p.pronto()
    r = vco.roda().resize((150, 150))
    for x in (130, 830):
        img.alpha_composite(r, (x, 360))
    return img


def lixeira():
    p = Pincel(500, 600)
    p.poli([(60, 120), (440, 120), (400, 580), (100, 580)], (90, 140, 90))
    p.ret((30, 80, 470, 140), (70, 120, 70), r=14)
    for x in (160, 250, 340):
        p.linha([(x, 180), (x - 10 + (x - 250) * 0.1, 540)], fill=(70, 110, 70), w=8)
    return p.pronto()


def relogio_pulso():
    p = Pincel(300, 300)
    p.ret((110, 0, 190, 300), (60, 60, 70), r=20)
    p.elipse((50, 50, 250, 250), (230, 200, 90))
    p.elipse((75, 75, 225, 225), (255, 255, 255), ow=5)
    p.linha([(150, 150), (150, 100)], w=8)
    p.linha([(150, 150), (190, 160)], w=8)
    return p.pronto()


def celular_icone():
    p = Pincel(220, 380)
    p.ret((10, 10, 210, 370), (30, 30, 40), r=34)
    p.ret((26, 50, 194, 320), (90, 160, 230), r=10, ow=0)
    return p.pronto()


def confete(f, t, n=80):
    d = ImageDraw.Draw(f)
    rng = random.Random(3)
    cores = [(240, 80, 80), (250, 210, 60), (80, 180, 240), (120, 210, 120), (220, 120, 220)]
    for _ in range(n):
        x = (rng.uniform(0, OUT_W) + 30 * math.sin(t * 3 + rng.uniform(0, 6)))
        y = (rng.uniform(0, OUT_H) + t * rng.uniform(150, 300)) % OUT_H
        a = t * 5 + rng.uniform(0, 6)
        s = 10
        d.polygon([(x + s * math.cos(a), y + s * math.sin(a)), (x - s * math.sin(a), y + s * math.cos(a)),
                   (x - s * math.cos(a), y - s * math.sin(a)), (x + s * math.sin(a), y - s * math.cos(a))],
                  fill=rng.choice(cores))


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def governo(fc):
    base = gradiente(WW, WH, (130, 190, 240), (215, 235, 250))
    p = Pincel(WW, WH)
    vc.nuvem(p, 100, 260, 0.9)
    vc.nuvem(p, 760, 380, 0.7)
    p.ret((100, 900, 980, 1420), (245, 245, 240), r=6)
    p.poli([(80, 905), (540, 650), (1000, 905)], (235, 235, 230))
    for x in range(170, 960, 120):
        p.ret((x, 960, x + 50, 1400), (225, 225, 220), r=10, ow=5)
    p.ret((-20, 1410, WW + 20, WH + 20), (120, 180, 110), r=0)
    p.ret((470, 520, 490, 660), (90, 90, 95), r=4)
    p.ret((490, 520, 640, 610), (40, 150, 70), r=0, ow=5)                     # bandeira
    p.poli([(500, 565), (565, 532), (630, 565), (565, 598)], (250, 210, 40), ow=0)
    p.elipse((545, 545, 585, 585), (40, 80, 170), ow=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = fnt(fc, 60)
    d.text((540 - f.getlength("GOVERNO") / 2, 820), "GOVERNO", font=f, fill=(90, 90, 100))
    return base


def padaria(fc, fila=False):
    base = gradiente(WW, WH, (130, 190, 240) if not fila else (250, 200, 140),
                     (215, 235, 250) if not fila else (255, 230, 190))
    p = Pincel(WW, WH)
    p.ret((80, 560, 1000, 1420), (250, 220, 170), r=8)
    p.ret((60, 520, 1020, 640), (190, 110, 60), r=10)
    for i, x in enumerate(range(80, 1000, 115)):                               # toldo
        p.ret((x, 640, x + 115, 760), (220, 60, 60) if i % 2 else (250, 250, 250), r=0, ow=0)
    p.ret((150, 860, 560, 1200), (180, 215, 240), r=12, ow=8)                 # vitrine
    p.ret((650, 900, 900, 1420), (150, 90, 60), r=12)
    p.ret((-20, 1410, WW + 20, 1500), (200, 190, 175), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (90, 90, 100), r=0)
    base.alpha_composite(p.pronto())
    for k in range(3):
        pz = pao(150)
        base.alpha_composite(pz, (190 + k * 120, 1080))
    d = ImageDraw.Draw(base)
    f = fnt(fc, 64)
    d.text((540 - f.getlength("PADARIA DA CIDA") / 2, 548), "PADARIA DA CIDA", font=f, fill=(255, 240, 200))
    return base


def loja(fc, nome, cor):
    base = gradiente(WW, WH, (150, 160, 175), (190, 195, 205))
    p = Pincel(WW, WH)
    p.ret((80, 560, 1000, 1420), (225, 225, 220), r=8)
    p.ret((60, 520, 1020, 680), cor, r=10)
    p.ret((200, 820, 880, 1420), (60, 60, 70), r=10)
    for y in range(840, 1400, 40):
        p.linha([(200, y), (880, y)], fill=(90, 90, 100), w=6)
    p.ret((-20, 1410, WW + 20, 1500), (190, 185, 175), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (90, 90, 100), r=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = fnt(fc, 76)
    d.text((540 - f.getlength(nome) / 2, 555), nome, font=f, fill=(255, 255, 255))
    base.alpha_composite(placa_fechado(fc).resize((560, 237)), (260, 740))
    return base


def escritorio():
    base = gradiente(WW, WH, (220, 225, 235), (200, 205, 215))
    p = Pincel(WW, WH)
    p.ret((560, 260, 980, 700), (170, 210, 240), r=10, ow=10)
    p.ret((-20, 1450, WW + 20, WH + 20), (150, 140, 135), r=0)
    p.ret((100, 1150, 980, 1230), (150, 110, 80), r=10)
    p.ret((150, 1230, 190, 1600), (130, 95, 70), r=8)
    p.ret((890, 1230, 930, 1600), (130, 95, 70), r=8)
    p.ret((560, 960, 820, 1150), (40, 40, 50), r=10)
    base.alpha_composite(p.pronto())
    return base


def goias(fc):
    base = gradiente(WW, WH, (130, 190, 240), (225, 235, 245))
    p = Pincel(WW, WH)
    p.elipse((760, 200, 920, 360), (255, 220, 90), ow=0)
    p.ret((-20, 1250, WW + 20, WH + 20), (200, 160, 90), r=0)
    for x in range(0, WW, 90):
        p.poli([(x, 1260), (x + 20, 1200), (x + 40, 1260)], (110, 160, 70), ow=0)
    p.ret((740, 900, 770, 1260), (120, 90, 60), r=6)
    p.ret((620, 860, 980, 980), (60, 140, 80), r=10)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = fnt(fc, 64)
    d.text((800 - f.getlength("GOIÁS") / 2, 885), "GOIÁS", font=f, fill=(255, 255, 255))
    return base


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeMilhao(vc.Filme):
    def __init__(self, palavras, fc, dur_total):
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.voce, self.chefe, self.cida = Ator(VOCE), Ator(CHEFE), Ator(CIDA)
        self.viz, self.tia = Ator(VIZINHO), Ator(TIA)
        self.povo = [Ator(c) for c in POVO]
        self.gov = governo(fc)
        self.rua = vco.rua(fc)
        self.rua_vazia = vco.rua(fc, chuva=True)
        self.padaria = padaria(fc)
        self.padaria_fila = padaria(fc, fila=True)
        self.mercado = loja(fc, "MERCADO", (40, 120, 200))
        self.farmacia = loja(fc, "FARMÁCIA", (60, 170, 100))
        self.escritorio = escritorio()
        self.goias = goias(fc)
        self.carros = [vco.Carro((220, 50, 50)), vco.Carro((40, 110, 200)), vco.Carro((250, 200, 50))]
        self.lancha = lancha()
        self.carrinho = carrinho()
        self.pao, self.pq = pao(), pao_queijo()
        self.nota = nota_trilhoes(fc)
        self.fechado = placa_fechado(fc)
        self.caminhao, self.onibus = caminhao(), onibus()
        self.lixeira = lixeira()
        self.relogio, self.cel = relogio_pulso(), celular_icone()
        self.dinheiro = vco.dinheiro(5)
        self.pix = vs.celular(fc, "PIX", [("Você recebeu", 50, (60, 60, 80)),
                                          ("R$ 1.000.000", 84, VERDE), ("Governo Federal", 40, (130, 130, 145))],
                              cor=(50, 190, 170))
        self.tags = {k: etiqueta(fc, k) for k in ("R$ 30", "R$ 300", "R$ 3.000")}
        self.tag_pq = etiqueta(fc, "R$ 1.000.000", "PÃO DE QUEIJO")
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        P = [
            (0.00, self.p_governo, "", "corte"),
            (3.82, self.p_pix, "", "whip"),
            (5.32, self.p_sonho, "", "corte"),
            (6.54, self.p_festa, "quente", "whip"),
            (9.46, self.p_demissao, "", "corte"),
            (10.96, self.p_carros, "", "whip"),
            (13.06, self.p_lancha, "", "corte"),
            (14.86, self.p_goias, "", "corte"),
            (16.08, self.p_padaria, "", "whip"),
            (20.84, self.p_chefe_ri, "", "corte"),
            (23.12, self.p_chefe_close, "", "corte"),
            (26.46, self.p_rua_vazia, "triste", "zoom"),
            (29.00, self.p_caminhao, "triste", "corte"),
            (31.08, self.p_mercado, "triste", "corte"),
            (32.48, self.p_farmacia, "triste", "corte"),
            (33.78, self.p_estranha, "triste", "corte"),
            (35.76, self.p_arroz, "", "whip"),
            (40.02, self.p_3mil, "", "corte"),
            (41.72, self.p_carrinho, "", "corte"),
            (45.46, self.p_licao, "", "whip"),
            (50.42, self.p_fato, "", "corte"),
            (52.06, self.p_zimbabue, "sepia", "zoom"),
            (54.08, self.p_nota, "sepia", "corte"),
            (57.02, self.p_onibus, "sepia", "corte"),
            (60.00, self.p_quem, "", "whip"),
            (62.68, self.p_cida_rica, "quente", "corte"),
            (63.58, self.p_lixo, "", "corte"),
            (65.30, self.p_pao, "quente", "corte"),
            (66.68, self.p_fila, "quente", "whip"),
            (68.70, self.p_trocas, "quente", "corte"),
            (72.96, self.p_chefe_fila, "", "whip"),
            (76.92, self.p_cida_olha, "quente", "corte"),
            (79.86, self.p_fala, "quente", "corte"),
            (81.96, self.p_final, "quente", "corte"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))

    def fundo(self, c1=(250, 225, 180), c2=(240, 195, 150)):
        return gradiente(WW, WH, c1, c2)

    def chuva_dinheiro(self, f, t, n=16):
        dr = ImageDraw.Draw(f)
        rng = random.Random(1)
        for _ in range(n):
            x = rng.uniform(0, OUT_W)
            y = (rng.uniform(-400, 0) + t * rng.uniform(250, 420)) % (OUT_H + 100) - 50
            a = rng.uniform(0, 6) + t * 3
            pts = [(-38, -20), (38, -20), (38, 20), (-38, 20)]
            pts = [(x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)) for px, py in pts]
            dr.polygon(pts, fill=(110, 190, 140), outline=(40, 100, 60))

    # ------------------------- planos -------------------------
    def p_governo(self, t, d):
        f = camera(self.gov.copy(), 540, 1050, 1.0 + 0.12 * ease_io(t / d))
        if t > 1.5:
            texto_pop(f, "R$ 1.000.000", self.fc, t - 1.5, OUT_W / 2, OUT_H * 0.2, 88, (255, 214, 40))
        if t > 2.6:
            texto_pop(f, "PRA CADA UM", self.fc, t - 2.6, OUT_W / 2, OUT_H * 0.3, 60)
        return f

    def p_pix(self, t, d):
        m = self.fundo((40, 60, 70), (20, 30, 35))
        m.alpha_composite(brilho((1000, 1000), (80, 230, 200), 500, 0.5), (40, 460))
        tr = 8 * math.sin(t * 50) if t < 0.4 else 0
        self.segura(m, self.pix, 540 + tr, 900, 760)
        return camera(m, 540, 960, 1.05 + 0.1 * ease_out(t / d))

    def p_sonho(self, t, d):
        m = self.fundo((140, 220, 160), (90, 180, 120))
        self.voce.desenhar(m, t, 540, 2450, escala=2.7, expr="ri" if int(t * 5) % 2 else "feliz", piscar=False)
        f = camera(m, 540, 1000, 1.05)
        self.chuva_dinheiro(f, t)
        return f

    def p_festa(self, t, d):
        m = self.rua.copy()
        for i, (a, x) in enumerate(zip(self.povo, (130, 340, 540, 740, 950))):
            pulo = 30 * abs(math.sin(t * 7 + i))
            a.desenhar(m, t + i, x, 1760, escala=0.9, expr="ri" if int(t * 5 + i) % 2 else "feliz",
                       pose="acena" if int(t * 3 + i) % 2 else "idle", pulo=pulo)
        f = camera(m, 540, 1250, 1.12)
        confete(f, t)
        return f

    def p_demissao(self, t, d):
        m = self.escritorio.copy()
        self.voce.desenhar(m, t, 380, 1700, escala=1.3, expr="ri", pose="acena")
        f = camera(m, 540, 1200, 1.1)
        dr = ImageDraw.Draw(f)
        rng = random.Random(7)
        for i in range(8):     # papéis voando
            x = OUT_W * 0.6 + rng.uniform(-200, 200) + t * rng.uniform(-80, 80)
            y = OUT_H * 0.4 - t * rng.uniform(100, 300) + rng.uniform(-100, 100)
            a = t * 4 + i
            pts = [(-30, -40), (30, -40), (30, 40), (-30, 40)]
            pts = [(x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)) for px, py in pts]
            dr.polygon(pts, fill=(250, 250, 250), outline=(60, 60, 60))
        texto_pop(f, "DEMISSÃO!", self.fc, t, OUT_W * 0.5, OUT_H * 0.15, 100, (230, 50, 50))
        return f

    def p_carros(self, t, d):
        m = self.rua.copy()
        for i, c in enumerate(self.carros):
            k = ease_out(min(1, max(0, (t - i * 0.35) / 0.5)))
            if k > 0:
                c.desenhar(m, 1500 - 800 * k, 1500 + i * 150, escala=0.55, giro=-k * 600)
        self.viz.desenhar(m, t, 260, 1780, escala=1.1, expr="ri", pose="acena")
        f = camera(m, 540, 1300, 1.15)
        if t > 1.1:
            texto_pop(f, "3 CARROS", self.fc, t - 1.1, OUT_W * 0.6, OUT_H * 0.15, 90, (255, 214, 40))
        return f

    def p_lancha(self, t, d):
        m = self.fundo((120, 200, 240), (60, 150, 210))
        self.segura(m, self.lancha, 560, 1200 + 10 * math.sin(t * 3), 880, rot=2 * math.sin(t * 2))
        self.tia.desenhar(m, t, 520, 1150, escala=0.8, expr="ri", pose="acena")
        f = camera(m, 540, 1050, 1.1)
        return f

    def p_goias(self, t, d):
        m = self.goias.copy()
        self.segura(m, self.lancha, 420, 1170, 700)
        self.tia.desenhar(m, t, 420, 1150, escala=0.75, expr="surpreso")
        f = camera(m, 540, 1050, 1.1)
        texto_pop(f, "?", self.fc, t, OUT_W * 0.3, OUT_H * 0.25, 140)
        return f

    def p_padaria(self, t, d):
        m = self.padaria.copy()
        self.cida.desenhar(m, t, 780, 1720, escala=1.25, expr="feliz", pose="entrega")
        hx, hy = self.mao(780, 1720, 1.25, t)
        self.segura(m, self.pao, hx + 40, hy - 10, 180)
        f = camera(m, 560, 1200, 1.1)
        if t > 1.2:
            texto_pop(f, "DONA CIDA", self.fc, t - 1.2, OUT_W * 0.5, OUT_H * 0.12, 90, (255, 214, 40))
        if t > 3.6:
            texto_pop(f, "5:00", self.fc, t - 3.6, OUT_W * 0.25, OUT_H * 0.22, 100, (255, 255, 255))
        return f

    def p_chefe_ri(self, t, d):
        m = self.padaria.copy()
        self.cida.desenhar(m, t, 820, 1720, escala=1.15, expr="neutro")
        rindo = int(t * 5) % 2
        self.chefe.desenhar(m, t, 330, 1740, escala=1.3, expr="ri" if rindo else "feliz", pose="aponta", pulo=6 * rindo)
        f = camera(m, 560, 1220, 1.12)
        texto_pop(f, "HA HA", self.fc, t, OUT_W * 0.28, OUT_H * 0.18, 80)
        return f

    def p_chefe_close(self, t, d):
        m = self.fundo((220, 220, 230), (190, 190, 205))
        self.chefe.desenhar(m, t, 540, 2450, escala=2.7, expr="ri" if t > 1.5 else "bravo", piscar=False)
        return camera(m, 540, 1000, 1.05 + 0.08 * ease_io(t / d))

    def p_rua_vazia(self, t, d):
        m = self.rua_vazia.copy()
        f = camera(m, 540, 1150, 1.05 + 0.08 * ease_io(t / d))
        texto_pop(f, "SEGUNDA-FEIRA", self.fc, t, OUT_W * 0.5, OUT_H * 0.15, 80, (255, 255, 255))
        dr = ImageDraw.Draw(f, "RGBA")
        x = (t * 160) % (OUT_W + 200) - 100       # bola de feno passando
        y = OUT_H * 0.72 - abs(math.sin(t * 5)) * 30
        dr.ellipse((x - 40, y - 40, x + 40, y + 40), fill=(170, 140, 90, 230), outline=(110, 90, 60), width=4)
        return f

    def p_caminhao(self, t, d):
        m = self.rua_vazia.copy()
        self.segura(m, self.caminhao, 540, 1430, 960)
        self.segura(m, self.fechado, 330, 1240, 360, rot=-8)
        return camera(m, 540, 1200, 1.15)

    def p_mercado(self, t, d):
        return camera(self.mercado.copy(), 540, 1050, 1.05 + 0.08 * ease_io(t / d))

    def p_farmacia(self, t, d):
        return camera(self.farmacia.copy(), 540, 1050, 1.05 + 0.08 * ease_io(t / d))

    def p_estranha(self, t, d):
        m = self.fundo((210, 205, 200), (180, 175, 170))
        self.voce.desenhar(m, t, 540, 2450, escala=2.7, expr="surpreso", piscar=False)
        f = camera(m, 540, 1000, 1.05 + 0.08 * ease_io(t / d))
        texto_pop(f, "?", self.fc, t, OUT_W * 0.8, OUT_H * 0.2, 160)
        return f

    def tag(self, chave, t, d, tremor=0.0, raio=False):
        m = self.fundo((250, 240, 220), (230, 215, 190))
        if raio:
            m.alpha_composite(brilho((1080, 1080), (255, 230, 120), 540, 0.7), (0, 420))
        dx = tremor * math.sin(t * 50)
        self.segura(m, self.tags[chave] if isinstance(chave, str) else chave, 540 + dx, 900, 800)
        return camera(m, 540, 960, 1.05)

    def p_arroz(self, t, d):
        k = "R$ 30" if t < 37.9 - 35.76 else "R$ 300"
        f = self.tag(k, t, d, tremor=4 if k == "R$ 300" else 0)
        if k == "R$ 300":
            texto_pop(f, "x10", self.fc, t - (37.9 - 35.76), OUT_W * 0.8, OUT_H * 0.22, 120, (230, 50, 50))
        return f

    def p_3mil(self, t, d):
        return self.tag("R$ 3.000", t, d, tremor=9, raio=True)

    def p_carrinho(self, t, d):
        m = self.fundo((200, 225, 245), (170, 200, 230))
        self.segura(m, self.carrinho, 420, 1150, 700)
        self.segura(m, self.pq, 830, 1250, 200)
        f = camera(m, 540, 1000, 1.05)
        if t > 1.2:
            texto_pop(f, "1 PÃO DE QUEIJO", self.fc, t - 1.2, OUT_W * 0.5, OUT_H * 0.15, 70, (255, 214, 40))
        return f

    def p_licao(self, t, d):
        m = self.fundo((250, 240, 220), (230, 215, 190))
        # balança: dinheiro (muito) x comida (pouca) — o dinheiro vai "perdendo a cor"
        p = Pincel(WW, WH)
        p.ret((520, 700, 560, 1500), (120, 100, 80), r=10)
        ang = math.radians(-12 * ease_io(min(1, t / 1.5)))
        x0, y0 = 540, 760
        a = (x0 - 290 * math.cos(ang), y0 - 290 * math.sin(ang))
        b = (x0 + 290 * math.cos(ang), y0 + 290 * math.sin(ang))
        p.linha([a, b], fill=(120, 100, 80), w=20)
        p.ret((440, 1480, 640, 1540), (120, 100, 80), r=10)
        m.alpha_composite(p.pronto())
        din = self.dinheiro.resize((300, 195))
        if t > 2.0:
            din = ImageEnhance.Color(din).enhance(max(0, 1 - (t - 2.0) / 1.5))
            din.putalpha(din.getchannel("A").point(lambda v: int(v * max(0.35, 1 - (t - 2.0) / 3))))
        m.alpha_composite(din, (int(a[0] - 150), int(a[1] - 185)))
        self.segura(m, self.pao, b[0], b[1] - 60, 200)
        f = camera(m, 540, 960, 1.05)
        if t > 3.0:
            texto_pop(f, "SEM PRODUÇÃO = SEM VALOR", self.fc, t - 3.0, OUT_W * 0.5, OUT_H * 0.13, 50, (230, 50, 50))
        return f

    def p_fato(self, t, d):
        m = self.fundo((40, 40, 55), (20, 20, 30))
        f = camera(m, 540, 960, 1.0)
        texto_pop(f, "FATO REAL", self.fc, t, OUT_W * 0.5, OUT_H * 0.42, 130, (255, 214, 40))
        return f

    def p_zimbabue(self, t, d):
        m = self.fundo((230, 200, 150), (200, 160, 110))
        p = Pincel(WW, WH)
        for i, cor in enumerate(((40, 150, 70), (250, 210, 40), (220, 40, 40), (30, 30, 30),
                                 (220, 40, 40), (250, 210, 40), (40, 150, 70))):
            p.ret((140, 560 + i * 90, 940, 650 + i * 90), cor, r=0, ow=0)
        p.poli([(140, 560), (520, 875), (140, 1190)], (250, 250, 250), ow=0)
        m.alpha_composite(p.pronto())
        f = camera(m, 540, 900, 1.05 + 0.1 * ease_io(t / d))
        texto_pop(f, "ZIMBÁBUE · 2008", self.fc, t, OUT_W * 0.5, OUT_H * 0.14, 76, (255, 255, 255))
        return f

    def p_nota(self, t, d):
        m = self.fundo((230, 220, 200), (210, 195, 170))
        self.segura(m, self.nota, 540, 900, 960, rot=-4 + 2 * math.sin(t * 2))
        return camera(m, 540, 950, 1.0 + 0.2 * ease_io(t / d))

    def p_onibus(self, t, d):
        m = self.rua.copy()
        k = ease_io(min(1, max(0, t - 0.8) / 1.6))
        self.segura(m, self.onibus, 640 + 1100 * k, 1460, 900)
        self.voce.desenhar(m, t, 230, 1760, escala=1.15, expr="triste" if k > 0.2 else "neutro", pose="entrega")
        hx, hy = self.mao(230, 1760, 1.15, t)
        self.segura(m, self.nota, hx + 70, hy - 10, 200)
        f = camera(m, 540, 1250, 1.12)
        if k > 0.3:
            texto_pop(f, "NÃO ACEITO", self.fc, t - 1.3, OUT_W * 0.6, OUT_H * 0.18, 80, (230, 50, 50))
        return f

    def p_quem(self, t, d):
        m = self.fundo((30, 30, 45), (15, 15, 25))
        spr = self.cida.spr("neutro", "idle")
        sil = Image.new("RGBA", spr.size, (10, 10, 15, 255))
        sil.putalpha(spr.getchannel("A"))
        m.alpha_composite(brilho((900, 900), (255, 220, 120), 450, 0.4), (90, 700))
        g.colar(m, sil, 540, 1800, escala=1.6)
        f = camera(m, 540, 1150, 1.05 + 0.1 * ease_io(t / d))
        texto_pop(f, "?", self.fc, t, OUT_W * 0.5, OUT_H * 0.2, 180, (255, 214, 40))
        return f

    def p_cida_rica(self, t, d):
        m = self.fundo((255, 215, 140), (245, 170, 90))
        m.alpha_composite(brilho((1080, 1080), (255, 245, 200), 540, 0.9), (0, 400))
        self.cida.desenhar(m, t, 540, 1800, escala=1.6, expr="feliz", pose="acena")
        p = Pincel(400, 260)                       # coroa
        p.poli([(20, 240), (20, 60), (110, 150), (200, 20), (290, 150), (380, 60), (380, 240)], (250, 200, 40))
        coroa = p.pronto()
        self.segura(m, coroa, 540, 1800 - 640 * 1.6 + 30, 230)
        f = camera(m, 540, 1200, 1.1)
        particulas(f, t, 50, semente=60)
        return f

    def p_lixo(self, t, d):
        m = self.fundo((210, 220, 210), (180, 195, 180))
        self.segura(m, self.lixeira, 540, 1250, 520)
        k = min(1, t / 0.7)
        y = 500 + 600 * ease_out(k)
        if t < 0.9:
            self.segura(m, self.dinheiro, 540, y, 420, rot=t * 200)
        return camera(m, 540, 1000, 1.05)

    def p_pao(self, t, d):
        m = self.fundo((255, 220, 160), (245, 180, 110))
        m.alpha_composite(brilho((1080, 1080), (255, 245, 200), 540, 0.9), (0, 420))
        self.segura(m, self.pao, 540, 950, 760, rot=3 * math.sin(t * 2))
        f = camera(m, 540, 960, 1.0 + 0.1 * ease_io(t / d))
        particulas(f, t, 40, semente=61)
        return f

    def p_fila(self, t, d):
        m = self.padaria_fila.copy()
        larg = WW * 2
        mundo = Image.new("RGBA", (larg, WH))
        mundo.alpha_composite(m, (0, 0))
        mundo.alpha_composite(self.rua, (WW, 0))
        for i in range(10):
            a = self.povo[i % len(self.povo)]
            a.desenhar(mundo, t + i, 700 + i * 150, 1760 + (i % 2) * 30, escala=0.85,
                       expr="neutro" if i % 3 else "triste")
        self.cida.desenhar(mundo, t, 560, 1720, escala=1.1, expr="feliz", pose="entrega")
        x = 540 + 900 * ease_io(t / d)
        vw = WW / 1.1
        crop = mundo.crop((int(x - vw / 2), 0, int(x + vw / 2), WH))
        f = camera(crop.resize((WW, WH)), 540, 1150, 1.1)
        return f

    def p_trocas(self, t, d):
        m = self.padaria_fila.copy()
        self.cida.desenhar(m, t, 760, 1720, escala=1.25, expr="feliz", pose="entrega")
        hx, hy = self.mao(760, 1720, 1.25, t)
        self.segura(m, self.pao, hx + 30, hy - 10, 180)
        itens = [(self.relogio, 69.58), (self.cel, 70.30), (None, 71.16)]
        for i, (obj, ts) in enumerate(itens):
            tt = t - (ts - 68.70)
            if tt > 0:
                k = ease_out(min(1, tt / 0.4))
                x, y = 120 + 520 * k, 900 + i * 150
                if obj is None:
                    self.carros[0].desenhar(m, x, y + 180, escala=0.35)
                else:
                    self.segura(m, obj, x, y, 140)
        return camera(m, 540, 1200, 1.1)

    def p_chefe_fila(self, t, d):
        m = self.padaria_fila.copy()
        for i in range(3):
            self.povo[i].desenhar(m, t + i, 640 - i * 160, 1740, escala=0.9, expr="neutro")
        self.chefe.desenhar(m, t, 150, 1780, escala=1.0, expr="triste", rot=3 * math.sin(t * 2))
        k = ease_io(min(1, t / 1.6))
        f = camera(m, 540 - 300 * k, 1200 + 150 * k, 1.1 + 0.6 * k)
        dr = ImageDraw.Draw(f, "RGBA")
        if k > 0.8:
            for (x, y) in ((0.38, 0.5), (0.6, 0.42), (0.52, 0.62)):
                dr.ellipse((OUT_W * x - 18, OUT_H * y - 10, OUT_W * x + 18, OUT_H * y + 10), fill=(60, 50, 40, 160))
            texto_pop(f, "ronc…", self.fc, t - 1.6, OUT_W * 0.7, OUT_H * 0.3, 60)
        return f

    def p_cida_olha(self, t, d):
        m = self.fundo((255, 215, 160), (240, 180, 120))
        self.cida.desenhar(m, t, 540, 2450, escala=2.7, expr="neutro" if t < 1.4 else "feliz", piscar=False)
        return camera(m, 540, 1000, 1.05 + 0.08 * ease_io(t / d))

    def p_fala(self, t, d):
        m = self.padaria_fila.copy()
        self.chefe.desenhar(m, t, 300, 1740, escala=1.2, expr="triste")
        self.cida.desenhar(m, t, 760, 1720, escala=1.3, expr="feliz", pose="entrega")
        hx, hy = self.mao(760, 1720, 1.3, t)
        self.segura(m, self.pao, hx + 30, hy - 10, 200)
        return camera(m, 540, 1200, 1.12)

    def p_final(self, t, d):
        m = self.fundo((255, 210, 140), (245, 170, 90))
        m.alpha_composite(brilho((1080, 1080), (255, 245, 200), 540, 0.9), (0, 400))
        self.cida.desenhar(m, t, 540, 2450, escala=2.7, expr="ri" if int(t * 3) % 2 else "feliz", piscar=False)
        self.segura(m, self.pao, 540, 1720, 520)
        f = camera(m, 540, 1000, 1.05 + 0.1 * ease_io(t / d))
        particulas(f, t, 40, semente=70)
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
        ev += [("brilho", 3.82), ("brilho", 62.68), ("brilho", 65.30), ("brilho", 37.9), ("brilho", 40.02)]
        ev += [("toc", 69.58), ("toc", 70.30), ("toc", 71.16)]
        return ev


def carregar_palavras(caminho):
    pal = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            if w["w"].startswith("-") and pal:
                pal[-1]["w"] += w["w"]
                pal[-1]["e"] = w["e"]
                continue
            pal.append(dict(w=w["w"], s=w["s"], e=w["e"]))
    troca = {"30": "trinta", "300.": "trezentos.", "3": "três", "100": "cem", "dona": "Dona"}
    for w in pal:
        w["w"] = troca.get(w["w"], w["w"])
    return pal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_milhao_de_todo_mundo.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeMilhao(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.2)
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

    tmp = tempfile.mkdtemp(prefix="milhao_")
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
