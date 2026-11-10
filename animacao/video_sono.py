#!/usr/bin/env python3
"""
"O Aplicativo do Sono" — suspense narrado em 2ª pessoa (estilo vídeos de mistério).

Diferenças em relação aos vídeos emocionais:
  * paleta escura/azulada, cortes mais rápidos (~1,5 s)
  * muitos closes de tela de celular, bilhetes e objetos-pista
  * "câmera noturna" (verde, ruído, REC, timestamp)
  * trilha de tensão (drone grave + batida de coração) no lugar do piano

Uso:
    python3 animacao/video_sono.py --narracao narr.wav --transcricao transcricao.json --fonte Poppins.ttf
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
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, Ator, gradiente, brilho,
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(33)

VOCE = dict(pele=(214, 165, 125), cabelo=(40, 32, 30), camisa=(60, 85, 110), calca=(45, 50, 65),
            sapato=(235, 235, 240), tipo="pai", bigode=False)
VOCE_SUJO = dict(VOCE, sapato=(110, 80, 50))

CORRECOES = {"rir": "ri", "18": "dezoito", "As": "Às", "Coloca": "Coloca a"}
TROCA_POR_TEMPO = {17.42: "às"}
vc.DESTAQUE_VERMELHO = {"regra.", "nunca", "lama.", "sexta.", "sorri.", "Pronto.", "acordar.", "estranhas."}

ROXO = (110, 70, 200)


# --------------------------------------------------------------------------
# Objetos
# --------------------------------------------------------------------------
def fnt(fc, tam):
    return vc.fonte(fc, tam)


def celular(fc, titulo, linhas, destaque=None, botao=None, cor=ROXO, w=620):
    """Tela de app. linhas: lista de (texto, tamanho, cor)."""
    h = int(w * 1.9)
    p = Pincel(w, h)
    p.ret((10, 10, w - 10, h - 10), (25, 25, 32), r=70, ow=8)
    p.ret((40, 40, w - 40, h - 40), (245, 244, 250), r=50, ow=0)
    p.ret((40, 40, w - 40, 260), cor, r=50, ow=0)
    p.ret((40, 180, w - 40, 260), cor, r=0, ow=0)
    p.ret((w / 2 - 60, 58, w / 2 + 60, 78), (25, 25, 32), r=10, ow=0)
    if botao:
        p.ret((90, h - 260, w - 90, h - 150), (60, 190, 120), r=40, ow=0)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = fnt(fc, 46)
    d.text((80, 150), titulo, font=f, fill=(255, 255, 255))
    y = 320
    for txt, tam, c in linhas:
        ff = fnt(fc, tam)
        d.text((80, y), txt, font=ff, fill=c)
        y += tam + 34
    if botao:
        fb = fnt(fc, 50)
        d.text((w / 2 - fb.getlength(botao) / 2, h - 236), botao, font=fb, fill=(255, 255, 255))
    return img


def foto(cena, w=420, h=420):
    """Moldura de foto da galeria contendo uma mini-cena desenhada."""
    p = Pincel(w, h)
    cena(p, w, h)
    return p.pronto()


def c_rua(p, w, h):
    p.ret((0, 0, w, h), (30, 35, 60), r=0, ow=0)
    for i, x in enumerate(range(-20, w, 110)):
        p.ret((x, h * 0.35 + (i % 2) * 30, x + 100, h * 0.8), (55, 60, 90), r=4, ow=4)
        p.ret((x + 30, h * 0.45 + (i % 2) * 30, x + 60, h * 0.55 + (i % 2) * 30), (230, 200, 120), r=3, ow=0)
    p.ret((0, h * 0.8, w, h), (45, 45, 55), r=0, ow=0)
    p.elipse((w * 0.75, 40, w * 0.9, 100), (240, 235, 210), ow=0)


def c_porta(p, w, h):
    p.ret((0, 0, w, h), (70, 70, 85), r=0, ow=0)
    p.ret((w * 0.25, h * 0.15, w * 0.75, h), (40, 90, 190), r=10, ow=6)
    p.elipse((w * 0.64, h * 0.55, w * 0.7, h * 0.61), (230, 200, 80), ow=4)
    p.ret((w * 0.4, h * 0.22, w * 0.6, h * 0.34), (240, 240, 240), r=6, ow=4)


def c_47(p, w, h):
    p.ret((0, 0, w, h), (40, 90, 190), r=0, ow=0)
    p.ret((w * 0.15, h * 0.25, w * 0.85, h * 0.75), (240, 240, 240), r=16, ow=8)


def tenis(sujo=True):
    p = Pincel(700, 360)
    for k, x in enumerate((40, 340)):
        cor = (235, 235, 240)
        p.poli([(x, 300), (x, 180), (x + 80, 120), (x + 200, 130), (x + 300, 250), (x + 310, 300)], cor)
        p.ret((x - 6, 290, x + 316, 330), (200, 200, 205), r=14)
        for j in range(3):
            p.linha([(x + 110 + j * 30, 150 + j * 18), (x + 160 + j * 30, 145 + j * 18)], w=6)
        if sujo:
            rng = random.Random(k)
            for _ in range(14):
                cx, cy = x + rng.uniform(10, 300), rng.uniform(220, 325)
                r = rng.uniform(12, 30)
                p.elipse((cx - r, cy - r * 0.6, cx + r, cy + r * 0.6), (110, 80, 50), ow=0)
    return p.pronto()


def pulseira(brilho_azul=True, w=520):
    p = Pincel(w, 300)
    p.ret((20, 90, w - 20, 210), (40, 40, 55), r=60)
    p.ret((w / 2 - 90, 70, w / 2 + 90, 230), (25, 25, 35), r=40)
    p.ret((w / 2 - 70, 95, w / 2 + 70, 205), (80, 160, 255) if brilho_azul else (60, 60, 80), r=30, ow=0)
    return p.pronto()


def chave():
    p = Pincel(500, 220)
    p.elipse((20, 40, 170, 190), (200, 170, 80))
    p.elipse((65, 85, 125, 145), (30, 30, 40), ow=0)
    p.ret((160, 95, 460, 135), (200, 170, 80), r=8)
    for x in (360, 410):
        p.ret((x, 130, x + 30, 185), (200, 170, 80), r=4)
    return p.pronto()


def mao_cortada():
    p = Pincel(600, 700)
    pele = VOCE["pele"]
    p.ret((150, 300, 450, 700), pele, r=80)
    for i, x in enumerate((150, 225, 300, 375)):
        p.capsula((x + 37, 320), (x + 37 - (i - 1.5) * 10, 90 + abs(i - 1.5) * 30), 64, pele)
    p.capsula((450, 450), (560, 330), 66, pele)
    p.linha([(200, 470), (330, 400), (420, 430)], fill=(200, 40, 50), w=14)
    return p.pronto()


def espelho(fc, texto_vis):
    p = Pincel(WW, WH)
    p.ret((-20, -20, WW + 20, WH + 20), (60, 75, 90), r=0, ow=0)
    for y in range(0, WH, 140):           # azulejos
        for x in range(0, WW, 140):
            p.ret((x + 4, y + 4, x + 136, y + 136), (70, 88, 105), r=6, ow=0)
    p.ret((170, 260, 910, 1250), (150, 175, 190), r=30, ow=16)
    p.ret((120, 1330, 960, 1450), (220, 225, 230), r=20)
    p.ret((470, 1260, 610, 1340), (190, 190, 200), r=10)
    img = p.pronto()
    if texto_vis:
        d = ImageDraw.Draw(img)
        f = fnt(fc, 70)
        for i, l in enumerate(["Não venda", "a noite", "de sexta."][:texto_vis]):
            d.text((260, 520 + i * 120), l, font=f, fill=(180, 30, 40))
    return img


def calendario_semana(fc, marcados):
    p = Pincel(WW, 900)
    p.ret((60, 60, WW - 60, 860), (245, 245, 245), r=24)
    p.ret((60, 60, WW - 60, 210), (60, 60, 80), r=24)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    dias = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
    f = fnt(fc, 44)
    d.text((WW / 2 - f.getlength("NOITES VENDIDAS") / 2, 110), "NOITES VENDIDAS", font=f, fill=(255, 255, 255))
    for i, dd in enumerate(dias):
        x = 100 + i * 128
        d.text((x, 300), dd, font=fnt(fc, 36), fill=(60, 60, 80))
        if i < marcados:
            d.line((x - 5, 380, x + 80, 470), fill=(60, 160, 100), width=14)
            d.line((x + 80, 380, x - 5, 470), fill=(60, 160, 100), width=14)
        if dd == "SEX" and marcados >= 5:
            d.ellipse((x - 30, 270, x + 110, 520), outline=(210, 40, 40), width=10)
    return img


def lista_nomes(fc, destaque):
    w, h = 820, 1100
    p = Pincel(w, h)
    p.ret((10, 10, w - 10, h - 10), (240, 236, 222), r=10)
    p.ret((300, -10, 520, 60), (120, 120, 130), r=10)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    nomes = ["Carlos M.", "Ana P.", "Rafael S.", "Júlia T.", "Bruno A.", "Lia F.", "Diego R.",
             "Marta C.", "Igor B.", "VOCÊ"]
    f = fnt(fc, 46)
    for i, n in enumerate(nomes):
        y = 110 + i * 92
        ult = n == "VOCÊ"
        d.text((70, y), n, font=f, fill=(170, 30, 40) if ult else (50, 50, 60))
        d.text((480, y), "PRONTO" if (ult and destaque) else ("PRONTO" if not ult else "........"),
               font=f, fill=(170, 30, 40) if ult else (90, 90, 100))
        d.line((70, y + 70, w - 70, y + 70), fill=(200, 195, 185), width=3)
    return img


def parede_pulseiras(t):
    m = gradiente(WW, WH, (15, 15, 25), (8, 8, 15))
    p = Pincel(WW, WH)
    for lin in range(16):
        for col in range(6):
            x, y = 40 + col * 175, 60 + lin * 118
            p.ret((x, y + 20, x + 150, y + 70), (35, 35, 48), r=24, ow=4)
            on = (lin * 7 + col * 3 + int(t * 6)) % 9 != 0
            p.ret((x + 50, y + 25, x + 100, y + 65), (80, 160, 255) if on else (40, 60, 90), r=12, ow=0)
    m.alpha_composite(p.pronto())
    return m


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def quarto_noite():
    base = gradiente(WW, WH, (22, 26, 48), (35, 38, 62))
    p = Pincel(WW, WH)
    p.ret((640, 260, 960, 660), (18, 22, 45), r=10, ow=10)
    p.elipse((760, 330, 850, 420), (220, 225, 240), ow=0)
    p.linha([(800, 260), (800, 660)], w=10)
    p.ret((-20, 1450, WW + 20, WH + 20), (45, 42, 58), r=0)
    p.ret((60, 1150, 1020, 1500), (55, 70, 110), r=30)
    p.ret((60, 1040, 340, 1200), (180, 185, 200), r=30)
    p.ret((40, 1000, 90, 1650), (70, 55, 50), r=12)
    p.ret((990, 1100, 1040, 1650), (70, 55, 50), r=12)
    p.ret((880, 900, 1000, 1000), (40, 40, 50), r=10)        # criado-mudo + relógio
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((700, 700), (120, 140, 220), 350, 0.25), (450, 0))
    return base


def quarto_manha():
    base = gradiente(WW, WH, (215, 205, 190), (190, 180, 165))
    p = Pincel(WW, WH)
    p.ret((640, 260, 960, 660), (180, 215, 240), r=10, ow=10)
    p.linha([(800, 260), (800, 660)], w=10)
    p.ret((-20, 1450, WW + 20, WH + 20), (150, 120, 95), r=0)
    p.ret((60, 1150, 1020, 1500), (100, 120, 170), r=30)
    p.ret((60, 1040, 340, 1200), (240, 240, 245), r=30)
    p.ret((40, 1000, 90, 1650), (120, 85, 60), r=12)
    p.ret((990, 1100, 1040, 1650), (120, 85, 60), r=12)
    base.alpha_composite(p.pronto())
    return base


def cobertor(cor=(55, 70, 110)):
    p = Pincel(WW, 600)
    p.ret((80, 60, 1010, 420), cor, r=40)
    return p.pronto()


def rua_noite(fc, com_porta=False):
    base = gradiente(WW, WH, (15, 18, 38), (35, 35, 60))
    p = Pincel(WW, WH)
    for i, x in enumerate((-60, 250, 560, 870)):
        top = 600 + (i % 2) * 80
        p.ret((x, top, x + 290, 1420), (40 + i * 6, 45, 70), r=6)
        for jy in range(top + 60, 1300, 200):
            for jx in (x + 40, x + 170):
                acesa = (jx + jy) % 3 == 0
                p.ret((jx, jy, jx + 70, jy + 100), (220, 190, 110) if acesa else (25, 28, 45), r=6, ow=5)
    if com_porta:
        p.ret((400, 1000, 680, 1420), (40, 90, 190), r=12, ow=10)
        p.ret((480, 1060, 600, 1140), (240, 240, 240), r=8, ow=6)
        p.elipse((620, 1220, 650, 1250), (230, 200, 80), ow=5)
    p.ret((-20, 1410, WW + 20, 1500), (60, 60, 70), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (30, 30, 38), r=0)
    p.ret((80, 850, 100, 1420), (50, 50, 60), r=6)
    p.elipse((56, 810, 124, 878), (230, 220, 160))
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((600, 600), (230, 210, 140), 300, 0.4), (-210, 545))
    if com_porta:
        d = ImageDraw.Draw(base)
        f = fnt(fc, 64)
        d.text((540 - f.getlength("47") / 2, 1060), "47", font=f, fill=(30, 30, 40))
    return base


def sala_escura():
    base = gradiente(WW, WH, (12, 12, 20), (5, 5, 10))
    return base


# --------------------------------------------------------------------------
# Efeitos
# --------------------------------------------------------------------------
def noite(f, k=1.0):
    a = np.asarray(f, np.float32)
    a = a * (1 - 0.35 * k) * np.array([0.85, 0.92, 1.15]) ** k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def cam_noturna(f, fc, t, hora="03:00"):
    """Filtro de câmera de visão noturna: verde, ruído, linhas, REC, timestamp."""
    l = np.asarray(f.convert("L"), np.float32)
    l = np.clip(l * 1.3 + 15, 0, 255)
    rng = np.random.default_rng(int(t * 30))
    l = l + rng.normal(0, 14, l.shape)
    l[::4, :] *= 0.8
    rgb = np.stack([l * 0.35, l * 1.0, l * 0.45], -1)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    f1 = fnt(fc, 34)
    if int(t * 2) % 2 == 0:
        d.ellipse((40, 52, 70, 82), fill=(230, 40, 40))
    d.text((84, 46), "REC", font=f1, fill=(240, 240, 240))
    seg = int(t) % 60
    d.text((OUT_W - 210, 46), f"{hora}:{seg:02d}", font=f1, fill=(240, 240, 240))
    for (x0, y0, dx, dy) in ((30, 30, 1, 1), (OUT_W - 30, 30, -1, 1), (30, OUT_H - 30, 1, -1),
                             (OUT_W - 30, OUT_H - 30, -1, -1)):
        d.line((x0, y0, x0 + 60 * dx, y0), fill=(240, 240, 240), width=4)
        d.line((x0, y0, x0, y0 + 60 * dy), fill=(240, 240, 240), width=4)
    return img


def proj(wx, wy, cx, cy, z):
    """Converte coordenada do mundo em coordenada de tela para a câmera usada."""
    vw, vh = WW / z, WH / z
    x0 = min(max(cx - vw / 2, 0), WW - vw)
    y0 = min(max(cy - vh / 2, 0), WH - vh)
    return (wx - x0) / vw * OUT_W, (wy - y0) / vh * OUT_H, OUT_W / vw


def olhos_do(cx, by, e):
    """Posição (mundo) do centro dos olhos de um sprite colado em (cx, by) com escala e."""
    return cx, by - (640 - 193) * e, 46 * e


def olhos_brilhando(f, x, y, sep, r, k=1.0):
    gl = Image.new("RGBA", f.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(gl)
    for ex in (x - sep, x + sep):
        d.ellipse((ex - r * 2.2, y - r * 2.2, ex + r * 2.2, y + r * 2.2), fill=(255, 255, 255, int(90 * k)))
        d.ellipse((ex - r, y - r, ex + r, y + r), fill=(255, 255, 255, int(255 * k)))
    gl = gl.filter(ImageFilter.GaussianBlur(r * 0.4))
    base = f.convert("RGBA")
    base.alpha_composite(gl)
    return base.convert("RGB")


def glitch(f, t, forca=1.0):
    a = np.asarray(f).copy()
    rng = random.Random(int(t * 30))
    for _ in range(int(6 * forca)):
        y = rng.randint(0, OUT_H - 40)
        h = rng.randint(6, 40)
        s = rng.randint(-40, 40)
        a[y:y + h] = np.roll(a[y:y + h], s, axis=1)
    a[..., 0] = np.roll(a[..., 0], int(4 * forca), axis=1)
    return Image.fromarray(a)


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeSono(vc.Filme):
    def __init__(self, palavras, fc, dur_total):
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.voce, self.voce_sujo = Ator(VOCE), Ator(VOCE_SUJO)
        self.q_noite, self.q_manha = quarto_noite(), quarto_manha()
        self.cob_n, self.cob_m = cobertor(), cobertor((100, 120, 170))
        self.rua, self.rua_porta = rua_noite(fc), rua_noite(fc, True)
        self.tenis, self.pulseira, self.pulseira_off = tenis(), pulseira(), pulseira(False)
        self.chave, self.mao = chave(), mao_cortada()
        self.esp = [espelho(fc, k) for k in range(4)]
        self.f_rua, self.f_porta, self.f_47 = foto(c_rua), foto(c_porta), foto(c_47)
        d = ImageDraw.Draw(self.f_47)
        ff = fnt(fc, 150)
        d.text((210 - ff.getlength("47") / 2, 110), "47", font=ff, fill=(30, 30, 40))
        W = (255, 255, 255)
        cinza, verde, escuro = (120, 120, 135), (40, 160, 90), (40, 40, 55)
        self.app_oferta = celular(fc, "SONO+", [("Venda suas horas", 52, escuro), ("de sono.", 52, escuro),
                                               ("", 20, escuro), ("R$ 1.000", 110, verde), ("por hora", 48, cinza)])
        self.app_regra = celular(fc, "SONO+", [("Termos de uso", 50, escuro), ("1. Durma.", 44, cinza),
                                              ("2. Receba.", 44, cinza), ("3. NUNCA pergunte", 46, (190, 30, 40)),
                                              ("quem comprou.", 46, (190, 30, 40))])
        self.app_aceitar = celular(fc, "SONO+", [("Pronto pra", 52, escuro), ("começar?", 52, escuro)],
                                   botao="ACEITAR")
        self.app_saldo = celular(fc, "SONO+", [("Saldo", 46, cinza), ("R$ 8.000", 110, verde),
                                              ("+8 horas vendidas", 44, cinza)])
        self.app_passos = celular(fc, "SAÚDE", [("Passos hoje", 46, cinza), ("18.000", 130, (230, 110, 40)),
                                               ("entre 00h e 06h", 44, cinza)], cor=(230, 110, 40))
        self.app_vendido = celular(fc, "SONO+", [("Sexta-feira", 50, escuro), ("VENDIDA", 100, (190, 30, 40)),
                                                ("+R$ 8.000", 60, verde)])
        self.app_saldos = [celular(fc, "SONO+", [("Saldo", 46, cinza), (f"R$ {v}.000", 110, verde)])
                           for v in (16, 24, 32)]
        self.cal = [calendario_semana(fc, k) for k in range(6)]
        self.lista = lista_nomes(fc, False)
        self.lista_p = lista_nomes(fc, True)
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        P = [
            (0.00, self.p_app_oferta, "", "corte"),
            (1.90, self.p_dormindo_dinheiro, "noite", "whip"),
            (4.28, self.p_facil, "", "corte"),
            (6.88, self.p_app_regra, "", "corte"),
            (10.58, self.p_pensa, "", "corte"),
            (13.70, self.p_aceitar, "", "corte"),
            (14.80, self.p_pulseira, "noite", "corte"),
            (16.10, self.p_apaga, "noite", "corte"),
            (17.06, self.p_relogio, "", "corte"),
            (18.14, self.p_saldo, "", "whip"),
            (19.68, self.p_ri, "", "corte"),
            (21.36, self.p_olha_chao, "", "corte"),
            (22.60, self.p_tenis, "", "corte"),
            (24.76, self.p_susto, "frio", "corte"),
            (26.38, self.p_passos, "", "whip"),
            (29.96, self.p_galeria, "", "corte"),
            (31.94, self.p_foto(lambda: self.f_rua), "", "corte"),
            (33.78, self.p_foto(lambda: self.f_porta), "", "corte"),
            (34.80, self.p_foto(lambda: self.f_47), "", "corte"),
            (36.40, self.p_calendario, "", "whip"),
            (39.38, self.p_saldos, "", "corte"),
            (42.86, self.p_mao, "frio", "corte"),
            (43.86, self.p_chave, "frio", "corte"),
            (45.44, self.p_espelho, "frio", "whip"),
            (50.56, self.p_sexta, "", "corte"),
            (53.04, self.p_vendido, "", "corte"),
            (53.90, self.p_gravando, "noite", "corte"),
            (56.68, self.p_assiste, "", "corte"),
            (58.38, self.p_cam_levanta, "", "zoom"),
            (60.80, self.p_cam_olhos, "", "corte"),
            (61.94, self.p_cam_chave, "", "corte"),
            (64.56, self.p_cam_vira, "", "corte"),
            (67.30, self.p_cam_sorriso, "", "corte"),
            (69.32, self.p_corre, "noite", "whip"),
            (71.14, self.p_porta47, "", "corte"),
            (73.78, self.p_fechadura, "", "corte"),
            (74.96, self.p_entra, "", "corte"),
            (75.74, self.p_parede, "", "corte"),
            (79.62, self.p_lista, "", "corte"),
            (81.08, self.p_lista_zoom, "", "corte"),
            (84.34, self.p_pronto, "", "corte"),
            (84.94, self.p_passos_atras, "", "corte"),
            (87.20, self.p_silhueta, "", "corte"),
            (90.16, self.p_final, "", "corte"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))

    # ----- helpers -----
    def fundo(self, c1=(30, 30, 45), c2=(15, 15, 25)):
        return gradiente(WW, WH, c1, c2)

    def tela(self, img, t, d, larg=780, z0=1.0, z1=1.1, tremor=0.0):
        m = self.fundo()
        m.alpha_composite(brilho((1000, 1000), (140, 110, 230), 500, 0.35), (40, 460))
        dx = tremor * math.sin(t * 40)
        self.segura(m, img, 540 + dx, 900, larg)
        return camera(m, 540, 960, z0 + (z1 - z0) * ease_io(t / d))

    # ----- planos -----
    def p_app_oferta(self, t, d):
        f = self.tela(self.app_oferta, t, d, z0=1.0, z1=1.15)
        return f

    def p_dormindo_dinheiro(self, t, d):
        m = self.q_noite.copy()
        self.voce.desenhar(m, t, 400, 1400, escala=1.15, expr="ri", piscar=False)
        m.alpha_composite(self.cob_n, (0, 1160))
        f = camera(m, 540, 1150, 1.1)
        dr = ImageDraw.Draw(f)
        rng = random.Random(1)
        for i in range(18):         # notas caindo
            x = rng.uniform(0, OUT_W)
            y = (rng.uniform(-400, 0) + t * rng.uniform(250, 420)) % (OUT_H + 100) - 50
            a = rng.uniform(0, 6) + t * 3
            pts = [(-34, -18), (34, -18), (34, 18), (-34, 18)]
            pts = [(x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)) for px, py in pts]
            dr.polygon(pts, fill=(90, 190, 110), outline=(30, 90, 50))
        if t > 0.2:
            texto_pop(f, "Z z z", self.fc, t - 0.2, OUT_W * 0.35, OUT_H * 0.3, 70, (200, 210, 255))
        return f

    def p_facil(self, t, d):
        m = self.fundo((60, 60, 85), (35, 35, 55))
        self.voce.desenhar(m, t, 540, 2400, escala=2.6, expr="feliz")
        return camera(m, 540, 1000, 1.05 + 0.08 * ease_io(t / d))

    def p_app_regra(self, t, d):
        f = self.tela(self.app_regra, t, d, z0=1.0, z1=1.25)
        return f

    def p_pensa(self, t, d):
        m = self.fundo((60, 60, 85), (35, 35, 55))
        self.voce.desenhar(m, t, 380, 1800, escala=1.6, expr="neutro")
        cont = Image.new("RGB", (380, 300), (40, 150, 90))
        dd = ImageDraw.Draw(cont)
        ff = fnt(self.fc, 90)
        dd.text((190 - ff.getlength("R$") / 2, 90), "R$", font=ff, fill=(255, 255, 255))
        s = ease_out((t - 0.3) / 0.3)
        if s > 0:
            b = g.balao_pensamento(cont).resize((int(520 * s) + 1, int(520 * s) + 1), Image.BICUBIC)
            m.alpha_composite(b, (int(780 - b.width / 2), int(620 - b.height / 2)))
        return camera(m, 540, 1150, 1.1)

    def p_aceitar(self, t, d):
        f = self.tela(self.app_aceitar, t, d, z0=1.05, z1=1.15)
        # dedo tocando o botão
        k = ease_out(min(1, t / 0.4))
        dr = ImageDraw.Draw(f)
        x, y = OUT_W * 0.52, OUT_H * 0.83 + 260 * (1 - k)
        dr.rounded_rectangle((x - 40, y - 10, x + 40, y + 300), radius=40, fill=VOCE["pele"], outline=OUTLINE, width=5)
        if t > 0.4 and t < 0.6:
            dr.ellipse((x - 70, y - 50, x + 70, y + 50), outline=(255, 255, 255), width=6)
        return f

    def p_pulseira(self, t, d):
        m = self.fundo((20, 22, 40), (10, 10, 20))
        p = Pincel(WW, WH)
        p.ret((-100, 820, WW + 100, 1180), VOCE["pele"], r=150)
        m.alpha_composite(p.pronto())
        k = 0.6 + 0.4 * math.sin(t * 8)
        m.alpha_composite(brilho((700, 700), (80, 160, 255), 350, 0.7 * k), (190, 650))
        self.segura(m, self.pulseira, 540, 1000, 720)
        return camera(m, 540, 1000, 1.1 + 0.1 * ease_io(t / d))

    def p_apaga(self, t, d):
        m = self.fundo((20, 22, 40), (10, 10, 20))
        self.segura(m, self.pulseira, 540, 1000, 720)
        f = camera(m, 540, 1000, 1.2)
        return ImageEnhance.Brightness(f).enhance(max(0.0, 1 - t / 0.35))

    def p_relogio(self, t, d):
        m = self.fundo((40, 40, 50), (20, 20, 25))
        p = Pincel(WW, WH)
        p.ret((190, 700, 890, 1150), (30, 30, 35), r=40)
        p.ret((240, 760, 840, 1090), (10, 15, 10), r=20)
        m.alpha_composite(p.pronto())
        dd = ImageDraw.Draw(m)
        ff = fnt(self.fc, 230)
        if int(t * 4) % 2 == 0:
            dd.text((540 - ff.getlength("07:00") / 2, 790), "07:00", font=ff, fill=(240, 60, 60))
        f = camera(m, 540, 950, 1.1 + (0.03 * math.sin(t * 50) if t < 0.6 else 0))
        return f

    def p_saldo(self, t, d):
        return self.tela(self.app_saldo, t, d, z0=1.0, z1=1.2)

    def p_ri(self, t, d):
        m = self.q_manha.copy()
        rindo = int(t * 5) % 2
        self.voce.desenhar(m, t, 520, 1500, escala=1.2, expr="ri" if rindo else "feliz", pulo=6 * rindo)
        m.alpha_composite(self.cob_m, (0, 1160))
        return camera(m, 540, 1150, 1.1)

    def p_olha_chao(self, t, d):
        m = self.q_manha.copy()
        self.voce.desenhar(m, t, 520, 1500, escala=1.2, expr="neutro")
        m.alpha_composite(self.cob_m, (0, 1160))
        self.segura(m, self.tenis, 540, 1720, 520)
        k = ease_io(t / d)
        return camera(m, 540, 1150 + 500 * k, 1.1 + 0.3 * k)

    def p_tenis(self, t, d):
        m = gradiente(WW, WH, (150, 120, 95), (120, 95, 75))
        self.segura(m, self.tenis, 540, 1000, 960)
        f = camera(m, 540, 1000, 1.0 + 0.25 * ease_out(t / 0.4))
        return f

    def p_susto(self, t, d):
        m = self.fundo((60, 60, 80), (35, 35, 50))
        self.voce.desenhar(m, t, 540, 2450, escala=2.7, expr="surpreso", piscar=False)
        f = camera(m, 540, 1000, 1.0 + 0.35 * ease_out(t / 0.3))
        if t < 0.1:
            f = Image.blend(f, Image.new("RGB", f.size, (255, 255, 255)), 0.6)
        return f

    def p_passos(self, t, d):
        return self.tela(self.app_passos, t, d, z0=1.0, z1=1.25)

    def p_galeria(self, t, d):
        m = self.fundo()
        tel = celular(self.fc, "GALERIA", [], cor=(50, 50, 70))
        m2 = tel.copy()
        for i, fo in enumerate((self.f_rua, self.f_porta, self.f_47, self.f_rua, self.f_porta, self.f_47)):
            if t > 0.15 * i:
                th = fo.resize((240, 240))
                m2.alpha_composite(th, (60 + (i % 2) * 260, 300 + (i // 2) * 260))
        self.segura(m, m2, 540, 900, 780)
        return camera(m, 540, 960, 1.05)

    def p_foto(self, getter):
        def plano(t, d):
            m = self.fundo()
            self.segura(m, getter(), 540, 900, 860, rot=-3)
            return camera(m, 540, 950, 1.0 + 0.2 * ease_out(t / d))
        return plano

    def p_calendario(self, t, d):
        m = self.fundo((40, 40, 55), (20, 20, 30))
        k = min(4, 2 + int(t / 0.9))
        m.alpha_composite(self.cal[k], (0, 500))
        return camera(m, 540, 960, 1.05)

    def p_saldos(self, t, d):
        k = min(2, int(t / (d / 3)))
        return self.tela(self.app_saldos[k], t, d, z0=1.1, z1=1.1)

    def p_mao(self, t, d):
        m = self.fundo((50, 50, 60), (25, 25, 35))
        self.segura(m, self.mao, 540, 950, 720)
        return camera(m, 540, 950, 1.0 + 0.3 * ease_out(t / 0.4))

    def p_chave(self, t, d):
        m = self.fundo((50, 50, 60), (25, 25, 35))
        m.alpha_composite(brilho((800, 800), (230, 200, 120), 400, 0.4), (140, 500))
        self.segura(m, self.chave, 540, 900, 820, rot=-10 + 6 * math.sin(t * 3))
        return camera(m, 540, 950, 1.1)

    def p_espelho(self, t, d):
        # o texto vai aparecendo enquanto a narração lê o bilhete
        T = 45.44 + t
        k = 0 if T < 48.44 else (1 if T < 49.24 else (2 if T < 49.70 else 3))
        m = self.esp[k].copy()
        f = camera(m, 540, 800, 1.05 + 0.15 * ease_io(t / d))
        return f

    def p_sexta(self, t, d):
        m = self.fundo((40, 40, 55), (20, 20, 30))
        m.alpha_composite(self.cal[5], (0, 500))
        return camera(m, 820, 960, 1.0 + 0.6 * ease_out(t / 0.5))

    def p_vendido(self, t, d):
        f = self.tela(self.app_vendido, t, d, z0=1.15, z1=1.2, tremor=6)
        return f

    def p_gravando(self, t, d):
        m = self.q_noite.copy()
        self.voce.desenhar(m, t, 400, 1400, escala=1.15, expr="ri", piscar=False)
        m.alpha_composite(self.cob_n, (0, 1160))
        tel = celular(self.fc, "CÂMERA", [("● REC", 60, (220, 40, 40))], cor=(40, 40, 50))
        self.segura(m, tel, 900, 860, 240, rot=-4)
        return camera(m, 600, 1100, 1.1)

    def p_assiste(self, t, d):
        m = self.fundo((60, 60, 80), (35, 35, 50))
        m.alpha_composite(brilho((900, 900), (140, 200, 160), 450, 0.5), (90, 600))
        self.voce.desenhar(m, t, 540, 2350, escala=2.5, expr="neutro")
        tel = celular(self.fc, "VÍDEO", [("03:00", 70, (40, 40, 55))], cor=(40, 40, 50))
        self.segura(m, tel, 540, 1700, 380)
        return camera(m, 540, 1050, 1.05 + 0.1 * ease_io(t / d))

    # --- câmera noturna ---
    def cena_cama(self, t, sentado=0.0, expr="neutro", pose="idle", fora=False, tenis=False):
        m = self.q_noite.copy()
        if not fora:
            self.voce_sujo.desenhar(m, t, 520, 1400 - 260 * sentado, escala=1.15, expr=expr, pose=pose, piscar=False)
        m.alpha_composite(self.cob_n, (0, int(1160 + 120 * sentado)))
        return m

    def p_cam_levanta(self, t, d):
        k = ease_io(min(1, t / 1.6))
        m = self.cena_cama(t, sentado=k)
        f = camera(m, 540, 1150, 1.05)
        return cam_noturna(f, self.fc, 58.38 + t)

    def p_cam_olhos(self, t, d):
        m = self.cena_cama(t, sentado=1.0)
        z = 1.9 + 0.2 * ease_io(t / d)
        f = camera(m, 520, 940, z)
        f = cam_noturna(f, self.fc, 60.8 + t)
        ox, oy, sep = olhos_do(520, 1400 - 260, 1.15)
        x, y, k = proj(ox, oy - 4 * math.sin(t * 2 * math.pi * 0.9), 520, 940, z)
        return olhos_brilhando(f, x, y, sep * k, 12 * k, 0.9)

    def p_cam_chave(self, t, d):
        m = self.q_noite.copy()
        pose = "entrega" if t < 1.2 else "idle"
        self.voce_sujo.desenhar(m, t, 640, 1720, escala=1.3, expr="neutro", pose=pose, piscar=False)
        if t < 1.2:
            hx, hy = self.mao(640, 1720, 1.3, t)
            self.segura(m, self.chave, hx + 30, hy - 10, 160)
        else:
            self.segura(m, self.tenis, 640, 1730, 380)
        f = camera(m, 600, 1250, 1.1)
        return cam_noturna(f, self.fc, 61.94 + t)

    def p_cam_vira(self, t, d):
        m = self.q_noite.copy()
        self.voce_sujo.desenhar(m, t, 540, 1720, escala=1.4,
                                expr="feliz" if t > d * 0.6 else "neutro", piscar=False)
        f = camera(m, 540, 1150, 1.1 + 0.3 * ease_io(t / d))
        f = cam_noturna(f, self.fc, 64.56 + t)
        if t > d * 0.6:
            f = glitch(f, t, 0.6)
        return f

    def p_cam_sorriso(self, t, d):
        m = self.fundo((60, 60, 80), (30, 30, 40))
        self.voce_sujo.desenhar(m, t, 540, 2500, escala=2.8, expr="feliz", piscar=False)
        z = 1.05 + 0.15 * ease_io(t / d)
        f = camera(m, 540, 1000, z)
        f = cam_noturna(f, self.fc, 67.3 + t)
        ox, oy, sep = olhos_do(540, 2500, 2.8)
        x, y, k = proj(ox, oy - 4 * math.sin(t * 2 * math.pi * 0.9), 540, 1000, z)
        f = olhos_brilhando(f, x, y, sep * k, 12 * k, 0.6 + 0.4 * math.sin(t * 6))
        return glitch(f, t, 0.4 + 0.8 * (int(t * 7) % 3 == 0))

    def p_corre(self, t, d):
        off = (t * 1100) % WW
        m = Image.new("RGBA", (WW, WH))
        m.alpha_composite(self.rua, (int(-off), 0))
        m.alpha_composite(self.rua, (int(WW - off), 0))
        passo = int(t * 8) % 2
        self.voce.desenhar(m, t, 540, 1760, escala=1.25, expr="surpreso", pose="acena" if passo else "idle",
                           rot=-8, pulo=25 * passo)
        f = camera(m, WW / 2, 1150, 1.15)
        dr = ImageDraw.Draw(f)
        rng = random.Random(int(t * 10))
        for _ in range(8):
            y, x = rng.uniform(200, 1100), rng.uniform(0, OUT_W)
            dr.line((x, y, x + rng.uniform(80, 200), y), fill=(200, 200, 230), width=4)
        return f

    def p_porta47(self, t, d):
        m = self.rua_porta.copy()
        self.voce.desenhar(m, t, 240, 1760, escala=1.1, expr="neutro")
        return camera(m, 540, 1200, 1.1 + 0.35 * ease_io(t / d))

    def p_fechadura(self, t, d):
        m = gradiente(WW, WH, (40, 90, 190), (30, 70, 150))
        p = Pincel(WW, WH)
        p.elipse((400, 760, 680, 1040), (230, 200, 80))
        p.ret((515, 830, 565, 980), (30, 30, 40), r=20, ow=0)
        m.alpha_composite(p.pronto())
        k = ease_out(min(1, t / 0.5))
        ch = self.chave.rotate(0 if t < 0.6 else -90 * ease_out((t - 0.6) / 0.3), expand=True, resample=Image.BICUBIC)
        self.segura(m, ch, 540 - 420 * (1 - k) - 200, 900, 700)
        return camera(m, 540, 950, 1.1)

    def p_entra(self, t, d):
        m = self.fundo((10, 10, 18), (5, 5, 10))
        k = ease_out(t / d)
        m.alpha_composite(brilho((900, 1400), (80, 150, 255), 600, 0.8 * k), (90, 260))
        p = Pincel(WW, WH)
        p.ret((540 - 420 * k, 260, 540 + 420 * k, 1700), (20, 40, 80), r=0, ow=0)
        m.alpha_composite(p.pronto())
        return camera(m, 540, 960, 1.0)

    def p_parede(self, t, d):
        m = parede_pulseiras(t)
        return camera(m, 540, 700 + 500 * ease_io(t / d), 1.3 - 0.25 * ease_io(t / d))

    def p_lista(self, t, d):
        m = self.fundo((30, 30, 40), (15, 15, 20))
        self.segura(m, self.lista, 540, 950, 860)
        return camera(m, 540, 960, 1.0 + 0.05 * ease_io(t / d))

    def p_lista_zoom(self, t, d):
        m = self.fundo((30, 30, 40), (15, 15, 20))
        self.segura(m, self.lista, 540, 950, 860)
        k = ease_io(t / d)
        return camera(m, 540 - 90 * k, 960 + 420 * k, 1.0 + 0.6 * k)

    def p_pronto(self, t, d):
        m = self.fundo((30, 30, 40), (15, 15, 20))
        self.segura(m, self.lista_p, 540, 950, 860)
        f = camera(m, 530, 1380, 1.45 + 0.2 * ease_out(t / 0.2))
        if t < 0.08:
            f = Image.blend(f, Image.new("RGB", f.size, (200, 30, 40)), 0.5)
        return glitch(f, t, 0.5)

    def p_passos_atras(self, t, d):
        m = parede_pulseiras(t)
        f0 = Image.new("RGBA", (WW, WH))
        f0.alpha_composite(m)
        self.voce.desenhar(f0, t, 540, 2100, escala=2.0, expr="surpreso", piscar=False)
        f = camera(f0, 540, 1150, 1.1 + 0.08 * ease_io(t / d))
        return noite(f, 0.6)

    def p_silhueta(self, t, d):
        m = self.fundo((10, 10, 15), (3, 3, 6))
        k = min(1, t / 1.2)
        spr = self.voce_sujo.spr("neutro", "idle")
        sil = Image.new("RGBA", spr.size, (8, 8, 12, 255))
        sil.putalpha(spr.getchannel("A"))
        e = 2.6 + 0.3 * k
        g.colar(m, sil, 540, 2300, escala=e)
        f = camera(m, 540, 1000, 1.0)
        ox, oy, sep = olhos_do(540, 2300, e)
        x, y, kk = proj(ox, oy, 540, 1000, 1.0)
        f = olhos_brilhando(f, x, y, sep * kk, 12 * kk, ease_io(t / 0.8))
        return f

    def p_final(self, t, d):
        m = self.fundo((10, 10, 15), (3, 3, 6))
        spr = self.voce_sujo.spr("feliz", "idle")
        g.colar(m, spr, 540, 2600, escala=3.0)
        z = 1.05 + 0.15 * ease_io(t / d)
        f = camera(m, 540, 1000, z)
        f = noite(f, 1.0)
        ox, oy, sep = olhos_do(540, 2600, 3.0)
        x, y, k = proj(ox, oy, 540, 1000, z)
        f = olhos_brilhando(f, x, y, sep * k, 12 * k, 1.0)
        f = glitch(f, t, 0.3 + 1.5 * (t > d - 0.6))
        if t > d - 0.5:
            f = ImageEnhance.Brightness(f).enhance(max(0, 1 - (t - (d - 0.5)) / 0.5))
        return f

    # ----- montagem: graduação "noite"/"frio" e cortes rápidos -----
    def frame(self, n):
        t = n / FPS
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if t < ini + d or i == len(self.planos) - 1:
                tl = t - ini
                f = fn(tl, d)
                f = self.gradear(f, clima)
                if i > 0 and tl < 0.18 and tr in ("whip", "zoom"):
                    pi, pd, pfn, pcl, _ = self.planos[i - 1]
                    prev = self.gradear(pfn(pd - 0.001, pd), pcl)
                    x = tl / 0.18
                    if tr == "whip":
                        off = int(OUT_W * ease_io(x))
                        comp = Image.new("RGB", (OUT_W, OUT_H))
                        comp.paste(prev, (-off, 0))
                        comp.paste(f, (OUT_W - off, 0))
                        f = g.motion_blur_h(comp, 60 * math.sin(math.pi * x))
                    else:
                        f = g.zoom_blur(Image.blend(prev, f, ease_io(x)), 0.4 * math.sin(math.pi * x))
                f = g.vinheta(f, 0.5)
                self.legenda(f, t)
                return f

    @staticmethod
    def gradear(f, clima):
        if clima == "noite":
            return noite(f, 0.8)
        if clima == "frio":
            f = ImageEnhance.Color(f).enhance(0.5)
            return noite(f, 0.4)
        return noite(f, 0.15)

    def eventos_sfx(self):
        ev = []
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if i and tr in ("whip", "zoom"):
                ev.append(("whoosh", ini - 0.06))
            elif i:
                ev.append(("tick", ini))
        ev += [("ding", 18.14), ("ding", 39.38), ("ding", 40.4), ("ding", 41.4), ("ding", 53.04),
               ("impacto", 22.60), ("impacto", 24.76), ("impacto", 84.34), ("impacto", 87.20),
               ("alarme", 17.06), ("click", 13.9), ("click", 74.5)]
        ev += [("batida", 84.94 + k * 0.85) for k in range(7)]
        return ev


# --------------------------------------------------------------------------
# Áudio de suspense
# --------------------------------------------------------------------------
SR = g.SR


def drone(dur):
    t = np.arange(int(SR * dur)) / SR
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.08 * t)
    s = (np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.4 * t + 0.3)
         + 0.3 * np.sin(2 * np.pi * 110.5 * t) + 0.2 * np.sin(2 * np.pi * 164.8 * t * (1 + 0.002 * np.sin(t))))
    ruido = np.convolve(np.random.default_rng(1).standard_normal(len(t)), np.ones(200) / 200, "same")
    sobe = np.clip((t - 55) / 35, 0, 1)  # tensão cresce no 3º ato
    return (s * 0.18 * lfo + ruido * 0.6) * (0.7 + 0.6 * sobe)


def sfx(tipo):
    rng = np.random.default_rng(5)
    t = lambda d: np.arange(int(SR * d)) / SR  # noqa: E731
    if tipo == "tick":
        x = t(0.05)
        return np.sin(2 * np.pi * 1800 * x) * np.exp(-x * 120) * 0.15
    if tipo == "ding":
        x = t(0.6)
        return (np.sin(2 * np.pi * 1320 * x) + 0.5 * np.sin(2 * np.pi * 1980 * x)) * np.exp(-x * 6) * 0.25
    if tipo == "impacto":
        x = t(1.4)
        boom = np.sin(2 * np.pi * (60 - 25 * x) * x) * np.exp(-x * 2.5)
        return (boom + 0.3 * rng.standard_normal(len(x)) * np.exp(-x * 12)) * 0.9
    if tipo == "batida":
        x = t(0.5)
        b = np.sin(2 * np.pi * 50 * x) * np.exp(-x * 14)
        b2 = np.zeros_like(b)
        k = int(0.16 * SR)
        b2[k:] = b[:-k] * 0.7
        return (b + b2) * 0.8
    if tipo == "alarme":
        x = t(0.9)
        return np.sign(np.sin(2 * np.pi * 900 * x)) * (np.sin(2 * np.pi * 4 * x) > 0) * 0.08
    if tipo == "click":
        x = t(0.08)
        return rng.standard_normal(len(x)) * np.exp(-x * 90) * 0.4
    return g.sfx(tipo)


def mixar(filme, narracao, saida):
    voz = vc.ler_wav_mono(narracao)
    n = int(filme.dur_total * SR)
    mix = np.zeros(n, np.float32)
    mix[:min(n, len(voz))] += voz[:n]
    dr = drone(filme.dur_total)
    mix[:len(dr)] += (dr / max(1e-6, np.abs(dr).max()) * 0.13)[:n]
    for tipo, t0 in filme.eventos_sfx():
        s = sfx(tipo)
        if tipo == "whoosh":
            s = s * 0.35
        a = int(max(0, t0) * SR)
        b = min(n, a + len(s))
        mix[a:b] += s[: b - a]
    fade = int(SR * 0.6)
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
            txt = TROCA_POR_TEMPO.get(round(w["s"], 2), CORRECOES.get(w["w"], w["w"]))
            pal.append(dict(w=txt, s=w["s"], e=w["e"]))
    return pal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_aplicativo_do_sono.mp4"))
    ap.add_argument("--preview", default=None)
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / SR
    filme = FilmeSono(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.0)
    total = int(filme.dur_total * FPS)

    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        for i, (ini, d, *_r) in enumerate(filme.planos):
            filme.frame(int((ini + d * 0.6) * FPS)).save(os.path.join(a.preview, f"plano_{i:02d}.png"))
        print("preview em", a.preview)
        return

    tmp = tempfile.mkdtemp(prefix="sono_")
    wav = os.path.join(tmp, "mix.wav")
    mixar(filme, a.narracao, wav)
    print(f"• renderizando {total} frames ({filme.dur_total:.1f}s)…", flush=True)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}",
         "-r", str(FPS), "-i", "-", "-i", wav, "-vf", "scale=1080:1920:flags=lanczos",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
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
