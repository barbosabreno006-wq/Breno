#!/usr/bin/env python3
"""Cenários de "Boa Noite, Meu Velho": ponte, cemitério, padaria, cozinha com fogo, mesa de jantar, sofá, porta de hospital,
ambulância, chuva e adereços (recibo, placa, balão de cachorro)."""
import math
import random

from PIL import Image, ImageDraw

import video_carta as vc
import cao as cao_
from gerar_video import WW, WH, Pincel, gradiente, brilho

_C = {}


def _t(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def chuva(f, t, n=150, alpha=130, seed=1):
    """Chuva diagonal por cima do quadro (f = imagem RGB já recortada)."""
    w, h = f.size
    ov = Image.new("RGBA", f.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    rng = random.Random(seed)
    for i in range(n):
        x0 = rng.uniform(-60, w)
        v = rng.uniform(1500, 2400)
        y0 = (rng.uniform(0, h) + t * v) % (h + 100) - 50
        d.line((x0, y0, x0 - 14, y0 + 48), fill=(205, 220, 255, alpha), width=3)
    b = f.convert("RGBA")
    b.alpha_composite(ov)
    return b.convert("RGB")


def laranja():
    if "lar" not in _C:
        _C["lar"] = gradiente(WW, WH, (255, 176, 60), (214, 98, 24))
    return _C["lar"]


def piso(p, y=1500, cor=(150, 112, 80)):
    p.ret((-20, y, WW + 20, WH + 20), cor, r=0, ow=0)


def ponte(fc):
    if "ponte" in _C:
        return _C["ponte"]
    base = gradiente(WW, WH, (26, 30, 70), (12, 14, 34))
    p = Pincel(WW, WH)
    p.ret((-20, 1500, WW + 20, WH + 20), (44, 48, 66), r=0, ow=0)
    p.ret((-20, 900, WW + 20, 1010), (88, 90, 106), r=0)
    for x in (80, 340, 600, 860):
        p.ret((x, 1010, x + 140, 1500), (70, 72, 90), r=0)
    p.ret((0, 1480, WW, 1560), (30, 70, 120), r=0, ow=0)
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((700, 700), (200, 210, 255), 280, 0.25), (380, 150))
    p2 = Pincel(360, 220)
    p2.poli([(10, 60), (350, 60), (320, 210), (40, 210)], (190, 140, 90))
    p2.poli([(10, 60), (90, 10), (170, 60)], (210, 160, 110))
    p2.poli([(190, 60), (270, 10), (350, 60)], (210, 160, 110))
    base.alpha_composite(p2.pronto(), (680, 1260))
    _C["ponte"] = base
    return base


def cemiterio(fc):
    if "cem" in _C:
        return _C["cem"]
    base = gradiente(WW, WH, (150, 156, 170), (206, 208, 216))
    p = Pincel(WW, WH)
    p.ret((-20, 1380, WW + 20, WH + 20), (110, 140, 100), r=0, ow=0)
    for x, y in ((120, 1360), (300, 1330), (700, 1340), (900, 1370)):
        p.ret((x, y - 130, x + 110, y), (170, 172, 182), r=40)
        p.linha([(x + 55, y - 100), (x + 55, y - 40)], w=8)
        p.linha([(x + 30, y - 75), (x + 80, y - 75)], w=8)
    p.ret((470, 1440, 640, 1520), (96, 70, 50), r=10)                            # túmulo novo
    p.ret((540, 1330, 560, 1450), (230, 230, 236), r=4)
    p.ret((500, 1360, 600, 1376), (230, 230, 236), r=4)
    base.alpha_composite(p.pronto())
    _C["cem"] = base
    return base


def padaria(fc, n_apostas=0):
    k = ("pad", n_apostas)
    if k in _C:
        return _C[k]
    base = gradiente(WW, WH, (252, 230, 190), (236, 204, 158))
    p = Pincel(WW, WH)
    piso(p, 1500, (176, 130, 96))
    p.ret((60, 300, 1020, 400), (200, 70, 60), r=10)                             # faixa
    p.ret((560, 480, 1000, 760), (46, 84, 60), r=10, ow=10)                      # lousa
    for x in (90, 190, 290, 390):
        p.ret((x, 480, x + 70, 700), (240, 190, 90), r=26)                       # pães na estante
    p.ret((60, 1180, 1020, 1500), (150, 100, 66), r=8)                           # balcão
    p.ret((60, 1150, 1020, 1210), (200, 150, 100), r=8)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f1, f2 = vc.fonte(fc, 56), vc.fonte(fc, 40)
    d.text((540 - f1.getlength("PADARIA DO ZÉ") / 2, 316), "PADARIA DO ZÉ", font=f1, fill=(255, 255, 255))
    d.text((780 - f2.getlength("BOLÃO DO TECO") / 2, 506), "BOLÃO DO TECO", font=f2, fill=(255, 240, 160))
    d.text((780 - f2.getlength("R$ 5 / palpite") / 2, 560), "R$ 5 / palpite", font=f2, fill=(255, 255, 255))
    for i in range(n_apostas):
        d.text((600, 620 + i * 34), "Oi, Teco!", font=vc.fonte(fc, 28), fill=(255, 255, 255))
    _C[k] = base
    return base


def cozinha(fc, fogo=0.0, t=0.0):
    """Cozinha; fogo 0–1 mostra chamas no fogão."""
    base = gradiente(WW, WH, (232, 222, 200), (212, 198, 170)).copy()
    p = Pincel(WW, WH)
    piso(p, 1500, (140, 110, 90))
    p.ret((240, 1000, 840, 1500), (210, 210, 218), r=14)                         # fogão
    p.ret((280, 1020, 800, 1100), (60, 60, 72), r=8)
    p.ret((40, 380, 340, 640), (170, 130, 90), r=10)                             # armário
    p.ret((740, 380, 1040, 640), (170, 130, 90), r=10)
    base.alpha_composite(p.pronto())
    if fogo > 0:
        d = ImageDraw.Draw(base, "RGBA")
        for i in range(7):
            x = 320 + i * 70
            hgt = (120 + 80 * math.sin(t * 9 + i * 1.7) ** 2) * fogo * 2
            d.polygon([(x - 36, 1020), (x, 1020 - hgt), (x + 36, 1020)], fill=(255, 150, 30, 240))
            d.polygon([(x - 18, 1020), (x, 1020 - hgt * 0.6), (x + 18, 1020)], fill=(255, 230, 90, 240))
        base.alpha_composite(brilho((1000, 800), (255, 150, 60), 440, 0.5 * fogo), (40, 500))
    return base


def mesa(fc):
    if "mesa" in _C:
        return _C["mesa"]
    base = gradiente(WW, WH, (250, 226, 176), (232, 204, 152))
    p = Pincel(WW, WH)
    piso(p, 1520, (160, 110, 80))
    p.ret((60, 1240, 1020, 1300), (130, 86, 56), r=10)
    p.ret((120, 1300, 170, 1560), (110, 72, 46), r=4)
    p.ret((910, 1300, 960, 1560), (110, 72, 46), r=4)
    p.ret((200, 1180, 360, 1240), (250, 250, 250), r=30)                         # pratos
    p.ret((460, 1180, 620, 1240), (250, 250, 250), r=30)
    p.ret((720, 1180, 880, 1240), (250, 250, 250), r=30)
    p.elipse((250, 1150, 310, 1190), (230, 150, 70))
    p.elipse((510, 1150, 570, 1190), (230, 150, 70))
    p.elipse((770, 1150, 830, 1190), (230, 150, 70))
    base.alpha_composite(p.pronto())
    _C["mesa"] = base
    return base


def sofa(fc, noite=False):
    k = ("sofa", noite)
    if k in _C:
        return _C[k]
    base = gradiente(WW, WH, (74, 70, 110), (46, 42, 78)) if noite else gradiente(WW, WH, (238, 218, 184), (216, 194, 158))
    p = Pincel(WW, WH)
    piso(p, 1500, (120, 90, 72) if noite else (168, 128, 98))
    p.ret((620, 260, 980, 700), (24, 30, 60) if noite else (176, 216, 240), r=10, ow=10)
    p.ret((60, 1100, 800, 1500), (200, 90, 80), r=60)
    p.ret((60, 960, 800, 1200), (214, 104, 94), r=60)
    p.ret((30, 1060, 150, 1500), (180, 76, 68), r=40)
    p.ret((720, 1060, 840, 1500), (180, 76, 68), r=40)
    base.alpha_composite(p.pronto())
    _C[k] = base
    return base


def hospital_porta(fc, chuva_=False):
    k = ("hp", chuva_)
    if k in _C:
        return _C[k]
    base = gradiente(WW, WH, (60, 70, 100), (34, 40, 62)) if chuva_ else gradiente(WW, WH, (214, 226, 238), (186, 204, 222))
    p = Pincel(WW, WH)
    piso(p, 1500, (70, 76, 96) if chuva_ else (176, 180, 190))
    p.ret((80, 420, 1000, 1500), (224, 232, 240), r=8)
    p.ret((340, 760, 740, 1500), (130, 190, 220), r=8, ow=8)
    p.linha([(540, 760), (540, 1500)], w=6)
    p.ret((300, 520, 780, 640), (200, 50, 60), r=10)
    p.ret((470, 540, 610, 620), (255, 255, 255), r=4, ow=0)                       # cruz
    p.ret((520, 530, 560, 630), (255, 255, 255), r=4, ow=0)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 44)
    d.text((540 - f.getlength("HOSPITAL") / 2, 650), "HOSPITAL", font=f, fill=(70, 70, 80))
    if chuva_:
        base.alpha_composite(brilho((900, 500), (255, 255, 200), 380, 0.35), (90, 760))
    _C[k] = base
    return base


