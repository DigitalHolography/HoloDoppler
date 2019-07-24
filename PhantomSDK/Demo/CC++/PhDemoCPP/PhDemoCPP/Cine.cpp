#include "StdAfx.h"
#include "Cine.h"

Cine::Cine(char* cineFilePath)
{
	//init file cine handle
	ErrorHandler::CheckError(
		PhNewCineFromFile(cineFilePath, &mCineHandle));
    mIsLive = FALSE;
}

Cine::Cine(INT cameraNumber, INT cineNumber)
{
	InitCameraCineHandle(cameraNumber, cineNumber);
}

//Copy constructor
Cine::Cine(const Cine& cine)
{
	mIsLive = cine.mIsLive;
	if (cine.mIsLive)
		//Live cine handle cannot have a duplicate, is unique per camera
		mCineHandle = cine.mCineHandle;
	else
		ErrorHandler::CheckError(
			PhDuplicateCine(&mCineHandle, cine.mCineHandle));
}

Cine::~Cine(void)
{
    //Live cine handle is managed internally in dlls and is destroyed within ph dlls when camera life ends. 
	if (!mIsLive)
		DestroyCineHandle();
}

BOOL Cine::IsLive()
{
	return mIsLive;
}

void Cine::InitCameraCineHandle(INT cameraNumber, INT cineNumber)
{
	if (cineNumber == CINE_PREVIEW && cineNumber < CINE_CURRENT)
		return;

	if (cineNumber == CINE_CURRENT)
	{
		//Live cine
		ErrorHandler::CheckError(
			PhGetCineLive(cameraNumber, &mCineHandle));
		mIsLive = TRUE;
	}
	else
	{
		ErrorHandler::CheckError(
			PhNewCineFromCamera(cameraNumber, cineNumber, &mCineHandle));
		mIsLive = FALSE;
	}
}

void Cine::DestroyCineHandle()
{
	if (mCineHandle!=NULL)
	{
		ErrorHandler::CheckError(
			PhDestroyCine(mCineHandle));
		mCineHandle = NULL;
	}
}

#pragma region GeneralInfo
INT Cine::GetFirstImageNumber()
{
	INT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_FIRSTIMAGENO, (PVOID)&value));
	return value;
}

UINT Cine::GetImageCount()
{
	UINT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_IMAGECOUNT, (PVOID)&value));
	return value;
}

UINT Cine::GetPostTriggerFrames()
{
	UINT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_POSTTRIGGER, (PVOID)&value));
	return value;
}

INT Cine::GetLastImageNumber()
{
	return Cine::GetFirstImageNumber() + Cine::GetImageCount() - 1;
}

UINT Cine::GetTriggerDelay()
{
	UINT postTriggFrames = Cine::GetPostTriggerFrames();
	UINT imCount = Cine::GetImageCount();
	if (postTriggFrames <= imCount)
		return 0;
	else
		return postTriggFrames - imCount;
}

INT Cine::GetCineFileType()
{
	INT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_FROMFILETYPE, (PVOID)&value));
	return value;
}

BOOL Cine::IsFileCine()
{
	BOOL value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_ISFILECINE, (PVOID)&value));
	return value;
}

BOOL Cine::HasMetaWB()
{
	BOOL value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_WBISMETA, (PVOID)&value));
	return value;
}

INT Cine::GetUseCase()
{
	INT cineUseCaseID;
	ErrorHandler::CheckError(
		PhGetUseCase(mCineHandle, &cineUseCaseID));
	return cineUseCaseID;
}

void Cine::SetUseCase(INT cineUseCaseID)
{
	ErrorHandler::CheckError(
		PhSetUseCase(mCineHandle, cineUseCaseID));
}
#pragma endregion

#pragma region Cine Metadata
BOOL Cine::IsColor()
{
	BOOL value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_ISCOLORCINE, (PVOID)&value));
	return value;
}

BOOL Cine::Is16Bpp()
{
	BOOL value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_IS16BPPCINE, (PVOID)&value));
	return value;
}

