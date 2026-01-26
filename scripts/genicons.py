#!/usr/bin/env python3
# coding: utf-8
import re
from glob import glob
from itertools import pairwise, product
from os import listdir, makedirs, remove, symlink
from os.path import basename, dirname, exists, isfile, islink, relpath, splitext
from re import findall
from typing import Iterable

from s57 import S57, abbr_color

outpath = "gen"

patterns = (
    None,
    "horizontal",
    "vertical",
    "squared",
    "border",
    "cross",
)  # "saltire"

object_colors = {
    "": None,
    "white": "#ffffff",  # 1
    "black": "#000000",  # 2
    "red": "#ed1c24",  # 3
    "green": "#00a650",  # 4
    "blue": "#10508c",  # 5
    "yellow": "#fab20b",  # 6
    "grey": "#808080",  # 7
    "brown": "#A52A2A",  # 8
    "amber": "#FFBF00",  # 9
    "violet": "#EE82EE",  # 10
    "orange": "#F7A837",  # 11
    "magenta": "#ec008c",  # 12
    "pink": "#FFC0CB",  # 13
}

light_colors = {
    "generic": "#800080",
    "white": "#fab20b",
    "red": "#ed1c24",
    "green": "#00a650",
    "blue": "#10508c",
    "yellow": "#fab20b",
    "orange": "#fa870b",
    "amber": "#FFBF00",  # 9
}

lights = {
    "light",
    "floodlight",
}

color_types = {  # to reduce numer of combinations
    "pillar spar can spherical barrel super-buoy conical light_float": "white black red green yellow",
    "tower lattice pile stake cairn": "white black red green yellow brown grey",
    "sphere": "black white red green",
    "x-shape cross": "black yellow",
    "2_spheres 2_cones_up 2_cones_down 2_cones_base_together 2_cones_point_together": "black red green",
    "cylinder cone_point_down cone_point_up": "black white red green",
    "circle sphere_over_rhombus": "black white red green",
    "triangle_point_up triangle_point_down square rhombus flag": "black white red green yellow grey",
}


def colors_for(s):
    if s in lights:
        return light_colors.keys()

    colors = None
    for types, cols in color_types.items():
        types = types.split()
        cols = [""] + cols.split()
        if s in types:
            return cols

    return object_colors.keys()


def patterns_for(s):
    return patterns


S57data = {
    k: v for k, v in S57.items() if k in "COLOUR COLPAT TOPSHP BOYSHP BCNSHP CATLMK"
}


def s57id(value):
    if not value:
        return
    for n, d in S57data.items():
        if not isinstance(d, dict):
            continue
        for k, v in d.items():
            if v == value:
                # return f'{n}_{k}'
                return k


def read(f):
    with open(f) as f:
        return f.read()


def alt_name(svg):
    m = re.search(r'"([A-Z]{6}_\d+)"', svg)
    if m:
        return m[1].replace("_", "/")


# for f in object_colors.keys():
#   id=s57id(f)
#   if id: print(f,id)
#
# for f in patterns:
#   id=s57id(f)
#   if id: print(f,id)
#
# for f in glob('../icons/*.svg'):
#   print(f,alt_name(read(f)))
#
# xxx


def write(f, c):
    print(f)
    # assert not exists(f), f
    makedirs(dirname(f), exist_ok=True)
    with open(f, "w") as f:
        if isinstance(c, list):
            f.writelines(l + "\n" for l in c)
        else:
            f.write(c)


def link(src, dst):
    makedirs(dirname(dst), exist_ok=1)
    try:
        remove(dst)
    except:
        pass
    symlink(relpath(src, dirname(dst)), dst)


def main():
    for f in glob("*.svg"):
        svg = read(f)
        icon = splitext(f)[0]

        if "COLORING{}" not in svg:
            out = "/".join((outpath, f"{icon}.svg"))
            write(out, svg)
            alt = alt_name(svg)
            if alt:
                alt = "/".join((outpath, alt + ".svg"))
                print(">", alt)
                link(out, alt)
            continue
        # continue

        color_codes = light_colors if icon in lights else object_colors

        for p in patterns_for(icon):
            matches = findall(rf" {p}\d(\d)", svg) if p else 1
            if not matches:
                continue
            sections = {int(m[0]) for m in matches} if p else {1}
            # print(icon, p, sections)

            for s in sections:
                colors = colors_for(icon)

                cols = list(
                    filter(
                        lambda l: len(set(l)) <= 2
                        and all(len(set(p)) == 2 for p in pairwise(l)),
                        product(filter(lambda c: c or s == 1, colors), repeat=s),
                    )
                )

                # print(cols)

                for cs in cols:
                    # print(icon,p,cs)

                    width_out = 0.3
                    width_in = 0.8
                    width_base = 0.5
                    color_out = "black"
                    color_base_out = "black"
                    color_base_fill = "white"

                    svg_lines = svg.splitlines()
                    styles = []
                    for i, c in enumerate(filter(bool, cs)):
                        c = color_codes[c]
                        lines = []
                        for l in svg_lines:
                            if "class" in l and "style" not in l:
                                css_class = f"{p}{i}{s}" if p else "uniform"
                                if css_class in l:
                                    if "fill" in l:
                                        style = f"fill:{c}; stroke:none;"
                                    elif "outline" in l:
                                        style = f"fill:none; stroke:{c}; stroke-width:{width_in};"
                                    elif "inline" in l:
                                        style = f"fill:none; stroke:{c}; stroke-width:{width_in};"
                                    else:
                                        assert 0, (p, i, c, s, l)
                                    l += f' style="{style}"'  # style in element, JOSM does not support global <style/>
                                    styles.append(f".{css_class} {{ {style} }}")
                            lines.append(l)
                        svg_lines = lines

                    lines = []
                    for l in svg_lines:
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
                    svg_lines = lines

                    # svg_lines = svg_lines.replace("COLORING{}", "\n".join(styles))
                    # print(svg_lines)

                    out = (
                        "/".join(
                            filter(
                                bool,
                                (
                                    outpath,
                                    icon,
                                    p,
                                    "_".join([c or "generic" for c in cs]),
                                ),
                            )
                        )
                        + ".svg"
                    )
                    write(out, svg_lines)

                    aname = alt_name(svg)
                    if aname:
                        alt = (
                            "/".join(
                                (
                                    outpath,
                                    aname,
                                    str(s57id(p) or 0),
                                    ",".join(
                                        list(map(lambda i: str(i or 0), map(s57id, cs)))
                                    )
                                    or "0",
                                )
                            )
                            + ".svg"
                        )
                        print(">", alt)
                        link(out, alt)

                        alt = (
                            "/".join(
                                (
                                    outpath,
                                    aname,
                                    str(s57id(p) or 0),
                                    "".join(
                                        list(
                                            map(
                                                lambda i: abbr_color(i) if i else "_",
                                                map(s57id, cs),
                                            )
                                        )
                                    )
                                    or "0",
                                )
                            )
                            + ".svg"
                        )
                        print(">", alt)
                        link(out, alt)

                    if icon in lights:
                        alt = (
                            "/".join(
                                (
                                    outpath,
                                    icon,
                                    str(s57id(cs[0]) if cs[0] != "generic" else 0),
                                )
                            )
                            + ".svg"
                        )
                        print(">", alt)
                        link(out, alt)

                        alt = (
                            "/".join(
                                (
                                    outpath,
                                    icon,
                                    abbr_color(cs[0]) if cs[0] != "generic" else "_",
                                )
                            )
                            + ".svg"
                        )
                        print(">", alt)
                        link(out, alt)


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
