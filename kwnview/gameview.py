import os, struct

def readpack(inputfile, fmt):
    return struct.unpack("<" + fmt, inputfile.read(struct.calcsize("<" + fmt)))

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

num3,num4 = readpack(kwn, "II")
#kwn.seek(0x3223d, os.SEEK_SET)
while True:
    o = kwn.tell()
    ss, = readpack(kwn, "H")
    assert ss < 256
    name = kwn.read(ss)
    print(hex(o), name)
    print(readpack(kwn, "13i"))
    #kwn.seek(0x34, os.SEEK_CUR)

kwn.close()
