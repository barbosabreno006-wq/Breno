#!/usr/bin/env python3
"""
"Os Quatro Deuses" — numa cidade todo mundo é apaixonado pelo narrador, mas é a Admiradora (alta, sem rosto,
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
import cenario_deuses as pd_  # noqa: E402
import video_abracos as vb_  # noqa: E402
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

NARR = dict(pele=(232, 186, 150), cabelo=(70, 44, 32), camisa=(70, 130, 220), calca=(60, 70, 110),
            sapato=(240, 240, 245), tipo="menino", cabelo_estilo="topete", iris=(70, 110, 190), bolso=True)
NARR = dict(pele=(232, 186, 150), cabelo=(70, 44, 32), camisa=(190, 190, 200), calca=(90, 90, 110), sapato=(240, 240, 245),
            tipo="menino", cabelo_estilo="topete", iris=(70, 110, 190))
JOV = dict(NARR, tipo="pai", bigode=False)
SOLARA = dict(pele=(240, 196, 150), cabelo=(255, 200, 60), camisa=(255, 190, 50), calca=(0, 0, 0), sapato=(230, 170, 60),
              tipo="moca", vestido=(255, 190, 50), cabelo_estilo="longo", brinco=(255, 240, 160), iris=(220, 140, 40))
NOCTIS = dict(pele=(200, 190, 230), cabelo=(40, 40, 110), camisa=(40, 50, 130), calca=(30, 36, 90), sapato=(20, 24, 60),
              tipo="pai", bigode=False, cabelo_estilo="longo", cachecol=(130, 150, 255), iris=(150, 170, 255))
FORTUNA = dict(pele=(222, 176, 140), cabelo=(60, 170, 90), camisa=(60, 180, 100), calca=(0, 0, 0), sapato=(40, 120, 70),
               tipo="moca", vestido=(60, 180, 100), cabelo_estilo="cacheado", brinco=(255, 220, 90), iris=(40, 120, 70))
FIM = dict(pele=(206, 200, 210), cabelo=(40, 40, 50), camisa=(60, 60, 76), calca=(40, 40, 56), sapato=(30, 30, 40),
           tipo="pai", bigode=False, cabelo_estilo="careca", capuz=None, iris=(120, 120, 140))
vc.DESTAQUE_VERMELHO = set()
_C = {}
_T = {}


def cz_ponte_rua(f):  # noqa: E301
    if "ruanoite" not in _T:
        _T["ruanoite"] = ca.noite(f.rua().copy(), 0.6)
    return _T["ruanoite"]


IRIS = {"b_aqui", "b_solara", "b_aos17", "b_quatro", "b_fim_levanta", "b_desci", "b_nunca_esquecido", "b_pergunta"}


class FilmeTodos(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao, camera, ancoras):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.solara, self.noctis, self.fortuna, self.fim = P_(SOLARA), P_(NOCTIS), P_(FORTUNA), P_(FIM)
        self.narr, self.jov = P_(NARR), P_(JOV)
        self.kids = [P_(c) for c in ve.POVO]
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.cortes = [(0.0, 0)]
        self.spec, self.u, self.sub = None, 0.0, 0
        self.dlg = {"solara": [(35.8, 36.6)], "noctis": [(37.8, 38.6)], "fortuna": [(47.1, 49.5)], "fortuna2": [(49.9, 52.9)],
                    "fim": [(55.2, 59.4)]}
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
        sol_, lua_, tre_, fim_, narr, jov = self.solara, self.noctis, self.fortuna, self.fim, self.narr, self.jov
        pd = pd_
        D = self.dlg

        def bal(txt, t0, y=0.1, x=0.5):
            return [(txt, OUT_W * x, OUT_H * y, t0)]

        def prop(img, x, y):
            return lambda m: m.alpha_composite(img, (int(x - img.width / 2), int(y - img.height / 2)))

        def aura_(x, y, tipo, raio=380, f=0.55):
            fn = lambda m: pd.aura(m, x, y, tipo, raio, f)  # noqa: E731
            fn._back = True
            return fn

        def simb(x, y, tipo, w=170):
            return prop(pd.simbolo(tipo, w), x, y)

        def deuses_mesa(t, falando=None, tristes=False):
            """Os quatro em volta da mesa de pedra."""
            ex = "bravo" if not tristes else "triste"
            return [C(sol_, 190, 1760, 1.45, ex, "aponta", D["solara"] if falando == "solara" else None, 1),
                    C(lua_, 410, 1770, 1.45, ex, "aponta", D["noctis"] if falando == "noctis" else None, 1),
                    C(tre_, 670, 1770, 1.45, ex, "aponta", D["fortuna"] if falando == "fortuna" else None, -1),
                    C(fim_, 890, 1760, 1.45, ex, "aponta", D["fim"] if falando == "fim" else None, -1)]

        def auras_mesa():
            return [aura_(190, 1250, "sol", 330), aura_(410, 1250, "lua", 330), aura_(670, 1250, "trevo", 330),
                    aura_(890, 1250, "fim", 330)]

        mont = lambda: pd.montanha(self.fc, "dia")  # noqa: E731
        aldeia = lambda: pd.aldeia(self.fc)  # noqa: E731

        @B(0.0)
        def b_brigaram(t, d, T):
            return self.S(mont(), deuses_mesa(t), auras_mesa(), (540, 1300, 1.15), t)

        @B(1.00)
        def b_por_mim(t, d, T):
            return self.S(mont(), [C(narr, 540, 1860, 1.9, "surpreso", "idle")],
                          [aura_(180, 900, "sol", 300), aura_(900, 900, "lua", 300)], (540, 1250, 1.3), t)

        @B(2.00)
        def b_nenhum(t, d, T):
            return self.S(mont(), [C(narr, 300, 1860, 1.7, "triste", "idle")] + [
                C(sol_, 700, 1760, 1.2, "neutro", "idle", None, -1), C(lua_, 900, 1770, 1.2, "neutro", "idle", None, -1)],
                [], (540, 1300, 1.15), t, bal=bal("?", 2.6, 0.2, 0.3))

        @B(3.80)
        def b_aqui(t, d, T):
            im = vb_.bebe(420)
            raio = lambda m: m.alpha_composite(brilho((900, 900), (255, 236, 160), 400, 0.55), (90, 700))  # noqa: E731
            return self.S(aldeia(), [], [raio, prop(im, 540, 1180)], (540, 1250, 1.2), t)

        @B(7.00)
        def b_solara(t, d, T):
            return self.S(self.fundo_cor((255, 200, 70), (220, 120, 30)), [C(sol_, 540, 1860, 1.9, "feliz", "bracos_abertos")],
                          [aura_(540, 900, "sol", 520, 0.8), simb(540, 380, "sol", 260)], (540, 1250, 1.25), t)

        @B(9.80)
        def b_noctis(t, d, T):
            return self.S(self.fundo_cor((30, 34, 84), (10, 12, 36)), [C(lua_, 540, 1860, 1.9, "neutro", "idle")],
                          [lambda m: pd.estrelas(m, t), aura_(540, 900, "lua", 520, 0.7), simb(540, 380, "lua", 260)],
                          (540, 1250, 1.25), t)

        @B(12.60)
        def b_fortuna(t, d, T):
            return self.S(self.fundo_cor((60, 190, 110), (20, 100, 60)), [C(tre_, 540, 1860, 1.9, "feliz", "acena")],
                          [aura_(540, 900, "trevo", 520, 0.7), simb(540, 380, "trevo", 260)], (540, 1250, 1.25), t)

        @B(15.80)
        def b_fim(t, d, T):
            return self.S(self.fundo_cor((110, 110, 126), (40, 40, 56)), [C(fim_, 540, 1860, 1.9, "neutro", "idle")],
                          [aura_(540, 900, "fim", 520, 0.6), simb(540, 380, "fim", 260)], (540, 1250, 1.25), t)

        @B(18.60)
        def b_unico(t, d, T):
            chars = [C(K[0], 160, 1840, 1.2, "feliz", "idle"), C(K[1], 400, 1840, 1.2, "feliz", "idle"),
                     C(K[3], 680, 1840, 1.2, "feliz", "idle"), C(narr, 900, 1850, 1.2, "triste", "idle")]
            sims = [simb(160, 1000, "sol", 150), simb(400, 1000, "lua", 150), simb(680, 1000, "trevo", 150)]
            return self.S(aldeia(), chars, sims, (540, 1350, 1.2), t)

        @B(20.50)
        def b_chamavam(t, d, T):
            chars = [C(K[0], 240, 1840, 1.3, "ri", "aponta"), C(K[1], 520, 1840, 1.3, "ri", "aponta"),
                     C(narr, 850, 1850, 1.4, "triste", "idle", None, -1)]
            return self.S(aldeia(), chars, [simb(240, 1000, "sol", 150), simb(520, 1000, "lua", 150)], (540, 1350, 1.2), t,
                          bal=bal("O Esquecido!", 21.8, 0.12))

        @B(23.00)
        def b_cresci(t, d, T):
            chars = [C(K[0], 160, 1840, 1.2, "feliz", "idle"), C(K[2], 400, 1840, 1.2, "feliz", "idle"),
                     C(K[4], 640, 1840, 1.2, "feliz", "idle"), C(narr, 900, 1850, 1.2, "triste", "idle")]
            return self.S(aldeia(), chars, [aura_(160, 1300, "sol", 260), aura_(400, 1300, "lua", 260),
                                            aura_(640, 1300, "trevo", 260)], (540, 1350, 1.2), t)

        @B(25.00)
        def b_nunca_tive(t, d, T):
            vazios = [prop(pd.simbolo(s, 130), 220 + i * 210, 560) for i, s in enumerate(("sol", "lua", "trevo", "fim"))]
            return self.S(self.fundo_cor((60, 60, 80), (24, 24, 36)), [C(narr, 540, 1860, 1.9, "triste", "idle")],
                          [lambda m: [v(m) for v in vazios]], (540, 1250, 1.3), t,
                          fx=lambda f: Image.blend(f, Image.new("RGB", f.size, (30, 30, 40)), 0.2))

        @B(29.00)
        def b_aos17(t, d, T):
            x = 150 + 520 * ease_io(min(1, (T - 29.0) / 2.4))
            return self.S(mont(), [C(jov, x, 1850, 1.5, "neutro", "anda")], cam=(540, 1300, 1.15), t=t)

        @B(30.80)
        def b_montanha(t, d, T):
            return self.S(pd.montanha(self.fc, "poente"), [C(jov, 300, 1850, 1.4, "bravo", "aponta")], cam=(540, 1100, 1.1),
                          t=t)

        @B(32.40)
        def b_quatro(t, d, T):
            return self.S(mont(), deuses_mesa(t), auras_mesa(), (540, 1300, 1.15), t)

        @B(35.60)
        def b_solara_fala(t, d, T):
            return self.S(mont(), [C(sol_, 540, 1860, 1.9, "bravo", "aponta", D["solara"], 1)], [aura_(540, 900, "sol", 480)],
                          (540, 1250, 1.3), t, bal=bal("Ele é meu!", 35.8))

        @B(37.30)
        def b_noctis_fala(t, d, T):
            return self.S(mont(), [C(lua_, 540, 1860, 1.9, "bravo", "aponta", D["noctis"], -1)],
                          [aura_(540, 900, "lua", 480)], (540, 1250, 1.3), t, bal=bal("Não, é meu!", 37.8))

        @B(39.50)
        def b_parei(t, d, T):
            return self.S(mont(), [C(jov, 300, 1860, 1.6, "surpreso", "idle", None, 1)] + [
                C(tre_, 720, 1770, 1.2, "bravo", "aponta", None, -1), C(fim_, 920, 1760, 1.2, "bravo", "aponta", None, -1)],
                [], (540, 1300, 1.15), t)

        @B(40.90)
        def b_nao_ter(t, d, T):
            return self.S(mont(), [C(jov, 540, 1860, 1.9, "surpreso", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(42.40)
        def b_decidir(t, d, T):
            return self.S(mont(), deuses_mesa(t), auras_mesa(), (540, 1300, 1.2), t)

        @B(45.10)
        def b_fortuna_cansada(t, d, T):
            return self.S(mont(), [C(tre_, 540, 1860, 1.9, "triste", "idle")], [aura_(540, 900, "trevo", 480, 0.5)],
                          (540, 1250, 1.3), t)

        @B(47.10)
        def b_servo(t, d, T):
            k = ease_io(min(1, (T - 47.1) / 1.5))
            chars = [C(tre_, 300, 1860, 1.6, "triste", "idle", D["fortuna"], 1), C(K[0], 820, 1850, 1.4, "neutro", "idle", None, -1)]
            return self.S(mont(), chars, [lambda m: pd.correntes(m, 820, 1520, 0.0)], (540, 1250, 1.2), t,
                          bal=bal("Quem é abençoado vira nosso servo.", 47.3))

        @B(49.90)
        def b_livre(t, d, T):
            return self.S(mont(), [C(tre_, 300, 1860, 1.6, "triste", "idle", D["fortuna2"], 1),
                                   C(jov, 820, 1850, 1.5, "surpreso", "idle", None, -1)], cam=(540, 1250, 1.2), t=t,
                          bal=bal("Você veio sem nada nosso.", 50.0, 0.08))

        @B(51.60)
        def b_unico_livre(t, d, T):
            return self.S(mont(), [C(jov, 540, 1860, 1.9, "surpreso", "idle")], cam=(540, 1250, 1.3), t=t,
                          bal=bal("É o único livre.", 52.3))

        @B(53.40)
        def b_fim_levanta(t, d, T):
            return self.S(mont(), [C(fim_, 540, 1860, 1.9, "neutro", "aponta")], [aura_(540, 900, "fim", 480, 0.5)],
                          (540, 1250, 1.3), t)

        @B(55.20)
        def b_livres(t, d, T):
            return self.S(mont(), [C(fim_, 540, 1860, 1.9, "neutro", "idle", D["fim"])], [aura_(540, 900, "fim", 480, 0.5)],
                          (540, 1250, 1.3), t, bal=bal("Humanos livres escrevem o próprio destino.", 55.4, 0.08))

        @B(57.80)
        def b_medo(t, d, T):
            tre = 6 * math.sin(T * 40)
            return self.S(mont(), deuses_mesa(t, tristes=True), auras_mesa(), (540 + tre, 1300, 1.2), t,
                          bal=bal("A gente tem medo de você.", 58.0, 0.08))

        @B(59.80)
        def b_desci(t, d, T):
            x = 800 - 480 * ease_io(min(1, (T - 59.8) / 2.2))
            return self.S(pd.montanha(self.fc, "poente"), [C(jov, x, 1850, 1.5, "neutro", "anda", None, -1)],
                          cam=(540, 1300, 1.15), t=t)

        @B(62.10)
        def b_entendi(t, d, T):
            return self.S(pd.montanha(self.fc, "poente"), [C(jov, 540, 1860, 1.9, "surpreso", "idle")],
                          cam=(540, 1250, 1.3), t=t)

        @B(63.30)
        def b_nunca_esquecido(t, d, T):
            return self.S(self.fundo_cor((255, 214, 120), (230, 130, 70)), [C(jov, 540, 1860, 1.9, "feliz", "idle")],
                          cam=(540, 1250, 1.3), t=t, fx=lambda f: ef.raios(f, t, (255, 236, 160), 14, 40))

        @B(64.80)
        def b_livre2(t, d, T):
            q = max(0, min(1, (T - 65.0) / 1.0))
            return self.S(self.fundo_cor((255, 214, 120), (230, 130, 70)), [C(jov, 540, 1860, 1.9, "feliz", "bracos_abertos")],
                          [lambda m: pd.correntes(m, 540, 1250, q)], (540, 1250, 1.3), t,
                          fx=lambda f: ef.raios(f, t, (255, 236, 160), 14, 45))

        @B(66.80)
        def b_pergunta(t, d, T):
            k = max(0, (T - 69.0) / 1.2)
            im_ = [pd.simbolo(s, 230) for s in ("sol", "lua", "trevo", "fim")]
            props = [prop(im_[i], 260 + (i % 2) * 560, 700 + (i // 2) * 420 + 10 * math.sin(T * 2 + i)) for i in range(4)]
            f = self.S(self.fundo_cor((40, 36, 70), (14, 12, 30)), props=props, cam=(540, 1000, 1.0), t=t)
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
    ev += [("riser", 0.0, 0.3), ("hit", 3.8, 0.4), ("ding", 7.0, 0.5), ("ding", 9.8, 0.4), ("ding", 12.6, 0.4), ("hit", 15.8, 0.5),
           ("pop", 20.5, 0.3), ("hit", 35.6, 0.5), ("hit", 37.3, 0.5), ("riser", 44.0, 0.4), ("hit", 53.4, 0.6),
           ("hit", 57.8, 0.6), ("ding", 63.3, 0.5), ("riser", 62.0, 0.4), ("ding", 65.2, 0.6)]
    amb_ = [("vento", 0.0, 3.5, 0.3), ("cidade", 3.5, 29.0, 0.25), ("vento", 29.0, 60.0, 0.4), ("cidade", 60.0, dur - 1.5, 0.2)]
    picos = [(15.8, 0.6), (37.5, 0.8), (53.4, 0.9), (63.3, 1.0), (68.0, 0.7)]
    mix = som.mixar_v2(dur, voz, ev, amb_, picos, "triste", 0.2)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def carregar_palavras(caminho):
    troca = {"serve": "servo", "17": "dezessete", "Platrodeuses": "quatro deuses?"}
    out = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            if w["w"] == "a" and abs(w["s"] - 50.9) < 0.1:
                continue
            out.append(dict(w=troca.get(w["w"], w["w"]), s=w["s"], e=w["e"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--camera", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_os_quatro_deuses.mp4"))
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

    tmp = tempfile.mkdtemp(prefix="deuses_")
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
