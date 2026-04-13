#!/usr/bin/env python3
"""
decode.py — Extract a hidden text message or image from a stego image.

Usage:
  python decode.py --stego <stego.png>
  python decode.py --stego <stego.png> --out recovered.png --lsb 2
"""

import argparse
import sys
import os
import hashlib
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from stego_core import (
    parse_header, extract,
    HEADER_SIZE, TYPE_TEXT, TYPE_IMAGE
)


def load_rgb(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.array(img, dtype=np.uint8)


def main():
    parser = argparse.ArgumentParser(
        description="LSB Image Steganography — Decoder"
    )
    parser.add_argument("--stego", required=True, help="Path to stego PNG image")
    parser.add_argument("--out",   default="recovered.png",
                        help="Output path for recovered image (image payloads only)")
    parser.add_argument("--lsb",   type=int, default=1, choices=[1, 2],
                        help="LSB bits used during encoding (must match encoder)")
    args = parser.parse_args()

    print(f"\n{'='*52}")
    print(f"  Image Steganography — Decoder")
    print(f"{'='*52}")
    print(f"  Stego image  : {args.stego}")
    print(f"  LSB bits     : {args.lsb}")

    stego = load_rgb(args.stego)

    # Step 1: extract header
    header_bits = HEADER_SIZE * 8
    raw_header = extract(stego, header_bits, args.lsb)[:HEADER_SIZE]

    try:
        payload_type, img_w, img_h, payload_len, digest8 = parse_header(raw_header)
    except ValueError as e:
        sys.exit(f"[!] {e}")

    type_name = "TEXT" if payload_type == TYPE_TEXT else "IMAGE"
    print(f"  Payload type : {type_name}")
    print(f"  Payload size : {payload_len} bytes")

    # Step 2: extract payload
    total_bits = (HEADER_SIZE + payload_len) * 8
    raw_all    = extract(stego, total_bits, args.lsb)
    payload    = raw_all[HEADER_SIZE : HEADER_SIZE + payload_len]

    # Step 3: verify integrity
    actual_digest = hashlib.sha256(payload).digest()[:8]
    if actual_digest != digest8:
        print("[!] WARNING: Integrity check FAILED — payload may be corrupt or LSB mismatch.")
    else:
        print("  [✓] Integrity check  : PASSED (SHA-256 match)")

    # Step 4: output
    if payload_type == TYPE_TEXT:
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError:
            sys.exit("[!] Failed to decode text — check --lsb value matches encoder.")
        print(f"\n  {'─'*46}")
        print(f"  Hidden message:\n")
        print(f"    {text}")
        print(f"  {'─'*46}\n")

    elif payload_type == TYPE_IMAGE:
        arr = np.frombuffer(payload, dtype=np.uint8).reshape((img_h, img_w, 3))
        Image.fromarray(arr).save(args.out, format="PNG")
        print(f"  [✓] Recovered image  : {args.out}  ({img_w}×{img_h} px)")

    print(f"{'='*52}\n")


if __name__ == "__main__":
    main()
