#!/usr/bin/env python3
# coding: utf-8

from datetime import datetime
import os.path
import re
import sys


def main():
    with open(sys.argv[1]) as f:
        input = f.read()

    output = []
    for line in input.splitlines():
        # line=line.strip()
        m = re.search(r"\[.+\]\((.+?)\)\{:download\}", line)
        if m:
            try:
                # print(m.groups())
                filename = m.group(1)
                # filename="index.md"
                mtime = os.path.getmtime(filename)
                fsize = os.path.getsize(filename)
                line = (line
                  .replace('{:download}', f" ({datetime.fromtimestamp(mtime):%Y-%m-%d}/{fsize/1e6:.1f}MB)")
                  .replace(f'({filename})',f'({filename}?t={int(mtime)})'))
            except:
                pass
        print(line)
        # output.append(line + "\n")
    #
    # with open(sys.argv[1], "w") as f:
    #     f.writelines(output)


main()
