#!/usr/bin/env python3
"""Cachorros de desenho animado (sentado / em pé / deitado), com rabo abanando, piscar, respiração e boca falando.
Raças por paleta: vira-lata (orelha caída ou uma só), rottweiler, salsicha, pug, poodle."""
import math

from PIL import Image

from gerar_video import Pincel

_C = {}

VIRA_LATA = dict(corpo=(40, 38, 46), foc=(70, 66, 76), nariz=(15, 15, 20), orelha=(28, 26, 34), orelhas="uma", cauda=1.0)
CARAMELO = dict(corpo=(220, 160, 90), foc=(244, 214, 170), nariz=(40, 30, 30), orelha=(170, 110, 60), orelhas="cai", cauda=1.0)
ROTT = dict(corpo=(36, 34, 40), foc=(196, 130, 70), nariz=(10, 10, 12), orelha=(24, 22, 28), orelhas="cai", cauda=0.3,
            largo=1.25)
SALSICHA = dict(corpo=(170, 90, 50), foc=(200, 130, 80), nariz=(20, 14, 12), orelha=(120, 62, 34), orelhas="cai", cauda=0.8,
                comprido=1.55, baixo=0.62)
PUG = dict(corpo=(236, 212, 170), foc=(60, 50, 50), nariz=(15, 12, 12), orelha=(70, 60, 56), orelhas="cai", cauda=0.2,
           focinho_curto=True, largo=1.1)
POODLE = dict(corpo=(250, 246, 250), foc=(250, 246, 250), nariz=(30, 20, 30), orelha=(236, 230, 240), orelhas="fofa", cauda=0.6,
              fofo=True)


