# Image Steganography Tool

Hide secret text messages or images inside ordinary PNG images using LSB (Least Significant Bit) pixel manipulation. No visible trace. No GUI required.

---

## Requirements

```
pip install numpy pillow opencv-python
```

---

## Project Structure

```
stego/
├── stego_core.py   # Core engine: embed, extract, PSNR, header
├── encode.py       # CLI encoder
├── decode.py       # CLI decoder
├── analyze.py      # Capacity report + bit-plane visualizer
├── demo.py         # End-to-end demo (no external files needed)
└── README.md
```

---

## Quick Start

### Run the demo (no files needed)
```bash
cd stego
python demo.py
```
This creates a synthetic cover image, hides a message, decodes it, and saves the bit-plane visualization to `demo_output/`.

---

## Usage

### Encode — hide a text message
```bash
python encode.py --cover photo.png --text "your secret message" --out stego.png
```

### Encode — hide an image inside an image
```bash
python encode.py --cover photo.png --secret-image hidden.png --out stego.png
```

### Encode — use 2 LSBs for 2× capacity (slight quality tradeoff)
```bash
python encode.py --cover photo.png --text "long secret..." --lsb 2 --out stego.png
```

### Decode
```bash
python decode.py --stego stego.png
python decode.py --stego stego.png --lsb 2          # if encoded with --lsb 2
python decode.py --stego stego.png --out recovered.png   # for image payloads
```

### Analyze capacity & generate bit-plane visual
```bash
python analyze.py --cover photo.png
python analyze.py --cover photo.png --stego stego.png --out bitplanes.png
```

---

## How It Works

Every pixel in an RGB image is represented as three values (R, G, B), each 0–255.  
The **least significant bit** of each value contributes only ±1 to the color — completely imperceptible to human vision.

By replacing those LSBs with the binary representation of a secret payload:
- 1 LSB/channel → **3 bits per pixel**, invisible change
- 2 LSBs/channel → **6 bits per pixel**, still barely visible (PSNR ~44 dB)

A 21-byte header is embedded before the payload containing:
- Magic bytes `STEG` for identification
- Payload type (text or image)
- Payload dimensions (for image payloads)
- Payload length in bytes
- 8-byte SHA-256 digest for integrity verification

---

## Output Example

```
====================================================
  Image Steganography — Encoder
====================================================
  Cover image  : photo.png
  LSB bits     : 1
  Cover size   : 512×512 px
  [+] Text payload   : 91 bytes
  [+] Total to embed : 112 bytes (896 bits)
  [+] Cover capacity : 98304 bytes

  [✓] Stego image saved : stego.png
  [✓] PSNR score        : 78.34 dB  (excellent — invisible)
====================================================
```

---

## PSNR Quality Guide

| PSNR       | Quality                          |
|------------|----------------------------------|
| > 50 dB    | Excellent — visually identical   |
| 35–50 dB   | Good — imperceptible to most     |
| < 35 dB    | Noticeable — use LSB=1           |

---

## Challenges Addressed

1. **Lossless encoding** — LSB replacement ensures pixel values change by at most 1, preserving visual integrity (PSNR typically > 70 dB with LSB=1).
2. **Payload capacity management** — Header + payload size is checked against available bits before embedding; error thrown if too large.
3. **Encode/decode symmetry** — A structured 21-byte header with magic bytes, length field, and SHA-256 digest ensures perfect extraction.
4. **Dual payload support** — Both text (UTF-8 serialized) and image (raw RGB bytes) payloads share the same pipeline with a type flag in the header.
