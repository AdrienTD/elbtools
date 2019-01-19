import io,math,os,struct,time,wx,wx.glcanvas,wx.dataview
from OpenGL.GL import *
from OpenGL.GLU import *
from utils import *

class Texture:
    def __init__(self):
        pass
    def __init__(self, f):
        self.load(f)
    def load(self, f):
        self.name = f.read(32).rstrip(b'\0')
        self.v = readpack(f, "III")
        #print('v:',self.v)
        rtt, rts, rtv = readpack(f, "III")
        assert rtt == 0x18
        self.rwver = rtv
        stt, sts, stv = readpack(f, "III")
        assert stt == 1 and sts == 16
        self.width,self.height,self.bpp,self.pitch = readpack(f, "IIII")
        #print(self.bpp)
        self.dat = f.read(self.pitch * self.height)
        self.pal = []
        if self.bpp <= 8:
            for pe in range(1<<self.bpp):
                self.pal.append(readpack(f,"BBBB"))
    def save(self, f):
        tsiz = self.pitch*self.height + len(self.pal)*4
        f.write(self.name.ljust(32,b'\0'))
        writepack(f, "III", *self.v)
        writepack(f, "III", 0x18, 12+16+tsiz, self.rwver)
        writepack(f, "III", 1, 16, self.rwver)
        writepack(f, "IIII", self.width,self.height,self.bpp,self.pitch)
        f.write(self.dat)
        if self.bpp <= 8:
            for pe in self.pal:
                writepack(f, "BBBB", *pe)
    def convertToWxImage(self):
        d = bytearray(self.width * self.height * 3)
        a = bytearray(self.width * self.height)
        if self.bpp <= 8:
            o = n = 0
            for p in self.dat:
                c = self.pal[p]
                d[o:o+3] = c[0:3]
                o += 3
                a[n] = c[3]
                n += 1
        elif self.bpp == 32:
            o = x = 0
            for p in range(len(self.dat)//4):
                d[o:o+3] = self.dat[x:x+3]
                o += 3
                lll = self.dat[x+3]
                a[p] = lll
                x += 4
        img = wx.Image(self.width,self.height,d)
        img.SetAlpha(a)
        return img

class GeometryList:
    def __init__(self):
        pass
    def __init__(self, f):
        self.load(f)
    def load(self, f):
        self.geos = []
        self.u1,self.flags = readpack(f, "II")
        if self.flags & 0x800:
            return
        num_geos = 1
        if self.flags & 0x2000:
            num_geos, = readpack(f, "I")
        for i in range(num_geos):
            self.geos.append(Geometry(f))

class Geometry:
    class Material:
        pass
    def __init__(self):
        pass
    def __init__(self, f):
        self.load(f)
    def load(self, f):
        def dbg(*args):
            pass #print(*args)
        self.valid = False
        atomt,atoms,atomv = readpack(f, "III")
        dbg('aaa', atomt,atoms,atomv)
        if atomt == 0xE:
            f.seek(atoms, os.SEEK_CUR)
            atomt,atoms,atomv = readpack(f, "III")
        assert atomt == 0x14
        geoend = f.tell() + atoms
        stt, sts, stv = readpack(f, "III")
        assert stt == 1 and sts == 16
        av = readpack(f, "4I")
        
        gmt, gms, gmv = readpack(f, "III")
        assert gmt == 0xF
        stt, sts, stv = readpack(f, "III")
        assert stt == 1
        self.flags,self.num_uvmaps = readpack(f, "HH")
        self.num_tris,self.num_verts, = readpack(f, "II")
        self.num_morph_targets, = readpack(f, "I")
        dbg('num_morph_targets:', self.num_morph_targets)
        assert self.num_morph_targets == 1
        self.colors = []
        for i in range(self.num_verts):
            self.colors.append(readpack(f, "4B"))
        self.texcrd = []
        for i in range(self.num_verts):
            self.texcrd.append(readpack(f, "ff"))
        dbg(self.num_uvmaps)
        f.seek(8*self.num_verts*(self.num_uvmaps-1), os.SEEK_CUR)
        self.tris = []
        for i in range(self.num_tris):
            t = readpack(f, "4H")
            self.tris.append((t[0],t[1],t[3],t[2]))
        self.sphere = readpack(f, "4f")
        self.haspos,self.hasnorms = readpack(f, "II")
        #for i in range(self.num_morph_targets):
        self.verts = []
        for j in range(self.num_verts):
            self.verts.append(readpack(f, "fff"))
        self.normals = []
        if self.flags & 0x10:
            for j in range(self.num_verts):
                self.normals.append(readpack(f, "fff"))
        dbg('ml', hex(f.tell()))

##        dbg('num_tris:', self.num_tris)
##        dbg('num_verts:', self.num_verts)
##        dbg('num_morph_targets:', self.num_morph_targets)
##        dbg('colors:', self.colors)
##        dbg('texcrd:', self.texcrd)
##        dbg('tris:', self.tris)
##        dbg('sphere:', self.sphere)
##        dbg('verts:', self.verts)
        
        mlt, mls, mlv = readpack(f, "III")
        dbg(mlt,mls,mlv)
        assert mlt == 8
        stt, sts, stv = readpack(f, "III")
        dbg('sts:', sts)
        assert stt == 1 and sts in (4,8)
        num_mats, = readpack(f, "I")
        dbg(num_mats)
        if num_mats > 0:
            readpack(f, "I")
        self.materials = []
        for i in range(num_mats):
            m = self.Material()
            mat, mas, mav = readpack(f, "III")
            assert mat == 7
            stt, sts, stv = readpack(f, "III")
            assert stt == 1 and sts == 28
            m.u1,m.color,m.u2,m.textured,m.ambient,m.specular,m.diffuse = readpack(f, "IIIIfff")
            dbg('txt:', hex(f.tell()))
            if m.textured:
                txt, txs, txv = readpack(f, "III")
                assert txt == 6
                stt, sts, stv = readpack(f, "III")
                assert stt == 1 and sts == 4
                mfl, = readpack(f, "I")
                m.filter = mfl & 255
                m.uaddress = (mfl << 8) & 15
                m.vaddress = (mfl << 12) & 15
                nat, nas, nav = readpack(f, "III")
                assert nat == 2
                m.name = f.read(nas).rstrip(b'\0')
                nat, nas, nav = readpack(f, "III")
                assert nat == 2
                m.maskname = f.read(nas).rstrip(b'\0')
                dbg(m.name)
            else:
                m.name = b'NoTexture'
            self.materials.append(m)
        
        #f.seek(mls, os.SEEK_CUR)
        f.seek(geoend, os.SEEK_SET)
        dbg('yes')
        self.valid = True

class UnknownView(wx.Panel):
    def __init__(self, chk, *args, **kw):
        super(UnknownView,self).__init__(*args,**kw)
        wx.StaticText(self, label=str(chk))

class TexDictView(wx.Panel):
            
    def __init__(self, chk, *args, **kw):
        super().__init__(*args,**kw)
        self.chk = chk
        #self.SetBackgroundColour(wx.Colour(255,0,0))
        self.split1 = split1 = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE|wx.SP_3D)#, size=(700,500))
        self.lb = wx.ListBox(split1)
        tp = self.tp = wx.Panel(split1)
        split1.SplitVertically(self.lb, tp, 150)
        bs = wx.BoxSizer(orient=wx.VERTICAL)
        cmds = wx.BoxSizer()
        bt = wx.Button(tp, label="Replace texture")
        bt2 = wx.Button(tp, label="Save dictionary")
        cmds.AddMany((bt,bt2))
        #self.sb = wx.StaticBitmap(tp,size=wx.Size(256,256))
        #self.sb.SetSize(wx.Size(256,256))
        bs.Add(cmds)
        #bs.Add(self.sb, proportion=1, flag=wx.EXPAND)
        tp.SetSizerAndFit(bs)
        #bmp = wx.Bitmap(256,256)
        #self.sb.SetBitmap(bmp)

        self.curbmp = None
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.lb.Bind(wx.EVT_LISTBOX, self.seltexchanged)
        bt.Bind(wx.EVT_BUTTON, self.replacetex)
        bt2.Bind(wx.EVT_BUTTON, self.savedict)
        tp.Bind(wx.EVT_PAINT, self.OnPaint)
        
        f = io.BytesIO(chk.data)
        #if True: fstbyte, = readpack(f, "B")
        num_tex, = readpack(f, "I")
        self.textures = []
        for i in range(num_tex):
            t = Texture(f)
            self.textures.append(t)
            self.lb.Append(t.name.decode(encoding='latin_1'))

    def OnSize(self, event):
        self.split1.SetSize(self.GetClientSize())

    def seltexchanged(self, event):
        #item = event.GetSelection()
        #tex = self.textures[item]
        self.drawtex()
    
    def drawtex(self):
        tex = self.textures[self.lb.GetSelection()]
        img = tex.convertToWxImage()
        self.curbmp = img.ConvertToBitmap()
        self.tp.Refresh()
        #self.sb.SetBitmap(img.ConvertToBitmap())
        #self.sb.SetSize(wx.Size(256,256))
        #self.sb.Refresh()

    def OnPaint(self, event):
        dc = wx.PaintDC(event.GetEventObject())
        #dc.DrawLine(0,0,100,150)
        if self.curbmp:
            dc.DrawBitmap(self.curbmp, 48, 48)

    def replacetex(self, event):
        fn = wx.FileSelector("Replace texture with")
        print(fn)
        if not fn.strip():
            return
        newimg = wx.Image(fn)
        newdat = newimg.GetData()
        tex = self.textures[self.lb.GetSelection()]
        tex.width = newimg.GetWidth()
        tex.height = newimg.GetHeight()
        tex.bpp = 32
        tex.pitch = tex.width * 4
        tex.pal = []
        tex.dat = bytearray(tex.pitch*tex.height)
        x = y = 0
        for i in range(tex.width*tex.height):
            tex.dat[x:x+4] = (*newdat[y:y+3], 255)
            x += 4
            y += 3
        self.drawtex()
        
    def update(self, chk):
        bo = io.BytesIO()
        writepack(bo, "I", len(self.textures))
        for t in self.textures:
            t.save(bo)
        bo.seek(0, os.SEEK_SET)
        chk.data = bo.read()

    def savedict(self, event):
        self.update(self.chk)

