"""Cenas do vídeo (cada função desenha um quadro em tempo local lt)."""
import math, random
from lib import *


def P(sh, n, default=0.0):
    return sh["pt"].get(n, default)


def pool_side(cv, lt, y0=600, y1=900, col=(70, 175, 230), clear=True, turbid=False):
    # deck + piscina em perspectiva
    cv.rect(0, y0 - 60, W, H, (222, 218, 210))
    cv.poly([(70, y0), (506, y0), (560, y1), (16, y1)], fill=(244, 244, 248), out=OUT, w=5)
    c = (150, 140, 70) if turbid else col
    cv.poly([(96, y0 + 22), (480, y0 + 22), (524, y1 - 24), (52, y1 - 24)], fill=c, out=OUT, w=4)
    for i in range(6):
        yy = y0 + 40 + i * (y1 - y0 - 80) / 6
        pts = [(60 + k * 20 + (yy - y0) * 0.1, yy + math.sin(lt * 2.4 + k * 0.7 + i) * 4) for k in range(22)]
        cv.lines(pts, (120, 105, 55) if turbid else (160, 225, 248), 3)
    if clear:
        for i in range(5):
            sx = 120 + (i * 83) % 380
            sy = y0 + 70 + (i * 47) % 160
            a = (math.sin(lt * 4 + i) + 1) / 2
            if a > 0.5:
                cv.line(sx - 8, sy, sx + 8, sy, WHITE, 3)
                cv.line(sx, sy - 8, sx, sy + 8, WHITE, 3)


def backyard(cv, lt, clear=True, turbid=False):
    sky(cv, 520)
    cv.rect(0, 380, W, 560, (206, 168, 120))
    for i in range(0, W, 48):
        cv.rect(i, 380, i + 44, 560, (206, 168, 120), OUT, 3)
        cv.line(i + 22, 380, i + 22, 560, (180, 140, 95), 2)
    lawn(cv, 560)
    pool_side(cv, lt, 640, 900, clear=clear, turbid=turbid)


# 1 -------------------------------------------------------------- título
def s_title(cv, lt, sh):
    cv.rect(0, 0, W, H, (22, 92, 70))
    for gx in range(0, W, 96):
        cv.line(gx, 0, gx, 560, (28, 108, 82), 2)
    candles(cv, lt)
    cv.rect(0, 640, W, H, (116, 64, 40))
    cv.rect(0, 640, W, 652, (80, 44, 28))
    for sx in (30, 530):
        for i in range(4):
            cv.rr(sx - 38, 612 - i * 20, sx + 38, 632 - i * 20, 3, fill=(150, 225, 160), out=OUT, w=3)
            cv.line(sx - 38, 622 - i * 20, sx + 38, 622 - i * 20, (110, 190, 125), 2)
    expr = "wink" if lt < 0.9 else ("smirk" if lt < 1.8 else "dollar")
    ph = person(cv, 288, 840, 1.5, "hero", expr, lt, armL="front", armR="front")
    # leque de notas
    for i in range(5):
        ang = -0.55 + i * 0.28
        note(cv, 288 + math.sin(ang) * 70, 700 - math.cos(ang) * 30 + abs(i - 2) * 8, rot=-ang * 57, sc=0.7)
    cv.rect(0, 740, W, H, (116, 64, 40))
    cv.rect(0, 740, W, 752, (80, 44, 28))
    for sx in (30, 530):
        for i in range(4):
            cv.rr(sx - 38, 712 - i * 20, sx + 38, 732 - i * 20, 3, fill=(150, 225, 160), out=OUT, w=3)


# 2 -------------------------------------------------------------- gancho
def s_hook(cv, lt, sh):
    backyard(cv, lt)
    ph = person(cv, 400, 960, 1.35, "hero", "smile", lt, armL="down", armR="hold")
    peneira(cv, ph["hands"]["R"], 1.35, lt, tilt=0.1, long=230)
    s = pop(lt, 1.0)
    sticker(cv, "R$ 200", 440, 470, 46, YEL, scale=s, rot=6)


