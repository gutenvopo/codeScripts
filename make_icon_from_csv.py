#!/usr/bin/env python3
"""Generate a simple .ico from the provided CSV by rendering the first row's server/sponsor.
"""
import csv
import argparse
from PIL import Image, ImageDraw, ImageFont
import os


def pick_text_from_csv(csv_path):
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) >= 2:
                # Use the sponsor (index 2) or server (index 1)
                first = rows[1]
                if len(first) > 2 and first[2].strip():
                    return first[2]
                if len(first) > 1 and first[1].strip():
                    return first[1]
    except Exception:
        pass
    # Fallback
    return "SpeedTest"


def make_icon(text, out_path, size=256):
    img = Image.new('RGBA', (size, size), (40, 116, 166, 255))
    draw = ImageDraw.Draw(img)
    try:
        # Try to load a truetype font; falls back to default
        font = ImageFont.truetype('arial.ttf', int(size / 5))
    except Exception:
        font = ImageFont.load_default()

    # Shorten text to a few chars if too long
    if len(text) > 12:
        text = ''.join(w[0] for w in text.split()[:3]).upper()

    w, h = draw.textsize(text, font=font)
    draw.text(((size - w) / 2, (size - h) / 2), text, font=font, fill=(255, 255, 255, 255))

    # Save as .ico (Pillow will include multiple sizes if provided)
    try:
        img.save(out_path, format='ICO')
    except Exception:
        # fallback: save PNG and then try to convert via .ico extension
        png_path = out_path + '.png'
        img.save(png_path, format='PNG')
        os.replace(png_path, out_path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--csv', required=True, help='Path to internet_speed_log.csv')
    p.add_argument('--out', required=True, help='Output .ico path')
    args = p.parse_args()

    text = pick_text_from_csv(args.csv)
    make_icon(text, args.out)
    print(f"Generated icon at: {args.out} (text: {text})")


if __name__ == '__main__':
    main()
