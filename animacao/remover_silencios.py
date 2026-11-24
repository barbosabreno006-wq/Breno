#!/usr/bin/env python3
"""
Remove/encurta os silêncios de uma narração (ex.: ElevenLabs) para deixá-la
mais dinâmica, no ritmo dos vídeos virais.

Cada pausa maior que --min é reduzida para --manter segundos (metade antes,
metade depois), com micro-fades para não estalar.

Uso:
    python3 animacao/remover_silencios.py entrada.mp3 saida.wav [--limiar -40] [--min 0.18] [--manter 0.12]
"""
import argparse
import re
import subprocess

import numpy as np

SR = 44100


def carregar(caminho):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", caminho, "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def silencios(caminho, limiar, minimo):
    log = subprocess.run(["ffmpeg", "-i", caminho, "-af", f"silencedetect=noise={limiar}dB:d={minimo}",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    ini = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    return list(zip(ini, fim + [None] * (len(ini) - len(fim))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("saida")
    ap.add_argument("--limiar", type=float, default=-40)
    ap.add_argument("--min", type=float, default=0.18)
    ap.add_argument("--manter", type=float, default=0.12)
    ap.add_argument("--pausas", default="",
                    help="pausas dramáticas a preservar: 'tempo:duracao,...' (tempo = início da fala seguinte, no áudio original)")
    a = ap.parse_args()
    pausas = [tuple(map(float, x.split(":"))) for x in a.pausas.split(",") if x]

    x = carregar(a.entrada)
    dur = len(x) / SR
    sil = silencios(a.entrada, a.limiar, a.min)
    meio = a.manter / 2
    fade = int(0.006 * SR)
    pedacos, cursor = [], 0.0
    for (s, e) in sil:
        e = dur if e is None else e
        if s <= 0.01:                       # silêncio inicial: corta quase tudo
            cursor = max(0.0, e - 0.03)
            continue
        if e >= dur - 0.01:                 # silêncio final
            pedacos.append((cursor, min(dur, s + 0.15)))
            cursor = dur
            break
        manter = next((dur for (tp, dur) in pausas if abs(e - tp) < 0.35), None)
        if manter is not None:          # pausa dramática: mantém (até o tamanho pedido)
            keep = min(manter, e - s)
            pedacos.append((cursor, s + keep / 2))
            cursor = e - keep / 2
            continue
        pedacos.append((cursor, s + meio))
        cursor = e - meio
    if cursor < dur:
        pedacos.append((cursor, dur))

    out = []
    for (s, e) in pedacos:
        seg = x[int(s * SR):int(e * SR)].copy()
        if len(seg) > 2 * fade:
            seg[:fade] *= np.linspace(0, 1, fade)
            seg[-fade:] *= np.linspace(1, 0, fade)
        out.append(seg)
    y = np.concatenate(out)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    a.saida], input=y.tobytes(), check=True)
    print(f"{dur:.2f}s -> {len(y) / SR:.2f}s  ({len(sil)} pausas encurtadas)")


if __name__ == "__main__":
    main()
