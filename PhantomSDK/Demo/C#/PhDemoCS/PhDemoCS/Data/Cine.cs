using System;
using System.Collections.Generic;
using System.Text;
using PhDemoCS.Util;
using System.Drawing;
using System.Windows.Forms;
using PhSharp;


namespace PhDemoCS.Data
{
    /// <summary>
    /// A class that encapsulates a cine handle.
    /// </summary>
    public class Cine : IDisposable, ICloneable
    {
        public const string PREVIEW_NAME = "Preview";

        private bool zIsLive;
        /// <summary>
        /// True if the cine is used for camera live images, false if it is a true stored cine
        /// </summary>
        public bool IsLive
        {
            get { return this.zIsLive; }
        }

        public Cine(string cineFilePath)
        {
            StringBuilder filePathSB = new StringBuilder(PhFile.MAX_PATH, PhFile.MAX_PATH);
            filePathSB.Append(cineFilePath);
            ErrorHandler.CheckError(
                PhFile.PhNewCineFromFile(filePathSB, ref zCineHandle));
            zIsLive = false;
        }

        public Cine(int cameraNumber, int cineNumber)
        {
            InitCameraCineHandle(cameraNumber, cineNumber);
        }

        private void InitCameraCineHandle(int cameraNumber, int cineNumber)
        {
            if (cineNumber == (int)CineNumber.CINE_PREVIEW && cineNumber < (int)CineNumber.CINE_CURRENT)
                return;

            if (cineNumber == (int)CineNumber.CINE_CURRENT)
            {
                //Live cine
                ErrorHandler.CheckError(
                    PhFile.PhGetCineLive(cameraNumber, ref zCineHandle));
                zIsLive = true;
            }
            else
            {
                ErrorHandler.CheckError(
                    PhFile.PhNewCineFromCamera(cameraNumber, cineNumber, ref zCineHandle));
                zIsLive = false;
            }
        }

        ~Cine()
        {
            Dispose(false);
        }

        #region CineHandle
        private IntPtr zCineHandle;
        /// <summary>
        /// The cine handle. The structure around which the Cine class is built.
        /// </summary>
        private IntPtr CineHandle
        {
            get { return this.zCineHandle; }
            set { this.zCineHandle = value; }
        }

        /// <summary>
        /// Free memory associated with the current cine handle
        /// </summary>
        private void DestroyCineHandle()
        {
            if (CineHandle != IntPtr.Zero)
            {
                ErrorHandler.CheckError(
                    PhFile.PhDestroyCine(CineHandle));
                CineHandle = IntPtr.Zero;
            }
        }
        #endregion

        #region IDisposable
        private bool zDisposed;

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        /// <summary>
        /// Dispose the memory used by the current object.
        /// </summary>
        /// <param name="disposing">True if it is called from Dispose()</param>
        protected virtual void Dispose(bool disposing)
        {
            if (!this.zDisposed)
            {
                if (disposing)
                {
                    // Dispose managed resources. (No managed resources to dipose yet)
                }

                //Live cine handle is updated after a camera pool refresh. 
                //Live cine handle is managed internally in dlls and is destroyed within ph dlls when camera life ends. 
                //(camera leaves pool or unregister client)
                if (!IsLive)
                    DestroyCineHandle();

                zDisposed = true;
            }
        }

        #endregion

        #region ICloneable
        public object Clone()
        {
            Cine newCine = (Cine)this.MemberwiseClone();

            //Live cine handle cannot have a duplicate, is unique per camera
            if (!this.IsLive)
            {
                //Create a deep copy of the cine handle. The MemberwiseClone copyed just a reference for the handle.
                newCine.zCineHandle = IntPtr.Zero;
                ErrorHandler.CheckError(
                    PhFile.PhDuplicateCine(ref newCine.zCineHandle, this.zCineHandle));
            }
            return newCine;
        }
        #endregion

