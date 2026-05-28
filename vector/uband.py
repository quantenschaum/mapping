#!/usr/bin/env python3
import sys

# https://nauticalcharts.noaa.gov/charts/rescheming-and-improving-electronic-navigational-charts.html
UBANDS = {
    1: 10_000_000,  # <=6 10M-3.5M
    2: 1_500_000,  # 7-8 1.5M-700k
    3: 350_000,  # 9-10 350k-180k
    4: 90_000,  # 11-12 90k-45k
    5: 22_000,  # 13 22k-12k
    6: 9_000,  # 14 4k-2k
}


def main():
    assert len(sys.argv) == 2

    s = int(sys.argv[1])

    if s in UBANDS:
        print(UBANDS[s])
        return

    u = max(uband for uband, scale in UBANDS.items() if s <= scale)
    print(u)


main()
