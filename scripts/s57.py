# https://wiki.openstreetmap.org/wiki/Seamarks/Seamark_Attributes

from collections import OrderedDict
from itertools import groupby
import re

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
        1: None,  # stake, pole, perch, post
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
        6: "board",
        7: "x-shape",
        8: "cross",
        9: "cube, point up",
        10: "2 cones point together",  # west
        11: "2 cones base together",  # east
        12: "rhombus",  # east
        13: "2 cones up",  # north
        14: "2 cones down",  # south
        15: "besom, point up",
        16: "besom, point down",
        19: "square",
        20: "rectangle, horizontal",
        21: "rectangle, vertical",
        22: "trapezium, up",
        23: "trapezium, down",
        24: "triangle, point up",
        25: "triangle, point down",
        28: "t-shape",
        29: "triangle, point up over circle",
        31: "rhombus over circle",
        33: "other",
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
        1: "part-submerged",
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
        # non-standard/inland
        7: "channel_right",
        8: "channel_left",
        10: "channel_separation",
        15: "danger_right",
        16: "danger_left",
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
        # https://wiki.openstreetmap.org/wiki/Seamarks/Special_Purpose_Marks
        1: "firing_danger_area",
        2: "target",
        3: "marker_ship",
        4: "degaussing_range",
        5: "barge",
        6: "cable",
        7: "spoil_ground",
        8: "outfall",
        9: "odas",
        10: "recording",
        11: "seaplane_anchorage",
        12: "recreation_zone",
        13: "private",
        14: "mooring",
        15: "lanby",
        16: "leading",
        17: "measured_distance",
        18: "notice",
        19: "tss",
        20: "anchoring",
        21: "no_berthing",
        22: "no_overtaking",
        23: "no_two-way_traffic",
        24: "reduced_wake",
        25: "speed_limit",
        26: "stop",
        27: "warning",
        28: "sound_ship_siren",
        29: "restricted_vertical_clearance",
        30: "maximum_vessel_draught",
        31: "restricted_horizontal_clearance",
        32: "strong_current",
        33: "berthing",
        34: "overhead_power_cable",
        35: "channel_edge_gradient",
        36: "telephone",
        37: "ferry_crossing",
        # 38:"traffic_lights",
        39: "pipeline",
        40: "anchorage",
        41: "clearing",
        42: "control",
        43: "diving",
        44: "refuge_beacon",
        45: "foul_ground",
        46: "yachting",
        47: "heliport",
        48: "gps",
        49: "seaplane_landing",
        50: "no_entry",
        51: "work_in_progress",
        52: "unknown_purpose",
        53: "wellhead",
        54: "	channel_separation",
        55: "marine_farm",
        56: "artificial_reef",
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
        1: "dolphin",
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
        9: "none",
        10: "other",
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
    "VERLEN": None,
    "MLTYLT": None,
    "VALNMR": None,
    "SIGGRP": lambda s: s.replace("(1)", "").replace("(", "").replace(")", "") or None,
    "SIGPER": None,
    "SIGSEQ": None,
    "SIGFRQ": None,
    "HEIGHT": None,
    "VERACC": None,
    "ELEVAT": None,
    "VALSOU": None,
    "SOUACC": None,
    "QUASOU": {
        1: "known",
        2: "unknown",  # remove depth tag
        3: "doubtful",
        4: "unreliable",
        5: "no_bottom",
        6: "least_depth_known",
        7: "least_depth_unknown",
        8: "not_surveyed",
        9: "not_confirmed",
        10: "maintained",
        11: "not_maintained",
    },
    "EXPSOU": {
        1: "within_range",
        2: "shoaler",
        3: "deeper",
    },
    "TECSOU": {
        1: "echo",
        2: "sonar",
        3: "multi-beam",
        4: "diver",
        5: "lead-line",
        6: "wire-drag",
        7: "laser",
        8: "acoustic",
        9: "electromagnetic",
        10: "photogrammetry",
        11: "satellite_imagery",
        12: "levelling",
        13: "sonar",
        14: "computer_generated",
    },
    "CATSIL": {
        1: "silo",
        2: "tank",
        3: "grain_elevator",
        4: "water_tower",
    },
    "CATLMK": {
        1: "cairn",
        2: "cemetery",
        3: "chimney",
        9: "monument",
        10: "column",
        14: "cross",
        4: "dish_aerial",
        15: "dome",
        5: "flagstaff",
        6: "flare_stack",
        7: "mast",
        11: "memorial",
        12: "obelisk",
        16: "radar_scanner",
        20: "spire",
        13: "statue",
        17: "tower",
        18: "windmill",
        19: "windmotor",
        8: "windsock",
        21: "boulder",
    },
    "BUISHP": {
        5: "high-rise",
        6: "pyramid",
        7: "cylindrical",
        8: "spherical",
        9: "cubic",
    },
    "CATHAF": {
        1: "roro",
        3: "ferry",
        4: "fishing",
        5: "marina",
        #:"marina_no_facilities",
        6: "naval",
        7: "tanker",
        8: "passenger",
        9: "shipyard",
        10: "container",
        11: "bulk",
        12: "syncrolift",
        13: "straddle_carrier",
    },
    "CATOFP": {
        1: "oil",
        2: "production",
        3: "observation",
        4: "alp",
        5: "salm",
        6: "mooring",
        7: "artificial_island",
        8: "fpso",
        9: "accommodation",
        10: "nccb",
    },
    "CATCRN": {
        2: "container",
        3: "sheerlegs",
        4: "travelling",
        5: "a-frame",
    },
    "NATCON": {
        1: "masonry",
        2: "concreted",
        3: "loose_boulders",
        4: "hard-surfaced",
        5: "unsurfaced",
        6: "wooden",
        7: "metal",
        8: "grp",
        9: "painted",
        # :"framework",
    },
    "CATFOG": {
        1: "explosive",
        2: "diaphone",
        3: "siren",
        4: "nautophone",
        5: "reed",
        6: "tyfon",
        7: "bell",
        8: "whistle",
        9: "gong",
        10: "horn",
    },
    "CONRAD": {
        1: "conspicuous",
        2: "not_conspicuous",
        3: "reflector",
    },
    "CONVIS": {
        1: "conspicuous",
        2: "not_conspicuous",
    },
    "CATRTB": {
        1: "ramark",
        2: "racon",
        3: "leading",
    },
    "VALMXR": None,
    "RADWAL": None,
    "CALSGN": None,
    "COMCHA": None,
    "ESTRNG": None,
    "CATSCF": {
        1: "visitor_berth",
        2: "nautical_club",
        3: "boat_hoist",
        4: "sailmaker",
        5: "boatyard",
        6: "public_inn",
        7: "restaurant",
        8: "chandler",
        9: "provisions",
        10: "doctor",
        11: "pharmacy",
        12: "watertap",
        13: "fuelstation",
        14: "electricity",
        15: "bottle_gas",
        16: "showers",
        17: "launderette",
        18: "toilets",
        19: "post_box",
        20: "telephone",
        21: "refuse_bin",
        22: "car_park",
        23: "boat_trailers_park",
        24: "caravan_site",
        25: "camping_site",
        26: "pump-out",
        27: "emergency_telephone",
        28: "slipway",
        29: "visitors_mooring",
        30: "scrubbing_berth",
        31: "picnic_area",
        32: "mechanics_workshop",
        33: "security_service",
    },
    "CATSIW": {
        1: "danger",
        2: "maritime_obstruction",
        3: "cable",
        4: "military",
        5: "distress",
        6: "weather",
        7: "storm",
        8: "ice",
        9: "time",
        10: "tide",
        11: "tidal_stream",
        12: "tide_gauge",
        13: "tide_scale",
        14: "diving",
        15: "water_level_gauge",
    },
    "CATSIT": {
        1: "port_control",
        2: "port_entry_departure",
        3: "ipt",
        4: "berthing",
        5: "dock",
        6: "lock",
        7: "flood_barrage",
        8: "bridge_passage",
        9: "dredging",
        10: "traffic_control",
    },
    "CATPIL": {
        1: "cruising_vessel",
        2: "helicopter",
        3: "from_shore",
    },
    "TRAFIC": {
        1: "inbound",
        2: "outbound",
        3: "one-way",
        4: "two-way",
    },
    "CATROS": {
        1: "omnidirectional",
        2: "directional",
        3: "rotating_pattern",
        4: "consol",
        5: "rdf",
        6: "qtg",
        7: "aeronautical",
        8: "decca",
        9: "loran",
        10: "dgps",
        11: "toran",
        12: "omega",
        13: "syledis",
        14: "chiaka",
    },
    "CATPLE": {
        1: "stake",
        3: "post",
        4: "tripodal",
    },
}