        #region GeneralInfo
        /// <summary>
        /// First saved image number.
        /// </summary>
        public int FirstImageNumber
        {
            get { return PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_FIRSTIMAGENO); }
        }

        /// <summary>
        /// The number of images a cine contains.
        /// </summary>
        public uint ImageCount
        {
            get
            {
                uint totalImageCount;
                ErrorHandler.CheckError(
                    PhFile.PhGetCineInfo(CineHandle, CineInfo.GCI_IMAGECOUNT, out totalImageCount));
                return totalImageCount;
            }
        }

        /// <summary>
        /// The number of frames after the trigger.
        /// </summary>
        public uint PostTriggerFrames
        {
            get
            {
                uint val;
                ErrorHandler.CheckError(
                    PhFile.PhGetCineInfo(CineHandle, CineInfo.GCI_POSTTRIGGER, out val));
                return val;
            }
        }

        public int LastImageNumber
        {
            get { return (int)((long)FirstImageNumber + ImageCount - 1); }
        }

        /// <summary>
        /// Trigger delay in frames. 
        /// Setting postrigger frames larger than cine partition image capacity will work as a trigger delay.
        /// </summary>
        public uint TriggerDelay
        {
            get
            {
                if (PostTriggerFrames <= ImageCount)
                    return 0;
                else
                    return (uint)((long)PostTriggerFrames - ImageCount);
            }
        }

