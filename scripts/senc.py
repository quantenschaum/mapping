'''
SENC/S57 binary file interface

The SENC format use by o-charts is a derivative of the S57 format invented for OpenCPN. SENC has a few additional record types and uses an edge table stride of 4 instead of 3. The fourth entry (0 or 1) indicates that the edge needs to be flipped. This allows edges to be stored once and used in both directions, which saves some space.

Thus, these formats are effectively incompatible, but otherwise almost identical.

The SENC library by o-charts can read both formats, S57 is indicated by file version 200, SENC by 201, whereas OpenCPN is only able to read S57 files.

https://github.com/OpenCPN/OpenCPN/blob/master/gui/include/gui/Osenc.h
https://github.com/bdbcat/o-charts_pi/blob/master/src/Osenc.h
'''

import struct
from math import radians, log, tan, pi, atan, degrees, exp
from os.path import join, dirname

HEADER_SENC_VERSION = 1
HEADER_CELL_NAME = 2
HEADER_CELL_PUBLISHDATE = 3
HEADER_CELL_EDITION = 4
HEADER_CELL_UPDATEDATE = 5
HEADER_CELL_UPDATE = 6
HEADER_CELL_NATIVESCALE = 7
HEADER_CELL_SENCCREATEDATE = 8
FEATURE_ID_RECORD = 64
FEATURE_ATTRIBUTE_RECORD = 65
FEATURE_GEOMETRY_RECORD_POINT = 80
FEATURE_GEOMETRY_RECORD_LINE = 81
FEATURE_GEOMETRY_RECORD_AREA = 82
FEATURE_GEOMETRY_RECORD_MULTIPOINT = 83
VECTOR_EDGE_NODE_TABLE_RECORD = 96
VECTOR_CONNECTED_NODE_TABLE_RECORD = 97
CELL_COVR_RECORD = 98
CELL_NOCOVR_RECORD = 99
CELL_EXTENT_RECORD = 100

HEADER_CELL_SOUNDINGDATUM = 9
CELL_TXTDSC_INFO_FILE_RECORD = 101
SERVER_STATUS_RECORD = 200
FEATURE_GEOMETRY_RECORD_AREA_EXT = 84
VECTOR_EDGE_NODE_TABLE_EXT_RECORD = 85
VECTOR_CONNECTED_NODE_TABLE_EXT_RECORD = 86

S57_RECORD_TYPES=1,2,3,4,5,6,7,8,64,65,80,81,82,83,96,97,98,99,100

R = 6378137.0

def ll2grid(lon, lat):
    easting = radians(lon) * R
    northing = log(tan(pi / 4 + radians(lat) / 2)) * R
    return easting, northing


def grid2ll(easting, northing):
    lat = degrees(2 * atan(exp(northing / R)) - pi / 2.0)
    lon = degrees(easting / R)
    return lon, lat


def multipoint(data, unpack=None, pack=None):
    if unpack:
      data["points"] = [unpack("fff") for i in range(data["count"])]

    if pack:
      points=data['points']
      assert len(points)==data['count']
      for p in points: pack('fff',*p)


def line(data, unpack=None, pack=None):
    stride=data['stride']
    fmt = 'I'*stride

    if unpack:
      pad = (0,)*(4-stride)
      data["edges"] = [unpack(fmt)+pad for i in range(data["count"])]

    if pack:
      edges=data['edges']
      assert len(edges)==data['count']
      for e in edges: pack(fmt,*e[:stride])


def area(data, unpack=None, pack=None):
    if unpack:
        contours, tris = [data[k] for k in ("contours", "trias")]
        pointcount = unpack(f"{contours}I")
        data["pointcount"] = pointcount
        triangles = data["triangles"] = []
        for t in range(tris):
            ttype, nvert = unpack("BI")
            bbox = unpack("dddd")
            vertices = [unpack("ff") for i in range(nvert)]
            triangles.append({"ttype": ttype, "bbox": bbox, "vertices": vertices})

    if pack:
        c=data['contours']
        p=data['pointcount']
        assert len(p)==c
        pack(f'{c}I',*p)
        triangles=data['triangles']
        assert len(triangles)==data['trias']
        for t in triangles:
          tt,bb,vs=t['ttype'],t['bbox'],t['vertices'] # bbox=WESN
          pack('BIdddd',tt,len(vs),*bb)
          for v in vs: pack('ff',*v)

    line(data,unpack,pack)


def edge_table(data, unpack=None, pack=None):
    if unpack:
      edges = {}
      for i in range(data["count"]):
          index, points = unpack("II")
          assert index
          edges[index] = [unpack("ff") for j in range(points)]
      data["edges"] = edges

    if pack:
      edges=data['edges']
      assert len(edges)==data['count']
      for i,vs in edges.items():
        pack('II',i,len(vs))
        for v in vs: pack('ff',*v)