S57keys = {
    "objnam": "seamark:name",
    "lnam": "seamark:lnam",
    "colour": "seamark:{typ}:colour",
    # buoys/beacons
    "boyshp": "seamark:{typ}:shape",
    "bcnshp": "seamark:{typ}:shape",
    "topshp": "seamark:topmark:shape",
    "catlam": "seamark:{typ}:category",
    "catspm": "seamark:{typ}:category",
    "catcam": "seamark:{typ}:category",
    "colpat": "seamark:{typ}:colour_pattern",
    "marsys": "seamark:{typ}:system",
    "natcon": "seamark:{typ}:construction",
    "verlen": "seamark:{typ}:vertical_length",
    "catple": "seamark:pile:category",
    # lights
    "catlit": "seamark:light:category",
    "litchr": "seamark:light:character",
    "siggrp": "seamark:{typ}:group",
    "sigper": "seamark:{typ}:period",
    "sigseq": "seamark:{typ}:sequence",
    "litvis": "seamark:light:visibility",
    "exclit": "seamark:light:exhibition",
    "mltylt": "seamark:light:multiple",
    "height": "seamark:{typ}:height",
    "veracc": "seamark:{typ}:height:accuracy",
    "verdat": "seamark:{typ}:vertical_datum",
    "valnmr": "seamark:{typ}:range",
    "sectr1": "seamark:{typ}:sector_start",
    "sectr2": "seamark:{typ}:sector_end",
    "orient": "seamark:{typ}:orientation",
    # depth
    "valsou": "depth",
    "quasou": "depth:source_quality",
    "souacc": "depth:accuracy",
    "expsou": "depth:exposition",
    "tecsou": "depth:technique",
    "watlev": "seamark:{typ}:water_level",
    "catwrk": "seamark:wreck:category",
    "catobs": "seamark:obstruction:category",
    # seabed
    "natsur": "seamark:seabed_area:surface",
    "natqua": "seamark:seabed_area:quality",
    "catwed": "seamark:weed:category",
    "catseg": "seamark:seagrass:category",
    # landmarks
    "catlmk": "seamark:landmark:category",
    "catsil": "seamark:tank:category",
    "buishp": "seamark:building:shape",
    "catofp": "seamark:platform:category",
    # facilities
    "cathaf": "seamark:harbour:category",
    "catcrn": "seamark:crane:category",
    "catscf": "seamark:small_craft_facility:category",
    # stations
    "catsit": "seamark:signal_station_traffic:category",
    "catsiw": "seamark:signal_station_warning:category",
    "catros": "seamark:radio_station:category",
    "calsgn": "seamark:{typ}:callsign",
    "comcha": "seamark:{typ}:channel",
    "catpil": "seamark:pilot_boarding:category",
    # fog signal
    "catfog": "seamark:fog_signal:category",
    "sigfrq": "seamark:{typ}:frequency",
    # transponder
    "catrtb": "seamark:radar_transponder:category",
    "valmxr": "seamark:{typ}:range",
    "estrng": "seamark:{typ}:range",
    "radwal": "seamark:{typ}:wavelength",
    # other/general
    "conrad": "seamark:{typ}:reflectivity",
    "convis": "seamark:{typ}:conspicuity",
    "catmor": "seamark:mooring:category",
    "trafic": "seamark:{typ}:traffic_flow",
    "elevat": "seamark:{typ}:elevation",
    "status": "seamark:{typ}:status",
    "persta": "seamark:{typ}:period_start",
    "perend": "seamark:{typ}:period_end",
    "inform": "seamark:information",
    # "sorind": "seamark:source",
    # "sordat": "seamark:source_date",
}

