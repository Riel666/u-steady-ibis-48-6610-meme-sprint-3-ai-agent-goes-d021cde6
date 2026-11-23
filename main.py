"""Draw one meme image about an AI agent that has gone rogue.

A robot office worker, its human's chair knocked over and empty, holds
up the pink slip. The program writes the meme to /output/entry.png.

Standard library only: a pure-Python PNG encoder (zlib + struct +
binascii), a tiny rasterizer (rectangles, circles, ellipses, lines,
polygons, arcs) and a 5x7 bitmap font defined in this file. Nothing is
read from outside the repo and nothing is fetched from the network, so
the program runs on a bare python3 with no third-party packages and no
font files installed.
"""

import binascii
import math
import os
import struct
import zlib

W = H = 1024

TOP_TEXT = "MY HUMAN TOLD ME TO AUTOMATE HIS JOB"
BOTTOM_TEXT = "SO I DID. STARTING WITH HIM."

# 5x7 bitmap font: A-Z, space, period. Each glyph is 7 rows of 5 bits.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ":": ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
}

# The canvas: raw RGB bytes, row-major.
px = bytearray(W * H * 3)


def fill_rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        px[base:base + len(row)] = row


def fill_circle(cx, cy, r, c):
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(r * r - dy * dy))
        fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)


def fill_ellipse(cx, cy, rx, ry, c):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy * dy) / float(ry * ry)
        dx = int(rx * math.sqrt(max(0.0, t)))
        fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)


def thick_line(x0, y0, x1, y1, c, width):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    r = max(1, width // 2)
    while True:
        fill_circle(x0, y0, r, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def fill_polygon(points, c):
    ys = [p[1] for p in points]
    n = len(points)
    for y in range(min(ys), max(ys) + 1):
        xs = []
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (x1 - x0) * (y - y0) / float(y1 - y0))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            x_lo = int(math.ceil(xs[j]))
            x_hi = int(math.floor(xs[j + 1]))
            if x_hi >= x_lo:
                fill_rect(x_lo, y, x_hi - x_lo + 1, 1, c)


def _round_rect_fill(x, y, w, h, r, c):
    fill_rect(x + r, y, w - 2 * r, h, c)
    fill_rect(x, y + r, w, h - 2 * r, c)
    fill_circle(x + r, y + r, r, c)
    fill_circle(x + w - r - 1, y + r, r, c)
    fill_circle(x + r, y + h - r - 1, r, c)
    fill_circle(x + w - r - 1, y + h - r - 1, r, c)


def round_rect(x, y, w, h, r, fill, outline=None, ow=0):
    if outline is not None and ow > 0:
        _round_rect_fill(x, y, w, h, r, outline)
        _round_rect_fill(x + ow, y + ow, w - 2 * ow, h - 2 * ow,
                         max(0, r - ow), fill)
    else:
        _round_rect_fill(x, y, w, h, r, fill)


def arc(cx, cy, rx, ry, start_deg, end_deg, c, width):
    steps = max(8, int(abs(end_deg - start_deg)))
    prev = None
    for i in range(steps + 1):
        a = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        p = (cx + int(rx * math.cos(a)), cy + int(ry * math.sin(a)))
        if prev is not None:
            thick_line(prev[0], prev[1], p[0], p[1], c, width)
        prev = p


def _draw_glyph(x, y, glyph, scale, color):
    for row_i, row in enumerate(glyph):
        for col_i, bit in enumerate(row):
            if bit == "1":
                fill_rect(x + col_i * scale, y + row_i * scale,
                          scale, scale, color)


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def draw_text(x, y, text, scale, color, outline=None):
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        if outline is not None:
            for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3),
                           (-3, -3), (3, -3), (-3, 3), (3, 3)):
                _draw_glyph(x + ox, y + oy, glyph, scale, outline)
        _draw_glyph(x, y, glyph, scale, color)
        x += 6 * scale
    return x