def ambulancia(w=900):
    if ("amb", w) in _C:
        return _C[("amb", w)]
    p = Pincel(900, 460)
    p.ret((20, 80, 640, 380), (250, 250, 252), r=30)
    p.ret((620, 150, 880, 380), (250, 250, 252), r=40)
    p.ret((660, 170, 820, 270), (150, 200, 230), r=14)
    p.ret((260, 160, 340, 300), (210, 40, 50), r=4, ow=0)
    p.ret((230, 200, 370, 260), (210, 40, 50), r=4, ow=0)
    p.elipse((120, 330, 240, 450), (40, 40, 50))
    p.elipse((640, 330, 760, 450), (40, 40, 50))
    p.ret((300, 50, 400, 90), (220, 50, 60), r=8)
    im = p.pronto()
    _C[("amb", w)] = im if w == 900 else im.resize((w, int(460 * w / 900)), Image.BICUBIC)
    return _C[("amb", w)]


def recibo(fc, w=620):
    p = Pincel(620, 760)
    p.ret((10, 10, 610, 750), (250, 248, 240), r=10)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    f1, f2, f3 = vc.fonte(fc, 56), vc.fonte(fc, 34), vc.fonte(fc, 90)
    d.text((310 - f1.getlength("RECIBO") / 2, 50), "RECIBO", font=f1, fill=(40, 40, 50))
    d.text((310 - f2.getlength("ADESTRAMENTO VERBAL") / 2, 150), "ADESTRAMENTO VERBAL", font=f2, fill=(80, 80, 90))
    d.text((310 - f2.getlength("Cão: DUQUE (poodle)") / 2, 220), "Cão: DUQUE (poodle)", font=f2, fill=(80, 80, 90))
    d.text((310 - f3.getlength("R$ 1.000") / 2, 330), "R$ 1.000", font=f3, fill=(40, 120, 60))
    return im if w == 620 else im.resize((w, int(760 * w / 620)), Image.BICUBIC)


