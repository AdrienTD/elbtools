import os, struct

def readpack(inputfile, fmt):
    return struct.unpack("<" + fmt, inputfile.read(struct.calcsize("<" + fmt)))

#fn = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\aoxxl2demo\\Astérix & Obélix XXL2 DEMO\\LVL001\\LVL01.KWN"
#fn = "C:\\Apps\\Asterix and Obelix XXL2\\LVL000\\LVL00.KWN"
fn = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\Asterix & Obelix XXL\\LVL006\\LVL06fixed.KWN"
#fn = "D:\\LVL001\\LVL01.KP2"
#fn = "C:\\Users\\Adrien\\Downloads\\ax2hack\\LVL01.KGC"
kwn = open(fn, 'rb')

numz, = readpack(kwn, "I")
chunk_offset, = readpack(kwn, "I")
print('Should end at:', hex(chunk_offset))
fstbyte, = readpack(kwn, "B")
#stn1 = readpack(kwn, "16B")

numa, = readpack(kwn, "I")
print('numa:', numa)
for i in range(15):
    print('---- A', i, '----')
    print('Offset:', hex(kwn.tell()))
    numb, = readpack(kwn, "H")
    print('Num bees:', numb)
    nc = 0
    for j in range(numb):
        h1,h2,b1 = readpack(kwn, "HHB")
        print(j,':', h1,h2,b1)
        if not (h1 == 0 and h2 == 0):
            nc += 1
        #if b1 != 0:
        #    for k in range(h2):
        #        stnk = readpack(kwn, "16B")
    print('Valid bees:', nc)

print('Ended at:', hex(kwn.tell()))
kwn.close()
