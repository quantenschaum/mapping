#!/usr/bin/env python3
# coding: utf-8

import json
import os.path

import requests

mv_base="https://www.nationalpark-vorpommersche-boddenlandschaft.de/"
url_mv=f"{mv_base}/assets/map/navigation-755.json"

mapid=56358
url=f"https://umap.openstreetmap.de/de/map/nordsbefv-wassersport_{mapid}"

def main():
  r=requests.get(url_mv)
  r.raise_for_status()
  for e in r.json():
    if e.get("label")=="Schutzzonen":
      for c in e["children"]:
        for d in c["children"]:
          data_url=d.get("dataUrl")
          if data_url:
            data_url=mv_base+data_url
            # print(data_url)
            # print(os.path.basename(data_url))
            r=requests.get(data_url)
            r.raise_for_status()
            write(os.path.basename(data_url),r.content,"wb")

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
    # print(l["name"])
    name=l["name"].replace(" ","-").replace("--","-")
    write(f"{name}.json",r.text)


def write(filename, data,mode="w"):
  print(filename)
  with open(filename, mode) as f:
    f.write(data)

main()