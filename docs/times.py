#!/usr/bin/env python3
# coding: utf-8

import datetime
import os.path
import re
import sys


def main():
    with open(sys.argv[1]) as f:
        input = f.read()

    output = []
    for line in input.splitlines():
        # line=line.strip()
        m = re.match(r"(-\s+\[.+\]\((.+?)\).*)", line) if ":download" in line else None
        if m:
            try:
                # print(m.groups(), m.group(2))
                filename = m.group(2)
                # filename="index.md"
                mtime = os.path.getmtime(filename)
                fsize = os.path.getsize(filename)
                line = (
                    m.group(1).replace('{:download}','')
                    + f" ({datetime.datetime.fromtimestamp(mtime):%Y-%m-%d}/{fsize/1e6:.1f}MB)"
                )
            except:
                pass
        # print(line)
        output.append(line + "\n")

    with open(sys.argv[1], "w") as f:
        f.writelines(output)


main()
