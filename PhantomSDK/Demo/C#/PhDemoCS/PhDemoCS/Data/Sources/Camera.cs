using System;
using System.Collections.Generic;
using System.Text;
using PhDemoCS.Util;
using PhDemoCS.Exceptions;
using System.Runtime.InteropServices;
using PhSharp;
namespace PhDemoCS.Data
{
    public enum CameraStatus
    {
        NotAvailable,
        Preview,
        RecWaitingForTrigger,
        RecPostriggerFrames
    }

    /// <summary>
    /// Class for controlling a Phantom camera, setting camera options or parameters and reading camera info
    /// </summary>
    public class Camera : ISource, IDisposable
    {
        #region Constructor
        public Camera(uint cameraNo)
        {
            CameraNumber = cameraNo;

            InitSerial();
            InitCines();

            offline = offlineState();
        }

        private void InitSerial()
        {
            //We need camera serial whatever it is connected or not. Serial is not changing and will be available when camera is offline.
            StringBuilder cameraNameBuilder = new StringBuilder(PhCon.MAXSTDSTRSZ);
            ErrorHandler.CheckError(
                PhCon.PhGetCameraID(CameraNumber, out zSerial, cameraNameBuilder));
        }

        private void InitCines()
        {
            LiveCine = new Cine((int)CameraNumber, (int)CineNumber.CINE_CURRENT);
            zSelectedCinePartNo = (int)CineNumber.CINE_PREVIEW;
            zSelectedCine = null;
        }
        #endregion

        #region Destructors
        ~Camera()
        {
            Dispose(false);
        }

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
                    // Dispose managed resources.
                    DeleteCines();
                }

