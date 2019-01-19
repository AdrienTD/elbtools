import io, os, struct, wx
import chkviewers, sceneviewer
from utils import *

import ctypes
ctypes.windll.user32.SetProcessDPIAware()

def fixoffsets(f, l, po=0):
    for i in range(len(l)-1):
        f.seek(l[i]+po, os.SEEK_SET)
        writepack(f, "I", l[i+1])
    f.seek(0, os.SEEK_END)

def changekver(newkver):
    global kver, grpord, clname, grpnumcl
    kver = newkver
    if kver >= 2: grpord = [9,0,1,2,3,4,5,6,7,8,10,11,12,13,14]
    else:         grpord = [0,9,1,2,3,4,5,6,7,8,10,11,12,13,14]
    cnfile = open('classes_ax2demo.txt' if kver >= 2 else 'classes_ax1.txt')
    cnfile.readline()
    clname = {}
    for l in cnfile:
        s = l.split()
        clname[(int(s[0]),int(s[1]))] = s[2]
    cnfile.close()
    #grpnumcl = [max([x[1] for x in clname if x[0] == n],default=0)+1 for n in range(15)]
    #grpnumcl = [5, 15, 196, 126, 78, 30, 32, 11, 29, 5, 4, 28, 106, 26, 5]
    #grpnumcl = [5, 21, 269, 1, 104, 1, 67, 16, 36, 5, 4, 37, 249, 53, 5]
    #print(grpnumcl)
    grpnumcl = [5, 15, 208, 127, 78, 30, 32, 11, 33, 5, 4, 28, 133, 26, 6]

changekver(1)
grpname = ['Managers', 'Services', 'Hooks', 'Hook Lives', 'Groups', 'Group Lives',
          'Components', 'Cameras', 'Cinematic blocs', 'Dictionaries',
          'Geometry', 'Nodes', '3D things', '2D things', 'Errors']

def getclname(t, i):
    if (t,i) in clname:
        return clname[(t,i)]
    else:
        return "<%i,%i>" % (t,i)

app = wx.App()
locale = wx.Locale(wx.LANGUAGE_ENGLISH)
frm = wx.Frame(None, title="KWN Editor", size=(960,600))

hexmode = True
def gotonormalview(e):
    global hexmode
    hexmode = False
    changeviewer()
def gotohexview(e):
    global hexmode
    hexmode = True
    changeviewer()

notebook = wx.Notebook(frm)
split1 = wx.SplitterWindow(notebook, style=wx.SP_LIVE_UPDATE|wx.SP_3D)
tree = wx.TreeCtrl(split1)
chkpanel = wx.Panel(split1, size=wx.Size(400,300))
cpsiz = wx.BoxSizer(orient=wx.VERTICAL)
btsrow = wx.BoxSizer(orient=wx.HORIZONTAL)
bt1 = wx.RadioButton(chkpanel, label="Normal")
bt2 = wx.RadioButton(chkpanel, label="Hex")
bt1.Bind(wx.EVT_RADIOBUTTON, gotonormalview)
bt2.Bind(wx.EVT_RADIOBUTTON, gotohexview)
btsrow.AddMany((bt1,bt2))
cpsiz.Add(btsrow)
cvw = wx.StaticText(chkpanel, label=":)")
cpsiz.Add(cvw, proportion=1, flag=wx.EXPAND)
chkpanel.SetSizerAndFit(cpsiz)
split1.SplitVertically(tree, chkpanel, 150)
notebook.AddPage(split1, "Chunks")

def savelvl(event): lvl.save('lvl.kwn')
def saveloc(event): loc.save('loc.kwn')
def savesec(event): sec.save('sec.kwn')

def openkf(event):
    global lvl, sec, loc, gam
    fn = wx.FileSelector("Open K file", wildcard="K file (*.kwn;*.kgc;*.kp2)|*.kwn;*.kgc;*.kp2")
    if fn.strip():
        name = os.path.basename(fn).upper()
        print(name)
        if name.find('LVL') != -1:
            lvl = LevelFile(fn)
        elif name.find('STR') != -1:
            sec = SectorFile(fn)
        elif name.find('GAME') != -1:
            gam = GameFile(fn)
        elif name.find('LOC') != -1:
            loc = LocFile(fn)
        else:
            wx.MessageBox("Unknown KWN type.\nThe file must have LVL, STR, GAME, or LOC in his file name so that the editor can identify the type.")
        updateChunkTree()

