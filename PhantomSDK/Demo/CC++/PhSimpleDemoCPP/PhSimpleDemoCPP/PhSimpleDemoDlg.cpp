
// PhSimpleDemoDlg.cpp : implementation file
//

#include "stdafx.h"
#include <stdlib.h>
#include <malloc.h> 
#include "PhSimpleDemoCPP.h"
#include "PhSimpleDemoDlg.h"
#include "afxdialogex.h"
#include "ErrorHandler.h"


#ifdef _DEBUG
#define new DEBUG_NEW
#endif


// CPhSimpleDemoDlg dialog

UINT CineSaveProgress;

CPhSimpleDemoDlg::CPhSimpleDemoDlg(CWnd* pParent /*=NULL*/)
	: CDialog(CPhSimpleDemoDlg::IDD, pParent)
{
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);
    m_CameraCount = 0;
    m_CurrentCamera = -1;
    m_Offline = FALSE;
    m_PlaybackActive = FALSE;
    m_ClearImageDisplay = FALSE;
    m_SaveInProgress = FALSE;
    m_DialogUpdateTick = UPDATE_RATE;
    m_MaxImageSizeInBytes = 0;
    m_ImageSizeInBytes = 0;
    CineSaveProgress = 0;
    m_CurrentPercent = 0;

    m_LiveCineHandle = NULL;
    m_StoredCineHandle = NULL;
    m_SaveCineHandle = NULL;
    m_PauseCheck = FALSE;

}

void CPhSimpleDemoDlg::DoDataExchange(CDataExchange* pDX)
{
    CDialog::DoDataExchange(pDX);
    DDX_Control(pDX, IDC_OFFLINE_STATIC, m_OfflineLabel);
    DDX_Control(pDX, IDC_LIVE_IMAGE_STATIC, m_LiveLabel);
    DDX_Control(pDX, IDC_RECORDING_STATIC, m_RecordingLabel);
    DDX_Control(pDX, IDC_TRIGGERED_STATIC, m_TriggeredLabel);
    DDX_Control(pDX, IDC_PLAYBACK_STATIC, m_PlaybackLabel);

    DDX_Control(pDX, IDC_CAMERA_COMBO, m_CameraComboBox);
    DDX_Control(pDX, IDC_RESOLUTION_COMBO, m_ResComboBox);

    DDX_Control(pDX, IDC_RECORD_BUTTON, m_recordButton);
    DDX_Control(pDX, IDC_TRIGGER_BUTTON, m_TriggerButton);
    DDX_Control(pDX, IDC_PLAYBACK_MODE_BUTTON, m_PlaybackButton);
    DDX_Control(pDX, IDC_SET_BUTTON, m_SetButton);
    DDX_Control(pDX, IDC_PAUSE_BUTTON, m_PauseButton);
    DDX_Control(pDX, IDC_STOP_BUTTON, m_StopButton);
    DDX_Control(pDX, IDC_SAVE_BUTTON, m_SaveButton);

    DDX_Control(pDX, IDC_IP_ADDRESS_EDIT, m_IpAddrEditBox);
    DDX_Control(pDX, IDC_SERIAL_NUMBER_EDIT, m_SerialNumEditBox);
    DDX_Control(pDX, IDC_NAME_EDIT, m_CameraNameEditBox);
    DDX_Control(pDX, IDC_MODEL_EDIT, m_ModelEditBox);
    DDX_Control(pDX, IDC_EXPOSURE_EDIT, m_ExpEditBox);
    DDX_Control(pDX, IDC_FRAME_RATE_EDIT, m_FrameRateEditBox);

    DDX_Control(pDX, IDC_SAVE_CINE_TO_FILE_STATIC, m_SaveCineToFileLabel);

    DDX_Control(pDX, IDC_FIRST_IMAGE_EDIT, m_FirstImageEditBox);
    DDX_Control(pDX, IDC_CURRENT_IMAGE_EDIT, m_CurrentImageEditBox);
    DDX_Control(pDX, IDC_LAST_IMAGE_EDIT, m_LastImageEditBox);

    DDX_Control(pDX, IDC_PROGRESS, m_SaveProgressBar);

    DDX_Control(pDX, IDC_PLAYBACK_WINDOW_STATIC, m_ImagePictureBox);
}

BEGIN_MESSAGE_MAP(CPhSimpleDemoDlg, CDialog)
	ON_WM_PAINT()
    ON_WM_TIMER()
	ON_WM_QUERYDRAGICON()
    ON_BN_CLICKED(IDC_RECORD_BUTTON, &CPhSimpleDemoDlg::OnBnClickedRecordButton)
    ON_BN_CLICKED(IDC_TRIGGER_BUTTON, &CPhSimpleDemoDlg::OnBnClickedTriggerButton)
    ON_BN_CLICKED(IDC_PLAYBACK_MODE_BUTTON, &CPhSimpleDemoDlg::OnBnClickedPlaybackModeButton)
    ON_BN_CLICKED(IDC_PAUSE_BUTTON, &CPhSimpleDemoDlg::OnBnClickedPauseButton)
    ON_BN_CLICKED(IDC_STOP_BUTTON, &CPhSimpleDemoDlg::OnBnClickedStopButton)
    ON_BN_CLICKED(IDC_SAVE_BUTTON, &CPhSimpleDemoDlg::OnBnClickedSaveButton)
    ON_CBN_SELCHANGE(IDC_CAMERA_COMBO, &CPhSimpleDemoDlg::OnCbnSelchangeCameraCombo)
    ON_BN_CLICKED(IDC_SET_BUTTON, &CPhSimpleDemoDlg::OnBnClickedSetButton)
    ON_WM_CLOSE()
    ON_WM_DESTROY()
