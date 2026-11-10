#!/usr/bin/env python3
"""
Gerador do vídeo-demo "A Vela da Dona Cida" — no estilo dos vídeos virais
de animação 2D (cutout / vetor flat) analisados em animacao/ANALISE.md.

Tudo é desenhado por código (Pillow + numpy) e montado com ffmpeg:
  * cenários e personagens vetoriais com contorno grosso
  * animação "cutout": respiração, bob, piscada, troca de pose
  * câmera virtual: push-in lento (Ken Burns) e punch-in rápido
  * transições whip-pan com motion blur, dissolve e zoom-blur
  * legenda karaokê (palavra atual em amarelo, contorno preto, pop-in)
  * trilha e efeitos sonoros sintetizados (sem arquivos externos)

Uso:
    python3 animacao/gerar_video.py [--fonte caminho.ttf] [--saida video.mp4]
"""
import argparse
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

# --------------------------------------------------------------------------
# Configuração geral
# --------------------------------------------------------------------------
FPS = 30
OUT_W, OUT_H = 720, 1280          # saída 9:16
WW, WH = 1080, 1920               # "mundo" (1.5x da saída) p/ mover câmera
SS = 2                            # supersampling para anti-aliasing
OUTLINE = (43, 40, 58)
OW = 7                            # espessura do contorno (unidades do mundo)

random.seed(7)


