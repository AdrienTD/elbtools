import array,io,math,os,struct,time,wx,wx.glcanvas,wx.propgrid
import cProfile
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo
from utils import *
from kfiles import *
from objects import *
#import numpy as np
#import imgui

class GLGeometry:
    def __init__(self, tris, verts, uvs = None, colors = None, usevbo=False):
        self.num_tris = len(tris)
        self.num_verts = len(verts)
        self.indarr = array.array('H')
        for t in tris:
            self.indarr.extend(t)
        self.indbytes = bytes(self.indarr)
        self.verarr = array.array('f')
        for v in verts:
            self.verarr.extend(v)
        self.verbytes = bytes(self.verarr)
        self.uvsarr = self.uvsbytes = None
        if uvs:
            self.uvsarr = array.array('f')
            for u in uvs:
                self.uvsarr.extend(u)
            self.uvsbytes = bytes(self.uvsarr)
        self.colarr = self.colbytes = None
        if colors:
            self.colarr = array.array('B')
            for c in colors:
                self.colarr.extend(c)
            self.colbytes = bytes(self.colarr)
        self.usevbo = usevbo
        self.vbomade = False
    def createvbo(self):
        self.indvbo = vbo.VBO(self.indbytes, usage='GL_STATIC_DRAW', target='GL_ELEMENT_ARRAY_BUFFER')
        vbobytes = self.verbytes
        if self.uvsbytes:
            self.uvsoff = len(vbobytes)
            vbobytes += self.uvsbytes
        if self.colbytes:
            self.coloff = len(vbobytes)
            vbobytes += self.colbytes
        self.vervbo = vbo.VBO(vbobytes, usage='GL_STATIC_DRAW')
        self.vbomade = True
    def draw(self):
        if self.usevbo:
            if not self.vbomade:
                self.createvbo()
            self.indvbo.bind()
            glEnableClientState(GL_VERTEX_ARRAY)
            self.vervbo.bind()
            glVertexPointer(3, GL_FLOAT, 0, self.vervbo)
            if self.uvsbytes:
                glEnableClientState(GL_TEXTURE_COORD_ARRAY)
                glTexCoordPointer(2, GL_FLOAT, 0, self.vervbo + self.uvsoff)
            else:
                glDisableClientState(GL_TEXTURE_COORD_ARRAY)
            if self.colbytes:
                glEnableClientState(GL_COLOR_ARRAY)
                glColorPointer(4, GL_UNSIGNED_BYTE, 0, self.vervbo + self.coloff)
            else:
                glDisableClientState(GL_COLOR_ARRAY)
            glDrawElements(GL_TRIANGLES, 3*self.num_tris, GL_UNSIGNED_SHORT, self.indvbo)
            self.vervbo.unbind()
            self.indvbo.unbind()
        else:
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, self.verbytes)
            if self.uvsbytes:
                glEnableClientState(GL_TEXTURE_COORD_ARRAY)
                glTexCoordPointer(2, GL_FLOAT, 0, self.uvsbytes)
            else:
                glDisableClientState(GL_TEXTURE_COORD_ARRAY)
            if self.colbytes:
                glEnableClientState(GL_COLOR_ARRAY)
                glColorPointer(4, GL_UNSIGNED_BYTE, 0, self.colbytes)
            else:
                glDisableClientState(GL_COLOR_ARRAY)
            glDrawElements(GL_TRIANGLES, 3*self.num_tris, GL_UNSIGNED_SHORT, self.indbytes)


def getChunkFromInt(kflist: list, a: int) -> KChunk:
    cltype,clid,chkid = a & 63, (a >> 6) & 2047, a >> 17
    #print('gcfi:', cltype,clid,chkid)
    for kf in kflist:
        if kf == None: continue
        cti = (cltype, clid)
        if cti not in kf.kclasses: continue
        for chk in kf.kclasses[cti].chunks:
            if chk.cid == chkid:
                #print('Found')
                return chk
    return None

lightdir = Vector3(0,1,0).unit()
tcdict = {0: (1,1,1), 1: (1,0,0), 2: (0,1,0), 4: (1,1,0), 8: (0,0,1), 16: (0,1,1), 128: (1,0,1)}