INT Cine::GetBppReal()
{
	INT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_REALBPP, (PVOID)&value));
	return value;
}

INT Cine::GetImWidth()
{
	INT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_IMWIDTH, (PVOID)&value));
	return value;
}

INT Cine::GetImHeight()
{
	INT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_IMHEIGHT, (PVOID)&value));
	return value;
}

double Cine::GetFrameRate()
{
	double value;
    ErrorHandler::CheckError(
        PhGetCineInfo(mCineHandle, GCI_DFRAMERATE, (PVOID)&value));
    return value;
}

//Note: returns exposure in ns
UINT Cine::GetExposure()
{
	UINT value;
    ErrorHandler::CheckError(
        PhGetCineInfo(mCineHandle, GCI_EXPOSURENS, (PVOID)&value));
	return value;
}

UINT Cine::GetEDRExposureNs()
{
	UINT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_EDREXPOSURENS, (PVOID)&value));
	return value;
}
#pragma endregion

#pragma region ImageProcessing
FLOAT Cine::GetBrightness()
{
	FLOAT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_BRIGHT, (PVOID)&value));
	return value;
}
void Cine::SetBrightness(FLOAT value)
{
	ErrorHandler::CheckError(
		PhSetCineInfo(mCineHandle, GCI_BRIGHT, (PVOID)&value));
}

FLOAT Cine::GetContrast()
{
	FLOAT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_CONTRAST, (PVOID)&value));
	return value;
}

void Cine::SetContrast(FLOAT value)
{
	ErrorHandler::CheckError(
		PhSetCineInfo(mCineHandle, GCI_CONTRAST, (PVOID)&value));
}

FLOAT Cine::GetGamma()
{
	FLOAT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_GAMMA, (PVOID)&value));
	return value;
}

void Cine::SetGamma(FLOAT value)
{
	ErrorHandler::CheckError(
		PhSetCineInfo(mCineHandle, GCI_GAMMA, (PVOID)&value));
}

FLOAT Cine::GetSaturation()
{
	FLOAT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_SATURATION, (PVOID)&value));
	return value;
}

void Cine::SetSaturation(FLOAT value)
{
	ErrorHandler::CheckError(
		PhSetCineInfo(mCineHandle, GCI_SATURATION, (PVOID)&value));
}

FLOAT Cine::GetHue()
{
	FLOAT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_HUE, (PVOID)&value));
	return value;
}

void Cine::SetHue(FLOAT value)
{
	ErrorHandler::CheckError(
		PhSetCineInfo(mCineHandle, GCI_HUE, (PVOID)&value));
}

FLOAT Cine::GetSensitivity()
{
	FLOAT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_GAIN16_8, (PVOID)&value));

	return value;
}

void Cine::GetWhiteBalanceGain(PWBGAIN wbValue)
{
	if (HasMetaWB())
	{
		ErrorHandler::CheckError(
			PhGetCineInfo(mCineHandle, GCI_WB, (PVOID)wbValue));//get the WB applied before image interpolation (on raw image)
	}
	else
	{
		ErrorHandler::CheckError(
			PhGetCineInfo(mCineHandle, GCI_WBVIEW, (PVOID)wbValue));//get the WB applied on already interpolated images
	}
}

void Cine::SetWhiteBalanceGain(PWBGAIN wbValue)
{
	if (HasMetaWB())
	{
		ErrorHandler::CheckError(
			PhSetCineInfo(mCineHandle, GCI_WB, (PVOID)wbValue));//will be set before image interpolation (on raw image)
	}
	else
	{
		ErrorHandler::CheckError(
			PhSetCineInfo(mCineHandle, GCI_WBVIEW, (PVOID)wbValue));//will be set on already interpolated images
	}
}
#pragma endregion

