#!/usr/bin/env python3
# coding: utf-8

import os.path
from pyquery import PyQuery as pq

from filter import save_json

def main():
  xml=pq(filename=os.path.dirname(__file__)+'/../data/bsh/catalog.html')
  # print(xml)
  catalog={}
  for enc in xml('enc_entry'):
    enc=pq(enc)
    # print(enc)
    meta={c.tag:c.text for c in enc('*') if 'gml' not in c.tag and c.text and c.text.strip()}
    print(meta['c_number'])
    catalog[meta['c_number']]=meta

  save_json(os.path.dirname(__file__)+'/../data/bsh/catalog.json',catalog,indent=2)

if __name__=='__main__':
  main()
