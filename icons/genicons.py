#!/usr/bin/env python
# coding: utf-8

from os import listdir, makedirs
from os.path import isfile, basename, splitext, dirname
from itertools import product
from re import findall, sub

patterns = (None, "vertical", "horizontal", "cross", "border")
colors = {
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
    # "violet":"violet",
    "orange": "#F7A837",
    # "magenta":"#DE44E8",
    # "pink":"pink",
}


def read(f):
    with open(f) as f:
        return f.read()


def write(f, c):
    with open(f, "w") as f:
        f.write(c)


def main():
    for f in list(filter(lambda f: isfile(f) and f.endswith(".svg"), listdir("."))):
        svg = read(f)
        if "COLORING{}" not in svg:
            continue
        s = splitext(f)[0]
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
                                ("gen", s, p, "_".join([c or "generic" for c in cs])),
                            )
                        )
                        + ".svg"
                    )
                    # print(out)
                    style = ""
                    for i, c in enumerate(filter(bool, cs)):
                        c = colors[c]
                        fill = "fill"
                        if s == "stake" or s == "barrel" and i == 1 and p == "cross":
                            fill = "stroke"
                        if p:
                            style += f".fill.{p}{i}{n} {{ {fill}: {c}; }}\n"
                        else:
                            style += f".fill {{ {fill}: {c}; }}\n"
                    # print(style)
                    # svgout = svg.replace("COLORING{}", style)

                    svgout = svg
                    for i, c in enumerate(filter(bool, cs)):
                        c = colors[c]
                        lines = []
                        for l in svgout.splitlines():
                            if "class" in l and "style" not in l:
                                if (f"{p}{i}{n}" if p else "uniform") in l:
                                    if "fill" in l and "outline" in l:
                                        l += f' style="fill:{c};stroke:black;stroke-width:0.5;"'
                                    elif "fill" in l:
                                        l += f' style="fill:{c};stroke:none;"'
                                    elif "outline" in l or "inline" in l:
                                        l += f' style="fill:none;stroke:{c};stroke-width:0.7;"'
                            lines.append(l)
                        svgout = "\n".join(lines)

                    lines = []
                    for l in svgout.splitlines():
                        if "class" in l and "style" not in l:
                            if "fill" in l and "outline" in l:
                                l += (
                                    f' style="fill:none;stroke:black;stroke-width:0.5;"'
                                )
                            elif "fill" in l:
                                l += f' style="fill:none;stroke:none;"'
                            elif "outline" in l:
                                l += (
                                    f' style="fill:none;stroke:black;stroke-width:0.5;"'
                                )
                            elif "inline" in l:
                                l += f' style="fill:none;stroke:none;stroke-width:0.5;"'
                            elif "base" in l:
                                l += f' style="fill:white;stroke:black;stroke-width:0.5;"'
                        lines.append(l)
                    svgout = "\n".join(lines)
                    # print(svgout)

                    makedirs(dirname(out), exist_ok=True)
                    write(out, svgout)


main()
