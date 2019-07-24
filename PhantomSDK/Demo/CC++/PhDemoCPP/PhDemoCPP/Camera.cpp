#include "StdAfx.h"
#include "Camera.h"
#include "ErrorHandler.h"


Camera::Camera(UINT cameraNo) : ISource()
{
	mCameraNumber = cameraNo;

	InitSerial();
	InitCines();

    mOffline = OfflineState();
}

//default constructor. Only camera number is initialized. Do not use it.
Camera::Camera(void) : ISource()
{
	mCameraNumber = 0;
    mLiveCine = NULL;
	mSelectedCine = NULL;
}

Camera::~Camera(void)
{
	DeleteCines();
}

Camera::Camera(const Camera& cam) 
{
	mCameraNumber = cam.mCameraNumber;
	mSerial = cam.mSerial;
	mSelectedCinePartNo = cam.mSelectedCinePartNo;
	mSelectedCine = NULL;//it will be created at first access
	CreateLiveCine();

    mOffline = OfflineState();
}

Camera& Camera::operator= (const Camera& cam)
{
	if (this==NULL || this != &cam)
	{
		DeleteCines();

		mCameraNumber = cam.mCameraNumber;
		mSerial = cam.mSerial;
		mSelectedCinePartNo = cam.mSelectedCinePartNo;
		mSelectedCine = NULL;//it will be created at first acces
        mOffline = cam.mOffline;
        CreateLiveCine();
	}
	return *this;
}

void Camera::InitSerial()
{
	//We need camera serial whatever it is connected or not. Serial is not changing and will be available when camera is offline.
	char camName[MAXSTDSTRSZ];
	ErrorHandler::CheckError(
		PhGetCameraID(mCameraNumber, &mSerial, camName));	
}

void Camera::InitCines()
{
	CreateLiveCine();
	mSelectedCinePartNo = CINE_PREVIEW;
	mSelectedCine = NULL;
}

void Camera::CreateLiveCine()
{
	mLiveCine = new Cine(mCameraNumber, CINE_CURRENT);
}

void Camera::DeleteCines()
{
	if (mLiveCine!=NULL)
	{
		delete mLiveCine;
		mLiveCine = NULL;
	}
	DestroySelectedCine();
}


#pragma region Members Access
UINT Camera::GetCameraNumber()
{
	return mCameraNumber;
}

UINT Camera::GetCameraSerial()
{
	return mSerial;
}

INT Camera::GetSelectedCinePartNo()
{
	return mSelectedCinePartNo;
}

BOOL Camera::OfflineState()
{
    return (PhOffline(mCameraNumber));
}

BOOL Camera::ParamsChanged()
{
    BOOL Changed = FALSE;

    PhParamsChanged(mCameraNumber, &Changed);
    return (Changed);
}

//
// Did a Camera go from Online  --> Offline or
// Did a Camera go from Offline --> Online 
//
BOOL Camera::offlineStateChange()
{
    BOOL stateChanged = FALSE;

    BOOL currentState = OfflineState();

    if (mOffline != currentState)
    {
        mOffline = currentState;

        stateChanged = TRUE;
    }
    return (stateChanged);
}

void Camera::SetSelectedCinePartNo(INT partNo)
{
	//destroys the old selected cine
	DestroySelectedCine();

	mSelectedCinePartNo = partNo;
}

void Camera::DestroySelectedCine()
{
	if (mSelectedCine!=NULL)
	{
		delete mSelectedCine;
		mSelectedCine = NULL;
	}
}

//ISource
Cine* Camera::CurrentCine()
{
	Cine* pCine = NULL;
	if (IsCinePartitionStored(mSelectedCinePartNo))
	{
		//if needed create the selected cine
		if (mSelectedCine == NULL)
			mSelectedCine = new Cine(mCameraNumber, mSelectedCinePartNo);
		pCine = mSelectedCine;
	}
	else
	{
		pCine = mLiveCine;
		//the selected cine partition is not stored, destroy the cine
		DestroySelectedCine();
	}
	return pCine;
}
#pragma endregion

#pragma region CameraInfo
void Camera::GetCameraName(CString* pCameraName)
{
	UINT serial;
	char camName[MAXSTDSTRSZ];
    TCHAR TcamName[MAXSTDSTRSZ];
    size_t convertedChars = 0;
    
    pCameraName->Empty();
	ErrorHandler::CheckError(
		PhGetCameraID(mCameraNumber, &serial, camName));

    mbstowcs_s(&convertedChars, TcamName, MAXIPSTRSZ, camName, _TRUNCATE);

	pCameraName->Append(TcamName);
}

void Camera::SetCameraName(CString* pCameraName)
{
	char camName[MAXSTDSTRSZ];
    size_t convertedChars = 0;

    wcstombs_s(&convertedChars, camName, MAXSTDSTRSZ, pCameraName->GetString(), _TRUNCATE);

	//strcpy_s(camName, MAXSTDSTRSZ, pCameraName->GetString());

	ErrorHandler::CheckError(
		PhSetCameraName(mCameraNumber, camName));
}

