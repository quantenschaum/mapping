#!/usr/bin/env python
# coding: utf-8

import json
import os
from datetime import datetime
from math import inf, isnan, log, pi, pow, sqrt, tan
import re
import datetime
import pendulum
import requests
from pyquery import PyQuery as pq
from s57 import *


dx = 0.01
dy = dx


def load_json(filename):
    with open(filename) as f:
        return json.load(f)


def latlon_to_grid(lat, lon):
    f = 20037508.34
    x = (lon * f) / 180
    y = log(tan((90 + lat) * pi / 360)) / (pi / 180)
    y = (y * f) / 180
    return x, y


def distance(a, b):
    a, b = [latlon_to_grid(*p) for p in (a, b)]
    return sqrt(sum([pow(a[i] - b[i], 2) for i in range(2)]))


def in_usageband(f, bands=["Approach", "Harbour", "Berthing"]):
    # https://www.nauticalcharts.noaa.gov/charts/rescheming-and-improving-electronic-navigational-charts.html
    return any(b in f["id"] for b in bands)


def gtype(f):
    return f["geometry"]["type"]


def latlon(f):
    p = f["properties"]
    if "x_wgs84" in p:
        return p["y_wgs84"], p["x_wgs84"]
    ll = f["geometry"]["coordinates"]
    return ll[1], ll[0]


def is_int(v):
    try:
        int(v)
        return True
    except:
        return False


def josm_zoom(ll, node=None, delta=0.01):
    select = f"&select=node{node}" if node and int(node) > 0 else ""
    return f"http://localhost:8111/zoom?left={ll[1] - delta}&right={ll[1] + delta}&bottom={ll[0] - delta}&top={ll[0] + delta}{select}"


def get_bounds(xml):
    bounds = xml("osm bounds")
    if bounds:
        return {
            a: float(bounds.attr[a]) for a in ("minlat", "maxlat", "minlon", "maxlon")
        }
    b = {"minlat": +inf, "maxlat": -inf, "minlon": +inf, "maxlon": -inf}
    for e in xml("node"):
        n = pq(e)
        if not n.attr["lat"]:
            continue
        ll = [float(n.attr[a]) for a in ("lat", "lon")]
        b["minlat"] = min(b["minlat"], ll[0])
        b["maxlat"] = max(b["maxlat"], ll[0])
        b["minlon"] = min(b["minlon"], ll[1])
        b["maxlon"] = max(b["maxlon"], ll[1])
    return b


def get_lnam(f):
    return f["properties"]["lnam"]


def load_geojson(filename, geotype="point"):
    print("loading GeoJSON", filename)
    data = load_json(filename)
    features = {}
    merged = 0
    for f1 in data["features"]:
        if gtype(f1).lower() == geotype and in_usageband(f1):
            p1 = f1["properties"]
            lnam = get_lnam(f1)
            f0 = features.get(lnam)
            if f0:
                assert lnam == get_lnam(f0)
                p0 = f0["properties"]
                s0, s1 = [p["scamax"] for p in (p0, p1)]
                if s1 < s0:
                    merged += 1
                    features[lnam] = f1
            else:
                features[lnam] = f1

    print("total", len(data["features"]), "filtered", len(features))
    # print(features)

    return list(features.values())


# load_geojson("data/bsh/AidsAndServices.json")
# load_geojson("data/bsh/Hydrography.json")
# load_geojson("data/bsh/RocksWrecksObstructions.json")
# load_geojson("data/bsh/SkinOfTheEarth.json", "polygon")
# load_geojson("data/bsh/Topography.json")
# oops


def load_bsh_rocks(filename):
    data = load_geojson(filename)
    points = []
    for f in data["features"]:
        # print(f)
        if "Rock" in f["id"]:
            ll = latlon(f)
            tags = {"ll": ll}
            p = f["properties"]
            tags["properties"] = p
            tags["seamark:type"] = "rock"
            tags["seamark:lnam"] = p["lnam"]
            tags["seamark:rock:water_level"] = s57attr("watlev", p)
            depth = p.get("valsou")
            if "valsou" in p:
                tags["depth"] = float(p["valsou"])

            points.append(tags)

    print("rocks", len(points))

    return points


