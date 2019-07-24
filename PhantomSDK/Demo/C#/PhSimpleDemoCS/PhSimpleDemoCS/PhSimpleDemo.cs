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
//                                                                              //
//////////////////////////////////////////////////////////////////////////////////
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.Runtime.InteropServices;
using System.Collections;
using System.Drawing.Imaging;


using PhSharp;


namespace SdkSimpleDemo
{
    public partial class PhSimpleDemo : Form
    {
        private const int UPDATE_RATE = 10;     // update dialog every 10 refresh ticks;

        //
        // handle max cameras
        //
        private List<CameraId> camId = new List<CameraId>();
        private uint cameraCount = 0;
        private int currentCamera = -1;
        private bool offline = false;
        private bool playbackActive = false;
        private bool[] warningMessageShown = new bool[PhCon.MAXCAMERACNT];     // max number of possible cameras

        private int dialogUpdateTick = UPDATE_RATE;
        private uint maxImageSizeInBytes = 0;
        private uint imageSizeInBytes = 0;
        private int currentImage;                               // used for Stored cine playback

        IntPtr liveCineHandle = IntPtr.Zero;
        IntPtr storedCineHandle = IntPtr.Zero;
        IntPtr saveCineHandle = IntPtr.Zero;
        ImRange imageRange;
        ImRange storedImageRange;                               // used for stored cine
        AcquiParams acquiParams = new AcquiParams();

        private PROGRESSCB saveCineCallbackDelegate;            // Callback for Save Cine
        private delegate void UpdateDelegate(uint percent);


        public IntPtr pImageBuffer = new IntPtr();
        IH imageHeader = new IH();
        public Bitmap imageBitmap;

        public PhSimpleDemo()
        {
            InitializeComponent();

        }

        private void SimpleDemo_Load(object sender, EventArgs e)
        {
            HRESULT result;

            try
            {
                ErrorHandler.zMainForm = this;

                //
                // Enable message boxes from dlls
                //
                ErrorHandler.CheckError(PhCon.PhEnableMessages(true));

                //
                // Initialize registration object
                //
                result = PhCon.PhRegisterClientEx(this.Handle, null, null, PhCon.PHCONHEADERVERSION);
                ErrorHandler.CheckError(result);

                result = PhCon.PhConfigPoolUpdate(1500); //look for new cameras as fast as possible
                ErrorHandler.CheckError(result);

                //
                // Do initial check for cameras
                //
                updateCameraPool();

                //
                // Start timer to check for cameras every 3 seconds
                //
                cameraPoolTimer.Start();

                //
                // Start timer to update the display
                //
                refreshTimer.Start();
            }
            catch (DllNotFoundException dllEx)
            {
                MessageBox.Show(this, string.Format("An important dll required to run this demo was not found. {0} Exception message: {1}.Application will exit",
                    Environment.NewLine, dllEx.Message), "Dll not found", MessageBoxButtons.OK);
                Application.Exit();
            }
        }
        
        
        private void SimpleDemo_FormClosing(object sender, FormClosingEventArgs e)
        {
            HRESULT result = PhCon.PhUnregisterClient(this.Handle);

            Marshal.FreeHGlobal(pImageBuffer);
            maxImageSizeInBytes = 0;
            pImageBuffer = IntPtr.Zero;
        }


