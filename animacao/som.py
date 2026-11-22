#!/usr/bin/env python3
"""
Sound design v2: sons ambiente em camadas, efeitos mais ricos e música com arco emocional,
tudo sintetizado com numpy e misturado com 'ducking' (a música/ambiente abaixam quando a voz fala).
"""
import numpy as np

SR = 44100
_rng = np.random.default_rng(7)


def _env(n, ataque=0.005, queda=0.2):
    t = np.arange(n) / SR
    a = np.minimum(1, t / max(1e-4, ataque))
    return a * np.exp(-t / max(1e-3, queda))


def ruido(dur, f0=None, f1=None, cor="branco"):
    """Ruído filtrado por FFT: banda [f0, f1] Hz (ou todo o espectro)."""
    n = int(dur * SR)
    x = _rng.standard_normal(n).astype(np.float32)
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(n, 1 / SR)
    m = np.ones_like(fr)
    if cor == "rosa":
        m = 1 / np.sqrt(np.maximum(fr, 30))
    elif cor == "marrom":
        m = 1 / np.maximum(fr, 30)
    if f0:
        m = m * (fr >= f0)
    if f1:
        m = m * (fr <= f1)
    y = np.fft.irfft(X * m, n).astype(np.float32)
    return y / max(1e-6, np.abs(y).max())


# ---------------------------------------------------------------- efeitos
def sfx(tipo):
    if tipo == "whoosh":
        n = int(0.55 * SR)
        r = ruido(0.55, 300, 7000)
        t = np.arange(n) / SR
        env = np.sin(np.pi * t / 0.55) ** 2
        # varredura: mais agudo no meio
        brilho = 0.6 + 0.4 * np.sin(np.pi * t / 0.55)
        return (r * env * brilho * 0.8).astype(np.float32)
    if tipo == "pop":
        n = int(0.16 * SR)
        t = np.arange(n) / SR
        f = 700 * np.exp(-t * 18) + 180
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.04) * 0.9).astype(np.float32)
    if tipo == "hit":
        n = int(0.9 * SR)
        t = np.arange(n) / SR
        sub = np.sin(2 * np.pi * (52 + 70 * np.exp(-t * 14)) * t) * np.exp(-t * 5)
        r = ruido(0.9, 120, 3500)[:n] * np.exp(-t * 22)
        return (0.9 * sub + 0.35 * r).astype(np.float32)
    if tipo == "shutter":
        a = np.zeros(int(0.32 * SR), np.float32)
        for t0, g in ((0.0, 1.0), (0.11, 0.8)):
            r = ruido(0.05, 1200, 9000)[: int(0.05 * SR)] * _env(int(0.05 * SR), 0.001, 0.012) * g
            i0 = int(t0 * SR)
            a[i0:i0 + len(r)] += r
        return a * 0.8
    if tipo == "pagina":
        r = ruido(0.28, 2000, 9000) * np.sin(np.linspace(0, np.pi, int(0.28 * SR))) ** 2
        return (r * 0.5).astype(np.float32)
    if tipo == "ding":
        n = int(1.1 * SR)
        t = np.arange(n) / SR
        y = np.sin(2 * np.pi * 1318 * t) + 0.4 * np.sin(2 * np.pi * 2637 * t) + 0.2 * np.sin(2 * np.pi * 3951 * t)
        return (y * _env(n, 0.003, 0.35) * 0.45).astype(np.float32)
    if tipo == "bip":
        n = int(0.16 * SR)
        t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 980 * t) * np.minimum(1, t / 0.004) * np.minimum(1, (0.16 - t) / 0.01) * 0.5).astype(np.float32)
    if tipo == "coracao":
        a = np.zeros(int(0.9 * SR), np.float32)
        for t0, g in ((0.0, 1.0), (0.22, 0.7)):
            n = int(0.2 * SR)
            t = np.arange(n) / SR
            y = np.sin(2 * np.pi * 58 * t) * np.exp(-t * 18) * g
            i0 = int(t0 * SR)
            a[i0:i0 + n] += y
        return a
    if tipo == "riser":
        n = int(2.2 * SR)
        r = ruido(2.2, 200, 9000)
        t = np.arange(n) / SR
        return (r * (t / 2.2) ** 2.2 * 0.7).astype(np.float32)
    return np.zeros(int(0.1 * SR), np.float32)


