"""Build the static images used by the project page (docs/index.html).

  docs/media/system-config-1600.png  web-size copy of docs/system-config-open.png
  docs/media/og_card.png             1200x630 link-preview card (LinkedIn, X, Slack)

Run after tools/media/build_poster_videos.py, because the card uses the heart
video still. Requires: matplotlib (for the bundled DejaVu fonts) and pillow.
"""

import os

import matplotlib
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MEDIA = os.path.join(REPO, "docs", "media")
FONT_DIR = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
INK, MUTED, ACCENT = "#1b1f24", "#5b6470", "#c2410c"


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def system_figure():
    im = Image.open(os.path.join(REPO, "docs", "system-config-open.png")).convert("RGB")
    w = 1600
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(os.path.join(MEDIA, "system-config-1600.png"), optimize=True)


def og_card():
    card = Image.new("RGB", (1200, 630), "white")
    dr = ImageDraw.Draw(card)
    dr.rectangle([0, 0, 12, 630], fill=ACCENT)
    dr.text((60, 60), "OPERA", font=font(84, True), fill=INK)
    dr.text((60, 165), "OPOTEK-Verasonics Architecture", font=font(30), fill=MUTED)
    lines = ["Open-source real-time", "multi-spectral", "photoacoustic imaging"]
    for i, t in enumerate(lines):
        dr.text((60, 250 + i * 52), t, font=font(40, True), fill=INK)
    dr.text((60, 540), "MCU pulse tagging  ·  TCP + shared memory  ·  MIT",
            font=font(22), fill=MUTED)
    still = Image.open(os.path.join(MEDIA, "opera_heart_ablation.jpg")).convert("RGB")
    still = still.crop((95, 115, 1250, 680))
    still.thumbnail((520, 440), Image.LANCZOS)
    card.paste(still, (1200 - still.width - 40, (630 - still.height) // 2))
    card.save(os.path.join(MEDIA, "og_card.png"), optimize=True)


if __name__ == "__main__":
    system_figure()
    og_card()
    print("wrote system-config-1600.png and og_card.png")
