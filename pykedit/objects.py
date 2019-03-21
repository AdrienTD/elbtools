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

def getChunkFromInt(kflist: list, a: int):
    cltype,clid,chkid = a & 63, (a >> 6) & 2047, a >> 17
    #print('gcfi:', cltype,clid,chkid)
    for kf in kflist:
        if kf == None: continue
        cti = (cltype, clid)
        if cti not in kf.kclasses: continue
        for chk in kf.kclasses[cti].chunks:
            if chk.cid == chkid:
                #print('Found')
                return chk
    return None

class GeometryList:
    def __init__(self):
        pass
    def __init__(self, f, ver=1, kfiles=()):
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

class Geometry:
    class Material:
        pass
    def __init__(self):
        pass
    def __init__(self, f):
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
        assert atomt == 0x14
        geoend = f.tell() + atoms
        stt, sts, stv = readpack(f, "III")
        assert stt == 1 and sts == 16
        av = readpack(f, "4I")
        
        gmt, gms, gmv = readpack(f, "III")
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
        self.texcrd = []
        for i in range(self.num_verts):
            self.texcrd.append(readpack(f, "ff"))
        dbg(self.num_uvmaps)
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
                m.uaddress = (mfl << 8) & 15
                m.vaddress = (mfl << 12) & 15
                nat, nas, nav = readpack(f, "III")
                assert nat == 2
                m.name = f.read(nas).rstrip(b'\0')
                nat, nas, nav = readpack(f, "III")
                assert nat == 2
                m.maskname = f.read(nas).rstrip(b'\0')
                dbg(m.name)
            else:
                m.name = b'NoTexture'
            self.materials.append(m)
        
        #f.seek(mls, os.SEEK_CUR)
        f.seek(geoend, os.SEEK_SET)
        dbg('yes')
        self.valid = True

    def save(self, f):
        writepack(f, "III", 0x14, 0, self.rwver)
        writepack(f, "III", 1, 16, self.rwver)
        writepack(f, "4I", 0,0,0,0)
        writepack(f, "III", 0xF, 0, self.rwver)
        writepack(f, "III", 1, 0, self.rwver)
        writepack(f, "HBB", self.flags, self.num_uvmaps, self.natflags)
        writepack(f, "II", self.num_tris, self.num_verts)
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

        writepack(f, "III", 8, 0, self.rwver)
        writepack(f, "III", 1, 0, self.rwver)
        writepack(f, "I", len(self.materials))
        if len(self.materials) > 0:
            writepack(f, "I", 0) # ??
        for m in self.materials:
            writepack(f, "III", 7, 0, self.rwver)
            writepack(f, "III", 1, 28, self.rwver)
            writepack(f, "IIIIfff", m.u1,m.color,m.u2,m.textured,m.ambient,m.specular,m.diffuse)
            if m.textures:
                writepack(f, "III", 6, 0, self.rwver)
                writepack(f, "III", 1, 4, self.rwver)

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
            for i in range(3):
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
