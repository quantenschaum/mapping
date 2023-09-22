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


types = [
    "buoy_isolated_danger",
    "buoy_safe_water",
    "buoy_special_purpose",
    "buoy_cardinal",
    "buoy_lateral",
]


def type_cat(c, p):
    # print(c, p)
    c = color(c)
    p = pattern(p)
    # print(c, p)
    cat = None
    if "black" in c and "red" in c:
        t = "buoy_isolated_danger"
    elif "white" in c and "red" in c and p == "vertical":
        t = "buoy_safe_water"
    elif "black" in c and "yellow" in c:
        t = "buoy_cardinal"
        if c == "black;yellow":
            cat = "north"
        elif c == "black;yellow;black":
            cat = "east"
        elif c == "yellow;black":
            cat = "south"
        elif c == "yellow;black;yellow":
            cat = "west"
    elif "yellow" in c:
        t = "buoy_special_purpose"
    elif "grey" in c:
        t = "buoy_special_purpose"
    elif "green" in c or "red" in c:
        t = "buoy_lateral"
        if c.startswith("green"):
            if "red" in c:
                if c.count(";") > 2:
                    cat = "channel_separation"
                else:
                    cat = "preferred_channel_port"
            elif "white" in c:
                cat = "danger_left"
            else:
                assert c.count(";") == 0
                cat = "starboard"
        elif c.startswith("red"):
            if "green" in c:
                if c.count(";") > 2:
                    cat = "channel_separation"
                else:
                    cat = "preferred_channel_starboard"
            elif "white" in c:
                cat = "danger_right"
            else:
                assert c.count(";") == 0
                cat = "port"
    return t, cat


def color(s, osm=0):
    if s == "#":
        return
    for k, v in S57["COLOUR"].items():
        s = s.replace(str(k), v)
    return s.replace(",", ";")


def shape(s):
    if s == "#":
        return
    return s57toOSM("boyshp", int(s))


colpat = {1: "horizontal", 2: "vertical"}


def pattern(s):
    if s == "#":
        return
    return colpat[int(s)]


def topmark(s):
    if s == "#":
        return
    return s57toOSM("topshp", int(s))


def light_chr(s):
    if s == "#":
        return
    return s57toOSM("litchr", int(s))


def light_per(s):
    s = s.strip() if s else s
    if not s or s == "#":
        return
    try:
        return str(int(s))
    except:
        return str(float(s))


def light_grp(s):
    s = s.strip() if s else s
    if not s or s == "#":
        return
    return s.replace("(1)", "").replace("(", "").replace(")", "") or None


def latlon_to_grid(lat, lon):
    f = 20037508.34
    x = (lon * f) / 180
    y = log(tan((90 + lat) * pi / 360)) / (pi / 180)
    y = (y * f) / 180
    return x, y


def distance(a, b):
    a, b = [latlon_to_grid(*p) for p in (a, b)]
    return sqrt(sum([pow(a[i] - b[i], 2) for i in range(2)]))


def usageband(f, bands=["Approach", "Harbour", "Berthing"]):
    return any(b in f["id"] for b in bands)


def gtype(f):
    return f["geometry"]["type"]


def latlon(f):
    p = f["properties"]
    if "x_wgs84" in p:
        return p["y_wgs84"], p["x_wgs84"]
    ll = f["geometry"]["coordinates"]
    return ll[1], ll[0]


def load_bsh_rocks(filename):
    print("loading BSH rocks", filename)
    data = load_json(filename)
    points = []
    positions = []
    for f in data["features"]:
        # print(f)
        if "Rock" in f["id"] and usageband(f) and gtype(f) == "Point":
            ll = latlon(f)
            tags = {"ll": ll}
            p = f["properties"]
            tags["properties"] = p
            tags["seamark:type"] = "rock"
            tags["seamark:rock:water_level"] = s57toOSM("watlev", p)
            depth = p.get("valsou")
            if "valsou" in p:
                tags["depth"] = float(p["valsou"])

            if ll not in positions and not any(
                filter(lambda p: distance(p, ll) < 1, positions)
            ):
                points.append(tags)
                positions.append(ll)

    print(len(points))

    return points


