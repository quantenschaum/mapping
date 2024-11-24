#!/usr/bin/env python3

import os
from itertools import chain
from math import ceil
from math import radians, degrees, sin, cos, tan, asin, atan2, atan, exp, log, pi
from sys import stderr

import requests
from pyquery import PyQuery as pq

from s57 import *


def linspace(start, stop, num=10):
    delta = (stop - start) / num
    points = [(start + i * delta) if i < num else stop for i in range(num + 1)]
    return points


def get_tag(key, node, type=lambda v: v):
    v = node.find(f"tag[k='{key}']").attr("v")
    try:
        return type(v) if v else None
    except:
        print("error getting", key, node, file=stderr)
        return None


def set_tag(key, value, node):
    tag = node.find(f"tag[k='{key}']")
    tag.remove()
    pq(f'<tag k="{key}" v="{value}" />').append_to(node)


def get_ll(node, osm=None):
    if not node.attr("lat"):
        ll = [], []
        for r in node.find("nd[ref]"):
            r = pq(r)
            r = r.attr("ref")
            r = osm(f"node[id='{r}']")
            r = get_ll(r, osm)
            for i in range(2):
                ll[i].append(r[i])
        ll = [sum(e) / len(e) for e in ll]
        return ll
    return float(node.attr("lat")), float(node.attr("lon"))


def set_ll(lat, lon, node):
    node.attr("lat", lat)
    node.attr("lon", lon)


ID = 0


def next_id():
    global ID
    ID -= 1
    return ID


def new_node(lat="nan", lon="nan", id=None):
    id = id or next_id()
    return pq(f'<node id="{id}" visible="true" lat="{lat}" lon="{lon}"/>')


def new_way(nodes, id=None):
    id = id or next_id()
    w = pq(f'<way id="{id}" visible="true')
    for n in nodes:
        try:
            n = n.attr("id")
        except:
            pass
        pq(f'<nd ref="{n}"/>').append_to(w)
    return w


R = 6378137.0


def ll2grid(point):
    lat, lon = point
    x = radians(lon) * R
    y = log(tan(pi / 4 + radians(lat) / 2)) * R
    return x, y


def grid2ll(xy):
    x, y = xy
    lat = degrees(2 * atan(exp(y / R)) - pi / 2.0)
    lon = degrees(x / R)
    return lat, lon


def project(point, bearing, distance):
    "https://wiki.openstreetmap.org/wiki/Mercator"
    x, y = ll2grid(point)
    bearing = radians(bearing)
    distance *= 1852
    x += sin(bearing) * distance
    y += cos(bearing) * distance
    return grid2ll((x, y))


def project_gc(point, bearing, distance):
    "great circle projection"
    lat1, lon1 = (radians(a) for a in point)
    bearing = radians(bearing)
    distance *= 1852  # to meters
    distance /= 6371008.8  # m

    lat2 = asin(sin(lat1) * cos(distance) + cos(lat1) * sin(distance) * cos(bearing))
    y = sin(bearing) * sin(distance) * cos(lat1)
    x = cos(distance) - sin(lat1) * sin(lat2)

    lon2 = lon1 + atan2(y, x)

    return degrees(lat2), (degrees(lon2) + 540) % 360 - 180


light_properties = {
    "sector_start": float,
    "sector_end": float,
    "orientation": float,
    "colour": str,
    "character": str,
    "category": str,
    "status": str,
    "visibility": str,
    "exhibition": str,
    "group": str,
    "period": str,
    "sequence": str,
    "height": lambda s: float(s.split()[0].replace("m", "")),
    "range": lambda s: float(s.split()[0]),
}


def nformat(v):
    return f"{v:.1f}".replace(".0", "")


def label(sector, height_range=False, sep="\u00A0"):
    l = ""
    c = sector.get("character")
    if c and c != "?":
        l += c

    g = sector.get("group")
    if l and g and g != "?":
        l += f"({g})"

    c = sector.get("colour")
    if c and c != "?":
        s = "" if not l or l[-1] == ")" else sep
        l += s + "".join(sorted((p[0].upper() for p in c.split(";")), reverse=True))

    p = sector.get("period")
    if p and p != "?":
        l += f"{sep}{p}s"

    if height_range:
        h = sector.get("height")
        if h:
            if isinstance(h, list):
                a, b = min(h), max(h)
                l += (
                    f"{sep}{nformat(a)}-{nformat(b)}m"
                    if a != b
                    else f"{sep}{nformat(a)}m"
                )
            else:
                l += f"{sep}{nformat(h)}m"

        r = sector.get("range")
        if r:
            if isinstance(r, list):
                a, b = min(r), max(r)
                l += (
                    f"{sep}{nformat(a)}-{nformat(b)}M"
                    if a != b
                    else f"{sep}{nformat(a)}M"
                )
            else:
                l += f"{sep}{nformat(r)}M"

    m = []
    for p in "status", "visibility", "exhibition":
        s = sector.get(p)
        if s:
            m = m + abbrev(s)
    if m:
        l += sep + "(" + ",".join(m) + ")"

    return l.replace(";", "/")


