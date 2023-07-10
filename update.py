#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import os
from datetime import datetime
from math import inf, isnan, log, pi, pow, sqrt, tan

import requests
from pyquery import PyQuery as pq


# In[2]:


def load_json(filename):
  with open(filename) as f:
    return json.load(f)


# In[3]:


types = [
  "buoy_isolated_danger",
  "buoy_safe_water",
  "buoy_special_purpose",
  "buoy_cardinal",
  "buoy_lateral",
]


def type_cat(c, p):
  c = color(c)
  p = pattern(p)
  cat = None
  if "black" in c and "red" in c:
    t = "buoy_isolated_danger"
  if "white" in c and "red" in c and p == "vertical":
    t = "buoy_safe_water"
  elif c == "yellow":
    t = "buoy_special_purpose"
  elif "black" in c and "yellow" in c:
    t = "buoy_cardinal"
    if c == "black;yellow":
      cat = "north"
    elif c == "black;yellow;black":
      cat = "east"
    elif c == "yellow;black":
      cat = "south"
    elif c == "yellow;black;yellow":
      cat = "west"
  elif "green" in c or "red" in c:
    t = "buoy_lateral"
    if c.startswith("green"):
      if "red" in c:
        if c.count(";") > 2:
          cat = "channel_separation"
        else:
          cat = "preferred_channel_port"
      elif "white" in c:
        cat = "danger_left"
      else:
        assert c.count(";") == 0
        cat = "starboard"
    elif c.startswith("red"):
      if "green" in c:
        if c.count(";") > 2:
          cat = "channel_separation"
        else:
          cat = "preferred_channel_starboard"
      elif "white" in c:
        cat = "danger_right"
      else:
        assert c.count(";") == 0
        cat = "port"
  return t, cat


# In[4]:


colors = {1: "white", 2: "black", 3: "red", 4: "green", 6: "yellow"}


def color(s, osm=0):
  if s == "#":
    return
  for k, v in colors.items():
    s = s.replace(str(k), v)
  return s.replace(",", ";")


# In[5]:


shapes = {
  1: "conical",
  2: "can",
  3: "spherical",
  4: "pillar",
  5: "spar",
  6: "barrel",
  7: "super-buoy",
}


def shape(s):
  if s == "#":
    return
  return shapes[int(s)]


# In[6]:


patterns = {1: "horizontal", 2: "vertical"}


def pattern(s):
  if s == "#":
    return
  return patterns[int(s)]


# In[7]:


topmarks = {
  1: "cone, point up",
  2: "cone, point down",
  3: "sphere",
  5: "cylinder",
  7: "x-shape",
  10: "2 cones point together",
  11: "2 cones base together",
  13: "2 cones up",
  14: "2 cones down",
  98: "cylinder over sphere",
  99: "cone, point up over sphere",
}


def topmark(s):
  if s == "#":
    return
  return topmarks[int(s)]


# In[8]:


light_characters = {
  1: "F",
  2: "Fl",
  3: "LFl",
  4: "Q",
  5: "VQ",
  6: "UQ",
  7: "Iso",
  8: "Oc",
  9: "IQ",
  10: "IVQ",
  11: "IUQ",
  12: "Mo",
  13: "FFl",
  14: "FLFl",
  15: "OcFl",
  16: "FLFl",
  17: "OcAlt",
  18: "LFlAlt",
  19: "FlAlt",
  25: "Q+LFl",
  26: "VQ+LFl",
  27: "UQ+LFl",
  28: "Al",
  29: "F+FlAlt",
}


def light_chr(s):
  if s == "#":
    return
  return light_characters[int(s)]


# In[9]:


def light_per(s):
  if s == "#":
    return
  return str(int(s))


# In[10]:


def light_grp(s):
  if s == "#":
    return
  return s.replace("(1)", "").replace("(", "").replace(")", "") or None


# In[11]:


def latlon_to_grid(lat, lon):
  f = 20037508.34
  x = (lon * f) / 180
  y = log(tan((90 + lat) * pi / 360)) / (pi / 180)
  y = (y * f) / 180
  return x, y


# In[12]:


def distance(a, b):
  a, b = [latlon_to_grid(*p) for p in (a, b)]
  return sqrt(sum([pow(a[i] - b[i], 2) for i in range(2)]))


# In[13]:


