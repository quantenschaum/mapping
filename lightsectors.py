#!/usr/bin/env python

from pyquery import PyQuery as pq
import requests, os
from math import ceil
from itertools import chain
from sys import stderr
from math import radians, degrees, sin, cos, tan, asin, atan2, atan, exp, log, pi


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
    "group": str,
    "period": str,
    "sequence": str,
    "height": lambda s: float(s.split()[0].replace("m", "")),
    "range": lambda s: float(s.split()[0]),
}


def nformat(v):
    return f"{v:.1f}".replace(".0", "")


def light_label(sector, extended=False, sep="\u00A0"):
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

    if not extended:
        return l

    h = sector.get("height")
    if h:
        if isinstance(h, list):
            a, b = min(h), max(h)
            l += f"{sep}{nformat(a)}-{nformat(b)}m" if a != b else f"{sep}{nformat(a)}m"
        else:
            l += f"{sep}{nformat(h)}m"

    r = sector.get("range")
    if r:
        if isinstance(r, list):
            a, b = min(r), max(r)
            l += f"{sep}{nformat(a)}-{nformat(b)}M" if a != b else f"{sep}{nformat(a)}M"
        else:
            l += f"{sep}{nformat(r)}M"

    return l


SSO = "sector_start", "sector_end", "orientation"


def get_sectors(node):
    sectors = []
    for i in range(0, 21, 1):
        s = {}
        for p, t in light_properties.items():
            x = f"{i}:" if i else ""
            v = get_tag(f"seamark:light:{x}{p}", node, t)
            if v is not None:
                s[p] = v
        if not s and i > 0:
            break
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
            if k == "colour" and k in merged:
                if v not in merged[k]:
                    merged[k] += ";" + v
            elif k in ("range", "height"):
                merged[k] = merged.get(k, []) + [v]
            elif k in merged:
                if v != merged[k]:
                    merged[k] = "?"
            else:
                merged[k] = v
    return merged


def colors(sectors):
    cols = set()
    for s in sectors:
        c = s.get("colour")
        if c:
            cols.add(c)
    return ";".join(sorted(cols, reverse=True))


def generate_sectors(infile, outfile, config={}):
    print("reading", infile)
    osm = pq(filename=infile)
    out = pq('<osm version="0.6"/>')

    major = config.get("major", ["light_major", "landmark"])
    min_range = config.get("min_range", 5)
    max_range = config.get("max_range", 10)
    full_range = config.get("full", 999)
    f_range = config.get("f_range", 0.6)
    f_arc = config.get("f_arc", 0.2)

    osm_objects = list(chain(osm("node"), osm("way")))
    N = len(osm_objects)

    for i, n in enumerate(osm_objects, 1):
        n = pq(n)

        seamark_type = get_tag("seamark:type", n)
        sectors = get_sectors(n)

        if (
            not sectors
            or seamark_type not in major
            and not any(s.get("range", 0) >= min_range for s in sectors)
        ):
            continue

        name = get_tag("seamark:name", n) or get_tag("name", n)
        merged_label = light_label(merge(sectors), True)

        print(f"{i}/{N}", seamark_type, name, merged_label.replace("\u00A0", " "))
        ll = get_ll(n, osm)

        center = new_node(*ll)
        t = "light_major" if seamark_type in major else "light_minor"
        set_tag("lightsector", "source", center)
        set_tag("seamark:type", t, center)
        if name:
            set_tag("seamark:name", name, center)
        set_tag("seamark:light:character", merged_label, center)
        set_tag("seamark:light:colour", colors(sectors), center)
        out.append(center)

        lines = {}
        for s in sectors:
            r0 = s.get("range", min_range)  # nominal range
            r1 = min(r0 * f_range, max_range)  # rendered range
            a, b, o = [s.get(k) for k in SSO]
            is_ori = o is not None
            is_sector = a is not None and b is not None
            is_full = is_sector and a % 360 == b % 360

            # leading line
            if is_ori:
                lines[o] = {
                    "range": r1,
                    "name": f"{nformat(o)}° {light_label(s)}",
                    "sector": "orientation",
                }

            # sector limits
            if is_sector and not is_full:
                for d in a, b:
                    if lines.get(d, {}).get("range", 0) < r1:
                        lines[d] = {
                            "range": r1,
                            "name": f"{nformat(d)}°",
                            "sector": "limit",
                        }

            # sector arc
            if is_sector and (not is_full or r0 >= full_range):
                if a >= b:
                    b += 360
                m = max(3, ceil(abs(b - a) / 5))
                points = [
                    new_node(*project(ll, d + 180, r1 * f_arc))
                    for d in linspace(a, b, m)
                ]
                w = new_way(points)
                set_tag("lightsector", "arc", w)
                set_tag("name", light_label(s), w)
                set_tag("colour", s.get("colour"), w)
                for m in points + [w]:
                    out.append(m)

        if lines:
            for d, l in lines.items():
                b = new_node(*project(ll, d + 180, l["range"]))
                w = new_way((center, b))
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
        description="generate light sector limits and arcs from OSM data",
        epilog="https://github.com/quantenschaum/mapping/",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "infile",
        help="OSM XML file to read",
        default="lights.osm",
        nargs="?",
    )
    parser.add_argument(
        "outfile",
        help="OSM XML file to write",
        default="lightsectors.osm",
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
        help="seamark:type for major lights (comma separated list, major lights are always included, even if range<min_range)",
        type=lambda s: s.split(","),
        default="light_major,landmark",
    )
    parser.add_argument(
        "-r",
        "--min-range",
        help="min. range non-major light must have to be included",
        type=float,
        default=5,
    )
    parser.add_argument(
        "-R",
        "--max-range",
        help="max. range used for generating sectors",
        type=float,
        default=10,
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
        "-o",
        "--full",
        help="generate arcs for 360° sectors if range >= this value",
        type=float,
        default=15,
    )

    args = parser.parse_args()
    args.get = MethodType(
        lambda s, k, d=None: d if getattr(s, k) is None else getattr(s, k), args
    )

    generate_sectors(args.infile, args.outfile, args)

    if args.josm:
        requests.get(
            f"http://localhost:8111/open_file?filename={os.path.abspath(args.outfile)}"
        )


if __name__ == "__main__":
    main()
