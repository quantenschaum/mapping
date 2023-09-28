# https://wiki.openstreetmap.org/wiki/Seamarks/Seamark_Attributes
S57 = {
    "COLOUR": {
        1: "white",
        2: "black",
        3: "red",
        4: "green",
        5: "blue",
        6: "yellow",
        7: "grey",
        8: "brown",
        9: "amber",
        10: "violet",
        11: "orange",
        12: "magenta",
        13: "pink",
    },
    "BOYSHP": {
        1: "conical",
        2: "can",
        3: "spherical",
        4: "pillar",
        5: "spar",
        6: "barrel",
        7: "super-buoy",
    },
    "BCNSHP": {
        # 1: "post",
        1: None,
        2: "withy",
        3: "tower",
        4: "pile",
        5: "lattice",
        6: "cairn",
        7: "buoyant",
    },
    "TOPSHP": {
        1: "cone, point up",  # starboard
        2: "cone, point down",
        3: "sphere",  # safe water
        4: "2 spheres",  # isolated danger
        5: "cylinder",  # port
        7: "x-shape",
        10: "2 cones point together",  # west
        11: "2 cones base together",  # east
        12: "rhombus",  # east
        13: "2 cones up",  # north
        14: "2 cones down",  # south
        19: "square",
        20: "rectangle, horizontal",
        21: "rectangle, vertical",
        22: "trapezium, up",
        23: "trapezium, down",
        24: "triangle, point up",
        25: "triangle, point down",
        98: "cylinder over sphere",
        99: "cone, point up over sphere",
    },
    "LITCHR": {
        1: "F",
        2: "Fl",
        3: "LFl",
        4: "Q",
        5: "VQ",
        6: "UQ",
        7: "Iso",
        8: "Oc",
        9: "IQ",
        10: "IVQ",
        11: "IUQ",
        12: "Mo",
        13: "FFl",
        14: "FlLFl",
        15: "OcFl",
        16: "FLFl",
        17: "Al.Oc",
        18: "Al.LFl",
        19: "Al.Fl",
        20: "Al.Gr",
        25: "Q+LFl",
        26: "VQ+LFl",
        27: "UQ+LFl",
        28: "Al",
        29: "Al.FFl",
    },
    "CATLIT": {
        1: "directional",
        4: "leading",
        5: "aero",
        6: "air_obstruction",
        7: "fog_detector",
        8: "floodlight",
        9: "strip_light",
        10: "subsidiary",
        11: "spotlight",
        12: "front",
        13: "rear",
        14: "lower",
        15: "upper",
        16: "moire",
        17: "emergency",
        18: "bearing",
        19: "horizontal",
        20: "vertical",
    },
    "WATLEV": {
        2: "dry",
        3: "submerged",
        4: "covers",
        5: "awash",
    },
    "CATWRK": {
        1: "non-dangerous",
        2: "dangerous",
        3: "distributed_remains",
        4: "mast_showing",
        5: "hull_showing",
    },
    "CATOBS": {
        1: "stump",
        2: "wellhead",
        3: "diffuser",
        4: "crib",
        5: "fish_haven",
        6: "foul_area",
        7: "foul_ground",
        8: "ice_boom",
        9: "ground_tackle",
        10: "boom",
    },
    "NATSUR": {
        1: "mud",
        2: "clay",
        3: "silt",
        4: "sand",
        5: "stones",
        6: "gravel",
        7: "pebbles",
        8: "cobbles",
        9: "rocky",
        11: "lava",
        14: "coral",
        17: "shells",
        18: "boulders",
    },
    "NATQUA": {
        1: "fine",
        2: "medium",
        3: "coarse",
        4: "broken",
        5: "sticky",
        6: "soft",
        7: "stiff",
        8: "volcanic",
        9: "calcareous",
        10: "hard",
    },
    "CATWED": {
        1: "kelp",
        2: "sea_weed",
        3: "sea_grass",
        4: "sargasso",
    },
    "CATLAM": {
        1: "port",
        2: "starboard",
        3: "preferred_channel_starboard",
        4: "preferred_channel_port",
    },
    "CATCAM": {
        1: "north",
        2: "east",
        3: "south",
        4: "west",
    },
    "COLPAT": {
        1: "horizontal",
        2: "vertical",
        3: "diagonal",
        4: "squared",
        5: "stripes",
        6: "border",
    },
    "CATSPM": {
        1: "firing_danger_area",
        2: "target",
        3: "marker_ship",
        4: "degaussing_range",
        8: "outfall",
        9: "odas",
        6: "cable",
        7: "spoil_ground",
        10: "recording",
        12: "recreation_zone",
        14: "mooring",
        16: "leading",
        17: "measured_distance",
        18: "notice",
        19: "tss",
        20: "anchoring",
        27: "warning",
        39: "pipeline",
        40: "anchorage",
        41: "clearing",
        42: "control",
        44: "refuge_beacon",
        45: "foul_ground",
        46: "yachting",
        50: "no_entry",
        52: "unknown_purpose",
        55: "marine_farm",
    },
    "STATUS": {
        1: "permanent",
        2: "occasional",
        3: "recommended",
        4: "not_in_use",
        5: "intermittent",
        6: "reserved",
        7: "temporary",
        8: "private",
        9: "mandatory",
        11: "extinguished",
        12: "illuminated",
        13: "historic",
        14: "public",
        15: "synchronized",
        16: "watched",
        17: "unwatched",
        18: "existence_doubtful",
    },
    "LITVIS": {
        1: "high",
        2: "low",
        3: "faint",
        4: "intensified",
        5: "unintensified",
        6: "restricted",
        7: "obscured",
        8: "part_obscured",
    },
    "EXCLIT": {
        1: "24h",
        2: "day",
        3: "fog",
        4: "night",
    },
    "VERDAT": {
        1: "mlws",
        2: "mllws",
        3: "msl",
        4: "llw",
        5: "mlw",
        6: "llws",
        7: "amlws",
        8: "islw",
        9: "lws",
        10: "alat",
        11: "nllw",
        12: "mllw",
        13: "lw",
        14: "amlw",
        15: "amllw",
        16: "mhw",
        17: "mhws",
        18: "hw",
        19: "amsl",
        20: "hws",
        21: "mhhw",
        22: "eslw",
        23: "lat",
        24: "ld",
        25: "igld1985",
        26: "mwl",
        27: "llwlt",
        28: "hhwlt",
        29: "nhhw",
        30: "hat",
    },
    "CATMOR": {
        1: "dophin",
        2: "deviation_dolphin",
        3: "bollard",
        4: "wall",
        5: "post",
        6: "chain",
        7: "buoy",
    },
    "MARSYS": {
        1: "iala-a",
        2: "iala-b",
    },
    "LNAM": None,
    "OBJNAM": None,
    "SORIND": None,
    "SORDAT": None,
    "INFORM": None,
    "PERSTA": None,
    "PEREND": None,
    "SECTR1": None,
    "SECTR2": None,
    "ORIENT": None,
    "MLTYLT": None,
    "VALNMR": None,
    "SIGGRP": lambda s: s.replace("(1)", "").replace("(", "").replace(")", "") or None,
    "SIGPER": None,
    "SIGSEQ": None,
    "HEIGHT": None,
    "ELEVAT": None,
}

