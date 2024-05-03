#!/usr/bin/env python3
# coding: utf-8

import json

import requests

mapid=56358
url=f"https://umap.openstreetmap.de/de/map/nordsbefv-wassersport_{mapid}"

def main():
  r=requests.get(url)
  r.raise_for_status()
  datalayers=""
  for line in r.text.splitlines():
    if '"datalayers": [' in line or datalayers:
      datalayers+=(line+"\n") if datalayers else "["
      if line.strip()=="]":
        break
  # print(datalayers)
  datalayers=json.loads(datalayers)
  # print(json.dumps(datalayers,indent=2))

  for l in datalayers:
    r=requests.get(f"https://umap.openstreetmap.de/de/datalayer/{mapid}/{l['id']}/")
    r.raise_for_status()
    print(l["name"])
    name=l["name"].replace(" ","-").replace("--","-")
    write(f"{name}.json",r.text)


def write(filename, data):
  with open(filename,"w") as f:
    f.write(data)

main()