def _tom(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def cao(pal, pose="sentado", boca=0.0, piscar=False, cauda=0.0, w=420, olhar=0.0):
    """Sprite RGBA de cachorro virado para a direita. boca 0–1; cauda -1..1 (abanar); olhar -1..1."""
    qb, qc = round(boca * 3) / 3, round(cauda * 3) / 3
    k = (tuple(sorted((a, str(b)) for a, b in pal.items())), pose, qb, piscar, qc, w, round(olhar * 2) / 2)
    if k in _C:
        return _C[k]
    W, H = 660, 520
    p = Pincel(W, H)
    c, f, n, o = pal["corpo"], pal["foc"], pal["nariz"], pal["orelha"]
    lg, cp, bx = pal.get("largo", 1.0), pal.get("comprido", 1.0), pal.get("baixo", 1.0)
    esc = _tom(c, 0.8)
    if pose == "sentado":
        # rabo (atrás, abana)
        a = qc * 22
        p.linha([(120, 430), (60 + a, 390), (40 + a * 1.6, 330)], fill=c, w=int(34 * pal.get("cauda", 1.0) + 12))
        p.elipse((100, 250, 310 + 20 * lg, 460), c)                           # corpo + anca
        p.elipse((140, 340, 300, 470), esc, ow=0)
        p.capsula((250, 330), (270, 470), 40, c)                              # perna da frente
        p.capsula((300, 330), (320, 470), 40, c)
        p.elipse((235, 450, 300, 490), f)                                     # patas
        p.elipse((290, 450, 360, 490), f)
        hx, hy = 330, 150
    elif pose == "deitado":
        a = qc * 20
        p.linha([(90, 410), (40 + a, 390), (20 + a * 1.4, 350)], fill=c, w=int(30 * pal.get("cauda", 1.0) + 10))
        p.elipse((70, 290, 340 + 20 * (cp - 1), 460), c)
        p.capsula((250, 420), (390, 440), 40, c)
        p.elipse((350, 420, 440, 470), f)
        hx, hy = 360, 290
    else:  # em pé
        a = qc * 24
        p.linha([(80, 270), (40 + a, 230), (30 + a * 1.4, 170)], fill=c, w=int(30 * pal.get("cauda", 1.0) + 10))
        L = 270 * cp
        p.elipse((70, 235, 70 + L, 385), c)
        for x in (110, 150, 70 + L - 90, 70 + L - 50):
            p.capsula((x, 340), (x, 470), 34, c)
            p.elipse((x - 30, 450, x + 34, 490), f)
        hx, hy = 70 + L + 30, 200
    # cabeça
    cab = (hx - 95, hy - 90, hx + 85, hy + 80)
    if pal.get("fofo"):
        for dx, dy in ((-60, -70), (0, -90), (60, -70)):
            p.elipse((hx + dx - 45, hy + dy - 40, hx + dx + 45, hy + dy + 40), c)
    p.elipse(cab, c)
    if pal.get("focinho_curto"):
        p.elipse((hx + 30, hy - 10, hx + 110, hy + 60), f)
        fx = hx + 105
    else:
        p.elipse((hx + 10, hy - 20, hx + 135, hy + 55), f)
        fx = hx + 128
    p.elipse((fx - 24, hy - 28, fx + 14, hy), n, ow=0)                         # nariz
    # orelhas
    if pal["orelhas"] == "cai":
        p.elipse((hx - 92, hy - 50, hx - 20, hy + 100), o)
    elif pal["orelhas"] == "uma":
        p.elipse((hx - 92, hy - 50, hx - 20, hy + 100), o)
        p.poli([(hx + 10, hy - 85), (hx + 40, hy - 150), (hx + 62, hy - 80)], c)    # orelha em pé
    else:
        p.elipse((hx - 105, hy - 40, hx - 25, hy + 110), o)
    im = p.pronto()
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    # olho
    ex, ey = hx + 38 + olhar * 8, hy - 30
    if piscar:
        d.arc((ex - 16, ey - 8, ex + 16, ey + 18), 200, 340, fill=(20, 20, 30, 255), width=6)
    else:
        d.ellipse((ex - 16, ey - 16, ex + 16, ey + 18), fill=(255, 255, 255, 255), outline=(20, 20, 30, 255), width=4)
        d.ellipse((ex - 7 + olhar * 6, ey - 8, ex + 7 + olhar * 6, ey + 10), fill=(20, 20, 30, 255))
        d.ellipse((ex - 3 + olhar * 6, ey - 8, ex + 1 + olhar * 6, ey - 3), fill=(255, 255, 255, 255))
    # boca
    if qb > 0.01:
        mh = 10 + 30 * qb
        d.polygon([(fx - 50, hy + 22), (fx + 4, hy + 22), (fx - 20, hy + 22 + mh)], fill=(150, 40, 60, 255),
                  outline=(30, 20, 30, 255))
        d.ellipse((fx - 38, hy + 22 + mh * 0.4, fx - 12, hy + 22 + mh * 0.9), fill=(240, 120, 130, 255))
    else:
        d.arc((fx - 60, hy - 12, fx + 8, hy + 40), 20, 90, fill=(30, 20, 30, 255), width=5)
    if pal.get("focinho_curto"):                                                   # rugas do pug
        d.arc((hx - 10, hy - 70, hx + 50, hy - 20), 200, 340, fill=(60, 50, 50, 255), width=4)
    s = w / W
    res = im.resize((w, int(H * s)), Image.BICUBIC)
    _C[k] = res
    return res


def desenhar(m, t, x, by, e, pal, pose="sentado", falando=False, sx=1, cauda_vel=0.0, w=420, rot=0.0, boca=None):
    """Cola o cachorro no mundo com base em (x, by); respira e pisca sozinho."""
    piscar = (t % 3.4) < 0.14
    b = boca if boca is not None else (0.5 + 0.5 * math.sin(t * 14)) if falando else 0.0
    ca = math.sin(t * 9) * cauda_vel
    im = cao(pal, pose, b, piscar, ca, w)
    resp = 1 + 0.012 * math.sin(t * 2.2)
    ww = int(im.width * e)
    hh = int(im.height * e * resp)
    im = im.resize((ww, hh), Image.BICUBIC)
    if sx < 0:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if rot:
        im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    m.alpha_composite(im, (int(x - im.width / 2), int(by - im.height + 10 * e)))