#pragma region GetImage
HRESULT Cine::GetCineImage(PBYTE pImgBuffer, PIMRANGE pImgRange, PIH pImgHeader, UINT imgSizeInBytes)
{
	HRESULT result = PhGetCineImage(mCineHandle, pImgRange, pImgBuffer, imgSizeInBytes, pImgHeader);
 	return result;
}

UINT Cine::GetMaxImageSizeInBytes()
{
	UINT value;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_MAXIMGSIZE, (PVOID)&value));
	return value;
}

void Cine::SetVFlipView(BOOL flipV)
{
	ErrorHandler::CheckError(
		PhSetCineInfo(mCineHandle, GCI_VFLIPVIEWACTIVE, (PVOID)&flipV));
}
#pragma endregion

#pragma region SaveCine
BOOL Cine::GetSaveCineName()
{
	//will show the dialog to browse for a file where the cine will be saved.
	return PhGetSaveCineName(mCineHandle) != 0;
}

void Cine::SaveCine(PROGRESSCB pfnCallback)
{
	ErrorHandler::CheckError(
		PhWriteCineFile(mCineHandle, pfnCallback));
}

BOOL Cine::StartSaveCineAsync(PROGRESSCB pfnCallback)
{
	ErrorHandler::CheckError(
		PhWriteCineFileAsync(mCineHandle, pfnCallback));

	return ErrorHandler::m_LastError>=0;
}

void Cine::StopSaveCineAsync()
{
	ErrorHandler::CheckError(
		PhStopWriteCineFileAsync(mCineHandle));
}

HRESULT Cine::GetSaveCineError()
{
	HRESULT errCode;
	ErrorHandler::CheckError(
		PhGetCineInfo(mCineHandle, GCI_WRITEERR, &errCode));
	return errCode;
}
#pragma endregion

#pragma region Static Methods
INT Cine::ParseCineNo(CString* cineStrID, int firstFlashCine)
{
	INT cineNo;
	if (cineStrID->Compare(_T(PREVIEW_CINE_NAME))==0)
	{
		cineNo = (int)CINE_PREVIEW;
	}
	else
	{
		CString firstChar = cineStrID->Mid(0,1);
		if (firstChar.CompareNoCase(_T("F"))==0)
		{
			//flash cine
			CString numberStr = cineStrID->Mid(1).Trim();
			cineNo = _ttoi(numberStr.GetString());
            cineNo = (int)firstFlashCine + cineNo - 1;//flash cine number
		}
		else
		{
			//the cine is from ram
			cineNo = _ttoi(cineStrID->GetString());
		}
	}
	return cineNo;
}

void Cine::GetStringForCineNo(CString* cineStrID, INT cineNo, int firstFlashCine)
{
	cineStrID->Empty();
	if (cineNo == CINE_PREVIEW)
	{
		cineStrID->Append(_T(PREVIEW_CINE_NAME));
	}
    else if (cineNo >= firstFlashCine)
	{
		TCHAR cineNoStr[SMALL_STR_MAXSZ];
		cineStrID->Append(_T("F"));
        _itot_s(cineNo - firstFlashCine + 1, cineNoStr, SMALL_STR_MAXSZ, 10);
		cineStrID->Append(cineNoStr);
	}
	else
	{
		TCHAR cineNoStr[SMALL_STR_MAXSZ];
		_itot_s(cineNo, cineNoStr, SMALL_STR_MAXSZ, 10);
		cineStrID->Append(cineNoStr);
	}
}
#pragma endregion


#pragma region Daq



