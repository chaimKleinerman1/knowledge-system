"""Generate the three sample images in samples/ with Pillow.

Run: python scripts/make_samples.py

The images are drawn from code so the repository ships no downloaded photos.
The output is deterministic apart from the font, which depends on the machine.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SAMPLES_DIRECTORY = Path(__file__).resolve().parent.parent / "samples"

WHITE = "#ffffff"
BLACK = "#000000"
INK = "#1f2933"
GREY = "#8a94a6"
LIGHT_GREY = "#e4e7eb"
CARD_BLUE = "#dbe7f5"
ROAD_GREY = "#c9ced6"

CANDIDATE_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arial.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for font_path in CANDIDATE_FONT_PATHS:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)
    # Pillow ships a scalable default font since 10.1, so the script works on a bare machine too.
    return ImageFont.load_default(size=size)


def draw_dashed_line(draw: ImageDraw.ImageDraw, y: int, width: int) -> None:
    for dash_x in range(30, width - 30, 14):
        draw.line([(dash_x, y), (dash_x + 7, y)], fill=GREY, width=2)


def draw_receipt(output_path: Path) -> None:
    width, height = 420, 640
    image = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(image)
    title_font = load_font(30)
    body_font = load_font(22)
    left_x, right_x = 40, width - 40

    y = 36
    draw.text((width / 2, y), "CORNER CAFE", fill=INK, font=title_font, anchor="mt")
    y += 46
    for text in ("12 Herzl Street, Tel Aviv", "Receipt no. 10482", "2026-09-20  08:41"):
        draw.text((width / 2, y), text, fill=INK, font=body_font, anchor="mt")
        y += 32

    y += 14
    draw_dashed_line(draw, y, width)
    y += 20
    for name, amount in (("Cappuccino", "14.00"), ("Croissant", "12.00"), ("Orange juice", "16.00")):
        draw.text((left_x, y), name, fill=INK, font=body_font, anchor="lt")
        draw.text((right_x, y), amount, fill=INK, font=body_font, anchor="rt")
        y += 34

    y += 6
    draw_dashed_line(draw, y, width)
    y += 20
    for name, amount, font in (("Subtotal", "42.00", body_font), ("VAT 17%", "7.14", body_font)):
        draw.text((left_x, y), name, fill=INK, font=font, anchor="lt")
        draw.text((right_x, y), amount, fill=INK, font=font, anchor="rt")
        y += 34
    draw.text((left_x, y), "TOTAL", fill=INK, font=title_font, anchor="lt")
    draw.text((right_x, y), "49.14", fill=INK, font=title_font, anchor="rt")
    y += 46

    draw_dashed_line(draw, y, width)
    y += 30
    for text in ("Paid by card", "Thank you, come again!"):
        draw.text((width / 2, y), text, fill=INK, font=body_font, anchor="mt")
        y += 32

    image.save(output_path, format="PNG", optimize=True)


def draw_id_card(output_path: Path) -> None:
    width, height = 640, 400
    image = Image.new("RGB", (width, height), LIGHT_GREY)
    draw = ImageDraw.Draw(image)
    header_font = load_font(30)
    label_font = load_font(18)
    value_font = load_font(24)

    draw.rounded_rectangle([(20, 20), (width - 20, height - 20)], radius=24, fill=CARD_BLUE, outline=INK, width=3)
    draw.text((width / 2, 52), "IDENTITY CARD", fill=INK, font=header_font, anchor="mm")

    # Photo placeholder: a framed box with a simple head-and-shoulders silhouette.
    photo_box = [(50, 100), (210, 300)]
    draw.rectangle(photo_box, fill=WHITE, outline=INK, width=2)
    draw.ellipse([(100, 130), (160, 190)], fill=GREY)
    draw.chord([(70, 185), (190, 300)], start=180, end=360, fill=GREY)

    fields = [
        ("Name", "Dana Levi"),
        ("ID number", "032-546-718"),
        ("Date of birth", "14 March 1992"),
        ("Valid until", "31 December 2031"),
    ]
    y = 110
    for label, value in fields:
        draw.text((250, y), label.upper(), fill=GREY, font=label_font)
        draw.text((250, y + 22), value, fill=INK, font=value_font)
        y += 62

    image.save(output_path, format="PNG", optimize=True)


def draw_black_car(output_path: Path) -> None:
    width, height = 640, 400
    image = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(image)
    caption_font = load_font(34)

    draw.rectangle([(0, 322), (width, 352)], fill=ROAD_GREY)

    body_outline = [
        (80, 290),
        (80, 230),
        (130, 220),
        (190, 150),
        (400, 150),
        (500, 220),
        (560, 230),
        (560, 290),
    ]
    draw.polygon(body_outline, fill=BLACK)

    window_fill = LIGHT_GREY
    draw.polygon([(200, 160), (290, 160), (290, 218), (150, 218)], fill=window_fill)
    draw.polygon([(310, 160), (395, 160), (480, 218), (310, 218)], fill=window_fill)

    for wheel_center_x in (170, 470):
        draw.ellipse([(wheel_center_x - 42, 248), (wheel_center_x + 42, 332)], fill=BLACK)
        draw.ellipse([(wheel_center_x - 18, 272), (wheel_center_x + 18, 308)], fill=GREY)

    draw.text((width / 2, 376), "black car", fill=INK, font=caption_font, anchor="mm")

    image.save(output_path, format="PNG", optimize=True)


def main() -> None:
    SAMPLES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    draw_receipt(SAMPLES_DIRECTORY / "receipt.png")
    draw_id_card(SAMPLES_DIRECTORY / "id_card.png")
    draw_black_car(SAMPLES_DIRECTORY / "black_car.png")
    for name in ("receipt.png", "id_card.png", "black_car.png"):
        print(f"wrote {SAMPLES_DIRECTORY / name}")


if __name__ == "__main__":
    main()
