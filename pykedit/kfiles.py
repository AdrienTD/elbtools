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
    cfilenames = [None, 'classes_ax1.txt', 'classes_ax2.txt', 'classes_aog.txt', 'classes_aog.txt']
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
    elif kver == 4: grpnumcl = [6, 28, 268, 1, 102, 1, 364, 16, 37, 5, 4, 37, 517, 151, 6]

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
    def __init__(self,kcl,cid=0,data=b'',ver=kver,offset=0):
        self.kcl = kcl
        self.cid = cid
        self.data = data
        self.ver = ver
        self.guid = None
        self.offset = offset
    def getRefInt(self):
        return self.kcl.getRefInt() | (self.cid << 17)

class GameStateChunk(KChunk):
    def __init__(self,kcl,cid,data,ver,off):
        super().__init__(self, kcl, cid, data, ver)
        bi = io.BytesIO(data)
        namsiz, = readpack(bi, "H")
        self.name = bi.read(namsiz)
        bi.read(4) #?
        self.gamestruct = readobjref(bi)
        

class KShadow:
    def __init__(self, kwn, siz):
        self.data = kwn.read(siz)
    def save(kwn):
        kwn.write(self.data)
# class DataShadow(KShadow):
#     def __init__(self, data=b''):
#         self.data = data
class GameStateShadow:
    def __init__(self, kwn):
        self.parts = [{}, {}]
        for p in self.parts:
            nump, = readpack(kwn, "I")
            for i in range(nump):
                k = readobjref(kwn)
                end, = readpack(kwn, "I")
                p[k] = kwn.read(end - kwn.tell())
    def save(self, kwn):
        for p in self.parts:
            writepack(kwn, "I", len(p))
            for k in p:
                dat = p[k]
                writeobjref(kwn, k)
                writepack(kwn, "I", kwn.tell() + 4 + len(dat))
                kwn.write(dat)

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
    def getRefInt(self):
        return self.cltype | (self.clid << 6)

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
    def __init__(self, fn, ver=kver, hasdrm=khasdrm, config=None):
        super().__init__(fn, ver)
        #logfile = open('lvl_load_dbg.txt', 'w')
        def dbg(*args):
            pass #print(*args, file=logfile, flush=True)
        def dreadpack(f, v):
            dbg('readpack:', v, 'from', hex(f.tell()))
            return readpack(f, v)
        if os.path.splitext(fn)[1].lower() != '.kwn':
            print('not KWN -> console version -> No DRM')
            hasdrm = False
        self.hasdrm = hasdrm
        bfn = os.path.basename(fn)
        tnpos = bfn.find('LVL')
        if tnpos != -1:
            self.lvlnum = int(bfn[tnpos+3:tnpos+5])
            print('lvlnum:', self.lvlnum)
        kwnfile = open(fn, 'rb')
        self.nodrmformat = False
        if self.ver <= 1:
            self.numz, = dreadpack(kwnfile, "I")
            if self.numz == 0x65747341:
                if dreadpack(kwnfile, "I")[0] == 0x20786972:   # what about case with Aste and something else than rix?
                    hasdrm = False
                    self.nodrmformat = True
                    self.numz, = dreadpack(kwnfile, "I")
        dhfile = kwnfile
        self.encryptedHeader = None
        if hasdrm or ver >= 3:
            self.obssize, = dreadpack(kwnfile, "I")
            self.obsoff = kwnfile.tell()
            # Check if encrypted
            if ver==1 or ver==2:
                resoff = kwnfile.tell()
                kwnfile.seek(5 if (ver==1) else 0x15, os.SEEK_CUR)
                tst, = dreadpack(kwnfile, "I")
                kwnfile.seek(resoff, os.SEEK_SET)
                if tst != 5:
                    print('ENCRYPTED!!!')
                    # try:
                    dhbytes = getDecryptedHeaderFromEXE(config['GameModules']['xxl%i' % ver], self.ver, self.lvlnum)
                    dhfile = io.BytesIO(dhbytes)
                    self.encryptedHeader = kwnfile.read(self.obssize)
                    # except Exception as e:
                    #     wx.MessageBox('Failed to obtain unencrypted header from GameModule.\nReason: %s\nBe sure you set the paths to the patched GameModules correctly in Tools > Settings.' % str(e))

        self.fstbyte, = dreadpack(dhfile, "B")
        if self.ver >= 2: self.que = readque(dhfile)
        self.numa, = dreadpack(dhfile, "I")
        self.kclasses = {}
        grplen = []
        for i in range(15):
            numb, = dreadpack(dhfile, "H")
            print('#', numb)
            grplen.append(numb)
            for j in range(numb):
                kcl = KClass(i,j,kf=self)
                if self.ver >= 2:
                    h1,h2,t1,t2,b1 = dreadpack(dhfile, "HHHBB")
                    kcl.ques1 = []
                    kcl.ques2 = []
                    for k in range(t1): kcl.ques1.append(readque(dhfile))
                    if t2 != 0:
                        for k in range(h2): kcl.ques2.append(readque(dhfile))
                    kcl.numtotchunks = h1
                    kcl.numchunkshere = h2
                    kcl.rep = b1
                    kcl.numquads = t1
                    kcl.qbyte = t2
                else:
                    h1,h2,b1 = dreadpack(dhfile, "HHB")
                    kcl.numtotchunks = h1
                    kcl.numchunkshere = h2
                    kcl.rep = b1
                    kcl.numquads = 0
                    kcl.qbyte = 0
                    kcl.ques1 = []
                    kcl.ques2 = []
                self.kclasses[(i,j)] = kcl
        print('head end', hex(kwnfile.tell()))
        # if self.ver >= 3: kwnfile.seek(8, os.SEEK_CUR)
        # elif self.ver == 2: kwnfile.seek(16 if hasdrm else 8, os.SEEK_CUR)
        # else: kwnfile.seek(12 if hasdrm else 8, os.SEEK_CUR)
        # dbg('a', hex(kwnfile.tell()))
        self.hasdrm = hasdrm
        if hasdrm:
            kwnfile.seek(self.obsoff+self.obssize, os.SEEK_SET)
        kwnfile.seek(4 if (self.ver >= 4) else 8, os.SEEK_CUR)  # self.ver >= 3 or >= 4 ?
        if self.ver == 2 and False: # XXL2 Remaster
            kwnfile.seek(-4, os.SEEK_CUR)
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
                            # if kcl.cltype == 12 and (kcl.clid == 222 or kcl.clid == 341): # CKA?GameState
                            #     shad = GameStateShadow(kwnfile)
                            # else:
                            #     shad = KShadow(kwnfile, nz - kwnfile.tell())
                            shad = kwnfile.read(nz - kwnfile.tell())
                            kcl.shadow.append(shad)
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
                    chkoff = kwnfile.tell()
                    kcl.chunks.append(KChunk(kcl,cid,kwnfile.read(subsub - kwnfile.tell()),ver=ver,offset=chkoff))
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
        if self.nodrmformat:
            kfile.write(b'Asterix ')
        if self.ver <= 1:
            writepack(kfile, "I", self.numz)
        if self.encryptedHeader:
            writepack(kfile, 'I', len(self.encryptedHeader))
            kfile.write(self.encryptedHeader)
        else:
            if self.hasdrm:
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
            if kver <= 2 and self.hasdrm: # < 3
                print('Not well tested case!!!')
                if kver==2: writepack(kfile, "I", 0)
                writepack(kfile, "I", 0)
                #writepack(kfile, "I", 0x7CFA06F6)
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
                        for sh in range(len(kc.shadow)):
                            nxtshads.append(kfile.tell())
                            writepack(kfile, "I", 0)
                            twr = kc.shadow[sh]
                            if kc.cltype == 12 and kc.clid in (222, 341):
                                # Fix/rebase some file offsets inside the CKA*GameState shadows
                                twr = bytes(findAndFixOffsetsInChunk(kc.shadow[sh], kc.shadoff[sh], kfile.tell()))
                            kfile.write(twr)
                        nxtshads.append(kfile.tell())
                        fixoffsets(kfile, nxtshads, 0)
                    writepack(kfile, "H", kc.startid)
                nxtchk = []
                for chk in kc.chunks:
                    nxtchk.append(kfile.tell())
                    writepack(kfile, "I", 0)
                    twr = chk.data
                    if kc.cltype == 12 and kc.clid in (222, 341):
                        # Fix/rebase some file offsets inside the CKA*GameState chunk
                        twr = bytes(findAndFixOffsetsInChunk(chk.data, chk.offset, kfile.tell()))
                    kfile.write(twr)
                nxtchk.append(kfile.tell())
                fixoffsets(kfile, nxtchk, 0)
                
            nxtclass.append(kfile.tell())
            fixoffsets(kfile, nxtclass, 0)
        nxtgrps.append(kfile.tell())
        fixoffsets(kfile, nxtgrps, 2)

        # Name table
        writepack(kfile, "II", 0, 0)

        kfile.close()

