import io, os, struct, wx
import chkviewers, sceneviewer
from utils import *
from objects import *
import kfiles
from kfiles import *

if os.name == 'nt':
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()

app = wx.App()
#locale = wx.Locale(wx.LANGUAGE_ENGLISH)
frm = wx.Frame(None, title="XXL Editor", size=(960,600))

hexmode = False
def gotonormalview(e):
    global hexmode
    hexmode = False
    changeviewer()
def gotohexview(e):
    global hexmode
    hexmode = True
    changeviewer()

def setkver1(ev): changekver(1); vermenu.Check(101, kfiles.kver)
def setkver2(ev): changekver(2); vermenu.Check(102, kfiles.kver)
def setkver3(ev): changekver(3); vermenu.Check(103, kfiles.kver)
def toggledrm(ev):
    kfiles.khasdrm = not kfiles.khasdrm
    vermenu.Check(109, not kfiles.khasdrm)

#notebook = wx.Notebook(frm)
split1 = wx.SplitterWindow(frm, style=wx.SP_LIVE_UPDATE|wx.SP_3D)
split1.SetMinimumPaneSize(16)
tree = wx.TreeCtrl(split1)
chkpanel = wx.Panel(split1)
cpsiz = wx.BoxSizer(orient=wx.VERTICAL)
btsrow = wx.BoxSizer(orient=wx.HORIZONTAL)
bt1 = wx.RadioButton(chkpanel, label="Normal")
bt1.SetValue(True)
bt2 = wx.RadioButton(chkpanel, label="Hex")
bt1.Bind(wx.EVT_RADIOBUTTON, gotonormalview)
bt2.Bind(wx.EVT_RADIOBUTTON, gotohexview)
btsrow.AddMany((bt1,bt2))
cvw = chkviewers.HomeViewer([setkver1,setkver2,setkver3], chkpanel)
cpsiz.Add(cvw, proportion=1, flag=wx.EXPAND)
cpsiz.Add(btsrow)
cpsiz.Add(wx.StaticLine())
#cvw = wx.StaticText(chkpanel, label=":)")
chkpanel.SetSizerAndFit(cpsiz)
split1.SplitVertically(tree, chkpanel, 200)
#notebook.AddPage(split1, "Chunks")