        public int CameraSerial
        {
            get { return PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_CAMERASERIAL); }
        }

        public int CameraVersion
        {
            get
            {
                int camver = PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_CAMERAVERSION);
                return camver;
            }
        }

        public FileType FileType
        {
            get { return (FileType)PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_FROMFILETYPE); }
        }

        public bool IsFileCine
        {
            get { return PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_ISFILECINE) != 0; }
        }

        public bool HasMetaWB
        {
            get { return PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_WBISMETA) != 0; }
        }

        #region UseCase
        public UseCase GetUseCase()
        {
            UseCase useCase;
            PhFile.PhGetUseCase(CineHandle, out useCase);
            return useCase;
        }

        public void SetUseCase(UseCase cineUseCase)
        {
            PhFile.PhSetUseCase(CineHandle, cineUseCase);
        }
        #endregion
        #endregion

        #region CineMetadata
        public bool IsColor
        {
            get
            {
                int color = PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_ISCOLORCINE);
                return color != 0;
            }
        }

        public bool Is16Bpp
        {
            get
            {
                int is16Bpp = PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_IS16BPPCINE);
                return is16Bpp != 0;
            }
        }

        /// <summary>
        /// Actual image width
        /// </summary>
        public int ImWidth
        {
            get { return PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_IMWIDTH); }
        }

        /// <summary>
        /// Actual image height
        /// </summary>
        public int ImHeight
        {
            get { return PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_IMHEIGHT); }
        }

        /// <summary>
        /// Image width at acquisition
        /// </summary>
        public int ImWidthAcq
        {
            get { return PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_IMWIDTHACQ); }
        }

        /// <summary>
        /// Image height at acquisition
        /// </summary>
        public int ImHeightAcq
        {
            get { return PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_IMHEIGHTACQ); }
        }

        public int BppReal
        {
            get { return PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_REALBPP); }
        }

        public uint FrameRate
        {
            get
            {
                uint val;
                ErrorHandler.CheckError(
                    PhFile.PhGetCineInfo(CineHandle, CineInfo.GCI_FRAMERATE, out  val));
                return val;
            }
        }

        public uint Exposure
        {
            get
            {
                uint val;
                ErrorHandler.CheckError(
                    PhFile.PhGetCineInfo(CineHandle, CineInfo.GCI_EXPOSURE, out  val));
                return val;
            }
        }

        public uint EDRExposureNs
        {
            get
            {
                uint val;
                ErrorHandler.CheckError(
                    PhFile.PhGetCineInfo(CineHandle, CineInfo.GCI_EDREXPOSURENS, out  val));
                return val;
            }
        }
        #endregion

        #region ImageProcessing
        public float Brightness
        {
            get { return PhFileWrappers.GetCineInfoFloatValue(this.CineHandle, CineInfo.GCI_BRIGHT); }
            set { PhFileWrappers.SetCineInfoFloatValue(value, this.CineHandle, CineInfo.GCI_BRIGHT); }
        }

        public float Contrast
        {
            get { return PhFileWrappers.GetCineInfoFloatValue(this.CineHandle, CineInfo.GCI_CONTRAST); }
            set { PhFileWrappers.SetCineInfoFloatValue(value, this.CineHandle, CineInfo.GCI_CONTRAST); }
        }

        public float Gamma
        {
            get { return PhFileWrappers.GetCineInfoFloatValue(this.CineHandle, CineInfo.GCI_GAMMA); }
            set { PhFileWrappers.SetCineInfoFloatValue(value, this.CineHandle, CineInfo.GCI_GAMMA); }
        }

        public float Saturation
        {
            get { return PhFileWrappers.GetCineInfoFloatValue(this.CineHandle, CineInfo.GCI_SATURATION); }
            set { PhFileWrappers.SetCineInfoFloatValue(value, this.CineHandle, CineInfo.GCI_SATURATION); }
        }

        public float Hue
        {
            get { return PhFileWrappers.GetCineInfoFloatValue(this.CineHandle, CineInfo.GCI_HUE); }
            set { PhFileWrappers.SetCineInfoFloatValue(value, this.CineHandle, CineInfo.GCI_HUE); }
        }

        public WBGain WhiteBalanceGain
        {
            get
            {
                WBGain wb;
                if (HasMetaWB)
                    wb = PhFileWrappers.GetCineInfoWB(CineHandle, CineInfo.GCI_WB);//get the WB applied before image interpolation (on raw image)
                else
                    wb = PhFileWrappers.GetCineInfoWB(CineHandle, CineInfo.GCI_WBVIEW);//get the WB applied on already interpolated images
                return wb;
            }
            set
            {
                if (HasMetaWB)
                    PhFileWrappers.SetCineInfoWB(value, CineHandle, CineInfo.GCI_WB);//will be set before image interpolation (on raw image)
                else
                    PhFileWrappers.SetCineInfoWB(value, CineHandle, CineInfo.GCI_WBVIEW);//will be set on already interpolated images
            }
        }

        public int Rotate
        {
            get { return PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_ROTATE); }
            set { PhFileWrappers.SetCineInfoIntegerValue(value, this.CineHandle, CineInfo.GCI_ROTATE); }
        }

        public bool FlipH
        {
            get { return (PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_FLIPH) == 1); }
            set
            {
                int val = value ? 1 : 0;
                PhFileWrappers.SetCineInfoIntegerValue(val, this.CineHandle, CineInfo.GCI_FLIPH);
            }
        }

        public bool FlipV
        {
            get { return (PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_FLIPV) == 1); }
            set
            {
                int val = value ? 1 : 0;
                PhFileWrappers.SetCineInfoIntegerValue(val, this.CineHandle, CineInfo.GCI_FLIPV);
            }
        }

        public float Sensitivity
        {
            get { return PhFileWrappers.GetCineInfoFloatValue(CineHandle, CineInfo.GCI_GAIN16_8); }
            set { PhFileWrappers.SetCineInfoFloatValue(value, this.CineHandle, CineInfo.GCI_GAIN16_8); }
        }

        // felix
        public bool Resample
        {
            get { return (PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_RESAMPLEACTIVE) != 0); }
            set { PhFileWrappers.SetCineInfoIntegerValue(value ? 1 : 0, this.CineHandle, CineInfo.GCI_RESAMPLEACTIVE); }
        }
        public int ResampleWidth
        {
            get { return PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_RESAMPLEWIDTH); }
            set { PhFileWrappers.SetCineInfoIntegerValue(value, this.CineHandle, CineInfo.GCI_RESAMPLEWIDTH); }
        }
        public int ResampleHeight
        {
            get { return PhFileWrappers.GetCineInfoIntegerValue(this.CineHandle, CineInfo.GCI_RESAMPLEHEIGHT); }
            set { PhFileWrappers.SetCineInfoIntegerValue(value, this.CineHandle, CineInfo.GCI_RESAMPLEHEIGHT); }
        }
        #endregion

        #region GetImage
        public HRESULT GetCineImage(ImRange imgRange, IntPtr pImgBuffer, uint imgSizeInBytes, ref IH imgHeader)
        {
            HRESULT result = PhFile.PhGetCineImage(zCineHandle, ref imgRange, pImgBuffer, imgSizeInBytes, ref imgHeader);
            return result;
        }

        /// <summary>
        /// Maximum image size in bytes. Used with PhGetCineImage.
        /// </summary>
        public uint MaxImageSizeInBytes
        {
            get
            {
                uint imgSizeInBytes = 0;
                ErrorHandler.CheckError(
                    PhFile.PhGetCineInfo(CineHandle, CineInfo.GCI_MAXIMGSIZE, out imgSizeInBytes));
                return imgSizeInBytes;
            }
        }

        public void SetVFlipView(bool flipV)
        {
            PhFileWrappers.SetCineInfoIntegerValue(flipV ? 1 : 0, CineHandle, CineInfo.GCI_VFLIPVIEWACTIVE);
        }
        #endregion

        #region SaveCine
        /// <summary>
        /// Display the get cine name dialog.
        /// </summary>
        /// <returns></returns>
        public bool GetSaveCineName()
        {
            return PhFile.PhGetSaveCineName(zCineHandle);
        }

        public void SaveCine(PROGRESSCB pfnCallback)
        {
            ErrorHandler.CheckError(
                PhFile.PhWriteCineFile(zCineHandle, pfnCallback));
        }

        //threaded version of save cine
        public bool StartSaveCineAsync(PROGRESSCB pfnCallback)
        {
            ErrorHandler.CheckError(
                PhFile.PhWriteCineFileAsync(zCineHandle, pfnCallback));

            return ErrorHandler.LastErrorCode >= 0;
        }

        public void StopSaveCineAsync()
        {
            ErrorHandler.CheckError(
                PhFile.PhStopWriteCineFileAsync(zCineHandle));
        }

        public HRESULT GetSaveCineError()
        {
            int errCode;
            ErrorHandler.CheckError(
                PhFile.PhGetCineInfo(zCineHandle, CineInfo.GCI_WRITEERR, out errCode));
            return (HRESULT)errCode;
        }
        #endregion

        #region Utils
        public static int Parse(string cineStrID, int firstFlashCine)
        {
            int cineNo = (int)CineNumber.CINE_PREVIEW;
            if (cineStrID == PREVIEW_NAME)
            {
                cineNo = (int)CineNumber.CINE_PREVIEW;
            }
            else if (int.TryParse(cineStrID, out cineNo))
            {
                //the cine number is from ram
            }
            else if (cineStrID.Contains("F") && int.TryParse(cineStrID.Substring(1).Trim(), out cineNo))
            {
                cineNo = firstFlashCine + cineNo - 1;//flash cine number
            }
            else
                throw new NotSupportedException();

            return cineNo;
        }

        public static string GetStringForCineNo(int cineNo, int FirstFlashCine)
        {
            string returnedStr = "";
            if (cineNo == (int)CineNumber.CINE_PREVIEW)
                returnedStr = PREVIEW_NAME;
            else if (cineNo >= FirstFlashCine)
                returnedStr = "F" + (cineNo - FirstFlashCine + 1).ToString();
            else
                returnedStr = cineNo.ToString();

            return returnedStr;
        }
        #endregion
    }
}
