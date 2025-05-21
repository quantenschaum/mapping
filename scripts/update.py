#!/usr/bin/env python3
# coding: utf-8

import json
import os
import re
from functools import reduce
from math import inf, isnan, log, pi, pow, sqrt, tan, isfinite
from os.path import basename, splitext
from os.path import isfile

import pendulum
import requests
from lxml import etree
from pyquery import PyQuery as pq

from s57 import *

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
try:
  from rich_argparse import ArgumentDefaultsRichHelpFormatter as ArgumentDefaultsHelpFormatter
except: pass

from functools import partial
from rich.console import Console
from rich.progress import track
from rich.traceback import install
console=Console()
if console.is_terminal:
  print=console.print
  track=partial(track,console=console)
  install()

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


ubands = ["Approach", "Harbour", "Berthing"]
# ubands = ["Approach"]


def in_usageband(f, bands=ubands):
    # https://www.nauticalcharts.noaa.gov/charts/rescheming-and-improving-electronic-navigational-charts.html
    if "id" in f:
        return any(b in f["id"] for b in bands)
    else:
        return True


def gtype(f):
    g = f.get("geometry")
    if g:
        t = g.get("type")
        if t:
            return t.lower() if t else None


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
    return b if isfinite(sum(b.values())) else None


def get_lnam(f):
    return f["properties"]["lnam"]


def load_geojson(filename, geotype="point", inject={}):
    print("loading GeoJSON", filename)
    data = load_json(filename)
    features = {}
    merged = 0

    filtered = filter(
        lambda f: gtype(f) == geotype and in_usageband(f),
        data["features"],
    )

    grouped = group_by(filtered, get_lnam)

    def key(e):
        p = e["properties"]
        return int(p.get("scamax") or p.get("scamin") or 99999999)

    selected = [sorted(g, key=key)[0] for g in grouped.values()]

    print("total", len(data["features"]), "selected", len(selected))

    keys = set()
    types = set()
    for e in selected:
        p = e["properties"]
        update_nc(p, inject)
        keys.update(p.keys())
        try:
            types.add(s57type(p))
        except:
            types.add("unknown")

    # print("known keys", keys.intersection(S57keys.keys()))
    # print("other keys", keys.difference(S57keys.keys()))
    # print("types", types)

    return selected


# f = "data/waddenzee/BOYLAT.json"
# d = load_geojson(f)


def load_enc(layer_files, other_files):
    if isinstance(layer_files, str):
        layer_files = [layer_files]
    if isinstance(other_files, str):
        other_files = [other_files]

    def load(f):
        try:
            t = S57types.get(splitext(basename(f))[0])
            t = {"_type_": t} if t else {}
            return load_geojson(f, inject=t)
        except Exception as x:
            print(x, f)
            return []

    data, other = [
        reduce(lambda a, b: a + b, [load(f) for f in files], [])
        for files in (layer_files, other_files)
    ]
    other = {k: v[0] for k, v in group_by(other, get_lnam).items()}

    points = []
    for f in data:
        ll = latlon(f)
        tags = {"ll": ll}
        p = f["properties"]

        # if not is_something(p): continue

        add_tags(tags, f)

        refs = p.get("lnam_refs") or []
        refs = [add_tags({}, other[r]) for r in refs if r in other]
        for t, rs in group_by(refs, smtype).items():
            if t == "light":
                update_nc(tags, merge_lights(rs))
            else:
                for r in rs:
                    update_nc(tags, r)

        fix_tags(tags)
        add_generic_topmark(tags)

        # if "mmsi" in str(tags):
        #     print("-" * 100)
        #     print(p)
        #     for r in refs:
        #         print(r)
        #     for k, v in tags.items():
        #         print(k, "=", v)

        points.append(tags)

    g = group_by(points, smtype)
    print("\n".join([f">{k} {len(v)}" for k, v in g.items()]))

    return points


