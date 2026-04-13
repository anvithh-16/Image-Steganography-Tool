"""
stego_core.py — Core LSB steganography engine
Supports hiding text or images inside a PNG cover image.
"""

import numpy as np
from PIL import Image
import struct
import hashlib

HEADER_MAGIC = b"STEG"   # 4 bytes
TYPE_TEXT  = 0x01
TYPE_IMAGE = 0x02
# Header layout: MAGIC(4) + TYPE(1) + WIDTH(2) + HEIGHT(2) + PAYLOAD_LEN(4) + SHA256(8) = 21 bytes
HEADER_SIZE = 21


def _to_bits(data: bytes) -> np.ndarray:
    """Convert bytes to a flat array of bits (MSB first)."""
    arr = np.frombuffer(data, dtype=np.uint8)
    bits = np.unpackbits(arr)
    return bits


def _from_bits(bits: np.ndarray) -> bytes:
    """Convert flat bit array back to bytes."""
    # Pad to multiple of 8
    pad = (8 - len(bits) % 8) % 8
    if pad:
        bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
    return np.packbits(bits).tobytes()


def capacity(cover: np.ndarray, bits: int = 1) -> int:
    """Return max embeddable bytes for a given cover image using N LSBs per channel."""
    h, w, c = cover.shape
    return (h * w * c * bits) // 8


def build_header(payload_type: int, payload_bytes: bytes,
                 img_w: int = 0, img_h: int = 0) -> bytes:
    """
    Build a 21-byte header:
      4  MAGIC
      1  TYPE
      2  img width  (0 for text)
      2  img height (0 for text)
      4  payload length in bytes
      8  first 8 bytes of SHA-256 of payload
    """
    length = len(payload_bytes)
    digest = hashlib.sha256(payload_bytes).digest()[:8]
    header = (
        HEADER_MAGIC
        + struct.pack(">BHHH", payload_type, img_w, img_h, 0)[:5]  # manual below
    )
    header = (
        HEADER_MAGIC
        + struct.pack(">B", payload_type)
        + struct.pack(">H", img_w)
        + struct.pack(">H", img_h)
        + struct.pack(">I", length)
        + digest
    )
    assert len(header) == HEADER_SIZE
    return header


def parse_header(raw: bytes):
    """Parse a 21-byte header. Returns (type, img_w, img_h, payload_len, digest8)."""
    if raw[:4] != HEADER_MAGIC:
        raise ValueError("Invalid magic bytes — this image has no hidden payload.")
    payload_type = struct.unpack(">B", raw[4:5])[0]
    img_w        = struct.unpack(">H", raw[5:7])[0]
    img_h        = struct.unpack(">H", raw[7:9])[0]
    payload_len  = struct.unpack(">I", raw[9:13])[0]
    digest8      = raw[13:21]
    return payload_type, img_w, img_h, payload_len, digest8


def embed(cover: np.ndarray, data: bytes, lsb_bits: int = 1) -> np.ndarray:
    """
    Embed `data` (bytes) into the LSBs of `cover`.
    Works in-place on a copy; returns the stego array.
    """
    flat = cover.flatten().astype(np.uint8)
    bits = _to_bits(data)
    needed = len(bits)
    available = len(flat) * lsb_bits

    if needed > available:
        raise ValueError(
            f"Payload too large: need {needed} bits, cover only holds {available} bits."
        )

    mask = np.uint8((1 << lsb_bits) - 1)          # e.g. 0x01 for 1 bit
    clear_mask = np.uint8(~mask & 0xFF)

    stego = flat.copy()
    for i in range(0, needed, lsb_bits):
        chunk = bits[i : i + lsb_bits]
        # Pack chunk bits into a single value
        val = np.uint8(0)
        for b in chunk:
            val = np.uint8((val << 1) | b)
        # If chunk shorter than lsb_bits, left-shift remainder
        if len(chunk) < lsb_bits:
            val = np.uint8(val << (lsb_bits - len(chunk)))
        pixel_idx = i // lsb_bits
        stego[pixel_idx] = np.uint8((stego[pixel_idx] & clear_mask) | val)

    return stego.reshape(cover.shape)


def extract(stego: np.ndarray, n_bits: int, lsb_bits: int = 1) -> bytes:
    """
    Extract `n_bits` bits from the LSBs of `stego` and return as bytes.
    """
    flat = stego.flatten().astype(np.uint8)
    mask = np.uint8((1 << lsb_bits) - 1)
    bits = []
    pixels_needed = -(-n_bits // lsb_bits)   # ceiling division

    for i in range(pixels_needed):
        val = flat[i] & mask
        for b in range(lsb_bits - 1, -1, -1):
            bits.append(int((val >> b) & 1))

    bits_arr = np.array(bits[:n_bits], dtype=np.uint8)
    return _from_bits(bits_arr)


def psnr(original: np.ndarray, stego: np.ndarray) -> float:
    """Compute Peak Signal-to-Noise Ratio between two uint8 images."""
    mse = np.mean((original.astype(np.float64) - stego.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return 10 * np.log10((255.0 ** 2) / mse)
