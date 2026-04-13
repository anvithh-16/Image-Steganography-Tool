#!/usr/bin/env python3
"""
demo.py — Full end-to-end demonstration of the steganography tool.
Creates a synthetic cover image, hides a message, decodes it,
and generates the bit-plane visualization — all without any external files.
"""

import sys
import os
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))


def make_cover(path: str, size: int = 512):
    """Generate a colorful synthetic cover image."""
    h = w = size
    img = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            img[y, x] = [
                int(255 * (x / w)),
                int(255 * (y / h)),
                int(255 * ((x + y) / (w + h))),
            ]
    # Add some noise-like texture
    rng = np.random.default_rng(42)
    img = np.clip(img.astype(np.int16) + rng.integers(-10, 10, img.shape), 0, 255).astype(np.uint8)
    Image.fromarray(img).save(path, format="PNG")
    print(f"  [+] Created cover image: {path} ({w}×{h} px)")


def run():
    os.makedirs("demo_output", exist_ok=True)
    cover_path = "demo_output/cover.png"
    stego_path = "demo_output/stego.png"
    visual_path = "demo_output/bitplanes.png"

    print(f"\n{'='*52}")
    print(f"  Image Steganography — Full Demo")
    print(f"{'='*52}\n")

    # 1. Create cover
    make_cover(cover_path)

    # 2. Encode
    secret = "Hello! This message is hidden inside the image using LSB steganography. You cannot see me!"
    print(f"\n  Secret message: \"{secret[:60]}...\"")
    print()
    os.system(f'python encode.py --cover {cover_path} --text "{secret}" --out {stego_path} --lsb 1')

    # 3. Decode
    os.system(f"python decode.py --stego {stego_path} --lsb 1")

    # 4. Analyze + visual
    os.system(f"python analyze.py --cover {cover_path} --stego {stego_path} --out {visual_path}")

    print(f"\n  Demo files written to: demo_output/")
    print(f"    cover.png      — original cover image")
    print(f"    stego.png      — stego image with hidden message")
    print(f"    bitplanes.png  — LSB plane comparison visual")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    run()
