namespace PhDemoCS.Forms
{
    partial class RegisterForm
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
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(RegisterForm));
            this.progressBarRegister = new System.Windows.Forms.ProgressBar();
            this.labelRegistration = new System.Windows.Forms.Label();
            this.SuspendLayout();
            // 
            // progressBarRegister
            // 
            this.progressBarRegister.Location = new System.Drawing.Point(12, 41);
            this.progressBarRegister.Name = "progressBarRegister";
            this.progressBarRegister.Size = new System.Drawing.Size(290, 23);
            this.progressBarRegister.TabIndex = 0;
            // 
            // labelRegistration
            // 
            this.labelRegistration.AutoSize = true;
            this.labelRegistration.Location = new System.Drawing.Point(13, 25);
            this.labelRegistration.Name = "labelRegistration";
            this.labelRegistration.Size = new System.Drawing.Size(134, 13);
            this.labelRegistration.TabIndex = 2;
            this.labelRegistration.Text = "Reading stg from camera...";
            // 
            // RegisterForm
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(314, 76);
            this.ControlBox = false;
            this.Controls.Add(this.labelRegistration);
            this.Controls.Add(this.progressBarRegister);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedToolWindow;
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.Name = "RegisterForm";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Starting PhDemo...";
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.ProgressBar progressBarRegister;
        private System.Windows.Forms.Label labelRegistration;
    }
}