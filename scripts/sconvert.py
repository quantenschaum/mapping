#!/usr/bin/env python3
# coding: utf-8
import collections

import csv
import itertools
import json
import os
import struct
import sys
from datetime import datetime
from math import radians, degrees, log, tan, pi, atan, exp, isfinite
import argparse
import triangle
from collections import defaultdict
import shapely

from geojson import (
    Point,
    LineString,
    Polygon,
    MultiPoint,
    MultiLineString,
    MultiPolygon,
    Feature,
    FeatureCollection,
)
from jinja2.nodes import FromImport

BYTE_ORDER = "="

# https://github.com/bdbcat/o-charts_pi/blob/master/src/Osenc.h#L88
HEADER_SENC_VERSION = 1
HEADER_CELL_NAME = 2
HEADER_CELL_PUBLISHDATE = 3
HEADER_CELL_EDITION = 4
HEADER_CELL_UPDATEDATE = 5
HEADER_CELL_UPDATE = 6
HEADER_CELL_NATIVESCALE = 7
HEADER_CELL_SENCCREATEDATE = 8
HEADER_CELL_SOUNDINGDATUM = 9
FEATURE_ID_RECORD = 64
FEATURE_ATTRIBUTE_RECORD = 65
FEATURE_GEOMETRY_RECORD_POINT = 80
FEATURE_GEOMETRY_RECORD_LINE = 81
FEATURE_GEOMETRY_RECORD_AREA = 82
FEATURE_GEOMETRY_RECORD_MULTIPOINT = 83
FEATURE_GEOMETRY_RECORD_AREA_EXT = 84
VECTOR_EDGE_NODE_TABLE_EXT_RECORD = 85
VECTOR_CONNECTED_NODE_TABLE_EXT_RECORD = 86
VECTOR_EDGE_NODE_TABLE_RECORD = 96
VECTOR_CONNECTED_NODE_TABLE_RECORD = 97
CELL_COVR_RECORD = 98
CELL_NOCOVR_RECORD = 99
CELL_EXTENT_RECORD = 100
CELL_TXTDSC_INFO_FILE_RECORD = 101
SERVER_STATUS_RECORD = 200


def to(typ, val):
    try:
        return typ(val)
    except:
        return val


def read_csv(filename):
    with open(filename) as f:
        table = {}
        reader = csv.reader(f, delimiter=",", quotechar='"')
        for row in reader:
            if not row:
                continue
            # print(row)
            k = to(int, row[0])
            if k not in table:
                v = [
                    list(filter(len, s.split(";"))) if ";" in s else s for s in row[1:]
                ]
                table[k] = v
        # print(table)
        return table

# https://github.com/OpenCPN/OpenCPN/tree/master/data/s57data
csvdir=os.path.dirname(__file__)
s57obj = read_csv(csvdir+"/s57objectclasses.csv")
s57attr = read_csv(csvdir+"/s57attributes.csv")

# if attributes that are unique to one layer
# attributes={}
# for v in s57obj.values():
#   layer,attr,cls,types=v[1],v[2:5],v[5],v[6]
#   # print(layer,attr)
#   for a in [x for xs in attr for x in xs]:
#     layers=attributes.get(a,set())
#     layers.add(layer)
#     attributes[a]=layers
# unique={a:l.pop() for a,l in attributes.items() if len(l)==1 and len(a)==6}
# print(unique)
# exit()


def acronym(data, read):
    val = data.get("ftype")
    if val and val in s57obj:
        # data["object"] = s57obj[val][0]
        data["acronym"] = s57obj[val][1]
    val = data.get("atype")
    if val and val in s57attr:
        # data["attribute"] = s57attr[val][0]
        data["acronym"] = s57attr[val][1]
    # if 'ftype' in data: print(data)

def acronym_code(name):
    name=name.upper()
    for k,v in s57attr.items():
        if name==v[1].upper():
            return k
    for k,v in s57obj.items():
        if name==v[1].upper():
            return k