def groundsToObj(obj,kk,base=1,prefix=''):
    if kk != None:
        l = []
        if (12,18) in kk.kclasses: # CGround
            l.append(kk.kclasses[(12,18)])
        #if (12,19) in kk.kclasses: # CDynamicGround
        #    l.append(kk.kclasses[(12,19)])
        for gkc in l:
            for chk in gkc.chunks:
                obj.write('o %s%s_Ground_%04i\n' % (prefix,kk.desc,chk.cid))
                bi = io.BytesIO(chk.data)
                numa,num_tris,num_verts = readpack(bi, "IHH")
                tris = []
                verts = []
                for i in range(num_tris):
                    tris.append(readpack(bi, "HHH"))
                for i in range(num_verts):
                    verts.append(readpack(bi, "fff"))
                for v in verts:
                    obj.write('v %f %f %f\n' % v)
                for t in tris:
                    obj.write('f %i %i %i\n' % (t[0]+base, t[1]+base, t[2]+base))
                base += num_verts
    return base

def colobj(event):
    obj = open('colli.obj', mode='w')
    base = 1
    for kk in (lvl,sec):
        base = groundsToObj(obj,kk,base)
    obj.close()

def geoobj(event):
    obj = open('geom.obj', mode='w')
    obj.write('mtllib geom.mtl\n')
    base = 1
    normbase = 1
    for kk in (lvl,sec):
        if kk != None:
            for gt in (1,2,3):
                if (10,gt) in kk.kclasses:
                    gkc = kk.kclasses[(10,gt)]
                    print('-- %i --' % gt)
                    for chk in gkc.chunks:
                        geolist = chkviewers.GeometryList(io.BytesIO(chk.data))
                        if len(geolist.geos) == 0:
                            continue
                        geo = geolist.geos[0]
                        print(chk.cid, ':', geo.valid)
                        if geo.valid:
                            obj.write('o %s_%s_%04i\n' % (kk.desc,getclname(10,gt),chk.cid))
                            for v in geo.verts:
                                obj.write('v %f %f %f\n' % v)
                            for u in geo.texcrd:
                                obj.write('vt %f %f\n' % (u[0], 1-u[1]))
                            for n in geo.normals:
                                obj.write('vn %f %f %f\n' % n)
                            curtex = b'NoTexture'
                            for t in geo.tris:
                                tex = geo.materials[t[3]].name
                                if tex != curtex:
                                    if type(tex) == str:
                                        print('what:',tex)
                                    obj.write('usemtl %s\n' % tex.decode(encoding='latin_1'))
                                    curtex = tex
                                obj.write('f')
                                for i in range(3):
                                    if geo.normals:
                                        obj.write(' %i/%i/%i' % (t[i]+base, t[i]+base, t[i]+normbase))
                                    else:
                                        obj.write(' %i/%i' % (t[i]+base, t[i]+base))
                                    assert 0 <= t[i] < geo.num_verts
                                obj.write('\n')
                            assert geo.num_verts == len(geo.verts)
                            assert geo.num_tris == len(geo.tris)
                            base += geo.num_verts
                            if geo.normals:
                                normbase += geo.num_verts
    obj.close()

def romeobj(event):
    obj = open('rome.obj', mode='w')
    base = 1
    xxldir = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\Asterix & Obelix XXL\\LVL006\\"
    kfiles = [LevelFile(xxldir+"LVL06fixed.KWN")]
    for i in range(5):
        kfiles.append(SectorFile(xxldir+("STR06_%02i.KWN"%i)))
    for i in range(len(kfiles)):
        base = groundsToObj(obj,kfiles[i],base,'%02i_'%i)
    obj.close()