# 3 ------------------------------------------------------------- cliente agradece
def s_client(cv, lt, sh):
    backyard(cv, lt)
    cv.rect(0, 380, W, 560, (206, 168, 120))
    ph = person(cv, 288, 960, 1.5, "client", "happy", lt, armL="down", armR="up")
    s = pop(lt, 0.2)
    if s:
        cv.poly([(130 * s + 140, 410), (330 + 70 * s, 410), (330 + 70 * s, 500), (330, 500), (300, 540), (290, 500), (140, 500)], fill=WHITE, out=OUT, w=4)
        cv.text("VALEU!", 275, 455, 40 * min(1, s), fill=OUT)


# 4 -------------------------------------------------------------- te explico (close)
def s_close(cv, lt, sh):
    sky(cv, 600)
    cv.rect(0, 560, W, H, (60, 90, 150))
    for i in range(6):
        cv.line(i * 110 - 60, 560, i * 110 + 80, H, (90, 125, 190), 6)
    ph = person(cv, 288, 1180, 2.6, "hero", "wink", lt, armL="down", armR="hold")


# 5 -------------------------------------------------------------- passo (azul-escuro)
def dark_blue(cv, lt):
    vgrad(cv, 0, H, (20, 34, 96), (18, 22, 64))
    for i in range(8):
        a = (i * 80 + lt * 14) % 800 - 100
        cv.line(a, 0, a - 220, H, (28, 46, 118), 5)


def s_passo1(cv, lt, sh):
    dark_blue(cv, lt)
    person(cv, 288, 1010, 1.7, "hero", "smirk", lt, armL="hip", armR="hip")


def s_passo2(cv, lt, sh):
    dark_blue(cv, lt)
    person(cv, 288, 1010, 1.7, "hero", "smile" if lt < 1.0 else "smirk", lt, armL="hip", armR="hold")


# 6 -------------------------------------------------------------- piscina verde (aérea)
def aerial_pool(cv, lt, col=(76, 140, 52), dirt=True, leaves=False, rot=0):
    cv.rect(0, 0, W, H, (122, 186, 96))
    for i in range(0, W, 64):
        cv.rect(i, 0, i + 32, H, (116, 180, 90))
    cv.rr(60, 140, 516, 860, 46, fill=(240, 242, 248), out=OUT, w=6)
    cv.rr(92, 172, 484, 828, 30, fill=col, out=OUT, w=5)
    r = random.Random(7)
    for i in range(14):
        bx, by = r.randint(120, 456), r.randint(200, 800)
        cv.ell(bx, by, r.randint(14, 34), r.randint(10, 24), fill=(60, 110, 40) if dirt else None)
    for i in range(7):
        yy = 210 + i * 90
        pts = [(100 + k * 16, yy + math.sin(lt * 2 + k * 0.8 + i) * 5) for k in range(25)]
        cv.lines(pts, (110, 170, 80), 3)
    if leaves:
        for i in range(22):
            lx = 110 + (i * 97) % 360
            ly = (150 + (i * 61) % 700 + lt * (60 + i * 3)) % 700 + 150
            cv.ell(lx, ly, 13, 7, fill=[(210, 120, 40), (150, 90, 40), (190, 160, 50)][i % 3], out=OUT, w=2)


def s_green_pool(cv, lt, sh):
    aerial_pool(cv, lt)
    z = pop(lt, 0.4)
    ph = person(cv, 288, 960, 0.75, "client", "worry", lt)


def s_leaves(cv, lt, sh):
    aerial_pool(cv, lt, col=(110, 165, 70), leaves=True)


# 8 -------------------------------------------------------------- cliente + cloro
def patio(cv, lt):
    cv.rect(0, 0, W, 640, (206, 176, 138))
    for i in range(0, W, 72):
        cv.line(i, 0, i, 640, (190, 158, 120), 3)
    cv.rect(0, 640, W, H, (190, 192, 204))
    for i in range(0, H, 90):
        cv.line(0, 640 + i, W, 640 + i, (170, 172, 186), 3)


def s_cloro(cv, lt, sh):
    patio(cv, lt)
    ph = person(cv, 288, 960, 1.5, "client", "worry", lt, armL="down", armR="hold")
    hx, hy = ph["hands"]["R"]
    tilt = ease((lt - P(sh, 9, 3.0) + 0.2) / 0.8) * 0.8 if lt > P(sh, 9, 3.0) - 0.2 else 0
    bucket(cv, hx + 24, hy + 16, 1.25, "CLORO")
    if lt > P(sh, 9, 3.0):
        for i in range(5):
            u = ((lt * 1.4 + i * 0.2) % 1)
            note(cv, 110 + i * 95, 760 - u * 360, rot=u * 140 * (1 if i % 2 else -1), sc=0.55)