def node_table(data, unpack=None, pack=None):
    if unpack:
      nodes = {}
      for i in range(data["count"]):
          index = unpack("I")[0]
          assert index
          nodes[index] = unpack("ff")
      data["nodes"] = nodes

    if pack:
      nodes=data['nodes']
      assert len(nodes)==data['count']
      for i,n in nodes.items():
        pack('Iff',i,*n)


RECORDS = {
    HEADER_SENC_VERSION: ['cell_version',"version:H"],
    HEADER_CELL_NAME: ['cell_name',"cellname:z"],
    HEADER_CELL_PUBLISHDATE: ['cell_publish_date',"published:z"],
    HEADER_CELL_EDITION: ['cell_edition',"edition:H"],
    HEADER_CELL_UPDATEDATE: ['cell_update_date',"updated:z"],
    HEADER_CELL_UPDATE: ['cell_update',"update:H"],
    HEADER_CELL_NATIVESCALE: ['cell_native_scale',"scale:I"],
    HEADER_CELL_SENCCREATEDATE: ['cell_creation_date',"created:z"],
    HEADER_CELL_SOUNDINGDATUM: ['cell_sounding_datum',"datum:z"],
    CELL_EXTENT_RECORD: ['cell_extent','sw:dd','nw:dd','ne:dd','se:dd'],
    CELL_COVR_RECORD: ['cell_coverage',"count:I", "array:{2*d['count']}f"],
    CELL_NOCOVR_RECORD: ['cell_no_coverage',"count:I", "array:{2*d['count']}f"],
    FEATURE_ID_RECORD: ['feature',"ftype:H", "id:H", "primitive:B"],
    FEATURE_ATTRIBUTE_RECORD: [
        'attribute',
        "atype:H",
        "vtype:B",
        "value:{'z' if d['vtype']==4 else 'd' if d['vtype']==2 else 'I'}",
    ],
    FEATURE_GEOMETRY_RECORD_POINT: ['point',"lat:d", "lon:d"],
    FEATURE_GEOMETRY_RECORD_MULTIPOINT: [
        'multipoint',
        'bbox:dddd', # SNWE
        "count:I",
        multipoint,
    ],
    FEATURE_GEOMETRY_RECORD_LINE: [
        'line',
        'bbox:dddd', # SNWE
        "count:I",
        line,
    ],
    FEATURE_GEOMETRY_RECORD_AREA: [
        'area',
        'bbox:dddd', # SNWE
        "contours:I",
        "trias:I",
        "count:I",
        area,
    ],
    FEATURE_GEOMETRY_RECORD_AREA_EXT: [
        'area',
        'bbox:dddd', # SNWE
        "contours:I",
        "trias:I",
        "count:I",
        "scale:d",
        area,
    ],
    VECTOR_EDGE_NODE_TABLE_RECORD: ['edge_table',"count:I", edge_table],
    VECTOR_EDGE_NODE_TABLE_EXT_RECORD: ['edge_table',"count:I", "scale:d", edge_table],
    VECTOR_CONNECTED_NODE_TABLE_RECORD: ['node_table',"count:I", node_table],
    VECTOR_CONNECTED_NODE_TABLE_EXT_RECORD: ['node_table,'"count:I", "scale:d", node_table],
    CELL_TXTDSC_INFO_FILE_RECORD: ['text',"flength:I","clength:I","file:z","text:z"],
    SERVER_STATUS_RECORD: [
        'server_status',
        "server:H",
        "decrypt:H",
        "expire:H",
        "expire_days_remaining:H",
        "grace_days_allowed:H",
        "grace_days_remaining:H",
    ],
}


