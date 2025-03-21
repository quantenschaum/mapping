#!/usr/bin/env python3
# coding: utf-8

import json
import os
import sys
import re
from collections import defaultdict
from itertools import groupby, permutations, combinations_with_replacement, product, pairwise, chain
from os import makedirs
from os.path import dirname, exists
from time import sleep
from types import NoneType
from s57 import resolve, abbr_color
from pyquery import PyQuery as pq

def load_json(filename):
  with open(filename) as f:
    return json.load(f)


def save_json(filename,data,**kwargs):
  makedirs(dirname(filename) or '.',exist_ok=1)
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

BANDS={
  'Overview':1,
  'General':2,
  'Coastal':3,
  'Coastel':3,
  'Approach':4,
  'Harbor':5,
  'Harbour':5,
  'Berthing':6,
}

def band(fid):
  b=list(filter(fid.startswith,BANDS.keys()))
  # print(fid,b)
  if len(b)==1:
    return BANDS[b[0]]


def light_spec(data):
  data=dict(data)
  data.update(resolve(data))

  ch=data.get('LITCHR','?')
  ch+=data.get('SIGGRP','').replace('()','').replace('(1)','')

  co=data.get('COLOUR',' ')[0].upper().replace(' ','').replace('W','')

  pe=data.get('SIGPER')
  pe=f'{pe}s' if pe else ''

  ra=data.get('VALMNR')
  ra=f'{pe}M' if ra else ''

  he=data.get('HEIGHT')
  he=f'{he}m' if he else ''

  ex=data.get('EXCLIT')
  ex=f'({ex})' if ex else ''

  return ' '.join(filter(bool,[ch,co,pe,he,ra]))

def number(s):
  if isinstance(s,str):
    for t in [int,float]:
      try:
        return t(s)
      except: continue
  return s


def array(s,etype=int):
  try:
    return list(map(etype,s.split(',')))
  except:
    return s


def parse(s):
  # return s
  return number(s)
  # return array(number(s))


TYPES = None, int, float, list, str

def data_types(features):
  types={}
  for f in features:
    for k,v in f['properties'].items():
      t=types.get(k)
      st=type(parse(v))
      # print(k,v,st)
      types[k]=max(t,st,key=TYPES.index)
      # print(st,t,types[k])
  return {k:(array if v==list else v) for k,v in types.items()}


def convert_xml(ifile,ofile):
  print('converting',ifile,'-->',ofile)
  xml=pq(filename=ifile)
  items=xml('item')
  print(len(items),'items')
  features=[]
  for i in items:
    i=pq(i)
    title=i('title').text()
    # print(title)
    gtype,coords=None,None

    if not gtype:
      try:
        coords=i(r'georss\:point').text()
        assert coords
        coords=list(map(float,coords.split()))
        assert len(coords)%2==0,str(i)
        coords=list(zip(coords[1::2], coords[::2]))
        if len(coords)>2:
          gtype='MultiPoint'
        else:
          gtype='Point'
          coords=coords[0]
      except: pass

    if not gtype:
      try:
        coords=i(r'georss\:line').text()
        assert coords
        coords=list(map(float,coords.split()))
        assert len(coords)%2==0,str(i)
        coords=list(zip(coords[1::2], coords[::2]))
        gtype='LineString'

        r=[]
        rings=[]
        for c in coords:
          if len(r)==0: rings.append(r)
          r.append(c)
          if len(r)>1 and r[0]==r[-1]: r=[]
        # if len(rings)<2: continue
        # print('lines',len(rings))

        if len(rings)>1:
          gtype='MultiLineString'
          coords=rings
      except: pass

    if not gtype:
      try:
        coords=i(r'georss\:polygon').text()
        assert coords
        coords=list(map(float,coords.split()))
        assert len(coords)%2==0,str(i)
        coords=list(zip(coords[1::2], coords[::2]))

        r=[]
        rings=[]
        for c in coords:
          if len(r)==0: rings.append(r)
          r.append(c)
          if len(r)>1 and r[0]==r[-1]: r=[]
        # if len(rings)<2: continue
        # print('polygons',len(rings),rings)

        coords=rings
        gtype='Polygon'
      except: pass

    # if not (gtype and coords): continue
    assert gtype and coords,(title,gtype,coords,str(i))

    # print(gtype,coords)
    desc=pq(i('description').text())
    # print(desc)
    props={}
    for li in desc('li'):
      li=pq(li)
      # print(li)
      key=pq(li('span[class="atr-name"]')).text().strip()
      val=pq(li('span[class="atr-value"]')).text().strip()
      val=parse(val)
      # print(key,'=',val)
      props[key]=val

    f={
      'type':'Feature',
      'id':title,
      'properties':props,
      'geometry':{
        'type':gtype,
        'coordinates':coords,
      },
    }
    # print(f)
    features.append(f)
    # break
  save_json(ofile,{ 'type':'FeatureCollection', 'features':features })

