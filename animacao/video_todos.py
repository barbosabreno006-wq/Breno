#!/usr/bin/env python3
"""
"Todo Mundo Me Ama" — numa cidade todo mundo é apaixonado pelo narrador, mas é a Admiradora (alta, sem rosto,
sorriso enorme, coração no peito) que mexe com a cabeça de todos. Quem para de amar some.

Feito no estilo da referência "cidade de cegos" (mesma grade de cortes e movimentos de câmera, medidos por ORB):
  * 41 cortes (grade da referência, encaixada nas palavras da narração) e câmera por cena;
  * cada cena com lugar e objetos próprios; só legenda + balões de fala.

    python3 animacao/video_todos.py --narracao n.mp3 --transcricao t.json --camera camera.json --fonte Poppins.ttf
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
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_video as g  # noqa: E402
import video_carta as vc  # noqa: E402
import video_estatua as ve  # noqa: E402
import video_areia as va  # noqa: E402
import ambiente as amb  # noqa: E402
import boneco  # noqa: E402
import cenario_rico as cr  # noqa: E402
import cenario_escola as cs  # noqa: E402
import cenario_selo as cz  # noqa: E402
import cenario_amor as ca  # noqa: E402
import efeitos as ef  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io)

g.HANDHELD = False
g.PERMITE_FLIP = False
boneco.Boneco.AMP = 1.7
boneco.Boneco.SHADE = 1.0
g.GRAO = 0.6
random.seed(4242)

NARR = dict(pele=(232, 186, 150), cabelo=(70, 44, 32), camisa=(70, 130, 220), calca=(60, 70, 110),
            sapato=(240, 240, 245), tipo="menino", cabelo_estilo="topete", iris=(70, 110, 190), bolso=True)
LIA = dict(pele=(150, 100, 70), cabelo=(30, 24, 26), camisa=(90, 180, 130), calca=(0, 0, 0), sapato=(230, 230, 235),
           tipo="moca", vestido=(90, 180, 130), cabelo_estilo="trancas", iris=(60, 40, 30), brinco=(250, 210, 60))
ALVARO = dict(pele=(214, 164, 126), cabelo=(200, 200, 206), camisa=(170, 120, 80), calca=(80, 70, 70),
              sapato=(60, 50, 45), tipo="pai", bigode=True, cabelo_estilo="ralo", oculos=True, colete=(110, 90, 70))
MAE_LIA = dict(pele=(150, 100, 70), cabelo=(30, 24, 26), camisa=(210, 120, 60), calca=(0, 0, 0), sapato=(110, 80, 60),
               tipo="moca", vestido=(210, 120, 60), cabelo_estilo="coque")
vc.DESTAQUE_VERMELHO = set()
_C = {}
_T = {}


class FilmeTodos(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao, camera, ancoras):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.narr, self.lia, self.alv, self.mae = P_(NARR), P_(LIA), P_(ALVARO), P_(MAE_LIA)
        self.kids = [P_(c) for c in ve.POVO]
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.cortes = [(0.0, 0)]
        self.spec, self.u, self.sub = None, 0.0, 0
        self.dlg = {"narr": [(38.44, 39.9)], "lia": [(47.40, 49.0)], "povo": [(35.82, 36.2)]}
        self.inicios = np.array([w["s"] for w in palavras])
        self.beats = self._beats()
        ra = np.array([a for a, _ in ancoras])
        oa = np.array([b for _, b in ancoras])
        n = len(camera)
        iniciais = []
        for i, c in enumerate(camera):
            a = 0.0 if i == 0 else self._encaixar(float(np.interp(c["ini"], ra, oa)))
            iniciais.append(a)
        iniciais = [0.0] + [max(iniciais[i], iniciais[i - 1] + 0.3) for i in range(1, n)]
        fins = iniciais[1:] + [dur_total]
        sub_cont, ult = {}, []
        for a, b in zip(iniciais, fins):
            bi = self._achar_idx((a + b) / 2)
            sub_cont[bi] = sub_cont.get(bi, -1) + 1
            ult.append((bi, sub_cont[bi]))
        self.planos, self.sfx_cortes = [], []
        iris_em = {"b_reveal", "b_vazia", "b_lia", "b_escola", "b_orelha", "b_cinco_anos", "b_fim"}
        for i, (a, b) in enumerate(zip(iniciais, fins)):
            bi, sub = ult[i]
            tr = "iris" if (sub == 0 and self.beats[bi][1].__name__ in iris_em) else "corte"
            self.planos.append((a, max(0.2, b - a), self._fazer(i, camera[i], ult[i]), "", tr))
            if i:
                self.sfx_cortes.append(a)
        self.p_preto = None

    def _encaixar(self, t):
        """Puxa o corte para o início de palavra mais próximo (até 0.3 s)."""
        j = int(np.argmin(np.abs(self.inicios - t)))
        return float(self.inicios[j]) if abs(self.inicios[j] - t) < 0.3 else t

    # ----- câmera copiada da referência -----
    def spec_de(self, i, c):
        r = c.get("r", 0)
        z, dx, dy = c.get("zoom", 1.0), c.get("dx", 0.0), c.get("dy", 0.0)
        if r >= 0.4 and 0.7 <= z <= 1.6 and abs(dx) < 0.35 and abs(dy) < 0.35:
            return min(1.35, max(0.8, z)), max(-0.15, min(0.15, dx)), max(-0.15, min(0.15, dy))
        return (1.07 if i % 2 == 0 else 0.95), 0.0, 0.0

    def _fazer(self, i, c, bs):
        z, dx, dy = self.spec_de(i, c)
        bi, sub = bs

        def fn(t, d):
            self.spec = (z, dx, dy)
            self.u = ease_io(min(1, t / max(0.1, d)))
            self.sub = sub
            return self.beats[bi][1](t, d, self.T)
        return fn

    def cam(self, m, cx, cy, zb):
        z, dx, dy = self.spec if self.spec else (1.0, 0, 0)
        u = self.u
        s = self.sub
        cx = cx + (-1, 0, 1)[s % 3] * 70
        zb = zb * (1.0, 1.12, 1.25, 1.06)[s % 4]
        zz = zb * (1 + (z - 1) * u) if z >= 1 else zb / z * (z ** u)
        vw, vh = WW / zz, WH / zz
        return g.camera(m, cx - dx * u * vw, cy - dy * u * vh, zz)

    def _achar_idx(self, t):
        idx = 0
        for i, (ini, _) in enumerate(self.beats):
            if ini <= t:
                idx = i
        return idx

    # ----- utilidades de cena -----
    def balao_t(self, f, txt, x, y, t0):
        if self.T >= t0:
            self.balao(f, txt, x, y, self.T - t0)

    def S(self, bg, chars=(), props=(), cam=(540, 1250, 1.3), t=0.0, bal=(), fx=None, front=()):
        m = bg.copy()
        for pers, x, by, e, expr, pose, fala, sx in chars:
            cr.sombra(m, x, by - 4, e * 250)
            pers(m, t, x, by, e, expr=expr, pose=pose, fala=fala, sx=sx)
        for pr in props:
            pr(m)
        for pr in front:
            pr(m)
        f = self.cam(m, *cam)
        for txt, x, y, t0 in bal:
            if len(txt) > 24:
                w_ = txt.split(" ")
                mid = len(txt) / 2
                acum, cut = 0, len(w_) // 2
                for i_, p_ in enumerate(w_):
                    acum += len(p_) + 1
                    if acum >= mid:
                        cut = i_ + 1
                        break
                self.balao_t(f, " ".join(w_[:cut]), x, y, t0)
                self.balao_t(f, " ".join(w_[cut:]), x, y + OUT_H * 0.085, t0 + 0.25)
            else:
                self.balao_t(f, txt, x, y, t0)
        if fx:
            f = fx(f)
        return f

    def C(self, pers, x, by, e=1.4, expr="neutro", pose="idle", fala=None, sx=1):
        return (pers, x, by, e, expr, pose, fala, sx)

    def img(self, im, x, y, rot=0.0):
        def f(m):
            i2 = im.rotate(rot, expand=True, resample=Image.BICUBIC) if rot else im
            m.alpha_composite(i2, (int(x - i2.width / 2), int(y - i2.height / 2)))
        return f

    def adm(self, x, by, h=1500, t=0.0, boca=1.0, giro=0.0):
        def f(m):
            im = ca.admiradora(h, 0.5 + 0.5 * math.sin(t * 5.5), boca, giro)
            cr.sombra(m, x, by - 4, h * 0.22)
            m.alpha_composite(im, (int(x - im.width / 2), int(by - im.height)))
        return f

    def cor_bal(self, x, y, t, n=5, w=44, seed=1):
        def f(m):
            ca.coracoes_flutuando(m, t, x, y, n, w, seed)
        return f

    # ----- cenários -----
    def rua(self, hora="dia"):
        k = ("rua", hora)
        if k not in _T:
            _T[k] = cr.praca_rica(self.fc, "dia" if hora == "dia" else "noite").copy()
        return _T[k]

    def casa_noite(self):
        if "casan" not in _T:
            _T["casan"] = ca.noite(cz.fachada(self.fc, "CASA", (220, 190, 170), (150, 60, 90)), 0.5)
        return _T["casan"]

    def casa_dia(self):
        if "casad" not in _T:
            _T["casad"] = cz.fachada(self.fc, "CASA", (220, 190, 170), (150, 60, 90))
        return _T["casad"]

    def quarto(self):
        return cz.quarto_simples(self.fc, False, True)

    def fundo_rosa(self, a=(96, 30, 78), b=(40, 12, 40)):
        k = ("rosa", a)
        if k not in _T:
            _T[k] = gradiente(WW, WH, a, b)
        return _T[k]

    # ----- beats -----
    def _beats(self):  # noqa: C901
        R = []

        def B(ini):
            def deco(fn):
                R.append((ini, fn))
                return fn
            return deco

        C, K = self.C, self.kids
        narr, lia, alv, mae = self.narr, self.lia, self.alv, self.mae

        def multidao(ini_x=140, n=5, esp=210, expr="feliz", pose="acena", e=1.0, base=1830):
            return [C(K[i % len(K)], ini_x + i * esp, base, e, expr, pose) for i in range(n)]

        @B(0.0)
        def b_cidade(t, d, T):
            bg = self.rua().copy()
            amb.nuvens(bg, t, n=4, seed=3)
            chars = [C(narr, 300, 1840, 1.3, "feliz", "idle")] + multidao(560, 4, 170, "feliz", "acena", 1.0)
            return self.S(bg, chars, cam=(540, 1350, 1.2), t=t, front=[self.cor_bal(300, 1100, t, 6, 50, 1),
                                                                      self.cor_bal(720, 1150, t, 4, 40, 2)])

        @B(1.04)
        def b_apaixonado(t, d, T):
            bg = self.rua()
            return self.S(bg, [C(narr, 540, 1860, 1.9, "surpreso", "idle")], cam=(540, 1250, 1.3), t=t,
                          front=[self.cor_bal(540, 1000, t, 7, 54, 3)])

        @B(3.12)
        def b_todo_mundo(t, d, T):
            bg = self.rua()
            chars = multidao(120, 6, 180, "feliz", "bracos_abertos", 0.95)
            return self.S(bg, chars, cam=(540, 1350, 1.2), t=t, front=[self.cor_bal(540, 1150, t, 9, 46, 4)])

        @B(4.00)
        def b_nao_tem(t, d, T):
            return self.S(self.rua(), [C(narr, 420, 1860, 1.9, "surpreso", "idle")], cam=(540, 1250, 1.3), t=t,
                          front=[self.cor_bal(760, 1100, t, 5, 50, 5)])

        @B(6.12)
        def b_esperam(t, d, T):
            chars = [C(K[i % 5], 180 + i * 190, 1840, 1.2, "feliz", "idle") for i in range(5)]
            return self.S(self.casa_noite(), chars, cam=(540, 1250, 1.15), t=t)

        @B(8.74)
        def b_sorrindo(t, d, T):
            chars = [C(K[0], 300, 1860, 1.9, "feliz", "idle"), C(K[1], 800, 1860, 1.9, "feliz", "idle")]
            return self.S(self.casa_noite(), chars, cam=(540, 1250, 1.3), t=t)

        @B(10.40)
        def b_presente(t, d, T):
            pres = lambda m: m.alpha_composite(ca.presente(260), (620, 1380))  # noqa: E731
            return self.S(self.casa_noite(), [C(K[3], 380, 1840, 1.5, "feliz", "entrega"),
                                              C(K[4], 880, 1830, 1.1, "feliz", "idle")], [pres], (540, 1250, 1.2), t)

        @B(12.04)
        def b_nunca_embora(t, d, T):
            chars = [C(K[i % 5], 130 + i * 160, 1830, 1.15, "feliz", "idle") for i in range(6)]
            return self.S(self.casa_noite(), chars, cam=(540, 1300, 1.15), t=t)

        @B(13.54)
        def b_sei_porque(t, d, T):
            return self.S(self.quarto(), [C(narr, 460, 1860, 1.9, "neutro", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(14.82)
        def b_atras(t, d, T):
            chars = [C(K[i % 5], 170 + i * 200, 1850, 1.0, "feliz", "idle") for i in range(5)]
            return self.S(self.rua("noite"), chars, front=[self.adm(540, 1650, 1250, t)], cam=(540, 1200, 1.1), t=t)

        @B(17.14)
        def b_reveal(t, d, T):
            return self.S(self.rua("noite"), [], front=[self.adm(540, 1860, 1700, t)], cam=(540, 1000, 1.05), t=t)

        @B(19.16)
        def b_sem_rosto(t, d, T):
            im = ca.cabeca_admiradora(720, 0.4)
            return self.S(self.fundo_rosa(), props=[self.img(im, 540, 1000)], cam=(540, 1000, 1.0), t=t)

        @B(20.06)
        def b_sorriso(t, d, T):
            im = ca.cabeca_admiradora(760, 1.0 + 0.1 * math.sin(t * 3))
            return self.S(self.fundo_rosa(), props=[self.img(im, 540, 1000)], cam=(540, 1000, 1.0), t=t)

        @B(21.52)
        def b_coracao(t, d, T):
            im = ca.coracao(560, (236, 46, 90), 0.5 + 0.5 * math.sin(t * 7))
            gl = brilho((1000, 1000), (255, 80, 120), 460, 0.8)
            return self.S(self.fundo_rosa((60, 14, 36), (20, 6, 16)),
                          props=[self.img(gl, 540, 960), self.img(im, 540, 960)], cam=(540, 960, 1.0), t=t)

        @B(23.56)
        def b_mexe(t, d, T):
            xs = [160 + i * 190 for i in range(5)]
            chars = [C(K[i % 5], x, 1850, 1.0, "feliz", "idle") for i, x in enumerate(xs)]
            alvos = [(x, 1850 - 470 * 1.0 - 20) for x in xs]
            fio = lambda m: ca.fios(m, (540, 560), alvos, t)  # noqa: E731
            return self.S(self.rua("noite"), chars, [fio], (540, 1200, 1.1), t, front=[self.adm(540, 1100, 1300, t)])

        @B(25.86)
        def b_para(t, d, T):
            chars = [C(K[2], 300, 1860, 1.8, "triste", "idle"), C(K[0], 820, 1850, 1.2, "feliz", "idle")]
            return self.S(self.rua("noite"), chars, cam=(540, 1250, 1.25), t=t, front=[self.adm(960, 1500, 1300, t)])

        @B(27.40)
        def b_leva(t, d, T):
            return self.S(self.rua("noite"), [C(K[2], 360, 1850, 1.5, "chora", "idle")], cam=(540, 1250, 1.2), t=t,
                          front=[self.adm(760, 1750, 1500, t, 1.0, 0.5)])

        @B(28.34)
        def b_alvaro(t, d, T):
            return self.S(self.casa_dia(), [C(alv, 540, 1860, 1.8, "feliz", "acena")], cam=(540, 1250, 1.3), t=t)

        @B(30.32)
        def b_feio(t, d, T):
            return self.S(self.casa_dia(), [C(alv, 300, 1860, 1.5, "bravo", "aponta", None, 1),
                                            C(narr, 840, 1850, 1.3, "surpreso", "idle", None, -1)],
                          cam=(540, 1250, 1.2), t=t)

        @B(32.16)
        def b_vazia(t, d, T):
            bg = ca.noite(cz.fachada(self.fc, "CASA", (200, 190, 180), (100, 100, 100)), 0.3)
            return self.S(bg, [C(narr, 300, 1850, 1.2, "surpreso", "idle", None, -1)], cam=(540, 1250, 1.15), t=t)

        @B(34.30)
        def b_quem(t, d, T):
            chars = [C(K[i % 5], 160 + i * 190, 1840, 1.1, "surpreso", "idle", self.dlg["povo"]) for i in range(5)]
            return self.S(self.rua(), chars, cam=(540, 1300, 1.15), t=t,
                          bal=[("Quem?", OUT_W * 0.5, OUT_H * 0.12, 35.82)])

        @B(36.26)
        def b_sorrio(t, d, T):
            return self.S(self.quarto(), [C(narr, 540, 1860, 1.9, "feliz", "idle", self.dlg["narr"])], cam=(540, 1250, 1.3),
                          t=t)

        @B(38.44)
        def b_amo(t, d, T):
            return self.S(self.rua(), [C(narr, 540, 1860, 1.8, "feliz", "bracos_abertos", self.dlg["narr"])],
                          cam=(540, 1250, 1.25), t=t,
                          bal=[("Eu também amo vocês!", OUT_W * 0.5, OUT_H * 0.1, 38.44)],
                          front=[self.cor_bal(540, 1000, t, 6, 50, 6)])

        @B(40.02)
        def b_lia(t, d, T):
            return self.S(self.rua(), [C(lia, 540, 1860, 1.8, "neutro", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(41.72)
        def b_nao_gostava(t, d, T):
            return self.S(cs.sala_aula(self.fc), [C(lia, 540, 1860, 1.9, "bravo", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(43.08)
        def b_unica(t, d, T):
            chars = [C(lia, 280, 1850, 1.5, "neutro", "idle", None, 1)] + \
                [C(K[i], 640 + i * 170, 1830, 1.0, "feliz", "idle") for i in range(3)]
            return self.S(cs.sala_aula(self.fc), chars, cam=(540, 1250, 1.2), t=t)

        @B(44.90)
        def b_chave(t, d, T):
            ch = lambda m: m.alpha_composite(ca.chave(260, 12), (560, 1430))  # noqa: E731
            return self.S(self.rua(), [C(lia, 300, 1850, 1.5, "neutro", "entrega"), C(narr, 800, 1850, 1.4, "feliz", "idle",
                                                                                     None, -1)], [ch], (540, 1250, 1.15), t)

        @B(46.36)
        def b_cochichou(t, d, T):
            return self.S(self.rua(), [C(lia, 380, 1860, 1.9, "neutro", "idle", self.dlg["lia"], 1)], cam=(540, 1250, 1.3), t=t,
                          bal=[("Guarda pra quando você quiser sair.", OUT_W * 0.52, OUT_H * 0.1, 47.40)])

        @B(49.28)
        def b_fugir(t, d, T):
            x = 300 + 520 * ease_io(min(1, (T - 49.3) / 1.5))
            return self.S(cs.corredor(self.fc, "SAÍDA"), [C(lia, x, 1840, 1.4, "surpreso", "corre", None, 1)],
                          cam=(540, 1250, 1.15), t=t)

        @B(50.68)
        def b_parou(t, d, T):
            chars = [C(K[i % 5], 130 + i * 170, 1830, 1.1, "neutro", "idle") for i in range(6)]
            return self.S(self.rua("noite"), chars, cam=(540, 1300, 1.15), t=t)

        @B(53.06)
        def b_virou(t, d, T):
            return self.S(self.rua("noite"), [C(K[1], 360, 1860, 1.9, "neutro", "idle", None, -1),
                                              C(K[4], 840, 1860, 1.7, "neutro", "idle", None, -1)], cam=(540, 1250, 1.3), t=t)

        @B(54.52)
        def b_manha(t, d, T):
            bg = cs.sala_aula(self.fc)
            return self.S(bg, [], [lambda m: m.alpha_composite(cs.carteira(520), (140, 1500))], (540, 1250, 1.2), t)

        @B(55.56)
        def b_vazio(t, d, T):
            return self.S(cs.sala_aula(self.fc), [C(K[3], 800, 1840, 1.2, "neutro", "idle")],
                          [lambda m: m.alpha_composite(cs.carteira(560), (110, 1500))], (540, 1300, 1.15), t)

        @B(57.46)
        def b_aprendi(t, d, T):
            return self.S(self.quarto(), [C(narr, 540, 1860, 1.9, "surpreso", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(58.84)
        def b_nunca_mais(t, d, T):
            return self.S(self.rua(), [C(narr, 460, 1860, 1.8, "feliz", "idle"),
                                       C(K[0], 880, 1840, 1.2, "feliz", "idle")], cam=(540, 1250, 1.25), t=t)

        @B(61.08)
        def b_esqueci(t, d, T):
            return self.S(self.quarto(), [C(narr, 540, 1860, 1.9, "neutro", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(63.40)
        def b_orelha(t, d, T):
            im = ca.cabeca_admiradora(720, 1.0)
            return self.S(self.fundo_rosa((50, 20, 60), (20, 8, 28)),
                          [C(narr, 300, 1860, 1.8, "surpreso", "idle", None, 1)],
                          [self.img(im, 760, 1050, 12)], (540, 1100, 1.0), t)

        @B(65.78)
        def b_tudo_bem(t, d, T):
            im = ca.cabeca_admiradora(720, 1.0)
            return self.S(self.fundo_rosa((50, 20, 60), (20, 8, 28)), props=[self.img(im, 540, 1000)],
                          cam=(540, 1000, 1.0), t=t,
                          bal=[("Tá tudo bem, meu bem?", OUT_W * 0.5, OUT_H * 0.1, 65.78)])

        @B(66.92)
        def b_cinco_anos(t, d, T):
            bg = gradiente(WW, WH, (34, 34, 52), (14, 14, 24))
            im = cr.calendario(self.fc, "ANOS", int(min(5, (T - 66.9) * 2.5)), total=5, w=960, cor_topo=(70, 74, 90))
            return self.S(bg, props=[self.img(im, 540, 960)], cam=(540, 1000, 1.0), t=t)

        @B(68.70)
        def b_chave_bolso(t, d, T):
            ch = lambda m: m.alpha_composite(ca.chave(300, -20), (330, 1380))  # noqa: E731
            return self.S(self.quarto(), [C(narr, 540, 1860, 1.8, "neutro", "bolso")], [ch], (540, 1250, 1.3), t)

        @B(70.86)
        def b_hoje(t, d, T):
            return self.S(self.quarto(), [C(narr, 540, 1860, 1.9, "neutro", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(72.08)
        def b_fim(t, d, T):
            k = max(0, (T - 73.0) / 1.0)
            f = self.S(self.rua("noite"), [C(narr, 540, 1860, 1.9, "feliz", "idle")], cam=(540, 1250, 1.3), t=t,
                       front=[self.adm(900, 1900, 1500, t)])
            return Image.blend(f, Image.new("RGB", f.size, (0, 0, 0)), min(1, k)) if k > 0 else f

        R.sort(key=lambda x: x[0])
        return R


# --------------------------------------------------------------------------
def mixar(filme, narracao, saida):
    import som
    SR = som.SR
    voz = vc.ler_wav_mono(narracao)
    dur = filme.dur_total
    ev = []
    for i, c in enumerate(filme.sfx_cortes):
        ev.append(("whoosh" if i % 3 == 0 else "pop", c - 0.04, 0.22 if i % 3 == 0 else 0.2))
    ev += [("hit", 17.14, 0.8), ("riser", 15.8, 0.4), ("hit", 63.5, 0.9), ("hit", 50.7, 0.5), ("hit", 32.2, 0.5)]
    for k in range(8):
        ev.append(("coracao", 21.6 + k * 0.8, 0.7))
    ev += [("pagina", 54.5, 0.3), ("ding", 44.9, 0.4)]
    amb_ = [("cidade", 0.0, 6.0, 0.3), ("noite", 6.0, dur - 1.5, 0.4)]
    picos = [(17.2, 0.9), (26, 0.6), (50.7, 0.7), (63.6, 1.0), (72.0, 0.8)]
    mix = som.mixar_v2(dur, voz, ev, amb_, picos, "triste", 0.2)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def carregar_palavras(caminho):
    troca = {"admiradora,": "Admiradora,", "admiradora": "Admiradora", "coxechou,": "cochichou,"}
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
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_todo_mundo_me_ama.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    ap.add_argument("--de", type=float, default=None)
    ap.add_argument("--ate", type=float, default=None)
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    cam = json.load(open(a.camera))
    ref_dur = cam[-1]["ini"] + cam[-1]["dur"]
    filme = FilmeTodos(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.4, a.narracao, cam,
                       [(0.0, 0.0), (ref_dur, voz_dur)])
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

    tmp = tempfile.mkdtemp(prefix="todos_")
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
         "-c:v", "libx264", "-preset", "medium", "-crf", "26", "-maxrate", "3500k", "-bufsize", "7M",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.saida],
        stdin=subprocess.PIPE)
    import render
    render.renderizar(filme, n0, n1, proc.stdin, progresso=True, total=total)
    proc.stdin.close()
    proc.wait()
    print("✔ vídeo salvo em", a.saida)


if __name__ == "__main__":
    main()
