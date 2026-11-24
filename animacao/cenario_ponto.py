#!/usr/bin/env python3
"""Cenários de "O Ponto do Marcelo": garagem de ônibus, relógio de ponto, cartão, vestiário, escritório do RH,
estacionamento, folha de ponto, plano de saúde, ônibus."""
import math

from PIL import Image, ImageDraw

import video_carta as vc
import cenario_escola as cs
from gerar_video import WW, WH, Pincel, gradiente, brilho

_C = {}


def _piso(p, y=1500, cor=(90, 94, 106)):
    p.ret((-20, y, WW + 20, WH + 20), cor, r=0, ow=0)


def onibus(w=900, cor=(240, 190, 60)):
    k = ("bus", w, cor)
    if k not in _C:
        p = Pincel(900, 440)
        p.ret((20, 60, 880, 360), cor, r=40)
        p.ret((20, 220, 880, 260), (60, 60, 70), r=0, ow=0)
        for i in range(6):
            p.ret((60 + i * 135, 90, 170 + i * 135, 190), (176, 216, 240), r=12)
        p.elipse((120, 310, 250, 440), (36, 36, 44))
        p.elipse((620, 310, 750, 440), (36, 36, 44))
        p.ret((800, 90, 860, 200), (150, 200, 230), r=8)
        _C[k] = p.pronto().resize((w, int(440 * w / 900)), Image.BICUBIC)
    return _C[k]


def garagem(fc, hora="madrugada", box=3):
    """Interior da garagem: ônibus ao fundo, placa do box, piso de cimento."""
    k = ("gar", hora, box)
    if k in _C:
        return _C[k]
    topo, baixo = ((40, 48, 90), (22, 26, 50)) if hora == "madrugada" else ((200, 210, 226), (160, 172, 190))
    img = gradiente(WW, WH, topo, baixo)
    p = Pincel(WW, WH)
    _piso(p, 1500, (70, 74, 88) if hora == "madrugada" else (130, 134, 146))
    p.ret((60, 360, 1020, 1000), (60, 68, 100) if hora == "madrugada" else (176, 184, 200), r=6, ow=6)
    p.ret((380, 300, 700, 400), (230, 190, 60), r=10)
    img.alpha_composite(p.pronto())
    img.alpha_composite(onibus(780, (230, 180, 60) if hora != "madrugada" else (170, 130, 50)), (150, 1000))
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 56)
    s = f"BOX {box}"
    d.text((540 - f.getlength(s) / 2, 316), s, font=f, fill=(40, 40, 50))
    img.alpha_composite(brilho((900, 400), (255, 240, 180), 320, 0.4 if hora == "madrugada" else 0.2), (90, 160))
    _C[k] = img
    return img


def portao(fc, hora="madrugada"):
    k = ("port", hora)
    if k in _C:
        return _C[k]
    img = gradiente(WW, WH, (30, 36, 76), (14, 16, 36)) if hora == "madrugada" else gradiente(WW, WH, (190, 214, 240), (230, 236, 244))
    p = Pincel(WW, WH)
    _piso(p, 1540, (60, 64, 76) if hora == "madrugada" else (150, 154, 166))
    p.ret((80, 560, 1000, 1540), (90, 96, 124), r=8)
    p.poli([(60, 570), (540, 360), (1020, 570)], (70, 76, 104))
    p.ret((380, 1000, 700, 1540), (50, 54, 70), r=6, ow=8)
    p.ret((200, 440, 880, 520), (230, 190, 60), r=8)
    img.alpha_composite(p.pronto())
    d = ImageDraw.Draw(img)
    f = vc.fonte(fc, 48)
    d.text((540 - f.getlength("GARAGEM CENTRAL") / 2, 450), "GARAGEM CENTRAL", font=f, fill=(40, 40, 50))
    img.alpha_composite(brilho((500, 300), (255, 240, 180), 200, 0.5), (290, 870))
    _C[k] = img
    return img


