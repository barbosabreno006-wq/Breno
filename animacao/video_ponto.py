#!/usr/bin/env python3
"""
"O Ponto do Marcelo" — numa cidade todo mundo é apaixonado pelo narrador, mas é a Admiradora (alta, sem rosto,
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
import cenario_ponto as pp_  # noqa: E402
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

VAL = dict(pele=(214, 170, 130), cabelo=(60, 44, 36), camisa=(50, 90, 170), calca=(50, 70, 130), sapato=(50, 44, 40),
           tipo="pai", bigode=True, listras=(230, 230, 240), iris=(80, 60, 40))
HEL = dict(pele=(232, 186, 150), cabelo=(120, 78, 56), camisa=(120, 126, 140), calca=(70, 74, 90), sapato=(60, 50, 60),
           tipo="moca", vestido=(120, 126, 140), cabelo_estilo="coque", oculos=True, iris=(70, 110, 70))
MAR = dict(pele=(206, 156, 116), cabelo=(40, 30, 28), camisa=(50, 90, 170), calca=(50, 70, 130), sapato=(50, 44, 40),
           tipo="pai", bigode=False, listras=(230, 230, 240), iris=(60, 40, 30))
BIA = dict(pele=(206, 156, 116), cabelo=(40, 30, 28), camisa=(240, 130, 170), calca=(0, 0, 0), sapato=(230, 230, 235),
           tipo="moca", vestido=(240, 130, 170), cabelo_estilo="careca", bandana=(240, 90, 130), iris=(60, 40, 30))
vc.DESTAQUE_VERMELHO = set()
_C = {}
_T = {}


def cz_ponte_rua(f):  # noqa: E301
    if "ruanoite" not in _T:
        _T["ruanoite"] = ca.noite(f.rua().copy(), 0.6)
    return _T["ruanoite"]


IRIS = {"b_cinco", "b_marcelo", "b_internado", "b_helena", "b_sexta", "b_foto", "b_licenca", "b_acordou"}


class FilmeTodos(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao, camera, ancoras):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.val, self.hel, self.mar, self.bia = P_(VAL), P_(HEL), P_(MAR), P_(BIA)
        self.kids = [P_(c) for c in ve.POVO]
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.cortes = [(0.0, 0)]
        self.spec, self.u, self.sub = None, 0.0, 0
        self.dlg = {"hel1": [(44.9, 45.8)], "hel2": [(46.8, 48.7)], "hel3": [(69.3, 70.8)], "hel4": [(72.4, 74.9)],
                    "val1": [(62.4, 65.6)], "val2": [(86.8, 88.6)], "mar1": [(84.3, 85.6)]}
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

        C = self.C
        val, hel, mar, bia = self.val, self.hel, self.mar, self.bia
        pp = pp_
        D = self.dlg

        def bal(txt, t0, y=0.1, x=0.5):
            return [(txt, OUT_W * x, OUT_H * y, t0)]

        def prop(img, x, y):
            return lambda m: m.alpha_composite(img, (int(x - img.width / 2), int(y - img.height / 2)))

        gar = lambda h="madrugada": pp.garagem(self.fc, h)  # noqa: E731
        hosp = lambda: cs.quarto_hospital(self.fc)  # noqa: E731
        cama = lambda x=540, y=1380, w=900: (lambda m: m.alpha_composite(cs.cama_hospital(w), (int(x - w / 2), y)))  # noqa: E731
        escr = lambda n=False: pp.escritorio(self.fc, n)  # noqa: E731

        @B(0.0)
        def b_bato(t, d, T):
            return self.S(pp.portao(self.fc), [C(val, 300, 1860, 1.5, "neutro", "anda", None, 1)], cam=(540, 1250, 1.15), t=t)

        @B(1.50)
        def b_cinco(t, d, T):
            return self.S(self.fundo_cor((24, 30, 60), (10, 12, 30)), props=[prop(pp.relogio_ponto(self.fc, "05:00", 700), 540, 980)],
                          cam=(540, 1000, 1.0), t=t)

        @B(2.80)
        def b_nao_meu(t, d, T):
            return self.S(gar(), [C(val, 300, 1860, 1.6, "neutro", "entrega", None, 1)],
                          [prop(pp.cartao(self.fc, "MARCELO SOUZA", "Mat. 0417", 520), 760, 1330)], (540, 1250, 1.2), t)

        @B(4.10)
        def b_nome(t, d, T):
            return self.S(gar(), [C(val, 540, 1860, 1.9, "feliz", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(6.70)
        def b_mecanico(t, d, T):
            return self.S(gar(), [C(val, 540, 1860, 1.7, "neutro", "bate")], cam=(540, 1250, 1.2), t=t)

        @B(8.90)
        def b_cartao(t, d, T):
            return self.S(self.fundo_cor((24, 30, 60), (10, 12, 30)), props=[prop(pp.cartao(self.fc, "MARCELO SOUZA", "Mat. 0417", 900), 540, 960)],
                          cam=(540, 1000, 1.0), t=t)

        @B(11.70)
        def b_marcelo(t, d, T):
            return self.S(gar("dia"), [C(mar, 540, 1860, 1.9, "feliz", "acena")], cam=(540, 1250, 1.3), t=t)

        @B(13.30)
        def b_box3(t, d, T):
            return self.S(gar("dia"), [C(mar, 300, 1860, 1.5, "feliz", "bate"), C(val, 800, 1860, 1.5, "feliz", "bate", None, -1)],
                          cam=(540, 1250, 1.15), t=t)

        @B(14.60)
        def b_oito_meses(t, d, T):
            bg = gradiente(WW, WH, (34, 34, 52), (14, 14, 24))
            im = cr.calendario(self.fc, "MESES", int(min(8, (T - 14.6) * 5)), total=12, w=960, cor_topo=(70, 74, 90))
            return self.S(bg, props=[prop(im, 540, 960)], cam=(540, 1000, 1.0), t=t)

        @B(16.80)
        def b_internado(t, d, T):
            return self.S(hosp(), [C(mar, 540, 1750, 1.6, "neutro", "idle")], [cama()], (540, 1250, 1.25), t)

        @B(18.00)
        def b_coma(t, d, T):
            im = cs.respirador(t, True, 800)
            return self.S(gradiente(WW, WH, (60, 70, 86), (24, 28, 38)), props=[prop(im, 540, 960)], cam=(540, 1000, 1.0), t=t)

        @B(18.80)
        def b_empresa(t, d, T):
            return self.S(escr(), [C(hel, 540, 1860, 1.8, "neutro", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(19.70)
        def b_trinta(t, d, T):
            bg = gradiente(WW, WH, (34, 34, 52), (14, 14, 24))
            im = cr.calendario(self.fc, "DIAS", int(min(30, (T - 19.7) * 12)), total=30, w=960, cor_topo=(200, 60, 70))
            return self.S(bg, props=[prop(im, 540, 960)], cam=(540, 1000, 1.0), t=t)

        @B(21.80)
        def b_plano(t, d, T):
            ativo = T < 23.0
            return self.S(self.fundo_cor((30, 60, 100), (12, 24, 46)), props=[prop(pp.plano(self.fc, ativo, 900), 540, 960)],
                          cam=(540, 1000, 1.0), t=t)

        @B(24.70)
        def b_bia(t, d, T):
            return self.S(hosp(), [C(bia, 540, 1860, 1.8, "triste", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(27.40)
        def b_quimio(t, d, T):
            return self.S(hosp(), [C(bia, 540, 1750, 1.5, "triste", "idle")], [cama()], (540, 1250, 1.25), t)

        @B(28.40)
        def b_entao(t, d, T):
            return self.S(self.fundo_cor((24, 30, 60), (10, 12, 30)), props=[prop(pp.relogio_ponto(self.fc, "05:00", 760), 540, 980)],
                          cam=(540, 1000, 1.0), t=t)

        @B(30.50)
        def b_passo(t, d, T):
            return self.S(pp.portao(self.fc), [C(val, 300, 1860, 1.6, "neutro", "entrega")],
                          [prop(pp.relogio_ponto(self.fc, "05:00", 420), 800, 1150)], (540, 1250, 1.2), t)

        @B(32.40)
        def b_depois(t, d, T):
            return self.S(gar(), [C(val, 540, 1860, 1.7, "neutro", "bate")], cam=(540, 1250, 1.2), t=t)

        @B(34.60)
        def b_helena(t, d, T):
            return self.S(escr(), [C(hel, 540, 1860, 1.8, "neutro", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(36.80)
        def b_folha(t, d, T):
            return self.S(self.fundo_cor((70, 80, 100), (30, 34, 46)), props=[prop(pp.folha_ponto(self.fc, 8, 860), 540, 980)],
                          cam=(540, 1000, 1.0), t=t)

        @B(38.70)
        def b_nenhuma(t, d, T):
            return self.S(self.fundo_cor((70, 80, 100), (30, 34, 46)), props=[prop(pp.folha_ponto(self.fc, 8, 860), 540, 980)],
                          cam=(540, 800, 1.5), t=t)

        @B(41.60)
        def b_perfeito(t, d, T):
            return self.S(escr(), [C(hel, 540, 1860, 1.9, "surpreso", "idle")], cam=(540, 1250, 1.3), t=t,
                          bal=bal("?", 42.0, 0.2, 0.7))

        @B(42.80)
        def b_ficha(t, d, T):
            return self.S(escr(), [C(hel, 540, 1860, 1.9, "surpreso", "idle", D["hel1"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("Internado.", 44.9))

        @B(45.90)
        def b_pergunta(t, d, T):
            return self.S(escr(), [C(hel, 540, 1860, 1.9, "bravo", "aponta", D["hel2"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("Quem está batendo o ponto de um homem em coma?", 46.8))

        @B(49.10)
        def b_pra_mim(t, d, T):
            return self.S(escr(), [C(hel, 300, 1860, 1.5, "neutro", "aponta", None, 1), C(val, 800, 1860, 1.5, "neutro", "idle", None, -1)],
                          cam=(540, 1250, 1.2), t=t)

        @B(50.60)
        def b_chego(t, d, T):
            return self.S(escr(), [C(val, 540, 1860, 1.9, "surpreso", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(52.70)
        def b_sexta(t, d, T):
            return self.S(pp.estacionamento(self.fc), [], [prop(pp.carro(900), 540, 1700)], (540, 1450, 1.2), t,
                          fx=lambda f: Image.blend(f, Image.new("RGB", f.size, (10, 14, 50)), 0.15))

        @B(55.30)
        def b_cinco_ponto(t, d, T):
            return self.S(self.fundo_cor((24, 30, 60), (10, 12, 30)), props=[prop(pp.relogio_ponto(self.fc, "05:00", 760), 540, 980)],
                          cam=(540, 1000, 1.0), t=t)

        @B(56.50)
        def b_viu(t, d, T):
            return self.S(pp.portao(self.fc), [C(val, 300, 1860, 1.5, "neutro", "entrega", None, 1),
                                               C(hel, 820, 1860, 1.5, "surpreso", "idle", None, -1)],
                          [prop(pp.relogio_ponto(self.fc, "05:00", 380), 540, 1200)], (540, 1250, 1.2), t)

        @B(57.60)
        def b_nao_corri(t, d, T):
            return self.S(pp.portao(self.fc), [C(val, 540, 1860, 1.9, "neutro", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(58.80)
        def b_foto(t, d, T):
            im = cs.polaroid(self.fc, cs._fig(BIA, "feliz", 0.8), "BIA", 700)
            return self.S(self.fundo_cor((70, 60, 90), (30, 24, 44)), props=[prop(im, 540, 1000)], cam=(540, 1000, 1.05), t=t)

        @B(62.40)
        def b_cobriu(t, d, T):
            return self.S(pp.portao(self.fc), [C(val, 540, 1860, 1.9, "triste", "idle", D["val1"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("Ele cobriu meu turno por vinte anos, Helena.", 62.4))

        @B(64.80)
        def b_cobrindo(t, d, T):
            return self.S(pp.portao(self.fc), [C(val, 540, 1860, 1.9, "triste", "idle", D["val1"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("Eu só estou cobrindo o dele.", 64.8))

        @B(66.20)
        def b_silencio(t, d, T):
            return self.S(pp.portao(self.fc), [C(hel, 540, 1860, 1.9, "triste", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(68.00)
        def b_baixinho(t, d, T):
            return self.S(pp.portao(self.fc), [C(hel, 540, 1860, 1.9, "triste", "idle", D["hel3"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("Eu sei desde o primeiro mês.", 69.3))

        @B(71.00)
        def b_sem_entender(t, d, T):
            return self.S(pp.portao(self.fc), [C(val, 540, 1860, 1.9, "surpreso", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(72.20)
        def b_coragem(t, d, T):
            return self.S(pp.portao(self.fc), [C(hel, 540, 1860, 1.9, "feliz", "idle", D["hel4"])], cam=(540, 1250, 1.3), t=t,
                          bal=bal("Eu só precisava que alguém me pedisse ajuda.", 72.4))

        @B(75.30)
        def b_licenca(t, d, T):
            im = pp.papel_licenca(self.fc, min(1, (T - 76.0) / 1.2), 820)
            return self.S(escr(), [], [prop(im, 540, 980)], (540, 1100, 1.1), t)

        @B(78.40)
        def b_plano_ok(t, d, T):
            return self.S(self.fundo_cor((30, 60, 100), (12, 24, 46)), props=[prop(pp.plano(self.fc, True, 900), 540, 960)],
                          cam=(540, 1000, 1.0), t=t)

        @B(80.30)
        def b_ninguem(t, d, T):
            return self.S(gar("dia"), [C(val, 300, 1860, 1.6, "feliz", "idle", None, 1), C(hel, 800, 1860, 1.6, "feliz", "idle", None, -1)],
                          cam=(540, 1250, 1.2), t=t)

        @B(81.50)
        def b_acordou(t, d, T):
            return self.S(hosp(), [C(mar, 540, 1750, 1.7, "feliz", "idle"), C(bia, 220, 1860, 1.3, "feliz", "acena", None, 1)],
                          [cama()], (540, 1250, 1.2), t)

        @B(83.10)
        def b_atrasado(t, d, T):
            return self.S(hosp(), [C(mar, 540, 1750, 1.8, "surpreso", "idle", D["mar1"])], [cama()], (540, 1250, 1.3), t,
                          bal=bal("Tô atrasado?", 84.3))

        @B(85.90)
        def b_sorri(t, d, T):
            k = max(0, (T - 88.2) / 1.0)
            f = self.S(hosp(), [C(val, 540, 1860, 1.9, "feliz", "idle", D["val2"])], cam=(540, 1250, 1.3), t=t,
                       bal=bal("Não. Cheguei cedo, como sempre.", 86.8))
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
    ev += [("bip", 1.6, 0.6), ("bip", 28.9, 0.6), ("bip", 30.0, 0.6), ("bip", 55.4, 0.6), ("bip", 56.4, 0.6),
           ("hit", 42.8, 0.5), ("hit", 44.9, 0.4), ("riser", 66.0, 0.4), ("ding", 69.3, 0.4), ("pagina", 76.0, 0.3),
           ("ding", 78.5, 0.5), ("ding", 85.9, 0.5), ("hit", 62.4, 0.3)]
    for k in range(12):
        ev.append(("bip", 18.0 + k * 0.7, 0.45))
    amb_ = [("noite", 0.0, 11.0, 0.35), ("cidade", 11.0, 16.5, 0.2), ("hospital", 16.5, 19.0, 0.35), ("cidade", 19.0, 24.0, 0.2),
            ("hospital", 24.0, 28.0, 0.35), ("noite", 28.0, 34.0, 0.3), ("cidade", 34.0, 52.0, 0.2), ("noite", 52.0, 80.0, 0.35),
            ("hospital", 80.0, dur - 1.5, 0.35)]
    picos = [(18.0, 0.6), (42.8, 0.7), (62.4, 0.6), (69.3, 0.8), (84.3, 0.9)]
    mix = som.mixar_v2(dur, voz, ev, amb_, picos, "triste", 0.2)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def carregar_palavras(caminho):
    troca = {"5": "cinco", "49": "quarenta e nove", "3.": "três.", "8": "oito", "30": "trinta", "6": "seis", "20": "vinte",
             "efeito": "perfeito", "chega": "chego", "Tu": "Tô", "RH,": "RH,"}
    out = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            if w["w"] == "o" and abs(w["s"] - 51.2) < 0.1:
                continue
            out.append(dict(w=troca.get(w["w"], w["w"]), s=w["s"], e=w["e"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--camera", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_o_ponto_do_marcelo.mp4"))
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

    tmp = tempfile.mkdtemp(prefix="ponto_")
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
