import io,math,os,struct,wx
from utils import *

class TextureDictionary:
    def __init__(self):
        pass
    def __init__(self, f, ver, lv=False):
        self.load(f, ver, lv)
    def load(self, f, ver, lv):
        if (not lv) and ver >= 3: fstbyte, = readpack(f, "B")
        num_tex, = readpack(f, "I")
        self.textures = []
        for i in range(num_tex):
            if lv:
                name_len, = readpack(f, "H")
                name = f.read(name_len).rstrip(b'\0')
                if ver >= 3: f.read(2)
                print('ltex:', hex(f.tell()))
            else:
                name = f.read(32).rstrip(b'\0')
            t = Texture(f, lv)
            t.name = name
            self.textures.append(t)
    def save(self, f, ver):
        if ver >= 3: writepack(f, "B", 0)
        writepack(f, "I", len(self.textures))
        for t in self.textures:
            f.write(t.name.ljust(32,b'\0'))
            t.save(f)

class Texture:
    def __init__(self, f=None, lv=False):
        if f != None:
            self.load(f, lv)
    def load(self, f, lv):
        if not lv: self.v = readpack(f, "III")
        #print('v:',self.v)
        rtt, rts, rtv = readpack(f, "III")
        assert rtt == 0x18
        self.rwver = rtv
        stt, sts, stv = readpack(f, "III")
        assert stt == 1 and sts == 16
        self.width,self.height,self.bpp,self.pitch = readpack(f, "IIII")
        #print(self.bpp)
        self.dat = f.read(self.pitch * self.height)
        self.pal = []
        if self.bpp <= 8:
            for pe in range(1<<self.bpp):
                self.pal.append(readpack(f,"BBBB"))
    def save(self, f):
        tsiz = self.pitch*self.height + len(self.pal)*4
        writepack(f, "III", *self.v)
        writepack(f, "III", 0x18, 12+16+tsiz, self.rwver)
        writepack(f, "III", 1, 16, self.rwver)
        writepack(f, "IIII", self.width,self.height,self.bpp,self.pitch)
        f.write(self.dat)
        if self.bpp <= 8:
            for pe in self.pal:
                writepack(f, "BBBB", *pe)
    def convertToWxImage(self):
        d = bytearray(self.width * self.height * 3)
        a = bytearray(self.width * self.height)
        if self.bpp <= 8:
            o = n = 0
            for p in self.dat:
                c = self.pal[p]
                d[o:o+3] = c[0:3]
                o += 3
                a[n] = c[3]
                n += 1
        elif self.bpp == 32:
            o = x = 0
            for p in range(len(self.dat)//4):
                d[o:o+3] = self.dat[x:x+3]
                o += 3
                lll = self.dat[x+3]
                a[p] = lll
                x += 4
        img = wx.Image(self.width,self.height,d)
        img.SetAlpha(a)
        return img
    def loadFromWxImage(self, newimg):
        newdat = newimg.GetData()
        hasalp = newimg.HasAlpha()
        if hasalp:
            newalp = newimg.GetAlpha()
        self.width = newimg.GetWidth()
        self.height = newimg.GetHeight()
        self.bpp = 32
        self.pitch = self.width * 4
        self.pal = []
        self.dat = bytearray(self.pitch*self.height)
        x = y = a = 0
        for i in range(self.width*self.height):
            self.dat[x:x+4] = (*newdat[y:y+3], newalp[a] if hasalp else 255)
            x += 4
            y += 3
            a += 1

def getChunkFrom3IDs(kflist: list, cltype: int, clid: int, chkid: int):
    for kf in kflist:
        if kf == None: continue
        cti = (cltype, clid)
        if cti not in kf.kclasses: continue
        for chk in kf.kclasses[cti].chunks:
            if chk.cid == chkid:
                return chk
    return None

def getChunkFromInt(kflist: list, a: int):
    cltype,clid,chkid = a & 63, (a >> 6) & 2047, a >> 17
    return getChunkFrom3IDs(kflist, cltype, clid, chkid)

class GeometryList:
    def __init__(self, f=None, ver=1, kfiles=()):
        if f:
            self.load(f, ver, kfiles)
    def load(self, f, ver, kfiles):
        self.geos = []
        if ver <= 1:
            self.u1,self.flags = readpack(f, "II")
            self.nextgeo = getChunkFromInt(kfiles, self.u1)
            if self.flags & 0x800:
                return
            num_geos = 1
            if self.flags & 0x2000:
                num_geos, = readpack(f, "I")
            for i in range(num_geos):
                self.geos.append(Geometry(f))
        elif ver >= 2:
            f.seek(12, os.SEEK_CUR)
            self.nextgeo = getChunkFromInt(kfiles, *readpack(f, 'I'))
            f.seek(12 if (ver >= 3) else 8, os.SEEK_CUR)
            hasgeo, = readpack(f, "B")
            if hasgeo:
                self.geos.append(Geometry(f))
            else:
                anotherchk = getChunkFromInt(kfiles, *readpack(f, 'I'))
                anothergl = GeometryList(io.BytesIO(anotherchk.data), ver, kfiles)
                self.geos = anothergl.geos
    def save(self, f, ver):
        if ver <= 1:
            writepack(f, "II", self.u1, self.flags)
            #writepack(f, "i", -1) # No next geometry right now
            for geo in self.geos:
                geo.save(f)

class Geometry:
    class Material:
        pass
    def __init__(self, f=None):
        if f:
            self.load(f)
    def load(self, f):
        def dbg(*args):
            pass #print(*args)
        self.valid = False
        atomt,atoms,atomv = readpack(f, "III")
        dbg('aaa', atomt,atoms,atomv)
        if atomt == 0xE:
            f.seek(atoms, os.SEEK_CUR)
            atomt,atoms,atomv = readpack(f, "III")
        if atomt == 0x14:
            geoend = f.tell() + atoms
            stt, sts, stv = readpack(f, "III")
            assert stt == 1 and sts == 16
            av = readpack(f, "4I")
            gmt, gms, gmv = readpack(f, "III")
        else:
            geoend = f.tell() + atoms
            gmt, gms, gmv = atomt, atoms, atomv
        
        self.rwver = gmv
        assert gmt == 0xF
        stt, sts, stv = readpack(f, "III")
        assert stt == 1
        self.flags,self.num_uvmaps,self.natflags = readpack(f, "HBB")
        self.num_tris,self.num_verts, = readpack(f, "II")
        self.num_morph_targets, = readpack(f, "I")
        dbg('num_morph_targets:', self.num_morph_targets)
        assert self.num_morph_targets == 1

        self.colors = []
        if self.flags & 8:
            for i in range(self.num_verts):
                self.colors.append(readpack(f, "4B"))

        dbg(self.num_uvmaps)
        if self.num_uvmaps == 0:
            if self.flags & 4:
                self.num_uvmaps = 1
            if self.flags & 0x80:
                self.num_uvmaps = 2
        self.texcrd = []
        if self.num_uvmaps > 0:
            for i in range(self.num_verts):
                self.texcrd.append(readpack(f, "ff"))
            f.seek(8*self.num_verts*(self.num_uvmaps-1), os.SEEK_CUR)

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
        self.normals = []
        if self.flags & 0x10:
            for j in range(self.num_verts):
                self.normals.append(readpack(f, "fff"))
        dbg('ml', hex(f.tell()))

##        dbg('num_tris:', self.num_tris)
##        dbg('num_verts:', self.num_verts)
##        dbg('num_morph_targets:', self.num_morph_targets)
##        dbg('colors:', self.colors)
##        dbg('texcrd:', self.texcrd)
##        dbg('tris:', self.tris)
##        dbg('sphere:', self.sphere)
##        dbg('verts:', self.verts)
        
        mlt, mls, mlv = readpack(f, "III")
        dbg(mlt,mls,mlv)
        assert mlt == 8
        stt, sts, stv = readpack(f, "III")
        dbg('sts:', sts)
        assert stt == 1 and sts in (4,8)
        num_mats, = readpack(f, "I")
        dbg(num_mats)
        if num_mats > 0:
            readpack(f, "I")
        self.materials = []
        for i in range(num_mats):
            m = self.Material()
            mat, mas, mav = readpack(f, "III")
            assert mat == 7
            stt, sts, stv = readpack(f, "III")
            assert stt == 1 and sts == 28
            m.u1,m.color,m.u2,m.textured,m.ambient,m.specular,m.diffuse = readpack(f, "IIIIfff")
            dbg('txt:', hex(f.tell()))
            if m.textured:
                txt, txs, txv = readpack(f, "III")
                assert txt == 6
                stt, sts, stv = readpack(f, "III")
                assert stt == 1 and sts == 4
                mfl, = readpack(f, "I")
                m.filter = mfl & 255
                m.uaddress = (mfl >> 8) & 15
                m.vaddress = (mfl >> 12) & 15
                m.flags = mfl >> 16
                nat, nas, nav = readpack(f, "III")
                assert nat == 2
                m.name = f.read(nas).rstrip(b'\0\xDD')
                nat, nas, nav = readpack(f, "III")
                assert nat == 2
                m.maskname = f.read(nas).rstrip(b'\0\xDD')
                dbg(m.name)
            else:
                m.name = b'NoTexture'
            self.materials.append(m)
        
        #f.seek(mls, os.SEEK_CUR)
        f.seek(geoend, os.SEEK_SET)
        dbg('yes')
        self.valid = True

    def save(self, f):
        headstack = []
        def pushhs():
            headstack.append(f.tell())
        def pophs():
            p = headstack.pop()
            o = f.tell()
            f.seek(p-8, os.SEEK_SET)
            writepack(f, "I", o-p)
            f.seek(o, os.SEEK_SET)
        writepack(f, "III", 0x14, 0, self.rwver)
        pushhs()
        writepack(f, "III", 1, 16, self.rwver)
        writepack(f, "4I", 0,0,5,0)
        writepack(f, "III", 0xF, 0, self.rwver)
        pushhs()
        writepack(f, "III", 1, 0, self.rwver)
        pushhs()
        writepack(f, "HBB", self.flags, self.num_uvmaps, self.natflags)
        #writepack(f, "II", self.num_tris, self.num_verts)
        writepack(f, "II", len(self.tris), len(self.verts))
        writepack(f, "I", 1) # Num morph targets
        if self.flags & 8:
            for c in self.colors:
                writepack(f, "4B", *c)
        for u in self.texcrd:
            writepack(f, "ff", *u)
        for t in self.tris:
            writepack(f, "4H", t[0], t[1], t[3], t[2])
        writepack(f, "4f", *self.sphere)
        writepack(f, "II", self.haspos, self.hasnorms)
        for v in self.verts:
            writepack(f, "fff", *v)
        if self.flags & 0x10:
            for n in self.normals:
                writepack(f, "fff", *n)
        pophs()

        writepack(f, "III", 8, 0, self.rwver)
        pushhs()
        writepack(f, "III", 1, 8, self.rwver)
        writepack(f, "I", len(self.materials))
        if len(self.materials) > 0:
            writepack(f, "i", -1) # ??
        for m in self.materials:
            writepack(f, "III", 7, 0, self.rwver)
            pushhs()
            writepack(f, "III", 1, 28, self.rwver)
            writepack(f, "IIIIfff", m.u1,m.color,m.u2,m.textured,m.ambient,m.specular,m.diffuse)
            if m.textured:
                writepack(f, "III", 6, 0, self.rwver)
                pushhs()
                writepack(f, "III", 1, 4, self.rwver)
                mfl = m.filter | (m.uaddress << 8) | (m.vaddress << 12) | (m.flags << 16)
                writepack(f, "I", mfl)
                for nam in (m.name, m.maskname):
                    ln = (len(nam)//4)*4 + 4
                    writepack(f, "III", 2, ln, self.rwver)
                    f.write(nam.ljust(ln, b'\x00'))
                writepack(f, "III", 3, 0, self.rwver)
                pophs()
            writepack(f, "III", 3, 0, self.rwver)
            pophs()

        pophs() #End material list

        writepack(f, "III", 3, 0, self.rwver)
        pophs() #End geometry

        writepack(f, "III", 3, 0, self.rwver)
        pophs() #End atomic

        print(len(headstack))

    def exportToOBJ(self, obj, base=1, normbase=1):
        for v in self.verts:
            obj.write('v %f %f %f\n' % v)
        for u in self.texcrd:
            obj.write('vt %f %f\n' % (u[0], 1-u[1]))
        for n in self.normals:
            obj.write('vn %f %f %f\n' % n)
        curtex = b'NoTexture'
        for t in self.tris:
            tex = self.materials[t[3]].name
            if tex != curtex:
                obj.write('usemtl %s\n' % tex.decode(encoding='latin_1'))
                curtex = tex
            obj.write('f')
            for i in (0,2,1):
                if self.normals:
                    obj.write(' %i/%i/%i' % (t[i]+base, t[i]+base, t[i]+normbase))
                else:
                    obj.write(' %i/%i' % (t[i]+base, t[i]+base))
                assert 0 <= t[i] < self.num_verts
            obj.write('\n')
        base += self.num_verts
        if self.normals:
            normbase += self.num_verts
        return base,normbase

    def exportToDAE(self):
        pass
##        from lxml.builder import E
##        from lxml import etree
##        epverts = []
##        for v in self.verts:
##            epverts.extend(v)
##        xf = E.float_array(' '.join(epverts))
##        print(etree.tostring(xf))

    @staticmethod
    def importFromOBJ(objfn: str) -> 'Geometry':
        class ObjMat:
            def __init__(self, name):
                self.name = name
                #self.texfn = texfn

        objverts = []
        objtcrds = []
        objmats = {}
        objgeos = []
        curgeo = None
        curgeonum = -1
        with open(objfn, 'r') as objfile:
            for ln in objfile:
                words = ln.split()
                #print(words)
                if len(words) <= 0:
                    continue
                if words[0] == 'v':
                    objverts.append( tuple(float(k) for k in words[1:4]) )
                elif words[0] == 'vt':
                    objtcrds.append( (float(words[1]), 1-float(words[2])) )
                elif words[0] == 'mtllib':
                    with open(os.path.dirname(objfn) + '/' + words[1], 'r') as mtlfile:
                        curmat = None
                        for ml in mtlfile:
                            mords = ml.split()
                            if len(mords) <= 0:
                                continue
                            if mords[0] == 'newmtl':
                                curmat = ObjMat(mords[1])
                                objmats[mords[1]] = curmat
                                curmat.texfn = "NO_TEXTURE_PLEASE"
                            elif mords[0] == 'map_Kd':
                                # TODO: Consider white space chars!!!
                                curmat.texfn = os.path.splitext(os.path.basename(mords[-1]))[0]
                            elif mords[0] == 'map_Ka':
                                if curmat.texfn == "NO_TEXTURE_PLEASE":
                                    curmat.texfn = os.path.splitext(os.path.basename(mords[-1]))[0]

                elif words[0] == 'usemtl':
                    curgeo = Geometry()
                    curgeomat = objmats[words[1]]
                    objgeos.append(curgeo)
                    curgeonum += 1

                    curgeo.rwver = 0x1803FFFF
                    curgeo.flags = 0xf
                    curgeo.num_uvmaps = 1
                    curgeo.natflags = 0
                    #geo.num_tris = len(geo.tris)
                    #geo.num_verts = len(geo.verts)
                    curgeo.sphere = (0,0,0,1000000)
                    curgeo.haspos = 1
                    curgeo.hasnorms = 0

                    m = Geometry.Material()
                    m.u1 = 0
                    m.color = 0xFF000000
                    m.u2 = 4
                    m.textured = 1
                    m.ambient = 1.0
                    m.specular = 0.0
                    m.diffuse = 1.0
                    m.filter = 6
                    m.uaddress = 1
                    m.vaddress = 1
                    m.flags = 1
                    m.name = curgeomat.texfn.encode()
                    m.maskname = b""

                    curgeo.materials = [m]

                    curgeo.tris = []
                    curgeo.verts = []
                    curgeo.colors = []
                    curgeo.texcrd = []
                elif words[0] == 'f':
                    k = len(curgeo.verts)
                    for t in words[1:]:
                        c = t.split('/')
                        curgeo.verts.append(objverts[int(c[0])-1])
                        curgeo.texcrd.append(objtcrds[int(c[1])-1])
                        curgeo.colors.append((255, 255, 255, 255))
                    for i in range(len(words)-1-2):
                        curgeo.tris.append((k+0,k+2+i,k+1+i,0))

        return objgeos

    @staticmethod
    def importFromDFF(fn: str) -> 'Geometry':
        with open(fn, 'rb') as dff:
            cltyp, clsiz, clver = readpack(dff, 'III')
            assert cltyp == 0x10
            st, ss, sv = readpack(dff, 'III')
            assert st == 1
            numatoms, numlights, numcams = readpack(dff, 'III')

            frtyp, frsiz, frver = readpack(dff, 'III')
            assert frtyp == 0xE
            dff.seek(frsiz, os.SEEK_CUR)

            gltyp, glsiz, glver = readpack(dff, 'III')
            assert gltyp == 0x1A
            st, ss, sv = readpack(dff, 'III')
            assert st == 1
            numgeos, = readpack(dff, 'I')

            geos = [Geometry(dff) for i in range(numgeos)]

            print('done')
        return geos

class StringTable:
    def __init__(self):
        pass
    def __init__(self, f, ver):
        self.load(f, ver)
    def load_id(self, f):
        # Strings with ID
        self.identifiedStrings = []
        totchars, = readpack(f, "I")
        charsread = 0
        while charsread < totchars:
            sid,slen = readpack(f, "II")
            self.identifiedStrings.append((sid,f.read(2*slen).decode(encoding='utf_16_le')))
            charsread += slen
    def load_noid(self, f):
        # Strings without ID
        self.anonymousStrings = []
        totchars, = readpack(f, "I")
        charsread = 0
        while charsread < totchars:
            slen, = readpack(f, "I")
            self.anonymousStrings.append(f.read(2*slen).decode(encoding='utf_16_le'))
            charsread += slen
    def load(self, f, ver):
        numThings, = readpack(f, "H")
        self.thingTable1 = []
        self.thingTable2 = []
        for i in range(numThings): self.thingTable1.append(readpack(f, "I")[0])
        for i in range(numThings): self.thingTable2.append(readpack(f, "I")[0])
        if ver <= 2:
            self.load_id(f)
            self.load_noid(f)
        else:
            self.load_noid(f)
            self.load_id(f)
    def save_id(self, f):
        # Strings with ID
        totchars = 0
        enc = []
        for s in self.identifiedStrings:
            e = s[1].encode(encoding='utf_16_le')
            enc.append((s[0],e))
            totchars += len(e)//2
        writepack(f, "I", totchars)
        for e in enc:
            writepack(f, "II", e[0], len(e[1])//2)
            f.write(e[1])
    def save_noid(self, f):
        # Strings without ID
        totchars = 0
        enc = []
        for s in self.anonymousStrings:
            e = s.encode(encoding='utf_16_le')
            enc.append(e)
            totchars += len(e)//2
        writepack(f, "I", totchars)
        for e in enc:
            writepack(f, "I", len(e)//2)
            f.write(e)
    def save(self, f, ver):
        numThings = len(self.thingTable1)
        writepack(f, "H", numThings)
        for i in range(numThings): writepack(f, "I", self.thingTable1[i])
        for i in range(numThings): writepack(f, "I", self.thingTable2[i])
        if ver <= 2:
            self.save_id(f)
            self.save_noid(f)
        else:
            self.save_noid(f)
            self.save_id(f)

def readobjref(kwn):
    i, = readpack(kwn, 'I')
    if i == 0xFFFFFFFF:
        return None
    elif i == 0xFFFFFFFD:
        return kwn.read(16)
    else:
        return (i & 63, (i>>6) & 2047, i >> 17)

def writeobjref(kwn, ref):
    if ref == None:
        writepack(kwn, 'I', 0xFFFFFFFF)
    elif type(ref) == bytes:
        writepack(kwn, 'I', 0xFFFFFFFD)
        kwn.write(ref)
    elif type(ref) == tuple:
        writepack(kwn, 'I', ref[0] | (ref[1] << 6) | (ref[2] << 17))

class Ground:
    def __init__(self, f=None, ver=1):
        if f:
            self.load(f, ver)
        else:
            self.tris = []
            self.verts = []
            bs = 1000000
            self.aabb = (bs,bs,bs,-bs,-bs,-bs)
            self.param1 = (0,1)
            self.neobyte = 0
            self.unkref = None
            self.sectorobj = None
            self.infwalls = []
            self.finwalls = []
            self.param2 = (0,0)
    
    def load(self, bi, ver):
        self.numa, num_tris, num_verts = readpack(bi, "IHH")
        self.tris = []
        self.verts = []
        for i in range(num_tris):
            self.tris.append(readpack(bi, "HHH"))
        for i in range(num_verts):
            self.verts.append(readpack(bi, "fff"))
        self.aabb = readpack(bi, "6f")
        self.param1 = readpack(bi, "HH")
        if ver >= 2:
            self.neobyte, = readpack(bi, "B")
            if ver >= 4:
                self.unkref = readobjref(bi)
            self.sectorobj = readobjref(bi)
        num_infwalls, = readpack(bi, "H")
        self.infwalls = []
        for i in range(num_infwalls):
            self.infwalls.append(readpack(bi, "HH"))
        num_finwalls, = readpack(bi, "H")
        self.finwalls = []
        for i in range(num_finwalls):
            self.finwalls.append(readpack(bi, "HHff"))
        self.param2 = readpack(bi, "ff")

    def save(self, bi, ver):
        self.numa = len(self.tris)*6 + len(self.verts)*12 + len(self.infwalls)*4 + len(self.finwalls)*12
        writepack(bi, 'IHH', self.numa, len(self.tris), len(self.verts))
        for t in self.tris:
            writepack(bi, 'HHH', *t)
        for v in self.verts:
            writepack(bi, 'fff', *v)
        writepack(bi, '6f', *self.aabb)
        writepack(bi, 'HH', *self.param1)
        if ver >= 2:
            writepack(bi, "B", self.neobyte)
            if ver >= 4:
                writeobjref(bi, self.unkref)
            writeobjref(bi, self.sectorobj)
        writepack(bi, "H", len(self.infwalls))
        for w in self.infwalls:
            writepack(bi, "HH", *w)
        writepack(bi, "H", len(self.finwalls))
        for w in self.finwalls:
            writepack(bi, "HHff", *w)
        writepack(bi, "ff", *self.param2)
