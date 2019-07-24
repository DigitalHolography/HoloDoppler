using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;
using PhDemoCS.Data;
using PhDemoCS.UI;
using System.IO;
using PhDemoCS.Util;
using PhDemoCS.Forms;
using System.Runtime.InteropServices;
using PhSharp;


namespace PhDemoCS
{
    public partial class PhDemo : Form
    {
        private const int REFRESH_TIMER_INTERVAL = 30;

        //
        // check for new cameras every 5 seconds
        //
        private const int REFRESH_CAMERA_POOL_INTERVAL = 5000 / REFRESH_TIMER_INTERVAL;

        private const string FILE_SOURCE_NAME = "File";
        private const string IMPROC_FORMAT = "#0.00";

        private int cameraPoolRefreshTimer = 0;
        private Timer zRefreshTimer;
        private PoolBuilder zPoolBuilder;

        public PhDemo()
        {
            InitializeComponent();

            zRefreshTimer = new Timer();
            zRefreshTimer.Interval = REFRESH_TIMER_INTERVAL;
            zRefreshTimer.Tick += new EventHandler(zRefreshTimer_Tick);
        }

        #region UtilMembers
        //refresh UI flags
        private bool zRefreshing;
        private bool zPartComboRefreshing;

        /// <summary>
        /// Last cine status of selected cine.
        /// </summary>
        private Cinestatus zSelectedCineLastStatus;
        /// <summary>
        /// Previous tick time, used to update image refresh rate
        /// </summary>
        private DateTime zPreviousTime;
        /// <summary>
        /// Object which is used to save a cine.
        /// </summary>
        private CineSaver zCineSaver;
        #endregion

        #region Properties
        private ISource zSelectedSource;
        public ISource SelectedSource
        {
            get { return this.zSelectedSource; }
            set { this.zSelectedSource = value; }
        }

        private PoolRefresher zPoolRefresher;
        public PoolRefresher PoolRefresher
        {
            get { return this.zPoolRefresher; }
            set { this.zPoolRefresher = value; }
        }

        private FileSource zOpenedFile;
        public FileSource OpenedFile
        {
            get { return this.zOpenedFile; }
            set { this.zOpenedFile = value; }
        }

        private CinePlayer zCinePlayer;
        public CinePlayer CinePlayer
        {
            get { return this.zCinePlayer; }
            set { this.zCinePlayer = value; }
        }
        #endregion

        #region Load&Close
        private void PhDemo_Load(object sender, EventArgs e)
        {
            InitPhDemo();
        }

        private void PhDemo_FormClosing(object sender, FormClosingEventArgs e)
        {
            StopPhDemo();
        }

        private void InitPhDemo()
        {
            try
            {
                ErrorHandler.zMainForm = this;

                zPreviousTime = DateTime.Now;

                //Enable message boxes from dlls
                ErrorHandler.CheckError(
                    PhCon.PhEnableMessages(true));

                //Initialize registration object
                //Log folder is NULL to let dll's use default log folder: \Application Data\Phantom\DLLVersion
                //You may specify log folder
                zPoolBuilder = new PoolBuilder(this, null);
                zPoolBuilder.Register();
                if (!zPoolBuilder.IsRegistered)
                    Application.Exit();

                PoolRefresher = new PoolRefresher();
                //create the camera list
                PoolRefresher.InitCameraList();

                CinePlayer = new CinePlayer(pictureBoxPreview, buttonPlayCine, trackBarPlay, textBoxFrameNumber, labelRangeFirst, labelRangeLast);

                RefreshSourceAndCine();

                zRefreshTimer.Start();
            }
            catch (DllNotFoundException dllEx)
            {
                MessageBox.Show(this, string.Format("An important dll required to run this demo was not found. {0} Exception message: {1}.Application will exit",
                    Environment.NewLine, dllEx.Message), "Dll not found", MessageBoxButtons.OK);
                Application.Exit();
            }
        }

