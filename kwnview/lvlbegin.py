import os, struct

def readpack(inputfile, fmt):
    return struct.unpack("<" + fmt, inputfile.read(struct.calcsize("<" + fmt)))

fn = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\aoxxl2demo\\Astérix & Obélix XXL2 DEMO\\LVL001\\LVL01.KWN"
#fn = "C:\\Apps\\Asterix and Obelix XXL2\\LVL000\\LVL00.KWN"
kwn = open(fn, 'rb')

if False:
    chunk_offset, = readpack(kwn, "I")
    print('Should end at:', hex(chunk_offset))
fstbyte, = readpack(kwn, "B")
stn1 = readpack(kwn, "16B")

numa, = readpack(kwn, "I")
print('numa:', numa)
for i in range(15):
    print('---- A', i, '----')
    print('Offset:', hex(kwn.tell()))
    numb, = readpack(kwn, "H")
    print('Num bees:', numb)
    nc = 0
    for j in range(numb):
        h1,h2,h3,b1,b2 = readpack(kwn, "HHHBB")
        print(j,':', h1,h2,h3,b1,b2)
        #if (h1|h2|h3|b1|b2):
        if not (h1 == 0 and h2 == 0 and h3 == 0):
            nc += 1
        for k in range(h3):
            stnk = readpack(kwn, "16B")
        if b1 != 0:
            for k in range(h2):
                stnk = readpack(kwn, "16B")
    print('Valid bees:', nc)

print('Ended at:', hex(kwn.tell()))
kwn.close()