END_MESSAGE_MAP()


// CPhSimpleDemoDlg message handlers

BOOL CPhSimpleDemoDlg::OnInitDialog()
{
    HRESULT Result;
	CDialog::OnInitDialog();

    ErrorHandler::m_MainWindow = this->GetSafeHwnd();

    try
    {
        //
	    // Set the icon for this dialog.  The framework does this automatically
	    // when the application's main window is not a dialog
        //
	    SetIcon(m_hIcon, TRUE);			// Set big icon
	    SetIcon(m_hIcon, FALSE);		// Set small icon

        for (int Index = 0; Index < MAXCAMERACNT; Index++)
        {
            m_WarningMessageShown[Index] = FALSE;
        }

        //
        // Initialize registration object
        //
        Result = PhRegisterClientEx(NULL, NULL, NULL, PHCONHEADERVERSION);
        ErrorHandler::CheckError(Result);

        Result = PhConfigPoolUpdate(1500); //look for new cameras as fast as possible
        ErrorHandler::CheckError(Result);

        //
        // Do initial check for cameras
        //
        UpdateCameraPool();

        //
        // Start timer to check for cameras every 3 seconds
        //
        m_CameraPoolTimer = SetTimer(ID_CAMERA_POOL_TIMER, CAMERA_POOL_TIMER_INTERVAL, NULL);

        //
        // Start timer to update the display
        //
        m_RefreshTimer = SetTimer(ID_REFRESH_TIMER, REFRESH_TIMER_INTERVAL, NULL);
    }
    catch (CException* e)
    {
        CString Text;
        TCHAR err_message[DEFAULT_STR_MAXSZ];
        e->GetErrorMessage(err_message, DEFAULT_STR_MAXSZ);

        Text.Format(L"An important dll required to run this demo was not found./nException message:{%s} Application will exit", err_message);

        AfxMessageBox(Text);
    }
	return TRUE;  // return TRUE  unless you set the focus to a control
}

void CPhSimpleDemoDlg::OnDestroy()
{
    CDialog::OnDestroy();

    HRESULT result = PhUnregisterClient(this->m_hWnd);

    m_MaxImageSizeInBytes = 0;
    m_ImageSizeInBytes = 0;
}


