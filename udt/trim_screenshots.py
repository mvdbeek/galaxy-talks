#!/usr/bin/env python3
"""Trim the dark slide background around screenshots, keeping just the white
UI panel. Picks the largest connected bright region (so the slide title text,
a separate blob, is excluded).

Run:  source .venv/bin/activate && python3 trim_screenshots.py
Re-render images first (from the PDF) if you want to start from the originals.
"""
from PIL import Image, ImageFilter
import numpy as np
from scipy import ndimage

SLIDES = [6, 11, 12, 13]   # slides whose screenshots should be trimmed

def crop_panel(path, blur=10, thresh=170, pad=6):
    im = Image.open(path).convert("RGB")
    g = im.convert("L").filter(ImageFilter.GaussianBlur(blur))
    m = np.asarray(g) > thresh
    lbl, n = ndimage.label(m)
    if n == 0:
        return im
    sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
    big = int(np.argmax(sizes)) + 1
    ys, xs = np.where(lbl == big)
    H, W = m.shape
    box = (max(0, xs.min() - pad), max(0, ys.min() - pad),
           min(W, xs.max() + 1 + pad), min(H, ys.max() + 1 + pad))
    return im.crop(box)

if __name__ == "__main__":
    for n in SLIDES:
        p = f"images/slide-{n:02d}.png"
        out = crop_panel(p)
        out.save(p)
        print(f"trimmed {p} -> {out.size}")
