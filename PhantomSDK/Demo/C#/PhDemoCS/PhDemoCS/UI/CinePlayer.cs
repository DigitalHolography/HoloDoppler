using System;
using System.Collections.Generic;
using System.Text;
using PhDemoCS.Data;
using System.Windows.Forms;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Drawing.Imaging;
using System.Drawing.Drawing2D;
using PhSharp;


namespace PhDemoCS.UI
{
    public enum PlayerState
    {
        Playing,
        Stopped
    }

    /// <summary>
    /// Manage image acquisition and image displaying.
    /// </summary>
    public class CinePlayer : IDisposable
    {
        public CinePlayer(PictureBox pictureBox, Button buttonPlay, TrackBar playSlider, TextBox textBox, Label firstIm, Label lastIm)
        {
            PicBox = pictureBox;
            PlayButton = buttonPlay;
            PlaySlider = playSlider;
            FrameTextBox = textBox;
            LabelFirstIm = firstIm;
            LabelLastIm = lastIm;

            PicBox.Paint += new PaintEventHandler(PicBox_Paint);
            PlayButton.Click += new EventHandler(PlayButton_Click);
            FrameTextBox.Leave += new EventHandler(TextBox_Leave);
            FrameTextBox.KeyUp += new KeyEventHandler(TextBox_KeyUp);
            PlaySlider.ValueChanged += new EventHandler(PlaySlider_ValueChanged);

            ImageBuffer = new ImageBuffer();
            updateImageSize = true;
        }

        ~CinePlayer()
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
                    ImageBuffer.FreeBuffer();

                    PicBox.Paint -= new PaintEventHandler(PicBox_Paint);
                    PlayButton.Click -= new EventHandler(PlayButton_Click);
                    FrameTextBox.Leave -= new EventHandler(TextBox_Leave);
                    FrameTextBox.KeyUp -= new KeyEventHandler(TextBox_KeyUp);
                    PlaySlider.ValueChanged -= new EventHandler(PlaySlider_ValueChanged);
                }

