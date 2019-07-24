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
//              June 13, 2018   Added "SensorMode" to Setup structure           //
//                                                                              //
//////////////////////////////////////////////////////////////////////////////////

using System;
using System.Collections.Generic;
using System.Text;
using System.Runtime.InteropServices;


namespace PhSharp
{
 
    ///////////////////////////////////////////////////////////
    ////////////////////// Structures /////////////////////////
    ///////////////////////////////////////////////////////////

    #region Structures

    [StructLayout(LayoutKind.Sequential)]
    public struct BITMAPINFOHEADER
    {
        public uint biSize;
        public int biWidth;
        public int biHeight;
        public ushort biPlanes;
        public ushort biBitCount;
        public uint biCompression;
        public uint biSizeImage;
        public int biXPelsPerMeter;
        public int biYPelsPerMeter;
        public uint biClrUsed;
        public uint biClrImportant;
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential)]
    public struct CINEFILEHEADER
    {
        public ushort Type;             // must be "CI"
        public ushort HeaderSize;
        public ushort Compression;      // CC_RGB    = 0 - uncompressed BMP
                                        // CC_JPEG   = 1 - JPEG Compressed
                                        // CC_UNINT  = 2 - uncompressed color not 
                                        // interpolated CFA = GBRG/RGGB

        public ushort Version;          // upgrades, now 0
        public int FirstMovieImage;     // First image number, relative to trigger
        public uint TotalImageCount;    // Total count of cine images
        public int FirstImageNo;        // First image number from the range selected
                                        // (relative to trigger)

        public uint ImageCount;         // count of images from this file
        public uint OffImageHeader;     // offset in file of a BITMAPINFO
                                        // stucture for all images

        public uint OffSetup;           // offset in file of a SETUP structure
        public uint OffImageOffsets;    // offset in file of an array with position
        public Time64 TriggerTime;      // 32.32 time in seconds from Jan 1 1970
    }

    //
    // Our image header = Windows BITMAPINFOHEADER + extensions 
    //
    [StructLayout(LayoutKind.Sequential)]
    public struct IH
    {
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 biSize;
        [MarshalAs(UnmanagedType.I4)]
        public Int32 biWidth;
        [MarshalAs(UnmanagedType.I4)]
        public Int32 biHeight;
        [MarshalAs(UnmanagedType.U2)]
        public UInt16 biPlanes;
        [MarshalAs(UnmanagedType.U2)]
        public UInt16 biBitCount;
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 biCompression;
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 biSizeImage;
        [MarshalAs(UnmanagedType.I4)]
        public Int32 biXPelsPerMeter;
        [MarshalAs(UnmanagedType.I4)]
        public Int32 biYPelsPerMeter;
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 biClrUsed;
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 biClrImportant;

        // End of BITMAPINFOHEADER 

        [MarshalAs(UnmanagedType.I4)]
        public Int32 BlackLevel;               // Black level   (now: 0 or 4 on 8 bits, proportional on > 8bits)
        [MarshalAs(UnmanagedType.I4)]
        public Int32 WhiteLevel;               // White level   (now: MaxPix or MaxPix-1, proportional on > 8bits)
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential)]
    public struct ImFilter
    {
        public int dim;         // square kernel dimension 3,5
        public int shifts;      // right shifts of Coef (8 shifts means divide by 256)
        public int bias;        // bias to add at end

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 25)]
        public int[] Coef;      // [5*5];  //maximum alocation for a 5x5 filter
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential)]
    public struct Improcoptions
    {
        public int Bright;          // Brightness        (-100, 100; 0=do nothing)
        public int Contrast;        // Contrast          (-100, 100; 0=do nothing)
        public float Gamma;         // Gamma             (1.0=do nothing)

        public int Saturation;      // Color saturation  (-100, 100; 0 = do nothing)
        public int FlipH;           // flip horizontal (0 = false)
        public int FlipV;           // flip vertical   (0 = false)
        public int Rotate;          // 0   = do nothing 
                                    // +90 = counterclockwise 
                                    // -90 = clockwise, 
                                    // for +-180 use both flips

        public WBGain WBView;       // White balance adjustment for view cine from file
                                    // 1.0 = do nothing

        public int FilterCode;      // predefined filter or user filter: 0 = none
        public int FilterParam;     // filter parameter
        public ImFilter UF;         // user filter, used if FilterCode == -1
        public int Hue;             // hue corection (degrees: -180 ...180)

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
        public int[] Reserved;      // reserved for future expansion (please set them to 0)

        public void reset()
        {
            Bright = 0;
            Contrast = 0;
            Gamma = 2.2f;
            Saturation = 0;
            FlipH = 0;
            FlipV = 0;
            Rotate = 0;
            //WBView.R = 1;
            //WBView.B = 1;
            FilterCode = 0;
            //fake fields completed for C# struct
            FilterParam = 0;
            UF = new ImFilter();
            Hue = 0;
            Reserved = new int[4];
        }
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential)]
    public struct REDUCE16TO8PARAMS
    {
        [MarshalAs(UnmanagedType.R4)]
        public float fGain16_8;
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential)]
    public struct WBGain
    {
        [MarshalAs(UnmanagedType.R4)]
        public float R;    // White balance, gain correction for red
        [MarshalAs(UnmanagedType.R4)]
        public float B;    // White balance, gain correction for blue
    }

    [StructLayout(LayoutKind.Sequential, Pack = 1)]
    public struct TC
    {
        /***** This is a bitfield used in C *************
            byte framesU:4;        // Units of frames
            byte framesT:2;        // Tens of frames
            byte dropFrameFlag:1;  // Dropframe flag
            byte colorFrameFlag:1; // Colorframe flag
            byte secondsU:4;       // Units of seconds
            byte secondsT:3;       // Tens of seconds
            byte flag1:1;          // Flag 1
            byte minutesU:4;       // Units of minutes
            byte minutesT:3;       // Tens of minutes
            byte flag2:1;          // Flag 2
            byte hoursU:4;         // Units of hours
            byte hoursT:2;         // Tens of hours
            byte flag3:1;          // Flag 3
            byte flag4:1;          // Flag 4
            uint userBitData;      // 32 user bits
        ************************************************/

        //
        // Don't Care about the values in CSharp 
        // because the data is not used,
        // But need to define the Structure
        //
        public byte frames;
        public byte seconds;
        public byte minutes;
        public byte hours;
        public uint userBitData;
    };

   
    //////////////////////////////////////////////////////////////////////////////////////
    // SETUP structure - camera setup parameters                                        //
    //                                                                                  //
    // It was started in 1992 during the 16 bit compilers era;                          //
    // the fields are arranged compact with alignment at 1 byte - this was              //
    // the compiler default at that time. New fields were added, some of them           //
    // replace old fields but a compatibility is maintained with the old versions.      //
    //                                                                                  //
    // --UPDF = Updated Field. This field is maintained for compatibility with old      //
    //          versions but a new field was added for that information. The new        //
    //          field can be larger or may have a different measurement unit.           //
    //          For example FrameRate16 was a 16 bit field to specify frame             //
    //          rate up to 65535 fps (frames per second). When this was not enough      //
    //          anymore, a new field was added: FrameRate (32 bit integer, able to      //
    //          store values up to 4 billion fps). Another example: Shutter field       //
    //          (exposure duration) was specified initially in microseconds, later the  //
    //          field ShutterNs was added to store the value in nanoseconds. The UF can //
    //          be considered outdated and deprecated; they are updated in the Phantom  //
    //          libraries but the users of the SDK can ignore them.                     //
    //                                                                                  //
    // --TBI = to be ignored, not used anymore                                          //
    //                                                                                  //
    // Use the definition from stdint.h with known size for the integer types           //
    //////////////////////////////////////////////////////////////////////////////////////

    [StructLayout(LayoutKind.Sequential,Pack=1)]
    public struct Setup                 // camera setup information from dialog box
    {
        public ushort FrameRate16;      // ---UPDF replaced by FrameRate
        public ushort Shutter16;        // ---UPDF replaced by ShutterNs
        public ushort PostTrigger16;    // ---UPDF replaced by PostTrigger
        public ushort FrameDelay16;     // ---UPDF replaced by FrameDelayNs
        public ushort AspectRatio;      // ---UPDF replaced by ImWidth, ImHeight
        public ushort Res7;             // ---TBI Contrast16
        
        //
        // (analog controls, not available after Phantom v3)
        //
        public ushort Res8;             // ---TBI Bright16
        public byte Res9;               // ---TBI Rotate16
        public byte Res10;              // ---TBI TimeAnnotation                               
        public byte Res11;              // ---TBI TrigCine (all cines are triggered)      

        public byte TrigFrame;          // Sync imaging mode:
                                        //  0 = internal 
                                        //  1 = external
                                        //  2 = Lock to IRIG Timecode
                                        //  3 = Lock to Video
                                        //  5 = Lock to Trigger
                                        
        public byte Res12;              // ---TBI ShutterOn (the shutter is always on)

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = PhInt.MAXLENDESCRIPTION_OLD)]
        public byte[] DescriptionOld;   // ---UPDF replaced by larger Description able to
                                        // store 4k of user comments

        public ushort Mark;             // "ST"  -  marker for setup file
        public ushort Length;           // Length of the current version of setup
        public ushort Res13;            // ---TBI Binning (binning factor)

        public ushort SigOption;        // Global signals options:
                                        // MAXSAMPLES = records the max possible samples
                                        
        public short BinChannels;       // Number of binary channels read from the
                                        // SAM (Signal Acquisition Module)
                                        
        public byte SamplesPerImage;    // Number of samples acquired per image, both
                                        // binary and analog;
                                
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 8 * 11)]
        public byte[] BinName;          // [8][11] Names for the first 8 binary signals having
                                        // maximum 10 chars + null
 
        public ushort AnaOption;        // Global analog options single ended,  bipolar
        public short AnaChannels;       // Number of analog channels used (16 bit 2's
                                        // complement per channel)
                                        
        public byte Res6;               // ---TBI (reserved)
        public byte AnaBoard;           // Board type:
                                        //   0 = none
                                        //   1 = dsk (DSP system kit)
                                        //   2 = dsk+SAM
                                        //   3 = Data Translation DT9802
                                        //   4 = Data Translation DT3010

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 8)]
        public short[] ChOption;        // Per channel analog options;
                                        // now:bit 0...10 analog gain (1,2,4,8 ... 1000)
                                
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 8)]
        public float[] AnaGain;         // User gain correction for conversion from voltage
                                        // to real units , per channel
                                
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 8 * 6)]
        public byte[] AnaUnit;          // [8][6] Measurement unit for analog channels:
                                        // maximum 5 chars + null
                                
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 8 * 11)]
        public byte[] AnaName;          // [8][11] Channel name for the first 8 analog channels:
                                        // maximum 10 chars + null

        //
        // Range of images for continuous recording
        //
        public int lFirstImage;         // first image
        public uint dwImageCount;       // Image count for continuous recording;
                                        // used also for signal recording
                                        
        public short nQFactor;          // Quality - for saving to compressed file at
                                        // continuous recording; range 2...255
                                        
        public ushort wCineFileType;    // Cine file type - for continuous recording

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4 * PhInt.OLDMAXFILENAME)]
        public byte[] szCinePath;       // [4][OLDMAXFILENAME]; 
                                        // 4 paths to save cine files - for
                                        // continuous recording. After upgrading to Win32
                                        // this still remained 65 bytes long each
                                        // GetShortPathName is used for the filenames
                                        // saved here
        public ushort Res14;            // ---TBI bMainsFreq (Mains frequency:

        //
        // Time board - settings for PC104 irig board
        // used in Phantom v3 not used after v3
        //
        public byte Res15;              // ---TBI bTimeCode;
        public byte Res16;              // ---TBI bPriority
        public ushort Res17;            // ---TBI wLeapSecDY
        public double Res18;            // ---TBI dDelayTC Propagation delay for time code
        public double Res19;            // ---TBI dDelayPPS Propagation delay for PPS
        public ushort Res20;            // ---TBI GenBits      
        public int Res1;                // ---TBI
        public int Res2;                // ---TBI
        public int Res3;                // ---TBI

        //
        // Image dimensions in v4 and newer cameras:
        //
        public ushort ImWidth;          // Image Width
        public ushort ImHeight;         // Image height

        public ushort EDRShutter16;     // ---UPDF replaced by EDRShutterNs
        public uint Serial;             // Camera serial number. 
                                        // For firewire cameras you
                                        // have a translated value here:
                                        // factory serial + 0x58000
                                        
        public int Saturation;          // ---UPDF replaced by float fSaturation
        public byte Res5;               // ---TBI        
        public uint AutoExposure;       // Autoexposure control
                                        //   bit0       
                                        //     0 - disable AUTOEXP
                                        //     1 - enable AUTOEXP
                                        //
                                        //   bit 1      
                                        //     0 - lock at trigger
                                        //     1 - active after trigger
                                        //         Always 0 for cameras using V2 autoexp
                                        //         Read only for cameras using V2 autoexp
                                        //
                                        //   bit 3, 2            
                                        //     00 - for all cameras using V1 autoexp
                                        //
                                        //          Cameras using V2 autoexp
                                        //     01 - average
                                        //     10 - spot
                                        //     11 - center weighted
                                        
        public bool bFlipH;             // Flips image horizontally
        public bool bFlipV;             // Flips image vertically;
        public uint Grid;               // Displays a crosshair or a grid in setup, 
                                        //   0 = no grid
                                        //   2 = cross hair 
                                        //   8 = grid with 8 intervals

        public uint FrameRate;          // ---UPDF replaced by dFrameRate (double)
        public uint Shutter;            // ---UPDF replaced by ShutterNs
        public uint EDRShutter;         // ---UPDF replaced by EDRShutterNs
        public uint PostTrigger;        // Post trigger frames, measured in frames
        public uint FrameDelay;         // ---UPDF replaced by FrameDelayNs
        public bool bEnableColor;       // User option: when 0 forces gray images from
                                        // color cameras

        public uint CameraVersion;      // The version of camera hardware 
                                        // (without decimal point). 
                                        // Examples of cameras produced after the year 2000
                                        // 
                                        //   Firewire: 4, 5, 6
                                        //   Ethernet: 42 43 51 7 72 73 9 91 10
                                        //   650 (p65) 660 (hd)  ....
                                        //   4001   = Flex4K, 2001 = MIRO C210,
                                        //   160001 = V1610,  7001 = VEO 710S ....

        public uint FirmwareVersion;    // Firmware version
        public uint SoftwareVersion;    // Phantom software version
        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 551 (May 2001) ----------- //
        /////////////////////////////////////////////////////////////////////////////

        public int RecordingTimeZone;   // The time zone active during the recording
                                        // of the cine
                                        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 552 (May 2001) ----------- //
        /////////////////////////////////////////////////////////////////////////////
 
        public uint CFA;                // Code for the Color Filter Array of the sensor
                                        //   CFA_NONE      = 0 (gray) 
                                        //   CFA_VRI       = 1 (GBRG/RGGB)
                                        //   CFA_VRIV6     = 2 (BGGR/GRBG) 
                                        //   CFA_BAYER     = 3 (GB/RG)
                                        //   CFA_BAYERFLIP = 4 (RG/GB)
                                        //
                                        // high byte carries info about color/gray heads at
                                        // v6 and v6.2
                                        // Masks: 0x80000000: TLgray 
                                        //        0x40000000: TRgray
                                        //        0x20000000: BLgray 
                                        //        0x10000000: BRgray

        //
        // Final adjustments after image processing:
        //
        public int Bright;              // ---UPDF replaced by fOffset
        public int Contrast;            // ---UPDF replaced by fGain
        public int Gamma;               // ---UPDF replaced by fGamma
        public uint Res21;              // ---TBI
        public uint AutoExpLevel;       // Level for autoexposure control
        public uint AutoExpSpeed;       // Speed for autoexposure control
        public RECT AutoExpRect;        // Rectangle for autoexposure control

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
        public WBGain[] WBGain;         // Gain adjust on R,B components, for white balance,
                                        // at Recording
                                        // 1.0 = do nothing,
                                        // index 0: all image for v4,5,7...
                                        // and TL head for v6, v6.2 (multihead)
                                        // index 1, 2, 3 :   TR, BL, BR for multihead
                                        
        public int Rotate;              // Rotate the image 
                                        //   0   = do nothing
                                        //   +90 = counterclockwise 
                                        //   -90 = clockwise
                                        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 578 (Nov 2002) ----------- //
        /////////////////////////////////////////////////////////////////////////////

        public WBGain WBView;           // White balance to apply on color interpolated Cines
        public uint RealBPP;            // Current number of bits per pixel
                                        // used to store images of this cine

        //
        // First degree function to convert the 16 bits pixels to 8 bit
        // (for display or file convert)
        //
        public uint Conv8Min;           // ---TBI
        public uint Conv8Max;           // ---UPDF replaced by fGain16_8

        public int FilterCode;          // ImageProcessing: area processing code
        public int FilterParam;         // ImageProcessing: optional parameter
        public ImFilter UF;             // User filter: a 3x3 or 5x5 user convolution filter

        public uint BlackCalSVer;       // Software Version used for Black Reference
        public uint WhiteCalSVer;       // Software Version used for White Calibration
        public uint GrayCalSVer;        // Software Version used for Gray Calibration
        public bool bStampTime;         // Stamp time (in continuous recording)
                                        //   1 = absolute time, 
                                        //   3 = from trigger
                                
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 605 (Nov 2003) ----------- //
        /////////////////////////////////////////////////////////////////////////////
 
        public uint SoundDest;          // Sound device 
                                        //   0 = none
                                        //   1 = Speaker
                                        //   2 = sound board
        //
        // Frame rate profile Info
        //
        public uint FRPSteps;           // Suplimentary steps in frame rate profile
                                        // 0 means no frame rate profile
                                        
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public int[] FRPImgNr;          // Image number where to change the rate and/or
                                        // exposure allocated for 16 points 
                                        // (4 available in v7)
                                        
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public uint[] FRPRate;          // New value for frame rate (fps)
        
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public uint[] FRPExp;           // New value for exposure
                                        // (nanoseconds, not implemented in cameras)

        //
        // Multicine partition
        //
        public int MCCnt;               // Partition count (= cine count - 1)
                                        // Preview cine does not need a partition
                                        
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 64)]
        public float[] MCPercent;       // Percent of memory used for partitions
                                        // Allocated for 64 partitions
                                        // Not used on ph16 cameras - 
                                        //    PH16 Cameras have all equal size partitions
                                        //    Ph16 cameras can have more than 64 partitions, 
                                        //    only first 64 percents are stored here.
                                        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 606 (May 2004) ----------- //
        /////////////////////////////////////////////////////////////////////////////
 
        //
        // CALIBration on Current Image (CSR, current session reference)
        //
        public uint CICalib;            // This cine or this stg is the result of
                                        // a current image calibration
                                        // masks: 
                                        //   1 = BlackRef, 
                                        //   2 = WhiteCalib, 
                                        //   4 = GrayCheck
                                        //   Last cicalib done at the acqui params:
                                        
        public uint CalibWidth;         // Image dimensions
        public uint CalibHeight;
        public uint CalibRate;          // Frame rate (frames per second)
        public uint CalibExp;           // Exposure duration (nanoseconds)
        public uint CalibEDR;           // EDR (nanoseconds)
        public uint CalibTemp;          // Sensor Temperature

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
        public uint[] HeadSerial;       // Head serials for ethernet multihead cameras
                                        // (v6.2) When multiple heads are saved in a file,
                                        // the serials for existing heads are not zero
                                        // When one head is saved in a file its serial is
                                        // in HeadSerial[0] and the other head serials
                                        // are 0xFFffFFff
                                        // HeadSerial[0] is also used for nano Head 
                                        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 607 (Oct 2004) ----------- //
        /////////////////////////////////////////////////////////////////////////////

        public uint RangeCode;          // Range data code: describes the range data format
        public uint RangeSize;          // Range data,  per image size
        public uint Decimation;         // Factor to reduce the frame rate when sending
                                        // the images to i3 external memory by fiber
                                        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 614 (Feb 2005) ----------- //
        /////////////////////////////////////////////////////////////////////////////

        public uint MasterSerial;       // Master camera Serial for external sync. 
                                        // 0 means none (this camera is not a slave 
                                        // of another camera)
                                        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 624 (Jun 2005) ----------- //
        /////////////////////////////////////////////////////////////////////////////

        public uint Sensor;             // Camera sensor code
        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 625 (Jul 2005) ----------- //
        /////////////////////////////////////////////////////////////////////////////

        public uint ShutterNs;          // Exposure in nanoseconds
        public uint EDRShutterNs;       // EDRExp in nanoseconds
        public uint FrameDelayNs;       // FrameDelay in nanoseconds
        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 631 (Oct 2005) ----------- //
        /////////////////////////////////////////////////////////////////////////////
 
        //
        // Stamp outside the acquired image
        // (this increases the image size by adding a border with text information)
        // 
        public uint ImPosXAcq;          // Acquired image horizontal offset in
                                        // sideStamped image
                                        
        public uint ImPosYAcq;          // Acquired image vertical offset in 
                                        // sideStampedimage
                                        
        public uint ImWidthAcq;         // Acquired image width  
                                        // (different value from ImWidth 
                                        // if sideStamped file)
                                        
        public uint ImHeightAcq;        // Acquired image height 
                                        // (different value from ImHeight
                                        // if sideStamped file)

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = PhInt.MAXLENDESCRIPTION)]
        public byte[] Description;      // User description or comments
                                        // (enlarged to 4096 characters)
                                            
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 637 (Jul 2006) ----------- //
        /////////////////////////////////////////////////////////////////////////////

        public bool RisingEdge;         // TRUE rising, FALSE falling
        public uint FilterTime;         // time constant
        public bool LongReady;          // If TRUE the Ready is 1 from the start
                                        // to the end of recording (needed for signal
                                        // acquisition)
        public bool ShutterOff;         // Shutter off - to force maximum exposure for PIV
        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 658 (Mar 2008) ----------- //
        /////////////////////////////////////////////////////////////////////////////

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public byte[] Res4;             // ---TBI
        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 663 (May 2008) ----------- //
        /////////////////////////////////////////////////////////////////////////////

        public bool bMetaWB;            // pixels value does not have WB applied
                                        // (or any other processing)
                                        
        public int Hue;                 // ---UPDF replaced by float fHue
        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 671 (May 2009) ----------- //
        /////////////////////////////////////////////////////////////////////////////

        public int BlackLevel;          // Black level in the raw pixels
        public int WhiteLevel;          // White level in the raw pixels

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = PhInt.MAXSTDSTRSZ)]
        public byte[] LensDescription;  // text with the producer, model,                
                                        // focal range etc ...
                                        
        public float LensAperture;      // aperture f number
        public float LensFocusDistance; // distance where the objects are in focus in
                                        // meters, not available from Canon motorized lens
        public float LensFocalLength;   // current focal length; (zoom factor)
        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 691 (Jul 2010) ----------- //
        /////////////////////////////////////////////////////////////////////////////

        //
        // image adjustment
        //
        public float fOffset;           // [-1.0, 1.0], neutral 0.0;
                                        // 1.0 means shift by the maximum pixel value
                                        
        public float fGain;             // [0.0, Max], neutral 1.0;
        public float fSaturation;       // [0.0, Max], neutral 1.0;
        public float fHue;              // [-180.0, 180.0] neutral 0;
                                        // degrees and fractions of degree to rotate the hue

        public float fGamma;            // [0.0, Max], neutral 1.0; global gamma
                                        // (or green gamma)
                                        
        public float fGammaR;           // per component gammma (to be added to the field
                                        // Gamma)
                                        // 0 means neutral
                                        
        public float fGammaB;
        public float fFlare;            // [-1.0, 1.0], neutral 0.0;
                                        // 1.0 means shift by the maximum pixel value
                                        // pre White Balance offset

        public float fPedestalR;        // [-1.0, 1.0], neutral 0.0;
                                        // 1.0 means shift by the maximum pixel value
                                        
        public float fPedestalG;        // after gamma offset
        public float fPedestalB;
        public float fChroma;           // [0.0, Max], neutral 1.0;
                                        // chrominance adjustment (after gamma)

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = PhInt.MAXSTDSTRSZ)]
        public byte[] ToneLabel;
        public int TonePoints;
        
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 32 * 2)]
        public float[] fTone;           // up to 32  points  + 0.0, 0.0  1.0, 1.0
                                        // defining a LUT using spline curves

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = PhInt.MAXSTDSTRSZ)]
        public byte[] UserMatrixLabel;
        public bool EnableMatrices;
        
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 9)]
        public float[] cmUser;          // user color matrix

        public bool EnableCrop;         // The Output image will contains only a rectangle
                                        // portion of the input image
        public RECT CropRect;
        public bool EnableResample;     // Resample image to a desired output Resolution
        public uint ResampleWidth;
        public uint ResampleHeight;
        public float fGain16_8;         // Gain coefficient used when converting to 8bps
                                        // Input pixels (bitdepth>8) are multiplied by
                                        // the factor:  fGain16_8 * (2**8 / 2**bitdepth)
                                
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 693 (Oct 2010) ----------- //
        /////////////////////////////////////////////////////////////////////////////
 
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public uint[] FRPShape;         // 0: flat,  1 ramp
        public TC TrigTC;               // Trigger frame SMPTE time code and user bits
        public float fPbRate;           // Video playback rate (fps) active when the cine
                                        // was captured
                                        
        public float fTcRate;           // Playback rate (fps) used for generating SMPTE
                                        // time code
                                        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 701 (Apr 2011) ----------- //
        /////////////////////////////////////////////////////////////////////////////

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = PhInt.MAXSTDSTRSZ)]
        public byte[]CineName;          // Cine name
        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 705 (June 2011) ---------- //
        /////////////////////////////////////////////////////////////////////////////

        //
        // Per component gain - user adjustment    
        // [0.0, Max], neutral 1.0;
        //
        public float fGainR;
        public float fGainG;
        public float fGainB;

        //
        // RGB color calibration matrix bring camera pixels to rec 709
        // It includes the white balance set into the ph16 cameras using fWBTemp and fWBCc
        // and the original factory calibration
        // The cine player should decompose this matrix in two components: a diagonal 
        // one with the white balance to be applied before interpolation and a 
        // normalized one to be applied after interpolation
        //
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 9)]
        public float[] cmCalib;

        //
        // White balance based on color temperature and color compensation index
        // its effect is included in the cmCalib.
        //
        public float fWBTemp;
        public float fWBCc;

        //
        // original calibration matrices  :  used to calculate cmCalib in the camera
        //
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 1024)]
        public byte[] CalibrationInfo;

        //
        // Optical filter matrix  :  used to calculate cmCalib in the camera
        //
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 1024)]
        public byte[] OpticalFilter;
        
        /////////////////////////////////////////////////////////////////////////////
        // ----------- End of SETUP in software version 709 (Sept 2011) ---------- //
        /////////////////////////////////////////////////////////////////////////////
                                
        //
        // Current position and status info as received from a GPS receiver
        //
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = PhInt.MAXSTDSTRSZ)]
        public byte[] GpsInfo;
        
        //
        // Unique cine identifier
        //
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = PhInt.MAXSTDSTRSZ)]
        public byte[] Uuid;
        
        /////////////////////////////////////////////////////////////////////////////
        // --------- End of SETUP in software version 719  (Mar 9, 2012) --------- //
        /////////////////////////////////////////////////////////////////////////////
 
        //
        // The name of the application which created this cine
        //
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = PhInt.MAXSTDSTRSZ)]
        public byte[] CreatedBy;
        
        /////////////////////////////////////////////////////////////////////////////
        // --------- End of SETUP in software version 720  (Mar 16, 2012) -------- //
        /////////////////////////////////////////////////////////////////////////////
   
        public uint  RecBPP;            // Acquisition bit depth. It can be 8, 10, 12 or 14

        //
        // Description of the minimum format out of all formats the images of this cine
        // have been represented on since the moment of acquisition.
        //
        public ushort LowestFormatBPP;      
        public ushort LowestFormatQ;
        
        /////////////////////////////////////////////////////////////////////////////
        // --------- End of SETUP in software version 731  (Jan 24, 2013) -------- //
        /////////////////////////////////////////////////////////////////////////////
                             

        public float fToe;              // Controls the gamma curve in the blacks.
                                        // Neutral is 1.0f.
                                        // Decreasing fToe lifts the blacks, while
                                        // increasing it compresses them.
                                        
        public uint  LogMode;           // Configures the log mode.
                                        // 0 - log mode disabled.
                                        // 1, 2, etc - log mode enabled.
                                        // If log mode enabled, gain, gamma, the pedestals,
                                        // r/g/b gains, offset and flare are inactive.

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = PhInt.MAXSTDSTRSZ)]
        public byte[] CameraModel;      // Camera model string.
        
        /////////////////////////////////////////////////////////////////////////////
        // --------- End of SETUP in software version 742  (Nov 19, 2013) -------- //
        /////////////////////////////////////////////////////////////////////////////
 
        public uint WBType;             // For raw color cines, it describes how meta WB is stored.
                                        // If bit 0 is set - wb is stored in WBGain field.
                                        // If bit 1 is set - wb is stored in fWBTemp, fWBCc fields.
                                        
        public float fDecimation;       // Decimation coefficient 
                                        // employed when this cine was saved to file.
                                        
        /////////////////////////////////////////////////////////////////////////////
        // --------- End of SETUP in software version 745  (Apr 29, 2014) -------- //
        /////////////////////////////////////////////////////////////////////////////


        public uint MagSerial;          // The serial of the magazine where the cine 
                                        // was recorded or stored (if any, null otherwise)

        public uint CSSerial;           // Cine Save serial: The serial of the device 
                                        // (camera, cine station) used to save the cine to file 
                                        
        public double dFrameRate;       // High precision acquisition frame rate, 
                                        // replace uint32_t FrameRate
                                        
        /////////////////////////////////////////////////////////////////////////////
        // --------- End of SETUP in software version 751  (Jul 5, 2015)  -------- //
        /////////////////////////////////////////////////////////////////////////////
        
        public uint SensorMode;         // Camera sensor Mode used to define what mode the Sensor is in

        
        /////////////////////////////////////////////////////////////////////////////
        // ---------    End of SETUP in software version 771 (Dec 2017)   -------- //
        /////////////////////////////////////////////////////////////////////////////
    }

    #endregion

    ///////////////////////////////////////////////////////////
    ///////////////////////// enums ///////////////////////////
    ///////////////////////////////////////////////////////////

    #region enums

    public enum IMG_PROC : uint
    {
        REDUCE16TO8 = 1
    }

    //
    ////////////////
    //
    public enum InterpAlgorithm
    {
        FAST_ALGORITHM  = 1,
        ALGORITHM_2     = 2,
        ALGORITHM_3     = 3,
        ALGORITHM_4     = 4,
        BEST_ALGORITHM  = 5,
        NO_DEMOSAICING  = 6
    }

    #endregion

    public partial class PhInt
    {
        public const int MAXLENDESCRIPTION_OLD = 121;   // maximum length for setup description
                                                        // (before Phantom 638) 

        public const int OLDMAXFILENAME         = 65;   // maximum file path size for the 
                                                        // continuous recording to keep 
                                                        // compatibility with old setup file

        public const int MAXLENDESCRIPTION      = 4096; // maximum length for new setup description
        public const int MAXSTDSTRSZ            = 256;  // Standard maximum size for a string
       
        [DllImport("phint.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhProcessImage(IntPtr pPixelSrc, IntPtr pPixelDest, ref IH pIH, [MarshalAs(UnmanagedType.U4)] IMG_PROC procID, IntPtr pProcParams);

        [DllImport("phint.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern int PhSetImProcOptions(ref Improcoptions imOpt, ref Setup setup);
    }
}
