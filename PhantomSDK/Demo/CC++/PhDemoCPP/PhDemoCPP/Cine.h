#pragma once
#include "ErrorHandler.h"

//A class that encapsulates a cine handle.
class Cine
{

private:
	//The handle of the cine, the structure around which the Cine class is built.
	CINEHANDLE mCineHandle;
	//True if the cine is used for camera live images, false if it is a true stored cine
	BOOL mIsLive;

	void InitCameraCineHandle(INT cameraNumber, INT cineNumber);
	void DestroyCineHandle();

public:
	//costructor to create a cine from file
	Cine(char* cineFilePath);
	//constructor to create a cine from camera
	Cine(INT cameraNumber, INT cineNumber);
	//copy constructor
	Cine(const Cine& cine);

	~Cine(void);

	//GeneralInfo
	BOOL IsLive();
	INT GetFirstImageNumber();
	UINT GetImageCount();
	UINT GetPostTriggerFrames();
	INT GetLastImageNumber();
	// Trigger delay in frames. 
    // Setting postrigger frames larger than cine partition image capacity will work as a trigger delay.
	UINT GetTriggerDelay();
	INT GetCineFileType();
	BOOL IsFileCine();
	BOOL HasMetaWB();
	INT GetUseCase();
	void SetUseCase(INT cineUseCaseID);

	//Cine Metadata
	BOOL IsColor();
	BOOL Is16Bpp();
	INT GetBppReal();
	INT GetImWidth();
	INT GetImHeight();
	double GetFrameRate();
	UINT GetExposure();
	UINT GetEDRExposureNs();

	//ImageProcessing
	FLOAT GetBrightness();
	void SetBrightness(FLOAT value);
	FLOAT GetContrast();
	void SetContrast(FLOAT value);
	FLOAT GetGamma();
	void SetGamma(FLOAT value);
	FLOAT GetSaturation();
	void SetSaturation(FLOAT value);
	FLOAT GetHue();
	void SetHue(FLOAT value);
	FLOAT GetSensitivity();
	void GetWhiteBalanceGain(PWBGAIN wbValue);
	void SetWhiteBalanceGain(PWBGAIN wbValue);

	//Read a cine image into a buffer
	HRESULT GetCineImage(PBYTE pImgBuffer, PIMRANGE pImgRange, PIH pImgHeader, UINT imgSizeInBytes);
	// Get image buffer size in bytes
	UINT GetMaxImageSizeInBytes();
	void SetVFlipView(BOOL flipV);

	//Save cine
	// Will show the dialog to browse for a file where the cine will be saved.
	// The file name and other options are updated into the cine handle buffer.
	BOOL GetSaveCineName();
	// Single thread cine save function
	void SaveCine(PROGRESSCB pfnCallback);
	// Start a cine saving thread
	BOOL StartSaveCineAsync(PROGRESSCB pfnCallback);
	// Stop the cine saving thread
	void StopSaveCineAsync();
	HRESULT GetSaveCineError();

	//Static Methods, Utils
	// Transalte a cine string into a cine number
    static INT ParseCineNo(CString* cineStrID, int firstFlashCine);
	//Get a string associated with a cine number
    static void GetStringForCineNo(CString* strValue, INT cineNo, int firstFlashCine);

	void Cine::PrintSigInfo(CString *psigInfo);			//signal names, properties etc...
	void Cine::PrintAnaSig(CString *psigVal, INT ImNr);	//analog sig values - all samples for an image
	void Cine::PrintBinSig(CString *psigVal, INT ImNr);	//binary sig values - all samples for an image

};
