#!/usr/bin/env python3
# coding: utf-8

import csv
import json
from datetime import datetime
import argparse
from collections import defaultdict
from itertools import accumulate
from os import makedirs
from os.path import basename, splitext, dirname, join

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

try:
  import shapely
  import numpy as np
  import mapbox_earcut as earcut
except: pass

from senc import SENC, grid2ll, ll2grid, S57_RECORD_TYPES, HEADER_CELL_NAME, HEADER_CELL_PUBLISHDATE, HEADER_CELL_EDITION, HEADER_CELL_UPDATEDATE, HEADER_CELL_UPDATE, HEADER_CELL_NATIVESCALE, HEADER_CELL_SENCCREATEDATE, CELL_EXTENT_RECORD, HEADER_CELL_SOUNDINGDATUM, FEATURE_ID_RECORD, FEATURE_GEOMETRY_RECORD_POINT, VECTOR_CONNECTED_NODE_TABLE_RECORD, VECTOR_EDGE_NODE_TABLE_RECORD, FEATURE_ATTRIBUTE_RECORD, CELL_COVR_RECORD, CELL_NOCOVR_RECORD, FEATURE_GEOMETRY_RECORD_MULTIPOINT, FEATURE_GEOMETRY_RECORD_LINE, FEATURE_GEOMETRY_RECORD_AREA, write_txt, senc2s57

def to(typ, val):
    try: return typ(val)
    except: return val


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
csvdir=dirname(__file__)
s57obj = read_csv(csvdir+"/s57objectclasses.csv")
s57attr = read_csv(csvdir+"/s57attributes.csv")

def catalog():
  try:
    with open(dirname(__file__)+'/../data/bsh/catalog.json') as f:
          return json.load(f)
  except: return {}

CATALOG=catalog()
# print(CATALOG)

def layer_name(c): return s57obj[c][1]

def attr_name(c): return s57attr[c][1]

def acronym_code(name):
    name=name.upper()
    for k,v in s57attr.items():
        if name==v[1].upper():
            return k
    for k,v in s57obj.items():
        if name==v[1].upper():
            return k

