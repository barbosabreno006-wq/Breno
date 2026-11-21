#!/usr/bin/env python3
"""
"O Caderno" — tudo que o Davi desenha ganha vida… até ele descobrir que ele também é um desenho.

Efeitos: rascunho a lápis que ganha cor (o desenho "nasce"), página pautada, coisas gigantes caindo
do céu, céu de papel com linhas azuis, cadeia de Davis/cadernos (zoom infinito), avião de papel,
margem vermelha, rosto iluminado pela tela, contorno do personagem brilhando e o dedão gigante
tentando arrastar o vídeo.

    python3 animacao/video_caderno.py --narracao narr.wav --transcricao transcricao.json --fonte Poppins.ttf
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
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_video as g  # noqa: E402
import video_carta as vc  # noqa: E402
import video_corsa as vco  # noqa: E402
import video_estatua as ve  # noqa: E402
import video_controle as vct  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, OUTLINE, Pincel, gradiente, brilho,
                         ease_out, ease_io, camera, particulas, texto_pop)

random.seed(404)

DAVI = dict(pele=(222, 170, 128), cabelo=(70, 45, 30), camisa=(220, 60, 60), calca=(50, 70, 120),
            sapato=(240, 240, 240), tipo="menino")
PAI = dict(pele=(214, 160, 120), cabelo=(50, 38, 30), camisa=(90, 120, 160), calca=(60, 65, 80),
           sapato=(60, 50, 45), tipo="pai")
VOCE = dict(pele=(214, 165, 125), cabelo=(40, 30, 25), camisa=(60, 60, 70), calca=(40, 40, 50),
            sapato=(40, 40, 40), tipo="pai", bigode=False)
vc.DESTAQUE_VERMELHO = set()
PAPEL = (250, 248, 238)
AZUL_PAUTA = (170, 200, 235)
MARGEM = (230, 80, 80)


# --------------------------------------------------------------------------
# Efeito "rascunho": sprite vira desenho a lápis e vai ganhando cor
# --------------------------------------------------------------------------
_CACHE = {}


def rascunho(spr):
    k = ("r", id(spr))
    if k not in _CACHE:
        a = spr.getchannel("A")
        cinza = ImageOps.grayscale(spr.convert("RGB"))
        bordas = cinza.filter(ImageFilter.FIND_EDGES)
        bordas = ImageOps.autocontrast(bordas)
        tra = Image.composite(Image.new("L", spr.size, 0), Image.new("L", spr.size, 255),
                              bordas.point(lambda v: 255 if v > 40 else 0))
        rgb = Image.merge("RGB", (tra, tra, tra))
        rgb = ImageEnhance.Brightness(rgb).enhance(0.55)
        out = rgb.convert("RGBA")
        msk = Image.composite(bordas.point(lambda v: 230 if v > 40 else 0), Image.new("L", spr.size, 0), a)
        out.putalpha(msk)
        _CACHE[k] = out
    return _CACHE[k]


def nasce(m, spr, cx, by, e, k, rot=0.0):
    """k=0: só o rascunho a lápis; k=1: desenho colorido vivo."""
    if k < 1:
        g.colar(m, rascunho(spr), cx, by, e, rot=rot)
    if k > 0:
        g.colar(m, spr, cx, by, e, rot=rot, alpha=min(1, k))


def pagina(w=WW, h=WH, margem=True, cor=PAPEL):
    k = ("pag", w, h, margem)
    if k in _CACHE:
        return _CACHE[k].copy()
    base = Image.new("RGBA", (w, h), cor + (255,))
    d = ImageDraw.Draw(base)
    for y in range(120, h, 70):
        d.line((0, y, w, y), fill=AZUL_PAUTA, width=4)
    if margem:
        d.line((140, 0, 140, h), fill=MARGEM, width=5)
    _CACHE[k] = base
    return base.copy()


def lapis(w=560):
    p = Pincel(w, 120)
    p.ret((80, 30, w - 20, 90), (250, 200, 60), r=10)
    p.ret((w - 90, 30, w - 20, 90), (240, 150, 160), r=10)
    p.poli([(80, 30), (80, 90), (10, 60)], (230, 200, 160))
    p.poli([(32, 48), (32, 72), (10, 60)], (60, 60, 60), ow=0)
    return p.pronto()


def borracha(w=260):
    p = Pincel(w, w * 0.55)
    p.ret((10, 10, w - 10, w * 0.5), (240, 150, 160), r=20)
    p.ret((w * 0.55, 10, w - 10, w * 0.5), (90, 140, 220), r=20)
    return p.pronto()


def cachorro(w=420):
    p = Pincel(w, w * 0.9)
    p.elipse((70, 160, 340, 330), (220, 170, 110))
    p.elipse((250, 60, 400, 210), (220, 170, 110))
    p.elipse((240, 70, 290, 170), (150, 100, 60))
    p.elipse((330, 110, 350, 130), OUTLINE, ow=0)
    p.elipse((380, 150, 404, 172), OUTLINE, ow=0)
    for x in (110, 170, 250, 300):
        p.capsula((x, 300), (x, 370), 30, (220, 170, 110))
    p.linha([(70, 220), (20, 160)], fill=(220, 170, 110), w=26)
    return p.pronto()


def sol(w=420):
    p = Pincel(w, w)
    c = w / 2
    for a in range(0, 360, 30):
        r = math.radians(a)
        p.linha([(c + 120 * math.cos(r), c + 120 * math.sin(r)), (c + 190 * math.cos(r), c + 190 * math.sin(r))],
                fill=(250, 190, 40), w=16)
    p.elipse((c - 110, c - 110, c + 110, c + 110), (255, 210, 60))
    return p.pronto()


def pizza(w=600):
    return __import__("video_corsa").pizza(8, w)


def escada(h=1600):
    p = Pincel(260, h)
    p.ret((20, 0, 50, h), (190, 140, 80), r=8)
    p.ret((210, 0, 240, h), (190, 140, 80), r=8)
    for y in range(60, h, 110):
        p.ret((40, y, 220, y + 22), (190, 140, 80), r=6)
    return p.pronto()


def aviao(w=420):
    p = Pincel(w, w * 0.6)
    p.poli([(10, 120), (w - 10, 20), (180, 200)], (250, 250, 250))
    p.poli([(180, 200), (w - 10, 20), (220, 250)], (230, 230, 235))
    return p.pronto()


def dedao(w=700):
    p = Pincel(w, w * 1.6)
    p.ret((120, 140, w - 120, w * 1.6), (226, 178, 138), r=240)
    p.ret((200, 170, w - 200, 520), (245, 215, 195), r=150, ow=0)
    return p.pronto()


def celular_moldura(w=OUT_W, h=OUT_H):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 20, w - 20, h - 20), radius=70, outline=(25, 25, 32), width=40)
    d.rounded_rectangle((w / 2 - 90, 34, w / 2 + 90, 64), radius=14, fill=(25, 25, 32))
    for i, y in enumerate((h * 0.55, h * 0.63, h * 0.71)):      # ícones laterais
        d.ellipse((w - 110, y, w - 50, y + 60), fill=(255, 255, 255, 200))
    return img


def quarto(noite=False):
    base = gradiente(WW, WH, (40, 45, 80) if noite else (240, 225, 200), (60, 60, 95) if noite else (225, 210, 185))
    p = Pincel(WW, WH)
    p.ret((640, 260, 960, 620), (20, 25, 50) if noite else (170, 215, 240), r=10, ow=10)
    p.ret((-20, 1400, WW + 20, WH + 20), (90, 75, 80) if noite else (170, 130, 100), r=0)
    p.ret((60, 1250, 1020, 1330), (150, 100, 70), r=10)
    p.ret((100, 1330, 140, 1700), (130, 85, 60), r=10)
    p.ret((940, 1330, 980, 1700), (130, 85, 60), r=10)
    base.alpha_composite(p.pronto())
    if noite:
        base.alpha_composite(brilho((900, 900), (255, 220, 150), 450, 0.4), (90, 700))
    return base


def quintal(fc):
    base = gradiente(WW, WH, (150, 200, 240), (225, 238, 250))
    p = Pincel(WW, WH)
    vc.nuvem(p, 120, 260, 0.8)
    p.ret((60, 700, 1020, 1400), (240, 210, 150), r=6)
    p.poli([(30, 710), (540, 420), (1050, 710)], (170, 80, 70))
    p.ret((-20, 1400, WW + 20, WH + 20), (120, 180, 100), r=0)
    for x in range(0, WW, 60):
        p.ret((x, 1300, x + 30, 1420), (250, 250, 250), r=4)
    base.alpha_composite(p.pronto())
    return base


# --------------------------------------------------------------------------
# Filme
# --------------------------------------------------------------------------
class FilmeCaderno(ve.FilmeEstatua):
    def __init__(self, palavras, fc, dur_total, narracao):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.davi, self.pai, self.voce = P_(DAVI), P_(PAI), P_(VOCE)
        self.blur = {}
        self.quarto, self.quarto_n = quarto(), quarto(True)
        self.quintal = quintal(fc)
        self.lap, self.borr = lapis(), borracha()
        self.cao, self.sol_img, self.pizza_img = cachorro(), sol(), pizza()
        self.esc, self.av, self.ded = escada(), aviao(), dedao()
        self.moeda = vco.moeda()
        self.carro = vco.Carro((60, 120, 200))
        self.moldura = celular_moldura()
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.FALA_PAI = [(30.50, 31.0)]
        self.FALA_DAVI = [(31.30, 34.7), (85.16, 88.0), (88.48, 93.6), (94.88, 102.9)]
        self.TREMORES = [(21.34, 12), (27.26, 14), (30.56, 6), (88.48, 5)]

        P = [
            (0.00, self.p_hook, "", "corte"),
            (2.76, self.p_cachorro, "", "corte"),
            (5.42, self.p_sol, "", "corte"),
            (9.04, self.p_menino, "", "whip"),
            (13.26, self.p_davizinho, "", "corte"),
            (18.10, self.p_pizza_desenho, "", "corte"),
            (20.06, self.p_pizza_cai, "", "whip"),
            (25.68, self.p_real, "", "corte"),
            (27.04, self.p_moeda, "", "whip"),
            (30.56, self.p_pai, "", "corte"),
            (34.92, self.p_entendi, "", "zoom"),
            (40.32, self.p_quem, "", "corte"),
            (41.10, self.p_escada, "", "corte"),
            (45.36, self.p_sobe, "", "whip"),
            (50.14, self.p_caderno_gigante, "", "corte"),
            (54.54, self.p_outros, "", "zoom"),
            (60.00, self.p_50, "", "corte"),
            (63.04, self.p_aviao, "", "whip"),
            (66.86, self.p_margem, "", "corte"),
            (71.66, self.p_outro_lado, "", "dissolve"),
            (75.44, self.p_rosto, "", "dissolve"),
            (78.68, self.p_o_seu, "", "corte"),
            (79.38, self.p_desenho, "", "corte"),
            (82.54, self.p_linha, "", "corte"),
            (85.16, self.p_video, "", "zoom"),
            (88.48, self.p_dedao, "", "corte"),
            (94.10, self.p_ufa, "", "corte"),
            (95.82, self.p_pergunta, "quente", "corte"),
            (99.44, self.p_final, "", "dissolve"),
        ]
        self.planos = []
        for i, (ini, fn, clima, tr) in enumerate(P):
            fim = P[i + 1][0] if i + 1 < len(P) else dur_total
            self.planos.append((ini, fim - ini, fn, clima, tr))
        self.p_preto = None

    # ---------- utilidades ----------
    def cam(self, m, cx, cy, z):
        dx = dy = 0.0
        for tg, a in self.TREMORES:
            dt = self.T - tg
            if 0 <= dt < 0.5:
                k = a * (1 - dt / 0.5)
                dx, dy = k * math.sin(self.T * 90), k * math.cos(self.T * 70)
        return camera(m, cx + dx, cy + dy, z)

    def lapis_desenhando(self, m, t, x, y, amp=60):
        self.segura(m, self.lap, x + amp * math.sin(t * 9), y + amp * 0.5 * math.cos(t * 7), 380, rot=35)

    def caderno_mesa(self, m, x0=140, y0=900, w=800, h=560):
        pg = pagina(w, h).resize((w, h))
        p = Pincel(w + 40, h + 40)
        p.ret((0, 0, w + 40, h + 40), (60, 60, 70), r=20, ow=0)
        m.alpha_composite(p.pronto(), (x0 - 20, y0 - 20))
        m.alpha_composite(pg, (x0, y0))

    # ------------------------- planos -------------------------
    def p_hook(self, t, d):
        m = self.quarto.copy()
        self.caderno_mesa(m, 140, 1000, 800, 300)
        self.davi(m, t, 540, 1260, 1.0, expr="feliz", pose="entrega")
        self.lapis_desenhando(m, t, 640, 1100)
        f = self.cam(m, 540, 1150, 1.15)
        particulas(f, t, 30, (255, 230, 150), semente=1)
        return f

    def pagina_close(self, conteudo, t, k, cx=540, by=1300, e=1.0, rot=0.0, extra=None):
        m = pagina()
        nasce(m, conteudo, cx, by, e, k, rot)
        if extra:
            extra(m)
        return m

    def p_cachorro(self, t, d):
        k = ease_io(min(1, max(0, t - 0.4) / 0.8))
        m = self.pagina_close(self.cao, t, k, 540, 1250 + (20 * math.sin(t * 12) if k >= 1 else 0), 1.4)
        if k >= 1 and int(t * 4) % 2:      # lambida (língua)
            p = Pincel(WW, WH)
            p.elipse((820, 1050, 900, 1130), (240, 100, 120), ow=4)
            m.alpha_composite(p.pronto())
        f = self.cam(m, 540, 1000, 1.05)
        if k < 1:
            self.segura_tela(f, self.lap, OUT_W * 0.7, OUT_H * 0.4 + 30 * math.sin(t * 8), 260, t)
        return f

    def segura_tela(self, f, img, x, y, w, t, rot=35):
        o = img.resize((int(w), int(img.height * w / img.width)), Image.BICUBIC).rotate(rot, expand=True)
        f.paste(o, (int(x - o.width / 2), int(y - o.height / 2)), o)

    def p_sol(self, t, d):
        k = ease_io(min(1, t / 0.8))
        m = self.pagina_close(self.sol_img, t, k, 540, 1200, 1.6, rot=t * 20)
        if k >= 1:
            m.alpha_composite(brilho((1080, 1080), (255, 160, 60), 540, 0.5 + 0.3 * math.sin(t * 6)), (0, 400))
        f = self.cam(m, 540, 950, 1.05)
        dr = ImageDraw.Draw(f, "RGBA")
        if t > 1.5:                        # fumaça
            for i in range(6):
                tt = (t * 1.2 + i * 0.2) % 1.0
                x = OUT_W * (0.3 + 0.08 * i)
                y = OUT_H * (0.7 - tt * 0.5)
                r = 20 + tt * 50
                dr.ellipse((x - r, y - r, x + r, y + r), fill=(120, 120, 120, int(150 * (1 - tt))))
        if t > 2.8:                        # vira a página
            kk = ease_io(min(1, (t - 2.8) / 0.6))
            f2 = pagina().crop((0, 0, int(OUT_W * 1.5 * kk) + 1, WH)).resize((int(OUT_W * kk) + 1, OUT_H))
            f.paste(f2.convert("RGB"), (OUT_W - f2.width, 0))
        return f

    def p_menino(self, t, d):
        k = ease_io(min(1, max(0, t - 1.2) / 1.2))
        spr = self.davi.spr("feliz", "acena" if k >= 1 and int(t * 2) % 2 else "idle")
        m = self.pagina_close(spr, t, k, 540, 1400, 1.2)
        f = self.cam(m, 540, 1000, 1.05)
        if k < 1:
            self.segura_tela(f, self.lap, OUT_W * 0.65, OUT_H * 0.5 + 60 * math.sin(t * 8), 280, t)
        if self.T > 12.32:
            texto_pop(f, "DAVIZINHO", self.fc, self.T - 12.32, OUT_W / 2, OUT_H * 0.14, 80, (220, 60, 60))
        return f

    def p_davizinho(self, t, d):
        m = pagina()
        g.colar(m, self.davi.spr("feliz", "entrega"), 360, 1400, 1.0)
        mini = pagina(300, 220)
        m.alpha_composite(mini, (520, 1050))
        self.segura(m, self.lap, 600 + 30 * math.sin(t * 9), 1080, 120, rot=35)
        if t > 2.5:
            g.colar(m, rascunho(self.davi.spr("feliz", "idle")), 690, 1250, 0.25)
        return self.cam(m, 540, 1150, 1.2 + 0.15 * ease_io(t / d))

    def p_pizza_desenho(self, t, d):
        m = pagina()
        g.colar(m, self.davi.spr("ri" if t > 1 else "feliz", "idle"), 360, 1500, 1.0)
        k = ease_io(min(1, t / 1.2))
        nasce(m, self.pizza_img, 720, 1450, 0.5, k)
        return self.cam(m, 540, 1150, 1.1)

    def p_pizza_cai(self, t, d):
        m = self.quintal.copy()
        tc = 21.34 - 20.06
        y = -400 + 1900 * min(1, t / tc) if t < tc else 1500
        sq = 1.0 if t < tc else 1 + 0.25 * math.exp(-(t - tc) * 6) * math.cos((t - tc) * 30)
        pz = self.pizza_img.resize((int(900 * sq), int(900 / sq * 0.45)))
        if t < tc:
            pz = self.pizza_img.resize((900, 900))
        m.alpha_composite(pz, (int(540 - pz.width / 2), int(y - pz.height / 2)))
        self.davi(m, t, 180, 1780, 1.0, expr="surpreso" if t > tc else "neutro", pose="acena" if t > tc else "idle")
        f = self.cam(m, 540, 1250, 1.05)
        if t > tc:
            texto_pop(f, "PUM!", self.fc, t - tc, OUT_W / 2, OUT_H * 0.2, 130, (255, 214, 40))
        return f

    def p_real(self, t, d):
        m = pagina()
        g.colar(m, self.davi.spr("feliz", "idle"), 360, 1500, 1.0)
        nasce(m, self.moeda, 720, 1350, 3.0, ease_io(min(1, t / 0.9)))
        return self.cam(m, 540, 1150, 1.1)

    def p_moeda(self, t, d):
        m = self.quintal.copy()
        tc = 27.26 - 27.04 + 0.3
        amassa = t > tc
        self.carro.desenhar(m, 600, 1620, escala=1.0, pulo=0)
        if amassa:
            p = Pincel(WW, WH)
            p.poli([(250, 1320), (950, 1320), (900, 1400), (300, 1400)], (60, 120, 200))
            m.alpha_composite(p.pronto())
        y = -300 + 1500 * min(1, t / tc)
        mo = self.moeda.resize((620, 620))
        m.alpha_composite(mo, (290, int(min(y, 1000))))
        d_ = ImageDraw.Draw(m)
        f_ = vc.fonte(self.fc, 200)
        d_.text((600 - f_.getlength("1") / 2, min(y, 1000) + 170), "1", font=f_, fill=(150, 110, 30))
        f = self.cam(m, 540, 1250, 1.05)
        if amassa:
            texto_pop(f, "CRASH!", self.fc, t - tc, OUT_W / 2, OUT_H * 0.15, 110, (255, 255, 255))
        return f

    def p_pai(self, t, d):
        m = self.quintal.copy()
        self.pai(m, t, 330, 1780, 1.25, expr="bravo", pose="aponta", fala=self.FALA_PAI)
        self.davi(m, t, 770, 1800, 1.05, expr="surpreso", fala=self.FALA_DAVI)
        return self.cam(m, 540, 1250, 1.12)

    def p_entendi(self, t, d):
        m = self.fundo_blur("quarto", self.quarto)
        self.davi(m, t, 540, 2350, 2.5, expr="surpreso" if t > 1.0 else "neutro")
        f = self.cam(m, 540, 950, 1.05 + 0.1 * ease_io(t / d))
        if t > 2.2:                          # sombra de um lápis gigante lá de cima
            kk = ease_out(min(1, (t - 2.2) / 1.0))
            sh = self.lap.resize((1300, 280)).rotate(60, expand=True)
            sh = ImageEnhance.Brightness(sh).enhance(0.2)
            sh.putalpha(sh.getchannel("A").point(lambda v: int(v * 0.5)))
            f.paste(sh, (int(OUT_W * 0.2), int(-sh.height + 450 * kk)), sh)
        return f

    def p_quem(self, t, d):
        m = self.fundo_blur("quarto", self.quarto)
        self.davi(m, t, 540, 2350, 2.5, expr="surpreso")
        f = self.cam(m, 540, 950, 1.1)
        texto_pop(f, "QUEM?", self.fc, t, OUT_W / 2, OUT_H * 0.15, 120, (255, 214, 40))
        return f

    def p_escada(self, t, d):
        m = self.quintal.copy()
        k = ease_out(min(1, max(0, t - 1.6) / 1.2))
        m.alpha_composite(self.esc.resize((220, 1400)), (700, int(-1400 + 1400 * k + 300)))
        self.davi(m, t, 420, 1780, 1.1, expr="surpreso" if k > 0 else "feliz", pose="aponta" if k > 0 else "entrega")
        if k <= 0:
            hx, hy = self.mao(420, 1780, 1.1, t)
            self.segura(m, self.lap, hx + 60, hy - 20, 200, rot=35)
        return self.cam(m, 540, 1150, 1.05)

    def ceu_papel(self, t, off=0):
        m = gradiente(WW, WH, (235, 240, 250), (215, 225, 245))
        d = ImageDraw.Draw(m)
        for y in range(-200, WH + 200, 120):
            yy = (y + off) % (WH + 240) - 120
            d.line((0, yy, WW, yy), fill=AZUL_PAUTA, width=6)
        return m

    def p_sobe(self, t, d):
        m = self.ceu_papel(t, off=t * 300)
        m.alpha_composite(self.esc.resize((260, 2400)), (410, -200))
        passo = int(t * 3) % 2
        self.davi(m, t, 540, 1300 + 30 * passo, 1.0, expr="feliz", pose="acena" if passo else "idle")
        return self.cam(m, 540, 1000, 1.05)

    def p_caderno_gigante(self, t, d):
        m = self.ceu_papel(t)
        gig = self.davi.spr("neutro", "entrega").resize((1800, 3388))
        m.alpha_composite(gig, (-900, -900))
        self.segura(m, self.lap.resize((1400, 300)), 700 + 60 * math.sin(t * 6), 900, 1400, rot=30)
        self.davi(m, t, 860, 1820, 0.35, expr="surpreso")
        return self.cam(m, 540, 1100, 1.0)

    def p_outros(self, t, d):
        # zoom infinito: cada quadro contém o Davi desenhando um caderno onde há outro Davi
        base = pagina()
        k = (t / d) * 3 % 1.0
        esc = 1.0 + 1.8 * k
        img = Image.new("RGBA", (WW, WH))
        img.alpha_composite(base)
        for i in range(5):
            e = (0.9 ** 0) * (0.45 ** i) * esc
            if e < 0.02:
                continue
            g.colar(img, self.davi.spr("neutro", "entrega"), 540, 1700 - 400 * (1 - 0.45 ** i), 1.6 * e)
        f = camera(img, 540, 1100, 1.0 + 0.4 * k)
        texto_pop(f, "E OUTRO… E OUTRO…", self.fc, t, OUT_W / 2, OUT_H * 0.12, 54, (40, 60, 140))
        return f

    def p_50(self, t, d):
        m = self.ceu_papel(t)
        m.alpha_composite(self.esc.resize((260, 1400)), (410, 900))
        self.davi(m, t, 540, 960, 1.0, expr="surpreso", pose="acena")
        f = self.cam(m, 540, 1000, 1.05)
        self.painel(f, "CADERNO", "50", t, cor=(40, 60, 140))
        return f

    def p_aviao(self, t, d):
        m = self.ceu_papel(t, off=-t * 600)
        y = 1000 + 60 * math.sin(t * 3)
        self.segura(m, self.av, 540, y, 520, rot=6 * math.sin(t * 3))
        self.davi(m, t, 520, y - 40, 0.55, expr="ri")
        f = self.cam(m, 540, 1000, 1.05)
        dr = ImageDraw.Draw(f)
        rng = random.Random(int(t * 10))
        for _ in range(8):
            yy, x = rng.uniform(200, 1100), rng.uniform(0, OUT_W)
            dr.line((x, yy, x + rng.uniform(80, 200), yy), fill=(140, 160, 200), width=4)
        return f

    def p_margem(self, t, d):
        m = self.ceu_papel(t)
        d_ = ImageDraw.Draw(m)
        d_.rectangle((0, 300, WW, 330), fill=MARGEM)                 # margem vermelha (horizontal no topo)
        k = ease_io(min(1, max(0, t - 2.4) / 1.6))
        self.davi(m, t, 540, 1100 - 900 * k, 0.9, expr="surpreso", pose="anda1" if int(t * 3) % 2 else "anda2")
        f = self.cam(m, 540, 900 - 300 * k, 1.05)
        if self.T > 69.38:
            texto_pop(f, "A MARGEM", self.fc, self.T - 69.38, OUT_W / 2, OUT_H * 0.62, 80, MARGEM)
        return f

    def p_outro_lado(self, t, d):
        m = gradiente(WW, WH, (15, 18, 30), (5, 6, 12))
        self.davi(m, t, 540, 1800, 1.1, expr="surpreso")
        f = self.cam(m, 540, 1250, 1.1)
        T = self.T
        for i, (txt, ts) in enumerate((("SEM CADERNO", 73.0), ("SEM LÁPIS", 73.86), ("SEM DAVI", 74.80))):
            if T > ts:
                texto_pop(f, txt, self.fc, T - ts, OUT_W / 2, OUT_H * (0.12 + i * 0.07), 56, (200, 200, 220))
        return f

    def rosto(self, t, z=1.0):
        m = gradiente(WW, WH, (10, 12, 22), (5, 6, 12))
        m.alpha_composite(brilho((1400, 1400), (120, 170, 255), 700, 0.8), (-160, 200))
        spr = self.voce.spr("neutro", "idle")
        g.colar(m, spr, 540, 3600, 5.2)
        f = camera(m, 540, 1000, z)
        a = np.asarray(f, np.float32) * np.array([0.8, 0.9, 1.15])
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

    def p_rosto(self, t, d):
        return self.rosto(t, 1.0 + 0.1 * ease_io(t / d))

    def p_o_seu(self, t, d):
        f = self.rosto(t, 1.15)
        texto_pop(f, "O SEU", self.fc, t, OUT_W / 2, OUT_H * 0.82, 130, (255, 214, 40))
        return f

    def p_desenho(self, t, d):
        m = self.fundo_blur("pag", pagina())
        k = 0.5 + 0.5 * math.sin(t * 6)
        nasce(m, self.davi.spr("surpreso", "idle"), 540, 2350, 2.5, k)
        f = self.cam(m, 540, 950, 1.05)
        if self.T > 80.94:
            texto_pop(f, "EU ERA O DESENHO", self.fc, self.T - 80.94, OUT_W / 2, OUT_H * 0.12, 58, (220, 60, 60))
        return f

    def p_linha(self, t, d):
        m = self.fundo_blur("pag", pagina())
        spr = self.davi.spr("neutro", "aponta")
        brilho_contorno = rascunho(spr)
        g.colar(m, spr, 540, 1900, 1.8)
        glow = brilho_contorno.filter(ImageFilter.GaussianBlur(6))
        g.colar(m, glow, 540, 1900, 1.8)
        g.colar(m, glow, 540, 1900, 1.8)
        f = self.cam(m, 540, 1150, 1.1)
        texto_pop(f, "ESSA LINHA PRETA", self.fc, t, OUT_W / 2, OUT_H * 0.12, 60, (40, 40, 50))
        return f

    def video_cena(self, t, expr="feliz", fala=None):
        m = pagina()
        self.davi(m, t, 540, 1750, 1.3, expr=expr, fala=fala, pose="acena")
        f = self.cam(m, 540, 1150, 1.1)
        f2 = f.convert("RGBA")
        f2.alpha_composite(self.moldura)
        return f2.convert("RGB")

    def p_video(self, t, d):
        f = self.video_cena(t, "feliz", self.FALA_DAVI)
        texto_pop(f, "DENTRO DESSE VÍDEO", self.fc, t, OUT_W / 2, OUT_H * 0.12, 54, (40, 60, 140))
        return f

    def p_dedao(self, t, d):
        f = self.video_cena(t, "surpreso", self.FALA_DAVI)
        k = ease_io(min(1, t / 1.6))
        oscila = 40 * math.sin(t * 3) if t > 1.6 else 0
        de = self.ded.resize((560, 896))
        x = OUT_W * 0.55 + oscila - 60 * max(0, t - 3.5)
        y = OUT_H * (1.0 - 0.45 * k)
        f.paste(de, (int(x - de.width / 2), int(y)), de)
        return f

    def p_ufa(self, t, d):
        f = self.video_cena(t, "ri")
        k = ease_io(min(1, t / 0.8))
        de = self.ded.resize((560, 896))
        f.paste(de, (int(OUT_W * 0.55 - 280), int(OUT_H * (0.55 + 0.6 * k))), de)
        if t > 0.6:
            texto_pop(f, "UFA!", self.fc, t - 0.6, OUT_W / 2, OUT_H * 0.14, 110, (90, 220, 120))
        return f

    def p_pergunta(self, t, d):
        m = self.fundo_blur("pag", pagina())
        self.davi(m, t, 540, 2350, 2.5, expr="feliz", fala=self.FALA_DAVI)
        return self.cam(m, 540, 950, 1.05 + 0.08 * ease_io(t / d))

    def p_final(self, t, d):
        m = self.quarto_n.copy()
        self.caderno_mesa(m, 140, 1000, 800, 300)
        # um desenhinho no caderno vira os olhos pra você
        g.colar(m, rascunho(self.davi.spr("neutro", "idle")), 540, 1260, 0.38)
        if t > 2.0:
            g.colar(m, self.davi.spr("surpreso", "idle"), 540, 1260, 0.38, alpha=min(1, (t - 2.0) / 0.6))
        f = self.cam(m, 540, 1150, 1.1 + 0.5 * ease_io(t / d))
        if t > d - 0.6:
            f = ImageEnhance.Brightness(f).enhance(max(0, 1 - (t - (d - 0.6)) / 0.6))
        return f

    # ---------- montagem ----------
    def frame(self, n):
        t = n / FPS
        self.T = t
        g.CAM_T = t
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if t < ini + d or i == len(self.planos) - 1:
                tl = t - ini
                f = vc.gradear(fn(tl, d), clima)
                T_ = 0.2
                if i > 0 and tl < T_ and tr != "corte":
                    pi, pd, pfn, pcl, _ = self.planos[i - 1]
                    self.T = pi + pd - 0.001
                    prev = vc.gradear(pfn(pd - 0.001, pd), pcl)
                    self.T = t
                    x = tl / T_
                    if tr == "whip":
                        off = int(OUT_W * ease_io(x))
                        comp = Image.new("RGB", (OUT_W, OUT_H))
                        comp.paste(prev, (-off, 0))
                        comp.paste(f, (OUT_W - off, 0))
                        f = g.motion_blur_h(comp, 60 * math.sin(math.pi * x))
                    elif tr == "dissolve":
                        f = Image.blend(prev, f, ease_io(x))
                    elif tr == "zoom":
                        f = g.zoom_blur(Image.blend(prev, f, ease_io(x)), 0.35 * math.sin(math.pi * x))
                f = g.vinheta(f, 0.25)
                self.legenda(f, t)
                return f

    def eventos_sfx(self):
        ev = []
        for i, (ini, d, fn, clima, tr) in enumerate(self.planos):
            if i and tr in ("whoosh", "whip", "zoom"):
                ev.append(("whoosh", ini - 0.08))
            elif i and tr == "corte":
                ev.append(("pop", ini))
        return ev


def rabisco_sfx(dur=0.8):
    SR = g.SR
    rng = np.random.default_rng(9)
    x = rng.standard_normal(int(SR * dur))
    x = x - np.convolve(x, np.ones(30) / 30, "same")
    env = (np.abs(np.sin(np.linspace(0, dur * 22, len(x)))) ** 2)
    return x * env * 0.12


def mixar(filme, narracao, saida):
    SR = g.SR
    voz = vc.ler_wav_mono(narracao)
    n = int(filme.dur_total * SR)
    mix = np.zeros(n, np.float32)
    mix[:min(n, len(voz))] += voz[:n]
    mus = g.trilha(filme.dur_total)
    mus = mus / max(1e-6, np.abs(mus).max()) * 0.12
    tt = np.arange(len(mus)) / SR
    env = np.ones_like(tt)
    env[(tt > 71.5) & (tt < 79.4)] = 0.25                     # suspense antes de "O seu."
    mix[:len(mus)] += (mus * env)[:n]
    ev = filme.eventos_sfx()
    ev += [("rabisco", 0.2), ("rabisco", 3.1), ("rabisco", 9.9), ("rabisco", 18.2), ("rabisco", 25.7),
           ("rabisco", 41.3)]
    from video_sono import sfx as sfx_sono
    ev += [("impacto", 21.34), ("impacto", 27.56), ("brilho", 78.68), ("impacto", 88.6), ("brilho", 94.10)]
    for tipo, t0 in ev:
        if tipo == "rabisco":
            s = rabisco_sfx()
        elif tipo == "impacto":
            s = sfx_sono("impacto") * 0.6
        else:
            s = g.sfx(tipo) * (0.3 if tipo in ("whoosh", "pop") else 1.0)
        a = int(max(0, t0) * SR)
        b = min(n, a + len(s))
        mix[a:b] += s[: b - a]
    fade = int(SR * 0.8)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = mix / max(1.0, np.abs(mix).max() / 0.95)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def carregar_palavras(caminho):
    pal = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            pal.append(dict(w=w["w"], s=w["s"], e=w["e"]))
    out = []
    for i, w in enumerate(pal):
        if w["w"] == "o" and i + 1 < len(pal) and pal[i + 1]["w"] == "rabisco." and pal[i - 1]["w"] == "viro":
            continue
        out.append(dict(w={"50": "cinquenta"}.get(w["w"], w["w"]), s=w["s"], e=w["e"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_o_caderno.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeCaderno(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.2, a.narracao)
    total = int(filme.dur_total * FPS)

    if a.testar:
        for ini, d, *_r in filme.planos:
            for k in (0.01, 0.5, 0.99):
                filme.frame(int((ini + d * k) * FPS))
        print("todos os planos ok")
        return
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        for i, (ini, d, *_r) in enumerate(filme.planos):
            filme.frame(int((ini + d * 0.6) * FPS)).save(os.path.join(a.preview, f"plano_{i:02d}.png"))
        print("preview em", a.preview)
        return

    tmp = tempfile.mkdtemp(prefix="caderno_")
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
