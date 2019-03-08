import io, os, struct
from utils import *

def fixoffsets(f, l, po=0):
    for i in range(len(l)-1):
        f.seek(l[i]+po, os.SEEK_SET)
        writepack(f, "I", l[i+1])
    f.seek(0, os.SEEK_END)

def readobjref(kwn):
    i, = readpack(kwn, 'I')
    if i == 0xFFFFFFFD:
        return kwn.read(16)
    else:
        return (i & 63, (i>>6) & 2047, i >> 17)

def changekver(newkver):
    global kver, grpord, clname, grpnumcl
    kver = newkver
    if kver >= 2: grpord = [9,0,1,2,3,4,5,6,7,8,10,11,12,13,14]
    else:         grpord = [0,9,1,2,3,4,5,6,7,8,10,11,12,13,14]
    cfilenames = [None, 'classes_ax1.txt', 'classes_ax2demo.txt', 'classes_aog.txt']
    cnfile = open(cfilenames[kver], 'r')
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
    if kver == 1:   grpnumcl = [5, 15, 208, 127, 78, 30, 32, 11, 33, 5, 4, 28, 133, 26, 6]
    elif kver == 2: grpnumcl = [5, 21, 269, 1, 104, 1, 67, 16, 36, 5, 4, 37, 249, 53, 6]
    elif kver == 3: grpnumcl = [6, 28, 268, 1, 102, 1, 364, 16, 37, 5, 4, 37, 517, 151, 6]

changekver(1)
khasdrm = True
grpname = ['Managers', 'Services', 'Hooks', 'Hook Lives', 'Groups', 'Group Lives',
          'Components', 'Cameras', 'Cinematic blocs', 'Dictionaries',
          'Geometry', 'Nodes', 'Game things', 'Graphics things', 'Errors']

def getclname(t, i):
    if (t,i) in clname:
        return clname[(t,i)]
    else:
        return "<%i,%i>" % (t,i)

class KChunk:
    def __init__(self,kcl,cid=0,data=b'',ver=kver):
        self.kcl = kcl
        self.cid = cid
        self.data = data
        self.ver = kver
        self.guid = None
class KClass:
    def __init__(self,cltype,clid,sid=0,rep=0,kf=None):
        self.cltype = cltype
        self.clid = clid
        self.startid = sid
        self.rep = rep
        self.kfile = kf
        
        self.chunks = []
        self.numtotchunks = 0
        self.shadow = []
    def __str__(self):
        #return str((self.cltype, self.clid, self.startid, self.rep, len(self.chunks), self.numtotchunks))
        return str(self.__dict__)

def readque(f):
    return f.read(16)
def writeque(f, q):
    f.write(q)

class PackFile:
    desc = "Unknown K file"
    def __init__(self, fn, ver):
        self.filename = fn
        self.ver = ver
        self.strnum = 0
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
    def __init__(self, fn, ver=kver):
        super().__init__(fn, ver)
        kfile = open(fn, 'rb')
        self.kclasses = {}
        self.namedicts = []
        if kver <= 1:
            nchk,unk = readpack(kfile, "II")
            for i in range(nchk):
                cltype,clid,nxtchk = readpack(kfile, "III")
                assert (cltype,clid) not in self.kclasses
                kcls = KClass(cltype,clid,kf=self)
                kchk = KChunk(kcls,0,ver=ver)
                kchk.data = kfile.read(nxtchk - kfile.tell())
                kcls.chunks.append(kchk)
                self.kclasses[(cltype,clid)] = kcls
        else:
            nchk, = readpack(kfile, "I")
            quad1 = readque(kfile)
            num2, = readpack(kfile, "I")
            cp = 0
            kcllist = []
            while cp < nchk:
                clword,numinst,hasguid = readpack(kfile, "IIB")
                cltype,clid = clword & 63, clword >> 6
                kcls = KClass(cltype,clid,kf=self)
                for i in range(numinst):
                    kchk = KChunk(kcls,i,ver=ver)
                    if hasguid:
                        kchk.guid = readque(kfile)
                    kcls.chunks.append(kchk)
                self.kclasses[(cltype,clid)] = kcls
                kcllist.append(kcls)
                cp += numinst
            for kcls in kcllist:
                for chk in kcls.chunks:
                    nextchk, = readpack(kfile, 'I')
                    chk.data = kfile.read(nextchk - kfile.tell())
            numobj, = readpack(kfile, 'I')
            nd = {}
            self.namedicts.append(nd)
            for o in range(numobj):
                objref = readobjref(kfile)
                ns, = readpack(kfile, 'H')
                name = kfile.read(ns).decode(encoding='latin_1')
                h3,h4 = readpack(kfile, '2H')
                assert h4 == 0
                kfile.seek(28, os.SEEK_CUR)
                if objref in nd:
                    print('Duplicate objref:', objref)
                nd[objref] = name
        kfile.close()

