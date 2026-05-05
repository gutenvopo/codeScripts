from PIL import Image, ImageDraw, ImageFont

def make_icon(path='windows_button_test_for_Kwa.ico'):
    size = (256, 256)
    img = Image.new('RGBA', size, (28, 120, 210, 255))
    draw = ImageDraw.Draw(img)

    # Draw a rounded rectangle background
    draw.rectangle([24, 24, 232, 232], fill=(40, 140, 230, 255))

    # Draw a simple white 'K' in the center
    try:
        font = ImageFont.truetype('seguisym.ttf', 160)
    except Exception:
        try:
            font = ImageFont.truetype('arial.ttf', 160)
        except Exception:
            font = ImageFont.load_default()

    text = 'K'
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except Exception:
        try:
            w, h = font.getsize(text)
        except Exception:
            w, h = (64, 64)

    draw.text(((size[0]-w)/2, (size[1]-h)/2 - 8), text, font=font, fill=(255,255,255,255))

    # Save multiple sizes into an .ico
    sizes = [(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)]
    imgs = [img.resize(s, Image.LANCZOS) for s in sizes]
    imgs[0].save(path, formats=['ICO'], sizes=sizes)
    print(f'Icon written to: {path}')

if __name__ == '__main__':
    make_icon()
