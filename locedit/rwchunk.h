#pragma once

#include "global.h"

struct RwChunk
{
	uint32_t tag;
	uint32_t size;
	uint32_t ver;
	void *data;

	void load(void *mem);
	void freeData();

	RwChunk() : tag(0), size(0), ver(0xAD3132), data(0) {}
	RwChunk(void *mem) : RwChunk() { load(mem); }
	~RwChunk() { freeData(); }
};