class SectorFile(PackFile):
    desc = "Sector"
    def __init__(self, fn, ver):
        super().__init__(fn, ver)
        bfn = os.path.basename(fn)
        tnpos = bfn.find('STR')
        if tnpos != -1:
            self.lvlnum = int(bfn[tnpos+3:tnpos+5])
            print('lvlnum:', self.lvlnum)
            self.strnum = int(bfn[tnpos+6:tnpos+8]) + 1
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

def getDecryptedHeaderFromEXE(exefn: str, ver: int, lvlnb: int) -> bytes:
    if ver == 1:
        hextofind = bytearray.fromhex('05 00 00 00 00 00 00 01 00 01 00 00 01 00 01 00 00 01 00 01 00 00 01 00 01 00 00 0F 00')
        htfoff = 9
        lhstart = 4
        lvllist = (1,2,3,4,5,6,7,8)
    elif ver == 2:
        hextofind = bytearray.fromhex('05 00 00 00 00 00 00 00 00 00 01 00 01 00 00 00 00 00 01 00 01 00 00 00 00 00 01 00 01 00 00 00 00 00 01 00 01 00 00 00 00 00 15 00')
        htfoff = 0x19
        lhstart = 0
        lvllist = (1,2,3,4,6,7,8,9,10,11)

    exefile = open(exefn, 'rb')
    assert exefile, 'Could not open GameModule'
    exebytes = exefile.read()
    exefile.close()

    findoff = 0
    for i in range(1+lvllist.index(lvlnb)):
        fnd = exebytes.find(hextofind, findoff)
        assert fnd != -1, 'Header beginning was not found.'
        findoff = fnd + 1
    headoff = fnd - htfoff
    headsize, = struct.unpack('<I', exebytes[headoff:headoff+4])
    print('Head size:', hex(headsize))
    return exebytes[headoff+4:headoff+headsize+4]

def findAndFixOffsetsInChunk(chkbytes, off: int, newoff: int) -> bytearray:
    lg = len(chkbytes)
    ba = bytearray(chkbytes)
    for i in range(len(ba)-3):
        n, = struct.unpack('I', ba[i:i+4])
        if i+4 <= n - off <= lg:
            ba[i:i+4] = struct.pack('I', n - off + newoff)
    return ba
