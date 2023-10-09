#!/usr/bin/env python
# coding: utf-8

from os import listdir, makedirs
from os.path import isfile, basename, splitext, dirname
from itertools import product

patterns = (None, "vertical", "horizontal")
sections = {"vertical": (2,), "horizontal": (2, 3, 4)}
colors = (None, "white", "black", "red", "green", "blue", "yellow", "grey", "orange")
# colors = (None, "red", "white")


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
        for p in patterns:
            secs = sections[p] if p else (1,)
            for n in secs:
                cols = tuple(
                    product(*([tuple(filter(lambda c: c or n == 1, colors))] * n))
                )
                for cs in cols:
                    if len(cs) > 1:
                        if len(set(cs)) > 2:
                            continue  # >2 colors
                        discard = 0
                        for i, c in enumerate(cs[:-1]):
                            print(i, c, cs[i + 1], c == cs[i + 1])
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
                    print(out)
                    style = ""
                    for i, c in enumerate(filter(bool, cs)):
                        if p:
                            style += f".fill.{p[0]}{i}{n} {{ fill: {c}; }}\n"
                        else:
                            style += f".fill {{ fill: {c}; }}\n"
                    print(style)
                    makedirs(dirname(out), exist_ok=True)
                    write(out, svg.replace("FILL{}", style))


main()
