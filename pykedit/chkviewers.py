import io,math,os,struct,time
import wx,wx.glcanvas,wx.dataview #,wx.html
from OpenGL.GL import *
from OpenGL.GLU import *
from utils import *
from objects import *
from kfiles import *
import kfiles

class UnknownView(wx.Panel):
    def __init__(self, chk, *args, **kw):
        super(UnknownView,self).__init__(*args,**kw)
        wx.StaticText(self, label=str(chk)+
            "\nGUID: "+(''.join(('%X' % i for i in chk.guid)) if chk.guid else 'None')+
            "\nSize: " + str(len(chk.data)) +
            "\nNothing to see right now!\nWhat you can do however is toggle the 'Hex' button\nin the bottom to see the binary content.")

class TexDictView(wx.Panel):
            
    def __init__(self, chk, *args, **kw):
        self.texdic = TextureDictionary(io.BytesIO(chk.data),ver=chk.ver,lv=(chk.kcl.cltype==13))
        
        super().__init__(*args,**kw)
        self.chk = chk
        #self.SetBackgroundColour(wx.Colour(255,0,0))
        self.split1 = split1 = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE|wx.SP_3D)#, size=(700,500))
        self.lb = wx.ListBox(split1)
        tp = self.tp = wx.Panel(split1)
        split1.SplitVertically(self.lb, tp, 180)
        bs = wx.BoxSizer(orient=wx.VERTICAL)
        cmds = wx.BoxSizer()
        bt = wx.Button(tp, label="Replace texture")
        bt2 = wx.Button(tp, label="Save dictionary")
        cmds.AddMany((bt,bt2))
        #self.sb = wx.StaticBitmap(tp,size=wx.Size(256,256))
        #self.sb.SetSize(wx.Size(256,256))
        self.infotxt = wx.StaticText(tp)
        bs.Add(cmds)
        bs.Add(self.infotxt)
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
        
        self.textures = self.texdic.textures
        for t in self.textures:
            self.lb.Append(t.name.decode(encoding='latin_1'))

    def OnSize(self, event):
        self.split1.SetSize(self.GetClientSize())

    def seltexchanged(self, event):
        tex = self.textures[event.GetSelection()]
        self.infotxt.SetLabel('Size: %ix%i pixels\n%i bits per pixel' % (tex.width,tex.height,tex.bpp))
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
            dc.DrawBitmap(self.curbmp, 0, 96)

    def replacetex(self, event):
        fn = wx.FileSelector("Replace texture with", wildcard="Image file " + wx.Image.GetImageExtWildcard())
        print(fn)
        if not fn.strip():
            return
        newimg = wx.Image(fn)
        newdat = newimg.GetData()
        hasalp = newimg.HasAlpha()
        if hasalp:
            newalp = newimg.GetAlpha()
        tex = self.textures[self.lb.GetSelection()]
        self.modified = True
        tex.width = newimg.GetWidth()
        tex.height = newimg.GetHeight()
        tex.bpp = 32
        tex.pitch = tex.width * 4
        tex.pal = []
        tex.dat = bytearray(tex.pitch*tex.height)
        x = y = a = 0
        for i in range(tex.width*tex.height):
            tex.dat[x:x+4] = (*newdat[y:y+3], newalp[a] if hasalp else 255)
            x += 4
            y += 3
            a += 1
        self.drawtex()
        
    def update(self, chk):
        bo = io.BytesIO()
        self.texdic.save(bo, chk.ver)
        bo.seek(0, os.SEEK_SET)
        chk.data = bo.read()
        self.modified = False

    def savedict(self, event):
        self.update(self.chk)

class GeometryView(wx.glcanvas.GLCanvas):
            
    def __init__(self, chk, files, *args, **kw):
        self.valid = False
        
        self.texdicts = []
        for kk in files:
            if kk == None: continue
            if not ((9,2) in kk.kclasses): continue
            tc = kk.kclasses[(9,2)].chunks[0]
            tdt = TextureDictionary(io.BytesIO(tc.data), tc.ver)
            self.texdicts.append(tdt.textures)
            
        self.geolist = GeometryList(io.BytesIO(chk.data), ver=chk.ver)
        self.geoindex = 0
        if self.geolist.geos:
            self.geo = self.geolist.geos[self.geoindex]
            self.valid = self.geo.valid

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
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

        center = [0,0,0]
        if self.valid:
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
        if key == 'Z' or key == 'W':
            self.campos = tuple(self.campos[x] + self.camdir[x] for x in range(3))
        if key == 'S':
            self.campos = tuple(self.campos[x] - self.camdir[x] for x in range(3))
        if key == 'Q' or key == 'A':
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
    def OnLeftDown(self, event):
        self.SetFocus()
        event.Skip()

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
        if self.IsShown() and self.valid:
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
            glColor4f(1,1,1,1)
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
                    if self.geo.colors:
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
        super().__init__(style=wx.TE_MULTILINE|wx.TE_DONTWRAP|wx.TE_READONLY,*args,**kw)
        txt = io.StringIO()
        if type(chk) == KChunk:
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
            elif dattype == (13,3): # CCloneManager
                def to(*args): print(*args)
                to("clones")
                bi = io.BytesIO(chk.data)
