import os, struct

def readpack(inputfile, fmt):
    return struct.unpack("<" + fmt, inputfile.read(struct.calcsize("<" + fmt)))

cnfile = open('ax2demo_classes2.txt')
cnfile.readline()
clname = {}
for l in cnfile:
    s = l.split()
    clname[(int(s[0]),int(s[1]))] = s[2]
cnfile.close()

fn = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\aoxxl2demo\\Astérix & Obélix XXL2 DEMO\\GAME.KWN"
kwn = open(fn, 'rb')

num1, = readpack(kwn, "I")
quad1 = readpack(kwn, "16B")
num2, = readpack(kwn, "I")

print('num1:', num1)
print('quad1:', quad1)
print('num2:', num2)

i = 0
cp = 0
while cp < num1:
    c1,c2,c3 = readpack(kwn, "IIB")
    print('------ C', i, '------')
    print('Offset: %u / 0x%X' % (kwn.tell(), kwn.tell()))
    print('cp:', cp)
    print('Head:', c1, c2, c3)
    ctype = c1 & 63
    cid = c1 >> 6
    print('Class:', clname[(ctype,cid)])
    if c3 != 0:
        for j in range(c2):
            q = readpack(kwn, "16B")
    i += 1
    cp += c2

for i in range(num1):
    o = kwn.tell()
    p, = readpack(kwn, "I")
    print("0x%X -> 0x%X" % (o,p))
    kwn.seek(p, os.SEEK_SET)

##num3,num4 = readpack(kwn, "II")
###kwn.seek(0x3223d, os.SEEK_SET)
##while True:
##    o = kwn.tell()
##    ss, = readpack(kwn, "H")
##    assert ss < 256
##    name = kwn.read(ss)
##    print(hex(o), name)
##    print(readpack(kwn, "13i"))
##    #kwn.seek(0x34, os.SEEK_CUR)

np, = readpack(kwn, 'I')
i = 0
while i < np:
    o = kwn.tell()
    h0,h1,ns = readpack(kwn, '3H')
    if h0 >= 65533:
        print('(',h0,h1,ns,')')
        kwn.seek(10, os.SEEK_CUR)
        continue
    name = kwn.read(ns).decode(encoding='latin_1')
    #print(h0,h1,ns)
    h3,h4 = readpack(kwn, '2H')
    print(i,hex(o),':',h0,h1,ns,h3,h4,'/',h0&15,h0>>6,name)
    assert h4 == 0
    kwn.seek(28, os.SEEK_CUR)
    i += 1


kwn.close()