                zDisposed = true;
            }
        }
        #endregion

        #region UserInterfaceParts
        TextBox zTextBox;
        private TextBox FrameTextBox
        {
            get { return this.zTextBox; }
            set { this.zTextBox = value; }
        }

        TrackBar zPlaySlider;
        private TrackBar PlaySlider
        {
            get { return this.zPlaySlider; }
            set { this.zPlaySlider = value; }
        }

        private Label zFirstIm;
        private Label LabelFirstIm
        {
            get { return this.zFirstIm; }
            set { this.zFirstIm = value; }
        }

        private Label zLastIm;
        private Label LabelLastIm
        {
            get { return this.zLastIm; }
            set { this.zLastIm = value; }
        }

        private Button zPlayButton;
        private Button PlayButton
        {
            get { return this.zPlayButton; }
            set { this.zPlayButton = value; }
        }

        private PictureBox zPictureBox;
        private PictureBox PicBox
        {
            get { return this.zPictureBox; }
            set { this.zPictureBox = value; }
        }
        #endregion

        #region Properties

        public bool updateImageSize;

        private Cine zCurrentCine;
        public Cine CurrentCine
        {
            get { return this.zCurrentCine; }
            set
            {
                this.zCurrentCine = value;

                if (CurrentCine != null)
                {
                    if (CurrentCine.IsLive)
                    {
                        InitRange(0, 0);//live cine has no range, always show image 0
                        StartPlay();//always show live images
                    }
                    else
                    {
                        InitRange(CurrentCine.FirstImageNumber, CurrentCine.LastImageNumber);
                    }

                    //GetCineImage will return a vertical fliped image.
                    CurrentCine.SetVFlipView(true);
                    RefreshImageBuffer();
                }
                else
                    Stop();

                UpdatePlayUIVisibility();
            }
        }

        private int zCurrentFrame;
        public int CurrentFrame
        {
            get
            {
                return zCurrentFrame;
            }
            private set
            {
                zCurrentFrame = value;
                PlaySlider.Value = CurrentFrame;
                FrameTextBox.Text = CurrentFrame.ToString();
            }
        }

        private int zFirst;
        public int First
        {
            get { return this.zFirst; }
            private set
            {
                this.zFirst = value;
                PlaySlider.Minimum = First;
                LabelFirstIm.Text = First.ToString();
            }
        }

        private int zLast;
        public int Last
        {
            get { return this.zLast; }
            private set
            {
                this.zLast = value;
                PlaySlider.Maximum = Last;
                LabelLastIm.Text = Last.ToString();
            }
        }

        private PlayerState zState;
        public PlayerState State
        {
            get { return this.zState; }
            private set
            {
                this.zState = value;
                RefreshPlayButton();
            }
        }

        ImageBuffer zImageBuffer;
        private ImageBuffer ImageBuffer
        {
            get { return this.zImageBuffer; }
            set { this.zImageBuffer = value; }
        }

        bool zIsColorImage;
        public bool IsColorImage
        {
            get { return this.zIsColorImage; }
            private set { this.zIsColorImage = value; }
        }
        #endregion

        #region Methods
        private void RefreshPlayButton()
        {
            if (State == PlayerState.Stopped)
                PlayButton.Image = global::PhDemoCS.Properties.Resources.media_playback_start;
            else
                PlayButton.Image = global::PhDemoCS.Properties.Resources.media_playback_stop;
        }

        private void InitRange(int first, int last)
        {
            Stop();

            First = first;
            Last = last;
            CurrentFrame = first;
        }

        private void UpdatePlayUIVisibility()
        {
            bool frameControlVisible = true;

            //do not show play interface for live images
            if (CurrentCine == null || CurrentCine.IsLive)
                frameControlVisible = false;

            PlayButton.Visible = frameControlVisible;
            PlaySlider.Visible = frameControlVisible;
            LabelFirstIm.Visible = frameControlVisible;
            LabelLastIm.Visible = frameControlVisible;
            FrameTextBox.Visible = frameControlVisible;
        }

        private bool ParseCurrentFrame()
        {
            int crtFrame;
            if (int.TryParse(FrameTextBox.Text, out crtFrame) && (crtFrame >= First) && (crtFrame <= Last))
            {
                CurrentFrame = crtFrame;
                RefreshImageBuffer();
                return true;
            }
            else
            {
                FrameTextBox.Text = CurrentFrame.ToString();
                return false;
            }
        }

        public void StartPlay()
        {
            State = PlayerState.Playing;
        }

        public void Stop()
        {
            State = PlayerState.Stopped;
        }

        public void PlayNextImage()
        {
            if (State == PlayerState.Playing)
            {
                RefreshImageBuffer();
                //advance counter
                NextFrame();
            }
        }

        public bool IsLive()
        {
            bool live = false;

            if (CurrentCine != null)
            {
                live = CurrentCine.IsLive;
            }
            return (live);
        }

        /// <summary>
        /// Advance to the next frame number.
        /// </summary>
        private void NextFrame()
        {
            if (CurrentCine == null || CurrentCine.IsLive)
                return;

            if (CurrentFrame == Last)
                CurrentFrame = First;
            else
                CurrentFrame++;
        }

        /// <summary>
        /// Creates the image range for the current frame number.
        /// </summary>
        private ImRange GetCurrentImRange()
        {
            ImRange range = new ImRange();
            range.First = CurrentFrame;
            range.Cnt = 1u;
            return range;
        }

        public void RefreshImageBuffer()
        {
            if (CurrentCine == null)
                return;

            try
            {
                IH imgHeader = new IH();
                ImRange imgRange = GetCurrentImRange();

                if ((updateImageSize == true) || (ImageBuffer.Buffer == IntPtr.Zero))
                {

                    uint imgSizeInBytes = CurrentCine.MaxImageSizeInBytes;
                    //INIT ImageBuffer
                    ImageBuffer.FreeBuffer();
                    ImageBuffer.AllocBufferMemory((int)imgSizeInBytes);
                    updateImageSize = false;
                }
                try
                {
                    HRESULT result = CurrentCine.GetCineImage(imgRange, ImageBuffer.Buffer, ImageBuffer.BufferLength, ref imgHeader);

                    if (result < 0)
                    {
                        //
                        // want image refresh if camera disconnected (Offline)
                        // to support showing black image with offline message
                        //
                        if (ErrorHandler.IsConnectionError(result) == false)
                        {
                            ErrorHandler.CheckError(result);
                            return;
                        }
                    }
                }
                catch //(Exception ex16b)
                {
                    //
                    // If we go offline while we are doing a GetCineImage
                    // that routine can throw an Exception
                    // this is not bad, since we lost the connection. 
                    // So... let catch it here and just move on
                    // no need to recover anything, we now know we are offline
                    //
                    //MessageBox.Show(ex16b.Message);
                    return;
                }

                if (imgHeader.biWidth <= 0 && imgHeader.biHeight <= 0)
                    return;

                //if needed reduce image bitdepth to 8bpp in order to be displayed
                bool is16bpp = CurrentCine.Is16Bpp;
                try
                {
                    if (is16bpp)
                    {
                        ReduceTo8bpp(CurrentCine.Sensitivity, ref imgHeader);
                    }
                }
                catch (Exception ex16b)
                {
                    MessageBox.Show(ex16b.Message);
                    return;
                }

                IsColorImage = ImageBuffer.IsColorHeader(imgHeader);
                //create and asociate the bitmap with new image header as needed
                ImageBuffer.PerformBitmapUpdatesFromImgHeader(imgHeader);

                PicBox.Invalidate();
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        /// <summary>
        /// Reduces 16bpp image buffer to 8 bpp image buffer.
        /// </summary>
        private void ReduceTo8bpp(float sensitivity, ref IH imgHeader)
        {
            REDUCE16TO8PARAMS reduceOption = new REDUCE16TO8PARAMS();
            reduceOption.fGain16_8 = sensitivity;
            IntPtr procOptionsPtr = Marshal.AllocHGlobal(Marshal.SizeOf(reduceOption));
            Marshal.StructureToPtr(reduceOption, procOptionsPtr, true);
            PhInt.PhProcessImage(ImageBuffer.Buffer, ImageBuffer.Buffer, ref imgHeader, IMG_PROC.REDUCE16TO8, procOptionsPtr);
            Marshal.FreeHGlobal(procOptionsPtr);
        }
        #endregion

        #region EventHandlers
        private void PlayButton_Click(object sender, EventArgs e)
        {
            if (State == PlayerState.Playing)
                Stop();
            else
                StartPlay();
        }

        private void TextBox_KeyUp(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                ParseCurrentFrame();
            }
        }

        private void TextBox_Leave(object sender, EventArgs e)
        {
            ParseCurrentFrame();
        }

        private void PlaySlider_ValueChanged(object sender, EventArgs e)
        {
            CurrentFrame = PlaySlider.Value;
            RefreshImageBuffer();
        }

        /// <summary>
        /// Paint the buffered image on the picturebox area.
        /// </summary>
        private void PicBox_Paint(object sender, PaintEventArgs e)
        {
            try
            {
                if (ImageBuffer.Bitmap != null)
                {
                    double Zoom = Math.Min((double)PicBox.ClientRectangle.Width / (double)ImageBuffer.Bitmap.Width,
                        (double)PicBox.ClientRectangle.Height / (double)ImageBuffer.Bitmap.Height);

                    RectangleF srcRect = new RectangleF();//rectangle area which will be drawn
                    Rectangle destRect = new Rectangle();//rectangle where the srcRect will be draw

                    //Fit image into picturebox
                    srcRect.X = 0;
                    srcRect.Width = (float)ImageBuffer.Bitmap.Width;
                    double x = ((double)PicBox.ClientRectangle.Width - (double)ImageBuffer.Bitmap.Width * Zoom) / 2;
                    destRect.X = (int)Math.Truncate(x);
                    double width = (double)ImageBuffer.Bitmap.Width * Zoom;
                    destRect.Width = (int)Math.Truncate(width);

                    srcRect.Y = 0;
                    srcRect.Height = (float)ImageBuffer.Bitmap.Height;
                    double y = ((double)PicBox.ClientRectangle.Height - (double)ImageBuffer.Bitmap.Height * Zoom) / 2;
                    destRect.Y = (int)Math.Truncate(y);
                    double height = (double)ImageBuffer.Bitmap.Height * Zoom;
                    destRect.Height = (int)Math.Truncate(height);

                    //set low graphics
                    e.Graphics.InterpolationMode = InterpolationMode.NearestNeighbor;
                    e.Graphics.PixelOffsetMode = PixelOffsetMode.Half;//always use half
                    e.Graphics.SmoothingMode = SmoothingMode.None;
                    e.Graphics.CompositingQuality = CompositingQuality.HighSpeed;
                    e.Graphics.CompositingMode = CompositingMode.SourceOver;

                    e.Graphics.Clip = new Region(destRect);
                    e.Graphics.DrawImage(
                       ImageBuffer.Bitmap,
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
        #endregion

    }
}
