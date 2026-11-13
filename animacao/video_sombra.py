#!/usr/bin/env python3
"""
"A Sombra do Vitinho" — vídeo sincronizado com a narração do ElevenLabs.

Mesmo pipeline do video_carta.py:
    python3 animacao/remover_silencios.py narracao.mp3 narr.wav
    (faster-whisper -> transcricao.json)
    python3 animacao/video_sombra.py --narracao narr.wav --transcricao transcricao.json --fonte Poppins.ttf
"""
import argparse
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
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, Ator, gradiente, brilho,
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(21)

VITINHO = vc.VITINHO
PAI = dict(pele=(206, 150, 110), cabelo=(50, 36, 30), camisa=(240, 125, 40), calca=(225, 110, 35),
           sapato=(50, 45, 45), tipo="pai", chapeu=(235, 115, 35), faixas=True)
PAI_CASA = dict(PAI, chapeu=None, faixas=False, camisa=(120, 140, 170), calca=(70, 80, 110))
PROF = vc.MOCA
COLEGAS = [
    dict(pele=(150, 100, 70), cabelo=(30, 25, 25), camisa=(240, 200, 70), calca=(60, 80, 140),
         sapato=(200, 60, 60), tipo="menino"),
    dict(pele=(235, 190, 150), cabelo=(220, 160, 60), camisa=(170, 120, 200), calca=(0, 0, 0),
         sapato=(120, 60, 120), tipo="moca", vestido=(190, 140, 220)),
    dict(pele=(190, 130, 90), cabelo=(60, 40, 30), camisa=(120, 190, 110), calca=(90, 70, 60),
         sapato=(60, 60, 60), tipo="menino"),
]

CORRECOES = {"varreira": "varrer", "4": "quatro", "disse,": "disse:", "Pai,": "Pai,"}
vc.DESTAQUE_VERMELHO = {"mentira,", "vergonha.", "nada.", "sombra.", "mente?", "gari.", "forte"}


# --------------------------------------------------------------------------
# Sombras: silhueta do sprite deitada no chão (sol vindo da esquerda)
# --------------------------------------------------------------------------
_CACHE_SIL = {}


def silhueta(spr):
    k = id(spr)
    if k not in _CACHE_SIL:
        a = np.asarray(spr.getchannel("A"), np.float32)
        arr = np.zeros(a.shape + (4,), np.uint8)
        arr[..., 0], arr[..., 1], arr[..., 2] = 30, 30, 60
        arr[..., 3] = (a * 0.42).astype(np.uint8)
        _CACHE_SIL[k] = Image.fromarray(arr, "RGBA").transpose(Image.FLIP_TOP_BOTTOM)
    return _CACHE_SIL[k]


def sombra(base, spr, cx, by, escala, tam, incl=2.1):
    """Desenha a sombra projetada de um sprite. tam=1 sombra normal; 0 = sem sombra."""
    if tam <= 0.02:
        return
    sil = silhueta(spr)
    w = max(1, int(sil.width * escala * min(1.0, 0.35 + 0.65 * tam)))
    h = max(1, int(sil.height * escala * 0.24 * tam))
    s = sil.resize((w, h), Image.BICUBIC)
    extra = int(h * incl)
    s = s.transform((w + extra, h), Image.AFFINE, (1, -incl, 0, 0, 1, 0), resample=Image.BICUBIC)
    base.alpha_composite(s, (int(cx - w / 2), int(by - 12 * escala)))


def puf(img, t, x, y, tam=1.0):
    """Nuvenzinha de fumaça quando a sombra encolhe."""
    if not 0 <= t < 0.45:
        return
    k = t / 0.45
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(6):
        a = i * 60 + 20
        r = (14 + 26 * k) * tam
        px = x + math.cos(math.radians(a)) * 40 * k * tam
        py = y + math.sin(math.radians(a)) * 22 * k * tam
        d.ellipse((px - r, py - r, px + r, py + r), fill=(240, 240, 245, int(220 * (1 - k))))


# --------------------------------------------------------------------------
# Objetos e cenários
# --------------------------------------------------------------------------
def vassoura():
    p = Pincel(200, 760)
    p.ret((88, 20, 112, 560), (190, 140, 80), r=10)
    p.poli([(50, 560), (150, 560), (190, 740), (10, 740)], (240, 200, 90))
    for x in range(30, 180, 22):
        p.linha([(100 + (x - 100) * 0.55, 580), (x, 730)], fill=(200, 160, 60), w=4)
    p.ret((60, 540, 140, 580), (200, 60, 50), r=8)
    return p.pronto()


def mini(desenho):
    """Conteúdo de balão de pensamento (380x300)."""
    p = Pincel(380, 300)
    desenho(p)
    return p.pronto()