void CPhSimpleDemoDlg::UpdateCineStatus(PCINESTATUS pCinestatus)
{
    PCINESTATUS pCstatus;
    BOOL        FreeMemNeeded = FALSE;

    //
    // get the current Cine Status
    //
    if (m_CurrentCamera != -1)
    {
        if (pCinestatus != NULL)
        {
            //
            // Cine Status was passed in
            //
            pCstatus = pCinestatus;
        }
        else
        {
            //
            // Cine Status was not passed in
            // need to alloc memory and get it
            //
            pCstatus = (PCINESTATUS)malloc(sizeof(CINESTATUS) * PhMaxCineCnt((UINT)m_CurrentCamera));
            PhGetCineStatus((UINT)m_CurrentCamera, pCstatus);
            FreeMemNeeded = TRUE;
        }

        //////////////////////////////////////////////////
        // What is the camera doing                     //
        //////////////////////////////////////////////////

        if (m_PlaybackActive == TRUE)
        {
            m_PlaybackLabel.ShowWindow(SW_SHOW);

            m_LiveLabel.ShowWindow(SW_HIDE);
            m_RecordingLabel.ShowWindow(SW_HIDE);
            m_TriggeredLabel.ShowWindow(SW_HIDE);

            m_FirstImageEditBox.ShowWindow(SW_SHOW);
            m_CurrentImageEditBox.ShowWindow(SW_SHOW);
            m_LastImageEditBox.ShowWindow(SW_SHOW);

            m_recordButton.EnableWindow(FALSE);
            m_TriggerButton.EnableWindow(FALSE);

            m_PauseButton.EnableWindow(TRUE);
            m_StopButton.EnableWindow(TRUE);
        }
        else
        {
            //
            // Not playback
            //
            m_PlaybackLabel.ShowWindow(SW_HIDE);
            m_FirstImageEditBox.ShowWindow(SW_HIDE);
            m_CurrentImageEditBox.ShowWindow(SW_HIDE);
            m_LastImageEditBox.ShowWindow(SW_HIDE);

            m_recordButton.EnableWindow(TRUE);
            m_TriggerButton.EnableWindow(TRUE);

            m_PauseButton.EnableWindow(FALSE);
            m_StopButton.EnableWindow(FALSE);

            //
            // if Cine 0 (the preview Cine) is Active
            // then we are doing Preview
            //
            if (pCstatus[0].Active == TRUE)
            {
                //
                // Preview Mode
                //
                m_LiveLabel.ShowWindow(SW_SHOW);
                m_RecordingLabel.ShowWindow(SW_HIDE);
                m_TriggeredLabel.ShowWindow(SW_HIDE);

                m_recordButton.SetWindowText(_T("Record"));

                //
                // if we have a Stored Cine 
                // we can enable the playback button
                //
                if (pCstatus[1].Stored == TRUE)
                {
                    m_PlaybackButton.EnableWindow(TRUE);
                    m_SaveButton.EnableWindow(TRUE);
                    m_SaveProgressBar.EnableWindow(TRUE);
                }
                else
                {
                    m_PlaybackButton.EnableWindow(FALSE);

                    m_SaveButton.EnableWindow(FALSE);
                    m_SaveProgressBar.EnableWindow(FALSE);
                    m_SaveProgressBar.SetPos(0);

                    m_SaveCineToFileLabel.EnableWindow(FALSE);
                    m_SaveCineToFileLabel.SetWindowText(_T(""));
                }
            }
            else if (pCstatus[1].Active == TRUE)
            {
                m_LiveLabel.ShowWindow(SW_SHOW);

                m_recordButton.SetWindowText(_T("Stop Record"));

                //
                // are we recording?
                //
                if (pCstatus[1].Stored == FALSE)
                {
                    m_RecordingLabel.ShowWindow(SW_SHOW);

                    m_PlaybackButton.EnableWindow(FALSE);
               
                    m_SaveButton.EnableWindow(FALSE);
                    m_SaveProgressBar.EnableWindow(FALSE);
                    m_SaveProgressBar.SetPos(0);

                    m_SaveCineToFileLabel.EnableWindow(FALSE);
                    m_SaveCineToFileLabel.SetWindowText(_T(""));
                }
                else
                {
                    m_RecordingLabel.ShowWindow(SW_HIDE);
                }

                //
                // have we been triggered
                //
                if (pCstatus[1].Triggered == TRUE)
                {
                    m_TriggeredLabel.ShowWindow(SW_SHOW);
                }
                else
                {
                    m_TriggeredLabel.ShowWindow(SW_HIDE);
                }
            }
            else
            {
                //
                // some other Cine is active
                // this simple demo only supports Cine 1
                // so just turn all status FALSE
                //
                m_LiveLabel.ShowWindow(SW_HIDE);
                m_RecordingLabel.ShowWindow(SW_HIDE);
                m_TriggeredLabel.ShowWindow(SW_HIDE);

                m_PlaybackButton.EnableWindow(FALSE);
                m_SaveButton.EnableWindow(FALSE);

                m_SaveProgressBar.EnableWindow(FALSE);
                m_SaveProgressBar.SetPos(0);

                m_SaveCineToFileLabel.EnableWindow(FALSE);
                m_SaveCineToFileLabel.SetWindowText(_T(""));
            }
        }
    }
    else
    {
        //
        // no cameras 
        //
        m_LiveLabel.ShowWindow(SW_HIDE);
        m_RecordingLabel.ShowWindow(SW_HIDE);
        m_TriggeredLabel.ShowWindow(SW_HIDE);
        m_PlaybackLabel.ShowWindow(SW_HIDE);

        m_PlaybackButton.EnableWindow(FALSE);
        m_SaveButton.EnableWindow(FALSE);

        m_SaveProgressBar.EnableWindow(FALSE);
        m_SaveProgressBar.SetPos(0);

        m_SaveCineToFileLabel.EnableWindow(FALSE);
        m_SaveCineToFileLabel.SetWindowText(_T(""));
    }

    if (FreeMemNeeded == TRUE)
    {
        free(pCstatus);
    }
}


void CPhSimpleDemoDlg::UpdateCameraControls()
{
    CString Text;

    //
    // see if Current camera have changed 
    // from online  --> offline
    // or   offline --> online
    //
    if (m_CurrentCamera != -1)
    {
        m_Offline = PhOffline((UINT)m_CurrentCamera);
        if (m_Offline == TRUE)
        {
            m_OfflineLabel.ShowWindow(SW_SHOW);
        }
        else
        {
            m_OfflineLabel.ShowWindow(SW_HIDE);
        }
    }

    //
    // get the current setup for this camera
    //
    PhGetCineParams((UINT)m_CurrentCamera, 0, &m_AcquiParams, NULL);

    //
    // get the current Item to show on the ComboBox
    //
    Text.Format(L"%d x %d", m_AcquiParams.ImWidth, m_AcquiParams.ImHeight);
    m_ResComboBox.SetWindowText(Text);

    //
    // Update the current exposure (Display in uSec)
    //
    Text.Format(L"%d", m_AcquiParams.Exposure / 1000);
    m_ExpEditBox.SetWindowText(Text);

    //
    // Update the current Frame Rate
    //
    Text.Format(L"%d", (UINT)m_AcquiParams.dFrameRate);
    m_FrameRateEditBox.SetWindowText(Text);

    //
    // Update the Cine Status
    //
    UpdateCineStatus(NULL);
}