def senc2features(filename, txtdir=None, multipoints=False):
  'convert SENC records to GeoJSON features'
  recs=SENC(filename).records()

  features=[]
  node_table,edge_table={},{}

  chart=splitext(basename(filename))[0]
  uband=int(chart[-1])

  for r in recs: # first pass
    if r['name']=='cell_native_scale':
      scale=r['scale']
      continue

    if r['name']=='cell_name':
      chart=r['cellname'] or chart
      uband=int(chart[-1])
      continue

    if r['name']=='cell_extent':
      cs,cw=r['sw']
      cn,ce=r['ne']
      clat,clon=(cs+cn)/2,(cw+ce)/2
      cx,cy=ll2grid(clon,clat)
      continue

    if r['name']=='node_table':
      s=r.get('scale',1)
      for i,n in r['nodes'].items():
        assert i not in node_table, f'duplicate node {i}'
        node_table[i]=grid2ll(cx+n[0]/s,cy+n[1]/s)
      continue

    if r['name']=='edge_table':
      s=r.get('scale',1)
      for i,e in r['edges'].items():
        assert i not in edge_table, f'duplicate edge {i}'
        edge_table[i]=[grid2ll(cx+n[0]/s,cy+n[1]/s) for n in e]
      continue

    if r['name']=='text' and txtdir:
      with open(join(txtdir,r['file']),'w') as f:
        f.write(r['text'])
      continue

  props0={'chart':chart, 'uband':uband, 'scale':scale}

  for r in recs: # second pass
    if r['name']=='feature':
      layer=layer_name(r['ftype'])
      ptype=r['primitive']+1
      props=props0.copy()
      props['layer']=layer
      continue

    if r['name']=='attribute':
      props[attr_name(r['atype'])]=r['value']
      continue

    if r['name']=='point':
      assert ptype==1
      p=Point((r['lon'],r['lat']))
      f=Feature(geometry=p, properties=props)
      features.append(f)
      continue

    if r['name']=='multipoint':
      assert ptype==1
      if multipoints:
        p=MultiPoint([grid2ll(cx+p[0],cy+p[1])+(round(p[2],1),) for p in r['points']])
        f = Feature(geometry=p, properties=props)
        features.append(f)
      else:
        for x, y, depth in r['points']:
          props['VALSOU'] = round(depth,1)
          p = Point(grid2ll(cx+x,cy+y))
          f = Feature(geometry=p, properties=props.copy())
          features.append(f)
      continue

    def contours(edgelist,pc=None):
      line,lines,s,e = None,[],None,None
      for n0, ed, n1, flip in edgelist:
        if n0 != e: # start of new segment
        # if e is None: # start of new segment
          if line: lines.append(line)
          line = []
          s=n0
          line.append(node_table[n0])
          # print('\nline',end=' ')
        # print((n0,ed,n1),end=' ')
        if ed in edge_table:
          line += (reversed(edge_table[ed]) if flip else edge_table[ed]) if ed else []
        elif ed: print('skipped invalid edge')
        line.append(node_table[n1])
        e = None if n1==s else n1 # e=None if closed loop
        # if pc and len(line)>=pc[len(lines)]: e=None
      lines.append(line)
      # print()
      for l in lines:
        for a,b in zip(l[:-1],l[1:]): assert a!=b, 'repeated nodes'
      return lines

    if r['name']=='line':
      assert ptype==2
      lines=contours(r['edges'])
      l = LineString(lines[0]) if len(lines)==1 else MultiLineString(lines)
      f = Feature(geometry=l, properties=props)
      features.append(f)
      continue

    if r['name']=='area':
      assert ptype==3
      assert r['contours']==len(r['pointcount']),(r['contours'],len(r['pointcount']))
      # print(r['contours'])
      lines=contours(r['edges'],r['pointcount'])
      # assert len(lines)==r['contours'],(len(lines),r['contours'])
      for i,l in enumerate(lines):
        assert l[0]==l[-1],'polygon not closed'
        # assert len(l)==r['pointcount'][i],(len(l),r['pointcount'][i])
      l = Polygon(lines)
      f = Feature(geometry=l, properties=props)
      features.append(f)
      continue

  return features




def write_json(filename,data,**kwargs):
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



def sort_key(feature):
  p=PRIMITIVES[feature['geometry']['type']]
  if p==1: return 2
  if p==2: return 1
  c=feature['geometry']['coordinates']
  if 'Multi' in feature['geometry']['type']: c=c[0] # first polygon
  p=shapely.Polygon(c[0]) # outer contour
  return -abs(p.area) # sort by area, to get polygons big first, small last