# 10 ------------------------------------------------------------- pedreiro vai embora
def s_mason(cv, lt, sh):
    patio(cv, lt)
    x = 150 + lt * 120
    person(cv, x, 960, 1.45, "mason", "flat", lt, armL="down", armR="down", walk=lt * 7, hat=True)
    s = pop(lt, 1.0)
    sticker(cv, "R$ 200", 380, 520, 44, YEL, scale=s, rot=-5)
    if s:
        cv.line(300, 470, 460, 570, RED, 12 * min(1, s))
        cv.line(460, 470, 300, 570, RED, 12 * min(1, s))


# 11 ------------------------------------------------------------- você entra (portão)
def s_gate(cv, lt, sh):
    sky(cv, 560)
    cv.rect(0, 440, W, 760, (214, 200, 176))
    lawn(cv, 760, (126, 192, 94))
    for i in range(0, W, 36):
        cv.line(i, 360, i, 800, (80, 84, 96), 6)
    cv.line(0, 420, W, 420, (80, 84, 96), 8)
    cv.line(0, 740, W, 740, (80, 84, 96), 8)
    x = 90 + ease(lt / 0.9) * 200
    person(cv, x, 960, 1.6, "hero", "smirk", lt, walk=lt * 7 if lt < 0.9 else 0, armL="hold", armR="hold")


# 14 ------------------------------------------------------------- kit
def s_kit(cv, lt, sh):
    cv.rect(0, 0, W, H, (214, 200, 184))
    for i in range(0, W, 64):
        cv.line(i, 0, i, 620, (200, 184, 166), 3)
    person(cv, 288, 800, 1.35, "hero", "smile", lt, armL="front", armR="front")
    cv.rect(0, 660, W, H, (138, 92, 58))
    cv.rect(0, 660, W, 676, (96, 62, 38))
    for i in range(0, W, 100):
        cv.line(i, 676, i - 30, H, (122, 80, 50), 3)
    p = P(sh, 14, 0.0)
    t_items = [0.4, 1.3, 2.2, 3.1]
    # peneira
    s = pop(lt, p + t_items[0])
    if s:
        peneira(cv, (90, 985), 0.9 * s, lt, tilt=0.55, long=230)
    s = pop(lt, p + t_items[1])
    if s:
        cv.rr(220 - 60 * s, 860, 220 + 60 * s, 908, 10 * s, fill=(70, 140, 220), out=OUT, w=5)
        for i in range(-4, 5):
            cv.line(220 + i * 12 * s, 906, 220 + i * 12 * s, 936, OUT, 3)
        cv.rect(158, 905, 282, 918, (210, 210, 220), OUT, 3)
    s = pop(lt, p + t_items[2])
    if s:
        for r_ in (50, 36, 22):
            cv.ell(360, 930, r_ * s, r_ * 0.55 * s, out=(30, 140, 70), w=9)
        cv.line(398, 918, 450, 890, (30, 140, 70), 9)
    s = pop(lt, p + t_items[3])
    if s:
        cv.rr(450 - 62 * s, 850 + (1 - s) * 40, 450 + 62 * s, 950, 12 * s, fill=WHITE, out=OUT, w=5)
        for i, c in enumerate([(230, 70, 70), (240, 190, 40), (80, 190, 90)]):
            cv.rr(415 + i * 34, 870, 430 + i * 34, 920, 6, fill=c, out=OUT, w=3)
        cv.text("pH", 450, 938, 22, fill=OUT)
    s = pop(lt, P(sh, 15, 4.6) + 0.5)
    sticker(cv, "< R$ 500", 300, 560, 46, YEL, scale=s, rot=-4)


