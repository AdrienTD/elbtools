import io,math,os,struct,time,wx,wx.glcanvas
from OpenGL.GL import *

def readpack(inputfile, fmt):
    return struct.unpack("<" + fmt, inputfile.read(struct.calcsize("<" + fmt)))

def writepack(outputfile, a, *b):
	outputfile.write(struct.pack("<" + a, *b))

class UnknownView(wx.Panel):
    def __init__(self, chk, *args, **kw):
        super(UnknownView,self).__init__(*args,**kw)
        wx.StaticText(self, label=str(chk))

class TexDictView(wx.Panel):
    class Texture:
        def __init__(self):
            pass
        def __init__(self, f):
            self.load(f)
        def load(self, f):
            self.name = f.read(32)
            self.v = readpack(f, "III")
            print('v:',self.v)
            rtt, rts, rtv = readpack(f, "III")
            assert rtt == 0x18
            self.rwver = rtv
            stt, sts, stv = readpack(f, "III")
            assert stt == 1 and sts == 16
            self.width,self.height,self.bpp,self.pitch = readpack(f, "IIII")
            print(self.bpp)
            self.dat = f.read(self.pitch * self.height)
            self.pal = []
            if self.bpp <= 8:
                for pe in range(1<<self.bpp):
                    self.pal.append(readpack(f,"BBBB"))
        def save(self, f):
            tsiz = self.pitch*self.height + len(self.pal)*4
            f.write(self.name)
            writepack(f, "III", *self.v)
            writepack(f, "III", 0x18, 12+16+tsiz, self.rwver)
            writepack(f, "III", 1, 16, self.rwver)
            writepack(f, "IIII", self.width,self.height,self.bpp,self.pitch)
            f.write(self.dat)
            if self.bpp <= 8:
                for pe in self.pal:
                    writepack(f, "BBBB", *pe)
            
    def __init__(self, chk, *args, **kw):
        super().__init__(*args,**kw)
        self.chk = chk
        self.SetBackgroundColour(wx.Colour(255,0,0))
        self.split1 = split1 = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE|wx.SP_3D)#, size=(700,500))
        self.lb = wx.ListBox(split1)
        tp = wx.Panel(split1)
        split1.SplitVertically(self.lb, tp, 150)
        bs = wx.BoxSizer(orient=wx.VERTICAL)
        cmds = wx.BoxSizer()
        bt = wx.Button(tp, label="Replace texture")
        bt2 = wx.Button(tp, label="Save dictionary")
        cmds.AddMany((bt,bt2))
        self.sb = wx.StaticBitmap(tp)
        bs.AddMany((cmds, self.sb))
        tp.SetSizerAndFit(bs)
        bmp = wx.Bitmap(256,256)
        self.sb.SetBitmap(bmp)
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.lb.Bind(wx.EVT_LISTBOX, self.seltexchanged)
        bt.Bind(wx.EVT_BUTTON, self.replacetex)
        bt2.Bind(wx.EVT_BUTTON, self.savedict)
        
        f = io.BytesIO(chk.data)
        num_tex, = readpack(f, "I")
        self.textures = []
        for i in range(num_tex):
            t = self.Texture(f)
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
        d = bytearray(tex.width * tex.height * 3)
        o = 0
        if tex.bpp <= 8:
            for p in tex.dat:
                c = tex.pal[p]
                #d[o:o+3] = struct.pack("BBB", c[0],c[1],c[2])
                d[o:o+3] = c[0:3]
                o += 3
        elif tex.bpp == 32:
            x = 0
            for p in range(len(tex.dat)//4):
                d[o:o+3] = tex.dat[x:x+3]
                x += 4
                o += 3
        img = wx.Image(tex.width,tex.height,d)
        self.sb.SetBitmap(img.ConvertToBitmap())

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
    class Geometry:
        def __init__(self):
            pass
        def __init__(self, f):
            self.load(f)
        def load(self, f):
            self.valid = False
            self.u1,self.u2 = readpack(f, "II")
            self.atomt,self.atoms,self.atomv = readpack(f, "III")
            if self.atomt != 0x14:
                return
            stt, sts, stv = readpack(f, "III")
            assert stt == 1 and sts == 16
            av = readpack(f, "4I")
            
            gmt, gms, gmv = readpack(f, "III")
            assert gmt == 0xF
            stt, sts, stv = readpack(f, "III")
            assert stt == 1
            self.flags, = readpack(f, "I")
            self.num_tris,self.num_verts, = readpack(f, "II")
            self.num_morph_targets, = readpack(f, "I")
            self.colors = []
            for i in range(self.num_verts):
                self.colors.append(readpack(f, "4B"))
            self.texcrd = []
            for i in range(self.num_verts):
                self.texcrd.append(readpack(f, "ff"))
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

##            print('num_tris:', self.num_tris)
##            print('num_verts:', self.num_verts)
##            print('num_morph_targets:', self.num_morph_targets)
##            print('colors:', self.colors)
##            print('texcrd:', self.texcrd)
##            print('tris:', self.tris)
##            print('sphere:', self.sphere)
##            print('verts:', self.verts)
            
            #mlt, mls, mlv = readpack(f, "III")
            #assert mlt == 8
            #f.seek(mls, os.SEEK_CUR)
            
            print('yes')
            self.valid = True
            
    def __init__(self, chk, *args, **kw):
        super().__init__(*args,**kw)
        self.context = wx.glcanvas.GLContext(self)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        #self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        self.geo = self.Geometry(io.BytesIO(chk.data))
        
    def OnEraseBackground(self, event):
        pass
    def OnPaint(self, event):
        c = wx.PaintDC(self)
        if self.IsShown() and self.geo.valid:
            self.SetCurrent(self.context)
            winsize = self.GetClientSize()
            glViewport(0,0,winsize.width,winsize.height)
            glEnable(GL_DEPTH_TEST)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

            glClearColor(1,0,0,1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glFrustum(-0.5, 0.5, -0.5, 0.5, 1, 5)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glTranslatef(0,0,-3)
            #glRotatef(time.time(),0,1,0)
            glRotatef(time.time() % math.pi,0,1,0)
            
            glBegin(GL_TRIANGLES)
            d = 0
##            glColor3f(1,0,0)
##            glVertex3f(-1,-1,d)
##            glColor3f(0,1,0)
##            glVertex3f(-1,1,d)
##            glColor3f(0,0,1)
##            glVertex3f(1,0,d)
            for t in self.geo.tris:
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