def features2senc(filename,features):
    features=sorted(features, key=sort_key)

    S,N,W,E=bounds(features) # cell/chart bounds
    assert S<N and W<E
    clon,clat=(W+E)/2,(S+N)/2 # cell center lon, lat
    cx,cy=ll2grid(clon,clat) # cell center in grid coordinates

    version=201 if filename.endswith('.senc') else 200
    chart=cell=min(o['properties'].get('chart','chart') for o in features)
    uband=min(o['properties'].get('uband',0) for o in features)
    scamax=min(o['properties'].get('SCAMAX',999999) for o in features)
    scamin=max(o['properties'].get('SCAMIN',0) for o in features)
    scale=max(o['properties'].get('scale',0) for o in features) or SCALES.get(uband,0) or scamin
    sdatum=''
    edition=1
    published=''
    update=0
    updated=''

    # give overlapping cells not exactly the same scale
    # to prevent duplicate data to be rendered
    scale+=hash(chart)%100

    meta=CATALOG.get(cell)
    if meta:
      cell=meta['c_title']
      scale=int(meta['c_scale'])
      edition=int(meta['editionNumber'])
      update=int(meta['updateNumber'])
      published=meta.get('editionDate','')
      updated=meta.get('issueDate','')
    # else: return

    print(f'{chart} u{uband} 1:{scale} ed{edition} up{update} {cell}')
    assert edition>0,edition

    with SENC(filename,'w') as senc:
      senc.add_record(type=HEADER_CELL_NAME, cellname=cell)
      senc.add_record(type=HEADER_CELL_PUBLISHDATE, published=published)
      senc.add_record(type=HEADER_CELL_EDITION, edition=edition)
      senc.add_record(type=HEADER_CELL_UPDATEDATE, updated=updated)
      senc.add_record(type=HEADER_CELL_UPDATE, update=update)
      senc.add_record(type=HEADER_CELL_NATIVESCALE, scale=scale)
      senc.add_record(type=HEADER_CELL_SENCCREATEDATE, created=datetime.now().strftime('%Y%m%d'))
      # senc.add_record(type=HEADER_CELL_SOUNDINGDATUM, datum=sdatum)

      senc.add_record(type=CELL_EXTENT_RECORD,sw=(S,W),se=(S,E),ne=(N,E),nw=(N,W))

      def coverage(features):
        k=0
        for f in filter(lambda f:f['properties'].get('layer','').upper()=='M_COVR',features):
          g=f['geometry']
          assert g['type']=='Polygon',g
          c=g['coordinates']
          # assert len(c)==1,'coverage has holes'
          # verts=[y[i] for x in c for y in x for i in (1,0)]
          if len(c)>1: print('skipping holes in coverage')
          verts=[x[i] for x in c[0] for i in (1,0)]
          catcov=f['properties'].get('CATCOV',1)==1
          ctype=CELL_COVR_RECORD if catcov else CELL_NOCOVR_RECORD
          # print('coverage',catcov)
          senc.add_record(type=ctype,array=verts)
          k+=1
        return k

      if not coverage(features): # set coverage to bbox if no M_COVR present
        coverage([{'type':'Feature',
                   'properties':{'layer':'M_COVR','CATCOV':1},
                   'geometry':{'type':'Polygon','coordinates':[[(W,S),(E,S),(E,N),(W,N),(W,S)]]}}])

      nodes,edges={},{}

      def contours(coordinates, ptype):
        assert ptype in (2,3), ptype
        conts=[]
        edge_ids=[]
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

          edge=edge[1:-1] # inner nodes of edge
          edge_id=0
          if edge:
            edge_id=find_key(edges,edge)
            if not edge_id:
              edge_id=len(edges)+1
              edges[edge_id]=edge
            # else: print('edge',edge_id)
          edge_ids.append((node0_id,edge_id,node1_id,0))

        bbox=bounds(coordinates) # feature bounds

        if ptype==2:
          senc.add_record(type=FEATURE_GEOMETRY_RECORD_LINE, bbox=bbox, edges=edge_ids)

        if ptype==3:
          def triangulate(polygon):
            verts=np.array([v for c in polygon for v in c]).reshape(-1,2)
            rings=list(accumulate(len(c) for c in polygon))
            indices=earcut.triangulate_float32(verts, rings)
            return [verts[i] for i in indices]

          # ttype: 4=tris 5=strip 6=fan
          senc.add_record(type=FEATURE_GEOMETRY_RECORD_AREA, bbox=bbox,
                          contours=len(conts), pointcount=[len(c) for c in conts], edges=edge_ids,
                          triangles=[{'ttype':4, 'bbox':bbox[2:4]+bbox[:2], 'vertices':triangulate(conts)}])


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
          # print(a,v,acronym_code(a),vtype,type(v))
          senc.add_record(type=FEATURE_ATTRIBUTE_RECORD,atype=atype,value=v)


      for f in features:
        p=f['properties']
        l=p['layer']
        if l.upper()=='SOUNDG': continue
        g=f['geometry']
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

        senc.add_record(type=FEATURE_ID_RECORD,ftype=ftype,primitive=ptype-1)
        attributes(p)

        if gtype=='Point':
          senc.add_record(type=FEATURE_GEOMETRY_RECORD_POINT,lat=c[1],lon=c[0])

        elif 'Line' in gtype:
          if 'Multi' not in gtype: c=[c]
          contours(c,ptype)

        elif 'Polygon' in gtype:
          if 'Multi' in gtype:
            for p in c: contours(p,ptype)
          else:
            contours(c,ptype)
        else: print('skipped',l,gtype,ptype)

      if nodes:
        # print('nodes',len(nodes))
        senc.add_record(type=VECTOR_CONNECTED_NODE_TABLE_RECORD,nodes=nodes)

      if edges:
        # print('edges',len(edges))
        senc.add_record(type=VECTOR_EDGE_NODE_TABLE_RECORD,edges=edges)



      # soundings as 3D multipoints
      soundings=defaultdict(list) # group by attributes
      for s in filter(lambda o:o['properties']['layer'].upper()=='SOUNDG',features):
        p=str({k:v for k,v in s['properties'].items() if k.upper()!='DEPTH'})
        soundings[p].append(s)

      ftype=acronym_code('SOUNDG')
      # print('SOUNDGs',len(soundings))
      for sdgs in soundings.values():
        s=sdgs[0]
        props={k:v for k,v in s['properties'].items() if k.upper() not in ('VALSOU','DEPTH')}
        senc.add_record(type=FEATURE_ID_RECORD, ftype=ftype, primitive=0)
        attributes(props)
        bbox=bounds([s['geometry']['coordinates'] for s in sdgs])
        points=[]
        for s in sdgs:
          c=s['geometry']['coordinates']
          x,y=[a-b for a,b in zip(ll2grid(*c),(cx,cy))]
          p=s['properties']
          d=p.get('VALSOU',p.get('DEPTH',p.get('depth')))
          if d is not None: points.append((x,y,d))
        senc.add_record(type=FEATURE_GEOMETRY_RECORD_MULTIPOINT, bbox=bbox, points=points)

