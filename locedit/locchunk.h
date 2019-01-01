struct LocChunk
{
	uint32_t type;
	uint32_t id;
	void *data;
	uint32_t size;

	LocChunk() : type(0), id(0), data(0), size(0) {}

	bool hasData() {return data != 0;}
	void freeData();
	void setData(void *newdata, uint32_t newsize);
	~LocChunk() {freeData();}
};

class LocFile
{
public:
	std::vector<LocChunk*> chunks;
	LocFile(char *filename);
	void save(char *filename);
private:
	uint32_t readInt32(FILE *f);
	void writeInt32(FILE *f, uint32_t a);
};
