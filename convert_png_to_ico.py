#!/usr/bin/env python3
"""Convert a PNG image to a multi-size .ico file using Pillow.
Usage: python convert_png_to_ico.py --in input.png --out output.ico
"""
import argparse
from PIL import Image


def convert(in_path, out_path):
    img = Image.open(in_path).convert('RGBA')
    # Common icon sizes
    sizes = [(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)]
    icons = [img.resize(s, Image.LANCZOS) for s in sizes]
    icons[0].save(out_path, format='ICO', sizes=sizes)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--in', dest='inp', required=True)
    p.add_argument('--out', dest='out', required=True)
    args = p.parse_args()
    convert(args.inp, args.out)
    print(f"Saved ICO: {args.out}")


if __name__ == '__main__':
    main()
