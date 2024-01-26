#!/usr/bin/env python3

import sqlite3
import argparse
from datetime import datetime
from os.path import isfile, exists
from os import remove, makedirs
from shutil import rmtree


def main():
    parser = argparse.ArgumentParser(
        description="Converts mbtiles to sqlitedb for use with OsmAnd"
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
    parser.add_argument("-t", "--title", help="map title")
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
        "-y", "--inverted-y", action="store_true", help="inverted y tile number"
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
    args = parser.parse_args()

    inputs = args.input
    for f in inputs:
        assert isfile(f), f"{f} not found"

    output = args.output
    is_dir = output.endswith("/")
    ext = ".sqlitedb"
    if not is_dir and not output.endswith(ext):
        output += ext

    if exists(output) and args.force:
        print("deleting", output)
        if is_dir:
            rmtree(output)
        else:
            remove(output)

    assert (
        not exists(output) or args.append
    ), f"{output} exists, overwrite with -f or append with -a"

    print("writing to", output)
    dest = sqlite3.connect(output) if not is_dir else None

    timecol = args.timecol or args.expire

    if dest:
        dcur = dest.cursor()

        # dcur.execute("CREATE TABLE android_metadata (locale TEXT);")
        # dcur.execute("INSERT INTO android_metadata VALUES ('en_US');")

        dcur.execute(
            "CREATE TABLE IF NOT EXISTS info (tilenumbering, minzoom, maxzoom, title TEXT, url TEXT, randoms TEXT, ellipsoid TEXT, inverted_y TEXT, referer TEXT, useragent TEXT, timecolumn TEXT, expireminutes TEXT);"
        )
        dcur.execute(
            "INSERT INTO info (tilenumbering, minzoom, maxzoom, title, url, randoms, ellipsoid, inverted_y, referer, useragent, timecolumn, expireminutes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
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
                "Mozilla/5.0 AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
                if args.mozilla
                else args.agent,
                "yes" if timecol else "no",
                args.expire or -1,
            ],
        )
        dcur.execute(
            f"CREATE TABLE IF NOT EXISTS tiles (x int, y int, z int, s int, image blob, {'time long,' if timecol else ''} PRIMARY KEY (x,y,z,s));"
        )
        dcur.execute("CREATE INDEX IF NOT EXISTS IND on tiles (x,y,z,s);")

    now = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)

    i = 0
    for input in inputs:
        print("reading", input)
        source = sqlite3.connect(input)
        for row in source.execute(
            "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles"
        ):
            z, x, y, s = int(row[0]), int(row[1]), int(row[2]), 0
            if z < args.min_convert or z > args.max_convert:
                continue
            data = [x, y, z, s, sqlite3.Binary(row[3])]
            if timecol:
                data.append(now)
            i += 1
            if dest:
                insert = f"INSERT OR REPLACE INTO tiles (x,y,z,s,image{',time' if timecol else ''}) VALUES (?,?,?,?,?{',?' if timecol else ''})"
                dcur.execute(insert, data)
            if is_dir:
                dir = f"{output}/{z}/{x}"
                makedirs(dir, exist_ok=1)
                write(f"{dir}/{y}.png", row[3])
        source.close()
    if i:
        print("copied", i, "tiles")

    if dest:
        dest.commit()
        dest.close()


def write(filename, data):
    with open(filename, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