class Ground:
    def __init__(self, f, ver):
        self.load(f, ver)
    def load(self, bi, ver):
        numa,num_tris,num_verts = readpack(bi, "IHH")
        self.tris = []
        self.verts = []
        self.norms = []
        self.colors = []
        for i in range(num_tris):
            self.tris.append(readpack(bi, "HHH"))
        for i in range(num_verts):
            self.verts.append(readpack(bi, "fff"))
        
        self.aabb = readpack(bi, "6f")
        self.type,self.param = readpack(bi, "HH")
        self.infwalls = []
        self.finwalls = []
        if ver >= 2:
            bb, = readpack(bi, "B")
            if ver >= 4: readobjref(bi) # ?
            readobjref(bi) # Sector
        numinfwall, = readpack(bi, "H")
        for i in range(numinfwall):
            self.infwalls.append(readpack(bi, "HH"))
        numfinwall, = readpack(bi, "H")
        for i in range(numfinwall):
            self.finwalls.append(readpack(bi, "HHff"))

        # Add walls in mesh
        for w in self.finwalls:
            vi = len(self.verts)
            self.verts.append(tuple(Vector3(*self.verts[w[0]]) + Vector3(0,w[2],0)))
            self.verts.append(tuple(Vector3(*self.verts[w[1]]) + Vector3(0,w[3],0)))
            if w[2] >= 0:
                self.tris.append((w[1], w[0], vi+0))
                self.tris.append((w[1], vi+0, vi+1))
            else:
                self.tris.append((w[1], vi+0, w[0]))
                self.tris.append((w[1], vi+1, vi+0))

        #tc = Vector3(1,1,1) - Vector3((self.type>>1)&1, (self.type>>3)&1, (self.type>>4)&1)
        tc = Vector3(*tcdict.get(self.type, (0,0,0)))

        for t in self.tris:
            v1 = Vector3(*self.verts[t[1]]) - Vector3(*self.verts[t[0]])
            v2 = Vector3(*self.verts[t[2]]) - Vector3(*self.verts[t[0]])
            self.norms.append(v1.cross(v2).unit())

        self.vtxnorms =  [Vector3(0,0,0) for i in range(len(self.verts))]
        self.vtxnumnorms = len(self.verts) * [0]
        for t in range(len(self.tris)):
            for p in self.tris[t]:
                self.vtxnorms[p] += self.norms[t]
                self.vtxnumnorms[p] += 1
        for i in range(len(self.vtxnorms)):
            if self.vtxnumnorms[i]:
                self.vtxnorms[i] *= 1/self.vtxnumnorms[i]
        for n in self.vtxnorms:
            d = max(0, min(255, int(n.dot(lightdir)*255)))
            self.colors.append((d*tc.x,d*tc.y,d*tc.z,255))
        self.glgeo = GLGeometry(self.tris, self.verts, None, self.colors)

class Node:
    def __init__(self):
        pass
    def __init__(self, chk, kflist):
        self.load(chk, kflist)
    def load(self, chk, kflist):
        f = io.BytesIO(chk.data)
        self.chunk = chk
        self.clid = chk.kcl.clid
        self.id = chk.cid
        self.children = []
        self.matrix = list(readpack(f, "16f"))
        self.matrix[3] = self.matrix[7] = self.matrix[11] = 0
        self.matrix[15] = 1
        self.parentchk = getChunkFromInt(kflist, *readpack(f,"I"))
        if self.parentchk != None:
            assert self.parentchk.kcl.cltype == 11
        self.unk1 = readpack(f, 'I' if chk.ver >= 2 else 'H')
        self.unk2 = readpack(f, 'B')
        self.nextobjchk = getChunkFromInt(kflist, *readpack(f,"I"))
        try:
            self.subobjchk = getChunkFromInt(kflist, *readpack(f,"I"))
        except:
            print('no children for node 11,%i,%i!' % (chk.kcl.clid,chk.cid))
        try:
            self.geochk = getChunkFromInt(kflist, *readpack(f,"I"))
        except:
            print('geochk read failed in node 11,%i,%i!' % (chk.kcl.clid,chk.cid))
            self.geochk = None

