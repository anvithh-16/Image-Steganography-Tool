# 🔐 Image Steganography Tool

> Hide secret text messages or images inside ordinary PNG files using LSB (Least Significant Bit) pixel manipulation. No visible trace. No GUI required.

---

## 📦 Requirements

```bash
pip install numpy pillow opencv-python
```

---

## 🗂️ Project Structure

```
stego/
├── stego_core.py   # Core engine: embed, extract, PSNR, header logic
├── encode.py       # CLI encoder — hides text or image into a cover PNG
├── decode.py       # CLI decoder — extracts hidden payload from stego PNG
├── analyze.py      # Capacity report and bit-plane visualizer
├── demo.py         # End-to-end demo (no external files needed)
└── README.md
```

---

## 🚀 Quick Start

### Run the demo (no files needed)
```bash
python3 demo.py
```
This creates a synthetic cover image, encodes a message, decodes it, and saves a bit-plane visualization to `demo_output/`.

---

## 💻 Usage

### Encode — hide a text message
```bash
python3 encode.py --cover cover.png --text "your secret message" --out stego.png
```

### Encode — hide an image inside an image
```bash
python3 encode.py --cover cover.png --secret-image hidden.png --out stego.png
```

### Encode — use 2 LSBs for 2× capacity
```bash
python3 encode.py --cover cover.png --text "long secret..." --lsb 2 --out stego.png
```

### Decode — extract hidden payload
```bash
python3 decode.py --stego stego.png
python3 decode.py --stego stego.png --lsb 2              # if encoded with --lsb 2
python3 decode.py --stego stego.png --out recovered.png  # for image payloads
```

### Analyze — capacity report and bit-plane visual
```bash
python3 analyze.py --cover cover.png
python3 analyze.py --cover cover.png --stego stego.png --out bitplanes.png
```
---

## ⚙️ How It Works

Every pixel in an RGB image is represented as three values (R, G, B), each 0–255.  
The **least significant bit** of each value contributes only ±1 to the color — completely imperceptible to human vision.

By replacing those LSBs with the binary representation of a secret payload:

| LSB setting | Bits per pixel | Visibility |
|-------------|----------------|------------|
| `--lsb 1`   | 3 bits/px      | Invisible (PSNR > 70 dB) |
| `--lsb 2`   | 6 bits/px      | Barely visible (PSNR ~44 dB) |

### Header Format (21 bytes)

A structured header is embedded before the payload:

| Field         | Size    | Description                        |
|---------------|---------|------------------------------------|
| Magic bytes   | 4 bytes | `STEG` — identifies a stego image  |
| Payload type  | 1 byte  | `0x01` = text, `0x02` = image      |
| Width         | 2 bytes | Image width (0 for text payloads)  |
| Height        | 2 bytes | Image height (0 for text payloads) |
| Payload length| 4 bytes | Size of payload in bytes           |
| SHA-256 digest| 8 bytes | First 8 bytes for integrity check  |

---

## 📊 PSNR Quality Guide

| PSNR      | Quality                        |
|-----------|--------------------------------|
| > 50 dB   | Excellent — visually identical |
| 35–50 dB  | Good — imperceptible to most   |
| < 35 dB   | Noticeable — use `--lsb 1`     |

---

## 📋 Example Output

```
====================================================
  Image Steganography — Encoder
====================================================
  Cover image  : cover.png
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

## ✅ Challenges Addressed

1. **Lossless encoding** — LSB replacement changes pixel values by at most ±1, preserving visual integrity (PSNR typically > 70 dB with `--lsb 1`).
2. **Capacity management** — Header + payload size is checked against available bits before embedding; an error is thrown if too large.
3. **Encode/decode symmetry** — A structured 21-byte header with magic bytes, length field, and SHA-256 digest ensures perfect extraction every time.
4. **Dual payload support** — Both text (UTF-8) and image (raw RGB bytes) payloads share the same pipeline, differentiated by a type flag in the header.

---

## 📄 License

MIT License — free to use, modify, and distribute.
