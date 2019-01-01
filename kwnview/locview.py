import os, struct

def readpack(inputfile, fmt):
    return struct.unpack("<" + fmt, inputfile.read(struct.calcsize("<" + fmt)))

fn = "C:\\Apps\\Asterix at the Olympic Games\\00GLOC.KWN"
#fn = "C:\\Apps\\Asterix at the Olympic Games\\LVL000\\00LLOC00.KWN"
fn = "C:\\Users\\Adrien\\Downloads\\virtualboxshare\\Asterix & Obelix XXL\\00GLOC.KWN"
kwn = open(fn, 'rb')

num_chunks, = readpack(kwn, "I")
print('Number of chunks:', num_chunks)

olymp = bool(int(input('Engine version (0=XXL1/2, 1=OG)? ')))

for c in range(num_chunks):
    chk_offset = kwn.tell()
    chk_type, chk_id, chk_next = readpack(kwn, "III")
    print(8*'-', c, 8*'-')
    print('Offset: %08X' % chk_offset)
    print('Type:', chk_type)
    print('ID:  ', chk_id)
    print('Data size:', chk_next - chk_offset - 12)

    if chk_type == 12:
        # Localized text
        num_things, = readpack(kwn, "H")
        for j in range(2):
            for i in range(num_things):
                print(readpack(kwn, "I")[0], end=' ')
            print()
        def enumtext(hasid):
            total_size, = readpack(kwn, "I")
            s = 0
            while s < total_size:
                if hasid:
                    txtid, = readpack(kwn, "I")
                txtlen, = readpack(kwn, "I")
                txt = ''
                for i in range(txtlen):
                    txt += chr(readpack(kwn, "H")[0])
                if not hasid:
                    print(txt)
                else:
                    print(txtid, ':', txt)
                s += txtlen
        if olymp:
            enumtext(False)
            enumtext(True)
        else:
            enumtext(True)
            enumtext(False)

    kwn.seek(chk_next, os.SEEK_SET)

kwn.close()