void CPhSimpleDemoDlg::OnCbnSelchangeCameraCombo()
{
    CString Text;
    POINT Resolutions[MAX_RESOLUTIONS];
    UINT ResCount = MAX_RESOLUTIONS;
    TCHAR TCharArray[MAXSTDSTRSZ];
    size_t convertedChars = 0;
    BOOL FlipImage = FALSE;

    m_CurrentCamera = m_CameraComboBox.GetCurSel();
   
    //
    // Get Camera Info
    //
    Ip2text(m_CamId[m_CurrentCamera].IP, &Text);
    m_IpAddrEditBox.SetWindowText(Text);

    Text.Format(L"%d", m_CamId[m_CurrentCamera].Serial);
    m_SerialNumEditBox.SetWindowText(Text);

    mbstowcs_s(&convertedChars, TCharArray, MAXSTDSTRSZ, m_CamId[m_CurrentCamera].Name, _TRUNCATE);
    Text.Format(L"%s", TCharArray);
    m_CameraNameEditBox.SetWindowText(Text);

    mbstowcs_s(&convertedChars, TCharArray, MAXSTDSTRSZ, m_CamId[m_CurrentCamera].Model, _TRUNCATE);
    Text.Format(L"%s", TCharArray);
    m_ModelEditBox.SetWindowText(Text);

    PhGetCineLive((INT)m_CurrentCamera, &m_LiveCineHandle);
    PhGetCineInfo(m_LiveCineHandle, GCI_MAXIMGSIZE, &m_ImageSizeInBytes);

    //
    // GetCineImage image flip is inhibated.
    //
    PhSetCineInfo(m_LiveCineHandle, GCI_VFLIPVIEWACTIVE, (PVOID)&FlipImage); 

    //
    // get a list of standard supported resolution for this Camera
    //
    PhGetResolutions((UINT)m_CurrentCamera, Resolutions, &ResCount, NULL, NULL);

    //
    // Update resolution combo
    //
    m_ResComboBox.ResetContent();
    for (UINT ires = 0; ires < ResCount; ires++)
    {
        Text.Format(L"%d x %d", Resolutions[ires].x, Resolutions[ires].y);
        m_ResComboBox.AddString(Text);
    }

    //
    // Update the Camera Controls
    //
    UpdateCameraControls();

    //
    // Need to clear the display
    //
    m_ClearImageDisplay = TRUE;
}

/// <summary>
/// This coresponds to UINT representation found in Phantom
/// </summary>
/// <param name="ip"></param>
/// <returns></returns>
UINT CPhSimpleDemoDlg::IpFromString(CString IP)
{  
    unsigned IpAddress = 0;     // The return value.  
    int i;                      // The count of the number of bytes processed.
    int Index = 0;
    int Start = 0;
    int Octet = 0;
    CString Text;

    for (i = 0; i < 4; i++)
    {  
        if (i == 3)
        {
            //
            // last octet therefore no "." at end
            // will assume we have more string left
            //
            Text = IP.Mid(Start);
            Octet = _wtoi(Text);
        }
        else
        {
            Index = IP.Find(L".", Start);

            if (Index != -1)
            {
                Text = IP.Mid(Start, Index - Start);
                Octet = _wtoi(Text);
                Start = Index + 1;
            }
        }

        IpAddress *= 256;
        IpAddress += Octet;
    }
    return (IpAddress);
}

//
// See if we have any cameras, and 
// if any cameras have been added to the Pool
//
void CPhSimpleDemoDlg::UpdateCameraPool(void)
{
    UINT CurCamCount;
    UINT partCnt = 0;
    CString Text;
    size_t convertedChars = 0;
    char CharArray[MAXIPSTRSZ];
    TCHAR TCharArray[MAXIPSTRSZ];

    //
    // see if we have found any new cameras
    //
    PhGetCameraCount(&CurCamCount);

    //
    // we have no cameras, so add a simulated camera
    //
    if (CurCamCount == 0)
    {
        //
        // add a simulated VEO 710S
        //
        PhAddSimulatedCamera(7001, 1234);
        CurCamCount = 1;
    }

    if (CurCamCount > m_CameraCount)
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
        for (UINT i = m_CameraCount; i < CurCamCount; i++)
        {
            //
            // Ip Address
            //
            PhGet((UINT)i, gsIPAddress, &CharArray);

            mbstowcs_s(&convertedChars, TCharArray, MAXIPSTRSZ, CharArray, _TRUNCATE);

            Text.Format(L"%s", TCharArray);
            m_CamId[i].IP = IpFromString(Text);

            //
            // Serial Number and Name
            //
            PhGetCameraID((UINT)i, &m_CamId[i].Serial, m_CamId[i].Name);

            //
            // Max Cine Count (max number of Partition)
            //
            m_CamId[i].MaxCineCnt = (UINT)PhMaxCineCnt((UINT)i);

            //
            // Sensor CFA
            //
            PhGetVersion((UINT)i, GV_CFA, &m_CamId[i].CFA);

            //
            // Camera Hardware Version Number
            //
            PhGetVersion((UINT)i, GV_CAMERA, &m_CamId[i].CamVer);

            //
            // Model String
            //
            PhGet((UINT)i, gsModel, m_CamId[i].Model);

            if (m_CamId[i].Name[0] == NULL)
            {
                sprintf_s(m_CamId[i].Name, sizeof(m_CamId[i].Name), "%d", m_CamId[i].Serial);
            }

            Text.Format(L"%d", i);
            m_CameraComboBox.AddString(Text);

            //
            // check the new camera we just found to see if
            // it has more than 1 partition.
            // show warning message if > 1 partition
            // this is a simple demo and only supports a single partition
            //
            if (m_WarningMessageShown[i] == FALSE)
            {
                PhGetPartitions((UINT)i, &partCnt, NULL);
                if (partCnt > 1)
                {
                    AfxMessageBox(L"This camera has more than 1 partition\nThis is a simple demo and only supports a single partition");
                }
                m_WarningMessageShown[i] = TRUE;
            }

            //
            // if this is the first camera found
            // setup the combo box
            //
            if (m_CurrentCamera == -1)
            {
                m_CurrentCamera = 0;
                m_CameraComboBox.SetCurSel(m_CurrentCamera);
                OnCbnSelchangeCameraCombo();
            }
        }
        m_CameraCount = CurCamCount;
    }

    //
    // see if Current camera have changed 
    // from online  --> offline
    // or   offline --> online
    //
    if (m_CurrentCamera != -1)
    {
        m_Offline = PhOffline((UINT)m_CurrentCamera);
        if (m_Offline == TRUE)
        {
            m_OfflineLabel.ShowWindow(SW_SHOW);
        }
        else
        {
            m_OfflineLabel.ShowWindow(SW_HIDE);
        }
    }
}