def save_kfile(kf):
    if not AskForSavingChunk():
        return
    fn = wx.FileSelector("Save %s file" % kf.desc, wildcard="K file (*.kwn;*.kgc;*.kp2)|*.kwn;*.kgc;*.kp2", flags=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    if fn.strip():
        kf.save(fn)

def savelvl(event): save_kfile(lvl)
def saveloc(event): save_kfile(loc)
def savesec(event): save_kfile(sec)

def open_kfile(fn):
    global lvl, sec, loc, gam
    name = os.path.basename(fn).upper()
    if name.find('LVL') != -1:
        lvl = LevelFile(fn, kfiles.kver, hasdrm=kfiles.khasdrm)
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
    fn = wx.FileSelector("Open K file", wildcard="K file (*.kwn;*.kgc;*.kp2)|*.kwn;*.kgc;*.kp2", flags=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
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
                infwalls = []
                finwalls = []
                for i in range(num_tris):
                    tris.append(readpack(bi, "HHH"))
                for i in range(num_verts):
                    verts.append(readpack(bi, "fff"))
                aabb = readpack(bi, "6f")
                ctype,param = readpack(bi, "HH")
                if chk.ver >= 2:
                    bb, = readpack(bi, "B")
                    if chk.ver >= 3: readobjref(bi) # ?
                    readobjref(bi) # Sector
                numinfwall, = readpack(bi, "H")
                for i in range(numinfwall):
                    infwalls.append(readpack(bi, "HH"))
                numfinwall, = readpack(bi, "H")
                for i in range(numfinwall):
                    finwalls.append(readpack(bi, "HHff"))

                for v in verts:
                    obj.write('v %f %f %f\n' % v)
                for t in tris:
                    obj.write('f %i %i %i\n' % (t[0]+base, t[1]+base, t[2]+base))
                base += num_verts
                
                obj.write('o %s%s_Ground_%04i_Walls\n' % (prefix,kk.desc,chk.cid))
                for w in finwalls:
                    for s in range(2):
                        obj.write('v %f %f %f\n' % verts[w[s]])
                        obj.write('v %f %f %f\n' % (verts[w[s]][0], verts[w[s]][1] + w[s+2], verts[w[s]][2]))
                    obj.write('f %i %i %i %i\n' % (base+0, base+1, base+3, base+2))
                    base += 4
    return base

def colobj(event):
    fn = wx.FileSelector("Export collision to OBJ", wildcard="OBJ model file (*.obj)|*.obj", flags=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    if not fn.strip(): return
    obj = open(fn, mode='w')
    base = 1
    for kk in (lvl,sec):
        base = groundsToObj(obj,kk,base)
    obj.close()

def geoobj(event):
    fn = wx.FileSelector("Export all geometries to OBJ", wildcard="OBJ model file (*.obj)|*.obj", flags=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    if not fn.strip(): return
    mtlname = os.path.splitext(fn)[0] + ".mtl"
    matset = set()
    with open(fn, mode='w') as obj:
        obj.write('mtllib %s\n' % os.path.basename(mtlname))
        base,normbase = 1,1
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
                            print('Exporting', chk.cid, ':', geo.valid)
                            if geo.valid:
                                obj.write('o %s_%s_%04i\n' % (kk.desc,getclname(10,gt),chk.cid))
                                base,normbase = geo.exportToOBJ(obj, base, normbase)
                                matset.update((m.name for m in geo.materials))
    with open(mtlname, mode='w') as mtlfile:
        mtlfile.write('newmtl NoTexture\n')
        for matname in matset:
            name = matname.decode(encoding='latin_1')
            mtlfile.write('newmtl %s\nmap_Kd textures/%s\n' % (name, name+'.png'))

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
    dirname = wx.DirSelector(message="Select the destination directory for the extracted textures")
    if not dirname.strip(): return
    #os.makedirs(dirname, exist_ok=True)
    #mtl = open('geom.mtl', 'w')
    #mtl.write('newmtl NoTexture\n')
    for kk in (lvl,sec):
        if kk == None: continue
        if not ((9,2) in kk.kclasses): continue
        tc = kk.kclasses[(9,2)].chunks[0]
        tdt = TextureDictionary(io.BytesIO(tc.data), tc.ver)
        for tex in tdt.textures:
            img = tex.convertToWxImage()
            name = tex.name.decode(encoding='latin_1')
            img.SaveFile(dirname + '/' + name + '.png')
            #mtl.write('newmtl %s\nmap_Kd textures/%s\n' % (name, name+'.png'))
    #mtl.close()

def showscene(ev):
    sceneframe = wx.Frame(None, title="Scene Viewer", size=(960,600))
    sceneviewer.ScenePanel((lvl,sec), sceneframe)
    sceneframe.Show()

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

def findhex(bs):
    for kk in (gam,lvl,sec,loc):
        if kk == None: continue
        print('-----', kk.desc, '-----')
        for kcl in kk.kclasses.values():
            for chk in kcl.chunks:
                f = chk.data.find(bs)
                while f != -1:
                    print('Hex found in %s %i at 0x%X.' % (getclname(kcl.cltype,kcl.clid),chk.cid,f))
                    f = chk.data.find(bs, f+1)

def userfindhex(ev):
    tfu = wx.GetTextFromUser("Write the hex data you want to find:")
    if not tfu:
        return
    if tfu[0] == ':':
        nl = [int(x) for x in tfu[1:].split()]
        assert len(nl) >= 3
        bs = struct.pack('<I', nl[0] | (nl[1] << 6) | (nl[2] << 17))
    else:
        hs = tfu.replace(' ', '')
        assert len(hs) & 1 == 0
        bs = bytes(( int(hs[2*i:2*i+2], base=16) for i in range(len(hs)//2) ))
    findhex(bs)


def showRefViewer(ev):
    rv = wx.Dialog(frm, title="Reference Viewer", size=(960,600))
    siz = wx.BoxSizer(orient=wx.VERTICAL)
    edt = wx.TextCtrl(rv)
    res = wx.StaticText(rv, label="Type the hex value of the reference.")
    siz.AddMany((edt,res))
    rv.SetSizerAndFit(siz)
    def valchange(ev2):
        try:
            i = int(edt.GetValue(), base=16)
            n = (i & 63, (i>>6) & 2047, i >> 17)
            res.SetLabel('%s %s' % (getclname(n[0],n[1]), n))
        except:
            res.SetLabel('Invalid')
    print(edt)
    edt.Bind(wx.EVT_TEXT, valchange)
    rv.Show()

def readmefile(evt):
    if os.name == 'nt':
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(0, "open", "readme.txt", 0, 0, 10)

def aboutapp(evt):
    wx.MessageBox("XXL Editor - Preview 1\nAdrienTD")

menu = wx.Menu()
menu.Append(901, "Open...")
menu.AppendSeparator()
menu.Append(900, "Save LVL")
menu.Append(907, "Save LOC")
menu.Append(908, "Save STR")
chkmenu = wx.Menu()
chkmenu.Append(201, "Update")
toolmenu = wx.Menu()
toolmenu.Append(6, "Scene Viewer")
toolmenu.AppendSeparator()
toolmenu.Append(2, "Export collision to OBJ")
toolmenu.Append(3, "Export all geometries to OBJ")
#toolmenu.Append(4, "Export collision of whole Rome")
toolmenu.Append(5, "Export all textures")
toolmenu.AppendSeparator()
toolmenu.Append(10, "Find hex")
toolmenu.Append(11, "Reference viewer")
#toolmenu.Append(9, "List shadows")
vermenu = wx.Menu()
vermenu.AppendRadioItem(101, "Asterix XXL 1")
vermenu.AppendRadioItem(102, "Asterix XXL 2")
vermenu.AppendRadioItem(103, "Asterix Olympic Games")
vermenu.AppendSeparator()
vermenu.AppendCheckItem(109, "Demo")
helpmenu = wx.Menu()
helpmenu.Append(301, "Readme file")
helpmenu.Append(302, "About...")
menubar = wx.MenuBar()
menubar.Append(menu, "File")
#menubar.Append(chkmenu, "Chunk")
menubar.Append(toolmenu, "Tools")
menubar.Append(vermenu, "Version")
menubar.Append(helpmenu, "Help")
frm.SetMenuBar(menubar)
frm.Bind(wx.EVT_MENU, savelvl, id=900)
frm.Bind(wx.EVT_MENU, openkfcmd, id=901)
frm.Bind(wx.EVT_MENU, colobj, id=2)
frm.Bind(wx.EVT_MENU, geoobj, id=3)
frm.Bind(wx.EVT_MENU, romeobj, id=4)
frm.Bind(wx.EVT_MENU, exporttextures, id=5)
frm.Bind(wx.EVT_MENU, showscene, id=6)
frm.Bind(wx.EVT_MENU, saveloc, id=907)
frm.Bind(wx.EVT_MENU, savesec, id=908)
frm.Bind(wx.EVT_MENU, listshadow, id=9)
frm.Bind(wx.EVT_MENU, userfindhex, id=10)
frm.Bind(wx.EVT_MENU, showRefViewer, id=11)

frm.Bind(wx.EVT_MENU, setkver1, id=101)
frm.Bind(wx.EVT_MENU, setkver2, id=102)
frm.Bind(wx.EVT_MENU, setkver3, id=103)
frm.Bind(wx.EVT_MENU, toggledrm, id=109)

frm.Bind(wx.EVT_MENU, update_chunk, id=201)

frm.Bind(wx.EVT_MENU, readmefile, id=301)
frm.Bind(wx.EVT_MENU, aboutapp, id=302)

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
    troot = tree.AddRoot("Home")
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
                            if type(f) == GameFile:
                                if f.namedicts:
                                    name = f.namedicts[0].get((i,f.kclasses[j].clid,k.cid),'?')
                                    if name == '?' and k.guid:
                                        name = f.namedicts[0].get(k.guid, '?')
                            elif lvl != None:
                                if lvl.namedicts:
                                    name = lvl.namedicts[f.strnum].get((i,f.kclasses[j].clid,k.cid),'?')
                            tree.AppendItem(cti, str(k.cid) + ': ' + name, data=k)
    tree.Expand(troot)

curchk = None

def changeviewer():
    global cvw, curchk
    item = tree.GetSelection()
    td = tree.GetItemData(item)
    oldcvw = cvw
##    if not AskForSavingChunk():
##        return
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
        curchk = td
    elif type(td) == bytes:
        cvw = chkviewers.HexView(td, chkpanel)
        curchk = None
    elif type(td) == KClass:
        cvw = chkviewers.MoreSpecificInfoView(td, chkpanel)
        curchk = None
    else:
        #cvw = wx.StaticText(chkpanel, label=":(")
        cvw = chkviewers.HomeViewer([setkver1,setkver2,setkver3], chkpanel)
        curchk = None
    cpsiz.Replace(oldcvw, cvw)
    oldcvw.Destroy()
    cpsiz.Layout()

def selchunkchanged(event):
    changeviewer()

def selchunkchanging(event):
    if not AskForSavingChunk():
        event.Veto()

def AskForSavingChunk():
    td = curchk
    if 'modified' in cvw.__dict__ and cvw.modified:
        assert type(td) == KChunk
        answ = wx.MessageBox("Do you want to save and keep the changes to the currently selected chunk in memory?", style=wx.YES_NO | wx.CANCEL)
        if answ == wx.YES:
            cvw.update(td)
        elif answ == wx.CANCEL:
            return False
    return True

treemenuitem = None

def treemenu(event):
    global treemenuitem
    treemenuitem = event.GetItem()
    td = tree.GetItemData(treemenuitem)
    m = wx.Menu()
    if type(td) == KChunk:
        m.Append(1000, "Find in references")
        m.Append(1001, "Find in GUID references")
        m.Append(1002, "Find out references")
        m.AppendSeparator()
        m.Append(1003, "Export to file...")
        m.Append(1004, "Import from file...")
    elif isinstance(td, PackFile):
        m.Append(2000, "Close file")
    else:
        m.Append(1099, str(type(td)))
        m.Enable(1099, False)
    tree.PopupMenu(m)

def treefindref(event):
    td = tree.GetItemData(treemenuitem)
    if type(td) != KChunk: return
    bs = struct.pack('<I', td.kcl.cltype | (td.kcl.clid << 6) | (td.cid << 17))
    findhex(bs)

def treefindguid(event):
    td = tree.GetItemData(treemenuitem)
    if type(td) != KChunk: return
    bs = b'\xFD\xFF\xFF\xFF' + td.guid
    findhex(bs)

def getChunkFromGUID(guid):
    kfiles = (gam,)
    #print(gam, kfiles)
    if gam == None:
        return None
    for kk in kfiles:
        for kcl in kk.kclasses.values():
            #print(kcl)
            for chk in kcl.chunks:
                if chk.guid:
                    #print(type(chk.guid),type(guid))
                    assert type(chk.guid) == type(guid)
                    if chk.guid == guid:
                        return chk
    return None

def treefindrefout(event):
    td = tree.GetItemData(treemenuitem)
    print('----', getclname(td.kcl.cltype,td.kcl.clid), td.cid, '----')
    o = 0
    for o in range(len(td.data)-3):
        s = td.data[o:o+4]
        if s == b'\xFD\xFF\xFF\xFF':
            guid = td.data[o+4:o+4+16]
            chk = getChunkFromGUID(guid)
            if chk:
                n = getclname(chk.kcl.cltype,chk.kcl.clid)
                print('0x%08X: Found GUID:' % o, n, chk.cid)
            else:
                print('0x%08X: Found unknown GUID:' % o, guid)
        else:
            i, = struct.unpack('I', s)
            t = (i & 63, (i>>6) & 2047, i >> 17)
            if t[2] >= 2048: continue
            n = getclname(t[0],t[1])
            if n[0] != '<':
                print('0x%08X: Found ref:' % o, n, t)

def treeexportchunk(event):
    td = tree.GetItemData(treemenuitem)
    fn = wx.FileSelector("Export chunk data", flags=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    if not fn.strip(): return
    with open(fn, 'wb') as f:
        f.write(td.data)

def treeimportchunk(event):
    td = tree.GetItemData(treemenuitem)
    fn = wx.FileSelector("Import chunk data", flags=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
    if not fn.strip(): return
    with open(fn, 'rb') as f:
        td.data = f.read()

def treeclosefile(event):
    global gam,lvl,sec,loc
    td = tree.GetItemData(treemenuitem)
    if td == gam: gam = None
    if td == lvl: lvl = None
    if td == sec: sec = None
    if td == loc: loc = None
    updateChunkTree()

tree.Bind(wx.EVT_TREE_SEL_CHANGED, selchunkchanged)
tree.Bind(wx.EVT_TREE_SEL_CHANGING, selchunkchanging)
tree.Bind(wx.EVT_TREE_ITEM_MENU, treemenu)
tree.Bind(wx.EVT_MENU, treefindref, id=1000)
tree.Bind(wx.EVT_MENU, treefindguid, id=1001)
tree.Bind(wx.EVT_MENU, treefindrefout, id=1002)
tree.Bind(wx.EVT_MENU, treeexportchunk, id=1003)
tree.Bind(wx.EVT_MENU, treeimportchunk, id=1004)
tree.Bind(wx.EVT_MENU, treeclosefile, id=2000)

frm.Show()
app.MainLoop()
