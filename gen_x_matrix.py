# -*- coding: utf-8 -*-
"""
X投稿用「還元率マップ」マトリクス画像の生成（PIL・完全オリジナル）

- サイトの図解 diagram_store_matrix と同じデータ・配色をPNG化（1200x900）
- 保存版系のバズ型（表を画像で保存させる）用。ブランド名入りで拡散時の流入も狙う
使い方: python gen_x_matrix.py  → x_matrix.png を出力
"""
import os
import re
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE_DIR, "x_matrix.png")
FONT = r"C:\Windows\Fonts\meiryob.ttc"

W, H = 1200, 960
NAVY = "#283593"
BLUE = "#3949ab"
ORANGE = "#ff6f00"
ORANGE2 = "#ff9800"
LIGHT = "#eef0fa"
GRAY = "#8a90a8"
DARK = "#3a3f5a"

COLS = ["三井住友NL", "JCB CARD W", "楽天カード", "イオンカード"]
ROWS = [
    ("コンビニ", ["最大7%", "1%", "1%", "0.5%"]),
    ("ネット通販", ["0.5%", "Amazon 2%", "楽天市場 3%", "0.5%"]),
    ("イオン系", ["0.5%", "1%", "1%", "1%+優待"]),
    ("基本還元", ["0.5%", "1%", "1%", "0.5%"]),
]


def cell_style(v):
    m = re.search(r"(\d+\.?\d*)", v)
    n = float(m.group(1)) if m else 0
    if n >= 3:
        return ORANGE, "#ffffff"
    if n >= 2:
        return ORANGE2, "#ffffff"
    if n >= 1:
        return BLUE, "#ffffff"
    return LIGHT, DARK


def f(size):
    return ImageFont.truetype(FONT, size)


def center_text(d, xy, text, font, fill):
    x, y = xy
    bb = d.textbbox((0, 0), text, font=font)
    d.text((x - (bb[2] - bb[0]) / 2, y - (bb[3] - bb[1]) / 2 - bb[1]), text, font=font, fill=fill)


def main():
    img = Image.new("RGB", (W, H), "#f7f8fd")
    d = ImageDraw.Draw(img)

    # 上部バー＋タイトル
    d.rectangle([0, 0, W, 14], fill=ORANGE)
    center_text(d, (W / 2, 78), "どこで使う？×どのカード？", f(52), NAVY)
    center_text(d, (W / 2, 148), "還元率マップ【保存版】", f(52), NAVY)
    d.rounded_rectangle([W / 2 - 130, 190, W / 2 + 130, 198], 4, fill=ORANGE)

    # グリッド
    x0, y0 = 40, 250
    lw = 230                      # 行ラベル列の幅
    cw = (W - x0 * 2 - lw) // 4   # カード列の幅
    hh, rh, gap = 78, 108, 12

    for i, c in enumerate(COLS):
        x = x0 + lw + i * cw
        d.rounded_rectangle([x, y0, x + cw - gap, y0 + hh], 14, fill=NAVY)
        size = 30 if len(c) <= 6 else 26
        center_text(d, (x + (cw - gap) / 2, y0 + hh / 2), c, f(size), "#ffffff")

    for r, (label, cells) in enumerate(ROWS):
        y = y0 + hh + 16 + r * (rh + gap)
        d.text((x0 + lw - 24 - d.textbbox((0, 0), label, font=f(32))[2], y + rh / 2 - 22),
               label, font=f(32), fill=DARK)
        for i, v in enumerate(cells):
            x = x0 + lw + i * cw
            bg, fg = cell_style(v)
            d.rounded_rectangle([x, y, x + cw - gap, y + rh], 16, fill=bg)
            size = 40 if len(v) <= 4 else 30
            center_text(d, (x + (cw - gap) / 2, y + rh / 2), v, f(size), fg)

    # 注記＋ブランド
    y_note = y0 + hh + 16 + 4 * (rh + gap) + 18
    center_text(d, (W / 2, y_note), "※タッチ決済・特約店等の条件あり。最新の還元条件は各公式サイトで。", f(22), GRAY)
    center_text(d, (W / 2, y_note + 56), "クレカ比較Labo｜creca-labo.com", f(30), NAVY)

    img.save(OUT)
    print("saved:", OUT, img.size)


if __name__ == "__main__":
    main()