//
// make sure we have room to whole the image data
// it could have changed if they change the resolution
//
void CPhSimpleDemoDlg::SetImageBufferSize(CINEHANDLE CineHandle)
{
    PhGetCineInfo(CineHandle, GCI_MAXIMGSIZE, &m_ImageSizeInBytes);

    if (m_ImagePictureBox.GetImageBufferPtr() == NULL)
    {
        m_ImagePictureBox.SetImageBufferSize(m_ImageSizeInBytes);
        m_MaxImageSizeInBytes = m_ImageSizeInBytes;
    }
    else if (m_ImageSizeInBytes > m_MaxImageSizeInBytes)
    {
        //
        // need more space
        //
        m_ImagePictureBox.SetImageBufferSize(m_ImageSizeInBytes);
        m_MaxImageSizeInBytes = m_ImageSizeInBytes;
    }
}


void CPhSimpleDemoDlg::RefreshTimerTick(void)
{
    CString Text;
    HRESULT Result;
    IH ImageHeader;
    BOOL CurrentState;

    if (m_CurrentCamera != -1)
    {
        //
        // see if Current camera have changed 
        // from online  --> offline
        // or   offline --> online
        //
        if (m_CurrentCamera != -1)
        {
            CurrentState = PhOffline((UINT)m_CurrentCamera);

            //
            // update menu if the state has changed
            //
            if (CurrentState != m_Offline)
            {
                m_Offline = CurrentState;
                if (m_Offline == TRUE)
                {
                    m_OfflineLabel.ShowWindow(SW_SHOW);
                }
                else
                {
                    m_OfflineLabel.ShowWindow(SW_HIDE);
                }
            }
        }
        
        //
        // Do we need to clear the display
        //
        if (m_ClearImageDisplay == TRUE)
        {
            m_ClearImageDisplay = FALSE;
            m_ImagePictureBox.ClearPictureBox();
        }

        if (m_PlaybackActive == FALSE)
        {
            //
            // Show Live Images
            //
            m_ImageRange.First = 0;
            m_ImageRange.Cnt = 1;

            PhSetUseCase(m_LiveCineHandle, UC_VIEW);

            SetImageBufferSize(m_LiveCineHandle);

 
            Result = PhGetCineImage(m_LiveCineHandle, &m_ImageRange, m_ImagePictureBox.GetImageBufferPtr(), m_ImageSizeInBytes, &ImageHeader);
        }
        else
        {
            //
            // Show Stored Images
            //
            m_ImageRange.First = m_CurrentImage;
            m_ImageRange.Cnt = 1;

            Text.Format(L"%d", m_CurrentImage);
            m_CurrentImageEditBox.SetWindowText(Text);

            PhSetUseCase(m_StoredCineHandle, UC_VIEW);

            SetImageBufferSize(m_StoredCineHandle);

            Result = PhGetCineImage(m_StoredCineHandle, &m_ImageRange, m_ImagePictureBox.GetImageBufferPtr(), m_ImageSizeInBytes, &ImageHeader);
            if ((m_PauseCheck == FALSE) && (m_Offline == FALSE))
            {
                m_CurrentImage++;
                if (m_CurrentImage > (m_StoredImageRange.First + (INT)m_StoredImageRange.Cnt))
                {
                    m_CurrentImage = m_StoredImageRange.First;
                    SetPauseButton(TRUE);
                }
            }
        }

        //
        // if needed reduce image bitdepth to 8bpp in order to be displayed
        // the image will be 8bpp at drawing
        //
        if (ImageHeader.biBitCount == 16 || ImageHeader.biBitCount == 48)
        {
            FLOAT Sensitivity;
            REDUCE16TO8PARAMS ReduceOption;

            PhGetCineInfo(m_LiveCineHandle, GCI_GAIN16_8, (PVOID)&Sensitivity);
            ReduceOption.fGain16_8 = Sensitivity;

            PhProcessImage(m_ImagePictureBox.GetImageBufferPtr(), m_ImagePictureBox.GetImageBufferPtr(), &ImageHeader, IMG_PROC_REDUCE16TO8, &ReduceOption);
        }

        //
        // associate the bitmap header with image buffer.
        //
        BITMAPINFOHEADER bmiHeader;

        //
        // refresh the bitmap info
        //
        bmiHeader = *(PBITMAPINFOHEADER)(&ImageHeader);

        //
        // IH is bigger than BMIH, reassign the size
        //
        bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
        m_ImagePictureBox.SetBMIH(&bmiHeader);

        m_ImagePictureBox.Invalidate(TRUE);

     }

    //
    // don't need to update the dialog so offend 
    //
    m_DialogUpdateTick--;
    if (m_DialogUpdateTick <= 0)
    {
        //
        // update the Dialog
        //
        UpdateCineStatus(NULL);
        m_DialogUpdateTick = UPDATE_RATE;
    }
}

