import xml.etree.ElementTree as ET

xns = {'dae':'http://www.collada.org/2005/11/COLLADASchema'}

class DaeSource:
    def __init__(self, node):
        self.id = node.attrib['id']
        x_floatarray = node.find('dae:float_array', xns)
        self.floatArray = [float(x) for x in x_floatarray.text.split()]
        x_techcom = node.find('dae:technique_common', xns)
        x_accessor = x_techcom.find('dae:accessor', xns)
        self.stride = int(x_accessor.attrib.get('stride', '1'))

    def getElement(self, x: int):
        return tuple(self.floatArray[x*self.stride:(x+1)*self.stride])

    def getVertex(self, x: int, vsem: str, vset: int):
        return {(vsem,vset):self.getElement(x)}

def daeReadInputs(node, dmesh) -> dict:
    d = {}
    for xi in node.findall('dae:input', xns):
        inpsem = xi.attrib['semantic']
        inpset = int(xi.attrib.get('set', '0'))
        inpsrc = xi.attrib['source'].split('#')[1]
        inpoff = int(xi.attrib.get('offset', '0'))
        srcref = dmesh.vertices[inpsrc] if inpsem == 'VERTEX' else dmesh.sources[inpsrc]
        d[(inpsem,inpset)] = (srcref,inpoff)
    return d

def daeGetInputStride(inpdic: dict) -> int:
    return max(v[1] for v in inpdic.values()) + 1

class DaeVertices:
    def __init__(self, node, dmesh):
        self.id = node.attrib['id']
        self.inputs = daeReadInputs(node, dmesh)

    def getVertex(self, x: int, vsem: str, vset: int):
        d = {}
        for k,v in self.inputs.items():
            d[k] = v[0].getElement(x)
        return d

class DaePrimitives:
    def __init__(self, node, dmesh):
        self.material = node.attrib.get('material', None)
        self.count = int(node.attrib['count'])
        self.inputs = daeReadInputs(node, dmesh)
        self.stride = daeGetInputStride(self.inputs)

        self.pdata = [int(i) for i in node.find('dae:p', xns).text.split()]

class DaeTriangles(DaePrimitives):
    def __init__(self, node, dmesh):
        super().__init__(node, dmesh)
        self.vcount = [3 for i in range(self.count)]

class DaePolylist(DaePrimitives):
    def __init__(self, node, dmesh):
        super().__init__(node, dmesh)
        self.vcount = [int(i) for i in node.find('dae:vcount', xns).text.split()]

class DaeMesh:
    def __init__(self, node):
        self.sources =  {d.id:d for d in (DaeSource(x) for x in node.findall('dae:source', xns))}
        self.vertices = {d.id:d for d in (DaeVertices(x, self) for x in node.findall('dae:vertices', xns))}
        self.triangles = [DaeTriangles(x, self) for x in node.findall('dae:triangles', xns)]
        self.polylists = [DaePolylist(x, self) for x in node.findall('dae:polylist', xns)]

class DaeNode:
    def __init__(self, node):
        self.id = node.attrib['id']
        self.matrix = (1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1)
        x_matrix = node.find('dae:matrix', xns)
        if x_matrix != None:
            self.matrix = tuple(float(f) for f in x_matrix.text.split())
        self.geo = None
        x_instgeo = node.find('dae:instance_geometry', xns)
        if x_instgeo != None:
            self.geo = x_instgeo.attrib['url'].split('#')[1]

class DaeVisualScene:
    def __init__(self, node):
        self.id = node.attrib['id']
        self.nodes = {d.id:d for d in (DaeNode(x) for x in node.findall('dae:node', xns))}

class DaeGeometry:
    def __init__(self, node):
        self.id = node.attrib['id']
        self.mesh = DaeMesh(node.find('dae:mesh', xns))

class DaeDocument:
    def __init__(self, dae):
        x_asset = dae.find('dae:asset', xns)
        x_libimg = dae.find('dae:library_images', xns)
        x_libmat = dae.find('dae:library_materials', xns)
        x_libfx = dae.find('dae:library_effects', xns)
        x_libgeo = dae.find('dae:library_geometries', xns)
        x_libvs = dae.find('dae:library_visual_scenes', xns)

        self.images = {x.attrib['id']:x.find('dae:init_from',xns).text for x in x_libimg.findall('dae:image', xns)}
        self.effects = {} #{x.attrib['id']:x.find('.//dae:surface',xns).find('dae:init_from',xns).text for x in x_libfx.findall('dae:effect', xns)}
        for x in x_libfx.findall('dae:effect', xns):
            try:
                img = self.images[x.find('.//dae:surface',xns).find('dae:init_from',xns).text]
            except:
                img = None
            self.effects[x.attrib['id']] = img
        self.materials = {x.attrib['id']:self.effects[x.find('dae:instance_effect',xns).attrib['url'].split('#')[1]] for x in x_libmat.findall('dae:material', xns)}
        self.geometries = {d.id:d for d in (DaeGeometry(x) for x in x_libgeo.findall('dae:geometry', xns))}
        self.visualscenes = {d.id:d for d in (DaeVisualScene(x) for x in x_libvs.findall('dae:visual_scene', xns))}