class GeometryView(wx.glcanvas.GLCanvas):
            
    def __init__(self, chk, files, *args, **kw):
        super().__init__(*args,**kw)
        self.context = wx.glcanvas.GLContext(self)
        self.glinitialized = False
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMotion)
        self.Bind(wx.EVT_LEFT_UP, self.OnMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
        self.Bind(wx.EVT_CHAR, self.OnChar)

        self.texdicts = []
        for kk in files:
            if kk == None: continue
            if not ((9,2) in kk.kclasses): continue
            tc = kk.kclasses[(9,2)].chunks[0]
            f = io.BytesIO(tc.data)
            num_tex, = readpack(f, "I")
            textures = []
            for i in range(num_tex):
                t = Texture(f)
                textures.append(t)
            self.texdicts.append(textures)
            
        self.geolist = GeometryList(io.BytesIO(chk.data))
        self.geoindex = 0
        self.geo = self.geolist.geos[self.geoindex]

        center = [0,0,0]
        if self.geo.valid:
            if len(self.geo.verts) > 0:
                for v in self.geo.verts:
                    for i in range(3):
                        center[i] += v[i]
                for i in range(3):
                    center[i] /= len(self.geo.verts)
        center[2] += 10

        self.campos = tuple(center)
        self.camdir = (0,0,-1)
        self.camstr = (1,0,0)
        self.camori_y = math.pi
        self.camori_x = 0
        self.dragstart_m = None
        self.dragstart_o = None

        self.wireframe = False

    def OnEraseBackground(self, event):
        pass
    def OnSize(self, event):
        self.Refresh()
    def OnMotion(self, event):
        if event.LeftDown():
            self.dragstart_m = event.GetPosition()
            self.dragstart_y = self.camori_y
            self.dragstart_x = self.camori_x
            print(self.dragstart_m)
        elif event.LeftUp():
            self.dragstart_m = None
            self.dragstart_y = self.dragstart_x = None
        elif event.Dragging():
            rel = event.GetPosition() - self.dragstart_m
            self.camori_y = self.dragstart_y - rel.x * math.pi / 200
            self.camori_x = self.dragstart_x - rel.y * math.pi / 200
            #self.camdir = (math.sin(self.camori_y),0,math.cos(self.camori_y))
            self.camdir = (math.sin(self.camori_y)*math.cos(self.camori_x), math.sin(self.camori_x), math.cos(self.camori_y)*math.cos(self.camori_x))
            self.camstr = (math.cos(self.camori_y), 0, -math.sin(self.camori_y))
            self.Refresh()
    def OnWheel(self, event):
        w = event.GetWheelRotation()
        a = event.GetWheelAxis()
        if a == wx.MOUSE_WHEEL_VERTICAL:
            self.campos = tuple(self.campos[x] - self.camdir[x]*w*0.1 for x in range(3))
        elif a == wx.MOUSE_WHEEL_HORIZONTAL:
            self.campos = tuple(self.campos[x] - self.camstr[x]*w*0.1 for x in range(3))
        self.Refresh()
    def OnChar(self, event):
        key = chr(event.GetKeyCode()).upper()
        if key == 'Z':
            self.campos = tuple(self.campos[x] + self.camdir[x] for x in range(3))
        if key == 'S':
            self.campos = tuple(self.campos[x] - self.camdir[x] for x in range(3))
        if key == 'Q':
            self.campos = tuple(self.campos[x] + self.camstr[x] for x in range(3))
        if key == 'D':
            self.campos = tuple(self.campos[x] - self.camstr[x] for x in range(3))
        if key == 'L':
            self.wireframe = not self.wireframe
        if key == 'O':
            if self.geoindex > 0:
                self.geoindex -= 1
                self.geo = self.geolist.geos[self.geoindex]
        if key == 'P':
            if self.geoindex < len(self.geolist.geos)-1:
                self.geoindex += 1
                self.geo = self.geolist.geos[self.geoindex]
        self.Refresh()

    def InitGL(self):
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GEQUAL, 0.8)
        for g in self.geolist.geos:
            g.gltextures = []
            for m in g.materials:
                fnd = None
                for d in self.texdicts:
                    for t in d:
                        if t.name == m.name:
                            fnd = t
                if fnd:
                    if fnd.bpp <= 8:
                        td = bytearray(fnd.width*fnd.height*4)
                        for i in range(fnd.width*fnd.height):
                            td[4*i:4*i+4] = fnd.pal[fnd.dat[i]]
                    elif fnd.bpp == 32:
                        td = fnd.dat
                    else:
                        assert False
                    glt = glGenTextures(1)
                    glBindTexture(GL_TEXTURE_2D, glt)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, fnd.width, fnd.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, bytes(td))
                    g.gltextures.append(glt)
                else:
                    g.gltextures.append(None)
        self.glinitialized = True
        
    def OnPaint(self, event):
        c = wx.PaintDC(self)
        if self.IsShown() and self.geo.valid:
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
            gluPerspective(60, winsize.width/winsize.height, 0.1, 100)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            center = [self.campos[x] + self.camdir[x] for x in range(3)]
            gluLookAt(*self.campos, *center, 0,1,0)

            curtex = None
            glBegin(GL_TRIANGLES)
            for t in self.geo.tris:
                ttx = self.geo.gltextures[t[3]]
                if ttx != curtex:
                    glEnd()
                    if ttx == None:
                        glDisable(GL_TEXTURE_2D)
                    else:
                        glEnable(GL_TEXTURE_2D)
                        glBindTexture(GL_TEXTURE_2D, ttx)
                    curtex = ttx
                    glBegin(GL_TRIANGLES)
                for i in range(3):
                    x = t[i]
                    c = self.geo.colors[x]
                    glColor4ub(c[0],c[1],c[2],c[3])
                    u = self.geo.texcrd[x]
                    glTexCoord2f(u[0],u[1])
                    v = self.geo.verts[x]
                    glVertex3f(v[0],v[1],v[2])
            glEnd()
            self.SwapBuffers()

