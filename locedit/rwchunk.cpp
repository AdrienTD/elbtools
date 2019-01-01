#include "rwchunk.h"

void RwChunk::load(void * mem)
{
	uint32_t* pnt = (uint32_t*)mem;
	tag = pnt[0];
	size = pnt[1];
	ver = pnt[2];
	data = malloc(size);
	memcpy(data, mem, size);
}

void RwChunk::freeData()
{
	if (data) free(data);
	data = 0; size = 0;
}
