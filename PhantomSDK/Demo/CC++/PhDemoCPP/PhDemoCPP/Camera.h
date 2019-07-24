#pragma once
#include "DemoHead.h"
#include "ISource.h"


enum CameraStatus
{
    NotAvailable,
    Preview,
    RecWaitingForTrigger,
    RecPostriggerFrames
};

//Class for controlling a Phantom camera, setting camera options or parameters and reading camera info
class Camera: public ISource
{

private:
	//A camera identifier used in dlls acces.
	UINT mCameraNumber;
	//Serial is a unique camera id that does not change in a session. It will be buffered.
	UINT mSerial;
	//Cine from which live images are taken. Also image processing options will be read or set with this cine.
	Cine* mLiveCine;

    // Indicates if the camera is offline
    BOOL mOffline;

	//Buffers
	//Selected cine partition number (helper buffer). Used to keep track of cine partition selection.
	INT mSelectedCinePartNo;
	Cine* mSelectedCine;
	//End UI buffers

	void InitSerial();
	void InitCines();
	void CreateLiveCine();
	void DeleteCines();

public:
	Camera(UINT cameraNo);
	Camera(void);
	~Camera(void);

	Camera(const Camera& cam);
	Camera& operator= (const Camera& cam);

	//Members access
	UINT GetCameraNumber();
	UINT GetCameraSerial();
    BOOL offlineStateChange();
    BOOL OfflineState();
    BOOL ParamsChanged();

	INT GetSelectedCinePartNo();
	void SetSelectedCinePartNo(INT partNo);
	void DestroySelectedCine();

	// ISource
	// Get a cine from which to read images. Can be either live cine or selected cine.
	virtual Cine* CurrentCine();

	//CameraInfo
	void GetCameraName(CString* pCameraName);
	void SetCameraName(CString* pCameraName);
	UINT GetCameraVersion();
	void GetCameraModel(CString* pCameraModel);
	UINT GetFirmwareVersion();
	void GetIPAddress(CString* pEthAddress);

	//Camera Options & Parameters
	void GetCamOptions(PCAMERAOPTIONS pCamOptions);
	void SetCamOptions(PCAMERAOPTIONS pCamOptions);
	// Read the acquisition parameters from a specified camera cine partition.
	void GetAcquisitionParameters(INT partNo, PACQUIPARAMS pAcquisitionParams);
	// Set the acquisition parameters to a specified camera cine partition.
	void SetAcquisitionParameters(INT partNo, PACQUIPARAMS pAcquisitionParams);
	// Were camera options or parameteres changed by annother connection or another application instance?
	BOOL ParametersExternallyChanged();
	void GetCameraResolutions(PPOINT pRes, PUINT pCnt);
	void GetCameraBitDepths(PUINT pCnt, PUINT pBitDepths);

	//Camera partitons/cines infos
	CINESTATUS GetCinePartitionStatus(INT partNo);
	// Get the cine status of a camera cine.
	void GetRAMCinePartitionStatus(PCINESTATUS cstats);
	BOOL IsCinePartitionStored(INT partNo);
	// Determine if the camera has a stored cine partition in RAM.
	BOOL HasStoredRAMPart();

	BOOL IsOnSinglePartition();

    int GetFirstFlashCine();
	// Get the number of camera RAM cine partitions.
	UINT GetPartitionCount();
	// Set the number of camera RAM cine partitions.
	void SetPartitionCount(UINT partitions);
	// Get the maximum number of RAM cine partitions.
	UINT GetMaxPartitionCount();
	// Get the count of the recorded cine partitions in camera RAM.
	UINT GetRamCineCount();
	// Get the count of the cines in camera flash/CineMag.
	UINT GetFlashCineCount();
	UINT GetLastRamCineNo();
	UINT GetLastFlashCineNo();

	// Is false when the device does not have acqusition parts. 
	// As a result it will not provide live images or recording actions. 
	// The device can be a CineStation.
	BOOL GetSupportsRecordingCines();
	// Determine the current cine partition number where the recording it taking place.
	INT GetActiveCineNo();

	// Get the status of the camera.
	CameraStatus GetCamStatus();

	//Actions
	// Deletes all stored cine partitions and start recording
	void Record();
	// Start recording in specified partition deleting it first.
	void RecordSpecificCine(INT cineNo);
	// Send a software trigger to camera.
	void SendSoftwareTrigger();
	// Setup and configure signals acquisition
	void SignalsSetup();

	//Utils
	void ToString(CString* pStr);
	// Create equal length partition weights.
	static void GenerateEqualPartitionsWeights(UINT count, PUINT pWeights);
};
