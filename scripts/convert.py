#!/usr/bin/env python3

import glob
import re
import sqlite3
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from datetime import datetime
from io import BytesIO
from math import atan, degrees, pi, sinh
from os import makedirs, remove
from os.path import exists, isdir
from shutil import rmtree

from PIL import Image, ImageColor

try:
    import pillow_avif
except:
    pass

from functools import partial

from rich import print
from rich.console import Console
from rich.progress import track
from rich.traceback import install

try:
    from rich_argparse import (
        ArgumentDefaultsRichHelpFormatter as ArgumentDefaultsHelpFormatter,
    )
except:
    pass
# console=Console()
# if console.is_terminal:
#   print=console.log
#   track=partial(track,console=console)
#   install()


def main():
    parser = ArgumentParser(
        description="Converts mbtiles to sqlitedb for use with OsmAnd",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("input", help="input files", nargs="*")
    parser.add_argument("output", help="output file")
    parser.add_argument("-f", "--force", action="store_true", help="overwrite output")
    parser.add_argument("-C", "--reencode", action="store_true", help="reencode tiles")
    parser.add_argument(
        "-O", "--remove-transparency", action="store_true", help="remove transparency"
    )
    parser.add_argument("-a", "--append", action="store_true", help="append to output")
    # parser.add_argument("-t", "--time", action="store_true", help="add time column")
    parser.add_argument("-z", "--min-zoom", type=int, help="min zoom level", default=5)
    parser.add_argument("-Z", "--max-zoom", type=int, help="max zoom level", default=20)
    parser.add_argument("-t", "--title", help="map name or title")
    parser.add_argument(
        "-u",
        "--url",
        help="map tiles URL ({0}=z, {1}=x, {2}=y, {rnd}=random from list)",
    )
    parser.add_argument(
        "-r", "--randoms", help="values for {rnd} variable, comma separated"
    )
    parser.add_argument(
        "-R", "--referer", help="referer header to send with requests to URL"
    )
    parser.add_argument(
        "-A", "--agent", help="user-agent header to send with requests to URL"
    )
    parser.add_argument(
        "-m", "--mozilla", action="store_true", help="set user-agent to mozilla"
    )
    parser.add_argument(
        "-y",
        "--invert-y",
        action="store_true",
        help="invert the y tile number to convert XYZ<-->TMS, see https://t1p.de/u4nvc, use for mbtiles from mapproxy",
    )
    parser.add_argument(
        "-Y",
        "--inverted-y",
        action="store_true",
        help="set inverted y flag for sqlitedb (sets flag only, -y causes actual inversion)",
    )
    parser.add_argument("-F", "--format", help="tile format for mbtiles")
    parser.add_argument(
        "-I", "--indexed", help="used indexed palette 256 color", action="store_true"
    )
    parser.add_argument(
        "-P",
        "--palette",
        help="predefined colors in palette for indexed mode",
        type=lambda s: s.split(","),
    )
    parser.add_argument(
        "-e",
        "--elliptic",
        action="store_true",
        help="use elliptic mercartor (yandex) instead of webmercartor (osm)",
    )
    parser.add_argument(
        "-x", "--expire", type=int, help="expire tiles this many minutes (implies -T)"
    )
    parser.add_argument("-T", "--timecol", action="store_true", help="add time column")
    parser.add_argument(
        "-M",
        "--meta",
        help="additional metadata for mbtiles (key=value)",
        action="append",
        default=[],
    )
    parser.add_argument(
        "-s",
        "--min-size",
        help="minimal size in bytes of tile required to include the tile",
        type=int,
        default=0,
    )
    parser.add_argument(
        "-X",
        "--exclude-transparent",
        help="exclude fully transparent tiles",
        action="store_true",
    )
    parser.add_argument(
        "-c",
        "--transparent",
        metavar="RRGGBB",
        help="color to replace with transparency",
    )
    parser.add_argument("--west", help="western limit", type=float)
    parser.add_argument("--east", help="eastern limit", type=float)
    parser.add_argument("--south", help="southern limit", type=float)
    parser.add_argument("--north", help="northern limit", type=float)
    parser.add_argument(
        "-i",
        "--info",
        help="display file info",
        action="store_true",
    )
    args = parser.parse_args()

    inputs = args.input
    in_dir = inputs and inputs[0].endswith("/")
    for f in inputs:
        assert exists(f), f"{f} not found"

    output = args.output
    out_dir = output.endswith("/")

    assert output not in inputs, "output=input"

    if args.info:
        info(output, args)
        return

    assert (
        not all(x is not None for x in [args.west, args.east]) or args.west < args.east
    )
    assert (
        not all(x is not None for x in [args.south, args.north])
        or args.south < args.north
    )

    if exists(output) and args.force:
        print("deleting", output)
        if out_dir:
            rmtree(output)
        else:
            remove(output)

    assert not exists(output) or args.append, (
        f"{output} exists, overwrite with -f or append with -a (directory only)"
    )

    if args.invert_y:
        print("invert y")

    if out_dir:
        mbtiles2dir(inputs, output, args)
    elif output.endswith(".mbtiles"):
        if in_dir:
            dir2mbtiles(inputs, output, args)
        else:
            mbtiles2mbtiles(inputs, output, args)
    elif output.endswith(".sqlitedb"):
        mbtiles2sqlitedb(inputs, output, args)
    else:
        assert 0, f"cannot handle {output}"


def write(filename, data):
    with open(filename, "wb") as f:
        f.write(data)


def read(filename):
    with open(filename, "rb") as f:
        return f.read()


def lat_lon(z, x, y):
    n = 2**z
    lon = x / n * 360 - 180
    if y < 0:
        y = 2**z - 1 + y
    lat = degrees(atan(sinh(pi * (1 - 2 * y / n))))
    return lat, lon


def in_bbox(z, x, y, args):
    a, b = args.min_zoom, args.max_zoom
    if a is not None and z < a:
        return False
    if b is not None and z > b:
        return False
    lat, lon = lat_lon(z, x, y)
    w, e, s, n = args.west, args.east, args.south, args.north
    if w is not None and lon < w:
        return False
    if e is not None and lon > e:
        return False
    if s is not None and lat < s:
        return False
    if n is not None and lat > n:
        return False
    return True


def update_bbox(bbox, z, x, y):
    lat, lon = lat_lon(z, x, y)
    for k, v in [("z", z), ("x", lon), ("y", lat)]:
        for c, f in [(str.lower, min), (str.upper, max)]:
            bbox[c(k)] = f(bbox.get(c(k), v), v)
    return bbox


def is_transparent(data, args):
    if not args.exclude_transparent:
        return False
    with Image.open(BytesIO(data)) as img:
        if not img.mode.startswith("RGB"):
            return False
        # assert img.mode == "RGBA", img.mode
        extrema = img.getextrema()
        # return img.mode == "RGBA" and extrema[3][1] == 0
        # print(img.mode,img.size,extrema)
        return img.mode == "RGBA" and extrema[3][1] == 0  # transparent
        # or all(extrema[i][0]==255 for i in range(3)) # white
        # or all(extrema[i][1]==0 for i in range(3))) # black
        # all(extrema[i][0]==extrema[i][1] for i in range(len(img.mode))) # uniform


def img2bytes(img, format="png", **kwargs):
    b = BytesIO()
    if format == "avif":
        img.save(b, format=format, **kwargs)
        # img.save(b,format=format,codec="svt",**kwargs) # export SVT_LOG=1
    else:
        img.save(b, format=format, lossless=True, optimize=True, **kwargs)
    b.seek(0)
    return b.read()


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def palette(colors):
    pal = Image.new("P", (1, 1))
    pal.putpalette([v for c in colors for v in hex_to_rgb(c)])
    # return pal.palette.colors
    return pal


def quantize(img, fixed_colors=[], colors=256):
    if not fixed_colors or "A" in img.mode:
        return img.quantize(colors)
    n = len(fixed_colors)
    pal = palette(fixed_colors)
    if colors - n:
        imq = img.quantize(colors - n)
        pal.putpalette(pal.getpalette() + imq.getpalette())
    return img.quantize(colors, palette=pal)


def recode(tile, format, args):
    "reencode tile in given format"
    transparent = args.transparent
    assert format or not transparent, "need format when setting transparency"
    if not format:
        return tile
    if format == "jpg":
        format = "jpeg"
    if transparent:
        assert format != "jpeg", "jpeg does not support transparency"
        transparent = ImageColor.getcolor("#" + transparent, "RGB")
    with Image.open(BytesIO(tile)) as img:
        if (
            img.format == format.upper()
            and not transparent
            and not args.reencode
            and not args.indexed
        ):
            return tile
        # print(img.format,img.size,img.info)
        if args.remove_transparency:
            img = img.convert("RGB")
        if img.mode != "RGBA" and "transparency" in img.info:
            img = img.convert("RGBA")
        if transparent:
            img = make_transparent(img, transparent)
        if format == "jpeg" and img.mode != "RGB":
            img = img.convert("RGB")
        if img.mode == "RGBA" and img.getextrema()[3][0] == 255:
            img = img.convert("RGB")  # remove unused transparency
        if args.indexed:
            img = quantize(img, args.palette)
        # print(img.format,"->",format,len(tile),len(img2bytes(img,format,**kwargs)))
        # print(img.info,img.mode)
        return img2bytes(img, format)


def make_transparent(img, col):
    "make color `col` transparent"
    import numpy as np

    if img.mode != "RGBA":
        img = img.convert("RGBA")
    data = np.array(img)  # "data" is a height x width x 4 numpy array
    r, g, b, a = data.T  # Temporarily unpack the bands for readability
    mask = (r == col[0]) & (g == col[1]) & (b == col[2])
    if not mask.any():
        return img
    data[..., -1][mask.T] = 0  # Transpose back needed
    return Image.fromarray(data)


def skip(z, x, y, img, args):
    return (
        not in_bbox(z, x, y, args)
        or len(img) < args.min_size
        or is_transparent(img, args)
    )


MOZILLA = "Mozilla/5.0 AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"


def mbtiles_format(filename):
    db = sqlite3.connect(filename)
    cur = db.cursor()
    r = cur.execute("SELECT value FROM metadata WHERE name = 'format'").fetchone()
    db.close()
    return r[0] if r else None


def fmt(tile):
    with Image.open(BytesIO(tile)) as img:
        return img.format.lower()


def info(filename, args):
    db = sqlite3.connect(filename)
    cur = db.cursor()
    print("METADATA")
    for r in cur.execute("SELECT * FROM metadata"):
        print(r[0], "=", r[1])
    print("TILES")
    print("  z    count        size")
    for r in cur.execute(
        "SELECT zoom_level,COUNT(zoom_level),SUM(LENGTH(tile_data)) FROM tiles GROUP BY zoom_level"
    ):
        print(f"{r[0]:3} {r[1]:8} {r[2] / 1e6:8.2f} MB")
    for r in cur.execute(
        "SELECT 'sum',COUNT(zoom_level),SUM(LENGTH(tile_data)),AVG(LENGTH(tile_data)) FROM tiles"
    ):
        print(f"{r[0]:3} {r[1]:8} {r[2] / 1e6:8.2f} MB {r[3] / 1e3:8.2f} kB/tile")
    db.close()


def pbar(iter, m=0):
    if isinstance(m, sqlite3.Connection):
        m = m.execute("SELECT COUNT(zoom_level) FROM tiles").fetchone()[0]
    else:
        m = len(iter)
    return track(iter, "[green]converting[/]", total=m)
    # return tqdm(iter,total=m,unit='T',unit_scale=True,dynamic_ncols=True)


def mbtiles2mbtiles(inputs, output, args):
    assert not output.endswith("/")
    print("writing", output)
    dest = sqlite3.connect(output)
    dcur = dest.cursor()
    # https://github.com/mapbox/mbtiles-spec/blob/master/1.3/spec.md
    dcur.execute("PRAGMA application_id = 0x4d504258;")
    dcur.execute("CREATE TABLE metadata (name text, value text);")
    dcur.execute("CREATE UNIQUE INDEX meta_index on metadata (name);")
    dcur.execute(
        "CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob);"
    )
    dcur.execute(
        "CREATE UNIQUE INDEX tile_index on tiles (zoom_level, tile_column, tile_row);"
    )
    name = args.title or inputs[0]
    dcur.execute(f"INSERT INTO metadata VALUES ('name','{name}')")
    format = args.format or mbtiles_format(inputs[0])
    print("format", format)
    if format:
        dcur.execute(f"INSERT INTO metadata VALUES ('format','{format}')")

    i, n, b = 0, 0, 0
    bbox = {}
    for input in inputs:
        print("reading", input)
        source = sqlite3.connect(input)
        for row in pbar(
            source.execute(
                "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles"
            ),
            source,
        ):
            n += 1
            z, x, y = int(row[0]), int(row[1]), int(row[2])
            if args.invert_y:
                y = 2**z - 1 - y
            if skip(z, x, -y, row[3], args):
                continue
            tile = recode(row[3], format, args)
            b += len(tile)
            update_bbox(bbox, z, x, -y)
            dcur.execute(
                "INSERT OR REPLACE INTO tiles VALUES (?,?,?,?)",
                [z, x, y, sqlite3.Binary(tile)],
            )
            i += 1

        source.close()
    if i:
        print(f"copied {i}/{n} tiles, {b:,} bytes")
        print(
            f"bounds z={bbox['z']}..{bbox['Z']} x={bbox['x']:.5f}..{bbox['X']:.5f} z={bbox['y']:.5f}..{bbox['Y']:.5f}"
        )

    for m in [
        f"minzoom={bbox['z']}",
        f"maxzoom={bbox['Z']}",
        f"bounds={bbox['x']},{bbox['y']},{bbox['X']},{bbox['Y']}",
    ] + args.meta:
        k, v = m.split("=", 1)
        dcur.execute(f"INSERT OR REPLACE INTO metadata VALUES ('{k}','{v}')")

    dest.commit()
    dest.close()


def mbtiles2sqlitedb(inputs, output, args):
    assert not output.endswith("/")
    print("writing", output)
    dest = sqlite3.connect(output)

    timecol = args.timecol or args.expire

    dcur = dest.cursor()

    dcur.execute(
        "CREATE TABLE info (tilenumbering, minzoom, maxzoom, title TEXT, url TEXT, randoms TEXT, ellipsoid TEXT, inverted_y TEXT, referer TEXT, useragent TEXT, timecolumn TEXT, expireminutes TEXT);"
    )
    dcur.execute(
        "INSERT INTO info VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            "simple",
            args.min_zoom,
            args.max_zoom,
            args.title,
            args.url,
            args.randoms,
            1 if args.elliptic else 0,
            1 if args.inverted_y else 0,
            args.referer,
            MOZILLA if args.mozilla else args.agent,
            "yes" if timecol else "no",
            args.expire or -1,
        ],
    )
    dcur.execute(
        f"CREATE TABLE tiles (x int, y int, z int, s int, image blob, {'time long,' if timecol else ''} PRIMARY KEY (x,y,z,s));"
    )
    dcur.execute("CREATE UNIQUE INDEX IND on tiles (x,y,z,s);")

    now = (
        int((datetime.now() - datetime(1970, 1, 1)).total_seconds() * 1000)
        if timecol
        else None
    )

    format = args.format or (mbtiles_format(inputs[0]) if inputs else None)
    print("format", format)

    i, n, b = 0, 0, 0
    bbox = {}
    for input in inputs:
        print("reading", input)
        source = sqlite3.connect(input)
        for row in pbar(
            source.execute(
                "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles"
            ),
            source,
        ):
            n += 1
            z, x, y = int(row[0]), int(row[1]), int(row[2])
            if not args.invert_y:  # negate due to TMS scheme in mbtiles
                y = 2**z - 1 - y
            if skip(z, x, -y, row[3], args):
                continue
            tile = recode(row[3], format, args)
            b += len(tile)
            data = [x, y, z, 0, sqlite3.Binary(tile)]
            if timecol:
                data.append(now)
            insert = f"INSERT OR REPLACE INTO tiles VALUES (?,?,?,?,?{',?' if timecol else ''})"
            update_bbox(bbox, z, x, y)
            dcur.execute(insert, data)
            i += 1
        source.close()
    if i:
        print(f"copied {i}/{n} tiles, {b:,} bytes")
        print(
            f"bounds z={bbox['z']}..{bbox['Z']} x={bbox['x']:.5f}..{bbox['X']:.5f} z={bbox['y']:.5f}..{bbox['Y']:.5f}"
        )

    dest.commit()
    dest.close()