def load_enc_layers(
    datadir="data/waddenzee",
    layers=(
        "BOYLAT",
        "BOYCAR",
        "BOYSAW",
        "BOYSPP",
        "BCNLAT",
        "BCNCAR",
        "BCNISD",
        "BCNSPP",
        "LNDMRK",
        "PILPNT",
        "OFSPLF",
        "HRBFAC",
        # "UWTROC",
        # "WRECKS",
        # "OBSTRN",
    ),
    others=layers2,
):
    def filelist(directory, layers):
        files = [f"{datadir}/{l}.json" for l in layers]
        files = list(filter(isfile, files))
        return files

    return load_enc(
        filelist(datadir, layers),
        filelist(datadir, others),
    )


# load_enc_layers("data/us")


def load_bsh(filename, kind):
    data = load_geojson(filename)

    # g = group_by(data, lambda e: e["id"].split(".")[0].split("_")[-1])
    # print(sorted(g.keys()))
    #
    # p = set()
    # for l in (f["properties"].keys() for f in data):
    #     p.update(l)
    # print(sorted(p.difference(S57keys.keys())))

    print("kind", kind)

    lights = group_by(
        filter(lambda f: "Light" in f["id"], data),
        lambda f: str(latlon(f)),
    )
    print("lights", len(lights))

    daymarks = group_by(
        filter(
            lambda f: is_something(f["properties"])
            and (
                "Daymark" in f["id"]
                or ("Equipment" in f["id"] and "catrtb" in str(f))
                or ("Facility" in f["id"] and "feat" in kind)
                or ("Feature" in f["id"] and "faci" in kind)
            ),
            data,
        ),
        lambda f: str(latlon(f)),
    )
    print("daymarks", len(daymarks))

    points = []
    for f in data:
        if kind in f["id"].lower():
            ll = latlon(f)
            tags = {"ll": ll}
            p = f["properties"]

            if not is_something(p):
                continue

            add_tags(tags, f)
            # assert tags["seamark:type"].startswith(kind), (f, tags)

            d = daymarks.get(str(ll))
            if d:
                d = group_by(d, lambda e: int(e["properties"]["scamax"]))
                d = d[min(d.keys())]
                d = [s57translate(e["properties"]) for e in d]
                for m in d:
                    assert smtype(m) != "light", m
                    update_nc(tags, m)

            l = lights.get(str(ll))
            if l:
                l = group_by(l, lambda e: int(e["properties"]["scamax"]))
                l = l[min(l.keys())]
                l = [s57translate(e["properties"]) for e in l]
                for m in l:
                    assert smtype(m) == "light", m
                update_nc(tags, merge_lights(l))

            add_generic_topmark(tags)
            fix_tags(tags)

            # if "" in str(tags):
            #     print("-" * 100)
            #     for k, v in tags.items():
            #         print(k, "=", v)

            typ = smtype(tags)
            if typ in ("harbour",):
                continue

            points.append(tags)

    g = group_by(points, smtype)
    print("\n".join([f">{k} {len(v)}" for k, v in g.items()]))

    return points


# load_bsh("data/bsh/AidsAndServices.json", "buoy")
# load_bsh("data/bsh/AidsAndServices.json", "beac")
# load_bsh("data/bsh/AidsAndServices.json", "faci")
# load_bsh("data/bsh/AidsAndServices.json", "stat")
# load_bsh("data/bsh/AidsAndServices.json", "serv")
# load_bsh("data/bsh/AidsAndServices.json", "equi")