S57keys = {
    "objnam": "seamark:name",
    "lnam": "seamark:lnam",
    "colour": "seamark:{typ}:colour",
    # buoys/beacons
    "boyshp": "seamark:{typ}:shape",
    "bcnshp": "seamark:{typ}:shape",
    "topshp": "seamark:{typ}:shape",
    "catlam": "seamark:{typ}:category",
    "catspm": "seamark:{typ}:category",
    "catcam": "seamark:{typ}:category",
    "colpat": "seamark:{typ}:colour_pattern",
    "marsys": "seamark:{typ}:system",
    # lights
    "catlit": "seamark:{typ}:category",
    "litchr": "seamark:{typ}:character",
    "siggrp": "seamark:{typ}:group",
    "sigper": "seamark:{typ}:period",
    "sigseq": "seamark:{typ}:sequence",
    "height": "seamark:{typ}:height",
    "verdat": "seamark:{typ}:vertical_datum",
    "valnmr": "seamark:{typ}:range",
    "sectr1": "seamark:{typ}:sector_start",
    "sectr2": "seamark:{typ}:sector_end",
    "orient": "seamark:{typ}:orientation",
    "litvis": "seamark:{typ}:visibility",
    "exclit": "seamark:{typ}:exhibition",
    "mltylt": "seamark:{typ}:multiple",
    # other/general
    "catmor": "seamark:{typ}:category",
    "elevat": "seamark:{typ}:elevation",
    "status": "seamark:{typ}:status",
    "persta": "seamark:period_start",
    "perend": "seamark:period_end",
    # "inform": "seamark:description",
    # "sorind": "seamark:source",
    # "sordat": "seamark:source_date",
}

S57types = {
    "BOYLAT": "buoy_lateral",
    "BOYCAR": "buoy_cardinal",
    "BOYSAW": "buoy_safe_water",
    "BOYISD": "buoy_isolated_danger",
    "BOYSPP": "buoy_special_purpose",
    "BCNLAT": "beacon_lateral",
    "BCNCAR": "beacon_cardinal",
    "BCNSAW": "beacon_safe_water",
    "BCNISD": "beacon_isolated_danger",
    "BCNSPP": "beacon_special_purpose",
}


var_tags = set(k for k in S57keys.values() if "{typ}" in k)


def s57attr(attr, value):
    try:
        if isinstance(value, dict):
            return s57attr(attr, value[attr])
        try:
            if "," in value:
                return ";".join(s57attr(attr, c.strip()) for c in value.split(","))
        except:
            pass
        a = attr.upper()
        value = cleanup(value)
        try:
            return S57[a](value)
        except:
            pass
        return S57[a][int(value)] if S57[a] else value
    except Exception as x:
        raise Exception(x, attr, value)


