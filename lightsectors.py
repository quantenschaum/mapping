from geo.sphere import destination
from pyquery import PyQuery as pq
import json, requests, os
from math import ceil
from itertools import chain


def linspace(start, stop, num=10):
    delta = (stop - start) / num
    points = [(start + i * delta) if i < num else stop for i in range(num + 1)]
    return points


def get_tag(key, node, type=lambda v: v):
    v = node.find(f"tag[k='{key}']").attr("v")
    try:
        return type(v) if v else None
    except:
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


def label(sector):
    l = ""

    v = sector.get("character")
    if v:
        l = l + v

    v = sector.get("group")
    if v:
        l = l + f"({v})"

    v = sector.get("colour")
    if v:
        l = l + f".{v[0].upper()}"

    v = sector.get("period")
    if v:
        l = l + f" {v}s"

    v = 0  # sector.get("height")
    if v:
        l = l + f" {v}m"

    v = sector.get("range")
    if v:
        l = l + f" {v}M"

    return l


def get_sectors(node):
    sectors = []
    for i in range(0 if full360 else 1, 21, 1):
        s = {}
        for p, t in light_properties.items():
            x = f"{i}:" if i else ""
            v = get_tag(f"seamark:light:{x}{p}", node, t)
            if v:
                s[p] = v
        if not s and i > 0:
            break
        if s and i == 0 and s.get("range", 0) > 0:
            s["sector_start"] = 180
            s["sector_end"] = 180
        if "sector_start" in s and "sector_end" in s or "orientation" in s:
            sectors.append(s)
    return sectors


full360 = 1
min_range = 8
types_major = ["landmark", "light_major"]
types_minor = ["light_minor"]
types = types_major + types_minor

max_range = 8
f_range = 0.6
f_arc = 0.2


def generate_sectors(infile, outfile="lightsectors.osm"):
    osm = pq(filename=infile)
    out = pq('<osm version="0.6"/>')

    for n in chain(osm("node"), osm("way")):
        n = pq(n)

        smtype = get_tag("seamark:type", n)
        name = get_tag("seamark:name", n) or get_tag("name", n)

        if smtype in types:
            # print(n)
            sectors = get_sectors(n)

            if sectors and (
                smtype in types_major
                or any(s.get("range", 0) >= min_range for s in sectors)
            ):
                print(smtype, name, [label(s) for s in sectors])
                ll = get_ll(n, osm)
                # print(n)
                # print(json.dumps(sectors, indent=2))
                for s in sectors:
                    r = min(s.get("range", 3) * f_range, max_range)

                    # sector start/end
                    if s.get("sector_start", 0) != s.get("sector_end", 1):
                        for k in "orientation", "sector_start", "sector_end":
                            if k in s:
                                d = s[k]
                                a = new_node(*ll)
                                b = new_node(*project(ll, d + 180, r))
                                w = new_way((a, b))
                                set_tag("lightsector", k.replace("sector_", ""), w)
                                set_tag(
                                    "name",
                                    f"{d}°"
                                    + (" " + label(s) if k == "orientation" else ""),
                                    w,
                                )
                                for m in a, b, w:
                                    out.append(m)
                    # sector arc
                    ab = [s.get(k) for k in ("sector_start", "sector_end")]
                    if all(ab):
                        if ab[0] >= ab[1]:
                            ab[1] += 360
                        if not abs(ab[1] - ab[0]):
                            continue
                        points = [
                            new_node(*project(ll, d + 180, r * f_arc))
                            for d in linspace(*ab, ceil(abs(ab[1] - ab[0]) / 5))
                        ]
                        w = new_way(points)
                        set_tag("lightsector", "arc", w)
                        set_tag("name", label(s), w)
                        set_tag("colour", s.get("colour"), w)
                        points.append(w)
                        for m in points:
                            out.append(m)

    # print(osm)
    with open(outfile, "w") as f:
        f.write(str(out))

    requests.get(f"http://localhost:8111/open_file?filename={os.path.abspath(outfile)}")


generate_sectors("in.osm")
