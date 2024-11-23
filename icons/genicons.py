#!/usr/bin/env python3
# coding: utf-8

from os import listdir, makedirs
from os.path import isfile, basename, splitext, dirname
from itertools import product
from re import findall
from glob import glob

patterns = (None, "vertical", "horizontal", "cross", "saltire", "border", "squared")

object_colors = {
    "": None,
    "white": "#ffffff",
    "black": "#000000",
    "red": "#ed1c24",
    "green": "#00a650",
    "blue": "#10508c",
    "yellow": "#fab20b",
    "grey": "#808080",
    "brown": "#A52A2A",
    "amber": "#FFBF00",
    "violet": "#EE82EE",
    "orange": "#F7A837",
    "magenta": "#ec008c",  # ec008c DE44E8
    "pink": "#FFC0CB",
}

lights = {
    "light",
    "floodlight",
}

light_colors = {
    "generic": "#800080",
    "white": "#fab20b",
    "red": "#ed1c24",
    "green": "#00a650",
    "blue": "#10508c",
    "yellow": "#fab20b",
    "orange": "#fa870b",
}


outpath = "gen"


def read(f):
    with open(f) as f:
        return f.read()


def write(f, c):
    with open(f, "w") as f:
        f.write(c)


def main():
    for f in glob('*.svg'):
        svg = read(f)
        s = splitext(f)[0]
        if "COLORING{}" not in svg:
            makedirs(outpath, exist_ok=True)
            write("/".join((outpath, f"{s}.svg")), svg)
            continue
        # print(s)
        for p in patterns:
            # print(s, p)
            matches = findall(rf" {p}\d(\d)", svg) if p else 1
            if not matches:
                # print("SKIPPED", s, p)
                continue
            secs = {int(m[0]) for m in matches} if p else {1}
            print(s, p, secs)
            for n in secs:
                colors = light_colors if s in lights else object_colors
                cols = tuple(
                    product(
                        *([tuple(filter(lambda c: c or n == 1, colors.keys()))] * n)
                    )
                )
                for cs in cols:
                    if len(cs) > 1:
                        if len(set(cs)) > 2:
                            continue  # >2 colors
                        discard = 0
                        for i, c in enumerate(cs[:-1]):
                            if c == cs[i + 1]:
                                discard = 1  # same adjacent colors
                        if discard:
                            continue

                    out = (
                        "/".join(
                            filter(
                                bool,
                                (outpath, s, p, "_".join([c or "generic" for c in cs])),
                            )
                        )
                        + ".svg"
                    )
                    # print(out)

                    width_out = 0.3
                    width_in = 0.8
                    width_base = 0.5
                    color_out = "black"
                    color_base_out = "black"
                    color_base_fill = "white"

                    svgout = svg
                    styles = []
                    for i, c in enumerate(filter(bool, cs)):
                        c = colors[c]
                        lines = []
                        for l in svgout.splitlines():
                            if "class" in l and "style" not in l:
                                css_class = f"{p}{i}{n}" if p else "uniform"
                                if css_class in l:
                                    if "fill" in l:
                                        style = f"fill:{c}; stroke:none;"
                                    elif "outline" in l:
                                        style = f"fill:none; stroke:{c}; stroke-width:{width_in};"
                                    elif "inline" in l:
                                        style = f"fill:none; stroke:{c}; stroke-width:{width_in};"
                                    else:
                                        assert 0, (p, i, c, n, l)
                                    l += f' style="{style}"'  # style in element, JOSM does not support global <style/>
                                    styles.append(f".{css_class} {{ {style} }}")
                            lines.append(l)
                        svgout = "\n".join(lines)

                    lines = []
                    for l in svgout.splitlines():
                        if "class" in l and "style" not in l:
                            if "fill" in l:
                                style = f"fill:none; stroke:none;"
                            elif "outline" in l:
                                style = f"fill:none; stroke:{color_out}; stroke-width:{width_out};"
                            elif "inline" in l:
                                style = f"fill:none; stroke:none;"
                            elif "baseline" in l:
                                style = f"fill:none; stroke:{color_base_out}; stroke-width:{width_base};"
                            elif "basepoint" in l:
                                style = f"fill:{color_base_fill}; stroke:{color_base_out}; stroke-width:{width_base};"
                            l += f' style="{style}"'
                            # l += f' style="{style}" {param(l) if not cs[0] else ""}'
                        lines.append(l)
                    svgout = "\n".join(lines)

                    # svgout = svgout.replace("COLORING{}", "\n".join(styles))
                    # print(svgout)

                    makedirs(dirname(out), exist_ok=True)
                    write(out, svgout)


def param(line):
    p = None
    if "uniform" in line:
        p = "base"
    for a, b in product(("horizontal", "vertical"), ("12", "13", "23")):
        # print(a, b, a[0] + b)
        if a + b in line:
            p = a[0] + b
            break
    return f'\n  fill="param({p})"' if p else ""


main()
