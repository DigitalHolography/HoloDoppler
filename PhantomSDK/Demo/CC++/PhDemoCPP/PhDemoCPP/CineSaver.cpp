#include "StdAfx.h"
#include "CineSaver.h"

Cine* CineSaver::m_pCine = NULL;
BOOL CineSaver::m_Started = FALSE;
UINT CineSaver::m_Progress = 0;
BOOL CineSaver::m_AcknowledgedStop = TRUE;

BOOL CineSaver::IsStarted()
{
	return m_Started;
}
UINT CineSaver::GetProgress()
{
	return m_Progress;
}

void CineSaver::SetCine(Cine *pCine)
{
	//The old cine duplicate is destroyed.
	DestroyCine();

	//A cine used for save should be used just in that context. The cine is duplicated.
	m_pCine = new Cine(*pCine);

	m_Started = FALSE;
	m_Progress = 0;
	m_AcknowledgedStop = TRUE;

}

 void CineSaver::DestroyCine()
 {
	if (m_pCine!=NULL)
	{
		delete m_pCine;
		m_pCine = NULL;
	}
 }

BOOL CineSaver::ShowGetCineNameDialog()
{
	if (m_pCine->IsLive())
		return FALSE;//live cine cannot be saved
	else
		return m_pCine->GetSaveCineName();
}
BOOL CineSaver::StartSave()
{
	if (m_Started || m_pCine==NULL || m_pCine->IsLive())
		return FALSE;

	//set the usecase for save
	m_pCine->SetUseCase(UC_SAVE);
	//NOTE: We exemplify the m_pCine->StartSaveCineAsync because it has a much complex use scenario than m_pCine->SaveCine()
	//You may use the single thread function m_pCine->SaveCine() but you will need a thread if you want a responsive UI
	if (!m_pCine->StartSaveCineAsync(&CineSaver::SaveProgressChanged))
	{
		return FALSE;
	}

	m_Started = TRUE;
	m_AcknowledgedStop = FALSE;
	return TRUE;
}

void CineSaver::StopSave()
{
	if (m_pCine!=NULL && m_Started)
	{
		m_pCine->StopSaveCineAsync();
		ErrorHandler::CheckError(
			GetSaveCineError());
	}
}

//check if any errors occured during cine saving
HRESULT CineSaver::GetSaveCineError()
{
	return m_pCine->GetSaveCineError();
}

BOOL WINAPI CineSaver::SaveProgressChanged(UINT percent, CINEHANDLE ch)
{
	m_Progress = percent;
	//function will always call the 100
	if (percent == 100)
		m_Started = FALSE;

	//return true to continue saving
	return TRUE;
}
