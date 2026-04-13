#!/usr/bin/env python3
"""
analyze.py — Capacity report + bit-plane visualizer.

Usage:
  python analyze.py --cover cover.png
  python analyze.py --cover cover.png --stego stego.png --out bitplanes.png
"""

import argparse
import sys
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from stego_core import psnr, capacity


def load_rgb(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.uint8)


def extract_lsb_plane(img: np.ndarray, bit: int = 0) -> np.ndarray:
    """Extract a single bit plane and scale to 0/255 for visibility."""
    plane = ((img >> bit) & 1).astype(np.uint8) * 255
    return plane  # shape H×W×3


def make_bitplane_visual(original: np.ndarray, stego: np.ndarray,
                          out_path: str, thumb: int = 300):
    """
    Save a side-by-side comparison of the LSB planes of original vs stego,
    plus the original and stego thumbnails.
    Panel layout (left→right):
      [Original] [Stego] [LSB original] [LSB stego]
    """
    h, w, _ = original.shape
    # Resize to thumb for display
    def resize(arr):
        img = Image.fromarray(arr.astype(np.uint8))
        img.thumbnail((thumb, thumb))
        return np.array(img)

    orig_t  = resize(original)
    stego_t = resize(stego)
    lsb_o   = resize(extract_lsb_plane(original, 0))
    lsb_s   = resize(extract_lsb_plane(stego, 0))

    th, tw, _ = orig_t.shape
    pad = 8
    label_h = 22

    canvas_w = tw * 4 + pad * 5
    canvas_h = th + label_h + pad * 2
    canvas = np.full((canvas_h, canvas_w, 3), 240, dtype=np.uint8)

    panels = [orig_t, stego_t, lsb_o, lsb_s]
    labels = ["Original", "Stego image", "LSB plane (original)", "LSB plane (stego)"]
    colors_label = [(30, 30, 30)] * 4

    pil_canvas = Image.fromarray(canvas)
    draw = ImageDraw.Draw(pil_canvas)

    for i, (panel, label) in enumerate(zip(panels, labels)):
        x = pad + i * (tw + pad)
        y = label_h + pad
        ph, pw, _ = panel.shape
        pil_canvas.paste(Image.fromarray(panel.astype(np.uint8)), (x, y))
        draw.text((x, pad // 2), label, fill=colors_label[i])

    pil_canvas.save(out_path)
    print(f"  [✓] Bit-plane visual saved: {out_path}")


def capacity_report(cover: np.ndarray, path: str):
    h, w, c = cover.shape
    print(f"\n  {'─'*46}")
    print(f"  Capacity Report — {os.path.basename(path)}")
    print(f"  {'─'*46}")
    print(f"  Image dimensions : {w} × {h} px")
    print(f"  Channels         : {c} (RGB)")
    print(f"  Total pixels     : {w*h:,}")
    print(f"  {'─'*30}")
    for bits in [1, 2]:
        cap = capacity(cover, bits)
        print(f"  LSB={bits} capacity    : {cap:,} bytes  ({cap/1024:.1f} KB)")
    print(f"  {'─'*46}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Steganography Analyzer — Capacity report & bit-plane visualizer"
    )
    parser.add_argument("--cover", required=True, help="Original cover image")
    parser.add_argument("--stego", default=None,  help="Stego image (optional, for comparison)")
    parser.add_argument("--out",   default="bitplanes.png", help="Output visual path")
    args = parser.parse_args()

    print(f"\n{'='*52}")
    print(f"  Image Steganography — Analyzer")
    print(f"{'='*52}")

    cover = load_rgb(args.cover)
    capacity_report(cover, args.cover)

    if args.stego:
        stego = load_rgb(args.stego)
        score = psnr(cover, stego)
        quality = "excellent — visually identical" if score > 50 else "good" if score > 35 else "noticeable distortion"
        print(f"  PSNR score       : {score:.2f} dB  ({quality})")
        print()
        make_bitplane_visual(cover, stego, args.out)
    else:
        print("  (Pass --stego to compare with a stego image and generate bit-plane visual)")

    print(f"{'='*52}\n")


if __name__ == "__main__":
    main()