        public void updateCineStatus()
        {
            //
            // get the current Cine Status
            //
            if (currentCamera != -1)
            {
                Cinestatus[] cs = new Cinestatus[PhCon.PhMaxCineCnt((uint)currentCamera)];
                PhCon.PhGetCineStatus((uint)currentCamera, cs);

                //////////////////////////////////////////////////
                // What is the camera doing                     //
                //////////////////////////////////////////////////

                if (playbackActive == true)
                {
                    playbackLabel.Visible = true;

                    liveLabel.Visible = false;
                    recordingLabel.Visible = false;
                    triggeredLabel.Visible = false;

                    firstImageTextBox.Visible = true;
                    CurrentImageTextBox.Visible = true;
                    lastImageTextBox.Visible = true;

                    recordButton.Enabled = false;
                    TriggerButton.Enabled = false;

                    pauseCheckBox.Enabled = true;
                    stopButton.Enabled = true;
                }
                else
                {
                    //
                    // Not playback
                    //
                    playbackLabel.Visible = false;
                    firstImageTextBox.Visible = false;
                    CurrentImageTextBox.Visible = false;
                    lastImageTextBox.Visible = false;

                    recordButton.Enabled = true;
                    TriggerButton.Enabled = true;

                    pauseCheckBox.Enabled = false;
                    stopButton.Enabled = false;

                    //
                    // if Cine 0 (the preview Cine) is Active
                    // then we are doing Preview
                    //
                    if (cs[0].Active == true)
                    {
                        //
                        // Preview Mode
                        //
                        liveLabel.Visible = true;
                        recordingLabel.Visible = false;
                        triggeredLabel.Visible = false;

                        recordButton.Text = "Record";

                        //
                        // if we have a Stored Cine 
                        // we can enable the playback button
                        //
                        if (cs[1].Stored == true)
                        {
                            playbackButton.Enabled = true;
                            saveButton.Enabled = true;
                            saveProgressBar.Enabled = true;
                        }
                        else
                        {
                            playbackButton.Enabled = false;

                            saveButton.Enabled = false;
                            saveProgressBar.Enabled = false;
                            saveProgressBar.Value = 0;

                            saveCineToFileLabel.Enabled = false;
                            saveCineToFileLabel.Text = "";
                        }
                    }
                    else if (cs[1].Active == true)
                    {
                        liveLabel.Visible = true;

                        recordButton.Text = "Stop Record";

                        //
                        // are we recording?
                        //
                        if (cs[1].Stored == false)
                        {
                            recordingLabel.Visible = true;

                            playbackButton.Enabled = false;

                            saveButton.Enabled = false;
                            saveProgressBar.Enabled = false;
                            saveProgressBar.Value = 0;

                            saveCineToFileLabel.Enabled = false;
                            saveCineToFileLabel.Text = "";
                        }
                        else
                        {
                            recordingLabel.Visible = false;
                        }

                        //
                        // have we been triggered
                        //
                        if (cs[1].Triggered == true)
                        {
                            triggeredLabel.Visible = true;
                        }
                        else
                        {
                            triggeredLabel.Visible = false;
                        }
                    }
                    else
                    {
                        //
                        // some other Cine is active
                        // this simple demo only supports Cine 1
                        // so just turn all status false
                        //
                        liveLabel.Visible = false;
                        recordingLabel.Visible = false;
                        triggeredLabel.Visible = false;

                        playbackButton.Enabled = false;
                        saveButton.Enabled = false;

                        saveProgressBar.Enabled = false;
                        saveProgressBar.Value = 0;

                        saveCineToFileLabel.Enabled = false;
                        saveCineToFileLabel.Text = "";
                    }
                }
            }
            else
            {
                //
                // no cameras 
                //
                liveLabel.Visible = false;
                recordingLabel.Visible = false;
                triggeredLabel.Visible = false;
                playbackLabel.Visible = false;

                playbackButton.Enabled = false;
                saveButton.Enabled = false;

                saveProgressBar.Enabled = false;
                saveProgressBar.Value = 0;

                saveCineToFileLabel.Enabled = false;
                saveCineToFileLabel.Text = "";

            }
        }

        private void updateCameraControls()
        {
            //
            // see if Current camera have changed 
            // from online  --> offline
            // or   offline --> online
            //
            if (currentCamera != -1)
            {
                offline = PhCon.PhOffline((uint)currentCamera);
                offlineLabel.Visible = offline;
            }
            
            //
            // get the current setup for this camera
            //
            PhCon.PhGetCineParams((uint)currentCamera, 0, ref acquiParams, IntPtr.Zero);

            //
            // get the current Item to show on the ComboBox
            //
            resComboBox.Text = acquiParams.ImWidth.ToString() + " x " + acquiParams.ImHeight.ToString();

            //
            // Update the current exposure (Display in uSec)
            //
            expTextBox.Text = (acquiParams.Exposure / 1000).ToString();

            //
            // Update the current Frame Rate
            //
            frameRateTextBox.Text = acquiParams.dFrameRate.ToString();

            //
            // Update the Cine Status
            //
            updateCineStatus();
        }