def center(data, read):
    data["north"] = data["nw_lat"]
    data["south"] = data["se_lat"]
    data["west"] = data["nw_lon"]
    data["east"] = data["se_lon"]
    data["lat"] = (data["south"] + data["north"]) / 2
    data["lon"] = (data["west"] + data["east"]) / 2


R = 6378137.0


def ll2grid(lon, lat):
    easting = radians(lon) * R
    northing = log(tan(pi / 4 + radians(lat) / 2)) * R
    return easting, northing


def grid2ll(easting, northing):
    lat = degrees(2 * atan(exp(northing / R)) - pi / 2.0)
    lon = degrees(easting / R)
    return lon, lat


def multipoint(data, read):
    data["points"] = [unpack(read, "fff") for i in range(data["count"])]


def lines(data, read):
    data["edges"] = [unpack(read, "IIII") for j in range(data["count"])]


def areas(data, read, skip_triangles=1):
    # print(data)
    if skip_triangles:
        read(data["rlen"] - 50 - data["count"] * 16)
    else:
        conts, tris = [data[k] for k in ("contours", "triprim")]
        pointcount = unpack(read, f"{conts}I")
        data["pointcount"] = pointcount
        triangles = data["triangles"] = []
        for t in range(tris):
            tritype, nvert = unpack(read, "BI")
            bbox = unpack(read, "dddd")
            # print(bbox)
            vertices = [unpack(read, "ff") for i in range(nvert)]
            triangles.append({"ttype": tritype, "bbox": bbox, "vertices": vertices})
    data["edges"] = [unpack(read, "IIII") for j in range(data["count"])]


def edge_node_table(data, read):
    edges = {}
    s = data.get("scale", 1)
    for i in range(data["count"]):
        index, points = unpack(read, "II")
        assert index
        edges[index] = [[v / s for v in unpack(read, "ff")] for j in range(points)]
    data["edges"] = edges


def connected_node_table(data, read):
    nodes = {}
    s = data.get("scale", 1)
    for i in range(data["count"]):
        index = unpack(read, "I")[0]
        assert index
        nodes[index] = [v / s for v in unpack(read, "ff")]
    data["nodes"] = nodes


# <key>:<datatype>
TYPE2DATA = {
    HEADER_SENC_VERSION: ["version:H"],
    HEADER_CELL_NAME: ["cellname:{r}s"],
    HEADER_CELL_PUBLISHDATE: ["published:{r}s"],
    HEADER_CELL_EDITION: ["edition:H"],
    HEADER_CELL_UPDATEDATE: ["updated:{r}s"],
    HEADER_CELL_UPDATE: ["update:H"],
    HEADER_CELL_NATIVESCALE: ["scale:I"],
    HEADER_CELL_SENCCREATEDATE: ["created:{r}s"],
    HEADER_CELL_SOUNDINGDATUM: ["datum:{r}s"],
    FEATURE_ID_RECORD: ["ftype:H", "id:H", "primitive:B", acronym],
    FEATURE_ATTRIBUTE_RECORD: [
        "atype:H",
        "vtype:B",
        "value:{'I' if d['vtype']==0 else str(r)+'s' if d['vtype']==4 else 'd'}",
        acronym,
    ],
    FEATURE_GEOMETRY_RECORD_POINT: ["lat:d", "lon:d"],
    FEATURE_GEOMETRY_RECORD_LINE: [
        "south:d",
        "north:d",
        "west:d",
        "east:d",
        "count:I",
        lines,
    ],
    FEATURE_GEOMETRY_RECORD_AREA: [
        "south:d",
        "north:d",
        "west:d",
        "east:d",
        "contours:I",
        "triprim:I",
        "count:I",
        areas,
    ],
    FEATURE_GEOMETRY_RECORD_MULTIPOINT: [
        "south:d",
        "north:d",
        "west:d",
        "east:d",
        "count:I",
        multipoint,
    ],
    FEATURE_GEOMETRY_RECORD_AREA_EXT: [
        "south:d",
        "north:d",
        "west:d",
        "east:d",
        "contours:I",
        "triprim:I",
        "count:I",
        "scale:d",
        areas,
    ],
    VECTOR_EDGE_NODE_TABLE_EXT_RECORD: ["count:I", "scale:d", edge_node_table],
    VECTOR_CONNECTED_NODE_TABLE_EXT_RECORD: [
        "count:I",
        "scale:d",
        connected_node_table,
    ],
    VECTOR_EDGE_NODE_TABLE_RECORD: ["count:I", edge_node_table],
    VECTOR_CONNECTED_NODE_TABLE_RECORD: ["count:I", connected_node_table],
    CELL_COVR_RECORD: ["count:I", "array:{r//4}f"],
    CELL_NOCOVR_RECORD: ["count:I", "array:{r//4}f"],
    CELL_EXTENT_RECORD: [
        "sw_lat:d",
        "sw_lon:d",
        "nw_lat:d",
        "nw_lon:d",
        "ne_lat:d",
        "ne_lon:d",
        "se_lat:d",
        "se_lon:d",
        center,
    ],
    CELL_TXTDSC_INFO_FILE_RECORD: [
        "flength:I",
        "clength:I",
        "file:{d['flength']}s",
        "text:{r}s",
    ],
    SERVER_STATUS_RECORD: [
        "server:H",
        "decrypt:H",
        "expire:H",
        "expire_days_remaining:H",
        "grace_days_allowed:H",
        "grace_days_remaining:H",
    ],
}


