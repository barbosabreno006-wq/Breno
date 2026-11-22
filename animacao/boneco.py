#!/usr/bin/env python3
"""
Boneco articulado (rig 2D cutout com esqueleto) — substitui o Ator "figurinha".

Cada personagem é desenhado a cada frame com peças separadas e articulações:
  coxa + canela (joelho), braço + antebraço (cotovelo, IK de 2 ossos), tronco e cabeça
  (girando no pescoço). Uma biblioteca de movimentos contínuos é escolhida pela
  expressão/pose: respiração, troca de peso, gesticular falando, caminhada de verdade,
  rir sacudindo o corpo, choro com ombros tremendo, susto com braços pra cima, aceno…

A interface é a mesma do gerar_video.Ator (desenhar/spr), então os vídeos antigos
funcionam trocando Ator → Boneco.
"""
import math

from PIL import Image

import gerar_video as g
from gerar_video import Pincel, OUTLINE

OX = 50                 # margem lateral do canvas (braços abertos não cortam)
CW, CH = 340 + 2 * OX, 640
OMBRO_E, OMBRO_D = (100, 335), (240, 335)
L_BRACO, L_ANTE = 66, 64
QUADRIL_Y = 440
L_COXA, L_CANELA = 70, 66
POSES_RIG = {"idle", "aponta", "bate", "bate2", "entrega", "acena", "anda1", "anda2", "anda", "corre",
             "abraca_d", "abraca_e", "bolso", "palmas", "bracos_abertos"}


def _s(x):
    return math.sin(x)


def ik(ombro, alvo, l1, l2, dobra=1):
    """IK de 2 ossos: retorna (cotovelo, mão)."""
    sx, sy = ombro
    dx, dy = alvo[0] - sx, alvo[1] - sy
    d = max(1e-3, math.hypot(dx, dy))
    d2 = min(d, l1 + l2 - 0.5)
    a = math.atan2(dy, dx)
    c = (l1 * l1 + d2 * d2 - l2 * l2) / (2 * l1 * d2)
    b = math.acos(max(-1, min(1, c)))
    ang = a + dobra * b
    cot = (sx + l1 * math.cos(ang), sy + l1 * math.sin(ang))
    mao = (sx + d2 * math.cos(a), sy + d2 * math.sin(a))
    return cot, mao


def fk(raiz, ang1, ang2, l1, l2):
    """Perna por ângulos (0 = para baixo, + = para a direita da tela)."""
    jx = raiz[0] + l1 * math.sin(ang1)
    jy = raiz[1] + l1 * math.cos(ang1)
    a2 = ang1 + ang2
    return (jx, jy), (jx + l2 * math.sin(a2), jy + l2 * math.cos(a2))


def membro(p, pts, w, cor):
    """Membro de 2+ segmentos sem 'costura' na articulação (contorno de tudo, depois o recheio)."""
    s = p.s
    for col, ww in ((OUTLINE, w + 2 * g.OW), (cor, w)):
        q = [(x * s, y * s) for x, y in pts]
        p.d.line(q, fill=col, width=int(ww * s), joint="curve")
        r = ww * s / 2
        for (x, y) in q:
            p.d.ellipse((x - r, y - r, x + r, y + r), fill=col)


def _ret_pts(x0, y0, x1, y1, r, sk=0.0, n=6):
    """Pontos de um retângulo arredondado com cisalhamento horizontal (saia balançando)."""
    pts = []
    cs = [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]
    for cx, cy, a0 in cs:
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            pts.append((x + sk * (y - y0) / max(1, y1 - y0), y))
    return pts