def exporttextures(event):
    os.makedirs('textures', exist_ok=True)
    mtl = open('geom.mtl', 'w')
    mtl.write('newmtl NoTexture\n')
    for kk in (lvl,sec):
        if kk == None: continue
        if not ((9,2) in kk.kclasses): continue
        tc = kk.kclasses[(9,2)].chunks[0]
        f = io.BytesIO(tc.data)
        num_tex, = readpack(f, "I")
        for i in range(num_tex):
            tex = chkviewers.Texture(f)
            img = tex.convertToWxImage()
            name = tex.name.decode(encoding='latin_1')
            img.SaveFile('textures/' + name + '.png')
            mtl.write('newmtl %s\nmap_Kd textures/%s\n' % (name, name+'.png'))
    mtl.close()

def showscene(ev):
    sceneframe = wx.Frame(None, title="Scene Viewer", size=(960,600))
    sceneviewer.SceneViewer((lvl,sec), sceneframe)
    sceneframe.Show()

def setkver1(ev): changekver(1)
def setkver2(ev): changekver(2)
def setkver3(ev): changekver(3)

def update_chunk(ev):
    item = tree.GetSelection()
    td = tree.GetItemData(item)
    if type(td) != KChunk:
        return
    cvw.update(td)

menu = wx.Menu()
menu.Append(1, "Open...")
menu.Append(0, "Save LVL")
menu.Append(7, "Save LOC")
menu.Append(8, "Save STR")
menu.Append(2, "Create collision OBJ")
menu.Append(3, "Create geometry OBJ")
menu.Append(4, "Export collision of whole Rome")
menu.Append(5, "Export all textures")
menu.Append(6, "Scene Viewer")
chkmenu = wx.Menu()
chkmenu.Append(201, "Update")
vermenu = wx.Menu()
vermenu.AppendRadioItem(101, "Asterix XXL 1")
vermenu.AppendRadioItem(102, "Asterix XXL 2")
vermenu.AppendRadioItem(103, "Asterix Olympic Games")
menubar = wx.MenuBar()
menubar.Append(menu, "File")
menubar.Append(chkmenu, "Chunk")
menubar.Append(vermenu, "Version")
frm.SetMenuBar(menubar)
frm.Bind(wx.EVT_MENU, savelvl, id=0)
frm.Bind(wx.EVT_MENU, openkf, id=1)
frm.Bind(wx.EVT_MENU, colobj, id=2)
frm.Bind(wx.EVT_MENU, geoobj, id=3)
frm.Bind(wx.EVT_MENU, romeobj, id=4)
frm.Bind(wx.EVT_MENU, exporttextures, id=5)
frm.Bind(wx.EVT_MENU, showscene, id=6)
frm.Bind(wx.EVT_MENU, saveloc, id=7)
frm.Bind(wx.EVT_MENU, savesec, id=8)

frm.Bind(wx.EVT_MENU, setkver1, id=101)
frm.Bind(wx.EVT_MENU, setkver2, id=102)
frm.Bind(wx.EVT_MENU, setkver3, id=103)

frm.Bind(wx.EVT_MENU, update_chunk, id=201)

class KChunk:
    def __init__(self,kcl,cid=0,data=b''):
        self.kcl = kcl
        self.cid = cid
        self.data = data
class KClass:
    def __init__(self,cltype,clid,sid=0,rep=0):
        self.cltype = cltype
        self.clid = clid
        self.startid = sid
        self.rep = rep
        self.chunks = []
        self.numtotchunks = 0

def readque(f):
    return f.read(16)

class PackFile:
    desc = "Unknown K file"
    def getChunk(self,cltype,clid,chk):
        return None
    def debug(self):
        for clid in self.kclasses:
            print('-->', getclname(*clid))
            cl = self.kclasses[clid]
            print('start id:', cl.startid)
            print('chunks:', [hex(len(chk)) for chk in cl.chunks])