UINT Camera::GetCameraVersion()
{
	UINT camVersion;
	ErrorHandler::CheckError(
		PhGetVersion(mCameraNumber, GV_CAMERA, &camVersion));
	return camVersion;
}


void Camera::GetCameraModel(CString* pCameraModel)
{
	char versionString[MAXSTDSTRSZ];
    TCHAR TversionString[MAXSTDSTRSZ];
    size_t convertedChars = 0;

    ErrorHandler::CheckError(
		PhGet(mCameraNumber, gsModel, versionString));
	pCameraModel->Empty();

    mbstowcs_s(&convertedChars, TversionString, MAXIPSTRSZ, versionString, _TRUNCATE);

	pCameraModel->Append(TversionString);
}

UINT Camera::GetFirmwareVersion()
{
	UINT firmWare;
	ErrorHandler::CheckError(
		PhGetVersion(mCameraNumber, GV_FIRMWARE, &firmWare));
	return firmWare;
}

void Camera::GetIPAddress(CString* pEthAddress)
{
	char ethAddress[MAXIPSTRSZ];
    TCHAR TethAddress[MAXIPSTRSZ];
    size_t convertedChars = 0;
    
    ErrorHandler::CheckError(
		PhGet(mCameraNumber, gsIPAddress, ethAddress));
	pEthAddress->Empty();

    mbstowcs_s(&convertedChars, TethAddress, MAXIPSTRSZ, ethAddress, _TRUNCATE);

	pEthAddress->Append(TethAddress);
}

//status info
CameraStatus Camera::GetCamStatus()
{
	if (GetSupportsRecordingCines())
	{
		INT activeCineNo = GetActiveCineNo();
		if (activeCineNo == CINE_PREVIEW)
			return ::Preview;
		else
		{
            PCINESTATUS pCstats = (PCINESTATUS)malloc(sizeof(CINESTATUS) * PhMaxCineCnt((UINT)mCameraNumber));
            GetRAMCinePartitionStatus(pCstats);
            if (pCstats[activeCineNo].Triggered)
            {
                free(pCstats);
                return ::RecPostriggerFrames;
            }
            else
            {
                free(pCstats);
                return ::RecWaitingForTrigger;
            }
		}
	}
	else
		return ::NotAvailable;
}
#pragma endregion

#pragma region Camera Options & Parameters
void Camera::GetCamOptions(PCAMERAOPTIONS pCamOptions)
{
	ErrorHandler::CheckError(
		PhGetCameraOptions(mCameraNumber, pCamOptions));
}

void Camera::SetCamOptions(PCAMERAOPTIONS pCamOptions)
{
	ErrorHandler::CheckError(
		PhSetCameraOptions(mCameraNumber, pCamOptions));
}

void Camera::GetAcquisitionParameters(INT partNo, PACQUIPARAMS pAcquisitionParams)
{
	ErrorHandler::CheckError(
		PhGetCineParams(mCameraNumber, partNo, pAcquisitionParams, NULL));
}

void Camera::SetAcquisitionParameters(INT partNo, PACQUIPARAMS pAcquisitionParams)
{
	if (IsOnSinglePartition())
		ErrorHandler::CheckError(
			PhSetSingleCineParams(mCameraNumber, pAcquisitionParams));
	else
		ErrorHandler::CheckError(
			PhSetCineParams(mCameraNumber, partNo, pAcquisitionParams));
}

BOOL Camera::ParametersExternallyChanged()
{
	BOOL changed;
	ErrorHandler::CheckError(
		PhParamsChanged(mCameraNumber, &changed));
	return changed;
}

void Camera::GetCameraResolutions(PPOINT pRes, PUINT pCnt)
{
	ErrorHandler::CheckError(
		PhGetResolutions(mCameraNumber, pRes, pCnt, NULL, NULL));
}

void Camera::GetCameraBitDepths(PUINT pCnt, PUINT pBitDepths)
{
	ErrorHandler::CheckError(
		PhGetBitDepths(mCameraNumber, pCnt, pBitDepths));
}
#pragma endregion

#pragma region Camera Partitons/Cines Infos
BOOL Camera::IsOnSinglePartition()
{
	return GetPartitionCount()==1;
}

void Camera::GetRAMCinePartitionStatus(PCINESTATUS cstats)
{
	ErrorHandler::CheckError(
		PhGetCineStatus(mCameraNumber, cstats));
}

CINESTATUS Camera::GetCinePartitionStatus(INT partNo)
{
    CINESTATUS cs;

    if (partNo >= CINE_PREVIEW && partNo < GetFirstFlashCine())
	{
        PCINESTATUS pCstats = (PCINESTATUS)malloc(sizeof(CINESTATUS) * PhMaxCineCnt((UINT)mCameraNumber));
        GetRAMCinePartitionStatus(pCstats);
        cs = pCstats[partNo];
        free(pCstats);
    }
	else if (partNo<=(INT)GetLastFlashCineNo())
	{
		cs.Stored = TRUE;
	}
	else
	{
		cs.Stored = FALSE;
	}
    return(cs);
}