def unpack(stream, fmt):
    fmt = BYTE_ORDER + fmt
    size = struct.calcsize(fmt)
    buf = stream(size) if callable(stream) else stream.read(size)
    # print('fmt',fmt,buf)
    return struct.unpack(fmt, buf)


def read(stream):
    size, rlen = 0, 0

    def readdata(n):
        nonlocal size
        assert rlen == 0 or rlen - size >= n,(rlen,size,rlen-size,n)
        d = stream.read(n)
        size += len(d)
        return d

    buf = readdata(2)
    if len(buf) < 2 or sum(buf) == 0: return
    rtype = struct.unpack(BYTE_ORDER + "H", buf)[0]
    assert rtype in TYPE2DATA, f"unknown type: {rtype}"
    rlen = struct.unpack(BYTE_ORDER + "I", readdata(4))[0]
    d = data = {"rtype": rtype, "rlen": rlen}

    # print("*data:", data)

    for f in TYPE2DATA[rtype]:
        if callable(f):
            f(data, readdata)
            continue
        assert ":" in f, f
        name, fmt = f.split(":")
        r = rlen - size
        fmt = eval(f'f"{fmt}"')
        val = unpack(readdata, fmt)
        # print("name:", name, "fmt:", fmt,'val:',val)
        val = val[0] if len(val) == 1 else val
        if fmt.endswith("s"):
            try:
                val = val.decode().replace("\x00", "")
            except:
                pass
        data[name] = val
    r = rlen - size
    if r:
        print(data["rtype"], "skipped", r)
        readdata(r)
    # if rtype==FEATURE_GEOMETRY_RECORD_LINE: print("line:", data)
    # print("data:", data)
    return data


def read_oesu(filename):
    records = []
    with open(filename, "rb") as f:
        while True:
            r = read(f)
            if not r:
                break
            records.append(r)
    return records