def load_bsh_lights(filename):
    data = load_geojson(filename)

    kind = "light"
    print("kind", kind)

    other = group_by(
        filter(lambda f: "Light" not in f["id"], data),
        lambda f: str(latlon(f)),
    )

    lights = []
    typ = "light"
    for f in data:
        if kind in f["id"].lower():
            ll = latlon(f)
            if str(ll) in other:
                # continue
                if any(any(x in g["id"] for x in ("Buoy","Beac","Facil")) for g in other[str(ll)]):
                    continue
            tags = {"ll": ll}
            add_tags(tags, f)
            assert smtype(tags).startswith(kind), (f, tags)

            if (
                float(tags.get(f"seamark:{typ}:range", 0)) > 19
                and f"seamark:{typ}:colour" in tags
                and f"seamark:{typ}:character" in tags
            ):
                tags["seamark:type"] = "light_major"
            else:
                tags["seamark:type"] = "light_minor"

            lights.append(tags)

    glights = group_by(lights, lambda e: str(e["ll"]))
    lights = [merge_lights(s) for s in glights.values()]

    print(kind, len(lights))
    return lights


# load_bsh_lights("data/bsh/AidsAndServices.json")


def load_bsh_obstr(filename, kind):
    data = load_geojson(filename)
    points = []
    typ = {"r": "rock", "w": "wreck", "o": "obstruction"}[kind[0]]
    for f in data:
        if kind in f["id"].lower():
            ll = latlon(f)
            tags = {"ll": ll}
            f["properties"]["_type_"] = typ
            add_tags(tags, f)
            fix_tags(tags)
            assert smtype(tags) == typ, (f, tags)
            points.append(tags)

    print(kind, len(points))

    return points


# load_bsh_obstr("data/bsh/RocksWrecksObstructions.json", "rock")
# load_bsh_obstr("data/bsh/RocksWrecksObstructions.json", "wreck")
# load_bsh_obstr("data/bsh/RocksWrecksObstructions.json", "obstr")


def load_bsh_seabed(filename):
    # https://wiki.openstreetmap.org/wiki/Tag:seamark:type%3Dobstruction
    data = load_geojson(filename)
    points = []
    kind = "seabed"
    for f in data:
        if kind in f["id"].lower():
            ll = latlon(f)
            tags = {"ll": ll}
            p = f["properties"]

            if any(is_int(p.get(k)) for k in ("natsur", "catwed", "catseg")):
                add_tags(tags, p)
                fix_tags(tags)
                assert smtype(tags) in ("seabed_area", "weed", "seagrass"), (
                    f,
                    tags,
                )
                points.append(tags)

    print(kind, len(points))

    return points


# load_bsh_seabed("data/bsh/Hydrography.json")

rws_buoy = {
    "benaming": "objnam",
    "obj_vorm_c": "boyshp",
    "obj_kleur_": "colour",
    "kleurpatr_": "colpat",
}
rws_topmark = {
    "_type_": "topmark",
    "v_tt_c": "topshp",
    "tt_kleur_c": "colour",
    "tt_pat_c": "colpat",
}
rws_light = {
    "_type_": "light",
    "licht_kl_c": "colour",
    "sign_kar_c": "litchr",
    "sign_gr_c": "siggrp",
    "sign_perio": "sigper",
    # "licht_hgt": "height",
    # "licht_rich": "orient",
}


def load_rws_buoys(filename, skip_errors=0):
    data = load_json(filename)
    points = []
    for f in data["features"]:
        try:
            ll = latlon(f)
            tags = {"ll": ll}
            # print(json.dumps(f["properties"], indent=2))

            for i, l in enumerate((rws_buoy, rws_topmark, rws_light)):
                p = f["properties"]
                p = {b: p[a] for a, b in l.items() if p.get(a,'#') != '#'}
                if i == 0:
                    p["buoy_type"] = 1
                for k,v in dict(p).items():
                    if v=='L': del p[k]
                if p:
                    add_tags(tags, p)
                    fix_tags(tags)
            # add_generic_topmark(tags)

            points.append(tags)
        except Exception as x:
            print(x)
            assert skip_errors, (x,f)

    print("buoys", len(points))

    return points


rws_beacon = {
    "benaming": "objnam",
    "obj_vorm_c": "bcnshp",
    "obj_kleur_": "colour",
    "kleurpatr_": "colpat",
    # "obj_hoogte": "verlen",
}
rws_racon = {
    "_type_": "radar_transponder",
    "racon_code": "siggrp",
}


