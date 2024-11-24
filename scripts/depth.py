#!/usr/bin/env python3
# coding: utf-8

import os,sys
from pyquery import PyQuery as pq
import pendulum
from functools import partial

def process(fn):
  x=pq(filename=fn)

  attrs={
   # 'date':['Date',pendulum.parse],
   # 'time':['Time',partial(pendulum.parse,exact=True)],
   'gpsalt':['Corrected_Altitude_GPS_Antenna',float],
   'ellalt':['Difference_Ellipsoid_Altitude',float],
   'valid':['Depth_Valid',lambda s:s=='true'],
   'lat':['Corrected_Latitude',float],
   'lon':['Corrected_Longitude',float],
   'north':['Corrected_X_North',float],
   'east':['Corrected_Y_East',float],
   'wlc1':['Water_Level_Corr1',float],
   'wlc2':['Water_Level_Corr2',float],
   'wlc3':['Water_Level_Corr3',float],
   'wlc4':['Water_Level_Corr4',float],
   'f_high':['Backscattering_high_Freq',float],
   'f_low':['Backscattering_low_Freq',float],
   'd_high':['Corrected_Depth_high_Freq_onFootprint',float],
   'd_low':['Corrected_Depth_low_Freq_onFootprint',float],
   'd_acc':['Accuracy_Depth',float],
   'p_acc':['Accuracy_Position',float],
  }

  for d in x('*'):
    if d.tag=="Depth":
      q=pq(d)
      data={k:v[1](q.attr(v[0])) for k,v in attrs.items()}
      if data['valid']:
        # print(data)
        print(' '.join(str(data[k]) for k in fields.split()))

fields='east north d_high d_low wlc1 wlc2'

def main():
  # process('data/Verm_Single_Beam_Nordsee_2024_9342400/9342400_Kontrollprofile/9342400_111_11_9004_21-06-2024_09-53-00.XML')
  print(fields)
  for f in sys.argv:
    process(f)

main()