def load_bsh_wrecks(filename):
    # https://wiki.openstreetmap.org/wiki/Seamarks/Wrecks
    # https://wiki.openstreetmap.org/wiki/Tag:seamark:type%3Dwreck
    print("loading BSH wrecks", filename)
    data = load_json(filename)
    points = []
    positions = []
    for f in data["features"]:
        # print(f)
        if "Wreck" in f["id"] and usageband(f) and gtype(f) == "Point":
            ll = latlon(f)
            tags = {"ll": ll}
            p = f["properties"]
            tags["properties"] = p
            tags["seamark:type"] = "wreck"
            tags["seamark:wreck:category"] = s57toOSM("catwrk", p)
            if "watlev" in p:
                tags["seamark:wreck:water_level"] = s57toOSM("watlev", p)
            if "valsou" in p:
                tags["depth"] = float(p["valsou"])

            if ll not in positions and not any(
                filter(lambda p: distance(p, ll) < 50, positions)
            ):
                points.append(tags)
                positions.append(ll)

    print(len(points))

    return points


def load_bsh_obstructions(filename):
    # https://wiki.openstreetmap.org/wiki/Tag:seamark:type%3Dobstruction
    print("loading BSH obstructions", filename)
    data = load_json(filename)
    points = []
    positions = []
    for f in data["features"]:
        # print(f)
        if (
            ("Obstruction" in f["id"] or "Foul" in f["id"])
            and usageband(f)
            and gtype(f) == "Point"
        ):
            # print(json.dumps(f, indent=2))
            ll = latlon(f)
            tags = {"ll": ll}
            p = f["properties"]
            tags["properties"] = p
            tags["seamark:type"] = "obstruction"
            if "catobs" in p:
                tags["seamark:obstruction:category"] = s57toOSM("catobs", p)
            if "watlev" in p:
                tags["seamark:obstruction:water_level"] = s57toOSM("watlev", p)
            if "valsou" in p:
                tags["depth"] = float(p["valsou"])

            if ll not in positions and not any(
                filter(lambda p: distance(p, ll) < 50, positions)
            ):
                points.append(tags)
                positions.append(ll)

    print(len(points))

    return points


def is_int(v):
    try:
        int(v)
        return True
    except:
        return False


def load_bsh_seabed(filename):
    # https://wiki.openstreetmap.org/wiki/Tag:seamark:type%3Dobstruction
    print("loading BSH nature of seabed", filename)
    data = load_json(filename)
    points = []
    positions = []
    for f in data["features"]:
        # print(f)
        if "Seabed" in f["id"] and usageband(f) and gtype(f) == "Point":
            # print(json.dumps(f, indent=2))
            ll = latlon(f)
            tags = {"ll": ll}
            p = f["properties"]
            tags["properties"] = p

            found = 0

            if is_int(p.get("natsur")):
                found = 1
                tags["seamark:type"] = "seabed_area"
                tags["seamark:seabed_area:surface"] = s57toOSM("natsur", p)
                if p.get("natqua"):
                    tags["seamark:seabed_area:quality"] = s57toOSM("natqua", p)

            if is_int(p.get("catwed")):
                cat = s57toOSM("catwed", p)
                if cat == "sea_grass":
                    found = 3
                    tags["seamark:type"] = "seagrass"
                else:
                    found = 2
                    tags["seamark:type"] = "weed"
                    tags["seamark:weed:category"] = s57toOSM("catwed", p)

            if (
                found
                and ll not in positions
                and not any(filter(lambda p: distance(p, ll) < 50, positions))
            ):
                points.append(tags)
                positions.append(ll)

    print(len(points))

    return points


