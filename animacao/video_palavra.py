#!/usr/bin/env python3
"""
"A Única Palavra" — nesse mundo você volta no tempo uma vez e só pode dizer uma palavra. Na rodoviária,
Lia (18) recusa mais um café com a mãe; a Lia de 78 anos sai de um portal e gasta a única palavra: "Fica."

Ritmo pedido pelo usuário: 13 cortes a cada 10 s (≈0,77 s por take) — gerar_video.CORTE_ALVO = 0.77.
Rig articulado, cenários novos (rodoviária de madrugada, portal azul, cozinha).

    python3 animacao/video_palavra.py --narracao narr.mp3 --transcricao transcricao.json --fonte Poppins.ttf
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
import video_azar as vz  # noqa: E402
import video_taxista as vt  # noqa: E402
import video_lagrima as vl  # noqa: E402
import cenarios as cen  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io, particulas, texto_pop)

g.CORTE_ALVO = 0.66      # 13 cortes a cada 10 segundos
g.CORTE_MIN = 0.45
g.PERMITE_FLIP = False   # há texto desenhado no cenário (placar, celular): não espelhar
random.seed(1313)

AZUL = (90, 170, 255)
LIA = dict(pele=(222, 170, 128), cabelo=(70, 45, 30), camisa=(250, 190, 70), calca=(60, 80, 130),
           sapato=(240, 240, 245), tipo="moca", vestido=(250, 190, 70))
LIA_V = dict(pele=(214, 160, 120), cabelo=(238, 238, 242), camisa=(120, 90, 170), calca=(0, 0, 0),
             sapato=(110, 80, 70), tipo="vovo", vestido=(120, 90, 170))
MAE = dict(pele=(222, 170, 128), cabelo=(140, 120, 110), camisa=(90, 160, 130), calca=(0, 0, 0),
           sapato=(80, 100, 90), tipo="moca", vestido=(90, 160, 130))
NETA = dict(pele=(222, 170, 128), cabelo=(60, 40, 30), camisa=(230, 120, 140), calca=(0, 0, 0),
            sapato=(90, 80, 90), tipo="moca", vestido=(230, 120, 140))
RICO = dict(pele=(232, 186, 150), cabelo=(60, 50, 45), camisa=(30, 30, 40), calca=(30, 30, 40),
            sapato=(20, 20, 24), tipo="pai", bigode=False, gravata=(250, 205, 70))
TIMIDO = dict(pele=(235, 190, 150), cabelo=(100, 60, 40), camisa=(120, 170, 220), calca=(70, 80, 110),
              sapato=(50, 50, 55), tipo="menino")
vc.DESTAQUE_VERMELHO = set()
_C = {}


# --------------------------------------------------------------------------
# Objetos / cenários
# --------------------------------------------------------------------------
def portal(m, cx, cy, r, t, abertura=1.0, alpha=1.0):
    """Portal de luz azul (anel + brilho + partículas)."""
    if abertura <= 0.02:
        return
    r = r * abertura
    glow = brilho((int(r * 4), int(r * 4)), AZUL, int(r * 2), 0.85 * alpha)
    m.alpha_composite(glow, (int(cx - r * 2), int(cy - r * 2)))
    p = Pincel(int(r * 2.4), int(r * 2.4))
    c = r * 1.2
    p.elipse((c - r * 0.55, c - r, c + r * 0.55, c + r), (200, 235, 255), ow=0)
    p.elipse((c - r * 0.42, c - r * 0.85, c + r * 0.42, c + r * 0.85), (70, 150, 255), ow=0)
    p.elipse((c - r * 0.30, c - r * 0.70, c + r * 0.30, c + r * 0.70), (230, 248, 255), ow=0)
    img = p.pronto()
    m.alpha_composite(img, (int(cx - c), int(cy - c)))
    d = ImageDraw.Draw(m)
    for i in range(14):
        a = t * 2 + i * 0.9
        x = cx + r * 0.7 * math.cos(a)
        y = cy + r * 0.95 * math.sin(a * 1.3)
        d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 255, 255, 230))


def relogio(w=420, hora="05:00", fc=None, cor=(250, 250, 255)):
    p = Pincel(420, 420)
    p.elipse((10, 10, 410, 410), cor, ow=10)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 70)
    d.text((210 - f.getlength(hora) / 2, 150), hora, font=f, fill=(40, 40, 60))
    return img if w == 420 else img.resize((w, w), Image.BICUBIC)


def relogio_ponteiros(m, cx, cy, r, ang_h, ang_m):
    d = ImageDraw.Draw(m)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(250, 250, 255, 255), outline=(43, 40, 58, 255), width=10)
    for i in range(12):
        a = math.radians(i * 30)
        d.line((cx + r * 0.82 * math.sin(a), cy - r * 0.82 * math.cos(a), cx + r * 0.94 * math.sin(a),
                cy - r * 0.94 * math.cos(a)), fill=(43, 40, 58, 255), width=8)
    for ang, L, w in ((ang_h, 0.5, 14), (ang_m, 0.78, 9)):
        a = math.radians(ang)
        d.line((cx, cy, cx + r * L * math.sin(a), cy - r * L * math.cos(a)), fill=(43, 40, 58, 255), width=w)
    d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=(43, 40, 58, 255))


def rodoviaria_noite(fc):
    base = cen.rodoviaria()
    base.alpha_composite(Image.new("RGBA", (WW, WH), (10, 14, 44, 150)))
    base.alpha_composite(brilho((900, 500), (200, 220, 255), 300, 0.4), (90, 200))
    p = Pincel(WW, WH)
    for x in (240, 540, 840):
        p.ret((x - 120, 1350, x + 120, 1400), (70, 76, 100), r=10)
        p.ret((x - 110, 1400, x - 90, 1500), (50, 54, 70), r=4, ow=0)
        p.ret((x + 90, 1400, x + 110, 1500), (50, 54, 70), r=4, ow=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 40)
    for i, (a, b) in enumerate((("CAPITAL", "05:00"), ("LITORAL", "05:40"), ("SERRA", "06:10"))):
        y = 276 + i * 48
        d.text((130, y), a, font=f, fill=(250, 210, 80))
        d.text((960 - f.getlength(b), y), b, font=f, fill=(120, 235, 140))
    return base


def cozinha_neta():
    base = va.cozinha()
    p = Pincel(WW, WH)
    p.ret((640, 1000, 840, 1300), (220, 170, 120), r=10)
    base.alpha_composite(p.pronto())
    return base


def mala(w=300):
    k = ("mala", w)
    if k not in _C:
        p = Pincel(300, 330)
        p.ret((30, 70, 270, 300), (180, 70, 70), r=24)
        p.ret((105, 20, 195, 80), (110, 40, 40), r=12, ow=6)
        p.ret((30, 150, 270, 170), (140, 50, 50), r=4, ow=0)
        p.elipse((60, 290, 100, 325), (40, 40, 50), ow=0)
        p.elipse((200, 290, 240, 325), (40, 40, 50), ow=0)
        img = p.pronto()
        _C[k] = img if w == 300 else img.resize((w, int(330 * w / 300)), Image.BICUBIC)
    return _C[k]


def garrafa_pao(w=260):
    k = ("gp", w)
    if k not in _C:
        p = Pincel(300, 300)
        p.ret((50, 70, 130, 270), (170, 90, 60), r=22)
        p.ret((60, 40, 120, 80), (60, 40, 30), r=10)
        p.ret((150, 170, 270, 260), (230, 180, 100), r=40)
        p.arco((170, 190, 250, 230), 200, 340, fill=(200, 140, 70), w=6)
        img = p.pronto()
        _C[k] = img if w == 300 else img.resize((w, w), Image.BICUBIC)
    return _C[k]


def xicara(w=260):
    k = ("xic", w)
    if k not in _C:
        p = Pincel(300, 300)
        p.ret((70, 110, 220, 250), (250, 250, 255), r=36)
        p.arco((200, 130, 270, 210), 270, 90, fill=(43, 40, 58), w=14)
        p.elipse((70, 100, 220, 140), (120, 70, 40), ow=6)
        img = p.pronto()
        _C[k] = img if w == 300 else img.resize((w, w), Image.BICUBIC)
    return _C[k]


def bengala(m, pers, by, e):
    hx, hy = pers.a.maos_mundo[1]
    d = ImageDraw.Draw(m)
    d.line((hx, hy, hx + 6 * e, by), fill=(43, 40, 58, 255), width=int(18 * e))
    d.line((hx, hy, hx + 6 * e, by), fill=(150, 100, 60, 255), width=int(10 * e))


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmePalavra(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.lia, self.liav, self.mae, self.neta = P_(LIA), P_(LIA_V), P_(MAE), P_(NETA)
        self.rico, self.timido = P_(RICO), P_(TIMIDO)
        self.povo = [P_(c) for c in ve.POVO]
        self.blur = {}
        self.rod = rodoviaria_noite(fc)
        self.coz = cozinha_neta()
        self.cidade = vz.ponto_dia()
        self.sala = va.sala()
        self.bus = __import__("video_mala").Onibus(fc)
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)

        P = [
            (0.00, self.p_hook, "", "corte"), (3.34, self.p_uma_palavra, "", "corte"),
            (5.86, self.p_rico, "", "whip"), (7.88, self.p_compra, "", "corte"),
            (10.10, self.p_vergonha, "", "whip"), (12.32, self.p_mensagem, "", "whip"),
            (14.58, self.p_erro, "", "whip"), (16.04, self.p_sai_portal, "", "whip"),
            (18.44, self.p_frente, "", "corte"), (21.92, self.p_rodoviaria, "frio", "dissolve"),
            (24.62, self.p_mala, "frio", "corte"), (26.64, self.p_onibus5, "frio", "whip"),
            (28.92, self.p_emprego, "frio", "corte"), (31.02, self.p_mae_vem, "frio", "whip"),
            (33.02, self.p_cafe_pao, "frio", "corte"), (35.08, self.p_fica_cafe, "frio", "corte"),
            (36.90, self.p_perco, "frio", "corte"), (38.70, self.p_depois, "frio", "corte"),
            (39.84, self.p_ar_abriu, "", "zoom"), (42.20, self.p_velha, "", "corte"),
            (44.06, self.p_bengala, "", "corte"), (45.82, self.p_olhos, "", "zoom"),
            (47.80, self.p_velha_assim, "", "corte"), (49.34, self.p_sorriu, "", "corte"),
            (50.46, self.p_molhados, "", "corte"), (52.40, self.p_sabia, "", "corte"),
            (53.14, self.p_so_uma, "", "corte"), (54.92, self.p_escolhendo, "", "corte"),
            (55.98, self.p_apaga, "", "whip"), (60.26, self.p_mimica, "", "whip"),
            (62.04, self.p_dinheiro, "", "corte"), (64.00, self.p_investir, "", "corte"),
            (65.32, self.p_aviao, "", "whip"), (67.08, self.p_viagem, "", "corte"),
            (69.32, self.p_xicara, "", "whip"), (72.22, self.p_cafe, "", "corte"),
            (72.86, self.p_voltou, "", "corte"), (75.40, self.p_apontou, "", "whip"),
            (78.54, self.p_entendi, "", "zoom"), (79.40, self.p_loteria, "", "corte"),
            (82.20, self.p_emprego_certo, "", "corte"), (83.86, self.p_milhoes, "", "corte"),
            (85.72, self.p_me_olhou, "", "zoom"), (87.18, self.p_palavra_dela, "", "corte"),
            (88.44, self.p_e_disse, "", "corte"), (89.18, self.p_fica, "", "zoom"),
            (89.88, self.p_parada, "", "corte"), (91.04, self.p_gastou, "", "corte"),
            (93.82, self.p_serio, "", "corte"), (94.60, self.p_fechou, "", "dissolve"),
            (95.58, self.p_sentei, "quente", "dissolve"), (97.36, self.p_tomamos, "quente", "corte"),
            (99.82, self.p_historias, "quente", "corte"), (102.26, self.p_onibus_foi, "", "whip"),
            (104.50, self.p_capital, "", "whip"), (106.54, self.p_emprego_ok, "", "corte"),
            (108.68, self.p_so_onibus, "", "corte"), (110.08, self.p_perdeu_cafe, "", "corte"),
            (112.48, self.p_derrame, "triste", "dissolve"), (114.70, self.p_ultima, "triste", "dissolve"),
            (119.48, self.p_mundo, "quente", "dissolve"), (123.18, self.p_atravessou, "quente", "dissolve"),
            (126.46, self.p_manha, "quente", "corte"), (129.18, self.p_78, "", "dissolve"),
            (131.52, self.p_nunca, "", "corte"), (133.66, self.p_nao_preciso, "", "corte"),
            (134.44, self.p_neta, "", "dissolve"), (136.24, self.p_mala_chao, "", "corte"),
            (138.38, self.p_neta_pede, "quente", "corte"), (140.60, self.p_fico, "quente", "corte"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))
        self.p_preto = None

    # ---------- utilidades ----------
    def txt(self, f, s, t0, y=0.1, tam=60, cor=(255, 255, 255)):
        if self.T >= t0:
            texto_pop(f, s, self.fc, self.T - t0, OUT_W / 2, OUT_H * y, tam, cor)

    def balao_t(self, f, txt, x, y, t0):
        if self.T >= t0:
            self.balao(f, txt, x, y, self.T - t0)

    def rod_cena(self, t, lia=None, mae=None, velha=None, mala_=True, portal_=0.0, z=1.12, cx=540):
        m = self.rod.copy()
        if portal_ > 0:
            portal(m, 780, 1330, 330, t, portal_)
        if mae:
            self.mae(m, t, 240, 1800, 1.15, expr=mae[0], pose=mae[1])
            m.alpha_composite(garrafa_pao(210), (330, 1560))
        if lia:
            self.lia(m, t, 560, 1800, 1.2, expr=lia[0], pose=lia[1])
            if mala_:
                m.alpha_composite(mala(200), (360, 1590))
        if velha:
            self.liav(m, t, 850, 1800, 1.2, expr=velha[0], pose=velha[1])
            bengala(m, self.liav, 1800, 1.2)
        return self.cam(m, cx, 1300, z)

    def cena_azul(self, t, bg=(10, 20, 60), c2=(40, 80, 160)):
        m = gradiente(WW, WH, bg, c2)
        portal(m, 540, 1000, 420, t)
        return m

    # ---------- planos ----------
    def p_hook(self, t, d):
        m = self.cena_azul(t)
        T = self.T
        relogio_ponteiros(m, 540, 1000, 300, -T * 200, -T * 2400)
        f = self.cam(m, 540, 1000, 1.0)
        self.txt(f, "UMA VIAGEM NO TEMPO", 0.9, 0.1, 54, (255, 255, 255))
        return f

    def p_uma_palavra(self, t, d):
        m = self.cena_azul(t)
        f = self.cam(m, 540, 1000, 1.0)
        self.txt(f, "1 PALAVRA", 3.5, 0.45, 96, (255, 214, 40))
        return f

    def p_rico(self, t, d):
        m = self.cidade.copy()
        for i, (p, x) in enumerate(zip((self.rico, self.povo[0], self.rico), (260, 560, 860))):
            p(m, t + i, x, 1800, 1.1, expr="feliz", pose="bracos_abertos")
            m.alpha_composite(vt.maco_dinheiro(200), (int(x - 100), int(1450 - 30 * abs(math.sin(t * 3 + i)))))
        f = self.cam(m, 540, 1300, 1.1)
        self.txt(f, "FICAR RICO", 6.9, 0.1, 80, (255, 214, 40))
        return f

    def p_compra(self, t, d):
        m = self.cidade.copy()
        self.rico(m, t, 540, 1800, 1.4, expr="ri", pose="aponta")
        for i in range(10):
            ph = (t * 0.8 + i * 0.1) % 1
            m.alpha_composite(vt.maco_dinheiro(150), (int(160 + i * 80), int(900 + ph * 800)))
        f = self.cam(m, 540, 1250, 1.1)
        self.txt(f, "\"COMPRA!\"", 7.88, 0.1, 100, (255, 214, 40))
        self.txt(f, "MILIONÁRIO", 8.88, 0.2, 70, (120, 235, 140))
        return f

    def p_vergonha(self, t, d):
        m = self.sala.copy()
        self.timido(m, t, 540, 1800, 1.4, expr="triste", pose="bolso")
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "VERGONHA", 11.06, 0.1, 90, (255, 130, 140))
        return f

    def p_mensagem(self, t, d):
        m = gradiente(WW, WH, (30, 30, 44), (14, 14, 24))
        c = vl.celular(self.fc, "Mensagem", "Tá com saudade?", 760)
        m.alpha_composite(c, (540 - c.width // 2, 600))
        f = self.cam(m, 540, 1100, 1.0 + 0.1 * ease_io(t / d))
        self.txt(f, "NÃO MANDAR", 12.88, 0.1, 80, (255, 130, 140))
        return f

    def p_erro(self, t, d):
        m = gradiente(WW, WH, (40, 30, 40), (18, 14, 20))
        p = Pincel(WW, WH)
        p.linha([(250, 700), (830, 1280)], fill=(235, 50, 60), w=90)
        p.linha([(830, 700), (250, 1280)], fill=(235, 50, 60), w=90)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 1000, 1.0 + 0.1 * ease_io(t / d))
        self.txt(f, "UM ERRO", 15.54, 0.12, 100, (255, 255, 255))
        return f

    def p_sai_portal(self, t, d):
        m = self.cena_azul(t)
        self.liav(m, t, 540, 1500, 0.9, expr="neutro", alpha=0.55 + 0.4 * ease_out(min(1, t / 1.0)))
        f = self.cam(m, 540, 1100, 1.0)
        self.txt(f, "SAI SEMPRE VOCÊ", 16.94, 0.1, 64, (255, 255, 255))
        return f

    def p_frente(self, t, d):
        m = self.cidade.copy()
        self.lia(m, t, 300, 1800, 1.2, expr="surpreso")
        self.liav(m, t, 780, 1800, 1.2, expr="feliz")
        bengala(m, self.liav, 1800, 1.2)
        f = self.cam(m, 540, 1300, 1.1)
        self.txt(f, "VOCÊ, MAIS VELHA", 19.18, 0.1, 62, (255, 214, 40))
        return f

    def p_rodoviaria(self, t, d):
        f = self.rod_cena(t, lia=("neutro", "idle"), z=1.1)
        self.txt(f, "18 ANOS", 22.04, 0.1, 100, (255, 214, 40))
        return f

    def p_mala(self, t, d):
        m = self.rod.copy()
        self.lia(m, t, 540, 1800, 1.4, expr="feliz", pose="entrega")
        m.alpha_composite(mala(260), (300, 1560))
        relogio_ponteiros(m, 840, 560, 120, 150, 300)
        f = self.cam(m, 540, 1300, 1.1)
        self.txt(f, "DE MADRUGADA", 24.74, 0.1, 64, (255, 255, 255))
        return f

    def p_onibus5(self, t, d):
        m = self.rod.copy()
        x = -400 + 900 * ease_out(min(1, t / 1.6))
        self.bus.desenhar(m, x, 1760, 0.85, farol=True)
        self.lia(m, t, 850, 1800, 1.2, expr="feliz")
        f = self.cam(m, 540, 1300, 1.1)
        self.txt(f, "ÔNIBUS DAS 5", 27.06, 0.1, 70, (255, 214, 40))
        return f

    def p_emprego(self, t, d):
        m = gradiente(WW, WH, (40, 50, 90), (20, 24, 50))
        self.lia(m, t, 400, 1800, 1.3, expr="feliz", pose="bracos_abertos")
        p = Pincel(WW, WH)
        p.ret((620, 900, 940, 1500), (90, 130, 200), r=10)
        for i in range(4):
            for j in range(3):
                p.ret((650 + j * 95, 940 + i * 130, 710 + j * 95, 1010 + i * 130), (255, 235, 150), r=6, ow=4)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 1250, 1.1)
        self.txt(f, "EMPREGO DOS SONHOS", 29.2, 0.1, 54, (255, 214, 40))
        return f

    def p_mae_vem(self, t, d):
        m = self.rod.copy()
        x = -100 + 400 * ease_io(min(1, t / 1.6))
        self.mae(m, t, x, 1800, 1.2, expr="feliz", pose="anda" if t < 1.6 else "acena")
        self.lia(m, t, 760, 1800, 1.2, expr="neutro")
        f = self.cam(m, 540, 1300, 1.1)
        self.txt(f, "A MINHA MÃE VEIO", 31.14, 0.1, 56, (255, 255, 255))
        return f

    def p_cafe_pao(self, t, d):
        m = self.rod.copy()
        self.mae(m, t, 360, 1800, 1.3, expr="feliz", pose="entrega")
        hx, hy = self.mae.a.maos_mundo[1]
        m.alpha_composite(garrafa_pao(280), (int(hx - 20), int(hy - 160)))
        self.lia(m, t, 780, 1800, 1.2, expr="neutro")
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "CAFÉ E PÃO", 33.88, 0.1, 80, (255, 214, 40))
        return f

    def p_fica_cafe(self, t, d):
        f = self.rod_cena(t, lia=("neutro", "idle"), mae=("feliz", "aponta"), z=1.15)
        self.balao_t(f, "Fica mais um café?", OUT_W * 0.35, OUT_H * 0.14, 35.08)
        return f

    def p_perco(self, t, d):
        m = self.rod.copy()
        self.lia(m, t, 540, 1800, 1.4, expr="triste", pose="aponta")
        relogio_ponteiros(m, 840, 560, 120, 150, 300)
        f = self.cam(m, 540, 1300, 1.1)
        self.balao_t(f, "Perco o ônibus.", OUT_W * 0.5, OUT_H * 0.14, 36.9)
        return f

    def p_depois(self, t, d):
        f = self.rod_cena(t, lia=("neutro", "bate"), mae=("triste", "idle"), z=1.15)
        self.balao_t(f, "Depois, mãe.", OUT_W * 0.55, OUT_H * 0.14, 38.7)
        return f

    def p_ar_abriu(self, t, d):
        k = ease_out(min(1, t / 1.4))
        return self.rod_cena(t, lia=("surpreso", "idle"), mae=("surpreso", "idle"), portal_=k, z=1.12)

    def p_velha(self, t, d):
        return self.rod_cena(t, lia=("surpreso", "idle"), mae=("surpreso", "idle"), velha=("feliz", "idle"),
                             portal_=1.0, z=1.12)

    def p_bengala(self, t, d):
        m = self.rod.copy()
        portal(m, 300, 1300, 300, t)
        self.liav(m, t, 600, 1800, 1.5, expr="feliz", pose="entrega")
        bengala(m, self.liav, 1800, 1.5)
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "BENGALA", 44.88, 0.1, 80, (255, 255, 255))
        return f

    def p_olhos(self, t, d):
        m = self.fundo_blur("rodn", self.rod)
        self.liav(m, t, 540, 2350, 2.5, expr="feliz")
        f = self.cam(m, 540, 950, 1.1)
        self.txt(f, "OS MEUS OLHOS", 46.46, 0.1, 70, (255, 255, 255))
        return f

    def p_velha_assim(self, t, d):
        f = self.rod_cena(t, lia=("surpreso", "bracos_abertos"), velha=("feliz", "idle"), portal_=1.0, z=1.15)
        self.balao_t(f, "Eu fiquei velha assim?", OUT_W * 0.4, OUT_H * 0.14, 47.96)
        return f

    def p_sorriu(self, t, d):
        m = self.fundo_blur("rodn", self.rod)
        self.liav(m, t, 540, 2350, 2.5, expr="feliz")
        return self.cam(m, 540, 950, 1.1)

    def p_molhados(self, t, d):
        m = self.fundo_blur("rodn", self.rod)
        self.liav(m, t, 540, 2350, 2.5, expr="chora")
        vl.lagrima(m, 540, 2350, 2.5, AZUL, t, getattr(self.liav.a, "ultimo_bob", 0.0))
        f = self.cam(m, 540, 950, 1.1)
        self.txt(f, "OLHOS MOLHADOS", 50.62, 0.1, 60, (255, 255, 255))
        return f

    def p_sabia(self, t, d):
        f = self.close(self.lia, t, self.rod, "rod", expr="neutro", z=1.05)
        return f

    def p_so_uma(self, t, d):
        m = self.cena_azul(t)
        f = self.cam(m, 540, 1000, 1.0)
        self.txt(f, "SÓ UMA PALAVRA", 53.28, 0.45, 80, (255, 214, 40))
        return f

    def p_escolhendo(self, t, d):
        m = self.fundo_blur("rodn", self.rod)
        self.liav(m, t, 540, 2350, 2.5, expr="neutro")
        f = self.cam(m, 540, 950, 1.1)
        self.txt(f, "ESCOLHENDO…", 54.96, 0.1, 80, (255, 255, 255))
        return f

    def p_apaga(self, t, d):
        m = self.cena_azul(t)
        f = self.cam(m, 540, 1000, 1.0)
        T = self.T
        for i, (w, ts) in enumerate((("PALAVRA", 57.38), ("FALADA", 58.86), ("ESCRITA", 59.62))):
            if T > ts:
                k = min(1, (T - ts) / 0.9)
                cor = (255, 214 - int(100 * k), 40 + int(100 * k))
                self.txt(f, w, ts, 0.38 + i * 0.09, int(70 * (1 - 0.3 * k)), cor)
        return f

    def p_mimica(self, t, d):
        m = self.rod.copy()
        portal(m, 300, 1300, 260, t)
        self.liav(m, t, 600, 1800, 1.4, expr="ri", pose="acena")
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "SÓ MÍMICA", 60.86, 0.1, 80, (255, 255, 255))
        return f

    def mimica_cena(self, t, icone, expr="feliz", pose="entrega"):
        m = self.rod.copy()
        self.liav(m, t, 360, 1800, 1.3, expr=expr, pose=pose)
        self.lia(m, t, 800, 1800, 1.2, expr="surpreso")
        if icone:
            icone(m)
        return self.cam(m, 540, 1300, 1.12)

    def p_dinheiro(self, t, d):
        def ic(m):
            hx, hy = self.liav.a.maos_mundo[1]
            m.alpha_composite(vt.maco_dinheiro(240), (int(hx - 20), int(hy - 160)))
        f = self.mimica_cena(t, ic)
        self.txt(f, "DINHEIRO", 63.08, 0.1, 80, (120, 235, 140))
        return f

    def p_investir(self, t, d):
        f = self.mimica_cena(t, None, expr="neutro", pose="bracos_abertos")
        self.balao_t(f, "Investir? Em quê?", OUT_W * 0.6, OUT_H * 0.14, 64.0)
        return f

    def p_aviao(self, t, d):
        def ic(m):
            x = 450 + 500 * ease_io(min(1, (self.T - 65.32) / 1.5))
            p = Pincel(300, 160)
            p.poli([(20, 80), (200, 60), (280, 80), (200, 100)], (250, 250, 255), ow=6)
            p.poli([(110, 70), (160, 10), (190, 70)], (200, 210, 235), ow=5)
            p.poli([(110, 90), (160, 150), (190, 90)], (200, 210, 235), ow=5)
            m.alpha_composite(p.pronto(), (int(x), 1000))
        f = self.mimica_cena(t, ic, pose="acena")
        self.txt(f, "AVIÃO", 66.24, 0.1, 90, (255, 255, 255))
        return f

    def p_viagem(self, t, d):
        f = self.mimica_cena(t, None, expr="neutro", pose="bracos_abertos")
        self.balao_t(f, "Eu vou viajar o mundo?", OUT_W * 0.55, OUT_H * 0.14, 67.78)
        return f

    def p_xicara(self, t, d):
        def ic(m):
            hx, hy = self.liav.a.maos_mundo[1]
            m.alpha_composite(xicara(240), (int(hx - 30), int(hy - 140)))
        f = self.mimica_cena(t, ic)
        self.txt(f, "UMA XÍCARA", 70.84, 0.1, 80, (255, 214, 40))
        return f

    def p_cafe(self, t, d):
        m = self.fundo_blur("rodn", self.rod)
        self.lia(m, t, 540, 2350, 2.5, expr="surpreso")
        f = self.cam(m, 540, 950, 1.1)
        self.txt(f, "CAFÉ?", 72.22, 0.1, 120, (255, 214, 40))
        return f

    def p_voltou(self, t, d):
        f = self.mimica_cena(t, None, expr="neutro", pose="idle")
        self.balao_t(f, "Voltou por um café?", OUT_W * 0.5, OUT_H * 0.14, 72.86)
        return f

    def p_apontou(self, t, d):
        m = self.rod.copy()
        self.liav(m, t, 780, 1800, 1.3, expr="feliz", pose="aponta")
        self.mae(m, t, 240, 1800, 1.2, expr="neutro", pose="idle")
        m.alpha_composite(garrafa_pao(220), (320, 1560))
        self.lia(m, t, 520, 1800, 1.1, expr="surpreso")
        return self.cam(m, 540, 1300, 1.12)

    def p_entendi(self, t, d):
        f = self.close(self.lia, t, self.rod, "rod", expr="surpreso", z=1.1)
        self.txt(f, "E EU ENTENDI", 78.72, 0.1, 64, (255, 255, 255))
        return f

    def p_loteria(self, t, d):
        m = gradiente(WW, WH, (40, 50, 90), (20, 24, 50))
        T = self.T
        n = "".join(str(random.Random(int(T * 6) * 7 + j).randint(0, 9)) for j in range(6))
        f = self.cam(m, 540, 1000, 1.0)
        self.txt(f, "NÚMERO DA LOTERIA", 80.12, 0.2, 48, (255, 255, 255))
        self.txt(f, n, 80.2, 0.4, 130, (255, 214, 40))
        return f

    def p_emprego_certo(self, t, d):
        m = gradiente(WW, WH, (40, 50, 90), (20, 24, 50))
        p = Pincel(WW, WH)
        p.ret((360, 800, 720, 1500), (90, 130, 200), r=10)
        for i in range(5):
            for j in range(3):
                p.ret((390 + j * 110, 840 + i * 120, 450 + j * 110, 910 + i * 120), (255, 235, 150), r=6, ow=4)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 1150, 1.0)
        self.txt(f, "O EMPREGO CERTO", 82.34, 0.1, 54, (255, 214, 40))
        return f

    def p_milhoes(self, t, d):
        m = gradiente(WW, WH, (40, 50, 90), (20, 24, 50))
        for i in range(14):
            ph = (t * 0.7 + i * 0.07) % 1
            m.alpha_composite(vt.maco_dinheiro(150), (int(80 + (i % 7) * 140), int(500 + ph * 1200)))
        f = self.cam(m, 540, 1000, 1.0)
        self.txt(f, "MILHÕES", 84.9, 0.12, 110, (120, 235, 140))
        return f

    def p_me_olhou(self, t, d):
        m = self.fundo_blur("rodn", self.rod)
        self.liav(m, t, 540, 2350, 2.5, expr="feliz")
        f = self.cam(m, 540, 950, 1.1)
        self.txt(f, "A PALAVRA DELA", 87.2, 0.1, 64, (255, 214, 40))
        return f

    def p_palavra_dela(self, t, d):
        m = self.cena_azul(t)
        f = self.cam(m, 540, 1000, 1.0)
        self.txt(f, "?", 87.5, 0.4, 260, (255, 214, 40))
        return f

    def p_e_disse(self, t, d):
        m = self.fundo_blur("rodn", self.rod)
        self.liav(m, t, 540, 2350, 2.5, expr="fala")
        return self.cam(m, 540, 950, 1.15)

    def p_fica(self, t, d):
        m = self.cena_azul(t)
        f = self.cam(m, 540, 1000, 1.0 + 0.2 * ease_out(min(1, t / 0.5)))
        self.txt(f, "FICA.", 89.18, 0.4, 220, (255, 255, 255))
        return f

    def p_parada(self, t, d):
        f = self.close(self.lia, t, self.rod, "rod", expr="surpreso", z=1.1)
        return f

    def p_gastou(self, t, d):
        f = self.rod_cena(t, lia=("surpreso", "bracos_abertos"), velha=("feliz", "idle"), portal_=1.0, z=1.15)
        self.balao_t(f, "Gastou a palavra nisso?", OUT_W * 0.4, OUT_H * 0.14, 91.16)
        return f

    def p_serio(self, t, d):
        f = self.close(self.lia, t, self.rod, "rod", expr="bravo", z=1.1)
        self.balao_t(f, "Sério?", OUT_W / 2, OUT_H * 0.16, 93.82)
        return f

    def p_fechou(self, t, d):
        k = 1 - ease_out(min(1, t / 0.9))
        return self.rod_cena(t, lia=("neutro", "idle"), mae=("neutro", "idle"), portal_=k, z=1.1)

    def p_sentei(self, t, d):
        m = self.rod.copy()
        m.alpha_composite(brilho((900, 900), (255, 220, 150), 420, 0.35), (90, 900))
        self.mae(m, t, 380, 1800, 1.3, expr="feliz", pose="idle")
        self.lia(m, t, 700, 1800, 1.3, expr="feliz", pose="idle")
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "FIQUEI COM ELA", 95.78, 0.1, 54, (255, 255, 255))
        return f

    def p_tomamos(self, t, d):
        m = self.rod.copy()
        m.alpha_composite(brilho((900, 900), (255, 220, 150), 420, 0.35), (90, 900))
        self.mae(m, t, 380, 1800, 1.3, expr="ri", pose="entrega")
        self.lia(m, t, 700, 1800, 1.3, expr="ri", pose="entrega")
        for p_ in (self.mae, self.lia):
            hx, hy = p_.a.maos_mundo[1]
            m.alpha_composite(xicara(150), (int(hx - 40), int(hy - 90)))
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "O CAFÉ INTEIRO", 98.1, 0.1, 62, (255, 214, 40))
        return f

    def p_historias(self, t, d):
        m = self.rod.copy()
        self.mae(m, t, 380, 1800, 1.3, expr="ri", pose="acena")
        self.lia(m, t, 700, 1800, 1.3, expr="ri")
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "HISTÓRIAS DE PEQUENA", 100.44, 0.1, 50, (255, 255, 255))
        return f

    def p_onibus_foi(self, t, d):
        m = self.rod.copy()
        self.bus.desenhar(m, 540 + 1100 * (t / d) ** 2, 1760, 0.85, giro=t * 500, farol=True)
        self.lia(m, t, 300, 1800, 1.2, expr="ri")
        f = self.cam(m, 540, 1300, 1.1)
        self.txt(f, "O ÔNIBUS FOI EMBORA", 102.36, 0.1, 50, (255, 255, 255))
        return f

    def p_capital(self, t, d):
        m = self.cidade.copy()
        x = -100 + 600 * ease_out(min(1, t / 1.6))
        self.lia(m, t, x, 1800, 1.3, expr="feliz", pose="anda")
        m.alpha_composite(mala(200), (int(x + 120), 1600))
        f = self.cam(m, 540, 1300, 1.1)
        self.txt(f, "NO DIA SEGUINTE", 105.36, 0.1, 54, (255, 255, 255))
        return f

    def p_emprego_ok(self, t, d):
        m = self.cidade.copy()
        self.lia(m, t, 540, 1800, 1.4, expr="feliz", pose="bracos_abertos")
        f = self.cam(m, 540, 1300, 1.1)
        self.txt(f, "O EMPREGO ESTAVA LÁ", 106.64, 0.1, 48, (120, 235, 140))
        return f

    def p_so_onibus(self, t, d):
        f = self.close(self.lia, t, self.cidade, "cid", expr="neutro", z=1.1)
        self.txt(f, "SÓ PERDI UM ÔNIBUS", 108.82, 0.1, 50, (255, 255, 255))
        return f

    def p_perdeu_cafe(self, t, d):
        m = self.fundo_blur("rodn", self.rod)
        self.liav(m, t, 540, 2350, 2.5, expr="triste")
        f = self.cam(m, 540, 950, 1.1)
        self.txt(f, "ELA PERDEU UM CAFÉ", 110.36, 0.1, 50, (255, 130, 140))
        return f

    def p_derrame(self, t, d):
        m = self.coz.copy()
        m.alpha_composite(Image.new("RGBA", (WW, WH), (10, 10, 30, 120)))
        self.lia(m, t, 700, 1800, 1.3, expr="chora", pose="idle")
        p = Pincel(WW, WH)
        p.ret((200, 1450, 420, 1700), (150, 100, 70), r=10)
        m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "UM MÊS DEPOIS", 112.66, 0.1, 60, (255, 255, 255))
        return f

    def p_ultima(self, t, d):
        m = self.rod.copy()
        m.alpha_composite(brilho((900, 900), (255, 220, 150), 420, 0.35), (90, 900))
        self.mae(m, t, 380, 1800, 1.3, expr="feliz", pose="acena", alpha=0.85)
        self.lia(m, t, 700, 1800, 1.3, expr="triste", pose="idle")
        m.alpha_composite(garrafa_pao(220), (460, 1560))
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "A ÚLTIMA VEZ EM PÉ", 114.98, 0.1, 50, (255, 255, 255))
        return f

    def p_mundo(self, t, d):
        m = self.rod.copy()
        m.alpha_composite(brilho((900, 900), (255, 220, 150), 420, 0.35), (90, 900))
        self.mae(m, t, 380, 1800, 1.3, expr="feliz", pose="idle")
        self.lia(m, t, 700, 1800, 1.3, expr="feliz", pose="bracos_abertos")
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "UM MUNDO PELA FRENTE", 121.46, 0.1, 44, (255, 214, 40))
        return f

    def p_atravessou(self, t, d):
        m = self.cena_azul(t)
        self.liav(m, t, 540, 1700, 1.0, expr="feliz")
        bengala(m, self.liav, 1700, 1.0)
        f = self.cam(m, 540, 1100, 1.0)
        self.txt(f, "ATRAVESSOU O TEMPO", 123.68, 0.1, 54, (255, 255, 255))
        return f

    def p_manha(self, t, d):
        m = self.rod.copy()
        m.alpha_composite(brilho((900, 900), (255, 220, 150), 420, 0.5), (90, 900))
        self.mae(m, t, 380, 1800, 1.3, expr="ri")
        self.lia(m, t, 700, 1800, 1.3, expr="ri")
        f = self.cam(m, 540, 1300, 1.12)
        self.txt(f, "A MELHOR MANHÃ DA MINHA VIDA", 127.2, 0.1, 38, (255, 214, 40))
        return f

    def p_78(self, t, d):
        m = self.coz.copy()
        self.liav(m, t, 540, 1800, 1.4, expr="feliz", pose="idle")
        bengala(m, self.liav, 1800, 1.4)
        f = self.cam(m, 540, 1250, 1.12)
        self.txt(f, "78 ANOS", 129.76, 0.1, 100, (255, 214, 40))
        return f

    def p_nunca(self, t, d):
        m = self.coz.copy()
        self.liav(m, t, 540, 1800, 1.4, expr="neutro", pose="idle")
        bengala(m, self.liav, 1800, 1.4)
        p = Pincel(300, 300)
        m2 = m
        portal(m2, 840, 1100, 160, t, 1.0, 0.5)
        f = self.cam(m2, 540, 1250, 1.12)
        self.txt(f, "NUNCA USEI", 132.9, 0.1, 80, (255, 255, 255))
        return f

    def p_nao_preciso(self, t, d):
        f = self.close(self.liav, t, self.coz, "coz", expr="feliz", z=1.1)
        self.txt(f, "NÃO PRECISO", 133.72, 0.1, 80, (255, 214, 40))
        return f

    def p_neta(self, t, d):
        m = self.coz.copy()
        x = 1150 - 450 * ease_out(min(1, t / 1.4))
        self.neta(m, t, x, 1800, 1.2, expr="neutro", pose="anda" if t < 1.4 else "idle", sx=-1)
        self.liav(m, t, 300, 1800, 1.3, expr="feliz")
        bengala(m, self.liav, 1800, 1.3)
        return self.cam(m, 540, 1250, 1.1)

    def p_mala_chao(self, t, d):
        m = self.coz.copy()
        self.neta(m, t, 740, 1800, 1.3, expr="triste", pose="idle")
        m.alpha_composite(mala(240), (500, 1580))
        self.liav(m, t, 280, 1800, 1.3, expr="feliz")
        bengala(m, self.liav, 1800, 1.3)
        return self.cam(m, 540, 1250, 1.12)

    def p_neta_pede(self, t, d):
        m = self.coz.copy()
        self.neta(m, t, 740, 1800, 1.3, expr="feliz", pose="entrega")
        self.liav(m, t, 280, 1800, 1.3, expr="surpreso")
        bengala(m, self.liav, 1800, 1.3)
        f = self.cam(m, 540, 1250, 1.12)
        self.balao_t(f, "Vó, fica mais um café?", OUT_W * 0.55, OUT_H * 0.14, 138.82)
        return f

    def p_fico(self, t, d):
        m = self.coz.copy()
        m.alpha_composite(brilho((900, 900), (255, 220, 150), 420, 0.5), (90, 700))
        self.neta(m, t, 740, 1800, 1.3, expr="ri", pose="idle")
        self.liav(m, t, 280, 1800, 1.3, expr="ri", pose="abraca_d")
        f = self.cam(m, 540, 1250, 1.12 + 0.08 * ease_io(t / d))
        self.txt(f, "\"FICO.\"", 140.6, 0.1, 110, (255, 214, 40))
        k = max(0, (t - (d - 1.2)) / 1.2)
        if k > 0:
            f = Image.blend(f, Image.new("RGB", f.size, (0, 0, 0)), min(1, k))
        return f


# --------------------------------------------------------------------------
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
    ev += [("brilho", 0.2), ("brilho", 3.5), ("brilho", 16.04), ("brilho", 39.84), ("brilho", 89.18),
           ("brilho", 94.6), ("toc", 112.66), ("brilho", 140.6)]
    for tipo, t0 in ev:
        s = g.sfx(tipo) * (0.3 if tipo in ("whoosh", "pop") else 0.8)
        a = int(max(0, t0) * SR)
        b = min(n, a + len(s))
        mix[a:b] += s[: b - a]
    fade = int(SR * 1.0)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = mix / max(1.0, np.abs(mix).max() / 0.95)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def carregar_palavras(caminho):
    troca = {"18": "18", "5": "5"}
    out = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            out.append(dict(w=troca.get(w["w"], w["w"]), s=w["s"], e=w["e"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_a_unica_palavra.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmePalavra(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.4, a.narracao)
    total = int(filme.dur_total * FPS)

    if a.testar:
        for ini, d, *_r in filme.planos:
            for k in (0.01, 0.5, 0.99):
                filme.frame(int((ini + d * k) * FPS))
        filme.frame(0)
        n_cortes = len(filme.cortes)
        print(f"todos os planos ok — {n_cortes} cortes em {filme.dur_total:.1f}s "
              f"= {n_cortes / filme.dur_total * 10:.1f} cenas a cada 10 s")
        return
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        filme.frame(0)
        ts = [c for c, _ in filme.cortes] + [filme.dur_total]
        for i, (x, y) in enumerate(zip(ts, ts[1:])):
            filme.frame(int((x + y) / 2 * FPS)).save(os.path.join(a.preview, f"take_{i:03d}.png"))
        print("preview em", a.preview, len(ts) - 1, "takes")
        return

    tmp = tempfile.mkdtemp(prefix="palavra_")
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