class LocFile(PackFile):
    desc = "Local"
    def __init__(self, fn, ver):
        super().__init__(fn, ver)
        kfile = open(fn, 'rb')
        nchk, = readpack(kfile, "I")
        self.kclasses = {}
        for i in range(nchk):
            cltype,clid,nxtchk = readpack(kfile, "III")
            assert (cltype,clid) not in self.kclasses
            kcls = KClass(cltype,clid,kf=self)
            kchk = KChunk(kcls,0,ver=ver)
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
    def __init__(self, fn, ver=kver, hasdrm=khasdrm):
        super().__init__(fn, ver)
        #logfile = open('lvl_load_dbg.txt', 'w')
        def dbg(*args):
            pass #print(*args, file=logfile, flush=True)
        def dreadpack(f, v):
            dbg('readpack:', v, 'from', hex(f.tell()))
            return readpack(f, v)
        kwnfile = open(fn, 'rb')
        if self.ver <= 1: self.numz, = dreadpack(kwnfile, "I")
        if hasdrm:
            self.obssize, = dreadpack(kwnfile, "I")
        self.fstbyte, = dreadpack(kwnfile, "B")
        if self.ver >= 2: self.que = readque(kwnfile)
        self.numa, = dreadpack(kwnfile, "I")
        self.kclasses = {}
        grplen = []
        for i in range(15):
            numb, = dreadpack(kwnfile, "H")
            print('#', numb)
            grplen.append(numb)
            for j in range(numb):
                kcl = KClass(i,j,kf=self)
                if self.ver >= 2:
                    h1,h2,t1,t2,b1 = dreadpack(kwnfile, "HHHBB")
                    kcl.ques1 = []
                    kcl.ques2 = []
                    for k in range(t1): kcl.ques1.append(readque(kwnfile))
                    if t2 != 0:
                        for k in range(h2): kcl.ques2.append(readque(kwnfile))
                    kcl.numtotchunks = h1
                    kcl.numchunkshere = h2
                    kcl.rep = b1
                    kcl.numquads = t1
                    kcl.qbyte = t2
                else:
                    h1,h2,b1 = dreadpack(kwnfile, "HHB")
                    kcl.numtotchunks = h1
                    kcl.numchunkshere = h2
                    kcl.rep = b1
                    kcl.numquads = 0
                    kcl.qbyte = 0
                    kcl.ques1 = []
                    kcl.ques2 = []
                self.kclasses[(i,j)] = kcl
        dbg('a', hex(kwnfile.tell()))
        if self.ver >= 3: kwnfile.seek(8, os.SEEK_CUR)
        elif self.ver == 2: kwnfile.seek(16 if hasdrm else 8, os.SEEK_CUR)
        else: kwnfile.seek(12 if hasdrm else 8, os.SEEK_CUR)
        dbg('a', hex(kwnfile.tell()))
        for i in range(15):
            d = grpord[i]
            nsubchk,nextchkoff = dreadpack(kwnfile, "HI")
            dbg('d', d, nsubchk, hex(nextchkoff))
            j = nj = 0
            cllist = [self.kclasses[x] for x in self.kclasses if x[0] == d]
            #print('cllist1', cllist)
            cllist = [x for x in cllist if x.numchunkshere or x.numquads]
            #print('cllist', cllist)
            print('nsubchk', nsubchk, ', cllist', len(cllist))
            assert len(cllist) == nsubchk
            for kcl in cllist:
                dbg('b', hex(kwnfile.tell()), str(kcl))
                nextsubchkoff, = dreadpack(kwnfile, "I")
                if self.ver >= 2:
                    if kcl.rep:
                        smth, = dreadpack(kwnfile, "H")
                        kcl.shadow = []
                        kcl.shadoff = []
                        for z in range(smth):
                            nz, = dreadpack(kwnfile, "I")
                            #kwnfile.seek(nz, os.SEEK_SET)
                            kcl.shadoff.append(kwnfile.tell())
                            kcl.shadow.append(kwnfile.read(nz - kwnfile.tell()))
                        startid, = dreadpack(kwnfile, "H")
                    else:
                        startid = 0
                else:
                    if kcl.rep:
                        startid, = dreadpack(kwnfile, "H")
                    else:
                        startid = 0
                kcl.sid = startid
                subsub = kwnfile.tell()
                dbg('s1', hex(subsub))
                cid = startid
                nnn = 0
                while subsub < nextsubchkoff:
                    subsub, = dreadpack(kwnfile, "I")
                    assert subsub <= nextsubchkoff
                    dbg('s2', hex(subsub))
                    kcl.chunks.append(KChunk(kcl,cid,kwnfile.read(subsub - kwnfile.tell()),ver=ver))
                    cid += 1
                    nnn += 1
                dbg(kcl.numchunkshere, nnn)
                assert kcl.numchunkshere == nnn
                kwnfile.seek(nextsubchkoff, os.SEEK_SET)
                nj += 1
            assert nsubchk == nj
            kwnfile.seek(nextchkoff, os.SEEK_SET)
            
        # Read the names of the objects if they are present.
        self.namedicts = []
        if ver >= 2:
            nthead = kwnfile.read(8)
            if len(nthead) == 8:
                ntoff,numstr = struct.unpack('II', nthead)
                for s in range(numstr):
                    numobj, = readpack(kwnfile, 'I')
                    nd = {}
                    self.namedicts.append(nd)
                    for o in range(numobj):
                        objref = readobjref(kwnfile)
                        ns, = readpack(kwnfile, 'H')
                        name = kwnfile.read(ns).decode(encoding='latin_1')
                        h3,h4 = readpack(kwnfile, '2H')
                        assert h4 == 0
                        kwnfile.seek(28, os.SEEK_CUR)
                        if objref in nd:
                            print('Duplicate objref:', objref)
                        nd[objref] = name