class ScenePanel(wx.Panel):
    def __init__(self, kfiles, *args, **kw):
        super().__init__(*args,**kw)

        self.nodes = {}
        #ntl = [(11,3),(11,21),(11,12),(11,22)]
        for kk in kfiles:
            print(kk)
            if kk == None: continue
            ntl = [x for x in kk.kclasses if x[0] == 11]
            for cl in ntl:
                if not (cl in kk.kclasses): continue
                for chk in kk.kclasses[cl].chunks:
                    self.nodes[chk] = Node(chk,kfiles)

        for node in self.nodes.values():
            if node.parentchk:
                node.parent = self.nodes[node.parentchk]
                node.parent.children.append(node)
            else:
                node.parent = None

        self.secroots = []

        self.spl = wx.SplitterWindow(self)
        self.spl2 = wx.SplitterWindow(self.spl)
        self.nodetree = wx.TreeCtrl(self.spl2)
        self.propgrid = wx.propgrid.PropertyGrid(self.spl2)
        self.viewer = SceneViewer(kfiles, self, self.spl)
        self.spl.SetMinimumPaneSize(16)
        self.spl2.SetMinimumPaneSize(16)
        self.spl2.SplitHorizontally(self.nodetree, self.propgrid, -150)
        self.spl.SplitVertically(self.spl2, self.viewer, 150)
        self.spl2.SetSashGravity(1)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.nodetree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnTree)
        self.nodetree.Bind(wx.EVT_TREE_ITEM_MENU, self.OnTreeMenu)
        self.Bind(wx.EVT_MENU, self.OnExportDFF, id=1001)

        def insertnode(node, parent_tree_item):
            if kfiles[0] and kfiles[0].namedicts:
                txt = kfiles[0].namedicts[node.chunk.kcl.kfile.strnum][(11,node.clid,node.id)]
            else:
                txt = '%s %i' % (getclname(11,node.clid),node.id)
            if not parent_tree_item:
                ti = self.nodetree.AddRoot(txt, data=node)
            else:
                ti = self.nodetree.AppendItem(parent_tree_item, txt, data=node)
            for c in node.children:
                insertnode(c, ti)
        try:
            rootnode = self.nodes[kfiles[0].kclasses[(11,1)].chunks[0]]
        except:
            rootnode = None
        treeroot = self.nodetree.AddRoot("Root", data=rootnode)
        for kk in kfiles:
            if kk != None:
                secrootnode = self.nodes[kk.kclasses[(11,2)].chunks[0]]
                self.secroots.append(secrootnode)
                insertnode(secrootnode, treeroot)

        self.p_type = self.propgrid.Append(wx.propgrid.StringProperty('Type'))
        self.p_id   = self.propgrid.Append(wx.propgrid.IntProperty('ID'))
        self.p_posx = self.propgrid.Append(wx.propgrid.FloatProperty('Pos X'))
        self.p_posy = self.propgrid.Append(wx.propgrid.FloatProperty('Pos Y'))
        self.p_posz = self.propgrid.Append(wx.propgrid.FloatProperty('Pos Z'))
        self.propgrid.Bind(wx.propgrid.EVT_PG_CHANGED, self.OnPropChanged)

        for node in self.nodes.values():
            node.binmatrix = bytes(array.array('f', node.matrix))

        self.selected_node = None

        self.kfiles = kfiles

    def OnPropChanged(self, event):
        prop = event.GetProperty()
        if self.selected_node:
            if prop == self.p_posx:
                self.selected_node.matrix[12] = event.GetPropertyValue()
            elif prop == self.p_posy:
                self.selected_node.matrix[13] = event.GetPropertyValue()
            elif prop == self.p_posz:
                self.selected_node.matrix[14] = event.GetPropertyValue()
            if prop in (self.p_posx, self.p_posy, self.p_posz):
                self.UpdateObject(self.selected_node)
                self.viewer.Refresh()

    def UpdateObject(self, node):
        newdata = bytearray(node.chunk.data)
        newdata[0:64] = struct.pack('<16f', *node.matrix)
        node.chunk.data = bytes(newdata)
        node.binmatrix = bytes(array.array('f', node.matrix))
    
    def OnSize(self, event):
        self.spl.SetSize(self.GetClientSize())
        
    def OnTree(self, event):
        node = self.nodetree.GetItemData(event.GetItem())
        self.selected_node = node
        self.viewer.campos = tuple(Vector3(*node.matrix[12:15]) - 5*Vector3(*self.viewer.camdir))
        self.p_type.SetValue(getclname(11, node.clid))
        self.p_id.SetValue(node.id)
        self.p_posx.SetValue(node.matrix[12])
        self.p_posy.SetValue(node.matrix[13])
        self.p_posz.SetValue(node.matrix[14])
        self.viewer.Refresh()

    def OnTreeMenu(self, event):
        m = wx.Menu()
        m.Append(1001, "Export to DFF")
        self.nodetree_menuitem = event.GetItem()
        self.PopupMenu(m)

    def OnExportDFF(self, event):
        print('export :)')
        td = self.nodetree.GetItemData(self.nodetree_menuitem)
        print(td)
        print(td.geochk)

        geochk = td.geochk
        #gl = GeometryList(io.BytesIO(geochk.data), geochk.ver, self.kfiles)
        nextgeo,geoflags = struct.unpack('<II', geochk.data[0:8])
        if geoflags & 0x2000:
            num_geos, = struct.unpack('<I', geochk.data[8:0xC])
            cht,chs,chv = struct.unpack('<III', geochk.data[0xC:0x18])
            geooff = 0x18 + chs + 0x28
        else:
            geooff = 0x30
        rwgeotype,rwgeosize,rwver = struct.unpack('<III', geochk.data[geooff:geooff+12])
        assert rwgeotype == 0xF
        #rwver = 0x1803FFFF

        # Get bones
        ha = io.BytesIO(td.chunk.data[0xBF:])
        hat,has,hav = readpack(ha, 'III')
        assert hat == 0x11E
        ha_ver,ha_nodeId,ha_numNodes,ha_flags,ha_kfs = readpack(ha, 'IIIII')
        parbonestack = [0]
        parbone = 0
        bones = []

        for i in range(ha_numNodes):
            uid,nindex,flags = readpack(ha, 'III')
            assert nindex == i
            bones.append((uid,parbone))
            if flags & 2: # Push
                parbonestack.append(parbone)
            parbone = i
            if flags & 1: # Pop
                parbone = parbonestack.pop()

        print('bones:')
        for i in bones:
            print(i)
        print('stack', parbonestack)

        with open('node.dff', 'wb') as dff:
            headstack = []
            def pushhs():
                headstack.append(dff.tell())
            def pophs():
                p = headstack.pop()
                o = dff.tell()
                dff.seek(p-8, os.SEEK_SET)
                writepack(dff, "I", o-p)
                dff.seek(o, os.SEEK_SET)

            writepack(dff, 'III', 0x10, 0, rwver)
            pushhs()

            writepack(dff, 'III', 1, 12, rwver)
            writepack(dff, 'III', 1, 0, 0)

            #dff.write(td.chunk.data[0x5F:])

            # Frame list
            writepack(dff, 'III', 0xE, 0, rwver)
            pushhs()
            writepack(dff, 'III', 1, 0, rwver)
            pushhs()
            writepack(dff, 'I', 1 + len(bones)) # Number of frames
            # Root frame
            writepack(dff, '12fiI', 1,0,0, 0,1,0, 0,0,1, 0,0,0, -1, 0x00020003)
            # First root bone
            dff.write(td.chunk.data[0x7B:0x7B+0x30])
            writepack(dff, 'iI', 0, 3)
            # Bones
            for b in bones[1:]:
                writepack(dff, '12fiI', 1,0,0, 0,1,0, 0,0,1, 0,0,0, b[1]+1, 3)
            pophs() # End frame list struct

            writepack(dff, 'III', 3, 12 + 9, rwver) # Extension chunk for first root frame
            writepack(dff, 'III', 0x253F2FE, 9, rwver)
            dff.write(b"ClumpRoot")
            hanimext = bytearray(td.chunk.data[0xB3:])
            hanimext[0x1C:0x20] = struct.pack('I', 0)
            dff.write(hanimext) # Extension for second frame / first bone

            # Extensions for bones
            for b in bones[1:]:
                writepack(dff, 'III', 3, (12 + 8) + (12 + 12), rwver)
                writepack(dff, 'III', 0x253F2FE, 8, rwver)
                dff.write(b'Bone%04i' % b[0])
                writepack(dff, 'III', 0x11E, 12, rwver)
                writepack(dff, 'III', 0x100, b[0], 0)

            pophs() # End frame list

            # Geometry list
            writepack(dff, 'III', 0x1A, 0, rwver)
            pushhs()
            writepack(dff, 'III', 1, 4, rwver)
            writepack(dff, 'I', 1)

            #gl.geos[0].save(dff, saveAtomic=False)
            dff.write(geochk.data[geooff:geooff+12+rwgeosize])

            pophs() # End geometry list

            # Atomic
            writepack(dff, 'III', 0x14, 0, rwver)
            pushhs()
            writepack(dff, 'III', 1, 0x10, rwver)
            writepack(dff, 'IIII', 0, 0, 4, 0)
            writepack(dff, 'III', 3, 20, rwver)
            writepack(dff, 'III', 0x1F, 8, rwver) # Right to render
            writepack(dff, 'II', 0x116, 1)
            pophs() # End atomic

            writepack(dff, 'III', 3, 0, rwver) # Clump extensions
            pophs() # End clump