# 16 ------------------------------------------------------------- custos / margem
def s_cost(cv, lt, sh):
    cv.rect(0, 0, W, H, (148, 152, 164))
    for i in range(0, W, 80):
        cv.line(i, 0, i, 700, (136, 140, 152), 4)
    cv.rect(0, 700, W, H, (112, 114, 128))
    ph = person(cv, 288, 980, 1.5, "hero", "smile" if lt < P(sh, 17, 4.6) else "dollar", lt, armL="front", armR="hold")
    s = pop(lt, 0.8)
    sticker(cv, "R$ 15", 150, 470, 46, (120, 226, 150), scale=s, rot=-6)
    cv.text("produto", 150, 520, 28, fill=WHITE, stroke=3) if s else None
    s = pop(lt, P(sh, 17, 4.6))
    if s:
        sticker(cv, "R$ 200", 430, 430, 58, YEL, scale=s, rot=5)
        for i in range(6):
            a = lt * 6 + i * 1.05
            r = 80 + 14 * math.sin(a * 2)
            cv.line(430 + math.cos(a) * 126, 430 + math.sin(a) * 76, 430 + math.cos(a) * (126 + 14), 430 + math.sin(a) * (76 + 10), YEL2, 5)


# 18 ------------------------------------------------------------- relógio + 5 piscinas
def s_clock(cv, lt, sh):
    vgrad(cv, 0, H, (28, 40, 96), (14, 18, 52))
    p18 = P(sh, 18, 0.0)
    p19 = P(sh, 19, 2.4)
    if lt < p19:
        cv.ell(288, 420, 190, fill=WHITE, out=OUT, w=10)
        for i in range(12):
            a = i * math.pi / 6
            cv.line(288 + math.sin(a) * 160, 420 - math.cos(a) * 160, 288 + math.sin(a) * 178, 420 - math.cos(a) * 178, OUT, 8)
        u = ease((lt - p18) / 1.8)
        a = u * 2 * math.pi
        cv.line(288, 420, 288 + math.sin(a) * 140, 420 - math.cos(a) * 140, OUT, 8)
        cv.line(288, 420, 288 + math.sin(a / 12) * 90, 420 - math.cos(a / 12) * 90, RED, 12)
        cv.ell(288, 420, 14, fill=OUT)
        person(cv, 288, 1010, 0.9, "hero", "smile", lt, armL="hip", armR="hip")
    else:
        for i in range(5):
            s = pop(lt, p19 + 0.15 + i * 0.28)
            if s:
                cy = 220 + i * 120
                cv.rr(88, cy - 44 * s, 488, cy + 44 * s, 20, fill=(236, 240, 250), out=OUT, w=5)
                cv.rr(112, cy - 26, 220, cy + 26, 10, fill=(70, 175, 230), out=OUT, w=4)
                cv.text("R$ 200", 360, cy, 38, fill=OUT)
        s = pop(lt, p19 + 1.4)
        sticker(cv, "R$ 1.000", 288, 870, 64, (120, 226, 150), scale=s, rot=-3)


# 20 ------------------------------------------------------------- print do teste (celular)
def phone(cv, x0=118, y0=130, x1=458, y1=880):
    cv.rr(x0, y0, x1, y1, 38, fill=(20, 22, 30), out=OUT, w=5)
    cv.rr(x0 + 14, y0 + 20, x1 - 14, y1 - 20, 26, fill=(238, 242, 248))


def s_phone(cv, lt, sh):
    vgrad(cv, 0, H, (28, 40, 96), (14, 18, 52))
    phone(cv, 118, 90, 458, 940)
    cv.text("ANTES", 288, 160, 34, fill=OUT)
    cv.rr(150, 190, 426, 330, 16, fill=(84, 150, 56), out=OUT, w=4)
    sticker(cv, "pH 8.4", 288, 378, 34, (244, 150, 130), scale=pop(lt, 0.2))
    cv.text("DEPOIS", 288, 450, 34, fill=OUT)
    cv.rr(150, 480, 426, 620, 16, fill=(70, 175, 230), out=OUT, w=4)
    sticker(cv, "pH 7.2", 288, 668, 34, (120, 226, 150), scale=pop(lt, 0.7))