def load_bsh_wrecks(filename):
    # https://wiki.openstreetmap.org/wiki/Seamarks/Wrecks
    # https://wiki.openstreetmap.org/wiki/Tag:seamark:type%3Dwreck
    data = load_geojson(filename)
    points = []
    for f in data["features"]:
        # print(f)
        if "Wreck" in f["id"]:
            ll = latlon(f)
            tags = {"ll": ll}
            p = f["properties"]
            tags["properties"] = p
            tags["seamark:type"] = "wreck"
            tags["seamark:lnam"] = p["lnam"]
            tags["seamark:wreck:category"] = s57attr("catwrk", p)
            if "watlev" in p:
                tags["seamark:wreck:water_level"] = s57attr("watlev", p)
            if "valsou" in p:
                tags["depth"] = float(p["valsou"])

            points.append(tags)

    print("wrecks", len(points))

    return points


def load_bsh_obstructions(filename):
    # https://wiki.openstreetmap.org/wiki/Tag:seamark:type%3Dobstruction
    data = load_geojson(filename)
    points = []
    for f in data["features"]:
        # print(f)
        if "Obstruction" in f["id"] or "Foul" in f["id"]:
            # print(json.dumps(f, indent=2))
            ll = latlon(f)
            tags = {"ll": ll}
            p = f["properties"]
            tags["properties"] = p
            tags["seamark:type"] = "obstruction"
            tags["seamark:lnam"] = p["lnam"]
            if "catobs" in p:
                tags["seamark:obstruction:category"] = s57attr("catobs", p)
            if "watlev" in p:
                tags["seamark:obstruction:water_level"] = s57attr("watlev", p)
            if "valsou" in p:
                tags["depth"] = float(p["valsou"])

            points.append(tags)

    print("obstructions", len(points))

    return points


def load_bsh_seabed(filename):
    # https://wiki.openstreetmap.org/wiki/Tag:seamark:type%3Dobstruction
    data = load_geojson(filename)
    points = []
    for f in data["features"]:
        # print(f)
        if "Seabed" in f["id"]:
            # print(json.dumps(f, indent=2))
            ll = latlon(f)
            tags = {"ll": ll}
            p = f["properties"]
            tags["properties"] = p
            tags["seamark:lnam"] = p["lnam"]

            found = 0

            if is_int(p.get("natsur")):
                found = 1
                tags["seamark:type"] = "seabed_area"
                tags["seamark:seabed_area:surface"] = s57attr("natsur", p)
                if p.get("natqua"):
                    tags["seamark:seabed_area:quality"] = s57attr("natqua", p)

            if is_int(p.get("catwed")):
                cat = s57attr("catwed", p)
                if cat == "sea_grass":
                    found = 3
                    tags["seamark:type"] = "seagrass"
                else:
                    found = 2
                    tags["seamark:type"] = "weed"
                    tags["seamark:weed:category"] = s57attr("catwed", p)

            points.append(tags)

    print("seabed infos", len(points))

    return points


_keys = set()


def add_keys(p):
    try:
        p = p["properties"]
    except:
        pass
    _keys.update(p.keys())


def print_keys():
    print("processed", _keys.intersection(S57keys.keys()))
    print("ununsed  ", _keys.difference(S57keys.keys()))


def group_by(data, key=lambda v: v):
    grp = {}
    for e in data:
        k = key(e)
        grp[k] = grp.get(k, []) + [e]
    return grp


