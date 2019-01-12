import os, struct

def readpack(inputfile, fmt):
    return struct.unpack("<" + fmt, inputfile.read(struct.calcsize("<" + fmt)))

fn = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\aoxxl2demo\\Astérix & Obélix XXL2 DEMO\\LVL001\\STR01_00.KWN"
#fn = "C:\\Apps\\Asterix and Obelix XXL2\\LVL000\\LVL00.KWN"
#fn = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\Asterix & Obelix XXL\\LVL006\\STR06_02.KWN"
kwn = open(fn, 'rb')

for i in range(15):
    n, = readpack(kwn, "H")
    print('---- Class type', i, '----')
    for j in range(n):
        a, = readpack(kwn, "H")
        print(j,':',a)

print('Ended at', hex(kwn.tell()))

for i in range(15):
    o = kwn.tell()
    num_chunks,next_offset = readpack(kwn, "HI")
    print('---- Class type', i, '----')
    print('Offset:', hex(o))
    print('Num chunks:', num_chunks)
    for c in range(num_chunks):
        next_chunk_offset, = readpack(kwn, "I")
        print('Chunk', c, 'at', hex(kwn.tell()))
        kwn.seek(next_chunk_offset, os.SEEK_SET)
    #kwn.seek(next_offset, os.SEEK_SET)

print('Ended at', hex(kwn.tell()))
kwn.close()