void CPhSimpleDemoDlg::OnTimer(UINT_PTR nIDEvent)
{
    if (nIDEvent == ID_REFRESH_TIMER)
    {
        RefreshTimerTick();

        //
        // only need to update if Active and value changed
        //
        if ((m_SaveInProgress == TRUE) && (m_CurrentPercent != CineSaveProgress))
        {
            m_CurrentPercent = CineSaveProgress;
            UpdateCineSaveProgressInfo(CineSaveProgress);
        }
    }
    else if (nIDEvent == ID_CAMERA_POOL_TIMER)
    {
        UpdateCameraPool();
    }
}


// If you add a minimize button to your dialog, you will need the code below
//  to draw the icon.  For MFC applications using the document/view model,
//  this is automatically done for you by the framework.

void CPhSimpleDemoDlg::OnPaint()
{
	if (IsIconic())
	{
		CPaintDC dc(this); // device context for painting

		SendMessage(WM_ICONERASEBKGND, reinterpret_cast<WPARAM>(dc.GetSafeHdc()), 0);

		// Center icon in client rectangle
		INT cxIcon = GetSystemMetrics(SM_CXICON);
		INT cyIcon = GetSystemMetrics(SM_CYICON);
		CRect rect;
		GetClientRect(&rect);
		INT x = (rect.Width() - cxIcon + 1) / 2;
		INT y = (rect.Height() - cyIcon + 1) / 2;

		// Draw the icon
		dc.DrawIcon(x, y, m_hIcon);
	}
	else
	{
		CDialog::OnPaint();
	}
}

// The system calls this function to obtain the cursor to display while the user drags
//  the minimized window.
HCURSOR CPhSimpleDemoDlg::OnQueryDragIcon()
{
	return static_cast<HCURSOR>(m_hIcon);
}

void CPhSimpleDemoDlg::Ip2text(UINT ip, CString* Text)
{
    Text->Format(L"%d.%d.%d.%d", ip >> 24 & 0xff, ip >> 16 & 0xff, ip >> 8 & 0xff, ip & 0xff);
}


void CPhSimpleDemoDlg::OnBnClickedRecordButton()
{
    CString Text;
    int Result = IDYES;
    
    if (m_CurrentCamera != -1)
    {
        PCINESTATUS pCinestatus = (PCINESTATUS)malloc(sizeof(CINESTATUS) * PhMaxCineCnt((UINT)m_CurrentCamera));
        PhGetCineStatus((UINT)m_CurrentCamera, pCinestatus);

        if (pCinestatus[0].Active == TRUE)
        {
            //
            // start record
            //
            if (pCinestatus[1].Stored == TRUE)
            {
                //
                // Starting New Record
                // need to delete old record
                //
                Result = AfxMessageBox(L"Delete Old Record?", MB_YESNO);

                if (Result == IDYES)
                {
                    PhDeleteCine((UINT)m_CurrentCamera, 1);
                }
            }

            if (Result == IDYES)
            {
                PhRecordCine((UINT)m_CurrentCamera);
            }
        }
        else
        {
            if (pCinestatus[1].Stored == FALSE)
            {
                //
                // Stop record and go into preview
                //
                PhRecordSpecificCine((UINT)m_CurrentCamera, 0);
            }
        }

        //
        // update the Dialog
        //
        UpdateCineStatus(pCinestatus);
        free(pCinestatus);
    }
}


void CPhSimpleDemoDlg::OnBnClickedTriggerButton()
{
    if (m_CurrentCamera != -1)
    {
        PCINESTATUS pCinestatus = (PCINESTATUS)malloc(sizeof(CINESTATUS) * PhMaxCineCnt((UINT)m_CurrentCamera));

        PhGetCineStatus((UINT)m_CurrentCamera, pCinestatus);

        //
        // only send trigger command when
        // we are in the record mode
        // (ie. not preview or playback)
        //
        if (pCinestatus[1].Active == TRUE)
        {
            PhSendSoftwareTrigger((UINT)m_CurrentCamera);
        }

        free(pCinestatus);
    }
}


