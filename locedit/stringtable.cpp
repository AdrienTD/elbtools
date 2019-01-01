#include "global.h"
#include "locchunk.h"
#include <wx/string.h>
#include <wx/msgdlg.h>
#include "stringtable.h"

const wxString zeroString = "[0-sized string, DO NOT CHANGE!]";

StringTable::StringTable(LocChunk *chk, bool naog)
{
	pnt = (char*)chk->data;
	numThings = *(uint16_t*)pnt; pnt += 2;
	//wxMessageBox(wxString::Format("numThings = %i", numThings));
	for(uint16_t i = 0; i < numThings; i++)
		{thingTable1.push_back(*(uint32_t*)pnt); pnt += 4;}
	for(uint16_t i = 0; i < numThings; i++)
		{thingTable2.push_back(*(uint32_t*)pnt); pnt += 4;}
	//wxMessageBox(wxString::Format("%08X", pnt - (char*)chk->data));
	aog = *(uint32_t*)(pnt + 4) != 0;
	if (aog) {
		readAnonymous();
		readIdentified();
	}
	else {
		readIdentified();
		readAnonymous();
	}
}

void StringTable::readIdentified()
{
	uint32_t total = *(uint32_t*)pnt; pnt += 4;
	uint32_t cur = 0;
	//wxMessageBox(wxString::Format("%08X", total));
	while(cur < total)
	{
		uint32_t tid = *(uint32_t*)pnt; pnt += 4;
		uint32_t tsiz = *(uint32_t*)pnt; pnt += 4;
		//wxMessageBox(wxString::Format("%08X %08X", tid, tsiz));
		if (tsiz > 0)
		{
			wchar_t *wc = new wchar_t[tsiz + 1];
			for (int i = 0; i < tsiz; i++)
			{
				wc[i] = *(wchar_t*)pnt; pnt += 2;
			}
			wc[tsiz] = 0;
			identified.push_back(std::make_pair(tid, wxString(wc)));
			delete[] wc;
		}
		else
			identified.push_back(std::make_pair(tid, zeroString));
		cur += tsiz;
	}
}

void StringTable::readAnonymous()
{
	uint32_t total = *(uint32_t*)pnt; pnt += 4;
	uint32_t cur = 0;
	//wxMessageBox(wxString::Format("%08X", total));
	while(cur < total)
	{
		uint32_t tsiz = *(uint32_t*)pnt; pnt += 4;
		//wxMessageBox(wxString::Format("tsiz=%08X", tsiz));
		if (tsiz > 0)
		{
			wchar_t *wc = new wchar_t[tsiz + 1];
			for (int i = 0; i < tsiz; i++)
			{
				wc[i] = *(wchar_t*)pnt; pnt += 2;
			}
			wc[tsiz] = 0;
			anonymous.push_back(wxString(wc));
			delete[] wc;
		}
		else
			anonymous.push_back(zeroString);
		cur += tsiz;
	}
}

std::stringbuf *StringTable::writeChunkData()
{
	sbuf = new std::stringbuf;
	sbuf->sputn((char*)&numThings, 2);
	//for(int i = 0; i < numThings; i++)
	//	sbuf.sputn(
	sbuf->sputn((char*)thingTable1.data(), thingTable1.size()*4);
	sbuf->sputn((char*)thingTable2.data(), thingTable2.size()*4);
	if (aog) {
		writeAnonymous();
		writeIdentified();
	}
	else {
		writeIdentified();
		writeAnonymous();
	}
	return sbuf;
}

void StringTable::writeAnonymous()
{
	const static uint32_t zero = 0;
	// Count total characters
	uint32_t tot = 0;
	for(auto s = anonymous.begin(); s != anonymous.end(); s++)
		if(*s != zeroString)
			tot += s->size() + 1;
	sbuf->sputn((char*)&tot, 4);
	for(auto s = anonymous.begin(); s != anonymous.end(); s++)
	{
		if (*s != zeroString)
		{
			uint32_t len = (uint32_t)s->size() + 1;
			sbuf->sputn((char*)&len, 4);
			sbuf->sputn((char*)s->wc_str(), s->size() * 2 + 2);
		}
		else {
			uint32_t z = 0;
			sbuf->sputn((char*)&z, 4);
		}
	}
}

void StringTable::writeIdentified()
{
	const static uint32_t zero = 0;
	// Count total characters
	uint32_t tot = 0;
	for(auto s = identified.begin(); s != identified.end(); s++)
		if(s->second != zeroString)
			tot += s->second.size() + 1;
	sbuf->sputn((char*)&tot, 4);
	for(auto s = identified.begin(); s != identified.end(); s++)
	{
		sbuf->sputn((char*)&s->first, 4);
		if (s->second != zeroString) {
			uint32_t len = (uint32_t)s->second.size() + 1;
			sbuf->sputn((char*)&len, 4);
			sbuf->sputn((char*)s->second.wc_str(), s->second.size() * 2 + 2);
		}
		else {
			uint32_t z = 0;
			sbuf->sputn((char*)&z, 4);
		}
	}
}

void StringTable::debug()
{
	printf("numThings = %u\n", numThings);
}