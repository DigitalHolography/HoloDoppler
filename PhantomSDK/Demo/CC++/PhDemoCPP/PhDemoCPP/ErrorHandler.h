#pragma once
#include "DemoHead.h"

// Handles Phantom dll errors
class ErrorHandler
{
private:
	static BOOL bErrMsgDisplayed;
	static void GetErrorMessage(HRESULT errorCode, char* message);

public:
	static HRESULT m_LastError;
	static HWND m_MainWindow;
	static void CheckError(HRESULT errorCode);
    static BOOL IsConnectionError(HRESULT result);
};