def m_aviao(p):
    p.ret((0, 0, 380, 300), (150, 205, 245), r=0, ow=0)
    vc.nuvem(p, 40, 220, 0.5)
    p.ret((60, 130, 330, 180), (250, 250, 255), r=25)
    p.poli([(160, 140), (240, 140), (170, 60)], (220, 70, 70))
    p.poli([(160, 170), (240, 170), (170, 250)], (220, 70, 70))
    p.poli([(70, 140), (110, 140), (70, 90)], (220, 70, 70))
    for x in (200, 240, 280):
        p.elipse((x, 145, x + 18, 163), (120, 180, 230), ow=4)


def m_piscina(p):
    p.ret((0, 0, 380, 300), (150, 210, 130), r=0, ow=0)
    p.ret((40, 80, 340, 250), (90, 190, 240), r=30)
    for y in (130, 180):
        p.arco((70, y - 20, 170, y + 20), 200, 340, fill=(220, 245, 255), w=6)
        p.arco((200, y - 20, 300, y + 20), 200, 340, fill=(220, 245, 255), w=6)
    p.elipse((290, 30, 350, 90), (255, 210, 60), ow=0)


def m_praia(p):
    p.ret((0, 0, 380, 300), (140, 200, 245), r=0, ow=0)
    p.ret((0, 170, 380, 300), (90, 170, 230), r=0, ow=0)
    p.ret((0, 230, 380, 300), (245, 220, 160), r=0, ow=0)
    p.elipse((250, 40, 330, 120), (255, 210, 60), ow=0)
    p.capsula((90, 250), (110, 120), 14, (140, 90, 50), ow=4)
    for a in (-60, -20, 20, 60):
        p.capsula((110, 120), (110 + 70 * math.sin(math.radians(a)), 120 - 30 * math.cos(math.radians(a))),
                  16, (80, 170, 80), ow=4)


def m_carro(p):
    p.ret((0, 0, 380, 300), (230, 230, 240), r=0, ow=0)
    p.ret((40, 140, 340, 220), (220, 50, 50), r=24)
    p.poli([(100, 145), (140, 90), (260, 90), (300, 145)], (220, 50, 50))
    p.ret((150, 100, 250, 140), (180, 220, 245), r=6, ow=5)
    for x in (100, 280):
        p.elipse((x - 32, 190, x + 32, 254), (50, 50, 60))
        p.elipse((x - 12, 210, x + 12, 234), (200, 200, 210), ow=0)


def sala_aula(fc):
    base = gradiente(WW, WH, (240, 225, 200), (225, 205, 180))
    p = Pincel(WW, WH)
    p.ret((120, 260, 960, 780), (50, 100, 80), r=10, ow=14)
    p.ret((110, 780, 970, 810), (170, 120, 80), r=6)
    p.ret((-20, 1400, WW + 20, WH + 20), (180, 140, 100), r=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 64)
    t = "PROFISSÕES"
    d.text((540 - f.getlength(t) / 2, 470), t, font=f, fill=(240, 240, 230))
    return base


def carteiras():
    p = Pincel(WW, 500)
    for x in (40, 390, 740):
        p.ret((x, 60, x + 300, 130), (200, 150, 100), r=10)
        p.ret((x + 20, 130, x + 280, 500), (180, 130, 85), r=8)
    return p.pronto()


def quarto_dia():
    base = gradiente(WW, WH, (200, 215, 240), (180, 195, 225))
    p = Pincel(WW, WH)
    p.ret((640, 300, 960, 700), (170, 215, 245), r=10, ow=10)
    p.linha([(800, 300), (800, 700)], w=10)
    p.ret((-20, 1450, WW + 20, WH + 20), (160, 130, 110), r=0)
    p.ret((60, 1150, 1020, 1500), (120, 150, 210), r=30)        # cama
    p.ret((60, 1040, 340, 1200), (250, 250, 255), r=30)          # travesseiro
    p.ret((40, 1000, 90, 1650), (150, 100, 70), r=12)
    p.ret((990, 1100, 1040, 1650), (150, 100, 70), r=12)
    base.alpha_composite(p.pronto())
    return base


def cobertor():
    p = Pincel(WW, 600)
    p.ret((80, 60, 1010, 420), (90, 130, 200), r=40)
    for x in range(140, 1000, 120):
        p.linha([(x, 70), (x, 410)], fill=(110, 150, 215), w=10)
    return p.pronto()