def load_bsh_buoys(filename):
    print("loading BSH buoys", filename)
    data = load_json(filename)
    data = list(filter(usageband, data["features"]))
    lights = {}
    for f in data:
        if "Light" in f["id"]:
            ll = latlon(f)
            lls = str(ll)
            # assert lls not in lights, json.dumps((f, lights[lls]), indent=2)
            lights[lls] = f
    buoys = {}
    for f in data:
        if "Buoy" in f["id"]:
            # print(json.dumps(f, indent=2))
            ll = latlon(f)
            lls = str(ll)
            tags = {"ll": ll, "feature": f}
            p = f["properties"]
            # print(p["lnam"])

            n = p.get("objnam")

            tags["seamark:name"] = n
            tags["seamark"] = None

            if "sorind" in p:
                tags["seamark:source"] = p["sorind"] + " " + p["sordat"]

            k = color(p["colour"])
            if not k:
                continue
            t, c = type_cat(k, p.get("colpat", "#"))
            tags["seamark:type"] = t
            for u in types:
                if u == t:
                    continue
                tags[f"seamark:{u}:category"] = None
                tags[f"seamark:{u}:shape"] = None
                tags[f"seamark:{u}:colour"] = None
                tags[f"seamark:{u}:colour_pattern"] = None
            if c:
                tags[f"seamark:{t}:category"] = c
            tags["seamark:buoy_lateral:system"] = (
                (
                    "cevni"
                    if c and (k.count(";") % 2 or "danger" in c or "separation" in c)
                    else "iala-a"
                )
                if "lateral" in t
                else None
            )
            tags[f"seamark:{t}:shape"] = shape(p["boyshp"])
            tags[f"seamark:{t}:colour"] = "red;white" if t == "buoy_safe_water" else k
            tags[f"seamark:{t}:colour_pattern"] = (
                pattern(p["colpat"]) if ";" in k else None
            )

            if t == "buoy_safe_water":
                tags["seamark:topmark:colour"] = "red"
                tags["seamark:topmark:shape"] = topmark(3)
            elif t == "buoy_isolated_danger":
                tags["seamark:topmark:colour"] = "black"
                tags["seamark:topmark:shape"] = topmark(4)
            elif t == "buoy_cardinal":
                tags["seamark:topmark:colour"] = "black"
                if c == "north":
                    tags["seamark:topmark:shape"] = topmark(13)
                if c == "south":
                    tags["seamark:topmark:shape"] = topmark(14)
                if c == "east":
                    tags["seamark:topmark:shape"] = topmark(11)
                if c == "west":
                    tags["seamark:topmark:shape"] = topmark(10)

            l = lights.get(lls)
            if l:
                l = l["properties"]
                tags["seamark:light:colour"] = color(l["colour"])
                tags["seamark:light:character"] = light_chr(l["litchr"])
                tags["seamark:light:period"] = light_per(l.get("sigper"))
                tags["seamark:light:group"] = light_grp(l.get("siggrp"))
                # print(json.dumps(l, indent=2))

            similar = list(
                filter(
                    lambda p: p["ll"] == ll
                    or distance(p["ll"], ll) < 100
                    and p["seamark:name"] == tags["seamark:name"],
                    buoys.values(),
                )
            )

            if similar:
                similar.append(tags)
                similar.sort(key=lambda p: p["feature"]["properties"]["scamax"])
                # assert 0, json.dumps(similar, indent=2)
                for p in similar:
                    if str(p["ll"]) in buoys:
                        del buoys[str(p["ll"])]
                buoys[str(similar[0]["ll"])] = similar[0]
            else:
                buoys[lls] = tags

    print(len(buoys))

    return buoys.values()


def load_rws_buoys(filename):
    data = load_json(filename)
    points = []
    for f in data["features"]:
        try:
            ll = latlon(f)
            tags = {"ll": ll}
            p = f["properties"]
            n = p["benaming"]
            assert n and "#" not in n
            tags["seamark:name"] = n
            tags["seamark:source"] = None
            tags["seamark:source:id"] = None

            k = color(p["obj_kleur_"])
            if not k:
                continue
            t, c = type_cat(k, p["kleurpatr_"])
            tags["seamark:type"] = t
            for u in types:
                if u == t:
                    continue
                tags[f"seamark:{u}:category"] = None
                tags[f"seamark:{u}:shape"] = None
                tags[f"seamark:{u}:colour"] = None
                tags[f"seamark:{u}:colour_pattern"] = None
            if c:
                tags[f"seamark:{t}:category"] = c
            tags["seamark:buoy_lateral:system"] = (
                (
                    "cevni"
                    if c and (k.count(";") % 2 or "danger" in c or "separation" in c)
                    else "iala-a"
                )
                if "lateral" in t
                else None
            )
            tags[f"seamark:{t}:shape"] = shape(p["obj_vorm_c"])
            tags[f"seamark:{t}:colour"] = "red;white" if t == "buoy_safe_water" else k
            tags[f"seamark:{t}:colour_pattern"] = (
                pattern(p["kleurpatr_"]) if ";" in k else None
            )
            tags["seamark:topmark:shape"] = topmark(p["v_tt_c"])
            tc = color(p["tt_kleur_c"])
            tags["seamark:topmark:colour"] = tc
            tags["seamark:topmark:colour_pattern"] = (
                pattern(p["tt_pat_c"]) if tc and ";" in tc else None
            )
            tags["seamark:light:colour"] = color(p["licht_kl_c"])
            tags["seamark:light:character"] = light_chr(p["sign_kar_c"])
            tags["seamark:light:period"] = light_per(p["sign_perio"])
            tags["seamark:light:group"] = light_grp(p["sign_gr_c"])

            tags["seamark"] = None

            tags["properties"] = p

            points.append(tags)

            # if 'PM 40-WE 1' in tags['seamark:name']:
            #    print(json.dumps(tags, indent=2))
            #    print(json.dumps(f, indent=2))
            #   break
        except:
            print(json.dumps(f, indent=2))
            raise

    # print(json.dumps(points[0], indent=2))
    # print(len(points),'points')
    print(len(points))

    return points