BOOL Camera::IsCinePartitionStored(INT partNo)
{
	CINESTATUS cs = GetCinePartitionStatus(partNo);
	return cs.Stored;
}

BOOL Camera::HasStoredRAMPart()
{
    BOOL  HasStoredRAM = FALSE;

	if (GetSupportsRecordingCines())
	{
        PCINESTATUS pCstats = (PCINESTATUS)malloc(sizeof(CINESTATUS) * PhMaxCineCnt((UINT)mCameraNumber));
        GetRAMCinePartitionStatus(pCstats);
		INT partCount = GetPartitionCount();
		for (INT i=0; i<= partCount; i++)
		{
            if (pCstats[i].Stored)
            {
                HasStoredRAM = TRUE;
                break;
            }
		}
        free(pCstats);
	}
    return (HasStoredRAM);
}

int Camera::GetFirstFlashCine()
{
    int firstFlashCine = PhFirstFlashCine(mCameraNumber);

    return (firstFlashCine);
}

UINT Camera::GetPartitionCount()
{
	UINT partCount;
	ErrorHandler::CheckError(
		PhGetPartitions(mCameraNumber, &partCount, NULL));
	return partCount;
}

void Camera::SetPartitionCount(UINT partitions)
{
    PUINT pPartitionWeights = (PUINT)malloc(sizeof(UINT) * PhMaxCineCnt((UINT)mCameraNumber));

    GenerateEqualPartitionsWeights(partitions, pPartitionWeights);
	ErrorHandler::CheckError(
        PhSetPartitions(mCameraNumber, partitions, pPartitionWeights));
    free(pPartitionWeights);
}

UINT Camera::GetMaxPartitionCount()
{
	UINT maxPartCount = 0;
	PhGet(mCameraNumber, gsMaxPartitionCount, &maxPartCount);
	return maxPartCount;
}

UINT Camera::GetRamCineCount()
{
	UINT ramCineCount, flashCineCount;
	ErrorHandler::CheckError(
		PhGetCineCount(mCameraNumber, &ramCineCount, &flashCineCount));
	return ramCineCount;
}

UINT Camera::GetFlashCineCount()
{
	UINT ramCineCount, flashCineCount;
	ErrorHandler::CheckError(
		PhGetCineCount(mCameraNumber, &ramCineCount, &flashCineCount));
	return flashCineCount;
}

UINT Camera::GetLastRamCineNo()
{
	return (CINE_FIRST + GetRamCineCount() - 1);
}

UINT Camera::GetLastFlashCineNo()
{
    return (GetFirstFlashCine() + GetFlashCineCount() - 1);
}

BOOL Camera::GetSupportsRecordingCines()
{
	BOOL supportsRecCines;
	ErrorHandler::CheckError(
		PhGet(mCameraNumber, gsSupportsRecordingCines, &supportsRecCines));
	return supportsRecCines;
}

INT Camera::GetActiveCineNo()
{
    PCINESTATUS pCstats = (PCINESTATUS)malloc(sizeof(CINESTATUS) * PhMaxCineCnt((UINT)mCameraNumber));

    GetRAMCinePartitionStatus(pCstats);
	INT partCount = GetPartitionCount();
	for (INT i=0; i<=partCount; i++)
	{
        if (pCstats[i].Active)
        {
            free(pCstats);
            return (i);
        }
	}
	return CINE_PREVIEW;
}
#pragma endregion

#pragma region Actions
//Deletes all stored cines and start recording
void Camera::Record()
{
	ErrorHandler::CheckError(
		PhRecordCine(mCameraNumber));
}

//Start recording in specified cine partition. Its content is deleted.
void Camera::RecordSpecificCine(INT cineNo)
{
	ErrorHandler::CheckError(
		PhRecordSpecificCine(mCameraNumber, cineNo));
}

void Camera::SendSoftwareTrigger()
{
	ErrorHandler::CheckError(
		PhSendSoftwareTrigger(mCameraNumber));
}
void Camera::SignalsSetup()
{
	ErrorHandler::CheckError(
		PhSigSetup(mCameraNumber));
}
#pragma endregion

#pragma region Utils
void Camera::ToString(CString* pStr)
{
	pStr->Empty();
	Camera::GetCameraName(pStr);
	pStr->Append(_T(" ("));
	TCHAR serialStr[SMALL_STR_MAXSZ];
	_ui64tot_s(mSerial, serialStr, SMALL_STR_MAXSZ, 10);
	pStr->Append(serialStr);
	pStr->Append(_T(") "));

    //
    // see if the camera is offline
    //
    if (mOffline == TRUE)
    {
        pStr->Append(_T("[Offline]"));
    }
}

void Camera::GenerateEqualPartitionsWeights(UINT count, PUINT weights)
{
	float percent;
	// Create equal length partition weights.
	for (UINT i = 0; i < count; i++)
	{
		percent = (float)100 / count;
		//multiply by 100 to get 2 point precision into int weights
		weights[i] = (UINT)(100 * percent);
	}
}
#pragma endregion
