//////////////////////////////////////////////////////////////////////////////////
//  Copyright (C) 1992-2019                                                     //
//       Vision Research Inc. (An AMETEK Company) All Rights Reserved.          //
//                                                                              //
//  The licensed information contained herein is the property of                //
//  Vision Research Inc., Wayne, NJ, USA  and is subject to change              //
//  without notice.                                                             //
//                                                                              //
//  Redistribution and use in source and binary forms, with or without          //
//  modification, are permitted with the following conditions.                  //
//                                                                              //
//  THIS SOFTWARE IS PROVIDED BY VISION RESEARCH INC ``AS IS'' AND              //
//  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE       //
//  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE  //
//  ARE DISCLAIMED.  IN NO EVENT SHALL VISION RESEARCH INC BE LIABLE            //
//  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL  //
//  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS     //
//  OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)       //
//  HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT  //
//  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY   //
//  OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF      //
//  SUCH DAMAGE.                                                                //
//                                                                              //
//  Updates:                                                                    //
//              June 28, 2017   Updated for 770 SDK Release                     //
//              July 20, 2017   Updated for 770 SDK Release                     //
//              July 20, 2017   Ver 2, Updated for 770 SDK Release              //
//              Sept 05, 2017   Ver 3, Updated for 770 SDK Release              //
//              Sept 14, 2017   Ver 4, Updated for 770 SDK Release              //
//              Oct   4, 2017   Ver 5, Minor Cleanup no functional change       //
//              June 13, 2018   Ver 6, SensorMode support                       //
//              Aug  14, 2018   Ver 7, Added New PhRange DLL                    //
//              Jan  31, 2019   Ver 8, Added New Nucleus functions              //
//                                                                              //
//////////////////////////////////////////////////////////////////////////////////

using System;
using System.Collections.Generic;
using System.Text;
using System.Runtime.InteropServices;
using System.Drawing;


