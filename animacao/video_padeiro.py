#!/usr/bin/env python3
"""
"Eu Dou Uma Todo Dia" — numa cidade todo mundo é apaixonado pelo narrador, mas é a Admiradora (alta, sem rosto,
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
import cenario_apagador as ca2  # noqa: E402
import cenario_cao as cc_  # noqa: E402
import cenario_quatro as qq_  # noqa: E402
import cenario_padeiro as pdr_  # noqa: E402
import cenario_porao as pc_  # noqa: E402
import cenario_porao as pz_  # noqa: E402
import cenario_amor as ca_  # noqa: E402
import cao as cao_  # noqa: E402
import efeitos as ef  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io)

g.HANDHELD = False
g.PERMITE_FLIP = False
boneco.Boneco.AMP = 2.4
boneco.Boneco.SHADE = 1.0
g.GRAO = 0.6
random.seed(4242)

RAI = dict(pele=(222, 176, 140), cabelo=(226, 226, 232), camisa=(250, 250, 250), calca=(80, 84, 104), sapato=(60, 50, 45),
           tipo="pai", bigode=True, cabelo_estilo="ralo", oculos=False, chapeu=(250, 250, 250), avental=(255, 255, 255),
           iris=(80, 60, 40))
DAN = dict(pele=(206, 156, 116), cabelo=(40, 30, 28), camisa=(70, 74, 96), calca=(40, 44, 62), sapato=(40, 40, 48),
           tipo="pai", bigode=False, iris=(60, 40, 30), gorro=(60, 64, 86))
DANJ = dict(pele=(206, 156, 116), cabelo=(40, 30, 28), camisa=(250, 250, 252), calca=(70, 150, 170), sapato=(240, 240, 245),
            tipo="pai", bigode=False, iris=(60, 40, 30), gravata=(70, 150, 170))
DANM = dict(pele=(206, 156, 116), cabelo=(40, 30, 28), camisa=(90, 90, 110), calca=(60, 60, 80), sapato=(200, 200, 205),
            tipo="menino", cabelo_estilo="topete", iris=(60, 40, 30))
ENF = dict(pele=(150, 100, 70), cabelo=(30, 24, 26), camisa=(240, 246, 250), calca=(0, 0, 0), sapato=(240, 240, 245),
           tipo="moca", vestido=(240, 246, 250), cabelo_estilo="coque", iris=(60, 40, 30))
vc.DESTAQUE_VERMELHO = set()
_C = {}
_T = {}


def cz_ponte_rua(f):  # noqa: E301
    if "ruanoite" not in _T:
        _T["ruanoite"] = ca.noite(f.rua().copy(), 0.6)
    return _T["ruanoite"]


IRIS = {"b_pergunta_none", "b_forno", "b_graca", "b_homem", "b_hospital", "b_gaveta", "b_menino", "b_ontem"}


MAPA = None      # {"delta", "ini_novo", "bato_novo", "bato_velho", "fim_velho"}: encaixe da nova abertura


def to_old(t):
    """Tempo do vídeo (novo) -> tempo da linha do tempo original das cenas."""
    m = MAPA
    if m is None:
        return t
    if t >= m["ini_novo"]:
        return t - m["delta"]
    if t >= m["bato_novo"]:
        return m["bato_velho"] + (t - m["bato_novo"]) * (m["fim_velho"] - m["bato_velho"]) / (m["ini_novo"] - m["bato_novo"])
    return t * m["bato_velho"] / m["bato_novo"]


def to_new(t):
    m = MAPA
    if m is None:
        return t
    if t >= m["fim_velho"]:
        return t + m["delta"]
    if t >= m["bato_velho"]:
        return m["bato_novo"] + (t - m["bato_velho"]) * (m["ini_novo"] - m["bato_novo"]) / (m["fim_velho"] - m["bato_velho"])
    return t * m["bato_novo"] / m["bato_velho"]


class FilmeTodos(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao, camera, ancoras):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.rai, self.dan, self.danj, self.danm, self.enf = P_(RAI), P_(DAN), P_(DANJ), P_(DANM), P_(ENF)
        self.kids = [P_(c) for c in ve.POVO]
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.cortes = [(0.0, 0)]
        self.spec, self.u, self.sub = None, 0.0, 0
        self.dlg = {"abre": [(0.0, 2.6)], "calma": [(2.9, 4.2)], "enf": [(41.3, 42.2), (42.2, 46.4)], "rai2": [(69.9, 72.2)]}
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
        # cortes = grade da referência + início de cada cena (nenhuma cena fica sem aparecer e cada uma começa na sua frase)
        bt = [b_ for b_, _ in self.beats]
        cand = [(a_, i_) for i_, a_ in enumerate(iniciais) if i_ > 0 and min(abs(a_ - x_) for x_ in bt) > 1.5] + \
            [(b_, None) for b_ in bt if b_ > 0.2]
        cand.sort(key=lambda x: (x[0], x[1] is None))
        cortes = [(0.0, 0)]
        for tt, idx in cand:
            if tt - cortes[-1][0] < 0.45:
                if idx is None:
                    cortes[-1] = (tt, cortes[-1][1])
                continue
            cortes.append((tt, idx if idx is not None else self._cam_idx(iniciais, tt)))
        fins = [c[0] for c in cortes[1:]] + [dur_total]
        sub_cont, ult = {}, []
        for (a, ci), b in zip(cortes, fins):
            bi = self._achar_idx(a + 0.05)
            sub_cont[bi] = sub_cont.get(bi, -1) + 1
            ult.append((bi, sub_cont[bi], ci))
        self.planos, self.sfx_cortes = [], []
        iris_em = IRIS
        for i, ((a, ci), b) in enumerate(zip(cortes, fins)):
            bi, sub, _ = ult[i]
            tr = "iris" if (sub == 0 and self.beats[bi][1].__name__ in iris_em) else "corte"
            self.planos.append((a, max(0.2, b - a), self._fazer(i, camera[ci], (bi, sub)), "", tr))
            if i:
                self.sfx_cortes.append(a)
        self.p_preto = None

    @staticmethod
    def _cam_idx(iniciais, t):
        k = 0
        for i, a in enumerate(iniciais):
            if a <= t:
                k = i
        return k

    def frame(self, n):
        if MAPA is None:
            return super().frame(n)
        return super().frame(int(round(to_old(n / FPS) * FPS)))

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
            self.tl = t
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
        cxx, cyy = cx - dx * u * vw, cy - dy * u * vh
        tl = getattr(self, "tl", 0.0)
        if self.T < 11.0:                                   # ABERTURA VIVA: pancada de zoom + tremida + balanço contínuo
            ataque = max(0.0, 1.0 - tl / 0.28)
            zz *= 1 + 0.20 * ataque ** 2 + 0.03 * math.sin(self.T * 5)
            cxx += 16 * math.sin(self.T * 3.1) + 22 * ataque * math.sin(tl * 60)
            cyy += 10 * math.sin(self.T * 2.3) + 16 * ataque * math.cos(tl * 52)
        return g.camera(m, cxx, cyy, zz)

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
        for pr in props:
            if getattr(pr, "_back", False):
                pr(m)
        props = [pr for pr in props if not getattr(pr, "_back", False)]
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

    def quarto_noite(self):
        return cz.quarto_simples(self.fc, False, True)

    def quarto_dia(self):
        return cz.quarto_simples(self.fc, False, False)

    def fundo_noite(self):
        return self.fundo_rosa((24, 28, 66), (10, 12, 30))

    def fundo_cor(self, a, b):
        return self.fundo_rosa(a, b)

    def celular_prop(self):
        if "cel" not in _T:
            p = Pincel(240, 400)
            p.ret((10, 10, 230, 390), (30, 30, 40), r=30)
            p.ret((24, 36, 216, 360), (120, 200, 255), r=14, ow=0)
            p.elipse((90, 300, 150, 350), (220, 60, 70), ow=0)
            _T["cel"] = p.pronto()
        return _T["cel"]

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
        rai, dan, danj, danm, enf = self.rai, self.dan, self.danj, self.danm, self.enf
        pdr = pdr_
        D = self.dlg

        def bal(txt, t0, y=0.1, x=0.5):
            return [(txt, OUT_W * x, OUT_H * y, t0)]

        def prop(img, x, y):
            return lambda m: m.alpha_composite(img, (int(x - img.width / 2), int(y - img.height / 2)))

        pad = lambda n=0: pdr.padaria_interior(self.fc)  # noqa: E731
        alv = lambda: pdr.padaria_alvorada(self.fc)  # noqa: E731
        amarelo = lambda: self.fundo_cor((255, 214, 90), (255, 150, 60))  # noqa: E731
        rosa = lambda: self.fundo_cor((255, 130, 150), (255, 190, 110))  # noqa: E731
        noite = lambda: pdr.rua_noite_poste(self.fc)  # noqa: E731
        rua = lambda: self.rua()  # noqa: E731

        # ---------- ABERTURA VIVA (cortes de ~0,6 a 0,9 s, cores vivas, personagem enorme e animado) ----------
        @B(0.0)
        def b_dou(t, d, T):
            return self.S(pad(), [C(rai, 540, 1860, 2.3, "feliz", "bracos_abertos", D["abre"])], cam=(540, 1250, 1.35), t=t)

        @B(0.55)
        def b_uma(t, d, T):
            return self.S(amarelo(), [C(rai, 330, 1860, 2.0, "surpreso", "entrega", None, 1)],
                          [prop(pdr.pao(560), 780, 1200)], (540, 1250, 1.3), t)

        @B(0.95)
        def b_todo_dia(t, d, T):
            im = ca2.relogio_torre(self.fc, 4, 0, 820)
            return self.S(rosa(), props=[prop(im, 540, 960)], cam=(540, 1000, 1.05), t=t)

        @B(1.40)
        def b_quatro(t, d, T):
            return self.S(rosa(), [C(rai, 540, 1860, 2.2, "ri", "acena")], cam=(540, 1250, 1.3), t=t)

        @B(2.10)
        def b_madrugada(t, d, T):
            return self.S(alv(), [C(rai, 330, 1860, 1.9, "feliz", "bracos_abertos", None, 1)], cam=(540, 1250, 1.2), t=t)

        @B(2.90)
        def b_calma(t, d, T):
            return self.S(amarelo(), [C(rai, 540, 1860, 2.4, "feliz", "acena", D["calma"])], cam=(540, 1250, 1.3), t=t)

        @B(3.50)
        def b_explicar(t, d, T):
            return self.S(rosa(), [C(rai, 540, 1860, 2.2, "ri", "aponta", D["calma"])], cam=(540, 1250, 1.3), t=t)

        @B(4.50)
        def b_eu_sou(t, d, T):
            return self.S(pad(), [C(rai, 540, 1860, 1.9, "feliz", "acena")], cam=(540, 1250, 1.25), t=t)

        @B(5.70)
        def b_63(t, d, T):
            return self.S(amarelo(), [C(rai, 330, 1860, 1.9, "feliz", "bracos_abertos", None, 1)], cam=(540, 1250, 1.2), t=t,
                          bal=bal("63 anos!", 5.9, 0.1, 0.7))

        @B(7.00)
        def b_padaria(t, d, T):
            return self.S(alv(), [C(rai, 760, 1860, 1.7, "feliz", "acena", None, -1)], cam=(540, 1250, 1.15), t=t)

        @B(8.20)
        def b_forno(t, d, T):
            return self.S(self.fundo_cor((255, 190, 90), (230, 110, 50)), props=[prop(pdr.forno(self.fc, t, 900), 540, 1000)],
                          cam=(540, 1000, 1.05), t=t)

        @B(9.90)
        def b_fornada(t, d, T):
            return self.S(pad(), [C(rai, 330, 1860, 1.9, "feliz", "entrega", None, 1)],
                          [prop(pdr.tabuleiro(900, 6), 700, 1300), lambda m: pc_.vapor(m, t, 700, 1180, 6)], (540, 1250, 1.2), t)

        @B(10.60)
        def b_pao(t, d, T):
            return self.S(amarelo(), props=[prop(pdr.pao(720), 540, 1000), lambda m: pc_.vapor(m, t, 540, 880, 6)],
                          cam=(540, 1000, 1.05), t=t)

        # ---------- história ----------
        @B(11.70)
        def b_graca(t, d, T):
            pl = lambda m: m.alpha_composite(cc_.placa(self.fc, "PÃO\nDE GRAÇA", (60, 150, 80), 700), (190, 480))  # noqa: E731
            return self.S(pad(), [C(rai, 540, 1860, 1.8, "feliz", "aponta")], [pl], (540, 1250, 1.2), t)

        @B(12.40)
        def b_fila(t, d, T):
            chars = [C(K[i % 5], 130 + i * 190, 1840, 1.2, "feliz", "acena") for i in range(5)]
            return self.S(alv(), chars, cam=(540, 1350, 1.2), t=t)

        @B(14.00)
        def b_gente(t, d, T):
            chars = [C(K[i % 5], 160 + i * 210, 1840, 1.1, "feliz", "idle") for i in range(5)]
            return self.S(rua(), chars, cam=(540, 1350, 1.2), t=t)

        @B(15.30)
        def b_mae(t, d, T):
            return self.S(rua(), [C(K[1], 360, 1850, 1.7, "feliz", "idle"), C(K[4], 760, 1850, 1.1, "feliz", "acena")],
                          cam=(540, 1300, 1.2), t=t)

        @B(16.50)
        def b_entregador(t, d, T):
            return self.S(rua(), [C(K[2], 540, 1860, 1.8, "feliz", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(17.30)
        def b_morador(t, d, T):
            return self.S(rua(), [C(K[3], 540, 1860, 1.8, "neutro", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(18.30)
        def b_ninguem(t, d, T):
            return self.S(pad(), [C(rai, 300, 1860, 1.7, "feliz", "entrega", None, 1), C(K[1], 800, 1860, 1.5, "feliz", "idle", None, -1)],
                          [prop(pdr.pao(300), 560, 1380)], (540, 1250, 1.15), t)

        @B(19.90)
        def b_homem(t, d, T):
            p_ = lambda m: m.alpha_composite(pdr.poste(260, 1200), (760, 460))  # noqa: E731
            return self.S(noite(), [C(dan, 640, 1850, 1.5, "neutro", "idle", None, -1)], [], (540, 1250, 1.15), t, front=[p_])

        @B(21.50)
        def b_intriga(t, d, T):
            return self.S(noite(), [C(dan, 540, 1860, 1.9, "neutro", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(23.50)
        def b_nunca_pega(t, d, T):
            p_ = lambda m: m.alpha_composite(pdr.poste(260, 1200), (400, 460))  # noqa: E731
            return self.S(noite(), [C(dan, 520, 1850, 1.6, "triste", "idle", None, -1)], [], (540, 1250, 1.15), t, front=[p_])

        @B(25.80)
        def b_olhando(t, d, T):
            return self.S(noite(), [C(dan, 540, 1860, 2.0, "triste", "idle")], cam=(540, 1250, 1.35), t=t)

        @B(26.80)
        def b_embora(t, d, T):
            x = 540 + 400 * ease_io(min(1, (T - 26.8) / 1.5))
            return self.S(noite(), [C(dan, x, 1850, 1.5, "triste", "anda", None, 1)], cam=(540, 1250, 1.15), t=t)

        @B(27.20)
        def b_coisa(t, d, T):
            return self.S(pad(), [C(rai, 540, 1860, 1.9, "surpreso", "idle")], cam=(540, 1250, 1.3), t=t,
                          bal=bal("?", 27.8, 0.18, 0.7))

        @B(29.30)
        def b_farinha(t, d, T):
            return self.S(amarelo(), props=[prop(pdr.saco_farinha(self.fc, 720), 540, 1000)], cam=(540, 1000, 1.05), t=t)

        @B(30.60)
        def b_nunca_soube(t, d, T):
            return self.S(pad(), [C(rai, 540, 1860, 1.9, "triste", "bolso")], cam=(540, 1250, 1.3), t=t)

        @B(33.10)
        def b_oito_anos(t, d, T):
            bg = gradiente(WW, WH, (34, 34, 52), (14, 14, 24))
            im = cr.calendario(self.fc, "ANOS", int(min(8, (T - 33.1) * 5)), total=8, w=960, cor_topo=(70, 74, 90))
            return self.S(bg, props=[prop(im, 540, 960)], cam=(540, 1000, 1.0), t=t)

        @B(34.00)
        def b_anteontem(t, d, T):
            x = 150 + 520 * ease_io(min(1, (T - 34.0) / 2.6))
            return self.S(noite(), [C(rai, x, 1850, 1.5, "neutro", "anda", None, 1)], cam=(540, 1250, 1.15), t=t)

        @B(35.70)
        def b_hospital(t, d, T):
            return self.S(cc_.hospital_porta(self.fc, True), [C(dan, 540, 1860, 1.6, "neutro", "idle", None, 1)],
                          cam=(540, 1250, 1.2), t=t)

        @B(37.70)
        def b_jaleco(t, d, T):
            return self.S(cc_.hospital_porta(self.fc, False), [C(danj, 540, 1860, 1.9, "neutro", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(39.60)
        def b_enfermeira(t, d, T):
            return self.S(cc_.hospital_porta(self.fc, False), [C(rai, 280, 1860, 1.5, "neutro", "idle", None, 1),
                                                               C(enf, 800, 1860, 1.5, "feliz", "idle", D["enf"], -1)],
                          cam=(540, 1250, 1.2), t=t)

        @B(41.30)
        def b_sorriu(t, d, T):
            return self.S(cc_.hospital_porta(self.fc, False), [C(enf, 540, 1860, 1.9, "feliz", "idle", D["enf"])], cam=(540, 1250, 1.3),
                          t=t, bal=bal("É o doutor Daniel.", 42.2))

        @B(43.40)
        def b_noite_toda(t, d, T):
            return self.S(cc_.hospital_porta(self.fc, False), [C(enf, 540, 1860, 1.9, "feliz", "acena", D["enf"])],
                          cam=(540, 1250, 1.3), t=t, bal=bal("Passa na sua padaria toda madrugada.", 43.6))

        @B(46.60)
        def b_voltei(t, d, T):
            return self.S(self.quarto_noite(), [C(rai, 540, 1860, 1.9, "neutro", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(48.00)
        def b_gaveta(t, d, T):
            return self.S(self.fundo_cor((110, 80, 56), (44, 30, 22)), props=[prop(qq_.gaveta(self.fc, True, 880), 540, 1050)],
                          cam=(540, 1000, 1.05), t=t)

        @B(49.20)
        def b_envelopes(t, d, T):
            return self.S(self.fundo_cor((110, 80, 56), (44, 30, 22)), props=[prop(pdr.envelopes(8, 900), 540, 980)],
                          cam=(540, 1000, 1.1), t=t)

        @B(53.80)
        def b_antigo(t, d, T):
            return self.S(self.fundo_cor((90, 70, 60), (36, 26, 24)), props=[prop(pdr.bilhete(self.fc, 880, (T - 57.6) / 2.8), 540, 980)],
                          cam=(540, 1000, 1.05), t=t)

        @B(60.70)
        def b_menino(t, d, T):
            return self.S(pad(), [C(danm, 540, 1860, 1.9, "triste", "idle")], cam=(540, 1250, 1.3), t=t,
                          fx=lambda f: pz_.sepia(f, 0.6))

        @B(62.80)
        def b_arma(t, d, T):
            return self.S(self.fundo_cor((90, 70, 60), (36, 26, 24)), props=[prop(pdr.arma_brinquedo(640), 540, 980)],
                          cam=(540, 1000, 1.05), t=t)

        @B(64.00)
        def b_paga(t, d, T):
            return self.S(cc_.hospital_porta(self.fc, False), [C(danj, 540, 1860, 1.9, "feliz", "idle")], cam=(540, 1250, 1.3), t=t,
                          front=[lambda m: ca_.coracoes_flutuando(m, t, 540, 1000, 5, 44, 5)])

        @B(65.70)
        def b_ontem(t, d, T):
            x = 150 + 360 * ease_io(min(1, (T - 65.7) / 2.8))
            return self.S(noite(), [C(rai, x, 1850, 1.5, "feliz", "entrega", None, 1), C(dan, 800, 1850, 1.5, "triste", "idle", None, -1)],
                          [prop(pdr.pao(240), x + 200, 1400)], (540, 1250, 1.15), t)

        @B(69.90)
        def b_pega(t, d, T):
            k = max(0, (T - 72.0) / 1.0)
            f = self.S(noite(), [C(rai, 540, 1860, 1.9, "feliz", "idle", D["rai2"])], cam=(540, 1250, 1.3), t=t,
                       bal=bal("Pega. Esse é seu há oito anos.", 69.9),
                       front=[lambda m: ca_.coracoes_flutuando(m, t, 540, 1000, 6, 48, 7)])
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
    ev += [("hit", 0.0, 0.7), ("pop", 0.55, 0.5), ("hit", 0.95, 0.5), ("pop", 1.4, 0.4), ("ding", 2.1, 0.4), ("pop", 2.9, 0.4),
           ("pop", 4.5, 0.3), ("pop", 5.7, 0.3), ("ding", 9.9, 0.4), ("hit", 19.9, 0.5), ("hit", 35.7, 0.4), ("pagina", 49.2, 0.3),
           ("riser", 58.0, 0.4), ("hit", 62.8, 0.6), ("ding", 64.0, 0.5), ("coracao", 70.0, 0.5), ("coracao", 70.8, 0.5)]
    amb_ = [("cidade", 0.0, 19.0, 0.2), ("noite", 19.0, 34.0, 0.3), ("cidade", 34.0, 46.0, 0.15), ("noite", 46.0, dur - 1.5, 0.3)]
    picos = [(0.0, 0.8), (9.9, 0.7), (19.9, 0.5), (58.0, 0.8), (64.0, 0.9), (70.0, 1.0)]
    ev = [(k_, to_new(t_), *r_) for (k_, t_, *r_) in ev]
    amb_ = [(n_, to_new(a_), to_new(b_) if b_ < dur - 2 else b_, v_) for (n_, a_, b_, v_) in amb_]
    picos = [(to_new(t_), v_) for (t_, v_) in picos]
    mix = som.mixar_v2(dur, voz, ev, amb_, picos, "triste", 0.2)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def carregar_palavras(caminho):
    troca = {"63": "sessenta e três", "4": "quatro", "8": "oito", "vingente": "Vem gente", "vesti": "Vestia", "cesta": "sexta",
             "conseguir": "consegui"}
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
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_eu_dou_uma_todo_dia.mp4"))
    ap.add_argument("--abertura", default=None, help="json das palavras da nova abertura (narracao = abertura + resto)")
    ap.add_argument("--so_audio", action="store_true", help="refaz só o áudio e troca no mp4 já renderizado")
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    ap.add_argument("--de", type=float, default=None)
    ap.add_argument("--ate", type=float, default=None)
    a = ap.parse_args()

    global MAPA
    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    cam = json.load(open(a.camera))
    palavras = carregar_palavras(a.transcricao)
    delta = 0.0
    if a.abertura:
        ab = [w for seg in json.load(open(a.abertura)) for w in seg["words"]]
        ab_dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                                a.abertura.replace(".json", ".mp3")]).decode().strip())
        ini_novo = ab_dur + 0.12
        bato_novo = [w for w in ab if w["w"].lower().startswith("bato")][1]["s"]
        delta = ini_novo - 4.05
        MAPA = dict(delta=delta, ini_novo=ini_novo, bato_novo=bato_novo, bato_velho=1.5, fim_velho=4.05)
        novas = [dict(w=w["w"], s=to_old(w["s"]), e=to_old(w["e"])) for w in ab]
        palavras = novas + [w for w in palavras if w["s"] >= 4.05]
    ref_dur = cam[-1]["ini"] + cam[-1]["dur"]
    voz_velha = voz_dur - delta
    filme = FilmeTodos(palavras, a.fonte, voz_velha + 1.4, a.narracao, cam, [(0.0, 0.0), (ref_dur, voz_velha)])
    filme.dur_total += delta
    total = int(filme.dur_total * FPS)

    if a.so_audio:
        tmp = tempfile.mkdtemp(prefix="audio_")
        wav = os.path.join(tmp, "mix.wav")
        mixar(filme, a.narracao, wav)
        novo = os.path.join(tmp, "novo.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.saida, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", novo], check=True)
        os.replace(novo, a.saida)
        print("✔ áudio refeito em", a.saida)
        return
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

    tmp = tempfile.mkdtemp(prefix="padeiro_")
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
