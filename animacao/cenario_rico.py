#!/usr/bin/env python3
"""
Cenários ricos (profundidade em camadas, lojas com toldo e letreiro, postes, árvores, calçadão ondulado)
e props que contam a história (celular com conversas, calendário com X, relógio).

Criado depois de comparar os meus vídeos com uma referência: lá cada cena tem lugar próprio, objetos da
história em destaque e profundidade; aqui o fundo era sempre a mesma praça chapada.
"""
import math
import random

from PIL import Image, ImageDraw

import video_carta as vc
from gerar_video import WW, WH, Pincel, gradiente, brilho

_C = {}


def _tom(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def _misturar(c, c2, k):
    return tuple(int(a * (1 - k) + b * k) for a, b in zip(c, c2))


def poste(p, x, y_base, h=420, cor=(40, 44, 52)):
    p.ret((x - 8, y_base - h, x + 8, y_base), cor, r=4)
    p.ret((x - 20, y_base - h - 6, x + 20, y_base - h + 10), cor, r=6)
    p.ret((x - 26, y_base - h - 70, x + 26, y_base - h - 8), (255, 236, 170), r=10, ow=6)
    p.poli([(x - 34, y_base - h - 70), (x, y_base - h - 104), (x + 34, y_base - h - 70)], cor, ow=5)


def arvore_praca(p, x, y_base, esc=1.0, cor=(94, 170, 100)):
    p.ret((x - 16 * esc, y_base - 190 * esc, x + 16 * esc, y_base), (118, 84, 58), r=6)
    for ox, oy, r in ((-46, -250, 64), (46, -250, 64), (0, -300, 74), (-18, -214, 56), (30, -216, 56)):
        p.elipse((x + (ox - r) * esc, y_base + (oy - r * 0.85) * esc, x + (ox + r) * esc, y_base + (oy + r * 0.85) * esc),
                 cor, ow=6)
    p.elipse((x - 40 * esc, y_base - 330 * esc, x - 8 * esc, y_base - 306 * esc), _tom(cor, 1.25), ow=0)


def loja(p, d, x, y, w, h, nome, cor_parede, cor_toldo, fonte, noite=False):
    p.ret((x, y, x + w, y + h), cor_parede, r=4)
    p.ret((x + 18, y + 96, x + w - 18, y + h - 20), (255, 230, 150) if noite else (190, 225, 245), r=6, ow=6)
    p.ret((x + w // 2 - 28, y + h - 150, x + w // 2 + 28, y + h), _tom(cor_parede, 0.7), r=4)
    # toldo listrado
    n = 8
    for i in range(n):
        xi = x - 6 + i * (w + 12) / n
        p.poli([(xi, y + 40), (xi + (w + 12) / n, y + 40), (xi + (w + 12) / n + 4, y + 96), (xi + 4, y + 96)],
               cor_toldo if i % 2 == 0 else (250, 250, 250), ow=0)
    p.ret((x - 8, y + 6, x + w + 8, y + 46), cor_toldo, r=6, ow=6)


def praca_rica(fc, hora="dia"):
    k = ("pr", hora)
    if k in _C:
        return _C[k]
    noite = hora == "noite"
    topo, base_c = {"dia": ((140, 200, 245), (222, 238, 250)), "tarde": ((250, 176, 120), (255, 224, 176)),
                    "noite": ((12, 18, 52), (40, 38, 82)), "chuva": ((102, 114, 130), (150, 158, 170)),
                    "inverno": ((190, 205, 225), (236, 241, 248))}[hora]
    base = gradiente(WW, WH, topo, base_c)
    p = Pincel(WW, WH)
    rng = random.Random(7)
    if noite:
        for _ in range(70):
            x, y = rng.randint(0, WW), rng.randint(0, 760)
            r = rng.choice((2, 3, 4))
            p.elipse((x - r, y - r, x + r, y + r), (255, 255, 230), ow=0)
        p.elipse((820, 150, 940, 270), (250, 244, 210), ow=0)
    # skyline distante (perspectiva atmosférica: mais clara/azulada)
    fundo = _misturar((170, 190, 215), base_c, 0.45) if not noite else (44, 52, 100)
    x = -40
    while x < WW:
        w = rng.randint(120, 190)
        h = rng.randint(300, 560)
        p.ret((x, 1000 - h, x + w, 1000), fundo, r=2, ow=0)
        for yy in range(1000 - h + 24, 980, 46):
            for xx in range(x + 16, x + w - 24, 40):
                p.ret((xx, yy, xx + 20, yy + 26), (255, 226, 140) if noite and rng.random() < 0.6 else _tom(fundo, 1.12),
                      r=2, ow=0)
        x += w + 6
    # relógio da praça
    p.ret((850, 520, 874, 1140), (60, 64, 76), r=6)
    p.elipse((790, 440, 934, 584), (250, 250, 255), ow=8)
    # lojas (plano médio)
    nomes = (("FARMÁCIA", (230, 236, 232), (48, 140, 80)), ("FLORES", (246, 214, 224), (196, 60, 110)),
             ("CAFÉ", (240, 224, 196), (196, 96, 52)), ("PADARIA", (230, 214, 190), (210, 150, 50)))
    ds = ImageDraw.Draw(base)
    lojas = []
    for i, (nome, parede, toldo) in enumerate(nomes):
        lx = -30 + i * 285
        loja(p, ds, lx, 860, 270, 400, nome, _tom(parede, 0.78 if noite else 1.0), toldo, None, noite)
        lojas.append((lx, nome))
    # rua e calçada
    p.ret((-20, 1258, WW + 20, 1360), (92, 96, 108) if not noite else (50, 54, 70), r=0)
    for xx in range(0, WW, 180):
        p.ret((xx + 30, 1300, xx + 120, 1312), (230, 220, 160), r=4, ow=0)
    p.ret((-20, 1360, WW + 20, 1400), (214, 208, 198) if not noite else (110, 108, 124), r=0)
    p.ret((-20, 1396, WW + 20, 1408), (150, 146, 140) if not noite else (70, 68, 86), r=0, ow=0)
    base.alpha_composite(p.pronto())
    # letreiros (texto)
    ds = ImageDraw.Draw(base)
    f = vc.fonte(fc, 36)
    for lx, nome in lojas:
        ds.text((lx + 135 - f.getlength(nome) / 2, 892), nome, font=f, fill=(255, 255, 255))
    # calçadão ondulado em primeiro plano
    p2 = Pincel(WW, WH)
    c1 = (236, 232, 222) if not noite else (108, 104, 124)
    c2 = (70, 72, 84) if not noite else (34, 34, 52)
    p2.ret((-20, 1408, WW + 20, WH + 20), c1, r=0, ow=0)
    for j in range(7):
        yb = 1470 + j * 78
        pts = [(x, yb + 18 * math.sin(x / 70 + j * 1.1)) for x in range(-20, WW + 40, 20)]
        p2.linha(pts, fill=c2, w=14)
    # árvores e postes
    arvore_praca(p2, 110, 1440, 1.25)
    arvore_praca(p2, 970, 1440, 1.25, cor=(80, 156, 92))
    poste(p2, 330, 1430, 440)
    poste(p2, 760, 1430, 440)
    base.alpha_composite(p2.pronto())
    # detalhes de rua: fios com pássaros, cartazes, vasos de planta, gente nas janelas
    d2 = ImageDraw.Draw(base)
    fio = (36, 38, 46, 255)
    for (xa, xb) in ((330, 760), (760, 1120), (-40, 330)):
        pts = [(xa + (xb - xa) * i / 20, 1000 + 38 * math.sin(math.pi * i / 20)) for i in range(21)]
        d2.line(pts, fill=fio, width=4)
    for x in (450, 600, 690):
        d2.ellipse((x - 11, 968, x + 11, 992), fill=(60, 64, 80, 255))
        d2.polygon([(x + 9, 976), (x + 24, 980), (x + 9, 984)], fill=(240, 180, 60, 255))
    for i, (lx, nome) in enumerate(lojas):
        d2.rectangle((lx + 214, 1000, lx + 248, 1060), fill=[(240, 90, 90), (90, 150, 230), (240, 200, 80), (110, 200, 130)][i % 4],
                     outline=(43, 40, 58, 255), width=3)
        d2.rectangle((lx + 14, 1196, lx + 46, 1226), fill=(150, 96, 64, 255), outline=(43, 40, 58, 255), width=3)
        for ox, oy in ((-8, -22), (8, -26), (0, -34)):
            d2.ellipse((lx + 30 + ox - 12, 1196 + oy - 12, lx + 30 + ox + 12, 1196 + oy + 12), fill=(80, 170, 100, 255),
                       outline=(43, 40, 58, 255), width=2)
    if noite:
        for x in (330, 760):
            base.alpha_composite(brilho((620, 620), (255, 226, 150), 300, 0.55), (x - 310, 1430 - 440 - 70 - 300))
        base.alpha_composite(Image.new("RGBA", (WW, WH), (10, 16, 60, 70)))
    elif hora == "tarde":
        base.alpha_composite(Image.new("RGBA", (WW, WH), (255, 150, 70, 38)))
    elif hora == "chuva":
        base.alpha_composite(Image.new("RGBA", (WW, WH), (60, 70, 90, 60)))
    _C[k] = base
    return base


def banco_rico(w=700, noite=False):
    k = ("banco", w, noite)
    if k not in _C:
        p = Pincel(700, 300)
        madeira = (160, 108, 66) if not noite else (112, 76, 52)
        ferro = (46, 48, 56)
        for i, y in enumerate((20, 78, 136)):
            p.ret((20, y, 680, y + 40), madeira, r=8)
        p.ret((30, 190, 670, 230), madeira, r=8)
        for x in (60, 610):
            p.ret((x - 12, 10, x + 12, 270), ferro, r=6)
            p.ret((x - 20, 230, x + 20, 280), ferro, r=6)
        img = p.pronto()
        _C[k] = img if w == 700 else img.resize((w, int(300 * w / 700)), Image.BICUBIC)
    return _C[k]


# --------------------------------------------------------------------------
# Props que contam a história
# --------------------------------------------------------------------------
def celular_conversas(fc, itens, w=760, hora="23:41"):
    """Tela de celular com lista de conversas (como na referência)."""
    p = Pincel(500, 900)
    p.ret((8, 8, 492, 892), (24, 26, 34), r=62, ow=8)
    p.ret((30, 40, 470, 870), (246, 244, 232), r=36, ow=0)
    p.ret((30, 40, 470, 150), (46, 130, 78), r=36, ow=0)
    p.ret((30, 110, 470, 150), (46, 130, 78), r=0, ow=0)
    p.ret((190, 20, 310, 36), (14, 14, 20), r=8, ow=0)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    fh, f1, f2 = vc.fonte(fc, 26), vc.fonte(fc, 28), vc.fonte(fc, 22)
    d.text((60, 76), "CONVERSAS", font=fh, fill=(255, 255, 255))
    d.text((470 - 40 - fh.getlength(hora), 76), hora, font=fh, fill=(255, 255, 255))
    cores = [(214, 70, 60), (70, 120, 190), (230, 170, 60), (110, 70, 160), (60, 160, 130)]
    for i, (nome, msg) in enumerate(itens):
        y = 190 + i * 130
        d.ellipse((50, y, 114, y + 64), fill=cores[i % len(cores)])
        d.text((130, y - 2), nome, font=f1, fill=(30, 30, 38))
        d.text((130, y + 34), msg, font=f2, fill=(90, 90, 100))
        d.text((420 - 20, y + 36), "✓", font=f2, fill=(150, 150, 160)) if False else None
        d.line((130, y + 78, 456, y + 78), fill=(220, 218, 206), width=2)
    return img if w == 500 else img.resize((w, int(900 * w / 500)), Image.BICUBIC)


def calendario(fc, titulo, marcados, total=31, w=640, cor_topo=(200, 52, 62), inicio=0):
    """Calendário com dias riscados com X (animável: 'marcados' = quantos X aparecem)."""
    p = Pincel(640, 560)
    p.ret((10, 10, 630, 550), (248, 244, 232), r=24, ow=8)
    p.ret((10, 10, 630, 96), cor_topo, r=24, ow=8)
    p.ret((10, 60, 630, 96), cor_topo, r=0, ow=0)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    ft, fn = vc.fonte(fc, 44), vc.fonte(fc, 30)
    d.text((320 - ft.getlength(titulo) / 2, 26), titulo, font=ft, fill=(255, 255, 255))
    cols = 7
    for i in range(total):
        r_, c_ = divmod(i + inicio, cols)
        x, y = 40 + c_ * 80, 130 + r_ * 82
        d.text((x + 40 - fn.getlength(str(i + 1)) / 2, y), str(i + 1), font=fn, fill=(60, 60, 70))
        if i < marcados:
            d.line((x + 6, y - 4, x + 74, y + 54), fill=(214, 40, 50), width=7)
            d.line((x + 74, y - 4, x + 6, y + 54), fill=(214, 40, 50), width=7)
    return img if w == 640 else img.resize((w, int(560 * w / 640)), Image.BICUBIC)


def relogio_praca(m, cx, cy, r, hh, mm):
    d = ImageDraw.Draw(m)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(250, 250, 255, 255), outline=(43, 40, 58, 255), width=10)
    for i in range(12):
        a = math.radians(i * 30)
        d.line((cx + r * 0.82 * math.sin(a), cy - r * 0.82 * math.cos(a), cx + r * 0.94 * math.sin(a),
                cy - r * 0.94 * math.cos(a)), fill=(43, 40, 58, 255), width=8)
    ah, am = math.radians((hh % 12) * 30 + mm * 0.5), math.radians(mm * 6)
    d.line((cx, cy, cx + r * 0.5 * math.sin(ah), cy - r * 0.5 * math.cos(ah)), fill=(43, 40, 58, 255), width=14)
    d.line((cx, cy, cx + r * 0.78 * math.sin(am), cy - r * 0.78 * math.cos(am)), fill=(43, 40, 58, 255), width=9)
    d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=(43, 40, 58, 255))


def sombra(m, cx, by, w=260, alpha=90):
    """Sombra suave no chão sob o personagem (ancora ele na cena)."""
    k = ("sombra", int(w))
    if k not in _C:
        img = brilho((int(w), int(w * 0.28)), (10, 10, 20), int(w * 0.5), 1.0)
        _C[k] = img
    img = _C[k].copy()
    img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha / 255)))
    m.alpha_composite(img, (int(cx - w / 2), int(by - w * 0.14)))
