import io, os, struct, wx
import chkviewers, sceneviewer
from utils import *
from objects import *
import kfiles
from kfiles import *

import ctypes
ctypes.windll.user32.SetProcessDPIAware()

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
chkpanel = wx.Panel(split1)
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
split1.SplitVertically(tree, chkpanel, 200)
notebook.AddPage(split1, "Chunks")

def savelvl(event): lvl.save('lvl.kwn')
def saveloc(event): loc.save('loc.kwn')
def savesec(event): sec.save('sec.kwn')

def open_kfile(fn):
    global lvl, sec, loc, gam
    name = os.path.basename(fn).upper()
    if name.find('LVL') != -1:
        lvl = LevelFile(fn, kfiles.kver)
    elif name.find('STR') != -1:
        sec = SectorFile(fn, kfiles.kver)
    elif name.find('GAME') != -1:
        gam = GameFile(fn, kfiles.kver)
    elif name.find('LOC') != -1:
        loc = LocFile(fn, kfiles.kver)
    else:
        wx.MessageBox("Unknown KWN type.\nThe file must have LVL, STR, GAME, or LOC in his file name so that the editor can identify the type.")
    updateChunkTree()

def openkfcmd(event):
    fn = wx.FileSelector("Open K file", wildcard="K file (*.kwn;*.kgc;*.kp2)|*.kwn;*.kgc;*.kp2")
    if fn.strip():
        open_kfile(fn)

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
                        try:
                            geolist = chkviewers.GeometryList(io.BytesIO(chk.data),ver=chk.ver)
                        except:
                            print('Failed to open geometry', chk.cid)
                            continue
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
        tdt = TextureDictionary(io.BytesIO(tc.data), tc.ver)
        for tex in tdt.textures:
            img = tex.convertToWxImage()
            name = tex.name.decode(encoding='latin_1')
            img.SaveFile('textures/' + name + '.png')
            mtl.write('newmtl %s\nmap_Kd textures/%s\n' % (name, name+'.png'))
    mtl.close()

def showscene(ev):
    sceneframe = wx.Frame(None, title="Scene Viewer", size=(960,600))
    sceneviewer.ScenePanel((lvl,sec), sceneframe)
    sceneframe.Show()

def setkver1(ev): changekver(1); kfiles.hasdrm = True
def setkver2(ev): changekver(2); kfiles.hasdrm = True
def setkver3(ev): changekver(3); kfiles.hasdrm = True

def update_chunk(ev):
    item = tree.GetSelection()
    td = tree.GetItemData(item)
    if type(td) != KChunk:
        return
    cvw.update(td)

def listshadow(ev):
    for i in lvl.kclasses:
        kcl = lvl.kclasses[i]
        if kcl.shadow:
            print(getclname(*i), len(kcl.shadow), len(kcl.ques1), len(kcl.ques2), kcl.qbyte)

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
menu.Append(9, "List shadows")
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
frm.Bind(wx.EVT_MENU, openkfcmd, id=1)
frm.Bind(wx.EVT_MENU, colobj, id=2)
frm.Bind(wx.EVT_MENU, geoobj, id=3)
frm.Bind(wx.EVT_MENU, romeobj, id=4)
frm.Bind(wx.EVT_MENU, exporttextures, id=5)
frm.Bind(wx.EVT_MENU, showscene, id=6)
frm.Bind(wx.EVT_MENU, saveloc, id=7)
frm.Bind(wx.EVT_MENU, savesec, id=8)
frm.Bind(wx.EVT_MENU, listshadow, id=9)

frm.Bind(wx.EVT_MENU, setkver1, id=101)
frm.Bind(wx.EVT_MENU, setkver2, id=102)
frm.Bind(wx.EVT_MENU, setkver3, id=103)

frm.Bind(wx.EVT_MENU, update_chunk, id=201)

class KFileDropTarget(wx.FileDropTarget):
    def OnDropFiles(self, x, y, filenames):
        for fn in filenames:
            wx.CallAfter(open_kfile, fn)
        return True

frm.SetDropTarget(KFileDropTarget())

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
                    if f.kclasses[j].chunks or f.kclasses[j].shadow:
                        cti = tree.AppendItem(gti, getclname(*j), data=f.kclasses[j])
                        for k in range(len(f.kclasses[j].shadow)):
                            tree.AppendItem(cti, 'Shadow %i 0x%08X' % (k, f.kclasses[j].shadoff[k]), data=f.kclasses[j].shadow[k])
                        for k in f.kclasses[j].chunks:
                            name = '?'
                            if lvl != None:
                                if lvl.namedicts:
                                    name = lvl.namedicts[f.strnum].get((i,f.kclasses[j].clid,k.cid),'?')
                            tree.AppendItem(cti, str(k.cid) + ': ' + name, data=k)

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
            if dattype in ((9,2), (13,16)):
                cvw = chkviewers.TexDictView(td, chkpanel)
            elif dattype[0] == 10:
                cvw = chkviewers.GeometryView(td, [lvl,sec,loc], chkpanel)
            elif dtname == "CGround" or dtname == "CDynamicGround" or dtname == "CCloneManager" or dattype[0] == 11:
                cvw = chkviewers.MoreSpecificInfoView(td, chkpanel)
            elif dtname == "CLocManager":
                cvw = chkviewers.LocTextViewer(td, chkpanel)
            else:
                cvw = chkviewers.UnknownView(td, chkpanel)
    elif type(td) == bytes:
        cvw = chkviewers.HexView(td, chkpanel)
    elif type(td) == KClass:
        cvw = chkviewers.MoreSpecificInfoView(td, chkpanel)
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
