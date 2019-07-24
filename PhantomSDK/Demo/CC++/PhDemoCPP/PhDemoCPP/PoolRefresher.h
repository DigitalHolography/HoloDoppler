#pragma once
#include "Camera.h"
#include "DemoHead.h"

//Class to manage the online list of cameras
class PoolRefresher
{
private:
	CArray <Camera, Camera&> m_CameraList;

	void GetEthernetCameras(CArray<Camera, Camera&>  *pCameraList);
public:
	PoolRefresher(void);
	~PoolRefresher(void);

    UINT CameraCount;

	Camera* GetCameraAt(INT index);
	INT GetCameraListLength();

	void InitCameras();
	// Checks if the current camera list is up to date. If not refreshes the list.
	BOOL RefreshCameras();

    // Checks if the current camera list changed online/Offline State.
    BOOL cameraStateChange();

	INT PoolRefresher::GetCameraIndexForSerial(UINT serial);
};