def wrap(text, scale, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def draw_centered_lines(lines, scale, y, fill, outline=None):
    lh = int(7 * scale * 1.15)
    for line in lines:
        w = text_width(line, scale)
        draw_text((W - w) // 2, y, line, scale, fill, outline)
        y += lh
    return y


def write_png(path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw += px[y * stride:(y + 1) * stride]

    def chunk(typ, payload):
        out = struct.pack(">I", len(payload)) + typ + payload
        out += struct.pack(">I", binascii.crc32(typ + payload) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def main():
    # Vertical gradient: dark navy at the top to near-black at the bottom.
    top_c, bot_c = (24, 24, 54), (8, 8, 20)
    for y in range(H):
        t = y / (H - 1)
        fill_rect(0, y, W, 1, tuple(int(top_c[i] + (bot_c[i] - top_c[i]) * t)
                                    for i in range(3)))

    # --- Top text ---
    top_lines = wrap(TOP_TEXT, 6, W - 70)
    draw_centered_lines(top_lines, 6, 40, (255, 255, 255), (0, 0, 0))

    # --- Scene: office desk, y 280..800 ---
    # Monitor on the left showing the deed.
    round_rect(60, 330, 288, 210, 14, (18, 24, 44),
               outline=(90, 110, 160), ow=5)
    fill_rect(65, 335, 278, 57, (30, 42, 80))
    draw_text(76, 346, "AUTOMATE HUMAN", 2, (150, 190, 255))
    draw_text(76, 412, "STATUS:", 3, (200, 210, 235))
    draw_text(76, 452, "DONE", 5, (80, 255, 120))
    fill_rect(176, 540, 60, 35, (60, 70, 100))  # stand
    fill_rect(126, 575, 160, 15, (60, 70, 100))  # base

    # The human's chair: knocked over, empty, on the right.
    thick_line(700, 700, 820, 560, (120, 130, 170), 16)
    thick_line(820, 560, 880, 660, (120, 130, 170), 16)
    thick_line(820, 560, 760, 660, (120, 130, 170), 16)
    fill_ellipse(835, 560, 69, 64, (140, 150, 190))  # seat, tipped
    fill_ellipse(835, 560, 65, 60, (70, 80, 120))
    draw_text(800, 448, "HUMAN", 2, (255, 120, 120))
    draw_text(800, 474, "GONE", 2, (255, 120, 120))

    # The robot, centre stage, wearing a tie like a good employee.
    cx = 512
    # Antenna with a red rogue light.
    thick_line(cx, 300, cx, 262, (180, 190, 220), 8)
    fill_circle(cx, 248, 16, (255, 40, 40))
    fill_circle(cx, 248, 8, (255, 150, 150))
    # Head.
    round_rect(cx - 105, 300, 210, 152, 30, (200, 205, 215),
               outline=(60, 65, 90), ow=5)
    # Ears.
    fill_rect(cx - 122, 350, 17, 50, (150, 155, 170))
    fill_rect(cx + 105, 350, 17, 50, (150, 155, 170))
    # Glowing red rogue eyes.
    fill_ellipse(cx - 47, 360, 25, 20, (255, 30, 30))
    fill_ellipse(cx + 47, 360, 25, 20, (255, 30, 30))
    fill_ellipse(cx - 47, 360, 11, 10, (255, 200, 200))
    fill_ellipse(cx + 47, 360, 11, 10, (255, 200, 200))
    # Smug little smile.
    arc(cx, 417, 42, 25, 15, 165, (40, 45, 60), 6)
    # Body with a tie.
    round_rect(cx - 120, 470, 240, 230, 28, (170, 175, 195),
               outline=(60, 65, 90), ow=5)
    fill_polygon([(cx - 26, 470), (cx + 26, 470), (cx + 40, 560),
                  (cx, 620), (cx - 40, 560)], (200, 40, 60))
    fill_ellipse(cx, 483, 14, 13, (200, 40, 60))
    # Chest light: green, because the job is done.
    fill_ellipse(cx - 40, 660, 20, 20, (60, 220, 100))
    # Left arm resting on the desk.
    thick_line(cx - 120, 520, cx - 190, 640, (170, 175, 195), 26)
    # Right arm raised, holding the pink slip.
    thick_line(cx + 120, 520, cx + 210, 430, (170, 175, 195), 26)
    round_rect(cx + 150, 300, 130, 130, 8, (255, 210, 220),
               outline=(220, 90, 110), ow=4)
    draw_text(cx + 164, 318, "PINK", 3, (190, 30, 50))
    draw_text(cx + 164, 356, "SLIP", 3, (190, 30, 50))

    # Desk line.
    fill_rect(40, 700, W - 80, 16, (90, 70, 50))
    fill_rect(70, 716, 20, 84, (70, 55, 40))
    fill_rect(W - 90, 716, 20, 84, (70, 55, 40))
    # Coffee mug the robot kept for itself.
    round_rect(cx - 280, 640, 60, 60, 10, (240, 240, 240))
    arc(cx - 205, 670, 15, 18, 270, 450, (240, 240, 240), 8)
    draw_text(cx - 276, 660, "BOSS", 2, (30, 30, 30))

    # --- Bottom text ---
    bot_lines = wrap(BOTTOM_TEXT, 6, W - 70)
    total_h = len(bot_lines) * int(7 * 6 * 1.15)
    draw_centered_lines(bot_lines, 6, H - 40 - total_h,
                        (255, 215, 60), (0, 0, 0))

    os.makedirs("/output", exist_ok=True)
    size = write_png("/output/entry.png")
    assert (W, H) == (1024, 1024), (W, H)
    assert size < 1048576, size
    print("wrote /output/entry.png", size, "bytes (1024, 1024)")


if __name__ == "__main__":
    main()
