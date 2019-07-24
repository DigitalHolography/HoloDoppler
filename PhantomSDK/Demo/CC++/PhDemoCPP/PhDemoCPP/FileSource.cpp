#include "StdAfx.h"
#include "FileSource.h"

FileSource::FileSource(char* filePath)
{
	m_pAttachedCine = new Cine(filePath);
	strcpy_s(mFilePath, MAX_PATH, filePath);
}

FileSource::~FileSource(void)
{
	if (m_pAttachedCine!=NULL)
	{
		delete m_pAttachedCine;
		m_pAttachedCine = NULL;
	}
}

Cine* FileSource::CurrentCine()
{
	return m_pAttachedCine;
}

void FileSource::GetFilePath(TCHAR* pFilePath, UINT buffSz)
{
    size_t convertedChars = 0;

    mbstowcs_s(&convertedChars, pFilePath, buffSz, mFilePath, _TRUNCATE);


	//strcpy_s(pFilePath, buffSz, mFilePath);
}
