#include "StdAfx.h"
#include "PoolBuilder.h"
#include "ErrorHandler.h"
#include "DemoHead.h"

//dummy callback, can be used to show progress on PhRegisterClientEx
BOOL WINAPI ProgressCB(UINT CN, UINT Percent)
{
	return TRUE;//return true to continue
}


PoolBuilder::PoolBuilder(HWND clientFormHnd, char* stgAndLogFolder)
{
	mClientFormHnd = clientFormHnd;

	//If LogAndStgFolder == NULL then the Log&STG folder is the default generated in DLL's
    //default log folder is \Application Data\Phantom\DLLVersion
	if (stgAndLogFolder != NULL)
	{
		strcpy_s(mStgAndLogFolder, MAX_PATH, stgAndLogFolder);
	}
    mIsRegistered = FALSE;
}

BOOL PoolBuilder::IsRegistered()
{
	return mIsRegistered;
}

void PoolBuilder::Register(void)
{
	int hret;
	hret = PhRegisterClientEx(NULL, NULL, ProgressCB, PHCONHEADERVERSION);

	if (hret >= 0)
	{
        mIsRegistered = TRUE;
	}
    else
    {
        ErrorHandler::CheckError(hret);
    }
    PhConfigPoolUpdate(1500); // look for new cameras as fast as possible

}

BOOL PoolBuilder::UnRegister(void)
{
	return (PhUnregisterClient(mClientFormHnd) != 0);
}

PoolBuilder::~PoolBuilder(void)
{
}
