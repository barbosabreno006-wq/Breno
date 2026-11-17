"""Biblioteca de desenho: personagem boneco-palito, props, legendas e helpers."""
import math, random
from PIL import Image, ImageDraw, ImageFont

W, H, SS = 576, 1024, 2
OUT = (26, 26, 28)
SKIN = (251, 247, 238)
CAP = (31, 110, 62)
YEL = (244, 184, 10)
YEL2 = (255, 221, 51)
PURP = (123, 70, 184)
BLUE = (48, 116, 214)
RED = (214, 40, 40)
GREEN = (84, 214, 130)
WHITE = (255, 255, 255)
NAVY = (27, 37, 64)
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
_fonts = {}


def font(sz):
    k = int(sz)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(FONT, k)
    return _fonts[k]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def pop(lt, t0, dur=0.24):
    """0 antes de t0; 'pop' com overshoot depois."""
    if lt < t0:
        return 0.0
    u = clamp((lt - t0) / dur)
    if u >= 1:
        return 1.0
    return math.sin(u * math.pi / 2) * 1.18 if u < 0.7 else 1.18 - (u - 0.7) / 0.3 * 0.18


def ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


class Cv:
    def __init__(s, img):
        s.im = img
        s.d = ImageDraw.Draw(img)

    def rect(s, x0, y0, x1, y1, fill=None, out=None, w=0):
        s.d.rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=fill, outline=out, width=int(w * SS))

    def rr(s, x0, y0, x1, y1, r, fill=None, out=None, w=0):
        s.d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=r * SS, fill=fill, outline=out, width=int(w * SS))

    def ell(s, cx, cy, rx, ry=None, fill=None, out=None, w=0):
        ry = rx if ry is None else ry
        s.d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=fill, outline=out, width=int(w * SS))

    def poly(s, pts, fill=None, out=None, w=0):
        p = [(x * SS, y * SS) for x, y in pts]
        s.d.polygon(p, fill=fill)
        if out and w:
            s.d.line(p + [p[0]], fill=out, width=int(w * SS), joint="curve")

    def line(s, x0, y0, x1, y1, col=OUT, w=4):
        s.d.line([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=col, width=max(1, int(w * SS)))

    def lines(s, pts, col=OUT, w=4):
        s.d.line([(x * SS, y * SS) for x, y in pts], fill=col, width=max(1, int(w * SS)), joint="curve")

    def arc(s, cx, cy, rx, ry, a0, a1, col=OUT, w=4):
        s.d.arc([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], a0, a1, fill=col, width=max(1, int(w * SS)))

    def text(s, t, cx, cy, size, fill=WHITE, stroke=0, sfill=OUT, anchor="mm"):
        s.d.text((cx * SS, cy * SS), t, font=font(size * SS), fill=fill, anchor=anchor,
                 stroke_width=int(stroke * SS), stroke_fill=sfill)


def sticker(cv, text, cx, cy, size=40, fill=YEL, tcol=OUT, scale=1.0, rot=0, pad=14):
    """Etiqueta amarela/verde com texto, girada, centrada em (cx,cy)."""
    if scale <= 0.01:
        return
    f = font(size * SS)
    tmp = Image.new("L", (1, 1))
    bb = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=f, anchor="lt")
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    w, h = tw + pad * 2 * SS, th + pad * 1.6 * SS
    lay = Image.new("RGBA", (int(w + 20 * SS), int(h + 20 * SS)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([10 * SS, 10 * SS, 10 * SS + w, 10 * SS + h], radius=12 * SS, fill=fill, outline=OUT, width=int(4 * SS))
    d.text((10 * SS + w / 2, 10 * SS + h / 2 - bb[1] / 2 + 1), text, font=f, fill=tcol, anchor="mm")
    if rot:
        lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    if scale != 1.0:
        lay = lay.resize((max(1, int(lay.width * scale)), max(1, int(lay.height * scale))), Image.BICUBIC)
    cv.im.paste(lay, (int(cx * SS - lay.width / 2), int(cy * SS - lay.height / 2)), lay)


# ---------------------------------------------------------------- personagem
COL = {
    "hero": dict(body=YEL, extra="vest"),
    "client": dict(body=PURP, extra=None),
    "blue": dict(body=(47, 111, 214), extra=None),
    "suit": dict(body=NAVY, extra="suit"),
    "mason": dict(body=(140, 148, 158), extra=None),
    "kid": dict(body=(235, 110, 70), extra=None),
    "white": dict(body=(235, 235, 240), extra=None),
}


def face(cv, hx, hy, r, expr, t, sc):
    ex = 19 * sc
    ey = hy - 2 * sc
    dot = 6 * sc
    if expr in ("smile", "wink", "smirk", "flat", "worry", "dumb"):
        cv.ell(hx - ex, ey, dot, fill=OUT)
        if expr == "wink":
            cv.arc(hx + ex, ey + 4 * sc, 9 * sc, 7 * sc, 200, 340, OUT, 4 * sc)
        else:
            cv.ell(hx + ex, ey, dot, fill=OUT)
    if expr == "smile":
        cv.arc(hx, hy + 12 * sc, 22 * sc, 15 * sc, 20, 160, OUT, 4 * sc)
    elif expr == "wink":
        cv.arc(hx, hy + 12 * sc, 22 * sc, 15 * sc, 20, 160, OUT, 4 * sc)
    elif expr == "smirk":
        cv.line(hx - ex - 9 * sc, ey - 8 * sc, hx - ex + 9 * sc, ey - 3 * sc, OUT, 4 * sc)
        cv.line(hx + ex - 9 * sc, ey - 3 * sc, hx + ex + 9 * sc, ey - 8 * sc, OUT, 4 * sc)
        cv.arc(hx + 6 * sc, hy + 14 * sc, 20 * sc, 10 * sc, 20, 150, OUT, 4 * sc)
    elif expr == "flat":
        cv.line(hx - 14 * sc, hy + 24 * sc, hx + 14 * sc, hy + 24 * sc, OUT, 4 * sc)
    elif expr == "dumb":
        cv.arc(hx, hy + 14 * sc, 18 * sc, 14 * sc, 20, 160, OUT, 4 * sc)
    elif expr == "worry":
        cv.line(hx - ex - 10 * sc, ey - 16 * sc, hx - ex + 8 * sc, ey - 10 * sc, OUT, 4 * sc)
        cv.line(hx + ex + 10 * sc, ey - 16 * sc, hx + ex - 8 * sc, ey - 10 * sc, OUT, 4 * sc)
        cv.arc(hx, hy + 30 * sc, 14 * sc, 9 * sc, 200, 340, OUT, 4 * sc)
        dy = (t * 40) % 30
        cv.ell(hx + 44 * sc, hy - 20 * sc + dy * 0.6, 5 * sc, 8 * sc, fill=(120, 200, 245), out=OUT, w=2 * sc)
    elif expr == "dollar":
        for sx in (-1, 1):
            cv.ell(hx + sx * ex, ey - 2 * sc, 15 * sc, fill=(60, 185, 95), out=OUT, w=3 * sc)
            cv.text("$", hx + sx * ex, ey - 2 * sc, 22 * sc, fill=WHITE)
        cv.d.pieslice([(hx - 27 * sc) * SS, (hy + 2 * sc) * SS, (hx + 27 * sc) * SS, (hy + 44 * sc) * SS], 0, 180, fill=(120, 30, 30), outline=OUT, width=int(3 * SS))
    elif expr == "happy":
        for sx in (-1, 1):
            cv.arc(hx + sx * ex, ey + 4 * sc, 9 * sc, 8 * sc, 200, 340, OUT, 4 * sc)
        cv.d.pieslice([(hx - 22 * sc) * SS, (hy + 2 * sc) * SS, (hx + 22 * sc) * SS, (hy + 38 * sc) * SS], 0, 180, fill=(120, 30, 30), outline=OUT, width=int(3 * SS))
    elif expr == "shock":
        for sx in (-1, 1):
            cv.ell(hx + sx * ex, ey, 11 * sc, fill=WHITE, out=OUT, w=3 * sc)
            cv.ell(hx + sx * ex, ey, 4 * sc, fill=OUT)
        cv.ell(hx, hy + 26 * sc, 9 * sc, 12 * sc, fill=(120, 30, 30), out=OUT, w=3 * sc)


def person(cv, x, gy, sc=1.0, kind="hero", expr="smile", t=0.0, armL="down", armR="down",
           walk=0.0, bob=True, hat=None):
    """Desenha o boneco. Retorna posições das mãos {'L':(x,y),'R':(x,y)} e do topo da cabeça."""
    sc = sc * 1.3
    c = COL[kind]
    b = math.sin(t * 5.5) * 2.2 * sc if bob else 0
    # pernas
    for i, dx in enumerate((-19, 19)):
        sw = math.sin(walk + i * math.pi) * 14 * sc if walk else 0
        cv.line(x + dx * sc, gy - 64 * sc + b, x + dx * sc + sw, gy - 4 * sc, OUT, 6 * sc)
        cv.ell(x + dx * sc + sw + 5 * sc, gy - 3 * sc, 13 * sc, 6 * sc, fill=OUT)
    top = gy - 192 * sc + b
    bot = gy - 58 * sc + b
    cv.rr(x - 48 * sc, top, x + 48 * sc, bot, 42 * sc, fill=c["body"], out=OUT, w=5 * sc)
    if c["extra"] == "vest":
        cv.line(x, top + 34 * sc, x, bot - 4 * sc, OUT, 3.5 * sc)
        cv.rr(x - 34 * sc, top + 78 * sc, x - 14 * sc, top + 96 * sc, 3 * sc, out=OUT, w=3.5 * sc)
    if c["extra"] == "suit":
        cv.poly([(x - 14 * sc, top + 14 * sc), (x + 14 * sc, top + 14 * sc), (x, top + 56 * sc)], fill=WHITE, out=OUT, w=2.5 * sc)
        cv.poly([(x - 5 * sc, top + 28 * sc), (x + 5 * sc, top + 28 * sc), (x + 7 * sc, top + 85 * sc), (x, top + 95 * sc), (x - 7 * sc, top + 85 * sc)], fill=RED, out=OUT, w=2 * sc)
    # braços
    sy = top + 40 * sc
    hands = {}
    styles = {
        "down": (64, 78), "out": (96, 38), "hold": (78, 48), "up": (74, -60), "hip": (70, 56),
        "wave": (86, -52), "front": (50, 70), "cross": (30, 60),
    }
    for side, st in (("L", armL), ("R", armR)):
        sx = -1 if side == "L" else 1
        ox, oy = styles[st]
        if st == "wave":
            oy += math.sin(t * 9) * 14 * sc
        ex_, ey_ = x + sx * ox * sc, sy + oy * sc
        mx, my = x + sx * (48 + ox) / 2 * sc, sy + oy * sc * 0.4 + 6 * sc
        cv.lines([(x + sx * 46 * sc, sy), (mx, my), (ex_, ey_)], OUT, 5.5 * sc)
        cv.ell(ex_, ey_, 8 * sc, fill=SKIN, out=OUT, w=3 * sc)
        hands[side] = (ex_, ey_)
    # cabeça
    hx, hy, r = x, top - 26 * sc, 54 * sc
    cv.ell(hx, hy, r, fill=SKIN, out=OUT, w=5 * sc)
    face(cv, hx, hy, r, expr, t, sc)
    if kind == "hero":
        cv.d.pieslice([(hx - r) * SS, (hy - r - 1 * sc) * SS, (hx + r) * SS, (hy + r - 1 * sc) * SS], 188, 352, fill=CAP, outline=OUT, width=int(5 * SS))
        cv.poly([(hx + 4 * sc, hy - r + 6 * sc), (hx + r + 30 * sc, hy - r + 26 * sc), (hx + r + 22 * sc, hy - r + 36 * sc), (hx + 8 * sc, hy - r + 22 * sc)], fill=CAP, out=OUT, w=4 * sc)
    if kind == "blue":
        cv.d.pieslice([(hx - r - 4 * sc) * SS, (hy - r - 6 * sc) * SS, (hx + r + 4 * sc) * SS, (hy + r - 6 * sc) * SS], 180, 360, fill=YEL2, outline=OUT, width=int(5 * SS))
        cv.rr(hx - r - 10 * sc, hy - 8 * sc, hx + r + 10 * sc, hy - 0 * sc, 4 * sc, fill=YEL2, out=OUT, w=4 * sc)
    if kind == "mason":
        cv.d.pieslice([(hx - r - 4 * sc) * SS, (hy - r - 6 * sc) * SS, (hx + r + 4 * sc) * SS, (hy + r - 6 * sc) * SS], 180, 360, fill=(240, 130, 40), outline=OUT, width=int(5 * SS))
        cv.rr(hx - r - 10 * sc, hy - 8 * sc, hx + r + 10 * sc, hy - 0 * sc, 4 * sc, fill=(240, 130, 40), out=OUT, w=4 * sc)
    if kind == "kid":
        pass
    return dict(hands=hands, head=(hx, hy), top=top, sc=sc)


# ---------------------------------------------------------------- props
def peneira(cv, hand, sc=1.0, t=0, tilt=0.12, long=300):
    hx, hy = hand
    tx, ty = hx + long * sc * math.sin(tilt), hy - long * sc * math.cos(tilt)
    cv.line(hx, hy, tx, ty, OUT, 7 * sc)
    cv.line(hx, hy, tx, ty, (190, 190, 200), 3.5 * sc)
    cv.ell(tx, ty - 6 * sc, 46 * sc, 22 * sc, fill=(120, 205, 225), out=OUT, w=4 * sc)
    for i in range(-2, 3):
        cv.line(tx + i * 16 * sc, ty - 24 * sc, tx + i * 16 * sc, ty + 12 * sc, OUT, 1.5 * sc)
    cv.line(tx - 44 * sc, ty - 6 * sc, tx + 44 * sc, ty - 6 * sc, OUT, 1.5 * sc)


def bucket(cv, cx, cy, sc=1.0, label="CLORO", fill=RED, tilt=0):
    pts = [(cx - 38 * sc, cy - 40 * sc), (cx + 38 * sc, cy - 40 * sc), (cx + 28 * sc, cy + 40 * sc), (cx - 28 * sc, cy + 40 * sc)]
    cv.poly(pts, fill=fill, out=OUT, w=5 * sc)
    cv.ell(cx, cy - 40 * sc, 38 * sc, 9 * sc, fill=(60, 60, 70), out=OUT, w=4 * sc)
    cv.arc(cx, cy - 46 * sc, 36 * sc, 30 * sc, 190, 350, OUT, 4 * sc)
    if label:
        cv.text(label, cx, cy + 6 * sc, 17 * sc, fill=WHITE, stroke=0)


def note(cv, cx, cy, rot=0, sc=1.0):
    lay = Image.new("RGBA", (int(130 * SS * sc), int(80 * SS * sc)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([6 * SS * sc, 6 * SS * sc, 124 * SS * sc, 74 * SS * sc], radius=8 * SS * sc, fill=(150, 225, 160), outline=OUT, width=int(3 * SS))
    d.ellipse([45 * SS * sc, 20 * SS * sc, 85 * SS * sc, 60 * SS * sc], outline=OUT, width=int(2.5 * SS))
    d.text((65 * SS * sc, 40 * SS * sc), "$", font=font(28 * SS * sc), fill=OUT, anchor="mm")
    lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    cv.im.paste(lay, (int(cx * SS - lay.width / 2), int(cy * SS - lay.height / 2)), lay)


# ---------------------------------------------------------------- cenário
def vgrad(cv, y0, y1, c0, c1, steps=18):
    for i in range(steps):
        a = i / (steps - 1)
        col = tuple(int(c0[k] + (c1[k] - c0[k]) * a) for k in range(3))
        cv.rect(0, y0 + (y1 - y0) * i / steps, W, y0 + (y1 - y0) * (i + 1) / steps + 1, col)


def sky(cv, hor=560):
    vgrad(cv, 0, hor, (116, 178, 240), (206, 232, 250))


def lawn(cv, y0, col=(124, 190, 92)):
    cv.rect(0, y0, W, H, col)
    cv.rect(0, y0, W, y0 + 8, (90, 150, 66))


def water(cv, x0, y0, x1, y1, t, col=(70, 175, 230), light=(150, 220, 245), rip=6):
    cv.rect(x0, y0, x1, y1, col)
    for i in range(rip):
        yy = y0 + (y1 - y0) * (i + 0.5) / rip
        pts = [(x0 + k * (x1 - x0) / 24, yy + math.sin(t * 2.2 + k * 0.7 + i) * 4) for k in range(25)]
        cv.lines(pts, light, 3)


def candles(cv, t, seed=3):
    r = random.Random(seed)
    x = 8
    base = 520
    while x < W:
        h = r.randint(30, 150)
        up = r.random() > 0.35
        col = (130, 225, 165) if up else (240, 125, 125)
        y = base - h - (x / W) * 150 + math.sin(t * 1.2 + x * 0.05) * 3
        cv.line(x + 8, y - 20, x + 8, y + h + 20, col, 3)
        cv.rect(x, y, x + 16, y + h, col)
        x += 28


def seg_poly_band(cv, p, color=YEL):
    pass
