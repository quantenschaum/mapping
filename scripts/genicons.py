#!/usr/bin/env python3
# coding: utf-8

from os import listdir, makedirs
from os.path import isfile, basename, splitext, dirname
from itertools import product
from re import findall
from glob import glob
from s57 import S57

outpath = "gen"

patterns = (None, "vertical", "horizontal", "cross", "saltire", "border", "squared")

object_colors = {
    "": None,
    "white": "#ffffff", # 1
    "black": "#000000", # 2
    "red": "#ed1c24", # 3
    "green": "#00a650", # 4
    "blue": "#10508c", # 5
    "yellow": "#fab20b", # 6
    "grey": "#808080", # 7
    "brown": "#A52A2A", # 8
    "amber": "#FFBF00", # 9
    "violet": "#EE82EE", # 10
    "orange": "#F7A837", # 11
    "magenta": "#ec008c", # 12
    "pink": "#FFC0CB", # 13
}

color_types={ # to reduce numer of combinations
  'pillar spar can spherical barrel super-buoy conical light_float ':
  ['','white','black','red','green','yellow'],

  'tower lattice pile stake cairn ':
  ['','white','black','red','green','yellow','brown','grey'],

  'sphere ':
  ['','red','black'],

  'x-shape cross ':
  ['','yellow'],

  '2_spheres 2_cones_up 2_cones_down 2_cones_base_together 2_cones_point_together ':
  ['','black'],

  'cylinder cone_point_down cone_point_up ':
  ['','black','white','red','green'],

  'circle ':
  ['','black','white','white','red'],

  'triangle_point_up square rhombus triangle_point_down ':
  ['','white','black','red','green','yellow'],
}

def colors_for(s):
  colors=None
  for types,cols in color_types.items():
    if s+' ' in types: colors=cols
  # print(s,colors)
  if not colors: return object_colors
  return {k:v for k,v in object_colors.items() if k in colors}

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

def s57id(value):
  for n,d in S57.items():
    if type(d)!=dict: continue
    for k,v in d.items():
      if v==value:
        return k,n


def read(f):
    with open(f) as f:
        return f.read()


def write(f, c):
    # base,ext=splitext(f)
    # parts=base.split('/')
    # codes=[]
    # for p in parts:
    #   s=s57id(p)
    #   o=f'{s[1]}{s[0]}' if s else p
    #   if '_' in p:
    #     o=','.join(str(s57id(x)[0]) for x in p.split('_'))
    #   codes.append(str(o))
    # f2='/'.join(codes)+ext
    # print(f,f2)
    # f=f2
    assert not isfile(f), f
    makedirs(dirname(f), exist_ok=True)
    with open(f, "w") as f:
        f.write(c)


def main():
    for f in glob('*.svg'):
        svg = read(f)
        s = splitext(f)[0]
        if "COLORING{}" not in svg:
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
                colors = light_colors if s in lights else colors_for(s)
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
