#pragma once
#include "Cine.h"
#include "DemoHead.h"

//static class to start the save of a cine, stop it and keep track of the saving cine status
class CineSaver
{
private:
	static Cine* m_pCine;
	static BOOL m_Started;
	static UINT m_Progress;

public:
	static BOOL m_AcknowledgedStop;


	//Set the cine to be saved.
	static void SetCine(Cine *pCine);
	static void DestroyCine();
	static BOOL IsStarted();
	static UINT GetProgress();

	//Show a dialog to get the saving location of a cine
	static BOOL ShowGetCineNameDialog();
	static BOOL StartSave();
	static void StopSave();

	static HRESULT GetSaveCineError();

	static BOOL WINAPI SaveProgressChanged(UINT percent, CINEHANDLE cineHandle);
};
