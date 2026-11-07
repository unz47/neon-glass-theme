#!/usr/bin/env python3
"""Render the soft neon glow images painted under translucent terminals and chats.

Run from the plugin root:
  uv run --with numpy --with pillow python -I tools/backgrounds.py

Orca never blurs a theme background, so the glows are drawn already soft. Light is
mixed in linear space so the colors bloom instead of going muddy, and a little
noise is added before quantizing to keep the dark gradients from banding.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
W, H = 2560, 1600
rng = np.random.default_rng(47)


def to_linear(hex_color: str) -> np.ndarray:
    c = np.array([int(hex_color[i : i + 2], 16) for i in (1, 3, 5)], dtype=np.float64) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(lin: np.ndarray) -> np.ndarray:
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


ys, xs = np.mgrid[0:H, 0:W].astype(np.float64)
u = xs / W  # 0..1 across
v = ys / H  # 0..1 down
aspect = W / H


def glow(cx: float, cy: float, rx: float, ry: float, angle: float = 0.0) -> np.ndarray:
    """A soft elliptical falloff, 1 at the center. Radii are in units of image height."""
    dx = (u - cx) * aspect
    dy = v - cy
    ca, sa = np.cos(angle), np.sin(angle)
    x = dx * ca + dy * sa
    y = -dx * sa + dy * ca
    d2 = (x / rx) ** 2 + (y / ry) ** 2
    return np.exp(-0.5 * d2)


def sheen(offset: float, width: float, slope: float = 0.62) -> np.ndarray:
    """A wide diagonal band of light, like a reflection on a glass pane."""
    d = (u * aspect * slope + v) - offset
    return np.exp(-0.5 * (d / width) ** 2)


def base_gradient(top_left: str, bottom_right: str) -> np.ndarray:
    t = np.clip((u * 0.6 + v * 0.4), 0, 1)[..., None]
    return to_linear(top_left) * (1 - t) + to_linear(bottom_right) * t


def save(lin: np.ndarray, name: str) -> None:
    srgb = to_srgb(lin) * 255
    noise = rng.random(srgb.shape) - rng.random(srgb.shape)  # triangular dither, ±1 LSB
    img = np.clip(np.round(srgb + noise), 0, 255).astype(np.uint8)
    out = ROOT / "images" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img, "RGB").save(out, "WEBP", quality=90, method=6)
    print(f"{out.relative_to(ROOT)}: {out.stat().st_size / 1024:.0f} KB")


def dark() -> None:
    img = base_gradient("#120e21", "#08070f")
    layers = [
        ("#ff2d95", glow(0.84, 0.10, 0.36, 0.24, -0.35), 0.16),  # the neon pink bloom, top right
        ("#ff4fd8", glow(0.46, -0.08, 0.30, 0.10, 0.08), 0.05),  # magenta haze along the top edge
        ("#6c3cff", glow(0.06, 0.96, 0.40, 0.28, 0.25), 0.13),  # violet pool, bottom left
        ("#1fd5f0", glow(1.00, 1.04, 0.24, 0.16, 0.0), 0.06),  # a cool cyan edge
    ]
    for color, mask, strength in layers:
        img = img + to_linear(color) * (mask * strength)[..., None]
    # Two glass reflections, very faint so terminal text stays crisp.
    img = img + to_linear("#ffd6ec") * (sheen(1.05, 0.10) * 0.010)[..., None]
    img = img + to_linear("#d9ccff") * (sheen(1.42, 0.035) * 0.008)[..., None]
    save(img, "neon-glass-dark.webp")


def light() -> None:
    img = base_gradient("#f8f5fd", "#efe9f8")
    layers = [
        ("#ff7cc0", glow(0.84, 0.10, 0.42, 0.28, -0.35), 0.40),
        ("#ffb3dc", glow(0.44, -0.08, 0.34, 0.12, 0.08), 0.22),
        ("#b39bff", glow(0.06, 0.96, 0.46, 0.32, 0.25), 0.36),
        ("#8fe6ff", glow(1.00, 1.04, 0.30, 0.20, 0.0), 0.32),
    ]
    for color, mask, strength in layers:
        a = (mask * strength)[..., None]
        img = img * (1 - a) + to_linear(color) * a  # tint toward pastel, never darker than ink
    img = img + (sheen(1.05, 0.10) * 0.035)[..., None]
    img = img + (sheen(1.42, 0.035) * 0.025)[..., None]
    save(img, "neon-glass-light.webp")


if __name__ == "__main__":
    dark()
    light()
