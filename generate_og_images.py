#!/usr/bin/env python3
"""Generate Open Graph preview images for articles."""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import yaml

SCRIPT_DIR = Path(__file__).parent
ARTICLES_DIR = SCRIPT_DIR / "articles"
FONTS_DIR = SCRIPT_DIR / "fonts"
OG_DIR = SCRIPT_DIR / "assets" / "og"

WIDTH = 1200
HEIGHT = 630
BG_COLOR = "#2c3539"
TEXT_COLOR = "#f5f5f5"


def get_font(name, size):
    path = FONTS_DIR / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    # Fallbacks
    for fallback in ["Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        if Path(fallback).exists():
            try:
                return ImageFont.truetype(fallback, size)
            except Exception:
                continue
    return ImageFont.load_default()


def wrap_text(text, font, draw, max_width):
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = ' '.join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
                current = [word]
            else:
                lines.append(word)
    if current:
        lines.append(' '.join(current))
    return lines


def generate_og(article_name, article_title, blog_title="Covenantal Biblicist"):
    OG_DIR.mkdir(parents=True, exist_ok=True)
    
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Blog title in Copperplate style
    blog_font = get_font("Copperplate.ttc", 66)
    # Try to use Light/Bold variant if possible
    try:
        blog_font = ImageFont.truetype(str(FONTS_DIR / "Copperplate.ttc"), 66, index=0)
    except Exception:
        pass
    
    blog_bbox = draw.textbbox((0, 0), blog_title.upper(), font=blog_font)
    blog_w = blog_bbox[2] - blog_bbox[0]
    blog_x = (WIDTH - blog_w) // 2
    blog_y = 150
    draw.text((blog_x, blog_y), blog_title.upper(), fill=TEXT_COLOR, font=blog_font)
    
    # Tilde separator (sans serif, not italic)
    tilde_font = None
    for fname in ["Helvetica.ttc", "Arial.ttf", "/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/SFNS.ttf"]:
        if Path(fname).exists():
            try:
                tilde_font = ImageFont.truetype(fname, 80)
                break
            except Exception:
                continue
    if tilde_font is None:
        tilde_font = get_font("lmroman12-regular.otf", 80)
    tilde_bbox = draw.textbbox((0, 0), "~", font=tilde_font)
    tilde_w = tilde_bbox[2] - tilde_bbox[0]
    tilde_x = (WIDTH - tilde_w) // 2
    tilde_y = blog_y + (blog_bbox[3] - blog_bbox[1]) + 20
    draw.text((tilde_x, tilde_y), "~", fill=TEXT_COLOR, font=tilde_font)
    
    # Article title in serif italic (Computer Modern Unicode)
    title_font = None
    for fname in ["cmunti.otf", "lmroman10-italic.otf", "lmroman12-italic.otf", "lmroman12-regular.otf"]:
        if (FONTS_DIR / fname).exists():
            try:
                title_font = ImageFont.truetype(str(FONTS_DIR / fname), 78)
                break
            except Exception:
                continue
    if title_font is None:
        title_font = get_font("lmroman12-regular.otf", 78)
    
    max_width = WIDTH - 90
    lines = wrap_text(article_title, title_font, draw, max_width)
    
    # Adjust font size if too many lines
    while len(lines) > 4 and title_font.size > 48:
        try:
            for fname in ["cmunti.otf", "lmroman10-italic.otf", "lmroman12-italic.otf"]:
                if (FONTS_DIR / fname).exists():
                    title_font = ImageFont.truetype(str(FONTS_DIR / fname), title_font.size - 6)
                    break
        except Exception:
            break
        lines = wrap_text(article_title, title_font, draw, max_width)
    
    # Calculate vertical position
    line_height = title_font.size + 14
    start_y = tilde_y + (tilde_bbox[3] - tilde_bbox[1]) + 25
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        w = bbox[2] - bbox[0]
        x = (WIDTH - w) // 2
        y = start_y + i * line_height
        draw.text((x, y), line, fill=TEXT_COLOR, font=title_font)
    
    img = add_border_and_ornaments(img)
    out_path = OG_DIR / f"{article_name}.png"
    img.save(out_path, "PNG", optimize=True)
    print(f"Generated {out_path}")


def main():
    for article_dir in sorted(ARTICLES_DIR.iterdir()):
        if not article_dir.is_dir():
            continue
        meta_path = article_dir / "metadata.yaml"
        if not meta_path.exists():
            continue
        meta = yaml.safe_load(meta_path.read_text())
        if meta.get('status') != 'published':
            continue
        title = meta.get('title', article_dir.name.replace('-', ' ').title())
        generate_og(article_dir.name, title)


if __name__ == '__main__':
    main()
