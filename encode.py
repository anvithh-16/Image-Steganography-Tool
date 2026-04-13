#!/usr/bin/env python3
"""
encode.py — Embed a secret text message or image into a cover image.

Usage:
  python encode.py --cover <cover.png> --text "your secret" --out <stego.png>
  python encode.py --cover <cover.png> --secret-image <hidden.png> --out <stego.png>
  python encode.py --cover <cover.png> --text "secret" --lsb 2 --out <stego.png>
"""

import argparse
import sys
import os
import numpy as np
from PIL import Image

# Allow running from project root
sys.path.insert(0, os.path.dirname(__file__))
from stego_core import (
    build_header, embed, psnr, capacity,
    HEADER_SIZE, TYPE_TEXT, TYPE_IMAGE
)


def load_rgb(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.array(img, dtype=np.uint8)


def encode_text(cover: np.ndarray, text: str, lsb_bits: int) -> np.ndarray:
    payload = text.encode("utf-8")
    header  = build_header(TYPE_TEXT, payload, 0, 0)
    data    = header + payload
    print(f"  [+] Text payload   : {len(payload)} bytes")
    print(f"  [+] Total to embed : {len(data)} bytes ({len(data)*8} bits)")
    print(f"  [+] Cover capacity : {capacity(cover, lsb_bits)} bytes")
    if len(data) > capacity(cover, lsb_bits):
        sys.exit("[!] Error: payload too large for this cover image.")
    return embed(cover, data, lsb_bits)


def encode_image(cover: np.ndarray, secret_path: str, lsb_bits: int) -> np.ndarray:
    secret_img = Image.open(secret_path).convert("RGB")
    sw, sh = secret_img.size
    payload = np.array(secret_img, dtype=np.uint8).tobytes()
    header  = build_header(TYPE_IMAGE, payload, sw, sh)
    data    = header + payload
    print(f"  [+] Secret image   : {sw}×{sh} px, {len(payload)} bytes")
    print(f"  [+] Total to embed : {len(data)} bytes ({len(data)*8} bits)")
    print(f"  [+] Cover capacity : {capacity(cover, lsb_bits)} bytes")
    if len(data) > capacity(cover, lsb_bits):
        sys.exit("[!] Error: secret image too large for this cover image.")
    return embed(cover, data, lsb_bits)


def main():
    parser = argparse.ArgumentParser(
        description="LSB Image Steganography — Encoder"
    )
    parser.add_argument("--cover",        required=True, help="Path to cover (host) PNG image")
    parser.add_argument("--out",          required=True, help="Output stego PNG path")
    parser.add_argument("--text",         default=None,  help="Secret text to hide")
    parser.add_argument("--secret-image", default=None,  help="Secret image to hide")
    parser.add_argument("--lsb",          type=int, default=1, choices=[1, 2],
                        help="Number of LSBs to use per channel (1=invisible, 2=2× capacity)")
    args = parser.parse_args()

    if not args.text and not args.secret_image:
        sys.exit("[!] Provide --text or --secret-image.")
    if args.text and args.secret_image:
        sys.exit("[!] Provide only one of --text or --secret-image.")

    print(f"\n{'='*52}")
    print(f"  Image Steganography — Encoder")
    print(f"{'='*52}")
    print(f"  Cover image  : {args.cover}")
    print(f"  LSB bits     : {args.lsb}")

    cover = load_rgb(args.cover)
    h, w, _ = cover.shape
    print(f"  Cover size   : {w}×{h} px")

    if args.text:
        stego = encode_text(cover, args.text, args.lsb)
    else:
        stego = encode_image(cover, args.secret_image, args.lsb)

    # Save
    Image.fromarray(stego.astype(np.uint8)).save(args.out, format="PNG")

    # Quality report
    score = psnr(cover, stego)
    print(f"\n  [✓] Stego image saved : {args.out}")
    print(f"  [✓] PSNR score        : {score:.2f} dB  {'(excellent — invisible)' if score > 50 else '(good)' if score > 35 else '(visible noise)'}")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    main()
