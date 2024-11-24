#!/usr/bin/env python3
# coding: utf-8

import json
import sys
import re

def load_json(filename):
    with open(filename) as f:
        return json.load(f)


def save_json(filename,data,**kwargs):
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


ZOOMS = [0,7,10,11,13,15,16]

def zooms(uband):
  return ZOOMS[uband-1]+1,ZOOMS[uband]


def main():
  ifile=sys.argv[1] if len(sys.argv)>1 else None
  ofile=sys.argv[2] if len(sys.argv)>2 else ifile
  # ifile='data/bsh/SkinOfTheEarth.json'
  # ofile='data/bsh/xxxSkinOfTheEarth.json'
  print('processing', ifile, '-->', ofile)
  data=load_json(ifile)
  for f in data['features']:
    props=f['properties']
    if 'id' in f:
      b=band(f['id'])
      if b:
        if props.get('marsys')==1: b-=1
        props['uband']=b

    for k in list(props.keys()):
      v=props[k]
      if type(v)==str:
        props[k]=v.strip()
        if not props[k]:
          del props[k]
          continue
        try: props[k]=int(v.strip())
        except:
          try: props[k]=float(v.strip())
          except: pass

    name=props.get('name')
    if name:
      m=re.match(r'(.+)\.000$',name)
      if m:
        props['name']=m.group(1)

    # print(fid,b)
  save_json(ofile,data)


if __name__=='__main__':
  main()