S57types = {
    # primary
    "BOYLAT": "buoy_lateral",
    "BOYCAR": "buoy_cardinal",
    "BOYSAW": "buoy_safe_water",
    "BOYISD": "buoy_isolated_danger",
    "BOYSPP": "buoy_special_purpose",
    "BOYINB": "buoy_installation",
    "BCNLAT": "beacon_lateral",
    "BCNCAR": "beacon_cardinal",
    "BCNSAW": "beacon_safe_water",
    "BCNISD": "beacon_isolated_danger",
    "BCNSPP": "beacon_special_purpose",
    "PILPNT": "pile",
    "LNDMRK": "landmark",
    "OFSPLF": "platform",
    "UWTROC": "rock",
    "WRECKS": "wreck",
    "OBSTRN": "obstruction",
    "SBDARE": "seabed_area",
    "HRBFAC": "harbour",
    "SMCFAC": "small_craft_facility",
    # secondary
    "LIGHTS": "light",
    "TOPMAR": "topmark",
    "DAYMAR": "topmark",
    "FOGSIG": "fog_signal",
    "RTPBCN": "radar_transponder",
}

secondary = (
    "LIGHTS",
    "TOPMAR",
    "DAYMAR",
    "FOGSIG",
    "RTPBCN",
)


def is_primary(l):
    return l not in secondary


