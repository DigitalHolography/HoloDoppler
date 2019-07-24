using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;
using PhDemoCS.Data;

namespace PhDemoCS.Forms
{
    public partial class CameraInfoForm : Form
    {
        public CameraInfoForm()
        {
            InitializeComponent();
        }

        Camera zAttachedCamera;
        public Camera AttachedCamera
        {
            get { return this.zAttachedCamera; }
            set { this.zAttachedCamera = value; }
        }

        private void CameraInfo_Load(object sender, EventArgs e)
        {
            RefreshInfo();
        }

        private void RefreshInfo()
        {
            textBoxName.Text = AttachedCamera.GetCameraName();
            textBoxIP.Text = AttachedCamera.GetIPAddress();
            textBoxSerial.Text = AttachedCamera.Serial.ToString();
            textBoxVersion.Text = AttachedCamera.GetVersion().ToString();
            textBoxModel.Text = AttachedCamera.GetCameraModel();
            textBoxFirmware.Text = AttachedCamera.GetFirmwareVersion().ToString();
        }

        private void textBoxName_Leave(object sender, EventArgs e)
        {
            AttachedCamera.SetCameraName(textBoxName.Text);
        }

        private void textBoxName_KeyUp(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
                AttachedCamera.SetCameraName(textBoxName.Text);
        }
    }
}
