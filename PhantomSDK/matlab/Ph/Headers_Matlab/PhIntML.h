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

// Color interpolation library for the Phantom High Speed Camera
// PhInt.h (public structures, constants and functions)

#ifndef __PHINTINCLUDED__
#define __PHINTINCLUDED__

//Do not define the symbol _PHINT_ in your program to allow compiler optimization
#if defined(_PHINT_)
#define EXIMPROC __declspec(dllexport)
#else
#define EXIMPROC __declspec(dllimport)
#endif

#ifdef __cplusplus
extern "C"
{
#endif

#if !defined (int8_t)
    //define the integer types with known size according to C99 and stdint.h
    typedef               char int8_t;
    typedef unsigned      char uint8_t;
    typedef          short int int16_t;
    typedef unsigned short int uint16_t;
    typedef                int int32_t;
    typedef unsigned       int uint32_t;
    typedef            __int64 int64_t;
    typedef unsigned   __int64 uint64_t;
#endif
typedef int bool32_t;
/*****************************************************************************/

#if !defined(_TIMEDEFINED_)
#define _TIMEDEFINED_

//A format for small intervals of time: [250 picosecond ... 1 second)
//It is fixed point 0.32 or, in other words, the time in seconds is
//stored multiplied by 4Gig i.e.  4294967296.0 and rounded to int.
typedef uint32_t FRACTIONS, *PFRACTIONS;

//The absolute time format used in PC software is TIME64
typedef struct tagTIME64    // A compact format for time 64 bits
                            // fixed point (32.32 seconds)
{
    FRACTIONS fractions;    // Fractions of seconds
                            // (resolution 1/4Gig i.e.  cca. 1/4 ns)
                            // The fractions of the second are stored here
                            // multiplied by 2**32. Least significant 2 bits
                            // store info about IRIG synchronization
                            // bit0 = 0 IRIG synchronized
                            // bit0 = 1 not synchronized
                            // bit1 = 0 Event input=0 (short to ground)
                            // bit1 = 1 Event input=1 (open)
    uint32_t seconds;       // Seconds from Jan 1 1970, compatible with the C
                            // library routines
                            // (max year: 2038 signed, 2106 unsigned)
                            // VS2005 changed the default time_t to 64 bits;
                            // here we have to maintain the 32 bits size to
                            // remain compatible with the stored file format
                            // and the public interfaces
} TIME64, *PTIME64;
/*****************************************************************************/

//Time code according to the standard SMPTE 12M-1999
typedef struct tagTC
{
/*
	Redefined the this part of structure for MATLAB use
    uint8_t framesU:4;        // Units of frames
    uint8_t framesT:2;        // Tens of frames
    uint8_t dropFrameFlag:1;  // Dropframe flag
    uint8_t colorFrameFlag:1; // Colorframe flag
    uint8_t secondsU:4;       // Units of seconds
    uint8_t secondsT:3;       // Tens of seconds
    uint8_t flag1:1;          // Flag 1
    uint8_t minutesU:4;       // Units of minutes
    uint8_t minutesT:3;       // Tens of minutes
    uint8_t flag2:1;          // Flag 2
    uint8_t hoursU:4;         // Units of hours
    uint8_t hoursT:2;         // Tens of hours
    uint8_t flag3:1;          // Flag 3
    uint8_t flag4:1;          // Flag 4
*/
    uint8_t frames;        	
    uint8_t seconds;       	
    uint8_t minutes;       	
    uint8_t hours;         	
    uint32_t userBitData;     // 32 user bits
}TC, *PTC;

// Unpacked representation of SMPTE 12M-1999 Time Code
typedef struct tagTCU
{
    uint32_t frames;
    uint32_t seconds;
    uint32_t minutes;
    uint32_t hours;
    bool32_t dropFrameFlag;
    bool32_t colorFrameFlag;
    bool32_t flag1;
    bool32_t flag2;
    bool32_t flag3;
    bool32_t flag4;
    uint32_t userBitData;
}TCU, *PTCU;
#endif
/*****************************************************************************/

#if !defined(_WBGAIN_)
#define _WBGAIN_
    //Color channels adjustment
    //intended for the White balance adjustment on color camera
    //by changing the gains of the red and blue channels
    typedef struct tagWBGAIN
    {
        float R;    //White balance, gain correction for red
        float B;    //White balance, gain correction for blue
    }
    WBGAIN, *PWBGAIN;
#endif
/*****************************************************************************/

#if !defined(_WINDOWS)
//Rectangle with well defined fields size
typedef struct tagRECT
{
    int32_t left;
    int32_t top;
    int32_t right;
    int32_t bottom;
} RECT, *PRECT;
#endif

#define OLDMAXFILENAME 65       // maximum file path size for the continuous recording
                                // to keep compatibility with old setup files
#define MAXLENDESCRIPTION_OLD 121//maximum length for setup description
                                 //(before Phantom 638)
#define MAXLENDESCRIPTION 4096  // maximum length for new setup description
#define MAXSTDSTRSZ		  256	// Standard maximum size for a string

#define fUserMatrix cmUser       //changed the convention to name matrices
/*****************************************************************************/

// Image processing: Filtering
typedef struct tagIMFILTER
{
    int32_t dim;        //square kernel dimension 3,5
    int32_t shifts;     //right shifts of Coef (8 shifts means divide by 256)
    int32_t bias;       //bias to add at end
    int32_t Coef[5*5];  //maximum alocation for a 5x5 filter
}
IMFILTER, *PIMFILTER;
/*****************************************************************************/

// SETUP structure - camera setup parameters
// It started to be used in 1992 during the 16 bit compilers era;
// the fields are arranged compact with alignment at 1 byte - this was
// the compiler default at that time. New fields were added, some of them
// replace old fields but a compatibility is maintained with the old versions.

// ---UPDF = Updated Field. This field is maintained for compatibility with old
// versions but a new field was added for that information. The new field can
// be larger or may have a different measurement unit. For example FrameRate16
// was a 16 bit field to specify frame rate up to 65535 fps (frames per second).
// When this was not enough anymore, a new field was added: FrameRate (32 bit
// integer, able to store values up to 4 billion fps). Another example: Shutter
// field (exposure duration) was specified initially in microseconds,
// later the field ShutterNs was added to store the value in nanoseconds.
// The UF can be considered outdated and deprecated; they are updated in the
// Phantom libraries but the users of the SDK can ignore them.
//
// ---TBI - to be ignored, not used anymore
//
// Use the definition from stdint.h with known size for the integer types
//
#pragma pack(push,1)
typedef struct tagSETUP
{
    uint16_t FrameRate16;   // ---UPDF replaced by FrameRate
    uint16_t Shutter16;     // ---UPDF replaced by ShutterNs
    uint16_t PostTrigger16; // ---UPDF replaced by PostTrigger
    uint16_t FrameDelay16;  // ---UPDF replaced by FrameDelayNs
    uint16_t AspectRatio;   // ---UPDF replaced by ImWidth, ImHeight
    uint16_t Res7;          // ---TBI Contrast16
                            // (analog controls, not available after
                            // Phantom v3)
    uint16_t Res8;          // ---TBI Bright16
    uint8_t Res9;           // ---TBI Rotate16
    uint8_t Res10;          // ---TBI TimeAnnotation
                            // (time always comes from camera )
    uint8_t Res11;          // ---TBI TrigCine (all cines are triggered)
    uint8_t TrigFrame;      // Sync imaging mode:
                            // 0, 1, 2 = internal, external, locktoirig
    uint8_t Res12;          // ---TBI ShutterOn (the shutter is always on)
    char DescriptionOld[MAXLENDESCRIPTION_OLD];
                            // ---UPDF replaced by larger Description able to
                            // store 4k of user comments

    uint16_t Mark;          // "ST"  -  marker for setup file
    uint16_t Length;        // Length of the current version of setup
    uint16_t Res13;         // ---TBI Binning (binning factor)

    uint16_t SigOption;     // Global signals options:
                            // MAXSAMPLES = records the max possible samples
    int16_t BinChannels;    // Number of binary channels read from the
                            // SAM (Signal Acquisition Module)
    uint8_t SamplesPerImage;// Number of samples acquired per image, both
                            // binary and analog;
	//MATLAB custom redefiniton
    char BinName[8*11];     // Names for the first 8 binary signals having
                            // maximum 10 chars/name; each string ended by a
                            // byte = 0
    uint16_t AnaOption;     // Global analog options single ended,  bipolar
    int16_t AnaChannels;    // Number of analog channels used (16 bit 2's
                            // complement per channel)
    uint8_t Res6;           // ---TBI (reserved)
    uint8_t AnaBoard;       // Board type 0=none, 1=dsk (DSP system kit),
                            // 2 dsk+SAM
                            // 3 Data Translation DT9802
                            // 4 Data Translation DT3010

    int16_t ChOption[8];    // Per channel analog options;
                            // now:bit 0...10 analog gain (1,2,4,8 ... 1000)
    float AnaGain[8];       // User gain correction for conversion from voltage
                            // to real units ,   per channel
	//MATLAB custom redefiniton
    char AnaUnit[8*6];     // Measurement unit for analog channels: max 5
                            // chars/name ended each by a byte = 0
	//MATLAB custom redefiniton
    char AnaName[8*11];    // Channel name for the first 8 analog channels:
                            // max 10 chars/name ended each by a byte = 0

    int32_t lFirstImage;    // Range of images for continuous recording:
                            // first image
    uint32_t dwImageCount;  // Image count for continuous recording;
                            // used also for signal recording
    int16_t nQFactor;       // Quality  -  for saving to compressed file at
                            // continuous recording; range 2...255
    uint16_t wCineFileType; // Cine file type  -  for continuous recording
	//MATLAB custom redefiniton
    char szCinePath[4 * OLDMAXFILENAME]; //4 paths to save cine files - for
                            // continuous recording. After upgrading to Win32
                            // this still remained 65 bytes long each
                            // GetShortPathName is used for the filenames
                            // saved here

    uint16_t Res14;         // ---TBI bMainsFreq (Mains frequency:
                            // TRUE = 60Hz USA,  FALSE = 50Hz
                            // Europe, for signal view in DSP)

                            // Time board - settings for PC104 irig board
                            // used in Phantom v3 not used anymore after v3
    uint8_t Res15;          // ---TBI  bTimeCode;
                            // Time code: IRIG_B, NASA36, IRIG-A
    uint8_t Res16;          // ---TBI bPriority
                            // Time code has priority over PPS
    uint16_t Res17;         // ---TBI wLeapSecDY
                            // Next day of year with leap second
    double Res18;           // ---TBI dDelayTC Propagation delay for time code
    double Res19;           // ---TBI dDelayPPS Propagation delay for PPS

    uint16_t Res20;         // ---TBI  GenBits
    int32_t Res1;           // ---TBI
    int32_t Res2;           // ---TBI
    int32_t Res3;           // ---TBI

    uint16_t ImWidth;       // Image dimensions in v4 and newer cameras: Width
    uint16_t ImHeight;      // Image height

    uint16_t EDRShutter16;  // ---UPDF replaced by EDRShutterNs
    uint32_t Serial;        // Camera serial number. For firewire cameras you
                            // have a translated value here:
                            // factory serial + 0x58000
    int32_t Saturation;     // ---UPDF replaced by float fSaturation
                            // Color saturation adjustmment [-100,   100] neutral 0

    uint8_t Res5;           // ---TBI
    uint32_t AutoExposure;  // Autoexposure control
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
    bool32_t bFlipH;        // Flips image horizontally
    bool32_t bFlipV;        // Flips image vertically;
    uint32_t Grid;          // Displays a crosshair or a grid in setup, 0=no grid
                            // 2=cross hair, 8= grid with 8 intervals

    uint32_t FrameRateInt;  // ---UPDF replaced by dFrameRate (double)
							// Frame rate in frames per seconds, as 32 bit integer
    uint32_t Shutter;       // ---UPDF replaced by ShutterNs
                            // (here the value is in microseconds)
    uint32_t EDRShutter;    // ---UPDF replaced by EDRShutterNs
                            // (here the value is in microseconds)
    uint32_t PostTrigger;   // Post trigger frames, measured in frames
    uint32_t FrameDelay;    // ---UPDF replaced by FrameDelayNs
                            // (here the value is in microseconds)

    bool32_t bEnableColor;  // User option: when 0 forces gray images from
                            // color cameras

    uint32_t CameraVersion; // The version of camera hardware (without decimal
                            // point). Examples of cameras produced after the
                            // year 2000
                            // Firewire: 4, 5, 6
                            // Ethernet: 42 43 51 7 72 73 9 91 10
                            // 650 (p65) 660 (hd)  ....
    uint32_t FirmwareVersion;// Firmware version
    uint32_t SoftwareVersion;// Phantom software version
                            // End of SETUP in software version 551 (May 2001)

    int32_t RecordingTimeZone;// The time zone active during the recording of
                            // the cine
                            // End of SETUP in software version 552 (May 2001)

    uint32_t CFA;               // Code for the Color Filter Array of the sensor
                            // CFA_NONE=0,(gray) CFA_VRI=1(gbrg/rggb),
                            // CFA_VRIV6=2(bggr/grbg), CFA_BAYER=3(gb/rg)
                            // CFA_BAYERFLIP=4 (rg/gb)
                            // high byte carries info about color/gray heads at
                            // v6 and v6.2
                            // Masks: 0x80000000: TLgray 0x40000000: TRgray
                            // 0x20000000: BLgray 0x10000000: BRgray

    //Final adjustments after image processing:
    int32_t Bright;         // ---UPDF replaced by fOffset
                            // Brightness -100...100 neutral:0
    int32_t Contrast;       // ---UPDF replaced by fGain
                            // -100...100 neutral:0
    int32_t Gamma;          // ---UPDF replaced by fGamma
                            // -100...100 neutral:0

    uint32_t Res21;         // ---TBI

    uint32_t AutoExpLevel;  // Level for autoexposure control
    uint32_t AutoExpSpeed;  // Speed for autoexposure control
    RECT AutoExpRect;     // Rectangle for autoexposure control

    float WBGainR0;			// Gain adjust on R,B components, for white balance,      
    float WBGainB0;			// at Recording
    float WBGainR1;			// 1.0 = do nothing,
    float WBGainB1;			// index 0: all image for v4,5,7... 
    float WBGainR2;			// and TL head for v6, v6.2 (multihead)
    float WBGainB2;			// index 1, 2, 3 :   TR, BL, BR for multihead
    float WBGainR3;
    float WBGainB3;
	
    int32_t Rotate;         // Rotate the image 0=do nothing
                            // +90=counterclockwise -90=clockwise
                            // End of SETUP in software version 578 (Nov 2002)

    WBGAIN WBView;          // White balance to apply on color interpolated Cines

    uint32_t RealBPP;       // Current number of bits per pixel
							// used to store images of this cine

    //First degree function to convert the 16 bits pixels to 8 bit
    //(for display or file convert)
    uint32_t Conv8Min;      // ---TBI
                            // Minimum value when converting to 8 bits
    uint32_t Conv8Max;      // ---UPDF replaced by fGain16_8
                            // Max value when converting to 8 bits

    int32_t FilterCode;     // ImageProcessing: area processing code
    int32_t FilterParam;    // ImageProcessing: optional parameter
    IMFILTER UF;            // User filter: a 3x3 or 5x5 user convolution filter

    uint32_t BlackCalSVer;  // Software Version used for Black Reference
    uint32_t WhiteCalSVer;  // Software Version used for White Calibration
    uint32_t GrayCalSVer;   // Software Version used for Gray Calibration
    bool32_t bStampTime;    // Stamp time (in continuous recording)
                            // 1 = absolute time, 3 = from trigger
                            // End of SETUP in software version 605 (Nov 2003)

    uint32_t SoundDest;     // Sound device 0: none, 1: Speaker, 2: sound board

    //Frame rate profile
    uint32_t FRPSteps;      // Suplimentary steps in frame rate profile
                            // 0 means no frame rate profile
    int32_t FRPImgNr[16];   // Image number where to change the rate and/or
                            // exposure allocated for 16 points (4 available
                            // in v7)
    uint32_t FRPRate[16];   // New value for frame rate (fps)
    uint32_t FRPExp[16];    // New value for exposure
                            // (nanoseconds, not implemented in cameras)

    //Multicine partition
    int32_t MCCnt;          // Partition count (= cine count - 1)
                            // Preview cine does not need a partition
    float MCPercent[64];    // Percent of memory used for partitions
                            // Allocated for 64 partitions
                            // Not used at ph16 cameras - all partitions are equal in size
							// Ph16 cameras can have more than 64 partitions, only first 64 percents are stored here.
                            // End of SETUP in software version 606 (May 2004)

    // CALIBration on Current Image (CSR, current session reference)
    uint32_t CICalib;       // This cine or this stg is the result of
                            // a current image calibration
                            // masks: 1 BlackRef, 2 WhiteCalib, 4 GrayCheck
                            // Last cicalib done at the acqui params:
    uint32_t CalibWidth;    // Image dimensions
    uint32_t CalibHeight;
    uint32_t CalibRate;     // Frame rate (frames per second)
    uint32_t CalibExp;      // Exposure duration (nanoseconds)
    uint32_t CalibEDR;      // EDR (nanoseconds)
    uint32_t CalibTemp;     // Sensor Temperature

    uint32_t HeadSerial[4]; // Head serials for ethernet multihead cameras
                            // (v6.2) When multiple heads are saved in a file,
                            // the serials for existing heads are not zero
                            // When one head is saved in a file its serial is
                            // in HeadSerial[0] and the other head serials
                            // are 0xFFffFFff
                            // End of SETUP in software version 607 (Oct 2004)

    uint32_t RangeCode;     // Range data code: describes the range data format
    uint32_t RangeSize;     // Range data,  per image size

    uint32_t Decimation;    // Factor to reduce the frame rate when sending
                            //the images to i3 external memory by fiber
                            // End of SETUP in software version 614 (Feb 2005)

    uint32_t MasterSerial;  // Master camera Serial for external sync. 0 means
                            // none (this camera is not a slave of another
                            // camera)
                            // End of SETUP in software version 624 (Jun 2005)

    uint32_t Sensor;        // Camera sensor code
                            // End of SETUP in software version 625 (Jul 2005)

    //Acquisition parameters in nanoseconds
    uint32_t ShutterNs;     // Exposure, in nanoseconds
    uint32_t EDRShutterNs;  // EDRExp, in nanoseconds
    uint32_t FrameDelayNs;  // FrameDelay, in nanoseconds
                            // End of SETUP in software version 631 (Oct 2005)

    //Stamp outside the acquired image
    //(this increases the image size by adding a border with text information)
    uint32_t ImPosXAcq;     // Acquired image horizontal offset in
                            // sideStamped image
    uint32_t ImPosYAcq;     // Acquired image vertical offset in sideStamped
                            // image
    uint32_t ImWidthAcq;    // Acquired image width  (different value from
                            // ImWidth if sideStamped file)
    uint32_t ImHeightAcq;   // Acquired image height (different value from
                            // ImHeight if sideStamped file)

    char Description[MAXLENDESCRIPTION];//User description or comments
                                        //(enlarged to 4096 characters)
                            // End of SETUP in software version 637 (Jul 2006)

    bool32_t RisingEdge;    // TRUE rising, FALSE falling
    uint32_t FilterTime;    // time constant
    bool32_t LongReady;     // If TRUE the Ready is 1 from the start
                            // to the end of recording (needed for signal
                            // acquisition)
    bool32_t ShutterOff;    // Shutter off - to force maximum exposure for PIV
                            // End of SETUP in software version 658 (Mar 2008)

    uint8_t Res4[16];       // ---TBI
                            // End of SETUP in software version 663 (May 2008)

    bool32_t bMetaWB;       // pixels value does not have WB applied
                            // (or any other processing)
    int32_t Hue;            // ---UPDF replaced by float fHue
                            // hue corection (degrees: -180 ...180)
                            // End of SETUP in software version 671 (May 2009)

    int32_t BlackLevel;     // Black level in the raw pixels
    int32_t WhiteLevel;     // White level in the raw pixels

    char  LensDescription[MAXSTDSTRSZ];
							// text with the producer, model,
                            // focal range etc ...
    float LensAperture;     // aperture f number
    float LensFocusDistance;// distance where the objects are in  focus in
                            // meters, not available from Canon motorized lens
    float LensFocalLength;  // current focal length; (zoom factor)
                            // End of SETUP in software version 691 (Jul 2010)

    //image adjustment
    float fOffset;          // [-1.0, 1.0], neutral 0.0;
                            // 1.0 means shift by the maximum pixel value
    float fGain;            // [0.0, Max], neutral 1.0;
    float fSaturation;      // [0.0, Max], neutral 1.0;

    float fHue;             // [-180.0, 180.0] neutral 0;
                            // degrees and fractions of degree to rotate the hue

    float fGamma;           // [0.0, Max], neutral 1.0;  global gamma
                            // (or green gamma)
    float fGammaR;          // per component gammma (to be added to the field
                            // Gamma)
                            // 0 means neutral
    float fGammaB;

    float fFlare;           // [-1.0, 1.0], neutral 0.0;
                            // 1.0 means shift by the maximum pixel value
                            // pre White Balance offset

    float fPedestalR;       // [-1.0, 1.0], neutral 0.0;
                            // 1.0 means shift by the maximum pixel value
    float fPedestalG;       // after gamma offset
    float fPedestalB;
    float fChroma;          // [0.0, Max], neutral 1.0;
                            // chrominance adjustment (after gamma)
    char  ToneLabel[256];
    int32_t   TonePoints;
    float fTone[32*2];      // up to 32  points  + 0.0,0.0  1.0,1.0
                            // defining a LUT using spline curves

    char  UserMatrixLabel[256];
    bool32_t  EnableMatrices;
    float cmUser[9];        // user color matrix

    bool32_t  EnableCrop;   // The Output image will contains only a rectangle
                            // portion of the input image
    RECT  CropRect;
    bool32_t  EnableResample;// Resample image to a desired output Resolution
    uint32_t  ResampleWidth;
    uint32_t  ResampleHeight;

    float fGain16_8;        // Gain coefficient used when converting to 8bps
                            // Input pixels (bitdepth>8) are multiplied by
                            // the factor:  fGain16_8 * (2**8 / 2**bitdepth)
                            // End of SETUP in software version 693 (Oct 2010)

    uint32_t FRPShape[16];  // 0: flat,  1 ramp
    TC TrigTC;              // Trigger frame SMPTE time code and user bits
    float fPbRate;          // Video playback rate (fps) active when the cine
                            // was captured
    float fTcRate;          // Playback rate (fps) used for generating SMPTE
                            // time code
                            // End of SETUP in software version 701 (Apr 2011)

    char CineName[MAXSTDSTRSZ];
							// Cine name
                            // End of SETUP in software version 705 (June 2011)

     //Per component gain - user adjustment    [0.0, Max], neutral 1.0;
    float fGainR;
    float fGainG;
    float fGainB;

    // RGB color calibration matrix bring camera pixels to rec 709
    // It includes the white balance set into the ph16 cameras using fWBTemp and fWBCc
    // and the original factory calibration
    // The cine player should decompose this matrix in two components: a diagonal 
    // one with the white balance to be applied before interpolation and a 
    // normalized one to be applied after interpolation
    float cmCalib[9];

    // White balance based on color temperature and color compensation index
    // its effect is included in the cmCalib.
    float fWBTemp;
    float fWBCc;

    //original calibration matrices  :  used to calculate cmCalib in the camera
    char CalibrationInfo[1024];

    //Optical filter matrix  :  used to calculate cmCalib in the camera
    char OpticalFilter[1024];
                            // End of SETUP in software version 709 (September 2011)
	//Current position and status info as received from a GPS receiver
	char GpsInfo[MAXSTDSTRSZ];
	// Unique cine identifier
	char Uuid[MAXSTDSTRSZ];
							// End of SETUP in software version 719
	// The name of the application which created this cine
	char CreatedBy[MAXSTDSTRSZ];
							// End of SETUP in software version 720
	// Acquisition bit depth. It can be 8, 10, 12 or 14
	uint32_t RecBPP;		

	// Description of the minimum format out of all formats the images of this cine
	// have been represented on since the moment of acquisition.
	uint16_t LowestFormatBPP;		
	uint16_t LowestFormatQ;
							// End of SETUP in software version 731

	float fToe;				// Controls the gamma curve in the blacks.
							// Neutral is 1.0f.
							// Decreasing fToe lifts the blacks, while
							// increasing it compresses them.
	uint32_t LogMode;		// Configures the log mode.
							// 0 - log mode disabled.
							// 1, 2, etc - log mode enabled.
							// If log mode enabled, gain, gamma, the pedestals,
							// r/g/b gains, offset and flare are inactive.
							// Camera model string.
	char CameraModel[MAXSTDSTRSZ];
							// End of SETUP in software version 742	

	uint32_t WBType;		// For raw color cines, it describes how meta WB is stored.
							// If bit 0 is set - wb is stored in WBGain field.
							// If bit 1 is set - wb is stored in fWBTemp, fWBCc fields.						
	float fDecimation;		// Decimation coefficient employed when this cine was saved to file.
							// End of SETUP in software version 745

	uint32_t MagSerial;		// The serial of the magazine where the cine was recorded or stored (if any, null otherwise)
	uint32_t CSSerial;		// Cine Save serial: The serial of the device (camera, cine station) used to save the cine to file 
	double dFrameRate;		// High precision acquisition frame rate, replace uint32_t FrameRate
							// End of SETUP in software version 751


    //VRI internal note: Size checked structure.
    //Update oldcomp.c if new fields are added
    //------------------------------------------------------------------------
} SETUP, *PSETUP;
/*****************************************************************************/

#pragma pack(pop)

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
//MATLAB-------------------->
typedef int HRESULT;

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
//<----------------MATLAB END
#endif

// Our image header = Windows BITMAPINFOHEADER + extensions
typedef struct tagIH
{
    DWORD      biSize;          // not used
    LONG       biWidth;         // width
    LONG       biHeight;        // height
    WORD       biPlanes;        // not used
    WORD       biBitCount;      // bpp= 8,16,24,48 (maybe 32, 96)
    DWORD      biCompression;   // format RGB uncompressed, packed ...
    DWORD      biSizeImage;     // not used
    LONG       biXPelsPerMeter; // not used - if not changing
    LONG       biYPelsPerMeter; // not used - if not changing
    DWORD      biClrUsed;       // not used
    DWORD      biClrImportant;  // MaxPix+1

    //Here BITMAPINFOHEADER ends

    int       BlackLevel;       // Black level (now: 0 or 4 on 8 bits,
                                // proportional on > 8bits)
    int       WhiteLevel;       // White level (now: MaxPix or MaxPix-1,
                                // proportional on > 8bits)
} IH, *PIH;
/*****************************************************************************/

// PhProcessImage parameters
typedef struct tagREDUCE16TO8PARAMS
{
    float fGain16_8;
} REDUCE16TO8PARAMS, *PREDUCE16TO8PARAMS;

// Signal acquisition (Data Translation 9802)
#define MAXBINCNT 128   //simulated values
#define MAXANACNT 128

// Masks in the SigOption field
#define MAXSAMPLES 1

// Masks in the AnaOption field
#define BIPOLAR		1	//+ and - values  and signed encoding
#define DIFF		2	//differential input
#define ENCODING  (4+8)	//value encoding 0=12 bits(from16)  1=16 bits
						//2=double(64bit) 3=reserved
#define BITENC      2	//starting with bit 2

/*****************************************************************************/

#if !defined(CFA_VRI)

//Color Filter Array used on the sensor
//In mixed multihead system the gray heads have also some of the msbit set (see XX_GRAY below)
#define CFA_NONE        0     //gray sensor
#define CFA_VRI         1     //gbrg/rggb
#define CFA_VRIV6       2     //bggr/grbg
#define CFA_BAYER       3     //gb/rg
#define CFA_BAYERFLIP   4     //rg/gb
#define CFA_MASK  0xff  //only lsbyte is used for cfa code, the rest is for multiheads

//these masks combined with  CFA_VRIV6  describe a mixed (gray&color) image
#define TL_GRAY  0x80000000    //top left head of v6 multihead system is color
#define TR_GRAY  0x40000000    //top right head of v6 multihead system is color
#define BL_GRAY  0x20000000    //bottom left head of v6 multihead system is color
#define BR_GRAY  0x10000000    //bottom right head of v6 multihead system is color

#define ALLHEADS_GRAY (TL_GRAY|TR_GRAY|BL_GRAY|BR_GRAY)
#endif
/*****************************************************************************/

// Processing options: speed / quality
#define FAST_ALGORITHM 1
#define BEST_ALGORITHM 5
#define NO_DEMOSAICING 6
/*****************************************************************************/

// Filter codes
#define PREWITT_3x3_V   1
#define PREWITT_3x3_H   2
#define SOBEL_3x3_V     3
#define SOBEL_3x3_H     4
#define LAPLACIAN_3x3   5
#define LAPLACIAN_5x5   6
#define GAUSSIAN_3x3    7
#define GAUSSIAN_5x5    8
#define HIPASS_3x3      9
#define HIPASS_5x5     10
#define SHARPEN_3x3    11

#define USERFILTER     -1
/*****************************************************************************/

// PhProcessImage selectors
#define IMG_PROC_REDUCE16TO8             1
/*****************************************************************************/

// Function prototypes

// PhInterpolateColor convert a 8 (or 16) bitsperpixel bitmap from a color
// Phantom camera to a 24 (or 48) bpp full color bitmap (BGR color order).
// Use BEST_ALGORITHM as the last parameter and CFA_VRI as the ColorFilterArray
// code for Phantom v4,v5,v6.
// _Note_: It is very important to allocate the pPixels buffer 3 times larger
// than the unintepolated pixel array size because you will get the result in
// the same buffer
// All parameters are inputs to the procedure except pPixels: this buffer is both
// an input and an output
EXIMPROC void PhInterpolateColor(PBITMAPINFOHEADER pBMIH, PBYTE pPixel, UINT CFA, UINT Algorithm);
/*****************************************************************************/

EXIMPROC HRESULT PhProcessImage(PBYTE pPixelSrc, PBYTE pPixelDest, PIH pIH, UINT ProcID, PVOID pProcParams);
EXIMPROC HRESULT PhIHtoBITMAPINFOHEADER(PIH pIH, PBITMAPINFOHEADER pBMIH);
/*****************************************************************************/

// Compute the histogram and a color weights on a DIB image
EXIMPROC void PhImHisto(PBITMAPINFOHEADER pBMIH, PBYTE pPixel,
                        UINT HistoSize, UINT Color, PUINT pHisto,
                        PUINT pAvgR, PUINT pAvgG, PUINT pAvgB);
/*****************************************************************************/

// Apply white balance correction to an uninterpolated image
EXIMPROC void PhWBAdjustUnint(PBITMAPINFOHEADER pBMIH, PBYTE pPixel,
                              UINT CFA, PWBGAIN pWBg);
// Convert a monochrome image to a color bitmap
EXIMPROC void PhTriplicateGray(PBITMAPINFOHEADER pBMIH, PBYTE pPixel);
/*****************************************************************************/

// Version of above function without structure parameters to make the use easier from
// Mathlab, LabView, Diadem, Visual Basic  etc.
// Suggestion for the future: Try to access the structure as array of integers!
// PBITMAPINFOHEADER was replaced by Width, Height (image dimensions)
// and BitCount(8 for gray images and 24 for color images)
EXIMPROC void PhInterpolateColorPAR(int Width, int Height, int BitCount, unsigned char * pPixel, int CFA, int Algorithm);
EXIMPROC void PhFlipsPAR(int Width, int Height, int BitCount, unsigned char * pPixel, int bFlipH, int bFlipV);
EXIMPROC void PhSaturationPAR(int Width, int Height, int BitCount, unsigned char * pPixel, int nSaturation);
EXIMPROC void PhMakeColorPAR(int Width, int Height, int BitCount, unsigned char * pPixel, int CFA, int Saturation,
                             int bFlipH, int bFlipV, int Algorithm);
/*****************************************************************************/

///////////////////////////////////////////////////////////////////////////////
//								DEPRECATED									 //
///////////////////////////////////////////////////////////////////////////////

//Image processing options for the routine PhImProc()
typedef struct tagIMPROCOPTIONS
{
    int Bright;         //Brightness        (-100, 100; 0=do nothing)
    int Contrast;       //Contrast          (-100, 100; 0=do nothing)
    float Gamma;        //Gamma             (1.0=do nothing)

    int Saturation;     //Color saturation  (-100, 100; 0=do nothing)
    BOOL FlipH;         //flip horizontal
    BOOL FlipV;         //flip vertical
    int Rotate;         //rotate (+90 or -90), for +-180 use both flips

    WBGAIN WBView;      //White balance adjustment for view cine from file
    //1.0=do nothing

    int FilterCode;     //predefined filter or user filter : 0: none
    int FilterParam;    //filter parameter
    IMFILTER UF;        //user filter, used if FilterCode==-1

    int Hue;            //hue corection (degrees: -180 ...180)

    /*
        RGBQUAD *pCzTable;  //colorization table
    */

    int Reserved[4];    //reserved for future expansion (please set
    //them to 0)
} IMPROCOPTIONS, *PIMPROCOPTIONS;
/*****************************************************************************/

// Range of pixel values used in conversion from 16 bits to 8 bits
typedef struct tagRANGE
{
    int First;
    UINT Cnt;
} RANGE, *PRANGE;
/*****************************************************************************/

EXIMPROC void PhAdjustToMaxLevels(PBITMAPINFOHEADER pBMIH, PBYTE pPixel, WORD inBlackLevel, WORD inWhiteLevel);
EXIMPROC void PhReduceDIB16To8(PBITMAPINFOHEADER pBMIH, PRANGE pPixRng, PWORD pPixel16, PBYTE pPixel8);
/*****************************************************************************/

//Process an image
EXIMPROC void PhImProc(PBITMAPINFOHEADER pBMIH, PBYTE pPixel, PIMPROCOPTIONS pOpt);
//Convert the image adjustments from the setup structure to IMPROCOPTIONS, to
//be applied to an image using PhImProc
EXIMPROC void PhSetImProcOptions(PIMPROCOPTIONS pOpt, PSETUP pSet);
/*****************************************************************************/

//Flip a standard Windows DIB in the horizontal or vertical direction
EXIMPROC void PhFlips(PBITMAPINFOHEADER pBMIH, PBYTE pPixel, BOOL bFlipH, BOOL bFlipV);
/*****************************************************************************/

//Change the color saturation of a standard Windows DIB. nSaturation is from -100 to 100.
//-100 remove colors and produce a gray image (still 24 bpp)
EXIMPROC void PhSaturation(PBITMAPINFOHEADER pBMIH, PBYTE pPixel, int nSaturation);

// PhMakeColor is intended to be used to interpolate the pixels from uninterpolated cine files
// where information about CFA, Saturation, flipping is available from the SETUP structure
// _Note_: It is very important to allocate the pPixels buffer 3 times larger than the unintepolated
// pixel array size because you will get the result in the same buffer
EXIMPROC void PhMakeColor(PBITMAPINFOHEADER pBMIH, PBYTE pPixel, PSETUP pSet, UINT Algorithm);
EXIMPROC void MakeColor(PBITMAPINFOHEADER pBMIH, PBYTE pPixel, PSETUP pSet);
EXIMPROC void InterpolateColor(PBITMAPINFOHEADER pBMIH, PBYTE pPixel);
EXIMPROC void Flips(PBITMAPINFOHEADER pBMIH, PBYTE pPixel, BOOL bFlipH, BOOL bFlipV);
EXIMPROC void Saturation(PBITMAPINFOHEADER pBMIH, PBYTE pPixel, int nSaturation);
/*****************************************************************************/

#undef EXIMPROC     //avoid conflicts with other similar headers

#ifdef __cplusplus
}
#endif
#endif