class SceneViewer(wx.glcanvas.GLCanvas):
    def __init__(self, kfiles, panel, *args, **kw):
        super().__init__(*args,**kw, style=wx.WANTS_CHARS)
        self.context = wx.glcanvas.GLContext(self)
        self.glinitialized = False
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMotion)
        self.Bind(wx.EVT_LEFT_UP, self.OnMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
        self.Bind(wx.EVT_KEY_DOWN, self.OnChar)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_MENU, self.OnInsertColInScene, id=9001)

        keymap = {1001:'L',1002:'N',1003:'G'}
        for i in keymap:
            self.Bind(wx.EVT_MENU, self.CmdChangeView, id=i)
        accent = [wx.AcceleratorEntry(0, ord(keymap[i]), i) for i in keymap]
        acctab = wx.AcceleratorTable(accent)
        self.SetAcceleratorTable(acctab)

        self.campos = (0,0,0)
        self.camdir = (0,0,-1)
        self.camstr = (1,0,0)
        self.camori_y = math.pi
        self.camori_x = 0
        self.dragstart_m = None
        self.dragstart_o = None
        self.wireframe = False
        self.lightdir = (1,1,1)
        self.shownodes = True
        self.showgrounds = True

        self.grounds = []
        for kk in kfiles:
            if kk == None: continue
            if not ((12,18) in kk.kclasses): continue
            for chk in kk.kclasses[(12,18)].chunks:
                self.grounds.append(Ground(io.BytesIO(chk.data), ver=chk.ver))

        self.nodes = panel.nodes
        self.secroots = panel.secroots

        self.igcontext = None

        self.geos = {}
        for kk in kfiles:
            if kk == None: continue
            for r in (1,2,3):
                if not ((10,r) in kk.kclasses): continue
                for chk in kk.kclasses[(10,r)].chunks:
                    try:
                        geolist = GeometryList(io.BytesIO(chk.data), chk.ver, kfiles)
                        geo = geolist.geos[0]
                        glgeo = GLGeometry([t[0:3] for t in geo.tris], geo.verts, geo.texcrd, geo.colors)
                        #print('nummat', len(geo.materials))
                        #assert len(geo.materials) <= 1
                        tex = ''
                        if geo.materials:
                            tex = geo.materials[0].name
                        self.geos[chk] = (glgeo, geolist.nextgeo, tex)
                        #print('Managed to load geometry 10,%i,%i' % (r,chk.cid))
                    except Exception as e:
                        print('Could not load geometry 10,%i,%i: %s %s' % (r,chk.cid,type(e),e))
                        # import traceback
                        # traceback.print_tb(e.__traceback__)