class GameFile(PackFile):
    desc = "Game"
    def __init__(self, fn):
        kfile = open(fn, 'rb')
        nchk,unk = readpack(kfile, "II")
        self.kclasses = {}
        for i in range(nchk):
            cltype,clid,nxtchk = readpack(kfile, "III")
            assert (cltype,clid) not in self.kclasses
            kcls = KClass(cltype,clid)
            kchk = KChunk(kcls,0)
            kchk.data = kfile.read(nxtchk - kfile.tell())
            kcls.chunks.append(kchk)
            self.kclasses[(cltype,clid)] = kcls
        kfile.close()

class LocFile(PackFile):
    desc = "Local"
    def __init__(self, fn):
        kfile = open(fn, 'rb')
        nchk, = readpack(kfile, "I")
        self.kclasses = {}
        for i in range(nchk):
            cltype,clid,nxtchk = readpack(kfile, "III")
            assert (cltype,clid) not in self.kclasses
            kcls = KClass(cltype,clid)
            kchk = KChunk(kcls,0)
            kchk.data = kfile.read(nxtchk - kfile.tell())
            kcls.chunks.append(kchk)
            self.kclasses[(cltype,clid)] = kcls
        kfile.close()
    def save(self,fn):
        kfile = open(fn, 'wb')
        writepack(kfile, "I", len(self.kclasses))
        chkoffs = []
        for i in self.kclasses:
            kcl = self.kclasses[i]
            if len(kcl.chunks) == 0: continue
            chkoffs.append(kfile.tell())
            writepack(kfile, "III", kcl.cltype, kcl.clid, 0)
            kfile.write(kcl.chunks[0].data)
        chkoffs.append(kfile.tell())
        fixoffsets(kfile, chkoffs, 8)
        kfile.close()

