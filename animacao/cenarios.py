#!/usr/bin/env python3
"""
Biblioteca de cenários novos (para cada vídeo abrir num lugar diferente, sem repetir a rua).
Todos no tamanho do mundo (WW x WH) e com o chão por volta de y≈1450–1800.
"""
import math
import random

from PIL import Image

from gerar_video import WW, WH, Pincel, gradiente, brilho


def _chao(p, y, cor):
    p.ret((-20, y, WW + 20, WH + 20), cor, r=0)


def praia():
    base = gradiente(WW, WH, (120, 200, 245), (200, 235, 250))
    p = Pincel(WW, WH)
    p.elipse((760, 180, 940, 360), (255, 230, 120), ow=0)
    p.ret((-20, 1000, WW + 20, 1300), (60, 150, 210), r=0, ow=0)
    for x in range(-40, WW, 160):
        p.arco((x, 1030, x + 160, 1090), 200, 340, fill=(230, 245, 255), w=6)
    p.ret((-20, 1280, WW + 20, WH + 20), (245, 220, 160), r=0)
    p.ret((150, 820, 175, 1500), (200, 200, 200), r=6)                       # guarda-sol
    p.chord((20, 760, 310, 960), 180, 360, (240, 90, 90))
    p.elipse((700, 1560, 980, 1640), (240, 120, 160))                          # toalha
    base.alpha_composite(p.pronto())
    return base