# ---------------------------------------------------------------- ambientes (loops longos)
def ambiente(nome, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if nome == "chuva":
        base = ruido(dur, 1500, 9000) * 0.5 + ruido(dur, 200, 900, "rosa") * 0.25
        gotas = ruido(dur, 3000, 12000) * (np.abs(_rng.standard_normal(n)) > 2.7)
        return (base + 0.5 * gotas).astype(np.float32) * 0.5
    if nome == "vento":
        m = 0.6 + 0.4 * np.sin(2 * np.pi * t / 7.0 + 1.2) * np.sin(2 * np.pi * t / 3.1)
        return (ruido(dur, 80, 900, "marrom") * m).astype(np.float32) * 0.6
    if nome == "multidao":
        base = ruido(dur, 250, 3200, "rosa")
        m = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * t / 2.3 + np.cumsum(_rng.standard_normal(n)) * 1e-4))
        return (base * m).astype(np.float32) * 0.55
    if nome == "cidade":
        return (ruido(dur, 40, 500, "marrom") * 0.7 + ruido(dur, 500, 4000, "rosa") * 0.2).astype(np.float32) * 0.5
    if nome == "noite":
        gr = np.zeros(n, np.float32)
        for k in range(int(dur * 1.5)):
            i0 = int(_rng.uniform(0, max(1, dur - 0.3)) * SR)
            f = _rng.uniform(4200, 5200)
            ln = int(0.09 * SR)
            tt = np.arange(ln) / SR
            gr[i0:i0 + ln] += (np.sin(2 * np.pi * f * tt) * np.sin(np.pi * tt / 0.09) ** 2 * 0.35)[: max(0, min(ln, n - i0))]
        return gr + ruido(dur, 60, 400, "marrom") * 0.18
    if nome == "hospital":
        z = ruido(dur, 100, 700, "marrom") * 0.35
        b = np.zeros(n, np.float32)
        bip = sfx("bip") * 0.45
        for t0 in np.arange(1.0, dur - 0.3, 1.15):
            i0 = int(t0 * SR)
            b[i0:i0 + len(bip)] += bip[: max(0, min(len(bip), n - i0))]
        return z + b
    if nome == "escola":
        return (ruido(dur, 300, 2800, "rosa") * (0.35 + 0.15 * np.sin(2 * np.pi * t / 5.3))).astype(np.float32) * 0.4
    return np.zeros(n, np.float32)


# ---------------------------------------------------------------- música com arco emocional
NOTAS = {"A": 220.0, "F": 174.6, "C": 261.6, "G": 196.0, "D": 146.8, "E": 164.8, "B": 246.9}


def _nota(f, dur, ataque=0.01, queda=0.5, harm=(1, 0.5, 0.25)):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = sum(h * np.sin(2 * np.pi * f * (i + 1) * t) for i, h in enumerate(harm))
    return (y * _env(n, ataque, queda)).astype(np.float32)


