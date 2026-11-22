#!/usr/bin/env python3
"""
"A Árvore da Praça" — quem fica um ano sem abraçar ninguém vira árvore e só volta se alguém abraçar o tronco.

Feito para copiar o RITMO de um vídeo de referência (pedido do usuário):
  * grade de cortes = os 75 cortes do vídeo de referência, remapeados para a narração por alinhamento de palavras
    (ancoras.json) → mesmo tempo de cena;
  * movimento de câmera de cada cena = zoom/pan medido na referência (camera.json), câmera lisa (sem balanço);
  * efeitos sonoros (whoosh/pop/batida) nos mesmos instantes dos cortes.

    python3 animacao/video_arvore.py --narracao narr.mp3 --transcricao transcricao.json --fonte Poppins.ttf \
        --camera camera.json --ancoras ancoras.json
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
import video_lagrima as vl  # noqa: E402
import ambiente as amb  # noqa: E402
import boneco  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io, particulas, texto_pop)

g.HANDHELD = False           # câmera lisa, como na referência
boneco.Boneco.AMP = 1.8      # personagens bem mais vivos
random.seed(1717)
_C = {}

VITOR = dict(pele=(222, 170, 128), cabelo=(70, 48, 36), camisa=(110, 150, 200), calca=(80, 80, 100),
             sapato=(60, 50, 50), tipo="pai", bigode=False)
MOCA = dict(pele=(226, 176, 136), cabelo=(70, 40, 30), camisa=(250, 205, 90), calca=(0, 0, 0),
            sapato=(150, 70, 70), tipo="moca", vestido=(250, 205, 90))
MOCA_V = dict(MOCA, camisa=(230, 90, 110), vestido=(230, 90, 110))
EX = dict(pele=(232, 186, 150), cabelo=(150, 70, 50), camisa=(230, 120, 160), calca=(0, 0, 0), sapato=(150, 70, 90),
          tipo="moca", vestido=(230, 120, 160))
OUTRO = dict(pele=(200, 150, 110), cabelo=(40, 30, 28), camisa=(70, 90, 140), calca=(60, 62, 80), sapato=(30, 30, 34),
             tipo="pai", bigode=False)
BEBADO = dict(pele=(222, 170, 128), cabelo=(100, 80, 60), camisa=(140, 120, 90), calca=(90, 80, 70), sapato=(50, 40, 40),
              tipo="pai", chapeu=(110, 90, 70))
CRIANCA = dict(pele=(222, 170, 128), cabelo=(60, 40, 30), camisa=(120, 200, 140), calca=(80, 90, 150),
               sapato=(230, 230, 235), tipo="menino")
VERDE, VERDE2 = (90, 170, 100), (70, 150, 90)


# --------------------------------------------------------------------------
# Árvores com cara
# --------------------------------------------------------------------------
def arvore(expr="neutro", fechado=False, folha=VERDE, tronco=(140, 96, 64), sway=0.0, w=340, so_tronco=False, boca=0):
    p = Pincel(420, 700)
    cx = 210
    # raízes
    for sx in (-1, 1):
        p.poli([(cx + sx * 40, 600), (cx + sx * 130, 650), (cx + sx * 160, 690), (cx + sx * 60, 668)], tronco, ow=6)
    p.ret((cx - 70, 300, cx + 70, 672), tronco, r=30)                                  # tronco
    p.poli([(cx - 70, 300), (cx - 150, 220 + sway), (cx - 130, 180 + sway), (cx - 40, 280)], tronco, ow=6)  # galhos
    p.poli([(cx + 70, 300), (cx + 150, 220 - sway), (cx + 130, 180 - sway), (cx + 40, 280)], tronco, ow=6)
    if not so_tronco:
        for ox, oy, r in ((-90, 170, 100), (90, 170, 100), (0, 110, 120), (-40, 230, 84), (50, 230, 84)):
            p.elipse((cx + ox - r + sway * 0.6, oy - r * 0.8, cx + ox + r + sway * 0.6, oy + r * 0.8), folha, ow=6)
        for ox, oy in ((-60, 120), (50, 150), (0, 200)):
            p.elipse((cx + ox - 16, oy - 10, cx + ox + 16, oy + 10), tuple(min(255, c + 40) for c in folha), ow=0)
    ey = 410
    for sx in (-1, 1):
        ex = cx + sx * 28
        if fechado or expr == "ri":
            p.arco((ex - 16, ey - 8, ex + 16, ey + 14), 200, 340, w=6)
        else:
            p.elipse((ex - 17, ey - 22, ex + 17, ey + 22), (255, 255, 255), ow=5)
            p.elipse((ex - 8, ey - 8 + (4 if expr == "triste" else 0), ex + 8, ey + 8 + (4 if expr == "triste" else 0)),
                     (43, 40, 58), ow=0)
        if expr == "triste" or expr == "chora":
            p.linha([(ex - sx * 16, ey - 34 - sx * -4 * 0), (ex + sx * 14, ey - 44)], w=6)
        else:
            p.linha([(ex - 16, ey - 34), (ex + 16, ey - 38)], w=6)
    if boca == 2:
        p.elipse((cx - 17, 450, cx + 17, 492), (150, 40, 50), ow=5)
    elif boca == 1:
        p.elipse((cx - 13, 454, cx + 13, 476), (150, 40, 50), ow=5)
    elif expr == "feliz" or expr == "ri":
        p.chord((cx - 22, 452, cx + 22, 490), 0, 180, (150, 40, 50), ow=5)
    elif expr == "triste" or expr == "chora":
        p.arco((cx - 20, 462, cx + 20, 488), 200, 340, w=6)
    elif expr == "surpreso":
        p.elipse((cx - 10, 452, cx + 10, 482), (150, 40, 50), ow=5)
    else:
        p.linha([(cx - 14, 470), (cx + 14, 470)], w=6)
    if expr == "chora":
        for sx in (-1, 1):
            p.ret((cx + sx * 28 - 7, ey + 24, cx + sx * 28 + 7, ey + 80), (120, 190, 255), r=7, ow=3)
    img = p.pronto()
    return img if w == 420 else img.resize((w, int(700 * w / 420)), Image.BICUBIC)


class Arvore:
    def __init__(self, folha=VERDE, tronco=(140, 96, 64), semente=0.0, filme=None):
        self.folha, self.tronco, self.semente, self.filme = folha, tronco, semente, filme
        self.ultimo_bob = 0.0

    def __call__(self, m, t, cx, by, e, expr="neutro", pose="idle", alpha=1.0, fala=None, **kw):
        sway = 13 * math.sin(t * 1.5 + self.semente) + 5 * math.sin(t * 3.1 + self.semente)
        fechado = (int(t * g.FPS) % 110) in (0, 1, 2)
        boca = self.filme.boca_estado(fala) if (fala and self.filme) else 0
        img = arvore(expr, fechado, self.folha, self.tronco, round(sway), 420, boca=boca)
        w = int(img.width * e)
        img = img.resize((w, int(img.height * e)), Image.BICUBIC)
        # balanço do tronco inteiro + respiração
        ang = 2.2 * math.sin(t * 1.1 + self.semente) + (1.2 * math.sin(t * 7) if boca else 0)
        img = img.rotate(ang, resample=Image.BICUBIC, center=(w / 2, img.height - 30 * e))
        if alpha < 1:
            img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
        m.alpha_composite(img, (int(cx - w / 2), int(by - img.height + 30 * e)))


def laco(m, cx, by, e, cor, alt):
    """Fita/lenço: pequena faixa colorida (no pescoço do personagem ou galho da árvore)."""
    p = Pincel(160, 90)
    p.poli([(10, 30), (80, 10), (80, 60), (10, 50)], cor, ow=5)
    p.poli([(150, 30), (80, 10), (80, 60), (150, 50)], cor, ow=5)
    p.elipse((66, 22, 94, 50), cor, ow=5)
    img = p.pronto()
    w = int(160 * e)
    img = img.resize((w, int(90 * e)), Image.BICUBIC)
    m.alpha_composite(img, (int(cx - w / 2), int(by - alt * e)))


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
def praca(hora="dia", fc=None):
    k = ("praca", hora)
    if k in _C:
        return _C[k]
    topo, base_c = {"dia": ((150, 205, 245), (225, 240, 250)), "tarde": ((255, 190, 130), (255, 225, 180)),
                    "noite": ((16, 22, 56), (44, 40, 84)), "chuva": ((110, 120, 135), (150, 158, 170)),
                    "inverno": ((190, 205, 225), (235, 240, 248))}[hora]
    base = gradiente(WW, WH, topo, base_c)
    p = Pincel(WW, WH)
    if hora in ("dia", "tarde"):
        p.elipse((780, 160, 940, 320), (255, 245, 200), ow=0)
    if hora == "noite":
        p.elipse((140, 160, 260, 280), (250, 244, 210), ow=0)
        rng = random.Random(3)
        for _ in range(40):
            x, y = rng.randint(0, WW), rng.randint(0, 700)
            p.elipse((x - 3, y - 3, x + 3, y + 3), (255, 255, 230), ow=0)
    for i, x in enumerate((-60, 280, 620, 960)):                                     # prédios ao fundo
        top = 640 + (i % 2) * 110
        cor = (150, 160, 190) if hora in ("noite", "chuva") else [(220, 160, 140), (150, 190, 215), (230, 210, 140),
                                                                   (170, 205, 160)][i]
        p.ret((x, top, x + 260, 1300), cor, r=4)
    p.ret((-20, 1300, WW + 20, WH + 20), (110, 170, 100) if hora != "noite" else (50, 90, 80), r=0)   # grama
    p.poli([(300, 1300), (780, 1300), (1100, WH + 20), (-20, WH + 20)], (225, 205, 170) if hora != "noite" else (110, 100, 110),
           ow=0)                                                                      # caminho
    for x in (140, 940):                                                              # canteiros
        p.elipse((x - 150, 1560, x + 150, 1700), (90, 62, 44), ow=6)
    base.alpha_composite(p.pronto())
    if hora == "noite":
        base.alpha_composite(brilho((700, 700), (255, 230, 170), 330, 0.4), (190, 650))
    _C[k] = base
    return base


def banco_sprite(w=620):
    p = Pincel(620, 260)
    p.ret((20, 60, 600, 120), (150, 105, 70), r=10)
    p.ret((20, 140, 600, 190), (170, 120, 80), r=10)
    for x in (60, 530):
        p.ret((x, 190, x + 28, 250), (90, 70, 60), r=4)
    img = p.pronto()
    return img if w == 620 else img.resize((w, int(260 * w / 620)), Image.BICUBIC)


def celular(fc, titulo, w=640):
    return vl.celular(fc, titulo, "Alguém aí?", w)


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeArvore(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao, camera, ancoras):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.vitor, self.moca, self.mocav = P_(VITOR), P_(MOCA), P_(MOCA_V)
        self.ex, self.outro, self.beb, self.cri = P_(EX), P_(OUTRO), P_(BEBADO), P_(CRIANCA)
        self.av = Arvore(VERDE, (140, 96, 64), 0.0, self)       # o narrador
        self.ar = Arvore(VERDE2, (120, 84, 60), 1.7, self)      # o Rodrigo
        self.fundo = [P_(c) for c in ve.POVO]                   # gente ao fundo
        dlg = [(59.62, 66.5), (103.42, 110.2), (126.74, 132.2), (142.74, 149.0), (160.44, 165.4), (172.0, 172.2)]
        self.FALA_MOCA = dlg
        self.FALA_RODRIGO = [(165.54, 169.9)]
        ini, narr = 0.0, []
        for a, b in sorted(dlg + self.FALA_RODRIGO):
            narr.append((ini, a))
            ini = b
        narr.append((ini, 999.0))
        self.FALA_NARR = narr
        self.blur = {}
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.cortes = [(0.0, 0)]                                  # sem variações automáticas de câmera
        self.spec = None
        self.u = 0.0

        ra = np.array([a for a, _ in ancoras])
        oa = np.array([b for _, b in ancoras])
        self.beats = self._beats()
        self.planos = []
        self.sfx_cortes = []
        n = len(camera)
        for i, c in enumerate(camera):
            a = float(np.interp(c["ini"], ra, oa))
            b = float(np.interp(c["ini"] + c["dur"], ra, oa)) if i + 1 < n else dur_total
            if i == 0:
                a = 0.0
            self.planos.append((a, max(0.2, b - a), self._fazer(i, c), "", "corte"))
            if i:
                self.sfx_cortes.append(a)
        self.p_preto = None

    # ----- movimento de câmera copiado da referência -----
    def spec_de(self, i, c):
        r = c.get("r", 0)
        if r >= 0.4:
            z = min(1.3, max(0.85, c["zoom"]))
            dx = max(-0.12, min(0.12, c["dx"]))
            dy = max(-0.12, min(0.12, c["dy"]))
        else:
            z = 1.07 if i % 2 == 0 else 0.95
            dx = dy = 0.0
        return z, dx, dy

    def _fazer(self, i, c):
        z, dx, dy = self.spec_de(i, c)

        def fn(t, d):
            self.spec = (z, dx, dy)
            self.u = ease_io(min(1, t / max(0.1, d)))
            T = self.T
            ini = T - t
            beat = self._achar(ini + d / 2)
            return beat(t, d, T)
        return fn

    def cam(self, m, cx, cy, zb):
        z, dx, dy = self.spec if self.spec else (1.0, 0, 0)
        u = self.u
        if z >= 1:
            zz = zb * (1 + (z - 1) * u)
        else:
            zz = zb / z * (z ** u)
        vw, vh = WW / zz, WH / zz
        return g.camera(m, cx - dx * u * vw, cy - dy * u * vh, zz)

    def vida(self, m, t, hora):
        """Elementos animados que dão vida ao fundo da praça."""
        if hora in ("dia", "tarde", "inverno"):
            amb.nuvens(m, t, n=5, seed=11, vel=22, alpha=230 if hora != "tarde" else 190)
        if hora in ("dia", "tarde"):
            amb.passaros(m, t, n=4, seed=12)
            amb.folhas(m, t, n=16, seed=13)
            amb.gente_fundo(m, t, self.fundo, n=5, seed=14, escala=0.4)
        if hora == "tarde":
            amb.raios_luz(m, t)
        if hora == "noite":
            amb.vagalumes(m, t, n=22)
        if hora == "chuva":
            amb.nuvens(m, t, n=6, seed=15, vel=26, cor=(120, 128, 142), alpha=235)

    # ----- utilidades -----
    def txt(self, f, s, t0, y=0.1, tam=58, cor=(255, 255, 255)):
        if self.T >= t0:
            texto_pop(f, s, self.fc, self.T - t0, OUT_W / 2, OUT_H * y, tam, cor)

    def balao_t(self, f, txt, x, y, t0):
        if self.T >= t0:
            self.balao(f, txt, x, y, self.T - t0)

    def _achar(self, t):
        fn = self.beats[0][1]
        for ini, f in self.beats:
            if ini <= t:
                fn = f
        return fn

    def praca_cena(self, t, hora="dia", narr="arvore", ne="neutro", rod="arvore", re="neutro", moca=None,
                   me="neutro", mpose="idle", banco=True, extra=None, cx=540, cy=1250, z=1.1, sentada=True,
                   lenco=True, fita=False, chuva=False):
        m = praca(hora).copy()
        self.vida(m, t, hora)
        # narrador (esquerda) e Rodrigo (direita)
        if narr == "arvore":
            self.av(m, t, 330, 1720, 1.15, expr=ne, fala=self.FALA_NARR)
        elif narr == "humano":
            self.vitor(m, t, 330, 1780, 1.2, expr=ne, pose="idle", fala=self.FALA_NARR)
        if rod == "arvore":
            self.ar(m, t, 810, 1720, 1.15, expr=re, fala=self.FALA_RODRIGO)
        elif rod == "humano":
            self.outro(m, t, 810, 1780, 1.2, expr=re, pose="idle")
        if fita:
            laco(m, 570, 1330, 1.0, (250, 205, 60), 0)
        if moca:
            mx = moca
            self.moca(m, t, mx, 1830 if sentada else 1800, 1.2, expr=me, pose=mpose, fala=self.FALA_MOCA)
            if lenco:
                laco(m, mx, 1830 - 325 * 1.2, 0.7, (235, 50, 60), 0)
        if banco:
            b = banco_sprite(640)
            m.alpha_composite(b, (540 - 320, 1650)) if moca is None else m.alpha_composite(b, (int(moca - 320), 1650))
        if extra:
            extra(m)
        f = self.cam(m, cx, cy, z)
        if chuva:
            vl.FilmeLagrima.chuva_f(self, f, t, 120)
        return f

    # ----- beats (começo, função) -----
    def _beats(self):
        R = []

        def B(ini):
            def deco(fn):
                R.append((ini, fn))
                return fn
            return deco

        @B(0.0)
        def hook(t, d, T):
            f = self.praca_cena(t, "dia", ne="neutro", re="neutro")
            self.txt(f, "UM ANO SEM ABRAÇAR…", 0.3, 0.1, 54, (255, 255, 255))
            self.txt(f, "VIRA ÁRVORE", 2.7, 0.18, 70, (255, 214, 40))
            return f

        @B(5.68)
        def so_volta(t, d, T):
            m = gradiente(WW, WH, (150, 205, 245), (225, 240, 250))
            self.av(m, t, 340, 1700, 1.2, expr="neutro")
            self.moca(m, t, 800, 1800, 1.2, expr="feliz", pose="bracos_abertos")
            f = self.cam(m, 540, 1250, 1.1)
            self.txt(f, "UM ABRAÇO NO TRONCO", 5.9, 0.1, 50, (255, 255, 255))
            return f

        @B(7.72)
        def virei(t, d, T):
            f = self.praca_cena(t, "dia", ne="triste", rod="arvore", re="triste", cx=400, z=1.25)
            self.txt(f, "EU VIREI", 7.9, 0.1, 80, (255, 214, 40))
            self.txt(f, "FAZ DOIS ANOS", 9.0, 0.18, 54, (255, 255, 255))
            return f

        @B(10.8)
        def mensagem(t, d, T):
            m = gradiente(WW, WH, (30, 30, 44), (14, 14, 24))
            c = celular(self.fc, "Mensagem", 760)
            m.alpha_composite(c, (540 - c.width // 2, 600))
            f = self.cam(m, 540, 1100, 1.0)
            self.txt(f, "MANDEI MENSAGEM", 11.0, 0.1, 54, (255, 255, 255))
            self.txt(f, "NINGUÉM RESPONDEU", 14.0, 0.18, 46, (255, 130, 140)) if T > 14.0 else None
            return f

        @B(16.94)
        def meia_noite(t, d, T):
            m = praca("noite").copy()
            self.vitor(m, t, 540, 1780, 1.3, expr="triste", pose="idle")
            m.alpha_composite(banco_sprite(640), (220, 1650))
            f = self.cam(m, 540, 1250, 1.1)
            self.txt(f, "MEIA-NOITE", 17.0, 0.1, 80, (255, 214, 40))
            return f

        @B(20.0)
        def pesar(t, d, T):
            m = praca("noite").copy()
            k = ease_io(min(1, max(0, (T - 20.0) / 4.4)))
            tmp_h = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
            tmp_t = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
            self.vitor(tmp_h, t, 540, 1760, 1.3, expr="surpreso", pose="idle")
            self.av(tmp_t, t, 540, 1760, 1.3, expr="surpreso")
            linha = int(1760 - 800 * (1 - k))
            mask = Image.new("L", (WW, WH), 0)
            ImageDraw.Draw(mask).rectangle((0, linha, WW, WH), fill=255)
            res = Image.composite(tmp_t, tmp_h, mask)
            m.alpha_composite(res)
            m.alpha_composite(banco_sprite(640), (220, 1700))
            f = self.cam(m, 540, 1250, 1.1)
            self.txt(f, "OS PÉS PESARAM…", 20.2, 0.1, 54, (255, 255, 255))
            self.txt(f, "AS PERNAS… O PEITO", 22.7, 0.18, 46, (255, 130, 140))
            return f

        @B(24.62)
        def plantou(t, d, T):
            f = self.praca_cena(t, "dia", ne="triste", re="neutro", cx=540, z=1.12, banco=False)
            self.txt(f, "A PREFEITURA ME PLANTOU", 25.0, 0.1, 44, (255, 255, 255))
            self.txt(f, "DO LADO DO RODRIGO", 27.9, 0.17, 44, (255, 214, 40))
            return f

        @B(31.22)
        def ouvindo(t, d, T):
            m = self.fundo_blur("pr", praca("dia"))
            self.av(m, t, 540, 2250, 2.6, expr="triste")
            f = self.cam(m, 540, 1000, 1.0)
            self.txt(f, "VEJO E OUÇO TUDO", 31.5, 0.1, 54, (255, 255, 255))
            self.txt(f, "SÓ NÃO ME MEXO", 35.0, 0.18, 54, (255, 130, 140))
            return f

        @B(37.34)
        def ex(t, d, T):
            def ext(m):
                self.ex(m, t, 120 + 700 * ease_io(min(1, (T - 37.3) / 4.0)), 1790, 1.1, expr="feliz", pose="anda")
                self.outro(m, t, 280 + 700 * ease_io(min(1, (T - 37.3) / 4.0)), 1790, 1.1, expr="feliz", pose="anda")
            f = self.praca_cena(t, "dia", ne="triste", re="neutro", banco=False, extra=ext, z=1.1)
            self.txt(f, "A MINHA EX", 37.6, 0.1, 64, (255, 255, 255))
            self.txt(f, "NUNCA OLHOU PRA CIMA", 42.9, 0.18, 44, (255, 130, 140))
            return f

        @B(44.48)
        def crianca(t, d, T):
            def ext(m):
                self.cri(m, t, 330, 1500, 0.55, expr="ri", pose="acena")
                p = Pincel(120, 90)
                p.elipse((20, 30, 100, 80), (110, 130, 200), ow=5)
                p.poli([(90, 50), (116, 56), (90, 64)], (250, 190, 60), ow=4)
                m.alpha_composite(p.pronto(), (int(300 + 20 * math.sin(t * 5)), 1050))
            f = self.praca_cena(t, "dia", ne="feliz", re="neutro", banco=False, extra=ext, cx=400, z=1.2)
            self.txt(f, "CRIANÇA NOS GALHOS", 44.8, 0.1, 50, (255, 255, 255))
            self.txt(f, "PASSARINHO NA CABEÇA", 46.4, 0.18, 44, (255, 214, 40))
            return f

        @B(48.98)
        def bebado(t, d, T):
            def ext(m):
                self.beb(m, t, 330, 1800, 1.1, expr="chora", pose="idle")
            f = self.praca_cena(t, "noite", ne="triste", re="neutro", banco=False, extra=ext, cx=420, z=1.2)
            self.txt(f, "UM BÊBADO ME CHAMOU DE IRMÃO", 49.0, 0.1, 36, (255, 255, 255))
            self.txt(f, "E CHOROU NO MEU PÉ", 51.4, 0.17, 44, (255, 130, 140))
            return f

        @B(53.06)
        def moca_chega(t, d, T):
            x = 1100 - 560 * ease_out(min(1, (T - 53.0) / 3.0))
            f = self.praca_cena(t, "tarde", ne="neutro", re="neutro", moca=int(x), me="neutro",
                                mpose="anda" if T < 56.0 else "idle", sentada=False, z=1.1)
            self.txt(f, "UMA TERÇA…", 53.3, 0.1, 70, (255, 255, 255))
            self.txt(f, "MOÇA DE LENÇO VERMELHO", 55.0, 0.18, 40, (255, 130, 140))
            return f

        @B(59.62)
        def oi(t, d, T):
            f = self.praca_cena(t, "tarde", ne="surpreso", re="neutro", moca=540, me="triste", mpose="idle", z=1.15)
            self.balao_t(f, "Eu sei que é estranho…", OUT_W * 0.55, OUT_H * 0.12, 60.0)
            self.balao_t(f, "Precisava falar com alguém.", OUT_W * 0.5, OUT_H * 0.2, 63.0)
            return f

        @B(67.04)
        def voltou(t, d, T):
            f = self.praca_cena(t, "tarde", ne="feliz", re="neutro", moca=540, me="feliz", mpose="idle", z=1.15)
            self.txt(f, "TODO DIA, ÀS SEIS", 67.3, 0.1, 58, (255, 214, 40))
            return f

        @B(72.6)
        def contava(t, d, T):
            f = self.praca_cena(t, "tarde", ne="feliz", re="neutro", moca=540, me="ri", mpose="acena", z=1.15)
            self.txt(f, "O CHEFE QUE GRITAVA", 72.7, 0.1, 44, (255, 255, 255))
            self.txt(f, "O CACHORRO BOLINHA", 75.0, 0.17, 44, (255, 255, 255))
            self.txt(f, "MEDO DE TROVÃO", 77.8, 0.24, 52, (255, 214, 40))
            return f

        @B(79.32)
        def livro(t, d, T):
            def ext(m):
                p = Pincel(200, 150)
                p.ret((10, 20, 190, 130), (200, 70, 70), r=10)
                p.ret((20, 28, 180, 122), (250, 245, 225), r=6, ow=0)
                m.alpha_composite(p.pronto(), (590, 1560))
            f = self.praca_cena(t, "tarde", ne="feliz", re="neutro", moca=540, me="neutro", mpose="idle", extra=ext,
                                z=1.15)
            self.txt(f, "LIA UM LIVRO EM VOZ ALTA", 79.6, 0.1, 40, (255, 255, 255))
            self.txt(f, "OU SÓ OLHAVA PRA CIMA", 82.3, 0.17, 40, (255, 214, 40))
            return f

        @B(86.24)
        def fita(t, d, T):
            f = self.praca_cena(t, "inverno", ne="feliz", re="feliz", moca=540, me="feliz", mpose="bracos_abertos",
                                fita=True, z=1.15)
            self.txt(f, "UMA FITA AMARELA", 86.5, 0.1, 54, (255, 214, 40))
            self.txt(f, "ENTRE MIM E O RODRIGO", 89.0, 0.17, 40, (255, 255, 255))
            return f

        @B(93.6)
        def apaixonando(t, d, T):
            m = self.fundo_blur("pr", praca("tarde"))
            self.av(m, t, 540, 2250, 2.6, expr="feliz")
            f = self.cam(m, 540, 1000, 1.0)
            self.txt(f, "ME APAIXONANDO", 93.7, 0.1, 64, (255, 130, 160))
            self.txt(f, "SEM CONSEGUIR PISCAR", 95.0, 0.18, 44, (255, 255, 255))
            return f

        @B(96.66)
        def horas(t, d, T):
            m = gradiente(WW, WH, (40, 50, 90), (20, 24, 50))
            p = Pincel(WW, WH)
            m.alpha_composite(p.pronto())
            d_ = ImageDraw.Draw(m)
            import video_palavra as vp
            vp.relogio_ponteiros(m, 540, 950, 300, (T - 96.6) * 60, (T - 96.6) * 720)
            f = self.cam(m, 540, 1000, 1.0)
            self.txt(f, "CONTANDO AS HORAS", 96.9, 0.1, 54, (255, 255, 255))
            self.txt(f, "ATÉ ÀS SEIS", 98.0, 0.18, 70, (255, 214, 40))
            return f

        @B(99.3)
        def chovia(t, d, T):
            f = self.praca_cena(t, "chuva", ne="triste", re="triste", chuva=True, z=1.12)
            self.txt(f, "QUANDO CHOVIA E ELA NÃO VINHA", 99.5, 0.1, 36, (255, 255, 255))
            self.txt(f, "ERA O PIOR DIA", 101.5, 0.17, 54, (255, 130, 140))
            return f

        @B(103.42)
        def domingo(t, d, T):
            f = self.praca_cena(t, "tarde", ne="triste", re="neutro", moca=540, me="chora", z=1.15)
            self.balao_t(f, "Em sete dias faz um ano", OUT_W * 0.55, OUT_H * 0.1, 106.0)
            self.balao_t(f, "que eu tô sozinha.", OUT_W * 0.5, OUT_H * 0.18, 108.3)
            return f

        @B(110.46)
        def gritar(t, d, T):
            m = self.fundo_blur("pr", praca("tarde"))
            self.av(m, t, 540, 2250, 2.6, expr="surpreso")
            f = self.cam(m, 540, 1000, 1.0)
            self.txt(f, "QUERIA ME ARRANCAR DA TERRA", 110.7, 0.1, 40, (255, 255, 255))
            self.txt(f, "E SEGURAR A MÃO DELA", 112.6, 0.17, 44, (255, 214, 40))
            return f

        @B(114.98)
        def contando(t, d, T):
            f = self.praca_cena(t, "tarde", ne="triste", re="neutro", moca=540, me="triste", z=1.15)
            self.txt(f, "ELA CONTAVA OS DIAS", 115.2, 0.1, 50, (255, 255, 255))
            self.txt(f, "IGUAL EU CONTEI", 117.3, 0.17, 54, (255, 214, 40))
            return f

        @B(119.86)
        def entendia(t, d, T):
            m = self.fundo_blur("pr", praca("tarde"))
            self.av(m, t, 540, 2250, 2.6, expr="chora")
            f = self.cam(m, 540, 1000, 1.0)
            self.txt(f, "ALGUÉM AQUI ENTENDIA", 120.0, 0.1, 50, (255, 255, 255))
            return f

        @B(123.24)
        def tres_dias(t, d, T):
            f = self.praca_cena(t, "tarde", ne="neutro", re="neutro", moca=540, me="neutro", z=1.12)
            self.txt(f, "FALTANDO 3 DIAS", 123.4, 0.1, 64, (255, 214, 40))
            return f

        @B(126.74)
        def coragem(t, d, T):
            f = self.praca_cena(t, "tarde", ne="surpreso", re="neutro", moca=330, me="feliz", mpose="entrega",
                                sentada=False, z=1.2, cx=400)
            self.balao_t(f, "Eu vou ter coragem.", OUT_W * 0.55, OUT_H * 0.12, 129.5)
            return f

        @B(132.66)
        def faltando_um(t, d, T):
            f = self.praca_cena(t, "chuva", ne="triste", re="triste", chuva=True, z=1.12)
            self.txt(f, "FALTANDO 1 DIA", 132.9, 0.1, 64, (255, 255, 255))
            self.txt(f, "ELA NÃO APARECEU", 134.0, 0.18, 50, (255, 130, 140))
            return f

        @B(135.42)
        def noite_rua(t, d, T):
            f = self.praca_cena(t, "noite", ne="triste", re="triste", z=1.12)
            self.txt(f, "A NOITE INTEIRA OLHANDO PRA RUA", 135.6, 0.1, 36, (255, 255, 255))
            return f

        @B(138.0)
        def setimo(t, d, T):
            x = 1100 - 560 * ease_out(min(1, (T - 138.0) / 3.0))
            f = self.praca_cena(t, "tarde", ne="surpreso", re="neutro", moca=int(x), me="feliz",
                                mpose="anda" if T < 141.0 else "idle", sentada=False, z=1.12)
            f = f
            self.txt(f, "SÉTIMO DIA", 138.2, 0.1, 70, (255, 214, 40))
            self.txt(f, "DE VESTIDO E CABELO ARRUMADO", 140.0, 0.18, 36, (255, 255, 255))
            return f

        @B(142.74)
        def vergonha(t, d, T):
            f = self.praca_cena(t, "tarde", ne="neutro", re="neutro", moca=540, me="triste", z=1.15)
            self.balao_t(f, "Tenho vergonha de nunca", OUT_W * 0.55, OUT_H * 0.1, 144.5)
            self.balao_t(f, "ter tido coragem antes.", OUT_W * 0.5, OUT_H * 0.18, 146.5)
            return f

        @B(149.56)
        def abraca_rodrigo(t, d, T):
            m = praca("tarde").copy()
            self.av(m, t, 260, 1720, 1.1, expr="surpreso")
            self.ar(m, t, 760, 1720, 1.2, expr="surpreso")
            self.moca(m, t, 560, 1800, 1.2, expr="feliz", pose="abraca_d")
            f = self.cam(m, 540, 1250, 1.12)
            self.txt(f, "ELA ABRAÇOU O RODRIGO", 150.0, 0.1, 50, (255, 214, 40))
            return f

        @B(153.52)
        def mexeu(t, d, T):
            m = praca("tarde").copy()
            self.av(m, t, 260, 1720, 1.1, expr="surpreso")
            ro = self.outro if T > 155.0 else self.ar
            if T < 155.0:
                self.ar(m, t, 700, 1720, 1.2, expr="surpreso")
            else:
                self.outro(m, t, 700, 1800 + 60 * ease_out(min(1, (T - 155.0) / 1.0)), 1.2, expr="chora", pose="idle")
            self.moca(m, t, 480, 1800, 1.2, expr="feliz", pose="abraca_d")
            f = self.cam(m, 540, 1250, 1.12)
            self.txt(f, "MEXEU OS DEDOS", 153.7, 0.1, 54, (255, 255, 255))
            self.txt(f, "CAIU DE JOELHOS CHORANDO", 155.8, 0.17, 40, (255, 214, 40))
            return f

        @B(158.34)
        def passava(t, d, T):
            m = praca("tarde").copy()
            self.av(m, t, 260, 1720, 1.1, expr="triste")
            self.outro(m, t, 760, 1800, 1.2, expr="chora", pose="abraca_e")
            self.moca(m, t, 560, 1800, 1.2, expr="feliz", pose="abraca_d")
            f = self.cam(m, 600, 1250, 1.15)
            self.balao_t(f, "Eu passava aqui todo dia,", OUT_W * 0.5, OUT_H * 0.1, 160.5)
            self.balao_t(f, "você nunca reparou em mim?", OUT_W * 0.5, OUT_H * 0.18, 163.96)
            return f

        @B(165.54)
        def nome(t, d, T):
            m = praca("tarde").copy()
            self.av(m, t, 260, 1720, 1.1, expr="triste")
            self.outro(m, t, 760, 1800, 1.2, expr="surpreso")
            self.moca(m, t, 480, 1800, 1.2, expr="feliz")
            f = self.cam(m, 600, 1250, 1.15)
            self.balao_t(f, "Qual é o seu nome?", OUT_W * 0.55, OUT_H * 0.14, 166.0)
            return f

        @B(170.32)
        def riu(t, d, T):
            m = praca("tarde").copy()
            self.av(m, t, 260, 1720, 1.1, expr="triste")
            self.outro(m, t, 760, 1800, 1.2, expr="feliz")
            self.moca(m, t, 480, 1800, 1.2, expr="ri", pose="bracos_abertos")
            f = self.cam(m, 600, 1250, 1.15)
            self.txt(f, "ELA RIU, CHORANDO", 170.5, 0.1, 50, (255, 255, 255))
            return f

        @B(173.22 - 0.0)
        def embora(t, d, T):
            m = praca("tarde").copy()
            self.av(m, t, 260, 1720, 1.1, expr="triste")
            x = 700 + 450 * ease_in((T - 173.0) / 3.0) if False else 700 + 450 * min(1, max(0, (T - 173.0) / 3.0))
            self.outro(m, t, x, 1800, 1.1, expr="feliz", pose="anda", sx=-1)
            self.moca(m, t, x - 200, 1800, 1.1, expr="feliz", pose="anda", sx=-1)
            laco(m, x - 200, 1800 - 300 * 1.1, 0.7, (250, 205, 60), 0)
            f = self.cam(m, 540, 1250, 1.1)
            self.txt(f, "DE MÃO DADA", 173.4, 0.1, 64, (255, 255, 255))
            return f

        @B(176.68)
        def sabia(t, d, T):
            m = self.fundo_blur("pr", praca("tarde"))
            self.av(m, t, 540, 2250, 2.6, expr="chora")
            f = self.cam(m, 540, 1000, 1.0)
            self.txt(f, "ELE NÃO SABIA O NOME DELA", 176.8, 0.1, 40, (255, 255, 255))
            self.txt(f, "EU SABIA TUDO", 178.5, 0.17, 60, (255, 214, 40))
            return f

        @B(180.5)
        def fim(t, d, T):
            m = praca("tarde").copy()
            self.av(m, t, 540, 1720, 1.3, expr="chora")
            laco(m, 540, 1330, 1.0, (250, 205, 60), 0) if False else None
            f = self.cam(m, 540, 1250, 1.12)
            self.txt(f, "NADA DAQUILO ERA PRA MIM", 181.0, 0.1, 40, (255, 130, 140))
            k = max(0, (t - (d - 1.5)) / 1.5)
            if k > 0:
                f = Image.blend(f, Image.new("RGB", f.size, (0, 0, 0)), min(1, k))
            return f

        R.sort(key=lambda x: x[0])
        return R


def ease_in(x):
    return x * x


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
    ev = []
    for i, c in enumerate(filme.sfx_cortes):
        ev.append(("whoosh" if i % 3 == 0 else "pop", c - 0.04))
    ev += [("toc", 24.6), ("brilho", 86.5), ("toc", 103.4), ("brilho", 123.4), ("toc", 135.4), ("brilho", 149.8),
           ("brilho", 155.0), ("brilho", 166.0), ("toc", 180.5)]
    for tipo, t0 in ev:
        s = g.sfx(tipo) * (0.25 if tipo in ("whoosh", "pop") else 0.8)
        a = int(max(0, t0) * SR)
        b = min(n, a + len(s))
        mix[a:b] += s[: b - a]
    fade = int(SR * 1.2)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = mix / max(1.0, np.abs(mix).max() / 0.95)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def carregar_palavras(caminho):
    troca = {"virá": "vira", "Árvore,": "árvore,", "ximelo,": "chinelo,", "enxado": "inchado", "divestido,": "de vestido,",
             "Divestido": "De vestido"}
    out = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            out.append(dict(w=troca.get(w["w"], w["w"]), s=w["s"], e=w["e"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--camera", required=True)
    ap.add_argument("--ancoras", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_arvore_da_praca.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    ap.add_argument("--de", type=float, default=None)
    ap.add_argument("--ate", type=float, default=None)
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    cam = json.load(open(a.camera))
    anc = json.load(open(a.ancoras))
    filme = FilmeArvore(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.4, a.narracao, cam, anc)
    total = int(filme.dur_total * FPS)

    if a.testar:
        for ini, d, *_r in filme.planos:
            for k in (0.01, 0.5, 0.99):
                filme.frame(int((ini + d * k) * FPS))
        print(f"todos os planos ok — {len(filme.planos)} cenas em {filme.dur_total:.1f}s")
        return
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        for i, (ini, d, *_r) in enumerate(filme.planos):
            filme.frame(int((ini + d * 0.6) * FPS)).save(os.path.join(a.preview, f"cena_{i:03d}.png"))
        print("preview em", a.preview, len(filme.planos), "cenas")
        return

    tmp = tempfile.mkdtemp(prefix="arvore_")
    wav = os.path.join(tmp, "mix.wav")
    mixar(filme, a.narracao, wav)
    n0 = int((a.de or 0) * FPS)
    n1 = int(a.ate * FPS) if a.ate else total
    if a.de or a.ate:
        tr = os.path.join(tmp, "trecho.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.de or 0), "-t", str((n1 - n0) / FPS), "-i", wav, tr],
                       check=True)
        wav = tr
    print(f"• renderizando {total} frames ({filme.dur_total:.1f}s)…", flush=True)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}",
         "-r", str(FPS), "-i", "-", "-i", wav, "-vf", "scale=1080:1920:flags=lanczos",
         "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-maxrate", "6M", "-bufsize", "12M",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.saida],
        stdin=subprocess.PIPE)
    for n in range(n0, n1):
        proc.stdin.write(filme.frame(n).tobytes())
        if n % 150 == 0:
            print(f"  {n}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("✔ vídeo salvo em", a.saida)


if __name__ == "__main__":
    main()