        private void cameraComboBox_SelectedIndexChanged(object sender, EventArgs e)
        {
            Point[] resolutions = new Point[PhCon.MAX_RESOLUTIONS];
            uint resCount = PhCon.MAX_RESOLUTIONS; 

            currentCamera = cameraComboBox.SelectedIndex;

            //
            // Get Camera Info
            //
            CameraId id = camId.ElementAt(currentCamera);
            ipAddrTextBox.Text = ip2text(id.ip);
            SerialNumTextBox.Text = id.serial.ToString();
            CameraNameTextBox.Text = id.Name.ToString();
            modelTextBox.Text = id.Model.ToString();

            PhFile.PhGetCineLive((int)currentCamera, ref liveCineHandle);
            PhFile.PhGetCineInfo(liveCineHandle, CineInfo.GCI_MAXIMGSIZE, out imageSizeInBytes);

            //
            // get a list of standard supported resolution for this Camera
            //
            PhCon.PhGetResolutions((uint)currentCamera, resolutions, ref resCount, IntPtr.Zero, IntPtr.Zero);

            //
            // Update resolution combo
            //
            string selectedResolution = "";
            resComboBox.Items.Clear();
            for (int ires = 0; ires < resCount; ires++)
            {
                Point res = resolutions[ires];
                selectedResolution = res.X.ToString() + " x " + res.Y.ToString();
                resComboBox.Items.Add(selectedResolution);
            }

            //
            // Update the Camera Controls
            //
            updateCameraControls();
        }

        /// <summary>
        /// This coresponds to uint representation found in Phantom
        /// </summary>
        /// <param name="ip"></param>
        /// <returns></returns>
        public static uint ipFromString(string ip)
        {

            string[] temp = ip.Split(new char[] { '.' }, StringSplitOptions.None);
            uint[] octets = new uint[4];

            //
            // simple test to handle invalid ip addresses
            //
            int length = temp.Length;

            for (int i = 0; i < length; i++)
            {
                string ipNumber = temp[i];
                if (!string.IsNullOrEmpty(ipNumber))
                {
                    octets[i] = uint.Parse(ipNumber);
                }
                else
                {
                    octets[i] = 0;
                }
            }
            return octets[3] + (octets[2] << 8) + (octets[1] << 16) + (octets[0] << 24);
        }