##                with open('names.txt', 'w') as dbgout:
##                    dbgout.write(str(self.namedicts))
                
        kwnfile.close()
        #logfile.close()
    def save(self,fn):
        kfile = open(fn, 'wb')
        if self.ver <= 1:
            writepack(kfile, "I", self.numz)
        if self.ver != 2:
            writepack(kfile, "I", self.obssize)
        writepack(kfile, "B", self.fstbyte)
        if self.ver >= 2:
            writeque(kfile, self.que)
        writepack(kfile, "I", self.numa)
        for i in range(15):
            writepack(kfile, "H", grpnumcl[i])
            if kver <= 1:
                for j in range(grpnumcl[i]):
                    if (i,j) in self.kclasses:
                        kc = self.kclasses[(i,j)]
                        writepack(kfile, "HHB", kc.numtotchunks, len(kc.chunks), kc.rep)
                    else:
                        writepack(kfile, "HHB", 0,0,0)
            elif kver >= 2:
                for j in range(grpnumcl[i]):
                    if (i,j) in self.kclasses:
                        kc = self.kclasses[(i,j)]
                        writepack(kfile, "HHHBB", kc.numtotchunks, len(kc.chunks), kc.numquads, kc.qbyte, kc.rep)
                        for q in kc.ques1:
                            writeque(kfile, q)
                        if kc.qbyte != 0:
                            for q in kc.ques2:
                                writeque(kfile, q)
                    else:
                        writepack(kfile, "HHHBB", 0,0,0,0,0)
        if kver < 2: # < 3
            writepack(kfile, "I", 0x7CFA06F6)
        writepack(kfile, "II", 0,0)
        nxtgrps = []
        for i in range(15):
            d = grpord[i]
            ctl = [self.kclasses[x] for x in self.kclasses if x[0] == d]
            ctl = [x for x in ctl if x.numchunkshere or x.numquads]
            print(ctl)
            nxtgrps.append(kfile.tell())
            writepack(kfile, "HI", len(ctl), 0)
            nxtclass = []
            for kc in ctl:
                nxtclass.append(kfile.tell())
                writepack(kfile, "I", 0)
                if kc.rep != 0:
                    if self.ver >= 2:
                        writepack(kfile, "H", len(kc.shadow))
                        nxtshads = []
                        for sh in kc.shadow:
                            nxtshads.append(kfile.tell())
                            writepack(kfile, "I", 0)
                            kfile.write(sh)
                        nxtshads.append(kfile.tell())
                        fixoffsets(kfile, nxtshads, 0)
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
    def __init__(self, fn, ver):
        super().__init__(fn, ver)
        tnpos = fn.find('STR')
        if tnpos != -1:
            self.strnum = int(fn[tnpos+6:tnpos+8]) + 1
            print('strnum:', self.strnum)
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
                kc = KClass(d,idlist[d][j][0],startid,kf=self)
                subsub = kwnfile.tell()
                cid = startid
                while subsub < nextsubchkoff:
                    subsub, = readpack(kwnfile, "I")
                    kc.chunks.append(KChunk(kc,cid,kwnfile.read(subsub - kwnfile.tell()),ver=ver))
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

