#pragma once
#include "windef.h"
#include "DemoHead.h"

class PoolBuilder
{
private:
	HWND	mClientFormHnd;
	char	mStgAndLogFolder[MAX_PATH];
	BOOL	mIsRegistered;

public:
	PoolBuilder(HWND clientFormHnd, char* stgAndLogFolder);

	~PoolBuilder(void);

	BOOL IsRegistered();
	void Register(void);
	BOOL UnRegister(void);
};