def mbtiles2dir(inputs, output, args):
    assert output.endswith("/")
    print("writing", output)

    format = args.format or mbtiles_format(inputs[0])
    print("format", format)

    i, n, b = 0, 0, 0
    bbox = {}
    for input in inputs:
        print("reading", input)
        source = sqlite3.connect(input)
        for row in pbar(
            source.execute(
                "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles"
            ),
            source,
        ):
            n += 1
            z, x, y = int(row[0]), int(row[1]), int(row[2])
            if not args.invert_y:  # negate due to TMS scheme in mbtiles
                y = 2**z - 1 - y
            if skip(z, x, -y, row[3], args):
                continue
            tile = recode(row[3], format, args)
            b += len(tile)
            dir = f"{output}/{z}/{x}"
            makedirs(dir, exist_ok=1)
            update_bbox(bbox, z, x, y)
            write(f"{dir}/{y}.{format or fmt(tile)}", tile)
            i += 1
        source.close()
    if i:
        print(f"copied {i}/{n} tiles, {b:,} bytes")
        print(
            f"bounds z={bbox['z']}..{bbox['Z']} x={bbox['x']:.5f}..{bbox['X']:.5f} z={bbox['y']:.5f}..{bbox['Y']:.5f}"
        )


def dir2mbtiles(inputs, output, args):
    assert not output.endswith("/")
    print("writing", output)
    dest = sqlite3.connect(output)
    dcur = dest.cursor()
    # https://github.com/mapbox/mbtiles-spec/blob/master/1.3/spec.md
    dcur.execute("CREATE TABLE metadata (name text, value text);")
    dcur.execute(
        "CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob);"
    )
    dcur.execute(
        "CREATE UNIQUE INDEX tile_index on tiles (zoom_level, tile_column, tile_row);"
    )
    name = args.title or inputs[0]
    dcur.execute(f"INSERT INTO metadata VALUES ('name','{name}')")
    format = args.format
    print("format", format)
    if format:
        dcur.execute(f"INSERT INTO metadata VALUES ('format','{format}')")

    i, n, b = 0, 0, 0
    bbox = {}
    for input in inputs:
        print("reading", input)
        assert isdir(input)
        files = glob.glob(f"{input}*/*/*.*")
        for f in pbar(glob.glob(f"{input}*/*/*.*")):
            m = re.match(r".*/(\d+)/(\d+)/(\d+)\..+", f)
            if m:
                n += 1
                tile = read(f)
                z, x, y = list(map(int, m.groups()))
                # print(f, z, x, y, len(tile), lat_lon(z, x, y))
                if skip(z, x, y, tile, args):
                    continue
                tile = recode(tile, format, args)
                b += len(tile)
                if not args.invert_y:
                    y = 2**z - 1 - y
                update_bbox(bbox, z, x, -y)
                dcur.execute(
                    "INSERT OR REPLACE INTO tiles VALUES (?,?,?,?)",
                    [z, x, y, sqlite3.Binary(tile)],
                )
                i += 1

    if i:
        print(f"copied {i}/{n} tiles, {b:,} bytes")
        print(
            f"bounds z={bbox['z']}..{bbox['Z']} x={bbox['x']:.5f}..{bbox['X']:.5f} z={bbox['y']:.5f}..{bbox['Y']:.5f}"
        )

    for m in [
        f"minzoom={bbox['z']}",
        f"maxzoom={bbox['Z']}",
        f"bounds={bbox['x']},{bbox['y']},{bbox['X']},{bbox['Y']}",
    ] + args.meta:
        k, v = m.split("=", 1)
        dcur.execute(f"INSERT OR REPLACE INTO metadata VALUES ('{k}','{v}')")

    dest.commit()
    dest.close()


if __name__ == "__main__":
    main()
