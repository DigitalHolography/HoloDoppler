#pragma once
#include "DemoHead.h"
#include "ISource.h"

class FileSource: public ISource
{
private:
	Cine* m_pAttachedCine;
	char  mFilePath[MAX_PATH];

public:
	FileSource(char* filePath);
	~FileSource(void);

	virtual Cine* CurrentCine();

	void GetFilePath(TCHAR* pFilePath, UINT buffSz);

};