def load_rws_beacons(filename):
    data = load_json(filename)
    points = []
    for f in data["features"]:
        ll = latlon(f)
        tags = {"ll": ll}
        # print(json.dumps(f["properties"], indent=2))

        t = "_type_"
        for i, l in enumerate((rws_beacon, rws_topmark, rws_light, rws_racon)):
            p = f["properties"]
            p = {b: p[a] for a, b in l.items() if p.get(a) and p[a] != "#"}
            if t in l:
                p[t] = l[t]
            if i == 0:
                p["beacon_type"] = 1
            if p:
                add_tags(tags, p)
        # add_generic_topmark(tags)

        sectors = []
        p = f["properties"]
        for i in range(1, 16, 1):
            c = f"licht_{i}_k_"[:10]
            g = f"licht_{i}_g"
            if i == 11:
                g = g.replace("_g", "g")
            if p[c] == "#":
                break
            sectors.append((s57attr("colour", p[c]), float(p[g].replace(",", "."))))
        if sectors:
            lights = []
            for i, s in enumerate(sectors):
                l = smtype({k: v for k, v in tags.items() if "light" in k}, "light")
                l["seamark:light:colour"] = s[0]
                l["seamark:light:sector_start"] = s[1]
                l["seamark:light:sector_end"] = sectors[(i + 1) % len(sectors)][1]
                if s[0] != "black":
                    lights.append(l)
            lights = merge_lights(lights)
            update_nc(tags, lights)

        fix_tags(tags)

        # if "light:1" in str(tags):
        #     print(f["properties"])
        #     print(tags)

        points.append(tags)

    print("beacons", len(points))

    return points


# load_rws_beacons("data/vwm/vast.json")


def load_marrekrite(gpx="marrekrite.gpx"):
    import gpxpy

    with open(gpx) as f:
        gpx = gpxpy.parse(f)

    points = []
    for wpt in gpx.waypoints:
        tags = {}
        tags["ll"] = wpt.latitude, wpt.longitude
        tags["seamark:name"] = wpt.name.split()[0]
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
        modifications.append(("POS", tags["ll"], 0 if isnan(d) else round(d)))

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
                elif (not str_equals(w, v)) if k == "seamark:name" else w != v:
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
                if k == "seamark:source":
                    if not tag.attr["v"].endswith("*"):
                        tag.attr["v"] += " *"
                else:
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
    infile = infile if infile != "none" else None
    x = pq(filename=infile) if infile else pq("<osm version='0.6'/>")
    add |= not infile

    now = pendulum.now()

    bounds = get_bounds(x)
    print("bounds", bounds)
    data = (
        list(
            filter(
                lambda p: bounds["minlat"] <= p["ll"][0] <= bounds["maxlat"]
                and bounds["minlon"] <= p["ll"][1] <= bounds["maxlon"],
                points,
            )
        )
        if bounds
        else points
    )
    print("points", len(data))

    matches = {}
    modifications = []
    for e in track(list(x("node")),'updating nodes'):
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
                "[red]AMBIGOUS",
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
                print("[yellow]SKIPPED", type, name, ts)
                continue
            if user and (
                n.attr("user") == user[1:]
                if user.startswith("-")
                else n.attr("user") != user
            ):
                print("[yellow]SKIPPED", type, name, n.attr("user"))
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
                    # print(*m[:3])
                    modifications.append(m)

    added = 0
    if add:
        for i, p in track(enumerate(data, 1),'adding points',total=len(data)):
            n = pq(f'<node id="{-i}" visible="true" lat="nan" lon="nan"/>')
            m = update_node(n, p, s_dist)
            m.insert(0, "ADDED")
            # print(*m[:3])
            modifications.append(m)
            x("osm").append(n)
            added += 1

    print("[yellow]MATCHED", matches)
    print("[green]ADDED", added)

    if modifications:
        with open(outfile, "wb") as f:
            etree.indent(x.root, space="  ")
            s = etree.tostring(x.root, pretty_print=True, encoding="utf-8")
            f.write(s)

        try:
            requests.get(
                f"http://localhost:8111/open_file?filename={os.path.abspath(outfile)}"
            )
        except:
            pass

        if review:
            def sortkey(e):
              name=str(e[1][1] or '')
              name=name.replace(' ','')
              m=re.match(r'(.*?)(\d+)',name)
              if m:
                name=f'{m.group(1)}{int(m.group(2)):06}'
              return name

            modifications.sort(key=sortkey)

            for i, m in enumerate(modifications, 1):
                for j, l in enumerate(m):
                    print(f"{'  'if j>1 else ''}{l}", end=" " if j == 0 else "\n")
                if len(m) <= 4 and "seamark:lnam" in str(m):
                    continue
                # if all(x not in str(m) for x in ("'POS'", "'MOD'")):
                #     continue
                # if all(x not in str(m) for x in ("'MOD'",)):
                #     if m[3][0] == "POS" and m[3][2] < 30:
                #         continue
                requests.get(m[2])
                input(f"  {i}/{len(modifications)}")