        private void StopPhDemo()
        {
            try
            {
                zRefreshTimer.Stop();
                if (zPoolBuilder != null && zPoolBuilder.IsRegistered)
                {
                    if (zCineSaver != null)
                    {
                        if (zCineSaver.Started)
                            zCineSaver.StopSave();
                        zCineSaver.Dispose();
                        zCineSaver = null;
                    }

                    //clean resources
                    if (CinePlayer != null)
                    {
                        CinePlayer.Dispose();
                        CinePlayer = null;
                    }
                    if (PoolRefresher != null)
                        PoolRefresher.DisposeCameras();
                    if (OpenedFile != null)
                    {
                        OpenedFile.Dispose();
                        OpenedFile = null;
                    }

                    //always unregister at application close
                    if (zPoolBuilder != null)
                        zPoolBuilder.Unregister();
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(this, string.Format("PhDemo encountered an exception on closing: {0}", ex.Message), "Exception", MessageBoxButtons.OK);
            }
        }
        #endregion

        #region RefreshMethods

        private void RefreshSourceAndCine()
        {
            zRefreshing = true;

            RefreshSourceCombo();
            SelectSourceFromCombo();
            RefreshCineCombo();
            SelectCineFromCombo();

            zRefreshing = false;
        }

        /// <summary>
        /// Refresh the soruce combo with available cameras, add file selection. Select the current selection.
        /// </summary>
        private void RefreshSourceCombo()
        {
            comboBoxSource.Items.Clear();
            //populate listbox with current cameras
            List<string> cameraItems = new List<string>();
            int cameraCount = PoolRefresher.GetCameraListLength();
            for (int icam = 0; icam < cameraCount; icam++)
            {
                Camera cam = PoolRefresher.GetCameraAt(icam);
                cameraItems.Add(cam.ToString());
            }
            comboBoxSource.Items.AddRange(cameraItems.ToArray());
            //add the file ID if any opened file exist
            if (OpenedFile != null)
                comboBoxSource.Items.Add(FILE_SOURCE_NAME);

            //select combo item index based on selected source
            //the camera list index is the same as the combo item index
            if (SelectedSource is Camera)
            {
                Camera selectedCamera = SelectedSource as Camera;
                int cameraIndex;
                Camera cam = PoolRefresher.GetCameraWithSerial(selectedCamera.Serial, out cameraIndex);
                if (cam != null)
                    comboBoxSource.SelectedIndex = cameraIndex;
                else
                    comboBoxSource.SelectedIndex = 0;
            }
            else if (SelectedSource is FileSource)
            {
                comboBoxSource.SelectedIndex = comboBoxSource.Items.Count - 1;//select last item
            }
            else if (SelectedSource == null)
            {
                comboBoxSource.SelectedIndex = comboBoxSource.Items.Count > 0 ? 0 : -1;
            }
        }


        /// <summary>
        /// Populates cineCombo with avaialable cines. Select the selected cine.
        /// </summary>
        private void RefreshCineCombo()
        {
            int firstFlashCine;

            comboBoxCine.Items.Clear();
            if (SelectedSource is Camera)
            {
                //populate the list with available cines
                Camera selectedCamera = SelectedSource as Camera;
                int selectedIndex = 0;

                //RAM cine partitions should not be added on the list for CineStation devices.
                if (selectedCamera.SupportsRecordingCines)
                {
                    int startCineNo = (int)CineNumber.CINE_PREVIEW;
                    int lastCineNo = (int)selectedCamera.GetPartitionCount();
                    firstFlashCine = selectedCamera.GetFirstFlashCine();
                    for (int iCine = startCineNo; iCine <= lastCineNo; iCine++)
                    {
                        string cineStr = Cine.GetStringForCineNo(iCine, firstFlashCine);
                        comboBoxCine.Items.Add(cineStr);
                        if (iCine == selectedCamera.SelectedCinePartNo)
                            selectedIndex = comboBoxCine.Items.Count - 1;
                    }
                }

                int lastFlashCineNo = (int)selectedCamera.GetLastFlashCineNo();
                firstFlashCine = selectedCamera.GetFirstFlashCine();
                for (int iCine = firstFlashCine; iCine <= lastFlashCineNo; iCine++)
                {
                    string cineStr = Cine.GetStringForCineNo(iCine, firstFlashCine);
                    comboBoxCine.Items.Add(cineStr);
                    if (iCine == selectedCamera.SelectedCinePartNo)
                        selectedIndex = comboBoxCine.Items.Count - 1;
                }
                if (comboBoxCine.Items.Count > 0)
                    comboBoxCine.SelectedIndex = selectedIndex;

            }
            else if (SelectedSource is FileSource)
            {
                if (OpenedFile != null)
                {
                    comboBoxCine.Items.Add(Path.GetFileName((OpenedFile as FileSource).CineFilePath));
                    comboBoxCine.SelectedIndex = 0;
                }
            }
        }

        /// <summary>
        /// Select the source from the selected combo item.
        /// </summary>
        private void SelectSourceFromCombo()
        {
            if (comboBoxSource.SelectedItem != null)
            {
                if (comboBoxSource.SelectedItem.ToString() == FILE_SOURCE_NAME)//file source selected
                {
                    SelectedSource = OpenedFile;
                }
                else
                {
                    uint serial;
                    //parse camera serial from combo item. The camera serial is an unique ID
                    string cameraStr = comboBoxSource.SelectedItem.ToString();
                    string[] strParts = cameraStr.Split(new string[] { "(", ")" }, StringSplitOptions.None);
                    if (uint.TryParse(strParts[1], out serial))
                    {
                        //select the camera with serial
                        SelectedSource = PoolRefresher.GetCameraWithSerial(serial);
                        RefreshPartitionCombo();
                    }
                }
            }
            else
                SelectedSource = null;

            buttonCamInfo.Visible = SelectedSource is Camera;

            //show/hide camera settings
            panelCameraSettings.Visible = SelectedSource is Camera && (SelectedSource as Camera).SupportsRecordingCines;

            panelParameters.Enabled = SelectedSource != null;

            //
            // Assume the Image Size has changed
            //
            CinePlayer.updateImageSize = true;
        }

        /// <summary>
        /// Selects the cine from combo selected item.
        /// </summary>
        private void SelectCineFromCombo()
        {
            if (SelectedSource is Camera)
            {
                Camera selectedCam = SelectedSource as Camera;
                int firstFlashCine = selectedCam.GetFirstFlashCine();
                selectedCam.SelectedCinePartNo = Cine.Parse(comboBoxCine.SelectedItem.ToString(), firstFlashCine);

                Cinestatus selectedCineStatus = selectedCam.GetCinePartitionStatus(selectedCam.SelectedCinePartNo);
                zSelectedCineLastStatus = selectedCineStatus;

                //if cine partition is empty
                if (selectedCam.CurrentCine != null && !selectedCineStatus.Stored && !selectedCineStatus.Triggered)
                    //make the selected empty partition active in camera (start recording)
                    selectedCam.RecordSpecificCine(selectedCam.SelectedCinePartNo);
            }

            RefreshAcqParameters();
            RefreshPlayInterface();
            RefreshImProcessing();

            //
            // Assume the Image Size has changed
            //
            CinePlayer.updateImageSize = true;
        }

        /// <summary>
        /// Populates partition combo with possible partitions numbers
        /// </summary>
        private void RefreshPartitionCombo()
        {
            zPartComboRefreshing = true;

            comboBoxPartitions.Items.Clear();
            if (SelectedSource is Camera)
            {
                Camera selectedCamera = SelectedSource as Camera;
                if (selectedCamera.SupportsRecordingCines)
                {
                    //populate partitions combo up to the number of maximum partitions
                    int maxPartCount = selectedCamera.GetMaxPartitionCount();

                    comboBoxPartitions.SelectedItem = null;
                    comboBoxPartitions.Text = "";

                    if (maxPartCount <= 1)
                    {
                        comboBoxPartitions.Items.Add("1");
                        comboBoxPartitions.SelectedIndex = 0;
                        comboBoxPartitions.Enabled = false;
                    }
                    else
                    {
                        uint partNo = selectedCamera.GetPartitionCount();
                        int selectedIndex = 0;
                        for (int i = 1; i < maxPartCount; i++)
                        {
                            comboBoxPartitions.Items.Add(i);
                            if (i == partNo)
                                selectedIndex = i - 1;
                        }
                        comboBoxPartitions.SelectedIndex = selectedIndex;
                    }
                }
            }
            zPartComboRefreshing = false;
        }

        /// <summary>
        /// Refreshes acquisition parameters
        /// </summary>
        private void RefreshAcqParameters()
        {
            if (SelectedSource is Camera)
            {
                Camera selectedCamera = SelectedSource as Camera;
                Cine selectedCine = selectedCamera.CurrentCine;
                bool selPartIsStored = selectedCamera.IsCinePartitionStored(selectedCamera.SelectedCinePartNo);
                if (selPartIsStored)
                {
                    RefreshAcquisitionParamtersStoredCine(selectedCine);
                }
                else
                {
                    RefreshAcquisitionParamtersNotStoredCine(selectedCamera, selectedCine);
                }
            }
            else if (SelectedSource is FileSource)
            {
                RefreshAcquisitionParamtersStoredCine(SelectedSource.CurrentCine);
            }
        }



        /// <summary>
        /// Refreshes acquisition parameters for cine partitions.
        /// </summary>
        private void RefreshAcquisitionParamtersNotStoredCine(Camera selectedCamera, Cine selectedCine)
        {
            RefreshAcquisitionUI_RW(false);

            //get the acquisition parameters
            AcquiParams acqParams = selectedCamera.GetAcquisitionParameters(selectedCamera.SelectedCinePartNo);

            Point currentResolution = new Point();
            currentResolution.X = (int)acqParams.ImWidth;
            currentResolution.Y = (int)acqParams.ImHeight;

            uint resolutionCount = PhCon.MAX_RESOLUTIONS;
            Point[] resolutions = new Point[PhCon.MAX_RESOLUTIONS];
            //get a list of standard supported resolution
            ErrorHandler.CheckError(
                PhCon.PhGetResolutions(selectedCamera.CameraNumber, resolutions, ref resolutionCount, IntPtr.Zero, IntPtr.Zero));

            //update resolution combo
            List<string> resolutionList = new List<string>();
            string selectedResolution = "";
            for (int ires = 0; ires < resolutionCount; ires++)
            {
                Point res = resolutions[ires];
                ResolutionItem resItem = new ResolutionItem((uint)res.X, (uint)res.Y);
                resolutionList.Add(resItem.ToString());
                if (res.Equals(currentResolution))
                    selectedResolution = resItem.ToString();
            }
            comboResolution.BeginUpdate();
            comboResolution.Items.Clear();
            comboResolution.Items.AddRange(resolutionList.ToArray());
            comboResolution.SelectedItem = selectedResolution;
            comboResolution.EndUpdate();

            //update bitdepth combo
            comboBitDepth.BeginUpdate();
            comboBitDepth.Items.Clear();
            uint count;
            uint[] bitDepths = new uint[20];
            //get the supported list of bitdepths
            ErrorHandler.CheckError(
                PhCon.PhGetBitDepths(selectedCamera.CameraNumber, out count, bitDepths));
            //get the actual bitdepth
            uint actualBitDepth = selectedCamera.GetCameraOptions().RAMBitDepth;
            int selectedIndexBitDepth = 0;
            for (int iBitDepth = 0; iBitDepth < count; iBitDepth++)
            {
                if (bitDepths[iBitDepth] == actualBitDepth)
                    selectedIndexBitDepth = iBitDepth;
                comboBitDepth.Items.Add(bitDepths[iBitDepth]);
            }
            comboBitDepth.SelectedIndex = selectedIndexBitDepth;
            comboBitDepth.EndUpdate();

            textBoxFrameRate.Text = acqParams.dFrameRate.ToString("F0");
            textBoxExposure.Text = ExposureToMicroS(acqParams.Exposure).ToString();
            textBoxERDExposure.Text = ExposureToMicroS(acqParams.EDRExposure).ToString();
            textBoxPostTriggFrames.Text = acqParams.PTFrames.ToString();
            textBoxImgCount.Text = acqParams.ImCount.ToString();
            uint delay = (acqParams.PTFrames > acqParams.ImCount) ? acqParams.PTFrames - acqParams.ImCount : 0;
            textBoxDelay.Text = delay.ToString();
        }

        /// <summary>
        /// Refreshes acquisition parameters for Stored (recorded) cines.
        /// </summary>
        /// <param name="cine"></param>
        private void RefreshAcquisitionParamtersStoredCine(Cine cine)
        {
            RefreshAcquisitionUI_RW(true);

            comboResolution.BeginUpdate();
            comboResolution.Items.Clear();
            ResolutionItem resItem = new ResolutionItem((uint)cine.ImWidth, (uint)cine.ImHeight);
            comboResolution.Items.Add(resItem.ToString());
            comboResolution.SelectedIndex = 0;
            comboResolution.EndUpdate();

            comboBitDepth.Items.Clear();
            comboBitDepth.Items.Add(cine.BppReal);
            comboBitDepth.SelectedIndex = 0;

            textBoxFrameRate.Text = cine.FrameRate.ToString();
            textBoxExposure.Text = cine.Exposure.ToString();
            textBoxERDExposure.Text = ExposureToMicroS(cine.EDRExposureNs).ToString("F0");
            textBoxPostTriggFrames.Text = cine.PostTriggerFrames.ToString();
            textBoxImgCount.Text = cine.ImageCount.ToString();
            textBoxDelay.Text = cine.TriggerDelay.ToString();
        }

        /// <summary>
        /// Refresh ability to change properties depending on cine stored status.
        /// </summary>
        private void RefreshAcquisitionUI_RW(bool isStored)
        {
            comboResolution.Enabled = !isStored;
            comboBitDepth.Enabled = !isStored;
            textBoxFrameRate.ReadOnly = isStored;
            textBoxExposure.ReadOnly = isStored;
            textBoxERDExposure.ReadOnly = isStored;
            textBoxPostTriggFrames.ReadOnly = isStored;

            buttonSetAcqParam.Enabled = !isStored;
        }

        /// <summary>
        /// Refreshes image processing options.
        /// </summary>
        private void RefreshImProcessing()
        {
            Cine currentCine = null;
            if (SelectedSource != null)
            {
                currentCine = SelectedSource.CurrentCine;
            }

            if (currentCine == null)
                return;

            textBoxBrightness.Text = currentCine.Brightness.ToString(IMPROC_FORMAT);
            textBoxGain.Text = currentCine.Contrast.ToString(IMPROC_FORMAT);
            textBoxGamma.Text = currentCine.Gamma.ToString(IMPROC_FORMAT);
            textBoxSaturation.Text = currentCine.Saturation.ToString(IMPROC_FORMAT);
            textBoxHue.Text = currentCine.Hue.ToString(IMPROC_FORMAT);
            WBGain whitebalance = currentCine.WhiteBalanceGain;
            textBoxWBRed.Text = whitebalance.R.ToString(IMPROC_FORMAT);
            textBoxWBBlue.Text = whitebalance.B.ToString(IMPROC_FORMAT);
        }

        private void RefreshPlayInterface()
        {
            if (SelectedSource != null)
            {
                CinePlayer.CurrentCine = SelectedSource.CurrentCine;
            }
        }

        void RefreshColorDependentControls(bool isColorImage)
        {
            textBoxSaturation.Enabled = isColorImage;
            textBoxHue.Enabled = isColorImage;
            textBoxWBRed.Enabled = isColorImage;
            textBoxWBBlue.Enabled = isColorImage;
        }

        /// <summary>
        /// Refresh availability of record actions.
        /// </summary>
        private void RefreshRecordActions(CameraStatus camStatus)
        {
            if (camStatus == CameraStatus.Preview)
            {
                buttonCapture.Enabled = true;
                buttonTrigger.Enabled = false;
            }
            else if (camStatus == CameraStatus.RecWaitingForTrigger)
            {
                buttonCapture.Enabled = false;
                buttonTrigger.Enabled = true;
            }
            else if (camStatus == CameraStatus.RecPostriggerFrames || camStatus == CameraStatus.NotAvailable)
            {
                buttonCapture.Enabled = false;
                buttonTrigger.Enabled = false;
            }
        }
        #endregion

        #region SetParameters
        /// <summary>
        /// Set the acquisition parameters into camera for selected cine partitions.
        /// </summary>
        private void SetAcquisitionParams()
        {
            bool resolutionChanged = false;

            Camera selectedCam = SelectedSource as Camera;
            if (SelectedSource is Camera && !selectedCam.IsCinePartitionStored(selectedCam.SelectedCinePartNo))
            {
                CameraOptions camOptions = selectedCam.GetCameraOptions();
                camOptions.RAMBitDepth = uint.Parse(comboBitDepth.Text);
                selectedCam.SetCameraOptions(camOptions);

                AcquiParams acqParams = selectedCam.GetAcquisitionParameters(selectedCam.SelectedCinePartNo);
                //set resolution
                string resolutionItemStr = comboResolution.Text;
                ResolutionItem resItem = ResolutionItem.Parse(resolutionItemStr);
                if (resItem != null)
                {
                    //
                    // See if the Resolution has changed
                    // if so clear the Display
                    //
                    if ((acqParams.ImWidth != resItem.ImWidth) || (acqParams.ImHeight != resItem.ImHeight))
                    {
                        resolutionChanged = true;
                    }
                    acqParams.ImWidth = resItem.ImWidth;
                    acqParams.ImHeight = resItem.ImHeight;
                }
                uint parsedVal = 0;
                if (uint.TryParse(textBoxFrameRate.Text, out parsedVal))
                {
                    acqParams.dFrameRate = (double)parsedVal;
                }
                if (uint.TryParse(textBoxExposure.Text, out parsedVal))
                {
                    acqParams.Exposure = ExposureToNS(parsedVal);
                }
                if (uint.TryParse(textBoxERDExposure.Text, out parsedVal))
                {
                    acqParams.EDRExposure = ExposureToNS(parsedVal);//to ns
                }
                if (uint.TryParse(textBoxPostTriggFrames.Text, out parsedVal))
                {
                    acqParams.PTFrames = parsedVal;
                }
                selectedCam.SetAcquisitionParameters(selectedCam.SelectedCinePartNo, acqParams);

                if (resolutionChanged == true)
                {
                    //
                    // Assume the Image Size has changed
                    //
                    CinePlayer.updateImageSize = true;
                }
            }
        }

        /// <summary>
        /// Set image processing for selected cine.
        /// </summary>
        private void SetImProcessing()
        {
            Cine currentCine = null;
            if (SelectedSource != null)
                currentCine = SelectedSource.CurrentCine;

            if (currentCine == null)
                return;

            float parsedVal = 0;
            if (float.TryParse(textBoxBrightness.Text, out parsedVal))
            {
                currentCine.Brightness = parsedVal;
            }
            if (float.TryParse(textBoxGain.Text, out parsedVal))
            {
                currentCine.Contrast = parsedVal;
            }
            if (float.TryParse(textBoxGamma.Text, out parsedVal))
            {
                currentCine.Gamma = parsedVal;
            }

            if (CinePlayer.IsColorImage)
            {
                if (float.TryParse(textBoxSaturation.Text, out parsedVal))
                {
                    currentCine.Saturation = parsedVal;
                }
                if (float.TryParse(textBoxHue.Text, out parsedVal))
                {
                    currentCine.Hue = parsedVal;
                }
                if (float.TryParse(textBoxWBRed.Text, out parsedVal))
                {
                    WBGain whitebalance = currentCine.WhiteBalanceGain;
                    whitebalance.R = parsedVal;
                    currentCine.WhiteBalanceGain = whitebalance;
                }
                if (float.TryParse(textBoxWBBlue.Text, out parsedVal))
                {
                    WBGain whitebalance = currentCine.WhiteBalanceGain;
                    whitebalance.B = parsedVal;
                    currentCine.WhiteBalanceGain = whitebalance;
                }
            }
        }

        /// <summary>
        /// Set the number of partitions from partitionCombo
        /// </summary>
        private void SetPartitionFromCombo()
        {
            if (SelectedSource is Camera)
            {
                Camera selectedCam = SelectedSource as Camera;
                if (!selectedCam.GetHasStoredRAMPart() || ShowDeleteAllCinesMessage())
                {
                    selectedCam.SetPartitionCount(uint.Parse(comboBoxPartitions.SelectedItem.ToString()));
                    RefreshCineCombo();
                    SelectCineFromCombo();
                }
                else
                {
                    RefreshPartitionCombo();
                }

                //
                // Assume the Image Size has changed
                //
                CinePlayer.updateImageSize = true;
            }
        }

        #endregion

        #region Utils
        /// <param name="expVal">exposure value in Ns</param>
        /// <returns>value in micros</returns>
        private uint ExposureToMicroS(uint expNsVal)
        {
            return (uint)(expNsVal / 1000.0);
        }

        /// <param name="expVal">exposure value in micro-seconds</param>
        /// <returns>value in nanos</returns>
        private uint ExposureToNS(uint expmsVal)
        {
            return (uint)(expmsVal * 1000);
        }

        private bool ShowDeleteAllCinesMessage()
        {
            return MessageBox.Show("All stored cines will be deleted. Continue?", "Delete stored cines?", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes;
        }

        /// <summary>
        /// Print the status from the camera.
        /// </summary>
        private string PrintCameraStatus(CameraStatus status, int activeCine)
        {
            string camSatusStr = "";
            switch (status)
            {
                case CameraStatus.Preview:
                    camSatusStr = Cine.PREVIEW_NAME;
                    break;
                case CameraStatus.RecPostriggerFrames:
                    camSatusStr = string.Format("Recording in cine partition {0} postrigger frames", activeCine);
                    break;
                case CameraStatus.RecWaitingForTrigger:
                    camSatusStr = string.Format("Recording in cine partition {0}, waiting for trigger", activeCine);
                    break;
                default:
                    camSatusStr = "";
                    break;
            }
            return camSatusStr;
        }
        #endregion

        #region Actions
        /// <summary>
        /// Send record command to camera.
        /// </summary>
        private void Record()
        {
            if (SelectedSource is Camera)
            {
                Camera selectedCam = SelectedSource as Camera;
                int cineToCapture = selectedCam.SelectedCinePartNo;
                //delete all cine partitions and send record command 
                if (cineToCapture == (int)CineNumber.CINE_PREVIEW)
                {
                    if (!selectedCam.GetHasStoredRAMPart() || ShowDeleteAllCinesMessage())
                        selectedCam.Record();
                }
                else
                {
                    if (selectedCam.IsCinePartitionStored(cineToCapture)
                        && MessageBox.Show("Stored cine will be deleted in order to be recorded. Continue?", "Delete stored cine",
                        MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.No)
                        return;

                    selectedCam.RecordSpecificCine(cineToCapture);
                }
            }
        }

        /// <summary>
        /// Send trigger command to camera.
        /// </summary>
        private void SendTrigger()
        {
            if (SelectedSource is Camera)
            {
                Camera selectedCam = SelectedSource as Camera;
                selectedCam.SendTrigger();
            }
        }

        private void OpenFileCine()
        {
            string cineFilePath;

            //You may use the following commented code if you wish to start browsing at a predifened location.
            //string cineFilePath = PhFileWrappers.GetOpenCineName(OFN.SINGLESELECT, Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments));

            if (PhFileWrappers.GetOpenCineName(OFN.SINGLESELECT, "", out cineFilePath))
            {
                if (File.Exists(cineFilePath))
                {
                    if (OpenedFile != null)
                    {
                        OpenedFile.Dispose();
                        OpenedFile = null;
                    }

                    OpenedFile = new FileSource(cineFilePath);

                    zRefreshing = true;
                    SelectedSource = OpenedFile;
                    RefreshSourceCombo();

                    SelectSourceFromCombo();
                    RefreshCineCombo();
                    SelectCineFromCombo();
                    zRefreshing = false;

                    //
                    // Assume the Image Size has changed
                    //
                    CinePlayer.updateImageSize = true;
                }
            }
        }

        /// <summary>
        /// Start the saving of cine.
        /// </summary>
        private void StartSaveCine()
        {
            if (zCineSaver == null || !zCineSaver.Started)
            {
                Cine selectedCine = null;

                if (SelectedSource != null)
                {
                    selectedCine = SelectedSource.CurrentCine;
                }

                if (selectedCine != null && !selectedCine.IsLive)
                {
                    // felix: just to test resampling; to comment out for release
//                    resample_cine(selectedCine);

                    zCineSaver = new CineSaver(selectedCine, labelProgressStatus, progressBarActionProgress);
                    if (zCineSaver.ShowGetCineNameDialog())
                    {
                        zCineSaver.SaveFinished += new EventHandler(zCineSaver_SaveFinished);
                        buttonSave.Enabled = false;
                        buttonOpen.Enabled = false;
                        zCineSaver.StartSaveCine();
                    }
                    else
                        zCineSaver = null;
                }
                else
                {
                    MessageBox.Show("Not a suitable cine to be saved.", "", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }
            }
        }
        #endregion

        private bool resample_cine(Cine cine)
        {
            cine.Resample = true;
            cine.ResampleWidth = 300;
            cine.ResampleHeight = 200;
//            uint imgSizeInBytes = AttachedCine.MaxImageSizeInBytes;
            CinePlayer.RefreshImageBuffer();
            return true;
        }

        #region Timer
        private void zRefreshTimer_Tick(object sender, EventArgs e)
        {
            DateTime timeNow = DateTime.Now;
            TimeSpan difference = timeNow - zPreviousTime;
            bool noImage = false;

            zPreviousTime = timeNow;
            labeRefreshSpeed.Text = string.Format("{0} Hz", (1.0 / difference.TotalSeconds).ToString("F2"));

            //
            // get the current state of the camera
            //
            if (SelectedSource is Camera)
            {
                Camera selectedCam = SelectedSource as Camera;

                //
                // Is the camera Offline?
                // Need to execute a command that talks to the camera
                // don't care about the result of the command, only want
                // to see if it responds 
                //
                selectedCam.ParamsChanged();

                if (selectedCam.offlineState() == true)
                {
                    //
                    // the camera is offline, is this a live image or stored Image
                    //
                    if (CinePlayer.IsLive() == false)
                    {
                        noImage = true;
                    }
                }
            }
            
            //
            // did any camera change offline/Online State?
            //
            if (PoolRefresher.cameraStateChange() == true)
            {
                String text;

                if (SelectedSource is Camera)
                {
                    text = SelectedSource.ToString();

                    //
                    // need to save the current selected source
                    // the order of the will never change, just grow
                    //
                    int selectIndex = comboBoxSource.SelectedIndex;

                    zRefreshing = true;
                    comboBoxSource.Items.RemoveAt(selectIndex);
                    comboBoxSource.Items.Insert(selectIndex, text);

                    comboBoxSource.SelectedIndex = selectIndex;
                    zRefreshing = false;
                }
            }

            //
            // update Camera Pool Timer
            //
            cameraPoolRefreshTimer++;
            if ((cameraPoolRefreshTimer > REFRESH_CAMERA_POOL_INTERVAL) )
            {
                cameraPoolRefreshTimer = 0;

                //
                // has the Camera Pool Changed
                //
                if (PoolRefresher.RefreshCameras() == true) 
                {
                    zRefreshTimer.Stop();
                    RefreshSourceAndCine();
                    zRefreshTimer.Start();
                }
            }

            try
            {
                if (noImage == false)
                {
                    CinePlayer.PlayNextImage();

                    RefreshColorDependentControls(CinePlayer.IsColorImage);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }

            if (SelectedSource is Camera)
            {
                Camera selectedCam = SelectedSource as Camera;

                //update camera status
                CameraStatus camStatus = selectedCam.CamStatus;
                if (camStatus == CameraStatus.NotAvailable)
                {
                    labelCameraStatus.Text = "";
                }
                else
                {
                    if (selectedCam.offlineState() == true)
                    {
                        labelCameraStatus.Text = "Camera status: Offline";
                    }
                    else
                    {
                        labelCameraStatus.Text = "Camera status: " + PrintCameraStatus(camStatus, selectedCam.GetActiveCineNo());
                    }
                }

                RefreshRecordActions(camStatus);

                if (selectedCam.offlineState() == false)
                {
                    //if selected cine status had been changed, update interface
                    Cine currentCine = selectedCam.CurrentCine;
                    if (currentCine != null)
                    {
                        //
                        // make sure the camera is online
                        //
                        if (selectedCam.offlineState() == false)
                        {
                            Cinestatus selectedCineCurrentStatus = selectedCam.GetCinePartitionStatus(selectedCam.SelectedCinePartNo);
                            if (selectedCineCurrentStatus.Stored != zSelectedCineLastStatus.Stored)
                            {
                                if (selectedCam.offlineState() == false)
                                {
                                    SelectCineFromCombo();
                                    zSelectedCineLastStatus = selectedCineCurrentStatus;
                                }
                            }

                            if (selectedCam.offlineState() == false)
                            {
                                if (selectedCam.ParametersExternallyChanged)
                                {
                                    RefreshPartitionCombo();
                                    RefreshAcqParameters();
                                    RefreshImProcessing();
                                }
                            }
                        }
                    }
                }
            }
            else
            {
                labelCameraStatus.Text = "";
                RefreshRecordActions(CameraStatus.NotAvailable);
            }
        }
        #endregion

        #region EventHandlers
        private void comboBoxSource_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (zRefreshing)
            {
                return;
            }

            SelectSourceFromCombo();
            RefreshCineCombo();
        }

        private void comboBoxCine_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (zRefreshing)
                return;

            SelectCineFromCombo();
        }

        private void buttonSourceInfo_Click(object sender, EventArgs e)
        {
            if (SelectedSource is Camera)
            {
                using (CameraInfoForm camInfoDlg = new CameraInfoForm())
                {
                    camInfoDlg.AttachedCamera = SelectedSource as Camera;
                    camInfoDlg.ShowDialog();
                }
            }
        }

        private void buttonSetAcqParam_Click(object sender, EventArgs e)
        {
            SetAcquisitionParams();

            //feedback accepted values
            RefreshAcqParameters();
        }

        private void buttonSetImProcessing_Click(object sender, EventArgs e)
        {
            SetImProcessing();

            //feedback accepted values
            RefreshImProcessing();
            CinePlayer.RefreshImageBuffer();
        }

        private void buttonCapture_Click(object sender, EventArgs e)
        {
            Record();
        }

        private void buttonTrigger_Click(object sender, EventArgs e)
        {
            SendTrigger();
        }

        private void buttonOpen_Click(object sender, EventArgs e)
        {
            OpenFileCine();
        }

        private void buttonSave_Click(object sender, EventArgs e)
        {
            StartSaveCine();
        }

        private void zCineSaver_SaveFinished(object sender, EventArgs e)
        {
            //release writer
            zCineSaver.SaveFinished -= new EventHandler(zCineSaver_SaveFinished);
            zCineSaver.Dispose();
            zCineSaver = null;
            //allow saving
            buttonSave.Enabled = true;
            buttonOpen.Enabled = true;
        }

        private void comboBoxPartitions_SelectionChangeCommitted(object sender, EventArgs e)
        {
            if (zPartComboRefreshing)
                return;

            SetPartitionFromCombo();
        }
        #endregion
    }
}
