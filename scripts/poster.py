#!/usr/bin/env python3
import argparse
from itertools import product
from pathlib import Path
from subprocess import run

import pikepdf
from pikepdf import Dictionary, Name, Stream
from rich import print

MEDIA = {
    "a6": "105x148",
    "a5": "148x210",
    "a4": "210x297",
    "a3": "297x420",
    "a2": "420x594",
    "a1": "594x841",
    "a0": "841x1189",
    "letter": "216x279",
    "legal": "216x356",
    "tabloid": "279x432",
}


def pt_to_mm(pt: float) -> float:
    return pt * 25.4 / 72.0


def mm_to_pt(pt: float) -> float:
    return pt * 72.0 / 25.4


def crop_marks(x0, y0, x1, y1, length, width=0.2):
    x0, y0 = mm_to_pt(x0), mm_to_pt(y0)
    x1, y1 = mm_to_pt(x1), mm_to_pt(y1)
    w, m = mm_to_pt(width), mm_to_pt(length)
    lines = [f"{w:.4f} w"]
    lines.append(f"{x0 - m:.4f} {y0:.4f} m {x0 + m:.4f} {y0:.4f} l S")
    lines.append(f"{x0:.4f} {y0 - m:.4f} m {x0:.4f} {y0 + m:.4f} l S")
    lines.append(f"{x1 - m:.4f} {y0:.4f} m {x1 + m:.4f} {y0:.4f} l S")
    lines.append(f"{x1:.4f} {y0 - m:.4f} m {x1:.4f} {y0 + m:.4f} l S")
    lines.append(f"{x0 - m:.4f} {y1:.4f} m {x0 + m:.4f} {y1:.4f} l S")
    lines.append(f"{x0:.4f} {y1 - m:.4f} m {x0:.4f} {y1 + m:.4f} l S")
    lines.append(f"{x1 - m:.4f} {y1:.4f} m {x1 + m:.4f} {y1:.4f} l S")
    lines.append(f"{x1:.4f} {y1 - m:.4f} m {x1:.4f} {y1 + m:.4f} l S")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(
        description="tiled poster sheets from an input PDF using LaTeX.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("input", help="input PDF")
    ap.add_argument("-p", "--page", type=int, default=1, help="input page")
    ap.add_argument(
        "-t", "--tiles", default="1x1", metavar="ROWSxCOLS", help="tiles layout"
    )
    ap.add_argument(
        "-M", "--media", default="a4", metavar="WIDTHxHEIGHT", help="media size (mm)"
    )
    ap.add_argument("-l", "--landscape", action="store_true", help="landscape media")
    ap.add_argument(
        "-m", "--margin", type=float, default=10, help="unprintable/glue margin (mm)"
    )
    ap.add_argument(
        "-b", "--bleed", type=float, default=5, help="bleed into margin (mm)"
    )
    ap.add_argument("-c", "--mark", type=float, default=5, help="cut mark size (mm)")
    ap.add_argument("-o", "--open", action="store_true", help="open output pdf")
    args = ap.parse_args()

    input_pdf = Path(args.input)
    output_pdf = input_pdf.with_suffix(f".{args.tiles}.pdf")
    with pikepdf.open(input_pdf) as src, pikepdf.Pdf.new() as dst:
        tiles = args.tiles
        rows, cols = list(map(int, tiles.split("x")))
        margin = args.margin
        bleed = min(margin, args.bleed)
        mark = args.mark
        print(f"         tiles: {tiles}")

        src_page = src.pages[args.page - 1]
        src_mb = src_page.MediaBox
        src_w, src_h = (
            pt_to_mm(float(src_mb[2]) - float(src_mb[0])),
            pt_to_mm(float(src_mb[3]) - float(src_mb[1])),
        )
        print(f"    input size: {src_w:.1f} x {src_h:.1f} mm")

        media = MEDIA.get(args.media, args.media)
        media_w, media_h = list(map(float, media.split("x")))
        if args.landscape:
            media_w, media_h = media_h, media_w
        print(f"    media size: {media_w:.1f} x {media_h:.1f} mm")

        print_w, print_h = media_w - 2 * margin, media_h - 2 * margin
        print(f"printable area: {print_w:.1f} x {print_h:.1f} mm")

        total_w, total_h = cols * print_w, rows * print_h
        print(f"    total area: {total_w:.1f} x {total_h:.1f} mm")

        # Best fit: compare unrotated vs rotated 90°
        s00 = min(total_w / src_w, total_h / src_h)
        s90 = min(total_w / src_h, total_h / src_w)

        if s90 > s00:
            rotation = 90
            scale = s90
            src_w, src_h = src_h, src_w
        else:
            rotation = 0
            scale = s00

        print(f"      rotation: {rotation} deg")
        print(f"         scale: {scale:.3f}")

        img_w, img_h = scale * src_w, scale * src_h
        print(f"    image area: {img_w:.1f} x {img_h:.1f} mm")

        form = dst.copy_foreign(src_page.as_form_xobject())
        for row, col in product(range(rows), range(cols)):
            tile_w = img_w - (cols - 1) * print_w if col == cols - 1 else print_w
            tile_h = img_h - (rows - 1) * print_h if row == rows - 1 else print_h

            page = dst.add_blank_page(page_size=(mm_to_pt(media_w), mm_to_pt(media_h)))

            if "/Resources" not in page.obj:
                page.obj.Resources = Dictionary()
            if "/XObject" not in page.obj.Resources:
                page.obj.Resources.XObject = Dictionary()
            page.obj.Resources.XObject[Name("/SRC")] = form

            clip_x = mm_to_pt(margin - bleed)
            clip_y = mm_to_pt(margin - bleed)
            clip_w = mm_to_pt(print_w + 2 * bleed)
            clip_h = mm_to_pt(print_h + 2 * bleed)
            cost, sint, shift = (0, 1, img_w) if rotation else (1, 0, 0)
            a, b = scale * cost, scale * sint
            c, d = -scale * sint, scale * cost
            e, f = (
                mm_to_pt(margin + shift - col * print_w),
                mm_to_pt(media_h - margin - img_h + row * print_h),
            )
            content = f"q {clip_x:.6f} {clip_y:.6f} {clip_w:.6f} {clip_h:.6f} re W n {a:.9f} {b:.9f} {c:.9f} {d:.9f} {e:.6f} {f:.6f} cm /SRC Do Q\n"

            content += crop_marks(
                margin,
                media_h - tile_h - margin,
                tile_w + margin,
                media_h - margin,
                mark,
            )

            page.obj.Contents = Stream(dst, content.encode("ascii"))
        dst.save(output_pdf)

    if args.open:
        run(f'xdg-open "{output_pdf}"', shell=True)


if __name__ == "__main__":
    main()
