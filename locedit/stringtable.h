#include <sstream>

class StringTable
{
public:
	std::vector<wxString> anonymous;
	std::vector<std::pair<uint32_t, wxString>> identified;
	uint16_t numThings;
	std::vector<uint32_t> thingTable1, thingTable2;
	bool aog;

	StringTable(bool naog = true) : numThings(0), aog(naog) {}
	StringTable(LocChunk *chk, bool naog = true);
	std::stringbuf *StringTable::writeChunkData();
	void debug();

private:
	char *pnt;
	std::stringbuf *sbuf;
	void readAnonymous();
	void readIdentified();
	void writeAnonymous();
	void writeIdentified();
};