def load_geojson(filename, timestamp=None, source=None):
  data = load_json(filename)
  now = timestamp or datetime.now().date().isoformat()
  source = source or f"https://data.overheid.nl/dataset/2c5f6817-d902-4123-9b1d-103a0a484979 {now}"

  points = []
  for f in data["features"]:
    try:
      p = f["properties"]
      ll = p["y_wgs84"], p["x_wgs84"]
      tags = {"ll": ll}
      n = p["benaming"]
      assert n and "#" not in n
      tags["seamark:name"] = n
      tags["seamark:source"] = source
      tags["seamark:source:id"] = None

      k = color(p["obj_kleur_"])
      if not k: continue
      t, c = type_cat(k, p["kleurpatr_"])
      tags["seamark:type"] = t
      for u in types:
        if u == t:
          continue
        tags[f"seamark:{u}:category"] = None
        tags[f"seamark:{u}:shape"] = None
        tags[f"seamark:{u}:colour"] = None
        tags[f"seamark:{u}:colour_pattern"] = None
      if c:
        tags[f"seamark:{t}:category"] = c
      tags["seamark:buoy_lateral:system"] = (
        (
          "cevni"
          if c and (k.count(";") % 2 or "danger" in c or "separation" in c)
          else "iala-a"
        )
        if "lateral" in t
        else None
      )
      tags[f"seamark:{t}:shape"] = shape(p["obj_vorm_c"])
      tags[f"seamark:{t}:colour"] = "red;white" if t == "buoy_safe_water" else k
      tags[f"seamark:{t}:colour_pattern"] = (
        pattern(p["kleurpatr_"]) if ";" in k else None
      )
      tc = color(p["tt_kleur_c"])
      tags["seamark:topmark:colour"] = tc
      tags["seamark:topmark:colour_pattern"] = (
        pattern(p["tt_pat_c"]) if tc and ";" in tc else None
      )
      tags["seamark:light:colour"] = color(p["licht_kl_c"])
      tags["seamark:light:character"] = light_chr(p["sign_kar_c"])
      tags["seamark:light:period"] = light_per(p["sign_perio"])
      tags["seamark:light:group"] = light_grp(p["sign_gr_c"])

      tags["seamark"] = None

      tags["properties"] = p

      points.append(tags)

      # if 'PM 40-WE 1' in tags['seamark:name']:
      #    print(json.dumps(tags, indent=2))
      #    print(json.dumps(f, indent=2))
      #   break
    except:
      print(json.dumps(f, indent=2))
      raise

  # print(json.dumps(points[0], indent=2))
  # print(len(points),'points')

  return points


# load_geojson('vwm/drijvend.json')


# In[14]:


def load_marrekrite(gpx="marrekrite.gpx"):
  import gpxpy

  with open(gpx) as f:
    gpx = gpxpy.parse(f)

  points = []
  for wpt in gpx.waypoints:
    tags = {}
    tags["ll"] = wpt.latitude, wpt.longitude
    tags["seamark:name"] = wpt.name.split()[0]
    tags["seamark:source"] = "https://github.com/marcelrv/OpenCPN-Waypoints"
    tags["seamark:type"] = "mooring"
    if wpt.name.startswith("MB"):
      tags["seamark:mooring:category"] = "buoy"
      tags["seamark:mooring:colour"] = "yellow;blue"
      tags["seamark:mooring:colour_pattern"] = "horizontal"
      tags["seamark:mooring:shape"] = "spherical"
      tags["seamark:information"] = "max 24h"
      # print(wpt)
      # print(json.dumps(tags,indent=2))
      points.append(tags)
    # elif 'steiger' in wpt.name.lower():
    #    tags["seamark:mooring:category"] = "wall"

  return points


# In[15]:


def update_node(n, p, dmin=1):
  ll = [float(n.attr[a]) for a in ("lat", "lon")]
  name = p["seamark:name"]
  modifications = []
  # print(n)
  # print(json.dumps(p, indent=2))

  d = distance(ll, p["ll"])
  if d > dmin or isnan(d):
    n.attr["lat"], n.attr["lon"] = [str(x) for x in p["ll"]]
    modifications.append(("POS", p["ll"], "d", "*" if isnan(d) else round(d), "m"))

  for k, v in p.items():
    if k.startswith("seamark") and "source" not in k:
      tag = n.find(f"tag[k='{k}']")
      if tag:
        w = tag.attr["v"]
        if not v:
          tag.remove()
          modifications.append(("DEL", f"{k}={w}"))
        elif w != v:
          tag.attr["v"] = v
          modifications.append(("MOD", f"{k}={v}", f"({w})"))
      elif v:
        pq(f'<tag k="{k}" v="{v}" />').append_to(n)
        modifications.append(("ADD", f"{k}={v}"))

  if modifications:
    n.attr["action"] = "modify"
    for k in "source", "seamark:source", "seamark:source:id":
      tag = n.find(f"tag[k='{k}']")
      if tag:
        tag.remove()
      v = p.get(k)
      if v:
        pq(f'<tag k="{k}" v="{v}" />').append_to(n)

    id = n.attr["id"]
    ll = [float(n.attr[a]) for a in ("lat", "lon")]
    dx, dy = 0.001, 0.001
    print(
      "node",
      id,
      f"name={name}",
      "matched by",
      p.get("match"),
      f"http://localhost:8111/zoom?left={ll[1] - dx}&right={ll[1] + dx}&bottom={ll[0] - dy}&top={ll[0] + dy}&select=node{id}",
    )
    for l in modifications:
      print("    ", *[str(s).strip() for s in l])

    # print(n)


# In[16]:


def get_bounds(xml):
  bounds = xml("osm bounds")
  if bounds:
    return {
      a: float(bounds.attr[a]) for a in ("minlat", "maxlat", "minlon", "maxlon")
    }
  b = {"minlat": +inf, "maxlat": -inf, "minlon": +inf, "maxlon": -inf}
  for e in xml("node"):
    n = pq(e)
    if not n.attr["lat"]:
      continue
    ll = [float(n.attr[a]) for a in ("lat", "lon")]
    b["minlat"] = min(b["minlat"], ll[0])
    b["maxlat"] = max(b["maxlat"], ll[0])
    b["minlon"] = min(b["minlon"], ll[1])
    b["maxlon"] = max(b["maxlon"], ll[1])
  return b


# In[17]:


def update_osm(infile, points, outfile, add=True, remod=False, remove=False, n_dist=1000, p_dist=50, s_dist=1):
  x = pq(filename=infile)

  bounds = get_bounds(x)
  print("bounds", bounds)
  data = list(
    filter(
      lambda p: bounds["minlat"] <= p["ll"][0] <= bounds["maxlat"]
                and bounds["minlon"] <= p["ll"][1] <= bounds["maxlon"],
      points,
    )
  )

  matches = {}
  for e in x("node"):
    n = pq(e)
    if not n.find("tag[k='seamark:type']"):
      continue
    if "buoy_" not in n.find("tag[k='seamark:type']").attr["v"]:
      continue
    # print(n)
    ll = [float(n.attr[a]) for a in ("lat", "lon")]
    if bounds and not (
      bounds["minlat"] <= ll[0] <= bounds["maxlat"]
      and bounds["minlon"] <= ll[1] <= bounds["maxlon"]
    ):
      continue
    name = n.find("tag[k='seamark:name']").attr["v"]

    # print(ll,name,src,id)
    p = []
    match = "NONE"
    if not p:
      p = list(
        filter(
          lambda p: distance(ll, p["ll"]) <= n_dist and name == p["seamark:name"],
          data,
        )
      )
      if p:
        match = "NAME"
    if not p:
      p = list(filter(lambda p: distance(ll, p["ll"]) <= p_dist, data))
      if p:
        match = "POS"
    # print(json.dumps(p, indent=2))

    matches[match] = matches.get(match, 0) + 1

    if len(p) > 1:
      print("AMBIGOUS", len(p), match, name)
    assert len(p) <= 1, json.dumps(p, indent=2)
    for m in p:
      data.remove(m)
    if remove and len(p) == 0:
      dx, dy = 0.001, 0.001
      print(
        "REMOVE?",
        name,
        f"http://localhost:8111/zoom?left={ll[1] - dx}&right={ll[1] + dx}&bottom={ll[0] - dy}&top={ll[0] + dy}&select=node{n.attr['id']}",
      )
    if len(p) == 1:
      p = p[0]
      p["match"] = match
      if remod or not n.attr["action"]:
        update_node(n, p, s_dist)

  print("MATCHED NODES ", matches)
  print("MATCHED POINTS", len(data))

  if bounds and add:
    for i, p in enumerate(data, 10000):
      n = pq(f'<node id="{-i}" visible="true" lat="nan" lon="nan"/>')
      update_node(n, p, s_dist)
      x("osm").prepend(n)

  with open(outfile, "w") as f:
    f.write(str(x))


# In[18]:

def main():
  from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

  parser = ArgumentParser(prog='buoy updater',
                          description='update buoys by manipulating OSM xml from geojson',
                          epilog='https://github.com/quantenschaum/mapping/',
                          formatter_class=ArgumentDefaultsHelpFormatter)

  parser.add_argument("-i", "--osm-in", help="OSM XML file to read", metavar="osm", default="in.osm")
  parser.add_argument("-o", "--osm-out", help="OSM XML file to write", metavar="osm", default="out.osm")
  parser.add_argument("-g", "--json", help="GeoJSON input file to read", metavar="geojson", default="buoys.json")
  parser.add_argument("-M", "--marrekrite", help="GPX file with marrekrite points", metavar="gpx")
  parser.add_argument("-a", "--add", help="add buoys", action="store_true")
  parser.add_argument("-m", "--remod", help="update nodes that already have been modified", action="store_true")
  parser.add_argument("-r", "--remove", help="print hint for node to be removed (they are not removed automatically)",
                      action="store_true")
  parser.add_argument("-N", "--n-dist", help="distance in meters for matching nodes by name", type=int, default=1000)
  parser.add_argument("-P", "--p-dist", help="distance in meters for matching nodes by position", type=int, default=50)
  parser.add_argument("-S", "--s-dist", help="threshold in meters for actually moving a node", type=int, default=1)

  args = parser.parse_args()

  if args.marrekrite:
    data = load_marrekrite(args.marrekrite)
  else:
    data = load_geojson(args.json)
  update_osm("saved.osm", data, args.osm_out, add=args.add, remod=args.remod, remove=args.remove, n_dist=args.n_dist,
             p_dist=args.p_dist, s_dist=args.s_dist)
  requests.get(f"http://localhost:8111/open_file?filename={os.path.abspath(args.osm_out)}")


if __name__ == "__main__":
  main()
