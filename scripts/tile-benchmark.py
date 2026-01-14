#!/usr/bin/env python3
import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from itertools import product
from pathlib import Path

from PIL import Image
from requests import session
from rich import print
from rich.progress import track

try:
    import pillow_avif
except:
    pass

try:
    from rich_argparse import (
        ArgumentDefaultsRichHelpFormatter as ArgumentDefaultsHelpFormatter,
    )
except:
    pass


def download_tiles(base, odir, x=550, y=335, z=10, n=10):
    s = session()
    odir = Path(odir)
    odir.mkdir(parents=True, exist_ok=True)
    xo, yo = int(x * 2 ** (z - 10)), int(y * 2 ** (z - 10))
    for x, y in track(product(range(n), range(n)), "downloading", total=n * n):
        x, y = xo + x - n // 2, yo + y - n // 2
        # print(z, x, y)
        tile_file = Path(odir / f"{z}_{x}_{y}.png")
        if tile_file.exists():
            continue
        r = s.get(f"{base}/{z}/{x}/{y}.png")
        r.raise_for_status()
        if r.status_code != 200:
            continue
        with open(tile_file, "wb") as f:
            f.write(r.content)


def reencode(input_path, output_path, opts):
    img = Image.open(input_path)

    if img.mode != "RGB":
        img = img.convert("RGB")

    if "colors" in opts:
        img = img.quantize(colors=opts["colors"])

    format = output_path.suffix.lstrip(".").lower()
    t0 = time.monotonic()
    img.save(output_path, format, **opts)
    t1 = time.monotonic()
    return {
        "time": t1 - t0,
        "size": output_path.stat().st_size,
        "size0": input_path.stat().st_size,
    }


def reencode_dir(input_dir, output_dir, format, opts):
    # print(input_dir,'>',output_dir,format,opts)
    suf = "." + format.lower()
    stats = []
    output_dir.mkdir(parents=True, exist_ok=True)
    files = list(input_dir.glob("*"))
    for f in track(files, output_dir.name, total=len(files)):
        if f.is_dir():
            continue
        s = reencode(f, (output_dir / f.name).with_suffix(suf), opts)
        # print(s)
        stats.append(s)
    return stats


def fb(bytes_val):
    if bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.2f} KB"
    else:
        return f"{bytes_val / 1024 / 1024:.2f} MB"


PRESETS = [
    ("png", "png-RGB", {"optimize": True}),
    ("png", "png-P8", {"optimize": True, "colors": 2**8}),
    ("png", "png-P7", {"optimize": True, "colors": 2**7}),
    ("gif", "gif", {"optimize": True}),
    ("webp", "webp-LL", {"lossless": True}),
    ("webp", "webp-90", {"quality": 90}),
    ("webp", "webp-80", {"quality": 80}),
    ("avif", "avif-LL", {"quality": 100}),
    ("avif", "avif-90", {"quality": 90}),
    ("avif", "avif-80", {"quality": 80}),
    ("jpeg", "jpg-100", {"quality": 100, "optimize": True}),
    ("jpeg", "jpg-90", {"quality": 90, "optimize": True}),
    ("jpeg", "jpg-80", {"quality": 80, "optimize": True}),
]


def benchmark(input_dir, output_dir, avif=0, lossy=0):
    input_dir, output_dir = Path(input_dir), Path(output_dir)

    stats = {}

    for format, name, opts in PRESETS:
        if not avif and format == "avif":
            continue
        if not lossy and name[-1] == "0":
            continue

        s = reencode_dir(input_dir, output_dir / name, format, opts)

        stats[name] = {"n": len(s)}
        for k in s[0].keys():
            k_sum = sum(map(lambda d: d[k], s))
            stats[name][k] = k_sum

    print(stats)

    for n, d in sorted(stats.items(), key=lambda e: e[1]["size"]):
        s0, s, t = d["size0"], d["size"], d["time"]
        print(f"{n:<10} {fb(s):<8} {(s / s0 - 1) * 100:+6.0f}% {t:6.1f}s")


def main():
    parser = ArgumentParser(
        description="image encoding benchmark",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input_dir", help="input dir with tiles")
    parser.add_argument(
        "-d",
        "--download",
        help="download NxN test tiles to input_dir",
        type=int,
        metavar="N",
    )
    parser.add_argument(
        "-u",
        "--url",
        help="base URL for tile download",
        default="https://tile.openstreetmap.de/",
    )
    parser.add_argument(
        "-z",
        help="zoom level to download",
        type=int,
        default=10,
    )
    parser.add_argument(
        "-x",
        help="x center to download (at z=10)",
        type=int,
        default=550,
    )
    parser.add_argument(
        "-y",
        help="y center to download (at z=10)",
        type=int,
        default=335,
    )
    parser.add_argument(
        "-a",
        "--avif",
        help="include avif in tests",
        action="store_true",
    )
    parser.add_argument(
        "-l",
        "--lossy",
        help="include lossy modes",
        action="store_true",
    )
    args = parser.parse_args()

    if args.download:
        download_tiles(
            args.url, args.input_dir, x=args.x, y=args.y, z=args.z, n=args.download
        )

    benchmark(args.input_dir, args.input_dir, args.avif, args.lossy)


if __name__ == "__main__":
    main()