def load_bsh(filename, kind):
    data = load_geojson(filename)

    print("kind", kind)

    lights = group_by(
        filter(lambda f: "Light" in f["id"], data),
        lambda f: str(latlon(f)),
    )
    print("lights", len(lights))

    daymarks = group_by(
        filter(lambda f: "Daymark" in f["id"], data),
        lambda f: str(latlon(f)),
    )
    print("daymarks", len(daymarks))

    buoys = []
    for f in data:
        if kind in f["id"].lower():
            ll = latlon(f)
            tags = {"ll": ll}
            add_tags(tags, f)
            assert tags["seamark:type"].startswith(kind), (f, tags)

            d = daymarks.get(str(ll))
            if d:
                d = group_by(d, lambda e: int(e["properties"]["scamax"]))
                d = d[min(d.keys())]
                d = [s57translate(e["properties"]) for e in d]
                update_nc(tags, d[0])
            else:
                add_generic_topmark(tags)

            l = lights.get(str(ll))
            if l:
                l = group_by(l, lambda e: int(e["properties"]["scamax"]))
                l = l[min(l.keys())]
                l = [s57translate(e["properties"]) for e in l]
                if len(l) == 1:
                    update_nc(tags, l[0])
                else:
                    for i, e in enumerate(l, 1):
                        s = {}
                        for k, v in e.items():
                            s[k.replace("light:", f"light:{i}:")] = v
                        update_nc(tags, s)

            if 0:
                print("-" * 100)
                for k, v in tags.items():
                    print(k, "=", v)

            buoys.append(tags)

    print(kind, len(buoys))

    return buoys


def load_bsh_buoys(filename):
    return load_bsh(filename, "buoy")


def load_bsh_beacons(filename):
    return load_bsh(filename, "beacon")


rws_buoy = {
    "benaming": "objnam",
    "obj_vorm_c": "boyshp",
    "obj_kleur_": "colour",
    "kleurpatr_": "colpat",
}
rws_topmark = {
    "v_tt_c": "topshp",
    "tt_kleur_c": "colour",
    "tt_pat_c": "colpat",
}
rws_light = {
    "licht_kl_c": "colour",
    "sign_kar_c": "litchr",
    "sign_gr_c": "siggrp",
    "sign_perio": "sigper",
}


def load_rws_buoys(filename):
    data = load_json(filename)
    points = []
    for f in data["features"]:
        ll = latlon(f)
        tags = {"ll": ll}
        # print(json.dumps(f["properties"], indent=2))

        for i, l in enumerate((rws_buoy, rws_topmark, rws_light)):
            p = f["properties"]
            p = {b: p[a] for a, b in l.items() if p.get(a) and p[a] != "#"}
            if i == 0:
                p["buoy_type"] = 5
            if p:
                add_tags(tags, p)
        # add_generic_topmark(tags)

        points.append(tags)

    print(len(points))

    return points


def load_marrekrite(gpx="marrekrite.gpx"):
    import gpxpy

    with open(gpx) as f:
        gpx = gpxpy.parse(f)

    points = []
    for wpt in gpx.waypoints:
        tags = {}
        tags["ll"] = wpt.latitude, wpt.longitude
        tags["seamark:name"] = wpt.name.split()[0]
        # tags["seamark:source"] = "https://github.com/marcelrv/OpenCPN-Waypoints"
        tags["seamark:type"] = "mooring"
        if wpt.name.startswith("MB"):
            tags["seamark:mooring:category"] = "buoy"
            tags["seamark:mooring:colour"] = "yellow;blue"
            tags["seamark:mooring:colour_pattern"] = "horizontal"
            tags["seamark:mooring:shape"] = "spherical"
            tags["seamark:information"] = "max 24h"
            # print(wpt)
            # print(json.dumps(tags,indent=2))
            points.append(tags)
        # elif 'steiger' in wpt.name.lower():
        #    tags["seamark:mooring:category"] = "wall"

    return points


deprecated_tags = (
    "source",
    "seamark:source",
    "seamark:source:id",
    "seamark",
    "buoy",
    "beacon",
)


