#!/usr/bin/env python3

import sqlite3
import argparse
from datetime import datetime
from os.path import isfile, exists
from os import remove, makedirs
from shutil import rmtree
from argparse import ArgumentDefaultsHelpFormatter


def main():
    parser = argparse.ArgumentParser(
        description="Converts mbtiles to sqlitedb for use with OsmAnd",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "input", help="input file (omit for empty file)", metavar="mbtiles", nargs="*"
    )
    parser.add_argument("output", help="output file", metavar="sqlitedb")
    parser.add_argument("-f", "--force", action="store_true", help="overwrite output")
    parser.add_argument("-a", "--append", action="store_true", help="append to output")
    # parser.add_argument("-t", "--time", action="store_true", help="add time column")
    parser.add_argument("-z", "--min-zoom", type=int, help="min zoom level", default=5)
    parser.add_argument("-Z", "--max-zoom", type=int, help="max zoom level", default=18)
    parser.add_argument(
        "-c", "--min-convert", type=int, help="min zoom level to convert", default=5
    )
    parser.add_argument(
        "-C", "--max-convert", type=int, help="max zoom level to convert", default=18
    )
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
        "-y", "--invert-y", action="store_true", help="invert the y tile number"
    )
    parser.add_argument(
        "-Y",
        "--inverted-y",
        action="store_true",
        help="set inverted y flag for sqlitedb",
    )
    parser.add_argument("--format", help="tile format for mbtiles", default="png")
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
    )
    args = parser.parse_args()

    inputs = args.input
    for f in inputs:
        assert isfile(f), f"{f} not found"

    output = args.output
    is_dir = output.endswith("/")

    assert output not in inputs, "output=input"

    if exists(output) and args.force:
        print("deleting", output)
        if is_dir:
            rmtree(output)
        else:
            remove(output)

    assert (
        not exists(output) or args.append
    ), f"{output} exists, overwrite with -f or append with -a (directory only)"

    if args.invert_y:
        print("invert y")

    if is_dir:
        mbtiles2dir(inputs, output, args)
    elif output.endswith(".mbtiles"):
        mbtiles2mbtiles(inputs, output, args)
    elif output.endswith(".sqlitedb"):
        mbtiles2sqlitedb(inputs, output, args)
    else:
        assert 0, f"cannot handle {output}"


def write(filename, data):
    with open(filename, "wb") as f:
        f.write(data)


MOZILLA = "Mozilla/5.0 AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"


def mbtiles2sqlitedb(inputs, output, args):
    assert not output.endswith("/")
    print("writing to", output)
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

    now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)

    i = 0
    for input in inputs:
        print("reading", input)
        source = sqlite3.connect(input)
        for row in source.execute(
            "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles"
        ):
            z, x, y = int(row[0]), int(row[1]), int(row[2])
            if args.invert_y:
                y = 2**z - 1 - y
            if z < args.min_convert or z > args.max_convert:
                continue
            data = [x, y, z, 0, sqlite3.Binary(row[3])]
            if timecol:
                data.append(now)
            i += 1
            insert = f"INSERT OR REPLACE INTO tiles VALUES (?,?,?,?,?{',?' if timecol else ''})"
            dcur.execute(insert, data)
        source.close()
    if i:
        print("copied", i, "tiles")

    dest.commit()
    dest.close()


def mbtiles2dir(inputs, output, args):
    assert output.endswith("/")
    print("writing to", output)

    i = 0
    for input in inputs:
        print("reading", input)
        source = sqlite3.connect(input)
        for row in source.execute(
            "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles"
        ):
            z, x, y = int(row[0]), int(row[1]), int(row[2])
            if args.invert_y:
                y = 2**z - 1 - y
            if z < args.min_convert or z > args.max_convert:
                continue
            dir = f"{output}/{z}/{x}"
            makedirs(dir, exist_ok=1)
            write(f"{dir}/{y}.png", row[3])
        source.close()
    if i:
        print("copied", i, "tiles")


def mbtiles2mbtiles(inputs, output, args):
    assert not output.endswith("/")
    print("writing to", output)
    dest = sqlite3.connect(output)
    dcur = dest.cursor()
    dcur.execute("CREATE TABLE metadata (name text, value text);")
    dcur.execute(
        "CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob);"
    )
    dcur.execute(
        "CREATE UNIQUE INDEX tile_index on tiles (zoom_level, tile_column, tile_row);"
    )
    name = args.title or inputs[0]
    dcur.execute(f"INSERT INTO metadata VALUES ('name','{name}')")
    dcur.execute(f"INSERT INTO metadata VALUES ('format','{args.format}')")
    for m in args.meta or []:
        k, v = m.split("=", 1)
        dcur.execute(f"INSERT INTO metadata VALUES ('{k}','{v}')")

    i = 0
    for input in inputs:
        print("reading", input)
        source = sqlite3.connect(input)
        for row in source.execute(
            "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles"
        ):
            z, x, y = int(row[0]), int(row[1]), int(row[2])
            if args.invert_y:
                y = 2**z - 1 - y
            if z < args.min_convert or z > args.max_convert:
                continue

            dcur.execute(
                "INSERT OR REPLACE INTO tiles VALUES (?,?,?,?)",
                [z, x, y, sqlite3.Binary(row[3])],
            )

        source.close()
    if i:
        print("copied", i, "tiles")

    dest.commit()
    dest.close()


if __name__ == "__main__":
    main()