        //
        // See if we have any cameras, and 
        // if any cameras have been added to the Pool
        //
        private void updateCameraPool()
        {
            uint CurCamCount;
            uint partCnt = 0;
            string strValue;

            //
            // see if we have found any new cameras
            //
            PhCon.PhGetCameraCount(out CurCamCount);

            //
            // we have no cameras, so add a simulated camera
            //
            if (CurCamCount == 0)
            {
                //
                // add a simulated VEO 710S
                //
                PhCon.PhAddSimulatedCamera(7001, 1234);
                CurCamCount = 1;
            }

            if (CurCamCount > cameraCount)
            {
                // 
                // We have some new cameras, so Add them to the list
                // need to get the CameraID information
                //

                //
                // get camera Info
                // the order of the list will not change as new cameras are added
                // just add to the end of the list
                //
                for (int i = (int)cameraCount; i < CurCamCount; i++)
                {
                    IntPtr ptrString = Marshal.AllocHGlobal(PhCon.MAXIPSTRSZ);
                    StringBuilder cameraStringBuilder = new StringBuilder(PhCon.MAXSTDSTRSZ);
                    CameraId id = new CameraId();

                    //
                    // Ip Address
                    //
                    PhCon.PhGet((uint)i, GS.IPAddress, ptrString);
                    strValue = Marshal.PtrToStringAnsi(ptrString);
                    id.ip = ipFromString(strValue);

                    //
                    // Serial Number and Name
                    //
                    PhCon.PhGetCameraID((uint)i, out id.serial, cameraStringBuilder);
                    id.Name = cameraStringBuilder.ToString();


                    //
                    // Max Cine Count (max number of Partition)
                    //
                    id.MaxCineCnt = (uint)PhCon.PhMaxCineCnt((uint)i);

                    //
                    // Sensor CFA
                    //
                    PhCon.PhGetVersion((uint)i, Versions.GV_CFA, out id.CFA);

                    //
                    // Camera Hardware Version Number
                    //
                    PhCon.PhGetVersion((uint)i, Versions.GV_CAMERA, out id.CamVer);

                    //
                    // Model String
                    //
                    PhCon.PhGet((uint)i, GS.Model, ptrString);
                    strValue = Marshal.PtrToStringAnsi(ptrString);
                    Marshal.FreeHGlobal(ptrString);
                    id.Model = strValue.ToString();

                    if (id.Name == "")
                    {
                        id.Name = id.serial.ToString();
                    }

                    camId.Add(id);
                    cameraComboBox.Items.Add(i.ToString());

                    //
                    // check the new camera we just found to see if
                    // it has more than 1 partition.
                    // show warning message if > 1 partition
                    // this is a simple demo and only supports a single partition
                    //
                    if (warningMessageShown[i] == false)
                    {
                        PhCon.PhGetPartitions((uint)i, ref partCnt, null);
                        if (partCnt > 1)
                        {
                            MessageBox.Show(this,
                                "This camera has more than 1 partition\nThis is a simple demo and only supports a single partition",
                                "More than 1 partition found", MessageBoxButtons.OK);
                        }
                        warningMessageShown[i] = true;
                    }

                    //
                    // if this is the first camera found
                    // setup the combo box
                    //
                    if (currentCamera == -1)
                    {
                        currentCamera = 0;
                        cameraComboBox.SelectedIndex = 0;
                    }
                }
                cameraCount = CurCamCount;
            }

            //
            // see if Current camera have changed 
            // from online  --> offline
            // or   offline --> online
            //
            if (currentCamera != -1)
            {
                offline = PhCon.PhOffline((uint)currentCamera);
                offlineLabel.Visible = offline;
            } 
        }

        private void cameraPoolTimer_Tick(object sender, EventArgs e)
        {
            updateCameraPool();
        }

        //
        // make sure we have room to whole the image data
        // it could have changed if they change the resolution
        //
        public void setImageBufferSize(IntPtr cineHandle)
        {
            PhFile.PhGetCineInfo(cineHandle, CineInfo.GCI_MAXIMGSIZE, out imageSizeInBytes);

            if (pImageBuffer == IntPtr.Zero)
            {
                pImageBuffer = Marshal.AllocHGlobal((int)imageSizeInBytes);
                maxImageSizeInBytes = imageSizeInBytes;
            }
            else if (imageSizeInBytes > maxImageSizeInBytes)
            {
                //
                // need more space
                //
                pImageBuffer = Marshal.ReAllocHGlobal(pImageBuffer, (IntPtr)imageSizeInBytes);
                maxImageSizeInBytes = imageSizeInBytes;
            }
        }