void CPhSimpleDemoDlg::OnBnClickedPlaybackModeButton()
{
    CString Text;
    BOOL FlipImage = FALSE;

    //
    // Show the live cine or the Stored Recorded Cine
    //
    if (m_PlaybackActive == TRUE)
    {
        //
        // show live Cine
        //
        m_PlaybackActive = FALSE;

        //
        // reset the current Frame number in case
        // we re-enter Playback mode
        //
        m_CurrentImage = m_StoredImageRange.First;

        //
        // Need to clear the display
        //
        m_ClearImageDisplay = TRUE;
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
        if (m_StoredCineHandle != NULL)
        {
            PhDestroyCine(m_StoredCineHandle);
            m_StoredCineHandle = NULL;
        }
        PhNewCineFromCamera((INT)m_CurrentCamera, 1, &m_StoredCineHandle);

        //
        // GetCineImage image flip is inhibated.
        //
        PhSetCineInfo(m_StoredCineHandle, GCI_VFLIPVIEWACTIVE, (PVOID)&FlipImage);

        //
        // get number of images
        //
        PhGetCineInfo(m_StoredCineHandle, GCI_FIRSTIMAGENO, &m_StoredImageRange.First);
        PhGetCineInfo(m_StoredCineHandle, GCI_TOTALIMAGECOUNT, &m_StoredImageRange.Cnt);

        m_CurrentImage = m_StoredImageRange.First;

        Text.Format(L"First Frame: %d", m_StoredImageRange.First);
        m_FirstImageEditBox.SetWindowText(Text);

        Text.Format(L"Frame: %d", m_CurrentImage);
        m_CurrentImageEditBox.SetWindowText(Text);

        Text.Format(L"Last Frame: %d", m_StoredImageRange.First + m_StoredImageRange.Cnt - 1);
        m_LastImageEditBox.SetWindowText(Text);

        m_PlaybackActive = TRUE;

        //
        // Need to clear the display
        //
        m_ClearImageDisplay = TRUE;
    }
    //
    // update the Dialog
    //
    UpdateCineStatus(NULL);
}


void CPhSimpleDemoDlg::UpdateCineSaveProgressInfo(UINT Percent)
{
    CString Text;

    if ((Percent >= 0) && (Percent <= 100))
    {
        m_SaveProgressBar.SetPos(Percent);
        Text.Format(_T("Saving Cine to file: %d%%"), Percent);
        m_SaveCineToFileLabel.SetWindowText(Text);
    }

    //
    // callback function will always be called for 100
    //
    if (Percent >= 100)
    {
        m_SaveInProgress = FALSE;
        m_SaveProgressBar.EnableWindow(FALSE);
        m_SaveCineToFileLabel.EnableWindow(FALSE);
        if (m_PlaybackActive == TRUE)
        {
            m_PauseButton.EnableWindow(TRUE);
            m_StopButton.EnableWindow(TRUE);
        }
    }
}

BOOL WINAPI CPhSimpleDemoDlg::SaveCineProgressChanged(UINT Percent, CINEHANDLE CineHandle)
{
    CineSaveProgress = Percent;

    return (TRUE);
}

void CPhSimpleDemoDlg::OnBnClickedSaveButton()
{
    BOOL Result;

    // Need to get a cine handle
    // if we don't have one
    // if we have one already it could be old
    // so get a new one to be sure
    // we only handle the first cine file 
    // (ie. 0 = preview cine, 1= first stored cine)
    //
    if (m_SaveCineHandle != NULL)
    {
        PhDestroyCine(m_SaveCineHandle);
        m_SaveCineHandle = NULL;
    }
    PhNewCineFromCamera((INT)m_CurrentCamera, 1, &m_SaveCineHandle);

    //
    // get number of images
    //
    PhGetCineInfo(m_SaveCineHandle, GCI_FIRSTIMAGENO, &m_StoredImageRange.First);
    PhGetCineInfo(m_SaveCineHandle, GCI_TOTALIMAGECOUNT, &m_StoredImageRange.Cnt);

    Result = PhGetSaveCineName(m_SaveCineHandle);

    if (Result == TRUE)
    {
        //
        // Stop Playback during the Save
        //
        if (m_PlaybackActive == TRUE)
        {
            SetPauseButton(TRUE);
            m_PauseButton.EnableWindow(TRUE);
            m_StopButton.EnableWindow(TRUE);
        }

        m_SaveProgressBar.EnableWindow(TRUE);
        m_SaveProgressBar.SetPos(0);

        m_SaveCineToFileLabel.EnableWindow(TRUE);
        m_SaveCineToFileLabel.SetWindowText(_T("Saving Cine to file: 0%"));

        //
        // set the usecase for save
        //
        PhSetUseCase(m_SaveCineHandle, UC_SAVE);

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
        m_SaveInProgress = TRUE;
        m_CurrentPercent = 0;
        PhWriteCineFileAsync(m_SaveCineHandle, &CPhSimpleDemoDlg::SaveCineProgressChanged);
    }
}


int CPhSimpleDemoDlg::ResComboBox_Ctrl()
{
    int Update = -1;
    CString Text;
    int pos;
    UINT Width;
    UINT Height;

    m_ResComboBox.GetWindowText(Text);

    //
    // should always find the "x" 
    //
    pos = Text.Find(L"x");
    if (pos != -1)
    {
        Update = 0;
        Width = _wtoi(Text.Mid(0, pos));

        Height = _wtoi(Text.Mid(pos + 1));

        if ((Width != 0) && (Height != 0) )
        {
            //
            // only update if the values are different from the current
            //
            if ((Width != m_AcquiParams.ImWidth) &&
                (Height != m_AcquiParams.ImHeight))
            {
                m_AcquiParams.ImWidth = Width;
                m_AcquiParams.ImHeight = Height;
                m_ClearImageDisplay = TRUE;
                Update = 1;
            }
        }
        else
        {
            //
            // Error
            //
            Update = -1;
        }

    }
    return (Update);
}

