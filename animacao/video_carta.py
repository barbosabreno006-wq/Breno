#!/usr/bin/env python3
"""
"A Carta do Vô" — vídeo completo sincronizado com a narração do ElevenLabs.

Pipeline:
  1. remover_silencios.py  -> narração sem pausas longas (mais dinâmica)
  2. faster-whisper        -> tempos de cada palavra (transcricao.json)
  3. este script           -> ~29 planos, legenda karaokê nos tempos reais,
                              trilha + SFX mixados por baixo da voz

Uso:
    python3 animacao/video_carta.py --narracao narracao.wav --transcricao transcricao.json \
        --fonte Poppins-ExtraBold.ttf --saida animacao/video_carta_do_vo.mp4
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
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_video as g  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, Ator, gradiente, brilho,
                         colar, ease_out, ease_io, camera, motion_blur_h, zoom_blur, vinheta,
                         particulas, texto_pop)

random.seed(11)

# --------------------------------------------------------------------------
# Elenco
# --------------------------------------------------------------------------
VO = dict(pele=(214, 160, 120), cabelo=(228, 228, 232), camisa=(70, 110, 170), calca=(50, 70, 110),
          sapato=(60, 50, 50), tipo="vovo_h", chapeu=(60, 90, 160), bolsa=True)
VO_CASA = dict(VO, chapeu=None, bolsa=False, camisa=(150, 170, 120), calca=(110, 90, 70))
VITINHO = dict(pele=(232, 176, 128), cabelo=(92, 58, 38), camisa=(80, 170, 170), calca=(200, 170, 110),
               sapato=(230, 90, 80), tipo="menino")
VITINHO_CARTEIRO = dict(VITINHO, chapeu=(60, 90, 160), bolsa=True)
MOCA = dict(pele=(150, 100, 70), cabelo=(40, 30, 30), camisa=(240, 120, 120), calca=(0, 0, 0),
            sapato=(120, 60, 60), tipo="moca", vestido=(240, 140, 140))

# correções da transcrição automática (o Whisper errou alguns nomes)
CORRECOES = {"voo": "vô", "voo,": "vô,", "entregue": "Entrega", "tomho.": "Tonho.",
             "vitinho,": "Vitinho,", "Para": "Pra", "para": "pra"}
REMOVER = {(14.94, "a")}          # "toda a manhã" -> "toda manhã"
DESTAQUE_VERMELHO = {"esquecer,", "Quem", "notícia.", "esqueci", "nunca"}


# --------------------------------------------------------------------------
# Objetos de cena
# --------------------------------------------------------------------------
def fonte(caminho, tam):
    return ImageFont.truetype(caminho, tam) if caminho else ImageFont.load_default()


def envelope(w=420, texto=None, fonte_c=None, selo=True):
    h = int(w * 0.64)
    p = Pincel(w + 20, h + 20)
    p.ret((10, 10, w + 10, h + 10), (250, 238, 210), r=16)
    p.linha([(14, 14), (w / 2 + 10, h * 0.58), (w + 6, 14)], fill=OUTLINE, w=6)
    p.linha([(14, h + 6), (w * 0.38, h * 0.5)], fill=(210, 190, 160), w=5)
    p.linha([(w + 6, h + 6), (w * 0.62 + 20, h * 0.5)], fill=(210, 190, 160), w=5)
    if selo:
        cx, cy = w / 2 + 10, h * 0.58
        p.elipse((cx - 34, cy - 34, cx + 34, cy + 34), (210, 60, 60), ow=5)
        p.elipse((cx - 14, cy - 14, cx + 14, cy + 14), (240, 110, 100), ow=0)
    img = p.pronto()
    if texto:
        d = ImageDraw.Draw(img)
        f = fonte(fonte_c, int(w * 0.075))
        for i, linha in enumerate(texto.split("\n")):
            d.text((34, h * 0.70 + i * w * 0.085 - 10), linha, font=f, fill=(60, 60, 110))
    return img


def calendario(dia_marcado=None, fonte_c=None, w=620):
    p = Pincel(w, w * 1.05)
    p.ret((10, 40, w - 10, w * 1.03), (255, 255, 255), r=24)
    p.ret((10, 40, w - 10, 190), (220, 70, 70), r=24)
    for x in (w * 0.3, w * 0.7):
        p.ret((x - 12, 10, x + 12, 80), (90, 90, 100), r=10)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = fonte(fonte_c, 38)
    n = 1
    for lin in range(5):
        for col in range(7):
            if n > 31:
                break
            x, y = 40 + col * (w - 80) / 7, 220 + lin * 74
            if n == dia_marcado:
                d.ellipse((x - 10, y - 10, x + 64, y + 58), outline=(220, 40, 40), width=8)
            d.text((x + 4, y), str(n), font=f, fill=(60, 60, 80))
            n += 1
    return img


def desenho_crianca(w=560):
    """Desenho de giz: vô de quepe + criança + sol + coração."""
    p = Pincel(w, w * 1.2)
    p.ret((10, 10, w - 10, w * 1.2 - 10), (255, 252, 240), r=6, ow=6)
    giz = dict(ow=0)
    p.elipse((w - 170, 40, w - 60, 150), (255, 200, 40), **giz)
    for a in range(0, 360, 40):
        x, y = w - 115 + 85 * math.cos(math.radians(a)), 95 + 85 * math.sin(math.radians(a))
        p.linha([(w - 115 + 60 * math.cos(math.radians(a)), 95 + 60 * math.sin(math.radians(a))), (x, y)],
                fill=(255, 190, 40), w=8)
    # vô
    p.arco((90, 220, 230, 360), 0, 360, fill=(80, 80, 200), w=9)
    p.ret((80, 200, 240, 240), (60, 90, 200), r=6, ow=0)
    p.linha([(160, 360), (160, 540)], fill=(80, 80, 200), w=9)
    p.linha([(160, 420), (80, 480)], fill=(80, 80, 200), w=9)
    p.linha([(160, 420), (260, 460)], fill=(80, 80, 200), w=9)
    p.linha([(160, 540), (110, 640)], fill=(80, 80, 200), w=9)
    p.linha([(160, 540), (210, 640)], fill=(80, 80, 200), w=9)
    # criança
    p.arco((290, 340, 390, 440), 0, 360, fill=(40, 160, 140), w=9)
    p.linha([(340, 440), (340, 560)], fill=(40, 160, 140), w=9)
    p.linha([(340, 480), (270, 460)], fill=(40, 160, 140), w=9)
    p.linha([(340, 560), (300, 640)], fill=(40, 160, 140), w=9)
    p.linha([(340, 560), (380, 640)], fill=(40, 160, 140), w=9)
    # coração
    hx, hy = w / 2 + 10, 230
    p.elipse((hx - 40, hy - 30, hx, hy + 10), (230, 60, 80), ow=0)
    p.elipse((hx - 4, hy - 30, hx + 36, hy + 10), (230, 60, 80), ow=0)
    p.poli([(hx - 40, hy - 6), (hx + 36, hy - 6), (hx - 2, hy + 44)], (230, 60, 80), ow=0)
    p.linha([(30, 660), (w - 30, 660)], fill=(80, 180, 80), w=12)
    return p.pronto()


def chaves():
    p = Pincel(360, 360)
    p.arco((30, 30, 170, 170), 0, 360, fill=OUTLINE, w=22)
    p.arco((34, 34, 166, 166), 0, 360, fill=(210, 210, 220), w=12)
    for ang, cor in ((-20, (240, 200, 70)), (25, (200, 200, 210))):
        k = Pincel(360, 360)
        k.elipse((140, 120, 220, 200), cor)
        k.ret((205, 148, 340, 172), cor, r=6)
        k.ret((290, 168, 306, 200), cor, r=3, ow=5)
        k.ret((318, 168, 334, 192), cor, r=3, ow=5)
        p.img.alpha_composite(k.img.rotate(ang, center=(360, 320)))
    return p.pronto()


def carta_aberta(fonte_c, w=640):
    h = int(w * 1.25)
    p = Pincel(w, h)
    p.ret((10, 10, w - 10, h - 10), (252, 246, 228), r=10)
    for i in range(10):
        y = 210 + i * 70
        p.linha([(50, y), (w - 50, y)], fill=(200, 210, 235), w=3)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = fonte(fonte_c, 44)
    linhas = ["Vitinho,", "se essa carta chegou,", "eu já esqueci o", "seu nome.", "",
              "Agora é a sua vez", "de entregar.", "", "      — Vô"]
    for i, l in enumerate(linhas):
        d.text((60, 150 + i * 70), l, font=f, fill=(50, 60, 120))
    return img


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def nuvem(p, x, y, s=1.0):
    for dx, dy, r in ((0, 0, 60), (60, -30, 70), (130, 0, 60), (65, 20, 60)):
        p.elipse((x + dx * s - r * s, y + dy * s - r * s, x + dx * s + r * s, y + dy * s + r * s),
                 (255, 255, 255), ow=0)


def cidade_dia(fonte_c, por_do_sol=False, placa="CORREIO DO FUTURO"):
    base = gradiente(WW, WH, (250, 190, 140) if por_do_sol else (140, 200, 240),
                     (255, 230, 190) if por_do_sol else (225, 240, 250))
    p = Pincel(WW, WH)
    if por_do_sol:
        p.elipse((380, 560, 700, 880), (255, 220, 120), ow=0)
    nuvem(p, 120, 220, 1.0)
    nuvem(p, 700, 340, 0.8)
    cores = g.CORES_CASAS
    for i, x in enumerate((-60, 820)):
        top = 760
        p.ret((x, top, x + 320, 1400), cores[i * 2], r=6)
        p.poli([(x - 20, top + 4), (x + 160, top - 160), (x + 340, top + 4)], (170, 90, 80))
        for jx in (x + 50, x + 190):
            p.ret((jx, top + 80, jx + 80, top + 190), (255, 240, 200), r=8, ow=6)
        p.ret((x + 120, 1220, x + 200, 1400), (110, 70, 55), r=10)
    # correio no centro
    p.ret((250, 640, 830, 1400), (240, 200, 120), r=8)
    p.ret((220, 600, 860, 680), (200, 80, 70), r=10)
    p.elipse((460, 440, 620, 600), (255, 255, 255))            # relógio
    p.linha([(540, 520), (540, 465)], w=8)
    p.linha([(540, 520), (580, 535)], w=8)
    p.ret((300, 760, 780, 860), (250, 245, 230), r=10)          # placa
    for jx in (300, 640):
        p.ret((jx, 920, jx + 140, 1100), (180, 220, 240), r=10)
    p.ret((470, 1120, 610, 1400), (130, 80, 60), r=12)
    p.ret((-20, 1390, WW + 20, 1500), (200, 190, 175), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (120, 180, 110) if not por_do_sol else (200, 150, 110), r=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = fonte(fonte_c, 46)
    t = placa
    d.text((540 - f.getlength(t) / 2, 785), t, font=f, fill=(200, 80, 70))
    return base


def correio_interno(fonte_c):
    base = gradiente(WW, WH, (240, 220, 190), (230, 200, 170))
    p = Pincel(WW, WH)
    for lin in range(6):          # escaninhos com cartas
        for col in range(5):
            x, y = 90 + col * 185, 240 + lin * 150
            p.ret((x, y, x + 170, y + 135), (190, 140, 100), r=6, ow=6)
            if (lin * 5 + col) % 3:
                p.ret((x + 30, y + 40, x + 140, y + 120), (250, 240, 215), r=4, ow=4)
    p.ret((-20, 1300, WW + 20, WH + 20), (170, 120, 90), r=0)
    p.ret((-20, 1260, WW + 20, 1330), (120, 80, 60), r=6)
    base.alpha_composite(p.pronto())
    return base


def balcao():
    p = Pincel(WW, 600)
    p.ret((40, 40, WW - 40, 120), (200, 90, 80), r=14)
    p.ret((70, 110, WW - 70, 600), (230, 120, 100), r=10)
    for x in range(140, WW - 100, 220):
        p.ret((x, 170, x + 150, 520), (215, 105, 90), r=12, ow=6)
    return p.pronto()


def quarto_noite():
    base = gradiente(WW, WH, (40, 40, 80), (70, 60, 100))
    p = Pincel(WW, WH)
    p.ret((620, 300, 960, 720), (30, 40, 80), r=10, ow=10)
    p.elipse((760, 380, 860, 480), (250, 240, 200), ow=0)
    p.linha([(790, 300), (790, 720)], w=10)
    p.ret((-20, 1400, WW + 20, WH + 20), (90, 70, 80), r=0)
    p.ret((60, 1240, 1020, 1320), (150, 100, 70), r=10)          # mesa
    p.ret((100, 1320, 140, 1700), (130, 85, 60), r=10)
    p.ret((940, 1320, 980, 1700), (130, 85, 60), r=10)
    p.ret((790, 1020, 810, 1240), (80, 80, 90), r=6)               # luminária
    p.chord((700, 940, 900, 1100), 180, 360, (250, 200, 90))
    p.ret((500, 1205, 700, 1245), (252, 246, 228), r=4, ow=5)      # papel
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((900, 900), (255, 200, 110), 450, 0.7), (350, 700))
    return base


def janela_manha():
    base = gradiente(WW, WH, (250, 225, 190), (240, 200, 160))
    p = Pincel(WW, WH)
    p.ret((180, 360, 900, 1180), (170, 215, 245), r=14, ow=14)
    p.elipse((620, 460, 800, 640), (255, 230, 120), ow=0)
    nuvem(p, 260, 520, 0.7)
    p.linha([(540, 360), (540, 1180)], w=14)
    p.linha([(180, 770), (900, 770)], w=14)
    p.ret((140, 1170, 940, 1240), (240, 240, 235), r=10)
    p.ret((-20, 1500, WW + 20, WH + 20), (190, 140, 100), r=0)
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((900, 900), (255, 240, 180), 450, 0.6), (90, 320))
    return base


def setas_confusas(t):
    base = gradiente(WW, WH, (200, 190, 200), (170, 160, 175))
    p = Pincel(WW, WH)
    for i in range(7):
        x = -200 + i * 220
        p.poli([(x, WH), (x + 120, WH), (x + 380 + 40 * math.sin(t + i), 0), (x + 300, 0)],
               (215, 205, 215) if i % 2 else (190, 180, 195), ow=5)
    rng = random.Random(4)
    for i in range(9):
        cx, cy = rng.uniform(100, 980), rng.uniform(250, 1250)
        a = rng.uniform(0, 360) + t * rng.choice((-60, 60))
        cor = rng.choice([(120, 120, 140), (110, 150, 120), (160, 120, 150), (130, 130, 100)])
        pts = [(-70, -16), (20, -16), (20, -44), (80, 0), (20, 44), (20, 16), (-70, 16)]
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        p.poli([(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts], cor, ow=5)
    base.alpha_composite(p.pronto())
    return base


def porta_aberta():
    m = g.cenario_porta()
    p = Pincel(WW, WH)
    p.ret((260, 260, 820, 1510), (70, 55, 60), r=24, ow=14)
    m.alpha_composite(p.pronto())
    m.alpha_composite(brilho((700, 1100), (255, 210, 150), 500, 0.35), (190, 330))
    return m


# --------------------------------------------------------------------------
# Correção de cor por "clima" da cena
# --------------------------------------------------------------------------
def gradear(f, clima):
    if clima == "triste":
        f = ImageEnhance.Color(f).enhance(0.35)
        a = np.asarray(f, np.float32)
        a = a * np.array([0.92, 0.97, 1.08]) * 0.95
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if clima == "sepia":
        a = np.asarray(f.convert("L"), np.float32)[..., None]
        a = a * np.array([1.08, 0.92, 0.72])[None, None, :] + np.array([22, 12, 0])
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if clima == "quente":
        a = np.asarray(ImageEnhance.Color(f).enhance(1.12), np.float32)
        a = a * np.array([1.05, 1.0, 0.9])
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return f


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class Filme:
    def __init__(self, palavras, fonte_c, dur_total):
        self.fc = fonte_c
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.vo, self.vo_casa = Ator(VO), Ator(VO_CASA)
        self.vit, self.vit_c, self.moca = Ator(VITINHO), Ator(VITINHO_CARTEIRO), Ator(MOCA)
        self.cidade = cidade_dia(fonte_c)
        self.cidade_sol = cidade_dia(fonte_c, por_do_sol=True)
        self.env = envelope(420)
        self.env_nome = envelope(700, "Para: Vitinho\nDe: Vô", fonte_c)
        self.cal = calendario(18, fonte_c)
        self.desenho = desenho_crianca()
        self.chaves = chaves()
        self.carta = carta_aberta(fonte_c)
        self.correio = correio_interno(fonte_c)
        self.balcao = balcao()
        self.quarto = quarto_noite()
        self.janela = janela_manha()
        self.porta = g.cenario_porta()
        self.porta_ab = porta_aberta()
        self.f_leg = fonte(fonte_c, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        # (início, função, clima, transição)
        P = [
            (0.00, self.p_cidade, "", "corte"),
            (1.48, self.p_envelope, "", "whip"),
            (3.34, self.p_calendario, "", "whip"),
            (6.48, self.p_um, "", "corte"),
            (9.22, self.p_um_vida, "", "zoom"),
            (10.88, self.p_vo_carteiro, "", "whip"),
            (13.72, self.p_vo_carta_branca, "", "corte"),
            (14.94, self.p_vo_bate, "", "whip"),
            (17.80, self.p_entrega, "quente", "corte"),
            (19.70, self.p_desenho, "quente", "corte"),
            (21.48, self.p_vo_confuso, "triste", "dissolve"),
            (23.08, self.p_chaves, "triste", "corte"),
            (24.36, self.p_ruas, "triste", "whip"),
            (25.42, self.p_vo_close, "triste", "corte"),
            (27.62, self.p_vitinho_choque, "triste", "corte"),
            (28.72, self.p_corre, "", "whip"),
            (31.62, self.p_balcao, "", "corte"),
            (33.06, self.p_moca_carta, "", "corte"),
            (36.42, self.p_envelope_nome, "", "corte"),
            (37.90, self.p_flashback, "sepia", "zoom"),
            (41.78, self.p_carta_lida, "", "dissolve"),
            (45.12, self.p_vo_lembra, "sepia", "dissolve"),
            (47.22, self.p_vitinho_chora, "quente", "dissolve"),
            (51.66, self.p_vitinho_bate, "", "whip"),
            (53.76, self.p_entrega2, "quente", "corte"),
            (55.56, self.p_vo_sorri, "quente", "corte"),
            (57.16, self.p_juntos, "quente", "corte"),
            (59.54, self.p_janela, "quente", "dissolve"),
            (61.84, self.p_final, "quente", "whip"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))

    # ---------- legenda karaokê com tempos reais ----------
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
            fim = self.blocos[i + 1][0]["s"] if i + 1 < len(self.blocos) else b[-1]["e"] + 0.6
            if b[0]["s"] - 0.05 <= t < fim:
                bloco = b
                break
        if not bloco:
            return
        f = self.f_leg
        esp = f.getlength(" ")
        larg = sum(f.getlength(w["w"]) for w in bloco) + esp * (len(bloco) - 1)
        cam = Image.new("RGBA", (int(larg + 40), 120), (0, 0, 0, 0))
        dc = ImageDraw.Draw(cam)
        x = 20
        for w in bloco:
            ativa = w["s"] <= t
            atual = ativa and (w is bloco[-1] or not (bloco[bloco.index(w) + 1]["s"] <= t))
            cor = (255, 255, 255)
            if atual:
                cor = (255, 80, 70) if w["w"] in DESTAQUE_VERMELHO else (255, 214, 40)
            dc.text((x, 20), w["w"], font=f, fill=cor, stroke_width=7, stroke_fill=(20, 20, 26))
            x += f.getlength(w["w"]) + esp
        pop = 0.82 + 0.18 * ease_out((t - bloco[0]["s"]) / 0.12)
        esc = min(pop, (OUT_W - 40) / cam.width)
        cam = cam.resize((max(1, int(cam.width * esc)), max(1, int(cam.height * esc))), Image.BICUBIC)
        img.paste(cam, (int(OUT_W / 2 - cam.width / 2), int(OUT_H * 0.79 - cam.height / 2)), cam)

    # ---------- utilidades ----------
    def mao(self, cx, by, e, t, pulo=0.0):
        """Posição da mão direita na pose 'entrega' (para segurar objetos)."""
        bob = 4 * math.sin(t * 2 * math.pi * 0.9) + pulo
        return cx + (302 - 170) * e, by - bob - (640 - 372) * e

    def segura(self, m, obj, x, y, larg, rot=0.0):
        o = obj.resize((int(larg), int(obj.height * larg / obj.width)), Image.BICUBIC)
        if rot:
            o = o.rotate(rot, resample=Image.BICUBIC, expand=True)
        m.alpha_composite(o, (int(x - o.width / 2), int(y - o.height / 2)))

    def liso(self, c1, c2):
        return gradiente(WW, WH, c1, c2)

    # ---------- planos ----------
    def p_cidade(self, t, d):
        f = camera(self.cidade.copy(), WW / 2, 1000, 1.0 + 0.15 * ease_io(t / d))
        particulas(f, t, 16, (255, 255, 255))
        return f

    def p_envelope(self, t, d):
        m = self.liso((255, 210, 150), (250, 160, 120))
        m.alpha_composite(brilho((1000, 1000), (255, 240, 170), 500, 0.9), (40, 400))
        y = 900 + 20 * math.sin(t * 3)
        self.segura(m, self.env, 540, y, 640, rot=6 * math.sin(t * 2))
        f = camera(m, WW / 2, 960, 1.05 + 0.08 * ease_io(t / d))
        particulas(f, t, 40, semente=2)
        return f

    def p_calendario(self, t, d):
        m = self.liso((190, 220, 240), (160, 200, 230))
        self.segura(m, self.cal, 540, 950, 760, rot=-3)
        # carta voando até o dia marcado
        k = ease_io(min(1, t / 1.6))
        x = -200 + (40 + 3 * 680 / 7 * 1.22 + 300) * k
        y = 1500 - 760 * k + 180 * math.sin(k * math.pi)
        self.segura(m, self.env, x, y, 220, rot=-20 * (1 - k))
        if t > 1.6:
            m.alpha_composite(brilho((500, 500), (255, 230, 120), 250, 0.8 * ease_out((t - 1.6) / 0.3)),
                              (int(x - 250), int(y - 250)))
        return camera(m, WW / 2, 960, 1.15)

    def p_um(self, t, d):
        m = self.cidade.copy()
        self.vit.desenhar(m, t, 380, 1720, escala=1.45, expr="neutro", pose="acena")
        f = camera(m, 480, 1180, 1.3)
        if t > 1.6:
            texto_pop(f, "1", self.fc, t - 1.6, OUT_W * 0.8, OUT_H * 0.42, 260, (255, 214, 40))
        return f

    def p_um_vida(self, t, d):
        m = self.liso((40, 40, 70), (20, 20, 40))
        m.alpha_composite(brilho((1000, 1000), (255, 210, 100), 500, 0.7 + 0.2 * math.sin(t * 5)), (40, 460))
        self.segura(m, self.env, 540, 1000, 380)
        f = camera(m, WW / 2, 960, 1.0 + 0.3 * ease_out(t / d))
        texto_pop(f, "1", self.fc, t, OUT_W / 2, OUT_H * 0.3, 300, (255, 214, 40))
        particulas(f, t, 30, semente=8)
        return f

    def p_vo_carteiro(self, t, d):
        m = self.cidade.copy()
        self.vo.desenhar(m, t, 540, 1760, escala=1.5, expr="feliz", pose="acena")
        f = camera(m, 540, 1250, 1.25 + 0.06 * ease_io(t / d))
        if t > 1.3:
            texto_pop(f, "52 ANOS", self.fc, t - 1.3, OUT_W / 2, OUT_H * 0.16, 110, (255, 214, 40))
        return f

    def p_vo_carta_branca(self, t, d):
        m = self.liso((200, 210, 230), (170, 180, 210))
        e = 2.0
        self.vo.desenhar(m, t, 470, 2050, escala=e, expr="neutro", pose="entrega")
        hx, hy = self.mao(470, 2050, e, t)
        self.segura(m, envelope(420, selo=False), hx + 40, hy - 60, 380, rot=8)
        return camera(m, 560, 1050, 1.1 + 0.08 * ease_io(t / d))

    def p_vo_bate(self, t, d):
        m = self.porta.copy()
        tb = (16.16 - 14.94, 16.50 - 14.94)
        batendo = any(0 <= t - x < 0.15 for x in tb)
        self.vo.desenhar(m, t, 220, 1700, escala=1.25, expr="feliz", pose="bate2" if batendo else "bate")
        f = camera(m, WW / 2 + (5 if batendo else 0), 1100, 1.1)
        for i, x in enumerate(tb):
            if t > x:
                texto_pop(f, "TOC" if i == 0 else "TOC!", self.fc, t - x, 480 + i * 70, 330 + i * 130, 100)
        return f

    def p_entrega(self, t, d):
        m = self.porta_ab.copy()
        e = 1.35
        self.vit.desenhar(m, t, 640, 1700, escala=1.25, expr="feliz", pose="idle", pulo=8 * abs(math.sin(t * 6)))
        self.vo.desenhar(m, t, 230, 1720, escala=e, expr="feliz", pose="entrega")
        hx, hy = self.mao(230, 1720, e, t)
        self.segura(m, self.env, hx + 50, hy - 20, 230, rot=-8)
        return camera(m, WW / 2, 1200, 1.12)

    def p_desenho(self, t, d):
        m = self.liso((255, 220, 180), (250, 190, 150))
        s = 0.6 + 0.4 * ease_out(t / 0.3)
        self.segura(m, self.desenho, 540, 950, 760 * s, rot=-4 + 2 * math.sin(t * 2))
        f = camera(m, WW / 2, 960, 1.05 + 0.05 * ease_io(t / d))
        particulas(f, t, 24, semente=6)
        return f

    def p_vo_confuso(self, t, d):
        m = self.liso((210, 205, 200), (180, 175, 170))
        self.vo_casa.desenhar(m, t, 540, 1800, escala=1.7, expr="triste")
        f = camera(m, 540, 1150, 1.2)
        for i, (x, y) in enumerate(((180, 300), (560, 250), (380, 170))):
            if t > 0.3 + i * 0.35:
                texto_pop(f, "?", self.fc, t - 0.3 - i * 0.35, x, y + 8 * math.sin(t * 4 + i), 120)
        return f

    def p_chaves(self, t, d):
        m = self.liso((200, 190, 180), (160, 150, 140))
        y = -200 + 1150 * ease_out(min(1, t / 0.5))
        k = Image.new("RGBA", self.chaves.size)
        k.alpha_composite(self.chaves)
        alpha = 1 - max(0, (t - 0.7) / 0.5)
        if alpha > 0:
            k.putalpha(k.getchannel("A").point(lambda v: int(v * max(0, alpha))))
            self.segura(m, k, 540, y, 600, rot=20 * math.sin(t * 2))
        return camera(m, WW / 2, 960, 1.1)

    def p_ruas(self, t, d):
        m = setas_confusas(t)
        self.vo_casa.desenhar(m, t, 540, 1700, escala=1.0, expr="triste", rot=4 * math.sin(t * 3))
        return camera(m, WW / 2, 1100, 1.05 + 0.15 * ease_io(t / d))

    def p_vo_close(self, t, d):
        m = self.liso((190, 185, 190), (150, 150, 160))
        self.vo_casa.desenhar(m, t, 540, 2600, escala=3.0, expr="neutro", piscar=False)
        return camera(m, 540, 1000, 1.0 + 0.15 * ease_io(t / d))

    def p_vitinho_choque(self, t, d):
        m = self.liso((190, 185, 190), (150, 150, 160))
        self.vit.desenhar(m, t, 540, 2500, escala=3.0, expr="surpreso")
        z = 1.0 + 0.35 * ease_out(t / 0.3)
        f = camera(m, 540, 900, z)
        if t < 0.1:
            f = Image.blend(f, Image.new("RGB", f.size, (255, 255, 255)), 0.6 * (1 - t / 0.1))
        return f

    def p_corre(self, t, d):
        off = (t * 900) % WW
        m = Image.new("RGBA", (WW, WH))
        m.alpha_composite(self.cidade, (int(-off), 0))
        m.alpha_composite(self.cidade, (int(WW - off), 0))
        passo = int(t * 8) % 2
        self.vit.desenhar(m, t, 540, 1760, escala=1.3, expr="triste", pose="acena" if passo else "idle",
                          rot=-8, pulo=25 * passo)
        f = camera(m, WW / 2, 1150, 1.15)
        f = motion_blur_h(f, 0)  # fundo já se move; linhas de velocidade:
        dr = ImageDraw.Draw(f)
        rng = random.Random(int(t * 10))
        for _ in range(8):
            y = rng.uniform(200, 1100)
            x = rng.uniform(0, OUT_W)
            dr.line((x, y, x + rng.uniform(80, 200), y), fill=(255, 255, 255), width=5)
        return f

    def p_balcao(self, t, d):
        m = self.correio.copy()
        self.moca.desenhar(m, t, 540, 1560, escala=1.25, expr="neutro")
        m.alpha_composite(self.balcao, (0, 1250))
        return camera(m, 540, 1100, 1.1 + 0.05 * ease_io(t / d))

    def p_moca_carta(self, t, d):
        m = self.correio.copy()
        e = 1.35
        self.moca.desenhar(m, t, 380, 1560, escala=e, expr="feliz", pose="entrega")
        m.alpha_composite(self.balcao, (0, 1250))
        hx, hy = self.mao(380, 1560, e, t)
        self.segura(m, self.env, hx + 40, hy - 10, 240, rot=-6)
        self.vit.desenhar(m, t, 850, 2050, escala=1.6, expr="surpreso" if t > 0.6 else "neutro")
        return camera(m, 560, 1200, 1.15)

    def p_envelope_nome(self, t, d):
        m = self.liso((250, 230, 200), (230, 200, 170))
        self.segura(m, self.env_nome, 540, 900, 760, rot=-2)
        return camera(m, WW / 2, 960, 1.0 + 0.12 * ease_out(t / d))

    def p_flashback(self, t, d):
        m = self.quarto.copy()
        self.vo_casa.desenhar(m, t, 450, 1560, escala=1.1, expr="triste", pose="entrega")
        hx, hy = self.mao(450, 1560, 1.1, t)
        p = Pincel(60, 60)            # caneta escrevendo
        p.ret((24, 0, 36, 60), (60, 60, 90), r=5, ow=4)
        caneta = p.pronto()
        m.alpha_composite(caneta, (int(hx + 6 * math.sin(t * 14)), int(hy - 40)))
        f = camera(m, 560, 1150, 1.15 + 0.05 * ease_io(t / d))
        if t > 0.35:
            texto_pop(f, "3 ANOS ANTES", self.fc, t - 0.35, OUT_W / 2, OUT_H * 0.14, 80, (255, 240, 200))
        return f

    def p_carta_lida(self, t, d):
        m = self.liso((240, 220, 190), (220, 190, 160))
        self.segura(m, self.carta, 540, 860 + 80 * (1 - ease_io(t / d)), 820, rot=2)
        return camera(m, WW / 2, 960, 1.0 + 0.08 * ease_io(t / d))

    def p_vo_lembra(self, t, d):
        m = self.liso((250, 210, 150), (230, 170, 120))
        m.alpha_composite(brilho((1000, 1000), (255, 230, 160), 500, 0.7), (40, 300))
        e = 1.8
        self.vo.desenhar(m, t, 470, 1950, escala=e, expr="feliz", pose="entrega")
        hx, hy = self.mao(470, 1950, e, t)
        self.segura(m, self.env, hx + 50, hy - 30, 300, rot=-6)
        f = camera(m, 540, 1100, 1.1 + 0.08 * ease_io(t / d))
        particulas(f, t, 30, semente=12)
        return f

    def p_vitinho_chora(self, t, d):
        m = self.liso((250, 200, 150), (230, 160, 120))
        m.alpha_composite(brilho((1000, 1000), (255, 220, 150), 500, 0.6), (40, 500))
        self.vit.desenhar(m, t, 540, 2350, escala=2.6, expr="chora", piscar=False)
        self.segura(m, self.env, 540, 1780, 420, rot=-4)
        f = camera(m, 540, 1000, 1.05 + 0.12 * ease_io(t / d))
        particulas(f, t, 30, semente=13)
        return f

    def p_vitinho_bate(self, t, d):
        m = self.porta.copy()
        tb = (0.08, 0.74)
        batendo = any(0 <= t - x < 0.15 for x in tb)
        self.vit_c.desenhar(m, t, 230, 1700, escala=1.25, expr="feliz", pose="bate2" if batendo else "bate")
        f = camera(m, WW / 2 + (5 if batendo else 0), 1100, 1.1)
        for i, x in enumerate(tb):
            if t > x:
                texto_pop(f, "TOC" if i == 0 else "TOC!", self.fc, t - x, 480 + i * 70, 330 + i * 130, 100)
        return f

    def p_entrega2(self, t, d):
        m = self.porta_ab.copy()
        e = 1.3
        self.vo_casa.desenhar(m, t, 690, 1720, escala=1.35, expr="neutro")
        self.vit_c.desenhar(m, t, 260, 1720, escala=e, expr="feliz", pose="entrega")
        hx, hy = self.mao(260, 1720, e, t)
        self.segura(m, self.env, hx + 50, hy - 20, 230, rot=-8)
        return camera(m, WW / 2, 1200, 1.12)

    def p_vo_sorri(self, t, d):
        m = self.porta_ab.copy()
        self.vo_casa.desenhar(m, t, 540, 2500, escala=2.6, expr="feliz" if t > 0.5 else "surpreso")
        f = camera(m, 540, 1000, 1.0 + 0.2 * ease_out(t / 0.5))
        if t > 0.5:
            particulas(f, t, 45, semente=21)
        return f

    def p_juntos(self, t, d):
        m = self.liso((255, 215, 170), (245, 180, 140))
        m.alpha_composite(brilho((1080, 1080), (255, 235, 180), 540, 0.6), (0, 500))
        self.vo_casa.desenhar(m, t, 340, 1760, escala=1.5, expr="ri" if int(t * 3) % 3 == 0 else "feliz")
        self.vit_c.desenhar(m, t, 760, 1760, escala=1.3, expr="feliz")
        self.segura(m, self.desenho, 540, 1350, 340, rot=4)
        f = camera(m, WW / 2, 1200, 1.12)
        particulas(f, t, 30, semente=22)
        return f

    def p_janela(self, t, d):
        m = self.janela.copy()
        self.vo_casa.desenhar(m, t, 540, 1700, escala=1.5, expr="feliz", pose="acena" if int(t * 2) % 2 else "idle")
        return camera(m, WW / 2, 1100, 1.05 + 0.08 * ease_io(t / d))

    def p_final(self, t, d):
        m = self.cidade_sol.copy()
        self.vit_c.desenhar(m, t, 540, 1760, escala=1.3, expr="feliz", pose="acena")
        f = camera(m, 540, 1200 - 150 * ease_io(t / d), 1.3 - 0.3 * ease_io(t / d))
        particulas(f, t, 40, semente=31)
        if t > d - 0.8:
            f = ImageEnhance.Brightness(f).enhance(1 - ease_io((t - (d - 0.8)) / 0.8))
        return f

    # ---------- montagem ----------
    def frame(self, n):
        t = n / FPS
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if t < ini + d or i == len(self.planos) - 1:
                tl = t - ini
                f = gradear(fn(tl, d), clima)
                T = 0.22
                if i > 0 and tl < T and tr != "corte":
                    pi, pd, pfn, pcl, _ = self.planos[i - 1]
                    prev = gradear(pfn(pd - 0.001, pd), pcl)
                    x = tl / T
                    if tr == "whip":
                        off = int(OUT_W * ease_io(x))
                        comp = Image.new("RGB", (OUT_W, OUT_H))
                        comp.paste(prev, (-off, 0))
                        comp.paste(f, (OUT_W - off, 0))
                        f = motion_blur_h(comp, 60 * math.sin(math.pi * x))
                    elif tr == "dissolve":
                        f = Image.blend(prev, f, ease_io(x))
                    elif tr == "zoom":
                        f = zoom_blur(Image.blend(prev, f, ease_io(x)), 0.35 * math.sin(math.pi * x))
                f = vinheta(f, 0.45 if clima in ("triste", "sepia") else 0.3)
                self.legenda(f, t)
                return f

    def eventos_sfx(self):
        ev = []
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if i and tr in ("whip", "zoom"):
                ev.append(("whoosh", ini - 0.08))
            elif i and tr == "corte":
                ev.append(("pop", ini))
        ev += [("toc", 16.16), ("toc", 16.50), ("toc", 51.74), ("toc", 52.40),
               ("brilho", 3.34 + 1.6), ("brilho", 55.56 + 0.5), ("brilho", 9.22)]
        return ev


# --------------------------------------------------------------------------
# Áudio: voz + trilha baixinha + SFX
# --------------------------------------------------------------------------
def ler_wav_mono(caminho):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", caminho, "-f", "s16le", "-ac", "1",
                          "-ar", str(g.SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def mixar(filme, narracao, saida):
    voz = ler_wav_mono(narracao)
    n = int(filme.dur_total * g.SR)
    mix = np.zeros(n, np.float32)
    mix[:min(n, len(voz))] += voz[:n] * 1.0
    musica = g.trilha(filme.dur_total)
    musica = musica / max(1e-6, np.abs(musica).max()) * 0.16
    mix[:len(musica)] += musica[:n]
    for tipo, t0 in filme.eventos_sfx():
        s = g.sfx(tipo) * (0.35 if tipo in ("whoosh", "pop") else 0.5)
        a = int(max(0, t0) * g.SR)
        b = min(n, a + len(s))
        mix[a:b] += s[: b - a]
    fade = int(g.SR * 0.8)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = mix / max(1.0, np.abs(mix).max() / 0.95)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(g.SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def carregar_palavras(caminho):
    pal = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            if (round(w["s"], 2), w["w"]) in REMOVER:
                continue
            txt = CORRECOES.get(w["w"], w["w"])
            if txt.startswith("vitinho"):
                txt = "V" + txt[1:]
            pal.append(dict(w=txt, s=w["s"], e=w["e"]))
    # "Amanhã era do meu vô" -> "Amanhã. Era do meu vô"
    for i, w in enumerate(pal):
        if w["w"] == "Amanhã" and i + 1 < len(pal) and pal[i + 1]["w"] == "era":
            w["w"], pal[i + 1]["w"] = "Amanhã.", "Era"
        if w["w"] == "pra" and i + 1 < len(pal) and pal[i + 1]["w"] == "mim,":
            w["w"], pal[i + 1]["w"] = "Pra", "mim."
        if w["w"] == "ele" and i > 0 and pal[i - 1]["w"] == "mim.":
            w["w"] = "Ele"
    return pal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_carta_do_vo.mp4"))
    ap.add_argument("--preview", default=None, help="pasta para salvar 1 frame por plano")
    a = ap.parse_args()

    voz_dur = len(ler_wav_mono(a.narracao)) / g.SR
    filme = Filme(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.2)
    total = int(filme.dur_total * FPS)

    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        for i, (ini, d, *_r) in enumerate(filme.planos):
            filme.frame(int((ini + d * 0.6) * FPS)).save(os.path.join(a.preview, f"plano_{i:02d}.png"))
        print("preview em", a.preview)
        return

    tmp = tempfile.mkdtemp(prefix="carta_")
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
