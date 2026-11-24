#!/usr/bin/env python3
"""
Mede o movimento de câmera de um vídeo de referência, cena a cena, rastreando pontos (ORB + RANSAC)
frame a frame e acumulando zoom e deslocamento. Bem mais confiável que comparar só o 1º e o último quadro.

    python3 medir_camera.py video.mp4 saida.json
"""
import json
import subprocess
import sys

import cv2
import numpy as np


def cortes(video, limiar=0.15):
    r = subprocess.run(["ffmpeg", "-i", video, "-vf", f"select='gt(scene,{limiar})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    import re
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", r)]


def duracao(video):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                                capture_output=True, text=True).stdout)


def medir(video, saida, fps=12, W=216, H=384):
    dur = duracao(video)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},scale={W}:{H},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W)
    cs = [0.0] + cortes(video) + [dur]
    lim = [cs[0]]
    for c in cs[1:]:
        if c - lim[-1] >= 0.25:
            lim.append(c)
    orb = cv2.ORB_create(900, fastThreshold=7)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    res = []
    for i in range(len(lim) - 1):
        a, b = lim[i], lim[i + 1]
        ia, ib = int((a + 0.12) * fps), min(len(fr) - 1, int((b - 0.08) * fps))
        logs, tx, ty, ok, tot = 0.0, 0.0, 0.0, 0, 0
        for k in range(ia, ib):
            tot += 1
            k1, d1 = orb.detectAndCompute(fr[k], None)
            k2, d2 = orb.detectAndCompute(fr[k + 1], None)
            if d1 is None or d2 is None or len(k1) < 12 or len(k2) < 12:
                continue
            m = bf.match(d1, d2)
            if len(m) < 12:
                continue
            p1 = np.float32([k1[x.queryIdx].pt for x in m])
            p2 = np.float32([k2[x.trainIdx].pt for x in m])
            M, inl = cv2.estimateAffinePartial2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=2.5)
            if M is None or inl is None or inl.sum() < 10:
                continue
            s = float(np.hypot(M[0, 0], M[1, 0]))
            logs += np.log(max(0.5, min(2.0, s)))
            tx += M[0, 2] - (1 - s) * W / 2 * 0 - 0
            ty += M[1, 2]
            ok += 1
        conf = ok / max(1, tot)
        res.append(dict(ini=round(a, 2), dur=round(b - a, 2), zoom=round(float(np.exp(logs)), 3),
                        dx=round(float(tx / W), 3), dy=round(float(ty / H), 3), r=round(float(conf), 2)))
    json.dump(res, open(saida, "w"))
    bons = sum(1 for x in res if x["r"] >= 0.4)
    print(f"{len(res)} cenas; confiáveis (r>=0.4): {bons} ({100 * bons // max(1, len(res))}%)")
    return res


if __name__ == "__main__":
    medir(sys.argv[1], sys.argv[2])