# 21 ------------------------------------------------------------- vizinha / indicação
def s_neighbor(cv, lt, sh):
    sky(cv, 520)
    lawn(cv, 700)
    cv.rect(300, 340, 540, 720, (224, 200, 168), OUT, 5)
    cv.poly([(280, 340), (420, 230), (560, 340)], fill=(208, 100, 50), out=OUT, w=5)
    cv.rect(380, 520, 450, 720, RED, OUT, 4)
    person(cv, 150, 960, 1.35, "client", "happy", lt, armL="down", armR="up")
    for i in range(3):
        u = ((lt * 0.9 + i * 0.33) % 1)
        sticker(cv, "pH 7.2", 190 + u * 160, 520 - u * 120, 22, WHITE, scale=1.0, rot=0, pad=8)
    cv.ell(460, 610, 60, 30, fill=(70, 175, 230), out=OUT, w=4)


# 22 ------------------------------------------------------------- passo 3 / séria
def s_serious(cv, lt, sh):
    cv.rect(0, 0, W, H, (22, 92, 70))
    candles(cv, lt, seed=9)
    cv.rect(0, 800, W, H, (22, 80, 62))
    ph = person(cv, 288, 1010, 1.7, "hero", "smirk", lt, armL="hip", armR="hip")
    s = pop(lt, P(sh, 23, 1.3) + 1.2)
    if s:
        for sx in (70, 506):
            cv.poly([(sx + math.cos(a * 2 * math.pi / 5 - 1.57) * (40 if a % 2 == 0 else 18) * s, 600 + math.sin(a * 2 * math.pi / 5 - 1.57) * (40 if a % 2 == 0 else 18) * s) for a in range(10)], fill=YEL2, out=OUT, w=3) if False else None
        for sx in (80, 496):
            pts = []
            for k in range(10):
                rr = (44 if k % 2 == 0 else 19) * s
                ang = k * math.pi / 5 - math.pi / 2
                pts.append((sx + math.cos(ang) * rr, 620 + math.sin(ang) * rr))
            cv.poly(pts, fill=YEL2, out=OUT, w=3)


# 24 ------------------------------------------------------------- plano
def s_plan(cv, lt, sh):
    cv.rect(0, 0, W, 700, (206, 196, 176))
    cv.rect(0, 700, W, H, (150, 112, 76))
    p25 = P(sh, 25, 2.7)
    person(cv, 190, 960, 1.35, "hero", "smirk" if lt < p25 else "smile", lt, armL="hip", armR="hold")
    cv.rr(330, 760, 540, 900, 8, fill=(100, 112, 128), out=OUT, w=5)
    cv.rect(350, 780, 520, 880, (120, 190, 235), OUT, 3)
    s = pop(lt, 0.3)
    if lt < p25:
        sticker(cv, "LIMPEZA", 288, 400, 48, WHITE, scale=s, rot=-4)
        u = pop(lt, 1.2)
        if u:
            cv.line(130, 350, 450, 450, RED, 14 * min(1, u))
    else:
        u = ease((lt - p25) / 0.35)
        cv.rr(70, 260 - (1 - u) * 300, 506, 400 - (1 - u) * 300, 14, fill=(26, 130, 70), out=OUT, w=6)
        cv.text("PLANO", 288, 306 - (1 - u) * 300, 62, fill=WHITE)
        cv.text("PISCINA LIMPA", 288, 366 - (1 - u) * 300, 30, fill=WHITE)


# 26 ------------------------------------------------------------- calendário semanal
def s_calendar(cv, lt, sh):
    vgrad(cv, 0, H, (28, 40, 96), (14, 18, 52))
    cv.rr(52, 90, 524, 600, 22, fill=(240, 244, 252), out=OUT, w=6)
    cv.rr(52, 90, 524, 165, 22, fill=(214, 60, 60), out=OUT, w=6)
    cv.text("MÊS", 288, 128, 40, fill=WHITE)
    for i, d in enumerate("SDTQQSS"):
        cv.text(d, 90 + i * 66, 195, 26, fill=OUT)
    for r in range(4):
        for c in range(7):
            x = 90 + c * 66
            y = 255 + r * 85
            cv.rr(x - 26, y - 30, x + 26, y + 30, 8, fill=WHITE, out=(200, 205, 220), w=2)
            if c == 2:
                s_ = pop(lt, 0.4 + r * 0.45)
                if s_:
                    cv.ell(x, y, 22 * s_, fill=(84, 214, 130), out=OUT, w=3)
                    cv.lines([(x - 10, y), (x - 3, y + 8), (x + 11, y - 9)], OUT, 4)
    sticker(cv, "R$ 250/mês", 288, 690, 56, YEL, scale=pop(lt, 1.9), rot=-3)
    sticker(cv, "PIX", 288, 900, 50, (120, 226, 150), scale=pop(lt, 2.15), rot=3)


