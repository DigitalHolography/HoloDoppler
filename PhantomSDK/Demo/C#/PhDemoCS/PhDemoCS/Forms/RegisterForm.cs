using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;

namespace PhDemoCS.Forms
{
    public partial class RegisterForm : Form
    {
        public RegisterForm()
        {
            InitializeComponent();
        }

        /// <summary>
        /// Updates registration progress.
        /// </summary>
        /// <returns>returns true to continue</returns>
        public bool UpdateProgress(uint cameraNo, uint percent)
        {
            try
            {
                int progressValue = (int)percent;
                progressBarRegister.Value = (progressValue >= 0 && progressValue <= 100) ? progressValue : 0;
            }
            catch
            {
                return false;
            }

            return true;
        }
    }
}
