#!/usr/bin/env python3
# coding: utf-8

import json
import sys
import re
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

  if ofile:
    save_json(ofile,data)

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
