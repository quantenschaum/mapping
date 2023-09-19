#!/usr/bin/env python

from geo.sphere import destination  # https://pypi.org/project/geo-py/
from pyquery import PyQuery as pq
import json, requests, os
from math import ceil
from itertools import chain
from sys import stderr


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


def project(ll, direction_deg, distance_nm):
    d = destination((ll[1], ll[0]), distance_nm * 1852, direction_deg)
    return d[1], d[0]


light_properties = {
    "sector_start": float,
    "sector_end": float,
    "orientation": float,
    "colour": str,
    "character": str,
    "group": str,
    "period": str,
    "sequence": str,
    "height": str,
    "range": lambda s: float(s.split()[0]),
}


def nformat(v):
    return f"{v:.1f}".replace(".0", "")


def light_label(sector):
    l = sector.get("character", "?")

    g = sector.get("group")
    if g:
        l += f"({g})"

    c = sector.get("colour")
    if c:
        s = "" if g else "."
        l += s + "".join(sorted((p[0].upper() for p in c.split(";")), reverse=True))

    p = sector.get("period")
    if p:
        l += f" {p}s"

    h = 0  # sector.get("height")
    if h:
        l += f" {h}m"

    r = sector.get("range")
    if r:
        if isinstance(r, list):
            a, b = min(r), max(r)
            l += f" {nformat(a)}-{nformat(b)}M" if a != b else f" {nformat(a)}M"
        else:
            l += f" {nformat(r)}M"

    return l


def get_sectors(node, full=False):
    sectors = []
    for i in range(0 if full else 1, 21, 1):
        s = {}
        for p, t in light_properties.items():
            x = f"{i}:" if i else ""
            v = get_tag(f"seamark:light:{x}{p}", node, t)
            if v:
                s[p] = v
        if not s and i > 0:
            break
        if s and i == 0:
            s["sector_start"] = 180
            s["sector_end"] = 180
        if "sector_start" in s and "sector_end" in s or "orientation" in s:
            sectors.append(s)
    return sectors


def generate_sectors(infile, outfile="lightsectors.osm", config={}):
    print("reading", infile)
    osm = pq(filename=infile)
    out = pq('<osm version="0.6"/>')

    full = config.get("full", False)
    major = config.get("major", ["light_major", "landmark"])
    minor = config.get("minor", ["light_minor"])
    types = major + minor
    min_range = config.get("min_range", 8)
    max_range = config.get("max_range", 8)
    f_range = config.get("f_range", 0.6)
    f_arc = config.get("f_arc", 0.2)

    N = len(osm("node")) + len(osm("way"))

    for i, n in enumerate(chain(osm("node"), osm("way")), 1):
        n = pq(n)

        smtype = get_tag("seamark:type", n)
        name = get_tag("seamark:name", n) or get_tag("name", n)

        if smtype in types:
            sectors = get_sectors(n, full)

            if sectors and (
                smtype in major or any(s.get("range", 0) >= min_range for s in sectors)
            ):
                print(
                    f"{i}/{N}", smtype, f"'{name}'", [light_label(s) for s in sectors]
                )
                ll = get_ll(n, osm)
                # print(n)
                # print(json.dumps(sectors, indent=2))
                lines = {}
                ss = {}
                for s in sectors:
                    r = min(s.get("range", 3) * f_range, max_range)
                    ori, start, end = [
                        s.get(k) for k in ("orientation", "sector_start", "sector_end")
                    ]

                    ## merged characteristics
                    for k in light_properties.keys():
                        v = s.get(k)
                        if v:
                            if k == "colour" and k in ss:
                                if v not in ss[k]:
                                    ss[k] += ";" + v
                            elif k == "range":
                                ss[k] = ss.get(k, []) + [v]
                            elif k in ss:
                                if v != ss[k]:
                                    ss[k] = "?"
                            else:
                                ss[k] = v

                    # leading line
                    if ori is not None:
                        lines[ori] = {
                            "range": r,
                            "name": f"{nformat(ori)}° {light_label(s)}",
                            "sector": "orientation",
                        }

                    # sector limits
                    for d0, d1 in (start, end), (end, start):
                        if (
                            d0 is not None
                            and d0 != d1
                            and lines.get(d0, {}).get("range", 0) < r
                        ):
                            lines[d0] = {
                                "range": r,
                                "name": f"{nformat(d0)}°",
                                "sector": "limit",
                            }

                    # sector arc
                    ab = [start, end]
                    if all(ab):
                        if ab[0] >= ab[1]:
                            ab[1] += 360
                        points = [
                            new_node(*project(ll, d + 180, r * f_arc))
                            for d in linspace(*ab, ceil(abs(ab[1] - ab[0]) / 5))
                        ]
                        w = new_way(points)
                        set_tag("lightsector", "arc", w)
                        set_tag("name", light_label(s), w)
                        set_tag("colour", s.get("colour"), w)
                        for m in points + [w]:
                            out.append(m)

                if lines:
                    a = new_node(*ll)
                    set_tag(
                        "seamark:type",
                        major[0] if smtype in major else minor[0],
                        a,
                    )
                    n = name + " " if name else ""
                    set_tag(
                        "seamark:name",
                        n + light_label(ss),
                        a,
                    )
                    out.append(a)

                    for d, l in lines.items():
                        b = new_node(*project(ll, d + 180, l["range"]))
                        w = new_way((a, b))
                        set_tag("lightsector", l["sector"], w)
                        set_tag("name", l["name"], w)
                        for m in b, w:
                            out.append(m)

    print("writing", outfile)
    with open(outfile, "w") as f:
        f.write(str(out))


def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    from types import MethodType

    parser = ArgumentParser(
        prog="light sector generator",
        description="generate light sector limits and arcs from OSM xml",
        epilog="https://github.com/quantenschaum/mapping/",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "infile",
        help="OSM XML file to read",
        metavar="in-osm",
        default="in.osm",
        nargs="?",
    )
    parser.add_argument(
        "outfile",
        help="OSM XML file to write",
        metavar="out-osm",
        default="lightsectors.osm",
        nargs="?",
    )
    parser.add_argument(
        "-j",
        "--josm",
        help="open output file in JOSM (remote control)",
        action="store_true",
    )
    parser.add_argument(
        "-M",
        "--major",
        help="seamark:type for major lights",
        type=lambda s: s.split(","),
        default="light_major,landmark",
    )
    parser.add_argument(
        "-m",
        "--minor",
        help="seamark:type for minor lights",
        type=lambda s: s.split(","),
        default="light_minor",
    )
    parser.add_argument(
        "-r",
        "--min-range",
        help="min. range a minor light must have for sectors to be generated",
        type=float,
        default=8,
    )
    parser.add_argument(
        "-R",
        "--max-range",
        help="max. range used for generating sectors",
        type=float,
        default=8,
    )
    parser.add_argument(
        "-f",
        "--f-range",
        help="factor to scale range limit lines",
        type=float,
        default=0.6,
    )
    parser.add_argument(
        "-a",
        "--f-arc",
        help="factor to scale radius of arcs",
        type=float,
        default=0.2,
    )
    parser.add_argument(
        "-o", "--full", help="generate arcs for 360° sectors", action="store_true"
    )

    args = parser.parse_args()
    args.get = MethodType(lambda s, k, d=None: getattr(s, k) or d, args)

    generate_sectors(args.infile, args.outfile, args)

    if args.josm:
        requests.get(
            f"http://localhost:8111/open_file?filename={os.path.abspath(args.outfile)}"
        )


if __name__ == "__main__":
    main()
