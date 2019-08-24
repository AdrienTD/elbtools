import io,math,os,struct,time
import wx,wx.glcanvas,wx.dataview #,wx.html
from OpenGL.GL import *
from OpenGL.GLU import *
from utils import *
from objects import *
from kfiles import *
import kfiles

# def readobjref(kwn):
#     i, = readpack(kwn, 'I')
#     if i == 0xFFFFFFFF:
#         return None
#     elif i == 0xFFFFFFFD:
#         return kwn.read(16)
#     else:
#         return (i & 63, (i>>6) & 2047, i >> 17)

class UnknownView(wx.TextCtrl):
    def __init__(self, chk, *args, **kw):
        super(UnknownView,self).__init__(*args,**kw,style=wx.TE_MULTILINE|wx.TE_READONLY,value=str(chk)+
            "\nGUID: "+(''.join(('%02X' % i for i in chk.guid)) if chk.guid else 'None')+
            "\nSize: " + str(len(chk.data)) +
            "\nNothing to see right now!\nWhat you can do however is toggle the 'Hex' button\nin the bottom to see the binary content.")

class TexDictView(wx.Panel):
            
    def __init__(self, chk, *args, **kw):
        self.texdic = TextureDictionary(io.BytesIO(chk.data),ver=chk.ver,lv=(chk.kcl.cltype==13))
        
        super().__init__(*args,**kw)
        self.chk = chk
        #self.SetBackgroundColour(wx.Colour(255,0,0))
        self.split1 = split1 = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE|wx.SP_3D)#, size=(700,500))
        self.split1.SetMinimumPaneSize(16)
        self.lb = wx.ListBox(split1)
        tp = self.tp = wx.Panel(split1)
        split1.SplitVertically(self.lb, tp, 180)
        bs = wx.BoxSizer(orient=wx.VERTICAL)
        cmds = wx.BoxSizer()
        bt = wx.Button(tp, label="Replace texture")
        bt2 = wx.Button(tp, label="Save dictionary")
        bt3 = wx.Button(tp, label="Insert texture")
        cmds.AddMany((bt,bt3,bt2))
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
        bt3.Bind(wx.EVT_BUTTON, self.inserttex)
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
        fn = wx.FileSelector("Replace texture with", wildcard="Image file " + wx.Image.GetImageExtWildcard(), flags=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        if not fn.strip():
            return
        newimg = wx.Image(fn)
        if not newimg.HasAlpha():
            newimg.InitAlpha()
        tex = self.textures[self.lb.GetSelection()]
        self.modified = True
        tex.loadFromWxImage(newimg)
        self.drawtex()
        
    def update(self, chk):
        bo = io.BytesIO()
        self.texdic.save(bo, chk.ver)
        bo.seek(0, os.SEEK_SET)
        chk.data = bo.read()
        self.modified = False

    def savedict(self, event):
        self.update(self.chk)

    def inserttex(self, event):
        #fn = wx.FileSelector("Insert texture", wildcard="Image file " + wx.Image.GetImageExtWildcard(), flags=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        # if not fn.strip():
        #     return
        fdlg = wx.FileDialog(self, "Insert texture", wildcard="Image file " + wx.Image.GetImageExtWildcard(), style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST|wx.FD_MULTIPLE)
        if fdlg.ShowModal() == wx.ID_CANCEL:
            return
        for fn in fdlg.GetPaths():
            newimg = wx.Image(fn)
            if not newimg.HasAlpha():
                newimg.InitAlpha()
            tex = Texture()
            tex.loadFromWxImage(newimg)
            tex.name = os.path.splitext(os.path.basename(fn))[0].encode(encoding='latin_1')[:31]
            if self.textures:
                tex.rwver = self.textures[0].rwver
            else:
                tex.rwver = 0x1803FFFF
            tex.v = (2,1,1)
            self.modified = True
            self.textures.append(tex)
            self.lb.Append(tex.name.decode(encoding='latin_1'))
        

class GeometryView(wx.glcanvas.GLCanvas):
            
    def __init__(self, chk, files, *args, **kw):
        self.valid = False
        
        self.texdicts = []
        for kk in files:
            if kk == None: continue
            if not ((9,2) in kk.kclasses): continue
            try:
                tc = kk.kclasses[(9,2)].chunks[0]
                tdt = TextureDictionary(io.BytesIO(tc.data), tc.ver)
                self.texdicts.append(tdt.textures)
            except Exception as e:
                print('Failed to load texture dictionary:', e)
            
        self.geolists = []
        c = chk
        self.chk = chk
        while c:
            gl = GeometryList(io.BytesIO(c.data), ver=c.ver, kfiles=files)
            self.geolists.append(gl)
            c = gl.nextgeo
        assert self.geolists

        self.geoindex = 0
        if self.geolists[0].geos:
            self.geo = self.geolists[0].geos[self.geoindex]
            self.valid = self.geo.valid

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
        self.Bind(wx.EVT_MENU, self.CmdSaveOBJ, id=1000)
        self.Bind(wx.EVT_MENU, self.CmdTestSaveRw, id=9001)

        for i in (1001,1002,1003,1004):
            self.Bind(wx.EVT_MENU, self.CmdChangeView, id=i)

        accent = [wx.AcceleratorEntry(0, ord('L'), 1001),
                  wx.AcceleratorEntry(0, ord('M'), 1002),
                  wx.AcceleratorEntry(0, ord('O'), 1003),
                  wx.AcceleratorEntry(0, ord('P'), 1004)]
        acctab = wx.AcceleratorTable(accent)
        self.SetAcceleratorTable(acctab)

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
        self.camstr = (-1,0,0)
        self.camori_y = math.pi
        self.camori_x = 0
        self.dragstart_m = None
        self.dragstart_o = None

        self.wireframe = False
        self.shownextgeos = False

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
        self.Refresh()
    def OnLeftDown(self, event):
        self.SetFocus()
        event.Skip()

    def InitGL(self):
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GEQUAL, 0.8)
        for l in self.geolists:
            for g in l.geos:
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
            for gl in self.geolists if self.shownextgeos else self.geolists[0:1]:
                geo = gl.geos[self.geoindex]
                for t in geo.tris:
                    ttx = geo.gltextures[t[3]]
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
                        if geo.colors:
                            c = geo.colors[x]
                            glColor4ub(c[0],c[1],c[2],c[3])
                        if geo.texcrd:
                            u = geo.texcrd[x]
                            glTexCoord2f(u[0],u[1])
                        v = geo.verts[x]
                        glVertex3f(v[0],v[1],v[2])
            glEnd()
            self.SwapBuffers()

    def OnContextMenu(self, evt):
        m = wx.Menu()
        m.AppendCheckItem(1001, "Wireframe\tL")
        m.AppendCheckItem(1002, "Show connected geometries\tM")
        m.Append(1003, "Previous costume\tO")
        m.Append(1004, "Next costume\tP")
        m.AppendSeparator()
        m.Append(1000, "Save as OBJ...")
        m.Check(1001, self.wireframe)
        m.Check(1002, self.shownextgeos)
        m.AppendSeparator()
        m.Append(9001, "Test resaving in rw format")
        self.PopupMenu(m)

    def CmdChangeView(self, evt):
        cmd = evt.GetId()
        if cmd == 1001:
            self.wireframe = not self.wireframe
        elif cmd == 1003:
            if self.geoindex > 0:
                self.geoindex -= 1
                self.geo = self.geolists[0].geos[self.geoindex]
        elif cmd == 1004:
            if self.geoindex < len(self.geolists[0].geos)-1:
                self.geoindex += 1
                self.geo = self.geolists[0].geos[self.geoindex]
        elif cmd == 1002:
            self.shownextgeos = not self.shownextgeos
        self.Refresh()

    def CmdSaveOBJ(self, evt):
        fn = wx.FileSelector("Export to OBJ", wildcard="OBJ model file (*.obj)|*.obj", flags=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if not fn.strip(): return
        matlist = []
        with open(fn, 'w') as objfile:
            objfile.write('mtllib %s.mtl\n' % os.path.splitext(os.path.basename(fn))[0])
            base,normbase = 1,1
            for gl in self.geolists if self.shownextgeos else self.geolists[0:1]:
                geo = gl.geos[self.geoindex]
                base,normbase = geo.exportToOBJ(objfile, base, normbase)
                matlist.extend(geo.materials)
        mtlname = os.path.splitext(fn)[0] + ".mtl"
        with open(mtlname, 'w') as mtlfile:
            mtlfile.write('newmtl NoTexture\n')
            for mat in matlist:
                name = mat.name.decode(encoding='latin_1')
                mtlfile.write('newmtl %s\nKa 1.0 1.0 1.0\nKd 1.0 1.0 1.0\nmap_Kd textures/%s\n' % (name, name+'.png'))

    def CmdTestSaveRw(self, evt):
        with open('test.dff', 'wb') as f:
            self.geolists[0].save(f, self.chk.ver)
            writepack(f, "II", self.chk.getRefInt(), 0)

class MoreSpecificInfoView(wx.TextCtrl):
    def __init__(self, chk, *args, **kw):
        super().__init__(style=wx.TE_MULTILINE|wx.TE_DONTWRAP|wx.TE_READONLY,*args,**kw)
        txt = io.StringIO()
        def tcprint(*args):
            print(*args, file=txt)
        if type(chk) == KChunk:
            dattype = (chk.kcl.cltype,chk.kcl.clid)
            def objrefstr(objref):
                if type(objref) == tuple:
                    return getclname(objref[0], objref[1]) + ', ' + str(objref[2])
                else:
                    return str(objref)
            if dattype == (12,18) or dattype == (12,19): # CGround or CDynamicGround
                txt.write("CGround!\n\n")
                bi = io.BytesIO(chk.data)
                # numa,num_tris,num_verts = readpack(bi, "IHH")
                # tcprint('numa =', numa)
                # tcprint('num_tris =', num_tris)
                # tcprint('num_verts =', num_verts)
                # # tcprint('Indices:')
                # # for i in range(num_tris):
                # #     tcprint(readpack(bi, "HHH"))
                # # tcprint('Vertices:')
                # # for i in range(num_verts):
                # #     tcprint(readpack(bi, "fff"))
                # bi.seek(6*num_tris + 12*num_verts, os.SEEK_CUR)
                # tcprint('Misc:')
                # tcprint('off', hex(bi.tell()))
                # tcprint(readpack(bi, "6f"))
                # tcprint('off', hex(bi.tell()))
                # tcprint(readpack(bi, "HH"))
                # if chk.ver >= 2:
                #     tcprint('Neo byte:', readpack(bi, "B"))
                #     if chk.ver >= 3:
                #         tcprint('Invalid ref? :', readobjref(bi))
                #     tcprint('Sector :', readobjref(bi))
                # numy, = readpack(bi, "H")
                # tcprint('Infinite walls:', numy)
                # for i in range(numy):
                #     tcprint(readpack(bi, "HH"))
                # numz, = readpack(bi, "H")
                # tcprint('Finite walls:', numz)
                # for i in range(numz):
                #     tcprint(readpack(bi, "HHff"))
                # tcprint(readpack(bi, "ff"))
                # tcprint('off', hex(bi.tell()))
                gr = Ground(bi, chk.ver)
                for i in gr.__dict__.items():
                    tcprint(i[0], ':', i[1])
                
            elif dattype == (13,3): # CCloneManager
                tcprint("clones")
                objfile = open('clones.obj', 'w')
                try:
                    bi = io.BytesIO(chk.data)
                    if chk.ver < 2:
                        nthings,n1,n2,n3,n4 = readpack(bi, "5I")
                        for i in range(nthings):
                            tcprint(i, ':', readobjref(bi))
                        #bi.seek(4*nthings, os.SEEK_CUR)
                    else:
                        o1,o2,u1,nthings = readpack(bi, "4i")
                        qt = readpack(bi, "4i")
                        o3, = readpack(bi, "i")
                        bi.seek(4*nthings, os.SEEK_CUR)
                    
                    objbases = (1,1)
                    for team in range(1):
                        tcprint('team', team, 'at', hex(bi.tell()))
                        tmt,tms,tmv = readpack(bi, "3I")
                        assert tmt == 0x22
                        #bi.seek(tms, os.SEEK_CUR)
                        stt,sts,stv = readpack(bi, "3I")
                        assert stt == 1
                        ndings,n5 = readpack(bi, "2I")
                        tcprint(ndings, 'dings:')
                        for i in range(ndings):
                            tcprint(i, ':', readpack(bi, "I"))
                        s = 0
                        ff = 0
                        for i in range(300): #154
                            tcprint('atom', i, 'at', hex(bi.tell()))
                            two, = readpack(bi, "i")
                            tcprint('t:', two, '/ s:', s)
                            if two != -1: #0xffffffff:
                                s += two
                                #att, ats, atv = readpack(bi, "3I")
                                #assert att == 0x14
                                #bi.seek(ats, os.SEEK_CUR)
                                att, ats, atv = readpack(bi, "3I")
                                nxt = bi.tell() + ats
                                bi.seek(-12, os.SEEK_CUR)
                                try:
                                    geo = Geometry(bi)
                                    objfile.write('o Clone_%04i\n' % i)
                                    objbases = geo.exportToOBJ(objfile, *objbases)
                                except Exception as e:
                                    tcprint('Geofail')
                                bi.seek(nxt, os.SEEK_SET)
                            else:
                                ff += 1
                                print('ff:', ff)
                except Exception as e:
                    tcprint('!!! EXCEPTION !!!:', type(e), e)
                objfile.close()
            elif dattype[0] == 11: # Node
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
            elif dattype == (13, 8): #CAnimationManager
                try:
                    bi = io.BytesIO(chk.data)
                    numAnim, = readpack(bi, 'I')
                    tcprint('Num animations:', numAnim)
                    smv = 999999999; sm = -1
                    for i in range(numAnim):
                        rwt,rws,rwv = readpack(bi, '3I')
                        assert rwt == 0x1B
                        if rws < smv:
                            smv = rws
                            sm = i
                        animver, animtype, framecount, flags, duration = readpack(bi, 'IIIIf')
                        tcprint('---- Anim', i, '----')
                        tcprint('Size:', rws)
                        tcprint('Version:', animver)
                        tcprint('Type ID:', animtype)
                        tcprint('Frame count:', framecount)
                        tcprint('Flags:', flags)
                        tcprint('Duration:', duration)
                        for f in range(framecount):
                            tcprint('* Frame', f)
                            tcprint('  A:', *readpack(bi, 'I'))
                            tcprint('  B:', *readpack(bi, '7H'))
                            tcprint('  C:', *readpack(bi, 'I'))
                        tcprint('Bounding box:', readpack(bi, '6f'))
                        tcprint('D:', *readpack(bi, 'I'))
                        tcprint('E:', *readpack(bi, '3I'))
                        #bi.seek(rws+16-20, os.SEEK_CUR)
                    tcprint('Smallest anim:', sm)
                    tcprint('Ended at', hex(bi.tell()))
                except Exception as e:
                    tcprint('!!! EXCEPTION !!!:', type(e), e)
            elif dattype == (12, 73): #CKBeaconKluster
                try:
                    bi = io.BytesIO(chk.data)
                    nextbk, = readpack(bi, 'I')
                    hfloats = readpack(bi, '5f')
                    numBings,numDings = readpack(bi, 'HH')
                    tcprint('Header floats:', hfloats)
                    tcprint('Num Bings:', numBings)
                    tcprint('Num Dings:', numDings)
                    for i in range(numBings):
                        active, = readpack(bi, 'B')
                        tcprint('----- Bing %i %s -----' % (i, 'A' if active else 'I'))
                        if active == 1:
                            pk = readpack(bi, 'IHHHH')
                            ali, h1, h2, h3, h4 = pk
                            tcprint(pk)
                            if ali != 0:
                                ref = readobjref(bi)
                                smth, = readpack(bi, 'I')
                                tcprint(objrefstr(ref))
                                for j in range(ali):
                                    pp = readpack(bi, '3hh')
                                    tcprint(pp)
                                    #tcprint(*(n*0.1 for n in pp))
                except Exception as e:
                    tcprint('!!! EXCEPTION !!!:', type(e), e)

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
        self.versel = wx.RadioBox(self,
            choices=['Asterix XXL 1', 'Asterix XXL 2', 'Arthur Invisibles/Minimoys', 'Asterix Olympic Games'],
            majorDimension=2)
            #, label="Select the game you want to mod/explore:")
        self.versel.SetSelection(kfiles.kver-1)
        bs.AddMany((s1,s2,self.versel))
        bs.Add(wx.StaticText(self, label="For XXL1 PC and XXL2 PC you will also have to setup\nthe path to a patched GameModule.elb file in Tools > Settings."))
        bs.Add(wx.StaticText(self, label="Then open the file by drag-dropping a KWN file in this window."))
        bs.Add(wx.StaticText(self, label="For more help, click Help > Readme."))
        self.SetSizer(bs)
        self.versel.Bind(wx.EVT_RADIOBOX, self.OnRadioBox)
        self.versetters = versetters

    def OnRadioBox(self, evt):
        self.versetters[self.versel.GetSelection()](None)
        
