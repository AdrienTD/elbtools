import io, math, os, struct

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

class Vector3:
    def __init__(self,x=0,y=0,z=0):
        self.x = x
        self.y = y
        self.z = z
    def __repr__(self):
        return 'Vector3(%f, %f, %f)' % (self.x,self.y,self.z)

    def __add__(a, b):
        return Vector3(a.x+b.x, a.y+b.y, a.z+b.z)
    def __sub__(a, b):
        return Vector3(a.x-b.x, a.y-b.y, a.z-b.z)
    def __mul__(a, b):
        return Vector3(b*a.x, b*a.y, b*a.z)
    def __rmul__(a, b):
        return a*b

    def dot(a,b):
        return a.x*b.x + a.y*b.y + a.z*b.z
    def cross(a,b):
        return Vector3(a.y*b.z - a.z*b.y, a.z*b.x - a.x*b.z, a.x*b.y - a.y*b.x)

    def sqlen(a):
        return a.x*a.x + a.y*a.y + a.z*a.z
    def len(a):
        return math.sqrt(a.sqlen())

    def unit(a):
        n = a.len()
        if n != 0: return a * (1/n)
        else: return Vector3(0,0,0)

    def __iter__(a):
        yield a.x
        yield a.y
        yield a.z
