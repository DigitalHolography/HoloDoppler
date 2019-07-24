#include "StdAfx.h"
#include "ErrorHandler.h"

HRESULT ErrorHandler::m_LastError=0;
HWND ErrorHandler::m_MainWindow;

void ErrorHandler::GetErrorMessage(HRESULT errorCode, char* message)
{
	PhGetErrorMessage((int)errorCode, message);
}

BOOL ErrorHandler::IsConnectionError(HRESULT result)
{
    //
    // no longer want to see timeout error with new enumeration (06/16/2017)
    //
    return (result == ERR_NoResponseFromCamera || result == ERR_TimeOut
            || result == ERR_GetImageTimeOut || result == ERR_BadCameraNumber);
}

void ErrorHandler::CheckError(HRESULT errorCode)
{
	m_LastError = errorCode;
	if (errorCode < 0 
        
        //
        // an error was signaled
		// in this demo we are not interested in displaying errors: ERR_BadTriggerTime, ERR_BadImageInterval and ERR_NotIncreasingTime
		//
        && errorCode != ERR_BadTriggerTime 
        && errorCode != ERR_BadImageInterval 
        && errorCode != ERR_NotIncreasingTime

        //
        // no longer want to see timeout error with new enumeration (06/16/2017)
        //
        && errorCode != ERR_GetTimeTimeOut
        && errorCode != ERR_NoResponseFromCamera
        && errorCode != ERR_GetAudioTimeOut
        && errorCode != ERR_TimeOut
        && errorCode != ERR_GetImageTimeOut)

	{
		char message[MAXERRMESS];
        TCHAR Tmessage[MAXERRMESS];
        size_t convertedChars = 0;

        GetErrorMessage(errorCode, message);
		//alternatively you can throw new exception with message


        mbstowcs_s(&convertedChars, Tmessage, MAXERRMESS, message, _TRUNCATE);

		MessageBox(m_MainWindow, Tmessage, L"PhError", MB_OK|MB_ICONERROR);
	}
}
