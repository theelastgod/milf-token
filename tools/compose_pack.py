#!/usr/bin/env python3
"""Compose $MILF social + site assets from the voxel sprite and pose stills."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/Users/wendellphillips/milf-token")
SRC = Path("/Users/wendellphillips/.grok/sessions/%2FUsers%2Fwendellphillips/01a02cca-fda3-7720-a7f8-60fea331482c/images")
ORIG = Path("/Users/wendellphillips/Desktop/milftoken_social.png")
SPRITE = Path("/Users/wendellphillips/milf-cougar/assets/voxel-sprite.png")
TOKEN_SRC = Path("/Users/wendellphillips/milf-cougar/mint/token.png")

CYAN = (45, 206, 241, 255)
CYAN_RGB = (45, 206, 241)
WHITE = (255, 255, 255, 255)
NAVY = (36, 42, 120, 255)
RED = (226, 28, 44, 255)

ASSETS = ROOT / "assets"
SOCIAL = ROOT / "socials"
PACK = SOCIAL / "pack"
MINT = ROOT / "mint"

FONT_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"


def ensure():
    for p in (ASSETS, SOCIAL, PACK, MINT, ROOT / "copy"):
        p.mkdir(parents=True, exist_ok=True)


def font(path, size):
    return ImageFont.truetype(path, size)


def solid(size, color=CYAN):
    return Image.new("RGBA", size, color)


def chroma_cut(im: Image.Image, key=CYAN_RGB, tol=38) -> Image.Image:
    arr = np.array(im.convert("RGBA"))
    kr, kg, kb = key
    mask = (
        (np.abs(arr[:, :, 0].astype(np.int16) - kr) <= tol)
        & (np.abs(arr[:, :, 1].astype(np.int16) - kg) <= tol)
        & (np.abs(arr[:, :, 2].astype(np.int16) - kb) <= tol)
    )
    arr[mask, 3] = 0
    return Image.fromarray(arr, "RGBA")


def bbox_opaque(im: Image.Image, pad=8):
    a = im.split()[-1]
    box = a.getbbox()
    if not box:
        return im
    x0, y0, x1, y1 = box
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(im.width, x1 + pad)
    y1 = min(im.height, y1 + pad)
    return im.crop((x0, y0, x1, y1))


def fit_contain(im: Image.Image, box, anchor="center"):
    bw, bh = box
    im = im.convert("RGBA")
    scale = min(bw / im.width, bh / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    return im.resize((nw, nh), Image.Resampling.LANCZOS)


def paste_center(base, sprite, xy=None, y_bias=0):
    if xy is None:
        x = (base.width - sprite.width) // 2
        y = (base.height - sprite.height) // 2 + y_bias
    else:
        x, y = xy
    base.alpha_composite(sprite, (int(x), int(y)))
    return base


def crop_square_subject(im: Image.Image, scale_up=1.0):
    """Center-crop a tall cyan studio shot to square, keeping the figure."""
    im = im.convert("RGBA")
    w, h = im.size
    side = min(w, h)
    # bias toward upper body on tall shots
    left = (w - side) // 2
    top = max(0, int((h - side) * 0.12))
    if top + side > h:
        top = h - side
    crop = im.crop((left, top, left + side, top + side))
    if scale_up != 1.0:
        # zoom into subject
        s = crop.size[0]
        m = int(s * (1 - 1 / scale_up) / 2)
        crop = crop.crop((m, m, s - m, s - m)).resize((s, s), Image.Resampling.LANCZOS)
    return crop


def pixel_heart(size=128) -> Image.Image:
    """8-bit heart matching the original mark."""
    grid = [
        "0011001100",
        "0111111110",
        "1111111111",
        "1111111111",
        "1111111111",
        "0111111110",
        "0011111100",
        "0001111000",
        "0000110000",
        "0000000000",
    ]
    n = 10
    cell = size // n
    im = Image.new("RGBA", (cell * n, cell * n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shine = {(1, 2), (2, 1)}
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch != "1":
                continue
            x0, y0 = x * cell, y * cell
            color = (255, 255, 255, 255) if (x, y) in shine else RED
            d.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=color)
    return im


def extract_original_heart() -> Image.Image:
    im = Image.open(ORIG).convert("RGBA")
    heart = im.crop((538, 272, 584, 316))
    heart = chroma_cut(heart, CYAN_RGB, 50)
    return bbox_opaque(heart, 2)


def circle_mask(size):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size - 1, size - 1), fill=255)
    return m


def make_pfp(bust: Image.Image) -> Image.Image:
    sq = crop_square_subject(bust, scale_up=1.08)
    canvas = solid((1024, 1024))
    fitted = fit_contain(sq, (1024, 1024))
    paste_center(canvas, fitted)
    # circular export with thin white ring
    out = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    mask = circle_mask(1024)
    circ = Image.new("RGBA", (1024, 1024), CYAN)
    circ.paste(canvas, (0, 0))
    out.paste(circ, (0, 0), mask)
    ring = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((18, 18, 1005, 1005), outline=(255, 255, 255, 255), width=18)
    out.alpha_composite(ring)
    return out


def make_token(face: Image.Image, sprite: Image.Image) -> tuple[Image.Image, Image.Image]:
    # pump.fun token: full body on cyan square
    token = solid((1024, 1024))
    cut = chroma_cut(sprite, CYAN_RGB, 42)
    cut = bbox_opaque(cut, 4)
    body = fit_contain(cut, (860, 940))
    paste_center(token, body, y_bias=20)

    # circular logo from face
    face_sq = crop_square_subject(face, scale_up=1.15)
    logo = solid((1024, 1024))
    fitted = fit_contain(face_sq, (1024, 1024))
    paste_center(logo, fitted, y_bias=40)
    circ = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    mask = circle_mask(1024)
    circ.paste(logo, (0, 0), mask)
    ring = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((22, 22, 1001, 1001), outline=(255, 255, 255, 255), width=22)
    circ.alpha_composite(ring)
    heart = pixel_heart(150)
    circ.alpha_composite(heart, (1024 - 210, 1024 - 210))
    return token, circ


def draw_wordmark(draw: ImageDraw.ImageDraw, xy, size, fill=WHITE):
    f = font(FONT_BLACK, size)
    draw.text(xy, "MILF", font=f, fill=fill)
    return draw.textbbox(xy, "MILF", font=f)


def banner(mascot: Image.Image, size=(1500, 500), subtitle=None) -> Image.Image:
    w, h = size
    canvas = solid((w, h))
    cut = chroma_cut(mascot, CYAN_RGB, 42)
    cut = bbox_opaque(cut, 2)
    body = fit_contain(cut, (int(h * 0.92), int(h * 0.96)))
    paste_center(canvas, body, (int(w * 0.62), (h - body.height) // 2 + 8))
    d = ImageDraw.Draw(canvas)
    f = font(FONT_BLACK, int(h * 0.28))
    text = "MILF"
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = int(w * 0.08)
    ty = (h - th) // 2 - int(h * 0.04)
    d.text((tx, ty), text, font=f, fill=WHITE)
    heart = pixel_heart(int(h * 0.22))
    canvas.alpha_composite(heart, (tx + tw + int(h * 0.06), ty + th // 2 - heart.height // 2 + 8))
    if subtitle:
        sf = font(FONT_BOLD, int(h * 0.07))
        d.text((tx, ty + th + int(h * 0.04)), subtitle, font=sf, fill=(255, 255, 255, 230))
    return canvas


def og_card(mascot: Image.Image) -> Image.Image:
    canvas = banner(mascot, (1200, 630), subtitle="VOXEL PRIME ON SOLANA")
    return canvas


def story(mascot: Image.Image) -> Image.Image:
    w, h = 1080, 1920
    canvas = solid((w, h))
    cut = chroma_cut(mascot, CYAN_RGB, 42)
    cut = bbox_opaque(cut, 2)
    body = fit_contain(cut, (920, 1280))
    paste_center(canvas, body, ((w - body.width) // 2, int(h * 0.22)))
    d = ImageDraw.Draw(canvas)
    f = font(FONT_BLACK, 168)
    bbox = d.textbbox((0, 0), "MILF", font=f)
    tw = bbox[2] - bbox[0]
    tx = (w - tw) // 2 - 40
    d.text((tx, 120), "MILF", font=f, fill=WHITE)
    heart = pixel_heart(120)
    canvas.alpha_composite(heart, (tx + tw + 24, 168))
    sf = font(FONT_BOLD, 36)
    sub = "$MILF  ·  SOLANA"
    sb = d.textbbox((0, 0), sub, font=sf)
    d.text(((w - (sb[2] - sb[0])) // 2, h - 180), sub, font=sf, fill=WHITE)
    return canvas


def post_lockup(mascot: Image.Image) -> Image.Image:
    w = h = 1080
    canvas = solid((w, h))
    cut = chroma_cut(mascot, CYAN_RGB, 42)
    cut = bbox_opaque(cut, 2)
    body = fit_contain(cut, (720, 780))
    paste_center(canvas, body, y_bias=70)
    d = ImageDraw.Draw(canvas)
    f = font(FONT_BLACK, 140)
    bbox = d.textbbox((0, 0), "MILF", font=f)
    tw = bbox[2] - bbox[0]
    tx = (w - tw) // 2 - 36
    d.text((tx, 48), "MILF", font=f, fill=WHITE)
    heart = pixel_heart(96)
    canvas.alpha_composite(heart, (tx + tw + 18, 78))
    return canvas


def telegram(mascot: Image.Image) -> Image.Image:
    return post_lockup(mascot)


def save_jpeg(im: Image.Image, path: Path, quality=92):
    rgb = Image.new("RGB", im.size, CYAN_RGB)
    rgb.paste(im, mask=im.split()[-1] if im.mode == "RGBA" else None)
    rgb.save(path, "JPEG", quality=quality, optimize=True, subsampling=1)


def save_png(im: Image.Image, path: Path):
    im.save(path, "PNG", optimize=True)


def favicons(logo: Image.Image):
    for size, name in ((32, "favicon-32.png"), (180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")):
        save_png(logo.resize((size, size), Image.Resampling.LANCZOS), ASSETS / name)


def save_pose_square(src: Path, dest: Path, zoom=1.0):
    im = Image.open(src)
    sq = crop_square_subject(im, scale_up=zoom)
    canvas = solid(sq.size)
    canvas.alpha_composite(sq)
    save_jpeg(canvas, dest)
    save_jpeg(canvas, ASSETS / dest.name)


def main():
    ensure()
    wave = Image.open(SRC / "1.jpg")
    face = Image.open(SRC / "2.jpg")
    hip = Image.open(SRC / "3.jpg")
    bust = Image.open(SRC / "4.jpg")
    walk = Image.open(SRC / "5.jpg")
    sit = Image.open(SRC / "6.jpg")
    sprite = Image.open(SPRITE)
    orig = Image.open(ORIG)

    # site mascots
    save_png(sprite.convert("RGBA"), ASSETS / "mascot.png")
    save_jpeg(orig.convert("RGBA"), ASSETS / "lockup.jpg")
    save_pose_square(SRC / "1.jpg", SOCIAL / "wave.jpg", 1.0)
    save_pose_square(SRC / "3.jpg", SOCIAL / "hip.jpg", 1.0)
    save_pose_square(SRC / "4.jpg", SOCIAL / "bust.jpg", 1.05)
    save_pose_square(SRC / "5.jpg", SOCIAL / "walk.jpg", 1.0)
    save_pose_square(SRC / "6.jpg", SOCIAL / "sit.jpg", 1.0)
    save_pose_square(SRC / "2.jpg", SOCIAL / "face.jpg", 1.12)

    heart = pixel_heart(256)
    save_png(heart, ASSETS / "heart.png")
    orig_heart = extract_original_heart()
    save_png(orig_heart.resize((128, 128), Image.Resampling.NEAREST), ASSETS / "heart-src.png")

    pfp = make_pfp(bust)
    token, logo = make_token(face, sprite)
    save_png(pfp, ASSETS / "pfp.png")
    save_jpeg(pfp, SOCIAL / "pfp.jpg")
    save_jpeg(pfp, PACK / "01-pfp.jpg")
    save_png(token, ASSETS / "token.png")
    save_png(token, MINT / "token.png")
    save_png(logo, ASSETS / "logo.png")
    save_png(logo, MINT / "logo.png")
    save_jpeg(logo, SOCIAL / "logo.jpg")
    favicons(logo)

    b1500 = banner(sprite, (1500, 500))
    b1920 = banner(sprite, (1920, 640))
    b16 = banner(sprite, (1920, 1080), subtitle="VOXEL PRIME ON SOLANA")
    dex = banner(sprite, (1500, 500))
    og = og_card(sprite)
    st = story(hip)
    pst = post_lockup(wave)
    tg = telegram(sit)

    save_jpeg(b1500, SOCIAL / "x-banner.jpg")
    save_jpeg(b1500, PACK / "02-x-banner.jpg")
    save_png(dex, PACK / "07-dex-banner-1500x500.png")
    save_jpeg(dex, PACK / "07-dex-banner-1500x500.jpg")
    save_jpeg(dex, MINT / "dexscreener-header.jpg")
    save_jpeg(b1920, ASSETS / "banner.jpg")
    save_jpeg(b16, MINT / "banner.jpg")
    save_png(b16, MINT / "banner.png")
    save_jpeg(og, ASSETS / "og.jpg")
    save_jpeg(og, SOCIAL / "og.jpg")
    save_jpeg(og, PACK / "03-og.jpg")
    save_jpeg(pst, SOCIAL / "post.jpg")
    save_jpeg(pst, PACK / "04-post.jpg")
    save_jpeg(st, ASSETS / "story.jpg")
    save_jpeg(st, SOCIAL / "story.jpg")
    save_jpeg(st, PACK / "05-story.jpg")
    save_jpeg(st, MINT / "story.jpg")
    save_jpeg(tg, SOCIAL / "telegram.jpg")
    save_jpeg(tg, PACK / "06-telegram.jpg")

    # site gallery stills as jpeg
    for name in ("wave", "hip", "bust", "walk", "sit", "face"):
        src = SOCIAL / f"{name}.jpg"
        if src.exists():
            Image.open(src).save(ASSETS / f"{name}.jpg", quality=92)

    print("composed")
    for folder in (ASSETS, PACK, MINT):
        print(folder)
        for p in sorted(folder.iterdir()):
            if p.is_file():
                print(f"  {p.name:32} {p.stat().st_size:8d}")


if __name__ == "__main__":
    main()