##        for g in self.geos.values():
##            print(g[0], g[1])
        
        self.listofgeo = list(self.geos.values())
        self.geoprev = 0

        self.texdicts = []
        for kk in kfiles:
            if kk == None: continue
            if not ((9,2) in kk.kclasses): continue
            try:
                tc = kk.kclasses[(9,2)].chunks[0]
                tdt = TextureDictionary(io.BytesIO(tc.data), tc.ver)
                self.texdicts.append(tdt.textures)
            except Exception as e:
                print('Failed to load texture dictionary:', e)

        self.profiling = False

        self.strfile = None
        for kk in kfiles:
            if type(kk) == SectorFile:
                self.strfile = kk

    def OnEraseBackground(self, event):
        pass
    def OnSize(self, event):
        self.Refresh()
    def OnMotion(self, event):
        if event.LeftDown():
            self.dragstart_m = event.GetPosition()
            self.dragstart_y = self.camori_y
            self.dragstart_x = self.camori_x
            #print(self.dragstart_m)
        elif event.LeftUp():
            self.dragstart_m = None
            self.dragstart_y = self.dragstart_x = None
        elif event.Dragging():
            if self.dragstart_m == None: return
            rel = event.GetPosition() - self.dragstart_m
            self.camori_y = self.dragstart_y - rel.x * math.pi / 200
            self.camori_x = self.dragstart_x - rel.y * math.pi / 200
            self.camdir = (math.sin(self.camori_y)*math.cos(self.camori_x), math.sin(self.camori_x), math.cos(self.camori_y)*math.cos(self.camori_x))
            self.camstr = (math.cos(self.camori_y), 0, -math.sin(self.camori_y))
            self.Refresh()
    def OnWheel(self, event):
        w = event.GetWheelRotation()
        a = event.GetWheelAxis()
        if a == wx.MOUSE_WHEEL_VERTICAL:
            self.campos = tuple(self.campos[x] - self.camdir[x]*w*0.1 for x in range(3))
        elif a == wx.MOUSE_WHEEL_HORIZONTAL:
            self.campos = tuple(self.campos[x] + self.camstr[x]*w*0.1 for x in range(3))
        self.Refresh()
    def OnChar(self, event):
        keycode = event.GetKeyCode()
        keychar = chr(keycode).upper()
        if keycode == wx.WXK_UP or keychar == 'Z' or keychar == 'W':
            self.campos = tuple(self.campos[x] + self.camdir[x] for x in range(3))
        if keycode == wx.WXK_DOWN or keychar == 'S':
            self.campos = tuple(self.campos[x] - self.camdir[x] for x in range(3))
        if keycode == wx.WXK_LEFT or keychar == 'Q' or keychar == 'A':
            self.campos = tuple(self.campos[x] + self.camstr[x] for x in range(3))
        if keycode == wx.WXK_RIGHT or keychar == 'D':
            self.campos = tuple(self.campos[x] - self.camstr[x] for x in range(3))
        if keycode == wx.WXK_TAB:
            self.Navigate()
        if keychar == 'P':
            self.profiling = True
        self.Refresh()

    def CmdChangeView(self, event):
        cmd = event.GetId()
        if cmd == 1001:
            self.wireframe = not self.wireframe
        elif cmd == 1002:
            self.shownodes = not self.shownodes
        elif cmd == 1003:
            self.showgrounds = not self.showgrounds
        self.Refresh()

    def InitGL(self):
        self.glinitialized = True
        cubecolors = [(1,0,1),(0,1,0),(0,0,1),(1,1,1)]
        s = 0.5
        cubeverts = [(-s,s,-s),(-s,-s,-s),(s,s,-s),(s,-s,-s),(-s,s,s),(-s,-s,s),(s,s,s),(s,-s,s)]
        cubecols = [(255,0,255,255),(255,0,255,255),(0,255,0,255),(0,255,0,255),(0,0,255,255),(0,0,255,255),(255,255,255,255),(255,255,255,255)]
        cubeinds = [(0,1,2),(1,3,2),(2,3,6),(3,7,6),(6,7,4),(7,5,4),(4,5,0),(5,1,0)]
        self.cube = GLGeometry(cubeinds, cubeverts, None, cubecols)

        self.gltex = {}
        for texdic in self.texdicts:
            for t in texdic:
                glt = glGenTextures(1)
                if t.bpp <= 8:
                    td = bytearray(t.width*t.height*4)
                    for i in range(t.width*t.height):
                        td[4*i:4*i+4] = t.pal[t.dat[i]]
                elif t.bpp == 32:
                    td = t.dat
                else:
                    assert False
                glBindTexture(GL_TEXTURE_2D, glt)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, t.width, t.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, bytes(td))
                self.gltex[t.name] = glt
        #print(self.gltex)

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GEQUAL, 0.8)
        glEnable(GL_CULL_FACE)
        
    def OnPaint(self, event):
        prof = None
        if self.profiling:
            self.profiling = False
            prof = cProfile.Profile()
            prof.enable()
        c = wx.PaintDC(self)
        if self.IsShown():
            self.SetCurrent(self.context)
            if not self.glinitialized:
                self.InitGL()
            winsize = self.GetClientSize()
            glViewport(0,0,winsize.width,winsize.height)
            glEnable(GL_DEPTH_TEST)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if self.wireframe else GL_FILL)

            glClearColor(0.5,0.5,1,1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(60, winsize.width/winsize.height, 0.1, 1000)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            center = [self.campos[x] + self.camdir[x] for x in range(3)]
            gluLookAt(*self.campos, *center, 0,1,0)

            glCullFace(GL_BACK)
            glBindTexture(GL_TEXTURE_2D, 0)
            glColor3f(1,1,1)
            if self.showgrounds:
                for g in self.grounds:
                    g.glgeo.draw()

            glCullFace(GL_FRONT)

            def drawnode(node):
                glPushMatrix()
                glMultMatrixf(node.binmatrix)
                if node.geochk and (node.geochk in self.geos):
                    c = node.geochk
                    while c and (c in self.geos):
                        g = self.geos[c]
                        glBindTexture(GL_TEXTURE_2D, self.gltex.get(g[2], 0))
                        g[0].draw()
                        c = g[1]
                else:
                    glBindTexture(GL_TEXTURE_2D, 0)
                    self.cube.draw()
                for c in node.children:
                    drawnode(c)
                glPopMatrix()

            if self.shownodes:
                for s in self.secroots:
                    drawnode(s)
            
            glDisableClientState(GL_VERTEX_ARRAY)
            glDisableClientState(GL_TEXTURE_COORD_ARRAY)
            glDisableClientState(GL_COLOR_ARRAY)

            self.SwapBuffers()
        if prof:
            prof.disable()
            prof.print_stats()
            prof.dump_stats('last_drawing_profile.bin')

    def OnLeftDown(self, event):
        self.SetFocus()
        event.Skip()

    def OnContextMenu(self, evt):
        m = wx.Menu()
        m.AppendCheckItem(1001, "Wireframe\tL")
        m.AppendCheckItem(1002, "Show nodes\tN")
        m.AppendCheckItem(1003, "Show grounds (collision)\tG")
        m.Check(1001, self.wireframe)
        m.Check(1002, self.shownodes)
        m.Check(1003, self.showgrounds)
        m.Append(9001, "Insert collision model in scene")
        self.PopupMenu(m)

    def OnInsertColInScene(self, evt):
        geo = Geometry()

        geo.tris = []
        geo.verts = []
        geo.colors = []
        for gr in self.grounds:
            base = len(geo.verts)
            geo.tris.extend(((*(t[c]+base for c in (0,2,1)),0) for t in gr.tris))
            geo.verts.extend(gr.verts)
            geo.colors.extend(gr.colors)
        geo.texcrd = [(0,0) for i in range(len(geo.verts))]

        geo.rwver = 0x1803FFFF
        geo.flags = 0xf
        geo.num_uvmaps = 1
        geo.natflags = 0
        geo.num_tris = len(geo.tris)
        geo.num_verts = len(geo.verts)
        geo.sphere = (0,0,0,1000000)
        geo.haspos = 1
        geo.hasnorms = 0

        m = Geometry.Material()
        m.u1 = 0
        m.color = 0xFF000000
        m.u2 = 4
        m.textured = 1
        m.ambient = 1.0
        m.specular = 0.0
        m.diffuse = 1.0
        m.filter = 6
        m.uaddress = 1
        m.vaddress = 1
        m.flags = 1
        m.name = b"notexisting"
        m.maskname = b""

        geo.materials = [m]

        gli = GeometryList()
        gli.u1 = 0xFFFFFFFF
        gli.flags = 1
        gli.geos = [geo]

        kcl = self.strfile.kclasses[(10,2)]
        chk = KChunk(kcl, kcl.chunks[-1].cid+1, b'', 1)

        #with open('rwcol.dff', 'wb') as f:
        f = io.BytesIO()
        gli.save(f, ver=1)
        writepack(f, "II", chk.getRefInt(), 0)
        f.seek(0, os.SEEK_SET)
        chk.data = f.read()

        kcl.chunks.append(chk)

        strroot = self.strfile.kclasses[(11,2)].chunks[0]
        sra = bytearray(strroot.data)
        sra[0x4f:0x53] = struct.pack("I", chk.getRefInt())
        strroot.data = bytes(sra)