def read_senc(files):
    features = []
    for f in files:
        records = read_oesu(f)
        print("converting", f)
        # for t, n in TYPE2REC.items():
        #     c = len(list(filter(lambda r: r["rtype"] == t, records)))
        #     print(f"{t:3} {n:40} {c:6}")
        chart = os.path.basename(os.path.splitext(f)[0])
        uband = 0#int(chart[-1])
        state0 = {"chart": chart, "uband": uband}
        rx, ry = None, None
        lines = []
        areas = []
        edges = {}
        nodes = {}
        for r in records:
            rtype = r["rtype"]
            # print({k:('...' if k in ('points','edges','nodes','array') else v) for k,v in r.items()})
            # print({k:v for k,v in r.items()})
            if rtype == HEADER_CELL_NATIVESCALE:
                state0['scale']=r['scale']
            if rtype == CELL_EXTENT_RECORD:
                rlat, rlon = [r[k] for k in ("lat", "lon")]
                rx, ry = ll2grid(rlon, rlat)
                cell = r
            # if rtype in (CELL_COVR_RECORD,CELL_NOCOVR_RECORD):
            #     print(r)
            if rtype == FEATURE_ID_RECORD:
                state = state0.copy()
                state["layer"] = r["acronym"]
            if rtype == FEATURE_ATTRIBUTE_RECORD:
                state[r["acronym"]] = r["value"]
            if rtype == FEATURE_GEOMETRY_RECORD_POINT:
                lat, lon = [r[k] for k in ("lat", "lon")]
                p = Point((lon, lat))
                f = Feature(geometry=p, properties=state)
                features.append(f)
            if rtype == FEATURE_GEOMETRY_RECORD_MULTIPOINT:
                for x, y, depth in r["points"]:
                    state["DEPTH"] = round(depth, 1)
                    p = Point(grid2ll(rx + x, ry + y))
                    f = Feature(geometry=p, properties=state.copy())
                    features.append(f)
            if rtype == FEATURE_GEOMETRY_RECORD_LINE:
                r["state"] = state
                lines.append(r)
            if rtype in (
                FEATURE_GEOMETRY_RECORD_AREA,
                FEATURE_GEOMETRY_RECORD_AREA_EXT,
            ):
                r["state"] = state
                areas.append(r)
            if rtype in (
                VECTOR_EDGE_NODE_TABLE_RECORD,
                VECTOR_EDGE_NODE_TABLE_EXT_RECORD,
            ):
                for i, e in r["edges"].items():
                    edges[i] = [grid2ll(rx + x, ry + y) for x, y in e]
                    # l = LineString([grid2ll(rx + x, ry + y) for x, y in e])
                    # f = Feature(geometry=l, properties={"layer": "edge"})
                    # features.append(f)
            if rtype in (
                VECTOR_CONNECTED_NODE_TABLE_RECORD,
                VECTOR_CONNECTED_NODE_TABLE_EXT_RECORD,
            ):
                for i, xy in r["nodes"].items():
                    nodes[i] = grid2ll(rx + xy[0], ry + xy[1])
                    # p = Point(grid2ll(rx + xy[0], ry + xy[1]))
                    # f = Feature(geometry=p, properties={"layer": "node"})
                    # features.append(f)
            if rtype == CELL_TXTDSC_INFO_FILE_RECORD:
                p = Polygon(
                    [
                        [
                            (cell["sw_lon"], cell["sw_lat"]),
                            (cell["nw_lon"], cell["nw_lat"]),
                            (cell["ne_lon"], cell["ne_lat"]),
                            (cell["se_lon"], cell["se_lat"]),
                            (cell["sw_lon"], cell["sw_lat"]),
                        ]
                    ]
                )
                props = state0.copy()
                props.update({"layer": "text", "text": r["text"]})
                f = Feature(geometry=p, properties=props)
                features.append(f)

        for r in lines:
            # print(r)
            lines = []
            for a, b, c, v in r["edges"]:
                line = []
                line.append(nodes[a])
                line += (reversed(edges[b]) if v else edges[b]) if b else []
                line.append(nodes[c])
                lines.append(line)
            l = LineString(line) if len(lines) == 1 else MultiLineString(lines)
            f = Feature(geometry=l, properties=r["state"])
            # print(f)
            features.append(f)

        for r in areas:
            # print(r)
            line = []
            lines = []
            e = 0
            for a, b, c, v in r["edges"]:
                if a != e:
                    if line: lines.append(line)
                    line = []
                    line.append(nodes[a])
                line += (reversed(edges[b]) if v else edges[b]) if b else []
                line.append(nodes[c])
                e = c
            lines.append(line)
            # print(len(lines))
            # assert r["contours"] == len(lines), (r, len(lines))
            # l = Polygon([line]) if len(lines) == 1 else MultiPolygon([lines])
            l = Polygon(lines)
            # l = Polygon(lines)
            f = Feature(geometry=l, properties=r["state"])
            # print(f)
            features.append(f)

            # print(r)
            triangles = r.get("triangles", [])
            for t in triangles:
                ttype, vertices = [t[k] for k in ("ttype", "vertices")]
                # print(ttype, len(vertices))
                vertices = [grid2ll(rx + x, ry + y) for x, y in vertices]
                if ttype in (4, 5):  # single triangles (4) or  strip (5)
                    tris = [
                        [vertices[k] for k in (i, i + 1, i + 2, i)]
                        for i in range(0, len(vertices) - 2, 1 if ttype == 5 else 3)
                    ]
                elif ttype == 6:  # triangle fan
                    tris = [
                        [vertices[k] for k in (0, i, i + 1, 0)]
                        for i in range(1, len(vertices) - 1)
                    ]
                else:
                    assert 0, f"unknown tri type {ttype}"
                # print(tris)
                g = MultiPolygon([tris])
                s = r["state"].copy()
                s["ttype"] = ttype
                s["contours"] = r["contours"]
                s["pointcount"] = r["pointcount"]
                s["layer_area"] = s["layer"]
                s["layer"] = "triangles"
                f = Feature(geometry=g, properties=s)
                features.append(f)

    return features