class LevelFile(PackFile):
    desc = "Level"
    def __init__(self, fn):
        logfile = open('lvl_load_dbg.txt', 'w')
        def dbg(*args):
            print(*args, file=logfile, flush=True)
        def dreadpack(f, v):
            dbg('readpack:', v, 'from', hex(f.tell()))
            return readpack(f, v)
        kwnfile = open(fn, 'rb')
        if kver <= 1: self.numz, = dreadpack(kwnfile, "I")
        if True:
            self.obssize, = dreadpack(kwnfile, "I")
        self.fstbyte, = dreadpack(kwnfile, "B")
        if kver >= 2: self.que = readque(kwnfile)
        self.numa, = dreadpack(kwnfile, "I")
        self.kclasses = {}
        idlist = []
        for i in range(15):
            numb, = dreadpack(kwnfile, "H")
            l = []
            for j in range(numb):
                if kver >= 2:
                    h1,h2,t1,t2,b1 = dreadpack(kwnfile, "HHHBB")                    
                    for k in range(t1): stnk = readque(kwnfile)
                    if t2 != 0:
                        for k in range(h2): stnk = readque(kwnfile)
                    if not (h1 == 0 and h2 == 0 and t1 == 0):
                        l.append((j,h2,b1,h1,t1,t2))
                else:
                    h1,h2,b1 = dreadpack(kwnfile, "HHB")
                    if not (h1 == 0 and h2 == 0):
                        l.append((j,h2,b1,h1))
            idlist.append(l)
        #dbg(idlist)
        for i in range(len(idlist)):
            dbg(i, ':', idlist[i])
        dbg('a', hex(kwnfile.tell()))
        if kver >= 2: kwnfile.seek(4, os.SEEK_CUR)
        kwnfile.seek(12 if True else 8, os.SEEK_CUR)
        #kwnfile.seek(8, os.SEEK_CUR)
        dbg('a', hex(kwnfile.tell()))
        for i in range(15):
            d = grpord[i]
            dbg('d', d)
            nsubchk,nextchkoff = dreadpack(kwnfile, "HI")
            dbg(nsubchk,nextchkoff)
            dbg('sc:', nsubchk, len(idlist[d]))
            #assert nsubchk == len(idlist[d])
            #for j in range(nsubchk):
            j = nj = 0
            for j in range(len(idlist[d])):
                dbg('j', j)
                dbg(idlist[d][j])
                dbg('b', hex(kwnfile.tell()))
                if idlist[d][j][1] == 0:
                    continue
                nextsubchkoff, = dreadpack(kwnfile, "I")
                if kver >= 2:
                    if idlist[d][j][2]:
                        smth, = dreadpack(kwnfile, "H")
                        for z in range(smth):
                            nz, = dreadpack(kwnfile, "I")
                            kwnfile.seek(nz, os.SEEK_SET)
                        startid, = dreadpack(kwnfile, "H")
                    else:
                        startid = 0
                    if idlist[d][j][5]:
                        dreadpack(kwnfile, "H")
                else:
                    if idlist[d][j][2]:
                        startid, = dreadpack(kwnfile, "H")
                    else:
                        startid = 0
                kc = KClass(d,idlist[d][j][0],sid=startid,rep=idlist[d][j][2])
                kc.numtotchunks = idlist[d][j][3]
                subsub = kwnfile.tell()
                dbg('s1', hex(subsub))
                cid = startid
                nnn = 0
                while subsub < nextsubchkoff:
                #for o in range(idlist[d][j][1]):
                    subsub, = dreadpack(kwnfile, "I")
                    assert subsub <= nextsubchkoff
                    dbg('s2', hex(subsub))
                    kc.chunks.append(KChunk(kc,cid,kwnfile.read(subsub - kwnfile.tell())))
                    cid += 1
                    nnn += 1
                dbg(idlist[d][j], idlist[d][j][1], nnn)
                assert idlist[d][j][1] == nnn
                kwnfile.seek(nextsubchkoff, os.SEEK_SET)
                self.kclasses[(d,idlist[d][j][0])] = kc
                nj += 1
            assert nsubchk == nj
            kwnfile.seek(nextchkoff, os.SEEK_SET)
        kwnfile.close()
        logfile.close()
    def save(self,fn):
        kfile = open(fn, 'wb')
        writepack(kfile, "I", self.numz)
        if True:
            writepack(kfile, "I", self.obssize)
        writepack(kfile, "BI", self.fstbyte, self.numa)
        for i in range(15):
            writepack(kfile, "H", grpnumcl[i])
            for j in range(grpnumcl[i]):
                if (i,j) in self.kclasses:
                    kc = self.kclasses[(i,j)]
                    writepack(kfile, "HHB", kc.numtotchunks, len(kc.chunks), kc.rep)
                else:
                    writepack(kfile, "HHB", 0,0,0)
        writepack(kfile, "I", 0x7CFA06F6)
        writepack(kfile, "II", 0,0)
        nxtgrps = []
        for i in range(15):
            d = grpord[i]
            ctl = [x[1] for x in self.kclasses if x[0] == d]
            print(ctl)
            nxtgrps.append(kfile.tell())
            writepack(kfile, "HI", len(ctl), 0)
            nxtclass = []
            for j in ctl:
                nxtclass.append(kfile.tell())
                writepack(kfile, "I", 0)
                kc = self.kclasses[(d,j)]
                if kc.rep != 0:
                    writepack(kfile, "H", kc.startid)
                nxtchk = []
                for chk in kc.chunks:
                    nxtchk.append(kfile.tell())
                    writepack(kfile, "I", 0)
                    kfile.write(chk.data)
                nxtchk.append(kfile.tell())
                fixoffsets(kfile, nxtchk, 0)
                
            nxtclass.append(kfile.tell())
            fixoffsets(kfile, nxtclass, 0)
        nxtgrps.append(kfile.tell())
        fixoffsets(kfile, nxtgrps, 2)
        kfile.close()