##                nthings,n1,n2,n3,n4 = readpack(bi, "5I")
##                for i in range(nthings):
##                    to(i, ':', *readpack(bi, "I"))
##                bi.seek(4*nthings, os.SEEK_CUR)
                o1,o2,u1,nthings = readpack(bi, "4i")
                qt = readpack(bi, "4i")
                o3, = readpack(bi, "i")
                bi.seek(4*nthings, os.SEEK_CUR)
                
                for team in range(2):
                    print('team', team, 'at', hex(bi.tell()))
                    tmt,tms,tmv = readpack(bi, "3I")
                    assert tmt == 0x22
                    #bi.seek(tms, os.SEEK_CUR)
                    stt,sts,stv = readpack(bi, "3I")
                    assert stt == 1
                    ndings,n5 = readpack(bi, "2I")
                    for i in range(ndings):
                        readpack(bi, "I")
                    s = 0
                    for i in range(320):
                        print('atom', i, 'at', hex(bi.tell()))
                        two, = readpack(bi, "i")
                        print('t:', two, '/ s:', s)
                        if two != -1: #0xffffffff:
                            s += two
                            att, ats, atv = readpack(bi, "3I")
                            assert att == 0x14
                            bi.seek(ats, os.SEEK_CUR)
            elif dattype[0] == 11: # Node
                def readobjref(kwn):
                    i, = readpack(kwn, 'I')
                    if i == 0xFFFFFFFF:
                        return None
                    elif i == 0xFFFFFFFD:
                        return kwn.read(16)
                    else:
                        return (i & 63, (i>>6) & 2047, i >> 17)
                def objrefstr(objref):
                    if type(objref) == tuple:
                        return getclname(objref[0], objref[1]) + ', ' + str(objref[2])
                    else:
                        return str(objref)
                bi = io.BytesIO(chk.data)
                mtx = readpack(bi, '16f')
                parent = readobjref(bi)
                txt.write('Matrix:\n')
                for i in range(4):
                    txt.write('%f %f %f\n' % (mtx[4*i+0], mtx[4*i+1], mtx[4*i+2]))
                txt.write('\nParent: %s\n' % objrefstr(parent))
                txt.write('\nUnknown 1: ' + str(*readpack(bi, 'I' if chk.ver >= 2 else 'H')))
                txt.write('\nUnknown 2: ' + str(*readpack(bi, 'B')))
                txt.write('\nNext Object: ' + objrefstr(readobjref(bi)))
                txt.write('\nSubordinate Object: ' + objrefstr(readobjref(bi)))
                try:
                    txt.write('\nSome Object: ' + objrefstr(readobjref(bi)))
                    txt.write('\nAnother Object: ' + objrefstr(readobjref(bi)))
                except:
                    txt.write('\nThat\'s all.')
        elif type(chk) == KClass:
            for i in chk.__dict__:
                print(i, ':', chk.__dict__[i], file=txt)
        txt.seek(0, os.SEEK_SET)
        self.SetValue(txt.read())

class HexView(wx.TextCtrl):
    def __init__(self, chk, *args, **kw):
        super().__init__(style=wx.TE_MULTILINE|wx.TE_DONTWRAP|wx.TE_READONLY,*args,**kw)
        self.SetFont(wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        txt = io.StringIO()
        if type(chk) == KChunk:
            hexdump(txt, chk.data)
        else:
            hexdump(txt, chk)
        txt.seek(0, os.SEEK_SET)
        self.SetValue(txt.read())

class LocTextViewer(wx.dataview.DataViewListCtrl): #(wx.Panel):
    zeroString = "[0-sized string, DO NOT CHANGE!]"
    def __init__(self, chk, *args, **kw):
        self.strtab = StringTable(io.BytesIO(chk.data), chk.ver)

        super().__init__(*args,**kw)
        #self.dvlc = wx.dataview.DataViewListCtrl(self)
        self.dvlc = self
        self.dvlc.AppendTextColumn("ID")
        self.dvlc.AppendTextColumn("Text", wx.dataview.DATAVIEW_CELL_EDITABLE)
        self.dvlc.AppendTextColumn("Original text")
        #self.dvlc.AppendItem((1,2,3))
        self.frdata = wx.FindReplaceData()
        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self.OnValueChanged)
        self.Bind(wx.EVT_MENU, self.FindText, id=1000)

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
        self.strtab.save(bo, chk.ver)
        bo.seek(0, os.SEEK_SET)
        chk.data = bo.read()
        self.modified = False

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

    def OnValueChanged(self, ev):
        self.modified = True

##class HtmlHomeViewer(wx.html.HtmlWindow):
##    def __init__(self, *args, **kw):
##        super().__init__(*args,**kw)
##        self.SetPage("Hello <b>guys</b>!"
##                     "<ol>"
##                     "<li>Select the version of the in game in the <b>Version</b> menu.</li>"
##                     "<li>Open a KWN file by clicking <b>File > Open</b> or by <b>drag-dropping</b> the file here.</li>"
##                     "</ol>")

class HomeViewer(wx.Panel):
    def __init__(self, versetters, *args, **kw):
        super().__init__(*args,**kw)
        bs = wx.BoxSizer(wx.VERTICAL)
        s1=wx.StaticText(self, label="Welcome to the XXL Editor!")
        s1.SetFont(wx.Font(12, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        s2=wx.StaticText(self, label="First, select the game you want to mod/explore:")
        self.versel = wx.RadioBox(self, choices=['Asterix XXL 1', 'Asterix XXL 2', 'Asterix Olympic Games']) #, label="Select the game you want to mod/explore:")
        self.versel.SetSelection(kfiles.kver-1)
        bs.AddMany((s1,s2,self.versel))
        bs.Add(wx.StaticText(self, label="Then open the file by drag-dropping a KWN file in this window."))
        bs.Add(wx.StaticText(self, label="For more help, click Help > Readme."))
        self.SetSizer(bs)
        self.versel.Bind(wx.EVT_RADIOBOX, self.OnRadioBox)
        self.versetters = versetters

    def OnRadioBox(self, evt):
        self.versetters[self.versel.GetSelection()](None)
        