class MoreSpecificInfoView(wx.TextCtrl):
    def __init__(self, chk, *args, **kw):
        super().__init__(style=wx.TE_MULTILINE|wx.TE_DONTWRAP,*args,**kw)
        txt = io.StringIO()
        dattype = (chk.kcl.cltype,chk.kcl.clid)
        if dattype == (12,18) or dattype == (12,19): # CGround or CDynamicGround
            txt.write("CGround!\n\n")
            bi = io.BytesIO(chk.data)
            numa,num_tris,num_verts = readpack(bi, "IHH")
            print('numa =', numa)
            print('num_tris =', num_tris)
            print('num_verts =', num_verts)
            print('Indices:')
            for i in range(num_tris):
                print(readpack(bi, "HHH"))
            print('Vertices:')
            for i in range(num_verts):
                print(readpack(bi, "fff"))
            print('Misc:')
            print(hex(bi.tell()))
            print(readpack(bi, "6f"))
            print(hex(bi.tell()))
        txt.seek(0, os.SEEK_SET)
        self.SetValue(txt.read())

class HexView(wx.TextCtrl):
    def __init__(self, chk, *args, **kw):
        super().__init__(style=wx.TE_MULTILINE|wx.TE_DONTWRAP,*args,**kw)
        self.SetFont(wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        txt = io.StringIO()
        hexdump(txt, chk.data)
        txt.seek(0, os.SEEK_SET)
        self.SetValue(txt.read())

class StringTable:
    def __init__(self):
        pass
    def __init__(self, f):
        self.load(f)
    def load(self, f):
        numThings, = readpack(f, "H")
        self.thingTable1 = []
        self.thingTable2 = []
        for i in range(numThings): self.thingTable1.append(readpack(f, "I")[0])
        for i in range(numThings): self.thingTable2.append(readpack(f, "I")[0])
        print('x', hex(f.tell()))
        # Strings with ID
        self.identifiedStrings = []
        totchars, = readpack(f, "I")
        charsread = 0
        while charsread < totchars:
            print('z', hex(f.tell()))
            sid,slen = readpack(f, "II")
            self.identifiedStrings.append((sid,f.read(2*slen).decode(encoding='utf_16_le')))
            charsread += slen
        print('y', hex(f.tell()))
        # Strings without ID
        self.anonymousStrings = []
        totchars, = readpack(f, "I")
        charsread = 0
        while charsread < totchars:
            slen, = readpack(f, "I")
            self.anonymousStrings.append(f.read(2*slen).decode(encoding='utf_16_le'))
            charsread += slen
    def save(self, f):
        numThings = len(self.thingTable1)
        writepack(f, "H", numThings)
        for i in range(numThings): writepack(f, "I", self.thingTable1[i])
        for i in range(numThings): writepack(f, "I", self.thingTable2[i])
        # Strings with ID
        totchars = 0
        enc = []
        for s in self.identifiedStrings:
            e = s[1].encode(encoding='utf_16_le')
            enc.append((s[0],e))
            totchars += len(e)//2
        writepack(f, "I", totchars)
        for e in enc:
            writepack(f, "II", e[0], len(e[1])//2)
            f.write(e[1])
        # Strings without ID
        totchars = 0
        enc = []
        for s in self.anonymousStrings:
            e = s.encode(encoding='utf_16_le')
            enc.append(e)
            totchars += len(e)//2
        writepack(f, "I", totchars)
        for e in enc:
            writepack(f, "I", len(e)//2)
            f.write(e)

class LocTextViewer(wx.dataview.DataViewListCtrl): #(wx.Panel):
    zeroString = "[0-sized string, DO NOT CHANGE!]"
    def __init__(self, chk, *args, **kw):
        super().__init__(*args,**kw)
        #self.dvlc = wx.dataview.DataViewListCtrl(self)
        self.dvlc = self
        self.dvlc.AppendTextColumn("ID")
        self.dvlc.AppendTextColumn("Text", wx.dataview.DATAVIEW_CELL_EDITABLE)
        self.dvlc.AppendTextColumn("Original text")
        #self.dvlc.AppendItem((1,2,3))
        self.frdata = wx.FindReplaceData()
        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_MENU, self.FindText, id=1000)

        self.strtab = StringTable(io.BytesIO(chk.data))
        #print(self.strtab.identifiedStrings)
        for s in self.strtab.identifiedStrings:
            t = s[1] if len(s[1]) else self.zeroString
            self.dvlc.AppendItem((s[0],t,t))
        for s in self.strtab.anonymousStrings:
            t = s if len(s) else self.zeroString
            self.dvlc.AppendItem(('/',t,t))
            
    def update(self,chk):
        self.strtab.identifiedStrings = []
        self.strtab.anonymousStrings = []
        for i in range(self.dvlc.GetItemCount()):
            varid = self.dvlc.GetTextValue(i,0)
            vartxt = self.dvlc.GetTextValue(i,1)
            if vartxt == self.zeroString:
                s = ''
            else:
                s = vartxt + '\0'
            if varid == '/':
                self.strtab.anonymousStrings.append(s)
            else:
                self.strtab.identifiedStrings.append((int(varid),s))

        bo = io.BytesIO()
        self.strtab.save(bo)
        bo.seek(0, os.SEEK_SET)
        chk.data = bo.read()

    def OnContextMenu(self, ev):
        m = wx.Menu()
        m.Append(1000, "Find...")
        self.PopupMenu(m)

    def FindText(self, ev):
        self.frdialog = wx.FindReplaceDialog(self, self.frdata)
        self.frdialog.Bind(wx.EVT_FIND, self.OnFind)
        self.frdialog.Bind(wx.EVT_FIND_NEXT, self.OnFind)
        self.frdialog.Show()

    def OnFind(self, ev):
        r = self.GetSelectedRow()
        if r == wx.NOT_FOUND:
            r = 0
        else:
            r += 1
        while r < self.GetItemCount():
            if self.frdata.GetFindString() in self.GetValue(r,1):
                self.SelectRow(r)
                self.EnsureVisible(self.RowToItem(r))
                break
            r += 1