def placa(fc, texto, cor=(200, 50, 60), w=700):
    p = Pincel(700, 260)
    p.ret((10, 10, 690, 250), cor, r=30, ow=8)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    f = vc.fonte(fc, 56)
    partes = texto.split("\n")
    for i, s in enumerate(partes):
        d.text((350 - f.getlength(s) / 2, 130 - 34 * len(partes) / 2 * 1.5 + i * 62), s, font=f, fill=(255, 255, 255))
    return im if w == 700 else im.resize((w, int(260 * w / 700)), Image.BICUBIC)


class Cachorro:
    """Adaptador para usar o cachorro como personagem (mesma chamada do ve.Pers)."""

    POSES = {"idle": "sentado", "sentado": "sentado", "deitado": "deitado", "pe": "pe", "anda": "pe"}

    def __init__(self, pal, filme, tam=420):
        self.pal, self.filme, self.tam = pal, filme, tam

    def __call__(self, m, t, cx, by, e, expr="neutro", pose="idle", fala=None, sx=1, **kw):
        T = getattr(self.filme, "T", 0)
        falando = bool(fala) and any(a <= T < b for a, b in fala)
        cao_.desenhar(m, t, cx, by, e, self.pal, self.POSES.get(pose, "sentado"), falando, sx,
                      cauda_vel=0.5 if expr in ("feliz", "ri") else 0.0, w=self.tam)