layers1 = tuple(l for l in S57types.keys() if is_primary(l))
layers2 = tuple(l for l in S57types.keys() if not is_primary(l))

bb_types = set(
    k
    for k in S57keys.values()
    if "{typ}" in k and any(k.startswith(s) for s in ("buoy", "beacon"))
)


def s57attr(attr, value):
    try:
        a = attr.upper()
        if isinstance(value, dict):
            return s57attr(attr, value[attr])
        try:
            if "," in value and S57[a]:
                return ";".join(s57attr(attr, c.strip()) for c in value.split(","))
        except:
            pass
        value = cleanup(value)
        try:
            return S57[a](value)
        except:
            pass
        return S57[a][int(value)] if S57[a] else value
    except Exception as x:
        raise Exception(x, attr, value)


def cleanup(s):
    try:
        s = s.strip()
    except:
        pass
    try:
        v = float(s.replace(",", "."))
        return str(int(v) if int(v) == v else v)
    except:
        pass
    return s


def is_something(props):
    keys = (
        set(S57keys.keys())
        .intersection(props.keys())
        .difference(
            ["objnam", "lnam", "convis", "height", "colour", "inform", "status"]
        )
    )
    return bool(keys)


def s57type(props):
    _type_ = props.get("_type_")
    if _type_:
        return _type_
    # if "rock_type" in props:
    #     return "rock"
    # if "obstruction_type" in props:
    #     return "obstruction"
    if "catobs" in props:
        return "obstruction"
    types = set(
        v.split(":")[1] for k, v in S57keys.items() if v.count(":") == 2 and k in props
    ).difference(["{typ}"])
    if len(types) == 1:
        return list(types)[0]

    if "catsil" in props:
        return "tank"
    if "catpil" in props:
        return "pilot_boarding"
    if "comcha" in props:
        return "radio_station"
    if "calsgn" in props:
        return "radio_station"
    if "buishp" in props:
        return "building"
    if "catwed" in props:
        v = s57attr("catwed", props)
        return "seagrass" if "grass" in v else "weed"
    if any(k in props for k in ("litchr", "litvis", "catlit", "light_type")):
        return "light"
    if any(k in props for k in ("boyshp", "buoy_type", "bcnshp", "beacon_type")):
        bb = "buoy" if "boyshp" in props or "buoy_type" in props else "beacon"
        if "catlam" in props:
            return bb + "_lateral"
        if "catcam" in props:
            return bb + "_cardinal"
        if "catspm" in props:
            return bb + "_special_purpose"
        # otherwise decide by color
        col = s57attr("colour", props) if "colour" in props else ""
        pat = s57attr("colpat", props) if "colpat" in props else ""
        if "yellow" in col and "black" in col:
            return bb + "_cardinal"
        if "yellow" in col or "grey" in col:
            return bb + "_special_purpose"
        if "black" in col and "red" in col:
            return bb + "_isolated_danger"
        if "white" in col and "red" in col and pat == "vertical":
            return bb + "_safe_water"
        if "green" in col or "red" in col:
            return bb + "_lateral"
        if bb == "beacon":
            return bb + "_special_purpose"
    assert 0, (types, props)


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
            # assert t not in tags, (t, props, tags)
            tags[t] = w
    cat = s57cat(props)
    k = f"seamark:{typ}:category"
    if cat and k not in tags:
        tags[k] = cat
    # fix_tags(tags)
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
    return tags


