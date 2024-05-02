#!/usr/bin/env python3
# coding: utf-8

import datetime
import os.path
import re
import sys

def main():
  with open(sys.argv[1]) as f:
    input=f.read()

  for line in input.splitlines():
    # line=line.strip()
    m=re.match(r"(-\s+\[.+\]\((.+?)\))",line)
    if m:
      # print(m.groups(),m.group(2))
      filename=m.group(2)
      # filename="index.md"
      mtime=os.path.getmtime(filename)
      fsize=os.path.getsize(filename)
      line=m.group(1)+f" ({datetime.datetime.fromtimestamp(mtime):%Y-%m-%d} {fsize/1000:.1f}MB)"
    print(line)


main()