void Cine::PrintSigInfo(CString *psigInfo)			//signal names, properties etc...
{
	int i, SmpImg, BinCnt, AnaCnt, NameCnt, AnaBip, AnaDiff, AnaEnc;

	char *bn[MAXBINCNT], *an[MAXANACNT], *au[MAXANACNT];
	int AnaGain[MAXANACNT];
	double AnaUserGain[MAXANACNT];

	char ModuleName[MAX_PATH];
	int MaxBinCnt, MaxAnaCnt;
	int UnipolarRanges, BipolarRanges;
	BOOL SupportsSingleEnded, SupportsDifferential;
	double SupportedGainsUnipolar[MAXANACNT], SupportedGainsBipolar[MAXANACNT];

	TCHAR BinName0[MAXSTDSTRSZ], AnaName0[MAXSTDSTRSZ], AnaUnit0[MAXSTDSTRSZ];
	size_t convertedChars = 0;


	
	PhGetCineInfo(mCineHandle, GCI_SAMPLESPERIMAGE, &SmpImg);		//Selected value for Samples per Image
	PhGetCineInfo(mCineHandle, GCI_BINCNT, &BinCnt);				//Selected value for Binary channels count
	PhGetCineInfo(mCineHandle, GCI_ANACNT, &AnaCnt);				//Selected value for Analog channels count

	PhGetCineInfo(mCineHandle, GCI_ANABIPOLAR, &AnaBip);			//Configure DAQ for bipolar / unipolar acquisition  
	PhGetCineInfo(mCineHandle, GCI_ANADIFFERENTIAL, &AnaDiff);		//Configure DAQ for diferential / single ended acquisition 

	//Read Only fields
	PhGetCineInfo(mCineHandle, GCI_SIGNAMECNT, &NameCnt);			//In this version only first 8 channels supports a user name for them
	PhGetCineInfo(mCineHandle, GCI_ANAENCODING, &AnaEnc);			//Analog data encoding and sample size: 
	PhGetCineInfo(mCineHandle, GCI_SIGMODULENAME, ModuleName);		//Aquisition module name
	PhGetCineInfo(mCineHandle, GCI_MAXBINCNT, &MaxBinCnt);			//Maximum count of binary channels
	PhGetCineInfo(mCineHandle, GCI_MAXANACNTSE, &MaxAnaCnt);		//Maximum count of analog channels in single ended  mode (half in differential)
	PhGetCineInfo(mCineHandle, GCI_SUPPORTSSINGLEENDED, &SupportsSingleEnded);		//Analog inputs support single ended mode
	PhGetCineInfo(mCineHandle, GCI_SUPPORTSDIFFERENTIAL, &SupportsDifferential);	//Analog inputs support differential mode
	PhGetCineInfo(mCineHandle, GCI_UNIPOLARRANGES, &UnipolarRanges);				//How may analog ranges supports the module in unipolar mode, 0= no support for unipolar 
	PhGetCineInfo(mCineHandle, GCI_BIPOLARRANGES, &BipolarRanges);					//How may analog ranges supports the module in bipolar mode,0= no support for bipolar
	PhGetCineInfo(mCineHandle, GCI_SUPPORTEDGAINSU, &SupportedGainsUnipolar);		//Returns the array with all possible analog gains in unipolar mode (count in UnipolarRanges)
	PhGetCineInfo(mCineHandle, GCI_SUPPORTEDGAINSB, &SupportedGainsBipolar);		//Returns the array with all possible analog gains in bipolar mode (count in BipolarRanges)


	//Allocate memory for name strings 
	//C style, null terminated by zero
	for (i = 0; i < BinCnt; i++)
		bn[i] = new char[MAXSTDSTRSZ];
	for (i = 0; i < AnaCnt; i++)
	{
		an[i] = new char[MAXSTDSTRSZ];
		au[i] = new char[MAXSTDSTRSZ];
	}

	
	//==========================================//
	//   Name and gains using PhGetCineInfo1()  //   
	//   and GCI_.... (per channel)	            //
	//==========================================//
	//Binary channels name
	for (i = 0; i < BinCnt; i++)
		PhGetCineInfo1(mCineHandle, GCI_BINNAME, i, bn[i]);
	//Analog channels name and unit
	for (i = 0; i < AnaCnt; i++)
	{
		PhGetCineInfo1(mCineHandle, GCI_ANANAME, i, an[i]);
		PhGetCineInfo1(mCineHandle, GCI_ANAUNIT, i, au[i]);
	}
	//get info: array of int, array of double
	for (i = 0; i < AnaCnt; i++)
	{
		PhGetCineInfo1(mCineHandle, GCI_ANAGAIN, i, &AnaGain[i]);
		PhGetCineInfo1(mCineHandle, GCI_ANAUSERGAIN, i, &AnaUserGain[i]);
	}

	//Convert name of the first bin channel to C++ unicode string
	if (BinCnt > 0)
		mbstowcs_s(&convertedChars, BinName0, MAXSTDSTRSZ, bn[0], _TRUNCATE);
	else
		BinName0[0] = 0;
	//Convert name and unit of the first ana channel to C++ unicode string
	if (AnaCnt > 0)
	{
		mbstowcs_s(&convertedChars, AnaName0, MAXSTDSTRSZ, an[0], _TRUNCATE);
		mbstowcs_s(&convertedChars, AnaUnit0, MAXSTDSTRSZ, au[0], _TRUNCATE);
	}
	else
	{
		AnaName0[0] = 0;
		AnaUnit0[0] = 0;
	}
	
	psigInfo->Format(L"Signals: SamplesPerImage:%d, Channels count :Binary:%d Analog:%d, BinName0: %s AnaName0: %s AnaUnit0: %s AnaGain: %d UserGain %f", 
		SmpImg, BinCnt, AnaCnt, BinName0, AnaName0, AnaUnit0, AnaGain[0], AnaUserGain[0]);

	for (i = 0; i < BinCnt; i++)
		delete bn[i];
	for (i = 0; i < AnaCnt; i++)
	{
		delete an[i];
		delete au[i];
	}
}