class Boneco:
    AMP = 1.0          # multiplicador de movimento ocioso (1.0 = antigo; 1.8 = bem mais vivo)

    def __init__(self, pal):
        self.pal = pal
        self.ator = g.Ator(pal)
        self.cab = {}
        self.fala_ativa = False       # setado de fora (janela de fala)
        self.amp = 0.0                # amplitude da voz (0–1) p/ gestos
        self.ultimo_bob = 0.0
        self.semente = sum(sum(c) if isinstance(c, tuple) else 0 for c in pal.values()) % 97

    # compatibilidade (gelo / sprites estáticos)
    def spr(self, expr, pose, fechado=False):
        return self.ator.spr(expr, pose, fechado)

    def cabeca(self, expr, fechado, olhar=0):
        k = (expr, fechado, olhar)
        if k not in self.cab:
            self.cab[k] = g.desenhar_personagem(self.pal, expr, "idle", fechado, so_cabeca=True, olhar=olhar)
        return self.cab[k]

    # ------------------------------------------------------------------
    def _movimento(self, t, expr, pose):
        """Devolve o 'estado do esqueleto' para este instante."""
        tw = 2 * math.pi
        S = dict(hx=0.0, tdy=0.0, hrot=0.0, hdx=0.0, hdy=0.0, rot=0.0, bob=0.0, sq=0.0,
                 ombro_dy=0.0, pernas=None, maos_rosto=False)
        # respiração + troca de peso + cabeça viva (sempre)
        S["tdy"] = 2.5 * _s(t * tw * 0.9)
        S["ombro_dy"] = 2.0 * _s(t * tw * 0.9)
        S["hrot"] = 4.0 * _s(t * 0.9) + 2.0 * _s(t * 2.3 + 1)
        S["hx"] = 3.0 * _s(t * 0.7)
        S["rot"] = 1.2 * _s(t * 0.7 + 0.4)
        S["bob"] = 4 * _s(t * tw * 0.9)
        # braços em repouso balançando
        sw = 6 * _s(t * 1.3)
        A = self.AMP
        sw *= A
        S["hrot"] *= A
        S["hx"] *= A
        S["rot"] *= A
        S["bob"] *= (0.5 + 0.5 * A)
        S["tdy"] *= A
        # olhar: desvia os olhos de tempos em tempos (-1 esquerda, 0 frente, 1 direita)
        ol = _s(t * 0.55 + self.semente) + 0.6 * _s(t * 1.7 + self.semente * 2)
        S["olhar"] = 0 if abs(ol) < 0.7 * (1.0 if A > 1 else 9) else (1 if ol > 0 else -1)
        mE = (78 - 4 + sw * 0.5, 452)
        mD = (262 + 4 + sw * 0.5, 452)
        dobraE, dobraD = 1, -1

        falando = self.fala_ativa and expr not in ("chora", "cinza")
        if falando:
            a = self.amp
            S["hrot"] += 7 * a * _s(t * 9) + 4 * _s(t * 3.1)
            S["hdy"] += -5 * a * abs(_s(t * 7))
            S["bob"] += 3 * a * abs(_s(t * 6))
            S["rot"] += 2.0 * _s(t * 1.6)
            # mão direita gesticula (explicando), troca de gesto a cada ~1.1 s
            fase = t / 1.1
            k = int(fase)
            x = fase - k
            gestos = [(300, 380), (285, 330), (310, 410), (270, 360)]
            ga, gb = gestos[k % 4], gestos[(k + 1) % 4]
            e = g.ease_io(min(1, x * 2.2))
            gx = ga[0] + (gb[0] - ga[0]) * e + 10 * a * _s(t * 11)
            gy = ga[1] + (gb[1] - ga[1]) * e + 14 * a * _s(t * 8)
            mD = (gx, gy)
            if k % 3 == 1:          # às vezes as duas mãos
                mE = (40 + 8 * _s(t * 5), 370 + 10 * a * _s(t * 8))

        # gestos espontâneos quando parado (cada boneco num ritmo próprio)
        if not falando and pose == "idle" and expr in ("neutro", "feliz", "fala", "surpreso_leve"):
            per = 3.6 + (self.semente % 7) * 0.25
            u = (t + self.semente * 0.37) / per
            k = int(u)
            x = (u - k) * per
            if x < 1.6:
                w = g.ease_io(min(1, x / 0.35)) * g.ease_io(min(1, (1.6 - x) / 0.35))
                tipo = (k + self.semente) % 4
                def mix(a, b):
                    return (a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w)
                if tipo == 0:      # dá de ombros
                    mE, mD = mix(mE, (30, 380)), mix(mD, (310, 380))
                    S["ombro_dy"] -= 10 * w
                    S["hrot"] += 8 * w
                    dobraE, dobraD = -1, 1
                elif tipo == 1:    # mão no queixo, pensando
                    mD = mix(mD, (205, 262))
                    S["hrot"] -= 7 * w
                    dobraD = 1
                elif tipo == 2:    # mão na cintura + inclina
                    mE = mix(mE, (100, 440))
                    S["rot"] -= 3 * w
                    S["hrot"] -= 6 * w
                else:              # coça a cabeça
                    mD = mix(mD, (300 + 6 * _s(t * 25) * w, 150))
                    dobraD = 1
                    S["hrot"] += 6 * w

        if expr in ("feliz",):
            S["bob"] += 5 * abs(_s(t * tw * 1.6))
            S["hrot"] += 5 * _s(t * tw * 0.8)
        elif expr == "ri":
            S["tdy"] += 7 * abs(_s(t * tw * 3.2))
            S["bob"] += 8 * abs(_s(t * tw * 3.2))
            S["hrot"] += -6 + 5 * _s(t * tw * 3.2)
            S["hdy"] -= 6 * abs(_s(t * tw * 3.2))
            S["sq"] = 0.03 * _s(t * tw * 6.4)
            mE = (150, 440 + 6 * _s(t * tw * 3.2))       # mãos na barriga
            mD = (190, 440 + 6 * _s(t * tw * 3.2 + 1))
            dobraE, dobraD = -1, 1
        elif expr == "chora":
            tr = _s(t * tw * 7)
            S["ombro_dy"] += 4 * tr + 6
            S["tdy"] += 3 * tr
            S["hrot"] = 3 * _s(t * tw * 7) + 3 * _s(t * 0.8)
            S["hdy"] += 10
            ciclo = (t % 4.0)
            if ciclo < 2.4:         # enxuga os olhos com as mãos
                S["maos_rosto"] = True
                mE = (125 + 6 * _s(t * 9), 205 + 6 * _s(t * 7))
                mD = (215 + 6 * _s(t * 9 + 1), 205 + 6 * _s(t * 7 + 1))
                dobraE, dobraD = -1, 1
        elif expr == "triste":
            S["ombro_dy"] += 8
            S["hdy"] += 8
            S["hrot"] = 6 + 2 * _s(t * 0.6)
            S["bob"] *= 0.5
            mE, mD = (92, 456), (248, 456)
        elif expr == "surpreso":
            tr = _s(t * tw * 9)
            S["bob"] += 3 * abs(tr)
            S["hdy"] -= 6
            S["hrot"] = 2 * tr
            mE = (52 + 4 * tr, 240 + 5 * tr)
            mD = (288 - 4 * tr, 240 - 5 * tr)
        elif expr == "bravo":
            tr = _s(t * tw * 5)
            S["hrot"] = 4 * tr
            S["rot"] += 1.5 * tr
            S["bob"] += 3 * abs(tr)
            mE, mD = (100, 440), (240, 440)          # mãos na cintura, cotovelos pra fora
            dobraE, dobraD = 1, -1
            S["akimbo"] = True
        elif expr == "cinza":
            S["hrot"] *= 0.2
            S["bob"] *= 0.3

        # ---------- poses do braço direito ----------
        if pose == "entrega":
            mD = (302, 372)
            S["bob"] = 4 * _s(t * tw * 0.9)          # igual ao Filme.mao() → objetos não escorregam
            S["tdy"] = 0
            S["rot"] = 0
            S["hx"] = 0
            S["sq"] = 0
            S["ombro_dy"] = 0
            dobraD = 1
        elif pose == "aponta":
            jab = 8 * max(0, _s(t * tw * 1.2)) ** 3
            mD = (318 + jab, 252 - jab * 0.6)
            S["dedo"] = True
        elif pose in ("bate", "bate2"):
            k = (t * 4.2) % 1
            mD = (300, 260) if k < 0.5 else (318, 290)
            dobraD = 1
        elif pose == "acena":
            mD = (290 + 26 * _s(t * tw * 2.4), 210 + 6 * abs(_s(t * tw * 2.4)))
            dobraD = 1
            S["hrot"] += 4 * _s(t * tw * 1.2)
            S["bob"] += 3 * abs(_s(t * tw * 2.4))

        elif pose == "abraca_d":          # abraça quem está à direita (braço passa por trás dele)
            mD = (372, 372 + 4 * _s(t * 2))
            dobraD = 1
            mE = (215, 405)
            S["hrot"] = -9 + 2 * _s(t * 1.5)
            S["hdx"] = 12
            S["bob"] = 2 * _s(t * 2)
        elif pose == "abraca_e":
            mE = (-32, 372 + 4 * _s(t * 2))
            dobraE = -1
            mD = (125, 405)
            S["hrot"] = 9 + 2 * _s(t * 1.5)
            S["hdx"] = -12
            S["bob"] = 2 * _s(t * 2)
        elif pose == "bolso":
            mE, mD = (122, 446), (218, 446)
            dobraE, dobraD = 1, -1
            S["bolso"] = True
        elif pose == "palmas":
            k = max(0, _s(t * 2 * math.pi * 2.6))
            mE = (152 - 26 * k, 365)
            mD = (188 + 26 * k, 365)
            dobraE, dobraD = 1, -1
            S["bob"] += 2 * k
            S["esq_frente"] = True
        elif pose == "bracos_abertos":
            a = 6 * _s(t * 3)
            mE, mD = (10 - a, 330), (330 + a, 330)
            dobraE, dobraD = -1, 1
            S["bob"] += 3 * abs(_s(t * 3))

        # ---------- pernas / caminhada ----------
        if pose in ("anda1", "anda2", "anda", "corre"):
            vel = 2.2 if pose == "corre" else 1.6
            amp = 0.55 if pose == "corre" else 0.42
            ph = t * tw * vel
            S["pernas"] = (ph, amp)
            S["bob"] = 7 * abs(_s(ph)) + (4 if pose == "corre" else 0)
            S["rot"] = 2.5 * _s(ph) + (4 if pose == "corre" else 0)
            S["hrot"] = 3 * _s(ph * 2) * 0.5 + S["hrot"] * 0.3
            S["tdy"] = 3 * abs(_s(ph))
            if not falando and expr not in ("ri", "chora", "surpreso", "bravo"):
                ab = 70 if pose == "corre" else 55
                mE = (100 - 22 + ab * _s(ph), 448 - 18 * abs(_s(ph)))
                mD = (240 + 22 - ab * _s(ph), 448 - 18 * abs(_s(ph)))
                if pose == "corre":
                    dobraE, dobraD = 1, -1
        S["mE"], S["mD"], S["dobraE"], S["dobraD"] = mE, mD, dobraE, dobraD
        return S

    # ------------------------------------------------------------------
    def render(self, t, expr, pose, fechado):
        pal = self.pal
        S = self._movimento(t, expr, pose)
        p = Pincel(CW, CH)
        o = OX
        pele = pal["pele"]
        tipo = pal["tipo"]
        vestido = tipo in ("vovo", "moca")
        vovo = tipo == "vovo"
        hx = S["hx"]
        tdy = S["tdy"]

        # ---- pernas ----
        quadris = ((135 + hx, QUADRIL_Y), (205 + hx, QUADRIL_Y))
        if S["pernas"]:
            ph, amp = S["pernas"]
            angs = []
            for i, lado in enumerate((0, math.pi)):
                sph = _s(ph + lado)
                a1 = amp * sph
                cph = math.cos(ph + lado)
                a2 = -max(0, cph) * amp * 1.5          # joelho dobra quando a perna vem à frente
                angs.append((a1, a2))
        else:
            angs = [(0.0, 0.0), (0.0, 0.0)]
        pernas = []
        for (hx_, hy_), (a1, a2), lado in zip(quadris, angs, (-1, 1)):
            if vestido:
                raiz = (hx_, 520)
                joe, pe = fk(raiz, a1 * 0.6, a2 * 0.5, 30, 30)
                pe = (pe[0], min(pe[1], 588))
                pernas.append((raiz, joe, pe, lado))
            else:
                joe, pe = fk((hx_, hy_), a1, a2, L_COXA, L_CANELA)
                # pé apoiado nunca afunda abaixo do chão
                pe = (pe[0], min(pe[1], 576))
                pernas.append(((hx_, hy_), joe, pe, lado))
        # perna mais "atrás" primeiro
        for raiz, joe, pe, lado in pernas:
            cor = pele if vestido else pal["calca"]
            w = 30 if vestido else 38
            membro(p, [(raiz[0] + o, raiz[1]), (joe[0] + o, joe[1]), (pe[0] + o, pe[1])], w, cor)
        for raiz, joe, pe, lado in pernas:
            sx = pe[0] + 10 * lado + o
            sy = pe[1] + 17
            p.elipse((sx - 34, sy - 20, sx + 34, sy + 20), pal["sapato"])

        # ---- vestido ----
        if vestido:
            sk = 0
            if S["pernas"]:
                sk = 10 * _s(S["pernas"][0])
            p.poli([(x + o + hx, y + tdy * 0.5) for x, y in _ret_pts(100, 380, 240, 560, 50, sk)],
                   pal.get("vestido", pal["camisa"]))

        # ---- ombros ----
        oy = S["ombro_dy"] + tdy
        oE = (OMBRO_E[0] + hx, OMBRO_E[1] + oy)
        oD = (OMBRO_D[0] + hx, OMBRO_D[1] + oy)

        def braco(ombro, alvo, dobra, mao=True):
            alvo = (alvo[0] + hx, alvo[1] + tdy)
            cot, m = ik(ombro, alvo, L_BRACO, L_ANTE, dobra)
            membro(p, [(ombro[0] + o, ombro[1]), (cot[0] + o, cot[1]), (m[0] + o, m[1])], 33, pal["camisa"])
            if mao:
                p.elipse((m[0] + o - 20, m[1] - 20, m[0] + o + 20, m[1] + 20), pele)
            return cot, m

        def mao_so(m):
            p.elipse((m[0] + o - 20, m[1] - 20, m[0] + o + 20, m[1] + 20), pele)

        rosto = S["maos_rosto"] or S.get("bolso", False)
        if not S.get("esq_frente"):
            _, mE = braco(oE, S["mE"], S["dobraE"], mao=not rosto)

        # ---- tronco ----
        tb = (92 + hx + o, 310 + tdy, 248 + hx + o, 470 + tdy * 0.4)
        p.ret(tb, pal["camisa"], r=48)
        if pal.get("faixas"):
            for y in (380, 420):
                p.ret((96 + hx + o, y + tdy, 244 + hx + o, y + 14 + tdy), (225, 230, 235), r=4, ow=0)
        if not vovo:
            p.ret((150 + hx + o, 318 + tdy, 190 + hx + o, 330 + tdy), (255, 225, 140), r=6, ow=0)

        if S.get("esq_frente"):
            _, mE = braco(oE, S["mE"], S["dobraE"], mao=not rosto)
        _, mD = braco(oD, S["mD"], S["dobraD"], mao=not rosto)
        if S.get("dedo") and not rosto:
            p.capsula((mD[0] + o + 10, mD[1] - 14), (mD[0] + o + 18, mD[1] - 46), 13, pele, ow=4)

        def X(x, y):
            return (x + hx + o, y + tdy)
        if pal.get("gravata"):
            p.poli([X(160, 318), X(180, 318), X(186, 420), X(170, 440), X(154, 420)], pal["gravata"], ow=4)
        if pal.get("faixa_pres"):
            p.poli([X(100, 322), X(134, 312), X(250, 446), X(216, 462)], (40, 150, 70), ow=4)
            p.poli([X(112, 324), X(124, 320), X(238, 450), X(226, 455)], (250, 210, 40), ow=0)
        if pal.get("bolsa"):
            p.linha([X(110, 318), X(232, 452)], fill=(120, 72, 40), w=16)
            p.ret((*X(196, 420), *X(276, 500)), (150, 96, 54), r=12)
            p.ret((*X(196, 420), *X(276, 448)), (176, 116, 66), r=8, ow=5)
        corpo = p.pronto()

        # ---- cabeça (gira no pescoço) ----
        cab = self.cabeca(expr, fechado, S.get("olhar", 0))
        cab = cab.rotate(S["hrot"], resample=Image.BICUBIC, center=(170, 300))
        corpo.alpha_composite(cab, (int(o + hx + S["hdx"]), int(tdy + S["hdy"])))
        S["maos"] = ((mE[0] + o, mE[1]), (mD[0] + o, mD[1]))
        if S["maos_rosto"]:  # mãos por cima do rosto (choro)
            q = Pincel(CW, CH)
            for m in (mE, mD):
                q.elipse((m[0] + o - 22, m[1] - 22, m[0] + o + 22, m[1] + 22), pele)
            corpo.alpha_composite(q.pronto())
        return corpo, S

    def desenhar(self, base, t, cx, by, escala=1.0, expr="neutro", pose="idle",
                 rot=0.0, piscar=True, alpha=1.0, pulo=0.0, sx=1.0):
        if pose not in POSES_RIG:            # poses especiais (ajoelhado…) usam o sprite antigo
            return self.ator.desenhar(base, t, cx, by, escala, expr, pose, rot, piscar, alpha, pulo)
        fechado = piscar and (int(t * g.FPS) % 95) in (0, 1, 2)
        img, S = self.render(t, expr, pose, fechado)
        self.ultimo_bob = S["bob"] + pulo
        r_ = 1 + 0.012 * math.sin(t * 2 * math.pi * 0.9) + S["sq"]
        self.maos_mundo = [(cx + (1 if sx >= 0 else -1) * (x - CW / 2) * escala * (2 - r_),
                            by - S["bob"] - pulo - (CH - y) * escala * r_) for x, y in S["maos"]]
        respira = 1 + 0.012 * math.sin(t * 2 * math.pi * 0.9) + S["sq"]
        if sx < 0:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        g.colar(base, img, cx, by - S["bob"] - pulo, escala, sx=2 - respira, sy=respira,
                rot=rot + S["rot"], alpha=alpha)
