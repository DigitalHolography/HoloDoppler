/*****************************************************************************/
//
//  Copyright (C) 1992-2019 Vision Research Inc. All Rights Reserved.
//
//  The licensed information contained herein is the property of
//  Vision Research Inc., Wayne, NJ, USA  and is subject to change
//  without notice.
//
//  No part of this information may be reproduced, modified or
//  transmitted in any form or by any means, electronic or
//  mechanical, for any purpose, without the express written
//  permission of Vision Research Inc.
//
/*****************************************************************************/

#ifndef __PHFILEINCLUDED__
#define __PHFILEINCLUDED__

#ifdef __cplusplus
extern "C"
{
#endif

#if !defined (_WINDOWS)
//if the platform is not WIN32 define some common
//types from WIN32 that are used below
typedef unsigned char BYTE, *PBYTE;
typedef unsigned short WORD, *PWORD;
typedef int INT, *PINT, LONG, *PLONG, BOOL, *PBOOL;
typedef unsigned int UINT, *PUINT, DWORD, *PDWORD;
typedef float FLOAT, *PFLOAT;
typedef char *PSTR;
typedef void *PVOID;
#define CALLBACK __stdcall
#define WINAPI __stdcall
//replace the cine handle with an int (not a pointer)
//to simplify the Matlab functions call
typedef int CINEHANDLE, *PCINEHANDLE;
#else
//compile for WINDOWS sdk - use the standard definition of HANDLE
#if !defined (CINEHANDLEdefined)
DECLARE_HANDLE(CINEHANDLE);
typedef CINEHANDLE* PCINEHANDLE;
#define CINEHANDLEdefined
#endif
#endif

// Do not define neither _PHFILE_ nor _NOPHFILE_ in your program to allow
// compiler optimization
#if defined(_PHFILE_)
#define EXIMPROC __declspec(dllexport)
#elif !defined(_NOPHFILE_)
#define EXIMPROC __declspec(dllimport)
#else
#define EXIMPROC
#endif

typedef struct tagDIBSAVEOPTIONS
{
    INT FileType;
    UINT QFactor;
} DIBSAVEOPTIONS, *PDIBSAVEOPTIONS;
/*****************************************************************************/

// Info about a write cine file
// in progress operation
typedef struct tagSAVECINEINFO
{
    CINEHANDLE		CH;
    UINT			progressPercent;
}
SAVECINEINFO, *PSAVECINEINFO;
/*****************************************************************************/

// Tone parameters descriptor
typedef struct tagToneDesc
{
	int controlPointsCounter;		// Number of control points (n)
	float controlPoints[32 * 2];	// Control points: x0 y0 x1 y1... x(n-1) y(n-1)
									// All values in [0..1] range
	char label[256];				// Optional string label describing this tone
} TONEDESC, *PTONEDESC;
/*****************************************************************************/

// General color matrix descriptor
typedef struct tagCmDesc
{
	float matrix[9];				// RGB color matrix
	char label[256];				// Color matrix label
} CMDESC, *PCMDESC;
/*****************************************************************************/

// Cine File Codes
#define MIFILE_RAWCINE		0
#define MIFILE_CINE			1
#define MIFILE_JPEGCINE		2
#define MIFILE_AVI			3
#define MIFILE_TIFCINE		4
#define MIFILE_MPEG			5
#define MIFILE_MXFPAL		6
#define MIFILE_MXFNTSC		7
#define MIFILE_QTIME		8
#define MIFILE_MP4			9
/*****************************************************************************/

// Image File Codes
#define SIFILE_WBMP24		(-1)
#define	SIFILE_WBMP8		(-2)
#define SIFILE_WBMP4		(-3)
#define SIFILE_OBMP4		(-4)
#define SIFILE_OBMP8		(-5)
#define SIFILE_OBMP24		(-6)
#define SIFILE_TIF1			(-7)
#define SIFILE_TIF8			(-8)
#define SIFILE_TIF12		(-9)
#define SIFILE_TIF16		(-10)
#define	SIFILE_PCX1			(-11)
#define	SIFILE_PCX8			(-12)
#define SIFILE_PCX24		(-13)
#define SIFILE_TGA8			(-14)
#define SIFILE_TGA16		(-15)
#define	SIFILE_TGA24		(-16)
#define SIFILE_TGA32		(-17)
#define	SIFILE_LEAD			(-18)
#define	SIFILE_LEAD1JFIF	(-19)
#define	SIFILE_LEAD2JFIF	(-20)
#define SIFILE_LEAD1JTIF	(-21)
#define SIFILE_LEAD2JTIF	(-22)
#define SIFILE_JPEG			(-23)
#define SIFILE_JTIF			(-24)
#define	SIFILE_RAW			(-25)
#define SIFILE_DNG			(-26)
#define SIFILE_DPX			(-27)
#define SIFILE_EXR			(-28)
/*****************************************************************************/

// Time Formats
#define TF_LT					(0)			// Local Time
#define TF_UT					(1)			// Universal Time
#define TF_SMPTE				(2)			// SMPTE TimeCode

// Time Format Flags (For PhPrintTime use)
#define PPT_FULL				(0x000)		// Full time
#define PPT_DATE_ONLY			(0x100)		// Date Only
#define PPT_TIME_ONLY			(0x200)		// Time Only
#define PPT_FRAC_ONLY			(0x300)		// Fractions Only
#define PPT_ATTRIB_ONLY			(0x400)		// Attributes Only
/*****************************************************************************/


// Progress indicator
typedef BOOL (WINAPI* PROGRESSCB)(UINT Percent, CINEHANDLE hC);
// Pointer to demosaicing function
typedef void (*DEMOSAICINGFUNCPTR)(PBITMAPINFOHEADER pBMIH, PBYTE pPixel, UINT CFA, UINT Algorithm);
/*****************************************************************************/

#define UC_VIEW									(1)	// Use case - view
#define UC_SAVE									(2) // Use case - save
/*****************************************************************************/

// PhGetCineInfo/ PhSetCineInfo selectors
#define GCI_CFA							0
#define GCI_FRAMERATE					1
#define GCI_EXPOSURE					2
#define GCI_AUTOEXPOSURE				3
#define GCI_REALBPP						4
#define GCI_CAMERASERIAL				5
#define GCI_HEADSERIAL0					6
#define GCI_HEADSERIAL1					7
#define GCI_HEADSERIAL2					8
#define GCI_HEADSERIAL3					9
#define GCI_TRIGTIMESEC					10
#define GCI_TRIGTIMEFR					11
#define GCI_ISFILECINE					12
#define GCI_IS16BPPCINE					13
#define GCI_ISCOLORCINE					14
#define GCI_ISMULTIHEADCINE				15
#define GCI_EXPOSURENS					16
#define GCI_EDREXPOSURENS  			    17
#define GCI_FRAMEDELAYNS				19

#define GCI_FROMFILETYPE				20
#define GCI_COMPRESSION					21
#define GCI_CAMERAVERSION				22
#define GCI_ROTATE						23
#define GCI_IMWIDTH						24
#define GCI_IMHEIGHT					25
#define GCI_IMWIDTHACQ					26
#define GCI_IMHEIGHTACQ					27
#define GCI_POSTTRIGGER					28
#define GCI_IMAGECOUNT					29
#define GCI_TOTALIMAGECOUNT				30
#define GCI_TRIGFRAME					31
#define GCI_AUTOEXPLEVEL				32
#define GCI_AUTOEXPTOP					33
#define GCI_AUTOEXPLEFT					34
#define GCI_AUTOEXPBOTTOM				35
#define GCI_AUTOEXPRIGHT				36
#define GCI_RECORDINGTIMEZONE			37
#define GCI_FIRSTIMAGENO                38
#define GCI_FIRSTMOVIEIMAGE             39
#define GCI_CINENAME					40
#define GCI_TIMEFORMAT					41
#define GCI_MARKIN						42
#define GCI_MARKOUT						43
#define GCI_FROMFILENAME				44
#define GCI_PARTITIONNO					45
#define GCI_GPS							46
#define GCI_UUID						47
#define GCI_RECBPP						48
#define GCI_MAGSERIAL					49
#define GCI_CSSERIAL					50
#define GCI_SENSOR					    51
#define GCI_SENSORMODE				    52

#define GCI_FRPSTEPS					100
#define GCI_FRP1X						101
#define GCI_FRP1Y						102
#define GCI_FRP2X						103
#define GCI_FRP2Y						104
#define GCI_FRP3X						105
#define GCI_FRP3Y						106
#define GCI_FRP4X						107
#define GCI_FRP4Y						108
#define GCI_WRITEERR					109

#define GCI_LENSDESCRIPTION				110
#define GCI_LENSAPERTURE				111
#define GCI_LENSFOCALLENGTH				112

#define GCI_WB							200
#define GCI_WBVIEW						201
#define GCI_WBISMETA					230
#define GCI_BRIGHT						202
#define GCI_CONTRAST					203
#define GCI_GAINR						232
#define GCI_GAING						233
#define GCI_GAINB						234
#define GCI_GAMMA						204
#define GCI_GAMMAR						223
#define GCI_GAMMAB						224
#define GCI_SATURATION					205
#define GCI_HUE							206
#define GCI_FLIPH						207
#define GCI_FLIPV						208
#define GCI_FILTERCODE					209
#define GCI_IMFILTER					210
#define GCI_INTALGO						211
#define GCI_PEDESTALR					212
#define GCI_PEDESTALG					213
#define GCI_PEDESTALB					214
#define GCI_FLARE						225
#define GCI_CHROMA						226
#define GCI_TONE						227
#define GCI_ENABLEMATRICES				228
#define GCI_USERMATRIX					229
#define GCI_CALIBMATRIX					231
#define GCI_RESAMPLEACTIVE				215
#define GCI_RESAMPLEWIDTH				216
#define GCI_RESAMPLEHEIGHT				217
#define GCI_CROPACTIVE					218
#define GCI_CROPRECTANGLE				219
#define GCI_OFFSET16_8					220
#define GCI_GAIN16_8					221
#define GCI_MAXGAIN16_8					242
#define GCI_DEMOSAICINGFUNCPTR			222
#define GCI_WBTEMPERATURE				235
#define GCI_WBCOLCOMP					236
#define GCI_OPTICALFILTER				237
#define GCI_CALIBINFO					238
#define GCI_GAMMARCH					239
#define GCI_GAMMAGCH					240
#define GCI_GAMMABCH					241
#define GCI_SUPPORTSTOE					243
#define GCI_TOE							244
#define GCI_SUPPORTSLOGMODE				245
#define GCI_LOGMODE						246
#define GCI_EI							250
#define GCI_CAMERAMODEL					251
//										252

#define GCI_VFLIPVIEWACTIVE				300

#define GCI_MAXIMGSIZE					400

#define GCI_FRPIMGNOARRAY				450
#define GCI_FRPRATEARRAY				451
#define GCI_FRPSHAPEARRAY				452

#define GCI_TRIGTC						470
#define GCI_TRIGTCU						471
#define GCI_PBRATE						472
#define GCI_TCRATE						473

#define GCI_DFRAMERATE					480

#define GCI_SAVERANGE					500
#define GCI_SAVEFILENAME				501
#define GCI_SAVEFILETYPE				502
#define GCI_SAVE16BIT					503
#define GCI_SAVEPACKED					504
#define GCI_SAVEXML						505
#define GCI_SAVESTAMPTIME				506
#define GCI_SAVEDECIMATION				1035

#define GCI_SAVEAVIFRAMERATE			520
#define GCI_SAVEAVICOMPRESSORLIST		521
#define GCI_SAVEAVICOMPRESSORINDEX		522

#define GCI_SAVEDPXLSB					530
#define GCI_SAVEDPXTO10BPS				531
#define GCI_SAVEDPXDATAPACKING			532
#define GCI_SAVEDPX10BITLOG				533
#define GCI_SAVEDPXEXPORTLOGLUT			534
#define GCI_SAVEDPX10BITLOGREFWHITE		535
#define GCI_SAVEDPX10BITLOGREFBLACK		536
#define GCI_SAVEDPX10BITLOGGAMMA		537
#define GCI_SAVEDPX10BITLOGFILMGAMMA	538

#define GCI_SAVEQTPLAYBACKRATE			550

#define GCI_SAVECCIQUALITY				560

#define GCI_UNCALIBRATEDIMAGE			600
#define GCI_NOPROCESSING				601
#define GCI_BADPIXELREPAIR				602

#define GCI_CINEDESCRIPTION				603


//Range data information
//======================
#define GCI_RDTYPESCNT					700

//Range data, for PhGetCineInfo1()  PhSetCineInfo1()
#define GCI_RDNAME						701


/*****************************************************************************/

#define MAXCOMPRCNT						64		// Maximum compressor count
/*****************************************************************************/

// Create/destroy a CINEHANDLE
EXIMPROC HRESULT PhNewCineFromFile(PSTR szFN, PCINEHANDLE phC);
EXIMPROC HRESULT PhNewCineFromCamera(INT CN, INT CineNr, PCINEHANDLE phC);
EXIMPROC HRESULT PhGetCineLive(INT CN, PCINEHANDLE phC);
EXIMPROC HRESULT PhDestroyCine(CINEHANDLE hC);
EXIMPROC HRESULT PhDuplicateCine(PCINEHANDLE phCDest, CINEHANDLE hCSrc);
/*****************************************************************************/

// Get cine images
EXIMPROC HRESULT PhGetCineImage(CINEHANDLE hC, PIMRANGE pRng, PBYTE pPixel, UINT BufferSize, PIH pIH);
/*****************************************************************************/

// Cine use case
EXIMPROC HRESULT PhSetUseCase(CINEHANDLE hC, INT CineUseCaseID);
EXIMPROC HRESULT PhGetUseCase(CINEHANDLE hC, PINT pCineUseCaseID);
/*****************************************************************************/

// Cine get/set
EXIMPROC HRESULT PhGetCineInfo(CINEHANDLE hC, UINT Selector, PVOID pVal);
EXIMPROC HRESULT PhSetCineInfo(CINEHANDLE hC, UINT Selector, PVOID pVal);
EXIMPROC HRESULT PhGetCineInfo1(CINEHANDLE hC, UINT Selector, UINT Sel1, PVOID pVal);
EXIMPROC HRESULT PhSetCineInfo1(CINEHANDLE hC, UINT Selector, UINT Sel1, PVOID pVal);
/*****************************************************************************/

// Write cine to file
EXIMPROC HRESULT PhWriteCineFile(CINEHANDLE hC, PROGRESSCB pfnCallback);
EXIMPROC HRESULT PhWriteCineFileAsync(CINEHANDLE hC, PROGRESSCB pfnCallback);
EXIMPROC HRESULT PhGetWriteCineFileProgress(CINEHANDLE hC, PUINT pProgressPercent);
EXIMPROC HRESULT PhStopWriteCineFileAsync(CINEHANDLE hC);
EXIMPROC HRESULT PhGetWriteCineFileProgressAll(PSAVECINEINFO pSaveCineInfo, PUINT pCount);
/*****************************************************************************/

// User interface functions
EXIMPROC BOOL PhGetOpenCineName(PSTR szFileName, UINT Options);
EXIMPROC BOOL PhGetSaveCineName(CINEHANDLE hC);
EXIMPROC BOOL PhGetSaveCinePath(CINEHANDLE hC);
/*****************************************************************************/

// Get auxiliary data
EXIMPROC HRESULT PhGetCineAuxData(CINEHANDLE hC, INT ImageNumber, UINT SelectionCode, UINT DataSize, PVOID pData);
// Get cine image time
EXIMPROC HRESULT PhPrintTime(CINEHANDLE hC, INT ImNo, UINT Options, PSTR szTime);
// Auto white balance
EXIMPROC HRESULT PhMeasureCineWB(CINEHANDLE hC, PPOINT pP, int SquareSide, PIMRANGE pRng, PWBGAIN pWB, PUINT pSatCnt);
/*****************************************************************************/

// PhFile Error Codes
// Warnings
#define ERR_8BitDestinationCine			( 2000)
#define ERR_VoidRange					( 2001)
#define ERR_ReducedRange				( 2002)
#define ERR_Seeking						( 2003)
#define ERR_UserAbort					( 2004)
#define ERR_FreeLibrary			    	( 2005)
#define	ERR_LeadToolsNotFound			( 2006)
#define	ERR_EVSNotFound					( 2007)
#define ERR_BadResampleParam			( 2008)
#define ERR_BadCropParam				( 2009)
#define ERR_SearchedImageNotFound		( 2010)
#define ERR_FileFormatNotMatched		( 2011)

// Errors
#define ERR_BadCine						(-2000)
#define ERR_UnsupportedFormat			(-2002)
#define ERR_InsufficientAlloc			(-2003)
#define ERR_NotInRange					(-2004)
#define ERR_SaveAvi						(-2005)
#define ERR_Encoder						(-2006)
#define ERR_UnsupportedTiffFormat		(-2007)
#define ERR_SplitQuartersUnsupported	(-2009)
#define ERR_NotACineFile				(-2010)

#define ERR_FileOpen					(-2012)
#define ERR_FileRead					(-2013)
#define ERR_FileWrite					(-2014)
#define ERR_FileSeek					(-2015)
#define ERR_DecompressImage				(-2016)
#define ERR_CineVerNewer				(-2017)
#define ERR_NotSupported				(-2018)
#define ERR_FileInUse					(-2019)

#define ERR_CannotBuildGraph			(-2021)
#define ERR_AuxDataNotFound				(-2023)
#define ERR_NotEnoughMemory				(-2024)
#define ERR_MpegReaderNotFound			(-2025)

#define ERR_FunctionNotFound			(-2028)
#define ERR_CineInUse					(-2029)
#define ERR_SaveCineBufferFull			(-2030)
#define ERR_NoCineSaveInProgress		(-2031)
#define ERR_cfls                        (-2032)
#define ERR_cfread                      (-2033)
#define ERR_cfrm                        (-2034)

#define ERR_ANNOTATION_TOO_BIG			(-2040)

/*****************************************************************************/

///////////////////////////////////////////////////////////////////////////////
//								DEPRECATED									 //
///////////////////////////////////////////////////////////////////////////////

//options
#define OFN_MULTISELECT					1

#define SFH_HEAD0						1
#define SFH_HEAD1						2
#define SFH_HEAD2						4
#define SFH_HEAD3						8
#define SFH_ALLHEADS					0
/*****************************************************************************/

// Start / Stop functions to be called before and after calling PhFile functions,
// only if PhCon/PhRegisterClientEx  and  PhCon/PhUnRegisterClient are not called
EXIMPROC HRESULT PhStartPhFile(void);
EXIMPROC HRESULT PhStopPhFile(void);
/*****************************************************************************/

EXIMPROC HRESULT PhReadCineFileImage(CINEHANDLE hC, INT ImageNumber, PBYTE pPixel);
EXIMPROC HRESULT PhReadCineProcessedImage(CINEHANDLE hC, INT ImageNumber, PBYTE pPixel);
EXIMPROC HRESULT PhGetCineProcessedBMIH(CINEHANDLE hC, PBITMAPINFOHEADER pBMIH);
EXIMPROC HRESULT PhIsColorCine(CINEHANDLE hC, PBOOL IsColorCine);
EXIMPROC HRESULT PhGetCineTriggerTime(CINEHANDLE hC, PTIME64 pTriggerTime);
/*****************************************************************************/

// Image I/O functions
EXIMPROC BOOL PhGetOpenImageName(PSTR szFileName, UINT Options);
EXIMPROC BOOL PhGetSaveImageName(PSTR szFileName, PDIBSAVEOPTIONS pSaveOptions);
EXIMPROC HRESULT PhReadCineImage(CINEHANDLE hC, INT ImageNumber, INT Options, PBYTE pPixel);
EXIMPROC HRESULT PhWriteImageFile(PSTR szFN, PBYTE pDib, DIBSAVEOPTIONS SaveOptions);
EXIMPROC HRESULT PhGetDIBSize(PSTR szFN, PUINT pDibSize);
EXIMPROC HRESULT PhReadImageFile(PSTR szFN, PBYTE pDIB);
/*****************************************************************************/

EXIMPROC HRESULT PhGetCineBMIH(CINEHANDLE hC, PBITMAPINFOHEADER pBMIH);
EXIMPROC HRESULT PhGetCineRange(CINEHANDLE hC, PINT pFirstIm, PINT pLastIm);
EXIMPROC HRESULT PhSetCineSaveRange(CINEHANDLE hC, INT FirstIm, INT LastIm);
EXIMPROC HRESULT PhGetCineSaveRange(CINEHANDLE hC, PINT pFirstIm, PINT pLastIm);
EXIMPROC HRESULT PhSetCineSaveOptions(CINEHANDLE hC, PSTR szFileName, INT FileTypeIndex, UINT StampTime, UINT CCIQuality);
/*****************************************************************************/

EXIMPROC HRESULT PhSetCineProcessing(CINEHANDLE hC, PIMPROCOPTIONS pImOpt);
EXIMPROC HRESULT PhGetCineProcessing(CINEHANDLE hC, PIMPROCOPTIONS pImOpt);
EXIMPROC HRESULT PhSaveFromHeads(CINEHANDLE hC, UINT HeadSaveOptions);
EXIMPROC HRESULT PhEnableCineColor(CINEHANDLE hC, BOOL bEnableColor);
EXIMPROC HRESULT PhEnableCine16Bpp(CINEHANDLE hC, BOOL bEnable16Bpp);
/*****************************************************************************/

#define ERR_BADCINE						ERR_BadCine
#define ERR_NOCINE						ERR_NoCine
#define ERR_UNSUPPORTEDFORMAT			ERR_UnsupportedFormat
#define ERR_INSUFFICIENTALLOC			ERR_InsufficientAlloc
#define ERR_NOTINRANGE					ERR_NotInRange
#define ERR_SAVEAVI						ERR_SaveAvi
#define ERR_ENCODER						ERR_Encoder

#undef EXIMPROC     //avoid conflicts with other similar headers
#ifdef __cplusplus
}
#endif
#endif