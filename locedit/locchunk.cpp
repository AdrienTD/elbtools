#include "global.h"
#include "locchunk.h"

void LocChunk::freeData()
{
	if(data) free(data);
	data = 0; size = 0;
}

void LocChunk::setData(void *newdata, uint32_t newsize)
{
	freeData();
	data = malloc(newsize);
	size = newsize;
	memcpy(data, newdata, newsize);
}

uint32_t LocFile::readInt32(FILE *f) {uint32_t r; fread(&r, 4, 1, f); return r;}
void LocFile::writeInt32(FILE *f, uint32_t a) {fwrite(&a, 4, 1, f);}

LocFile::LocFile(char *filename)
{
	FILE *f = fopen(filename, "rb");
	uint32_t numChunks = readInt32(f);
	for(uint32_t i = 0; i < numChunks; i++)
	{
		LocChunk *chk = new LocChunk;
		chk->type = readInt32(f);
		chk->id = readInt32(f);
		uint32_t nextChunkOffset = readInt32(f);
		chk->size = nextChunkOffset - ftell(f);
		chk->data = malloc(chk->size);
		fread(chk->data, chk->size, 1, f);
		fseek(f, nextChunkOffset, SEEK_SET);
		chunks.push_back(chk);
	}
	fclose(f);
}

void LocFile::save(char *filename)
{
	FILE *f = fopen(filename, "wb");
	uint32_t numChunks = chunks.size();
	writeInt32(f, numChunks);
	for(uint32_t i = 0; i < numChunks; i++)
	//for(auto c = chunks.begin(); c != chunks.end(); c++)
	{
		LocChunk *c = chunks[i];
		uint32_t offset = ftell(f);
		writeInt32(f, c->type);
		writeInt32(f, c->id);
		writeInt32(f, offset+12+c->size);
		fwrite(c->data, c->size, 1, f);
	}
	fclose(f);
}