def abbrev(s):
    return [abbrevs[p] for p in s.split(";") if p in abbrevs]


SSO = "sector_start", "sector_end", "orientation"


def get_sectors(node):
    sectors = []
    for i in range(50):
        s = {}
        for p, t in light_properties.items():
            x = f"{i}:" if i else ""
            v = get_tag(f"seamark:light:{x}{p}", node, t)
            if v is not None:
                s[p] = v
        if not s and i > 0:
            break
        cat = s.get("category")
        if cat and not set(cat.split(";")).intersection(nav_light_categories):
            continue
        if s and all(x not in s for x in SSO):
            s["sector_start"] = 0
            s["sector_end"] = 360
        if s and any(x in s for x in SSO):
            sectors.append(s)

    return sectors


def merge(sectors):
    merged = {}
    for s in sectors:
        for k, v in s.items():
            if k in ("range", "height"):
                merged[k] = merged.get(k, []) + [v]
            elif k in merged:
                merged[k] = ";".join(set(merged[k].split(";") + str(v).split(";")))
            elif k in merged:
                if v != merged[k]:
                    merged[k] = "?"
            else:
                merged[k] = str(v)
    return merged


def colors(sectors):
    cols = set()
    for s in sectors:
        c = s.get("colour")
        if c:
            for p in c.split(";"):
                cols.add(p)
    return ";".join(sorted(cols, reverse=True))


config_defaults = {
    "major": ["light_major"],
    "min_range": 5,
    "max_range": 12,
    "f_range": 0.8,
    "f_arc": 0.2,
    "full": 19,
    "range0": 0,
    "leading": False,
    "sector_data": False,
}


def generate_sectors(infile, outfile, config={}):
    print("reading", infile)
    osm = pq(filename=infile)
    out = pq('<osm version="0.6"/>')

    update_nc(config, config_defaults)
    major = config["major"]
    min_range = config["min_range"]
    max_range = config["max_range"]
    full_range = config["full"]
    f_range = config["f_range"]
    f_arc = config["f_arc"]
    range0 = config["range0"]
    leading = config["leading"]
    add_sector_data = config["sector_data"]

    osm_objects = list(chain(osm("node"), osm("way")))
    N = len(osm_objects)

    for i, n in enumerate(osm_objects, 1):
        n = pq(n)

        seamark_type = get_tag("seamark:type", n)
        sectors = get_sectors(n)

        if (
            not sectors or seamark_type not in major
            and not any(s.get("range", range0) >= min_range for s in sectors)
        ):
            continue

        name = get_tag("seamark:name", n) or get_tag("name", n)
        lnam = get_tag("seamark:lnam", n)

        gsectors = group_by(
            sectors,
            lambda s: "-".join(s.get(p, "?") for p in ("character", "group", "period")),
        )

        merged_label = " ".join(label(merge(s), True) for s in gsectors.values())
        print(
            f"{i}/{N}",
            seamark_type,
            name,
            merged_label.replace(" ", " + ").replace("\u00A0", " "),
        )
        ll = get_ll(n, osm)

        center = new_node(*ll)
        t = "light_major" if seamark_type in major else "light_minor"
        set_tag("lightsector", "source", center)
        set_tag("seamark:type", t, center)
        if name:
            set_tag("seamark:name", name, center)
        if lnam:
            set_tag("seamark:lnam", lnam, center)
        set_tag("seamark:light:character", merged_label, center)
        set_tag("seamark:light:colour", colors(sectors), center)

        if add_sector_data:
            for i,s in enumerate(sectors,0 if len(sectors)==1 else 1):
                for k,v in s.items():
                    # print(f"seamark:light:{i}:{k}","=",v)
                    set_tag(f"seamark:light:{i}:{k}", v, center)


        out.append(center)

        lines = {}
        for s in sectors:
            r0 = s.get("range", max(min_range, range0))  # nominal range
            r1 = min(r0 * f_range, max_range)  # rendered range
            a, b, o = [s.get(k) for k in SSO]
            is_ori = o is not None
            is_sector = a is not None and b is not None
            is_full = is_sector and a % 360 == b % 360
            is_leading = len(sectors) == 1 and any(
                k in s.get("category", "") for k in leading_lights
            )
            is_low = any(k in str(s) for k in low_light if k!="low")

            # directional line
            if r1 and is_ori:
                lines[o] = {
                    "lightsector": "orientation",
                    "orientation": o,
                    "range": r1,
                    "name": f"{nformat(o)}° {label(s)}",
                    "colour": s.get("colour"),
                }

            if is_leading and not leading:
                continue

            # sector limits
            if r1 and is_sector and not is_full:
                for d in a, b:
                    l0 = lines.get(d, {})
                    if (
                        l0.get("range", 0) < r1
                        and l0.get("lightsector") != "orientation"
                    ):
                        lines[d] = {
                            "lightsector": "limit",
                            "orientation": d,
                            "range": r1,
                            "name": f"{nformat(d)}°",
                        }

            # sector arc
            if r1 and is_sector and (not is_full or r0 >= full_range):
                if a >= b:
                    b += 360
                m = max(3, ceil(abs(b - a) / 5))
                points = [
                    new_node(*project(ll, d + 180, r1 * f_arc))
                    for d in linspace(a, b, m)
                ]
                w = new_way(points)
                set_tag("lightsector", "arc", w)
                set_tag("colour", s.get("colour"), w)
                set_tag("name", label(s), w)
                if is_low:
                    set_tag("lightsector:low", "yes", w)
                for m in points + [w]:
                    out.append(m)

        if lines:
            for d, l in lines.items():
                b = new_node(*project(ll, d + 180, l["range"]))
                w = new_way((center, b))
                for k, v in l.items():
                    set_tag(k, v, w)
                for m in b, w:
                    out.append(m)

    print("writing", outfile)
    with open(outfile, "w") as f:
        f.write(str(out))


