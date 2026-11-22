#!/usr/bin/env python3
"""
Cenários e props para "A Foto do Futuro": sala de aula, mural de fotos com barbante, palco, grades,
corredor e quarto de hospital, centro cirúrgico, mapa do Brasil, polaroids "25 ANOS DEPOIS", e os
objetos da virada (enceradeira, tomada, respirador).
"""
import math
import random

from PIL import Image, ImageDraw

import gerar_video as g
import video_carta as vc
from gerar_video import WW, WH, Pincel, gradiente, brilho

_C = {}


def _tom(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


# ---------------------------------------------------------------- sala de aula
def sala_aula(fc, quadro="", dia="12", noite=False):
    k = ("sala", quadro, dia)
    if k in _C:
        return _C[k]
    base = gradiente(WW, WH, (236, 210, 164), (214, 186, 140))
    p = Pincel(WW, WH)
    p.ret((-20, 1180, WW + 20, 1540), (110, 168, 160), r=0, ow=0)                 # rodapé verde-água
    p.ret((-20, 1160, WW + 20, 1184), (86, 132, 126), r=0, ow=0)
    p.ret((-20, 1540, WW + 20, WH + 20), (176, 132, 92), r=0, ow=0)               # piso
    for i in range(10):
        p.ret((-20, 1540 + i * 40, WW + 20, 1544 + i * 40), (150, 108, 72), r=0, ow=0)
    # estante
    p.ret((60, 120, 520, 520), (150, 104, 70), r=10)
    for r_ in range(3):
        y = 150 + r_ * 125
        p.ret((70, y + 100, 510, y + 112), (112, 76, 50), r=0, ow=0)
        x = 82
        rng = random.Random(r_ + 3)
        while x < 490:
            w = rng.randint(26, 44)
            p.ret((x, y + rng.randint(0, 20), x + w, y + 100), [(200, 70, 70), (70, 120, 200), (230, 190, 70),
                                                                (100, 170, 110), (160, 90, 180)][rng.randint(0, 4)], r=3, ow=4)
            x += w + 4
    # quadro-negro
    p.ret((130, 640, 960, 1160), (150, 104, 70), r=14)
    p.ret((150, 660, 940, 1140), (48, 84, 70), r=6, ow=4)
    # janela e relógio
    p.ret((640, 120, 1020, 520), (170, 214, 238), r=10, ow=10)
    p.linha([(830, 120), (830, 520)], w=8)
    p.linha([(640, 320), (1020, 320)], w=8)
    p.elipse((560, 540, 640, 620), (250, 250, 255), ow=6)
    p.linha([(600, 580), (600, 552)], w=5)
    p.linha([(600, 580), (620, 586)], w=5)
    # calendário
    p.ret((970, 700, 1040, 800), (245, 242, 232), r=4)
    p.ret((970, 700, 1040, 730), (200, 52, 62), r=4, ow=4)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    if quadro:
        f = vc.fonte(fc, 120)
        d.text((545 - f.getlength(quadro) / 2, 820), quadro, font=f, fill=(244, 244, 236))
    f2 = vc.fonte(fc, 30)
    d.text((1005 - f2.getlength(dia) / 2, 738), dia, font=f2, fill=(50, 50, 60))
    base.alpha_composite(brilho((520, 520), (255, 240, 200), 260, 0.28), (560, 80))
    _C[k] = base
    return base


def carteira(w=360):
    p = Pincel(360, 260)
    p.ret((10, 20, 350, 70), (214, 170, 112), r=8)
    p.ret((30, 70, 52, 240), (80, 84, 96), r=4)
    p.ret((308, 70, 330, 240), (80, 84, 96), r=4)
    p.ret((60, 120, 300, 142), (80, 84, 96), r=4)
    img = p.pronto()
    return img if w == 360 else img.resize((w, int(260 * w / 360)), Image.BICUBIC)


# ---------------------------------------------------------------- polaroids
def _fig(pal, expr="neutro", escala=0.5):
    spr = g.desenhar_personagem(pal, expr, "idle")
    return spr.resize((int(spr.width * escala), int(spr.height * escala)), Image.BICUBIC)


def ph_palco(pals):
    p = Pincel(360, 300)
    p.ret((0, 0, 360, 300), (70, 30, 110), r=0, ow=0)
    p.ret((0, 0, 70, 300), (190, 40, 70), r=0, ow=0)
    p.ret((290, 0, 360, 300), (190, 40, 70), r=0, ow=0)
    p.poli([(180, 0), (110, 300), (250, 300)], (255, 240, 190), ow=0)
    p.ret((0, 262, 360, 300), (120, 84, 56), r=0, ow=0)
    img = p.pronto()
    ov = Image.new("RGBA", img.size, (255, 240, 190, 0))
    f = _fig(pals[0], "feliz", 0.42)
    img.alpha_composite(f, (180 - f.width // 2, 300 - f.height + 24))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 14, 340, 54), radius=10, fill=(255, 80, 190))
    return img


def ph_grades(pal):
    p = Pincel(360, 300)
    p.ret((0, 0, 360, 300), (118, 120, 128), r=0, ow=0)
    img = p.pronto()
    f = _fig(pal, "triste", 0.42)
    img.alpha_composite(f, (180 - f.width // 2, 300 - f.height + 20))
    q = Pincel(360, 300)
    for x in range(20, 360, 50):
        q.ret((x - 6, 0, x + 6, 300), (46, 48, 56), r=3, ow=0)
    q.ret((0, 20, 360, 34), (46, 48, 56), r=2, ow=0)
    img.alpha_composite(q.pronto())
    return img


def ph_hospital(med, paciente, pedro):
    p = Pincel(360, 300)
    p.ret((0, 0, 360, 300), (190, 226, 232), r=0, ow=0)
    p.ret((0, 250, 360, 300), (150, 190, 196), r=0, ow=0)
    p.ret((220, 190, 360, 270), (240, 244, 250), r=8)
    img = p.pronto()
    for pal, x, e in ((med, 70, 0.36), (pedro, 150, 0.36)):
        f = _fig(pal, "neutro", e)
        img.alpha_composite(f, (x - f.width // 2, 300 - f.height + 24))
    fp = _fig(paciente, "neutro", 0.34)
    img.alpha_composite(fp, (292 - fp.width // 2, 236 - fp.height + 40))
    q = Pincel(360, 300)
    q.ret((212, 226, 360, 280), (246, 248, 252), r=8)
    img.alpha_composite(q.pronto())
    return img


def polaroid(fc, conteudo, legenda="25 ANOS DEPOIS", w=640, cor=(250, 246, 236)):
    p = Pincel(420, 470)
    p.ret((8, 8, 412, 462), cor, r=8, ow=7)
    p.ret((26, 26, 394, 340), (30, 30, 38), r=2, ow=0)
    img = p.pronto()
    if conteudo is not None:
        c = conteudo.resize((364, 308), Image.BICUBIC)
        img.alpha_composite(c, (28, 28))
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 28)
    d.text((210 - f.getlength(legenda) / 2, 380), legenda, font=f, fill=(70, 60, 130))
    return img if w == 420 else img.resize((w, int(470 * w / 420)), Image.BICUBIC)


# ---------------------------------------------------------------- mural
def mural(fc, fotos, pregado=None):
    base = gradiente(WW, WH, (196, 140, 86), (170, 114, 66))
    p = Pincel(WW, WH)
    rng = random.Random(12)
    for _ in range(260):
        x, y = rng.randint(0, WW), rng.randint(0, WH)
        p.elipse((x - 3, y - 3, x + 3, y + 3), (150, 100, 58), ow=0)
    p.ret((30, 30, WW - 30, WH - 30), (0, 0, 0, 0), r=0, ow=0)
    base.alpha_composite(p.pronto())
    pos = [(80, 150), (420, 110), (740, 170), (140, 560), (500, 520), (820, 600), (90, 980), (450, 940), (780, 1000)]
    pontos = []
    for i, ph in enumerate(fotos[:len(pos)]):
        x, y = pos[i]
        im = polaroid(fc, ph, "", 240)
        im = im.rotate(rng.uniform(-8, 8), expand=True, resample=Image.BICUBIC)
        base.alpha_composite(im, (x, y))
        pontos.append((x + im.width // 2, y + 14))
    d = ImageDraw.Draw(base)
    for a, b in zip(pontos, pontos[1:] + pontos[:1]):
        d.line((a[0], a[1], b[0], b[1]), fill=(200, 40, 50, 255), width=4)
    for x, y in pontos:
        d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(230, 60, 70, 255), outline=(120, 20, 30, 255), width=3)
    return base


# ---------------------------------------------------------------- hospital
def quarto_hospital(fc, alarme=False):
    k = ("quarto", alarme)
    if k in _C:
        return _C[k]
    base = gradiente(WW, WH, (200, 226, 236), (170, 204, 218))
    p = Pincel(WW, WH)
    p.ret((-20, 1500, WW + 20, WH + 20), (150, 186, 196), r=0, ow=0)
    p.ret((70, 160, 500, 420), (210, 236, 246), r=10, ow=8)                     # janela com persiana
    for y in range(190, 410, 36):
        p.ret((80, y, 490, y + 14), (176, 204, 218), r=2, ow=0)
    p.ret((620, 300, 1000, 640), (28, 34, 44), r=14, ow=8)                       # monitor
    p.ret((640, 320, 980, 620), (12, 24, 20), r=6, ow=0)
    p.ret((700, 640, 720, 1300), (150, 156, 166), r=4)                           # suporte de soro
    p.ret((660, 720, 760, 860), (210, 236, 250), r=14, ow=6)
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    pts = [(650 + i * 6, 470 + (-70 * math.sin((i % 36) / 36 * math.pi * 2) if (i % 36) in range(14, 20) else 0))
           for i in range(56)]
    d.line(pts, fill=(255, 70, 70, 255) if alarme else (90, 240, 140, 255), width=6)
    base.alpha_composite(brilho((900, 700), (200, 230, 255), 420, 0.3), (90, 250))
    if alarme:
        base.alpha_composite(Image.new("RGBA", (WW, WH), (220, 30, 40, 60)))
    _C[k] = base
    return base


def cama_hospital(w=900):
    k = ("cama", w)
    if k not in _C:
        p = Pincel(900, 420)
        p.ret((20, 210, 880, 300), (232, 240, 248), r=26)                       # colchão/cobertor
        p.ret((20, 280, 880, 340), (140, 170, 188), r=12)
        p.ret((10, 90, 60, 340), (170, 182, 196), r=10)                          # cabeceira
        p.ret((840, 150, 890, 340), (170, 182, 196), r=10)
        for x in (60, 820):
            p.ret((x - 12, 340, x + 12, 410), (90, 96, 108), r=4)
        p.ret((70, 180, 230, 250), (246, 250, 255), r=26)                        # travesseiro
        img = p.pronto()
        _C[k] = img if w == 900 else img.resize((w, int(420 * w / 900)), Image.BICUBIC)
    return _C[k]


def centro_cirurgico(fc):
    k = "cc"
    if k in _C:
        return _C[k]
    base = gradiente(WW, WH, (150, 196, 196), (112, 160, 164))
    p = Pincel(WW, WH)
    p.ret((-20, 1500, WW + 20, WH + 20), (92, 138, 142), r=0, ow=0)
    for cx in (360, 720):                                                       # focos de luz
        p.elipse((cx - 150, 180, cx + 150, 320), (240, 246, 250), ow=8)
        p.ret((cx - 8, 0, cx + 8, 190), (170, 176, 186), r=4)
    p.ret((120, 1180, 960, 1260), (220, 232, 240), r=14)                         # mesa cirúrgica
    p.ret((200, 1260, 230, 1520), (140, 150, 162), r=4)
    p.ret((730, 1260, 760, 1520), (140, 150, 162), r=4)
    p.ret((60, 520, 330, 900), (30, 36, 46), r=12, ow=8)                         # monitor
    p.ret((80, 540, 310, 860), (12, 24, 20), r=4, ow=0)
    base.alpha_composite(p.pronto())
    for cx in (360, 720):
        base.alpha_composite(brilho((700, 700), (255, 255, 240), 340, 0.55), (cx - 350, 0))
    _C[k] = base
    return base


def corredor(fc, placa="UTI"):
    k = ("corr", placa)
    if k in _C:
        return _C[k]
    base = gradiente(WW, WH, (206, 226, 234), (176, 204, 214))
    p = Pincel(WW, WH)
    p.ret((-20, 1400, WW + 20, WH + 20), (150, 184, 194), r=0, ow=0)
    p.ret((340, 380, 740, 1400), (116, 134, 150), r=8, ow=8)                     # porta dupla
    p.linha([(540, 380), (540, 1400)], w=8)
    p.ret((380, 460, 500, 700), (170, 210, 236), r=6, ow=5)
    p.ret((580, 460, 700, 700), (170, 210, 236), r=6, ow=5)
    p.ret((380, 280, 700, 350), (46, 120, 190), r=10, ow=6)
    p.ret((-20, 1240, WW + 20, 1262), (120, 156, 168), r=0, ow=0)               # corrimão
    base.alpha_composite(p.pronto())
    d = ImageDraw.Draw(base)
    f = vc.fonte(fc, 44)
    d.text((540 - f.getlength(placa) / 2, 288), placa, font=f, fill=(255, 255, 255))
    _C[k] = base
    return base


# ---------------------------------------------------------------- mapa e objetos
BRASIL = [(300, 160), (360, 100), (440, 120), (520, 100), (600, 50), (690, 120), (790, 200), (900, 240), (990, 310),
          (1010, 400), (960, 500), (900, 590), (860, 690), (820, 790), (790, 890), (760, 980), (690, 1060),
          (610, 1120), (550, 1190), (500, 1290), (430, 1240), (400, 1140), (440, 1030), (390, 950), (320, 880),
          (270, 790), (190, 730), (120, 650), (150, 550), (220, 470), (240, 380), (190, 300), (260, 220)]


def mapa_brasil(fc, pin=None, w=860):
    p = Pincel(1080, 1300)
    p.ret((10, 10, 1070, 1290), (150, 200, 232), r=30, ow=10)
    p.poli([(x * 0.92 + 20, y * 0.9 + 70) for x, y in BRASIL], (112, 190, 120), ow=8)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 46)
    d.text((540 - f.getlength("BRASIL") / 2, 24), "BRASIL", font=f, fill=(255, 255, 255))
    if pin:
        x, y = int(pin[0] * 1.0), int(pin[1] * 1.0)
        d.line((x, y, x, y - 70), fill=(230, 50, 60, 255), width=10)
        d.ellipse((x - 22, y - 96, x + 22, y - 52), fill=(230, 50, 60, 255), outline=(120, 20, 30, 255), width=5)
    return img if w == 1080 else img.resize((w, int(1300 * w / 1080)), Image.BICUBIC)


def enceradeira(w=420):
    p = Pincel(420, 520)
    p.ret((190, 20, 230, 340), (90, 96, 108), r=8)                                # cabo
    p.ret((150, 10, 270, 50), (60, 64, 74), r=10)
    p.elipse((30, 340, 390, 480), (230, 150, 50), ow=8)                           # disco
    p.elipse((70, 370, 350, 450), (180, 110, 30), ow=0)
    p.ret((170, 300, 250, 350), (150, 156, 168), r=10)
    img = p.pronto()
    return img if w == 420 else img.resize((w, int(520 * w / 420)), Image.BICUBIC)


def tomada(plugada=True, w=520):
    p = Pincel(520, 420)
    p.ret((150, 60, 370, 280), (240, 238, 226), r=22, ow=8)
    for x in (210, 310):
        p.ret((x - 12, 120, x + 12, 190), (40, 40, 48), r=4, ow=0)
        p.ret((x - 12, 190, x + 12, 226), (40, 40, 48), r=4, ow=0)
    img = p.pronto()
    q = Pincel(520, 420)
    if plugada:
        q.ret((190, 90, 330, 230), (46, 50, 62), r=14)
        q.ret((240, 220, 280, 400), (46, 50, 62), r=10)
    else:
        q.ret((410, 200, 520, 330), (46, 50, 62), r=14)
        q.linha([(465, 330), (490, 410)], fill=(46, 50, 62), w=22)
    img.alpha_composite(q.pronto())
    return img if w == 520 else img.resize((w, int(420 * w / 520)), Image.BICUBIC)


def respirador(t, plugada=True, w=620):
    p = Pincel(620, 700)
    p.ret((60, 40, 560, 520), (214, 224, 232), r=26, ow=8)
    p.ret((100, 80, 520, 330), (14, 28, 24), r=14, ow=0)
    p.ret((260, 520, 360, 600), (160, 170, 180), r=8)
    p.linha([(310, 600), (330, 690)], fill=(46, 50, 62), w=20)
    img = p.pronto()
    d = ImageDraw.Draw(img)
    if plugada:
        pts = [(110 + i * 8, 205 + 60 * math.sin((i + t * 14) / 3.0) * (0.5 + 0.5 * math.sin(i / 7))) for i in range(50)]
        d.line(pts, fill=(90, 240, 150, 255), width=7)
    else:
        d.line((110, 205, 510, 205), fill=(255, 70, 70, 255), width=7)
    return img if w == 620 else img.resize((w, int(700 * w / 620)), Image.BICUBIC)


def coracao_partido(w=420, pulso=0.0):
    p = Pincel(420, 420)
    s = 1 + 0.08 * pulso
    p.elipse((40, 50, 220, 230), (230, 50, 70), ow=8)
    p.elipse((200, 50, 380, 230), (230, 50, 70), ow=8)
    p.poli([(54, 190), (366, 190), (210, 390)], (230, 50, 70), ow=8)
    p.elipse((54, 70, 210, 220), (230, 50, 70), ow=0)
    p.elipse((210, 70, 366, 220), (230, 50, 70), ow=0)
    p.linha([(210, 80), (190, 170), (230, 230), (200, 330)], fill=(250, 240, 240), w=10)
    img = p.pronto()
    nw = int(w * s)
    return img.resize((nw, nw), Image.BICUBIC)