def fill_types(tags):
    typ = smtype(tags)
    for t in S57types.values():
        if t == typ:
            continue
        for k in bb_types:
            k = k.format(typ=t)
            if k not in tags:
                tags[k] = None


def add_generic_topmark(tags):
    typ = smtype(tags)
    cat = tags.get(f"seamark:{typ}:category")
    tm = {}
    for b in ("buoy", "beacon"):
        if typ == f"{b}_safe_water":
            tm["seamark:topmark:colour"] = "red"
            tm["seamark:topmark:shape"] = s57attr("topshp", 3)
        elif typ == f"{b}_isolated_danger":
            tm["seamark:topmark:colour"] = "black"
            tm["seamark:topmark:shape"] = s57attr("topshp", 4)
        elif typ == f"{b}_cardinal":
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
    typ = smtype(tags)
    if "lateral" in typ:
        k = f"seamark:{typ}:system"
        if k not in tags:
            col = tags.get(f"seamark:{typ}:colour")
            cat = tags.get(f"seamark:{typ}:category")
            if not col or not cat:
                return
            if cat and (col.count(";") % 2 or "danger" in cat or "separation" in cat):
                tags[k] = "cevni"
            else:
                tags[k] = (
                    "iala-a"
                    if (cat == "port" and col.startswith("red"))
                    or (cat == "starboard" and col.startswith("green"))
                    or (cat == "preferred_channel_port" and col.startswith("green"))
                    or (cat == "preferred_channel_starboard" and col.startswith("red"))
                    else "iala-b"
                )


shape_replace = {
    "triangle": "cone",
    "square": "cylinder",
    "circle": "sphere",
}