def palco(fc):
    base = gradiente(WW, WH, (50, 30, 50), (30, 20, 35))
    p = Pincel(WW, WH)
    p.ret((-20, 1350, WW + 20, WH + 20), (150, 100, 60), r=0)
    for x in range(-20, WW, 90):
        p.linha([(x, 1350), (x - 30, WH)], fill=(130, 85, 50), w=5)
    for lado in (0, 1):
        x0 = -40 if lado == 0 else WW - 260
        p.ret((x0, -20, x0 + 300, 1400), (180, 30, 50), r=20)
        for k in range(5):
            xx = x0 + 30 + k * 55
            p.linha([(xx, 0), (xx, 1390)], fill=(150, 20, 40), w=10)
    p.ret((-20, -20, WW + 20, 160), (160, 25, 45), r=0)
    p.ret((240, 200, 840, 300), (250, 230, 150), r=14)
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((900, 1400), (255, 240, 200), 600, 0.55), (90, 450))
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 46)
    t = "FEIRA DE PROFISSÕES"
    d.text((540 - f.getlength(t) / 2, 222), t, font=f, fill=(170, 40, 60))
    return base


def microfone():
    p = Pincel(200, 900)
    p.ret((92, 120, 108, 860), (70, 70, 80), r=6)
    p.ret((30, 850, 170, 880), (70, 70, 80), r=10)
    p.elipse((70, 40, 130, 130), (60, 60, 70))
    return p.pronto()


def plateia(t):
    p = Pincel(WW, 520)
    rng = random.Random(3)
    for fila in range(2):
        for i in range(8):
            x = i * 150 + (75 if fila else 0) - 30
            y = 120 + fila * 160 + 6 * math.sin(t * 6 + i + fila)
            p.elipse((x, y, x + 150, y + 170), (25, 20, 30), ow=0)
            p.ret((x - 20, y + 150, x + 170, y + 400), (25, 20, 30), r=60, ow=0)
    return p.pronto()


def cozinha():
    base = gradiente(WW, WH, (250, 225, 170), (235, 200, 150))
    p = Pincel(WW, WH)
    for y in range(400, 1100, 90):
        for x in range(0, WW, 90):
            p.ret((x + 4, y + 4, x + 86, y + 86), (240, 235, 220), r=6, ow=0)
    p.ret((-20, 1450, WW + 20, WH + 20), (170, 120, 90), r=0)
    base.alpha_composite(p.pronto())
    return base


def mesa_pratos():
    p = Pincel(WW, 520)
    p.ret((40, 60, WW - 40, 150), (180, 110, 70), r=16)
    p.ret((90, 150, 140, 520), (150, 90, 60), r=10)
    p.ret((WW - 140, 150, WW - 90, 520), (150, 90, 60), r=10)
    for x, cheio in ((300, False), (780, True)):
        p.elipse((x - 130, 20, x + 130, 100), (250, 250, 250))
        if cheio:
            p.elipse((x - 90, 10, x + 10, 70), (250, 240, 200), ow=4)      # arroz
            p.elipse((x - 10, 14, x + 80, 72), (130, 70, 40), ow=4)        # feijão
            p.elipse((x - 40, 40, x + 30, 80), (240, 120, 60), ow=4)       # cenoura
    return p.pronto()


def degrau():
    p = Pincel(WW, 400)
    p.ret((-20, 40, WW + 20, 400), (190, 180, 170), r=0)
    p.ret((-20, 40, WW + 20, 80), (210, 200, 190), r=0)
    return p.pronto()


