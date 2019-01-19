import io, os, struct

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

