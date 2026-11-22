#!/usr/bin/env python3
"""Cenários e props de "O Selo": fachadas (faculdade, cartório), quarto, escada, certidão, livro de regras,
selos de dificuldade desenhados no mundo, relógio digital, pesos e partículas."""
import math

from PIL import Image, ImageDraw

import video_carta as vc
from gerar_video import WW, WH, Pincel, gradiente, brilho

_C = {}

NIVEIS = {"FÁCIL": (84, 200, 120), "NORMAL": (70, 150, 240), "DIFÍCIL": (255, 160, 50), "PESADELO": (230, 60, 150)}


def selo_mundo(m, fc, texto, x, y, escala=1.0, pulso=0.0):
    """Selo de dificuldade flutuando (desenhado em coordenadas do mundo)."""
    cor = NIVEIS.get(texto, (255, 214, 40))
    tam = max(22, int(40 * escala))
    fnt = vc.fonte(fc, tam)
    w = int(fnt.getlength(texto) + tam * 2.0)
    h = int(tam * 1.8)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=(26, 22, 56, 238), outline=cor + (255,), width=max(3, tam // 8))
    d.ellipse((tam * 0.4, h / 2 - tam * 0.34, tam * 1.08, h / 2 + tam * 0.34), fill=cor + (255,))
    d.text((tam * 1.35, h / 2 - tam * 0.66), texto, font=fnt, fill=(255, 255, 255))
    s = 1 + 0.05 * math.sin(pulso * 4)
    if s != 1:
        img = img.resize((int(w * s), int(h * s)), Image.BICUBIC)
    yy = y + 5 * math.sin(pulso * 2.4)
    m.alpha_composite(brilho((int(w * 1.6), int(h * 2.4)), cor, int(w * 0.7), 0.35),
                      (int(x - w * 0.8), int(yy - h * 1.2)))
    m.alpha_composite(img, (int(x - img.width / 2), int(yy - img.height / 2)))


def fachada(fc, nome, cor=(214, 196, 168), faixa=(60, 70, 130), hora="dia"):
    k = ("fach", nome, hora)
    if k in _C:
        return _C[k]
    topo, baixo = ((140, 200, 245), (222, 238, 250)) if hora == "dia" else ((250, 176, 120), (255, 224, 176))
    base = gradiente(WW, WH, topo, baixo)
    p = Pincel(WW, WH)
    p.ret((-20, 1480, WW + 20, WH + 20), (196, 190, 180), r=0, ow=0)
    p.ret((80, 560, 1000, 1480), cor, r=8)
    p.poli([(60, 570), (540, 360), (1020, 570)], _tom(cor, 0.82))
    for x in (150, 330, 510, 690, 870):
        p.ret((x - 24, 640, x + 24, 1400), _tom(cor, 1.08), r=6)
    p.ret((380, 1100, 700, 1480), (110, 76, 56), r=10, ow=8)
    p.linha([(540, 1100), (540, 1480)], w=6)
    for y in range(1400, 1480, 28):
        p.ret((300, y, 780, y + 28), (226, 220, 210), r=0, ow=4)
    p.ret((220, 480, 860, 560), faixa, r=8, ow=6)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 50)
    d.text((540 - f.getlength(nome) / 2, 488), nome, font=f, fill=(255, 255, 255))
    _C[k] = base
    return base