        private void refreshTimer_Tick(object sender, EventArgs e)
        {
            HRESULT result;
            bool currentState;

            if (currentCamera != -1)
            {
                //
                // see if Current camera have changed 
                // from online  --> offline
                // or   offline --> online
                //
                if (currentCamera != -1)
                {
                    currentState = PhCon.PhOffline((uint)currentCamera);

                    //
                    // update menu if the state has changed
                    //
                    if (currentState != offline)
                    {
                        offline = currentState;
                        offlineLabel.Visible = offline;
                    }
                }   

                if (playbackActive == false)
                {
                    //
                    // Show Live Images
                    //
                    imageRange.First = 0;
                    imageRange.Cnt = 1;

                    PhFile.PhSetUseCase(liveCineHandle, UseCase.UC_VIEW);

                    setImageBufferSize(liveCineHandle);

                    result = PhFile.PhGetCineImage(liveCineHandle, ref imageRange, pImageBuffer, imageSizeInBytes, ref imageHeader);
                }
                else
                {
                    //
                    // Show Stored Images
                    //
                    imageRange.First = currentImage;
                    imageRange.Cnt = 1;

                    CurrentImageTextBox.Text = "Frame: " + currentImage.ToString();

                    PhFile.PhSetUseCase(storedCineHandle, UseCase.UC_VIEW);

                    setImageBufferSize(storedCineHandle);

                    result = PhFile.PhGetCineImage(storedCineHandle, ref imageRange, pImageBuffer, imageSizeInBytes, ref imageHeader);
                    if ((pauseCheckBox.Checked == false) && (offline == false))
                    {
                        currentImage++;
                        if (currentImage > (storedImageRange.First + storedImageRange.Cnt))
                        {
                            currentImage = storedImageRange.First;
                            pauseCheckBox.Checked = true;
                        }
                    }
                    
                }

                PixelFormat pixelFormat = PixelFormat.Format48bppRgb;

                if (imageHeader.biBitCount == 48)
                {
                    pixelFormat = PixelFormat.Format48bppRgb;
                }
                else if (imageHeader.biBitCount == 24)
                {
                    pixelFormat = PixelFormat.Format24bppRgb;
                }
                else if (imageHeader.biBitCount == 16)
                {
                    pixelFormat = PixelFormat.Format8bppIndexed;

                    //
                    // need to reduce image bitdepth to 8bpp in order to be displayed
                    //
                    imageHeader.biSize = 40;
                    REDUCE16TO8PARAMS reduceOption = new REDUCE16TO8PARAMS();
                    reduceOption.fGain16_8 = (float)1.0;
                    IntPtr procOptionsPtr = Marshal.AllocHGlobal(Marshal.SizeOf(reduceOption));
                    Marshal.StructureToPtr(reduceOption, procOptionsPtr, false);
                    PhInt.PhProcessImage(pImageBuffer, pImageBuffer, ref imageHeader, IMG_PROC.REDUCE16TO8, procOptionsPtr);
                    Marshal.FreeHGlobal(procOptionsPtr);          
                }
                else
                {
                    pixelFormat = PixelFormat.Format8bppIndexed;
                }

                int stride = imageHeader.biWidth * (imageHeader.biBitCount / 8);
                imageBitmap = new Bitmap(imageHeader.biWidth, imageHeader.biHeight, stride, pixelFormat, pImageBuffer);

                //
                // if Monochrome Image; need to build Palette
                //
                if (pixelFormat == PixelFormat.Format8bppIndexed)
                {
                    ColorPalette pal = imageBitmap.Palette;
                    for (int k = 0; k < 256; k++)
                    {
                        pal.Entries[k] = Color.FromArgb(255, k, k, k);
                    }
                    imageBitmap.Palette = pal;
                }

                imagePictureBox.Invalidate();
            }

            //
            // don't need to update the dialog so offend 
            //
            dialogUpdateTick--;
            if (dialogUpdateTick <= 0)
            {
                //
                // update the Dialog
                //
                updateCineStatus();
                dialogUpdateTick = UPDATE_RATE;
            }
        }