def main():
  ifile = sys.argv[1] if len(sys.argv)>1 else None
  ofile = sys.argv[2] if len(sys.argv)>2 else None

  if ifile.endswith('.xml'):
    jfile=ifile.replace('.xml','.json')
    convert_xml(ifile,jfile)
    ifile=jfile

  if ofile=='.': ofile=ifile

  print('processing', ifile, '-->', ofile)

  data=load_json(ifile)

  features=data['features']

  for f in features:
    props=f['properties'] # make upper case keys for 6 char fields
    props={k.upper() if len(k)==6 else k:v for k,v in props.items()}
    f['properties']=props

    # remove empty data values
    for k,v in dict(props).items():
      if v is None:
        del props[k]
        continue
      if isinstance(v,str):
        v=v.strip()
        if not v:
          del props[k]
          continue
        props[k]=v

  # determine type of each field
  dtypes=data_types(features)
  # for k,v in dtypes.items(): print(k,v)

  for f in features:
    props=f['properties']

    # convert values to determined types
    props={k:dtypes[k](v) for k,v in props.items()}
    f['properties']=props

    # add usage bands
    if 'id' in f:
      b=band(f['id'])
      if b:
        # if props.get('MARSYS'): b-=1
        props['uband']=b

    name=props.get('name')
    if name:
      m=re.match(r'(.+)\.000$',name)
      if m:
        props['name']=m.group(1)

    if 'chart' not in props:
      name=props.get('name')
      if name:
        props['chart']=name
      dsnm=props.get('dsnm')
      if dsnm:
        props['chart']=dsnm.replace('.000','')

    # if 'LITCHR' in props:
    #   props['light']=light_spec(props)

    # props.update(resolve(props,'_'))
    # if 'litchr' in props: print(props['light_'])

    # for k in ['COLOUR']:
    #   v=props.get(k)
    #   if v:
    #     res=resolve({k:v},'_')
    #     if res:
    #       res[k+'__']=''.join(c[0] for c in res[k+'_'].split('_')).upper()
    #       props.update(res)

    cols=props.get('COLOUR')
    if cols:
      cs = ''.join(map(abbr_color,map(int, str(cols).split(','))))
      props['color']=cs

    if 'catgeo' not in props:
      g=f['geometry']['type']
      props['catgeo']=1 if 'Point' in g else 2 if 'Line' in g else 3 if 'Polygon' in g else 0

    if 'layer' not in props:
      l=layer(props)
      if l: props['layer']=l

  # remove old and HD charts - https://linchart60.bsh.de/chartserver/katalog.xml
  features=data['features']=[f for f in features if f['properties'].get('chart','xxxNO')[3:5] in ('NO','OS')]
  assert features

  if ofile:
    save_json(ofile,data)

  layers=set(filter(lambda x:x,(f['properties'].get('layer') for f in features)))
  for l in layers:
    filt = lambda f: f['properties'].get('layer')==l
    fn=f'{sys.argv[3]}/{ifile[0]}-{l}.json'
    save_json(fn, {"type": "FeatureCollection", "features": list(filter(filt,features))})

  unmatched=list(filter(lambda f:'layer' not in f['properties'],features))
  if unmatched:
    print('unmatched',len(unmatched))
    fn=f'{sys.argv[3]}/{ifile[0]}-unmatched.json'
    save_json(fn, {"type": "FeatureCollection", "features": unmatched})

  return
  values=group_keys(features,1)
  print()

  for k in sorted(values.keys()):
    if '_type' not in k: continue
    for v in sorted(values[k]):
      print(k,'=',v)
      filt = lambda f: f['properties'].get(k)==v
      group_keys(features,log=1, filt=filt)
      print()

      # if len(sys.argv)>3:
      #   fn=f'{sys.argv[3]}/{ifile[0]}-{k}={v}.json'
      #   save_json(fn, {"type": "FeatureCollection", "features": list(filter(filt,features))})

    if len(sys.argv)>3:
      filt = lambda f: f['properties'].get(k) is not None
      fn=f'{sys.argv[3]}/{ifile[0]}-{k}.json'
      save_json(fn, {"type": "FeatureCollection", "features": list(filter(filt,features))})

# https://github.com/OpenCPN/OpenCPN/tree/master/data/s57data
from sconvert import read_csv
csvdir=os.path.dirname(__file__)
s57obj = read_csv(csvdir+"/s57objectclasses.csv")
s57attr = read_csv(csvdir+"/s57attributes.csv")

