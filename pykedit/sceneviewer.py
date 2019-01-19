import io,math,os,struct,time,wx,wx.glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *
from utils import *
#import numpy as np

class Ground:
    def __init__(self):
        pass
    def __init__(self, f):
        self.load(f)
    def load(self, bi):
        numa,num_tris,num_verts = readpack(bi, "IHH")
        self.tris = []
        self.verts = []
        for i in range(num_tris):
            self.tris.append(readpack(bi, "HHH"))
        for i in range(num_verts):
            self.verts.append(readpack(bi, "fff"))

class Node:
    def __init__(self):
        pass
    def __init__(self, f):
        self.load(f)
    def load(self, f):
        self.matrix = list(readpack(f, "16f"))
        self.matrix[3] = self.matrix[7] = self.matrix[11] = 0
        self.matrix[15] = 1

class SceneViewer(wx.glcanvas.GLCanvas):
    def __init__(self, kfiles, *args, **kw):
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

        self.campos = (0,0,0)
        self.camdir = (0,0,-1)
        self.camstr = (1,0,0)
        self.camori_y = math.pi
        self.camori_x = 0
        self.dragstart_m = None
        self.dragstart_o = None
        self.wireframe = False
        self.lightdir = (1,1,0)

        self.grounds = []
        for kk in kfiles:
            if kk == None: continue
            if not ((12,18) in kk.kclasses): continue
            for chk in kk.kclasses[(12,18)].chunks:
                self.grounds.append(Ground(io.BytesIO(chk.data)))

        self.nodes = []
        ntl = [(11,3),(11,21),(11,12),(11,22)]
        for kk in kfiles:
            if kk == None: continue
            for cl in ntl:
                if not (cl in kk.kclasses): continue
                for chk in kk.kclasses[cl].chunks:
                    self.nodes.append(Node(io.BytesIO(chk.data)))

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
        self.Refresh()

    def InitGL(self):
        self.glinitialized = True
        
    def OnPaint(self, event):
        c = wx.PaintDC(self)
        if self.IsShown():
            self.SetCurrent(self.context)
            if not self.glinitialized:
                self.InitGL()
            winsize = self.GetClientSize()
            glViewport(0,0,winsize.width,winsize.height)
            glEnable(GL_DEPTH_TEST)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if self.wireframe else GL_FILL)

            glClearColor(1,0,0,1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(60, winsize.width/winsize.height, 0.1, 100)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            center = [self.campos[x] + self.camdir[x] for x in range(3)]
            gluLookAt(*self.campos, *center, 0,1,0)

            cubecolors = [(1,0,1),(0,1,0),(0,0,1),(1,1,1)]
            def drawcube():
                glBegin(GL_TRIANGLE_STRIP)
                for i in (0,1,3,2,0):
                    glColor3f(*cubecolors[i])
                    x = (i & 1) - 0.5
                    z = ((i >> 1) & 1) - 0.5
                    glVertex3f(x, 0.5, z)
                    glVertex3f(x, -0.5, z)
                glEnd()

            drawcube()

            glColor3f(1,1,1)
            glBegin(GL_TRIANGLES)
            for g in self.grounds:
                for t in g.tris:
##                    l = self.lightdir
##                    norm = [v[i]*l[(i+1)%3] - v[(i+1)%3]*l[i] for i in (1,2,0)]
##                    normlen = math.sqrt(sum([x*x for x in norm]))
##                    norm = [x / normlen for x in norm]
##                    dp =
##                    a1 = np.subtract(g.verts[1], g.verts[0])
##                    a2 = np.subtract(g.verts[2], g.verts[0])
##                    norm = np.cross(a1,a2)
##                    norm /= np.linalg.norm(norm)
##                    dp = np.dot(norm, self.lightdir)
##                    dp /= 2
##                    glColor3f(dp, dp, dp)
                    for c in range(3):
                        v = g.verts[t[c]]
                        glVertex3f(*v)
            glEnd()

            for n in self.nodes:
                glPushMatrix()
                glMultMatrixf(n.matrix)
                drawcube()
                glPopMatrix()

            self.SwapBuffers()
