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

def load_json(filename):
    with open(filename) as f:
        return json.load(f)


def save_json(filename,data,**kwargs):
    makedirs(dirname(filename) or '.',exist_ok=1)
    with open(filename,'w') as f:
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


def main():
  ifile = sys.argv[1] if len(sys.argv)>1 else None
  ofile = sys.argv[2] if len(sys.argv)>2 else None
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