void Cine::PrintBinSig(CString *psigVal, INT ImNr)	//binary sig values - sample 0 for first image
{
	int BinCnt, spi;
	BYTE BinSig[32]; //max 256 samples (bits) per image

	PhGetCineInfo(mCineHandle, GCI_BINCNT, &BinCnt);
	PhGetCineInfo(mCineHandle, GCI_SAMPLESPERIMAGE, &spi);

	if (BinCnt > 0)
	{
		//Example: read only the first channel binary value, live or recorded
		if (IsLive())
		{
			PhGetCineAuxData(mCineHandle, 0, GAD_BINSIG, ((BinCnt + 7) / 8), BinSig);
			psigVal->Format(L"Live BinCh0: %d", BinSig[0] & 1);
		}
		else
		{
			PhGetCineAuxData(mCineHandle, ImNr, GAD_BINSIG, spi * ((BinCnt + 7) / 8), BinSig);
			psigVal->Format(L"Image: %d BinCh0, Smp0: %d", ImNr, BinSig[0] & 1);

		}
	}
}


void Cine::PrintAnaSig(CString *psigVal, INT ImNr)	//analog sig values - sample 0 for first image
{
	int AnaCnt, spi, IntVal;
	BOOL Bipolar;
	WORD AnaSig[256]; //max 256 samples per image

	PhGetCineInfo(mCineHandle, GCI_ANACNT, &AnaCnt);
	PhGetCineInfo(mCineHandle, GCI_SAMPLESPERIMAGE, &spi);
	PhGetCineInfo(mCineHandle, GCI_ANABIPOLAR, &Bipolar);
	if (AnaCnt > 0)
	{
		//Example read only the first channel analog value, live or recorded
		if (IsLive())
			PhGetCineAuxData(mCineHandle, 0, GAD_ANASIG, AnaCnt * 2, AnaSig);	
		else
			PhGetCineAuxData(mCineHandle, ImNr, GAD_ANASIG, spi * AnaCnt * 2, AnaSig);
	
		if (Bipolar)
			IntVal = (SHORT)AnaSig[0];
		else
			IntVal = AnaSig[0];

		if (IsLive())
			psigVal->Format(L"Live AnaCh0: %d", IntVal);
		else
			psigVal->Format(L"Image: %d AnaCh0, Smp0: %d", ImNr, IntVal);

	}
}


#pragma endregion