def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(
        prog="light sector generator",
        description="generate light sector limits and arcs from OSM data",
        epilog="https://github.com/quantenschaum/mapping/",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "infile",
        help="OSM XML file to read",
        metavar="in.osm",
    )
    parser.add_argument(
        "outfile",
        help="OSM XML file to write",
        default="lights.osm",
        metavar="lights.osm",
        nargs="?",
    )
    parser.add_argument(
        "-j",
        "--josm",
        help="open output file in JOSM (via remote control)",
        action="store_true",
    )
    parser.add_argument(
        "-M",
        "--major",
        help="seamark:type(s) for major lights (comma separated list, major lights are always included, even if range<min_range)",
        type=lambda s: s.split(","),
        default=config_defaults["major"],
    )
    parser.add_argument(
        "-r",
        "--min-range",
        help="min. range non-major light must have to be included",
        type=float,
        default=config_defaults["min_range"],
    )
    parser.add_argument(
        "-R",
        "--max-range",
        help="max. range used for generating sectors",
        type=float,
        default=config_defaults["max_range"],
    )
    parser.add_argument(
        "-f",
        "--f-range",
        help="factor to scale range limit lines",
        type=float,
        default=config_defaults["f_range"],
    )
    parser.add_argument(
        "-a",
        "--f-arc",
        help="factor to scale radius of arcs",
        type=float,
        default=config_defaults["f_arc"],
    )
    parser.add_argument(
        "-o",
        "--full",
        help="generate arcs for 360° sectors if range >= this value",
        type=float,
        default=config_defaults["full"],
    )
    parser.add_argument(
        "--range0",
        help="default range to assume if no range is given in the input dataset",
        type=float,
        default=config_defaults["range0"],
    )
    parser.add_argument(
        "-l",
        "--leading",
        help="generate arcs and limits for single sector leading lights",
        action="store_true",
    )
    parser.add_argument(
        "-s",
        "--sector-data",
        help="add sector data to center node",
        action="store_true",
    )

    args = parser.parse_args()

    infile = args.infile
    outfile = args.outfile
    config = {k: getattr(args, k) for k in config_defaults.keys()}

    generate_sectors(infile, outfile, config)

    if args.josm:
        requests.get(
            f"http://localhost:8111/open_file?filename={os.path.abspath(outfile)}"
        )


if __name__ == "__main__":
    main()