def read_features(files):
    features=[]
    for fi in files:
      print(fi)
      layer=splitext(basename(fi))[0]
      with open(fi) as g:
        for f in json.load(g)['features']:
          p=f['properties']
          p['layer']=p.get('layer',layer)
          features.append(f)
    return features



def main():
    parser = argparse.ArgumentParser(description="chart converter: S57/SENC <--> GeoJSON and SENC --> S57")
    parser.add_argument('-o',"--output", help="output dir", default='.')
    parser.add_argument('-s',"--s57", help="convert SENC to S57", action='store_true')
    parser.add_argument("input", help="input files (senc/json)", nargs="+")
    args = parser.parse_args()

    files = args.input
    out = args.output
    makedirs(out, exist_ok=True)


    # SENC --> S57
    if args.s57:
      write_txt(join(out,'Chartinfo.txt'),f'ChartInfo:{basename(out)}\n')
      for fi in files:
        fo=join(out,basename(fi).replace('.senc','.S57'))
        print(fi,'-->',fo)
        senc2s57(fi,fo)
      return

    # GeoJSON --> SENC
    if files[0].endswith('json'):
      write_txt(join(out,'Chartinfo.txt'),f'ChartInfo:{basename(out)}\n')
      features=read_features(files)
      charts=set(filter(lambda f:f,(f['properties'].get('chart') for f in features)))
      print(len(charts),'charts')
      for c in sorted(charts):
        data1=list(filter(lambda f:f['properties'].get('chart')==c,features))
        s,n,w,e=bounds(data1)
        uband=min(o['properties'].get('uband',0) for o in data1)

        def filt(f):
          if 'chart' in f['properties']: return
          if f['geometry']['type']!='Point': return
          if f['properties'].get('uband')!=uband: return
          lon,lat=f['geometry']['coordinates']
          return w<=lon<=e and s<=lat<=n

        data2=list(filter(filt,features))
        features2senc(join(out,c+'.S57'),data1+data2)
      return


    # SENC --> GeoJSON
    features = []
    for f in files:
      print(f)
      features+=senc2features(f,out)

    for l in sorted({f.properties['layer'] for f in features}):
        fs = list(filter(lambda f: f.properties['layer'] == l, features))
        if l=='text':
          for f in fs:
            filename,text=f.properties['filename'],f.properties['text']
            print(filename)
            write_txt(join(out,filename),text)
          continue
        print(l, len(fs))
        write_json(f"{out}/{l}.json", FeatureCollection(fs))


if __name__ == "__main__":
    main()
