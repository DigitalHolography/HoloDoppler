using System;
using System.Collections.Generic;
using System.Text;
using PhSharp;


namespace PhDemoCS.Data
{
    /// <summary>
    /// A source which contains a cine file.
    /// </summary>
    public class FileSource : ISource, IDisposable
    {
        public FileSource(string filePath)
        {
            CineFilePath = filePath;
            zAttachedCine = new Cine(CineFilePath);
        }

        ~FileSource()
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
                    //Dispose managed resources.
                    zAttachedCine.Dispose();
                }

                zDisposed = true;
            }
        }
        #endregion

        private Cine zAttachedCine;

        private string zCineFilePath;
        public string CineFilePath
        {
            get { return this.zCineFilePath; }
            private set { this.zCineFilePath = value; }
        }

        #region ISource Members

        public Cine CurrentCine
        {
            get { return zAttachedCine; }
        }

        #endregion
    }
}
