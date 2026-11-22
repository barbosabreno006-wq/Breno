#!/usr/bin/env python3
"""
"A Foto do Futuro" — no dia da foto da escola, toda criança recebe uma foto de si mesma daqui a 25 anos.
A professora Marta decide o destino de cada aluno… e o Pedrinho, "caso perdido", aparece de roupa azul de hospital.

Feito no estilo da referência enviada pelo usuário:
  * 80 cortes (grade medida na referência, alinhada à narração por palavras) e movimento de câmera por cena;
  * cada cena com lugar e objetos próprios (sala, mural com barbante, polaroids, hospital, mapa, tomada…);
  * só legenda + balões de fala (sem títulos extras); boca mexe nas falas; câmera lisa.

    python3 animacao/video_foto.py --narracao narr.mp3 --transcricao transcricao.json --camera camera.json \
        --ancoras ancoras.json --fonte Poppins.ttf
"""
import argparse
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_video as g  # noqa: E402
import video_carta as vc  # noqa: E402
import video_estatua as ve  # noqa: E402
import video_areia as va  # noqa: E402
import ambiente as amb  # noqa: E402
import boneco  # noqa: E402
import cenario_rico as cr  # noqa: E402
import cenario_escola as cs  # noqa: E402
from gerar_video import (FPS, OUT_W, OUT_H, WW, WH, Pincel, gradiente, brilho,  # noqa: E402
                         ease_out, ease_io, particulas)

g.HANDHELD = False
boneco.Boneco.AMP = 1.7
random.seed(2525)

MARTA = dict(pele=(232, 186, 150), cabelo=(120, 78, 56), camisa=(150, 90, 170), calca=(110, 70, 130),
             sapato=(60, 50, 60), tipo="vovo", vestido=(150, 90, 170))
MARTA_V = dict(MARTA, cabelo=(226, 226, 232), camisa=(235, 242, 248), vestido=(235, 242, 248))
PEDRINHO = dict(pele=(232, 186, 150), cabelo=(240, 200, 80), camisa=(110, 190, 130), calca=(80, 90, 150),
                sapato=(230, 230, 235), tipo="menino")
PEDRO_AD = dict(pele=(232, 186, 150), cabelo=(240, 200, 80), camisa=(70, 140, 200), calca=(60, 120, 180),
                sapato=(240, 240, 245), tipo="pai", bigode=False, chapeu=(70, 140, 200))
CIRURGIAO = dict(pele=(214, 160, 120), cabelo=(60, 44, 36), camisa=(80, 170, 170), calca=(70, 150, 150),
                 sapato=(240, 240, 245), tipo="pai", bigode=False, chapeu=(80, 170, 170))
LUCIA = dict(pele=(222, 170, 128), cabelo=(70, 44, 32), camisa=(214, 120, 160), calca=(0, 0, 0),
             sapato=(120, 70, 90), tipo="moca", vestido=(214, 120, 160))
VITORIA = dict(pele=(214, 160, 120), cabelo=(150, 70, 200), camisa=(255, 100, 190), calca=(0, 0, 0),
               sapato=(200, 60, 140), tipo="moca", vestido=(255, 100, 190))
RAFAEL = dict(pele=(196, 140, 100), cabelo=(35, 28, 26), camisa=(240, 150, 60), calca=(70, 80, 110),
              sapato=(50, 50, 55), tipo="menino")
FOTOGRAFO = dict(pele=(232, 186, 150), cabelo=(90, 60, 40), camisa=(230, 230, 236), calca=(60, 62, 80),
                 sapato=(40, 40, 45), tipo="pai")
MEDICO = dict(pele=(232, 186, 150), cabelo=(150, 150, 156), camisa=(248, 248, 252), calca=(120, 140, 170),
              sapato=(240, 240, 245), tipo="pai", bigode=False, gravata=(80, 150, 210))
vc.DESTAQUE_VERMELHO = set()
_C = {}