namespace PhSharp
{
    [UnmanagedFunctionPointer(CallingConvention.Winapi)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public delegate bool PROGRESSCALLBACK(UInt32 cameraNo, UInt32 percent);

    ///////////////////////////////////////////////////////////
    ////////////////////// Structures /////////////////////////
    ///////////////////////////////////////////////////////////

    #region Structures

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]  //Ansi is C# default
    public struct CameraId
    {
        public uint ip;    //only v4 IP, for v6 to be extended to int64
        public uint serial;

        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 256)]
        public string Name;

        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 200)]
        public string Model;

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 44)]
        public byte[] reserved;
        
        public uint MaxCineCnt;		    // max partition count
        public uint CFA;				// Reserved space for Model was reduced to include other info  
        public uint CamVer;
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential)]
    public struct Cinestatus
    {
        [MarshalAs(UnmanagedType.Bool)]
        public bool Stored;        // Recording of this cine finished
        [MarshalAs(UnmanagedType.Bool)]
        public bool Active;        // Acquisition is currently taking place in this cine
        [MarshalAs(UnmanagedType.Bool)]
        public bool Triggered;     // The cine has received a trigger
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential)]
    public struct ImRange
    {
        [MarshalAs(UnmanagedType.I4)]
        public Int32 First;      // first image number
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 Cnt;       // count of images

        public bool IsFullRange()
        {
            return First == Int32.MinValue && Cnt == UInt32.MaxValue;
        }

        public Int32 LastImage()
        {
            return (int)((long)First + Cnt - 1);
        }

        public void SetFullRange()
        {
            First = Int32.MinValue;
            Cnt = UInt32.MaxValue;
        }

        public ImRange Clone()
        {
            ImRange rng = new ImRange();
            rng.First = First;
            rng.Cnt = Cnt;
            return rng;
        }
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential)]
    public struct PulseParam
    {
        public uint Size;           // for versioning in future if needed
        [MarshalAs(UnmanagedType.Bool)]
        public bool Invert;         // Invert signal at output
        [MarshalAs(UnmanagedType.Bool)]
        public bool Falling;        // Negative fixed width pulse triggered by falling input
        [MarshalAs(UnmanagedType.R8)]
        public double Delay;        // Delay from input edges to output edges
        public double Width;        // If not 0 will create a fixed width pulse
        public double Filter;       // Change status of the output after the input was 
                                    // in the new status for the specified interval of time
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT
    {
        [MarshalAs(UnmanagedType.I4)]
        public Int32 Left;
        [MarshalAs(UnmanagedType.I4)]
        public Int32 Top;
        [MarshalAs(UnmanagedType.I4)]
        public Int32 Right;
        [MarshalAs(UnmanagedType.I4)]
        public Int32 Bottom;

        public RECT(int left, int top, int right, int bottom)
        {
            Left = left;
            Top = top;
            Right = right;
            Bottom = bottom;
        }

        public RECT(Rectangle r)
        {
            Left = r.X;
            Top = r.Y;
            Right = r.Right;
            Bottom = r.Bottom;
        }

        public int Width
        {
            get { return Right - Left; }
            set { Right = Left + value; }
        }

        public int Height
        {
            get { return Bottom - Top; }
            set { Bottom = Top + value; }
        }
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential)]
    public struct Time64
    {
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 fractions;
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 seconds;

        public override bool Equals(object obj)
        {
            if (obj is Time64)
            {
                Time64 timeCmp = (Time64)obj;
                return this.seconds == timeCmp.seconds && this.fractions == timeCmp.fractions;
            }
            else
                return false;
        }

        public override int GetHashCode()
        {
            return base.GetHashCode();
        }
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential)]
    public struct AcquiParams
    {
        public uint ImWidth;            // Image dimensions
        public uint ImHeight;

        public uint FrameRateInt;       // Frame rate (frames per second, integer) changed name  
                                        // Obsolete: Not to be used anymore. 
                                        // Replaced it in applications by dFrameRate (frames per second, double)
                                        // Try to provide here rounded dFrameRate, for compatibility with older version of applications

        public uint Exposure;           // Exposure duration (nanoseconds)
        public uint EDRExposure;        // EDR (extended dynamic range) exposure duration (nanoseconds)
        public uint ImDelay;            // Image delay for the SyncImaging mode (nanoseconds)
                                        // (not available in all models)

        public uint PTFrames;           // Count of frames to be recorded after the trigger
        public uint ImCount;            // Count of images in this cine (read only field)
        public SyncMode SyncImaging;    // Sync imaging mode: acquire when an external clock rise
        public uint AutoExposure;       // Control of the exposure duration from the subject light 
                                        // bit 0		0		- disable AUTOEXP
                                        //				1		- enable AUTOEXP
                                        // bit 1		0		- lock at trigger
                                        //				1		- active after trigger
										//						Always 0 for cameras using V2 autoexp, that don't
										//                      support Lock at trigger
                                        //						Read only for cameras using V2 autoexp
                                        // bit 3, 2		Cameras using V1 autoexp
                                        //				00		- for all cameras using V1 autoexp
                                        //				Cameras using V2 autoexp
                                        //				01		- average
                                        //				10		- spot
                                        //				11		- center weighted

        public uint AutoExpLevel;       // Level for autoexposure control
        public uint AutoExpSpeed;       // Speed for autoexposure control

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
        public int[] AutoExpRect;       // Rectangle for autoexposure control /*!!*/

        public int Reserved1;           // LockToIRIG removed, replaced by a special value of SyncImaging

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 2)]
        public uint[] TriggerTime;      // Trigger time for the recorded cine (read only field)	

        public uint RecordedCount;      // initially recorded count; ImCount may be smaller
                                        // if the cine was partially saved to NonVolatile 
                                        // memory (read-only field)

        public int FirstIm;             // First image number of this cine; may be different
                                        // from PTFrames-ImCount if the cine was partially
                                        // saved to Non-Volatile memory (read-only field)

        //Frame rate profile
        public uint FRPSteps;           // Supplementary steps in frame rate profile
                                        // 0 means no frame rate profile 
   
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public int[] FRPImgNr;          // Image number where to change the rate and/or exposure
                                        // allocated for 16 points (4 available in v7)

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public uint[] FRPRate;          // new value for frame rate

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public uint[] FRPExp;           // new value for exposure    

        public uint Decimation;         // Reduce the frame rate when sending the images to i3 through fiber
        public uint BitDepth;           // Bit depth of the cines (read-only field) - usefull for flash; the 
                                        // images from flash have to be requested at the real bit depth.  
                                        // The images from RAM can be requested at different bit depth 

        public uint CamGainRed;         // Gains attached to a cine saved in the magazine
        public uint CamGainGreen;       // Normally they tell the White balance at recording time
        public uint CamGainBlue;
        public uint CamGain;            // global gain

        public uint ShutterOff;         // go to max exposure for piv mode
        public uint CFA;                // Color Filter Array at the recording of the cine

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 256)]
        public byte[] CineName;         // cine name

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4096)]
        public byte[] Description;      // Cine description on max 4095 chars (need space for null)

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public uint[] FRPShape;         // 0: flat,  1 ramp

        public double dFrameRate;       // Overrides older FrameRate (renamed to FrameRateInt)
        //-----------------------------------------------------------------------------------
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]
    public struct CameraOptions
    {
        // Phantom v4-v6
        // Analog video output
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 OSD;                  // enable the On Screen Display

        [MarshalAs(UnmanagedType.U4)]
        public UInt32 VideoSystem;          // Analog video output system 

        // IRIG
        [MarshalAs(UnmanagedType.Bool)]
        public bool ModulatedIRIG;          // bool,IRIG input accept modulated signal     

        //
        // Fields below are used starting with Phantom v7
        //

        [MarshalAs(UnmanagedType.Bool)]
        public bool RisingEdge;             // Trigger: bool, TRUE rising, FALSE falling

        [MarshalAs(UnmanagedType.U4)]
        public UInt32 FilterTime;           // time constant

        // Memory gate input meaning
        [MarshalAs(UnmanagedType.Bool)]
        public bool MemGate;                // bool TRUE: Memgate, FALSE: pretrigger

        [MarshalAs(UnmanagedType.Bool)]
        public bool StartInRec;             // bool TRUE:  Start in recording 
                                            //      FALSE: Start in preview wait 
                                            //      pretrigger to start the recording

        [MarshalAs(UnmanagedType.Bool)]
        public bool Color;                  // bool, create color video signal

        [MarshalAs(UnmanagedType.Bool)]
        public bool TestImage;              // bool, replace the FBM image by a test image (colored bars)

        // OnScreenDisplay colors
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4 * 8)]
        public byte[] OSDColor;             // set of colors used for the OSD painting 
                                            // Background  
                                            // Wtr mode     
                                            // Trig mode    
                                            // Cst mode     
                                            // Pre-trig mode
                                            // Id fields   
                                            // Acqui fields
                                            // Status, cine

        [MarshalAs(UnmanagedType.Bool)]
        public bool OSDOpaque;              // bool, OSD test is opaque or transparent

        [MarshalAs(UnmanagedType.I4)]
        public Int32 OSDLeft;               // limits of the OSD text on screen

        [MarshalAs(UnmanagedType.I4)]
        public Int32 OSDTop;

        [MarshalAs(UnmanagedType.I4)]
        public Int32 OSDBottom;

        [MarshalAs(UnmanagedType.I4)]
        public Int32 ImageX;                // image position on screen

        [MarshalAs(UnmanagedType.I4)]
        public Int32 ImageY;

        //
        // Automation on v7
        //
        [MarshalAs(UnmanagedType.Bool)]
        public bool AutoSaveNVM;            // save the cine to the nvm

        [MarshalAs(UnmanagedType.Bool)]
        public bool AutoSaveFile;           // save the cine to a file 

        [MarshalAs(UnmanagedType.Bool)]
        public bool AutoPlay;               // playback to video

        [MarshalAs(UnmanagedType.Bool)]
        public bool AutoCapture;            // restart capture

        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = PhFile.MAX_PATH)]
        public String FileName;             // filename to save (as seen from camera)

        [MarshalAs(UnmanagedType.Struct)]
        public ImRange SaveRng;             // image range for the above operations

        [MarshalAs(UnmanagedType.Bool)]
        public bool LongReady;              // If FALSE the Ready signal is 1 from the start 
                                            // of recording until the cine is triggered
                                            // If TRUE the Ready is 1 from the start 
                                            // to the end of recording

        [MarshalAs(UnmanagedType.Bool)]
        public bool RealTimeOutput;         // Enable the sending of the acquired image on fiber 

        [MarshalAs(UnmanagedType.U4)]
        public UInt32 RangeData;            // 0: none, 1:64bits, 2:128bits

        //
        // external memory slice
        //
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 SourceCamSer;         // Source camera serial 

        [MarshalAs(UnmanagedType.U4)]
        public UInt32 SliceNr;              // slice number (0, 1, 2 ....)

        [MarshalAs(UnmanagedType.U4)]
        public UInt32 SliceCnt;             // total count of slices connected to a certain camera

        [MarshalAs(UnmanagedType.Bool)]
        public bool FRPi3Trig;              // Frame rate profile start at i3 trigger

        [MarshalAs(UnmanagedType.U4)]
        public UInt32 UT;                   // OSD: Display time as: 0 LocalTime,  1: Universal Time (GMT)

        [MarshalAs(UnmanagedType.I4)]
        public Int32 AutoSaveFormat;        // save to flash or direct save to file from camera
                                            // -8 -16 =  save 8 bit or 16 bits

        [MarshalAs(UnmanagedType.U4)]
        public UInt32 SourceCamVer;         // Source camera version (external memory slice)

        [MarshalAs(UnmanagedType.U4)]
        public UInt32 RAMBitDepth;          // Set the current bit depth for pixel storage in the camera video RAM

        [MarshalAs(UnmanagedType.I4)]
        public Int32 VideoTone;             // tone curve to select for video

        [MarshalAs(UnmanagedType.I4)]
        public Int32 VideoZoom;             // Zoom of the video image: 0: Fit,  1: Zoom1

        [MarshalAs(UnmanagedType.I4)]
        public Int32 FormatWidth;           // Format rectangle to overlap on the video image

        [MarshalAs(UnmanagedType.I4)]
        public Int32 FormatHeight;

        [MarshalAs(UnmanagedType.U4)]
        public UInt32 AutoPlayCnt;          // repeat count for the playback to video

        [MarshalAs(UnmanagedType.U4)]
        public UInt32 OSDDisable;           // selective disable of the analog and digital OSD

        [MarshalAs(UnmanagedType.Bool)]
        public bool RecToMag;               // Record to the flash magazine

        [MarshalAs(UnmanagedType.Bool)]
        public bool IrigOut;                // Change the Strobe pin to Irig Out at Miro cameras (if TRUE)

        [MarshalAs(UnmanagedType.I4)]
        public Int32 FormatXOffset;		    // x offset for the format rectangle to overlap on the video image

        [MarshalAs(UnmanagedType.I4)]
        public Int32 FormatYOffset;		    // y offset for the format rectangle to overlap on the video image
    }

    #endregion

    ///////////////////////////////////////////////////////////
    ///////////////////////// enums ///////////////////////////
    ///////////////////////////////////////////////////////////

    #region enums

    //
    ////////////////
    //
    public enum AUXSIG : int
    {
        STROBE = 0,
        IRIGOUT = 1,
        EVENT = 2,
        MEMGATE = 3
    }

    //
    ////////////////
    //
    public enum AUX1SIG : int
    {
        STROBE = 0,
        EVENT = 1,
        MEMGATE = 2,
        FSYNC = 3
    }

    //
    ////////////////
    //
    public enum AUX2SIG : int
    {
        READY = 0,
        STROBE = 1,
        AES_EBU_OUT = 2
    }

    //
    ////////////////
    //
    public enum AUX3SIG : int
    {
        IRIGOUT = 0,
        STROBE = 1
    }

    //
    ////////////////
    //
    public enum BatteryCtrlFunction : int
    {
        BATTERY_ARM_CTRL = 0,
        BATTERY_ARM_ENABLE_CTRL = 1,
        BATTERY_PREVIEW_ENABLE_CTRL = 2,
        BATTERY_CAPTURE_ENABLE_CTRL = 3
    }

    //
    ////////////////
    //
    public enum BatteryState : int
    {
        BATTERY_NOT_PRESENT = 0,
        BATTERY_CHARGING = 1,
        BATTERY_CHARGING_HIGH = 2,
        BATTERY_CHARGED = 3,
        BATTERY_DISCHARGING = 4,
        BATTERY_LOW = 5,
        BATTERY_ARMED = 8,          // This is really just Bit 3  (8 is added to other values if armed)
        BATTERY_FAULT = 16
    }

    //
    ////////////////
    //
    public enum BatteryArmMode : int
    {
        BATTERY_MODE_DISABLE_CHARGING           = 1,    // Bit 0 
        BATTERY_MODE_DISABLE_DISCHARGING_ARMING = 2,    // Bit 1
        BATTERY_MODE_FORCE_ARMING               = 4,    // Bit 2
        BATTERY_MODE_ENABLE_PREVIEW_ARMING      = 8     // Bit 3
    }

    //
    ////////////////
    //
    public enum BatteryTime : int
    {
        BATTERY_RUNTIME_1 = 1,          // 1 Sec 
        BATTERY_RUNTIME_10 = 10,        // 10 Sec 
        BATTERY_RUNTIME_60 = 60,        // 1 Minute 
        BATTERY_RUNTIME_120 = 120,      // 2 Minute 
        BATTERY_RUNTIME_180 = 180,      // 3 Minute 
        BATTERY_RUNTIME_300 = 300,      // 5 Minute 
        BATTERY_RUNTIME_600 = 600       // 10 Minute 
    }

    //
    ////////////////
    //
    public enum CineNumber : int
    {
        //
        // Predefined cines
        //
        CINE_DEFAULT = -2,      // the number of the default cine
        CINE_CURRENT = -1,      // the cine number used to request live images
        CINE_PREVIEW = 0,       // the number of the preview cine
        CINE_FIRST = 1,         // the number of the first cine when emulating 
    }

    //
    ////////////////
    //
    public enum DllOptions : uint
    {
        DO_USEGPU = 3,                  // User option to enable or disable the use of GPU
        DO_IMGTRANSFFMT_UCVIEW = 5,     // Format to be used for transferring cine images from camera when the use case is set to UC_VIEW
                                        // Option meant to reduce the transfer time of images from camera to host
                                        // Uint value holding ((FormatQ << 16) | FormatBPP)
                                        //		FormatQ representation is identical to LowestFormatQ from SETUP
                                        //		FormatBPP representation is identical to LowestFormatBPP from SETUP	

        DO_XIMG_THROTTLE = 6,           // Ximg percentage of maximum transfer speed
        DO_SUPPRESSOFFLINESTAMP = 7     // suppress display of "Offline" stamp on black image, if camera is offline
    }

    //
    ////////////////
    //
    public enum Genlock : int
    {
        DISABLE = 0,
        ENABLE = 1,
        VITC_ENABLE = 3
    }


    //
    // Only a few errors which were needed in code are placed here. 
    // To get associated error message use PhGetErrorMessage
    //
    public enum HRESULT : int
    {
        ERR_UnknownErrorCode = 101,
        ERR_Ok = 0,

        //
        // serious
        //
        ERR_GetImageTimeOut = -217,

        ERR_NoResponseFromCamera = -259,

        ERR_GetTimeTimeOut = -264,
        ERR_GetAudioTimeOut = -266,

        ERR_NotIncreasingTime = -283,
        ERR_BadTriggerTime = -284,
        ERR_TimeOut = -285,

        ERR_BadImageInterval = -291,
        ERR_BadCameraNumber = -292,

        ERR_CineMagBusy = -320,
        ERR_NoCineSaveInProgress = -2031
    }

    //
    ////////////////
    //
    [Flags]
    public enum ImageOptions
    {
        GI_BW = 0,
        GI_INTERPOLATED = 4,
        GI_ONEHEAD = 8,
        GI_HEADMASK = 0xf0,
        GI_BPP12 = 0x100,
        GI_BPP16 = 0x200
    }

    //
    ////////////////
    //
    public enum LogSetCode : uint
    {
        SDLO_PHANTOM = 100,
        SDLO_PHCON = 101,
        SDLO_PHINT = 102,
        SDLO_PHFILE = 103,
        SDLO_PHSIG = 104,
        SDLO_PHSIGV = 105,
        SDLO_TORAM = 106,
        SDLO_PHRANGE = 107
    }

    //
    ////////////////
    //
    public enum LogGetCode : uint
    {
        GDLO_PHANTOM = 200,
        GDLO_PHCON = 201,
        GDLO_PHINT = 202,
        GDLO_PHFILE = 203,
        GDLO_PHSIG = 204,
        GDLO_PHSIGV = 205,
        GDLO_TORAM = 206,
        GDLO_PHRANGE = 207
    }

    //
    ////////////////
    //
    public enum MAGRECORDFORMAT : int
    {
        PACKED10 = 266,
        PRORES_HQ = 516
    }

    //
    ////////////////
    //
    public enum Notification
    {
        ERR_Ok = 0,
        ERR_FalseNotification = 1001,
        ERR_DoubtfullNotification = 1002
    }

    //
    ////////////////
    //
    public enum programmableIoType : int
    {
        PROGRAMMABLE_IO_OFF   = 0,          // Absent / Off disabled etc 
        PROGRAMMABLE_IO_FIXED = 1,          // Fixed 
        PROGRAMMABLE_IO_PROG  = 2           // Programmable 
    }

    //
    ////////////////
    //
    public enum SyncMode : uint
    {
        SYNC_INTERNAL = 0,      // free-run of camera
        SYNC_EXTERNAL = 1,      // locks to the FSYNC input
        SYNC_LOCKTOIRIG = 2,    // locks to IRIG timecode
        SYNC_LOCKTOVIDEO = 3,
        SYNC_SYNCTOTRIGGER = 5
    }

    //
    ////////////////
    //
    public enum TimeCodeOut : uint
    {
        IRIG  = 0,
        SMPTE = 1
    }

    public enum VideoSysCode : int
    {
        VIDEOSYS_NTSC = 0,              // USA analog system
        VIDEOSYS_PAL = 1,               // European analog system
        VIDEOSYS_720P60 = 4,            // Digital HDTV modes: Progressive
        VIDEOSYS_720P50 = 5,
        VIDEOSYS_720P59DOT9 = 12,
        VIDEOSYS_1080P30 = 20,
        VIDEOSYS_1080P25 = 21,
        VIDEOSYS_1080P29DOT9 = 28,
        VIDEOSYS_1080P24 = 36,
        VIDEOSYS_1080P23DOT9 = 44,
        VIDEOSYS_1080PSF30 = 52,        // Progressive split frame
        VIDEOSYS_1080PSF25 = 53,
        VIDEOSYS_1080PSF29DOT9 = 60,
        VIDEOSYS_1080I30 = 68,          // Interlaced
        VIDEOSYS_1080I25 = 69,
        VIDEOSYS_1080I29DOT9 = 76,
        VIDEOSYS_1080PSF24 = 84,
        VIDEOSYS_1080PSF23DOT9 = 92
    };

    //
    ////////////////
    //
    public enum CFA : uint
    {
        CFA_NONE = 0,   // gray - uninterpolated
        CFA_VRI = 1,
        CFA_VRI6 = 2,
        CFA_BAYER = 3,
        CFA_BAYERFLIP = 4,
        CFA_MASK = 0xff
    }

    #endregion

    ///////////////////////////////////////////////////////////
    /////////////////////// Selectors /////////////////////////
    ///////////////////////////////////////////////////////////

    #region Selectors
    public enum Versions : uint
    {
        GV_CAMERA = 1,
        GV_FIRMWARE = 2,
        GV_FPGA = 3,
        GV_PHCON = 4,
        GV_CFA = 5,
        GV_KERNEL = 6,
        GV_MAGAZINE = 7,
        GV_FIRMWAREPACK = 8,
        GV_HEAD_FIRMWARE  = 9,
        GV_HEAD_FPGA = 10,
        GV_HEAD_FIRMWAREPACK = 11
    }

    //
    ////////////////
    //
    public enum CGS : uint
    {
        CineVideoTone = 4097,
        CineName = 4098,
        VideoMarkIn = 4099,
        VideoMarkOut = 4100,
        IsRecorded = 4101,
        HqMode = 4102,
        BurstCount = 4103,
        BurstPeriod = 4104,
        LensDescription = 4105,
        LensAperture = 4106,
        LensFocalLength = 4107,
        ShutterOff = 4108,
        TriggerTime = 4109,

        AutoExpComp = 4200,
        AudioEnable = 4201
    }

    //
    // selection codes for PhGet PhSet
    //
    public enum GS : uint
    {
        //
        // Camera current status information
        //
        HasMechanicalShutter = 1025,
        HasBlackLevel4 = 1027,
        HasCardFlash = 1051,
        Has10G = 2000,
        HasV2AutoExposure = 2001,
		HasV2LockAtTrigger = 2002,
        HasV2ColorMatrices = 8000,
        HasColorMatrices = 8001,

        //
        // Camera current parameters
        //
        SensorTemperature = 1028,
        CameraTemperature = 1029,
        RequestedSensorTemperature = 1031,
        RequestedCameraTemperature = 1032,
        HeadTemperature = 1086,                 // ro   Nano Head FPGA Temperature and Sensor temperature

        VideoPlayCine = 1033,
        VideoPlaySpeed = 1034,
        VideoOutputConfig = 1035,
        MechanicalShutter = 1036,

        HasImageTrig = 1040,
        ImageTrigThreshold = 1041,
        ImageTrigArea = 1042,
        ImageTrigSpeed = 1043,
        ImageTrigMode = 1044,
        ImageTrigRect = 1045,

        AutoProgress = 1046,
        AutoBlackRef = 1047,

        CardFlashAble = 1050,
        CardFlashMounted = 1051,
        CardFlashSizeK = 1052,
        CardFlashFreeK = 1053,
        CardFlashError = 1054,

        IPAddress = 1070,                   // rw current IP address
        EthernetAddress = 1055,             // alias ip
        EthernetMask = 1056,
        EthernetBroadcast = 1057,
        EthernetGateway = 1058,
        Ethernet10GAddress = 1093,          // rw current 10G IP address
        Ethernet10GMask = 1094,             // rw 10G IP subnet mask
        Ethernet10GBroadcast = 1095,        // rw 10G IP broadcast
        EthernetDefaultAddress = 1096,      // ro 1G default IP address (IP address in hardware)

        LensFocus = 1059,		            // wo
        LensAperture = 1060,
        LensApertureRange = 1061,           // ro
        LensDescription = 1062,		        // ro
        LensFocusInProgress = 1063,
        LensFocusAtLimit = 1064,

        Genlock = 1065,
        GenlockStatus = 1066,
        VideoGenlock = 1065,                // two different name (need to keep just in case)
        VideoGenLockStatus = 1066,

        TurboMode = 1068,
        Model = 1069,
        MaxPartitionCount = 1071,
        AuxSignal = 1072,
        TimeCodeOutSignal = 1073,
        Quiet = 1074,
        VFMode = 1076,
        AnamorphicDesqRatio = 1077,
        AudioEnable = 1078,
        ClockPeriod = 1079,             // ro   obtain the camera clock period as a double value (seconds)
        PortCount = 1080,               // ro   how many ports (fixed + programmable)
                                        //      non-zero means ProgIO is available on this camera
        TriggerEdgeAndVoltage = 1081,   // rw   bit 0 rising edge, bit 1 high voltage (6v threshold instead of 1.5v)
        TriggerFilter = 1082,           // rw   filter constant (microseconds)
        TriggerDelay = 1083,            // rw   trigger delay microseconds available at cameras with ProgIO

        HeadSerial = 1085,		        // ro   Nano Head serial Number / available for Nano Cameras

        SensorModesList = 1087,         // ro  Get list of camera Sensor modes;  currently used for Flex 4K GS, VEO 4K and Virgo V2040
        SensorMode = 1088,              // rw  Get/Set Sensor Mode;  currently used for Flex 4K GS, VEO 4K and Virgo V2040
		
        ExpIndex = 1090,                // rw   Exposure Index control
        ExpIndexPresets = 1091,         // ro   Get Exposure Index ISO Table
        BatteryEnable = 1100,           // rw   Enable/Disable battery operation
        BatteryCaptureEnable = 1101,    // rw   Enable/Disable battery operation during capture
        BatteryPreviewEnable = 1102,    // rw   Enable/Disable battery operation during preview
        BatteryWtrRuntime = 1103,       // rw   (cam.wtrruntime) Time in seconds the camera will run on battery in WTR if a cine is not triggered.
        BatteryVoltage = 1104,          // ro   (info.vbatt) Battery voltage level 
        BatteryState = 1105,            // ro   (info.battstatus) Battery control status
        BatteryMode = 1106,             // rw   (cam.battmode) Used for disabling charging or discharging of the battery.
        BatteryArmDelay = 1107,         // rw   (cam.armdelay) Delay, in seconds, from the moment the camera is placed into WTR and the time the battery is armed.
        BatteryPrevRuntime = 1108,      // rw   (cam.prvruntime) Time in seconds the camera will run on battery in preview if a cine is not triggered.
        BatteryPwrOffDelay = 1109,      // rw   (cam.poffdelay) Time in seconds the battery still supplies power to the camera after it has been disarmed.
        BatteryReadyGate = 1110,        // rw   (cam.readygate) Set/Get Battery readygate control

        KernelType = 3000,
        GainUnit = 3001,
        AutoSaveNVM = 3003,

        Aux1Signal = 3008,
        Aux2Signal = 3009,
        Aux3Signal = 3010,

        MagRecordFormat = 3011,

        KernelTypeCAMVER = 4000,

        IsMiro = 8002,
        IsMidi = 8003,
        
        //
        // capabilities All Read Only
        //
        SupportsMagazine = 8193,        
        SupportsHQMode = 8194,
        SupportsGenlock = 8195,
        SupportsEDR = 8196,
        SupportsAutoExposure = 8197,
        SupportsTurbo = 8198,
        SupportsBurstMode = 8199,
        SupportsShutterOff = 8200,
        SupportsDualSDIOutput = 8201,
        SupportsRecordingCines = 8202,
        SupportsV444 = 8203,
        SupportsInterlacedSensor = 8204,
        SupportsRampFRP = 8205,
        SupportsOffGainCorrections = 8206,
        SupportsFRP = 8207,
        SupportedVideoSystems = 8208,
        SupportsRemovableSSD = 8209,
        SupportedAuxSignalFunctions = 8210,
        SupportsVideoSync = 8212,
        SupportsTimeCodeOutSignal = 8213,
        SupportsQuietMode = 8214,
        SupportsPreTriggerMemGate = 8215,
        SupportsV4K = 8216,
        SupportsAnamorphicDesqRatio = 8217,
        SupportsAudio = 8218,
        SupportsProRes = 8219,					// ro bit 1 = CineMag support , bit 0 = Camera support
        SupportsV3G = 8220,
        SupportsProgIO = 8221,                  // ro  camera has Programmable IO
        SupportsSyncToTrigger = 8222,
        SupportsSensorModes = 8223,     		// ro used for Sensor Mode;  currently used for Flex 4K GS, VEO 4K and Virgo V2040
        SupportsBattery = 8224,
        SupportsExpIndex = 8225,
        SupportsHvTrigger = 8226,
        Supports10G = 8227,

        StartOnAcqReadOnly = 9002,
        SupportsToe = 9004,
        SupportsLogMode = 9005,
        SupportsVFMode = 9006,

        SupportedAux1SignalFunctions = 9020,
        SupportedAux2SignalFunctions = 9021,
        SupportedAux3SignalFunctions = 9022,
        SupportedGenlockFunctions = 9023,

        SigCount = 10001,                       // ro  signal count available at the port
        SigSelect = 10002,                      // rw  select the signal to connect to a certain port
        PulseProc = 10003,                      // rw  parameters for pulse processor (in a structure)
        HasPulseProc = 10004,                   // ro  this port has pulse processor

        //
        // Get name from Firmware No Translation
        //
        SigNameFmw = 20001,                     // ro  signal name, given the port number and signal number

        //
        // Get Translated names
        //
        SigName = 20002                         // ro  signal name, given the port number and signal number 
    };

    //
    // selection codes for Nucleus Firmware Upgrade
    //
    public enum FWType : uint
    {
        FW_PHFW = 1,                // PH16 Camera Phfw
        FW_FIRMWARE = 2,
        FW_FPGA = 3,
        FW_FLASH_FPGA = 4,
        FW_MAGAZINE = 5,
        FW_10G_FPGA = 6,
        FW_KERNEL_FLA = 7,
        FW_KERNEL_NFS = 8
    }


    #endregion

    ///////////////////////////////////////////////////////////
    ///////////////////////////////////////////////////////////
    ///////////////////////////////////////////////////////////

    public static class PhCon
    {
        public const UInt32 PHCONHEADERVERSION  = 787;
        public const uint MAXCAMERACNT          = 63;

        public const Int32 MAX_RESOLUTIONS      = 100;
        public const Int32 MAXIPSTRSZ           = 16;
        public const Int32 MAXSTDSTRSZ          = 256;      // standard maximum size of strings
        public const Int32 MAX_DESCRIPTION      = 4096;
        public const Int32 MAX_EXP_INDEX        = 10;       // Normally 8 setting, but leave room for a table end, 0 = last

        #region Management
        [DllImport("Phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhRegisterClientEx(
            IntPtr hWnd,
            [param: MarshalAs(UnmanagedType.LPStr)] [In] StringBuilder szPath,
            PROGRESSCALLBACK pfnCallback,
            UInt32 PhConHeaderVer);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhEnableMessages([param: MarshalAs(UnmanagedType.Bool)]bool Enable);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetErrorMessage(Int32 ErrNo,
            [param: MarshalAs(UnmanagedType.LPStr, SizeConst = MAXSTDSTRSZ)] [Out] StringBuilder pErrText);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhUnregisterClient(IntPtr hWnd);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCameraCount(out UInt32 pCnt);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhAddSimulatedCamera(UInt32 CamVer, UInt32 Serial);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetDllsOption(DllOptions optionSelector, IntPtr pValue);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetDllsOption([MarshalAs(UnmanagedType.U4)]DllOptions optionSelector, ref bool value);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetDllsOption([MarshalAs(UnmanagedType.U4)]DllOptions optionSelector, ref UInt32 value);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetDllsOption([MarshalAs(UnmanagedType.U4)] DllOptions optionSelector, IntPtr pValue);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetDllsOption(
            [MarshalAs(UnmanagedType.U4)] DllOptions optionSelector,
            [MarshalAs(UnmanagedType.Bool)] ref bool Value);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetDllsOption(
            [MarshalAs(UnmanagedType.U4)] DllOptions optionSelector,
            [MarshalAs(UnmanagedType.U4)] ref UInt32 Value);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetDllsLogOption([MarshalAs(UnmanagedType.U4)]LogSetCode SelectCode, UInt32 Value);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetDllsLogOption([MarshalAs(UnmanagedType.U4)]LogGetCode SelectCode, out UInt32 Value);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetAllIpCameras(out UInt32 CamCnt, IntPtr camIds);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetVisibleIp(out UInt32 CamCnt, IntPtr Ips);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhAddVisibleIp(UInt32 IpAddress);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhRemoveVisibleIp(UInt32 IpAddress);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhMakeAllIpVisible();

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetIgnoredIp(out UInt32 CamCnt, IntPtr IPs);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhDisableVisible(bool value);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern bool PhIsVisibleDisabled();

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhFillIDInfo(IntPtr camIds);

        //new enumeration interface
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhConfigPoolUpdate(uint Period);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern bool PhOffline(uint CN);

        #endregion

        #region Camera Params
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCameraID(
            UInt32 CN,
            out UInt32 pSerial,
            [param: MarshalAs(UnmanagedType.LPStr, SizeConst = MAXSTDSTRSZ)] [Out] StringBuilder cameraName);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhFindCameraNumber(UInt32 Serial, out UInt32 CN);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetVersion(UInt32 CN, [MarshalAs(UnmanagedType.U4)]Versions verType, out UInt32 ver);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhGetCameraModel(uint CamVer, StringBuilder verName);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCameraOptions(UInt32 CN, [MarshalAs(UnmanagedType.Struct)] ref CameraOptions cOptions);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetCameraOptions(UInt32 CN, [In] ref CameraOptions cOptions);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetPartitions(UInt32 CN, [In, Out] ref UInt32 pCount, IntPtr pPartitionSize);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetPartitions(UInt32 CN, [In, Out] ref UInt32 pCount, UInt32[] pPartitionSize);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetPartitions(
            UInt32 CN,
            UInt32 Count,
            [param: In, MarshalAs(UnmanagedType.LPArray)]  UInt32[] pPartitionSize);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetBitDepths(
            UInt32 CN,
            out UInt32 Cnt,
            [param: Out, MarshalAs(UnmanagedType.LPArray)] UInt32[] BitDepths);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetDescription(
            UInt32 CN,
            [param: Out, MarshalAs(UnmanagedType.LPStr, SizeConst = MAX_DESCRIPTION)] StringBuilder description);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetDescription(
            UInt32 CN,
            [param: In, MarshalAs(UnmanagedType.LPStr)] StringBuilder description);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetFrameRateRange(UInt32 CN, Point Res, out UInt32 MinFrameRate, out UInt32 MaxFrameRate);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetExposureRange(UInt32 CN, UInt32 FrameRate, out UInt32 MinExposure, out UInt32 MaxExposure);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetCameraName(
            UInt32 CN,
            [param: In, MarshalAs(UnmanagedType.LPStr)] StringBuilder cameraName);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhParamsChanged(UInt32 CN, [param: MarshalAs(UnmanagedType.Bool)]out bool changed);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetResolutions(
            UInt32 CN,
            [param: In, Out, MarshalAs(UnmanagedType.LPArray, SizeConst = MAX_RESOLUTIONS)] Point[] Res,
            ref UInt32 Cnt,
            IntPtr nullCAR,
            IntPtr nullADCBits);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetExactFrameRate(
            UInt32 CamVer,
            [MarshalAs(UnmanagedType.U4)] SyncMode SyncMode,
            UInt32 RequestedFrameRate,
            out double ExactFrameRate);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetExactFrameRateDouble(
            UInt32 CamVer,
            [MarshalAs(UnmanagedType.U4)] SyncMode SyncMode,
            double RequestedFrameRate,
            out double ExactFrameRate);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCameraTime(UInt32 CN, ref Time64 t64);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetCameraTime(UInt32 CN, UInt32 timeSec1970);
        #endregion

        #region Get/Set
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGet(UInt32 CN, [MarshalAs(UnmanagedType.U4)]GS Sel, IntPtr data);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGet(UInt32 CN, [MarshalAs(UnmanagedType.U4)]GS Sel, out Int32 dataInt);  // overload

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGet(UInt32 CN, GS Sel, out uint dataInt);                                // overload

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGet(UInt32 CN, GS Sel, out bool dataInt);                                // overload


        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSet(UInt32 CN, [MarshalAs(UnmanagedType.U4)]GS Sel, IntPtr data);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSet(UInt32 CN, [MarshalAs(UnmanagedType.U4)]GS Sel, ref Int32 dataInt);  // overload

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhSet(UInt32 CN, GS Sel, [MarshalAs(UnmanagedType.Bool)] ref bool dataInt);    // overload

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGet1(UInt32 CN, GS Sel, uint Sel1, IntPtr data);
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGet1(UInt32 CN, GS Sel, uint Sel1, out int dataInt);     // overload
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGet1(UInt32 CN, GS Sel, uint Sel1, out uint dataInt);    // overload
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGet1(UInt32 CN, GS Sel, uint Sel1, out bool dataInt);    // overload

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSet1(UInt32 CN, GS Sel, uint Sel1, IntPtr data);
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhSet1(UInt32 CN, GS Sel, uint Sel1, ref int dataInt);         // overload
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhSet1(UInt32 CN, GS Sel, uint Sel1, ref uint dataInt);        // overload

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGet2(UInt32 CN, GS Sel, uint Sel1, uint Sel2, IntPtr data);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhiGet(UInt32 CN, GS Sel);
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern double PhdGet(UInt32 CN, GS Sel);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhiGet1(UInt32 CN, GS Sel, GS Sel1);
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern double PhdGet1(UInt32 CN, GS Sel, GS Sel1);

        #endregion

        #region Cine partition

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhFirstFlashCine(UInt32 CN);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhMaxCineCnt(UInt32 CN);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineCount(UInt32 CN, out UInt32 RAMCount, out UInt32 NVMCount);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineStatus(
            UInt32 CN,
            [param: In, Out, MarshalAs(UnmanagedType.LPArray, SizeConst = 512)]Cinestatus[] status);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineParams(UInt32 CN, Int32 Cine, ref AcquiParams pParams, IntPtr pBmi);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetSingleCineParams(UInt32 CN, ref AcquiParams Params);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetCineParams(UInt32 CN, Int32 Cine, ref AcquiParams pParams);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhCineGet(UInt32 CN, Int32 cineIndex, [MarshalAs(UnmanagedType.U4)]CGS Sel, IntPtr data);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhCineGet(UInt32 CN, Int32 cineIndex, [MarshalAs(UnmanagedType.U4)]CGS Sel, out Int32 dataInt);    // overload

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhCineSet(UInt32 CN, Int32 cineIndex, [MarshalAs(UnmanagedType.U4)]CGS Sel, IntPtr data);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhCineSet(UInt32 CN, Int32 cineIndex, [MarshalAs(UnmanagedType.U4)]CGS Sel, ref Int32 dataInt);    // overload
        #endregion

        #region Camera Actions
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhRecordCineNoDel(UInt32 CN);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhRecordCine(UInt32 CN);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhRecordSpecificCine(UInt32 CN, Int32 Cine);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSendSoftwareTrigger(UInt32 CN);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhDeleteCine(UInt32 CN, Int32 Cine);
        #endregion

        #region Video
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhVideoPlay(UInt32 CN, Int32 cine, ref ImRange rng, Int32 playSpeed);

        //overload of the same Ph function for null argument
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhVideoPlay(UInt32 CN, Int32 cine, IntPtr nullPtr, Int32 playSpeed);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetVideoFrNr(UInt32 CN, out Int32 CrtIm);
        #endregion

        #region BlackReference & White Balance
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhBlackReference(UInt32 CN, PROGRESSCALLBACK pfnCallback);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhBlackReferenceCI(UInt32 CN, PROGRESSCALLBACK pfnCallback);   // used for CSR

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhComputeWB(ref Bmih bmih, IntPtr pPixel, ref Point p, int SquareSide,
            CFA CFA, ref WBGain WB, out uint SatCnt);
        //null arg overload
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhComputeWB(ref Bmih bmih, IntPtr pPixel, ref Point p, int SquareSide,
            CFA CFA, IntPtr WB, out uint SatCnt);
        //null arg overload 2
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhComputeWB(ref Bmih bmih, IntPtr pPixel, ref Point p, int SquareSide,
            CFA CFA, ref WBGain WB, IntPtr nullSatCnt);
            
        #endregion

        #region Flash
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhNVMGetStatus(UInt32 CN, ref UInt32 CineCnt,
                                                    IntPtr pTime, out UInt32 FreeSp);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhNVMSaveClip(UInt32 CN, Int32 cineIndex, ref ImRange rng, UInt32 Options, PROGRESSCALLBACK pfnCallback);
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhNVMSaveClip(UInt32 CN, Int32 cineIndex, IntPtr rngNull, UInt32 Options, PROGRESSCALLBACK pfnCallback);   //send null for full rng

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhNVMContRec(UInt32 CN, IntPtr pSave, IntPtr pOldValue, ref UInt32 pEnable);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhNVMErase(UInt32 CN, PROGRESSCALLBACK cb);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhMemorySize(UInt32 CN, out UInt32 pDRAMSize, out UInt32 pNVMSize);
 
        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi)]
        public static extern HRESULT PhRemoveCameraFile(UInt32 CN, [MarshalAs(UnmanagedType.LPStr, SizeConst = PhFile.MAX_PATH)] string szCamFN);

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhfReadCFFileList(
            uint CN,
            ref IntPtr pCnt,    // input -- count of files for allocation, output -- count of files available
            ref IntPtr pTime,   // output, optional -- array of file time
            int FileNr,         // input -- file number to provide size and time
            ref IntPtr pSize,   // output, optional -- file size of selected file number
            ref IntPtr pName);  // output, optional -- file name of selected file number

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhfReadCFFileList(uint CN, out uint pCnt, IntPtr pTime, int FileNr, IntPtr pSize, IntPtr pName);
       
        
        #endregion

        #region Nucleus Functions

        [DllImport("phcon.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhUpgradeFirmware(uint IpAddress, uint camVer, FWType selectCode, String fileName);

        #endregion

    }
}
