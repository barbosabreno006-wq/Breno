#!/usr/bin/env python3
"""Props de "O Apagador": o monstro (altíssimo, sem olhos, boca costurada, mãos enormes), cama, toco de lápis,
relógio da praça, lua, desenho sendo apagado."""
import math

from PIL import Image, ImageDraw

import video_carta as vc
from gerar_video import Pincel, brilho

_C = {}


def apagador(h=1500, boca=0.0, mao_alta=0.0):
    """O Apagador: pele cinza-azulada, cabeça lisa sem olhos, boca costurada, mãos enormes.
    mao_alta (0–1) levanta a mão direita até a altura da cabeça."""
    k = ("apag", h, round(mao_alta * 4) / 4)
    if k in _C:
        return _C[k]
    W, H = 520, 1500
    p = Pincel(W, H)
    pele, esc = (112, 120, 150), (62, 68, 92)
    p.capsula((200, 940), (186, 1470), 30, esc)
    p.capsula((300, 940), (314, 1470), 30, esc)
    p.ret((150, 1450, 225, 1490), esc, r=10)
    p.ret((280, 1450, 360, 1490), esc, r=10)
    p.poli([(150, 380), (370, 380), (330, 970), (190, 970)], (70, 76, 104))      # sobretudo
    p.capsula((240, 300), (260, 390), 40, pele)
    # braço esquerdo caído
    p.capsula((160, 400), (80, 820), 32, (70, 76, 104))
    p.capsula((80, 820), (70, 1130), 28, pele)
    p.elipse((20, 1090, 130, 1260), pele)                                          # mão enorme
    # braço direito (levanta)
    y1 = 1130 - mao_alta * 620
    x1 = 440 - mao_alta * 50
    p.capsula((360, 400), (440, 820 - mao_alta * 260), 32, (70, 76, 104))
    p.capsula((440, 820 - mao_alta * 260), (x1, y1), 28, pele)
    p.elipse((x1 - 62, y1 - 40, x1 + 62, y1 + 160), pele)
    # cabeça lisa, sem olhos
    p.elipse((150, 30, 370, 340), pele)
    # boca costurada
    p.linha([(200, 250), (320, 250)], fill=(30, 20, 30), w=8)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    for i in range(7):
        x = 205 + i * 18
        d.line((x, 238, x + 5, 264), fill=(30, 20, 30, 255), width=5)
    # olheiras fundas (sem olhos)
    d.ellipse((190, 140, 250, 190), fill=(80, 86, 112, 255))
    d.ellipse((270, 140, 330, 190), fill=(80, 86, 112, 255))
    if h != H:
        im = im.resize((int(W * h / H), h), Image.BICUBIC)
    _C[k] = im
    return im


def cabeca(w=720):
    im = apagador(1500)
    return im.crop((120, 10, 400, 360)).resize((w, int(w * 350 / 280)), Image.BICUBIC)


def mao(w=700, flip=False):
    """Mão enorme aberta (para passar na cabeça das pessoas)."""
    p = Pincel(420, 520)
    pele = (112, 120, 150)
    p.elipse((90, 220, 330, 480), pele)
    for i in range(5):
        x = 90 + i * 52
        p.capsula((x + 22, 260), (x + 14 + i * 4 - 8, 20 + abs(i - 2) * 26), 38, pele)
    im = p.pronto().resize((w, int(w * 520 / 420)), Image.BICUBIC)
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def cama(w=900, cor=(110, 150, 220)):
    """Cama vista de frente: colchão, cobertor e travesseiro (desenhar na frente do personagem)."""
    k = ("cama", w, cor)
    if k not in _C:
        p = Pincel(900, 420)
        p.ret((30, 200, 870, 400), (120, 84, 60), r=14)                 # estrado
        p.ret((10, 90, 890, 330), cor, r=40)                            # cobertor
        p.ret((10, 90, 890, 150), tuple(min(255, c + 36) for c in cor), r=30)
        p.ret((40, 10, 320, 120), (246, 244, 250), r=36)                # travesseiro
        _C[k] = p.pronto().resize((w, int(420 * w / 900)), Image.BICUBIC)
    return _C[k]


def lapis(w=320, ang=0.0):
    p = Pincel(360, 90)
    p.ret((20, 24, 270, 66), (250, 200, 60), r=4)
    p.poli([(270, 24), (340, 45), (270, 66)], (232, 190, 140))
    p.poli([(318, 38), (340, 45), (318, 52)], (50, 50, 60), ow=2)
    p.ret((10, 24, 46, 66), (240, 130, 150), r=6)
    im = p.pronto().resize((w, int(90 * w / 360)), Image.BICUBIC)
    return im.rotate(ang, expand=True, resample=Image.BICUBIC) if ang else im


def lua(m, x, y, r=90):
    m.alpha_composite(brilho((r * 5, r * 5), (255, 244, 200), r * 2.4, 0.55), (int(x - r * 2.5), int(y - r * 2.5)))
    d = ImageDraw.Draw(m)
    d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 246, 210, 255), outline=(40, 40, 60, 255), width=6)
    d.ellipse((x + r * 0.2, y - r * 0.5, x + r * 0.6, y - r * 0.1), fill=(236, 226, 190, 255))


def relogio_torre(fc, hh=12, mm=0, w=800):
    """Relógio grande (mostra a hora)."""
    p = Pincel(800, 800)
    p.elipse((20, 20, 780, 780), (250, 246, 232), ow=14)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    f = vc.fonte(fc, 70)
    for n in range(1, 13):
        a = n / 12 * 2 * math.pi
        tx, ty = 400 + math.sin(a) * 300, 400 - math.cos(a) * 300
        s = str(n)
        d.text((tx - f.getlength(s) / 2, ty - 42), s, font=f, fill=(40, 40, 50))
    ah = (hh % 12 + mm / 60) / 12 * 2 * math.pi
    am = mm / 60 * 2 * math.pi
    d.line((400, 400, 400 + math.sin(ah) * 190, 400 - math.cos(ah) * 190), fill=(30, 30, 40), width=22)
    d.line((400, 400, 400 + math.sin(am) * 290, 400 - math.cos(am) * 290), fill=(30, 30, 40), width=14)
    d.ellipse((380, 380, 420, 420), fill=(200, 50, 60))
    return im if w == 800 else im.resize((w, w), Image.BICUBIC)


def rabisco_rosto(w=640, apagado=0.0):
    """Folha com desenho de um rosto sorrindo sendo apagado da esquerda para a direita."""
    p = Pincel(640, 640)
    p.ret((10, 10, 630, 630), (250, 246, 236), r=14)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    d.ellipse((140, 130, 500, 490), outline=(40, 40, 60, 255), width=10)
    d.ellipse((235, 250, 275, 300), fill=(40, 40, 60, 255))
    d.ellipse((365, 250, 405, 300), fill=(40, 40, 60, 255))
    d.arc((220, 300, 420, 430), 20, 160, fill=(40, 40, 60, 255), width=10)
    x = 10 + 620 * max(0, min(1, apagado))
    if apagado > 0:
        d.rectangle((10, 20, x, 620), fill=(250, 246, 236, 255))
        d.rounded_rectangle((x - 40, 200, x + 60, 440), radius=14, fill=(240, 130, 150, 255), outline=(40, 40, 60, 255),
                            width=6)
    return im if w == 640 else im.resize((w, w), Image.BICUBIC)
