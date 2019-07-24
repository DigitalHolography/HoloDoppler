/*****************************************************************************/
//                                                                   
//  Copyright (C) 1992-2017 Vision Research Inc. All Rights Reserved.
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


// Control library for the Phantom High Speed Camera
// PhCon.h (public structures, constants and functions)

#ifndef __PHCONINCLUDED__
#define __PHCONINCLUDED__

#ifdef __cplusplus
extern "C"
{
#endif

// Do not define neither _PHCON_ nor _NOPHCON_ in your program to allow
// compiler optimization
#if defined(_PHCON_)
#define EXIMPROC __declspec(dllexport)
#elif !defined(_NOPHCON_)
#define EXIMPROC __declspec(dllimport)
#else
#define EXIMPROC
#endif


#if !defined(_WINDOWS)
// If the platform is not WINDOWS sdk define some common
// types from WIN32 that are used below
typedef unsigned char BYTE, *PBYTE;
typedef unsigned short WORD, *PWORD;
typedef int INT, *PINT, LONG, *PLONG, BOOL, *PBOOL;
typedef unsigned int UINT, *PUINT, DWORD, *PDWORD;
typedef float FLOAT, *PFLOAT;
typedef char *PSTR;
typedef void *PVOID;
#define CALLBACK __stdcall
#define WINAPI __stdcall

//MATLAB ADD START ------------------------------------------------------------------------
typedef int HRESULT;
typedef unsigned int UINT32, *PUINT32;
typedef char CHAR, *PCHAR;
#define DECLARE_HANDLE(name) struct name##__ { int unused; }; typedef struct name##__ *name
#define MAX_PATH          260

DECLARE_HANDLE            (HWND);

typedef struct tagPOINT
{
    LONG  x;
    LONG  y;
} POINT, *PPOINT;

typedef struct tagRECT {
    LONG    left;
    LONG    top;
    LONG    right;
    LONG    bottom;
} RECT, *PRECT;
//MATLAB ADD END --------------------------------------------------------------------------

typedef struct tagBITMAPINFOHEADER
{
    DWORD      biSize;
    LONG       biWidth;
    LONG       biHeight;
    WORD       biPlanes;
    WORD       biBitCount;
    DWORD      biCompression;
    DWORD      biSizeImage;
    LONG       biXPelsPerMeter;
    LONG       biYPelsPerMeter;
    DWORD      biClrUsed;
    DWORD      biClrImportant;
} BITMAPINFOHEADER, *PBITMAPINFOHEADER;
typedef struct tagRGBQUAD
{
    BYTE    rgbBlue;
    BYTE    rgbGreen;
    BYTE    rgbRed;
    BYTE    rgbReserved;
} RGBQUAD;
typedef struct tagBITMAPINFO
{
    BITMAPINFOHEADER    bmiHeader;
    //RGBQUAD             bmiColors[1]; (changed to be compatible with MATLAB calllib)
	BYTE             bmiColors[4*256];
} BITMAPINFO, *PBITMAPINFO;
#endif


#if !defined(_TIMEDEFINED_)
#define _TIMEDEFINED_

// A format for small intervals of time: [250 picosecond ... 1 second)
// It is fixed point 0.32 or, with other words, the time in seconds is
// stored multiplied by 4Gig i.e.  4294967296.0 and rounded to int.
typedef UINT32 FRACTIONS, *PFRACTIONS;
/*****************************************************************************/


// The absolute time format used in PC software is TIME64
typedef struct tagTIME64	// A compact format for time 64 bits
							// fixed point (32.32 seconds)
{
    FRACTIONS fractions;	// Fractions of seconds  (resolution 1/4Gig i.e.  cca. 1/4 ns)
							// The fractions of the second are stored here multiplied by 2**32
							// Least significant 2 bits store info about IRIG synchronization
							// bit0 = 0 IRIG synchronized
							// bit0 = 1 not synchronized
							// bit1 = 0 Event input=0 (short to ground)
							// bit1 = 1 Event input=1 (open)
    UINT32 seconds;			// Seconds from Jan 1 1970, compatible with the C library routines
							// (max year: 2038 signed, 2106 unsigned)
							// VS2005 changed the default time_t to 64 bits; here we have to
							// maintain the 32 bits size to remain compatible with the stored
							// file format and the public interfaces
} TIME64, *PTIME64;
/*****************************************************************************/


// Time code according to the standard SMPTE 12M-1999
typedef struct tagTC
{
/*
	Redefined the this part of structure for MATLAB use
	unsigned char framesU:4;		// Units of frames
	unsigned char framesT:2;		// Tens of frames
	unsigned char dropFrameFlag:1;	// Dropframe flag
	unsigned char colorFrameFlag:1;	// Colorframe flag
	unsigned char secondsU:4;		// Units of seconds
	unsigned char secondsT:3;		// Tens of seconds
	unsigned char flag1:1;			// Flag 1
	unsigned char minutesU:4;		// Units of minutes
	unsigned char minutesT:3;		// Tens of minutes
	unsigned char flag2:1;			// Flag 2
	unsigned char hoursU:4;			// Units of hours
	unsigned char hoursT:2;			// Tens of hours
	unsigned char flag3:1;			// Flag 3
	unsigned char flag4:1;			// Flag 4
*/
    unsigned char frames;        	
    unsigned char seconds;       	
    unsigned char minutes;       	
    unsigned char hours;
	
	UINT userBitData;				// 32 user bits
}TC, *PTC;
/*****************************************************************************/


// Unpacked representation of SMPTE 12M-1999 Time Code
typedef struct tagTCU
{
	UINT frames;					// Frames
	UINT seconds;					// Seconds
	UINT minutes;					// Minutes
	UINT hours;						// Hours
	BOOL dropFrameFlag;				// Dropframe flag
	BOOL colorFrameFlag;			// Colorframe flag
	BOOL flag1;						// Flag 1
	BOOL flag2;						// Flag 2
	BOOL flag3;						// Flag 3
	BOOL flag4;						// Flag 4
	UINT userBitData;				// 32 user bits
}TCU, *PTCU;
/*****************************************************************************/
#endif


#if !defined(_WBGAIN_)
#define _WBGAIN_
// Color channels adjustment
// intended for the White balance adjustment on color camera
// by changing the gains of the red and blue channels
typedef struct tagWBGAIN
{
    float R;				// White balance, gain correction for red
    float B;				// White balance, gain correction for blue
}
WBGAIN, *PWBGAIN;
/*****************************************************************************/
#endif


// ACQUIPARAMS is the set of control parameters for the camera - upgrade-able
typedef struct tagACQUIPARAMS
{
    UINT ImWidth;			// Image dimensions
    UINT ImHeight;

    UINT FrameRateInt;		// Frame rate (frames per second, integer) changed name  
							// Obsolete: Not to be used anymore. Replaced it in applications by dFrameRate (frames per second, double)
							// Try to provide here rounded dFrameRate, for compatibility with older version of applications
    UINT Exposure;			// Exposure duration (nanoseconds)
    UINT EDRExposure;		// EDR (extended dynamic range) exposure duration (nanoseconds)
    UINT ImDelay;			// Image delay for the SyncImaging mode (nanoseconds)
							// (not available in all models)
    UINT PTFrames;          // Count of frames to be recorded after the trigger
    UINT ImCount;           // Count of images in this cine (read only field)

    UINT SyncImaging;       // Sync imaging mode: acquire when an external clock rise
							// changed to UINT: possible values SYNC_INTERNAL,
							// SYNC_EXTERNAL, SYNC_LOCKTOIRIG, SYNC_LOCKTOVIDEO, SYNC_SYNCTOTRIGGER
	UINT AutoExposure;      // Control of the exposure duration from the subject light
							// bit0			0		- disable AUTOEXP
							//				1		- enable AUTOEXP
							// bit 1		0		- lock at trigger
							//				1		- active after trigger
							//						Always 0 for cameras using V2 autoexp
							//						Read only for cameras using V2 autoexp
							// bit3bit2		Cameras using V1 autoexp
							//				00		- for all cameras using V1 autoexp
							//				Cameras using V2 autoexp
							//				01		- average
							//				10		- spot
							//				11		- center weighted
    UINT AutoExpLevel;      // Level for autoexposure control
    UINT AutoExpSpeed;      // Speed for autoexposure control
    RECT AutoExpRect;       // Rectangle for autoexposure control

    BOOL Recorded;          // The cine was recorded and is available for playback
							// TriggerTime, RecordedCount, ImCount, FirstIm are
							// valid and final   (read only field)
    TIME64 TriggerTime;     // Trigger time for the recorded cine (read only field)

    UINT RecordedCount;     // initially recorded count; ImCount may be smaller
							// if the cine was partially saved to flash
							// memory (read-only field)
    INT FirstIm;            // First image number of this cine; may be different
							// from PTFrames-ImCount if the cine was partially
							// saved to Non-Volatile memory (read-only field)

    //Frame rate profile
    UINT FRPSteps;          // Supplementary steps in frame rate profile
							// 0 means no frame rate profile
    INT FRPImgNr[16];       // Image number where to change the rate and/or exposure
							// allocated for 16 points (4 available in v7)
    UINT FRPRate[16];       // new value for frame rate (fps)
    UINT FRPExp[16];        // new value for exposure (nanoseconds)
							// The acquisition parameters used before FRPImgNr[0] are the
							// pretrigger parameters from the above fields FrameRate, Exposure

    UINT Decimation;        // Reduce the frame rate when sending the images to i3 through fiber
    UINT BitDepth;          // Bit depth of the cines (read-only field) - usefull for flash; the
							// images from flash have to be requested at the real bit depth.
							// The images from RAM can be requested at different bit depth

    UINT CamGainRed;        // Gains attached to a cine saved in the magazine
    UINT CamGainGreen;      // Normally they tell the White balance at recording time
    UINT CamGainBlue;
    UINT CamGain;           // global gain
    BOOL ShutterOff;        // go to max exposure for piv mode

    UINT CFA;               // Color Filter Array at the recording of the cine
    char CineName[256];     // cine name
    char Description[4096]; // Cine description on max 4095 chars

    UINT FRPShape[16];      // 0: flat,  1 ramp
	
	double dFrameRate;      // Overrides older FrameRate (renamed FrameRateInt)

    // VRI internal note: Size checked structure.
	// Update oldcomp.c if new fields are added  
} ACQUIPARAMS, *PACQUIPARAMS;
/*****************************************************************************/


typedef struct tagIMRANGE
{
    INT First;				//first image number
    UINT Cnt;				//count of images
} IMRANGE, *PIMRANGE;
/*****************************************************************************/


// General settigs of the camera - upgradeable
typedef struct tagCAMERAOPTIONS
{
    // Phantom v4-v6
    // Analog video output
    UINT OSD;               // enable the On Screen Display
    UINT VideoSystem;       // Analog video output system
							// IRIG
    BOOL ModulatedIRIG;     // IRIG input accept modulated signal


    // Fields below are used starting with Phantom v7
    // Trigger
    BOOL RisingEdge;        // TRUE rising, FALSE falling
    UINT FilterTime;        // time constant
    //Memory gate input meaning
    BOOL MemGate;           // TRUE: Memgate, FALSE: pretrigger
    BOOL StartInRec;        // TRUE: Start in recording
							// FALSE:start in preview wait
							//       pretrigger to start the recording
    BOOL Color;             // create color video signal
    BOOL TestImage;         // replace the FBM image by a test image (colored bars)
    //OnScreenDisplay colors
	//RGBQUAD OSDColor[8];  (changed to be compatible with MATLAB calllib)
    BYTE OSDColor[4*8];     // set of colors used for the OSD painting
							// Background
							// Wtr mode
							// Trig mode
							// Cst mode
							// Pre-trig mode
							// Id fields
							// Acqui fields
							// Status, cine

    BOOL OSDOpaque;         // OSD test is opaque or transparent
    int OSDLeft;            // limits of the OSD text on screen
    int OSDTop;
    int OSDBottom;
    int ImageX;             // image position on screen
    int ImageY;


    // End of recording automation on Ethernet cameras
    BOOL AutoSaveNVM;       // save the cine to the nvm
    BOOL AutoSaveFile;      // save the cine to a file
    BOOL AutoPlay;          // playback to video
    BOOL AutoCapture;       // restart capture
    CHAR FileName[MAX_PATH];// filename to save (as seen from camera)
    IMRANGE SaveRng;        // image range for the above operations

    BOOL LongReady;         // If FALSE the Ready signal is 1 from the start
							// of recording until the cine is triggered
							// If TRUE the Ready is 1 from the start
							// to the end of recording
    BOOL RealTimeOutput;    // Enable the sending of the acquired image on fiber
    UINT RangeData;         // 0: none, otherwise the size in bytes per image of the range data
							// implemented only 16 bytes

    //external memory slice
    UINT SourceCamSer;      // Source camera serial
    UINT SliceNr;           // slice number (0, 1, 2 ....)
    UINT SliceCnt;          // total count of slices connected to a certain camera
    BOOL FRPi3Trig;         // Frame rate profile start at i3 trigger
    UINT UT;                // OSD: Display time as: 0 LocalTime,  1: Universal Time (GMT)

    int AutoSaveFormat;     // save to flash or direct save to file from camera
							// -8 -16 =  save 8 bit or 16 bits

    UINT SourceCamVer;      // Source camera version (external memory slice)
    UINT RAMBitDepth;       // Set the current bit depth for pixel storage in the camera video RAM
    int VideoTone;          // tone curve to select for video
    int VideoZoom;          // Zoom of the video image: 0: Fit,  1: Zoom1
    int FormatWidth;        // Format rectangle to overlap on the video image
    int FormatHeight;

    UINT AutoPlayCnt;       // repeat count for the playback to video
    UINT OSDDisable;        // selective disable of the analog and digital OSD
    BOOL RecToMag;          // Record to the flash magazine

    BOOL IrigOut;           // Change the Strobe pin to Irig Out at Miro cameras (if TRUE)
							// For the new miros: it holds a numerical value identifying
							// aux signal function. Check AUXSIG_ symbols or
							// PhGet gsSupportedAuxSignalFunctions selector for possible values.

	int FormatXOffset;		// x offset for the format rectangle to overlap on the video image
	int FormatYOffset;		// y offset for the format rectangle to overlap on the video image

    //VRI internal note: Size checked structure. Update oldcomp.c if new fields are added    
} CAMERAOPTIONS, *PCAMERAOPTIONS;
/*****************************************************************************/


typedef struct tagCINESTATUS
{
    BOOL Stored;			// Recording of this cine finished
    BOOL Active;			// Acquisition is currently taking place in this cine
    BOOL Triggered;			// The cine has received a trigger
} CINESTATUS, *PCINESTATUS;
/*****************************************************************************/


// PhGetAllIpCameras
typedef struct tagCAMERAID
{
    UINT IP;				// only v4 IP, for v6 to be extended to int64
    UINT Serial;			
    char Name[256];			//Name remained 15 chars in the camera interface for compatibility with the past
    char Model[200];		//Model name is a few chars too (maximum now: 18 chars "Phantom Miro M3a10")
	BYTE reserved[44];
	UINT MaxCineCnt;		//max partition count
	UINT CFA;				//Reserved space for Model was reduced to include other info  
	UINT CamVer;			//(needed to simulate absent cameras from visible list)							
} CAMERAID, *PCAMERAID;
/*****************************************************************************/


// int array descriptor
typedef struct tagIArrayDesc
{
	UINT cnt;		// number of elements in a
	INT a[256];		// int array
} IARRAYDESC, *PIARRAYDESC;
/*****************************************************************************/

//Pulse Processor parameters  (for ProgIO)
typedef struct tagPulseParam
{
	UINT Size;		//for versioning in future if needed
	BOOL Invert;	//Invert signal at output
	BOOL Falling;	//Negative fixed width pulse triggered by falling input
	double Delay;	//Delay from input edges to output edges
	double Width;	//If not 0 will create a fixed width pulse
	double Filter;	//Change status of the output after the input was 
					//in the new status for the specified interval of time
}PULSEPARAM, *PPULSEPARAM;




// Constants area (has to be converted before being imported in MATLAB)
// Include here simple numerical substitutions that will be converted to VAR = value in the MATLAB compatible constants file
// MATLABconstants start


#define PHCONHEADERVERSION 770      // Call PhRegisterClientEx(...,PHCONHEADERVERSION) using this value
								    // has to be changed only here; it is the third component of the Phantom files version
/*****************************************************************************/


#define MAXCAMERACNT		63		//maximum count of cameras 
#define MAXERRMESS			256		// maximum size of error messages for PhGetErrorMessage function
#define MAXIPSTRSZ			16		// Maximum IP string length
/*****************************************************************************/


// Predefined cines
#define CINE_DEFAULT		-2		// The number of the default cine
#define CINE_CURRENT		-1		// The cine number used to request live images
#define CINE_PREVIEW		0		// The number of the preview cine
#define CINE_FIRST			1		// The number of the first cine when emulating 
									// a single cine camera 
/*****************************************************************************/

// Selection codes in the functions PhGet(),  PhSet()
// 1. Camera current status information
#define gsHasMechanicalShutter								1025
#define gsHasBlackLevel4									1027
#define gsHasCardFlash										1051
#define gsHas10G											2000
#define gsHasV2AutoExposure									2001
// Continue numbering gsHas... beginning with  next value!
/*****************************************************************************/


// 2. Capabilities
#define gsSupportsInternalBlackRef							1026
#define gsSupportsImageTrig									1040
#define gsSupportsCardFlash									1050
#define gsSupportsMagazine									8193
#define gsSupportsHQMode									8194
#define gsSupportsGenlock									8195
#define gsSupportsEDR										8196
#define gsSupportsAutoExposure								8197
#define gsSupportsTurbo										8198
#define gsSupportsBurstMode									8199
#define gsSupportsShutterOff								8200
#define gsSupportsDualSDIOutput								8201
#define gsSupportsRecordingCines							8202
#define gsSupportsV444										8203
#define gsSupportsInterlacedSensor							8204
#define gsSupportsRampFRP									8205
#define gsSupportsOffGainCorrections						8206
#define gsSupportsFRP										8207
#define gsSupportedVideoSystems								8208
#define gsSupportsRemovableSSD								8209
#define gsSupportedAuxSignalFunctions						8210
#define gsSupportsGps										8211
#define gsSupportsVideoSync									8212
#define gsSupportsTimeCodeOutSignal							8213
#define gsSupportsQuietMode									8214
#define gsSupportsPreTriggerMemGate							8215
#define gsSupportsV4K										8216
#define gsSupportsAnamorphicDesqRatio						8217
#define gsSupportsAudio										8218
#define gsSupportsProRes									8219
#define gsSupportsV3G										8220
#define gsSupportsProgIO									8221		// ro camera has Programmable IO
#define gsSupportsSyncToTrigger								8222
#define gsSupportsSensorModes							    8223        // ro used for Sensor Mode; currently used for Flex 4K GS, VEO 4K and Virgo V2040
#define gsSupportsBattery                                   8224        // ro used for new Battery Logic V2.1 (2016)
#define gsSupportsExpIndex                                  8225        
#define gsSupportsHvTrigger                                 8226        

// Continue numbering gsSupports... beginning with next value!
/*****************************************************************************/


// 3. Camera current parameters
#define gsSensorTemperature									1028
#define gsCameraTemperature									1029
#define gsThermoElectricPower								1030
#define gsSensorTemperatureThreshold						1031
#define gsCameraTemperatureThreshold						1032

#define gsVideoPlayCine										1033
#define gsVideoPlaySpeed									1034
#define gsVideoOutputConfig									1035

#define gsMechanicalShutter									1036

#define gsImageTrigThreshold								1041
#define gsImageTrigAreaPercentage							1042
#define gsImageTrigSpeed									1043
#define gsImageTrigMode										1044
#define gsImageTrigRect										1045

#define gsAutoProgress										1046
#define gsAutoBlackRef										1047

#define gsCardFlashSizeK									1052
#define gsCardFlashFreeK									1053
#define gsCardFlashError									1054

#define gsIPAddress											1070
#define gsEthernetAddress									1055
#define gsEthernetMask										1056
#define gsEthernetBroadcast									1057
#define gsEthernetGateway									1058

#define gsLensFocus											1059
#define gsLensAperture										1060
#define gsLensApertureRange									1061
#define gsLensDescription									1062
#define gsLensFocusInProgress								1063
#define gsLensFocusAtLimit									1064

#define gsGenlock											1065
#define gsGenlockStatus										1066

#define gsTurboMode											1068
#define gsModel												1069

#define gsMaxPartitionCount									1071
#define gsAuxSignal											1072
#define gsTimeCodeOutSignal									1073
#define gsQuiet												1074
#define gsBaseEI											1075
#define gsVFMode											1076
#define gsAnamorphicDesqRatio								1077

#define gsAudioEnable										1078

#define gsClockPeriod 										1079		//ro   obtain the camera clock period as a double value (seconds)
#define gsPortCount											1080		//ro   how many ports (fixed + programmable)

#define gsTriggerEdgeAndVoltage								1081		//rw   bit 0 rising edge, bit 1 high voltage (6v threshold instead of 1.5v)
#define gsTriggerFilter										1082		//rw   filter constant (double, seconds)
#define gsTriggerDelay										1083		//rw   trigger delay (double, seconds)   /   available at cameras with ProgIO

#define gsHeadSerial										1085		//ro   Nano Head serial Number   /   available for Nano Cameras
#define gsHeadTemperature									1086		//ro   Nano Head FPGA Temperature and Sensor temperature
#define gsSensorModesList                                   1087        //ro   Get list of camera Sensor modes; currently used for Flex 4K GS, VEO 4K and Virgo V2040
#define gsSensorMode                                        1088        //rw   Get/Set Sensor Mode; currently used for Flex 4K GS, VEO 4K and Virgo V2040

#define gsExpIndex                                          1090        //rw   Exposure Index control
#define gsExpIndexPresets                                   1091        //ro   Get Exposure Index ISO Table

#define gsBatteryEnable                                     1100        //rw   Enable/Disable battery operation
#define gsBatteryCaptureEnable                              1101        //rw   Enable/Disable battery operation during capture
#define gsBatteryPreviewEnable                              1102        //rw   Enable/Disable battery operation during preview
#define gsBatteryWtrRuntime                                 1103        //rw   (cam.wtrruntime) Time in seconds the camera will run on battery in WTR if a cine is not triggered.
#define gsBatteryVoltage                                    1104        //ro   (info.vbatt) Battery voltage level 
#define gsBatteryState                                      1105        //ro   (info.battstatus) Battery control status
#define gsBatteryMode                                       1106        //rw   (cam.battmode) Used for disabling charging or discharging of the battery.
#define gsBatteryArmDelay                                   1107        //rw   (cam.armdelay) Delay, in seconds, from the moment the camera is placed into WTR and the time the battery is armed.
#define gsBatteryPrevRuntime                                1108        //rw   (cam.prvruntime) Time in seconds the camera will run on battery in preview if a cine is not triggered.
#define gsBatteryPwrOffDelay                                1109        //rw   (cam.poffdelay) Time in seconds the battery still supplies power to the camera after it has been disarmed.
#define gsBatteryReadyGate                                  1110        //rw   (cam.readygate) Set/Get Battery readygate control

//Configure Aux1, Aux2, Aux3 signals for Miro M cameras, where available
//(see gsSupportedAuxXSignalFunctions)
//The type returned by these selectors is int
#define gsAux1Signal										3008		//rw what signal is available now at Aux1 pin
#define gsAux2Signal										3009        //rw what signal is available now at Aux2 pin
#define gsAux3Signal										3010        //rw what signal is available now at Aux3 pin

//Capabilities (signal supported) for Aux1, Aux2, Aux3 pins where available 
//The type returned by these selectors is IARRAYDESC
#define gsSupportedAux1SignalFunctions						9020		//ro what signals can be set to Aux1 pin 
                                                                        //   AUX1SIG_STROBE, AUX1SIG_EVENT, AUX1SIG_MEMGATE, AUX1SIG_FSYNC
#define gsSupportedAux2SignalFunctions						9021        //ro what signals can be set to Aux2 pin 
                                                                        //   AUX2SIG_READY, AUX2SIG_STROBE, AUX2SIG_AES_EBU_OUT
#define gsSupportedAux3SignalFunctions						9022        //ro what signals can be set to Aux3 pin 
                                                                        //   AUX3SIG_IRIGOUT, AUX3SIG_STROBE

                                                                        
// Continue numbering gs... beginning with next value!
/*****************************************************************************/

//Selection codes for PhSet1(), PhGet1() with one supplimentary selector

#define gsSigCount 											10001		//ro   signal count available at the port
#define gsSigSelect											10002		//rw   select the signal to connect to a certain port
#define gsPulseProc											10003		//rw   parameters for pulse processor (in a structure)
#define gsHasPulseProc										10004		//ro   this port has pulse processor

	
// Continue numbering gs... beginning with next value!
/*****************************************************************************/

//Selection codes for PhSet2(), PhGet2() with two supplimentary selectors
#define gsSigNameFmw										20001		//ro  signal name from Firmware, given the port number and signal number
#define gsSigName											20002		//ro  Translated "pretty" signal name, given the port number and signal number

// Continue numbering gs... beginning with next value!
/*****************************************************************************/




// Selection codes in the functions PhCineGet(), PhCineSet()
#define cgsVideoTone									4097

#define cgsName											4098

#define cgsVideoMarkIn									4099
#define cgsVideoMarkOut									4100

#define cgsIsRecorded                                   4101
#define cgsHqMode                                       4102

#define cgsBurstCount									4103
#define cgsBurstPeriod									4104

#define cgsLensDescription								4105
#define cgsLensAperture									4106
#define cgsLensFocalLength								4107

#define cgsShutterOff									4108

#define cgsTriggerTime									4109

#define cgsTrigTC										4110
#define cgsPbRate										4111
#define cgsTcRate										4112
#define cgsGps											4113
#define cgsUuid											4114

#define cgsModel										4120

#define cgsAutoExpComp									4200

#define cgsDescription									4210


/*****************************************************************************/


// PhGetVersion constants
#define GV_CAMERA			 1
#define GV_FIRMWARE			 2
#define GV_FPGA				 3
#define GV_PHCON			 4
#define GV_CFA				 5
#define GV_KERNEL			 6
#define GV_MAGAZINE			 7
#define GV_FIRMWAREPACK		 8
#define GV_HEAD_FIRMWARE     9
#define GV_HEAD_FPGA         10
#define GV_HEAD_FIRMWAREPACK 11

/*****************************************************************************/

//
// Sensor Mode Bit stored in setup.sensor (Currently used only on the Flex 4K GS, VEO 4K and VIRGO V2040 sensor)
//
#define SENSOR_MODE_BIT_MASK            0xFF000000  // Sensor mode bits (bits 31, 30, 29, 28, 27, 26, 25, 24)
                                                    // all bits not used, includes some spares bits

//
// Sensor Shutter Mode (Currently used only on the Flex 4K GS and VEO 4K sensor)
//
#define SENSOR_SHUTTER_MODE_BIT_MASK    0xE0000000  // Sensor shutter bits (bits 31, 30, 29)
#define DEFAULT_SHUTTER_BIT	            0x00000000  // old camera (assume Global) unless Flex 4k which would be rolling
#define ROLLING_SHUTTER_BIT	            0x40000000  // Sensor Set to 0x010 Rolling Shutter
#define GLOBAL_SHUTTER_BIT	            0x80000000  // Sensor Set to 0x800 Global Shutter
                                                    // all other values currently undefined


#define ROLLING_SHUTTER	        0		// Sensor Set to Rolling Shutter
#define GLOBAL_SHUTTER	        1		// Sensor Set to Global Shutter

//
// Sensor Acquisition Mode (Currently used only on the VIRGO V2040 sensor)
//
#define SENSOR_ACQ_MODE_BIT_MASK        0x0F000000  // Sensor acquisition mode bits (bits 27, 26, 25, 24)
#define ACDS12B_ACQ_BIT                 0x00000000  // Sensor Set to 0x0000 (HQ) ACDS12b acquisition 
#define ACDS10B_ACQ_BIT                 0x01000000  // Sensor Set to 0x0001 (HQEx) ACDS10b acquisition  
#define ACDS12BBINNED_ACQ_BIT           0x02000000  // Sensor Set to 0x0010 (Binned) ACDS12bBINNED acquisition  
#define ACDS10BBINNED_ACQ_BIT           0x03000000  // Sensor Set to 0x0011 (BinnedEx) ACDS10bBINNED acquisition  
#define SE12B_ACQ_BIT                   0x04000000  // Sensor Set to 0x0100 (Lightning) SE12b(single ended 12b / pixel acquisition   
#define SE10B_ACQ_BIT                   0x05000000  // Sensor Set to 0x0101 (LightningEx) SE10b(single ended 10b / pixel acquisition   
#define SE12BBINNED_ACQ_BIT             0x06000000  // Sensor Set to 0x0110 (LightningBin) SE12bbinned single ended 12b / pixel acquisition 
#define SE10BBINNED_ACQ_BIT             0x07000000  // Sensor Set to 0x0111 (LightningBinEx) SE10bbinned single ended 10b / pixel acquisition 


#define ACDS12B_ACQ             0  // Sensor Set to 0x0000 (HQ) ACDS12b acquisition 
#define ACDS10B_ACQ             1  // Sensor Set to 0x0001 (HQEx) ACDS10b acquisition  
#define ACDS12BBINNED_ACQ       2  // Sensor Set to 0x0010 (Binned) ACDS12bBINNED acquisition  
#define ACDS10BBINNED_ACQ       3  // Sensor Set to 0x0011 (BinnedEx) ACDS10bBINNED acquisition  
#define SE12B_ACQ               4  // Sensor Set to 0x0100 (Lightning) SE12b(single ended 12b / pixel acquisition   
#define SE10B_ACQ               5  // Sensor Set to 0x0101 (LightningEx) SE10b(single ended 10b / pixel acquisition   
#define SE12BBINNED_ACQ         6  // Sensor Set to 0x0110 (LightningBin) SE12bbinned single ended 12b / pixel acquisition  
#define SE10BBINNED_ACQ         7  // Sensor Set to 0x0111 (LightningBinEx) SE10bbinned single ended 10b / pixel acquisition  

/*****************************************************************************/


// PhGetAuxData selection codes
#define  GAD_TIMEXP         1001    // both image time and exposure
#define  GAD_TIME           1002
#define  GAD_EXPOSURE       1003
#define  GAD_RANGE1         1004    // range data 
#define  GAD_BINSIG         1005    // image binary signals multichannels multisample
									// 8 samples and or channels per byte
#define  GAD_ANASIG         1006    // image analog signals multichannels multisample
									// 2 bytes per sample
#define	 GAD_SMPTETC		1007	// SMPTE time code block (see TC)
#define	 GAD_SMPTETCU		1008	// SMPTE unpacked time code block (see TCU)

#define	 GAD_AUDIO			1009	// 48khz audio
/*****************************************************************************/


// Possible values for gsAuxSignal
#define AUXSIG_STROBE		0
#define AUXSIG_IRIGOUT		1
#define AUXSIG_EVENT		2
#define AUXSIG_MEMGATE		3
#define AUXSIG_FSYNC        4

/*****************************************************************************/

// Possible values for gsAuxSignal1
#define AUX1SIG_STROBE		0
#define AUX1SIG_EVENT		1
#define AUX1SIG_MEMGATE		2
#define AUX1SIG_FSYNC		3
/*****************************************************************************/

// Possible values for gsAuxSignal2
#define AUX2SIG_READY		0
#define AUX2SIG_STROBE		1
#define AUX2SIG_AES_EBU_OUT	2
/*****************************************************************************/

// Possible values for gsAuxSignal3
#define AUX3SIG_IRIGOUT		0
#define AUX3SIG_STROBE		1
/*****************************************************************************/


// Possible values for gsTimeCodeOutSignal
#define TIMECODEOUTSIG_IRIG		0
#define TIMECODEOUTSIG_SMPTE	1
/*****************************************************************************/


// PhSetDllsOptions selectors
#define DO_IGNORECAMERAS		1
#define DO_PERCAMERAACQPARAMS	2
#define DO_SUPPRESSOFFLINESTAMP 7
/*****************************************************************************/


// Set logging options - set the masks for selective dumps from Phantom dlls
// Use them as selection codes for the function PhSetDllsLogOption
#define  SDLO_PHANTOM		100
#define  SDLO_PHCON			101
#define  SDLO_PHINT			102
#define  SDLO_PHFILE		103
#define  SDLO_PHSIG			104
#define  SDLO_PHSIGV		105
#define  SDLO_TORAM			106
/*****************************************************************************/


// Get logging options - get the current settings
// Use them as selection codes for the function PhGetDllsLogOption
#define  GDLO_PHANTOM		200
#define  GDLO_PHCON			201
#define  GDLO_PHINT			202
#define  GDLO_PHFILE		203
#define  GDLO_PHSIG			204
#define  GDLO_PHSIGV		205
#define  GDLO_TORAM			206
/*****************************************************************************/


// Fill the requested data by simulated values
#define  SIMULATED_AUXDATA  0x80000000
/*****************************************************************************/


// Constants for the PhNVMContRec function
// NVM = Flash memory (NonVolatileMemory used for persistent cine store)
#define NVCR_CONT_REC		0x00000001  // Enable continuous recording to NVM mode
#define NVCR_APV			0x00000002  // Enable the automatic playback to video	
#define NVCR_REC_ONCE		0x00000004  // Enable the record once mode
/*****************************************************************************/


// SyncImaging field in ACQUIPARAMS
#define SYNC_INTERNAL		0		// Free-run of camera
#define SYNC_EXTERNAL		1		// Locks to the FSYNC input
#define SYNC_LOCKTOIRIG		2		// Locks to IRIG timecode
#define SYNC_LOCKTOVIDEO	3		// Locks to the video frame rate
/*****************************************************************************/


#if !defined(CFA_VRI)
// Color Filter Array used on the sensor
// In mixed multihead system the gray heads have also some of the msbit set (see XX_GRAY below)
#define CFA_NONE			0		// gray sensor
#define CFA_VRI				1		// gbrg/rggb
#define CFA_VRIV6			2		// bggr/grbg
#define CFA_BAYER			3		// gb/rg
#define CFA_BAYERFLIP		4		// rg/gb
#define CFA_MASK			0xff	// only lsbyte is used for cfa code, the rest is for multiheads
/*****************************************************************************/


// These masks combined with  CFA_VRIV6  describe a mixed (gray&color) image (Phantom v6)
#define TL_GRAY  0x80000000    // Top left head of v6 multihead system is gray
#define TR_GRAY  0x40000000    // Top right head of v6 multihead system is gray
#define BL_GRAY  0x20000000    // Bottom left head of v6 multihead system is gray
#define BR_GRAY  0x10000000    // Bottom right head of v6 multihead system is gray
/*****************************************************************************/


#define ALLHEADS_GRAY 0xF0000000    //(TL_GRAY|TR_GRAY|BL_GRAY|BR_GRAY)
#endif
/*****************************************************************************/


// Analog and digital video output
#define VIDEOSYS_NTSC	        0		// USA analog system
#define VIDEOSYS_PAL	        1		// European analog system

#define VIDEOSYS_720P60         4		// Digital HDTV modes: Progressive
#define VIDEOSYS_720P59DOT9     12
#define VIDEOSYS_720P50	        5
#define VIDEOSYS_1080P30        20
#define VIDEOSYS_1080P29DOT9    28
#define VIDEOSYS_1080P25        21
#define VIDEOSYS_1080P24        36
#define VIDEOSYS_1080P23DOT9    44

#define VIDEOSYS_1080I30        68      // Interlaced
#define VIDEOSYS_1080I29DOT9    76
#define VIDEOSYS_1080I25        69

#define VIDEOSYS_1080PSF30      52      // Progressive split frame
#define VIDEOSYS_1080PSF29DOT9  60
#define VIDEOSYS_1080PSF25      53
#define VIDEOSYS_1080PSF24      84
#define VIDEOSYS_1080PSF23DOT9  92
/*****************************************************************************/


// Notification messages sent to your main window  -  call the notification
// routines to process these messages
#if !defined(NOTIFY_DEVICE_CHANGE)
#define NOTIFY_DEVICE_CHANGE  1325              //(WM_USER+301)   WM_USER=0x0400
#define NOTIFY_BUS_RESET      1326              //(WM_USER+302)
#endif
//MATLABconstants end
/*****************************************************************************/

// for Battery Control

#define BATTERY_MODE_DISABLE_CHARGING               0x01        // Bit 0 
#define BATTERY_MODE_DISABLE_DISCHARGING_ARMING     0x02        // Bit 1
#define BATTERY_MODE_FORCE_ARMING                   0x04        // Bit 2
#define BATTERY_MODE_ENABLE_PREVIEW_ARMING          0x08        // Bit 3

#define BATTERY_RUNTIME_1                           1           // 1 Sec 
#define BATTERY_RUNTIME_10                          10          // 10 Sec 
#define BATTERY_RUNTIME_60                          60          // 1 Minute 
#define BATTERY_RUNTIME_120                         120         // 2 Minute 
#define BATTERY_RUNTIME_180                         180         // 3 Minute 
#define BATTERY_RUNTIME_300                         300         // 5 Minute 
#define BATTERY_RUNTIME_600                         600         // 10 Minute 

#define BATTERY_NOT_PRESENT                         0
#define BATTERY_CHARGING                            1
#define BATTERY_CHARGING_HIGH                       2
#define BATTERY_CHARGED                             3
#define BATTERY_DISCHARGING                         4
#define BATTERY_LOW                                 5
#define BATTERY_ARMED                               8          // This is really just Bit 3  (8 is added to other values if armed)
#define BATTERY_FAULT                               16

/*****************************************************************************/

#define MAX_EXP_INDEX                               10          // Normally 8 setting, but leave room for a table end, 0 = last

/*****************************************************************************/


#if !defined(_NVCRDEFINED_)
#define _NVCRDEFINED_
// Constants for the NVContRec commands and status 
// Write - Read bits 
#define NVCR_CONT_REC   0x00000001  // Enable continuous recording to NVM mode
#define NVCR_APV        0x00000002  // Enable the automatic playback to video
#define NVCR_REC_ONCE   0x00000004  // Enable the record once mode
// Read bits 
#define NVCR_NO_IMAGE   0x00000100  // No image can be sent because of save
									// to NVM during REC_ONCE mode
#endif
/*****************************************************************************/

typedef BOOL (WINAPI *PROGRESSCALLBACK)(UINT CN, UINT Percent);
EXIMPROC HRESULT PhSetDllsOption(UINT optionSelector, PVOID pValue);
EXIMPROC HRESULT PhGetDllsOption(UINT optionSelectro, PVOID pValue);
EXIMPROC HRESULT PhRegisterClientEx(HWND hWnd, char *pStgPath,
                                    PROGRESSCALLBACK pfnCallback, UINT PhConHeaderVer);
EXIMPROC HRESULT PhUnregisterClient(HWND hWnd);
/*****************************************************************************/


EXIMPROC HRESULT PhGet (UINT CN, UINT Selector, PVOID pVal);
EXIMPROC HRESULT PhSet (UINT CN, UINT Selector, PVOID pVal);
EXIMPROC HRESULT PhGet1(UINT CN, UINT Selector, UINT Selector1, PVOID pVal);
EXIMPROC HRESULT PhSet1(UINT CN, UINT Selector, UINT Selector1, PVOID pVal);
EXIMPROC HRESULT PhGet2(UINT CN, UINT Selector, UINT Selector1, UINT Selector2, PVOID pVal);


EXIMPROC HRESULT PhCineGet(UINT CN, INT Cine, UINT Selector, PVOID pVal);
EXIMPROC HRESULT PhCineSet(UINT CN, INT Cine, UINT Selector, PVOID pVal);
/*****************************************************************************/


EXIMPROC HRESULT PhGetCineStatus(UINT CN, PCINESTATUS pStatus);
EXIMPROC HRESULT PhGetCineCount(UINT CN, PUINT pRAMCount, PUINT pNVMCount);
EXIMPROC HRESULT PhRecordCine(UINT CN);
EXIMPROC HRESULT PhRecordSpecificCine(UINT CN, int Cine);
EXIMPROC HRESULT PhSendSoftwareTrigger(UINT CN);
EXIMPROC HRESULT PhDeleteCine(UINT CN, INT Cine);
/*****************************************************************************/


EXIMPROC HRESULT PhSetCineParams(UINT CN, INT Cine, PACQUIPARAMS pParams);
EXIMPROC HRESULT PhGetCineParams(UINT CN, INT Cine, PACQUIPARAMS pParams, PBITMAPINFO pBMI);
EXIMPROC HRESULT PhSetSingleCineParams(UINT CN, PACQUIPARAMS pParams);
/*****************************************************************************/


EXIMPROC HRESULT PhGetVersion(UINT CN, UINT VerSel, PUINT pVersion);
EXIMPROC HRESULT PhSetPartitions(UINT CN, UINT Count, PUINT pWeights);
EXIMPROC HRESULT PhGetPartitions(UINT CN, PUINT pCount, PUINT pPartitionSize);
/*****************************************************************************/


EXIMPROC HRESULT PhGetSupportedCameras(PIARRAYDESC supportedCamVerList);
EXIMPROC HRESULT PhAddSimulatedCamera(UINT CamVer, UINT Serial);
EXIMPROC HRESULT PhNotifyDeviceChangeCB(PROGRESSCALLBACK pfnCallback);
EXIMPROC HRESULT PhGetIgnoredIp(PUINT pCnt, PUINT pIpAddress);
EXIMPROC HRESULT PhAddIgnoredIp(UINT IpAddress);
EXIMPROC HRESULT PhRemoveIgnoredIp(UINT IpAddress);
EXIMPROC HRESULT PhGetVisibleIp(PUINT pCnt, PUINT pIpAddress);
EXIMPROC HRESULT PhAddVisibleIp(UINT IpAddress);
EXIMPROC HRESULT PhRemoveVisibleIp(UINT IpAddress);
EXIMPROC HRESULT PhMakeAllIpVisible(void);
EXIMPROC HRESULT PhDisableVisible(BOOL bDisabled);
EXIMPROC BOOL PhIsVisibleDisabled(void);

EXIMPROC HRESULT PhFillIDInfo(PCAMERAID pCam);

EXIMPROC HRESULT PhConfigPoolUpdate(UINT Period);
EXIMPROC BOOL    PhOffline(UINT CN);
/*****************************************************************************/


EXIMPROC HRESULT PhGetCameraCount(UINT *pCnt);
EXIMPROC HRESULT PhGetCameraID(UINT CN, UINT *pSerial, char *pCameraName);
EXIMPROC HRESULT PhFindCameraNumber(UINT Serial, UINT *pCN);
EXIMPROC int PhFirstFlashCine(UINT CN);
EXIMPROC int PhMaxCineCnt(UINT CN);
/*****************************************************************************/


EXIMPROC HRESULT PhSetCameraName(UINT CN, char *pCameraName);
EXIMPROC HRESULT PhGetCameraTime(UINT CN, PTIME64 pTime64);
EXIMPROC HRESULT PhSetCameraTime(UINT CN, UINT32 Time);
EXIMPROC HRESULT PhGetErrorMessage(int ErrNo, char *pErrText);
EXIMPROC HRESULT PhGetCameraErrMsg(UINT CN, char *pErrText);
EXIMPROC HRESULT PhSetDllsLogOption(UINT SelectCode, UINT Value);
EXIMPROC HRESULT PhGetDllsLogOption(UINT SelectCode, PUINT pValue);
/*****************************************************************************/


EXIMPROC HRESULT PhBlackReference(UINT CN, PROGRESSCALLBACK pfnCallback);
EXIMPROC HRESULT PhBlackReferenceCI(UINT CN, PROGRESSCALLBACK pfnCallback);
EXIMPROC HRESULT PhComputeWB(PBITMAPINFOHEADER pBMIH, PBYTE pPixel, PPOINT pP, int SquareSide,
                             UINT CFA, PWBGAIN pWB, PUINT pSatCnt);
/*****************************************************************************/


EXIMPROC HRESULT PhGetResolutions(UINT CN, PPOINT pRes, PUINT pCnt, PBOOL pCAR, PUINT pADCBits);
EXIMPROC HRESULT PhGetBitDepths(UINT CN, PUINT pCnt, PUINT pBitDepths);
EXIMPROC HRESULT PhGetFrameRateRange(UINT CN, POINT Res, UINT *pMinFrameRate, UINT *pMaxFrameRate);
EXIMPROC HRESULT PhGetExactFrameRate(UINT CamVer, UINT SyncMode, UINT RequestedFrameRate, double *pExactFrameRate);
EXIMPROC HRESULT PhGetExactFrameRateDouble(UINT CamVer, UINT SyncMode, double RequestedFrameRate, double *pExactFrameRate);
EXIMPROC HRESULT PhGetExposureRange(UINT CN, UINT FrameRate, UINT *pMinExposure, UINT *pMaxExposure);
/*****************************************************************************/


EXIMPROC HRESULT PhGetCameraOptions(UINT CN, PCAMERAOPTIONS pOptions);
EXIMPROC HRESULT PhSetCameraOptions(UINT CN, PCAMERAOPTIONS pOptions);
/*****************************************************************************/


// Write the calibrations and settings into the camera flash
EXIMPROC HRESULT PhWriteStgFlash(UINT CN, PROGRESSCALLBACK pfnCallback);
/*****************************************************************************/


// Flash (NonVolatileMemory) routines
EXIMPROC HRESULT PhMemorySize(UINT CN, PUINT pDRAMSize, PUINT pNVMSize);
EXIMPROC HRESULT PhNVMErase(UINT CN,  PROGRESSCALLBACK pfnCallback);
EXIMPROC HRESULT PhNVMGetStatus(UINT CN, PUINT pCineCnt, PUINT32 pTime, PUINT pFreeSp);
EXIMPROC HRESULT PhNVMRestore(UINT CN, UINT CineNo,  PROGRESSCALLBACK pfnCallback);
EXIMPROC HRESULT PhNVMContRec(UINT CN, PBOOL pSave, PUINT pOldValue, PUINT pEnable);
EXIMPROC HRESULT PhNVMGetSaveRange(UINT CN, PIMRANGE pRng);
EXIMPROC HRESULT PhNVMSetSaveRange(UINT CN, PIMRANGE pRng);
EXIMPROC HRESULT PhNVMSave(UINT CN, INT Cine, PROGRESSCALLBACK pfnCallback);
EXIMPROC HRESULT PhNVMSaveClip(UINT CN, int Cine, PIMRANGE pRng,
                               UINT Options, PROGRESSCALLBACK pfnCallback);
EXIMPROC HRESULT PhRemoveCameraFile(UINT CN, PCHAR szCamFN);
/*****************************************************************************/


// Video play control
EXIMPROC HRESULT PhVideoPlay(UINT CN, INT CineNr, PIMRANGE pRng, INT PlaySpeed);
EXIMPROC HRESULT PhGetVideoFrNr(UINT CN, PINT pCrtIm);
/*****************************************************************************/


// Routines used from LabView
EXIMPROC HRESULT PhLVRegisterClientEx(char *pStgPath, PROGRESSCALLBACK pfnCallback, UINT PhConHeaderVersion);
EXIMPROC HRESULT PhLVUnregisterClient();
EXIMPROC HRESULT PhLVProgress(UINT CallID, PUINT pPercent, BOOL Continue);
/*****************************************************************************/


EXIMPROC HRESULT PhGetAllIpCameras(PUINT pCnt, PCAMERAID pCam);
EXIMPROC HRESULT PhCheckCameraPool(PBOOL pChanged);
EXIMPROC HRESULT PhParamsChanged(UINT CN, PBOOL pChanged);
/*****************************************************************************/


// PhCon Error Codes
// Informative
#define ERR_Ok                          (0)
#define ERR_SimulatedCamera             (100)
#define ERR_UnknownErrorCode            (101)

#define ERR_BadResolution               (102)
#define ERR_BadFrameRate                (103)
#define ERR_BadPostTriggerFrames        (104)
#define ERR_BadExposure                 (105)
#define ERR_BadEDRExposure              (106)

#define ERR_BufferTooSmall              (107)
#define ERR_CannotSetTime               (108)
#define ERR_SerialNotFound              (109)
#define ERR_CannotOpenStgFile           (110)

#define ERR_UserInterrupt               (111)

#define ERR_NoSimulatedImageFile        (112)
#define ERR_SimulatedImageNot24bpp      (113)

#define ERR_BadParam                    (114)
#define ERR_FlashCalibrationNewer       (115)

#define ERR_ConnectedHeadsChanged       (117)
#define ERR_NoHead                      (118)
#define ERR_NVMNotInstalled             (119)
#define ERR_HeadNotAvailable            (120)
#define ERR_FunctionNotAvailable        (121)
#define ERR_Ph1394dllNotFound           (122)
#define ERR_oldtNotFound                (123)
#define ERR_BadFRPSteps                 (124)
#define ERR_BadFRPImgNr                 (125)
#define ERR_BadAutoExpLevel             (126)
#define ERR_BadAutoExpRect              (127)
#define ERR_BadDecimation               (128)
#define ERR_BadCineParams               (129)
#define ERR_IcmpNotAvailable            (130)
#define ERR_CorrectResetLine			(131)
#define ERR_CSRDoneInCamera             (132)
#define ERR_ParamsChanged               (133)

#define ERR_ParamReadOnly				(134)
#define ERR_ParamWriteOnly				(135)
#define ERR_ParamNotSupported			(136)

#define ERR_IppWarning					(137)

#define ERR_CannotOpenStpFile           (138)
#define ERR_CannotSetStpParameters      (139)

/*****************************************************************************/

// Serious
#define ERR_NULLPointer                 (-200)
#define ERR_MemoryAllocation            (-201)
#define ERR_NoWindow                    (-202)
#define ERR_CannotRegisterClient        (-203)
#define ERR_CannotUnregisterClient      (-204)

#define ERR_AsyncRead                   (-205)
#define ERR_AsyncWrite                  (-206)

#define ERR_IsochCIPHeader              (-207)
#define ERR_IsochDBCContinuity          (-208)
#define ERR_IsochNoHeader               (-209)
#define ERR_IsochAllocateResources      (-210)
#define ERR_IsochAttachBuffers          (-211)
#define ERR_IsochFreeResources          (-212)
#define ERR_IsochGetResult              (-213)

#define ERR_CannotReadTheSerialNumber   (-214)
#define ERR_SerialNumberOutOfRange      (-215)
#define ERR_UnknownCameraVersion        (-216)

#define ERR_GetImageTimeOut             (-217)
#define ERR_ImageNoOutOfRange           (-218)

#define ERR_CannotReadStgHeader         (-220)
#define ERR_ReadStg                     (-221)
#define ERR_StgContents                 (-222)
#define ERR_ReadStgOffsets              (-223)
#define ERR_ReadStgGains                (-224)
#define ERR_NotAStgFile                 (-225)
#define ERR_StgSetupCheckSum            (-226)
#define ERR_StgSetup                    (-227)
#define ERR_StgHardAdjCheckSum          (-228)
#define ERR_StgHardAdj                  (-229)
#define ERR_StgDifferentSerials         (-230)
#define ERR_WriteStg                    (-231)

#define ERR_NoCine                      (-232)
#define ERR_CannotOpenDevice            (-233)
#define ERR_TimeBufferSize              (-234)

#define ERR_CannotWriteCineParams       (-236)

#define ERR_NVMError                    (-250)
#define ERR_NoNVM                       (-251)

#define ERR_FlashEraseTimeout           (-253)
#define ERR_FlashWriteTimeout           (-254)

#define ERR_FlashContents               (-255)
#define ERR_FlashOffsetsCheckSum        (-256)
#define ERR_FlashGainsCheckSum          (-257)

#define ERR_TooManyCameras              (-258)
#define ERR_NoResponseFromCamera        (-259)
#define ERR_MessageFromCamera           (-260)

#define ERR_BadImgResponse              (-261)
#define ERR_AllPixelsBad                (-262)

#define ERR_BadTimeResponse             (-263)
#define ERR_GetTimeTimeOut              (-264)

#define ERR_BadAudioResponse            (-265)
#define ERR_GetAudioTimeOut             (-266)

//Base64 coding and decoding errors
#define ERR_InBlockTooBig               (-270)
#define ERR_OutBufferTooSmall           (-271)
#define ERR_BlockNotValid               (-272)
#define ERR_DataAfterPadding            (-273)
#define ERR_InvalidSlash                (-274)
#define ERR_UnknownChar                 (-275)
#define ERR_MalformedLine               (-276)
#define ERR_EndMarkerNotFound           (-277)

#define ERR_NoTimeData                  (-280)
#define ERR_NoExposureData              (-281)
#define ERR_NoRangeData                 (-282)

#define ERR_NotIncreasingTime           (-283)
#define ERR_BadTriggerTime              (-284)
#define ERR_TimeOut                     (-285)

#define ERR_NullWeightsSum              (-286)
#define ERR_BadCount                    (-287)
#define ERR_CannotChangeRecordedCine    (-288)

#define ERR_BadSliceCount               (-289)
#define ERR_NotAvailable                (-290)
#define ERR_BadImageInterval            (-291)

#define ERR_BadCameraNumber             (-292)
#define ERR_BadCineNumber               (-293)

#define ERR_BadSyncObject               (-294)
#define ERR_IcmpEchoError  			    (-295)

#define ERR_MlairReadFirstPacket		(-296)
#define ERR_MlairReadPacket				(-297)
#define ERR_MlairIncorrectOrder			(-298)

#define ERR_MlairStartRecorder			(-299)
#define ERR_MlairStopRecorder			(-300)
#define ERR_MlairOpenFile				(-301)

#define ERR_CmdMutexTimeOut				(-302)
#define ERR_CmdMutexAbandoned			(-303)

#define ERR_UnsupportedConversion		(-304)

#define ERR_TenGigLostPacket			(-305)

#define ERR_TooManyImgReq				(-306)

#define ERR_BadImRange					(-307)
#define ERR_ImgBufferTooSmall			(-308)
#define ERR_ImgSize0					(-309)

#define ERR_IppError					(-310)

#define ERR_pscpError					(-311)
#define ERR_plinkError					(-312)

#define ERR_CineMagBusy					(-320)
#define ERR_UnknownToken		        (-321)

#define ERR_BadPortNumber				(-330)
#define ERR_PortNotProg					(-331)
#define ERR_BadSigNumber				(-332)


/*****************************************************************************/


///////////////////////////////////////////////////////////////////////////////
//								DEPRECATED									 //
///////////////////////////////////////////////////////////////////////////////


// Set of digital adjustments that can be applied to the image acquired in PhGetImage
typedef struct tagIMPARAMS
{
	//WBGAIN WBGain[4]; (changed to be compatible with MATLAB calllib)
	float WBGainR0;         // Gain adjust on R,B components, for white balance,
	float WBGainB0;			// 1.0 = do nothing,
	float WBGainR1;			// index 0: full image for v4,5,7...TL head for v6
	float WBGainB1;			// index 1, 2, 3 :   TR, BL, BR for v6
	float WBGainR2;
    float WBGainB2;
    float WBGainR3;
    float WBGainB3;	

    // Analog video out image adjustments;
    // Do not change the digital image transferred to the computer
    int VideoBright;        // [-1024, 1024] neutral 0
    int VideoContrast;      // [1024, 8192] neutral 1024
    float VideoGamma;       // [1024, 4096] neutral 1024
    int VideoSaturation;    // [0, 2048] neutral 1024
    int PedestalR;          // small offset correction, separate on colors
    int PedestalG;
    int PedestalB;

    int VideoHue;           // [-180, 180] neutral 0

    // VRI internal note: Size checked structure.
	// Update oldcomp.c if new fields are added    
} IMPARAMS, *PIMPARAMS;
/*****************************************************************************/


// PhGetImage constants
#define GI_INTERPOLATED 4		// color image, RGB interpolated 
								// extensions for v6 and other multihead systems
#define GI_ONEHEAD      8		// multihead system, bit=1: select image from one head 
#define GI_HEADMASK  0xf0		// head number: 0:TL 1:TR 2:BL 3:BR.. (up to 16 heads, 
								// v6 has 4 heads)   -  bits 4...7 of the Options
								// extensions for v7
//#define GI_BPP12				0x100   // BitsPerPixel = 12 for the requested image - not implemented, not used
#define GI_BPP16	0x200		// BitsPerPixel = 16 for the requested image 

#define GI_PACKED	0x100		// return the pixels as read from camera; possible packed (10 bits: 4 pixels in 5 bytes) 

#define GI_DENORMALIZED	0x2000	// Leave the pixels as read from camera, possible with black level != 0 and white level != Maximum  
								//Default is to scale the pixels value so the black level is at 0 and white level at Maximum Pixel Value
/*****************************************************************************/


// PhGetI3Info
#define  GII_SOURCECAMERA   1		// Source camera number (camera connected through 
//fiber to memory slices)
#define  GII_SLICECOUNT     2		// Slice Count 
#define  GII_SLICELIST      3		// List of camera numbers to access the slices
#define  GII_VIRTUALCN      4		// Camera number of the virtual device
/*****************************************************************************/


EXIMPROC HRESULT PhRegisterClient(HWND hWnd, char *pStgPath);
EXIMPROC HRESULT PhRegisterClientCB(HWND hWnd, char *pStgPath,
                                    PROGRESSCALLBACK pfnCallback);
/*****************************************************************************/


EXIMPROC HRESULT PhSetImageParameters(UINT CN, PIMPARAMS pParams);
EXIMPROC HRESULT PhGetImageParameters(UINT CN, PIMPARAMS pParams);
EXIMPROC HRESULT PhSetCineImageParameters(UINT CN, int Cine, PIMPARAMS pIPPar);
EXIMPROC HRESULT PhGetCineImageParameters(UINT CN, int Cine, PIMPARAMS pIPPar);
/*****************************************************************************/


EXIMPROC HRESULT PhMeasureWB(UINT CN, PPOINT pP, int SquareSide, UINT ImageCount,
                             UINT Options, PROGRESSCALLBACK pfnCallback, PWBGAIN pWB, PUINT pSatCnt);
EXIMPROC HRESULT PhGetAuxData(UINT CN, UINT Sel, INT Cine, PIMRANGE pRng, PBYTE pData);
EXIMPROC HRESULT PhGetCameraModel(UINT CamVer, PSTR pModel);
/*****************************************************************************/


EXIMPROC HRESULT PhGetImage(UINT CN, PINT pCine, PIMRANGE pRng, UINT Options, PBYTE pPixel);
/*****************************************************************************/

EXIMPROC HRESULT PhRestoreCameraStatus(UINT CN);
EXIMPROC HRESULT PhNotifyBusReset(void);
EXIMPROC HRESULT PhBusReset(void);
EXIMPROC HRESULT PhCheckNotification(void);
EXIMPROC HRESULT PhStreamToVideo(UINT CN);
EXIMPROC HRESULT PhStreamTo1394(UINT CN);
/*****************************************************************************/


EXIMPROC HRESULT PhGetI3Info(UINT CN, UINT Selection, PVOID pData);
/*****************************************************************************/


EXIMPROC HRESULT PhSetSimulatedCamera(UINT CamVer, UINT CFA);
EXIMPROC HRESULT PhNotifyDeviceChange(void);
EXIMPROC HRESULT PhGetVersions(UINT CN, UINT *pCameraVersion, UINT *pFirmwareVersion, UINT *pDllVersion, UINT *pCFA);
EXIMPROC HRESULT PhBlackBalance(UINT CN, PROGRESSCALLBACK pfnCallback);//synonym for PhBlackReference, not to be used
EXIMPROC HRESULT PhGetCameraResolutions(UINT CN, PPOINT pRes, PUINT pCnt);
EXIMPROC HRESULT PhSetAcquisitionParameters(UINT CN, PACQUIPARAMS pParams);
EXIMPROC HRESULT PhGetAcquisitionParameters(UINT CN, PACQUIPARAMS pParams, PBITMAPINFO pBMI);
EXIMPROC HRESULT PhGetCineParameters(UINT CN, PACQUIPARAMS pParams, PBITMAPINFO pBMI);
EXIMPROC HRESULT PhHasCine(UINT CN, PBOOL pHasCine);    //has at least one cine

EXIMPROC HRESULT PhGetPreviewImage(UINT CN, PBITMAPINFOHEADER pBMIH, UINT Options, PBYTE pPixel);
EXIMPROC HRESULT PhGetRecordedImage(UINT CN, PBITMAPINFOHEADER pBMIH, INT ImageNo, UINT Options, PBYTE pPixel);
EXIMPROC HRESULT PhGetRecordedBlock(UINT CN, PBITMAPINFOHEADER pBMIH, INT ImageNo, UINT Options, PBYTE pPixel);

EXIMPROC HRESULT PhGetCineTime(UINT CN, PTIME64 pTime, PFRACTIONS pExposure);
EXIMPROC HRESULT PhGetTriggerTime(UINT CN, PTIME64 pTriggerTime);

EXIMPROC HRESULT PhSearchForAllCameras(PROGRESSCALLBACK pfnCallback);	//deprecated, to be replaced by PhGetAllIpCameras

// Function for starting/stopping ITT recorder app
EXIMPROC HRESULT PhStartIttRecorder();
EXIMPROC HRESULT PhStopIttRecorder();
/*****************************************************************************/

#undef EXIMPROC     // avoid conflicts with other similar headers

#ifdef __cplusplus
}
#endif
#endif
