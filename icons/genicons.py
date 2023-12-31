#!/usr/bin/env python
# coding: utf-8

from os import listdir, makedirs
from os.path import isfile, basename, splitext, dirname
from itertools import product
from re import findall

patterns = (None, "vertical", "horizontal", "cross", "saltire", "border", "squared")
object_colors = {
    "": None,
    "white": "white",
    "black": "black",
    "red": "#C72C14",
    "green": "#5BCE3E",
    "blue": "#002EF5",
    "yellow": "#FCD345",
    "grey": "#808080",
    # "brown":"brown",
    # "amber":"amber",
    "violet": "violet",
    "orange": "#F7A837",
    # "magenta":"#DE44E8",
    # "pink":"pink",
}
lights = {
    "light",
    "floodlight",
}
light_colors = {
    "generic": "#800080",
    "white": "yellow",
    "red": "red",
    "green": "green",
    "blue": "blue",
    "yellow": "yellow",
    "orange": "orange",
}


outpath = "gen"


def read(f):
    with open(f) as f:
        return f.read()


def write(f, c):
    with open(f, "w") as f:
        f.write(c)


def main():
    for f in list(filter(lambda f: isfile(f) and f.endswith(".svg"), listdir("."))):
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
                        lines.append(l)
                    svgout = "\n".join(lines)

                    # svgout = svgout.replace("COLORING{}", "\n".join(styles))
                    # print(svgout)

                    makedirs(dirname(out), exist_ok=True)
                    write(out, svgout)


main()