def _tom(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def quarto_simples(fc, inverno=False, noite=True):
    k = ("quarto", inverno, noite)
    if k in _C:
        return _C[k]
    base = gradiente(WW, WH, (74, 70, 110), (46, 42, 78)) if noite else gradiente(WW, WH, (236, 214, 176), (214, 192, 156))
    p = Pincel(WW, WH)
    p.ret((-20, 1500, WW + 20, WH + 20), (120, 90, 72), r=0, ow=0)
    p.ret((620, 260, 980, 700), (24, 30, 60) if noite else (176, 216, 240), r=10, ow=10)
    p.linha([(800, 260), (800, 700)], w=8)
    if inverno:
        for i in range(30):
            x, y = 640 + (i * 37) % 320, 280 + (i * 53) % 400
            p.elipse((x - 5, y - 5, x + 5, y + 5), (245, 248, 255), ow=0)
    p.ret((60, 900, 580, 1180), (200, 180, 150), r=6)                           # criado-mudo
    p.ret((300, 700, 360, 900), (250, 230, 150), r=8)                            # abajur
    base.alpha_composite(p.pronto())
    if noite:
        base.alpha_composite(brilho((700, 700), (255, 220, 150), 300, 0.4), (-20, 420))
    _C[k] = base
    return base


def escada(fc):
    k = "escada"
    if k in _C:
        return _C[k]
    base = gradiente(WW, WH, (226, 210, 184), (206, 188, 160))
    p = Pincel(WW, WH)
    p.ret((-20, 1500, WW + 20, WH + 20), (150, 112, 80), r=0, ow=0)
    for i in range(8):
        p.ret((120 + i * 110, 1500 - (i + 1) * 90, 1000, 1500 - i * 90), (190, 150, 110), r=0)
        p.ret((120 + i * 110, 1500 - (i + 1) * 90, 1000, 1500 - (i + 1) * 90 + 16), (150, 112, 80), r=0, ow=0)
    p.linha([(100, 1480), (1000, 640)], fill=(86, 66, 52), w=18)
    base.alpha_composite(p.pronto())
    _C[k] = base
    return base


def certidao(fc, nivel=0, anotacao_ate=0.0, carimbo=0.0, w=860):
    """Certidão de nascimento: cabeçalho, linhas, anotação à caneta que 'escreve' aos poucos e carimbo vermelho."""
    p = Pincel(700, 940)
    p.ret((10, 10, 690, 930), (248, 240, 218), r=14, ow=8)
    p.ret((40, 40, 660, 130), (200, 70, 70), r=8, ow=0)
    for i in range(7):
        p.linha([(70, 190 + i * 52), (630, 190 + i * 52)], fill=(190, 180, 160), w=4)
    p.elipse((540, 150, 640, 250), (214, 170, 70), ow=6)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f1, f2, f3 = vc.fonte(fc, 36), vc.fonte(fc, 26), vc.fonte(fc, 34)
    d.text((350 - f1.getlength("CERTIDÃO DE NASCIMENTO") / 2, 66), "CERTIDÃO DE NASCIMENTO", font=f1, fill=(255, 255, 255))
    for i, t in enumerate(("NOME: ____________________", "DATA: ___/___/______", "MÃE: _______________________",
                           "SELO: ____________________")):
        d.text((70, 176 + i * 52), t, font=f2, fill=(100, 96, 90))
    linhas = ("Selo de nascimento: PESADELO", "Transferido para a mãe,", "às 4h12.")
    total = sum(len(s) for s in linhas)
    n = int(total * max(0, min(1, anotacao_ate)))
    y = 470
    for s in linhas:
        k = min(len(s), n)
        d.text((70, y), s[:k], font=f3, fill=(36, 70, 190))
        n -= k
        y += 58
        if n <= 0:
            break
    if carimbo > 0:
        sc = 1 + 0.5 * (1 - min(1, carimbo))
        st = Image.new("RGBA", (460, 150), (0, 0, 0, 0))
        ds = ImageDraw.Draw(st)
        ds.rounded_rectangle((4, 4, 455, 145), radius=18, outline=(214, 40, 50, 235), width=10)
        fs = vc.fonte(fc, 46)
        ds.text((230 - fs.getlength("TRANSFERIDO") / 2, 22), "TRANSFERIDO", font=fs, fill=(214, 40, 50, 235))
        ds.text((230 - fs.getlength("4h12") / 2, 78), "4h12", font=fs, fill=(214, 40, 50, 235))
        st = st.rotate(-10, expand=True, resample=Image.BICUBIC)
        st = st.resize((int(st.width * sc), int(st.height * sc)), Image.BICUBIC)
        img.alpha_composite(st, (330 - st.width // 2, 780 - st.height // 2))
    return img if w == 700 else img.resize((w, int(940 * w / 700)), Image.BICUBIC)


def livro_regras(fc, w=820):
    p = Pincel(800, 560)
    p.ret((10, 40, 400, 540), (240, 232, 208), r=10, ow=8)
    p.ret((400, 40, 790, 540), (246, 238, 214), r=10, ow=8)
    p.ret((384, 30, 416, 550), (120, 70, 50), r=4, ow=0)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f1, f2 = vc.fonte(fc, 30), vc.fonte(fc, 24)
    d.text((410 - f1.getlength("LEI DOS SELOS") / 2 + 190, 74), "LEI DOS SELOS", font=f1, fill=(120, 40, 40))
    for i in range(7):
        d.line((430, 150 + i * 44, 770, 150 + i * 44), fill=(190, 180, 160), width=3)
    d.rounded_rectangle((424, 230, 776, 330), radius=8, fill=(255, 236, 130, 200))
    d.text((434, 240), "A mãe pode, no primeiro", font=f2, fill=(60, 50, 40))
    d.text((434, 270), "abraço, puxar o selo", font=f2, fill=(60, 50, 40))
    d.text((434, 300), "do filho para ela.", font=f2, fill=(60, 50, 40))
    for i in range(7):
        d.line((30, 100 + i * 52, 380, 100 + i * 52), fill=(200, 190, 170), width=3)
    return img if w == 800 else img.resize((w, int(560 * w / 800)), Image.BICUBIC)


def saco_peso(w=300, tam=1.0):
    k = ("peso", w, round(tam, 1))
    if k not in _C:
        p = Pincel(300, 300)
        r = 60 + 50 * tam
        p.ret((150 - r, 150 - r * 0.6 + 40, 150 + r, 150 + r * 0.9 + 40), (90, 94, 110), r=int(r * 0.4))
        p.ret((150 - r * 0.5, 150 - r * 0.9 + 40, 150 + r * 0.5, 150 - r * 0.45 + 40), (90, 94, 110), r=14)
        img = p.pronto()
        _C[k] = img.resize((w, w), Image.BICUBIC)
    return _C[k]


def relogio_digital(fc, hora="04:00", w=520, cor=(255, 80, 80)):
    p = Pincel(520, 240)
    p.ret((10, 10, 510, 230), (24, 24, 34), r=30, ow=8)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 150)
    d.text((260 - f.getlength(hora) / 2, 28), hora, font=f, fill=cor)
    return img if w == 520 else img.resize((w, int(240 * w / 520)), Image.BICUBIC)
