import io, os, struct, wx
import chkviewers

def readpack(inputfile, fmt):
    return struct.unpack("<" + fmt, inputfile.read(struct.calcsize("<" + fmt)))

def writepack(outputfile, a, *b):
	outputfile.write(struct.pack("<" + a, *b))

def hexline(f, data, o):
    f.write("%08X " % o)
    for i in range(16):
        if i < len(data):
            f.write("%02X " % data[i])
        else:
            f.write("   ")
    for i in range(16):
        if i < len(data):
            if 0x20 <= data[i] <= 0x7E:
                f.write(chr(data[i]))
            else:
                f.write(".")
    f.write("\n")

def hexdump(f, data, begoff=0):
    siz = len(data)
    lines = (siz // 16) + (1 if (siz & 15) else 0)
    for i in range(siz // 16):
        hexline(f, data[i*16:i*16+16], i*16 + begoff)
    if siz & 15:
        hexline(f, data[(siz//16)*16:siz], (siz//16)*16 + begoff)

def fixoffsets(f, l, po=0):
    for i in range(len(l)-1):
        f.seek(l[i]+po, os.SEEK_SET)
        writepack(f, "I", l[i+1])
    f.seek(0, os.SEEK_END)

kver = 1
if kver >= 2: grpord = [9,0,1,2,3,4,5,6,7,8,10,11,12,13,14]
else:         grpord = [0,9,1,2,3,4,5,6,7,8,10,11,12,13,14]
grpname = ['Managers', 'Services', 'Hooks', 'Hook Lives', 'Groups', 'Group Lives',
          'Components', 'Cameras', 'Cinematic blocs', 'Dictionaries',
          'Geometry', 'Nodes', '3D things', '2D things', 'Errors']
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

def getclname(t, i):
    if (t,i) in clname:
        return clname[(t,i)]
    else:
        return "<%i,%i>" % (t,i)

app = wx.App()
locale = wx.Locale(wx.LANGUAGE_ENGLISH)
frm = wx.Frame(None, title="KWN Editor", size=(960,600))
notebook = wx.Notebook(frm)
split1 = wx.SplitterWindow(notebook, style=wx.SP_LIVE_UPDATE|wx.SP_3D)
tree = wx.TreeCtrl(split1)
cbook = wx.Notebook(split1)
ebox = wx.TextCtrl(cbook, value=":)", style=wx.TE_MULTILINE|wx.TE_DONTWRAP)
cbook.AddPage(ebox, "Hex")
ebox.SetFont(wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
split1.SplitVertically(tree, cbook, 150)
notebook.AddPage(split1, "Chunks")
troot = tree.AddRoot("World")
cvw = None

def savelvl(event):
    lvl.save('test.kwn')

menu = wx.Menu()
menu.Append(0, "Save LVL")
menu.Append(1, "XXX")
menu.Append(2, "XXX")
menu.Append(3, "XXX")
menubar = wx.MenuBar()
menubar.Append(menu, "Tools")
frm.SetMenuBar(menubar)
frm.Bind(wx.EVT_MENU, savelvl, id=0)

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

class PackFile:
    def getChunk(self,cltype,clid,chk):
        return None
    def debug(self):
        for clid in self.kclasses:
            print('-->', getclname(*clid))
            cl = self.kclasses[clid]
            print('start id:', cl.startid)
            print('chunks:', [hex(len(chk)) for chk in cl.chunks])

class GameFile(PackFile):
    pass

class LocFile(PackFile):
    def __init__(self, fn):
        kfile = open(fn, 'rb')
        nchk, = readpack(kfile, "I")
        self.kclasses = {}
        for i in range(nchk):
            cltype,clid,nxtchk = readpack(kfile, "III")
            kcls = KClass(cltype,clid)
            kchk = KChunk(kcls,0)
            kchk.data = kfile.read(nxtchk - kfile.tell())
            kcls.chunks.append(kchk)
            self.kclasses[(cltype,clid)] = kcls
        kfile.close()

class LevelFile(PackFile):
    def __init__(self, fn):
        kwnfile = open(fn, 'rb')
        self.numz, = readpack(kwnfile, "I")
        if True:
            self.obssize, = readpack(kwnfile, "I")
        self.fstbyte, = readpack(kwnfile, "B")
        self.numa, = readpack(kwnfile, "I")
        self.kclasses = {}
        idlist = []
        for i in range(15):
            numb, = readpack(kwnfile, "H")
            l = []
            for j in range(numb):
                h1,h2,b1 = readpack(kwnfile, "HHB")
                if not (h1 == 0 and h2 == 0):
                    l.append((j,h2,b1,h1))
            idlist.append(l)
        kwnfile.seek(12 if True else 8, os.SEEK_CUR)
        print(hex(kwnfile.tell()))
        for i in range(15):
            d = grpord[i]
            nsubchk,nextchkoff = readpack(kwnfile, "HI")
            for j in range(nsubchk):
                nextsubchkoff, = readpack(kwnfile, "I")
                if idlist[d][j][2]:
                    startid, = readpack(kwnfile, "H")
                else:
                    startid = 0
                kc = KClass(d,idlist[d][j][0],sid=startid,rep=idlist[d][j][2])
                kc.numtotchunks = idlist[d][j][3]
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
    def __init__(self, fn):
        kwnfile = open(fn, 'rb')
        self.kclasses = {}
        idlist = []
        for i in range(15):
            numb, = readpack(kwnfile, "H")
            l = []
            for j in range(numb):
                h, = readpack(kwnfile, "H")
                if h != 0:
                    l.append((j,h,1))
            idlist.append(l)
        for i in range(15):
            d = grpord[i]
            nsubchk,nextchkoff = readpack(kwnfile, "HI")
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

xxl1dir = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\Asterix & Obelix XXL\\"

sec = SectorFile(xxl1dir + "LVL006\\STR06_03.KWN")
lvl = LevelFile(xxl1dir + "LVL000\\LVL00.KWN")
loc = LocFile(xxl1dir + "00GLOC.KWN")

for f in (lvl,"Level"),(sec,"Local"):
    fto = tree.AppendItem(troot, f[1], data=f[0])
    for i in range(15):
        gti = tree.AppendItem(fto, "%s" % (grpname[i]), data=None)
        for j in [x for x in f[0].kclasses if x[0]==i ]:
            cti = tree.AppendItem(gti, getclname(*j), data=f[0].kclasses[j])
            for k in f[0].kclasses[j].chunks:
                kti = tree.AppendItem(cti, str(k.cid), data=k)

def selchunkchanged(event):
    global cvw
    item = event.GetItem()
    td = tree.GetItemData(item)
    txt = io.StringIO()
    if cvw:
        cbook.RemovePage(1)
        cvw = None
    if type(td) == KChunk:
        #hexdump(txt, td.data)
        dattype = (td.kcl.cltype,td.kcl.clid)
        if dattype == (9,2):
            cvw = chkviewers.TexDictView(td, cbook)
        elif dattype[0] == 10:
            cvw = chkviewers.GeometryView(td, cbook)
        else:
            cvw = chkviewers.UnknownView(td, cbook)
        cbook.AddPage(cvw, getclname(*dattype))
        #cbook.ChangeSelection(1)
    else:
        txt.write(str(td))
    txt.seek(0, os.SEEK_SET)
    ebox.SetValue(txt.read())

tree.Bind(wx.EVT_TREE_SEL_CHANGED, selchunkchanged)

frm.Show()
app.MainLoop()
