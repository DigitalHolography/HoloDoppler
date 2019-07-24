using System;
using System.Collections.Generic;
using System.Text;
using System.Collections;
using PhDemoCS.Data;
using PhDemoCS.Forms;
using PhSharp;


namespace PhDemoCS
{
    /// <summary>
    /// Manages online camera list.
    /// </summary>
    public class PoolRefresher
    {
        uint cameraCount = 0;

        public PoolRefresher()
        {
            CameraList = new List<Camera>(2);
        }

        #region Properties
        List<Camera> zCameraList;
        private List<Camera> CameraList
        {
            get { return this.zCameraList; }
            set { this.zCameraList = value; }
        }

        #endregion


        #region Methods
        public void InitCameraList()
        {
            CameraList = GetEthernetCameras();
        }

        public int GetCameraListLength()
        {
            return CameraList.Count;
        }

        public Camera GetCameraAt(int index)
        {
            if (index >= 0 && index < CameraList.Count)
                return CameraList[index];
            else
                return null;
        }

        private List<Camera> GetEthernetCameras()
        {
            List<Camera> cameraList = new List<Camera>();

            //
            // Get the number of cameras connected
            //
            uint camCount;

            ErrorHandler.CheckError(
                PhCon.PhGetCameraCount(out camCount));

            if (camCount > 0)
            {
                cameraCount = camCount;

                for (uint CamNr = 0; CamNr < camCount; CamNr++)
                {
                    Camera cam = new Camera(CamNr);
                    cameraList.Add(cam);
                }
            }
            else
            {
                //
                // place a default simulated camera (VEO 710S) in the case of no camera connected
                //
                ErrorHandler.CheckError(
                    PhCon.PhAddSimulatedCamera(7001, 1234));
                Camera simCam = new Camera(0);
                cameraList.Add(simCam);
                cameraCount = 1;
            }

            return cameraList;
        }

        /// <summary>
        /// Did a Camera go from Online  --> Offline or
        /// Did a Camera go from Offline --> Online 
        /// </summary>
        public bool cameraStateChange()
        {
            bool refreshNeeded = false;
            int camCount = CameraList.Count;
            int icam = 0;

            while (icam < camCount)
            {
                Camera cam = CameraList[icam];

                //
                // see if the camera is offline state changed
                //
                refreshNeeded = cam.offlineStateChange();

                //
                // if any camera needs updating we do all
                //
                if (refreshNeeded == true)
                {
                    break;
                }
                icam++;
            }

            return (refreshNeeded);
        }

        /// <summary>
        /// Checks if the current camera list is up to date. If not refreshes the list.
        /// </summary>
        public bool RefreshCameras()
        {
            bool refreshNeeded = false;
            uint currentCameraCount;


            //
            // has the number of cameras connected changed
            //
            PhCon.PhGetCameraCount(out currentCameraCount);
            

            if (currentCameraCount > cameraCount) 
            {
                //
                // save new count
                cameraCount = currentCameraCount;

                //
                //clear all cameras resources
                //
                DisposeCameras();

                InitCameraList();

                refreshNeeded = true;
            }

            return (refreshNeeded);
        }

        public Camera GetCameraWithSerial(uint serial)
        {
            int index;
            return GetCameraWithSerial(serial, out index);
        }

        public Camera GetCameraWithSerial(uint serial, out int index)
        {
            int camCount = CameraList.Count;
            for (int icam = 0; icam < camCount; icam++)
            {
                Camera cam = CameraList[icam];
                if (cam.Serial == serial)
                {
                    index = icam;
                    return cam;
                }
            }

            index = -1;
            return null;
        }

        /// <summary>
        /// Will clear all unamanaged resources allocated for all cameras.
        /// Always call this before UnRegisterClient.
        /// </summary>
        public void DisposeCameras()
        {
            for (int icam = 0; icam < CameraList.Count; icam++)
            {
                CameraList[icam].Dispose();
            }
        }
        #endregion
    }
}