def main():
    parser = ArgumentParser(
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
        metavar="source",
    )
    parser.add_argument(
        "infile",
        help="OSM XML file to read",
        metavar="in.osm",
        nargs="?",
    )
    parser.add_argument(
        "outfile",
        help="OSM XML file to write",
        default="out.osm",
        metavar="out.osm",
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
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="skip errors when reading source file",
    )

    args = parser.parse_args()

    mode = args.mode
    datafile = args.datafile
    infile = args.infile
    outfile = args.outfile

    seamark_type = "xxx"
    if all(s in mode for s in ("rws", "buoy")):
        seamark_type = "buoy_.*"
        data = load_rws_buoys(datafile, args.skip_errors)
    if all(s in mode for s in ("rws", "beac")):
        seamark_type = "beacon_.*"
        data = load_rws_beacons(datafile, args.skip_errors)
    elif all(s in mode for s in ("marre",)):
        seamark_type = "buoy_.*"
        data = load_marrekrite(datafile)
    elif all(s in mode for s in ("bsh", "buoy")):
        seamark_type = "buoy_.*"
        data = load_bsh(datafile, "buoy")
    elif all(s in mode for s in ("bsh", "beac")):
        seamark_type = "beacon_.*"
        data = load_bsh(datafile, "beacon")
    elif all(s in mode for s in ("bsh", "rock")):
        seamark_type = "rock"
        data = load_bsh_obstr(datafile, seamark_type)
    elif all(s in mode for s in ("bsh", "wreck")):
        seamark_type = "wreck"
        data = load_bsh_obstr(datafile, seamark_type)
    elif all(s in mode for s in ("bsh", "obstr")):
        seamark_type = "obstruction"
        data = load_bsh_obstr(datafile, "obstr,foul")
    elif all(s in mode for s in ("bsh", "seabed")):
        seamark_type = "seabed_area|weed|seagrass"
        data = load_bsh_seabed(datafile)
    elif all(s in mode for s in ("bsh", "light")):
        seamark_type = "light_.*|landmark"
        data = load_bsh_lights(datafile)
    elif all(s in mode for s in ("bsh", "fac")):
        data = load_bsh(datafile, "facility")
    elif all(s in mode for s in ("bsh", "feat")):
        data = load_bsh(datafile, "feature")
    elif all(s in mode for s in ("bsh", "serv")):
        data = load_bsh(datafile, "service")
    elif all(s in mode for s in ("bsh", "stat")):
        data = load_bsh(datafile, "station")
    elif all(s in mode for s in ("bsh", "equi")):
        data = load_bsh(datafile, "equipment")

    elif all(s in mode for s in ("enc", "rock")):
        data = load_enc_layers(datafile, ["UWTROC", "WRECKS", "OBSTRN"], [])
    elif all(s in mode for s in ("enc")):
        data = load_enc_layers(datafile)

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