        private void imagePictureBox_Paint(object sender, PaintEventArgs e)
        {
            try
            {
                if (imageBitmap != null)
                {
                    double Zoom = Math.Min((double)imagePictureBox.ClientRectangle.Width / (double)imageBitmap.Width,
                                           (double)imagePictureBox.ClientRectangle.Height / (double)imageBitmap.Height);

                    RectangleF srcRect = new RectangleF();  // rectangle area which will be drawn
                    Rectangle destRect = new Rectangle();   // rectangle where the srcRect will be draw

                    //
                    //Fit image into picturebox
                    //
                    srcRect.X = 0;
                    srcRect.Width = (float)imageBitmap.Width;
                    double x = ((double)imagePictureBox.ClientRectangle.Width - (double)imageBitmap.Width * Zoom) / 2;
                    destRect.X = (int)Math.Truncate(x);
                    double width = (double)imageBitmap.Width * Zoom;
                    destRect.Width = (int)Math.Truncate(width);

                    srcRect.Y = 0;
                    srcRect.Height = (float)imageBitmap.Height;
                    double y = ((double)imagePictureBox.ClientRectangle.Height - (double)imageBitmap.Height * Zoom) / 2;
                    destRect.Y = (int)Math.Truncate(y);
                    double height = (double)imageBitmap.Height * Zoom;
                    destRect.Height = (int)Math.Truncate(height);

                    e.Graphics.InterpolationMode = InterpolationMode.NearestNeighbor;
                    e.Graphics.PixelOffsetMode = PixelOffsetMode.Half;
                    e.Graphics.SmoothingMode = SmoothingMode.None;
                    e.Graphics.CompositingQuality = CompositingQuality.HighSpeed;
                    e.Graphics.CompositingMode = CompositingMode.SourceOver;

                    e.Graphics.Clip = new Region(destRect);
                    e.Graphics.DrawImage(
                        imageBitmap,
                        destRect,
                        srcRect,
                        GraphicsUnit.Pixel
                        );
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }


        public static string ip2text(uint ip)
        {
            return string.Format("{0}.{1}.{2}.{3}",
                ip >> 24 & 0xff,
                ip >> 16 & 0xff,
                ip >> 8 & 0xff,
                ip & 0xff);
        }


        private void recordButton_Click(object sender, EventArgs e)
        {
            DialogResult result = DialogResult.Yes;
            Cinestatus[] cs = new Cinestatus[PhCon.PhMaxCineCnt((uint)currentCamera)];
            PhCon.PhGetCineStatus((uint)currentCamera, cs);

            if (cs[0].Active == true)
            {
                //
                // start record
                //
                if (cs[1].Stored == true)
                {
                    //
                    // Starting New Record
                    // need to delete old record
                    //

                    result = MessageBox.Show("Delete Old Record?", "Record", MessageBoxButtons.YesNo);

                    if (result == DialogResult.Yes)
                    {
                        PhCon.PhDeleteCine((uint)currentCamera, 1);
                    }
                }

                if (result == DialogResult.Yes)
                {
                    PhCon.PhRecordCine((uint)currentCamera);
                }
            }
            else
            {
                if (cs[1].Stored == false)
                {
                    //
                    // Stop record and go into preview
                    //
                    PhCon.PhRecordSpecificCine((uint)currentCamera, 0);
                }
            }

            //
            // update the Dialog
            //
            updateCineStatus();
        }

        private void TriggerButton_Click(object sender, EventArgs e)
        {
            Cinestatus[] cs = new Cinestatus[PhCon.PhMaxCineCnt((uint)currentCamera)];
            PhCon.PhGetCineStatus((uint)currentCamera, cs);

            //
            // only send trigger command when
            // we are in the record mode
            // (ie. not preview or playback)
            //
            if (cs[1].Active == true)
            {
                PhCon.PhSendSoftwareTrigger((uint)currentCamera);
            }
        }

        private void playbackButton_Click(object sender, EventArgs e)
        {
            //
            // Show the live cine or the Stored Recorded Cine
            //
            if (playbackActive == true)
            {
                //
                // show live Cine
                //
                playbackActive = false;

                //
                // reset the current Frame number in case
                // we re-enter Playback mode
                //
                currentImage = storedImageRange.First;
            }
            else
            {
                //
                // show Recorded Cine
                //
                // Need to get a cine handle
                // will do it here
                // if we have one already it could be old
                // so get a new one to be sure
                // we only handle the first cine file 
                // (ie. 0 = preview cine, 1= first stored cine)
                //
                if (storedCineHandle != IntPtr.Zero)
                {
                    PhFile.PhDestroyCine(storedCineHandle);
                    storedCineHandle = IntPtr.Zero;
                }
                PhFile.PhNewCineFromCamera((int)currentCamera, 1, ref storedCineHandle);

                //
                // get number of images
                //
                PhFile.PhGetCineInfo(storedCineHandle, CineInfo.GCI_FIRSTIMAGENO, out storedImageRange.First);
                PhFile.PhGetCineInfo(storedCineHandle, CineInfo.GCI_TOTALIMAGECOUNT, out storedImageRange.Cnt);

                currentImage = storedImageRange.First;
                firstImageTextBox.Text   = "First Frame: " + storedImageRange.First.ToString();
                CurrentImageTextBox.Text = "Frame: " + currentImage.ToString();
                lastImageTextBox.Text    = "Last Frame: " + (storedImageRange.First + storedImageRange.Cnt - 1).ToString();

                playbackActive = true;
            }
            //
            // update the Dialog
            //
            updateCineStatus();
        }

        private bool SaveCineProgressChanged(uint percent, IntPtr cineHandle)
        {
            if (saveProgressBar.InvokeRequired)
            {
                saveProgressBar.BeginInvoke(new UpdateDelegate(UpdateCineSaveInfo), new object[] { percent });
            }
            else
            {
                UpdateCineSaveInfo(percent);
            }

            //
            // return true in delegate to continue saving
            //
            return (true);
        }

        private void UpdateCineSaveInfo(uint percent)
        {
            if ((percent >= saveProgressBar.Minimum) && (percent <= saveProgressBar.Maximum))
            {
                saveProgressBar.Value = (int)percent;
                saveCineToFileLabel.Text = "Saving Cine to file: " + percent.ToString() + "%";
            }

            //
            // callback function will always be called for 100
            //
            if (percent >= 100)
            {
                saveProgressBar.Enabled = false;
                saveCineToFileLabel.Enabled = false;
                if (playbackActive == true)
                {
                    pauseCheckBox.Enabled = true;
                    stopButton.Enabled = true;
                }
            }
        }


        private void saveButton_Click(object sender, EventArgs e)
        {
            bool result;

            // Need to get a cine handle
            // if we don't have one
            // if we have one already it could be old
            // so get a new one to be sure
            // we only handle the first cine file 
            // (ie. 0 = preview cine, 1= first stored cine)
            //
            if (saveCineHandle != IntPtr.Zero)
            {
                PhFile.PhDestroyCine(saveCineHandle);
                saveCineHandle = IntPtr.Zero;
            }
            PhFile.PhNewCineFromCamera((int)currentCamera, 1, ref saveCineHandle);

            //
            // get number of images
            //
            PhFile.PhGetCineInfo(saveCineHandle, CineInfo.GCI_FIRSTIMAGENO, out storedImageRange.First);
            PhFile.PhGetCineInfo(saveCineHandle, CineInfo.GCI_TOTALIMAGECOUNT, out storedImageRange.Cnt);

            result = PhFile.PhGetSaveCineName(saveCineHandle);

            if (result == true)
            {
                //
                // Stop Playback during the Save
                //
                if (playbackActive == true)
                {
                    pauseCheckBox.Checked = true;
                    pauseCheckBox.Enabled = true;
                    stopButton.Enabled = true;
                }

                saveProgressBar.Enabled = true;
                saveProgressBar.Value = 0;

                saveCineToFileLabel.Enabled = true;
                saveCineToFileLabel.Text = "Saving Cine to file: 0%";

                //
                // set the usecase for save
                //
                PhFile.PhSetUseCase(saveCineHandle, UseCase.UC_SAVE);

                //////////////////////////////////////////////////////////////////
                // NOTE: We exemplify the PhWriteCineFileAsync because it has   //
                //       a much complex use scenario than PhWriteCineFile       //
                //                                                              //
                //       You may use the single thread function PhWriteCineFile //
                //       but you will need a thread if you want a responsive UI //
                //////////////////////////////////////////////////////////////////

                //
                // set the callback function
                //
                saveCineCallbackDelegate = new PROGRESSCB(SaveCineProgressChanged);

                PhFile.PhWriteCineFileAsync(saveCineHandle, saveCineCallbackDelegate);
            }
        }

        private int resComboBox_Ctrl()
        {
            int update = -1;
            string text;
            int pos;
            uint width;
            uint height;

            //
            // get the new selected Item
            //
            Object selectedItem = resComboBox.SelectedItem;

            text = selectedItem.ToString();

            //
            // should always find the "x" 
            //
            pos = text.IndexOf("x");
            if (pos != -1)
            {
                update = 0;
                uint.TryParse(text.Substring(0, pos - 1), out width);
                uint.TryParse(text.Substring(pos + 1), out height);

                if ((width != 0) && (height != 0))
                {
                    if ((width != acquiParams.ImWidth) &&
                        (height != acquiParams.ImHeight))
                    {
                        acquiParams.ImWidth = width;
                        acquiParams.ImHeight = height;
                        update = 1;
                    }
                }
                else
                {
                    //
                    // Error
                    //
                    update = -1;
                }
            }
            return (update);
        }

        private int expEditBox_Ctrl()
        {
            int update = 0;
            uint exposure;

            uint.TryParse(expTextBox.Text, out exposure);

            //
            // Exposure value is in nSec
            // only update if the values are different from the current
            //
            if (exposure != 0)
            {
                if (acquiParams.Exposure != (exposure * 1000))
                {
                    acquiParams.Exposure = exposure * 1000;
                    update = 1;
                }
            }
            else
            {
                //
                // Error
                //
                update = -1;
            }

            return (update);
        }

        private int frameRateEditBox_Ctrl()
        {
            int update = 0;
            uint frameRate;
            double exactFrameRate;

            uint.TryParse(frameRateTextBox.Text, out frameRate);

            if (frameRate != 0)
            {
                //
                // verify and get the frame rate the camera can actual do
                // only update if the values are different from the current
                //
                PhCon.PhGetExactFrameRate((uint)currentCamera, acquiParams.SyncImaging, frameRate, out exactFrameRate);

                if (acquiParams.dFrameRate != exactFrameRate)
                {
                    acquiParams.dFrameRate = exactFrameRate;
                    update = 1;
                }
            }
            else
            {
                //
                // Error
                //
                update = -1;
            }

            return (update);
        }

        private void setButton_Click(object sender, EventArgs e)
        {
            StringBuilder text = new StringBuilder("");
            String strtext;
            int resUpdate = 0;
            int exposureUpdate = 0;
            int frameRateUpdate = 0;

            //
            // get the current setup for this camera
            //
            PhCon.PhGetCineParams((uint)currentCamera, 0, ref acquiParams, IntPtr.Zero);

            //
            // make the needed changes (if any)
            //
            resUpdate = resComboBox_Ctrl();
            frameRateUpdate = frameRateEditBox_Ctrl();
            exposureUpdate = expEditBox_Ctrl();

            if (resUpdate == -1)
            {
                text.Append("Invalid Image Resolution\n");
            }
            if (exposureUpdate == -1)
            {
                text.Append("Invalid Exposure\n");
            }
            if (frameRateUpdate == -1)
            {
                text.Append("Invalid Framerate");
            }

            if ((resUpdate == -1) || (exposureUpdate == -1) || (frameRateUpdate == -1))
            {
                strtext = text.ToString();
                MessageBox.Show(strtext, "Input Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            else
            {
                //
                // update the camera if any of the setting have changed
                //
                if ((resUpdate > 0) || (exposureUpdate > 0) || (frameRateUpdate > 0))
                {
                    PhCon.PhSetCineParams((uint)currentCamera, 0, ref acquiParams);

                    //
                    // Changing Resolution will effect what FrameRate is Valid
                    // Changing FrameRate will effect what Exposure is Valid
                    // So now that we have set the camera lets make sure of
                    // what it is actually set to, in case we gave it invalid values
                    //
                    updateCameraControls();
                }
            }
        }

        private void pauseCheckBox_CheckedChanged(object sender, EventArgs e)
        {
            if (pauseCheckBox.Checked == false)
            {
                pauseCheckBox.Text = "Pause";
            }
            else
            {
                pauseCheckBox.Text = "Play";
            }
        }

        private void stopButton_Click(object sender, EventArgs e)
        {
            currentImage = storedImageRange.First;
            pauseCheckBox.Checked = true;
        }

        private void keyboardKeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                setButton_Click(sender, e);
                e.SuppressKeyPress = true;
            }
        }
    }
}