def unique_attributes():
  attributes=defaultdict(lambda: defaultdict(set))
  GEOMS={'Point':1,'Line':2,'Area':3}
  for v in s57obj.values():
    layer,attr,cls,geoms=v[1],v[2:5],v[5],v[6]
    geoms = list(map(GEOMS.get,geoms)) if isinstance(geoms,list) else None
    # print(layer,geoms)
    if not geoms: continue
    for g in geoms:
      for a in [x for xs in attr for x in xs]:
        if len(a)==6:
          attributes[a][g].add(layer)
  unique={a:{g:s.pop() for g,s in d.items() if len(s)==1} for a,d in attributes.items()}
  unique={a:d for a,d in unique.items() if d}
  del unique['catcbl']
  del unique['watlev']
  return unique

UNIQUE_ATTRS=unique_attributes()
# for i in UNIQUE_ATTRS.items(): print(i)


def layer(props):
  g=int(props.get('catgeo',0))
  point,line,area = g==1, g==2, g==3

  if props.get('util_type')==1 and area:
    return 'CBLARE'
  if props.get('util_type')==1 and line:
    return 'CBLOHD'
  if props.get('util_type')==2 and line:
    return 'CBLSUB'

  for a,ls in UNIQUE_ATTRS.items():
    if a.upper() in props or a.lower() in props:
      if g in ls: return ls[g]

  if 'BOYSHP' in props and point:
    if 'CATLAM' in props:
      return 'BOYLAT'
    if 'CATCAM' in props:
      return 'BOYCAR'
    if 'CATSPM' in props:
      return 'BOYSPP'
    if all(c in str(props.get('COLOUR','')) for c in '13'):
      return 'BOYSAW'
    if all(c in str(props.get('COLOUR','')) for c in '23'):
      return 'BOYISD'
    return 'BOYSPP'

  if 'BCNSHP' in props and point:
    if 'CATLAM' in props:
      return 'BCNLAT'
    if 'CATCAM' in props:
      return 'BCNCAR'
    if 'CATSPM' in props:
      return 'BCNSPP'
    if all(c in str(props.get('COLOUR','')) for c in '13'):
      return 'BCNSAW'
    if all(c in str(props.get('COLOUR','')) for c in '23'):
      return 'BCNISD'
    return 'BCNSPP'

  if props.get('beacon_type') and point:
    return 'BCNSPP'

  if 'TOPSHP' in props and point:
    return 'DAYMAR'
  if props.get('caution_type')==2:
    return 'OBSTRN'
  if props.get('caution_type')==6:
    return 'UWTROC'
  if 'MARSYS' in props or props.get('meta_type')==6:
    return 'M_NSYS'
  if props.get('signal_type')==1 and line:
    return 'RADLNE'
  if props.get('signal_type')==5 and point:
    return 'RTPBCN'
  if 'CATCRN' in props and (point or area):
    return 'CRANES'
  if 'TRAFIC' in props and point:
    return 'RDOCAL'
  if 'CATWED' in props or props.get('caution_type')==8:
    return 'WEDKLP'
  if 'NATSUR' in props and props.get('caution_type')==4:
    return 'SBDARE'
  if 'VALDCO' in props and line:
    return 'DEPCNT'
  if 'ELEVAT' in props and point:
    return 'LNDELV'
  if 'CATBRG' in props:
    return 'BRIDGE'
  if 'DRVAL1' in props and 'DRVAL2' in props and area:
    return 'DEPARE'
  if props.get('land_type')==1 and (point or area):
    return 'BUAARE'
  if props.get('depth_type')==1 and area:
    return 'LAKARE'
  if props.get('land_type')==4 and area:
    return 'LAKARE'
  if props.get('land_type')==7 and area:
    return 'PRDARE'
  if props.get('land_type')==5:
    return 'LNDARE'
  if props.get('land_type')==6 and (point or area):
    return 'LNDRGN'
  if props.get('land_type')==9:
    return 'RIVERS'
  if props.get('land_type')==10:
    return 'SLOGRD'
  if props.get('mark_type')==2:
    return 'DISMAR'
  if props.get('trans_type')==3 and (line or area):
    return 'CANALS'
  if props.get('trans_type')==7:
    return 'ROADWY'
  if props.get('dock_type')==4 and area:
    return 'DOCARE'
  if props.get('depth_type')==2 and area:
    return 'DRGARE'
  if props.get('caution_type')==4:
    return 'TIDEWY'
  if 'CATREA' in props and area:
    return 'RESARE'
  if 'CATACH' in props and (point or area):
    return 'ACHARE'
  if props.get('coast_type')==1 and area:
    return 'SEAARE'
  if props.get('coast_type')==1 and line:
    return 'COALNE'
  if 'CATPIP' in props and area:
    return 'PIPARE'
  if 'CATPIP' in props and line:
    return 'PIPSOL'
  if 'CATCBL' in props and area:
    return 'CBLARE'
  if 'CATCBL' in props and line:
    return 'CBLSUB'
  if props.get('util_type')==4 and line:
    return 'PIPSOL'
  if 'RYRMGV' in props and 'VALACM' in props and 'VALMAG' in props:
    return 'MAGVAR'

  if props.get('zone_type')==1 and area:
    return 'DWRTPT'
  if props.get('zone_type')==2 and area:
    return 'FAIRWY'
  if props.get('zone_type')==4 and line:
    return 'RCRTCL'
  if props.get('zone_type')==4 and area:
    return 'ISTZNE'
  if props.get('zone_type')==7 and area:
    return 'RCTLPT'
  if props.get('zone_type')==17 and area:
    return 'MIPARE'
  if props.get('zone_type')==10 and area:
    return 'FISGRD'

  if 'CATTSS' in props:
    if props.get('zone_type')==6 and line:
      return 'TSELNE'
    if props.get('zone_type')==7 and line:
      return 'TSSBND'
    if props.get('zone_type')==8 and area:
      return 'TSSCRS'
    if props.get('zone_type')==9 and area:
      return 'TSSLPT'
    if props.get('zone_type')==11 and area:
      return 'TSEZNE'

  if props.get('zone_type')==11 and area:
    return 'HRBARE'

  if props.get('zone_type')==18 and area:
    return 'OSPARE'
  if props.get('zone_type')==19 and area:
    return 'RESARE'
  if props.get('zone_type')==5 and line:
    return 'RECTRC'
  if props.get('berth_type')==2 and area:
    return 'ACHARE'

  if 'Radar' in props.get('OBJNAM','') and area:
    return 'RADRNG'
  if 'RADAR' in props.get('OBJNAM','') and area:
    return 'RADRNG'

  if props.get('light_type')==3 and point:
    return 'PILPNT'

  if 'FUNCTN' in props or props.get('facility_type')==1:
    return 'BUISGL'
  if props.get('facility_type')==3 and area:
    return 'CRANES'
  if props.get('facility_type')==4:
    return 'CRANES'
  if props.get('facility_type')==7 and point:
    return 'HRBFAC'
  if props.get('facility_type')==7 and area:
    return 'HULKES'
  if props.get('facility_type')==12 and (line or area):
    return 'PONTON'
  if props.get('facility_type')==9:
    return 'LNDMRK'
  if props.get('facility_type')==11 and (point or area):
    return 'OFSPLF'
  if props.get('facility_type')==13 and point:
    return 'RSCSTA'
  if props.get('facility_type')==6 and area:
    return 'HRBARE'

  if props.get('light_type')==1 and point:
    return 'DAYMAR'
  if props.get('light_type')==6 and point:
    return 'LIGHTS'
  if props.get('signal_type')==2 and point:
    return 'RADSTA'
  if props.get('trans_type')==9:
    return 'TUNNEL'
  if props.get('trans_type')==8:
    return 'RUNWAY'
  if props.get('trans_type')==2:
    return 'BRIDGE'
  if props.get('trans_type')==1 and (point or area):
    return 'AIRARE'
  if props.get('dock_type')==5 and area:
    return 'LOKBSN'
  if props.get('dock_type')==3 and (line or area):
    return 'FLODOC'
  if props.get('dock_type')==2 and area:
    return 'DRYDOC'
  if props.get('coast_type')==2:
    return 'SLCONS'
  if props.get('trans_type')==5 and line:
    return 'RAILWY'
  if props.get('trans_type')==4 and line:
    return 'CONVYR'
  if props.get('trans_type')==4 and area:
    return 'CAUSWY'
  if props.get('trans_type')==6 and area:
    return 'PYLONS'
  if props.get('land_type')==7 and (line or area):
    return 'RIVERS'
  if props.get('land_type')==4:
    return 'LNDELV'
  if props.get('land_type')==2 and line:
    return 'DYKCON'
  if props.get('land_type')==2 and area:
    return 'DAMCON'
  if props.get('land_type')==8 and (line or area):
    return 'SLOTOP'
  if props.get('berth_type')==3:
    return 'BERTHS'
  if props.get('util_type')==3 and line:
    return 'PIPOHD'



def group_keys(features, log=0, filt=None):
  values={}
  count=0
  if filt:
    features=filter(filt,features)
  for f in features:
    count+=1
    props=f.get('properties',f)
    for k,v in props.items():
      s=values.get(k)
      if not s:
        s=set()
        values[k]=s
      try: s.add(v)
      except: s.add(repr(v))

  if log:
    print(f'features: {count}')
    for k in sorted(values.keys()):
      vals=values[k]
      t=type(list(vals)[0])
      vals=', '.join(map(str,vals))
      print(f'{k:6} ({t.__name__ if t else None}):',vals[:200],'...' if len(vals)>200 else '')

  return values



if __name__=='__main__':
  main()
