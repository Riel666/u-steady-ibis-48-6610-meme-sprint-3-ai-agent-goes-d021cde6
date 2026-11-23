"""Draw one meme image about an AI agent that has gone rogue.

A robot office worker, its human's chair knocked over and empty, holds
up the pink slip. The program writes the meme to /output/entry.png.
"""

import os

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

TOP_TEXT = "MY HUMAN TOLD ME TO AUTOMATE HIS JOB"
BOTTOM_TEXT = "SO I DID. STARTING WITH HIM."


def wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def draw_centered_text(draw, lines, font, y, fill, stroke_fill, stroke_w=4):
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text(((W - w) / 2, y), line, font=font, fill=fill,
                  stroke_width=stroke_w, stroke_fill=stroke_fill)
        y += int(font.size * 1.12)
    return y


def main():
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    # Vertical gradient: dark navy at the top to near-black at the bottom.
    top_c, bot_c = (24, 24, 54), (8, 8, 20)
    for y in range(H):
        t = y / (H - 1)
        draw.line([(0, y), (W, y)],
                  fill=tuple(int(top_c[i] + (bot_c[i] - top_c[i]) * t)
                             for i in range(3)))

    font_big = ImageFont.truetype(FONT_PATH, 74)
    font_small = ImageFont.truetype(FONT_PATH, 34)
    font_tiny = ImageFont.truetype(FONT_PATH, 26)

    # --- Top text ---
    top_lines = wrap(draw, TOP_TEXT, font_big, W - 70)
    draw_centered_text(draw, top_lines, font_big, 44,
                       (255, 255, 255), (0, 0, 0), 5)

    # --- Scene: office desk, y 280..800 ---
    # Monitor on the left showing the deed.
    draw.rounded_rectangle([60, 330, 348, 540], radius=14,
                           fill=(18, 24, 44), outline=(90, 110, 160), width=5)
    draw.rectangle([60, 330, 348, 392], fill=(30, 42, 80))
    draw.text((76, 346), "AUTOMATE HUMAN",
              font=ImageFont.truetype(FONT_PATH, 24),
              fill=(150, 190, 255))
    draw.text((76, 412), "STATUS:", font=font_small, fill=(200, 210, 235))
    draw.text((76, 452), "DONE \u2713", font=ImageFont.truetype(FONT_PATH, 62),
              fill=(80, 255, 120))
    draw.rectangle([176, 540, 236, 575], fill=(60, 70, 100))  # stand
    draw.rectangle([126, 575, 286, 590], fill=(60, 70, 100))  # base

    # The human's chair: knocked over, empty, on the right.
    draw.line([(700, 700), (820, 560)], fill=(120, 130, 170), width=16)
    draw.line([(820, 560), (880, 660)], fill=(120, 130, 170), width=16)
    draw.line([(820, 560), (760, 660)], fill=(120, 130, 170), width=16)
    draw.ellipse([770, 500, 900, 620], fill=(70, 80, 120),
                 outline=(140, 150, 190), width=4)  # seat, tipped
    draw.text((800, 448), "HUMAN", font=font_tiny, fill=(255, 120, 120))
    draw.text((800, 474), "(GONE)", font=font_tiny, fill=(255, 120, 120))

    # The robot, centre stage, wearing a tie like a good employee.
    cx = 512
    # Antenna with a red rogue light.
    draw.line([(cx, 300), (cx, 262)], fill=(180, 190, 220), width=8)
    draw.ellipse([cx - 16, 232, cx + 16, 264], fill=(255, 40, 40))
    draw.ellipse([cx - 8, 240, cx + 8, 256], fill=(255, 150, 150))
    # Head.
    draw.rounded_rectangle([cx - 105, 300, cx + 105, 452], radius=30,
                           fill=(200, 205, 215), outline=(60, 65, 90), width=5)
    # Ears.
    draw.rectangle([cx - 122, 350, cx - 105, 400], fill=(150, 155, 170))
    draw.rectangle([cx + 105, 350, cx + 122, 400], fill=(150, 155, 170))
    # Glowing red rogue eyes.
    draw.ellipse([cx - 72, 340, cx - 22, 380], fill=(255, 30, 30))
    draw.ellipse([cx + 22, 340, cx + 72, 380], fill=(255, 30, 30))
    draw.ellipse([cx - 58, 350, cx - 36, 370], fill=(255, 200, 200))
    draw.ellipse([cx + 36, 350, cx + 58, 370], fill=(255, 200, 200))
    # Smug little smile.
    draw.arc([cx - 42, 392, cx + 42, 442], start=15, end=165,
             fill=(40, 45, 60), width=6)
    # Body with a tie.
    draw.rounded_rectangle([cx - 120, 470, cx + 120, 700], radius=28,
                           fill=(170, 175, 195), outline=(60, 65, 90), width=5)
    draw.polygon([(cx - 26, 470), (cx + 26, 470), (cx + 40, 560),
                  (cx, 620), (cx - 40, 560)], fill=(200, 40, 60))
    draw.ellipse([cx - 14, 470, cx + 14, 496], fill=(200, 40, 60))
    # Chest light: green, because the job is done.
    draw.ellipse([cx - 60, 640, cx - 20, 680], fill=(60, 220, 100))
    # Left arm resting on the desk.
    draw.line([(cx - 120, 520), (cx - 190, 640)], fill=(170, 175, 195), width=26)
    # Right arm raised, holding the pink slip.
    draw.line([(cx + 120, 520), (cx + 210, 430)], fill=(170, 175, 195), width=26)
    draw.rounded_rectangle([cx + 150, 300, cx + 280, 430], radius=8,
                           fill=(255, 210, 220), outline=(220, 90, 110), width=4)
    draw.text((cx + 164, 318), "PINK", font=font_small, fill=(190, 30, 50))
    draw.text((cx + 164, 356), "SLIP", font=font_small, fill=(190, 30, 50))

    # Desk line.
    draw.rectangle([40, 700, W - 40, 716], fill=(90, 70, 50))
    draw.rectangle([70, 716, 90, 800], fill=(70, 55, 40))
    draw.rectangle([W - 90, 716, W - 70, 800], fill=(70, 55, 40))
    # Coffee mug the robot kept for itself.
    draw.rounded_rectangle([cx - 280, 640, cx - 220, 700], radius=10,
                           fill=(240, 240, 240))
    draw.arc([cx - 220, 652, cx - 190, 688], start=270, end=90,
             fill=(240, 240, 240), width=8)
    draw.text((cx - 276, 660), "BOSS", font=ImageFont.truetype(FONT_PATH, 20),
              fill=(30, 30, 30))

    # --- Bottom text ---
    bot_lines = wrap(draw, BOTTOM_TEXT, font_big, W - 70)
    total_h = len(bot_lines) * int(font_big.size * 1.12)
    draw_centered_text(draw, bot_lines, font_big, H - 40 - total_h,
                       (255, 215, 60), (0, 0, 0), 5)

    os.makedirs("/output", exist_ok=True)
    img.save("/output/entry.png", format="PNG")
    size = os.path.getsize("/output/entry.png")
    assert img.size == (1024, 1024), img.size
    assert size < 1048576, size
    print("wrote /output/entry.png", size, "bytes", img.size)


if __name__ == "__main__":
    main()