def fonte_padrao():
    cands = [
        os.environ.get("FONTE_LEGENDA", ""),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for c in cands:
        if c and os.path.exists(c):
            return c
    return None


# --------------------------------------------------------------------------
# Utilidades de desenho (tudo em coordenadas do mundo, escalado por SS)
# --------------------------------------------------------------------------
class Pincel:
    """Envolve ImageDraw para desenhar com contorno grosso e supersampling."""

    def __init__(self, w, h, s=SS):
        self.s = s
        self.img = Image.new("RGBA", (int(w * s), int(h * s)), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def _b(self, box):
        return [v * self.s for v in box]

    def elipse(self, box, fill, ow=OW, outline=OUTLINE):
        if ow:
            x0, y0, x1, y1 = box
            self.d.ellipse(self._b((x0 - ow / 2, y0 - ow / 2, x1 + ow / 2, y1 + ow / 2)), fill=outline)
        self.d.ellipse(self._b(box), fill=fill)

    def ret(self, box, fill, r=0, ow=OW, outline=OUTLINE):
        if ow:
            x0, y0, x1, y1 = box
            self.d.rounded_rectangle(self._b((x0 - ow / 2, y0 - ow / 2, x1 + ow / 2, y1 + ow / 2)),
                                     radius=(r + ow / 2) * self.s, fill=outline)
        self.d.rounded_rectangle(self._b(box), radius=r * self.s, fill=fill)

    def poli(self, pts, fill, ow=OW, outline=OUTLINE):
        p = [(x * self.s, y * self.s) for x, y in pts]
        if ow:
            self.d.line(p + [p[0]], fill=outline, width=int(ow * self.s * 1.6), joint="curve")
        self.d.polygon(p, fill=fill)

    def capsula(self, p0, p1, w, fill, ow=OW, outline=OUTLINE):
        """Membro arredondado (braço/perna) de p0 a p1."""
        for col, ww in ((outline, w + ow * 2), (fill, w)):
            if col is outline and not ow:
                continue
            a = (p0[0] * self.s, p0[1] * self.s)
            b = (p1[0] * self.s, p1[1] * self.s)
            self.d.line([a, b], fill=col, width=int(ww * self.s))
            for (x, y) in (a, b):
                r = ww * self.s / 2
                self.d.ellipse((x - r, y - r, x + r, y + r), fill=col)

    def linha(self, pts, fill=OUTLINE, w=OW):
        p = [(x * self.s, y * self.s) for x, y in pts]
        self.d.line(p, fill=fill, width=int(w * self.s), joint="curve")
        r = w * self.s / 2
        for (x, y) in (p[0], p[-1]):
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=fill)

    def arco(self, box, a0, a1, fill=OUTLINE, w=OW):
        self.d.arc(self._b(box), a0, a1, fill=fill, width=int(w * self.s))

    def fatia(self, box, a0, a1, fill):
        self.d.pieslice(self._b(box), a0, a1, fill=fill)

    def chord(self, box, a0, a1, fill, outline=OUTLINE, ow=OW):
        if ow:
            x0, y0, x1, y1 = box
            self.d.chord(self._b((x0 - ow / 2, y0 - ow / 2, x1 + ow / 2, y1 + ow / 2)), a0, a1, fill=outline)
        self.d.chord(self._b(box), a0, a1, fill=fill)

    def pronto(self):
        w, h = self.img.size
        return self.img.resize((w // self.s, h // self.s), Image.LANCZOS)


def gradiente(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, float)[None, None, :]
    b = np.array(bottom, float)[None, None, :]
    arr = (a * (1 - t) + b * t).repeat(w, axis=1)
    return Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")


def brilho(size, cor, raio, intensidade=1.0):
    """Mancha de luz radial (glow) RGBA."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - w / 2) ** 2 + (yy - h / 2) ** 2) / raio
    a = np.clip(1 - d, 0, 1) ** 2 * 255 * intensidade
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = cor
    arr[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def colar(base, spr, cx, by, escala=1.0, sx=1.0, sy=1.0, rot=0.0, alpha=1.0):
    """Cola sprite com âncora no centro-inferior (cx, by) — típico de cutout."""
    w, h = spr.size
    nw, nh = max(1, int(w * escala * sx)), max(1, int(h * escala * sy))
    s = spr.resize((nw, nh), Image.BICUBIC)
    if rot:
        s = s.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = s.getchannel("A").point(lambda v: int(v * alpha))
        s.putalpha(a)
    base.alpha_composite(s, (int(cx - s.width / 2), int(by - s.height)))


def ease_out(x):
    x = min(max(x, 0), 1)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = min(max(x, 0), 1)
    return x * x * (3 - 2 * x)


# --------------------------------------------------------------------------
# Personagens (sprites por expressão/pose — troca de "peças" como no cutout)
# --------------------------------------------------------------------------
LELO = dict(pele=(232, 176, 128), cabelo=(92, 58, 38), camisa=(255, 196, 61),
            calca=(70, 112, 170), sapato=(230, 90, 80), tipo="menino")
CIDA = dict(pele=(214, 160, 120), cabelo=(220, 220, 228), camisa=(176, 120, 190),
            calca=(120, 90, 150), sapato=(110, 80, 70), tipo="vovo")


def desenhar_personagem(pal, expr="neutro", pose="idle", olhos_fechados=False):
    W, H = 340, 640
    p = Pincel(W, H)
    pele, cab = pal["pele"], pal["cabelo"]
    tipo = pal["tipo"]
    vovo = tipo == "vovo"
    vestido = tipo in ("vovo", "moca")
    oculos = tipo in ("vovo", "vovo_h")
    adulto = tipo == "pai"
    if expr == "chora":
        expr_olho = "triste"
    else:
        expr_olho = expr

    # pernas + sapatos
    if vestido:
        p.ret((100, 380, 240, 560), pal.get("vestido", pal["camisa"]), r=50)  # vestido
        for x in (135, 205):
            p.capsula((x, 540), (x, 585), 30, pele)
    else:
        for x in (135, 205):
            p.capsula((x, 440), (x, 575), 38, pal["calca"])
    for x in (125, 215):
        p.elipse((x - 34, 572, x + 34, 612), pal["sapato"])

    # braço esquerdo (do personagem à nossa esquerda)
    p.capsula((100, 335), (78, 455), 34, pal["camisa"])
    p.elipse((58, 440, 98, 480), pele)

    # tronco
    p.ret((92, 310, 248, 470), pal["camisa"], r=48)
    if pal.get("faixas"):  # faixas refletivas (uniforme de gari)
        for y in (380, 420):
            p.ret((96, y, 244, y + 14), (225, 230, 235), r=4, ow=0)
    if not vovo:
        p.ret((150, 318, 190, 330), (255, 225, 140), r=6, ow=0)  # gola

    # braço direito conforme pose
    if pose == "aponta":
        p.capsula((240, 335), (318, 255), 34, pal["camisa"])
        p.elipse((300, 230, 340, 270), pele)
        p.capsula((330, 238), (338, 205), 13, pele, ow=4)
    elif pose == "bate":
        p.capsula((240, 335), (300, 270), 34, pal["camisa"])
        p.elipse((282, 232, 326, 276), pele)
    elif pose == "bate2":
        p.capsula((240, 335), (312, 290), 34, pal["camisa"])
        p.elipse((296, 258, 340, 302), pele)
    elif pose == "entrega":
        p.capsula((240, 335), (296, 372), 34, pal["camisa"])
        p.elipse((282, 352, 322, 392), pele)
    elif pose == "acena":
        p.capsula((240, 335), (290, 230), 34, pal["camisa"])
        p.elipse((268, 190, 314, 236), pele)
    else:
        p.capsula((240, 335), (262, 455), 34, pal["camisa"])
        p.elipse((242, 440, 282, 480), pele)

    if pal.get("bolsa"):  # alça + bolsa de carteiro
        p.linha([(110, 318), (232, 452)], fill=(120, 72, 40), w=16)
        p.ret((196, 420, 276, 500), (150, 96, 54), r=12)
        p.ret((196, 420, 276, 448), (176, 116, 66), r=8, ow=5)

    # pescoço + cabeça
    p.ret((152, 285, 188, 320), pele, r=10)
    cx, cy, r = 170, 175, 122
    if vovo:  # coque atrás
        p.elipse((cx - 55, cy - r - 55, cx + 55, cy - r + 40), cab)
    p.elipse((cx - r - 14, cy - 10, cx - r + 26, cy + 34), pele)  # orelhas
    p.elipse((cx + r - 26, cy - 10, cx + r + 14, cy + 34), pele)
    p.elipse((cx - r, cy - r, cx + r, cy + r), pele)

    # cabelo
    if tipo == "vovo_h":
        for sx in (-1, 1):
            p.elipse((cx + sx * (r - 8) - 34, cy - 70, cx + sx * (r - 8) + 34, cy + 20), cab)
        p.poli([(cx - 20, cy - r + 4), (cx - 4, cy - r - 30), (cx + 14, cy - r + 6)], cab, ow=5)
    elif adulto:
        p.chord((cx - r - 4, cy - r - 6, cx + r + 4, cy + r * 0.2), 180, 360, cab)
        p.elipse((cx - r - 6, cy - 60, cx - r + 30, cy + 10), cab, ow=0)
        p.elipse((cx + r - 30, cy - 60, cx + r + 6, cy + 10), cab, ow=0)
    elif tipo == "moca":
        p.elipse((cx + r - 40, cy - r + 10, cx + r + 60, cy + 40), cab)       # rabo de cavalo
        p.chord((cx - r - 4, cy - r - 6, cx + r + 4, cy + r * 0.3), 180, 360, cab)
        p.elipse((cx + r - 34, cy - r + 30, cx + r + 2, cy - r + 66), (230, 90, 110), ow=5)
    elif vovo:
        p.chord((cx - r - 6, cy - r - 8, cx + r + 6, cy + r * 0.55), 180, 360, cab)
        for k in range(-2, 3):
            p.elipse((cx + k * 48 - 34, cy - r - 4, cx + k * 48 + 34, cy - r + 50), cab, ow=0)
    else:
        p.chord((cx - r - 4, cy - r - 6, cx + r + 4, cy + r * 0.35), 180, 360, cab)
        p.poli([(cx - 30, cy - r + 6), (cx - 8, cy - r - 62), (cx + 12, cy - r + 2)], cab)
        p.poli([(cx + 2, cy - r + 4), (cx + 40, cy - r - 48), (cx + 46, cy - r + 14)], cab)

    if pal.get("chapeu"):  # quepe de carteiro
        cc = pal["chapeu"]
        p.chord((cx - r + 6, cy - r - 30, cx + r - 6, cy - r + 110), 180, 360, cc)
        p.ret((cx - r + 2, cy - r + 36, cx + r - 2, cy - r + 66), cc, r=12)
        p.chord((cx - 40, cy - r + 44, cx + r + 4, cy - r + 96), 0, 180, (40, 50, 80), ow=6)
        p.elipse((cx - 16, cy - r + 6, cx + 16, cy - r + 34), (250, 200, 60), ow=5)

    # olhos
    ey = cy + 18
    for ex in (cx - 46, cx + 46):
        if olhos_fechados or expr == "ri":
            p.arco((ex - 28, ey - 18, ex + 28, ey + 26), 200, 340, w=8)
        else:
            p.elipse((ex - 30, ey - 36, ex + 30, ey + 36), (255, 255, 255), ow=6)
            dy = 6 if expr_olho == "triste" else 0
            pr = 15 if expr == "surpreso" else 19
            p.elipse((ex - pr, ey - pr + dy, ex + pr, ey + pr + dy), OUTLINE, ow=0)
            p.elipse((ex - 9 + 6, ey - 12 + dy, ex + 1 + 6, ey - 2 + dy), (255, 255, 255), ow=0)
    if oculos:  # óculos redondos
        for ex in (cx - 46, cx + 46):
            p.arco((ex - 40, ey - 42, ex + 40, ey + 42), 0, 360, fill=(120, 90, 60), w=6)
        p.linha([(cx - 8, ey - 4), (cx + 8, ey - 4)], fill=(120, 90, 60), w=6)

    # sobrancelhas
    by = ey - 52
    if expr == "bravo":
        p.linha([(cx - 74, by - 14), (cx - 22, by + 8)], w=10)
        p.linha([(cx + 22, by + 8), (cx + 74, by - 14)], w=10)
    elif expr_olho == "triste":
        p.linha([(cx - 72, by + 4), (cx - 24, by - 10)], w=8)
        p.linha([(cx + 24, by - 10), (cx + 72, by + 4)], w=8)
    elif expr == "surpreso":
        p.arco((cx - 76, by - 18, cx - 20, by + 14), 200, 340, w=8)
        p.arco((cx + 20, by - 18, cx + 76, by + 14), 200, 340, w=8)
    else:
        p.linha([(cx - 70, by), (cx - 26, by - 6)], w=8)
        p.linha([(cx + 26, by - 6), (cx + 70, by)], w=8)

    # bochechas
    for ex in (cx - 78, cx + 78):
        p.elipse((ex - 20, ey + 30, ex + 20, ey + 50), (240, 130, 130), ow=0)

    # boca
    my = cy + 78
    if expr in ("feliz", "ri"):
        p.chord((cx - 40, my - 30, cx + 40, my + 34), 0, 180, (150, 40, 50), ow=6)
        p.chord((cx - 22, my + 6, cx + 22, my + 32), 0, 180, (235, 100, 110), ow=0)
    elif expr == "bravo":
        p.elipse((cx - 34, my - 14, cx + 34, my + 34), (150, 40, 50), ow=6)
        p.ret((cx - 24, my - 10, cx + 24, my + 2), (255, 255, 255), r=3, ow=0)
    elif expr == "chora":
        p.chord((cx - 30, my - 4, cx + 30, my + 34), 180, 360, (150, 40, 50), ow=6)
    elif expr == "triste":
        p.arco((cx - 26, my - 2, cx + 26, my + 30), 200, 340, w=7)
    elif expr == "surpreso":
        p.elipse((cx - 15, my - 8, cx + 15, my + 26), (150, 40, 50), ow=6)
    else:
        p.arco((cx - 26, my - 26, cx + 26, my + 6), 30, 150, w=7)
    if adulto and pal.get("bigode", True):  # bigode + barba por fazer
        p.chord((cx - 48, my - 44, cx + 2, my - 14), 180, 360, cab, ow=5)
        p.chord((cx - 2, my - 44, cx + 48, my - 14), 180, 360, cab, ow=5)
        for k in range(14):
            a = math.radians(20 + k * 10)
            x, y = cx + 95 * math.cos(a), cy + 30 + 80 * math.sin(a)
            p.elipse((x - 3, y - 3, x + 3, y + 3), (170, 120, 90), ow=0)
    if tipo == "vovo_h":  # bigode
        p.chord((cx - 52, my - 46, cx + 4, my - 12), 180, 360, cab, ow=5)
        p.chord((cx - 4, my - 46, cx + 52, my - 12), 180, 360, cab, ow=5)
    if expr == "chora":  # lágrimas
        for ex in (cx - 46, cx + 46):
            p.ret((ex - 12, ey + 30, ex + 12, ey + 110), (120, 190, 255), r=12, ow=4)
    if oculos:  # rugas sutis
        p.arco((cx - 100, ey - 6, cx - 70, ey + 20), 100, 200, fill=(170, 120, 90), w=4)
        p.arco((cx + 70, ey - 6, cx + 100, ey + 20), -20, 80, fill=(170, 120, 90), w=4)
    return p.pronto()


class Ator:
    """Um personagem com sprites pré-renderizados e animação de idle."""

    def __init__(self, pal):
        self.pal = pal
        self.cache = {}

    def spr(self, expr, pose, fechado=False):
        k = (expr, pose, fechado)
        if k not in self.cache:
            self.cache[k] = desenhar_personagem(self.pal, expr, pose, fechado)
        return self.cache[k]

    def desenhar(self, base, t, cx, by, escala=1.0, expr="neutro", pose="idle",
                 rot=0.0, piscar=True, alpha=1.0, pulo=0.0):
        # piscada a cada ~3s, durando 3 frames
        fechado = piscar and (int(t * FPS) % 95) in (0, 1, 2)
        respira = 1 + 0.012 * math.sin(t * 2 * math.pi * 0.9)    # squash & stretch leve
        bob = 4 * math.sin(t * 2 * math.pi * 0.9) + pulo
        colar(base, self.spr(expr, pose, fechado), cx, by - bob, escala,
              sx=2 - respira, sy=respira, rot=rot, alpha=alpha)


# --------------------------------------------------------------------------
# Cenários
# --------------------------------------------------------------------------
CORES_CASAS = [(126, 166, 205), (240, 170, 120), (150, 196, 150), (220, 140, 160),
               (190, 170, 220), (240, 210, 130)]


def janela_vela(p, x, y, w, h, acesa=True):
    p.ret((x, y, x + w, y + h), (255, 214, 120) if acesa else (60, 66, 92), r=8, ow=6)
    p.linha([(x + w / 2, y), (x + w / 2, y + h)], w=5)
    p.linha([(x, y + h / 2), (x + w, y + h / 2)], w=5)
    if acesa:
        p.ret((x + w / 2 - 8, y + h - 40, x + w / 2 + 8, y + h - 8), (250, 245, 230), r=3, ow=4)
        p.elipse((x + w / 2 - 7, y + h - 60, x + w / 2 + 7, y + h - 38), (255, 150, 40), ow=0)


def cenario_rua(noite=True):
    """Rua de casinhas à noite com velas nas janelas. Retorna (img, janelas)."""
    base = gradiente(WW, WH, (24, 30, 66) if noite else (150, 200, 240),
                     (78, 70, 120) if noite else (230, 230, 250))
    p = Pincel(WW, WH)
    # lua e estrelas
    p.elipse((760, 140, 900, 280), (250, 240, 200), ow=0)
    for _ in range(60):
        x, y = random.randint(0, WW), random.randint(0, 700)
        r = random.choice((2, 3, 4))
        p.elipse((x - r, y - r, x + r, y + r), (255, 255, 230), ow=0)
    janelas = []
    # fileira de casas
    xs = [-40, 230, 500, 770]
    for i, x in enumerate(xs):
        cor = CORES_CASAS[i % len(CORES_CASAS)]
        top = 700 + (i % 2) * 60
        p.ret((x, top, x + 270, 1380), cor, r=6)
        p.poli([(x - 20, top + 4), (x + 135, top - 170), (x + 290, top + 4)], (150, 80, 80))
        p.ret((x + 100, 1180, x + 170, 1380), (110, 70, 55), r=10)  # porta
        for (jx, jy) in ((x + 30, top + 60), (x + 160, top + 60)):
            acesa = not (i == 2 and jx == x + 160)
            janela_vela(p, jx, jy, 80, 110, acesa)
            janelas.append((jx + 40, jy + 55, acesa))
    # calçada e rua
    p.ret((-20, 1370, WW + 20, 1480), (190, 180, 170), r=0)
    p.ret((-20, 1480, WW + 20, WH + 20), (80, 80, 96), r=0)
    for x in range(0, WW, 200):
        p.ret((x + 40, 1680, x + 140, 1700), (230, 220, 150), r=6, ow=0)
    # poste
    p.ret((60, 900, 82, 1400), (60, 60, 80), r=6)
    p.elipse((36, 860, 106, 930), (255, 230, 150))
    img = p.pronto()
    base.alpha_composite(img)
    # glows das janelas e poste
    for (x, y, acesa) in janelas:
        if acesa:
            g = brilho((300, 300), (255, 190, 90), 150, 0.55)
            base.alpha_composite(g, (int(x - 150), int(y - 150)))
    base.alpha_composite(brilho((500, 500), (255, 220, 140), 250, 0.4), (-180, 645))
    return base, janelas


def cenario_janela_close():
    base = gradiente(WW, WH, (60, 40, 70), (130, 80, 70))
    p = Pincel(WW, WH)
    p.ret((140, 300, 940, 1500), (60, 70, 110), r=30, ow=14)   # vidro
    p.linha([(540, 300), (540, 1500)], w=16)
    p.linha([(140, 900), (940, 900)], w=16)
    p.ret((80, 1480, 1000, 1580), (170, 110, 80), r=10, ow=10)  # peitoril
    p.ret((470, 1180, 610, 1490), (250, 244, 228), r=16, ow=10)  # vela
    p.ret((80, 1580, 1000, WH + 20), (150, 90, 70), r=0, ow=0)
    base.alpha_composite(p.pronto())
    return base


def chama(tam, t, semente=0):
    """Chama de vela com tremulação procedural."""
    p = Pincel(tam, tam * 1.6)
    k = 1 + 0.08 * math.sin(t * 17 + semente) + 0.05 * math.sin(t * 29 + semente * 2)
    w, h = tam * 0.5, tam * 1.2 * k
    cx, by = tam / 2 + 6 * math.sin(t * 9 + semente), tam * 1.55
    p.elipse((cx - w / 2, by - h, cx + w / 2, by), (255, 150, 40), ow=0)
    p.elipse((cx - w / 3.2, by - h * 0.7, cx + w / 3.2, by), (255, 225, 120), ow=0)
    return p.pronto()


def cenario_casa_cida(cor_fria=True):
    base = gradiente(WW, WH, (120, 130, 160) if cor_fria else (250, 220, 170),
                     (90, 96, 120) if cor_fria else (230, 170, 120))
    p = Pincel(WW, WH)
    p.ret((-20, 1380, WW + 20, WH + 20), (120, 100, 90) if cor_fria else (190, 130, 90), r=0)
    for x in range(-20, WW, 120):  # tábuas
        p.linha([(x, 1380), (x - 60, WH)], fill=(95, 78, 70) if cor_fria else (160, 105, 70), w=5)
    janela_vela(p, 640, 520, 260, 340, acesa=not cor_fria)
    p.ret((120, 600, 380, 820), (200, 190, 170) if cor_fria else (250, 230, 190), r=10, ow=8)  # quadro
    p.elipse((190, 650, 310, 770), (160, 150, 140) if cor_fria else (240, 160, 140), ow=6)
    base.alpha_composite(p.pronto())
    return base


def cadeira_balanço():
    p = Pincel(520, 700)
    cor = (140, 90, 60)
    p.ret((110, 60, 160, 470), cor, r=20)
    p.ret((360, 60, 410, 470), cor, r=20)
    for y in (110, 200, 290):
        p.ret((140, y, 380, y + 30), cor, r=10)
    p.ret((80, 430, 440, 490), cor, r=20)
    p.capsula((130, 480), (140, 640), 34, cor)
    p.capsula((390, 480), (380, 640), 34, cor)
    p.arco((-60, 400, 580, 700), 20, 160, fill=OUTLINE, w=30)
    p.arco((-56, 404, 576, 696), 22, 158, fill=cor, w=18)
    return p.pronto()


def cenario_porta():
    base = gradiente(WW, WH, (200, 150, 110), (150, 100, 80))
    p = Pincel(WW, WH)
    p.ret((-20, 1500, WW + 20, WH + 20), (170, 160, 150), r=0)
    p.ret((260, 260, 820, 1510), (110, 70, 55), r=24, ow=14)  # porta
    p.ret((330, 340, 750, 820), (130, 85, 65), r=18, ow=8)
    p.ret((330, 900, 750, 1430), (130, 85, 65), r=18, ow=8)
    p.elipse((720, 880, 770, 930), (240, 200, 90), ow=8)
    p.ret((-20, 120, 1100, 260), (150, 80, 80), r=0)
    base.alpha_composite(p.pronto())
    return base


def mesa_xicaras():
    p = Pincel(900, 420)
    p.ret((20, 120, 880, 200), (220, 120, 100), r=16)
    for i in range(0, 860, 60):
        p.ret((20 + i, 120, 50 + i, 200), (250, 245, 240), r=0, ow=0)
    p.ret((80, 200, 120, 420), (140, 90, 60), r=10)
    p.ret((780, 200, 820, 420), (140, 90, 60), r=10)
    for x in (260, 600):
        p.ret((x, 50, x + 80, 125), (250, 250, 250), r=14)
        p.arco((x + 66, 64, x + 110, 108), -90, 90, w=10)
    return p.pronto()


def balao_pensamento(conteudo):
    p = Pincel(520, 520)
    p.elipse((20, 20, 500, 420), (255, 255, 255))
    p.elipse((60, 430, 120, 490), (255, 255, 255))
    p.elipse((20, 480, 56, 516), (255, 255, 255))
    img = p.pronto()
    c = conteudo.resize((380, 300), Image.LANCZOS)
    m = Image.new("L", c.size, 0)
    ImageDraw.Draw(m).ellipse((0, 0, c.width, c.height), fill=255)
    img.paste(c, (70, 70), m)
    return img


# --------------------------------------------------------------------------
# Câmera, transições, legendas, efeitos
# --------------------------------------------------------------------------
def camera(mundo, cx, cy, zoom):
    """Recorta a janela 9:16 do mundo centrada em (cx, cy) com zoom."""
    vw = WW / zoom
    vh = WH / zoom
    x0 = min(max(cx - vw / 2, 0), WW - vw)
    y0 = min(max(cy - vh / 2, 0), WH - vh)
    return mundo.convert("RGB").resize((OUT_W, OUT_H), Image.BICUBIC,
                                       box=(x0, y0, x0 + vw, y0 + vh))


def motion_blur_h(img, forca):
    if forca < 1:
        return img
    a = np.asarray(img).astype(np.float32)
    n = int(min(forca, 60))
    acc = np.zeros_like(a)
    passos = range(-n, n + 1, max(1, n // 6))
    for s in passos:
        acc += np.roll(a, s, axis=1)
    return Image.fromarray((acc / len(passos)).astype(np.uint8))


def zoom_blur(img, forca):
    if forca < 0.01:
        return img
    acc = np.zeros((OUT_H, OUT_W, 3), np.float32)
    n = 6
    for i in range(n):
        z = 1 + forca * i / n
        w, h = OUT_W / z, OUT_H / z
        x0, y0 = (OUT_W - w) / 2, (OUT_H - h) / 2
        acc += np.asarray(img.resize((OUT_W, OUT_H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h)), np.float32)
    return Image.fromarray((acc / n).astype(np.uint8))


_VINHETA = None


def vinheta(img, forca=0.35):
    global _VINHETA
    if _VINHETA is None:
        yy, xx = np.mgrid[0:OUT_H, 0:OUT_W]
        d = np.sqrt(((xx - OUT_W / 2) / (OUT_W / 2)) ** 2 + ((yy - OUT_H / 2) / (OUT_H / 2)) ** 2)
        _VINHETA = np.clip(1 - (np.clip(d - 0.6, 0, 1) ** 1.6), 0, 1)[..., None]
    a = np.asarray(img, np.float32)
    f = 1 - forca * (1 - _VINHETA)
    return Image.fromarray(np.clip(a * f, 0, 255).astype(np.uint8))


class Legenda:
    """Legenda estilo karaokê: blocos de 2–4 palavras, palavra atual em amarelo."""

    def __init__(self, fonte, tamanho=46):
        self.f = ImageFont.truetype(fonte, tamanho) if fonte else ImageFont.load_default()

    @staticmethod
    def blocos(frase, maxp=3):
        pal = frase.split()
        out, cur = [], []
        for w in pal:
            cur.append(w)
            if len(cur) >= maxp or w[-1] in ",.!?…:":
                out.append(cur)
                cur = []
        if cur:
            out.append(cur)
        return out

    def desenhar(self, img, frase, t, dur, y=0.8):
        blocos = self.blocos(frase)
        tot = sum(len(w) + 2 for b in blocos for w in b)
        # tempo proporcional ao tamanho da palavra (aprox. fala natural)
        tempos, acc = [], 0.0
        for bi, b in enumerate(blocos):
            for wi, w in enumerate(b):
                tempos.append((bi, wi, acc / tot * dur))
                acc += len(w) + 2
        atual = max([x for x in tempos if x[2] <= t] or [tempos[0]], key=lambda x: x[2])
        bi, wi, t0b = atual[0], atual[1], [x[2] for x in tempos if x[0] == atual[0]][0]
        bloco = blocos[bi]
        d = ImageDraw.Draw(img)
        esp = self.f.getlength(" ")
        larg = sum(self.f.getlength(w) for w in bloco) + esp * (len(bloco) - 1)
        # pop-in do bloco
        pop = 0.82 + 0.18 * ease_out((t - t0b) / 0.12)
        camada = Image.new("RGBA", (int(larg + 40), 110), (0, 0, 0, 0))
        dc = ImageDraw.Draw(camada)
        x = 20
        for i, w in enumerate(bloco):
            cor = (255, 214, 40) if i == wi else (255, 255, 255)
            dc.text((x, 20), w, font=self.f, fill=cor, stroke_width=6, stroke_fill=(20, 20, 26))
            x += self.f.getlength(w) + esp
        camada = camada.resize((int(camada.width * pop), int(camada.height * pop)), Image.BICUBIC)
        img.paste(camada, (int(OUT_W / 2 - camada.width / 2), int(OUT_H * y - camada.height / 2)), camada)
        del d


def particulas(img, t, n=26, cor=(255, 230, 150), semente=1):
    rng = random.Random(semente)
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(n):
        x = rng.uniform(0, OUT_W)
        v = rng.uniform(20, 60)
        y = (rng.uniform(0, OUT_H) - t * v) % OUT_H
        r = rng.uniform(1.5, 3.5) * (0.6 + 0.4 * math.sin(t * 3 + x))
        d.ellipse((x - r, y - r, x + r, y + r), fill=cor + (int(180),))


def texto_pop(img, txt, fonte, t, cx, cy, tam=90, cor=(255, 255, 255)):
    f = ImageFont.truetype(fonte, tam) if fonte else ImageFont.load_default()
    s = 0.4 + 0.6 * ease_out(t / 0.15) + 0.08 * math.sin(min(t, 0.4) * 25) * (t < 0.4)
    cam = Image.new("RGBA", (int(f.getlength(txt) + 40), tam + 50), (0, 0, 0, 0))
    ImageDraw.Draw(cam).text((20, 10), txt, font=f, fill=cor, stroke_width=8, stroke_fill=(20, 20, 26))
    cam = cam.resize((max(1, int(cam.width * s)), max(1, int(cam.height * s))), Image.BICUBIC)
    img.paste(cam, (int(cx - cam.width / 2), int(cy - cam.height / 2)), cam)


# --------------------------------------------------------------------------
# Roteiro do demo (cenas)
# --------------------------------------------------------------------------
class Demo:
    def __init__(self, fonte):
        print("• pré-renderizando cenários e personagens…")
        self.fonte = fonte
        self.leg = Legenda(fonte)
        self.lelo = Ator(LELO)
        self.cida = Ator(CIDA)
        self.rua, self.janelas = cenario_rua()
        self.close = cenario_janela_close()
        self.casa_fria = cenario_casa_cida(True)
        self.casa_quente = cenario_casa_cida(False)
        self.cadeira = cadeira_balanço()
        self.porta = cenario_porta()
        self.mesa = mesa_xicaras()
        self.balao = balao_pensamento(
            ImageEnhance.Brightness(self.rua.crop((470, 600, 830, 1000)).convert("RGB")).enhance(1.1))

        # (duração, função, legenda, transição de entrada)
        self.cenas = [
            (3.4, self.c_rua, "Na minha rua, toda janela tem uma vela acesa.", "corte"),
            (3.4, self.c_vela, "Ela só fica acesa enquanto alguém lembra de você.", "whip"),
            (3.4, self.c_aponta, "Mas uma janela vivia apagada.", "whip"),
            (4.0, self.c_cida, "A da Dona Cida. Ninguém visitava ela há vinte anos.", "dissolve"),
            (3.6, self.c_pensa, "Num domingo, eu pensei nela o dia inteiro.", "whip"),
            (3.0, self.c_bate, "Então eu fui lá… e bati na porta.", "corte"),
            (3.2, self.c_surpresa, "Ela me olhou como se tivesse visto um fantasma.", "corte"),
            (4.2, self.c_mesa, "Naquela tarde a gente riu tanto… que a vela dela acendeu.", "whip"),
            (4.8, self.c_final, "Mas o que ela me contou depois… mudou tudo.", "zoom"),
        ]

    # --- cenas: cada uma devolve um frame RGB 720x1280 ----------------------
    def c_rua(self, t, d):
        m = self.rua.copy()
        z = 1.0 + 0.14 * ease_io(t / d)                 # push-in lento
        f = camera(m, WW / 2, WH * 0.5, z)
        particulas(f, t)
        return f

    def c_vela(self, t, d):
        m = self.close.copy()
        pulso = 0.75 + 0.15 * math.sin(t * 8)
        m.alpha_composite(brilho((900, 900), (255, 170, 70), 450, pulso), (90, 720))
        colar(m, chama(140, t), 540, 1195)
        f = camera(m, WW / 2, WH * 0.55, 1.05 + 0.1 * ease_io(t / d))
        particulas(f, t, 18, semente=3)
        return f

    def c_aponta(self, t, d):
        m = self.rua.copy()
        jx, jy, _ = [j for j in self.janelas if not j[2]][0]
        self.lelo.desenhar(m, t, 300, 1640, escala=1.25, expr="triste" if t > d * 0.55 else "neutro",
                           pose="aponta")
        cx = 420 + 140 * ease_io(t / d)                 # pan para a janela apagada
        return camera(m, cx, 1150, 1.25)

    def c_cida(self, t, d):
        m = self.casa_fria.copy()
        ang = 3.5 * math.sin(t * 2.2)                    # cadeira balançando
        cad = self.cadeira.resize((780, 1050), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC, expand=True)
        m.alpha_composite(cad, (int(420 - cad.width / 2), 760))
        self.cida.desenhar(m, t, 420, 1620, escala=1.15, expr="triste", rot=ang)
        f = camera(m, WW / 2, 1150, 1.15 + 0.08 * ease_io(t / d))
        f = ImageEnhance.Color(f).enhance(0.45)          # dessaturado = solidão
        return f

    def c_pensa(self, t, d):
        m = gradiente(WW, WH, (250, 200, 150), (240, 160, 120))
        p = Pincel(WW, WH)
        p.ret((-20, 1500, WW + 20, WH + 20), (200, 130, 90), r=0)
        m.alpha_composite(p.pronto())
        self.lelo.desenhar(m, t, 420, 1640, escala=1.35, expr="neutro" if t < d * 0.6 else "feliz")
        s = ease_out((t - 0.3) / 0.35)
        if s > 0:
            b = self.balao.resize((int(520 * s) + 1, int(520 * s) + 1), Image.BICUBIC)
            m.alpha_composite(b, (int(760 - b.width / 2), int(560 - b.height / 2)))
        return camera(m, WW / 2, 1100, 1.1)

    def c_bate(self, t, d):
        m = self.porta.copy()
        batida = int(t * 6) % 2 if 0.8 < t < 2.4 else 0
        shake = (6 if batida else 0) * (0.8 < t < 2.4)
        self.lelo.desenhar(m, t, 230, 1700, escala=1.2, pose="bate2" if batida else "bate")
        f = camera(m, WW / 2 + shake, 1100, 1.1)
        if t > 0.8:
            texto_pop(f, "TOC", self.fonte, t - 0.8, 500, 330, 100)
        if t > 1.4:
            texto_pop(f, "TOC!", self.fonte, t - 1.4, 560, 470, 110)
        return f

    def c_surpresa(self, t, d):
        m = self.porta.copy()
        p = Pincel(WW, WH)
        p.ret((260, 260, 820, 1510), (40, 30, 40), r=24, ow=14)   # porta aberta (vão escuro)
        m.alpha_composite(p.pronto())
        self.cida.desenhar(m, t, 540, 1560, escala=1.45, expr="surpreso")
        z = 1.0 + 0.55 * ease_out(t / 0.35)              # punch-in rápido no rosto
        f = camera(m, 540, 820 + 120 * (1 - ease_out(t / 0.35)), z)
        if t < 0.12:                                     # flash branco de impacto
            f = Image.blend(f, Image.new("RGB", f.size, (255, 255, 255)), 0.5 * (1 - t / 0.12))
        return f

    def c_mesa(self, t, d):
        m = self.casa_quente.copy() if t > d * 0.55 else self.casa_fria.copy()
        if t > d * 0.55:
            k = ease_out((t - d * 0.55) / 0.5)
            m.alpha_composite(brilho((900, 900), (255, 200, 90), 450, 0.9 * k), (320, 240))
            colar(m, chama(70, t), 770, 852)
        rindo = int(t * 5) % 2
        self.lelo.desenhar(m, t, 300, 1560, escala=1.0, expr="ri" if rindo else "feliz", pulo=6 * rindo)
        self.cida.desenhar(m, t, 760, 1560, escala=1.0, expr="ri" if not rindo else "feliz", pulo=6 * (1 - rindo))
        m.alpha_composite(self.mesa, (90, 1330))
        f = camera(m, WW / 2, 1200, 1.3)
        if t > d * 0.55:
            particulas(f, t, 40, semente=9)
        else:
            f = ImageEnhance.Color(f).enhance(0.6 + 0.4 * (t / (d * 0.55)))
        return f

    def c_final(self, t, d):
        m = self.rua.copy()
        jx, jy, _ = [j for j in self.janelas if not j[2]][0]
        p = Pincel(WW, WH)
        janela_vela(p, jx - 40, jy - 55, 80, 110, True)
        m.alpha_composite(p.pronto())
        k = 0.9 + 0.1 * math.sin(t * 6)
        m.alpha_composite(brilho((700, 700), (255, 210, 110), 350, k), (int(jx - 350), int(jy - 350)))
        f = camera(m, jx, jy + 200, 1.35 - 0.2 * ease_io(t / d))   # pull-out
        particulas(f, t, 30, semente=5)
        if t > d - 1.6:
            f = ImageEnhance.Brightness(f).enhance(1 - 0.55 * ease_out((t - (d - 1.6)) / 0.5))
            texto_pop(f, "PARTE 2", self.fonte, t - (d - 1.6), OUT_W / 2, OUT_H * 0.42, 96, (255, 214, 40))
        return f

    # --- montagem -----------------------------------------------------------
    def duracao(self):
        return sum(c[0] for c in self.cenas)

    def frame(self, n):
        t = n / FPS
        ini = 0.0
        for i, (d, fn, leg, trans) in enumerate(self.cenas):
            if t < ini + d or i == len(self.cenas) - 1:
                tl = t - ini
                f = fn(tl, d)
                T = 0.25
                # transição de entrada (os primeiros T segundos da cena)
                if i > 0 and tl < T and trans != "corte":
                    dp, fp, _, _ = self.cenas[i - 1]
                    prev = fp(dp - 0.001, dp)
                    x = tl / T
                    if trans == "whip":
                        off = int(OUT_W * ease_io(x))
                        comp = Image.new("RGB", (OUT_W, OUT_H))
                        comp.paste(prev, (-off, 0))
                        comp.paste(f, (OUT_W - off, 0))
                        f = motion_blur_h(comp, 60 * math.sin(math.pi * x))
                    elif trans == "dissolve":
                        f = Image.blend(prev, f, ease_io(x))
                    elif trans == "zoom":
                        f = zoom_blur(Image.blend(prev, f, ease_io(x)), 0.35 * math.sin(math.pi * x))
                f = vinheta(f)
                self.leg.desenhar(f, leg, tl, d)
                return f
            ini += d

    def tempos_sfx(self):
        ev, ini = [], 0.0
        for (d, fn, _, trans) in self.cenas:
            if trans in ("whip", "zoom") and ini > 0:
                ev.append(("whoosh", ini - 0.05))
            if trans == "corte" and ini > 0:
                ev.append(("pop", ini))
            if fn == self.c_bate:
                ev += [("toc", ini + 0.8), ("toc", ini + 1.15), ("toc", ini + 1.4), ("toc", ini + 1.75)]
            if fn == self.c_mesa:
                ev.append(("brilho", ini + d * 0.55))
            ini += d
        return ev


# --------------------------------------------------------------------------
# Áudio sintetizado: trilha emocional de piano + SFX
# --------------------------------------------------------------------------
SR = 44100


def nota(freq, dur, vol=0.2):
    t = np.arange(int(SR * dur)) / SR
    env = np.exp(-t * 2.2) * np.minimum(1, t * 80)
    s = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t)
         + 0.12 * np.sin(6 * np.pi * freq * t))
    return s * env * vol


def trilha(dur):
    out = np.zeros(int(SR * (dur + 2)))
    # Am – F – C – G (progressão "emocional" clássica desses vídeos)
    acordes = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 261.6, 329.6), (196.0, 246.9, 293.7)]
    beat = 60 / 72
    t, i = 0.0, 0
    while t < dur:
        ac = acordes[(i // 4) % 4]
        k = int(t * SR)
        for j, f in enumerate(ac):  # arpejo
            seg = nota(f * (2 if i % 2 else 1), 2.5, 0.09)
            a = k + int(j * beat / 3 * SR)
            out[a:a + len(seg)] += seg[: max(0, len(out) - a)]
        if i % 4 == 0:
            seg = nota(ac[0] / 2, 4, 0.14)
            out[k:k + len(seg)] += seg[: max(0, len(out) - k)]
        t += beat
        i += 1
    return out[: int(SR * dur)]


def sfx(tipo):
    rng = np.random.default_rng(3)
    if tipo == "whoosh":
        n = int(SR * 0.35)
        ruido = rng.standard_normal(n)
        env = np.sin(np.linspace(0, np.pi, n)) ** 2
        k = np.ones(30) / 30
        return np.convolve(ruido, k, "same") * env * 0.5
    if tipo == "toc":
        t = np.arange(int(SR * 0.12)) / SR
        return np.sin(2 * np.pi * 180 * t) * np.exp(-t * 60) * 0.7
    if tipo == "pop":
        t = np.arange(int(SR * 0.1)) / SR
        return np.sin(2 * np.pi * (600 - 3000 * t) * t) * np.exp(-t * 40) * 0.3
    if tipo == "brilho":
        out = np.zeros(int(SR * 1.5))
        for j, f in enumerate((1318.5, 1568.0, 1975.5, 2637.0)):
            s = nota(f, 1.0, 0.08)
            a = int(j * 0.07 * SR)
            out[a:a + len(s)] += s
        return out
    return np.zeros(1)


def gerar_audio(demo, caminho):
    dur = demo.duracao()
    mix = trilha(dur)
    for tipo, t0 in demo.tempos_sfx():
        s = sfx(tipo)
        a = int(t0 * SR)
        b = min(len(mix), a + len(s))
        if a < len(mix):
            mix[a:b] += s[: b - a]
    fade = int(SR * 1.2)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.8
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(caminho, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonte", default=fonte_padrao(), help="TTF/WOFF para a legenda (ex.: Poppins ExtraBold)")
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "demo_vela_dona_cida.mp4"))
    ap.add_argument("--preview", action="store_true", help="só salva alguns frames PNG")
    args = ap.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg não encontrado")

    demo = Demo(args.fonte)
    total = int(demo.duracao() * FPS)
    tmp = tempfile.mkdtemp(prefix="anim_")

    if args.preview:
        for s in range(0, total, FPS):
            demo.frame(s).save(os.path.join(tmp, f"p_{s:04d}.png"))
        print("frames de preview em", tmp)
        return

    wav = os.path.join(tmp, "audio.wav")
    gerar_audio(demo, wav)
    print(f"• renderizando {total} frames ({demo.duracao():.1f}s)…")
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{OUT_W}x{OUT_H}", "-r", str(FPS), "-i", "-", "-i", wav,
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", args.saida],
        stdin=subprocess.PIPE)
    for n in range(total):
        proc.stdin.write(demo.frame(n).tobytes())
        if n % 60 == 0:
            print(f"  {n}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()
    shutil.rmtree(tmp, ignore_errors=True)
    print("✔ vídeo salvo em", args.saida)


if __name__ == "__main__":
    main()