def cleanup(s):
    is_str = isinstance(s, str)
    s = s.strip() if is_str else s
    try:
        if is_str:
            v = float(s)
            return str(int(v) if int(v) == v else v)
    except:
        pass
    return s


def s57type(props):
    if "catmor" in props:
        return "mooring"
    if "topshp" in props:
        return "topmark"
    if any(k in props for k in ("boyshp", "bcnshp", "beacon_type")):
        bb = "buoy" if "boyshp" in props else "beacon"
        if "catlam" in props:
            return bb + "_lateral"
        if "catcam" in props:
            return bb + "_cardinal"
        if "catspm" in props:
            return bb + "_special_purpose"
        # otherwise decide by color
        col = s57attr("colour", props)
        if "yellow" in col or "grey" in col:
            return bb + "_special_purpose"
        if "black" in col and "red" in col:
            return bb + "_isolated_danger"
        if "white" in col and "red" in col and col.count(";") == 1:
            return bb + "_safe_water"
        if "green" in col or "red" in col:
            return bb + "_lateral"
    if any(k in props for k in ("litchr", "litvis", "catlit", "light_type")):
        return "light"
    assert 0, props


def s57cat(props):
    for k, t in S57keys.items():
        if t.endswith("category") and props.get(k):
            return s57attr(k, props)
    # otherwise decide by type and color
    if props.get("colour"):
        typ = s57type(props)
        col = s57attr("colour", props)
        if "cardinal" in typ:
            if col == "black;yellow":
                return "north"
            elif col == "black;yellow;black":
                return "east"
            elif col == "yellow;black":
                return "south"
            elif col == "yellow;black;yellow":
                return "west"
        if "lateral" in typ:
            if col.startswith("green"):
                if "red" in col:
                    if col.count(";") > 2:
                        return "channel_separation"
                    else:
                        return "preferred_channel_port"
                elif "white" in col:
                    return "danger_left"
                else:
                    assert col.count(";") == 0
                    return "starboard"
            elif col.startswith("red"):
                if "green" in col:
                    if col.count(";") > 2:
                        return "channel_separation"
                    else:
                        return "preferred_channel_starboard"
                elif "white" in col:
                    return "danger_right"
                else:
                    assert col.count(";") == 0
                    return "port"


def s57translate(props):
    typ = s57type(props)
    tags = {"seamark:type": typ}
    for k, t in S57keys.items():
        v = props.get(k)
        if v:
            w = s57attr(k, v)
            t = t.format(typ=typ)
            # print(k, "=", v, "-->", t, "=", w)
            assert t not in tags, props
            tags[t] = w
    tags[f"seamark:{typ}:category"] = s57cat(props)
    return tags


def update_nc(d1, d2):
    for k, v in d2.items():
        if k not in d1:
            d1[k] = v


def add_tags(tags, props):
    try:
        props = props["properties"]
    except:
        pass
    update_nc(tags, s57translate(props))


def fill_types(tags):
    typ = tags["seamark:type"]
    for t in S57types.values():
        if t == typ:
            continue
        for k in var_tags:
            k = k.format(typ=t)
            if k not in tags:
                tags[k] = None


def add_generic_topmark(tags):
    typ = tags["seamark:type"]
    cat = tags.get(f"seamark:{typ}:category")
    tm = {}
    if typ == "buoy_safe_water":
        tm["seamark:topmark:colour"] = "red"
        tm["seamark:topmark:shape"] = s57attr("topshp", 3)
    elif typ == "buoy_isolated_danger":
        tm["seamark:topmark:colour"] = "black"
        tm["seamark:topmark:shape"] = s57attr("topshp", 4)
    elif typ == "buoy_cardinal":
        tm["seamark:topmark:colour"] = "black"
        if cat == "north":
            tm["seamark:topmark:shape"] = s57attr("topshp", 13)
        if cat == "south":
            tm["seamark:topmark:shape"] = s57attr("topshp", 14)
        if cat == "east":
            tm["seamark:topmark:shape"] = s57attr("topshp", 11)
        if cat == "west":
            tm["seamark:topmark:shape"] = s57attr("topshp", 10)
    update_nc(tags, tm)


def add_system(tags):
    typ = tags["seamark:type"]
    if "lateral" in typ:
        k = f"seamark:{typ}:system"
        if k not in tags:
            col = tags.get(f"seamark:{typ}:colour")
            cat = tags.get(f"seamark:{typ}:category")
            if cat and (col.count(";") % 2 or "danger" in cat or "separation" in cat):
                tags[k] = "cevni"
            else:
                x = (
                    "a"
                    if (cat == "port" and col.startswith("red"))
                    or (cat == "starboard" and col.startswith("green"))
                    or (cat == "preferred_channel_port" and col.startswith("green"))
                    or (cat == "preferred_channel_starboard" and col.startswith("red"))
                    else "b"
                )
                tags[k] = f"iala-{x}"
