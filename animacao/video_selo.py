#!/usr/bin/env python3
"""
"O Selo" — vídeo original que junta o melhor dos exemplos do usuário:
  * regra do mundo na 1ª frase + gancho de cortes rápidos nos primeiros 10 s;
  * selos de dificuldade (FÁCIL / NORMAL / DIFÍCIL / PESADELO) flutuando sobre as cabeças, como no vídeo de jogo;
  * neblina vermelha no "pesadelo", props de história (certidão, relógio, livro de regras), polaroid/papel;
  * virada emocionante no final (a mãe puxou o selo do filho).
Motor v3: personagens variados com sombreado e olhar, boca mexendo, grão, som v2, render paralelo.

    python3 animacao/video_selo.py --narracao narr.mp3 --transcricao transcricao.json --fonte Poppins.ttf
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
import video_abracos as vb  # noqa: E402
import boneco  # noqa: E402
import cenario_rico as cr  # noqa: E402
import cenario_escola as cs  # noqa: E402
import cenario_selo as sl  # noqa: E402
import efeitos as ef  # noqa: E402
import ambiente as amb  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io, particulas)

g.HANDHELD = False
g.GRAO = 0.55
boneco.Boneco.AMP = 1.8
boneco.Boneco.SHADE = 1.0
random.seed(2828)

NARR = dict(pele=(226, 176, 134), cabelo=(70, 46, 34), camisa=(80, 150, 210), calca=(90, 90, 110), sapato=(240, 240, 245),
            tipo="pai", bigode=False, cabelo_estilo="topete", oculos=True, iris=(70, 130, 190), bolso=True)
NARR_C = dict(NARR, camisa=(250, 200, 70), calca=(70, 90, 140), tipo="menino", oculos=True)
MAE = dict(pele=(214, 160, 120), cabelo=(70, 44, 32), camisa=(214, 120, 160), calca=(0, 0, 0), sapato=(110, 70, 90),
           tipo="moca", vestido=(214, 120, 160), cabelo_estilo="coque", avental=(120, 170, 230), iris=(90, 60, 40),
           brinco=(250, 210, 60))
MAE_J = dict(MAE, cabelo_estilo="longo", avental=None, camisa=(245, 245, 250), vestido=(245, 245, 250))
CHEFE = dict(pele=(232, 186, 150), cabelo=(150, 150, 156), camisa=(240, 240, 245), calca=(60, 62, 80), sapato=(40, 40, 45),
             tipo="pai", gravata=(200, 60, 70), cabelo_estilo="ralo", oculos=True, iris=(80, 110, 80))
ENFERM = dict(pele=(196, 140, 100), cabelo=(40, 30, 28), camisa=(170, 220, 230), calca=(0, 0, 0), sapato=(240, 240, 245),
              tipo="moca", vestido=(170, 220, 230), cabelo_estilo="trancas", iris=(70, 50, 36))
POVO_P = [
    dict(pele=(150, 100, 70), cabelo=(35, 28, 26), camisa=(240, 150, 60), calca=(70, 80, 110), sapato=(50, 50, 55),
         tipo="menino", cabelo_estilo="afro", listras=(255, 255, 255)),
    dict(pele=(232, 186, 150), cabelo=(220, 60, 120), camisa=(40, 40, 50), calca=(60, 60, 80), sapato=(30, 30, 34),
         tipo="menino", cabelo_estilo="moicano"),
    dict(pele=(160, 110, 80), cabelo=(60, 40, 30), camisa=(250, 190, 60), calca=(0, 0, 0), sapato=(150, 70, 70),
         tipo="moca", vestido=(250, 190, 60), cabelo_estilo="cacheado", sardas=True),
    dict(pele=(222, 170, 128), cabelo=(110, 70, 50), camisa=(150, 90, 200), calca=(0, 0, 0), sapato=(90, 70, 110),
         tipo="moca", vestido=(150, 90, 200), cabelo_estilo="trancas"),
    dict(pele=(232, 186, 150), cabelo=(200, 200, 205), camisa=(110, 150, 110), calca=(110, 100, 80), sapato=(60, 50, 50),
         tipo="pai", cabelo_estilo="careca", colete=(80, 80, 90), oculos=True),
    dict(pele=(196, 140, 100), cabelo=(40, 32, 30), camisa=(210, 80, 70), calca=(60, 70, 100), sapato=(50, 50, 55),
         tipo="pai", bigode=False, cabelo_estilo="topete", gorro=None),
]
vc.DESTAQUE_VERMELHO = set()
_C = {}


class FilmeSelo(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers({k: v for k, v in pal.items() if v is not None}, self)  # noqa: E731
        self.narr, self.narrc, self.mae, self.maej = P_(NARR), P_(NARR_C), P_(MAE), P_(MAE_J)
        self.chefe, self.enf = P_(CHEFE), P_(ENFERM)
        self.povo = [P_(c) for c in POVO_P]
        self.blur = {}
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        fc_ = fc
        self.dia, self.tarde, self.noite = (cr.praca_rica(fc_, h) for h in ("dia", "tarde", "noite"))
        self.sala = cs.sala_aula(fc_, "", "12")
        self.univ = sl.fachada(fc_, "UNIVERSIDADE", (214, 196, 168), (60, 70, 130))
        self.cart = sl.fachada(fc_, "CARTÓRIO", (200, 214, 190), (70, 120, 90), "tarde")
        self.escr = va.escritorio()
        self.coz = va.cozinha()
        self.quarto = sl.quarto_simples(fc_, False, True)
        self.quarto_inv = sl.quarto_simples(fc_, True, True)
        self.esc = sl.escada(fc_)
        self.hosp = cs.quarto_hospital(fc_)
        self.dlg = {"mae": [(86.12, 90.2), (91.9, 94.4), (66.44, 69.0)], "narr": [(84.14, 85.8), (90.62, 91.7)]}

        self.beats = []
        self._definir()
        self.planos = []
        for i, (ini, fn) in enumerate(self.beats):
            fim = self.beats[i + 1][0] if i + 1 < len(self.beats) else dur_total
            tr = "iris" if fn.__name__ in ("b_certidao", "b_bebe_pesadelo", "b_corri", "b_mudou") else "corte"
            self.planos.append((ini, fim - ini, (lambda t, d, fn=fn: fn(t, d, self.T)), "", tr))
        self.p_preto = None
        self.cortes = g.subcortes(self.planos, palavras)

    # ----------------------------------------------------------------- utilidades
    def balao_t(self, f, txt, x, y, t0):
        if self.T >= t0:
            self.balao(f, txt, x, y, self.T - t0)

    def C(self, pers, x, by, e=1.4, expr="neutro", pose="idle", fala=None, sx=1, selo=None, **kw):
        return (pers, x, by, e, expr, pose, fala, sx, selo, kw)

    def S(self, bg, chars=(), props=(), cam=(540, 1250, 1.25), t=0.0, bal=(), fx=None, ambiente=None):
        m = bg.copy()
        if ambiente:
            ambiente(m, t)
        for pers, x, by, e, expr, pose, fala, sx, selo, kw in chars:
            cr.sombra(m, x, by - 4, e * 250)
            pers(m, t, x, by, e, expr=expr, pose=pose, fala=fala, sx=sx, **kw)
            if selo:
                sl.selo_mundo(m, self.fc, selo, x, by - 735 * e, max(0.5, e * 0.82), self.T)
        for pr in props:
            pr(m)
        f = self.cam(m, *cam)
        for txt, x, y, t0 in bal:
            self.balao_t(f, txt, x, y, t0)
        if fx:
            f = fx(f)
        return f

    def pesadelo(self, f):
        return ef.vinheta_cor(f, (200, 20, 70), 0.62, 0.5)

    def feliz(self, f):
        return ef.bloom(ef.raios(f, self.T, (255, 226, 130), 16, 22), 0.25)

    def perto(self, pers, bg, nome, expr="neutro", selo=None, z=1.05, fx=None, e=2.5, pose="idle", fala=None):
        m = self.fundo_blur(nome, bg)
        cr.sombra(m, 540, 2340, 520)
        pers(m, self.T, 540, 2350, e, expr=expr, pose=pose, fala=fala)
        if selo:
            sl.selo_mundo(m, self.fc, selo, 540, 2350 - 735 * e + 20, e * 0.82, self.T)
        f = self.cam(m, 540, 950, z)
        return fx(f) if fx else f

    def prop(self, img, x, y, w=None, rot=0.0):
        def f(m):
            im = img if not w else img.resize((w, int(img.height * w / img.width)), Image.BICUBIC)
            if rot:
                im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
            m.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))
        return f

    def peso_hum(self, tam):
        return lambda m: m.alpha_composite(sl.saco_peso(int(260 + 120 * tam), tam), (390, 1050 - int(120 * tam)))

    # ----------------------------------------------------------------- beats
    def _definir(self):
        B = self.beats
        C, S = self.C, self.S
        P = self.povo

        def beat(ini):
            def deco(fn):
                B.append((ini, fn))
                return fn
            return deco

        def vida_dia(m, t):
            amb.nuvens(m, t, n=4, seed=3)
            amb.passaros(m, t, n=3, seed=4)

        @beat(0.0)
        def b_regra(t, d, T):
            chars = [C(P[0], 130, 1830, 1.0, "feliz", "anda", selo="NORMAL"), C(P[2], 330, 1840, 1.1, "neutro", "idle",
                                                                                  selo="DIFÍCIL"),
                     C(self.narr, 560, 1850, 1.25, "surpreso", "idle", selo="FÁCIL"),
                     C(P[3], 800, 1840, 1.1, "triste", "idle", selo="PESADELO"),
                     C(P[1], 980, 1830, 1.0, "feliz", "anda", selo="NORMAL")]
            return S(self.dia, chars, cam=(540, 1300, 1.0), t=t, ambiente=vida_dia)

        @beat(4.84)
        def b_facil(t, d, T):
            return self.perto(P[5], self.dia, "p5", "feliz", "FÁCIL", fx=self.feliz)

        @beat(5.58)
        def b_normal(t, d, T):
            return self.perto(P[4], self.dia, "p4", "neutro", "NORMAL")

        @beat(6.36)
        def b_dificil(t, d, T):
            return self.perto(P[2], self.dia, "p2", "triste", "DIFÍCIL")

        @beat(7.34)
        def b_pesadelo(t, d, T):
            return self.perto(P[3], self.dia, "p3", "chora", "PESADELO", fx=self.pesadelo)

        @beat(8.52)
        def b_peso(t, d, T):
            bg = gradiente(WW, WH, (60, 56, 100), (32, 28, 60))
            chars = [C(P[5], 160, 1840, 1.0, "feliz", "idle", selo="FÁCIL"), C(P[4], 440, 1840, 1.1, "neutro", "idle",
                                                                                selo="NORMAL"),
                     C(P[2], 720, 1840, 1.2, "triste", "idle", selo="DIFÍCIL"), C(P[3], 960, 1840, 1.2, "chora", "idle",
                                                                                   selo="PESADELO")]
            pesos = [lambda m, i=i: m.alpha_composite(sl.saco_peso(120 + 80 * i, 0.2 + 0.7 * i / 3),
                                                      (80 + i * 270, 1500 - 70 * i)) for i in range(4)]
            return S(bg, chars, pesos, (540, 1300, 1.0), t)

        @beat(10.96)
        def b_ninguem_troca(t, d, T):
            chars = [C(P[i % 6], 100 + i * 180, 1840, 0.95, "neutro", "anda", selo=("NORMAL", "FÁCIL", "DIFÍCIL")[i % 3])
                     for i in range(6)]
            return S(self.tarde, chars, cam=(540, 1300, 1.0), t=t, ambiente=vida_dia)

        @beat(13.06)
        def b_meu_facil(t, d, T):
            return self.perto(self.narr, self.dia, "narr", "feliz", "FÁCIL", fx=self.feliz, pose="bracos_abertos")

        @beat(14.98)
        def b_dez(t, d, T):
            def prova(m):
                p = Pincel(WW, WH)
                p.ret((600, 1380, 980, 1720), (250, 248, 240), r=8, ow=6)
                m.alpha_composite(p.pronto())
                ImageDraw.Draw(m).text((690, 1440), "10", font=vc.fonte(self.fc, 190), fill=(40, 160, 90))
            return S(self.sala, [C(self.narrc, 320, 1840, 1.5, "feliz", "idle", selo="FÁCIL")], [prova], (540, 1250, 1.2), t)

        @beat(16.70)
        def b_bolsa(t, d, T):
            def carta(m):
                p = Pincel(WW, WH)
                p.ret((620, 1360, 960, 1600), (250, 248, 238), r=8, ow=6)
                p.elipse((830, 1510, 920, 1600), (214, 170, 70), ow=5)
                m.alpha_composite(p.pronto())
                ImageDraw.Draw(m).text((650, 1400), "BOLSA", font=vc.fonte(self.fc, 74), fill=(60, 80, 160))
            return S(self.univ, [C(self.narr, 340, 1850, 1.5, "feliz", "bracos_abertos", selo="FÁCIL")], [carta],
                     (540, 1250, 1.15), t, fx=self.feliz)

        @beat(18.32)
        def b_emprego(t, d, T):
            return S(self.escr, [C(self.chefe, 800, 1850, 1.5, "feliz", "entrega"),
                                 C(self.narr, 300, 1850, 1.5, "feliz", "entrega", selo="FÁCIL")], cam=(540, 1250, 1.15), t=t)

        @beat(20.64)
        def b_sortudo(t, d, T):
            chars = [C(P[i], 150 + i * 190, 1840, 1.0, "ri", "aponta") for i in range(4)]
            chars.append(C(self.narr, 900, 1850, 1.3, "feliz", "idle", selo="FÁCIL"))
            return S(self.tarde, chars, cam=(540, 1300, 1.05), t=t, ambiente=vida_dia)

        @beat(23.44)
        def b_mae_pesadelo(t, d, T):
            return self.perto(self.mae, self.coz, "coz", "neutro", "PESADELO", fx=self.pesadelo)

        @beat(25.86)
        def b_4manha(t, d, T):
            bg = self.quarto
            relogio = lambda m: m.alpha_composite(sl.relogio_digital(self.fc, "04:00", 560), (260, 520))  # noqa: E731
            return S(bg, [C(self.mae, 540, 1850, 1.6, "triste", "bate", selo="PESADELO")], [relogio], (540, 1250, 1.15), t,
                     fx=self.pesadelo)

        @beat(26.9)
        def b_limpar(t, d, T):
            bg = self.escr
            esfregao = lambda m: ImageDraw.Draw(m).line((700 + 40 * math.sin(t * 6), 1500, 820, 1840), fill=(120, 90, 60, 255),  # noqa: E731
                                                       width=18)
            return S(bg, [C(self.mae, 540, 1850, 1.6, "triste", "bate")], [esfregao], (540, 1250, 1.2), t)

        @beat(28.84)
        def b_dois_empregos(t, d, T):
            bg = gradiente(WW, WH, (50, 46, 74), (28, 24, 46))
            carta = lambda x, k: (lambda m: (m.alpha_composite(self._carta("DEMITIDA", k), (x, 700))))  # noqa: E731
            return S(bg, props=[carta(80, 0), carta(560, 1)], cam=(540, 1000, 1.0), t=t, fx=self.pesadelo)

        @beat(30.62)
        def b_escada(t, d, T):
            k = ease_in_(min(1, (T - 30.7) / 1.0))
            return S(self.esc, [C(self.mae, 740 - 240 * k, 1400 + 400 * k, 1.35, "surpreso", "bracos_abertos",
                                  rot=70 * k)], cam=(540, 1250, 1.1), t=t)

        @beat(32.58)
        def b_doente(t, d, T):
            cama = lambda m: m.alpha_composite(cs.cama_hospital(900), (90, 1400))  # noqa: E731
            return S(self.quarto_inv, [C(self.mae, 540, 1790, 1.5, "chora", "idle")], [cama], (540, 1250, 1.2), t,
                     fx=lambda f: ef.neblina(f, T, (200, 220, 255), 40))

        @beat(34.66)
        def b_jantar(t, d, T):
            def mesa(m):
                p = Pincel(WW, WH)
                p.ret((120, 1560, 960, 1640), (160, 108, 66), r=10)
                p.elipse((380, 1500, 700, 1580), (250, 250, 250), ow=6)
                m.alpha_composite(p.pronto())
                for i in range(4):
                    ph = (t * 0.7 + i * 0.25) % 1
                    m.alpha_composite(brilho((90, 90), (255, 255, 255), 40, 0.5 * (1 - ph)), (int(520 + 14 * math.sin(i + t * 3)), int(1440 - ph * 200)))
            return S(self.coz, [C(self.mae, 260, 1850, 1.4, "feliz", "entrega"),
                                C(self.narr, 820, 1850, 1.4, "feliz", "idle")], [mesa], (540, 1250, 1.1), t)

        @beat(38.40)
        def b_injusto(t, d, T):
            bg = gradiente(WW, WH, (60, 56, 100), (32, 28, 60))
            return S(bg, [C(self.narr, 320, 1850, 1.5, "triste", "bolso", selo="FÁCIL"),
                          C(self.mae, 780, 1850, 1.5, "triste", "idle", selo="PESADELO")], cam=(540, 1250, 1.1), t=t,
                     fx=self.pesadelo)

        @beat(39.98)
        def b_devia(t, d, T):
            bg = gradiente(WW, WH, (60, 56, 100), (32, 28, 60))
            troca = T > 40.9
            return S(bg, [C(self.narr, 320, 1850, 1.5, "triste", "idle", selo="PESADELO" if troca else "FÁCIL"),
                          C(self.mae, 780, 1850, 1.5, "feliz", "idle", selo="FÁCIL" if troca else "PESADELO")],
                     cam=(540, 1250, 1.1), t=t)

        @beat(41.84)
        def b_meu_nao(t, d, T):
            return self.perto(self.narr, self.coz, "coz", "triste", "FÁCIL")

        @beat(42.84)
        def b_18(t, d, T):
            return S(self.cart, [C(self.narr, 540, 1850, 1.5, "surpreso", "idle", selo="FÁCIL")], cam=(540, 1250, 1.1), t=t)

        @beat(45.62)
        def b_certidao(t, d, T):
            bg = gradiente(WW, WH, (72, 60, 56), (36, 30, 30))
            cert = sl.certidao(self.fc, 0, 0.0, 0.0, 860)
            return S(bg, props=[self.prop(cert, 540, 1000)], cam=(540, 1000, 1.0 + 0.15 * (T - 45.6) / 3), t=t)

        @beat(48.38)
        def b_anotacao(t, d, T):
            bg = gradiente(WW, WH, (72, 60, 56), (36, 30, 30))
            k = ease_io(min(1, (T - 48.4) / 4.0))
            cert = sl.certidao(self.fc, 0, k, 0.0, 860)
            return S(bg, props=[self.prop(cert, 540, 1000)], cam=(540, 1000, 1.25), t=t)

        @beat(52.6)
        def b_pesadelo_cert(t, d, T):
            bg = gradiente(WW, WH, (72, 40, 70), (36, 18, 40))
            m_ = lambda m: sl.selo_mundo(m, self.fc, "PESADELO", 540, 960, 2.6, T)  # noqa: E731
            return S(bg, props=[m_], cam=(540, 1000, 1.0), t=t, fx=self.pesadelo)

        @beat(53.36)
        def b_transferido(t, d, T):
            bg = gradiente(WW, WH, (72, 60, 56), (36, 30, 30))
            k = ease_out(min(1, (T - 53.4) / 0.35))
            cert = sl.certidao(self.fc, 0, 1.0, k, 860)
            f = S(bg, props=[self.prop(cert, 540, 1000)], cam=(540, 1000, 1.2), t=t)
            return f

        @beat(56.14)
        def b_li_duas(t, d, T):
            return self.perto(self.narr, self.cart, "cart", "surpreso", None, fx=None)

        @beat(57.28)
        def b_regra_livro(t, d, T):
            bg = gradiente(WW, WH, (60, 50, 70), (30, 26, 44))
            return S(bg, props=[self.prop(sl.livro_regras(self.fc, 960), 540, 1000)], cam=(540, 1000, 1.05 + 0.1 * (T - 57.3) / 3), t=t)

        @beat(60.48)
        def b_abraco_mae(t, d, T):
            cama = lambda m: m.alpha_composite(cs.cama_hospital(900), (90, 1400))  # noqa: E731
            bebe = lambda m: m.alpha_composite(vb.bebe(240), (480, 1460))  # noqa: E731
            return S(self.hosp, [C(self.maej, 560, 1760, 1.6, "feliz", "idle")], [cama, bebe], (540, 1250, 1.2), t)

        @beat(64.94)
        def b_bebe_pesadelo(t, d, T):
            bg = gradiente(WW, WH, (70, 40, 74), (34, 18, 42))
            bebe = lambda m: m.alpha_composite(vb.bebe(700), (190, 900))  # noqa: E731
            selo = lambda m: sl.selo_mundo(m, self.fc, "PESADELO", 540, 780, 1.8, T)  # noqa: E731
            return S(bg, props=[bebe, selo], cam=(540, 1100, 1.0), t=t, fx=self.pesadelo)

        @beat(66.44)
        def b_passa(t, d, T):
            return S(self.hosp, [C(self.maej, 500, 1760, 1.7, "feliz", "entrega", self.dlg["mae"][2:])],
                     [lambda m: m.alpha_composite(vb.bebe(260), (640, 1380))], (540, 1250, 1.2), t,
                     bal=[("Passa pra mim.", OUT_W * 0.55, OUT_H * 0.12, 67.8)])

        @beat(69.32)
        def b_bebe_doente(t, d, T):
            bg = gradiente(WW, WH, (40, 44, 62), (18, 20, 34))
            mon = lambda m: m.alpha_composite(cs.respirador(t, True, 700), (190, 640))  # noqa: E731
            f = S(bg, props=[mon], cam=(540, 1000, 1.0), t=t)
            ef.barra_vida(f, self.fc, 160, 160, 400, 0.15 + 0.03 * math.sin(T * 5), (230, 50, 70), "VIDA DO BEBÊ")
            return f

        @beat(73.10)
        def b_sabia(t, d, T):
            return self.perto(self.maej, self.hosp, "hosp", "triste", None)

        @beat(74.10)
        def b_puxou(t, d, T):
            bg = gradiente(WW, WH, (60, 50, 90), (30, 24, 54))
            k = ease_io(min(1, (T - 74.1) / 0.9))
            bebe = lambda m: m.alpha_composite(vb.bebe(300), (150, 1150))  # noqa: E731

            def voa(m):
                x, y = 300 + 520 * k, 1100 - 560 * k
                sl.selo_mundo(m, self.fc, "PESADELO", x, y, 1.5, T)
            f = S(bg, [C(self.maej, 820, 1850, 1.5, "feliz", "idle", selo=None)], [bebe, voa], (540, 1250, 1.0), t)
            return self.pesadelo(f) if k < 0.95 else f

        @beat(75.58)
        def b_tudo_certo(t, d, T):
            def colagem(m):
                for i, (x, y, tx) in enumerate(((140, 1180, "10"), (470, 1120, "OURO"), (790, 1180, "1º"))):
                    p = Pincel(320, 260)
                    p.ret((10, 10, 310, 250), (250, 248, 240), r=14, ow=6)
                    m.alpha_composite(p.pronto(), (x, y))
                    ImageDraw.Draw(m).text((x + 160 - vc.fonte(self.fc, 100).getlength(tx) / 2, y + 60), tx,
                                           font=vc.fonte(self.fc, 100), fill=(40, 160, 90))
            return S(self.tarde, [C(self.narrc, 540, 1850, 1.5, "feliz", "bracos_abertos", selo="FÁCIL")], [colagem],
                     (540, 1250, 1.1), t, fx=self.feliz)

        @beat(77.56)
        def b_tudo_errado(t, d, T):
            return S(self.dia, [C(self.mae, 540, 1850, 1.6, "chora", "idle", selo="PESADELO")], cam=(540, 1250, 1.15), t=t,
                     fx=lambda f: self.pesadelo(f))

        @beat(79.84)
        def b_corri(t, d, T):
            x = -100 + 800 * ease_io(min(1, (T - 79.8) / 1.2))
            return S(self.tarde, [C(self.narr, x, 1850, 1.4, "surpreso", "corre", selo="NORMAL")], cam=(540, 1300, 1.1), t=t,
                     ambiente=vida_dia)

        @beat(81.02)
        def b_cantarolando(t, d, T):
            def notas(m):
                d_ = ImageDraw.Draw(m)
                for i in range(4):
                    ph = (t * 0.5 + i * 0.25) % 1
                    d_.text((620 + 40 * i + 20 * math.sin(t * 3 + i), 1100 - ph * 400), "♪", font=vc.fonte(self.fc, 80 + 10 * i),
                            fill=(255, 214, 40, int(255 * (1 - ph))))
            return S(self.coz, [C(self.mae, 420, 1850, 1.6, "feliz", "bate", selo="PESADELO")], [notas], (540, 1250, 1.15), t)

        @beat(84.14)
        def b_senhora_sabia(t, d, T):
            return S(self.coz, [C(self.narr, 300, 1850, 1.5, "triste", "bracos_abertos", self.dlg["narr"][:1]),
                                C(self.mae, 780, 1850, 1.5, "neutro", "idle", selo="PESADELO")], cam=(540, 1250, 1.1), t=t,
                     bal=[("A senhora sabia?", OUT_W * 0.35, OUT_H * 0.12, 84.14)])

        @beat(86.12)
        def b_negocio(t, d, T):
            return S(self.coz, [C(self.narr, 300, 1850, 1.5, "surpreso", "idle"),
                                C(self.mae, 780, 1850, 1.5, "feliz", "entrega", self.dlg["mae"][:1], selo="PESADELO")],
                     cam=(540, 1250, 1.1), t=t,
                     bal=[("Foi o melhor negócio da minha vida.", OUT_W * 0.55, OUT_H * 0.1, 87.6)])

        @beat(90.62)
        def b_devolver(t, d, T):
            return S(self.coz, [C(self.narr, 300, 1850, 1.5, "chora", "entrega", self.dlg["narr"][1:]),
                                C(self.mae, 780, 1850, 1.5, "triste", "idle", self.dlg["mae"][1:2], selo="PESADELO")],
                     cam=(540, 1250, 1.1), t=t, bal=[("A regra só vale uma vez.", OUT_W * 0.55, OUT_H * 0.1, 93.14)])

        @beat(94.86)
        def b_descobri(t, d, T):
            def lampada(m):
                m.alpha_composite(brilho((500, 500), (255, 236, 150), 240, 0.9), (290, 520))
                p = Pincel(WW, WH)
                p.elipse((470, 700, 610, 840), (255, 240, 160), ow=8)
                p.ret((500, 830, 580, 880), (160, 160, 170), r=6)
                m.alpha_composite(p.pronto())
            return S(self.coz, [C(self.narr, 540, 1850, 1.6, "feliz", "aponta")], [lampada], (540, 1250, 1.15), t)

        @beat(97.14)
        def b_carregar(t, d, T):
            saco = lambda m: m.alpha_composite(sl.saco_peso(420, 0.9), (330, 1380))  # noqa: E731
            return S(self.tarde, [C(self.narr, 250, 1850, 1.5, "feliz", "entrega", selo="NORMAL"),
                                  C(self.mae, 830, 1850, 1.5, "feliz", "entrega", selo="PESADELO")], [saco], (540, 1250, 1.1), t,
                     ambiente=vida_dia)

        @beat(100.26)
        def b_4h(t, d, T):
            bg = self.noite
            x = 150 + 480 * ease_io(min(1, (T - 100.3) / 2.4))
            f = S(bg, [C(self.narr, x, 1850, 1.4, "neutro", "anda"), C(self.mae, x + 280, 1850, 1.4, "neutro", "anda")],
                  cam=(540, 1300, 1.1), t=t, ambiente=lambda m, tt: amb.vagalumes(m, tt, 16))
            return f

        @beat(103.00)
        def b_limpam(t, d, T):
            return S(self.escr, [C(self.narr, 300, 1850, 1.5, "feliz", "bate"), C(self.mae, 780, 1850, 1.5, "feliz", "bate2")],
                     cam=(540, 1250, 1.1), t=t)

        @beat(105.16)
        def b_louca(t, d, T):
            return S(self.coz, [C(self.narr, 300, 1850, 1.5, "ri", "entrega"), C(self.mae, 780, 1850, 1.5, "ri", "entrega")],
                     cam=(540, 1250, 1.1), t=t)

        @beat(106.96)
        def b_hoje(t, d, T):
            niv = "NORMAL" if T > 109.9 else "FÁCIL"
            return S(self.tarde, [C(self.narr, 540, 1850, 1.5, "feliz", "idle", selo=niv)], cam=(540, 1250, 1.15), t=t,
                     fx=self.feliz if niv == "NORMAL" else None, ambiente=vida_dia)

        @beat(110.02)
        def b_normal_final(t, d, T):
            return self.perto(self.narr, self.tarde, "tarde", "feliz", "NORMAL", fx=self.feliz)

        @beat(111.44)
        def b_mae_final(t, d, T):
            return S(self.tarde, [C(self.mae, 540, 1850, 1.6, "feliz", "acena", selo="PESADELO")], cam=(540, 1250, 1.15), t=t,
                     ambiente=vida_dia)

        @beat(115.72)
        def b_cidade(t, d, T):
            k = ease_io(min(1, (T - 116.4) / 2.0))
            chars = [C(P[i], 120 + i * 170, 1850, 1.0, "surpreso", "aponta") for i in range(6)]
            f = S(self.tarde, chars + [C(self.mae, 540, 1850, 1.5, "feliz", "acena", selo=None)],
                  [lambda m: sl.selo_mundo(m, self.fc, "PESADELO", 540, 1850 - 735 * 1.5, 0.82 * 1.5 * (1 - 0.35 * k), T)],
                  (540, 1250, 1.0), t, ambiente=vida_dia)
            kf = max(0, (T - (self.dur_total - 1.8)) / 1.8)
            return Image.blend(f, Image.new("RGB", f.size, (0, 0, 0)), min(1, kf)) if kf > 0 else f

    def _carta(self, texto, k):
        p = Pincel(440, 520)
        p.ret((10, 10, 430, 510), (250, 246, 232), r=14, ow=7)
        img = p.pronto()
        d = ImageDraw.Draw(img)
        f = vc.fonte(self.fc, 54)
        d.text((220 - f.getlength(texto) / 2, 180), texto, font=f, fill=(214, 40, 50))
        d.text((60, 70), "Empresa " + ("A" if k == 0 else "B"), font=vc.fonte(self.fc, 34), fill=(90, 90, 100))
        return img.rotate(-6 if k == 0 else 5, expand=True, resample=Image.BICUBIC)


def ease_in_(x):
    return x * x


# --------------------------------------------------------------------------
def mixar(filme, narracao, saida):
    import som
    voz = vc.ler_wav_mono(narracao)
    dur = filme.dur_total
    ev = []
    for i, (c, _v) in enumerate(filme.cortes[1:]):
        ev.append(("whoosh" if i % 3 == 0 else "pop", c - 0.04, 0.2 if i % 3 == 0 else 0.18))
    ev += [("ding", 14.3, 0.5), ("hit", 7.4, 0.8), ("hit", 24.9, 0.8), ("riser", 43.0, 0.45), ("pagina", 46.0, 0.4),
           ("hit", 52.7, 0.9), ("hit", 53.8, 1.0), ("pagina", 57.3, 0.4), ("coracao", 69.4, 0.8), ("coracao", 70.4, 0.8),
           ("coracao", 71.4, 0.8), ("riser", 73.2, 0.5), ("hit", 74.9, 0.9), ("ding", 77.0, 0.4), ("ding", 109.9, 0.7),
           ("ding", 110.7, 0.5)]
    amb_ = [("cidade", 0.0, 42.0, 0.35), ("noite", 25.0, 38.0, 0.25), ("hospital", 60.0, 76.0, 0.4), ("cidade", 79.0, 100.0, 0.3),
            ("noite", 100.0, 103.0, 0.3), ("cidade", 106.0, dur - 2, 0.3)]
    picos = [(7.4, 0.55), (24.9, 0.7), (42.4, 0.6), (53.8, 0.95), (70.0, 0.9), (74.9, 1.0), (86.0, 0.7), (99.0, 0.6), (110.0, 0.9)]
    mix = som.mixar_v2(dur, voz, ev, amb_, picos, "triste", 0.2)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(som.SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def carregar_palavras(caminho):
    troca = {"tesar": "pesar", "Pesadelo.": "Pesadelo.", "notação.": "anotação.", "Selo": "Selo"}
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
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_o_selo.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    ap.add_argument("--de", type=float, default=None)
    ap.add_argument("--ate", type=float, default=None)
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeSelo(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.4, a.narracao)
    total = int(filme.dur_total * FPS)

    if a.testar:
        for ini, d, *_r in filme.planos:
            for k in (0.01, 0.5, 0.99):
                filme.frame(int((ini + d * k) * FPS))
        c10 = len([c for c, _ in filme.cortes if c < 10])
        print(f"todos os planos ok — {len(filme.planos)} cenas, {len(filme.cortes)} cortes; {c10} nos 10 s iniciais")
        return
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        ts = [c for c, _ in filme.cortes] + [filme.dur_total]
        for i, (x, y) in enumerate(zip(ts, ts[1:])):
            filme.frame(int((x + y) / 2 * FPS)).save(os.path.join(a.preview, f"take_{i:03d}.png"))
        print("preview em", a.preview, len(ts) - 1, "takes")
        return

    tmp = tempfile.mkdtemp(prefix="selo_")
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
    import render
    render.renderizar(filme, n0, n1, proc.stdin, progresso=True, total=total)
    proc.stdin.close()
    proc.wait()
    print("✔ vídeo salvo em", a.saida)


if __name__ == "__main__":
    main()
