"""
Draw the PNG icons, favicon.ico and the social sharing card with Pillow.

    make assets

Output goes to static/img/. Requires the dev dependencies (Pillow) and the Inter font
(falls back to DejaVu Sans if Inter isn't installed).
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "static" / "img"
TEAL = (14, 107, 102)
PAPER = (244, 247, 243)
INK = (27, 42, 58)
MUTED = (82, 97, 112)
MARK = (242, 203, 76)
SOFT = (226, 241, 238)

FONT_CANDIDATES = {
    "bold": ["/usr/share/fonts/opentype/inter/Inter-Bold.otf", "DejaVuSans-Bold.ttf"],
    "regular": ["/usr/share/fonts/opentype/inter/Inter-Regular.otf", "DejaVuSans.ttf"],
    "mono": ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "DejaVuSansMono.ttf"],
}


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES[kind]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def draw_mark(size: int, background=None) -> Image.Image:
    """The logo: a rounded teal square with three neat text lines."""
    scale = 4  # draw large, then downsample for smooth edges
    s = size * scale
    img = Image.new("RGBA", (s, s), background or (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=s * 8 // 32, fill=TEAL)
    width = round(s * 2.6 / 32)
    for y, x_end in ((10.5, 24), (16, 24), (21.5, 17)):
        y_px = s * y / 32
        x0, x1 = s * 8 / 32, s * x_end / 32
        d.line([(x0, y_px), (x1, y_px)], fill=PAPER, width=width)
        for x in (x0, x1):  # round caps
            r = width / 2
            d.ellipse([x - r, y_px - r, x + r, y_px + r], fill=PAPER)
    return img.resize((size, size), Image.LANCZOS)


def social_card() -> Image.Image:
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)

    img.paste(draw_mark(96), (80, 80), draw_mark(96))
    d.text((196, 104), "TidyText", font=font("bold", 50), fill=INK)

    d.text((80, 232), "Clean up messy text", font=font("bold", 76), fill=INK)
    d.text((80, 322), "in seconds.", font=font("bold", 76), fill=INK)
    d.text(
        (80, 432),
        "Fix line breaks, extra spaces and letter case.",
        font=font("regular", 34),
        fill=MUTED,
    )

    # The highlighter stat that also appears in the app.
    mono = font("mono", 30)
    label = "1,240 characters"
    d.text((80, 520), label, font=mono, fill=INK)
    x = 80 + d.textlength(label, font=mono) + 18
    tag = "−312"
    tag_w = d.textlength(tag, font=mono)
    d.rectangle([x - 6, 532, x + tag_w + 6, 556], fill=MARK)
    d.text((x, 520), tag, font=mono, fill=INK)

    d.rounded_rectangle([1000, 0, 1200, 630], radius=0, fill=SOFT)
    for i, length in enumerate((120, 120, 120, 70, 120, 95)):
        y = 150 + i * 60
        d.rounded_rectangle([1040, y, 1040 + length, y + 14], radius=7, fill=TEAL)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    draw_mark(192).save(OUT / "icon-192.png")
    maskable = Image.new("RGBA", (512, 512), TEAL)
    maskable.paste(draw_mark(400), (56, 56), draw_mark(400))
    maskable.save(OUT / "icon-512.png")
    apple = Image.new("RGB", (180, 180), PAPER)
    apple.paste(draw_mark(150), (15, 15), draw_mark(150))
    apple.save(OUT / "apple-touch-icon.png")
    draw_mark(64).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    social_card().save(OUT / "og-image.png", optimize=True)
    print("Generated icons and social card in", OUT)


if __name__ == "__main__":
    main()
