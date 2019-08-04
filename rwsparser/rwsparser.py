import struct, sys

def readpack(inputfile, fmt):
    return struct.unpack("<" + fmt, inputfile.read(struct.calcsize("<" + fmt)))

def readAndFigure32(file):
    b = file.read(4)
    i, = struct.unpack("<I", b)
    f, = struct.unpack("<f", b)
    print(i, hex(i), f)

filename = sys.argv[1] if len(sys.argv) >= 2 else 'STRA4.rws'
print(filename)
f = open(filename, 'rb')

actype, acsize, acver = readpack(f, "III") # Audio container header
print('Audio container:', hex(actype), acsize, hex(acver))

ahtype, ahsize, ahver = readpack(f, "III") # Audio header header
print('Audio header:', hex(ahtype), ahsize, hex(ahver))

for i in range(8):
    readAndFigure32(f)

nsegments,nthings,ntracks = readpack(f, "III")
print('nsegments:', nsegments)
print('nthings:', nthings, hex(nthings))
print('ntracks:', ntracks)

for i in range(36//4):
    readAndFigure32(f)

streamname = readpack(f, "16s")
print('Stream name:', streamname)

print('Segment table 1:')
for i in range(nsegments):
    for c in range(8):
        readAndFigure32(f)
    print('---')
print('Segment table 2:')
for i in range(nsegments):
    for c in range(5):
        readAndFigure32(f)
    print('---')
print('Segment names:')
for i in range(nsegments):
    print(*readpack(f, "16s"))
