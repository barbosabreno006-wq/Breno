#!/usr/bin/env python3
"""
"De Quatro no Quarto" — numa cidade todo mundo é apaixonado pelo narrador, mas é a Admiradora (alta, sem rosto,
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
import cenario_amor as ca_  # noqa: E402
import cao as cao_  # noqa: E402
import efeitos as ef  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io)

g.HANDHELD = False
g.PERMITE_FLIP = False
boneco.Boneco.AMP = 1.7
boneco.Boneco.SHADE = 1.0
g.GRAO = 0.6
random.seed(4242)

SER = dict(pele=(222, 176, 140), cabelo=(226, 226, 232), camisa=(120, 150, 110), calca=(80, 84, 104), sapato=(60, 50, 45),
           tipo="pai", bigode=True, cabelo_estilo="ralo", oculos=True, colete=(100, 90, 80), iris=(80, 60, 40))
CEL = dict(pele=(232, 186, 150), cabelo=(226, 226, 232), camisa=(200, 120, 140), calca=(0, 0, 0), sapato=(110, 80, 90),
           tipo="vovo", vestido=(200, 120, 140), cabelo_estilo="coque", oculos=True, iris=(90, 70, 50))
SER_J = dict(SER, cabelo=(60, 44, 36), cabelo_estilo="topete", oculos=False, bigode=False)
CEL_J = dict(CEL, cabelo=(90, 56, 36), tipo="moca", cabelo_estilo="longo", oculos=False)
vc.DESTAQUE_VERMELHO = set()
_C = {}
_T = {}


def cz_ponte_rua(f):  # noqa: E301
    if "ruanoite" not in _T:
        _T["ruanoite"] = ca.noite(f.rua().copy(), 0.6)
    return _T["ruanoite"]


IRIS = {"b_alianca", "b_casal", "b_noite", "b_gaveta", "b_minutos", "b_filhos", "b_ontem", "b_final"}


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
        self.ser, self.cel = P_(SER), P_(CEL)
        self.kids = [P_(c) for c in ve.POVO]
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.cortes = [(0.0, 0)]
        self.spec, self.u, self.sub = None, 0.0, 0
        self.dlg = {"cel1": [(16.7, 20.0)], "ser1": [(39.1, 39.8)], "kid": [(45.2, 46.3)], "ser2": [(48.4, 51.3)], "cel2": [(57.1, 59.4)]}
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
        ser, cel = self.ser, self.cel
        qq = qq_
        D = self.dlg

        def bal(txt, t0, y=0.1, x=0.5):
            return [(txt, OUT_W * x, OUT_H * y, t0)]

        def prop(img, x, y):
            return lambda m: m.alpha_composite(img, (int(x - img.width / 2), int(y - img.height / 2)))

        def cama_na(cx, y=1520, w=900):
            return lambda m: m.alpha_composite(ca2.cama(w), (int(cx - w / 2), int(y)))

        noite = lambda: cz.quarto_simples(self.fc, False, True)  # noqa: E731
        sala = lambda: cc_.sofa(self.fc, False)  # noqa: E731

        @B(0.0)
        def b_quatro(t, d, T):
            return self.S(noite(), [C(ser, 540, 1800, 1.8, "neutro", "idle")], [cama_na(540)], (540, 1250, 1.3), t)

        @B(1.30)
        def b_quarto(t, d, T):
            return self.S(noite(), [C(ser, 280, 1860, 1.4, "neutro", "idle", None, 1), C(cel, 760, 1790, 1.4, "neutro", "idle")],
                          [cama_na(760, 1520, 800)], (540, 1250, 1.15), t)

        @B(2.20)
        def b_esperando(t, d, T):
            return self.S(noite(), [C(cel, 540, 1790, 1.8, "neutro", "idle")], [cama_na(540)], (540, 1250, 1.3), t)

        @B(3.80)
        def b_calma(t, d, T):
            return self.S(noite(), [C(ser, 540, 1860, 1.9, "feliz", "acena")], cam=(540, 1250, 1.3), t=t)

        @B(4.30)
        def b_alianca(t, d, T):
            return self.S(self.fundo_cor((30, 26, 56), (12, 10, 28)), props=[prop(qq.alianca(620, 0.5 + 0.5 * math.sin(T * 4)), 540, 960)],
                          cam=(540, 1000, 1.0), t=t)

        @B(5.90)
        def b_nome(t, d, T):
            return self.S(sala(), [C(ser, 540, 1860, 1.9, "feliz", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(8.40)
        def b_celia(t, d, T):
            return self.S(sala(), [C(cel, 540, 1860, 1.9, "feliz", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(9.90)
        def b_casal(t, d, T):
            im = qq.foto_casal(self.fc, SER_J, CEL_J, 760)
            return self.S(self.fundo_cor((80, 60, 70), (30, 22, 30)), props=[prop(im, 540, 980)], cam=(540, 1000, 1.05), t=t)

        @B(10.60)
        def b_alzheimer(t, d, T):
            return self.S(sala(), [C(cel, 540, 1860, 1.9, "surpreso", "idle")], cam=(540, 1250, 1.3), t=t,
                          fx=lambda f: ef.neblina(f, t, (255, 255, 255), 90), bal=bal("?", 11.9, 0.2, 0.7))

        @B(12.60)
        def b_noite(t, d, T):
            im = ca2.relogio_torre(self.fc, 10, 0, 760)
            return self.S(self.fundo_cor((24, 28, 66), (10, 12, 30)), props=[prop(im, 540, 960)], cam=(540, 1000, 1.0), t=t)

        @B(14.20)
        def b_senta(t, d, T):
            return self.S(noite(), [C(cel, 540, 1790, 1.8, "triste", "sentado")], [cama_na(540)], (540, 1250, 1.3), t)

        @B(16.70)
        def b_moco(t, d, T):
            return self.S(noite(), [C(cel, 540, 1860, 1.9, "triste", "idle", D["cel1"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("Moço, eu perdi a minha aliança!", 16.7))

        @B(18.70)
        def b_marido(t, d, T):
            return self.S(noite(), [C(cel, 540, 1860, 1.9, "chora", "idle", D["cel1"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("Meu marido vai ficar bravo!", 18.9))

        @B(20.20)
        def b_nao_sabe(t, d, T):
            return self.S(noite(), [C(ser, 540, 1860, 1.9, "triste", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(22.10)
        def b_gaveta(t, d, T):
            return self.S(self.fundo_cor((110, 80, 56), (44, 30, 22)),
                          props=[prop(qq.gaveta(self.fc, True, 880), 540, 1050), prop(qq.alianca(220, 0.8), 540, 1000)],
                          cam=(540, 1000, 1.05), t=t)

        @B(24.30)
        def b_dedo(t, d, T):
            return self.S(sala(), [C(cel, 420, 1860, 1.7, "triste", "entrega")], [prop(qq.alianca(300, 0.6), 780, 1320)],
                          (540, 1250, 1.25), t)

        @B(27.50)
        def b_nao_lembra(t, d, T):
            return self.S(sala(), [C(cel, 540, 1860, 1.9, "neutro", "idle")], cam=(540, 1250, 1.3), t=t,
                          fx=lambda f: ef.neblina(f, t, (255, 255, 255), 70))

        @B(28.50)
        def b_entao(t, d, T):
            return self.S(noite(), [C(ser, 540, 1800, 1.7, "neutro", "idle")], [cama_na(540)], (540, 1250, 1.25), t)

        @B(30.90)
        def b_de_quatro(t, d, T):
            return self.S(noite(), [C(ser, 540, 1800, 1.9, "neutro", "idle")], [cama_na(540)], (540, 1350, 1.4), t)

        @B(32.00)
        def b_procurar(t, d, T):
            return self.S(noite(), [C(ser, 380, 1800, 1.6, "neutro", "idle", None, 1)], [cama_na(540),
                                                                                         lambda m: qq.feixe(m, 560, 1540, -120)],
                          (540, 1350, 1.3), t)

        @B(33.90)
        def b_minutos(t, d, T):
            mm = int(10 + min(15, (T - 33.9) * 8))
            im = ca2.relogio_torre(self.fc, 10, mm, 760)
            return self.S(self.fundo_cor((24, 28, 66), (10, 12, 30)), props=[prop(im, 540, 960)], cam=(540, 1000, 1.0), t=t)

        @B(35.50)
        def b_olhos(t, d, T):
            return self.S(noite(), [C(cel, 540, 1860, 2.0, "chora", "idle")], cam=(540, 1250, 1.35), t=t)

        @B(37.60)
        def b_achei(t, d, T):
            return self.S(noite(), [C(ser, 540, 1860, 1.9, "feliz", "acena", D["ser1"])], [prop(qq.alianca(260, 0.9), 800, 1180)],
                          (540, 1250, 1.3), t, bal=bal("Achei!", 39.1))

        @B(39.90)
        def b_sorri(t, d, T):
            return self.S(noite(), [C(cel, 540, 1860, 1.9, "feliz", "idle")], cam=(540, 1250, 1.3), t=t,
                          front=[lambda m: ca_.coracoes_flutuando(m, t, 540, 1000, 6, 50, 2)])

        @B(43.30)
        def b_filhos(t, d, T):
            return self.S(sala(), [C(ser, 300, 1860, 1.5, "triste", "idle", None, 1), C(K[0], 760, 1850, 1.4, "neutro", "aponta", None, -1),
                                   C(K[3], 960, 1850, 1.2, "neutro", "idle", None, -1)], cam=(540, 1250, 1.15), t=t)

        @B(45.10)
        def b_teatro(t, d, T):
            return self.S(sala(), [C(K[0], 540, 1860, 1.9, "bravo", "aponta", D["kid"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("É só teatro, pai.", 45.2))

        @B(47.60)
        def b_responde(t, d, T):
            return self.S(sala(), [C(ser, 540, 1860, 1.9, "triste", "idle", D["ser2"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("Esquece. Mas durante cinco minutos, ela é feliz.", 48.4))

        @B(51.70)
        def b_ontem(t, d, T):
            return self.S(noite(), [C(ser, 540, 1860, 1.8, "triste", "bolso")], cam=(540, 1250, 1.25), t=t)

        @B(54.40)
        def b_segurou(t, d, T):
            return self.S(noite(), [C(cel, 380, 1860, 1.6, "feliz", "acena", None, 1), C(ser, 760, 1860, 1.6, "chora", "idle", None, -1)],
                          cam=(540, 1250, 1.2), t=t)

        @B(56.70)
        def b_falou(t, d, T):
            return self.S(noite(), [C(cel, 540, 1860, 1.9, "feliz", "idle", D["cel2"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("Obrigada por procurar de novo, Sérgio.", 57.1))

        @B(59.50)
        def b_nome2(t, d, T):
            return self.S(noite(), [C(ser, 540, 1860, 1.9, "chora", "idle")], cam=(540, 1250, 1.35), t=t,
                          front=[lambda m: ca_.coracoes_flutuando(m, t, 540, 1000, 5, 44, 5)])

        @B(62.40)
        def b_final(t, d, T):
            k = max(0, (T - 65.4) / 1.0)
            f = self.S(noite(), [C(ser, 540, 1800, 1.8, "neutro", "idle")], [cama_na(540)], (540, 1250, 1.3), t)
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
    ev += [("coracao", 40.2, 0.5), ("coracao", 41.0, 0.5), ("ding", 4.3, 0.5), ("ding", 39.1, 0.5), ("pagina", 22.2, 0.3),
           ("hit", 10.6, 0.3), ("riser", 55.0, 0.4), ("ding", 59.0, 0.6), ("coracao", 60.0, 0.6), ("coracao", 60.8, 0.6)]
    amb_ = [("noite", 0.0, 5.8, 0.3), ("cidade", 5.8, 12.0, 0.15), ("noite", 12.0, 43.0, 0.3), ("cidade", 43.0, 51.0, 0.15),
            ("noite", 51.0, dur - 1.5, 0.3)]
    picos = [(10.6, 0.5), (39.1, 0.6), (57.1, 0.8), (60.0, 1.0)]
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
    troca = {"61": "sessenta e um", "38,": "trinta e oito,", "38": "trinta e oito", "3": "três", "10,": "dez,", "10": "dez", "15,": "quinze,",
             "5": "cinco", "finge": "finjo", "O": "O"}
    out = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            if w["w"] == "o" and abs(w["s"] - 32.4) < 0.1:
                continue
            out.append(dict(w=troca.get(w["w"], w["w"]), s=w["s"], e=w["e"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--camera", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_de_quatro_no_quarto.mp4"))
    ap.add_argument("--abertura", default=None, help="json das palavras da nova abertura (narracao = abertura + resto)")
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

    tmp = tempfile.mkdtemp(prefix="quatro_")
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
