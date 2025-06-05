from qgis.core import QgsProject
import processing
from os.path import dirname

project=QgsProject.instance()
pdir=dirname(project.fileName())
datadir=pdir+'/../data/'

def layer(name):
     layers=project.mapLayersByName(name)
     if layers: return layers[0]

def fixed(name):
    name_fixed=name+'_fixed'
    l=layer(name_fixed)
    if l: return l
    print(f'fixing {name}...',end='')
    result = processing.run("native:fixgeometries", {
        'INPUT': layer(name),
        'OUTPUT': 'memory:'
    })
    print('done')

    l=result['OUTPUT']
    l.setName(name_fixed)
    project.addMapLayer(l)
    return l
    
def save(layer, name, filename, mode=0):
    r=processing.run("native:savefeatures", {
        'INPUT': layer,
        'OUTPUT': f"{filename}",
        'LAYER_NAME': name,
        'ACTION_ON_EXISTING_FILE': mode,
    })
    print(r)
    
def process(cmd, l1, l2, name):
    l=layer(name)
    if l: return l
    print(f'{cmd} {l1.name()} {l2.name()}')
    r=processing.run(f'native:{cmd}', {
        'INPUT': l1,
        'OVERLAY': l2,
        'OUTPUT': 'memory:',
    })
    print(r)
    l=r['OUTPUT']
    l.setName(name)
    project.addMapLayer(l)
    return l
    
def difference(l1, l2 ,name):
    return process('difference', l1, l2, name)
    
def intersect(l1, l2 ,name):
    return process('intersection', l1, l2, name)
    
def merge(l1, l2 ,name):
    l=layer(name)
    if l: return l
    print(f'merge {l1.name()} {l2.name() if l2 else None}')
    r=processing.run('native:mergevectorlayers', {
        'LAYERS': [l1, l2] if l2 else [l1],
        'OUTPUT': 'memory:',
    })
    print(r)
    l=r['OUTPUT']
    l.setName(name)
    project.addMapLayer(l)
    return l
 
contours=layer('contours')
depthareas=fixed('depthareas')
coverage=layer('coverage')
  
def select_uband(uband):
    contours.setSubsetString(f'VALDCO is not null and uband={uband}')
    depthareas.setSubsetString(f'DRVAL1 is not null and uband={uband}')
    coverage.setSubsetString(f'uband={uband}')

def strip_fields(layer):
    keep='uband contour contourtype depth contourarea areatype'.split()
    fields=layer.fields()
    indices = [fields.indexOf(f.name()) for f in fields if f.name() not in keep]
    layer.dataProvider().deleteAttributes(indices)
    layer.updateFields()
    layer.commitChanges()
        
a=depthareas
c=contours

for u in range(1,7):
    print(f'uband {u}')
    select_uband(u)
    if u>1:
        a1=diff(a,coverage,f'a{u}*')
        c1=diff(c,coverage,f'c{u}*')
        a=merge(a1,depthareas,f'a{u}')
        c=merge(c1,contours,f'c{u}')
    else:
        a=merge(a,None,f'a{u}')
        c=merge(c,None,f'c{u}')
    gpkg=f'{datadir}/depth-de-{u}.gpkg'
    strip_fields(a)
    strip_fields(c)
    save(a,'areas',gpkg)
    save(c,'conts',gpkg, 1)
    