def relogio_ponto(fc, texto="05:00", w=620, verde=True):
    p = Pincel(620, 820)
    p.ret((10, 10, 610, 810), (216, 220, 228), r=40)
    p.ret((60, 60, 560, 260), (22, 36, 28), r=20)
    p.ret((200, 340, 420, 420), (70, 74, 86), r=10)                       # fenda do cartão
    p.elipse((270, 520, 350, 600), (80, 210, 120) if verde else (220, 70, 70), ow=6)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    f = vc.fonte(fc, 120)
    d.text((310 - f.getlength(texto) / 2, 84), texto, font=f, fill=(120, 255, 150))
    f2 = vc.fonte(fc, 34)
    d.text((310 - f2.getlength("PONTO") / 2, 690), "PONTO", font=f2, fill=(80, 84, 96))
    return im if w == 620 else im.resize((w, int(820 * w / 620)), Image.BICUBIC)


def cartao(fc, nome="MARCELO SOUZA", mat="Mat. 0417", w=640):
    p = Pincel(640, 400)
    p.ret((10, 10, 630, 390), (250, 250, 252), r=24)
    p.ret((10, 10, 630, 90), (40, 70, 150), r=24)
    p.ret((40, 120, 220, 330), (214, 190, 160), r=10)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    f1, f2, f3 = vc.fonte(fc, 34), vc.fonte(fc, 36), vc.fonte(fc, 28)
    d.text((320 - f1.getlength("GARAGEM CENTRAL") / 2, 28), "GARAGEM CENTRAL", font=f1, fill=(255, 255, 255))
    d.text((250, 160), nome, font=f2, fill=(40, 40, 50))
    d.text((250, 220), mat, font=f3, fill=(100, 100, 110))
    d.ellipse((90, 150, 170, 230), fill=(236, 186, 150, 255), outline=(40, 40, 50, 255), width=4)
    d.rectangle((70, 245, 190, 320), fill=(60, 100, 190, 255))
    return im if w == 640 else im.resize((w, int(400 * w / 640)), Image.BICUBIC)


def vestiario(fc):
    if "vest" in _C:
        return _C["vest"]
    img = gradiente(WW, WH, (206, 214, 226), (170, 180, 196))
    p = Pincel(WW, WH)
    _piso(p, 1500, (120, 124, 140))
    for i in range(7):
        p.ret((20 + i * 150, 520, 150 + i * 150, 1500), (70, 110, 180), r=6)
        p.ret((40 + i * 150, 580, 130 + i * 150, 640), (50, 84, 140), r=3, ow=3)
    img.alpha_composite(p.pronto())
    _C["vest"] = img
    return img


def escritorio(fc, noite=False):
    k = ("rh", noite)
    if k in _C:
        return _C[k]
    img = gradiente(WW, WH, (240, 240, 232), (214, 216, 210)) if not noite else gradiente(WW, WH, (50, 56, 90), (28, 30, 56))
    p = Pincel(WW, WH)
    _piso(p, 1500, (150, 150, 160))
    p.ret((60, 360, 340, 640), (230, 236, 244), r=6, ow=6)
    p.ret((220, 1180, 1000, 1500), (150, 108, 76), r=8)                               # mesa
    p.ret((420, 880, 800, 1150), (30, 34, 48), r=14)                                   # monitor
    p.ret((440, 900, 780, 1130), (190, 226, 200), r=6, ow=0)
    for i in range(6):
        p.ret((470, 930 + i * 32, 750, 946 + i * 32), (90, 150, 110), r=2, ow=0)
    p.ret((580, 1150, 640, 1180), (60, 64, 76), r=4)
    img.alpha_composite(p.pronto())
    _C[k] = img
    return img


def estacionamento(fc):
    if "estac" in _C:
        return _C["estac"]
    img = gradiente(WW, WH, (20, 24, 58), (10, 12, 28))
    p = Pincel(WW, WH)
    _piso(p, 1380, (46, 50, 62))
    for x in range(60, 1040, 220):
        p.ret((x, 1560, x + 20, 1800), (220, 220, 230), r=2, ow=0)
    p.ret((780, 560, 800, 1380), (70, 74, 90), r=2)
    img.alpha_composite(p.pronto())
    img.alpha_composite(brilho((600, 600), (255, 230, 150), 260, 0.5), (580, 400))
    _C["estac"] = img
    return img


