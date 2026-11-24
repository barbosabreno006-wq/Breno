#!/usr/bin/env python3
"""Render em paralelo (usa todos os núcleos): ~3-4x mais rápido que renderizar frame a frame."""
import multiprocessing as mp
import os

_F = None


def _lote(args):
    n0, n1 = args
    return [_F.frame(n).tobytes() for n in range(n0, n1)]


def renderizar(filme, n0, n1, destino, workers=None, lote=20, progresso=None, total=None):
    """Escreve os frames n0..n1 (em ordem) em destino.write(bytes)."""
    global _F
    _F = filme
    workers = workers or max(1, (os.cpu_count() or 2))
    ctx = mp.get_context("fork")
    faixas = [(a, min(a + lote, n1)) for a in range(n0, n1, lote)]
    feitos = 0
    with ctx.Pool(workers) as pool:
        for b in pool.imap(_lote, faixas):
            for fr in b:
                destino.write(fr)
            feitos += len(b)
            if progresso and (feitos // 150 != (feitos - len(b)) // 150):
                print(f"  {n0 + feitos}/{total or n1}", flush=True)
