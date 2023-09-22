S57 = {
    "COLOUR": {
        1: "white",
        2: "black",
        3: "red",
        4: "green",
        6: "yellow",
        7: "grey",
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
    "TOPSHP": {
        1: "cone, point up",  # starboard
        2: "cone, point down",
        3: "sphere",  # safe water
        4: "2 spheres",  # isolated danger
        5: "cylinder",  # port
        7: "x-shape",
        10: "2 cones point together",  # west
        11: "2 cones base together",  # east
        13: "2 cones up",  # north
        14: "2 cones down",  # south
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
        14: "FLFl",
        15: "OcFl",
        16: "FLFl",
        17: "OcAlt",
        18: "LFlAlt",
        19: "FlAlt",
        25: "Q+LFl",
        26: "VQ+LFl",
        27: "UQ+LFl",
        28: "Al",
        29: "F+FlAlt",
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
}


def s57toOSM(attr, value):
    if isinstance(value, dict):
        return s57toOSM(attr, value[attr])
    return S57[attr.upper()][value]