def trilha_v2(dur, picos=(), clima="triste", vol=1.0):
    """Música em 4 camadas (pad, baixo, arpejo, percussão) com intensidade que sobe e desce.
    picos = [(tempo, intensidade 0..1)]: a intensidade interpola entre os picos (0.35 base)."""
    n = int(dur * SR)
    out = np.zeros(n + 4 * SR, np.float32)
    t = np.arange(len(out)) / SR
    pts = [(0.0, 0.3)] + sorted(picos) + [(dur, 0.2)]
    inten = np.interp(t, [p[0] for p in pts], [p[1] for p in pts]).astype(np.float32)
    prog = ([(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7), (164.8, 207.7, 246.9)] if clima == "triste"
            else [(261.6, 329.6, 392.0), (196.0, 246.9, 293.7), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6)])
    comp = 4.0
    for k in range(int(dur / comp) + 1):
        t0 = k * comp
        acorde = prog[k % 4]
        i0 = int(t0 * SR)
        # pad suave
        for f in acorde:
            seg = _nota(f * 0.5, comp + 1.0, 0.8, 5.0, (1, 0.3)) * 0.07
            out[i0:i0 + len(seg)] += seg[: len(out) - i0]
        # baixo
        sb = _nota(acorde[0] * 0.25, comp, 0.02, 2.0, (1, 0.4)) * 0.16
        out[i0:i0 + len(sb)] += sb[: len(out) - i0]
        # arpejo (entra com intensidade)
        for j in range(8):
            ta = t0 + j * comp / 8
            if inten[min(len(inten) - 1, int(ta * SR))] > 0.38:
                nt = _nota(acorde[j % 3] * (2 if j % 2 else 1), 0.9, 0.004, 0.28, (1, 0.35, 0.12)) * 0.11
                ia = int(ta * SR)
                out[ia:ia + len(nt)] += nt[: len(out) - ia]
        # percussão leve quando a intensidade passa de 0.6
        for j in range(4):
            tp = t0 + j * comp / 4
            if inten[min(len(inten) - 1, int(tp * SR))] > 0.6:
                h_ = sfx("hit")[: int(0.4 * SR)] * (0.18 if j % 2 == 0 else 0.1)
                ip = int(tp * SR)
                out[ip:ip + len(h_)] += h_[: len(out) - ip]
    out = out[:n] * (0.5 + 0.7 * inten[:n])
    return (out / max(1e-6, np.abs(out).max()) * 0.9 * vol).astype(np.float32)


# ---------------------------------------------------------------- mixagem com ducking
def ducking(voz, janela=0.08, forca=0.65, suave=0.25):
    """Curva (0..1) que reduz música/ambiente quando a voz está falando."""
    h = int(janela * SR)
    env = np.convolve(np.abs(voz), np.ones(h, np.float32) / h, mode="same")
    env = env / max(1e-6, np.percentile(env, 99))
    fala = np.clip(env * 3, 0, 1)
    k = int(suave * SR)
    fala = np.convolve(fala, np.ones(k, np.float32) / k, mode="same")
    return 1 - forca * fala


def mixar_v2(dur, voz, eventos, ambientes=(), picos=(), clima="triste", vol_musica=0.14):
    """eventos = [(tipo, tempo, ganho)]; ambientes = [(nome, t0, t1, ganho)]."""
    n = int(dur * SR)
    mix = np.zeros(n, np.float32)
    v = voz[:n]
    duck = ducking(np.pad(v, (0, max(0, n - len(v)))))
    mus = trilha_v2(dur, picos, clima)[:n] * vol_musica
    mix += mus * duck[: len(mus)]
    for nome, t0, t1, ganho in ambientes:
        a = ambiente(nome, t1 - t0) * ganho
        i0 = int(t0 * SR)
        f = int(min(len(a) // 4, 1.2 * SR))
        a[:f] *= np.linspace(0, 1, f)
        a[-f:] *= np.linspace(1, 0, f)
        mix[i0:i0 + len(a)] += (a * duck[i0:i0 + len(a)])[: max(0, n - i0)]
    mix[:len(v)] += v
    for tipo, t0, ganho in eventos:
        s = sfx(tipo) * ganho
        a = int(max(0, t0) * SR)
        b = min(n, a + len(s))
        if b > a:
            mix[a:b] += s[: b - a]
    f = int(SR * 1.2)
    mix[-f:] *= np.linspace(1, 0, f)
    return mix / max(1.0, np.abs(mix).max() / 0.95)