def rua_madrugada(fc):
    base = gradiente(WW, WH, (40, 50, 90), (120, 100, 140))
    p = Pincel(WW, WH)
    p.ret((150, 700, 930, 1400), (220, 200, 150), r=8)
    p.ret((120, 650, 960, 730), (90, 120, 170), r=10)
    p.ret((300, 760, 780, 860), (250, 245, 230), r=10)
    for jx in (220, 420, 620, 800):
        p.ret((jx, 920, jx + 100, 1060), (70, 80, 120), r=8)
    p.ret((-20, 1390, WW + 20, 1500), (170, 165, 165), r=0)
    p.ret((-20, 1500, WW + 20, WH + 20), (70, 70, 85), r=0)
    p.ret((960, 900, 984, 1400), (60, 60, 80), r=6)
    p.elipse((936, 860, 1008, 930), (255, 230, 150))
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((500, 500), (255, 220, 140), 250, 0.5), (720, 645))
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 60)
    d.text((540 - f.getlength("ESCOLA") / 2, 775), "ESCOLA", font=f, fill=(60, 90, 150))
    return base


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeSombra(vc.Filme):
    def __init__(self, palavras, fc, dur_total):  # noqa: C901 (lista de planos)
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.vit, self.pai, self.pai_c = Ator(VITINHO), Ator(PAI), Ator(PAI_CASA)
        self.prof = Ator(PROF)
        self.colegas = [Ator(c) for c in COLEGAS]
        self.rua = vc.cidade_dia(fc, placa="ESCOLA MUNICIPAL")
        self.rua_sol = vc.cidade_dia(fc, por_do_sol=True, placa="ESCOLA MUNICIPAL")
        self.madrugada = rua_madrugada(fc)
        self.sala = sala_aula(fc)
        self.carteiras = carteiras()
        self.quarto = quarto_dia()
        self.cobertor = cobertor()
        self.palco = palco(fc)
        self.mic = microfone()
        self.cozinha = cozinha()
        self.mesa = mesa_pratos()
        self.degrau = degrau()
        self.porta = g.cenario_porta()
        self.vass = vassoura()
        self.bal_aviao = g.balao_pensamento(mini(m_aviao).convert("RGB"))
        self.bal_pisc = g.balao_pensamento(mini(m_piscina).convert("RGB"))
        self.bal_praia = g.balao_pensamento(mini(m_praia).convert("RGB"))
        self.bal_carro = g.balao_pensamento(mini(m_carro).convert("RGB"))
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        # tamanho da sombra do Vitinho ao longo da história (mentiras = degraus)
        self.mentiras = [15.52, 19.06, 20.82, 22.46]

        P = [
            (0.00, self.p_rua_sombra, "", "corte"),
            (3.20, self.p_encolhe_demo, "", "whip"),
            (5.54, self.p_todos, "", "corte"),
            (7.52, self.p_chao, "", "corte"),
            (8.52, self.p_comecei, "", "whip"),
            (10.48, self.p_escola, "", "corte"),
            (12.98, self.p_piloto, "", "corte"),
            (14.88, self.p_encolheu, "", "corte"),
            (16.62, self.p_ninguem, "", "corte"),
            (17.68, self.p_bal(self.bal_pisc), "", "whip"),
            (19.84, self.p_bal(self.bal_praia), "", "corte"),
            (21.42, self.p_bal(self.bal_carro), "", "corte"),
            (23.26, self.p_pedacos, "", "corte"),
            (25.48, self.p_verdade, "", "whip"),
            (27.42, self.p_madrugada, "", "dissolve"),
            (31.00, self.p_vergonha, "triste", "corte"),
            (32.06, self.p_doente, "", "whip"),
            (35.32, self.p_casa, "", "corte"),
            (36.22, self.p_moeda, "", "corte"),
            (38.72, self.p_sem_sombra, "", "whip"),
            (42.98, self.p_unico, "triste", "zoom"),
            (45.70, self.p_corre, "triste", "whip"),
            (47.26, self.p_pai_porta, "triste", "corte"),
            (51.16, self.p_revelacao, "triste", "corte"),
            (54.56, self.p_pergunta, "triste", "corte"),
            (56.48, self.p_abaixa, "triste", "corte"),
            (57.74, self.p_jantar, "sepia", "dissolve"),
            (61.88, self.p_cansado, "sepia", "corte"),
            (63.58, self.p_tudo_bem, "sepia", "corte"),
            (65.36, self.p_palco, "", "zoom"),
            (70.18, self.p_nao_piloto, "", "corte"),
            (71.72, self.p_gari, "", "corte"),
            (73.08, self.p_forte, "quente", "corte"),
            (75.28, self.p_sombra_volta, "quente", "corte"),
            (78.18, self.p_final, "quente", "dissolve"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))

    # ----- helpers -----
    def tam_sombra(self, T):
        """Tamanho da sombra do Vitinho no tempo absoluto T."""
        if T >= 76.6:
            return 1.0 + 0.9 * ease_out((T - 76.6) / 1.2)
        if T >= 38.0:
            return 0.0
        n = sum(1 for m in self.mentiras if T >= m)
        tam = 1.0 - 0.17 * n
        if T >= 32.8:   # fingiu doença
            tam = max(0.08, tam - 0.45 * ease_out((T - 32.8) / 1.5))
        return tam

    def ator_com_sombra(self, m, ator, t, cx, by, e, tam, expr="neutro", pose="idle", **kw):
        sombra(m, ator.spr("neutro", "idle"), cx, by, e, tam)
        ator.desenhar(m, t, cx, by, escala=e, expr=expr, pose=pose, **kw)

    def T(self, ini, t):
        return ini + t

    # ----- planos -----
    def p_rua_sombra(self, t, d):
        m = self.rua.copy()
        x = 380 + 120 * (t / d)
        self.ator_com_sombra(m, self.vit, t, x, 1560, 1.3, 1.0, expr="feliz", pulo=6 * abs(math.sin(t * 7)))
        f = camera(m, 540, 1250, 1.2 + 0.1 * ease_io(t / d))
        particulas(f, t, 14, (255, 255, 255))
        return f

    def p_encolhe_demo(self, t, d):
        m = gradiente(WW, WH, (235, 225, 210), (210, 195, 175))
        p = Pincel(WW, WH)
        p.ret((-20, 1350, WW + 20, WH + 20), (200, 180, 150), r=0, ow=0)
        m.alpha_composite(p.pronto())
        tam = 1.0 - 0.35 * ease_out((t - 0.9) / 0.4) if t > 0.9 else 1.0
        self.ator_com_sombra(m, self.vit, t, 400, 1350, 1.25, tam, expr="neutro")
        f = camera(m, 600, 1250, 1.1)
        puf(f, t - 0.9, OUT_W * 0.75, OUT_H * 0.82, 1.4)
        return f

    def p_todos(self, t, d):
        m = self.rua.copy()
        for i, (ator, x) in enumerate(((self.colegas[0], 230), (self.prof, 540), (self.colegas[2], 840))):
            self.ator_com_sombra(m, ator, t + i, x, 1580, 1.05, 1.0, expr="feliz")
        return camera(m, 540, 1250, 1.15)

    def p_chao(self, t, d):
        m = gradiente(WW, WH, (200, 180, 150), (190, 170, 140))
        for i, (ator, x) in enumerate(((self.colegas[0], 200), (self.prof, 540), (self.colegas[2], 880))):
            self.ator_com_sombra(m, ator, t + i, x, 900, 1.0, 1.15)
        return camera(m, 540, 1250, 1.25 + 0.1 * ease_io(t / d))

    def p_comecei(self, t, d):
        m = gradiente(WW, WH, (220, 230, 245), (190, 205, 230))
        self.vit.desenhar(m, t, 540, 2300, escala=2.4, expr="neutro")
        return camera(m, 540, 1050, 1.05 + 0.08 * ease_io(t / d))

    def p_escola(self, t, d):
        m = self.sala.copy()
        self.prof.desenhar(m, t, 820, 1460, escala=1.05, expr="feliz", pose="aponta" if t < 1.4 else "idle")
        for i, (c, x) in enumerate(((self.colegas[0], 150), (self.vit, 470), (self.colegas[1], 780))):
            c.desenhar(m, t + i, x, 1760, escala=0.95, expr="surpreso" if c is self.vit else "feliz")
        m.alpha_composite(self.carteiras, (0, 1500))
        f = camera(m, 540, 1150, 1.1)
        if t > 0.6:
            texto_pop(f, "?", self.fc, t - 0.6, OUT_W * 0.78, OUT_H * 0.2, 130)
        return f

    def p_piloto(self, t, d):
        m = self.sala.copy()
        self.vit.desenhar(m, t, 380, 1800, escala=1.45, expr="feliz", pose="acena")
        s = ease_out((t - 0.4) / 0.3)
        if s > 0:
            b = self.bal_aviao.resize((int(560 * s) + 1, int(560 * s) + 1), Image.BICUBIC)
            m.alpha_composite(b, (int(760 - b.width / 2), int(620 - b.height / 2)))
        return camera(m, 540, 1150, 1.1)

    def p_encolheu(self, t, d):
        m = gradiente(WW, WH, (235, 225, 210), (210, 195, 175))
        p = Pincel(WW, WH)
        p.ret((-20, 1350, WW + 20, WH + 20), (200, 180, 150), r=0, ow=0)
        m.alpha_composite(p.pronto())
        self.ator_com_sombra(m, self.vit, t, 400, 1350, 1.25, self.tam_sombra(14.88 + t), expr="neutro")
        f = camera(m, 600, 1250, 1.15)
        puf(f, t - (15.52 - 14.88), OUT_W * 0.72, OUT_H * 0.82, 1.3)
        return f

    def p_ninguem(self, t, d):
        m = self.sala.copy()
        for i, (c, x) in enumerate(((self.colegas[0], 200), (self.colegas[1], 540), (self.colegas[2], 880))):
            c.desenhar(m, t + i, x, 1700, escala=1.0, expr="ri" if int(t * 5 + i) % 2 else "feliz",
                       pulo=6 * (int(t * 5 + i) % 2))
        m.alpha_composite(self.carteiras, (0, 1500))
        return camera(m, 540, 1150, 1.15)

    def p_bal(self, balao):
        def plano(t, d, balao=balao):
            ini = [p[0] for p in self.planos if p[2] is plano][0] if self.planos else 0
            m = self.rua.copy()
            self.ator_com_sombra(m, self.vit, t, 340, 1600, 1.3, self.tam_sombra(ini + t), expr="feliz", pose="acena")
            s = ease_out((t - 0.15) / 0.3)
            if s > 0:
                b = balao.resize((int(560 * s) + 1, int(560 * s) + 1), Image.BICUBIC)
                m.alpha_composite(b, (int(760 - b.width / 2), int(700 - b.height / 2)))
            f = camera(m, 560, 1200, 1.15)
            for mt in self.mentiras:
                puf(f, ini + t - mt, OUT_W * 0.62, OUT_H * 0.88, 1.1)
            return f
        return plano

    def p_pedacos(self, t, d):
        m = gradiente(WW, WH, (235, 225, 210), (210, 195, 175))
        p = Pincel(WW, WH)
        p.ret((-20, 1350, WW + 20, WH + 20), (200, 180, 150), r=0, ow=0)
        m.alpha_composite(p.pronto())
        tam = self.tam_sombra(23.26) - 0.08 * min(3, int(t / 0.6))
        self.ator_com_sombra(m, self.vit, t, 400, 1350, 1.25, max(0.12, tam), expr="triste")
        f = camera(m, 600, 1250, 1.15)
        for k in range(3):
            puf(f, t - k * 0.6, OUT_W * 0.7, OUT_H * 0.82, 1.0)
        return f

    def p_verdade(self, t, d):
        m = self.madrugada.copy()
        e = 1.55
        lado = 18 * math.sin(t * 5)
        m.alpha_composite(self.vass.rotate(15 + lado, expand=True, resample=Image.BICUBIC), (int(560 + lado * 3), 1180))
        self.pai.desenhar(m, t, 440, 1800, escala=e, expr="neutro")
        f = camera(m, 540, 1250, 1.15 + 0.08 * ease_io(t / d))
        if t > 1.5:
            texto_pop(f, "GARI", self.fc, t - 1.5, OUT_W / 2, OUT_H * 0.14, 120, (255, 160, 60))
        return f

    def p_madrugada(self, t, d):
        m = self.madrugada.copy()
        x = 760 - 260 * (t / d)
        lado = 18 * math.sin(t * 6)
        m.alpha_composite(self.vass.rotate(20 + lado, expand=True, resample=Image.BICUBIC), (int(x + 30 + lado * 3), 1310))
        self.pai.desenhar(m, t, x, 1760, escala=1.05, expr="neutro")
        f = camera(m, 540, 1150, 1.05)
        if t > 0.9:
            texto_pop(f, "4:00", self.fc, t - 0.9, OUT_W * 0.3, OUT_H * 0.16, 110, (255, 230, 150))
        particulas(f, t, 30, (255, 255, 230), semente=40)
        return f

    def p_vergonha(self, t, d):
        m = gradiente(WW, WH, (210, 205, 200), (180, 175, 170))
        self.vit.desenhar(m, t, 540, 2300, escala=2.4, expr="triste", rot=-4)
        return camera(m, 540, 1050, 1.05 + 0.1 * ease_io(t / d))

    def p_doente(self, t, d):
        m = self.quarto.copy()
        self.vit.desenhar(m, t, 520, 1500, escala=1.2, expr="triste", piscar=True)
        m.alpha_composite(self.cobertor, (0, 1160))
        f = camera(m, 540, 1150, 1.1)
        if t > 0.5:
            b = self.bal_pisc  # placeholder p/ tamanho
            texto_pop(f, "FEIRA DE PROFISSÕES", self.fc, t - 0.5, OUT_W / 2, OUT_H * 0.14, 56, (255, 214, 40))
        if 1.6 < t < 2.4:
            texto_pop(f, "cof cof", self.fc, t - 1.6, OUT_W * 0.72, OUT_H * 0.4, 60)
        return f

    def p_casa(self, t, d):
        m = self.quarto.copy()
        self.vit.desenhar(m, t, 520, 1500, escala=1.2, expr="triste")
        m.alpha_composite(self.cobertor, (0, 1160))
        return camera(m, 520, 1250, 1.35)

    def p_moeda(self, t, d):
        m = gradiente(WW, WH, (235, 225, 210), (210, 195, 175))
        p = Pincel(WW, WH)
        p.ret((-20, 1350, WW + 20, WH + 20), (200, 180, 150), r=0, ow=0)
        p.elipse((700, 1340, 820, 1400), (230, 190, 60))
        p.elipse((716, 1348, 804, 1392), (245, 210, 90), ow=0)
        m.alpha_composite(p.pronto())
        self.ator_com_sombra(m, self.vit, t, 420, 1350, 1.25, self.tam_sombra(36.22 + t), expr="triste")
        return camera(m, 560, 1200, 1.35 + 0.1 * ease_io(t / d))

    def p_sem_sombra(self, t, d):
        m = self.rua.copy()
        tam = self.tam_sombra(38.72 + t) if t < 2.2 else 0.0
        tam = 0.08 * (1 - ease_out((t - 1.8) / 0.5)) if t > 1.8 else 0.08
        sombra(m, self.vass, 860, 1560, 1.0, 1.0)  # a vassoura encostada tem sombra
        m.alpha_composite(self.vass.rotate(-8, expand=True), (800, 860))
        olha = t > 2.0
        self.ator_com_sombra(m, self.vit, t, 460, 1600, 1.35, tam,
                             expr="surpreso" if t > 3.0 else ("triste" if olha else "neutro"))
        z = 1.15 if t < 3.0 else 1.15 + 0.6 * ease_out((t - 3.0) / 0.3)
        cy = 1300 if t < 3.0 else 1300 - 300 * ease_out((t - 3.0) / 0.3)
        f = camera(m, 520, cy, z)
        if 1.8 < t < 2.3:
            puf(f, t - 1.8, OUT_W * 0.55, OUT_H * 0.9, 1.0)
        if 3.0 <= t < 3.1:
            f = Image.blend(f, Image.new("RGB", f.size, (255, 255, 255)), 0.6)
        return f

    def p_unico(self, t, d):
        m = self.rua.copy()
        pos = [(120, 0.85), (300, 0.9), (780, 0.9), (960, 0.85)]
        for i, (x, e) in enumerate(pos):
            ator = [self.colegas[0], self.prof, self.colegas[1], self.colegas[2]][i]
            self.ator_com_sombra(m, ator, t + i, x, 1560, e, 1.0, expr="neutro")
        self.vit.desenhar(m, t, 540, 1620, escala=1.05, expr="triste")
        f = camera(m, 540, 1250, 1.15 + 0.1 * ease_io(t / d))
        return f

    def p_corre(self, t, d):
        off = (t * 1000) % WW
        m = Image.new("RGBA", (WW, WH))
        m.alpha_composite(self.rua, (int(-off), 0))
        m.alpha_composite(self.rua, (int(WW - off), 0))
        passo = int(t * 8) % 2
        self.vit.desenhar(m, t, 540, 1760, escala=1.3, expr="chora", pose="acena" if passo else "idle",
                          rot=-8, pulo=25 * passo)
        f = camera(m, WW / 2, 1150, 1.15)
        dr = ImageDraw.Draw(f)
        rng = random.Random(int(t * 10))
        for _ in range(8):
            y, x = rng.uniform(200, 1100), rng.uniform(0, OUT_W)
            dr.line((x, y, x + rng.uniform(80, 200), y), fill=(255, 255, 255), width=5)
        return f

    def p_pai_porta(self, t, d):
        m = self.porta.copy()
        m.alpha_composite(self.vass.rotate(-10, expand=True), (720, 1020))
        self.pai.desenhar(m, t, 470, 1880, escala=1.45, expr="triste", piscar=t > 1.0)
        m.alpha_composite(self.degrau, (0, 1500))
        z = 1.12 + 0.06 * ease_io(t / d)
        return camera(m, 540, 1150, z)

    def p_revelacao(self, t, d):
        m = self.porta.copy()
        p = Pincel(WW, WH)
        p.ret((-20, 1500, WW + 20, WH + 20), (210, 200, 185), r=0, ow=0)
        m.alpha_composite(p.pronto())
        sombra(m, self.vass, 860, 1700, 1.0, 1.0)
        m.alpha_composite(self.vass.rotate(-8, expand=True), (800, 1000))
        self.pai.desenhar(m, t, 520, 1720, escala=1.35, expr="triste")
        self.vit.desenhar(m, t, 230, 1760, escala=1.0, expr="surpreso")
        # câmera desce até o chão (onde deveria estar a sombra)
        k = ease_io(min(1, t / 1.6))
        f = camera(m, 540, 1150 + 420 * k, 1.1 + 0.25 * k)
        if t > 1.6 and t < 1.7:
            f = Image.blend(f, Image.new("RGB", f.size, (255, 255, 255)), 0.5)
        return f

    def p_pergunta(self, t, d):
        m = gradiente(WW, WH, (200, 195, 195), (170, 165, 165))
        self.vit.desenhar(m, t, 540, 2350, escala=2.6, expr="chora", piscar=False)
        return camera(m, 540, 1000, 1.05 + 0.15 * ease_out(t / d))

    def p_abaixa(self, t, d):
        m = gradiente(WW, WH, (200, 195, 195), (170, 165, 165))
        k = ease_out(t / 0.6)
        self.pai.desenhar(m, t, 540, 2450 + 80 * k, escala=2.6, expr="triste", rot=-6 * k, piscar=False)
        return camera(m, 540, 1000, 1.08)

    def p_jantar(self, t, d):
        m = self.cozinha.copy()
        self.pai_c.desenhar(m, t, 300, 1560, escala=1.25, expr="feliz", pose="entrega")
        self.vit.desenhar(m, t, 790, 1560, escala=1.0, expr="ri" if int(t * 4) % 2 else "feliz")
        m.alpha_composite(self.mesa, (0, 1380))
        f = camera(m, 540, 1250, 1.15)
        if t > 1.2:
            texto_pop(f, "\"Já jantei\"", self.fc, t - 1.2, OUT_W * 0.3, OUT_H * 0.16, 64, (255, 240, 200))
        return f

    def p_cansado(self, t, d):
        m = self.madrugada.copy()
        lado = 14 * math.sin(t * 4)
        m.alpha_composite(self.vass.rotate(20 + lado, expand=True), (int(600 + lado * 3), 1230))
        self.pai.desenhar(m, t, 470, 1800, escala=1.4, expr="triste", rot=3)
        return camera(m, 540, 1250, 1.2)

    def p_tudo_bem(self, t, d):
        m = gradiente(WW, WH, (220, 200, 170), (190, 170, 140))
        self.pai_c.desenhar(m, t, 540, 2450, escala=2.6, expr="feliz", piscar=False)
        f = camera(m, 540, 1000, 1.05 + 0.1 * ease_io(t / d))
        return f

    def p_palco(self, t, d):
        m = self.palco.copy()
        self.vit.desenhar(m, t, 470, 1500, escala=1.05, expr="neutro" if t < 2.5 else "triste")
        m.alpha_composite(self.mic, (500, 830))
        m.alpha_composite(plateia(t), (0, 1450))
        return camera(m, 540, 1150, 1.0 + 0.12 * ease_io(t / d))

    def p_nao_piloto(self, t, d):
        m = self.palco.copy()
        self.vit.desenhar(m, t, 500, 2200, escala=2.2, expr="neutro")
        m.alpha_composite(self.mic.resize((360, 1620)), (520, 900))
        return camera(m, 540, 1000, 1.05 + 0.1 * ease_out(t / d))

    def p_gari(self, t, d):
        m = gradiente(WW, WH, (60, 45, 60), (35, 25, 40))
        m.alpha_composite(brilho((900, 900), (255, 200, 120), 450, 0.5), (90, 500))
        self.pai.desenhar(m, t, 540, 2000, escala=2.0, expr="surpreso")
        m.alpha_composite(plateia(t), (0, 1500))
        f = camera(m, 540, 1100, 1.0 + 0.3 * ease_out(t / 0.35))
        return f

    def p_forte(self, t, d):
        m = gradiente(WW, WH, (90, 60, 70), (50, 35, 50))
        m.alpha_composite(brilho((1000, 1000), (255, 210, 130), 500, 0.6), (40, 400))
        self.pai.desenhar(m, t, 540, 2450, escala=2.6, expr="chora", piscar=False)
        f = camera(m, 540, 1000, 1.05 + 0.1 * ease_io(t / d))
        particulas(f, t, 30, semente=51)
        return f

    def p_sombra_volta(self, t, d):
        m = self.palco.copy()
        p = Pincel(WW, WH)
        p.ret((-20, 1350, WW + 20, WH + 20), (175, 120, 75), r=0, ow=0)
        m.alpha_composite(p.pronto())
        tam = self.tam_sombra(75.28 + t)
        self.ator_com_sombra(m, self.vit, t, 420, 1350, 1.25, tam, expr="surpreso" if t < 1.3 else "feliz")
        if tam > 0:
            glow = brilho((900, 600), (255, 220, 120), 450, 0.5 * min(1, tam))
            m.alpha_composite(glow, (200, 1150))
        f = camera(m, 600, 1250, 1.15)
        particulas(f, t, 40, semente=60)
        return f

    def p_final(self, t, d):
        m = self.rua_sol.copy()
        e = 1.15
        # uma sombra gigante que cobre os dois
        sil = self.pai.spr("neutro", "idle")
        sombra(m, sil, 470, 1460, e * 1.7, 1.3)
        self.pai.desenhar(m, t, 380, 1460, escala=1.4, expr="feliz")
        self.vit.desenhar(m, t, 700, 1460, escala=1.05, expr="ri" if int(t * 3) % 3 == 0 else "feliz")
        f = camera(m, 540, 1150 - 60 * ease_io(t / d), 1.25 - 0.2 * ease_io(t / d))
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
        for t in self.mentiras + [3.20 + 0.9, 23.26, 23.86, 24.46, 40.5]:
            ev.append(("toc", t))  # "puf" grave
        ev += [("brilho", 76.6), ("brilho", 78.4)]
        return ev


def carregar_palavras(caminho):
    import json
    pal = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            pal.append(dict(w=CORRECOES.get(w["w"], w["w"]), s=w["s"], e=w["e"]))
    return pal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_sombra_do_vitinho.mp4"))
    ap.add_argument("--preview", default=None)
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeSombra(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.2)
    total = int(filme.dur_total * FPS)

    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        for i, (ini, d, *_r) in enumerate(filme.planos):
            filme.frame(int((ini + d * 0.6) * FPS)).save(os.path.join(a.preview, f"plano_{i:02d}.png"))
        print("preview em", a.preview)
        return

    tmp = tempfile.mkdtemp(prefix="sombra_")
    wav = os.path.join(tmp, "mix.wav")
    vc.mixar(filme, a.narracao, wav)
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
