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
//              June 13, 2018   Added Selector GCI_SAVEDECIMATION               //
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
    public delegate bool PROGRESSCB(UInt32 percent, IntPtr cineHandle);

    ///////////////////////////////////////////////////////////
    ////////////////////// Structures /////////////////////////
    ///////////////////////////////////////////////////////////

    #region Structures

    [Serializable]
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]
    public struct CMDESC
    {
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = PhFile.ColorMatrixSize, ArraySubType = UnmanagedType.R4)]
        public float[] matrix;				// RGB color matrix	
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = PhCon.MAXSTDSTRSZ)]
        public string label;				// Color matrix label

        public CMDESC Clone()
        {
            CMDESC cm = new CMDESC();
            cm.label = this.label;
            cm.matrix = (float[])this.matrix.Clone();
            return cm;
        }
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential)]
    public struct PixRng
    {
        [MarshalAs(UnmanagedType.I4)]
        public Int32 First;
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 Cnt;
    }

    //
    ////////////////
    //
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]
    public struct SaveFileName
    {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = PhFile.MAX_PATH)]
        public String FileName;         // filename to save (as seen from camera)
    }

    //
    ////////////////
    //
    [Serializable]
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]
    public struct ToneDesc
    {
        public int controlPointsCounter;		// Number of control points (n)

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = PhFile.ToneArraySize, ArraySubType = UnmanagedType.R4)]
        public float[] controlPoints;	        // Control points: x0 y0 x1 y1... x(n-1) y(n-1)
                                                // All values in [0..1] range

        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = PhCon.MAXSTDSTRSZ)]
        public string label;				    // Optional string label describing this tone
    }

    #endregion

    ///////////////////////////////////////////////////////////
    ///////////////////////// enums ///////////////////////////
    ///////////////////////////////////////////////////////////

    #region enums

    public enum CineInfo : uint
    {
        GCI_CFA = 0,
        GCI_FRAMERATE,
        GCI_EXPOSURE,
        GCI_AUTOEXPOSURE,
        GCI_REALBPP,
        GCI_CAMERASERIAL,
        GCI_HEADSERIAL0,
        GCI_HEADSERIAL1,
        GCI_HEADSERIAL2,
        GCI_HEADSERIAL3,
        GCI_TRIGTIMESEC,
        GCI_TRIGTIMEFR,
        GCI_ISFILECINE,
        GCI_IS16BPPCINE,
        GCI_ISCOLORCINE,
        GCI_ISMULTIHEADCINE,
        GCI_EXPOSURENS,
        GCI_EDREXPOSURENS = 17,

        //
        //////////
        //
        GCI_FRAMEDELAYNS = 19,
        GCI_FROMFILETYPE,
        GCI_COMPRESSION,
        GCI_CAMERAVERSION,
        GCI_ROTATE,
        GCI_IMWIDTH,
        GCI_IMHEIGHT,
        GCI_IMWIDTHACQ,
        GCI_IMHEIGHTACQ,
        GCI_POSTTRIGGER,
        GCI_IMAGECOUNT,
        GCI_TOTALIMAGECOUNT,
        GCI_TRIGFRAME,
        GCI_AUTOEXPLEVEL,
        GCI_AUTOEXPTOP,
        GCI_AUTOEXPLEFT,
        GCI_AUTOEXPBOTTOM,
        GCI_AUTOEXPRIGHT,
        GCI_RECORDINGTIMEZONE,
        GCI_FIRSTIMAGENO,
        GCI_FIRSTMOVIEIMAGE,
        GCI_SENSOR = 51,
        GCI_SENSORMODE = 52,

        //
        //////////
        //
        GCI_FRPSTEPS = 100,
        GCI_FRP1X,
        GCI_FRP1Y,
        GCI_FRP2X,
        GCI_FRP2Y,
        GCI_FRP3X,
        GCI_FRP3Y,
        GCI_FRP4X,
        GCI_FRP4Y,
        GCI_WRITEERR,
        GCI_LENSDESCRIPTION,
        GCI_LENSAPERTURE,
        GCI_LENSFOCALLENGTH,

        //
        //////////
        //
        GCI_WB = 200,
        GCI_WBVIEW = 201,
        GCI_WBISMETA = 230,
        GCI_BRIGHT = 202,
        GCI_CONTRAST = 203,
        GCI_GAMMA = 204,
        GCI_GAMMAR = 223,
        GCI_GAMMAB = 224,
        GCI_SATURATION = 205,
        GCI_HUE = 206,
        GCI_FLIPH = 207,
        GCI_FLIPV = 208,
        GCI_FILTERCODE = 209,
        GCI_IMFILTER = 210,
        GCI_INTALGO = 211,
        GCI_PEDESTALR = 212,
        GCI_PEDESTALG = 213,
        GCI_PEDESTALB = 214,
        GCI_FLARE = 225,
        GCI_CHROMA = 226,
        GCI_TONE = 227,
        GCI_ENABLEMATRICES = 228,
        GCI_USERMATRIX = 229,
        GCI_RESAMPLEACTIVE = 215,
        GCI_RESAMPLEWIDTH = 216,
        GCI_RESAMPLEHEIGHT = 217,
        GCI_CROPACTIVE = 218,
        GCI_CROPRECTANGLE = 219,
        GCI_OFFSET16_8 = 220,
        GCI_GAIN16_8 = 221,
        GCI_DEMOSAICINGFUNCPTR = 222,

        GCI_VFLIPVIEWACTIVE = 300,

        GCI_MAXIMGSIZE = 400,

        GCI_FRPIMGNOARRAY = 450,
        GCI_FRPRATEARRAY = 451,
        GCI_FRPSHAPEARRAY = 452,

        GCI_TRIGTC = 470,
        GCI_TRIGTCU = 471,
        GCI_PBRATE = 472,
        GCI_TCRATE = 473,

        GCI_SAVERANGE = 500,
        GCI_SAVEFILENAME = 501,
        GCI_SAVEFILETYPE = 502,
        GCI_SAVE16BIT = 503,
        GCI_SAVEPACKED = 504,
        GCI_SAVEXML = 505,
        GCI_SAVESTAMPTIME = 506,
		GCI_SAVEDECIMATION = 1035,

        GCI_SAVEAVIFRAMERATE = 520,
        GCI_SAVEAVICOMPRESSORLIST = 521,
        GCI_SAVEAVICOMPRESSORINDEX = 522,

        GCI_SAVEDPXLSB = 530,
        GCI_SAVEDPXTO10BPS = 531,
        GCI_SAVEDPXDATAPACKING = 532,
        GCI_SAVEDPX10BITLOG = 533,
        GCI_SAVEDPXEXPORTLOGLUT = 534,
        GCI_SAVEDPX10BITLOGREFWHITE = 535,
        GCI_SAVEDPX10BITLOGREFBLACK = 536,
        GCI_SAVEDPX10BITLOGGAMMA = 537,
        GCI_SAVEDPX10BITLOGFILMGAMMA = 538,

        GCI_SAVEQTPLAYBACKRATE = 550,

        GCI_SAVECCIQUALITY = 560,

        GCI_NOPROCESSING = 601,

        GCI_CINEDESCRIPTION = 603,

    }

    //
    ////////////////
    //
    public enum FileType : uint
    {
        MIFILE_RAWCINE = 0,
        MIFILE_CINE = 1,
        MIFILE_JPEGCINE = 2,
        MIFILE_AVI = 3,
        MIFILE_TIFCINE = 4,
        MIFILE_MPEG = 5,
        MIFILE_MXFPAL = 6,
        MIFILE_MXFNTSC = 7,
        MIFILE_QTIME = 8,
    }

    //
    ////////////////
    //
    public enum Compression : uint
    {
        RGB = 0,        // none (RGB)
        JPEG = 1,
        UNINT = 2,      // uninterpolated raw pixels from sensor, no compression
                        // CFA  GBRG / RGGB 
        MPEG = 3,
        MPEG2 = 4
    }

    //
    ////////////////
    //
    public enum GAD : uint
    {
        GAD_TIMEXP = 1001,      // both image time and exposure
        GAD_TIME = 1002,
        GAD_EXPOSURE = 1003,
        GAD_RANGE1 = 1004,      // range data 
        GAD_BINSIG = 1005,      // image binary signals multichannels multisample
                                // 8 samples and or channels per byte
        GAD_ANASIG = 1006,      // image analog signals multichannels multisample
                                // 2 bytes per sample

        GAD_SMPTETC = 1007,	    // SMPTE time code block
        GAD_SMPTETCU = 1008,
    }


    //
    ////////////////
    //
    public enum OFN : uint
    {
        SINGLESELECT = 0,
        MULTISELECT  = 1
    }

    //
    ////////////////
    //
    public enum UseCase : int
    {
        UC_VIEW = 1,	// Use case - view
        UC_SAVE = 2     // Use case - save
    }

    #endregion

    public static class PhFile
    {
        public const Int32 MAX_PATH         = 260;  //  cine file name
        public const Int32 MAX_MULTI_PATH   = 32768;

        public const int ColorMatrixSize    = 9;
        public const int ToneArraySize      = 32 * 2;
        public const int TONE_POINTS_NO     = 34;

        #region Create & Destroy Cine Objects

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineLive(Int32 cam, ref IntPtr pCH);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhNewCineFromCamera(Int32 cam, Int32 CineNo, ref IntPtr pCH);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhNewCineFromFile(
            [param: In, MarshalAs(UnmanagedType.LPStr)] StringBuilder szFN, ref IntPtr pCH);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhDuplicateCine(ref IntPtr phCDest, IntPtr hCSrc);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool PhGetOpenCineName(IntPtr szFileName, [MarshalAs(UnmanagedType.U4)]OFN Options);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhDestroyCine(IntPtr CH);

        #endregion

        #region Read Cine Images

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineImage(IntPtr hC, ref ImRange rng, IntPtr pPixelBuffer, UInt32 bufferByteSize, ref IH pIH);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetUseCase(IntPtr CH, [MarshalAs(UnmanagedType.I4)]UseCase cineUseCaseID);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetUseCase(IntPtr CH, out UseCase cineUseCaseID);
       
        #endregion

        #region Save Cine Images to File

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool PhGetSaveCineName(IntPtr CH);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool PhGetSaveCinePath(IntPtr CH);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhWriteCineFile(IntPtr CH, PROGRESSCB pfnCallback);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhWriteCineFileAsync(IntPtr CH, PROGRESSCB pfnCallback);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhStopWriteCineFileAsync(IntPtr CH);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetWriteCineFileProgress(IntPtr CH, ref UInt32 progress);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetWriteCineFileProgressAll(IntPtr pSaveCineInfo, ref UInt32 count);
             
        #endregion

        #region Cine Parameters


        //
        ////////// PhSetCineInfo Overload
        //
        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetCineInfo(IntPtr CH, [MarshalAs(UnmanagedType.U4)]CineInfo InfName, IntPtr pInfVal);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetCineInfo(IntPtr CH, [MarshalAs(UnmanagedType.U4)]CineInfo InfName, ref IntPtr pInfVal);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetCineInfo(IntPtr CH, [MarshalAs(UnmanagedType.U4)]CineInfo InfName, ref Int32 infVal);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetCineInfo(IntPtr CH, [MarshalAs(UnmanagedType.U4)]CineInfo InfName, ref UInt32 infVal);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetCineInfo(IntPtr CH, [MarshalAs(UnmanagedType.U4)]CineInfo InfName, ref float infVal);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhSetCineInfo(IntPtr CH, [MarshalAs(UnmanagedType.U4)]CineInfo InfName, ref RECT infVal);


        //
        ////////// PhGetCineInfo Overload
        //
        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineInfo(IntPtr CH, [MarshalAs(UnmanagedType.U4)]CineInfo InfName, IntPtr pInfVal);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineInfo(IntPtr CH, [MarshalAs(UnmanagedType.U4)]CineInfo InfName, out IntPtr pInfVal);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineInfo(IntPtr CH, [MarshalAs(UnmanagedType.U4)]CineInfo InfName, out Int32 infVal);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineInfo(IntPtr CH, [MarshalAs(UnmanagedType.U4)]CineInfo InfName, out UInt32 infVal);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineInfo(IntPtr CH, [MarshalAs(UnmanagedType.U4)]CineInfo InfName, out StringBuilder pInfVal);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineInfo(IntPtr CH, [MarshalAs(UnmanagedType.U4)]CineInfo InfName, out RECT pInfVal);

        //
        ////////// 
        //
        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineAuxData(IntPtr CH, Int32 ImageNumber, [MarshalAs(UnmanagedType.U4)] GAD SelectionCode, UInt32 DataSize, IntPtr pData);

        //
        ////////// PhMeasureCineWB Overload
        //
        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhMeasureCineWB(IntPtr cineHandle, ref Point p, int SquareSide,
            ref ImRange rng, ref WBGain wb, out uint SatCnt);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhMeasureCineWB(IntPtr cineHandle, ref Point p, int SquareSide,
            ref ImRange rng, IntPtr wb, out uint SatCnt);

        //
        //////////
        //
        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhMeasureCineWB(IntPtr cineHandle, ref Point p, int SquareSide,
            ref ImRange rng, ref WBGain wb, IntPtr nullSatCnt);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhPrintTime(IntPtr cineHandle, int ImNo, uint Options, IntPtr szTime);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineTriggerTime(IntPtr cineHandle, IntPtr pTriggerTime);

        [DllImport("phfile.dll", CallingConvention = CallingConvention.Cdecl)]
        public static extern HRESULT PhGetCineTriggerTime(IntPtr cineHandle, ref Time64 t64);
        
        #endregion

    }
}