def feira():
    base = gradiente(WW, WH, (150, 205, 240), (230, 240, 250))
    p = Pincel(WW, WH)
    _chao(p, 1450, (170, 160, 150))
    for i, x in enumerate((-40, 360, 760)):
        cor = [(240, 90, 80), (60, 160, 90), (250, 190, 60)][i]
        p.ret((x + 20, 900, x + 340, 1440), (190, 140, 90), r=4)
        p.poli([(x, 900), (x + 360, 900), (x + 330, 760), (x + 30, 760)], cor)
        for k in range(5):
            p.linha([(x + 40 + k * 64, 760), (x + 36 + k * 64, 900)], fill=(255, 255, 255), w=10)
        for k in range(6):
            fx = x + 60 + (k % 3) * 90
            fy = 1080 + (k // 3) * 80
            p.elipse((fx, fy, fx + 70, fy + 70), random.choice([(250, 150, 40), (220, 50, 60), (120, 200, 80)]))
    base.alpha_composite(p.pronto())
    return base


def onibus_dentro():
    base = gradiente(WW, WH, (225, 225, 220), (200, 200, 195))
    p = Pincel(WW, WH)
    for i in range(3):
        x = 60 + i * 340
        p.ret((x, 300, x + 300, 640), (140, 200, 235), r=20, ow=10)
        p.linha([(x + 40, 420), (x + 240, 420)], fill=(110, 170, 200), w=40)
    p.linha([(-20, 220), (WW + 20, 220)], fill=(180, 180, 185), w=16)
    for x in range(80, WW, 200):
        p.linha([(x, 220), (x, 300)], fill=(120, 120, 130), w=6)
        p.elipse((x - 22, 290, x + 22, 334), (0, 0, 0, 0), ow=0)
        p.arco((x - 22, 290, x + 22, 334), 0, 360, fill=(240, 200, 60), w=8)
    _chao(p, 1500, (110, 110, 120))
    for x in (0, 760):
        p.ret((x, 1180, x + 320, 1500), (60, 90, 160), r=24)
        p.ret((x, 980, x + 320, 1200), (70, 100, 175), r=24)
    base.alpha_composite(p.pronto())
    return base


def sala_aula():
    base = gradiente(WW, WH, (240, 235, 210), (225, 220, 195))
    p = Pincel(WW, WH)
    p.ret((140, 260, 940, 760), (50, 90, 70), r=12, ow=14)
    p.ret((140, 760, 940, 790), (180, 140, 90), r=4)
    p.elipse((860, 120, 960, 220), (250, 250, 250), ow=8)
    p.linha([(910, 170), (910, 135)], w=6)
    p.linha([(910, 170), (935, 175)], w=6)
    _chao(p, 1480, (190, 150, 110))
    for x in (60, 620):
        p.ret((x, 1500, x + 400, 1560), (200, 150, 100), r=10)
        p.ret((x + 30, 1560, x + 60, 1800), (120, 120, 130), r=6)
        p.ret((x + 340, 1560, x + 370, 1800), (120, 120, 130), r=6)
    base.alpha_composite(p.pronto())
    return base


def campo_futebol():
    base = gradiente(WW, WH, (120, 190, 245), (190, 225, 250))
    p = Pincel(WW, WH)
    p.ret((-20, 1100, WW + 20, WH + 20), (90, 170, 80), r=0)
    for k in range(6):
        p.ret((-20, 1100 + k * 140, WW + 20, 1170 + k * 140), (100, 180, 90), r=0, ow=0)
    p.linha([(300, 1100), (300, 760), (780, 760), (780, 1100)], fill=(250, 250, 250), w=18)
    for x in range(310, 780, 40):
        p.linha([(x, 770), (x, 1100)], fill=(230, 230, 230), w=3)
    p.ret((-20, 760, 200, 1100), (200, 200, 205), r=0)                       # arquibancada
    base.alpha_composite(p.pronto())
    return base


def padaria():
    base = gradiente(WW, WH, (250, 225, 190), (240, 210, 170))
    p = Pincel(WW, WH)
    for y in (300, 520):
        p.ret((60, y + 140, 1020, y + 170), (160, 100, 60), r=6)
        for x in range(90, 1000, 110):
            p.elipse((x, y + 60, x + 100, y + 145), (220, 160, 80), ow=6)
            p.arco((x + 25, y + 80, x + 75, y + 120), 200, 340, fill=(180, 120, 60), w=5)
    p.ret((-20, 1250, WW + 20, 1480), (190, 130, 80), r=10)                   # balcão
    p.ret((60, 1110, 1020, 1260), (200, 235, 250), r=14, ow=8)               # vitrine
    _chao(p, 1480, (210, 200, 190))
    base.alpha_composite(p.pronto())
    return base


def sitio():
    base = gradiente(WW, WH, (250, 200, 140), (180, 220, 240))
    p = Pincel(WW, WH)
    p.elipse((-300, 900, 700, 1500), (130, 180, 90), ow=0)
    p.elipse((300, 950, 1400, 1500), (110, 165, 80), ow=0)
    p.ret((560, 820, 960, 1200), (230, 220, 200), r=4)                       # casinha
    p.poli([(520, 830), (760, 640), (1000, 830)], (180, 80, 60))
    p.ret((720, 1020, 800, 1200), (120, 80, 55), r=6)
    for x in range(-20, WW, 90):                                              # cerca
        p.ret((x, 1360, x + 24, 1500), (170, 120, 80), r=4, ow=5)
    p.linha([(-20, 1400), (WW + 20, 1400)], fill=(170, 120, 80), w=14)
    _chao(p, 1480, (150, 120, 80))
    base.alpha_composite(p.pronto())
    return base


def morro_noite():
    base = gradiente(WW, WH, (30, 30, 70), (90, 60, 110))
    p = Pincel(WW, WH)
    p.elipse((120, 160, 240, 280), (250, 240, 200), ow=0)
    rng = random.Random(3)
    for fila in range(6):
        y = 700 + fila * 120
        for k in range(8):
            x = k * 140 - (fila % 2) * 70 + rng.randint(-10, 10)
            cor = rng.choice([(200, 120, 100), (230, 200, 140), (150, 170, 200), (220, 150, 170)])
            p.ret((x, y, x + 130, y + 120), cor, r=4, ow=5)
            if rng.random() < 0.7:
                p.ret((x + 40, y + 30, x + 80, y + 70), (255, 220, 120), r=4, ow=4)
    _chao(p, 1460, (90, 85, 95))
    base.alpha_composite(p.pronto())
    base.alpha_composite(brilho((1080, 600), (255, 200, 120), 500, 0.25), (0, 700))
    return base


def mercado():
    base = gradiente(WW, WH, (240, 245, 245), (225, 230, 230))
    p = Pincel(WW, WH)
    for col in range(2):
        x0 = 40 + col * 540
        for k in range(4):
            y = 400 + k * 230
            p.ret((x0, y + 170, x0 + 460, y + 195), (160, 160, 170), r=4)
            for j in range(6):
                cor = random.choice([(230, 70, 70), (250, 200, 60), (70, 150, 230), (120, 200, 110)])
                p.ret((x0 + 15 + j * 74, y + 50, x0 + 75 + j * 74, y + 170), cor, r=6, ow=5)
    p.ret((-20, 120, WW + 20, 200), (230, 60, 60), r=0)
    _chao(p, 1480, (200, 205, 210))
    base.alpha_composite(p.pronto())
    return base


def rodoviaria():
    base = gradiente(WW, WH, (180, 200, 220), (210, 220, 230))
    p = Pincel(WW, WH)
    p.ret((80, 240, 1000, 420), (30, 35, 50), r=12, ow=10)                   # painel de horários
    for k in range(3):
        p.ret((110, 270 + k * 48, 700, 300 + k * 48), (250, 200, 60), r=4, ow=0)
        p.ret((760, 270 + k * 48, 970, 300 + k * 48), (120, 230, 140), r=4, ow=0)
    p.ret((-20, 820, WW + 20, 1300), (240, 240, 245), r=0)
    p.ret((60, 900, 1020, 1280), (60, 130, 200), r=30)                        # ônibus
    for x in range(110, 980, 150):
        p.ret((x, 950, x + 120, 1080), (200, 230, 250), r=10, ow=6)
    for x in (230, 850):
        p.elipse((x - 70, 1220, x + 70, 1360), (40, 40, 45))
    _chao(p, 1330, (160, 160, 165))
    base.alpha_composite(p.pronto())
    return base


CENARIOS = dict(praia=praia, feira=feira, onibus=onibus_dentro, sala_aula=sala_aula, campo=campo_futebol,
                padaria=padaria, sitio=sitio, morro=morro_noite, mercado=mercado, rodoviaria=rodoviaria)
