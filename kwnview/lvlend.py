import os, struct

def readpack(inputfile, fmt):
    return struct.unpack("<" + fmt, inputfile.read(struct.calcsize("<" + fmt)))

fn = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\aoxxl2demo\\Astérix & Obélix XXL2 DEMO\\LVL001\\LVL01.KWN"
#fn = "C:\\Apps\\Asterix and Obelix XXL2\\LVL000\\LVL00.KWN"
kwn = open(fn, 'rb')

def readobjref(kwn):
    i, = readpack(kwn, 'I')
    if i == 0xFFFFFFFD:
        return kwn.read(16)
    else:
        return (i & 63, (i>>6) & 2047, i >> 17)

kwn.seek(0xF0F06C, os.SEEK_SET)
ngrp, = readpack(kwn, 'I')
for g in range(ngrp):
    np, = readpack(kwn, 'I')
    i = 0
    while i < np:
        o = kwn.tell()
##        h0,h1,ns = readpack(kwn, '3H')
##        if h0 >= 65533:
##            print('(',h0,h1,ns,')')
##            kwn.seek(10, os.SEEK_CUR)
##            continue
        objref = readobjref(kwn)
        ns, = readpack(kwn, 'H')
        name = kwn.read(ns).decode(encoding='latin_1')
        #print(h0,h1,ns)
        h3,h4 = readpack(kwn, '2H')
        print(i,hex(o),':',objref,ns,h3,h4,'/',name)
        assert h4 == 0
        kwn.seek(28, os.SEEK_CUR)
        i += 1
