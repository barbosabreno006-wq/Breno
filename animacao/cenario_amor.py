#!/usr/bin/env python3
"""Props de "Todo Mundo Me Ama": a Admiradora (alta, sem rosto, sorriso enorme, coração no peito),
corações, presente, chave, fios de marionete e filtro de noite."""
import math

from PIL import Image, ImageDraw

from gerar_video import Pincel, brilho

_C = {}


def _heart_pts(cx, cy, s):
    pts = []
    for i in range(48):
        a = i / 48 * 2 * math.pi
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((cx + x * s, cy - y * s))
    return pts


def coracao(w=160, cor=(232, 44, 84), pulso=0.0):
    """Coração com contorno e brilho; pulso de 0 a 1."""
    q = round(pulso * 6) / 6
    k = ("cor", w, cor, q)
    if k not in _C:
        s = w / 40 * (1 + 0.18 * q)
        p = Pincel(int(w * 1.6), int(w * 1.6))
        p.poli(_heart_pts(w * 0.8, w * 0.8, s), cor, ow=6)
        im = p.pronto()
        d = ImageDraw.Draw(im)
        d.ellipse((w * 0.5, w * 0.45, w * 0.68, w * 0.6), fill=(255, 255, 255, 150))
        _C[k] = im
    return _C[k]


def coracoes_flutuando(m, t, x, y, n=5, w=44, seed=1, alt=140, cor=(240, 70, 110)):
    """Corações subindo acima de (x, y)."""
    for i in range(n):
        ph = ((t * 0.5 + i / n + seed * 0.13) % 1.0)
        xx = x + math.sin(ph * 6 + i * 2.1) * 40 + (i - n / 2) * 38
        yy = y - ph * alt
        im = coracao(int(w * (0.7 + 0.5 * math.sin(i * 1.7) ** 2)), cor)
        a = int(255 * min(1, ph * 6, (1 - ph) * 3))
        if a <= 0:
            continue
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v, a=a: v * a // 255))
        m.alpha_composite(im, (int(xx - im.width / 2), int(yy - im.height / 2)))


def presente(w=200, cor=(230, 70, 90), fita=(255, 220, 90)):
    k = ("pres", w, cor)
    if k not in _C:
        p = Pincel(240, 240)
        p.ret((20, 90, 220, 220), cor, r=10)
        p.ret((10, 70, 230, 110), _t(cor, 1.12), r=10)
        p.ret((100, 70, 140, 220), fita, r=0)
        p.poli([(120, 70), (70, 20), (100, 8), (120, 70)], fita)
        p.poli([(120, 70), (170, 20), (140, 8), (120, 70)], fita)
        _C[k] = p.pronto().resize((w, w), Image.BICUBIC)
    return _C[k]