int CPhSimpleDemoDlg::ExpEditBox_Ctrl()
{
    int Update = 0;
    CString Text;
    UINT Exposure;

    m_ExpEditBox.GetWindowText(Text);

    Exposure = _wtoi(Text);

    if (Exposure != 0)
    {
        //
        // Exposure value is in nSec
        // only update if the values are different from the current
        //
        if (m_AcquiParams.Exposure != (Exposure * 1000))
        {
            m_AcquiParams.Exposure = Exposure * 1000;
            Update = 1;
        }
    }
    else
    {
        //
        // Error
        //
        Update = -1;
    }

    return (Update);
}


int CPhSimpleDemoDlg::FrameRateEditBox_Ctrl()
{
    int Update = 0;
    CString Text;
    UINT FrameRate;
    double ExactFrameRate;


    m_FrameRateEditBox.GetWindowText(Text);
    FrameRate = _wtoi(Text);

    if (FrameRate != 0)
    {
        //
        // verify and get the frame rate the camera can actual do
        // only update if the values are different from the current
        //
        PhGetExactFrameRate((UINT)m_CurrentCamera, m_AcquiParams.SyncImaging, FrameRate, &ExactFrameRate);

        if (m_AcquiParams.dFrameRate != ExactFrameRate)
        {
            m_AcquiParams.dFrameRate = ExactFrameRate;
            Update = 1;
        }
    }
    else
    {
        //
        // Error
        //
        Update = -1;
    }

    return (Update);
}


void CPhSimpleDemoDlg::OnBnClickedSetButton()
{
    CString Text;
    int ResUpdate = 0;
    int ExposureUpdate = 0;
    int FrameRateUpdate = 0;

    //
    // get the current setup for this camera
    //
    PhGetCineParams((UINT)m_CurrentCamera, 0, &m_AcquiParams, NULL);

    //
    // make the needed changes (if any)
    //
    ResUpdate = ResComboBox_Ctrl();
    FrameRateUpdate = FrameRateEditBox_Ctrl();
    ExposureUpdate = ExpEditBox_Ctrl();

    if (ResUpdate == -1)
    {
        Text.Format(L"Invalid Image Resolution\n");
    }
    if (ExposureUpdate == -1)
    {
        Text.AppendFormat(L"Invalid Exposure\n");
    }
    if (FrameRateUpdate == -1)
    {
        Text.AppendFormat(L"Invalid Framerate");
    }

    if ((ResUpdate == -1) || (ExposureUpdate == -1) || (FrameRateUpdate == -1))
    {
        AfxMessageBox(Text, MB_OK | MB_ICONSTOP);
    }
    else
    {
        //
        // update the camera if any of the setting have changed
        //
        if ((ResUpdate > 0) || (ExposureUpdate > 0) || (FrameRateUpdate > 0))
        {
            PhSetCineParams((UINT)m_CurrentCamera, 0, &m_AcquiParams);

            //
            // Changing Resolution will effect what FrameRate is Valid
            // Changing FrameRate will effect what Exposure is Valid
            // So now that we have set the camera lets make sure of
            // what it is actually set to, in case we gave it invalid values
            //
            UpdateCameraControls();
        }
    }
}


void CPhSimpleDemoDlg::OnBnClickedPauseButton()
{
    if (m_PauseCheck == FALSE)
    {
        m_PauseButton.SetWindowText(_T("Play"));
        m_PauseCheck = TRUE;
    }
    else
    {
        m_PauseButton.SetWindowText(_T("Pause"));
        m_PauseCheck = FALSE;
    }
}
void CPhSimpleDemoDlg::SetPauseButton(BOOL State)
{
    m_PauseCheck = State;
    if (m_PauseCheck == FALSE)
    {
        m_PauseButton.SetWindowText(_T("Pause"));

    }
    else
    {
        m_PauseButton.SetWindowText(_T("Play"));
    }
}

void CPhSimpleDemoDlg::OnBnClickedStopButton()
{
    m_CurrentImage = m_StoredImageRange.First;
    SetPauseButton(TRUE);
}


BOOL CPhSimpleDemoDlg::PreTranslateMessage(MSG* pMsg)
{
    char        CharCode;
    BOOL        MessageHandled = FALSE; // Message Not Handled

    if (pMsg->message == WM_CHAR)
    {
        CharCode = (char)pMsg->wParam;    // character code 

        if (CharCode == 0x0D)
        {
            CWnd*   CurrentFocusControl;

            //
            // it was the enter key do we need to do anything?
            // Only if we are on the FrameRate or Exposure Editbox
            // Resolution Combo
            //
            CurrentFocusControl = GetFocus();

            //
            // Assume Message Handled (for Now)
            //
            MessageHandled = TRUE;

            if ((GetDlgItem(IDC_RESOLUTION_COMBO) == CurrentFocusControl) ||
                (GetDlgItem(IDC_EXPOSURE_EDIT)    == CurrentFocusControl) ||
                (GetDlgItem(IDC_FRAME_RATE_EDIT)  == CurrentFocusControl))
            {
                //
                // it was the enter key so press the set button
                //
                OnBnClickedSetButton();
            }
 
            //
            // Assume Message Handled (for Now)
            //
            MessageHandled = TRUE; 
        }
    }

    //
    // Message not Handled
    //
    return(MessageHandled);
}