def update_node(n, tags, dmin=1):
    ll = [float(n.attr[a]) for a in ("lat", "lon")]
    modifications = []

    d = distance(ll, tags["ll"])
    if isnan(d) or d > dmin:
        n.attr["lat"], n.attr["lon"] = [str(x) for x in tags["ll"]]
        modifications.append(("POS", tags["ll"], "" if isnan(d) else f"{round(d)}m"))

    fill_types(tags)

    for k, v in tags.items():
        v = str(v) if v is not None else v
        if k.startswith("seamark") or k.startswith("depth"):
            tag = n.find(f"tag[k='{k}']")
            if tag:
                w = tag.attr["v"]
                if not v:
                    tag.remove()
                    modifications.append(("DEL", f"{k}={w}"))
                elif w != v:
                    tag.attr["v"] = v
                    modifications.append(("MOD", f"{k}={v}", w))
            elif v:
                pq(f'<tag k="{k}" v="{v}" />').append_to(n)
                modifications.append(("ADD", f"{k}={v}"))

    if modifications:
        n.attr["action"] = "modify"
        for k in deprecated_tags:
            tag = n.find(f"tag[k='{k}']")
            if tag:
                tag.remove()

        ll = [float(n.attr[a]) for a in ("lat", "lon")]
        msg = (
            tags.get("seamark:type"),
            tags.get("seamark:name"),
            "matched by",
            tags.get("match"),
            n.attr("timestamp"),
            n.attr("user"),
        )
        modifications.insert(0, josm_zoom(ll, n.attr["id"]))
        modifications.insert(0, msg)
        # for l in modifications:            print("\t", *[str(s).strip() for s in l])

    return modifications


def str_equals(a, b):
    a, b = [str(s).lower().replace(" ", "") for s in (a, b)]
    return a == b


def update_osm(
    infile,
    points,
    outfile,
    add=True,
    remod=False,
    remove=False,
    n_dist=1000,
    p_dist=50,
    s_dist=1,
    sm_type=None,
    min_age=0,
    user=None,
    review=False,
):
    x = pq(filename=infile)

    now = pendulum.now()

    bounds = get_bounds(x)
    print("bounds", bounds)
    data = list(
        filter(
            lambda p: bounds["minlat"] <= p["ll"][0] <= bounds["maxlat"]
            and bounds["minlon"] <= p["ll"][1] <= bounds["maxlon"],
            points,
        )
    )

    matches = {}
    modifications = []
    for e in x("node"):
        n = pq(e)
        if not n.find("tag[k='seamark:type']"):
            continue
        if re.match(sm_type, n.find("tag[k='seamark:type']").attr["v"]) is None:
            continue
        ll = [float(n.attr[a]) for a in ("lat", "lon")]
        if bounds and not (
            bounds["minlat"] <= ll[0] <= bounds["maxlat"]
            and bounds["minlon"] <= ll[1] <= bounds["maxlon"]
        ):
            continue
        ts = n.attr("timestamp")
        age = None
        if ts:
            ts = pendulum.parse(ts)
            age = now - ts

        type = n.find("tag[k='seamark:type']").attr["v"]
        name = (
            n.find("tag[k='seamark:name']").attr["v"]
            or n.find("tag[k='name']").attr["v"]
        )
        lnam = n.find("tag[k='seamark:lnam']").attr["v"]

        p = []
        match = "NONE"

        if lnam:
            p = list(filter(lambda e: lnam == e.get("seamark:lnam"), data))
            if p:
                match = "LNAM"

        if not p and name:
            p = list(
                filter(
                    lambda e: distance(ll, e["ll"]) <= n_dist
                    and str_equals(name, e.get("seamark:name")),
                    data,
                )
            )
            if p:
                match = "NAME"

        if not p:
            p = list(filter(lambda e: distance(ll, e["ll"]) <= p_dist, data))
            if p:
                match = "POSI"

        matches[match] = matches.get(match, 0) + 1

        if len(p) > 1:
            ll = p[0]["ll"]
            print(
                "AMBIGOUS",
                len(p),
                distance(ll, p[1]["ll"]),
                match,
                name,
                josm_zoom(ll)
                # json.dumps(p, indent=2),
            )

        for m in p:
            data.remove(m)

        if not n.attr["action"]:
            if age and age.days < min_age:
                print("SKIPPED", type, name, ts)
                continue
            if user and (
                n.attr("user") == user[1:]
                if user.startswith("-")
                else n.attr("user") != user
            ):
                print("SKIPPED", type, name, n.attr("user"))
                continue

        if remove and len(p) == 0:
            m = ["REMOVE?", (type, name), josm_zoom(ll, n.attr["id"])]
            print(*m[:3])
            modifications.append(m)

        if not add and len(p) == 1:
            p = p[0]
            p["match"] = match
            if remod or not n.attr["action"]:
                m = update_node(n, p, s_dist)
                if m:
                    m.insert(0, "CHANGED")
                    print(*m[:3])
                    modifications.append(m)

    added = 0
    if bounds and add:
        for i, p in enumerate(data, 10000):
            n = pq(f'<node id="{-i}" visible="true" lat="nan" lon="nan"/>')
            m = update_node(n, p, s_dist)
            m.insert(0, "ADDED")
            print(*m[:3])
            modifications.append(m)
            x("osm").prepend(n)
            added += 1

    print("MATCHED", matches)
    print("ADDED", added)

    if modifications:
        with open(outfile, "w") as f:
            f.write(str(x))

        requests.get(
            f"http://localhost:8111/open_file?filename={os.path.abspath(outfile)}"
        )

        if review:
            for i, m in enumerate(modifications, 1):
                for l in m:
                    print(l)
                requests.get(m[2])
                input(f"{i}/{len(modifications)}")