def _t(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def chave(w=240, ang=0.0, brilho_=0.0):
    """Chavinha dourada (a chave da Lia)."""
    p = Pincel(300, 140)
    ouro, esc = (250, 204, 70), (190, 140, 30)
    p.elipse((10, 20, 100, 110), ouro, ow=7)
    p.elipse((36, 46, 74, 84), (255, 255, 255, 0), ow=7)
    p.ret((96, 56, 270, 76), ouro, r=4, ow=6)
    p.ret((220, 70, 242, 112), ouro, r=2, ow=6)
    p.ret((248, 70, 268, 100), ouro, r=2, ow=6)
    p.ret((20, 28, 60, 40), (255, 244, 190), r=4, ow=0)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    d.ellipse((38, 48, 72, 82), fill=(0, 0, 0, 0))
    im = im.resize((w, int(140 * w / 300)), Image.BICUBIC)
    if ang:
        im = im.rotate(ang, expand=True, resample=Image.BICUBIC)
    return im


def admiradora(h=1500, pulso=0.0, boca=1.0, giro=0.0):
    """A Admiradora: muito alta e magra, rosto liso com sorriso enorme e um coração no peito.
    h = altura final em px; pulso 0–1 batimento; giro inclina a cabeça (-1..1)."""
    q = round(pulso * 5) / 5
    g_ = round(giro * 4) / 4
    k = ("adm", h, q, round(boca, 1), g_)
    if k in _C:
        return _C[k]
    W, H = 460, 1500
    p = Pincel(W, H)
    corpo, escuro = (122, 30, 84), (70, 18, 54)
    # pernas finíssimas
    p.capsula((190, 930), (176, 1470), 30, escuro)
    p.capsula((270, 930), (284, 1470), 30, escuro)
    p.ret((150, 1450, 215, 1490), escuro, r=10)
    p.ret((250, 1450, 320, 1490), escuro, r=10)
    # braços compridos até os joelhos, mãos de dedos longos
    p.capsula((150, 390), (80, 800), 30, corpo)
    p.capsula((80, 800), (70, 1090), 26, corpo)
    p.capsula((310, 390), (380, 800), 30, corpo)
    p.capsula((380, 800), (390, 1090), 26, corpo)
    for sx, x0 in ((-1, 70), (1, 390)):
        for j in range(4):
            p.linha([(x0, 1090), (x0 + sx * (14 + j * 7) - 14 * sx, 1170 + j * 6)], fill=(40, 10, 30), w=7)
    # tronco
    p.poli([(130, 380), (330, 380), (300, 960), (160, 960)], corpo)
    # pescoço
    p.capsula((230, 300), (230, 390), 36, (246, 206, 214))
    # cabeça inclinada
    dx = int(g_ * 22)
    hx = 230 + dx
    p.elipse((hx - 105, 40, hx + 105, 330), (250, 214, 224))
    # bochechas
    p.elipse((hx - 90, 190, hx - 40, 230), (244, 150, 176), ow=0)
    p.elipse((hx + 40, 190, hx + 90, 230), (244, 150, 176), ow=0)
    # sorriso gigante (sem olhos, sem nariz)
    bw = 82 * boca
    p.chord((hx - 92, 150, hx + 92, 150 + 70 + 70 * boca), 0, 180, (60, 8, 30), ow=6)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    # dentes pontudos (presas) saindo do teto da boca
    for i in range(9):
        x0 = hx - 80 + i * 18
        d.polygon([(x0, 186), (x0 + 18, 186), (x0 + 9, 186 + 30 + 10 * boca)], fill=(255, 255, 255, 255),
                  outline=(40, 10, 30, 255))
    # coração brilhando no peito
    cor = coracao(180, (236, 46, 90), pulso)
    glow = brilho((520, 520), (255, 80, 120), 240, 0.35 + 0.45 * q)
    im.alpha_composite(glow, (int(230 - 260), int(620 - 260)))
    im.alpha_composite(cor, (int(230 - cor.width / 2), int(620 - cor.height / 2)))
    if h != H:
        im = im.resize((int(W * h / H), h), Image.BICUBIC)
    _C[k] = im
    return im


def cabeca_admiradora(w=700, boca=1.0, giro=0.0):
    """Close do rosto liso e do sorriso (recorte da cabeça)."""
    im = admiradora(1500, 0.0, boca, giro)
    return im.crop((100, 20, 360, 350)).resize((w, int(w * 330 / 260)), Image.BICUBIC)


def fios(m, origem, alvos, t, cor=(255, 190, 220, 200)):
    """Fios de marionete saindo das mãos da Admiradora até a cabeça de cada pessoa."""
    d = ImageDraw.Draw(m, "RGBA")
    for i, (ax, ay) in enumerate(alvos):
        ox, oy = origem
        for s in range(2):
            sw = math.sin(t * 2 + i) * 14
            d.line([(ox + s * 6, oy), ((ox + ax) / 2 + sw, (oy + ay) / 2 - 40), (ax + s * 4, ay)], fill=cor, width=4)


def noite(img, forca=0.55, cor=(18, 22, 70)):
    """Escurece e azula uma imagem RGBA de cenário."""
    k = ("noite", id(img), forca)
    if k in _C:
        return _C[k]
    ov = Image.new("RGBA", img.size, cor + (255,))
    res = Image.blend(img.convert("RGBA"), ov, forca)
    _C[k] = res
    return res