# 27 ------------------------------------------------------------- 20 piscinas → ano
def s_grid(cv, lt, sh):
    cv.rect(0, 0, W, H, (124, 190, 94))
    for r in range(5):
        for c in range(4):
            x = 54 + c * 132
            y = 60 + r * 168
            cv.rect(x, y, x + 112, y + 140, (232, 222, 200), OUT, 3)
            cv.poly([(x - 6, y), (x + 56, y - 38), (x + 118, y)], fill=(208, 100, 50), out=OUT, w=3)
            s = pop(lt, (r * 4 + c) * 0.09)
            if s:
                cv.rr(x + 18, y + 20, x + 94, y + 110, 10, fill=(70, 175, 230), out=OUT, w=3)
    p28 = P(sh, 28, 2.1)
    s = pop(lt, 1.8)
    sticker(cv, "R$ 5.000/mês", 288, 360, 54, (120, 226, 150), scale=s, rot=-4)
    s = pop(lt, p28 + 0.7)
    sticker(cv, "R$ 60 mil/ano", 288, 640, 60, YEL, scale=s, rot=4)


# 29 ------------------------------------------------------------- sem chefe
def s_free(cv, lt, sh):
    cv.rect(0, 0, W, 700, (116, 78, 52))
    for i in range(0, W, 72):
        cv.line(i, 0, i, 700, (100, 66, 44), 3)
    cv.rect(0, 700, W, H, (86, 56, 40))
    person(cv, 288, 960, 1.55, "hero", "smile", lt, armL="up", armR="up")


# 30 ------------------------------------------------------------- loja indica
def s_store(cv, lt, sh):
    cv.rect(0, 0, W, 700, (218, 214, 224))
    for i in range(0, W, 80):
        cv.line(i, 0, i, 700, (204, 200, 212), 3)
    cv.rect(0, 700, W, H, (148, 100, 62))
    cv.rr(60, 140, 516, 260, 14, fill=(30, 100, 190), out=OUT, w=6)
    cv.text("LOJA DE PISCINA", 288, 200, 40, fill=WHITE)
    shake = math.sin(lt * 10) * 6 if lt > 1.3 else 0
    person(cv, 130, 980, 1.5, "suit", "smile", lt, armL="down", armR="out")
    person(cv, 446, 980, 1.5, "hero", "smile", lt, armL="out", armR="down")
    cv.ell(288, 780 + shake, 12, fill=SKIN, out=OUT, w=3)
    if lt > 1.8:
        s = pop(lt, 1.8)
        sticker(cv, "INDICA!", 288, 560, 46, YEL, scale=s, rot=3)


# 32 ------------------------------------------------------------- erro: cloro demais
def s_error(cv, lt, sh):
    backyard(cv, lt, clear=False, turbid=lt > 1.9)
    ph = person(cv, 150, 960, 1.45, "blue", "dumb", lt, armL="hold", armR="hold")
    p = ease((lt - 0.8) / 0.7)
    bucket(cv, 250 + 60 * p, 660 + 40 * p, 1.7, "CLORO", tilt=p)
    if lt > 1.2:
        for i in range(8):
            u = ((lt * 1.2 + i * 0.13) % 1)
            cv.ell(250 + 90 + i * 24 + u * 40, 740 + u * 120, 10 + i % 3 * 3, fill=(245, 245, 250), out=OUT, w=2)


# 34 ------------------------------------------------------------- vinil queima / pele irrita
def s_burn(cv, lt, sh):
    backyard(cv, lt, clear=False, turbid=True)
    ph = person(cv, 288, 960, 1.5, "client", "worry", lt, armL="front", armR="hold")
    ax, ay = ph["hands"]["L"]
    cv.line(ax + 30, ay - 40, ax - 20 + math.sin(lt * 14) * 10, ay + 30, OUT, 0)
    for i in range(4):
        cv.ell(ax - 10 + i * 10, ay - 10 + i * 6, 5, fill=(220, 50, 50))
    s = pop(lt, 0.5)
    sticker(cv, "COÇA!", 400, 520, 42, (244, 150, 130), scale=s, rot=7)