class SENC():
  'reads/writes an SENC/S57 file to/from dicts'
  def __init__(self,filename,mode='r'):
    self.filename=filename
    self._writeable='w' in mode
    self._BO='<'
    self._stride=4 if filename.endswith('.senc') else 3
    self._fid=0

  def __enter__(self):
    assert not hasattr(self,'_fd')
    self._fd=open(self.filename,'wb' if self._writeable else 'rb')
    self._limit=None
    if self._writeable:
      ver=201 if self._stride==4 else 200
      self.add_record(type=HEADER_SENC_VERSION, version=ver)
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self._fd.close()
    del self._fd

  def __iter__(self): return self

  def __next__(self):
    r=self.get_record()
    if r is None: raise StopIteration
    return r

  def records(self):
    'read all records from the file and close it'
    with self as s: return list(s)

  def limit(self,n=None):
    'set/get read limit relative to current position'
    if n is not None:
      self._limit=None if n<0 else n
    return self._limit

  def read(self, n, exactly=False):
    'read (exactly) n bytes, enforce limit'
    if self._limit is not None:
      assert self._limit-n>=0,f'limit exceeded: {self._limit}'
      self._limit-=n
    data=self._fd.read(n)
    assert not exactly or len(data)==n, f'not exactly: {len(data)}<{n}'
    return data

  def unpack(self,fmt):
    'read data from file'
    if fmt=='z': # zero terminated string
      s=b''
      while True:
        c=self.unpack('s')[0]
        if c!=b'\0': s+=c
        else: break
      # print('<z',s.decode())
      return s.decode()
    n=struct.calcsize(self._BO+fmt)
    b=self.read(n)
    if len(b)!=n: return
    return struct.unpack(self._BO+fmt,b)

  def pack(self,fmt,*vals):
    'write data to file'
    if fmt=='z':
      # print('>z',vals[0])
      self._fd.write(vals[0].encode()+b'\0')
    else:
      self._fd.write(struct.pack(self._BO+fmt,*vals))

  def get_type(self):
    'return next record type, set limit'
    l=self.limit()
    if l: self._fd.seek(l) # skip to next record
    self.limit(-1)
    h=self.unpack('HI')
    if h:
      self.limit(h[1]-6)
      return h[0]


  def start_record(self,rtype):
    assert not hasattr(self,'_pos')
    assert self._stride==4 or rtype in S57_RECORD_TYPES, f'record type {rtype} {RECORDS[rtype][0]} not allowed in S57'
    self._pos=self._fd.tell()
    self.pack('HI',rtype,0)


  def end_record(self,s=None,revert=False):
    if revert:
      self._fd.seek(self._pos)
      del self._pos
      return
    size=self._fd.tell()-self._pos
    # print('> size',size-6)
    assert s is None or size-6==s, (size-6,s)
    self._fd.seek(self._pos+2,0)
    self.pack('I',size)
    self._fd.seek(0,2)
    del self._pos


  def get_record(self):
    t=self.get_type()
    if not t: return
    fields=RECORDS[t]
    # print(fields)
    d=data={'type':t, 'size':self.limit(), 'stride':self._stride}
    for f in fields:
      if callable(f):
        f(data,self.unpack)
        continue
      if ':' not in f:
        data['name']=f
        continue
      name, fmt = f.split(":")
      fmt = eval(f'f"{fmt}"')
      # print(name,fmt)
      val=self.unpack(fmt)
      # print(val)
      data[name] = val[0] if len(val) == 1 else val

    assert not self.limit(), f'remaining bytes: {self.limit()}'
    return data


  def add_record(self,**data):
    t=data['type']
    fields=RECORDS[t]
    if 'edges' in data:
      data['stride']=self._stride
      data['count']=len(data['edges'])
    if 'nodes' in data: data['count']=len(data['nodes'])
    if 'points' in data: data['count']=len(data['points'])
    if 'array' in data: data['count']=len(data['array'])//2
    if 'triangles' in data: data['trias']=len(data['triangles'])
    if 'ftype' in data:
      if 'id' in data: self._fid=data['id']
      else:
        self._fid+=1
        data['id']=self._fid
    if 'value' in data:
      v=data['value']
      data['vtype']=4 if isinstance(v,str) else 2 if isinstance(v,float) else 0
    self.start_record(t)
    try:
      # print('>',data)
      d=data
      for f in fields:
        if callable(f):
          # print('>',f)
          f(data,pack=self.pack)
          continue
        if ':' not in f: continue
        name, fmt = f.split(":")
        fmt = eval(f'f"{fmt}"')
        val=data[name]
        # print('>',name,fmt0,fmt,val)
        if len(fmt)==1: val=[val]
        self.pack(fmt, *val)
      self.end_record()
    except Exception as x:
      print('reverted',x,data)
      self.end_record(revert=True)


def write_txt(filename,txt):
  with open(filename,'w') as f:
    f.write(txt)


def senc2s57(fi,fo):
  senc=SENC(fi).records()
  et={}
  for t in list(filter(lambda r:r['name']=='edge_table',senc)):
    assert 'scale' not in t
    for i,v in t['edges'].items():
      assert i not in et,f'duplicate edge id {i}'
      et[i]=v

  eid=max(et.keys())+1 # next edge ID

  with SENC(fo,'w') as s57:
    for r in senc:
      t=r['type']
      if t==CELL_TXTDSC_INFO_FILE_RECORD: write_txt(join(dirname(fo),r['file']),r['text'])
      if t in S57_RECORD_TYPES and t not in (HEADER_SENC_VERSION,VECTOR_EDGE_NODE_TABLE_RECORD):
        if 'edges' in r: # lines and areas
          edges=[]
          for e in r['edges']:
            if e[1] and e[3]: # edge with reverse flag
              et[eid]=list(reversed(et[e[1]])) # added flipped add to edge table
              e=(e[0],eid,e[2]) # update indices
              eid+=1
            else: e=e[:3] # drop 4th int
            edges.append(e) # set new indices
          r['edges']=edges
        s57.add_record(**r)
      else:
        assert t not in (VECTOR_EDGE_NODE_TABLE_EXT_RECORD,VECTOR_CONNECTED_NODE_TABLE_EXT_RECORD,FEATURE_GEOMETRY_RECORD_AREA_EXT),t # stop on EXT record (not implemented)
    s57.add_record(type=VECTOR_EDGE_NODE_TABLE_RECORD,edges=et) # write modified edge table


