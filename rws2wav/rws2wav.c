// Took http://wiki.xentax.com/index.php/RWS as a reference.

#include <stdio.h>
#include <assert.h>

#define printval(v) printf( #v " = %u\n", v)

typedef unsigned char uchar;
typedef unsigned short ushort;
typedef unsigned int uint;

FILE *file_i, *file_o;
uint headsize, nsegments, ntracks, clustersize, clusterusedbytes, clusterstart;
uint samplerate, nchannels;
uint datasize, dataread = 0, nwavchunks, wavsize;
uint samplesPerBlock = 64, blocksize;

uchar read8() {uchar a; fread(&a, 1, 1, file_i); return a;}
ushort read16() {ushort a; fread(&a, 2, 1, file_i); return a;}
uint read32() {uint a; fread(&a, 4, 1, file_i); return a;}

void write8(uchar a) {fwrite(&a, 1, 1, file_o);}
void write16(ushort a) {fwrite(&a, 2, 1, file_o);}
void write32(uint a) {fwrite(&a, 4, 1, file_o);}

void main(int argc, char *argv[])
{
	int i; char *reqfni = 0, *reqfno = 0; int reqsr = 0;

	// Read command line arguments
	for(i = 1; i < argc; i++)
	{
		if(argv[i][0] == 0) continue;
		if((argv[i][0] == '/') || (argv[i][0] == '-'))
		{
			switch(argv[i][1])
			{
				case 'o':
					i++; if(i >= argc) break;
					reqfno = argv[i];
					break;
				case 'r':
					i++; if(i >= argc) break;
					reqsr = atoi(argv[i]);
					break;
			}
		}
		else
		{
			if(!reqfni)
				reqfni = argv[i];
		}
	}

	file_i = fopen(reqfni ? reqfni : "input.rws", "rb"); assert(file_i);
	file_o = fopen(reqfno ? reqfno : "output.wav", "wb"); assert(file_o);

	assert(read32() == 0x80d);
	fseek(file_i, 8, SEEK_CUR);
	assert(read32() == 0x80e);
	headsize = read32();
	fseek(file_i, 4, SEEK_CUR);

	fseek(file_i, 32, SEEK_CUR);
	nsegments = read32();
	read32();
	ntracks = read32(); assert(ntracks == 1);
	fseek(file_i, 36 + 16, SEEK_CUR);

	for(i = 0; i < nsegments; i++)
		fseek(file_i, 32, SEEK_CUR);

	for(i = 0; i < nsegments; i++)
		fseek(file_i, 20, SEEK_CUR);

	for(i = 0; i < nsegments; i++)
		fseek(file_i, 16, SEEK_CUR);

	// Track
	printf("Track @ 0x%0X\n", ftell(file_i));
	fseek(file_i, 16, SEEK_CUR);
	clustersize = read32();
	fseek(file_i, 12, SEEK_CUR);
	clusterusedbytes = read32();
	clusterstart = read32();

	samplerate = read32();
	samplerate = (reqsr > 0) ? reqsr : samplerate;
	fseek(file_i, 9, SEEK_CUR);
	nchannels = read8();

	printval(headsize);
	printval(nsegments);
	printval(ntracks);
	printval(clustersize);
	printval(clusterusedbytes);
	printval(clusterstart);
	printval(samplerate);
	printval(nchannels);

	fseek(file_i, 24 + headsize, SEEK_SET);
	printf("Audio data chunk at 0x%0X\n", ftell(file_i));

	assert(read32() == 0x80f);
	datasize = read32();
	read32();
	printf("Audio chunk datasize = %u 0x%0X\n", datasize, datasize);

	nwavchunks = datasize / clustersize;
	wavsize = nwavchunks * clusterusedbytes;
	samplesPerBlock = 65;
	blocksize = (samplesPerBlock/2+4)*nchannels;

	// Write the header of the WAV file.
	write32('FFIR');
	write32(8 + 24 + 8 + wavsize);
	write32('EVAW');
	write32(' tmf');
	write32(20);
	write16(0x11);		// WAVE_FORMAT_IMA_ADPCM / WAVE_FORMAT_DVI_ADPCM
	write16(nchannels);	// Number of channels
	write32(samplerate);	// Samples per second (in Hz)
	write32(samplerate * blocksize / samplesPerBlock); // Bytes per second to load
	write16(blocksize);	// Block alignment (For PCM, bytes for 1 sample / For ADPCM, size of one compressed block)
	write16(4);		// Bits per sample
	write16(2);		// Custom size
	write16(samplesPerBlock); // Samples per ADPCM block
	write32('atad');
	write32(wavsize);

	while(dataread < datasize)
	{
		// Copy the wave data from the RWS to the WAV
		for(i = 0; i < clusterusedbytes; i++)
			write8(read8());

		// Ignore several bytes in the RWS chunk that are unused.
		fseek(file_i, clustersize - clusterusedbytes, SEEK_CUR);

		dataread += clustersize;
	}

	fclose(file_i); fclose(file_o);
}