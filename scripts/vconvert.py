#!/usr/bin/env python3

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

try:
    from rich_argparse import (
        ArgumentDefaultsRichHelpFormatter as ArgumentDefaultsHelpFormatter,
    )
except:
    pass

import json
from functools import partial
from os import makedirs
from os.path import dirname, exists

from rich import print
from rich.console import Console
from rich.progress import track
from rich.traceback import install

console = Console()
if console.is_terminal:
    # print=console.log
    track = partial(track, console=console)
    # install()


def load_json(filename):
    with open(filename) as f:
        return json.load(f)


def save_json(filename, data, **kwargs):
    makedirs(dirname(filename) or ".", exist_ok=1)
    with open(filename, "w") as f:
        try:
            assert data["type"] == "FeatureCollection"
            f.write('{"type":"FeatureCollection","features":[\n')
            n = len(data["features"])
            for i, e in enumerate(data["features"], 1):
                f.write(json.dumps(e) + ("," if i < n else "") + "\n")
            f.write("]}\n")
        except:
            return json.dump(data, f, **kwargs)


BOY_FIELDS = {
    "benaming": "OBJNAM",
    "obj_vorm_c": "BOYSHP",
    "obj_kleur_": "COLOUR",
    "kleurpatr_": "COLPAT",
}
BCN_FIELDS = {
    "benaming": "OBJNAM",
    "object_vorm_c": "BCNSHP",
    "obj_kleur_": "COLOUR",
    "kleurpatr_": "COLPAT",
}
TOP_FIELDS = {
    "v_tt_c": "TOPSHP",
    "tt_kleur_c": "COLOUR",
    "tt_pat_c": "COLPAT",
}
LIGHT_FIELDS = {
    "licht_kl_c": "COLOUR",
    "sign_kar_c": "LITCHR",
    "sign_gr_c": "SIGGRP",
    "sign_perio": "SIGPER",
    "licht_hgt": "HEIGHT",
    # 'licht_hoek':'ORIENT',
    "licht_rich": "ORIENT",
}
SECT_FIELDS = {
    "sign_kar_c": "LITCHR",
    "sign_gr_c": "SIGGRP",
    "sign_perio": "SIGPER",
    "licht_A_k_": "COLOUR",
    "licht_A_g": "SECTR1",
    "licht_B_g": "SECTR2",
}
TYPES = {
    "COLPAT": int,
    "BOYSHP": int,
    "BCNSHP": int,
    "TOPSHP": int,
    "HEIGHT": lambda s: float(s.replace(",", ".")),
    "ORIENT": lambda s: float(s.replace(",", ".")),
    "SECTR1": lambda s: float(s.replace(",", ".")),
    "SECTR2": lambda s: float(s.replace(",", ".")),
}


def translate(p, fields, layer):
    o = {}
    for k1, k2 in fields.items():
        v = p.get(k1)
        if v is not None and v not in "#XL":
            o[k2] = TYPES.get(k2, str)(v)
            if k2 == "HEIGHT" and o[k2] <= 0:
                del o[k2]
            if k2 == "ORIENT" and o[k2] <= 0:
                del o[k2]
    o["layer"] = layer
    return o


def buoy_beacon(p, kind):
    BXX_FIELDS = BOY_FIELDS if kind == "buoy" else BCN_FIELDS
    o = translate(p, BXX_FIELDS, "BOY/BCN")

    c = o.get("COLOUR", "")
    l = "BOY" if kind == "buoy" else "BCN"
    if any(i in c for i in "34"):  # red/green
        l += "LAT"
    elif all(i in c for i in "26"):  # black/yellow
        l += "CAR"
    elif all(i in c for i in "23"):  # black/red
        l += "ISD"
    elif all(i in c for i in "13"):  # red/white
        l += "SAW"
    else:
        l += "SPP"
    o["layer"] = l

    return o


def topmark(p):
    o = translate(p, TOP_FIELDS, "TOPMAR")
    return o


def light(p):
    o = translate(p, LIGHT_FIELDS, "LIGHTS")
    return o


def sector(p, i):
    fields = {}
    for k1, k2 in SECT_FIELDS.items():
        k1 = k1.replace("A", f"{i}")
        k1 = k1.replace("B", f"{i + 1}")
        fields[k1] = k2
    o = translate(p, fields, "LIGHTS")
    return o


def feature(props, lon, lat):
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": props,
    }


def main():
    parser = ArgumentParser(
        description="converter for vaarwegmarkeringen",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", help="input file (json)")
    parser.add_argument(
        "output", help="output file (json), overwrite input if omitted", nargs="?"
    )
    args = parser.parse_args()

    kind = "buoy" if "drijvend" in args.input else "beacon"

    features = []

    for f in track(load_json(args.input)["features"], "converting"):
        # print(f)

        g = f["geometry"]
        p = f["properties"]
        ll = p["x_wgs84"], p["y_wgs84"]
        # print(g)

        o = buoy_beacon(p, kind)
        # print(o)
        if len(o) > 1:
            features.append(feature(o, *ll))

        o = topmark(p)
        # print(o)
        if len(o) > 1:
            features.append(feature(o, *ll))

        o = light(p)
        # print(o)
        if "COLOUR" in o:
            features.append(feature(o, *ll))
        # assert 'ORIENT' not in o,f

        if "COLOUR" not in o or 1:
            for i in range(1, 16):
                o = sector(p, i)
                if "COLOUR" in o and o["COLOUR"] not in "27":
                    features.append(feature(o, *ll))
                else:
                    break
                # print(i,o)
            # assert i==1

        # for f in features: print(f)
        # assert 0

    save_json(
        args.output or args.input, {"type": "FeatureCollection", "features": features}
    )


if __name__ == "__main__":
    main()
