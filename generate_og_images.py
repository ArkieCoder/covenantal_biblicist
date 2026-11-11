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
BORDER_COLOR = "#f5f5f5"

# Facebook Page cover. 851x315 is Meta's recommended size; the 2x render keeps
# the wordmark crisp on high-DPI screens and is downscaled by Facebook.
# FB_WORDMARK_SPAN keeps the wordmark inside the mobile crop (~2.4:1, left
# aligned, i.e. the left ~756 of 851 px) and clear of the profile picture that
# overlaps the left edge.
FB_DIR = SCRIPT_DIR / "assets" / "fb"
FB_COVER_SIZES = [(1702, 630), (851, 315)]
FB_WORDMARK_SPAN = 0.75

# Cover spacing, expressed in 1x (851x315) pixels. Facebook displays the cover
# at that size, so the 2x render doubles both values and the two files stay
# proportionally identical.
FB_COVER_REF_WIDTH = 851
FB_COVER_MARGIN = 5     # blank canvas before the outer rule
FB_COVER_TITLE_LIFT = 20  # wordmark raised above the vertical centre

# Facebook profile picture. Facebook crops it to a circle, so each letter is
# pinched on its outer edge to follow the crop. Copperplate Bold is 1.35x as
# wide as its cap height, so a C and B side by side read squat in a square and
# are stretched vertically to fill it.
PROFILE_SIZE = 1024
PROFILE_SUPERSAMPLE = 2
PROFILE_CAP = 315
PROFILE_GAP = 108
PROFILE_PINCH = 0.30
PROFILE_LETTER_STRETCH = 2.4
PROFILE_CROSS_HEIGHT = 560
COPPERPLATE_CAP_RATIO = 0.535  # cap height / font size, Copperplate Bold
DAGGER_HEIGHT_RATIO = 0.635    # glyph height / font size, U+2020


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


def add_border_and_ornaments(img, scale=1.0, inset=None):
    """Double white rule plus L-shaped corner flourishes.

    Metrics are those of the 1200x630 cards; ``scale`` multiplies them so the
    same design can be drawn on a larger or smaller canvas. ``inset`` overrides
    the outer rule's inset and shifts the rest of the assembly inward with it,
    preserving every gap, which gives the border a margin from the edge.
    """
    draw = ImageDraw.Draw(img)
    width, height = img.size

    def px(value):
        return max(1, round(value * scale))

    outer = px(2) if inset is None else inset
    delta = outer - px(2)
    inner = px(8) + delta
    offset, arm = px(16) + delta, px(22)

    # Double border
    draw.rectangle([outer, outer, width - 1 - outer, height - 1 - outer],
                   outline=BORDER_COLOR, width=1)
    draw.rectangle([inner, inner, width - 1 - inner, height - 1 - inner],
                   outline=BORDER_COLOR, width=1)

    # Corner flourishes - small L shapes
    right, bottom = width - offset, height - offset
    # Top-left
    draw.line([offset, offset, offset + arm, offset], fill=BORDER_COLOR, width=1)
    draw.line([offset, offset, offset, offset + arm], fill=BORDER_COLOR, width=1)
    # Top-right
    draw.line([right - arm, offset, right, offset], fill=BORDER_COLOR, width=1)
    draw.line([right, offset, right, offset + arm], fill=BORDER_COLOR, width=1)
    # Bottom-left
    draw.line([offset, bottom - arm, offset, bottom], fill=BORDER_COLOR, width=1)
    draw.line([offset, bottom, offset + arm, bottom], fill=BORDER_COLOR, width=1)
    # Bottom-right
    draw.line([right - arm, bottom, right, bottom], fill=BORDER_COLOR, width=1)
    draw.line([right, bottom - arm, right, bottom], fill=BORDER_COLOR, width=1)

    return img


def fit_font(font_path, index, text, draw, target_width, base_size=100):
    """Pick the font size whose rendered width is closest to ``target_width``."""
    try:
        base = ImageFont.truetype(str(font_path), base_size, index=index)
    except Exception:
        base = ImageFont.truetype(str(font_path), base_size)
    bbox = draw.textbbox((0, 0), text, font=base)
    measured = bbox[2] - bbox[0]
    size = max(1, round(base_size * target_width / measured))
    try:
        return ImageFont.truetype(str(font_path), size, index=index)
    except Exception:
        return ImageFont.truetype(str(font_path), size)


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


