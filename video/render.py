import json, math, re, sys, subprocess
from PIL import Image, ImageDraw
from lib import *
from scenes import SCENES, SHOTS

FPS = 30
words = json.load(open("words.json"))
DUR = words[-1]["e"] + 0.5
TOTAL = DUR + 0.45

# ------------------------------------------------------------------ tempos das cenas
first = {}
for w in words:
    first.setdefault(w["f"], w["s"])
shots = []
for i, (name, ph, tr) in enumerate(SHOTS):
    s = 0.0 if i == 0 else first[ph] - 0.05
    shots.append(dict(name=name, ph=ph, tr=tr, s=s))
for i, sh in enumerate(shots):
    sh["e"] = shots[i + 1]["s"] if i + 1 < len(shots) else TOTAL
    sh["dur"] = sh["e"] - sh["s"]
    sh["pt"] = {p: first[p] - sh["s"] for p in first if sh["s"] - 0.1 <= first[p] < sh["e"]}
    sh["z"] = (1.0, 1.07) if i % 2 == 0 else (1.07, 1.0)

# ------------------------------------------------------------------ legendas
KEY = {"dinheiro", "caralho", "jogada", "séria", "plano", "verde", "cloro", "pix"}


def is_key(w):
    t = re.sub(r"[^\wÀ-ú$.]", "", w).lower()
    return t.startswith("r$") or t in KEY or any(c.isdigit() for c in t)


chunks = []   # (t0, t1, [word dicts])
by_f = {}
for w in words:
    by_f.setdefault(w["f"], []).append(w)
for f, ws in by_f.items():
    cur = []
    for w in ws:
        cur.append(w)
        nchar = sum(len(x["w"]) + 1 for x in cur)
        if len(cur) >= 3 or nchar > 20 or w["w"].endswith(","):
            chunks.append(cur)
            cur = []
    if cur:
        # evita chunk de 1 palavra se der para juntar com o anterior
        if len(cur) == 1 and chunks and chunks[-1][0]["f"] == f and len(chunks[-1]) < 3 and len(cur[0]["w"]) < 8:
            chunks[-1] += cur
        else:
            chunks.append(cur)

_wc = {}