def carro(w=820):
    if ("carro", w) not in _C:
        p = Pincel(820, 400)
        p.ret((20, 160, 800, 330), (200, 60, 70), r=40)
        p.poli([(160, 160), (260, 40), (560, 40), (680, 160)], (216, 70, 80))
        p.poli([(200, 150), (280, 64), (400, 64), (400, 150)], (176, 216, 240))
        p.poli([(420, 150), (420, 64), (540, 64), (620, 150)], (176, 216, 240))
        p.elipse((100, 280, 240, 400), (36, 36, 44))
        p.elipse((580, 280, 720, 400), (36, 36, 44))
        _C[("carro", w)] = p.pronto().resize((w, int(400 * w / 820)), Image.BICUBIC)
    return _C[("carro", w)]


def folha_ponto(fc, meses=8, w=720):
    p = Pincel(720, 940)
    p.ret((10, 10, 710, 930), (250, 248, 240), r=12)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    f1, f2 = vc.fonte(fc, 44), vc.fonte(fc, 28)
    d.text((360 - f1.getlength("FOLHA DE PONTO") / 2, 40), "FOLHA DE PONTO", font=f1, fill=(40, 40, 50))
    d.text((60, 110), "MARCELO SOUZA   Mat. 0417", font=f2, fill=(80, 80, 90))
    for i in range(min(12, meses)):
        y = 170 + i * 58
        d.text((60, y), f"mês {i + 1:02d}", font=f2, fill=(90, 90, 100))
        d.text((300, y), "05:00  OK", font=f2, fill=(40, 150, 80))
        d.text((510, y), "faltas 0", font=f2, fill=(40, 150, 80))
    return im if w == 720 else im.resize((w, int(940 * w / 720)), Image.BICUBIC)


def plano(fc, ativo=True, w=640):
    p = Pincel(640, 400)
    p.ret((10, 10, 630, 390), (60, 150, 210), r=24)
    p.ret((10, 280, 630, 390), (40, 110, 170), r=24, ow=0)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    f1, f2 = vc.fonte(fc, 44), vc.fonte(fc, 30)
    d.text((320 - f1.getlength("PLANO DE SAÚDE") / 2, 70), "PLANO DE SAÚDE", font=f1, fill=(255, 255, 255))
    d.text((40, 180), "Titular: MARCELO SOUZA", font=f2, fill=(255, 255, 255))
    d.text((40, 230), "Dependente: BIA", font=f2, fill=(255, 255, 255))
    cor = (60, 220, 120, 255) if ativo else (230, 60, 70, 255)
    d.ellipse((470, 270, 600, 380), outline=cor, width=12)
    if ativo:
        d.line((496, 326, 530, 356), fill=cor, width=14)
        d.line((530, 356, 580, 294), fill=cor, width=14)
    else:
        d.line((500, 296, 570, 356), fill=cor, width=14)
        d.line((570, 296, 500, 356), fill=cor, width=14)
    return im if w == 640 else im.resize((w, int(400 * w / 640)), Image.BICUBIC)


def papel_licenca(fc, assinada=0.0, w=700):
    p = Pincel(700, 900)
    p.ret((10, 10, 690, 890), (250, 248, 240), r=12)
    im = p.pronto()
    d = ImageDraw.Draw(im)
    f1, f2 = vc.fonte(fc, 44), vc.fonte(fc, 30)
    d.text((350 - f1.getlength("LICENÇA MÉDICA") / 2, 50), "LICENÇA MÉDICA", font=f1, fill=(40, 40, 50))
    d.text((60, 140), "Retroativa a 8 meses", font=f2, fill=(90, 90, 100))
    for i in range(6):
        d.line((60, 230 + i * 56, 640, 230 + i * 56), fill=(200, 196, 186), width=3)
    n = int(60 * assinada)
    if n > 0:
        pts = [(80 + k * 9, 780 + 22 * math.sin(k * 0.5)) for k in range(n)]
        d.line(pts, fill=(30, 60, 180, 255), width=7)
    return im if w == 700 else im.resize((w, int(900 * w / 700)), Image.BICUBIC)