def write(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def save_json(filename,data,**kwargs):
  with open(filename,'w') as f:
    try:
      assert data['type']=='FeatureCollection'
      f.write('{"type":"FeatureCollection","features":[\n')
      n=len(data['features'])
      for i,e in enumerate(data['features'],1):
        f.write(json.dumps(e)+(',' if i<n else '')+'\n')
      f.write(']}\n')
    except:
      return json.dump(data,f,**kwargs)

def record(rtype,data):
    r=struct.pack(BYTE_ORDER+"HI",rtype,len(data)+6)+data
    # print('record',rtype,'len',len(data)+6,':',r[:6].hex(' ').upper(),'|',r[6:].hex(' ').upper())
    return r

def attributes(p):
  for a,v in p.items():
    atype=acronym_code(a)
    if v is None: continue
    if atype is None:
      # print('skipped',a)
      continue
    # print(s57attr[atype])
    if s57attr[atype][2]=='E': v=int(v)
    if s57attr[atype][2]=='F': v=float(v)
    if s57attr[atype][2]=='L': v=str(v)
    vtype = 4 if isinstance(v,str) else 2 if isinstance(v,float) else 0 if isinstance(v,int) else None
    assert vtype is not None,(a,v)
    # print(a,v,acronym_code(a),vtype,type(v))
    if vtype==0: v=struct.pack(BYTE_ORDER+'I',v)
    elif vtype==2: v=struct.pack(BYTE_ORDER+'d',v)
    elif vtype==4: v=v.encode()+b'\0'
    else: assert 0
    yield record(FEATURE_ATTRIBUTE_RECORD,struct.pack(BYTE_ORDER+'HB',atype,vtype)+v)


PRIMITIVES={'Point':1,'MultiPoint':1,
            'Line':2,'LineString':2,'MultiLineString':2,
            'Area':3,'Polygon':3,'MultiPolygon':3}

# https://www.bsh.de/DE/PUBLIKATIONEN/Naut_Produktkatalog/naut_produktkatalog_node.html
SCALES={1:1500000, 2:180000, 3:90000, 4:22000, 5:12000, 6:4000}


def bounds(coords):
  if isinstance(coords[0],dict):
    snwe=None
    for f in coords:
      b=bounds(f['geometry']['coordinates'])
      snwe=[m(a,b) for m,a,b in zip((min,max)*2,snwe or b,b)]
    return snwe

  while True:
    try: iter(coords[0])
    except: break
    coords=[x for l in coords for x in l]
  # print(coords)
  lons,lats=coords[::2],coords[1::2]
  # print(lons,lats)
  return min(lats),max(lats),min(lons),max(lons)


def find_keys(dic,val):
  return [k for k,v in dic.items() if v==val]

def find_key(dic,val):
  keys=find_keys(dic,val)
  if len(keys)==1: return keys[0]


def coverage(features):
  for f in filter(lambda o:o['properties'].get('layer','').upper()=='M_COVR',features):
    g=f['geometry']
    assert g['type']=='Polygon',g
    c=g['coordinates']
    verts=[y[i] for x in c for y in x for i in (1,0)]
    catcov=f['properties'].get('CATCOV',1)==1
    ctype=CELL_COVR_RECORD if catcov else CELL_NOCOVR_RECORD
    # print('coverage',catcov,verts)
    yield record(ctype,struct.pack(BYTE_ORDER+f'I{len(verts)}f',len(verts)//2,*verts))


def sort_key(feature):
  p=PRIMITIVES[feature['geometry']['type']]
  if p==1: return 2
  if p==2: return 1
  c=feature['geometry']['coordinates']
  if 'Multi' in feature['geometry']['type']: c=c[0] # first polygon
  p=shapely.Polygon(c[0]) # outer contour
  return -abs(p.area) # sort by area, to get polygons big first, small last


def catalog():
  try:
    with open(os.path.dirname(__file__)+'/../data/bsh/catalog.json') as f:
          return json.load(f)
  except: return {}

CATALOG=catalog()


def write_senc(filename,features):

    features=sorted(features, key=sort_key)

    S,N,W,E=bounds(features) # cell/chart bounds
    cell_center=(W+E)/2,(S+N)/2 # cell center lon, lat
    cx,cy=ll2grid(*cell_center) # cell center in grid coordinates

    cell=cellname=min(o['properties'].get('chart','chart') for o in features)
    uband=min(o['properties'].get('uband',0) for o in features)
    scamax=min(o['properties'].get('SCAMAX',999999) for o in features)
    scamin=max(o['properties'].get('SCAMIN',0) for o in features)
    scale=max(o['properties'].get('scale',0) for o in features) or SCALES.get(uband,0) or scamin
    sdatum=''
    edition=0
    published=''
    update=0
    updated=''
    created=datetime.now().strftime('%Y%m%d')

    meta=CATALOG.get(cellname)
    if meta:
      cellname=meta['c_title']
      scale=int(meta['c_scale'])
      edition=int(meta['editionNumber'])
      update=int(meta['updateNumber'])
      published=meta.get('editionDate','')
      updated=meta.get('issueDate','')

    print(cell,uband,scale,edition,update,updated,cellname)

    with (open(filename,'wb') as f):
      BO=BYTE_ORDER
      f.write(record(HEADER_SENC_VERSION,struct.pack(BO+'H',201)))
      f.write(record(HEADER_CELL_NAME,cellname.encode()+b'\0'))
      f.write(record(HEADER_CELL_PUBLISHDATE,published.encode()+b'\0'))
      f.write(record(HEADER_CELL_EDITION,struct.pack(BO+'H',edition)))
      f.write(record(HEADER_CELL_UPDATEDATE,updated.encode()+b'\0'))
      f.write(record(HEADER_CELL_UPDATE,struct.pack(BO+'H',update)))
      f.write(record(HEADER_CELL_NATIVESCALE,struct.pack(BO+'I',scale)))
      f.write(record(HEADER_CELL_SENCCREATEDATE,created.encode()+b'\0'))
      f.write(record(HEADER_CELL_SOUNDINGDATUM,sdatum.encode()+b'\0'))
      f.write(record(CELL_EXTENT_RECORD,struct.pack(BO+'8d',S,W,N,W,N,E,S,E)))
      for r in coverage(features): f.write(r)

      fid=0

      def next_id():
        nonlocal fid
        fid+=1
        return fid

      nodes={}
      edges={}

      def contours(coordinates, ptype):
        assert ptype in (2,3), ptype
        r,m=b'',0
        conts=[]
        for c in coordinates:
          edge=[(x-cx,y-cy) for x,y in map(lambda x:ll2grid(*x),c)]
          conts.append(edge)
          assert len(edge)>=2, edge

          # first/last node of edge
          node0,node1=edge[0],edge[-1]

          node0_id=find_key(nodes,node0)
          if not node0_id:
            node0_id=len(nodes)+1
            nodes[node0_id]=node0
          # else: print('node',node0_id)

          if ptype==3:
            assert node0==node1, 'polygon not closed'
            node1_id=node0_id
          else:
            node1_id=find_key(nodes,node1)
            if not node1_id:
              node1_id=len(nodes)+1
              nodes[node1_id]=node1

          # inner nodes of edge
          edge=edge[1:-1]
          edge_id=0
          if edge:
            edge_id=find_key(edges,edge)
            if not edge_id:
              edge_id=len(edges)+1
              edges[edge_id]=edge
            # else: print('edge',edge_id)
          # print((node0_id,edge_id,node1_id,0))
          r+=struct.pack(BO+'IIII',node0_id,edge_id,node1_id,0)
          m+=1

        S,N,W,E=bounds(coordinates) # feature bounds

        if ptype==2:
          return record(FEATURE_GEOMETRY_RECORD_LINE,struct.pack(BO+'ddddI',S,N,W,E,m)+r)

        if ptype==3:
          t=struct.pack(BO+f'{m}I',*[len(c) for c in conts]) # points per contour

          if len(conts)>1: print('skipping holes in polygon')
          polygon=conts[0] # outer contour only
          assert polygon[0]==polygon[-1]

          if polygon:
            polygon=polygon[:-1]
            n=len(polygon)

            trias=triangle.triangulate({
              'vertices': polygon,
              'segments': [[i,(i+1)%n] for i in range(n)],
            },'p')
            verts=trias['vertices']
            trias=trias['triangles']
            trias=[[verts[i] for i in tri] for tri in trias]
          else:
            trias=[]

          k=1
          ttype=4 # 4=tris 5=strip 6=fan
          t+=struct.pack(BO+'BIdddd',ttype,3*len(trias),W,E,S,N)
          for tri in trias:
            assert len(tri)==3
            for v in tri:
              t+=struct.pack(BO+'ff',*v)

          return record(FEATURE_GEOMETRY_RECORD_AREA,struct.pack(BO+'ddddIII',S,N,W,E,len(conts),k,m)+t+r)


      for o in features:
        p=o['properties']
        l=p['layer']
        if l.upper()=='SOUNDG': continue
        g=o['geometry']
        gtype=g['type']
        ptype=PRIMITIVES[gtype]
        c=g['coordinates']
        if len(l)!=6: continue
        ftype=acronym_code(l)
        if ftype is None:
          print('skipped',l)
          continue
        # print(l,ftype)
        primitives={PRIMITIVES[v] for v in s57obj[ftype][6]}
        if ptype not in primitives:
          print('skipped invalid primitive',l,gtype)
          continue
        f.write(record(FEATURE_ID_RECORD,struct.pack(BO+'HHB',ftype,next_id(),ptype-1)))

        for r in attributes(p): f.write(r)

        if gtype=='Point':
          f.write(record(FEATURE_GEOMETRY_RECORD_POINT,struct.pack(BO+'dd',c[1],c[0])))

        elif 'Line' in gtype:
          if 'Multi' not in gtype: c=[c]
          f.write(contours(c,ptype))

        elif 'Polygon' in gtype:
          if 'Multi' in gtype:
            print('skipped',gtype,l)
            continue
          f.write(contours(c,ptype))
        # else: print('skipped',l,gtype,ptype)

      if nodes:
        # print('nodes',len(nodes))
        r=struct.pack(BO+'I',len(nodes))
        for i,xy in nodes.items():
          r+=struct.pack(BO+'Iff',i,*xy)
        f.write(record(VECTOR_CONNECTED_NODE_TABLE_RECORD,r))

      if edges:
        # print('edges',len(edges))
        r=struct.pack(BO+'I',len(edges))
        for i,e in edges.items():
          r+=struct.pack(BO+'II',i,len(e))
          for xy in e:
            r+=struct.pack(BO+'ff',*xy)
        f.write(record(VECTOR_EDGE_NODE_TABLE_RECORD,r))



      # soundings as 3D multipoints
      soundings=defaultdict(list)
      for s in filter(lambda o:o['properties']['layer'].upper()=='SOUNDG',features):
        p=str({k:v for k,v in s['properties'].items() if k.upper()!='DEPTH'})
        soundings[p].append(s)

      ftype=acronym_code('SOUNDG')
      # print('SOUNDGs',len(soundings))
      for sdgs in soundings.values():
        s=sdgs[0]
        props={k:v for k,v in s['properties'].items() if k.upper()!='DEPTH'}
        f.write(record(FEATURE_ID_RECORD,struct.pack(BO+'HHB',ftype,next_id(),1)))
        for r in attributes(props): f.write(r)
        s,n,w,e=bounds([s['geometry']['coordinates'] for s in sdgs])
        r=struct.pack(BO+'4dI',s,n,w,e,len(sdgs))
        for s in sdgs:
          c=s['geometry']['coordinates']
          x,y=[a-b for a,b in zip(ll2grid(*c),(cx,cy))]
          d=s['properties'].get('DEPTH') or s['properties'].get('depth',0)
          r+=struct.pack(BO+'fff',x,y,d)
        f.write(record(FEATURE_GEOMETRY_RECORD_MULTIPOINT,r))

      f.write(b'\0')


def read_features(files):
    features=[]
    for f in files:
        layer=os.path.splitext(os.path.basename(f))[0]
        with open(f) as g:
          data=json.load(g)
          for o in data['features']:
            p=o['properties']
            p['layer']=p.get('layer',layer)
            features.append(o)
    return features


def main():
    parser = argparse.ArgumentParser(description="senc converter: senc <--> geojson")
    parser.add_argument('-o',"--output", help="output dir", default='.')
    parser.add_argument("input", help="input files (senc/json)", nargs="+")
    args = parser.parse_args()

    files = args.input
    out = args.output
    os.makedirs(out, exist_ok=True)

    if files[0].endswith('json'):
        data=read_features(files)
        field='chart'
        charts=set(filter(lambda o:o,(o['properties'].get(field) for o in data)))
        print(len(charts),'charts')
        for c in sorted(charts):
          data1=list(filter(lambda o:o['properties'].get(field)==c,data))
          s,n,w,e=bounds(data1)
          uband=min(o['properties'].get('uband',0) for o in data1)

          def filt(o):
            if field in o['properties']: return
            if o['geometry']['type']!='Point': return
            if o['properties'].get('uband')!=uband: return
            lon,lat=o['geometry']['coordinates']
            return w<=lon<=e and s<=lat<=n

          data2=list(filter(filt,data))
          write_senc(os.path.join(out,c+'.senc'),data1+data2)
        return


    features = read_senc(files)
    for l in sorted({f.properties['layer'] for f in features}):
        fs = list(filter(lambda f: f.properties['layer'] == l, features))
        print(l, len(fs))
        save_json(f"{out}/{l}.json", FeatureCollection(fs))


if __name__ == "__main__":
    main()
