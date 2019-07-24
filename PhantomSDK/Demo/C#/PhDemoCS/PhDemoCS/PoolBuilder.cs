using System;
using System.Collections.Generic;
using System.Text;
using System.Windows.Forms;
using PhDemoCS.Forms;
using PhSharp;


namespace PhDemoCS
{
    /// <summary>
    /// Start/Stop registration to Phantom dlls. Updates registration UI progress.
    /// </summary>
    public class PoolBuilder
    {

        private bool zIsRegistered;
        public bool IsRegistered
        {
            get { return this.zIsRegistered; }
            private set { this.zIsRegistered = value; }
        }

        private Form zClientForm;
        public Form ClientForm
        {
            get { return this.zClientForm; }
            private set { this.zClientForm = value; }
        }

        private string zLogAndStgFolder;
        public string LogAndStgFolder
        {
            get { return this.zLogAndStgFolder; }
            private set { zLogAndStgFolder = value; }
        }

        private RegisterForm zRegisterForm;
        private RegisterForm RegisterProgressForm
        {
            get { return this.zRegisterForm; }
            set { this.zRegisterForm = value; }
        }

        public PoolBuilder(Form form, string logAndStgFolder)
        {
            IsRegistered = false;
            ClientForm = form;
            LogAndStgFolder = logAndStgFolder;
        }

        public void Register()
        {
            try
            {
                RegisterProgressForm = new RegisterForm();
                //show registration progress form
                RegisterProgressForm.Show();

                //Register to DLL
                //If LogAndStgFolder == NULL then the Log&STG folder is the default generated in DLL's
                //Default log folder is \Application Data\Phantom\PhVer
                StringBuilder logAndStgFolderSB = null;
                if (!string.IsNullOrEmpty(LogAndStgFolder))
                {
                    logAndStgFolderSB = new StringBuilder(PhFile.MAX_PATH);
                    logAndStgFolderSB.Append(LogAndStgFolder);
                }
                //The use of PhRegisterClientEx as a platform invoke raises a "MDA LoaderLock" warning.
                //The warning text starts with: "Managed Debugging Assistant 'LoaderLock' has detected a problem in ...'.
                //A temporary, but stable solution is to disable the warning.
                //To disable MDA LoaderLock in Visual Studio 2008, go to Debug->Exceptions and uncheck MDA LoaderLock.
                ErrorHandler.CheckError(
                    PhCon.PhRegisterClientEx(
                                            ClientForm.Handle,
                                            logAndStgFolderSB,
                                            new PROGRESSCALLBACK(RegisterCallback),
                                            PhCon.PHCONHEADERVERSION));

                HRESULT result = PhCon.PhConfigPoolUpdate(1500); // look for new cameras as fast as possible

                IsRegistered = true;
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
                IsRegistered = false;
            }
            finally
            {
                RegisterProgressForm.Close();
                RegisterProgressForm = null;
            }
        }

        /// <summary>
        /// Ends the registration to dll. Dlls elibarate resources.
        /// </summary>
        public void Unregister()
        {
            if (IsRegistered)
                PhCon.PhUnregisterClient(ClientForm.Handle);
        }

        /// <summary>
        /// Callback on which User Interface is updated.
        /// </summary>
        private bool RegisterCallback(uint cameraNo, uint percent)
        {
            if (ClientForm.InvokeRequired)
                return (bool)ClientForm.Invoke(new PROGRESSCALLBACK(RegisterProgressForm.UpdateProgress), new object[] { cameraNo, percent });
            else
                return RegisterProgressForm.UpdateProgress(cameraNo, percent);
        }
    }
}
