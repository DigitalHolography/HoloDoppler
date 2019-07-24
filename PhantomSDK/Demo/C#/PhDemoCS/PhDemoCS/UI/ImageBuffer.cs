using System;
using System.Collections.Generic;
using System.Text;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Drawing.Imaging;
using PhSharp;


namespace PhDemoCS.UI
{
    /// <summary>
    /// Image buffer resource management.
    /// </summary>
    public class ImageBuffer
    {
        private IntPtr zBuffer;
        public IntPtr Buffer
        {
            get
            {
                return zBuffer;
            }
            set
            {
                zBuffer = value;
            }
        }

        private uint zBufferLength;
        public uint BufferLength
        {
            get { return zBufferLength; }
            set { zBufferLength = value; }
        }

        private Bitmap zBitmap;
        public Bitmap Bitmap
        {
            get { return this.zBitmap; }
            private set { this.zBitmap = value; }
        }

        public ImageBuffer()
        { 

        }

        #region Static Util Methods
        public static void CreateBWPalette(Bitmap bmp)
        {
            using (Bitmap dummy = new Bitmap(1, 1, PixelFormat.Format8bppIndexed))
            {
                ColorPalette palette = dummy.Palette;
                for (int k = 0; k < 256; k++)
                    palette.Entries[k] = Color.FromArgb(k, k, k);
                bmp.Palette = palette;
            }
        }

        public static bool IsColorHeader(IH ih)
        {
            if (ih.biBitCount == 8 || ih.biBitCount == 16)
                return false;
            else
                return true;
        }
        #endregion

        #region Methods
        /// <summary>
        /// Creates a new bitmap if the current bitmap does not match current image header or if it does not exist.
        /// </summary>
        /// <param name="imgHeader"></param>
        public void PerformBitmapUpdatesFromImgHeader(IH imgHeader)
        {
            bool isColor = IsColorHeader(imgHeader);
            PixelFormat pixelFormat = isColor ? PixelFormat.Format24bppRgb : PixelFormat.Format8bppIndexed;
            //bitmap dimensions changed and need to be changed?
            if (this.Bitmap == null ||
                this.Bitmap.Width != imgHeader.biWidth ||
                this.Bitmap.Height != imgHeader.biHeight ||
                this.Bitmap.PixelFormat != pixelFormat)
            {
                int stride = imgHeader.biWidth * (imgHeader.biBitCount / 8);//stride is calcualted for a 8bpp image
                this.Bitmap = new Bitmap(imgHeader.biWidth, imgHeader.biHeight, stride, pixelFormat, this.Buffer);
                if (!isColor)
                {
                    CreateBWPalette(this.Bitmap);
                }
            }
        }

        public void AllocBufferMemory(int imgSizeInBytes)
        {
            if (imgSizeInBytes > 0)
            {
                Buffer = Marshal.AllocHGlobal(imgSizeInBytes);
                BufferLength = (uint)imgSizeInBytes;
            }
        }

        /// <summary>
        /// Clean resources associated with image buffer.
        /// </summary>
        public void FreeBuffer()
        {
            //bitmap should be disposed before the image buffer because we used a special cosntructor for BMP
            if (Bitmap != null)
            {
                Bitmap toBeDisposed = Bitmap;
                Bitmap = null;
                toBeDisposed.Dispose();
            }
            //free memory asociated with image buffer
            if (Buffer != IntPtr.Zero)
            {
                Marshal.FreeHGlobal(Buffer);
                Buffer = IntPtr.Zero;
            }
        }
        #endregion
    }
}