def word_img(txt, active, key):
    k = (txt, active, key)
    if k in _wc:
        return _wc[k]
    f = font(58 * SS)
    tmp = Image.new("RGBA", (1, 1))
    bb = ImageDraw.Draw(tmp).textbbox((0, 0), txt, font=f, anchor="ls", stroke_width=7 * SS // 2)
    tw, th = bb[2] - bb[0] + 4, 78 * SS
    pad = 16 * SS
    lay = Image.new("RGBA", (tw + pad * 2, th + 22 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy = lay.width // 2, lay.height // 2 + 2 * SS
    if active:
        col = (112, 232, 150) if key else (255, 214, 40)
        d.rounded_rectangle([4 * SS, 4 * SS, lay.width - 4 * SS, lay.height - 4 * SS], radius=11 * SS, fill=col, outline=OUT, width=int(4 * SS))
        d.text((cx, cy), txt, font=f, fill=OUT, anchor="mm")
    else:
        d.text((cx, cy), txt, font=f, fill=(112, 232, 150) if key else WHITE, anchor="mm", stroke_width=int(3.5 * SS), stroke_fill=OUT)
    # comprime horizontalmente (fonte condensada)
    lay = lay.resize((int(lay.width * 0.80), lay.height), Image.LANCZOS)
    _wc[k] = lay
    return lay


def caption_layer(t):
    cur = None
    for i, ch in enumerate(chunks):
        t0 = ch[0]["s"] - 0.04
        nxt = chunks[i + 1][0]["s"] - 0.04 if i + 1 < len(chunks) else ch[-1]["e"] + 0.5
        t1 = min(nxt, ch[-1]["e"] + 0.35) if i + 1 < len(chunks) else ch[-1]["e"] + 0.3
        if t0 <= t < max(t1, t0 + 0.1):
            cur = (ch, t0)
            break
    if cur is None:
        return None
    ch, t0 = cur
    imgs = []
    for j, w in enumerate(ch):
        nxt = ch[j + 1]["s"] - 0.04 if j + 1 < len(ch) else 1e9
        active = (w["s"] - 0.04 <= t < nxt)
        imgs.append(word_img(w["w"].rstrip(",.").replace("R$", "R$"), active, is_key(w["w"])))
    # quebra em linhas (<= 2)
    maxw = int(W * SS * 0.94)
    lines, cur_l, cw = [], [], 0
    for im in imgs:
        if cur_l and cw + im.width - 20 * SS > maxw:
            lines.append(cur_l)
            cur_l, cw = [], 0
        cur_l.append(im)
        cw += im.width - 16 * SS
    lines.append(cur_l)
    lh = imgs[0].height - 6 * SS
    total_h = lh * len(lines)
    lay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    y = int(770 * SS - total_h / 2)
    # pequeno pop de entrada
    u = clamp((t - t0) / 0.10)
    scl = 0.86 + 0.14 * math.sin(u * math.pi / 2)
    for ln in lines:
        wsum = sum(i.width - 16 * SS for i in ln)
        x = (W * SS - wsum) // 2
        for im in ln:
            lay.alpha_composite(im, (int(x - 8 * SS), int(y)))
            x += im.width - 16 * SS
        y += lh
    if scl < 0.999:
        sz = (int(lay.width * scl), int(lay.height * scl))
        sm = lay.resize(sz, Image.BICUBIC)
        lay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        lay.alpha_composite(sm, ((W * SS - sz[0]) // 2, int(770 * SS * (1 - scl))))
    return lay


# ------------------------------------------------------------------ composição
def draw_shot(sh, t):
    lt = t - sh["s"]
    img = Image.new("RGB", (W * SS, H * SS), (0, 0, 0))
    SCENES[sh["name"]](Cv(img), lt, sh)
    u = clamp(lt / max(sh["dur"], 0.1))
    z = sh["z"][0] + (sh["z"][1] - sh["z"][0]) * u
    cw, ch = W * SS / z, H * SS / z
    cx, cy = W * SS / 2, H * SS * 0.55
    box = (cx - cw / 2, min(max(cy - ch / 2, 0), H * SS - ch), cx + cw / 2, min(max(cy - ch / 2, 0), H * SS - ch) + ch)
    return img.resize((W * SS, H * SS), Image.BICUBIC, box=box) if z != 1.0 else img


def frame(t):
    idx = max(i for i, s in enumerate(shots) if s["s"] <= t + 1e-6)
    sh = shots[idx]
    base = draw_shot(sh, t)
    WIPE = 0.30
    lt = t - sh["s"]
    if sh["tr"] == "wipe" and lt < WIPE and idx > 0:
        prev = draw_shot(shots[idx - 1], t)
        p = ease(lt / WIPE)
        xb = -200 + p * (W + 400)
        slant = 150
        mask = Image.new("L", (W * SS, H * SS), 0)
        md = ImageDraw.Draw(mask)
        md.polygon([(0, 0), ((xb + slant) * SS, 0), ((xb - slant) * SS, H * SS), (0, H * SS)], fill=255)
        comp = Image.composite(base, prev, mask)
        d = ImageDraw.Draw(comp)
        d.polygon([((xb + slant) * SS, 0), ((xb + slant + 46) * SS, 0), ((xb - slant + 46) * SS, H * SS), ((xb - slant) * SS, H * SS)], fill=(250, 204, 20), outline=OUT, width=int(4 * SS))
        base = comp
    out = base.convert("RGBA")
    cap = caption_layer(t) if t < DUR + 0.3 else None
    if cap is not None:
        out.alpha_composite(cap)
    # tela final escura
    if t > DUR + 0.02:
        k = clamp((t - DUR) / 0.4)
        ov = Image.new("RGBA", out.size, (14, 16, 26, int(255 * k)))
        out.alpha_composite(ov)
    return out.convert("RGB").resize((W, H), Image.LANCZOS)


# ------------------------------------------------------------------ main
if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "test":
        ts = [float(x) for x in sys.argv[2:]]
        ims = [frame(t) for t in ts]
        sheet = Image.new("RGB", (W * len(ims) // 2, H // 2), (0, 0, 0))
        for i, im in enumerate(ims):
            sheet.paste(im.resize((W // 2, H // 2), Image.LANCZOS), (i * W // 2, 0))
        sheet.save("test.png")
        print("shots", len(shots), "chunks", len(chunks), "TOTAL", round(TOTAL, 2))
    elif mode == "chunk":
        a, b, outp = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p", outp], stdin=subprocess.PIPE)
        for n in range(a, b):
            p.stdin.write(frame(n / FPS).tobytes())
        p.stdin.close()
        p.wait()
