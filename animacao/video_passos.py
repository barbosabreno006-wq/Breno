#!/usr/bin/env python3
"""
"Cem Passos" — bairro onde cada pessoa só pode dar 100 passos por dia.

Muito movimento: caminhadas com o contador da pulseira subindo a cada passo (com som de passo),
pão no varal, carta voando, corrida "São Parado", torre de recarga, cadeirinhas, a chuva
lavando o muro e revelando o cartaz, flashback da maratona, contagem em câmera lenta,
os "Parados" fugindo e o Caio sem ar no meio-fio.

    python3 animacao/video_passos.py --narracao narr.wav --transcricao transcricao.json --fonte Poppins.ttf
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
import video_numero as vn  # noqa: E402
import video_estatua as ve  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, gradiente, brilho,
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(101)

TEO = dict(pele=(214, 160, 120), cabelo=(70, 45, 30), camisa=(230, 90, 60), calca=(50, 70, 120),
           sapato=(240, 240, 240), tipo="menino")
BENTO = dict(pele=(176, 120, 85), cabelo=(225, 225, 230), camisa=(70, 120, 190), calca=(90, 80, 70),
             sapato=(70, 55, 45), tipo="vovo_h")
BENTO_JOVEM = dict(pele=(176, 120, 85), cabelo=(40, 30, 25), camisa=(250, 250, 250), calca=(40, 90, 200),
                   sapato=(230, 60, 60), tipo="pai", bigode=False)
CAIO = dict(pele=(235, 195, 160), cabelo=(200, 150, 60), camisa=(120, 60, 160), calca=(40, 40, 60),
            sapato=(250, 210, 60), tipo="menino")
VARGAS = dict(pele=(232, 186, 150), cabelo=(40, 35, 30), camisa=(40, 40, 50), calca=(35, 35, 45),
              sapato=(25, 25, 25), tipo="pai", gravata=(240, 190, 40))
POVO = ve.POVO
DOURADO = (250, 200, 50)
vc.DESTAQUE_VERMELHO = set()


# --------------------------------------------------------------------------
# Objetos
# --------------------------------------------------------------------------
_CACHE_PULS = {}


def pulseira(fc, n, estilo="normal", w=520):
    """Pulseira de passos: estilo normal | dourada | vermelha | verde."""
    k = (n, estilo, w)
    if k in _CACHE_PULS:
        return _CACHE_PULS[k]
    cores = {"normal": ((60, 62, 72), (120, 190, 110)), "dourada": ((200, 160, 40), (255, 240, 170)),
             "vermelha": ((60, 62, 72), (235, 70, 60)), "verde": ((60, 62, 72), (90, 220, 120))}
    corpo, visor = cores[estilo]
    p = Pincel(w, w * 0.62)
    p.ret((10, 90, w - 10, 230), corpo, r=60)
    p.ret((w * 0.18, 30, w * 0.82, 290), corpo, r=50)
    p.ret((w * 0.23, 60, w * 0.77, 260), visor, r=26, ow=6)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f1, f2 = vc.fonte(fc, 26), vc.fonte(fc, 104 if len(str(n)) <= 3 else 80)
    txt = str(n)
    d.text((w / 2 - f1.getlength("PASSOS") / 2, 70), "PASSOS", font=f1, fill=(30, 40, 30))
    d.text((w / 2 - f2.getlength(txt) / 2, 100), txt, font=f2, fill=(30, 40, 30))
    _CACHE_PULS[k] = img
    return img


def bengala():
    p = Pincel(160, 640)
    p.capsula((80, 120), (80, 620), 26, (130, 85, 55))
    p.arco((20, 30, 140, 170), 180, 360, fill=OUTLINE, w=40)
    p.arco((24, 34, 136, 166), 180, 360, fill=(130, 85, 55), w=24)
    return p.pronto()


def pao(w=220):
    return vm.pao(w)


def cadeirinha(cor=(220, 60, 60)):
    p = Pincel(420, 420)
    p.ret((80, 120, 340, 260), cor, r=24)
    p.ret((260, 20, 330, 200), cor, r=20)
    for x in (120, 300):
        p.elipse((x - 60, 260, x + 60, 380), (40, 40, 45))
        p.elipse((x - 22, 298, x + 22, 342), (200, 200, 205), ow=4)
    return p.pronto()


def cartaz(fc, w=620):
    h = int(w * 1.35)
    p = Pincel(w, h)
    p.ret((10, 10, w - 10, h - 10), (245, 235, 205), r=10)
    p.ret((60, 300, w - 60, 700), (200, 190, 170), r=8, ow=6)
    img = p.pronto()
    ator = g.Ator(BENTO_JOVEM)
    img.alpha_composite(ator.spr("ri", "acena").resize((240, 452)), (int(w / 2 - 120), 260))
    d = ImageDraw.Draw(img)
    for txt, y, tam, cor in (("MARATONA", 40, 76, (200, 50, 40)), ("DO BAIRRO", 130, 56, (200, 50, 40)),
                             ("42 KM", 210, 60, (40, 40, 60)), ("CAMPEÃO:", 720, 46, (40, 40, 60)),
                             ("BENTO SILVA", 780, 62, (40, 40, 60))):
        f = vc.fonte(fc, tam)
        d.text((w / 2 - f.getlength(txt) / 2, y), txt, font=f, fill=cor)
    return img


def maca():
    p = Pincel(900, 300)
    p.ret((40, 60, 860, 150), (240, 240, 245), r=20)
    p.ret((60, 150, 840, 175), (150, 150, 160), r=8)
    for x in (100, 800):
        p.ret((x - 10, 175, x + 10, 280), (150, 150, 160), r=4)
    return p.pronto()


def coracao(w=120, cor=(230, 60, 90)):
    p = Pincel(w, w)
    p.elipse((10, 15, w / 2 + 6, w / 2 + 10), cor, ow=0)
    p.elipse((w / 2 - 6, 15, w - 10, w / 2 + 10), cor, ow=0)
    p.poli([(12, w / 2 - 4), (w - 12, w / 2 - 4), (w / 2, w - 10)], cor, ow=0)
    return p.pronto()


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def bairro(fc, varal=True, tarde=False):
    base = gradiente(WW, WH, (250, 190, 140) if tarde else (150, 200, 240),
                     (255, 225, 180) if tarde else (225, 238, 250))
    p = Pincel(WW, WH)
    vc.nuvem(p, 140, 230, 0.8)
    cores = g.CORES_CASAS
    for i, x in enumerate((-40, 250, 540, 830)):
        top = 520 + (i % 2) * 70
        p.ret((x, top, x + 280, 1420), cores[(i + 1) % 6], r=6)
        for jy in range(top + 60, 1300, 220):
            p.ret((x + 40, jy, x + 130, jy + 120), (255, 240, 200), r=8, ow=6)
            p.ret((x + 160, jy, x + 250, jy + 120), (255, 240, 200), r=8, ow=6)
    if varal:
        for y0 in (640, 880):
            p.linha([(80, y0), (540, y0 + 40), (1000, y0)], fill=(80, 80, 80), w=4)
    p.ret((-20, 1410, WW + 20, 1500), (200, 190, 175), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (90, 90, 100), r=0)
    base.alpha_composite(p.pronto())
    return base


def torre_cena(fc):
    base = gradiente(WW, WH, (150, 200, 240), (225, 238, 250))
    p = Pincel(WW, WH)
    p.ret((-20, 1300, WW + 20, WH + 20), (120, 180, 100), r=0)
    p.poli([(400, 1310), (680, 1310), (600, 300), (480, 300)], (130, 130, 145))
    for y in range(380, 1300, 120):
        p.linha([(470 - (y - 300) * 0.08, y), (610 + (y - 300) * 0.08, y)], fill=(90, 90, 105), w=8)
    p.ret((380, 180, 700, 320), (110, 110, 125), r=16)
    p.ret((300, 360, 780, 520), (230, 60, 50), r=16, ow=8)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    for txt, y, tam in (("RECARGA", 372, 60), ("20 PASSOS  R$ 10", 448, 44)):
        f = vc.fonte(fc, tam)
        d.text((540 - f.getlength(txt) / 2, y), txt, font=f, fill=(255, 255, 255))
    return base


def praca(fc, tarde=False):
    base = gradiente(WW, WH, (250, 200, 150) if tarde else (150, 200, 240),
                     (255, 230, 190) if tarde else (225, 238, 250))
    p = Pincel(WW, WH)
    vc.nuvem(p, 700, 260, 0.8)
    for x in (120, 900):                                      # árvores
        p.ret((x - 20, 900, x + 20, 1300), (110, 75, 50), r=6)
        p.elipse((x - 150, 650, x + 150, 980), (90, 170, 90))
    p.ret((620, 760, 1040, 1300), (245, 245, 245), r=8)        # posto de saúde
    p.ret((780, 880, 880, 940), (230, 50, 50), r=0, ow=0)
    p.ret((800, 860, 860, 960), (230, 50, 50), r=0, ow=0)
    p.ret((-20, 1290, WW + 20, WH + 20), (210, 195, 170), r=0)
    for x in range(0, WW, 120):
        p.linha([(x, 1290), (x - 80, WH)], fill=(190, 175, 150), w=4)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 40)
    d.text((830 - f.getlength("POSTO") / 2, 1000), "POSTO", font=f, fill=(200, 40, 40))
    return base


def muro_cena(fc):
    base = gradiente(WW, WH, (110, 120, 140), (90, 100, 120))
    p = Pincel(WW, WH)
    p.ret((60, 300, 1020, 1500), (200, 190, 180), r=6)
    for y in range(340, 1480, 80):
        for x in range(60 + (y // 80 % 2) * 60, 1020, 120):
            p.ret((x, y, x + 116, y + 76), (190, 180, 170), r=4, ow=3, outline=(170, 160, 150))
    p.ret((-20, 1500, WW + 20, WH + 20), (80, 85, 95), r=0)
    base.alpha_composite(p.pronto())
    return base


def quarto_noite():
    base = gradiente(WW, WH, (35, 40, 75), (55, 55, 85))
    p = Pincel(WW, WH)
    p.ret((620, 260, 960, 620), (20, 25, 50), r=10, ow=10)
    p.elipse((760, 320, 860, 420), (240, 235, 210), ow=0)
    p.ret((-20, 1400, WW + 20, WH + 20), (70, 60, 70), r=0)
    p.ret((60, 1150, 1020, 1450), (80, 100, 150), r=30)
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((900, 900), (255, 220, 160), 450, 0.35), (90, 700))
    return base


def ponte_cena(fc):
    base = gradiente(WW, WH, (250, 170, 110), (255, 220, 170))
    p = Pincel(WW, WH)
    p.elipse((380, 520, 700, 840), (255, 215, 120), ow=0)
    p.ret((-20, 960, WW + 20, 1300), (90, 140, 200), r=0, ow=0)      # rio
    for y in range(990, 1290, 50):
        p.linha([(60, y), (300, y)], fill=(150, 190, 230), w=5)
        p.linha([(600, y + 20), (900, y + 20)], fill=(150, 190, 230), w=5)
    for i, x in enumerate(range(20, WW, 150)):                           # bairro do outro lado (cinza)
        p.ret((x, 760 - (i % 3) * 40, x + 130, 960), (120, 120, 130), r=4)
        p.ret((x + 40, 800 - (i % 3) * 40, x + 90, 850 - (i % 3) * 40), (90, 90, 100), r=4, ow=0)
    p.ret((-20, 1300, WW + 20, 1400), (150, 110, 80), r=0)               # ponte
    for x in range(0, WW, 90):
        p.ret((x, 1230, x + 16, 1310), (130, 90, 60), r=4)
    p.ret((-20, 1220, WW + 20, 1240), (130, 90, 60), r=0, ow=0)
    p.ret((-20, 1400, WW + 20, WH + 20), (120, 160, 110), r=0)
    base.alpha_composite(p.pronto())
    return base


def cinza(spr):
    k = ("c", id(spr))
    if k not in ve._CACHE_GELO:
        rgb = ImageEnhance.Color(spr.convert("RGB")).enhance(0.0)
        rgb = ImageEnhance.Brightness(rgb).enhance(0.95)
        out = rgb.convert("RGBA")
        out.putalpha(spr.getchannel("A"))
        ve._CACHE_GELO[k] = out
    return ve._CACHE_GELO[k]


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmePassos(ve.FilmeEstatua):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.teo, self.bento, self.bentoj = P_(TEO), P_(BENTO), P_(BENTO_JOVEM)
        self.caio, self.vargas = P_(CAIO), P_(VARGAS)
        self.povo = [P_(c) for c in POVO]
        self.blur = {}
        self.bairro, self.bairro_t = bairro(fc), bairro(fc, tarde=True)
        self.torre = torre_cena(fc)
        self.praca, self.praca_t = praca(fc), praca(fc, tarde=True)
        self.muro = muro_cena(fc)
        self.cartaz = cartaz(fc)
        self.quarto = quarto_noite()
        self.ponte = ponte_cena(fc)
        self.escola = vn.portao(fc)
        self.beng, self.cad, self.mac = bengala(), cadeirinha(), maca()
        self.pao_img, self.carta = pao(), vc.envelope(240, selo=True)
        self.env_pag = vc.envelope(760, "PAGAMENTO\nParado de praça\nSemana 40", fc)
        self.cor = coracao()
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.passos_sfx = []
        self.FALA_CAIO = [(72.66, 75.4), (78.54, 81.9), (105.62, 109.0)]
        self.FALA_TEO = [(90.16, 91.2)]
        self.FALA_BENTO = [(92.52, 95.0), (138.08, 142.9)]
        self.TREMORES = [(4.14, 8), (82.52, 14), (114.78, 6), (116.56, 10), (147.22, 10)]

        P = [
            (0.00, self.p_hook, "", "corte"),
            (3.54, self.p_trava, "", "corte"),
            (8.22, self.p_pulseira, "", "whip"),
            (11.26, self.p_varal, "", "whip"),
            (13.68, self.p_namoro, "", "corte"),
            (15.94, self.p_carta, "", "corte"),
            (18.50, self.p_sao_parado, "", "whip"),
            (23.62, self.p_torre, "", "zoom"),
            (28.44, self.p_cadeirinha, "", "corte"),
            (32.76, self.p_parados, "", "whip"),
            (39.78, self.p_casa, "quente", "dissolve"),
            (45.30, self.p_guarda, "quente", "corte"),
            (47.82, self.p_caminho, "", "whip"),
            (53.56, self.p_chuva, "", "dissolve"),
            (59.20, self.p_cartaz, "", "zoom"),
            (63.86, self.p_corredor, "sepia", "zoom"),
            (65.54, self.p_caio, "", "whip"),
            (72.66, self.p_caio_anda, "", "corte"),
            (75.86, self.p_provoca, "", "corte"),
            (82.40, self.p_bengala, "", "corte"),
            (84.32, self.p_respira, "", "corte"),
            (86.24, self.p_pega, "", "corte"),
            (88.20, self.p_noite, "", "dissolve"),
            (91.62, self.p_vo_sorri, "", "corte"),
            (95.52, self.p_passa_mal, "", "whip"),
            (100.50, self.p_97, "", "corte"),
            (103.38, self.p_bloqueia, "", "corte"),
            (109.38, self.p_olha, "", "corte"),
            (111.68, self.p_contagem, "", "corte"),
            (116.56, self.p_cento_um, "", "corte"),
            (117.64, self.p_nada, "", "corte"),
            (119.08, self.p_corre, "", "whip"),
            (122.92, self.p_silencio, "", "corte"),
            (125.12, self.p_todos, "quente", "corte"),
            (127.90, self.p_parados_fogem, "", "corte"),
            (132.46, self.p_envelope, "", "zoom"),
            (135.48, self.p_vo_fala, "", "corte"),
            (143.04, self.p_caio_corre, "", "whip"),
            (147.22, self.p_caio_cai, "", "corte"),
            (150.38, self.p_vida_cadeirinha, "sepia", "dissolve"),
            (154.12, self.p_unico, "", "corte"),
            (158.24, self.p_licao, "quente", "dissolve"),
            (162.16, self.p_domingo, "quente", "whip"),
            (167.84, self.p_ponte, "quente", "dissolve"),
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
            if 0 <= dt < 0.5:
                k = a * (1 - dt / 0.5)
                dx, dy = k * math.sin(self.T * 90), k * math.cos(self.T * 70)
        return camera(m, cx + dx, cy + dy, z)

    def anda(self, pers, m, t, x, by, e, rate=2.4, expr="neutro", **kw):
        pose = "anda1" if int(t * rate) % 2 else "anda2"
        pers(m, t, x, by, e, expr=expr, pose=pose, pulo=6 * abs(math.sin(t * rate * math.pi)), **kw)

    def pulso(self, f, n, t, estilo="normal", x=0.5, y=0.07, w=300):
        img = pulseira(self.fc, n, estilo)
        s = w / img.width
        img = img.resize((int(img.width * s), int(img.height * s)), Image.BICUBIC)
        f.paste(img, (int(OUT_W * x - img.width / 2), int(OUT_H * y)), img)

    def contagem(self, T, t0, n0, rate, nmax=10 ** 6):
        return min(nmax, n0 + max(0, int((T - t0) * rate)))

    # ------------------------- planos -------------------------
    def p_hook(self, t, d):
        m = self.bairro.copy()
        x = 200 + 180 * t
        self.anda(self.teo, m, t, x, 1780, 1.1, expr="feliz")
        f = self.cam(m, 540, 1250, 1.1)
        n = self.contagem(self.T, 0, 95, 2.4, 100)
        self.pulso(f, n, t, "vermelha" if n >= 100 else "normal")
        if self.T > 1.86:
            texto_pop(f, "100 POR DIA", self.fc, self.T - 1.86, OUT_W / 2, OUT_H * 0.28, 80, (255, 214, 40))
        return f

    def p_trava(self, t, d):
        m = self.bairro.copy()
        trav = self.T >= 4.14
        if not trav:
            self.anda(self.povo[2], m, t, 420 + 160 * t, 1780, 1.2, expr="neutro")
        else:
            spr = self.povo[2].spr("surpreso", "anda1")
            g.colar(m, cinza(spr), 420 + 160 * (4.14 - 3.54), 1780, 1.2)
        f = self.cam(m, 540, 1250, 1.15 + (0.25 * ease_out((self.T - 4.14) / 0.4) if trav else 0))
        self.pulso(f, 101 if trav else 100, t, "vermelha")
        if trav:
            texto_pop(f, "TRAVOU!", self.fc, self.T - 4.14, OUT_W / 2, OUT_H * 0.3, 100, (230, 60, 60))
            if self.T > 7.26:
                texto_pop(f, "PRA SEMPRE", self.fc, self.T - 7.26, OUT_W / 2, OUT_H * 0.38, 64, (255, 255, 255))
        return f

    def p_pulseira(self, t, d):
        m = gradiente(WW, WH, (60, 62, 80), (35, 36, 50))
        p = Pincel(WW, WH)
        p.ret((-100, 820, WW + 100, 1180), TEO["pele"], r=150)
        m.alpha_composite(p.pronto())
        n = self.contagem(self.T, 8.22, 12, 3.0)
        self.segura(m, pulseira(self.fc, n, "normal"), 540, 1000, 760)
        f = self.cam(m, 540, 1000, 1.05 + 0.08 * ease_io(t / d))
        texto_pop(f, "+1", self.fc, (t * 3) % 1 / 3, OUT_W * 0.8, OUT_H * 0.25 - 60 * ((t * 3) % 1), 60,
                  (90, 220, 120))
        return f

    def p_varal(self, t, d):
        m = self.bairro.copy()
        k = ease_io(min(1, t / (d * 0.85)))
        x = 220 + 640 * k
        y = 640 + 40 * math.sin(k * math.pi) + 15
        self.segura(m, self.pao_img, x, y + 40, 180, rot=8 * math.sin(t * 8))
        self.povo[1](m, t, 220, 760, 0.45, expr="feliz", pose="entrega")
        self.povo[0](m, t, 860, 760, 0.45, expr="ri" if k > 0.95 else "feliz", pose="acena")
        f = self.cam(m, 540, 900, 1.25)
        texto_pop(f, "PADARIA", self.fc, t, OUT_W * 0.2, OUT_H * 0.1, 40, (255, 255, 255))
        return f

    def p_namoro(self, t, d):
        m = self.bairro.copy()
        self.povo[0](m, t, 230, 1010, 0.5, expr="feliz", pose="acena")
        self.povo[1](m, t, 850, 1010, 0.5, expr="ri", pose="acena")
        for i in range(4):
            k = ((t * 0.8 + i * 0.25) % 1.0)
            self.segura(m, self.cor, 280 + 520 * k, 820 - 60 * math.sin(k * math.pi), 70 + 20 * math.sin(t * 6))
        return self.cam(m, 540, 950, 1.25)

    def p_carta(self, t, d):
        m = self.bairro_t.copy()
        k = ease_io(min(1, t / (d * 0.8)))
        self.segura(m, self.carta, 220 + 620 * k, 920 + 50 * math.sin(k * math.pi), 160, rot=-10 + 20 * k)
        self.povo[3](m, t, 860, 1010, 0.5, expr="ri" if k > 0.95 else "neutro", pose="acena")
        f = self.cam(m, 540, 1000, 1.2)
        if k > 0.95:
            texto_pop(f, "SIM!", self.fc, t - d * 0.8, OUT_W * 0.8, OUT_H * 0.2, 70, (230, 60, 90))
        return f

    def p_sao_parado(self, t, d):
        m = self.bairro.copy()
        p = Pincel(WW, WH)
        p.ret((60, 900, 1020, 1000), (230, 60, 60), r=10)
        p.ret((60, 1000, 90, 1500), (110, 110, 120), r=4)
        p.ret((990, 1000, 1020, 1500), (110, 110, 120), r=4)
        p.ret((-20, 1700, WW + 20, 1720), (250, 250, 250), r=0, ow=0)
        m.alpha_composite(p.pronto())
        for i, (pers, x) in enumerate(zip(self.povo, (150, 340, 540, 740, 930))):
            lento = i == 2
            y = 1780 - (40 * ease_io(min(1, t / d)) if lento else 0)
            if lento:
                pers(m, t, x, y, 0.85, expr="bravo", pose="anda1" if int(t * 0.6) % 2 else "anda2")
            else:
                pers(m, t, x, 1780, 0.85, expr="neutro")
        f = self.cam(m, 540, 1250, 1.1)
        texto_pop(f, "SÃO PARADO", self.fc, 0.5, OUT_W / 2, OUT_H * 0.335, 54, (255, 255, 255))
        if self.T > 21.9:
            texto_pop(f, "GANHA QUEM CHEGA POR ÚLTIMO", self.fc, self.T - 21.9, OUT_W / 2, OUT_H * 0.12, 40,
                      (255, 214, 40))
        return f

    def p_torre(self, t, d):
        m = self.torre.copy()
        self.vargas(m, t, 540, 330, 0.55, expr="ri" if int(t * 3) % 2 else "feliz", pose="acena")
        f = self.cam(m, 540, 900 - 200 * ease_io(t / d), 1.0 + 0.3 * ease_io(t / d))
        dr = ImageDraw.Draw(f)
        rng = random.Random(3)
        for i in range(6):                                   # notas subindo até ele
            k = (t * 0.7 + i / 6) % 1.0
            x = OUT_W * (0.2 + rng.random() * 0.6)
            y = OUT_H * (0.95 - 0.7 * k)
            dr.rectangle((x - 30, y - 16, x + 30, y + 16), fill=(110, 190, 140), outline=(40, 100, 60), width=3)
        return f

    def p_cadeirinha(self, t, d):
        m = self.bairro.copy()
        for i, pers in enumerate(self.povo[:3]):
            x = (t * 360 + i * 380) % 1500 - 200
            m.alpha_composite(self.cad.resize((300, 300)), (int(x - 150), 1500))
            pers(m, t, x + 10, 1660, 0.6, expr="feliz")
        f = self.cam(m, 540, 1250, 1.1)
        texto_pop(f, "R$ 5 / QUARTEIRÃO", self.fc, t, OUT_W / 2, OUT_H * 0.12, 60, (255, 214, 40))
        return f

    def p_parados(self, t, d):
        m = self.praca.copy()
        for i, (pers, x, y) in enumerate(zip(self.povo, (160, 380, 620, 840, 500), (1700, 1760, 1720, 1680, 1880))):
            spr = pers.spr(["surpreso", "neutro", "triste", "surpreso", "neutro"][i], "anda1" if i % 2 else "anda2")
            g.colar(m, cinza(spr), x, y, 0.85)
        # pombos pousando na cabeça
        p = Pincel(140, 100)
        p.elipse((20, 30, 120, 90), (170, 170, 180))
        p.elipse((80, 10, 130, 60), (170, 170, 180))
        pombo = p.pronto()
        m.alpha_composite(pombo, (330, int(1760 - 0.85 * 640 - 50 + 6 * math.sin(t * 3))))
        f = self.cam(m, 540, 1250, 1.1 + 0.08 * ease_io(t / d))
        texto_pop(f, "OS PARADOS", self.fc, t, OUT_W / 2, OUT_H * 0.12, 80, (200, 200, 210))
        return f

    def casa(self):
        m = gradiente(WW, WH, (245, 225, 195), (230, 205, 170))
        p = Pincel(WW, WH)
        p.ret((640, 260, 960, 620), (170, 215, 240), r=10, ow=10)
        p.ret((-20, 1450, WW + 20, WH + 20), (180, 140, 110), r=0)
        p.ret((140, 1300, 560, 1460), (120, 90, 140), r=30)              # poltrona
        p.ret((140, 1120, 230, 1460), (120, 90, 140), r=30)
        m.alpha_composite(p.pronto())
        return m

    def p_casa(self, t, d):
        m = self.casa()
        self.bento(m, t, 360, 1520, 1.2, expr="feliz")
        m.alpha_composite(self.beng.resize((80, 320)), (520, 1130))
        self.teo(m, t, 760, 1780, 1.05, expr="ri" if int(t * 2) % 2 else "feliz")
        f = self.cam(m, 540, 1250, 1.1)
        if self.T > 41.98:
            texto_pop(f, "VÔ BENTO", self.fc, self.T - 41.98, OUT_W * 0.33, OUT_H * 0.14, 60, (255, 214, 40))
        return f

    def p_guarda(self, t, d):
        m = self.casa()
        self.bento(m, t, 360, 1520, 1.2, expr="neutro")
        f = self.cam(m, 400, 1150, 1.4)
        self.pulso(f, 0, t)
        texto_pop(f, "GUARDANDO…", self.fc, t, OUT_W / 2, OUT_H * 0.3, 60, (255, 255, 255))
        return f

    def p_caminho(self, t, d):
        off = (t * 240) % WW
        m = Image.new("RGBA", (WW, WH))
        m.alpha_composite(self.bairro, (int(-off), 0))
        m.alpha_composite(self.bairro, (int(WW - off), 0))
        self.anda(self.bento, m, t, 540, 1780, 1.15, rate=2.0, expr="feliz")
        m.alpha_composite(self.beng.resize((70, 280)).rotate(-8, expand=True), (640, 1500))
        f = self.cam(m, 540, 1250, 1.1)
        n = self.contagem(self.T, 47.82, 1, 98 / (53.56 - 47.82 - 0.4), 98)
        self.pulso(f, n, t)
        if n >= 98:
            texto_pop(f, "98 PASSOS", self.fc, self.T - 52.9, OUT_W / 2, OUT_H * 0.3, 80,
                      (90, 220, 120))
        return f

    def p_chuva(self, t, d):
        m = self.muro.copy()
        k = ease_io(min(1, t / (d * 0.9)))
        # cartaz revelado de cima pra baixo (a tinta escorre)
        cart = self.cartaz.resize((560, 756))
        h = int(756 * k)
        if h > 0:
            m.alpha_composite(cart.crop((0, 0, 560, h)), (260, 420))
        p = Pincel(WW, WH)
        p.ret((260, 420 + h, 820, 1176), (205, 195, 185), r=0, ow=0)
        for x in range(270, 820, 40):                         # escorrido de tinta
            p.ret((x, 420 + h - 10, x + 20, 420 + h + 40 + 30 * math.sin(x)), (205, 195, 185), r=8, ow=0)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 900, 1.1)
        vco.gotas(f, t, 90)
        return f

    def p_cartaz(self, t, d):
        m = gradiente(WW, WH, (110, 120, 140), (90, 100, 120))
        self.segura(m, self.cartaz, 540, 950, 760)
        f = self.cam(m, 540, 950, 1.05 + 0.25 * ease_io(t / d))
        vco.gotas(f, t, 40)
        return f

    def p_corredor(self, t, d):
        off = (t * 1400) % WW
        m = Image.new("RGBA", (WW, WH))
        m.alpha_composite(self.bairro, (int(-off), 0))
        m.alpha_composite(self.bairro, (int(WW - off), 0))
        self.anda(self.bentoj, m, t, 540, 1780, 1.3, rate=6, expr="ri", rot=-8)
        f = self.cam(m, 540, 1250, 1.15)
        dr = ImageDraw.Draw(f)
        rng = random.Random(int(t * 10))
        for _ in range(10):
            y, x = rng.uniform(200, 1100), rng.uniform(0, OUT_W)
            dr.line((x, y, x + rng.uniform(80, 220), y), fill=(255, 255, 255), width=5)
        texto_pop(f, "CORREDOR!", self.fc, t, OUT_W / 2, OUT_H * 0.12, 90, (255, 214, 40))
        return f

    def p_caio(self, t, d):
        m = self.escola.copy()
        for i, (pers, x) in enumerate(zip(self.povo[3:], (180, 900))):
            pers(m, t + i, x, 1760, 0.8, expr="triste")
        self.caio(m, t, 540, 1800, 1.15, expr="ri" if int(t * 3) % 2 else "feliz", pose="acena")
        f = self.cam(m, 540, 1250, 1.12)
        self.pulso(f, 999, t, "dourada")
        if self.T > 71.96:
            texto_pop(f, "INFINITA", self.fc, self.T - 71.96, OUT_W / 2, OUT_H * 0.3, 80, DOURADO)
        return f

    def p_caio_anda(self, t, d):
        m = self.escola.copy()
        ang = t * 2.4
        x = 540 + 300 * math.cos(ang)
        e = 1.05 + 0.12 * math.sin(ang)
        self.anda(self.caio, m, t, x, 1760 + 60 * math.sin(ang), e, rate=4, expr="ri", fala=self.FALA_CAIO)
        f = self.cam(m, 540, 1250, 1.1)
        n = self.contagem(self.T, 72.66, 500, 40)
        self.pulso(f, n, t, "dourada")
        return f

    def p_provoca(self, t, d):
        m = self.escola.copy()
        self.bento(m, t, 540, 1780, 1.15, expr="neutro")
        m.alpha_composite(self.beng.resize((80, 320)), (660, 1470))
        ang = t * 2.0
        x = 540 + 330 * math.cos(ang)
        frente = math.sin(ang) > 0
        if not frente:
            self.anda(self.caio, m, t, x, 1700, 0.9, rate=4, expr="ri", fala=self.FALA_CAIO)
            self.bento(m, t, 540, 1780, 1.15, expr="neutro")
        else:
            self.anda(self.caio, m, t, x, 1860, 1.1, rate=4, expr="ri", fala=self.FALA_CAIO)
        return self.cam(m, 540, 1250, 1.12)

    def p_bengala(self, t, d):
        m = self.escola.copy()
        self.bento(m, t, 420, 1780, 1.15, expr="surpreso" if t > 0.15 else "neutro")
        self.caio(m, t, 760, 1800, 1.1, expr="bravo", pose="bate2" if t < 0.3 else "idle")
        k = ease_out(min(1, max(0, t - 0.1) / 0.8))
        self.segura(m, self.beng, 600 + 300 * k, 1500 - 400 * math.sin(k * math.pi) + 250 * k, 300, rot=k * 540)
        return self.cam(m, 560, 1250, 1.12)

    def p_respira(self, t, d):
        m = self.fundo_blur("escola", self.escola)
        respira = 1 + 0.04 * math.sin(t * 3)
        self.bento(m, t, 540, 2350, 2.5 * respira, expr="neutro")
        return self.cam(m, 540, 950, 1.05)

    def p_pega(self, t, d):
        m = self.escola.copy()
        self.bento(m, t, 380, 1780, 1.15, expr="feliz" if t > 1.2 else "neutro")
        k = ease_out(min(1, t / 0.8))
        self.teo(m, t, 760, 1800, 1.05, expr="neutro", pose="entrega")
        hx, hy = self.mao(760, 1800, 1.05, t)
        self.segura(m, self.beng, hx + 20, hy - 60 + 200 * (1 - k), 260, rot=20 * (1 - k))
        return self.cam(m, 560, 1250, 1.12)

    def p_noite(self, t, d):
        m = self.quarto.copy()
        self.bento(m, t, 360, 1500, 1.0, expr="feliz")
        self.teo(m, t, 720, 1520, 0.9, expr="neutro", fala=self.FALA_TEO)
        f = self.cam(m, 540, 1150, 1.15)
        particulas(f, t, 20, (255, 255, 230), semente=4)
        return f

    def p_vo_sorri(self, t, d):
        m = self.fundo_blur("quarto", self.quarto)
        m.alpha_composite(brilho((1000, 1000), (255, 220, 160), 500, 0.6), (40, 300))
        self.bento(m, t, 540, 2350, 2.5, expr="feliz", fala=self.FALA_BENTO)
        f = self.cam(m, 540, 950, 1.05 + 0.1 * ease_io(t / d))
        # lembrança da corrida no canto, em sépia
        if t > 1.0:
            mini = Image.new("RGBA", (WW, WH))
            mini.alpha_composite(self.bairro)
            self.anda(self.bentoj, mini, t, 540, 1780, 1.3, rate=6, expr="ri", rot=-8)
            th = vc.gradear(camera(mini, 540, 1250, 1.2), "sepia").resize((260, 462))
            msk = Image.new("L", th.size, 0)
            ImageDraw.Draw(msk).ellipse((0, 0, th.width, th.height), fill=255)
            f.paste(th, (OUT_W - 300, 60), msk)
        return f

    def p_passa_mal(self, t, d):
        m = self.praca.copy()
        k = ease_out(min(1, t / 0.8))
        self.bento(m, t, 300, 1700 + 120 * k, 1.1, expr="triste", rot=-70 * k)
        self.teo(m, t, 560, 1780, 1.0, expr="surpreso", pose="acena")
        f = self.cam(m, 540, 1250, 1.1)
        if self.T > 98.52:
            dr = ImageDraw.Draw(f)
            for i in range(10):
                x = OUT_W * (0.3 + i * 0.05)
                y = OUT_H * 0.78 - 8 * math.sin(t * 4 + i)
                dr.ellipse((x - 10, y - 14, x + 10, y + 14), fill=(255, 255, 255), outline=OUTLINE, width=3)
            texto_pop(f, "10 PASSOS", self.fc, self.T - 98.52, OUT_W / 2, OUT_H * 0.12, 90, (255, 214, 40))
        return f

    def p_97(self, t, d):
        m = gradiente(WW, WH, (80, 30, 35), (40, 15, 20))
        k = 0.5 + 0.5 * math.sin(t * 8)
        m.alpha_composite(brilho((900, 900), (255, 80, 60), 450, 0.5 * k), (90, 500))
        self.segura(m, pulseira(self.fc, 97, "normal"), 540, 1000, 800)
        f = self.cam(m, 540, 1000, 1.05 + 0.15 * ease_io(t / d))
        texto_pop(f, "SÓ FALTAM 3", self.fc, t, OUT_W / 2, OUT_H * 0.2, 80, (255, 120, 100))
        return f

    def p_bloqueia(self, t, d):
        m = self.praca.copy()
        self.bento(m, t, 840, 1820, 1.0, expr="triste", rot=-70)
        self.caio(m, t, 540, 1800, 1.25, expr="ri", pose="aponta", fala=self.FALA_CAIO)
        f = self.cam(m, 540, 1250, 1.15)
        self.pulso(f, 999, t, "dourada", x=0.8, y=0.05, w=200)
        self.pulso(f, 97, t, "normal", x=0.2, y=0.05, w=200)
        return f

    def p_olha(self, t, d):
        m = self.fundo_blur("praca", self.praca)
        self.teo(m, t, 540, 2350, 2.5, expr="triste" if t < 1.0 else "bravo")
        return self.cam(m, 540, 950, 1.05 + 0.15 * ease_out(t / d))

    def p_contagem(self, t, d):
        T = self.T
        marcos = [(111.68, 98), (112.94, 99), (114.06, 100)]
        n = 97
        tm = 111.68
        for ts, v in marcos:
            if T >= ts:
                n, tm = v, ts
        m = gradiente(WW, WH, (40, 40, 55), (20, 20, 30))
        verm = T >= 114.78
        if verm:
            k = 0.5 + 0.5 * math.sin(t * 10)
            m.alpha_composite(brilho((1000, 1000), (255, 60, 50), 500, 0.6 * k), (40, 500))
        self.anda(self.teo, m, (T - 111.68) * 0.6, 540, 1900, 1.5, rate=1.5, expr="bravo")
        f = self.cam(m, 540, 1200, 1.1)
        self.pulso(f, n, t, "vermelha" if verm else "normal", y=0.06, w=380)
        texto_pop(f, str(n), self.fc, T - tm, OUT_W / 2, OUT_H * 0.36, 200, (255, 80, 70) if verm else (255, 255, 255))
        return f

    def p_cento_um(self, t, d):
        m = gradiente(WW, WH, (20, 10, 12), (5, 5, 8))
        f = self.cam(m, 540, 1000, 1.0)
        texto_pop(f, "101", self.fc, t, OUT_W / 2, OUT_H * 0.42, int(280 + 30 * t), (255, 60, 50))
        self.pulso(f, 101, t, "vermelha", y=0.62, w=360)
        return f

    def p_nada(self, t, d):
        m = self.praca.copy()
        self.teo(m, t, 540, 1800, 1.3, expr="surpreso" if t < 0.8 else "neutro", pose="anda1")
        f = self.cam(m, 540, 1300, 1.25)
        self.pulso(f, 101, t, "normal")
        texto_pop(f, "…", self.fc, t, OUT_W / 2, OUT_H * 0.3, 140, (255, 255, 255))
        return f

    def p_corre(self, t, d):
        off = (t * 1300) % WW
        m = Image.new("RGBA", (WW, WH))
        m.alpha_composite(self.praca, (int(-off), 0))
        m.alpha_composite(self.praca, (int(WW - off), 0))
        self.anda(self.teo, m, t, 540, 1780, 1.2, rate=6, expr="bravo", rot=-10)
        f = self.cam(m, 540, 1250, 1.15)
        dr = ImageDraw.Draw(f)
        rng = random.Random(int(t * 10))
        for _ in range(10):
            y, x = rng.uniform(200, 1100), rng.uniform(0, OUT_W)
            dr.line((x, y, x + rng.uniform(80, 220), y), fill=(255, 255, 255), width=5)
        n = 101 + (1 if self.T >= 119.08 else 0) + (1 if self.T >= 120.08 else 0) + max(0, int((self.T - 121.0) * 4))
        self.pulso(f, n, t, "verde")
        return f

    def p_silencio(self, t, d):
        m = self.praca.copy()
        for i, (pers, x) in enumerate(zip(self.povo, (150, 340, 540, 740, 930))):
            pers(m, t, x, 1760, 0.85, expr="surpreso")
        return self.cam(m, 540, 1250, 1.05 + 0.06 * ease_io(t / d))

    def p_todos(self, t, d):
        m = self.praca_t.copy()
        for i, (pers, x) in enumerate(zip(self.povo, (150, 340, 540, 740, 930))):
            deu = t > i * 0.35
            pers(m, t, x, 1760 - (30 if deu and t - i * 0.35 < 0.3 else 0), 0.85, expr="ri" if deu else "neutro",
                 pose="acena" if deu else "idle")
        f = self.cam(m, 540, 1250, 1.1)
        vm.confete(f, t, 70)
        texto_pop(f, "101!", self.fc, t, OUT_W / 2, OUT_H * 0.12, 120, (90, 220, 120))
        return f

    def p_parados_fogem(self, t, d):
        m = self.praca.copy()
        for i, (pers, x0) in enumerate(zip(self.povo[:4], (160, 380, 620, 840))):
            k = ease_io(min(1, max(0, t - 0.3 - i * 0.2) / 2.0))
            x = x0 + (1300 if i % 2 else -1300) * k
            self.anda(pers, m, t, x, 1760, 0.85, rate=5, expr="surpreso")
        if t > 2.6:
            kk = ease_out(min(1, (t - 2.6) / 0.5))
            self.segura(m, self.carta, 540, 1400 + 300 * kk, 200, rot=200 * kk)
        f = self.cam(m, 540, 1250, 1.1)
        texto_pop(f, "PSIU…", self.fc, t, OUT_W * 0.7, OUT_H * 0.18, 70, (200, 200, 210))
        return f

    def p_envelope(self, t, d):
        m = gradiente(WW, WH, (210, 195, 170), (190, 175, 150))
        self.segura(m, self.env_pag, 540, 950, 760, rot=-3)
        return self.cam(m, 540, 950, 1.05 + 0.15 * ease_io(t / d))

    def p_vo_fala(self, t, d):
        m = self.praca.copy()
        m.alpha_composite(self.mac, (100, 1500))
        k = ease_out(min(1, t / 1.0))
        self.bento(m, t, 420, 1620 - 40 * k, 1.15, expr="bravo" if t > 2.5 else "neutro", pose="aponta" if t > 2.5 else "idle",
                   fala=self.FALA_BENTO)
        self.teo(m, t, 840, 1820, 1.0, expr="feliz")
        f = self.cam(m, 540, 1250, 1.12)
        if self.T > 140.74:
            texto_pop(f, "INVENTOU A CONTA!", self.fc, self.T - 140.74, OUT_W / 2, OUT_H * 0.12, 64, (230, 60, 60))
        return f

    def p_caio_corre(self, t, d):
        off = (t * 600) % WW
        m = Image.new("RGBA", (WW, WH))
        m.alpha_composite(self.bairro, (int(-off), 0))
        m.alpha_composite(self.bairro, (int(WW - off), 0))
        cansa = min(1, t / d)
        self.anda(self.caio, m, t, 540, 1780, 1.15, rate=5 - 2 * cansa, expr="surpreso" if cansa < 0.6 else "triste",
                  rot=-6)
        f = self.cam(m, 540, 1250, 1.12)
        n = self.contagem(self.T, 143.04, 60, 40 / (147.22 - 143.04), 100)
        self.pulso(f, n, t, "dourada")
        return f

    def p_caio_cai(self, t, d):
        m = self.bairro.copy()
        p = Pincel(WW, WH)
        p.ret((-20, 1480, WW + 20, 1530), (170, 165, 160), r=0)
        m.alpha_composite(p.pronto())
        resp = 1 + 0.06 * math.sin(t * 14)
        self.caio(m, t, 540, 1720, 1.25 * resp, expr="chora" if t > 1.2 else "triste")
        f = self.cam(m, 540, 1250, 1.2)
        dr = ImageDraw.Draw(f)
        for i in range(4):                                  # gotas de suor
            y = OUT_H * 0.32 + ((t * 160 + i * 50) % 140)
            dr.ellipse((OUT_W * 0.36 + i * 40, y, OUT_W * 0.36 + i * 40 + 16, y + 26), fill=(140, 200, 255))
        texto_pop(f, "SEM AR", self.fc, t, OUT_W / 2, OUT_H * 0.12, 90, (255, 255, 255))
        return f

    def p_vida_cadeirinha(self, t, d):
        m = self.bairro.copy()
        x = -200 + (t / d) * 1400
        m.alpha_composite(self.cad, (int(x - 210), 1400))
        self.caio(m, t, x + 20, 1560, 0.85, expr="ri")
        f = self.cam(m, 540, 1250, 1.1)
        texto_pop(f, "A VIDA INTEIRA", self.fc, t, OUT_W / 2, OUT_H * 0.12, 70, (255, 255, 255))
        return f

    def p_unico(self, t, d):
        m = self.fundo_blur("bairro", self.bairro)
        self.caio(m, t, 540, 2350, 2.5, expr="triste")
        f = self.cam(m, 540, 950, 1.05 + 0.1 * ease_io(t / d))
        self.pulso(f, 999, t, "dourada", y=0.06, w=320)
        return f

    def p_licao(self, t, d):
        m = self.praca_t.copy()
        f = self.cam(m, 540, 900, 1.1 + 0.05 * ease_io(t / d))
        f = ImageEnhance.Brightness(f).enhance(0.6)
        if t > 0.1:
            texto_pop(f, "QUEM VENDE O SEU LIMITE", self.fc, t - 0.1, OUT_W / 2, OUT_H * 0.36, 54, (255, 255, 255))
        if t > 1.6:
            texto_pop(f, "TEM MEDO DE ATÉ ONDE", self.fc, t - 1.6, OUT_W / 2, OUT_H * 0.43, 54, (255, 214, 40))
            texto_pop(f, "VOCÊ PODE CHEGAR", self.fc, t - 1.6, OUT_W / 2, OUT_H * 0.49, 54, (255, 214, 40))
        return f

    def p_domingo(self, t, d):
        off = (t * 300) % WW
        m = Image.new("RGBA", (WW, WH))
        m.alpha_composite(self.bairro_t, (int(-off), 0))
        m.alpha_composite(self.bairro_t, (int(WW - off), 0))
        self.anda(self.bento, m, t, 420, 1780, 1.15, rate=2.4, expr="ri")
        self.anda(self.teo, m, t + 0.2, 720, 1800, 1.0, rate=2.4, expr="ri")
        f = self.cam(m, 540, 1250, 1.1)
        n = self.contagem(self.T, 162.16, 120, 60)
        self.pulso(f, n, t, "verde")
        particulas(f, t, 30, (255, 230, 160), semente=21)
        return f

    def p_ponte(self, t, d):
        m = self.ponte.copy()
        self.bento(m, t, 420, 1330, 0.8, expr="feliz")
        self.teo(m, t, 640, 1340, 0.7, expr="surpreso" if t > 2.8 else "feliz", pose="aponta" if t > 2.8 else "idle")
        f = self.cam(m, 540, 1100 - 150 * ease_io(t / d), 1.15 - 0.1 * ease_io(t / d))
        if t > d - 0.8:
            f = ImageEnhance.Brightness(f).enhance(1 - ease_io((t - (d - 0.8)) / 0.8))
        return f

    # ---------- montagem ----------
    def frame(self, n):
        t = n / FPS
        self.T = t
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
                if fn not in (self.p_cento_um, self.p_licao):
                    self.legenda(f, t)
                return f

    def eventos_sfx(self):
        ev = []
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if i and tr in ("whip", "zoom"):
                ev.append(("whoosh", ini - 0.08))
            elif i and tr == "corte" and fn not in (self.p_cento_um, self.p_nada):
                ev.append(("pop", ini))
        return ev


# --------------------------------------------------------------------------
# Áudio: passos sincronizados, batida de coração na contagem, silêncio no 101
# --------------------------------------------------------------------------
def passo_sfx():
    SR = g.SR
    t = np.arange(int(SR * 0.12)) / SR
    rng = np.random.default_rng(3)
    return (np.sin(2 * np.pi * 110 * t) * np.exp(-t * 45) * 0.5
            + rng.standard_normal(len(t)) * np.exp(-t * 80) * 0.12)


def mixar(filme, narracao, saida):
    SR = g.SR
    voz = vc.ler_wav_mono(narracao)
    n = int(filme.dur_total * SR)
    mix = np.zeros(n, np.float32)
    mix[:min(n, len(voz))] += voz[:n]
    mus = g.trilha(filme.dur_total)
    mus = mus / max(1e-6, np.abs(mus).max()) * 0.13
    tt = np.arange(len(mus)) / SR
    env = np.ones_like(tt)
    env[(tt > 111.3) & (tt < 119.0)] = 0.0                # silêncio na contagem / 101
    env[(tt > 158.0) & (tt < 162.1)] *= 0.5
    mix[:len(mus)] += (mus * env)[:n]
    ev = filme.eventos_sfx()
    # passos (cadência de cada cena de caminhada)
    janelas = [(0.0, 3.5, 2.4), (3.54, 4.14, 2.4), (8.22, 11.2, 3.0), (47.82, 53.4, 2.0), (63.86, 65.5, 6.0),
               (72.66, 75.8, 4.0), (75.86, 82.3, 4.0), (119.08, 122.9, 6.0), (143.04, 147.2, 4.0),
               (162.16, 167.8, 2.4)]
    for a, b, r in janelas:
        t = a
        while t < b:
            ev.append(("passo", t))
            t += 1 / r
    ev += [("passo", x) for x in (111.68, 112.94, 114.06, 116.56)]
    ev += [("batida", 110.9 + k * 0.85) for k in range(8)]
    ev += [("gelo_", 4.14), ("brilho", 125.12), ("brilho", 59.20), ("toc", 82.52)]
    from video_sono import sfx as sfx_sono
    for tipo, t0 in ev:
        if tipo == "passo":
            s = passo_sfx()
        elif tipo == "batida":
            s = sfx_sono("batida") * 0.7
        elif tipo == "gelo_":
            s = ve.sfx_gelo() * 0.6
        else:
            s = g.sfx(tipo) * (0.3 if tipo in ("whoosh", "pop") else 1.0)
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
    out = []
    i = 0
    while i < len(pal):
        w = pal[i]
        nxt = pal[i + 1]["w"] if i + 1 < len(pal) else ""
        if w["w"] == "Na" and nxt == "moro":
            out.append(dict(w="Namoro", s=w["s"], e=pal[i + 1]["e"]))
            i += 2
            continue
        if w["w"] == "Vô" and nxt == "Vô.":
            out.append(dict(w="vovô.", s=w["s"], e=pal[i + 1]["e"]))
            i += 2
            continue
        if w["w"] == "meio" and nxt == "fio.":
            out.append(dict(w="meio-fio.", s=w["s"], e=pal[i + 1]["e"]))
            i += 2
            continue
        txt = {"trava": "travam", "Infimita.": "Infinita.", "Há": "A", "tél": "Téo"}.get(w["w"], w["w"])
        if w["w"] == "100" and round(w["s"], 2) == 148.08:
            txt = "Sem"
        out.append(dict(w=txt, s=w["s"], e=w["e"]))
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_cem_passos.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmePassos(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.2, a.narracao)
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

    tmp = tempfile.mkdtemp(prefix="passos_")
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
