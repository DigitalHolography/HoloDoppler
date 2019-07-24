#include "StdAfx.h"
#include "PoolRefresher.h"
#include <climits>


PoolRefresher::PoolRefresher(void)
{
    CameraCount = 0;

	m_CameraList.SetSize(0,1);
}

PoolRefresher::~PoolRefresher(void)
{
}

void PoolRefresher::GetEthernetCameras(CArray<Camera, Camera&>  *pCameraList)
{
    //
	// Get the number of cameras connected
    //
	UINT camCount;

	ErrorHandler::CheckError(
		PhGetCameraCount(&camCount));

	if (camCount > 0)
	{
        CameraCount = camCount;
		for (UINT CamNr = 0; CamNr < camCount; CamNr++)
		{
			Camera cam(CamNr);
			pCameraList->Add(cam);
		}
	}
	else
	{
        //
		// place a default simulated camera (VEO 710S) in the case of no camera connected
        //
		ErrorHandler::CheckError(
            PhAddSimulatedCamera(7001, 1234));

		Camera simCam(0);
		pCameraList->Add(simCam);
        CameraCount = 1;
	}
}

Camera* PoolRefresher::GetCameraAt(INT index)
{
	if (index>=0 && index<m_CameraList.GetCount())
		return &m_CameraList.GetAt(index);
	else
		return NULL;
}

INT PoolRefresher::GetCameraListLength()
{
	INT_PTR list_length = m_CameraList.GetCount();
	ASSERT( list_length <= INT_MAX );//the list will never reach this size, placed just an assert
	return static_cast< INT >(list_length);
}

void PoolRefresher::InitCameras()
{
	GetEthernetCameras(&m_CameraList);
}


//
// Did a Camera go from Online  --> Offline or
// Did a Camera go from Offline --> Online 
//
BOOL PoolRefresher::cameraStateChange()
{
    BOOL RefreshNeeded = FALSE;
    INT count = GetCameraListLength();
    INT i = 0;

    while  (i < count)
    {
        Camera* pCam = &(m_CameraList.GetAt(i));

        //
        // see if the camera is offline state changed
        //
        RefreshNeeded = pCam->offlineStateChange();

        //
        // if any camera needs updating we do all
        //
        if (RefreshNeeded == TRUE)
        {
            break;
        }
        i++;
    }

    return(RefreshNeeded);
}

BOOL PoolRefresher::RefreshCameras()
{
    BOOL RefreshNeeded = FALSE;
    UINT currentCameraCount;

    //
    // has the number of cameras connected changed
    //
    ErrorHandler::CheckError(
        PhGetCameraCount(&currentCameraCount));

    if (currentCameraCount > CameraCount) 
	{
		m_CameraList.RemoveAll();

        //
		// get the new list of cameras
        //
		GetEthernetCameras(&m_CameraList);

        RefreshNeeded = TRUE;
	}

    return(RefreshNeeded);
}

INT PoolRefresher::GetCameraIndexForSerial(UINT serial)
{
	INT count = GetCameraListLength();
	for (INT i=0; i<count; i++)
	{
		Camera* pCam = &(m_CameraList.GetAt(i));
		if (serial == pCam->GetCameraSerial())
		{
			return i;
		}
	}

    //
	// no camera found
    //
	return -1;
}