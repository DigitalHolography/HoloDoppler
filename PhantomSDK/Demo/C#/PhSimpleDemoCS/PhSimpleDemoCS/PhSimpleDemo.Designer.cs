namespace SdkSimpleDemo
{
    partial class PhSimpleDemo
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(PhSimpleDemo));
            this.imagePictureBox = new System.Windows.Forms.PictureBox();
            this.cameraComboBox = new System.Windows.Forms.ComboBox();
            this.iPAddrLabel = new System.Windows.Forms.Label();
            this.SerialNumLabel = new System.Windows.Forms.Label();
            this.CameraNameLabel = new System.Windows.Forms.Label();
            this.cameraNumLabel = new System.Windows.Forms.Label();
            this.recordButton = new System.Windows.Forms.Button();
            this.TriggerButton = new System.Windows.Forms.Button();
            this.playbackButton = new System.Windows.Forms.Button();
            this.saveButton = new System.Windows.Forms.Button();
            this.ipAddrTextBox = new System.Windows.Forms.TextBox();
            this.SerialNumTextBox = new System.Windows.Forms.TextBox();
            this.CameraNameTextBox = new System.Windows.Forms.TextBox();
            this.cameraPoolTimer = new System.Windows.Forms.Timer(this.components);
            this.refreshTimer = new System.Windows.Forms.Timer(this.components);
            this.offlineLabel = new System.Windows.Forms.Label();
            this.modelTextBox = new System.Windows.Forms.TextBox();
            this.modelLabel = new System.Windows.Forms.Label();
            this.expTextBox = new System.Windows.Forms.TextBox();
            this.expLabel = new System.Windows.Forms.Label();
            this.frameRateLabel = new System.Windows.Forms.Label();
            this.expUnitLabel = new System.Windows.Forms.Label();
            this.ppsLabel = new System.Windows.Forms.Label();
            this.resolutionLabel = new System.Windows.Forms.Label();
            this.resComboBox = new System.Windows.Forms.ComboBox();
            this.frameRateTextBox = new System.Windows.Forms.TextBox();
            this.liveLabel = new System.Windows.Forms.Label();
            this.playbackLabel = new System.Windows.Forms.Label();
            this.recordingLabel = new System.Windows.Forms.Label();
            this.triggeredLabel = new System.Windows.Forms.Label();
            this.firstImageTextBox = new System.Windows.Forms.TextBox();
            this.lastImageTextBox = new System.Windows.Forms.TextBox();
            this.CurrentImageTextBox = new System.Windows.Forms.TextBox();
            this.pauseCheckBox = new System.Windows.Forms.CheckBox();
            this.saveProgressBar = new System.Windows.Forms.ProgressBar();
            this.saveCineToFileLabel = new System.Windows.Forms.Label();
            this.saveCineGroupBox = new System.Windows.Forms.GroupBox();
            this.stopButton = new System.Windows.Forms.Button();
            this.camInfoGroupBox = new System.Windows.Forms.GroupBox();
            this.camCtrlGroupBox = new System.Windows.Forms.GroupBox();
            this.setButton = new System.Windows.Forms.Button();
            ((System.ComponentModel.ISupportInitialize)(this.imagePictureBox)).BeginInit();
            this.saveCineGroupBox.SuspendLayout();
            this.camInfoGroupBox.SuspendLayout();
            this.camCtrlGroupBox.SuspendLayout();
            this.SuspendLayout();
            // 
            // imagePictureBox
            // 
            this.imagePictureBox.Anchor = ((System.Windows.Forms.AnchorStyles)((((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom) 
            | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.imagePictureBox.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.imagePictureBox.Location = new System.Drawing.Point(218, 34);
            this.imagePictureBox.Name = "imagePictureBox";
            this.imagePictureBox.Size = new System.Drawing.Size(501, 400);
            this.imagePictureBox.TabIndex = 0;
            this.imagePictureBox.TabStop = false;
            this.imagePictureBox.Paint += new System.Windows.Forms.PaintEventHandler(this.imagePictureBox_Paint);
            // 
            // cameraComboBox
            // 
            this.cameraComboBox.FormattingEnabled = true;
            this.cameraComboBox.Location = new System.Drawing.Point(68, 7);
            this.cameraComboBox.Name = "cameraComboBox";
            this.cameraComboBox.Size = new System.Drawing.Size(43, 21);
            this.cameraComboBox.TabIndex = 1;
            this.cameraComboBox.SelectedIndexChanged += new System.EventHandler(this.cameraComboBox_SelectedIndexChanged);
            // 
            // iPAddrLabel
            // 
            this.iPAddrLabel.AutoSize = true;
            this.iPAddrLabel.Location = new System.Drawing.Point(10, 21);
            this.iPAddrLabel.Name = "iPAddrLabel";
            this.iPAddrLabel.Size = new System.Drawing.Size(61, 13);
            this.iPAddrLabel.TabIndex = 2;
            this.iPAddrLabel.Text = "IP Address:";
            // 
            // SerialNumLabel
            // 
            this.SerialNumLabel.AutoSize = true;
            this.SerialNumLabel.Location = new System.Drawing.Point(10, 54);
            this.SerialNumLabel.Name = "SerialNumLabel";
            this.SerialNumLabel.Size = new System.Drawing.Size(76, 13);
            this.SerialNumLabel.TabIndex = 3;
            this.SerialNumLabel.Text = "Serial Number:";
            // 
            // CameraNameLabel
            // 
            this.CameraNameLabel.AutoSize = true;
            this.CameraNameLabel.Location = new System.Drawing.Point(10, 87);
            this.CameraNameLabel.Name = "CameraNameLabel";
            this.CameraNameLabel.Size = new System.Drawing.Size(38, 13);
            this.CameraNameLabel.TabIndex = 4;
            this.CameraNameLabel.Text = "Name:";
            // 
            // cameraNumLabel
            // 
            this.cameraNumLabel.AutoSize = true;
            this.cameraNumLabel.Location = new System.Drawing.Point(15, 10);
            this.cameraNumLabel.Name = "cameraNumLabel";
            this.cameraNumLabel.Size = new System.Drawing.Size(46, 13);
            this.cameraNumLabel.TabIndex = 5;
            this.cameraNumLabel.Text = "Camera:";
            // 
            // recordButton
            // 
            this.recordButton.Location = new System.Drawing.Point(7, 135);
            this.recordButton.Name = "recordButton";
            this.recordButton.Size = new System.Drawing.Size(91, 27);
            this.recordButton.TabIndex = 9;
            this.recordButton.Text = "Record";
            this.recordButton.UseVisualStyleBackColor = true;
            this.recordButton.Click += new System.EventHandler(this.recordButton_Click);
            // 
            // TriggerButton
            // 
            this.TriggerButton.Location = new System.Drawing.Point(103, 135);
            this.TriggerButton.Name = "TriggerButton";
            this.TriggerButton.Size = new System.Drawing.Size(97, 27);
            this.TriggerButton.TabIndex = 10;
            this.TriggerButton.Text = "Software Trigger";
            this.TriggerButton.UseVisualStyleBackColor = true;
            this.TriggerButton.Click += new System.EventHandler(this.TriggerButton_Click);
            // 
            // playbackButton
            // 
            this.playbackButton.Location = new System.Drawing.Point(7, 170);
            this.playbackButton.Name = "playbackButton";
            this.playbackButton.Size = new System.Drawing.Size(91, 27);
            this.playbackButton.TabIndex = 11;
            this.playbackButton.Text = "Playback Mode";
            this.playbackButton.UseVisualStyleBackColor = true;
            this.playbackButton.Click += new System.EventHandler(this.playbackButton_Click);
            // 
            // saveButton
            // 
            this.saveButton.Location = new System.Drawing.Point(7, 16);
            this.saveButton.Name = "saveButton";
            this.saveButton.Size = new System.Drawing.Size(46, 27);
            this.saveButton.TabIndex = 12;
            this.saveButton.Text = "Save";
            this.saveButton.UseVisualStyleBackColor = true;
            this.saveButton.Click += new System.EventHandler(this.saveButton_Click);
            // 
            // ipAddrTextBox
            // 
            this.ipAddrTextBox.Location = new System.Drawing.Point(88, 18);
            this.ipAddrTextBox.Name = "ipAddrTextBox";
            this.ipAddrTextBox.Size = new System.Drawing.Size(107, 20);
            this.ipAddrTextBox.TabIndex = 13;
            // 
            // SerialNumTextBox
            // 
            this.SerialNumTextBox.Location = new System.Drawing.Point(88, 51);
            this.SerialNumTextBox.Name = "SerialNumTextBox";
            this.SerialNumTextBox.Size = new System.Drawing.Size(107, 20);
            this.SerialNumTextBox.TabIndex = 14;
            // 
            // CameraNameTextBox
            // 
            this.CameraNameTextBox.Location = new System.Drawing.Point(54, 84);
            this.CameraNameTextBox.Name = "CameraNameTextBox";
            this.CameraNameTextBox.Size = new System.Drawing.Size(141, 20);
            this.CameraNameTextBox.TabIndex = 15;
            // 
            // cameraPoolTimer
            // 
            this.cameraPoolTimer.Interval = 3000;
            this.cameraPoolTimer.Tick += new System.EventHandler(this.cameraPoolTimer_Tick);
            // 
            // refreshTimer
            // 
            this.refreshTimer.Tick += new System.EventHandler(this.refreshTimer_Tick);
            // 
            // offlineLabel
            // 
            this.offlineLabel.AutoSize = true;
            this.offlineLabel.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(192)))), ((int)(((byte)(0)))), ((int)(((byte)(0)))));
            this.offlineLabel.ForeColor = System.Drawing.Color.White;
            this.offlineLabel.Location = new System.Drawing.Point(123, 10);
            this.offlineLabel.Name = "offlineLabel";
            this.offlineLabel.Size = new System.Drawing.Size(37, 13);
            this.offlineLabel.TabIndex = 16;
            this.offlineLabel.Text = "Offline";
            this.offlineLabel.Visible = false;
            // 
            // modelTextBox
            // 
            this.modelTextBox.Location = new System.Drawing.Point(54, 116);
            this.modelTextBox.Name = "modelTextBox";
            this.modelTextBox.ReadOnly = true;
            this.modelTextBox.Size = new System.Drawing.Size(141, 20);
            this.modelTextBox.TabIndex = 18;
            // 
            // modelLabel
            // 
            this.modelLabel.AutoSize = true;
            this.modelLabel.Location = new System.Drawing.Point(10, 119);
            this.modelLabel.Name = "modelLabel";
            this.modelLabel.Size = new System.Drawing.Size(39, 13);
            this.modelLabel.TabIndex = 17;
            this.modelLabel.Text = "Model:";
            // 
            // expTextBox
            // 
            this.expTextBox.Location = new System.Drawing.Point(85, 49);
            this.expTextBox.Name = "expTextBox";
            this.expTextBox.Size = new System.Drawing.Size(80, 20);
            this.expTextBox.TabIndex = 22;
            this.expTextBox.KeyDown += new System.Windows.Forms.KeyEventHandler(this.keyboardKeyDown);
            // 
            // expLabel
            // 
            this.expLabel.AutoSize = true;
            this.expLabel.Location = new System.Drawing.Point(10, 56);
            this.expLabel.Name = "expLabel";
            this.expLabel.Size = new System.Drawing.Size(54, 13);
            this.expLabel.TabIndex = 21;
            this.expLabel.Text = "Exposure:";
            // 
            // frameRateLabel
            // 
            this.frameRateLabel.AutoSize = true;
            this.frameRateLabel.Location = new System.Drawing.Point(10, 82);
            this.frameRateLabel.Name = "frameRateLabel";
            this.frameRateLabel.Size = new System.Drawing.Size(65, 13);
            this.frameRateLabel.TabIndex = 23;
            this.frameRateLabel.Text = "Frame Rate:";
            // 
            // expUnitLabel
            // 
            this.expUnitLabel.AutoSize = true;
            this.expUnitLabel.Location = new System.Drawing.Point(171, 52);
            this.expUnitLabel.Name = "expUnitLabel";
            this.expUnitLabel.Size = new System.Drawing.Size(21, 13);
            this.expUnitLabel.TabIndex = 25;
            this.expUnitLabel.Text = " µs";
            // 
            // ppsLabel
            // 
            this.ppsLabel.AutoSize = true;
            this.ppsLabel.Location = new System.Drawing.Point(171, 82);
            this.ppsLabel.Name = "ppsLabel";
            this.ppsLabel.Size = new System.Drawing.Size(27, 13);
            this.ppsLabel.TabIndex = 26;
            this.ppsLabel.Text = "FPS";
            // 
            // resolutionLabel
            // 
            this.resolutionLabel.AutoSize = true;
            this.resolutionLabel.Location = new System.Drawing.Point(8, 23);
            this.resolutionLabel.Name = "resolutionLabel";
            this.resolutionLabel.Size = new System.Drawing.Size(60, 13);
            this.resolutionLabel.TabIndex = 27;
            this.resolutionLabel.Text = "Resolution:";
            // 
            // resComboBox
            // 
            this.resComboBox.FormattingEnabled = true;
            this.resComboBox.Location = new System.Drawing.Point(85, 20);
            this.resComboBox.Name = "resComboBox";
            this.resComboBox.Size = new System.Drawing.Size(80, 21);
            this.resComboBox.TabIndex = 28;
            this.resComboBox.KeyDown += new System.Windows.Forms.KeyEventHandler(this.keyboardKeyDown);
            // 
            // frameRateTextBox
            // 
            this.frameRateTextBox.Location = new System.Drawing.Point(85, 79);
            this.frameRateTextBox.Name = "frameRateTextBox";
            this.frameRateTextBox.Size = new System.Drawing.Size(80, 20);
            this.frameRateTextBox.TabIndex = 29;
            this.frameRateTextBox.KeyDown += new System.Windows.Forms.KeyEventHandler(this.keyboardKeyDown);
            // 
            // liveLabel
            // 
            this.liveLabel.AutoSize = true;
            this.liveLabel.BackColor = System.Drawing.Color.Blue;
            this.liveLabel.ForeColor = System.Drawing.Color.White;
            this.liveLabel.Location = new System.Drawing.Point(218, 7);
            this.liveLabel.Name = "liveLabel";
            this.liveLabel.Size = new System.Drawing.Size(59, 13);
            this.liveLabel.TabIndex = 32;
            this.liveLabel.Text = "Live Image";
            // 
            // playbackLabel
            // 
            this.playbackLabel.AutoSize = true;
            this.playbackLabel.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(0)))), ((int)(((byte)(192)))), ((int)(((byte)(0)))));
            this.playbackLabel.ForeColor = System.Drawing.Color.White;
            this.playbackLabel.Location = new System.Drawing.Point(646, 7);
            this.playbackLabel.Name = "playbackLabel";
            this.playbackLabel.Size = new System.Drawing.Size(51, 13);
            this.playbackLabel.TabIndex = 33;
            this.playbackLabel.Text = "Playback";
            // 
            // recordingLabel
            // 
            this.recordingLabel.AutoSize = true;
            this.recordingLabel.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(192)))), ((int)(((byte)(0)))), ((int)(((byte)(0)))));
            this.recordingLabel.ForeColor = System.Drawing.Color.White;
            this.recordingLabel.Location = new System.Drawing.Point(297, 7);
            this.recordingLabel.Name = "recordingLabel";
            this.recordingLabel.Size = new System.Drawing.Size(56, 13);
            this.recordingLabel.TabIndex = 34;
            this.recordingLabel.Text = "Recording";
            // 
            // triggeredLabel
            // 
            this.triggeredLabel.AutoSize = true;
            this.triggeredLabel.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(0)))), ((int)(((byte)(192)))), ((int)(((byte)(0)))));
            this.triggeredLabel.ForeColor = System.Drawing.Color.White;
            this.triggeredLabel.Location = new System.Drawing.Point(378, 7);
            this.triggeredLabel.Name = "triggeredLabel";
            this.triggeredLabel.Size = new System.Drawing.Size(52, 13);
            this.triggeredLabel.TabIndex = 37;
            this.triggeredLabel.Text = "Triggered";
            // 
            // firstImageTextBox
            // 
            this.firstImageTextBox.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.firstImageTextBox.Location = new System.Drawing.Point(219, 440);
            this.firstImageTextBox.Name = "firstImageTextBox";
            this.firstImageTextBox.ReadOnly = true;
            this.firstImageTextBox.Size = new System.Drawing.Size(110, 20);
            this.firstImageTextBox.TabIndex = 38;
            // 
            // lastImageTextBox
            // 
            this.lastImageTextBox.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Right)));
            this.lastImageTextBox.Location = new System.Drawing.Point(615, 440);
            this.lastImageTextBox.Name = "lastImageTextBox";
            this.lastImageTextBox.ReadOnly = true;
            this.lastImageTextBox.Size = new System.Drawing.Size(104, 20);
            this.lastImageTextBox.TabIndex = 39;
            // 
            // CurrentImageTextBox
            // 
            this.CurrentImageTextBox.Anchor = System.Windows.Forms.AnchorStyles.Bottom;
            this.CurrentImageTextBox.Location = new System.Drawing.Point(425, 440);
            this.CurrentImageTextBox.Name = "CurrentImageTextBox";
            this.CurrentImageTextBox.ReadOnly = true;
            this.CurrentImageTextBox.Size = new System.Drawing.Size(102, 20);
            this.CurrentImageTextBox.TabIndex = 40;
            // 
            // pauseCheckBox
            // 
            this.pauseCheckBox.Appearance = System.Windows.Forms.Appearance.Button;
            this.pauseCheckBox.CheckAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.pauseCheckBox.Location = new System.Drawing.Point(101, 170);
            this.pauseCheckBox.Name = "pauseCheckBox";
            this.pauseCheckBox.Size = new System.Drawing.Size(49, 27);
            this.pauseCheckBox.TabIndex = 41;
            this.pauseCheckBox.Text = "Pause";
            this.pauseCheckBox.UseVisualStyleBackColor = true;
            this.pauseCheckBox.CheckedChanged += new System.EventHandler(this.pauseCheckBox_CheckedChanged);
            // 
            // saveProgressBar
            // 
            this.saveProgressBar.Location = new System.Drawing.Point(59, 18);
            this.saveProgressBar.Name = "saveProgressBar";
            this.saveProgressBar.Size = new System.Drawing.Size(125, 20);
            this.saveProgressBar.TabIndex = 42;
            // 
            // saveCineToFileLabel
            // 
            this.saveCineToFileLabel.AutoSize = true;
            this.saveCineToFileLabel.Location = new System.Drawing.Point(57, 46);
            this.saveCineToFileLabel.Name = "saveCineToFileLabel";
            this.saveCineToFileLabel.Size = new System.Drawing.Size(94, 13);
            this.saveCineToFileLabel.TabIndex = 43;
            this.saveCineToFileLabel.Text = "Save Cine To File:";
            // 
            // saveCineGroupBox
            // 
            this.saveCineGroupBox.Controls.Add(this.saveProgressBar);
            this.saveCineGroupBox.Controls.Add(this.saveCineToFileLabel);
            this.saveCineGroupBox.Controls.Add(this.saveButton);
            this.saveCineGroupBox.Location = new System.Drawing.Point(6, 395);
            this.saveCineGroupBox.Name = "saveCineGroupBox";
            this.saveCineGroupBox.Size = new System.Drawing.Size(206, 66);
            this.saveCineGroupBox.TabIndex = 44;
            this.saveCineGroupBox.TabStop = false;
            this.saveCineGroupBox.Text = "Save Cine";
            // 
            // stopButton
            // 
            this.stopButton.Location = new System.Drawing.Point(152, 170);
            this.stopButton.Name = "stopButton";
            this.stopButton.Size = new System.Drawing.Size(48, 27);
            this.stopButton.TabIndex = 45;
            this.stopButton.Text = "Stop";
            this.stopButton.UseVisualStyleBackColor = true;
            this.stopButton.Click += new System.EventHandler(this.stopButton_Click);
            // 
            // camInfoGroupBox
            // 
            this.camInfoGroupBox.Controls.Add(this.modelTextBox);
            this.camInfoGroupBox.Controls.Add(this.modelLabel);
            this.camInfoGroupBox.Controls.Add(this.CameraNameTextBox);
            this.camInfoGroupBox.Controls.Add(this.SerialNumTextBox);
            this.camInfoGroupBox.Controls.Add(this.ipAddrTextBox);
            this.camInfoGroupBox.Controls.Add(this.CameraNameLabel);
            this.camInfoGroupBox.Controls.Add(this.SerialNumLabel);
            this.camInfoGroupBox.Controls.Add(this.iPAddrLabel);
            this.camInfoGroupBox.Location = new System.Drawing.Point(6, 31);
            this.camInfoGroupBox.Name = "camInfoGroupBox";
            this.camInfoGroupBox.Size = new System.Drawing.Size(206, 146);
            this.camInfoGroupBox.TabIndex = 46;
            this.camInfoGroupBox.TabStop = false;
            this.camInfoGroupBox.Text = "Camera Information";
            // 
            // camCtrlGroupBox
            // 
            this.camCtrlGroupBox.Controls.Add(this.setButton);
            this.camCtrlGroupBox.Controls.Add(this.resolutionLabel);
            this.camCtrlGroupBox.Controls.Add(this.resComboBox);
            this.camCtrlGroupBox.Controls.Add(this.expLabel);
            this.camCtrlGroupBox.Controls.Add(this.expTextBox);
            this.camCtrlGroupBox.Controls.Add(this.expUnitLabel);
            this.camCtrlGroupBox.Controls.Add(this.frameRateLabel);
            this.camCtrlGroupBox.Controls.Add(this.frameRateTextBox);
            this.camCtrlGroupBox.Controls.Add(this.ppsLabel);
            this.camCtrlGroupBox.Controls.Add(this.recordButton);
            this.camCtrlGroupBox.Controls.Add(this.TriggerButton);
            this.camCtrlGroupBox.Controls.Add(this.playbackButton);
            this.camCtrlGroupBox.Controls.Add(this.pauseCheckBox);
            this.camCtrlGroupBox.Controls.Add(this.stopButton);
            this.camCtrlGroupBox.Location = new System.Drawing.Point(6, 183);
            this.camCtrlGroupBox.Name = "camCtrlGroupBox";
            this.camCtrlGroupBox.Size = new System.Drawing.Size(206, 206);
            this.camCtrlGroupBox.TabIndex = 47;
            this.camCtrlGroupBox.TabStop = false;
            this.camCtrlGroupBox.Text = "Camera Control";
            // 
            // setButton
            // 
            this.setButton.Location = new System.Drawing.Point(59, 104);
            this.setButton.Name = "setButton";
            this.setButton.Size = new System.Drawing.Size(91, 27);
            this.setButton.TabIndex = 46;
            this.setButton.Text = "Set";
            this.setButton.UseVisualStyleBackColor = true;
            this.setButton.Click += new System.EventHandler(this.setButton_Click);
            // 
            // PhSimpleDemo
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(723, 465);
            this.Controls.Add(this.camCtrlGroupBox);
            this.Controls.Add(this.camInfoGroupBox);
            this.Controls.Add(this.saveCineGroupBox);
            this.Controls.Add(this.CurrentImageTextBox);
            this.Controls.Add(this.lastImageTextBox);
            this.Controls.Add(this.firstImageTextBox);
            this.Controls.Add(this.triggeredLabel);
            this.Controls.Add(this.recordingLabel);
            this.Controls.Add(this.playbackLabel);
            this.Controls.Add(this.liveLabel);
            this.Controls.Add(this.offlineLabel);
            this.Controls.Add(this.cameraNumLabel);
            this.Controls.Add(this.cameraComboBox);
            this.Controls.Add(this.imagePictureBox);
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.MinimumSize = new System.Drawing.Size(739, 481);
            this.Name = "PhSimpleDemo";
            this.Text = "Simple Demo (C#)";
            this.FormClosing += new System.Windows.Forms.FormClosingEventHandler(this.SimpleDemo_FormClosing);
            this.Load += new System.EventHandler(this.SimpleDemo_Load);
            ((System.ComponentModel.ISupportInitialize)(this.imagePictureBox)).EndInit();
            this.saveCineGroupBox.ResumeLayout(false);
            this.saveCineGroupBox.PerformLayout();
            this.camInfoGroupBox.ResumeLayout(false);
            this.camInfoGroupBox.PerformLayout();
            this.camCtrlGroupBox.ResumeLayout(false);
            this.camCtrlGroupBox.PerformLayout();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.PictureBox imagePictureBox;
        private System.Windows.Forms.ComboBox cameraComboBox;
        private System.Windows.Forms.Label iPAddrLabel;
        private System.Windows.Forms.Label SerialNumLabel;
        private System.Windows.Forms.Label CameraNameLabel;
        private System.Windows.Forms.Label cameraNumLabel;
        private System.Windows.Forms.Button recordButton;
        private System.Windows.Forms.Button TriggerButton;
        private System.Windows.Forms.Button playbackButton;
        private System.Windows.Forms.Button saveButton;
        private System.Windows.Forms.TextBox ipAddrTextBox;
        private System.Windows.Forms.TextBox SerialNumTextBox;
        private System.Windows.Forms.TextBox CameraNameTextBox;
        private System.Windows.Forms.Timer cameraPoolTimer;
        private System.Windows.Forms.Timer refreshTimer;
        private System.Windows.Forms.Label offlineLabel;
        private System.Windows.Forms.TextBox modelTextBox;
        private System.Windows.Forms.Label modelLabel;
        private System.Windows.Forms.TextBox expTextBox;
        private System.Windows.Forms.Label expLabel;
        private System.Windows.Forms.Label frameRateLabel;
        private System.Windows.Forms.Label expUnitLabel;
        private System.Windows.Forms.Label ppsLabel;
        private System.Windows.Forms.Label resolutionLabel;
        private System.Windows.Forms.ComboBox resComboBox;
        private System.Windows.Forms.TextBox frameRateTextBox;
        private System.Windows.Forms.Label liveLabel;
        private System.Windows.Forms.Label playbackLabel;
        private System.Windows.Forms.Label recordingLabel;
        private System.Windows.Forms.Label triggeredLabel;
        private System.Windows.Forms.TextBox firstImageTextBox;
        private System.Windows.Forms.TextBox lastImageTextBox;
        private System.Windows.Forms.TextBox CurrentImageTextBox;
        private System.Windows.Forms.CheckBox pauseCheckBox;
        private System.Windows.Forms.ProgressBar saveProgressBar;
        private System.Windows.Forms.Label saveCineToFileLabel;
        private System.Windows.Forms.GroupBox saveCineGroupBox;
        private System.Windows.Forms.Button stopButton;
        private System.Windows.Forms.GroupBox camInfoGroupBox;
        private System.Windows.Forms.GroupBox camCtrlGroupBox;
        private System.Windows.Forms.Button setButton;
    }
}