def generate_wordmark_card(width, height, out_path, blog_title="Covenantal Biblicist",
                           margin=None, lift=0):
    """Site/about style card: wordmark only, no separator, at any canvas size.

    ``margin`` is the blank canvas left before the outer rule; ``lift`` raises
    the wordmark above the vertical centre. Both are in canvas pixels.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new('RGB', (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    text = blog_title.upper()
    font = fit_font(FONTS_DIR / "Copperplate.ttc", 0, text, draw,
                    width * FB_WORDMARK_SPAN)

    bbox = draw.textbbox((0, 0), text, font=font)
    x = (width - (bbox[2] - bbox[0])) // 2
    y = (height - (bbox[3] - bbox[1])) // 2 - lift
    draw.text((x, y), text, fill=TEXT_COLOR, font=font)

    img = add_border_and_ornaments(img, scale=width / WIDTH, inset=margin)
    img.save(out_path, "PNG", optimize=True)
    print(f"Generated {out_path}")
    return out_path


def _profile_letter(char, size, canvas):
    """Draw one letter with its ink starting at x=0, centred vertically.

    Left-anchoring is what makes the caller's paste offsets meaningful: the
    advance width is fixed, so both letters land in predictable columns.
    """
    layer = Image.new('RGBA', (canvas, canvas), (0, 0, 0, 0))
    font = ImageFont.truetype(str(FONTS_DIR / "Copperplate.ttc"), size, index=2)
    ImageDraw.Draw(layer).text((0, canvas // 2), char, font=font,
                               fill=TEXT_COLOR, anchor='lm')
    return layer, font


def _stretch_vertical(layer, factor):
    """Scale the ink on the vertical axis only, keeping it centred."""
    if abs(factor - 1) < 1e-6:
        return layer
    box = layer.getchannel('A').getbbox()
    ink = layer.crop(box)
    ink = ink.resize((ink.width, max(1, round(ink.height * factor))),
                     Image.LANCZOS)
    out = Image.new('RGBA', layer.size, (0, 0, 0, 0))
    out.paste(ink, (box[0], (layer.height - ink.height) // 2))
    return out


def _pinch_outer_edge(layer, side, strength):
    """Compress each row toward the letter's inner edge.

    The compression follows ``k = 1 - strength * t^2`` where ``t`` runs -1..1
    down the ink, a second-order approximation to the circle Facebook crops to,
    so the outer corners tuck inside it while the middle stays full width.
    """
    x0, y0, x1, y1 = layer.getchannel('A').getbbox()
    x1 -= 1
    y1 -= 1
    mid, half = (y0 + y1) / 2, max(1.0, (y1 - y0) / 2)
    out = Image.new('RGBA', layer.size, (0, 0, 0, 0))
    for y in range(y0, y1 + 1):
        t = (y - mid) / half
        k = 1 - strength * t * t
        if k <= 0.02:
            continue
        row = layer.crop((x0, y, x1 + 1, y + 1))
        row = row.resize((max(1, round(row.width * k)), 1), Image.LANCZOS)
        out.paste(row, (x1 + 1 - row.width if side == 'left' else x0, y))
    return out


def _dagger(size, canvas):
    """The U+2020 dagger, cropped to its ink.

    It is the only cross-like glyph in Copperplate; the outline crosses
    (U+271D, U+2720, U+2719) all fall back to .notdef in this font.
    """
    layer = Image.new('RGBA', (canvas, canvas), (0, 0, 0, 0))
    font = ImageFont.truetype(str(FONTS_DIR / "Copperplate.ttc"), size, index=2)
    ImageDraw.Draw(layer).text((canvas // 2, canvas // 2), '\u2020',
                               font=font, fill=TEXT_COLOR, anchor='mm')
    return layer.crop(layer.getchannel('A').getbbox())


def _guard_band(glyph):
    """Rows covered by the crossguard: the widest part of the dagger."""
    alpha = glyph.getchannel('A').load()
    width, height = glyph.size
    spans = []
    for y in range(height):
        xs = [x for x in range(width) if alpha[x, y] > 128]
        spans.append(max(xs) - min(xs) if xs else 0)
    widest = max(spans)
    rows = [y for y, span in enumerate(spans) if span >= 0.92 * widest]
    return min(rows), max(rows)


def _stretch_dagger(glyph, target_height):
    """Lengthen the dagger's stem, leaving the crossguard untouched.

    Scaling the glyph normally would take the guard from 73 px to 153 px while
    the stem stayed thin, inverting the weight. Splitting the glyph at the
    guard and stretching only the stem above and below lengthens the cross
    while every stroke keeps its original thickness, and the guard keeps its
    flared ends.
    """
    guard_top, guard_bottom = _guard_band(glyph)
    width, height = glyph.size
    head = glyph.crop((0, 0, width, guard_top))
    guard = glyph.crop((0, guard_top, width, guard_bottom + 1))
    foot = glyph.crop((0, guard_bottom + 1, width, height))

    factor = (target_height - guard.height) / (head.height + foot.height)

    def scaled(part):
        return part.resize((part.width, max(1, round(part.height * factor))),
                           Image.LANCZOS)

    parts = [scaled(head), guard, scaled(foot)]
    out = Image.new('RGBA', (width, sum(p.height for p in parts)),
                    (0, 0, 0, 0))
    y = 0
    for part in parts:
        out.paste(part, (0, y))
        y += part.height
    return out.crop(out.getchannel('A').getbbox())


def generate_profile_pic(out_path):
    """Facebook profile picture: pinched C and B flanking a dagger cross.

    Rendered at ``PROFILE_SUPERSAMPLE``x and downscaled once, so the pinch and
    the dagger stretch are resampled a single time.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    size = PROFILE_SIZE * PROFILE_SUPERSAMPLE
    centre = size // 2

    cap_px = round(PROFILE_CAP * PROFILE_SUPERSAMPLE)
    gap_px = round(PROFILE_GAP * PROFILE_SUPERSAMPLE)
    font_size = round(cap_px / COPPERPLATE_CAP_RATIO)

    _, font = _profile_letter('C', font_size, size)
    box = font.getbbox('C')
    letter_w = box[2] - box[0]
    left = centre - (letter_w * 2 + gap_px) // 2

    img = Image.new('RGB', (size, size), BG_COLOR)

    c, _ = _profile_letter('C', font_size, size)
    c = _pinch_outer_edge(_stretch_vertical(c, PROFILE_LETTER_STRETCH),
                          'left', PROFILE_PINCH)
    img.paste(c, (left, 0), c)

    b, _ = _profile_letter('B', font_size, size)
    b = _pinch_outer_edge(_stretch_vertical(b, PROFILE_LETTER_STRETCH),
                          'right', PROFILE_PINCH)
    img.paste(b, (left + letter_w + gap_px, 0), b)

    dagger = _dagger(round(PROFILE_CAP * PROFILE_SUPERSAMPLE * 1.09
                           / DAGGER_HEIGHT_RATIO), size)
    dagger = _stretch_dagger(dagger, PROFILE_CROSS_HEIGHT * PROFILE_SUPERSAMPLE)
    img.paste(dagger, (centre - dagger.width // 2,
                       centre - dagger.height // 2), dagger)

    img = img.resize((PROFILE_SIZE, PROFILE_SIZE), Image.LANCZOS)
    img.save(out_path, "PNG", optimize=True)
    print(f"Generated {out_path}")
    return out_path


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

    for width, height in FB_COVER_SIZES:
        unit = width / FB_COVER_REF_WIDTH
        generate_wordmark_card(
            width, height, FB_DIR / f"cover-{width}x{height}.png",
            margin=round(FB_COVER_MARGIN * unit),
            lift=round(FB_COVER_TITLE_LIFT * unit))

    generate_profile_pic(
        FB_DIR / f"profile-{PROFILE_SIZE}x{PROFILE_SIZE}.png")


if __name__ == '__main__':
    main()