def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(
        prog="buoy updater",
        description="update buoys by manipulating OSM xml from geojson",
        epilog="https://github.com/quantenschaum/mapping/",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "mode",
        help="mode of operation (what kind of data to read and update)",
    )
    parser.add_argument(
        "datafile",
        help="data source file to read (geojson/gpx)",
    )
    parser.add_argument(
        "infile",
        help="OSM XML file to read",
    )
    parser.add_argument(
        "outfile",
        help="OSM XML file to write",
        default="out.osm",
        nargs="?",
    )
    parser.add_argument(
        "-a",
        "--add",
        help="add buoys",
        action="store_true",
    )
    parser.add_argument(
        "-m",
        "--remod",
        help="update nodes that already have been modified",
        action="store_true",
    )
    parser.add_argument(
        "-r",
        "--remove",
        help="print hint for node to be removed (they are not removed automatically)",
        action="store_true",
    )
    parser.add_argument(
        "-j",
        "--review",
        help="load and review changes in JOSM",
        action="store_true",
    )
    parser.add_argument(
        "-N",
        "--n-dist",
        help="distance in meters for matching nodes by name",
        type=int,
        default=1000,
    )
    parser.add_argument(
        "-P",
        "--p-dist",
        help="distance in meters for matching nodes by position",
        type=int,
        default=50,
    )
    parser.add_argument(
        "-S",
        "--s-dist",
        help="threshold in meters for actually moving a node",
        type=int,
        default=1,
    )
    parser.add_argument(
        "-A",
        "--age",
        help="min age (days) required for node to be changed",
        type=int,
        default=0,
    )
    parser.add_argument(
        "-U",
        "--user",
        help="user of previous change",
    )

    args = parser.parse_args()

    mode = args.mode
    datafile = args.datafile
    infile = args.infile
    outfile = args.outfile

    if all(s in mode for s in ("rws", "buoy")):
        seamark_type = "buoy_.*"
        data = load_rws_buoys(datafile)
    elif all(s in mode for s in ("marre",)):
        seamark_type = "buoy_.*"
        data = load_marrekrite(datafile)
    elif all(s in mode for s in ("bsh", "buoy")):
        seamark_type = "buoy_.*"
        data = load_bsh_buoys(datafile)
    elif all(s in mode for s in ("bsh", "beacon")):
        seamark_type = "beacon_.*"
        data = load_bsh_beacons(datafile)
    elif all(s in mode for s in ("bsh", "rock")):
        seamark_type = "rock"
        data = load_bsh_rocks(datafile)
    elif all(s in mode for s in ("bsh", "wreck")):
        seamark_type = "wreck"
        data = load_bsh_wrecks(datafile)
    elif all(s in mode for s in ("bsh", "obstr")):
        seamark_type = "obstruction"
        data = load_bsh_obstructions(datafile)
    elif all(s in mode for s in ("bsh", "seabed")):
        seamark_type = "seabed_area|weed|seagrass"
        data = load_bsh_seabed(datafile)

    print("seamark:type", seamark_type)

    update_osm(
        infile,
        data,
        outfile,
        add=args.add,
        remod=args.remod,
        remove=args.remove,
        n_dist=args.n_dist,
        p_dist=args.p_dist,
        s_dist=args.s_dist,
        sm_type=seamark_type,
        min_age=args.age,
        user=args.user,
        review=args.review,
    )


if __name__ == "__main__":
    main()