                zDisposed = true;
            }
        }
        #endregion

        private void DeleteCines()
        {
            if (LiveCine != null)
                LiveCine.Dispose();
            if (zSelectedCine != null)
                zSelectedCine.Dispose();
        }
        #endregion

        #region Buffers
        uint zCameraNumber;
        /// <summary>
        /// A camera identifier from dlls.
        /// </summary>
        public uint CameraNumber
        {
            get { return this.zCameraNumber; }
            private set { this.zCameraNumber = value; }
        }

        uint zSerial;
        /// <summary>
        /// Serial is a unique camera id that does not change in a session. It will be buffered.
        /// </summary>
        public uint Serial
        {
            get
            {
                return zSerial;
            }
        }

        private Cine zLiveCine;
        /// <summary>
        /// Cine from which live images are taken. Also image processing options will be read or set with this cine.
        /// </summary>
        private Cine LiveCine
        {
            get { return this.zLiveCine; }
            set { this.zLiveCine = value; }
        }

        #region SelectedCineBuffer
        /// <summary>
        /// Selected cine partition number (buffer). Used to keep tack of cine partition selection.
        /// </summary>
        private int zSelectedCinePartNo;
        public int SelectedCinePartNo
        {
            get { return this.zSelectedCinePartNo; }
            set
            {
                //destroy the old selected cine 
                DestroySelectedCine();

                this.zSelectedCinePartNo = value;
            }
        }

        /// <summary>
        /// Indicates if the camera is offline
        /// </summary>
        bool offline;

        public bool offlineState()
        {
            return (PhCon.PhOffline(CameraNumber));
        }

        public bool ParamsChanged()
        {
            bool changed = false;

            PhCon.PhParamsChanged(CameraNumber, out changed);
            return (changed);
        }

        /// <summary>
        /// Did a Camera go from Online  --> Offline or
        /// Did a Camera go from Offline --> Online 
        /// </summary>       
        public bool offlineStateChange()
        {
            bool stateChanged = false;

            bool currentState = offlineState();

            if (offline != currentState)
            {
                offline = currentState;

                stateChanged = true;
            }
            return (stateChanged);
        }

        /// <summary>
        /// The selected cine, other than live cine.
        /// </summary>
        Cine zSelectedCine;

        private void DestroySelectedCine()
        {
            if (zSelectedCine != null)
            {
                zSelectedCine.Dispose();
                zSelectedCine = null;
            }
        }

        #region ISource Members
        /// <summary>
        /// Get a cine from which to read images.
        /// </summary>
        public Cine CurrentCine
        {
            get
            {
                Cine cine;
                if (IsCinePartitionStored(zSelectedCinePartNo))
                {
                    //if stored create the selected cine if needed
                    if (zSelectedCine == null)
                        zSelectedCine = new Cine((int)CameraNumber, SelectedCinePartNo);
                    cine = zSelectedCine;
                }
                else
                {
                    cine = zLiveCine;
                    //The selected cine partition is not stored, destroy the cine to be sure the latest cine handle is used.
                    //If a cine is instantiated in software and then the cine is deleted in camera and recorded again, the cine is not any more actual. 
                    //We have to destroy the cine and create a new one later.
                    DestroySelectedCine();
                }
                return cine;
            }
        }

        #endregion
        #endregion
        #endregion

        #region CameraInfo
        /// <summary>
        /// Read the name of the camera.
        /// </summary>
        public string GetCameraName()
        {
            uint serial;
            StringBuilder cameraNameBuilder = new StringBuilder(PhCon.MAXSTDSTRSZ);
            ErrorHandler.CheckError(
                PhCon.PhGetCameraID(CameraNumber, out serial, cameraNameBuilder));
            return cameraNameBuilder.ToString();
        }

        /// <summary>
        /// Set the name of the camera.
        /// </summary>
        public void SetCameraName(string camName)
        {
            StringBuilder camNameSB = new StringBuilder(PhCon.MAXSTDSTRSZ);
            camNameSB.Append(camName);
            ErrorHandler.CheckError(
                  PhCon.PhSetCameraName(CameraNumber, camNameSB));
        }

        /// <summary>
        /// Get camera version number.
        /// </summary>
        public uint GetVersion()
        {
            uint version;
            ErrorHandler.CheckError(
                PhCon.PhGetVersion(CameraNumber, Versions.GV_CAMERA, out version));
            return version;
        }

        /// <summary>
        /// Get camera marketing name.
        /// </summary>
        public string GetCameraModel()
        {
            IntPtr pValue = Marshal.AllocHGlobal(PhCon.MAXSTDSTRSZ * sizeof(byte));
            PhCon.PhGet(CameraNumber, GS.Model, pValue);
            string cameraModel = Marshal.PtrToStringAnsi(pValue);
            Marshal.FreeHGlobal(pValue);

            return cameraModel;
        }

        /// <summary>
        /// Read the firmware version running in camera.
        /// </summary>
        public uint GetFirmwareVersion()
        {
            uint firmwareVer;
            ErrorHandler.CheckError(
                PhCon.PhGetVersion(CameraNumber, Versions.GV_FIRMWARE, out firmwareVer));
            return firmwareVer;
        }

        /// <summary>
        /// Get the IP address of the camera.
        /// </summary>
        public string GetIPAddress()
        {
            IntPtr ptr = Marshal.AllocHGlobal(PhCon.MAXIPSTRSZ);
            PhCon.PhGet(CameraNumber, GS.IPAddress, ptr);
            string strValue = Marshal.PtrToStringAnsi(ptr);
            Marshal.FreeHGlobal(ptr);
            return strValue;
        }
        #endregion

        #region Camera Options & Parameters
        /// <summary>
        /// Read CameraOptions from camera.
        /// </summary>
        public CameraOptions GetCameraOptions()
        {
            CameraOptions camOptions = new CameraOptions();
            ErrorHandler.CheckError(
                PhCon.PhGetCameraOptions(CameraNumber, ref camOptions));
            return camOptions;
        }

        /// <summary>
        /// Set the CameraOptions in camera.
        /// </summary>
        public void SetCameraOptions(CameraOptions camOptions)
        {
            ErrorHandler.CheckError(
                PhCon.PhSetCameraOptions(CameraNumber, ref camOptions));
        }

        /// <summary>
        /// Read the acquisition parameters from a specified camera cine partition.
        /// </summary>
        public AcquiParams GetAcquisitionParameters(int cinePartNo)
        {
            AcquiParams acquisitionParams = new AcquiParams();
            ErrorHandler.CheckError(
                PhCon.PhGetCineParams(CameraNumber, cinePartNo, ref acquisitionParams, IntPtr.Zero));
            return acquisitionParams;
        }

        /// <summary>
        /// Set the acquisition parameters to a specified camera cine partition.
        /// </summary>
        public void SetAcquisitionParameters(int cinePartNo, AcquiParams acqParams)
        {
            if (this.IsOnSinglePartition)
                ErrorHandler.CheckError(
                    PhCon.PhSetSingleCineParams(this.CameraNumber, ref acqParams));
            else
                ErrorHandler.CheckError(
                    PhCon.PhSetCineParams(this.CameraNumber, cinePartNo, ref acqParams));
        }
        #endregion

        #region Camera Partitons/Cines Infos
        /// <summary>
        /// Were camera options or parameteres changed by annother connection or another application instance?
        /// </summary>
        public bool ParametersExternallyChanged
        {
            get
            {
                bool changed;
                ErrorHandler.CheckError(
                    PhCon.PhParamsChanged(CameraNumber, out changed));
                return changed;
            }
        }

        /// <summary>
        /// Get the count of the recorded cine partitions in camera RAM.
        /// </summary>
        public uint GetRamCineCount()
        {
            uint cntRAM;
            uint cntFlash;
            ErrorHandler.CheckError(
                PhCon.PhGetCineCount(CameraNumber, out cntRAM, out cntFlash));
            return cntRAM;
        }

        /// <summary>
        /// Get the count of the cines in camera flash/CineMag.
        /// </summary>
        public uint GetFlashCineCount()
        {
            uint cntRAM;
            uint cntFlash;
            ErrorHandler.CheckError(
                PhCon.PhGetCineCount(CameraNumber, out cntRAM, out cntFlash));
            return cntFlash;
        }

        public uint GetLastRamCineNo()
        {
            return (int)CineNumber.CINE_FIRST + GetRamCineCount() - 1;
        }

        public uint GetLastFlashCineNo()
        {
            return (uint)GetFirstFlashCine() + GetFlashCineCount() - 1;
        }

        public Cinestatus[] GetRAMCinePartitionsStatus()
        {
            int maxCineCnt = PhCon.PhMaxCineCnt(CameraNumber);
            Cinestatus[] cs = new Cinestatus[maxCineCnt];

            ErrorHandler.CheckError(
                PhCon.PhGetCineStatus(CameraNumber, cs));
            return cs;
        }

        /// <summary>
        /// Get the cine recorded status of a camera cine. Helper function.
        /// </summary>
        public bool IsCinePartitionStored(int cinePartNo)
        {
            Cinestatus cs = GetCinePartitionStatus(cinePartNo);
            return cs.Stored;
        }

        /// <summary>
        /// Get the cine status of a camera cine.
        /// </summary>
        public Cinestatus GetCinePartitionStatus(int cinePartNo)
        {
            if (cinePartNo >= (int)CineNumber.CINE_PREVIEW && cinePartNo < (int)GetFirstFlashCine())
            {
                Cinestatus[] cstats = GetRAMCinePartitionsStatus();
                return cstats[cinePartNo];
            }
            else if (cinePartNo <= (int)GetLastFlashCineNo())
            {
                Cinestatus cs = new Cinestatus();
                cs.Stored = true;
                return cs;
            }
            else
            {
                Cinestatus cs = new Cinestatus(); ;
                cs.Stored = false;
                return cs;
            }
        }

        /// <summary>
        /// Determine if the camera has a stored cine partition in RAM.
        /// </summary>
        public bool GetHasStoredRAMPart()
        {
            if (SupportsRecordingCines)
            {
                Cinestatus[] cstats = GetRAMCinePartitionsStatus();
                uint partCount = GetPartitionCount();
                for (int iCine = 0; iCine <= partCount; iCine++)
                {
                    if (cstats[iCine].Stored)
                        return true;
                }
            }
            return false;
        }

        public bool IsOnSinglePartition
        {
            get { return GetPartitionCount() == 1; }
        }

        /// <summary>
        /// Get the number of camera RAM cine partitions.
        /// </summary>
        public uint GetPartitionCount()
        {
            uint partCount = 0;
            ErrorHandler.CheckError(
                    PhCon.PhGetPartitions(CameraNumber, ref partCount, IntPtr.Zero));
            return partCount;
        }

        /// <summary>
        /// Get the number of camera first flash cine.
        /// </summary>
        public int GetFirstFlashCine()
        {
            int firstFlashCine = PhCon.PhFirstFlashCine(CameraNumber);

            return (firstFlashCine);
        }

        /// <summary>
        /// Set the number of camera RAM cine partitions.
        /// </summary>
        public void SetPartitionCount(uint partCount)
        {
            //set equal size partition into ram

            uint[] partitionsSize = GeneratePartitionsWeights(partCount);
            ErrorHandler.CheckError(
                PhCon.PhSetPartitions(CameraNumber, partCount, partitionsSize));
        }

        /// <summary>
        /// Get the maximum number of RAM cine partitions.
        /// </summary>
        public int GetMaxPartitionCount()
        {
            int maxPartCount;
            //the maximum number of partitions will not exceed Int32.Max, no need to use uint
            ErrorHandler.CheckError(
                PhCon.PhGet(CameraNumber, GS.MaxPartitionCount, out maxPartCount));
            return maxPartCount;
        }

        /// <summary>
        /// Determine the current cine partition number where the recording it taking place.
        /// </summary>
        public int GetActiveCineNo()
        {
            Cinestatus[] cs = GetRAMCinePartitionsStatus();
            for (int cineIndex = 0; cineIndex < cs.Length; cineIndex++)
            {
                if (cs[cineIndex].Active)
                    return cineIndex;
            }

            //In case no cine is active an error may be thrown
            //All cameras should have an active cine at a momment. CineStation does not have active cine.
            return (int)CineNumber.CINE_PREVIEW;
        }

        /// <summary>
        /// Get the status of the camera.
        /// </summary>
        public CameraStatus CamStatus
        {
            get
            {
                if (SupportsRecordingCines)
                {
                    int activeCineNo = GetActiveCineNo();
                    if (activeCineNo == (int)CineNumber.CINE_PREVIEW)
                        return CameraStatus.Preview;
                    else
                    {
                        Cinestatus[] cstats = GetRAMCinePartitionsStatus();
                        if (cstats[activeCineNo].Triggered)
                            return CameraStatus.RecPostriggerFrames;
                        else
                            return CameraStatus.RecWaitingForTrigger;
                    }
                }
                else
                    return CameraStatus.NotAvailable;
            }
        }

        /// <summary>
        /// Is false when the device does not have acqusition parts.
        /// As a result it will not provide live images or recording actions. 
        /// The device can be a CineStation.
        /// </summary>
        public bool SupportsRecordingCines
        {
            get
            {
                int val;
                ErrorHandler.CheckError(
                    PhCon.PhGet(CameraNumber, GS.SupportsRecordingCines, out val));
                return val != 0;
            }
        }
        #endregion

        #region Actions
        /// <summary>
        /// Start recording in specified partition deleting it first.
        /// </summary>
        /// <param name="cineNo">Cine number in which to start recording</param>
        public void RecordSpecificCine(int cineNo)
        {

            ErrorHandler.CheckError(
                PhCon.PhRecordSpecificCine(CameraNumber, cineNo));
        }

        /// <summary>
        /// Deletes all stored cine partitions and start recording
        /// </summary>
        public void Record()
        {
            ErrorHandler.CheckError(
                PhCon.PhRecordCine(CameraNumber));
        }

        /// <summary>
        /// Send a software trigger to camera.
        /// </summary>
        public void SendTrigger()
        {
            ErrorHandler.CheckError(
                PhCon.PhSendSoftwareTrigger(CameraNumber));
        }
        #endregion

        #region Utils
        public override string ToString()
        {
            string returnedStr = "";
            returnedStr = GetCameraName() + " (" + Serial.ToString() + ")";

            //
            // see if the camera is offline
            //
            if (offline == true)
            {
                returnedStr = returnedStr + "[Offline]";
            }

            if (string.IsNullOrEmpty(returnedStr))
                returnedStr = "";

            return returnedStr;
        }

        /// <summary>
        /// Create equal length partition weights.
        /// </summary>
        private static uint[] GeneratePartitionsWeights(uint count)
        {
            float percent;

            uint[] weights = new uint[count];
            for (int i = 0; i < count; i++)
            {
                percent = (float)100 / count;
                //multiply by 100 to get 2 point precision into int weights
                weights[i] = (uint)Math.Round(100 * percent);
            }
            return weights;
        }
        #endregion
    }
}