def fix_tags(tags):
    typ = smtype(tags)
    is_bb = "buoy" in typ or "beacon" in typ

    c = f"seamark:{typ}:colour"
    if typ == "buoy_safe_water":
        tags[c] = "red;white"

    c = ":colour"
    for k in tags.keys():
        if k.endswith(c) and ";" in tags[k]:
            cs = list(set(tags[k].split(";")))
            if len(cs) == 1:
                tags[k] = cs[0]

    p = ":colour_pattern"
    for k in tags.keys():
        if k.endswith(p):
            if ";" not in tags.get(k.replace(p, c), ""):
                tags[k] = None

    s = "seamark:topmark:shape"
    if "buoy" in typ and s in tags:
        for k, v in shape_replace.items():
            tags[s] = tags[s].replace(k, v)

    for s in "shape", "reflectivity", "conspicuity":
        s = f"seamark:{typ}:{s}"
        if not tags.get(s, 1):
            del tags[s]

    g = "seamark:seagrass:category"
    if typ == "seagrass" and "grass" in tags.get(g, ""):
        del tags[g]

    s = f"seamark:{typ}:shape"
    if typ == "beacon_lateral" and c not in tags and s not in tags and len(tags) <= 4:
        tags[s] = "perch"

    r = f"seamark:{typ}:reflectivity"
    if tags.get(r) == "reflector":
        tags["seamark:radar_reflector"] = "yes"

    if typ == "pile" and not tags.get("catple"):
        smtype(tags, "beacon_special_purpose")

    i = "seamark:information"
    r = "seamark:radio_station:category"
    if is_bb and "AIS" in tags.get(i, ""):
        tags[r] = "ais"
        m = re.search(r"MMSI\s*(\d+)", tags[i])
        if m:
            tags["seamark:radio_station:mmsi"] = m.groups()[0]

    # q = "depth:source_quality"
    # if tags.get(q) == "unknown":
    #     for k in filter(lambda k: k.startswith("depth"), list(tags.keys())):
    #         del tags[k]

    n = "seamark:name"
    l = "seamark:lnam"
    if (
        len(tags.get(n, "")) > 6
        and is_bb
        and (tags.get(l, "").startswith("022") or tags.get(l, "").startswith("22"))
    ):
        ln = tags[n]
        sn = " ".join(filter(lambda p: not any(l.islower() for l in p), ln.split()))
        if sn:
            tags["seamark:description"] = ln
            tags[n] = sn

    # add_system(tags)


nav_light_categories = (
    "directional",
    "leading",
    "front",
    "rear",
    "lower",
    "upper",
    "moire",
    "bearing",
)

leading_lights = (
    "leading",
    "front",
    "rear",
    "lower",
    "upper",
)


low_light = (
    "fog",
    "low",
    "faint",
    "obscured",
    "part_obscured",
    "occasional",
    "not_in_use",
    "temporary",
    "extinguished",
    "existence_doubtful",
)


def light_order(l):
    p = l.get("seamark:light:category", "")
    c = 0 if any(v in p for v in nav_light_categories) else 30
    r = -float(l.get("seamark:light:range", 0))
    props = "visibility", "exhibition", "status"
    x = [
        10 if any(v in l.get("seamark:light:" + p, "") for v in low_light) else 0
        for p in props
    ]
    return c + r + sum(x)


def smtype(x, t=None):
    if t:
        x["seamark:type"] = t
        return x
    return x["seamark:type"]


def merge_lights(lights):
    if len(lights) == 1:
        return lights[0]
    else:
        merged = {}
        lights = sorted(lights, key=light_order)
        klnam = "seamark:lnam"
        for i, s in enumerate(lights, 1):
            assert smtype(s).startswith("light"), (i, lights)
            si = {k.replace("light:", f"light:{i}:"): v for k, v in s.items()}
            update_nc(merged, si)
        if klnam in merged:
            del merged[klnam]
        return merged


def group_by(data, key=lambda v: v):
    # return dict(groupby(data, key))
    grp = OrderedDict()
    for e in data:
        k = key(e)
        grp[k] = grp.get(k, []) + [e]
    return grp


abbrevs = {
    "permanent": "perm",
    "occasional": "occas",
    "recommended": "rcmnd",
    "not_in_use": "unused",
    "intermittent": "interm",
    "reserved": "resvd",
    "temporary": "temp",
    "private": "priv",
    "mandatory": "mand",
    "extinguished": "exting",
    "illuminated": "illum",
    "historic": "hist",
    "public": "pub",
    "synchronized": "sync",
    "watched": "watchd",
    "unwatched": "unwtchd",
    "existence_doubtful": "ED",
    "high": "high",
    "low": "low",
    "faint": "faint",
    "intensified": "intens",
    "unintensified": "uintens",
    "restricted": "restr",
    "obscured": "obscd",
    "part_obscured": "p.obscd",
    "fog": "fog",
    # "24h": "24h",
    # "night": "night",
    # "day": "day",
}
