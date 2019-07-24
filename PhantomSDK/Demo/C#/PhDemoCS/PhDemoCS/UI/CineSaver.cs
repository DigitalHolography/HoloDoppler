using System;
using System.Collections.Generic;
using System.Text;
using System.Windows.Forms;
using PhDemoCS.Data;
using System.Threading;
using System.ComponentModel;
using System.Runtime.InteropServices;
using PhDemoCS.Util;
using PhSharp;


namespace PhDemoCS.UI
{
    /// <summary>
    /// Manages cine saving actions. It does UI refresh for cine save progress.
    /// </summary>
    public class CineSaver : IDisposable
    {
        private delegate void UpdateDelegate(uint percent);

        public event EventHandler SaveFinished;
        private void OnSaveFinished()
        {
            if (SaveFinished != null)
                SaveFinished(this, new EventArgs());
        }

        public CineSaver(Cine cine, Label progressLabel, ProgressBar progressBar)
        {
            //A cine used for save should be used just in that context. The cine is duplicated.
            AttachedCine = (Cine)cine.Clone();

            ProgressLabel = progressLabel;
            ProgressBarUI = progressBar;
        }

        ~CineSaver()
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
                    if (AttachedCine != null)
                        AttachedCine.Dispose();
                }

                zDisposed = true;
            }
        }
        #endregion

        #region Properties
        private Cine zAttachedCine;
        private Cine AttachedCine
        {
            get { return this.zAttachedCine; }
            set { this.zAttachedCine = value; }
        }

        private Label zProgressLabel;
        private Label ProgressLabel
        {
            get { return this.zProgressLabel; }
            set { this.zProgressLabel = value; }
        }

        private ProgressBar zProgressBar;
        private ProgressBar ProgressBarUI
        {
            get { return this.zProgressBar; }
            set { this.zProgressBar = value; }
        }

        private bool zStarted;
        public bool Started
        {
            get { return this.zStarted; }
            private set
            {
                this.zStarted = value;
            }
        }

        private PROGRESSCB zSaveDelegate;
        #endregion

        #region Actions
        /// <summary>
        /// Show dialog to select save cine path. 
        /// Updates internal cine handle buffer for file path and other various options.
        /// </summary>
        public bool ShowGetCineNameDialog()
        {
            if (AttachedCine.IsLive)
                return false;
            else
                //return true on OK button press.
                return AttachedCine.GetSaveCineName();
        }

        public bool StartSaveCine()
        {
            if (Started)
                return false;

            //Live cine cannot be saved.
            if (AttachedCine.IsLive)
            {
                MessageBox.Show("Live cine cannot be saved.");
                return false;
            }

            Started = true;
            UpdateSaveUI(Started);

            //set the usecase for save
            AttachedCine.SetUseCase(UseCase.UC_SAVE);

            //NOTE: We exemplify the PhWriteCineFileAsync because it has a much complex use scenario than PhWriteCineFile
            //You may use the single thread function PhWriteCineFile but you will need a thread if you want a responsive UI
            zSaveDelegate = new PROGRESSCB(SaveProgressChanged);
            AttachedCine.StartSaveCineAsync(zSaveDelegate);

            return true;
        }

        public void StopSave()
        {
            AttachedCine.StopSaveCineAsync();
        }
        #endregion

        #region Save&Update
        private bool SaveProgressChanged(uint percent, IntPtr cineHandle)
        {
            if (ProgressBarUI.InvokeRequired)
                ProgressBarUI.BeginInvoke(new UpdateDelegate(UpdateSaveInfo), new object[] { percent });
            else
                UpdateSaveInfo(percent);

            //return true in delegate to continue saving
            return true;
        }

        private void UpdateSaveInfo(uint percent)
        {
            //callback function will always be called for 100
            if (percent == 100)
            {
                SaveFinishedActions();
                return;
            }

            ProgressLabel.Text = "Saving cine to file " + percent.ToString() + "%";
            if (percent < ProgressBarUI.Minimum || percent > ProgressBarUI.Maximum)
                return;
            ProgressBarUI.Value = (int)percent;
        }

        private void SaveFinishedActions()
        {
            Started = false;

            //save finished, update interface.
            UpdateSaveUI(Started);

            OnSaveFinished();
        }

        private void UpdateSaveUI(bool started)
        {
            ProgressBarUI.Visible = started;
            ProgressLabel.Visible = started;
        }
        #endregion
    }
}