class FilmeFoto(va.FilmeAreia):
    def __init__(self, palavras, fc, dur_total, narracao, camera, ancoras):  # noqa: C901
        self.fc = fc
        self.dur_total = dur_total
        print("• pré-renderizando arte…")
        self.env = self.envelope(narracao)
        P_ = lambda pal: ve.Pers(pal, self)  # noqa: E731
        self.marta, self.martav = P_(MARTA), P_(MARTA_V)
        self.pedro, self.pedroad, self.cir = P_(PEDRINHO), P_(PEDRO_AD), P_(CIRURGIAO)
        self.lucia, self.vit, self.raf, self.fot, self.med = P_(LUCIA), P_(VITORIA), P_(RAFAEL), P_(FOTOGRAFO), P_(MEDICO)
        self.kids = [P_(c) for c in ve.POVO]
        self.blur = {}
        self.f_leg = vc.fonte(fc, 50)
        self.palavras = palavras
        self.blocos = self._blocos(palavras)
        self.cortes = [(0.0, 0)]
        self.spec, self.u, self.sub = None, 0.0, 0

        # fotos (polaroids)
        self.ph_palco = cs.ph_palco([VITORIA])
        self.ph_grades = cs.ph_grades(RAFAEL)
        self.ph_hosp = cs.ph_hospital(CIRURGIAO, MARTA_V, PEDRO_AD)
        self.pol_palco = cs.polaroid(fc, self.ph_palco, "25 ANOS DEPOIS", 700)
        self.pol_grades = cs.polaroid(fc, self.ph_grades, "25 ANOS DEPOIS", 700)
        self.pol_hosp = cs.polaroid(fc, self.ph_hosp, "25 ANOS DEPOIS", 700)
        self.pol_hosp_q = cs.polaroid(fc, self.ph_hosp, "CIRURGIÃO?", 700)
        pb = Pincel(360, 300)
        pb.ret((0, 0, 360, 300), (50, 34, 96), r=0, ow=0)
        im_b = pb.pronto()
        im_b.alpha_composite(brilho((360, 300), (170, 130, 255), 150, 0.8))
        ImageDraw.Draw(im_b).text((180 - vc.fonte(fc, 220).getlength("?") / 2, 20), "?", font=vc.fonte(fc, 220),
                                  fill=(255, 255, 255))
        self.pol_branca = cs.polaroid(fc, im_b, "25 ANOS DEPOIS", 700)
        retratos = []
        for i, pal in enumerate((PEDRINHO, VITORIA, RAFAEL, dict(MARTA, camisa=(90, 170, 120)), LUCIA, CIRURGIAO)):
            p = Pincel(360, 300)
            p.ret((0, 0, 360, 300), [(190, 220, 240), (240, 200, 220), (200, 230, 200), (240, 226, 180), (210, 200, 240),
                                     (190, 226, 226)][i], r=0, ow=0)
            im = p.pronto()
            f_ = cs._fig(pal, "feliz", 0.55)
            im.alpha_composite(f_, (180 - f_.width // 2, 300 - f_.height + 10))
            retratos.append(im)
        self.mural_img = cs.mural(fc, [self.ph_palco, self.ph_grades] + retratos[2:] + [retratos[0]] + retratos[:2])
        self.mural_img2 = cs.mural(fc, [self.ph_palco, self.ph_grades, self.ph_hosp] + retratos)

        self.dlg = {"marta": [(58.12, 60.4), (66.02, 68.9), (69.02, 72.0), (115.18, 116.2)]}
        self.beats = self._beats()
        ra = np.array([a for a, _ in ancoras])
        oa = np.array([b for _, b in ancoras])
        n = len(camera)
        iniciais = []
        for i, c in enumerate(camera):
            a = 0.0 if i == 0 else float(np.interp(c["ini"], ra, oa))
            b = float(np.interp(c["ini"] + c["dur"], ra, oa)) if i + 1 < n else dur_total
            iniciais.append((a, max(0.2, b - a)))
        # sub-índice: quantas cenas anteriores caíram no mesmo beat
        sub_cont, ult_beat = {}, []
        for a, d in iniciais:
            bi = self._achar_idx(a + d / 2)
            sub_cont[bi] = sub_cont.get(bi, -1) + 1
            ult_beat.append((bi, sub_cont[bi]))
        self.planos, self.sfx_cortes = [], []
        for i, ((a, d), c) in enumerate(zip(iniciais, camera)):
            self.planos.append((a, d, self._fazer(i, c, ult_beat[i]), "", "corte"))
            if i:
                self.sfx_cortes.append(a)
        self.p_preto = None

    # ----- câmera copiada da referência -----
    def spec_de(self, i, c):
        r = c.get("r", 0)
        if r >= 0.4:
            return min(1.3, max(0.85, c["zoom"])), max(-0.12, min(0.12, c["dx"])), max(-0.12, min(0.12, c["dy"]))
        return (1.07 if i % 2 == 0 else 0.95), 0.0, 0.0

    def _fazer(self, i, c, bs):
        z, dx, dy = self.spec_de(i, c)
        bi, sub = bs

        def fn(t, d):
            self.spec = (z, dx, dy)
            self.u = ease_io(min(1, t / max(0.1, d)))
            self.sub = sub
            return self.beats[bi][1](t, d, self.T)
        return fn

    def cam(self, m, cx, cy, zb):
        z, dx, dy = self.spec if self.spec else (1.0, 0, 0)
        u = self.u
        s = self.sub
        cx = cx + (-1, 0, 1)[s % 3] * 70
        zb = zb * (1.0, 1.12, 1.25, 1.06)[s % 4]
        zz = zb * (1 + (z - 1) * u) if z >= 1 else zb / z * (z ** u)
        vw, vh = WW / zz, WH / zz
        return g.camera(m, cx - dx * u * vw, cy - dy * u * vh, zz)

    def _achar_idx(self, t):
        idx = 0
        for i, (ini, _) in enumerate(self.beats):
            if ini <= t:
                idx = i
        return idx

    # ----- utilidades de cena -----
    def balao_t(self, f, txt, x, y, t0):
        if self.T >= t0:
            self.balao(f, txt, x, y, self.T - t0)

    def S(self, bg, chars=(), props=(), cam=(540, 1250, 1.3), t=0.0, bal=(), fx=None):
        m = bg.copy()
        for pers, x, by, e, expr, pose, fala, sx in chars:
            cr.sombra(m, x, by - 4, e * 250)
            pers(m, t, x, by, e, expr=expr, pose=pose, fala=fala, sx=sx)
        for pr in props:
            pr(m)
        f = self.cam(m, *cam)
        for txt, x, y, t0 in bal:
            if len(txt) > 24:
                w_ = txt.split(" ")
                mid = len(txt) / 2
                acum, cut = 0, len(w_) // 2
                for i_, p_ in enumerate(w_):
                    acum += len(p_) + 1
                    if acum >= mid:
                        cut = i_ + 1
                        break
                self.balao_t(f, " ".join(w_[:cut]), x, y, t0)
                self.balao_t(f, " ".join(w_[cut:]), x, y + OUT_H * 0.085, t0 + 0.25)
            else:
                self.balao_t(f, txt, x, y, t0)
        if fx:
            f = fx(f)
        return f

    def C(self, pers, x, by, e=1.4, expr="neutro", pose="idle", fala=None, sx=1):
        return (pers, x, by, e, expr, pose, fala, sx)

    def pol(self, img, x, y, w=None, rot=0.0):
        def f(m):
            im = img if not w else img.resize((w, int(img.height * w / img.width)), Image.BICUBIC)
            if rot:
                im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
            m.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))
        return f

    def sala(self, quadro="", dia="12"):
        return cs.sala_aula(self.fc, quadro, dia)

    def foto_cena(self, t, img, cor=(60, 50, 70), z=1.0):
        bg = gradiente(WW, WH, cor, _tom(cor, 0.6))
        k = 1 + 0.03 * math.sin(t * 1.5)
        return self.S(bg, props=[self.pol(img, 540, 960 + 6 * math.sin(t * 2), int(900 * k), 2 * math.sin(t * 1.2))],
                      cam=(540, 1000, z), t=t)

    # ----- beats -----
    def _beats(self):
        R = []

        def B(ini):
            def deco(fn):
                R.append((ini, fn))
                return fn
            return deco

        sala = self.sala
        C = self.C
        K = self.kids

        @B(0.0)
        def b_dia_foto(t, d, T):
            flash = max(0, 1 - abs(T - 1.4) * 5)

            def fx(f):
                return Image.blend(f, Image.new("RGB", f.size, (255, 255, 255)), min(1, flash)) if flash > 0 else f
            return self.S(sala(), [C(self.fot, 280, 1840, 1.35, "feliz", "idle"), C(K[0], 640, 1830, 1.1, "feliz"),
                                   C(K[1], 840, 1830, 1.1, "feliz"), C(K[2], 1000, 1830, 1.1, "feliz")],
                          cam=(540, 1250, 1.2), t=t, fx=fx)

        @B(2.54)
        def b_recebe(t, d, T):
            return self.foto_cena(t, self.pol_branca, (74, 70, 110))

        @B(6.78)
        def b_defeito(t, d, T):
            return self.S(sala(), [C(K[3], 540, 1840, 1.5, "surpreso", "entrega")], cam=(540, 1250, 1.35), t=t,
                          props=[self.pol(self.pol_branca, 760, 1330, 380, 8)])

        @B(8.42)
        def b_um_momento(t, d, T):
            return self.foto_cena(t, self.pol_palco, (90, 70, 120), 1.05)

        @B(11.38)
        def b_vitoria(t, d, T):
            bg = gradiente(WW, WH, (60, 26, 96), (28, 12, 50))
            return self.S(bg, [C(self.vit, 540, 1800, 1.6, "feliz", "bracos_abertos")], cam=(540, 1250, 1.2), t=t,
                          props=[lambda m: m.alpha_composite(brilho((1000, 1000), (255, 230, 255), 480, 0.6), (40, 300))])

        @B(14.20)
        def b_fila(t, d, T):
            chars = [C(self.vit, 220, 1840, 1.25, "ri", "idle")] + [C(K[i], 520 + i * 170, 1830, 1.0, "feliz", "acena")
                                                                   for i in range(4)]
            return self.S(sala(), chars, cam=(640, 1250, 1.2), t=t)

        @B(17.10)
        def b_grades(t, d, T):
            return self.foto_cena(t, self.pol_grades, (60, 62, 72), 1.05)

        @B(19.52)
        def b_sozinho(t, d, T):
            chars = [C(self.raf, 300, 1840, 1.4, "triste", "bolso")] + [C(K[i], 700 + i * 150, 1830, 1.0, "neutro")
                                                                       for i in range(3)]
            return self.S(sala(), chars, [lambda m: m.alpha_composite(cs.carteira(420), (130, 1580))], (540, 1250, 1.25), t)

        @B(21.40)
        def b_marta(t, d, T):
            return self.S(sala(), [C(self.marta, 540, 1860, 1.7, "feliz", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(25.04)
        def b_mural(t, d, T):
            return self.S(self.mural_img, [C(self.marta, 280, 1860, 1.5, "feliz", "entrega")], cam=(540, 1100, 1.15), t=t)

        @B(27.74)
        def b_jurava(t, d, T):
            return self.S(self.mural_img, [C(self.marta, 540, 1860, 1.8, "feliz", "aponta")], cam=(540, 1250, 1.25), t=t)

        @B(31.58)
        def b_foto_pedro(t, d, T):
            return self.foto_cena(t, self.pol_hosp, (96, 70, 60), 1.0)

        @B(33.64)
        def b_ninguem_entendeu(t, d, T):
            chars = [C(K[i], 220 + i * 230, 1840, 1.2, "surpreso", "aponta") for i in range(4)]
            return self.S(sala(), chars, [self.pol(self.pol_hosp, 540, 760, 420, 0)], (540, 1250, 1.2), t)

        @B(35.42)
        def b_adulto(t, d, T):
            return self.foto_cena(t, self.pol_hosp, (70, 100, 120), 1.25)

        @B(38.36)
        def b_medico_paciente(t, d, T):
            bg = cs.quarto_hospital(self.fc)
            return self.S(bg, [C(self.cir, 280, 1840, 1.4, "neutro"), C(self.pedroad, 820, 1840, 1.4, "feliz")],
                          [lambda m: m.alpha_composite(cs.cama_hospital(760), (160, 1460))],
                          (540, 1250, 1.15), t)

        @B(40.66)
        def b_cidade(t, d, T):
            bg = cr.praca_rica(self.fc, "dia").copy()
            amb.nuvens(bg, t, n=4, seed=3)
            chars = [C(K[i], 150 + i * 200, 1840, 1.0, "ri", "bracos_abertos") for i in range(5)]
            return self.S(bg, chars, cam=(540, 1350, 1.2), t=t)

        @B(42.46)
        def b_cirurgiao(t, d, T):
            def bolha(m):
                p = Pincel(WW, WH)
                p.elipse((560, 760, 1020, 1140), (255, 255, 255), ow=8)
                m.alpha_composite(p.pronto())
                f_ = cs._fig(CIRURGIAO, "feliz", 0.85)
                m.alpha_composite(f_, (790 - f_.width // 2, 1130 - f_.height + 20))
            return self.S(sala(), [C(self.pedro, 380, 1840, 1.5, "feliz", "idle")], [bolha], (540, 1250, 1.2), t)

        @B(45.20)
        def b_problema(t, d, T):
            return self.S(sala("3 x 3 = ?"), [C(self.pedro, 540, 1860, 1.8, "surpreso", "idle")], cam=(540, 1250, 1.3), t=t)

        @B(46.62)
        def b_pior(t, d, T):
            def prova(m):
                p = Pincel(WW, WH)
                p.ret((620, 1420, 960, 1700), (250, 248, 240), r=8, ow=6)
                m.alpha_composite(p.pronto())
                d_ = ImageDraw.Draw(m)
                d_.text((680, 1500), "0", font=vc.fonte(self.fc, 150), fill=(214, 40, 50))
            return self.S(sala(), [C(self.pedro, 360, 1840, 1.5, "triste", "bolso")], [prova], (540, 1250, 1.2), t)

        @B(49.20)
        def b_tres_vezes(t, d, T):
            return self.S(sala("3 x 3 = 6"), [C(self.pedro, 300, 1840, 1.5, "triste", "aponta")], cam=(540, 1100, 1.2),
                          t=t)

        @B(51.28)
        def b_riem(t, d, T):
            chars = [C(self.pedro, 260, 1840, 1.3, "triste", "bolso")] + [C(K[i], 560 + i * 170, 1830, 1.05, "ri",
                                                                           "bate") for i in range(4)]
            return self.S(sala("3 x 3 = 6"), chars, cam=(640, 1250, 1.2), t=t)

        @B(52.86)
        def b_paciencia(t, d, T):
            return self.S(sala(), [C(self.marta, 540, 1860, 1.9, "bravo", "aponta")], cam=(540, 1250, 1.3), t=t)

        @B(55.48)
        def b_santo_dia(t, d, T):
            n = int((T - 55.5) * 2) % 3
            return self.S(sala("", str(12 + n)), [C(self.marta, 400, 1860, 1.7, "bravo", "bate"),
                                                  C(self.pedro, 880, 1840, 1.2, "triste", "idle")],
                          cam=(540, 1250, 1.2), t=t)

        @B(58.12)
        def b_grito(t, d, T):
            return self.S(sala(), [C(self.marta, 400, 1860, 1.8, "bravo", "aponta", self.dlg["marta"]),
                                   C(self.pedro, 900, 1840, 1.2, "surpreso", "idle")],
                          cam=(540, 1250, 1.25), t=t, bal=[("Pedrinho, você vai me deixar louca!", OUT_W * 0.5, OUT_H * 0.1,
                                                            58.12)])

        @B(60.34)
        def b_lucia_chega(t, d, T):
            bg = gradiente(WW, WH, (170, 212, 240), (226, 238, 248))
            p = Pincel(WW, WH)
            p.ret((-20, 1500, WW + 20, WH + 20), (186, 180, 170), r=0, ow=0)
            p.ret((80, 480, 1000, 1500), (232, 184, 132), r=6)
            p.ret((380, 1100, 700, 1500), (140, 96, 66), r=6)
            p.ret((260, 380, 820, 470), (200, 56, 70), r=8)
            bg.alpha_composite(p.pronto())
            d_ImageDraw = ImageDraw.Draw(bg)
            fnt = vc.fonte(self.fc, 60)
            d_ImageDraw.text((540 - fnt.getlength("ESCOLA") / 2, 392), "ESCOLA", font=fnt, fill=(255, 255, 255))
            x = 1150 - 560 * ease_out(min(1, (T - 60.3) / 2.4))
            return self.S(bg, [C(self.lucia, x, 1840, 1.3, "neutro", "anda" if T < 62.7 else "idle", None, -1)],
                          cam=(540, 1250, 1.1), t=t)

        @B(62.80)
        def b_escuta_porta(t, d, T):
            bg = cs.corredor(self.fc, "SALA 4")
            return self.S(bg, [C(self.lucia, 300, 1840, 1.5, "neutro", "idle")], cam=(540, 1250, 1.15), t=t)

        @B(65.14)
        def b_ouviu(t, d, T):
            return self.S(cs.corredor(self.fc, "SALA 4"), [C(self.lucia, 540, 1860, 1.9, "surpreso", "idle")],
                          cam=(540, 1250, 1.3), t=t)

        @B(66.02)
        def b_caso_perdido(t, d, T):
            return self.S(sala(), [C(self.marta, 640, 1860, 1.6, "bravo", "aponta", self.dlg["marta"]),
                                   C(self.lucia, 230, 1840, 1.3, "triste", "idle")],
                          cam=(540, 1250, 1.2), t=t, bal=[("Esse menino é o caso mais perdido que eu já tive.",
                                                           OUT_W * 0.52, OUT_H * 0.1, 66.02)])

        @B(69.02)
        def b_nunca_medico(t, d, T):
            return self.S(sala(), [C(self.marta, 640, 1860, 1.6, "bravo", "bate", self.dlg["marta"]),
                                   C(self.lucia, 230, 1840, 1.3, "chora", "idle")],
                          cam=(540, 1250, 1.2), t=t, bal=[("Com foto ou sem foto, ele nunca vai ser médico.",
                                                           OUT_W * 0.52, OUT_H * 0.1, 69.02)])

        @B(72.14)
        def b_arrasada(t, d, T):
            x = 800 - 380 * ease_io(min(1, (T - 72.1) / 2.4))
            return self.S(cs.corredor(self.fc, "SAÍDA"), [C(self.lucia, x, 1840, 1.5, "chora", "anda", None, 1)],
                          cam=(540, 1250, 1.15), t=t)

        @B(74.60)
        def b_tirou(t, d, T):
            x = 300 + 560 * ease_io(min(1, (T - 74.6) / 2.2))
            return self.S(cs.corredor(self.fc, "SAÍDA"), [C(self.lucia, x, 1840, 1.5, "triste", "anda"),
                                                          C(self.pedro, x - 190, 1840, 1.2, "triste", "anda")],
                          cam=(540, 1250, 1.2), t=t)

        @B(76.20)
        def b_mudou(t, d, T):
            bg = gradiente(WW, WH, (46, 70, 110), (30, 44, 76))
            k = ease_io(min(1, (T - 76.2) / 1.6))
            im = cs.mapa_brasil(self.fc, (int(380 + 220 * k), int(560 + 260 * k)), 860)
            return self.S(bg, props=[lambda m: m.alpha_composite(im, (110, 290))], cam=(540, 1000, 1.0), t=t)

        @B(77.12)
        def b_sumiu(t, d, T):
            return self.S(self.mural_img, [C(self.marta, 540, 1860, 1.6, "triste", "idle")], cam=(540, 1250, 1.25), t=t)

        @B(79.76)
        def b_25anos(t, d, T):
            bg = gradiente(WW, WH, (34, 34, 52), (14, 14, 24))
            f_c = cr.celular_conversas  # noqa: F841
            d_img = cr.calendario(self.fc, "ANOS", int(min(25, (T - 79.8) * 9)), total=31, w=760, cor_topo=(70, 74, 90))
            return self.S(bg, props=[lambda m: m.alpha_composite(d_img, (160, 600))], cam=(540, 1000, 1.0), t=t)

        @B(81.54)
        def b_noticia(t, d, T):
            bg = gradiente(WW, WH, (226, 232, 238), (196, 208, 220))
            return self.S(bg, [C(self.martav, 300, 1840, 1.5, "surpreso", "idle"), C(self.med, 800, 1840, 1.5, "triste",
                                                                                      "idle")],
                          cam=(540, 1250, 1.15), t=t)

        @B(83.06)
        def b_coracao(t, d, T):
            bg = gradiente(WW, WH, (46, 24, 34), (22, 10, 16))
            im = cs.coracao_partido(760, 0.5 + 0.5 * math.sin(t * 7))
            return self.S(bg, props=[lambda m: m.alpha_composite(im, (540 - im.width // 2, 960 - im.height // 2))],
                          cam=(540, 1000, 1.0), t=t)

        @B(85.00)
        def b_cirurgia_dificil(t, d, T):
            bg = gradiente(WW, WH, (226, 232, 238), (196, 208, 220))
            return self.S(bg, [C(self.med, 540, 1860, 1.8, "neutro", "aponta")], cam=(540, 1250, 1.25), t=t)

        @B(87.72)
        def b_um_cirurgiao(t, d, T):
            bg = gradiente(WW, WH, (46, 70, 110), (30, 44, 76))
            im = cs.mapa_brasil(self.fc, (640, 700), 860)
            return self.S(bg, props=[lambda m: m.alpha_composite(im, (110, 290))], cam=(640, 900, 1.2), t=t)

        @B(90.54)
        def b_aceitou(t, d, T):
            bg = gradiente(WW, WH, (226, 232, 238), (196, 208, 220))
            return self.S(bg, [C(self.martav, 540, 1860, 1.7, "triste", "entrega")], cam=(540, 1250, 1.3), t=t)

        @B(92.32)
        def b_mesa(t, d, T):
            chars = [C(self.cir, 280, 1840, 1.4, "neutro", "bate"), C(self.med, 820, 1840, 1.4, "neutro", "idle")]
            return self.S(cs.centro_cirurgico(self.fc), chars,
                          [lambda m: m.alpha_composite(cs.cama_hospital(860), (110, 1290))], (540, 1250, 1.15), t)

        @B(94.32)
        def b_certo(t, d, T):
            return self.S(cs.quarto_hospital(self.fc), [C(self.cir, 300, 1840, 1.5, "feliz", "acena")],
                          [lambda m: m.alpha_composite(cs.cama_hospital(760), (260, 1460))], (540, 1250, 1.15), t)

        @B(95.58)
        def b_abriu_olhos(t, d, T):
            f_ = self.S(cs.quarto_hospital(self.fc), [C(self.martav, 560, 1760, 1.6, "neutro", "idle")],
                        [lambda m: m.alpha_composite(cs.cama_hospital(900), (90, 1380))], (540, 1250, 1.35), t)
            k = 1 - ease_io(min(1, (T - 95.6) / 2.0))
            return f_.filter(__import__("PIL.ImageFilter", fromlist=["GaussianBlur"]).GaussianBlur(10 * k)) if k > 0.05 else f_

        @B(97.86)
        def b_medico_sorrindo(t, d, T):
            return self.S(cs.quarto_hospital(self.fc), [C(self.martav, 700, 1760, 1.5, "neutro", "idle"),
                                                        C(self.pedroad, 240, 1840, 1.5, "feliz", "acena")],
                          [lambda m: m.alpha_composite(cs.cama_hospital(880), (200, 1380))], (540, 1250, 1.15), t)

        @B(101.34)
        def b_lembrou(t, d, T):
            return self.foto_cena(t, self.pol_hosp, (70, 100, 120), 1.0)

        @B(102.94)
        def b_detalhes(t, d, T):
            return self.foto_cena(t, self.pol_hosp, (50, 70, 100), 1.4)

        @B(106.48)
        def b_sera(t, d, T):
            def bolha(m):
                p = Pincel(WW, WH)
                p.elipse((560, 720, 1020, 1120), (255, 255, 255), ow=8)
                m.alpha_composite(p.pronto())
                f_ = cs._fig(PEDRINHO, "feliz", 0.8)
                m.alpha_composite(f_, (790 - f_.width // 2, 1100 - f_.height + 20))
            return self.S(cs.quarto_hospital(self.fc), [C(self.martav, 420, 1760, 1.5, "surpreso", "idle")],
                          [lambda m: m.alpha_composite(cs.cama_hospital(860), (60, 1380)), bolha], (540, 1250, 1.2), t)

        @B(107.48)
        def b_provou(t, d, T):
            return self.S(cs.quarto_hospital(self.fc), [C(self.martav, 540, 1760, 1.7, "triste", "idle")],
                          [lambda m: m.alpha_composite(cs.cama_hospital(900), (90, 1380))], (540, 1250, 1.3), t)

        @B(112.00)
        def b_lagrimas(t, d, T):
            return self.S(cs.quarto_hospital(self.fc), [C(self.martav, 540, 1760, 1.8, "chora", "idle")],
                          [lambda m: m.alpha_composite(cs.cama_hospital(900), (90, 1380))], (540, 1250, 1.35), t)

        @B(115.18)
        def b_obrigada(t, d, T):
            return self.S(cs.quarto_hospital(self.fc), [C(self.martav, 540, 1760, 1.8, "chora", "idle",
                                                          self.dlg["marta"])],
                          [lambda m: m.alpha_composite(cs.cama_hospital(900), (90, 1380))], (540, 1250, 1.3), t,
                          bal=[("Obrigada.", OUT_W * 0.5, OUT_H * 0.14, 115.18)])

        @B(116.18)
        def b_errado(t, d, T):
            pisca = int(T * 4) % 2
            return self.S(cs.quarto_hospital(self.fc, bool(pisca)), [C(self.martav, 540, 1760, 1.5, "surpreso", "idle")],
                          [lambda m: m.alpha_composite(cs.cama_hospital(900), (90, 1380))], (540, 1250, 1.15), t)

        @B(119.58)
        def b_respirar(t, d, T):
            return self.S(cs.quarto_hospital(self.fc, True), [C(self.martav, 540, 1760, 1.8, "surpreso", "idle")],
                          [lambda m: m.alpha_composite(cs.cama_hospital(900), (90, 1380))], (540, 1250, 1.3), t)

        @B(121.20)
        def b_azul(t, d, T):
            k = min(1, (T - 121.2) / 1.2)

            def fx(f):
                return Image.blend(f, Image.new("RGB", f.size, (60, 90, 200)), 0.35 * k)
            return self.S(cs.quarto_hospital(self.fc, True), [C(self.martav, 540, 1760, 1.9, "chora", "idle")],
                          [lambda m: m.alpha_composite(cs.cama_hospital(900), (90, 1380))], (540, 1250, 1.3), t, fx=fx)

        @B(122.90)
        def b_mao(t, d, T):
            return self.S(cs.quarto_hospital(self.fc, True), [C(self.martav, 540, 1760, 1.7, "chora", "acena")],
                          [lambda m: m.alpha_composite(cs.cama_hospital(900), (90, 1380))], (540, 1250, 1.25), t)

        @B(125.24)
        def b_morreu(t, d, T):
            im = cs.respirador(t, False, 760)
            bg = gradiente(WW, WH, (40, 40, 52), (18, 18, 26))
            return self.S(bg, props=[lambda m: m.alpha_composite(im, (540 - im.width // 2, 520))],
                          cam=(540, 1000, 1.0), t=t)

        @B(127.46)
        def b_choque(t, d, T):
            return self.S(cs.centro_cirurgico(self.fc), [C(self.cir, 540, 1860, 1.8, "surpreso", "idle")],
                          cam=(540, 1250, 1.3), t=t)

        @B(129.24)
        def b_perfeita(t, d, T):
            return self.S(cs.centro_cirurgico(self.fc), [C(self.cir, 360, 1840, 1.5, "neutro", "bate"),
                                                         C(self.med, 820, 1840, 1.4, "neutro", "idle")],
                          cam=(540, 1250, 1.2), t=t)

        @B(131.28)
        def b_como(t, d, T):
            return self.S(cs.centro_cirurgico(self.fc), [C(self.cir, 540, 1860, 1.8, "triste", "bracos_abertos")],
                          cam=(540, 1250, 1.3), t=t)

        @B(132.88)
        def b_checar(t, d, T):
            x = 250 + 420 * ease_io(min(1, (T - 132.9) / 2.2))
            return self.S(cs.corredor(self.fc, "UTI"), [C(self.cir, x, 1840, 1.5, "neutro", "anda")],
                          cam=(540, 1250, 1.15), t=t)

        @B(134.20)
        def b_tomada(t, d, T):
            bg = gradiente(WW, WH, (206, 226, 234), (176, 204, 214))
            return self.S(bg, [C(self.pedroad, 760, 1860, 1.7, "neutro", "idle", None, -1)],
                          [lambda m: m.alpha_composite(cs.tomada(True, 420), (130, 1380)),
                           lambda m: m.alpha_composite(cs.enceradeira(380), (520, 1400))],
                          (540, 1250, 1.2), t)

        @B(138.02)
        def b_era_pedrinho(t, d, T):
            return self.S(cs.corredor(self.fc, "UTI"), [C(self.pedroad, 540, 1860, 1.9, "surpreso", "idle")],
                          cam=(540, 1250, 1.35), t=t)

        @B(139.04)
        def b_mesmo_menino(t, d, T):
            return self.S(sala(), [C(self.pedro, 300, 1840, 1.5, "triste", "bolso"),
                                   C(self.marta, 780, 1860, 1.6, "bravo", "aponta")], cam=(540, 1250, 1.15), t=t)

        @B(143.56)
        def b_nao_mentiu(t, d, T):
            return self.foto_cena(t, self.pol_hosp, (60, 90, 110), 1.2)

        @B(144.98)
        def b_hospital(t, d, T):
            return self.S(cs.corredor(self.fc, "HOSPITAL"), [C(self.pedroad, 540, 1860, 1.7, "neutro", "idle")],
                          cam=(540, 1250, 1.2), t=t)

        @B(146.94)
        def b_nao_cirurgiao(t, d, T):
            return self.foto_cena(t, self.pol_hosp_q, (60, 60, 80), 1.1)

        @B(148.46)
        def b_nem_medico(t, d, T):
            return self.S(cs.corredor(self.fc, "UTI"), [C(self.pedroad, 540, 1860, 1.8, "triste", "bolso")],
                          cam=(540, 1250, 1.25), t=t)

        @B(149.80)
        def b_faxineiro(t, d, T):
            return self.S(cs.corredor(self.fc, "UTI"), [C(self.pedroad, 360, 1860, 1.6, "feliz", "entrega")],
                          [lambda m: m.alpha_composite(cs.enceradeira(420), (620, 1360))], (540, 1250, 1.2), t)

        @B(150.92)
        def b_ligar(t, d, T):
            k = ease_io(min(1, max(0, (T - 152.8) / 1.4)))
            bg = gradiente(WW, WH, (206, 226, 234), (176, 204, 214))
            return self.S(bg, props=[lambda m: m.alpha_composite(cs.tomada(k < 0.5, 900), (90, 620))],
                          cam=(540, 1000, 1.0), t=t)

        @B(155.36)
        def b_maquina(t, d, T):
            im = cs.respirador(t, T < 156.2, 800)
            bg = gradiente(WW, WH, (60, 70, 86), (24, 28, 38))
            f = self.S(bg, props=[lambda m: m.alpha_composite(im, (540 - im.width // 2, 460))], cam=(540, 1000, 1.0), t=t)
            k = max(0, (T - 157.0) / 1.4)
            return Image.blend(f, Image.new("RGB", f.size, (0, 0, 0)), min(1, k)) if k > 0 else f

        R.sort(key=lambda x: x[0])
        return R


def _tom(c, f):
    return tuple(int(v * f) for v in c)


# --------------------------------------------------------------------------
def mixar(filme, narracao, saida):
    SR = g.SR
    voz = vc.ler_wav_mono(narracao)
    n = int(filme.dur_total * SR)
    mix = np.zeros(n, np.float32)
    mix[:min(n, len(voz))] += voz[:n]
    mus = g.trilha(filme.dur_total)
    mus = mus / max(1e-6, np.abs(mus).max()) * 0.11
    mix[:len(mus)] += mus[:n]
    ev = []
    for i, c in enumerate(filme.sfx_cortes):
        ev.append(("whoosh" if i % 3 == 0 else "pop", c - 0.04))
    ev += [("brilho", 1.4), ("brilho", 31.6), ("toc", 58.12), ("toc", 125.24), ("brilho", 134.2), ("toc", 152.8),
           ("toc", 157.4)]
    # alarme do monitor (116–125 s) — bipes
    for k in range(int((125.2 - 116.2) / 0.5)):
        ev.append(("ding", 116.2 + k * 0.5))
    for tipo, t0 in ev:
        s = g.sfx(tipo) if tipo != "ding" else g.sfx("brilho") * 0.6
        s = s * (0.25 if tipo in ("whoosh", "pop") else 0.8)
        a = int(max(0, t0) * SR)
        b = min(n, a + len(s))
        mix[a:b] += s[: b - a]
    fade = int(SR * 1.2)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = mix / max(1.0, np.abs(mix).max() / 0.95)
    with wave.open(saida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def carregar_palavras(caminho):
    troca = {"enseradeira,": "enceradeira,", "enseradeira.": "enceradeira.", "enseradeira": "enceradeira",
             "vitória": "Vitória", "3x3.": "3x3."}
    out = []
    for seg in json.load(open(caminho)):
        for w in seg["words"]:
            out.append(dict(w=troca.get(w["w"], w["w"]), s=w["s"], e=w["e"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narracao", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--camera", required=True)
    ap.add_argument("--ancoras", required=True)
    ap.add_argument("--fonte", default=g.fonte_padrao())
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(__file__), "video_a_foto_do_futuro.mp4"))
    ap.add_argument("--preview", default=None)
    ap.add_argument("--testar", action="store_true")
    ap.add_argument("--de", type=float, default=None)
    ap.add_argument("--ate", type=float, default=None)
    a = ap.parse_args()

    voz_dur = len(vc.ler_wav_mono(a.narracao)) / g.SR
    filme = FilmeFoto(carregar_palavras(a.transcricao), a.fonte, voz_dur + 1.4, a.narracao, json.load(open(a.camera)),
                      json.load(open(a.ancoras)))
    total = int(filme.dur_total * FPS)

    if a.testar:
        for ini, d, *_r in filme.planos:
            for k in (0.01, 0.5, 0.99):
                filme.frame(int((ini + d * k) * FPS))
        print(f"todos os planos ok — {len(filme.planos)} cenas em {filme.dur_total:.1f}s")
        return
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        for i, (ini, d, *_r) in enumerate(filme.planos):
            filme.frame(int((ini + d * 0.6) * FPS)).save(os.path.join(a.preview, f"cena_{i:03d}.png"))
        print("preview em", a.preview, len(filme.planos), "cenas")
        return

    tmp = tempfile.mkdtemp(prefix="foto_")
    wav = os.path.join(tmp, "mix.wav")
    mixar(filme, a.narracao, wav)
    n0 = int((a.de or 0) * FPS)
    n1 = int(a.ate * FPS) if a.ate else total
    if a.de or a.ate:
        tr = os.path.join(tmp, "trecho.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.de or 0), "-t", str((n1 - n0) / FPS), "-i", wav, tr],
                       check=True)
        wav = tr
    print(f"• renderizando {total} frames ({filme.dur_total:.1f}s)…", flush=True)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}",
         "-r", str(FPS), "-i", "-", "-i", wav, "-vf", "scale=1080:1920:flags=lanczos",
         "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-maxrate", "6M", "-bufsize", "12M",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.saida],
        stdin=subprocess.PIPE)
    for n in range(n0, n1):
        proc.stdin.write(filme.frame(n).tobytes())
        if n % 150 == 0:
            print(f"  {n}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("✔ vídeo salvo em", a.saida)


if __name__ == "__main__":
    main()
