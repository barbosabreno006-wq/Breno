#!/usr/bin/env python3
"""
"A Porta do Porão" — numa cidade todo mundo é apaixonado pelo narrador, mas é a Admiradora (alta, sem rosto,
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
import cenario_porao as pc_  # noqa: E402
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
AVO = dict(pele=(232, 186, 150), cabelo=(226, 226, 232), camisa=(200, 120, 90), calca=(0, 0, 0), sapato=(110, 80, 90),
           tipo="vovo", vestido=(200, 120, 90), cabelo_estilo="coque", oculos=True, avental=(250, 240, 220), iris=(90, 70, 50))
KID = dict(pele=(232, 186, 150), cabelo=(90, 56, 36), camisa=(230, 160, 60), calca=(60, 80, 130), sapato=(240, 240, 245),
           tipo="menino", cabelo_estilo="topete", iris=(70, 110, 160), sardas=True)
MAE = dict(pele=(232, 186, 150), cabelo=(90, 56, 36), camisa=(120, 160, 200), calca=(0, 0, 0), sapato=(110, 80, 90),
           tipo="moca", vestido=(120, 160, 200), cabelo_estilo="longo", iris=(80, 60, 40))
TIO = dict(pele=(222, 176, 140), cabelo=(60, 44, 36), camisa=(70, 130, 90), calca=(70, 74, 100), sapato=(60, 50, 45),
           tipo="pai", bigode=True)
ADULTO = dict(pele=(232, 186, 150), cabelo=(90, 56, 36), camisa=(230, 160, 60), calca=(60, 80, 130), sapato=(60, 50, 45),
              tipo="pai", bigode=False, sardas=True)
AVO_PAL = dict(pele=(214, 164, 126), cabelo=(226, 226, 232), camisa=(150, 110, 80), calca=(80, 84, 104), sapato=(60, 50, 45),
               tipo="pai", bigode=True, cabelo_estilo="ralo", oculos=True)
vc.DESTAQUE_VERMELHO = set()
_C = {}
_T = {}


def cz_ponte_rua(f):  # noqa: E301
    if "ruanoite" not in _T:
        _T["ruanoite"] = ca.noite(f.rua().copy(), 0.6)
    return _T["ruanoite"]


IRIS = {"b_seis", "b_semana", "b_escuro", "b_porao", "b_avo", "b_voltava", "b_hoje", "b_play"}


class FilmeTodos(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao, camera, ancoras):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.avo, self.kid, self.mae, self.tio, self.adulto = P_(AVO), P_(KID), P_(MAE), P_(TIO), P_(ADULTO)
        self.kids = [P_(c) for c in ve.POVO]
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.cortes = [(0.0, 0)]
        self.spec, self.u, self.sub = None, 0.0, 0
        self.dlg = {"mae": [(17.6, 18.5)], "tio": [(19.7, 20.8)], "avo": [(61.6, 62.6)], "avo2": [(76.9, 78.4)]}
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

    def fundo_quente(self):
        return self.fundo_rosa((120, 70, 40), (48, 28, 20))

    def sala(self):
        return cc_.sofa(self.fc, False)

    def lavanderia(self):
        k = "lav"
        if k not in _T:
            _T[k] = gradiente(WW, WH, (206, 222, 232), (172, 196, 212))
        return _T[k]

    def rua_noite(self):
        return cz_ponte_rua(self)

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
        avo, kid, mae, tio, adulto = self.avo, self.kid, self.mae, self.tio, self.adulto
        pc = pc_
        D = self.dlg

        def bal(txt, t0, y=0.1, x=0.5):
            return [(txt, OUT_W * x, OUT_H * y, t0)]

        def prop(fn_img, x, y):
            return lambda m: m.alpha_composite(fn_img, (int(x - fn_img.width / 2), int(y - fn_img.height / 2)))

        def memoria(f):
            return pc.sepia(f, 0.55)

        porta = lambda: pc.corredor_porta(self.fc)  # noqa: E731
        cozinha = lambda: cc_.cozinha(self.fc, 0.0, 0.0)  # noqa: E731

        @B(0.0)
        def b_pergunta(t, d, T):
            return self.S(porta(), [C(avo, 300, 1860, 1.8, "neutro", "idle", None, 1)], cam=(540, 1250, 1.2), t=t)

        @B(1.40)
        def b_porta(t, d, T):
            return self.S(pc.corredor_porta(self.fc, True), [], cam=(540, 1000, 1.25), t=t)

        @B(2.80)
        def b_seis(t, d, T):
            im = pc.relogio_parede(self.fc, 6, 0, 820)
            return self.S(self.fundo_quente(), props=[prop(im, 540, 960)], cam=(540, 1000, 1.0), t=t)

        @B(4.10)
        def b_nove_anos(t, d, T):
            return self.S(cozinha(), [C(kid, 540, 1860, 1.8, "neutro", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(5.90)
        def b_seis_ponto(t, d, T):
            return self.S(cozinha(), [C(avo, 540, 1860, 1.8, "neutro", "bate")],
                          [prop(pc.relogio_parede(self.fc, 6, 0, 260), 840, 480)], (540, 1250, 1.25), t)

        @B(8.40)
        def b_panela(t, d, T):
            return self.S(cozinha(), [C(avo, 300, 1860, 1.5, "neutro", "idle")],
                          [prop(pc.panela(420), 640, 960), lambda m: pc.vapor(m, t, 640, 900)], (540, 1250, 1.2), t)

        @B(9.90)
        def b_chave(t, d, T):
            return self.S(cozinha(), [C(avo, 540, 1860, 1.9, "neutro", "bolso")],
                          [prop(ca_.chave(300, 10), 820, 1280)], (540, 1250, 1.3), t)

        @B(11.70)
        def b_descia(t, d, T):
            x = 900 - 520 * ease_io(min(1, (T - 11.7) / 2.4))
            return self.S(porta(), [C(avo, x, 1860, 1.6, "neutro", "anda", None, -1)], cam=(540, 1250, 1.15), t=t)

        @B(12.60)
        def b_fechava(t, d, T):
            return self.S(pc.corredor_porta(self.fc, True), [], cam=(540, 1100, 1.2), t=t)

        @B(14.40)
        def b_ficava(t, d, T):
            mm = int(min(40, (T - 14.4) * 14))
            im = pc.relogio_parede(self.fc, 6, mm, 820)
            return self.S(self.fundo_quente(), props=[prop(im, 540, 960)], cam=(540, 1000, 1.0), t=t)

        @B(16.60)
        def b_mae(t, d, T):
            return self.S(cozinha(), [C(mae, 540, 1860, 1.8, "bravo", "aponta", D["mae"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("Não pergunta.", 17.6))

        @B(18.70)
        def b_tio(t, d, T):
            return self.S(self.sala(), [C(tio, 540, 1860, 1.8, "neutro", "acena", D["tio"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("É coisa de velho.", 19.7))

        @B(21.10)
        def b_toda_vez(t, d, T):
            return self.S(porta(), [C(avo, 360, 1860, 1.7, "neutro", "idle")], cam=(540, 1250, 1.25), t=t)

        @B(23.40)
        def b_barulho(t, d, T):
            return self.S(porta(), [C(avo, 540, 1860, 2.0, "surpreso", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(24.90)
        def b_sorria(t, d, T):
            return self.S(porta(), [C(avo, 540, 1860, 2.2, "feliz", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(25.70)
        def b_encostei(t, d, T):
            return self.S(pc.corredor_porta(self.fc, True), [C(kid, 160, 1860, 1.6, "surpreso", "idle", None, 1)],
                          cam=(420, 1250, 1.25), t=t)

        @B(28.30)
        def b_musica(t, d, T):
            return self.S(pc.corredor_porta(self.fc, True), [C(kid, 160, 1860, 1.6, "surpreso", "idle", None, 1)],
                          [lambda m: pc.notas(m, t, 540, 1100)], (540, 1250, 1.2), t)

        @B(30.20)
        def b_cadeira(t, d, T):
            return self.S(pc.corredor_porta(self.fc, True), [C(kid, 160, 1860, 1.6, "surpreso", "idle", None, 1)],
                          cam=(540, 1250, 1.15), t=t)

        @B(31.80)
        def b_voz(t, d, T):
            return self.S(pc.corredor_porta(self.fc, True), [C(kid, 240, 1860, 1.8, "surpreso", "idle")], cam=(540, 1250, 1.2),
                          t=t, bal=bal("Hoje o dia foi comprido, viu?", 33.7, 0.1))

        @B(35.60)
        def b_alguem(t, d, T):
            return self.S(pc.corredor_porta(self.fc, True), [C(kid, 240, 1860, 1.8, "surpreso", "idle")], cam=(540, 1250, 1.2),
                          t=t, bal=bal("?", 35.9, 0.2, 0.7))

        @B(36.80)
        def b_nao_ouvi(t, d, T):
            return self.S(porta(), [C(kid, 540, 1860, 1.9, "triste", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(38.10)
        def b_semana(t, d, T):
            im = cr.calendario(self.fc, "SEMANA", int(min(7, (T - 38.1) * 3)), total=7, w=960, cor_topo=(200, 80, 70))
            return self.S(self.fundo_quente(), props=[prop(im, 540, 960)], cam=(540, 1000, 1.0), t=t)

        @B(39.10)
        def b_lavar(t, d, T):
            return self.S(self.lavanderia(), [C(kid, 640, 1860, 1.6, "surpreso", "idle", None, -1)],
                          [prop(pc.maquina_lavar(560), 400, 1250)], (540, 1250, 1.2), t)

        @B(41.40)
        def b_seis2(t, d, T):
            im = pc.relogio_parede(self.fc, 6, 0, 700)
            return self.S(self.fundo_quente(), props=[prop(im, 540, 960)], cam=(540, 1000, 1.0), t=t)

        @B(42.20)
        def b_desceu(t, d, T):
            x = 860 - 480 * ease_io(min(1, (T - 42.2) / 1.8))
            return self.S(porta(), [C(avo, x, 1860, 1.6, "neutro", "anda", None, -1)], cam=(540, 1250, 1.15), t=t)

        @B(43.20)
        def b_esqueceu(t, d, T):
            return self.S(pc.corredor_porta(self.fc, True), [], cam=(700, 1100, 1.6), t=t)

        @B(44.70)
        def b_desci(t, d, T):
            return self.S(cz.escada(self.fc), [C(kid, 560, 1500, 1.2, "surpreso", "anda", None, 1)], cam=(540, 1250, 1.2), t=t)

        @B(46.60)
        def b_escuro(t, d, T):
            return self.S(pc.porao(self.fc), [C(kid, 300, 1860, 1.6, "surpreso", "idle")], cam=(540, 1250, 1.2), t=t,
                          fx=lambda f: ef.vinheta_cor(f, (0, 0, 10), 0.6))

        @B(47.40)
        def b_porao(t, d, T):
            bg, xs = pc.mesa_posta(self.fc, 2)
            return self.S(bg, [C(avo, 540, 1760, 1.2, "feliz", "idle")], cam=(540, 1250, 1.1), t=t)

        @B(48.40)
        def b_mesa(t, d, T):
            bg, xs = pc.mesa_posta(self.fc, 2)
            return self.S(bg, [], cam=(540, 1180, 1.4), t=t)

        @B(50.70)
        def b_prato(t, d, T):
            bg, xs = pc.mesa_posta(self.fc, 2)
            return self.S(bg, [], [lambda m: pc.vapor(m, t, xs[0], 1110, 6)], (xs[0], 1150, 1.7), t)

        @B(53.20)
        def b_radio(t, d, T):
            return self.S(pc.porao(self.fc), [], [prop(pc.radio(760), 540, 1100), lambda m: pc.notas(m, t, 540, 900, 3)],
                          (540, 1100, 1.2), t)

        @B(54.70)
        def b_caminhao(t, d, T):
            x = 1400 - 800 * ease_out(min(1, (T - 54.7) / 1.8))
            return self.S(self.rua_noite(), [], [prop(pc.caminhao(900), x, 1400)], (540, 1300, 1.15), t)

        @B(56.80)
        def b_portao(t, d, T):
            return self.S(cz.fachada(self.fc, "CASA", (220, 190, 170), (150, 60, 90), "dia"), [], cam=(540, 1250, 1.2), t=t)

        @B(58.00)
        def b_chave2(t, d, T):
            return self.S(pc.corredor_porta(self.fc, True), [], [prop(ca_.chave(300, -15), 700, 1130)], (700, 1100, 1.7), t)

        @B(59.50)
        def b_olhou(t, d, T):
            bg, xs = pc.mesa_posta(self.fc, 2)
            return self.S(bg, [C(avo, 760, 1860, 1.7, "feliz", "idle", None, -1)], cam=(600, 1250, 1.25), t=t)

        @B(61.60)
        def b_chegou_cedo(t, d, T):
            bg, xs = pc.mesa_posta(self.fc, 2)
            return self.S(bg, [C(avo, 540, 1860, 1.9, "feliz", "idle", D["avo"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("Chegou cedo, hoje.", 61.6))

        @B(63.30)
        def b_avo(t, d, T):
            return self.S(self.fundo_quente(), props=[prop(pc.retrato(self.fc, AVO_PAL, 760), 540, 980)],
                          cam=(540, 1000, 1.05), t=t)

        @B(65.00)
        def b_voltava(t, d, T):
            x = 1400 - 820 * ease_out(min(1, (T - 65.0) / 1.8))
            return self.S(self.rua_noite(), [], [prop(pc.caminhao(900), x, 1400)], (540, 1300, 1.15), t,
                          fx=lambda f: pc.sepia(f, 0.6))

        @B(67.10)
        def b_fita(t, d, T):
            return self.S(pc.porao(self.fc), [], [prop(pc.fita(760, t * 3), 540, 1000)], (540, 1050, 1.2), t)

        @B(68.50)
        def b_morrer(t, d, T):
            k = ease_io(min(1, (T - 68.5) / 1.0))
            return self.S(self.fundo_quente(), props=[prop(pc.retrato(self.fc, AVO_PAL, 760), 540, 980)],
                          cam=(540, 1000, 1.05), t=t, fx=lambda f: Image.blend(f, Image.new("RGB", f.size, (20, 20, 30)), 0.5 * k))

        @B(69.70)
        def b_as_seis(t, d, T):
            im = pc.relogio_parede(self.fc, 6, 0, 760)
            return self.S(self.fundo_quente(), props=[prop(im, 540, 960)], cam=(540, 1000, 1.0), t=t,
                          fx=lambda f: pc.sepia(f, 0.5))

        @B(73.00)
        def b_escada(t, d, T):
            return self.S(cz.escada(self.fc), [C(kid, 560, 1500, 1.2, "surpreso", "idle", None, 1)], cam=(540, 1250, 1.2), t=t)

        @B(74.30)
        def b_nao_brigou(t, d, T):
            bg, xs = pc.mesa_posta(self.fc, 2)
            return self.S(bg, [C(avo, 540, 1860, 1.9, "feliz", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(75.10)
        def b_cadeira3(t, d, T):
            bg, xs = pc.mesa_posta(self.fc, 2)
            return self.S(bg, [C(avo, 300, 1860, 1.6, "feliz", "entrega"), C(kid, 800, 1860, 1.3, "surpreso", "idle", None, -1)],
                          cam=(540, 1250, 1.15), t=t)

        @B(76.90)
        def b_senta(t, d, T):
            bg, xs = pc.mesa_posta(self.fc, 2)
            return self.S(bg, [C(avo, 540, 1860, 1.9, "feliz", "acena", D["avo2"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("Senta, que a sopa tá quente.", 76.9))

        @B(78.60)
        def b_hoje(t, d, T):
            bg, xs = pc.mesa_posta(self.fc, 2)
            return self.S(bg, [C(adulto, 540, 1860, 1.8, "triste", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(79.90)
        def b_todo_dia(t, d, T):
            im = pc.relogio_parede(self.fc, 6, 0, 700)
            return self.S(self.fundo_quente(), props=[prop(im, 540, 960)], cam=(540, 1000, 1.0), t=t)

        @B(82.20)
        def b_desco(t, d, T):
            return self.S(pc.porao(self.fc), [C(adulto, 540, 1860, 1.8, "neutro", "anda")], cam=(540, 1250, 1.2), t=t)

        @B(83.40)
        def b_tres_pratos(t, d, T):
            bg, xs = pc.mesa_posta(self.fc, 3)
            return self.S(bg, [], [lambda m: [pc.vapor(m, t, x, 1110, 4) for x in xs]], (540, 1180, 1.25), t)

        @B(84.80)
        def b_play(t, d, T):
            k = max(0, (T - 86.0) / 1.0)
            f = self.S(pc.porao(self.fc), [], [prop(pc.radio(760), 540, 1100), lambda m: pc.notas(m, t, 540, 900, 3)],
                       (540, 1100, 1.25), t)
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
    ev += [("hit", 12.7, 0.5), ("hit", 43.2, 0.4), ("ding", 58.0, 0.5), ("riser", 44.0, 0.4), ("hit", 47.4, 0.5),
           ("ding", 61.6, 0.4), ("pagina", 38.2, 0.3), ("hit", 66.4, 0.3), ("ding", 84.8, 0.5)]
    amb_ = [("cidade", 0.0, 12.0, 0.25), ("noite", 12.0, 38.0, 0.3), ("cidade", 38.0, 44.0, 0.25), ("noite", 44.0, 62.0, 0.35),
            ("cidade", 62.0, 74.0, 0.25), ("noite", 74.0, dur - 1.5, 0.3)]
    picos = [(12.7, 0.5), (47.4, 0.8), (61.6, 0.7), (76.9, 0.6), (84.8, 0.5)]
    mix = som.mixar_v2(dur, voz, ev, amb_, picos, "triste", 0.2)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def carregar_palavras(caminho):
    troca = {"ouvi": "ouvia", "cumprido,": "comprido,", "cuchou": "puxou", "6": "seis", "6.": "seis.", "9": "nove", "40": "quarenta",
             "2,": "dois,", "dois": "dois"}
    out = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            if w["w"] == "Em" and abs(w["s"] - 53.2) < 0.1:
                w = dict(w, w="E")
            out.append(dict(w=troca.get(w["w"], w["w"]), s=w["s"], e=w["e"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--camera", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_a_porta_do_porao.mp4"))
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

    tmp = tempfile.mkdtemp(prefix="porao_")
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