# load_geojson('vwm/drijvend.json')


# In[14]:


def load_marrekrite(gpx="marrekrite.gpx"):
    import gpxpy

    with open(gpx) as f:
        gpx = gpxpy.parse(f)

    points = []
    for wpt in gpx.waypoints:
        tags = {}
        tags["ll"] = wpt.latitude, wpt.longitude
        tags["seamark:name"] = wpt.name.split()[0]
        tags["seamark:source"] = "https://github.com/marcelrv/OpenCPN-Waypoints"
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


# In[15]:


def update_node(n, p, dmin=1):
    ll = [float(n.attr[a]) for a in ("lat", "lon")]
    type = p.get("seamark:type")
    name = p.get("seamark:name")
    if name:
        name = name.strip()
    modifications = []
    # print(n)
    # print(json.dumps(p, indent=2))

    d = distance(ll, p["ll"])
    if isnan(d) or d > dmin:
        n.attr["lat"], n.attr["lon"] = [str(x) for x in p["ll"]]
        modifications.append(("POS", p["ll"], "" if isnan(d) else f"{round(d)}m"))

    for k, v in p.items():
        v = str(v) if v is not None else v
        if (k.startswith("seamark") or k.startswith("depth")) and "source" not in k:
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

    source = None
    if modifications:
        n.attr["action"] = "modify"
        for k in "source", "seamark:source", "seamark:source:id":
            tag = n.find(f"tag[k='{k}']")
            if tag:
                source = tag.attr("v")
                tag.remove()
            v = p.get(k)
            if v:
                pq(f'<tag k="{k}" v="{v}" />').append_to(n)

        id = n.attr["id"]
        ll = [float(n.attr[a]) for a in ("lat", "lon")]
        msg = (
            type,
            name,
            "matched by",
            p.get("match"),
            n.attr("timestamp"),
            n.attr("user"),
            source,
        )
        modifications.insert(0, josm_zoom(ll, id))
        modifications.insert(0, msg)
        # for l in modifications:            print("\t", *[str(s).strip() for s in l])

    return modifications


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


# In[17]:


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
    # print(json.dumps(data, indent=2))

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
        name = n.find("tag[k='seamark:name']").attr["v"]

        # print(n)

        p = []
        match = "NONE"
        if name:
            p = list(
                filter(
                    lambda p: distance(ll, p["ll"]) <= n_dist
                    and name == p.get("seamark:name"),
                    data,
                )
            )
            if p:
                match = "NAME"
        if not p:
            p = list(filter(lambda p: distance(ll, p["ll"]) <= p_dist, data))
            if p:
                match = "POS"
        # print(json.dumps(p, indent=2))

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
        # assert len(p) <= 1, json.dumps(p, indent=2)
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

    print("MATCHED NODES ", matches)
    print("MATCHED POINTS", len(data))

    if bounds and add:
        for i, p in enumerate(data, 10000):
            n = pq(f'<node id="{-i}" visible="true" lat="nan" lon="nan"/>')
            m = update_node(n, p, s_dist)
            m.insert(0, "ADDED")
            print(*m[:3])
            modifications.append(m)
            x("osm").prepend(n)

    if modifications:
        with open(outfile, "w") as f:
            f.write(str(x))
        requests.get(
            f"http://localhost:8111/open_file?filename={os.path.abspath(outfile)}"
        )

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
        "infile",
        help="OSM XML file to read",
    )
    parser.add_argument(
        "datafile",
        help="data source file to read (geojson/gpx)",
    )
    parser.add_argument(
        "outfile",
        help="OSM XML file to write",
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

    infile = args.infile
    outfile = args.outfile or args.infile.replace(".osm", ".out.osm")
    datafile = args.datafile

    if "drijvend" in datafile:
        seamark_type = "buoy_.*"
        data = load_rws_buoys(datafile)
    elif "marrekrite" in datafile:
        seamark_type = "buoy_.*"
        data = load_marrekrite(datafile)
    elif "buoy" in infile:
        seamark_type = "buoy_.*"
        data = load_bsh_buoys(datafile)
    elif "rock" in infile:
        seamark_type = "rock"
        data = load_bsh_rocks(datafile)
    elif "wreck" in infile:
        seamark_type = "wreck"
        data = load_bsh_wrecks(datafile)
    elif "obstr" in infile:
        seamark_type = "obstruction"
        data = load_bsh_obstructions(datafile)
    elif "seabed" in infile:
        seamark_type = "seabed_area|weed|seagrass"
        data = load_bsh_seabed(datafile)

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
    )


if __name__ == "__main__":
    main()