# 35 ------------------------------------------------------------- certo: teste da água
def s_test(cv, lt, sh):
    backyard(cv, lt, clear=True)
    ph = person(cv, 420, 960, 1.4, "hero", "smile", lt, armL="down", armR="up")
    hx, hy = ph["hands"]["R"]
    p36 = P(sh, 36, 1.5)
    col = (230, 70, 70) if lt < p36 else (80, 190, 90)
    cv.rr(hx - 14, hy - 80, hx + 14, hy - 10, 8, fill=col, out=OUT, w=4)
    cv.rect(hx - 16, hy - 92, hx + 16, hy - 78, (210, 210, 220), OUT, 3)
    if lt >= p36:
        s = pop(lt, p36 + 0.2)
        sticker(cv, "dose certa", 200, 520, 36, (120, 226, 150), scale=s, rot=-4)
    else:
        s = pop(lt, 0.3)
        sticker(cv, "testa 1º", 200, 520, 36, YEL, scale=s, rot=-4)


# 37 ------------------------------------------------------------- família na piscina
def s_family(cv, lt, sh):
    backyard(cv, lt, clear=True)
    cv.ell(450, 80, 56, fill=(255, 226, 90), out=OUT, w=4)
    for i in range(8):
        a = i * math.pi / 4 + lt
        cv.line(450 + math.cos(a) * 70, 80 + math.sin(a) * 70, 450 + math.cos(a) * 92, 80 + math.sin(a) * 92, (255, 226, 90), 5)
    person(cv, 140, 960, 1.3, "client", "happy", lt, armL="wave", armR="down")
    person(cv, 288, 960, 0.9, "kid", "happy", lt, armL="up", armR="up")
    person(cv, 440, 960, 1.3, "hero", "smile", lt, armL="down", armR="wave")
    cv.ell(310 + math.sin(lt * 2) * 24, 760, 52, 26, out=(240, 80, 80), w=14)


# 38 ------------------------------------------------------------- fecho
def s_end(cv, lt, sh):
    vgrad(cv, 0, H, (46, 30, 110), (8, 8, 30))
    for i in range(14):
        u = ((lt * 0.35 + i * 0.071) % 1)
        x = 60 + (i * 83) % 460
        note(cv, x + math.sin(u * 8 + i) * 24, 1060 - u * 1160, rot=u * 220 * (1 if i % 2 else -1), sc=0.8)
    person(cv, 288, 620, 0.9, "hero", "smirk", lt, armL="hip", armR="hip")


SCENES = {
    "title": s_title, "hook": s_hook, "client": s_client, "close": s_close,
    "passo1": s_passo1, "greenpool": s_green_pool, "leaves": s_leaves, "cloro": s_cloro,
    "mason": s_mason, "gate": s_gate, "passo2": s_passo2, "kit": s_kit, "cost": s_cost,
    "clock": s_clock, "phone": s_phone, "neighbor": s_neighbor, "serious": s_serious,
    "plan": s_plan, "calendar": s_calendar, "grid": s_grid, "free": s_free,
    "store": s_store, "error": s_error, "burn": s_burn, "test": s_test,
    "family": s_family, "end": s_end,
}

# (cena, primeira frase, transição)
SHOTS = [
    ("title", 1, None), ("hook", 2, None), ("client", 3, None), ("close", 4, "wipe"),
    ("passo1", 5, None), ("greenpool", 6, None), ("leaves", 7, None), ("cloro", 8, None),
    ("mason", 10, None), ("gate", 11, "wipe"), ("passo2", 12, None), ("kit", 14, None),
    ("cost", 16, None), ("clock", 18, None), ("phone", 20, None), ("neighbor", 21, None),
    ("serious", 22, "wipe"), ("plan", 24, None), ("calendar", 26, None), ("grid", 27, None),
    ("free", 29, None), ("store", 30, None), ("error", 32, "wipe"), ("burn", 34, None),
    ("test", 35, None), ("family", 37, None), ("end", 38, None),
]
