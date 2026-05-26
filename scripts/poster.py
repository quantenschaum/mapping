#!/usr/bin/env python3
import argparse
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, select_autoescape
from pypdf import PdfReader
from rich import print

TEMPLATE = r"""\documentclass{article}
\usepackage[paperwidth={{media_w}}mm,paperheight={{media_h}}mm,margin={{margin}}mm]{geometry}
\usepackage{graphicx}
\usepackage{tikz}
\pagestyle{empty}
\setlength{\parindent}{0pt}

\begin{document}
{% for t in tiles %}
\begin{tikzpicture}[x=1mm,y=-1mm]
    \useasboundingbox (0,0) rectangle ({{print_w}},{{print_h}});
    \clip (-{{bleed}},-{{bleed}}) rectangle ({{t.w}}+{{bleed}},{{t.h}}+{{bleed}});

    \node[anchor=north west,inner sep=0pt] at ({{t.x}},{{t.y}}) {
        \includegraphics[page={{page}},angle={{rotation}},scale={{scale}}]{ {{- input -}} }
    };

    {% if debug %}
    \draw[red,line width=0.2mm] (0,0) rectangle ({{t.w}},{{t.h}});
    \draw[blue,line width=0.2mm] (-{{bleed}},-{{bleed}}) rectangle ({{t.w}}+{{bleed}},{{t.h}}+{{bleed}});
    {% endif %}

    % crop marks
    \draw[black,line width=0.2mm] (-{{mark}},0) -- ({{mark}},0);
    \draw[black,line width=0.2mm] (0,-{{mark}}) -- (0,{{mark}});
    \draw[black,line width=0.2mm] ({{t.w}}-{{mark}},0) -- ({{t.w}}+{{mark}},0);
    \draw[black,line width=0.2mm] ({{t.w}},-{{mark}}) -- ({{t.w}},{{mark}});
    \draw[black,line width=0.2mm] (-{{mark}},{{t.h}}) -- ({{mark}},{{t.h}});
    \draw[black,line width=0.2mm] (0,{{t.h}}-{{mark}}) -- (0,{{t.h}}+{{mark}});
    \draw[black,line width=0.2mm] ({{t.w}}-{{mark}},{{t.h}}) -- ({{t.w}}+{{mark}},{{t.h}});
    \draw[black,line width=0.2mm] ({{t.w}},{{t.h}}-{{mark}}) -- ({{t.w}},{{t.h}}+{{mark}});

    {% if text %}
    \node[anchor=center,font=\small] at (0.5*{{t.w}},-0.5*{{bleed}}) {tile ({{t.r}},{{t.c}}) {% if t.r==1 -%} CUT {%- else -%} GLUE to ({{t.r-1}},{{t.c}}) {%- endif -%} }; % top
    \node[anchor=center,font=\small] at (0.5*{{t.w}},{{t.h}}+0.5*{{bleed}}) {CUT}; % bottom
    \node[rotate=90,anchor=center,font=\small] at (-0.5*{{bleed}},0.5*{{t.h}}) { {%- if t.c==1 -%} CUT {%- else -%} GLUE to ({{t.r}},{{t.c-1}}) {%- endif -%} }; % left
    \node[rotate=270,anchor=center,font=\small] at ({{t.w}}+0.5*{{bleed}},0.5*{{t.h}}) {CUT}; % right
    {% endif %}
\end{tikzpicture}
\newpage

{% endfor %}
\end{document}
"""


def pt_to_mm(pt: float) -> float:
    return pt * 25.4 / 72.0


def read_pdf_page_size_mm(pdf_path: Path, page_num_1based: int) -> tuple[float, float]:
    reader = PdfReader(str(pdf_path))
    page = reader.pages[page_num_1based - 1]
    w_pt = float(page.mediabox.width)
    h_pt = float(page.mediabox.height)
    return pt_to_mm(w_pt), pt_to_mm(h_pt)


@dataclass
class Tile:
    r: int
    c: int
    x: float
    y: float
    w: float
    h: float


def run(cmd):
    print(f"[yellow]{cmd}")
    subprocess.run(cmd, shell=True, check=True)


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
        "-m", "--media", default="a4", metavar="WIDTHxHEIGHT", help="media size (mm)"
    )
    ap.add_argument("-l", "--landscape", action="store_true", help="landscape media")
    ap.add_argument(
        "-M", "--margin", type=float, default=10, help="unprintable/glue margin (mm)"
    )
    ap.add_argument(
        "-b", "--bleed", type=float, default=5, help="bleed into margin (mm)"
    )
    ap.add_argument("-c", "--mark", type=float, default=5, help="cut mark size (mm)")
    ap.add_argument(
        "-T", "--text", action="store_true", help="text instructions on margin"
    )
    ap.add_argument(
        "-d", "--debug", action="store_true", help="debug output, show bounding boxes"
    )
    ap.add_argument("-k", "--keep", action="store_true", help="keep intermediate files")
    ap.add_argument("-o", "--open", action="store_true", help="open output pdf")
    args = ap.parse_args()

    input_pdf = Path(args.input)

    tiles = args.tiles
    rows, cols = list(map(int, tiles.split("x")))
    margin = args.margin
    bleed = min(margin, args.bleed)
    mark = args.mark
    print(f"         tiles: {tiles}")

    src_w, src_h = read_pdf_page_size_mm(input_pdf, args.page)
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

    Tiles = []
    W, H = print_w, print_h
    for r in range(rows):
        for c in range(cols):
            w, h = W, H
            if r == rows - 1:
                h = img_h - (rows - 1) * H
            if c == cols - 1:
                w = img_w - (cols - 1) * W
            Tiles.append(Tile(r=r + 1, c=c + 1, x=-c * W, y=-r * H, w=w, h=h))

    env = Environment(
        autoescape=select_autoescape(enabled_extensions=(), default_for_string=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    tmpl = TEMPLATE
    if args.debug:
        tmpl = tmpl.replace("%debug", "")
    tmpl = env.from_string(tmpl)

    tex = tmpl.render(
        input=str(input_pdf),
        page=args.page,
        margin=margin,
        bleed=bleed,
        mark=mark,
        media_w=media_w,
        media_h=media_h,
        print_w=print_w,
        print_h=print_h,
        rotation=rotation,
        scale=scale,
        tiles=Tiles,
        debug=args.debug,
        text=args.text,
    )

    output_pdf = input_pdf.with_suffix(f".{tiles}.pdf")
    tex_file = Path("sheets.tex")
    tex_file.write_text(tex)
    run(f"latexmk -pdf -interaction=nonstopmode {tex_file}")
    shutil.move("sheets.pdf", output_pdf)
    if not args.keep:
        run(f"latexmk -C {tex_file}")
        tex_file.unlink()
    if args.open:
        run(f'xdg-open "{output_pdf}"')


if __name__ == "__main__":
    main()
