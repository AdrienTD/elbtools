import io, os, struct, wx

def readpack(inputfile, fmt):
    return struct.unpack("<" + fmt, inputfile.read(struct.calcsize("<" + fmt)))

def hexline(f, data, o):
    f.write("%08X " % o)
    for i in range(16):
        if i < len(data):
            f.write("%02X " % data[i])
        else:
            f.write("   ")
    for i in range(16):
        if i < len(data):
            #if data[i:i+1].isalnum():
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


app = wx.App()
frm = wx.Frame(None, title="KWN Viewer", size=(960,600))
notebook = wx.Notebook(frm)
split1 = wx.SplitterWindow(notebook, style=wx.SP_LIVE_UPDATE|wx.SP_3D)
tree = wx.TreeCtrl(split1)
ebox = wx.TextCtrl(split1, value=":)", style=wx.TE_MULTILINE|wx.TE_DONTWRAP)
ebox.SetFont(wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
split1.SplitVertically(tree, ebox, 150)
notebook.AddPage(split1, "Chunks")

kver = 2 # 1:XXL1, 2:XXL2, 3:OG
ktype = 2 # 1:LVL (common sector), 2:STR (sector)

#fn = "C:\\Apps\\Asterix and Obelix XXL2\\LVL001\\LVL01.KWN"
#fn = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\Asterix & Obelix XXL\\LVL000\\LVL00.KWN"
fn = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\aoxxl2demo\\Astérix & Obélix XXL2 DEMO\\LVL001\\LVL01.KWN"
#fn = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\aoxxl2demo\\Astérix & Obélix XXL2 DEMO\\LVL001\\STR01_05.KWN"
ktype = 2 if (os.path.basename(fn).upper().find('STR') != -1) else 1

kwnfile = open(fn, "rb") 

if(kver == 1):
    kwnfile.seek(4, os.SEEK_CUR)
#fto, = readpack(kwnfile, "I")
#fto = 0x32c3 #0x31c3

idlist = []
if ktype == 1:
    fstbyte, = readpack(kwnfile, "B")
    stn1 = readpack(kwnfile, "16B")
    numa, = readpack(kwnfile, "I")
    for i in range(15):
        numb, = readpack(kwnfile, "H")
        nc = 0
        l = []
        for j in range(numb):
            h1,h2,h3,b1,b2 = readpack(kwnfile, "HHHBB")
            if not (h1 == 0 and h2 == 0 and h3 == 0):
                l.append(j)
                nc += 1
            for k in range(h3):
                stnk = readpack(kwnfile, "16B")
            if b1 != 0:
                for k in range(h2):
                    stnk = readpack(kwnfile, "16B")
        idlist.append(l)
    kwnfile.seek(8, os.SEEK_CUR)
elif ktype == 2:
    for i in range(15):
        numb, = readpack(kwnfile, "H")
        nc = 0
        l = []
        for j in range(numb):
            h, = readpack(kwnfile, "H")
            if h != 0:
                l.append(j)
                nc += 1
        idlist.append(l)

print(idlist)

troot = tree.AddRoot("KWN")
grpord = [9,0,1,2,3,4,5,6,7,8,10,11,12,13,14]
grpname = ['Managers', 'Services', 'Hooks', '? 3', 'Groups', '? 5',
          'Components', 'Cameras', 'Cinematic blocs', 'Dictionaries',
          'Geometry', 'Nodes', '3D things', '2D things', 'Errors']

cnfile = open('ax2demo_classes2.txt')
cnfile.readline()
clname = {}
for l in cnfile:
    s = l.split()
    clname[(int(s[0]),int(s[1]))] = s[2]
#print(clname)

for i in range(15):
    d = grpord[i]
    o = kwnfile.tell()
    print("--- Chunk %i @ %08X ---" % (i, o))
    nsubchk,nextchkoff = readpack(kwnfile, "HI")
    print("Num. subchunks: ", nsubchk)
    cti = tree.AppendItem(troot, "%s (%08X)" % (grpname[d],o), data=0)
    for j in range(nsubchk):
        sec = tree.AppendItem(cti, "%s (%08X)" % (clname[(d,idlist[d][j])],kwnfile.tell()), data=1)
        nextsubchkoff, = readpack(kwnfile, "I")
        if ktype == 2:
            readpack(kwnfile, "H")
        subsub, = readpack(kwnfile, "I")
        if subsub != 0:
            kwnfile.seek(-4, os.SEEK_CUR)
        k = 0
        while subsub < nextsubchkoff:
            tree.AppendItem(sec, "%i (%08X)" % (k,kwnfile.tell()), data=1)
            subsub, = readpack(kwnfile, "I")
            assert subsub != 0
            kwnfile.seek(subsub, os.SEEK_SET)
            k += 1
        kwnfile.seek(nextsubchkoff, os.SEEK_SET)
    kwnfile.seek(nextchkoff, os.SEEK_SET)

def WriteChunkInfo(txt):
    chkbegin = kwnfile.tell()
    chkend, = readpack(kwnfile, "I")
    hexdump(txt, kwnfile.read(chkend-chkbegin-4), chkbegin+4)

def selchunkchanged(event):
    item = event.GetItem()
    depth = tree.GetItemData(item)
    if depth == 1:
        sp = tree.GetItemText(item).split()
        #if len(sp) >= 2:
        off = int(sp[1][1:-1], base=16)
        #else:
        #    off = int(sp[0], base=16)
        kwnfile.seek(off, os.SEEK_SET)
        ebox.Clear()
        t = io.StringIO()
        WriteChunkInfo(t)
        t.seek(0, os.SEEK_SET)
        ebox.SetValue(t.read())

tree.Bind(wx.EVT_TREE_SEL_CHANGED, selchunkchanged)

frm.Show()
app.MainLoop()

kwnfile.close()
