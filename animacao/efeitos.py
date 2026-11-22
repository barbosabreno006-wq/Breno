#!/usr/bin/env python3
"""
Efeitos de "cinema" e elementos de jogo na tela (depois de comparar com vídeos de referência):
vinheta colorida, raios de luz, neblina, bloom, desfoque de fundo, selos de dificuldade, barra de vida,
números flutuantes e transição em círculo (íris).
"""
import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

import video_carta as vc

_C = {}


def vinheta_cor(f, cor=(200, 20, 30), forca=0.75, raio=0.62):
    """Escurece/colore as bordas (ex.: neblina vermelha de perigo)."""
    w, h = f.size
    k = ("vig", w, h, raio)
    if k not in _C:
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 1.414
        _C[k] = np.clip((d - raio * 0.5) / (1 - raio * 0.5), 0, 1) ** 1.6
    m = _C[k]
    a = np.asarray(f).astype(np.float32)
    c = np.array(cor, np.float32)[None, None, :]
    a = a * (1 - m[..., None] * forca) + c * (m[..., None] * forca)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def raios(f, t, cor=(255, 226, 120), n=18, alpha=70, centro=None, giro=0.15):
    """Raios de luz saindo do centro (efeito de revelação/brilho)."""
    w, h = f.size
    cx, cy = centro or (w / 2, h / 2)
    ov = Image.new("RGBA", f.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    R = math.hypot(w, h)
    for i in range(n):
        a0 = (i / n) * 2 * math.pi + t * giro
        a1 = a0 + math.pi / n
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))],
                  fill=cor + (alpha,))
    base = f.convert("RGBA")
    base.alpha_composite(ov)
    return base.convert("RGB")


def bloom(f, forca=0.35, raio=18, limiar=190):
    """Brilho suave nas áreas claras."""
    cinza = f.convert("L").point(lambda v: 255 if v > limiar else 0)
    luz = Image.composite(f, Image.new("RGB", f.size, (0, 0, 0)), cinza).filter(ImageFilter.GaussianBlur(raio))
    return ImageChops.add(f, luz.point(lambda v: int(v * forca)))


def neblina(f, t, cor=(255, 255, 255), alpha=70):
    """Névoa colorida se movendo devagar."""
    w, h = f.size
    ov = Image.new("RGBA", f.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(5):
        x = (i * 0.28 * w + t * 18 * (1 + i * 0.3)) % (w * 1.4) - w * 0.2
        y = h * (0.55 + 0.1 * math.sin(t * 0.4 + i))
        d.ellipse((x - w * 0.35, y - h * 0.12, x + w * 0.35, y + h * 0.12), fill=cor + (alpha,))
    ov = ov.filter(ImageFilter.GaussianBlur(40))
    base = f.convert("RGBA")
    base.alpha_composite(ov)
    return base.convert("RGB")


def desfoque(img, raio=7):
    """Desfoque de fundo (profundidade de campo): aplicar no cenário antes de desenhar os personagens."""
    return img.filter(ImageFilter.GaussianBlur(raio))


def borrao_movimento(f, forca=40):
    a = np.asarray(f).astype(np.float32)
    n = int(max(1, min(forca, 60)))
    acc = np.zeros_like(a)
    passos = range(-n, n + 1, max(1, n // 6))
    for s in passos:
        acc += np.roll(a, s, axis=1)
    return Image.fromarray((acc / len(passos)).astype(np.uint8))


# ---------------------------------------------------------------- elementos de jogo
def selo(f, fc, texto, x, y, cor=(255, 190, 40), tam=34, fundo=(30, 26, 60)):
    """Selo tipo 'DIFÍCIL / NORMAL / PESADELO'."""
    fnt = vc.fonte(fc, tam)
    w = int(fnt.getlength(texto) + tam * 1.9)
    h = int(tam * 1.7)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=fundo + (235,), outline=cor + (255,), width=4)
    d.ellipse((tam * 0.35, h / 2 - tam * 0.3, tam * 0.95, h / 2 + tam * 0.3), fill=cor + (255,))
    d.text((tam * 1.25, h / 2 - tam * 0.62), texto, font=fnt, fill=(255, 255, 255))
    f.paste(img, (int(x - w / 2), int(y - h / 2)), img)


def barra_vida(f, fc, x, y, w, pct, cor=(220, 40, 60), rotulo=""):
    h = 26
    d = ImageDraw.Draw(f, "RGBA")
    d.rounded_rectangle((x, y, x + w, y + h), radius=10, fill=(20, 20, 30, 220), outline=(255, 255, 255, 255), width=3)
    d.rounded_rectangle((x + 4, y + 4, x + 4 + int((w - 8) * max(0, min(1, pct))), y + h - 4), radius=7, fill=cor + (255,))
    if rotulo:
        fnt = vc.fonte(fc, 22)
        d.text((x, y - 28), rotulo, font=fnt, fill=(255, 255, 255, 255))


def numero_flutuante(f, fc, texto, x, y, cor=(255, 214, 40), tam=30, t=0.0):
    fnt = vc.fonte(fc, tam)
    d = ImageDraw.Draw(f, "RGBA")
    yy = y + 4 * math.sin(t * 3)
    w = fnt.getlength(texto)
    d.rounded_rectangle((x - w / 2 - 14, yy - 4, x + w / 2 + 14, yy + tam * 1.35), radius=14, fill=(20, 20, 30, 215))
    d.text((x - w / 2, yy), texto, font=fnt, fill=cor + (255,))


def iris(prev, nova, x):
    """Transição em círculo: a nova cena abre a partir do centro (x de 0 a 1)."""
    w, h = nova.size
    r = int(x * math.hypot(w, h) / 2)
    mask = Image.new("L", nova.size, 0)
    ImageDraw.Draw(mask).ellipse((w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r), fill=255)
    return Image.composite(nova, prev, mask)


def moldura_redonda(f, cor=(190, 150, 40), esp=26):
    """Moldura circular de vigia/escotilha (como o rosto dentro do vidro redondo)."""
    w, h = f.size
    r = int(min(w, h) * 0.46)
    mask = Image.new("L", f.size, 0)
    ImageDraw.Draw(mask).ellipse((w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r), fill=255)
    fundo = Image.new("RGB", f.size, (14, 12, 22))
    res = Image.composite(f, fundo, mask)
    d = ImageDraw.Draw(res)
    d.ellipse((w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r), outline=cor, width=esp)
    d.ellipse((w / 2 - r + esp, h / 2 - r + esp, w / 2 + r - esp, h / 2 + r - esp), outline=(255, 232, 150), width=4)
    return res


def grao(f, forca=0.5, quadro=0):
    """Grão de filme/papel por cima da imagem (unifica o desenho e tira o aspecto 'digital liso')."""
    w, h = f.size
    k = ("grao", w, h, quadro % 6)
    if k not in _C:
        rng = np.random.default_rng(100 + quadro % 6)
        _C[k] = rng.standard_normal((h, w, 1)).astype(np.float32)
    a = np.asarray(f).astype(np.float32) + _C[k] * (6.0 * forca)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