class SectorFile(PackFile):
    desc = "Sector"
    def __init__(self, fn):
        kwnfile = open(fn, 'rb')
        self.kclasses = {}
        idlist = []
        for i in range(15):
            numb, = readpack(kwnfile, "H")
            print(numb)
            l = []
            for j in range(numb):
                h, = readpack(kwnfile, "H")
                if h != 0:
                    l.append((j,h,1))
            idlist.append(l)
        for i in range(15):
            d = grpord[i]
            nsubchk,nextchkoff = readpack(kwnfile, "HI")
            print(nsubchk,nextchkoff)
            for j in range(nsubchk):
                nextsubchkoff, = readpack(kwnfile, "I")
                startid, = readpack(kwnfile, "H")
                kc = KClass(d,idlist[d][j][0],startid)
                subsub = kwnfile.tell()
                cid = startid
                while subsub < nextsubchkoff:
                    subsub, = readpack(kwnfile, "I")
                    kc.chunks.append(KChunk(kc,cid,kwnfile.read(subsub - kwnfile.tell())))
                    cid += 1
                kwnfile.seek(nextsubchkoff, os.SEEK_SET)
                self.kclasses[(d,idlist[d][j][0])] = kc
            kwnfile.seek(nextchkoff, os.SEEK_SET)
        kwnfile.close()
    def save(self, fn):
        kfile = open(fn, 'wb')
        for i in range(15):
            writepack(kfile, "H", grpnumcl[i])
            for j in range(grpnumcl[i]):
                if (i,j) in self.kclasses:
                    writepack(kfile, "H", len(self.kclasses[(i,j)].chunks))
                else:
                    writepack(kfile, "H", 0)
        goffs = []
        for i in range(15):
            d = grpord[i]
            cls = [self.kclasses[x] for x in self.kclasses if x[0] == d]
            goffs.append(kfile.tell())
            writepack(kfile, "HI", len(cls), 0)
            cloffs = []
            for kcl in cls:
                cloffs.append(kfile.tell())
                writepack(kfile, "IH", 0, kcl.startid)
                chkoffs = []
                for chk in kcl.chunks:
                    chkoffs.append(kfile.tell())
                    writepack(kfile, "I", 0)
                    kfile.write(chk.data)
                chkoffs.append(kfile.tell())
                fixoffsets(kfile, chkoffs, 0)
            cloffs.append(kfile.tell())
            fixoffsets(kfile, cloffs, 0)
        goffs.append(kfile.tell())
        fixoffsets(kfile, goffs, 2)
        kfile.close()

xxl1dir = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\Asterix & Obelix XXL\\"

#sec = SectorFile(xxl1dir + "LVL006\\STR06_03.KWN")
#lvl = LevelFile(xxl1dir + "LVL000\\LVL00.KWN")
#loc = LocFile(xxl1dir + "00GLOC.KWN")

lvl = sec = loc = gam = None

def updateChunkTree():
    tree.DeleteAllItems()
    troot = tree.AddRoot("World")
    for f in (gam,lvl,sec,loc):
        if f != None:
            fto = tree.AppendItem(troot, f.desc, data=f)
            for i in range(15):
                gti = tree.AppendItem(fto, "%s" % (grpname[i]), data=None)
                for j in [x for x in f.kclasses if x[0]==i ]:
                    cti = tree.AppendItem(gti, getclname(*j), data=f.kclasses[j])
                    for k in f.kclasses[j].chunks:
                        kti = tree.AppendItem(cti, str(k.cid), data=k)

def changeviewer():
    global cvw
    item = tree.GetSelection()
    td = tree.GetItemData(item)
    oldcvw = cvw
    if type(td) == KChunk:
        if hexmode:
            cvw = chkviewers.HexView(td, chkpanel)
        else:
            dattype = (td.kcl.cltype,td.kcl.clid)
            dtname = getclname(*dattype)
            if dattype == (9,2):
                cvw = chkviewers.TexDictView(td, chkpanel)
            elif dattype[0] == 10:
                cvw = chkviewers.GeometryView(td, [lvl,sec,loc], chkpanel)
            elif dtname == "CGround" or dtname == "CDynamicGround":
                cvw = chkviewers.MoreSpecificInfoView(td, chkpanel)
            elif dtname == "CLocManager":
                cvw = chkviewers.LocTextViewer(td, chkpanel)
            else:
                cvw = chkviewers.UnknownView(td, chkpanel)
    else:
        cvw = wx.StaticText(chkpanel, label=":(")
    cpsiz.Replace(oldcvw, cvw)
    oldcvw.Destroy()
    cpsiz.Layout()

def selchunkchanged(event):
    changeviewer()

tree.Bind(wx.EVT_TREE_SEL_CHANGED, selchunkchanged)

frm.Show()
app.MainLoop()
