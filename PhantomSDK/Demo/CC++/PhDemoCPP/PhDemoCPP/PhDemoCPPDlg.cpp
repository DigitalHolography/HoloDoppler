
// PhDemoCPPDlg.cpp : implementation file
//

#include "stdafx.h"
#include <IO.h>
#include "PhDemoCPP.h"
#include "PhDemoCPPDlg.h"


// CAboutDlg dialog used for App About

class CAboutDlg : public CDialog
{
public:
	CAboutDlg();

	// Dialog Data
	enum { IDD = IDD_ABOUTBOX };

protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV support

	// Implementation
protected:
	DECLARE_MESSAGE_MAP()
};

CAboutDlg::CAboutDlg() : CDialog(CAboutDlg::IDD)
{
}

void CAboutDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
}

BEGIN_MESSAGE_MAP(CAboutDlg, CDialog)
END_MESSAGE_MAP()


// CPhDemoCPPDlg dialog

#pragma region PhDemoCPPDlg
CPhDemoCPPDlg::CPhDemoCPPDlg(CWnd* pParent /*=NULL*/)
: CDialog(CPhDemoCPPDlg::IDD, pParent)
{
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);

	m_pPoolBuilder = NULL;
	m_pPoolRefresher = NULL;
	m_pCinePlayer = NULL;

	m_pSelectedSource = NULL;
    m_pSelectedSourceIndex = -1;
    m_pOpenedFile = NULL;

	refreshTimer = 0;
    cameraPoolRefreshTimer = 0;
}

void CPhDemoCPPDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);

	DDX_Control(pDX, IDC_SOURCE, m_Source);
	DDX_Control(pDX, IDC_INFO, m_Info);
	DDX_Control(pDX, IDC_CINE, m_Cine);
	DDX_Control(pDX, IDC_CAPTURE, m_Capture);
	DDX_Control(pDX, IDC_TRIGGER, m_Trigger);
	DDX_Control(pDX, IDC_OPEN_CINE, m_OpenCine);
	DDX_Control(pDX, IDC_SAVE_CINE, m_SaveCine);

	DDX_Control(pDX, IDC_PART, m_Part);
	DDX_Control(pDX, IDC_PARTSTR, m_PartStr);
	DDX_Control(pDX, IDC_GROUP_CS, m_GCamSettings);

	DDX_Control(pDX, IDC_RESOLUTIONS, m_Resolutions);
	DDX_Control(pDX, IDC_BIT_DEPTH, m_BitDepth);
	DDX_Control(pDX, IDC_FRAME_RATE, m_FrameRate);
	DDX_Control(pDX, IDC_EXPOSURE, m_Exposure);
	DDX_Control(pDX, IDC_EDR_EXPOSURE, m_EDRExp);
	DDX_Control(pDX, IDC_PT_FRAMES, m_PTFrames);
	DDX_Control(pDX, IDC_IMAGE_COUNT, m_ImCount);
	DDX_Control(pDX, IDC_DELAY, m_Delay);
	DDX_Control(pDX, IDC_SETACQ, m_SetAcq);

	DDX_Control(pDX, IDC_BRIGHTNESS, m_Bright);
	DDX_Control(pDX, IDC_GAIN, m_Gain);
	DDX_Control(pDX, IDC_GAMMA, m_Gamma);
	DDX_Control(pDX, IDC_SATURATION, m_Saturation);
	DDX_Control(pDX, IDC_HUE, m_Hue);
	DDX_Control(pDX, IDC_WBRED, m_WBRed);
	DDX_Control(pDX, IDC_WBBLUE, m_WBBlue);
	DDX_Control(pDX, IDC_SET_IMPROC, m_SetImProc);

	//CinePlayer
	DDX_Control(pDX, IDC_PREVIEW, m_PreviewBox);
	DDX_Control(pDX, IDC_PLAY, m_BtnPlay);
	DDX_Control(pDX, IDC_FRAMER, m_Framer);
	DDX_Control(pDX, IDC_FIRST_IM, m_FirstIm);
	DDX_Control(pDX, IDC_LAST_IM, m_LastIm);
	DDX_Control(pDX, IDC_CRT_FR, m_CrtFr);
	////Buttom
	DDX_Control(pDX, IDC_SPEED, m_RefreshSpeed);
	DDX_Control(pDX, IDC_CAM_STATUS, m_CamStatus);
	DDX_Control(pDX, IDC_SAVE_STATUS, m_SaveStatus);
	DDX_Control(pDX, IDC_PROGRESS, m_Progress);
	DDX_Control(pDX, IDC_SIGNALS, m_Signals);
	DDX_Control(pDX, IDC_SIGGROUP, m_SigGrp);
	DDX_Control(pDX, IDC_BINSIG, m_SigBin);
	DDX_Control(pDX, IDC_ANASIG, m_SigAna);
}

BEGIN_MESSAGE_MAP(CPhDemoCPPDlg, CDialog)
	ON_WM_SYSCOMMAND()
	ON_WM_TIMER()
	ON_WM_PAINT()
	ON_WM_QUERYDRAGICON()
	//}}AFX_MSG_MAP
	ON_CBN_SELENDOK(IDC_SOURCE, &CPhDemoCPPDlg::OnCbnSelendokSource)
	ON_CBN_SELENDOK(IDC_CINE, &CPhDemoCPPDlg::OnCbnSelendokCine)
	ON_BN_CLICKED(IDC_SETACQ, &CPhDemoCPPDlg::OnBnClickedSetacq)
	ON_BN_CLICKED(IDC_SET_IMPROC, &CPhDemoCPPDlg::OnBnClickedSetImproc)
	ON_CBN_SELENDOK(IDC_PART, &CPhDemoCPPDlg::OnCbnSelendokPart)
	ON_WM_DESTROY()
	ON_BN_CLICKED(IDC_CAPTURE, &CPhDemoCPPDlg::OnBnClickedCapture)
	ON_BN_CLICKED(IDC_TRIGGER, &CPhDemoCPPDlg::OnBnClickedTrigger)
	ON_BN_CLICKED(IDC_PLAY, &CPhDemoCPPDlg::OnBnClickedPlay)
	ON_BN_CLICKED(IDC_OPEN_CINE, &CPhDemoCPPDlg::OnBnClickedOpenCine)
	ON_BN_CLICKED(IDC_SAVE_CINE, &CPhDemoCPPDlg::OnBnClickedSaveCine)
	ON_BN_CLICKED(IDC_INFO, &CPhDemoCPPDlg::OnBnClickedInfo)
	ON_WM_HSCROLL()
	ON_BN_CLICKED(IDC_SIGNALS, &CPhDemoCPPDlg::OnBnClickedSignals)
END_MESSAGE_MAP()


#pragma region CPhDemoCPPDlg message handlers
BOOL CPhDemoCPPDlg::OnInitDialog()
{
	CDialog::OnInitDialog();

	// Add "About..." menu item to system menu.

	// IDM_ABOUTBOX must be in the system command range.
	ASSERT((IDM_ABOUTBOX & 0xFFF0) == IDM_ABOUTBOX);
	ASSERT(IDM_ABOUTBOX < 0xF000);

	CMenu* pSysMenu = GetSystemMenu(FALSE);
	if (pSysMenu != NULL)
	{
		BOOL bNameValid;
		CString strAboutMenu;
		bNameValid = strAboutMenu.LoadString(IDS_ABOUTBOX);
		ASSERT(bNameValid);
		if (!strAboutMenu.IsEmpty())
		{
			pSysMenu->AppendMenu(MF_SEPARATOR);
			pSysMenu->AppendMenu(MF_STRING, IDM_ABOUTBOX, strAboutMenu);
		}
	}

	// Set the icon for this dialog.  The framework does this automatically
	//  when the application's main window is not a dialog
	SetIcon(m_hIcon, TRUE);			// Set big icon
	SetIcon(m_hIcon, FALSE);		// Set small icon

	InitPhDemo();

	return TRUE;  // return TRUE  unless you set the focus to a control
}

void CPhDemoCPPDlg::OnDestroy()
{
	StopPhDemo();
	CDialog::OnDestroy();
}

void CPhDemoCPPDlg::OnSysCommand(UINT nID, LPARAM lParam)
{
	if ((nID & 0xFFF0) == IDM_ABOUTBOX)
	{
		CAboutDlg dlgAbout;
		dlgAbout.DoModal();
	}
    else
	{
		CDialog::OnSysCommand(nID, lParam);
	}
}

void CPhDemoCPPDlg::OnTimer(UINT_PTR nIDEvent)
{
    BOOL StateRefreshNeeded = FALSE;
    BOOL NoImage = FALSE;

	if(nIDEvent == ID_REFRESH)	
	{
        //
        // get the current state of the camera
        //
        Camera* pSelectedCamera = dynamic_cast<Camera*>(m_pSelectedSource);
        if (pSelectedCamera != NULL)
        {
            //
            // Is the camera Offline?
            // Need to execute a command that talks to the camera
            // don't care about the result of the command, only want
            // to see if it responds 
            //
            pSelectedCamera->ParamsChanged();

            if (pSelectedCamera->OfflineState() == TRUE)
            {
                //
                // the camera is offline, is this a live image or stored Image
                //
                if (m_pCinePlayer->IsLive() == FALSE)
                {
                    NoImage = TRUE;
                }
            }
        }
            
        //
        // did any camera change offline/Online State?
        //
        if (m_pPoolRefresher->cameraStateChange() == TRUE)
        {
            CString Text;
            Camera* pSelectedCam = dynamic_cast<Camera*>(m_pSelectedSource);
            if (m_pSelectedSource != NULL)
            {
                pSelectedCam->ToString(&Text);
            
                //
                // need to save the current selected source
                // the order of the will never change, just grow
                //
                int selectIndex = m_Source.GetCurSel();

                m_Source.DeleteString(selectIndex);
                m_Source.InsertString(selectIndex, Text);

                m_Source.SetCurSel(selectIndex);               
            }            
        }

        //
        // update Camera Pool Timer
        //
        cameraPoolRefreshTimer++;
        if (cameraPoolRefreshTimer > REFRESH_CAMERA_POOL_INTERVAL) 
        {
            cameraPoolRefreshTimer = 0;

            //
            // has the Camera Pool Changed
            //
            if (m_pPoolRefresher->RefreshCameras() == TRUE)
            {
                StopRefreshTimer();

                //
                // the m_pSelectedSource will get return later
                // need to clear if for now
                //
                m_pSelectedSource = NULL;
                RefreshSourceAndCine();

                //restart refresh timer
                StartRefreshTimer();
            }
        }


		LARGE_INTEGER Frequency;
		//update timer refresh frequency
		if(QueryPerformanceFrequency(&Frequency))
		{
			::QueryPerformanceCounter(&liStop);
			LONGLONG llTimeDiff = liStop.QuadPart - liStart.QuadPart;
			DOUBLE diffDuration = (DOUBLE) llTimeDiff / (DOUBLE) Frequency.QuadPart;
			::QueryPerformanceCounter(&liStart);
			CString refreshSpeedStr;
            refreshSpeedStr.Format(L"%.2f Hz", (1.0 / diffDuration));
			m_RefreshSpeed.SetWindowText(refreshSpeedStr);
		}
		else
			m_RefreshSpeed.SetWindowText(_T("Not supported"));

		//image refreshing
		try
		{
            if ((m_pSelectedSource != NULL) && (NoImage == FALSE))
            {
                m_pCinePlayer->PlayNextImage();
                UpdateWindow();

                RefreshColorDependentControls(m_pCinePlayer->IsColorImage());
            }
		}
		catch (CException* e)
		{
			TCHAR err_message[DEFAULT_STR_MAXSZ];
			e->GetErrorMessage(err_message, DEFAULT_STR_MAXSZ);
			//you may log this message
			AfxMessageBox(err_message);
		}  

		//update camera status, current cine stored state
		//detect&refresh parameters changes
		Camera* pSelectedCam = dynamic_cast<Camera*>(m_pSelectedSource);
		CString camStatusStr;
		if (pSelectedCam != NULL)
		{
			//update camera status info
			INT activePart = pSelectedCam->GetActiveCineNo();
			CameraStatus camStatus = pSelectedCam->GetCamStatus();
			if (camStatus != ::NotAvailable)
			{
				camStatusStr.Empty();
				camStatusStr.Append(_T("Camera status: "));
				CString statusStr;

                if (pSelectedCam->OfflineState() == TRUE)
                {
                    camStatusStr.Append(_T("Offline"));
                }
                else
                {
                    PrintCameraStatus(camStatus, activePart, &statusStr);
                }
				camStatusStr.Append(statusStr);
			}
			RefreshRecordActions(camStatus);

            if (pSelectedCam->OfflineState() == FALSE)
            {
                Cine *pCine = pSelectedCam->CurrentCine();
                if (pCine != NULL)
                {
                    if (pSelectedCam->OfflineState() == FALSE)
                    {
                        CINESTATUS selectedCineCurrentStatus = pSelectedCam->GetCinePartitionStatus(pSelectedCam->GetSelectedCinePartNo());

                        //if selected partition stored status had been changed, update cine interface
                        if (selectedCineCurrentStatus.Stored != mLastSelectedCineStatus.Stored)
                        {
                            if (pSelectedCam->OfflineState() == FALSE)
                            {
                                SelectCineFromCombo();
                                memcpy(&mLastSelectedCineStatus, &selectedCineCurrentStatus, sizeof(CINESTATUS));
                            }
                        }

                        if (pSelectedCam->OfflineState() == FALSE)
                        {
                            //if parameters were changed by another connection update UI
                            if (pSelectedCam->ParametersExternallyChanged())
                            {
                                RefreshPartitionCombo();
                                RefreshAcqParameters();
                                RefreshImProcessing();
                            }
                        }
                    }
                }
            }
		}
		else
		{
			camStatusStr.Empty();
			RefreshRecordActions(::NotAvailable);
		}
		m_CamStatus.SetWindowText(camStatusStr);

		//update save cine progress interface
		if (CineSaver::IsStarted())
		{
			m_Progress.SetPos((INT)CineSaver::GetProgress());
		}
		else if (!CineSaver::m_AcknowledgedStop)//save stopped but UI did not Acknowledged -> refresh UI
		{
			OnCineSave(FALSE);
			//check if any errors ocurred during save
			//ErrorHandler::CheckError(CineSaver::GetSaveCineError());
			CineSaver::m_AcknowledgedStop = TRUE;
		}
	}
}

// If you add a minimize button to your dialog, you will need the code below
//  to draw the icon.  For MFC applications using the document/view model,
//  this is automatically done for you by the framework.

void CPhDemoCPPDlg::OnPaint()
{
	if (IsIconic())
	{
		CPaintDC dc(this); // device context for painting

		SendMessage(WM_ICONERASEBKGND, reinterpret_cast<WPARAM>(dc.GetSafeHdc()), 0);

		// Center icon in client rectangle
		int cxIcon = GetSystemMetrics(SM_CXICON);
		int cyIcon = GetSystemMetrics(SM_CYICON);
		CRect rect;
		GetClientRect(&rect);
		int x = (rect.Width() - cxIcon + 1) / 2;
		int y = (rect.Height() - cyIcon + 1) / 2;

		// Draw the icon
		dc.DrawIcon(x, y, m_hIcon);
	}
	else
	{
		CDialog::OnPaint();
	}
}

// The system calls this function to obtain the cursor to display while the user drags
// the minimized window.
HCURSOR CPhDemoCPPDlg::OnQueryDragIcon()
{
	return static_cast<HCURSOR>(m_hIcon);
}
#pragma endregion

void CPhDemoCPPDlg::InitPhDemo()
{
	ErrorHandler::m_MainWindow = this->GetSafeHwnd();

    // Initialize registration object
    // Log folder is NULL to let dll's use default log folder: \Application Data\Phantom\DLLVersion
    // You may specify log folder

	m_pPoolBuilder = new PoolBuilder(this->m_hWnd, NULL);
	m_pPoolBuilder->Register();

	if (!m_pPoolBuilder->IsRegistered())
	{
		this->ExitApp();
	}

	m_pPoolRefresher = new PoolRefresher();
	m_pPoolRefresher->InitCameras();

	m_pCinePlayer = new CinePlayer(&m_PreviewBox, &m_BtnPlay, &m_Framer, &m_CrtFr, &m_FirstIm, &m_LastIm, &m_SigGrp, &m_SigBin, &m_SigAna);
	m_pCinePlayer->UpdatePlayUIVisibility();

	RefreshSourceAndCine();

	StartRefreshTimer();

	OnCineSave(FALSE);
}

void CPhDemoCPPDlg::StopPhDemo()
{
	StopRefreshTimer();
	
	if (m_pPoolBuilder->IsRegistered())
	{
		if (CineSaver::IsStarted())
		{
			CineSaver::StopSave();
		}
		//make sure the cine used for save is deleted
		CineSaver::DestroyCine();

		//destroy all memebers
		if (m_pPoolRefresher!=NULL)
		{
			delete m_pPoolRefresher;
			m_pPoolRefresher = NULL;
		}
		if (m_pOpenedFile!=NULL)
		{
			delete m_pOpenedFile;
			m_pOpenedFile = NULL;
		}
		if (m_pCinePlayer!=NULL)
		{
			delete m_pCinePlayer;
			m_pCinePlayer = NULL;
		}

		//does ph dll clean up
		m_pPoolBuilder->UnRegister();
	}

	if (m_pPoolBuilder!=NULL)
	{
		delete m_pPoolBuilder;
		m_pPoolBuilder = NULL;
	}
}

#pragma region RefreshUIMethods
void CPhDemoCPPDlg::RefreshSourceAndCine()
{
	RefreshSourceCombo();
	SelectSourceFromCombo();
	RefreshCineCombo();
	SelectCineFromCombo();
}

// refresh the soruce combo with avaialble cameras, add file selection
void CPhDemoCPPDlg::RefreshSourceCombo()
{
	m_Source.ResetContent();
	//populate listbox with current cameras
	INT camCount = m_pPoolRefresher->GetCameraListLength();
	for (INT icam = 0; icam < camCount; icam++)
	{
		Camera* pCam = NULL;
		pCam = m_pPoolRefresher->GetCameraAt(icam);
		CString camStringItem;
		pCam->ToString(&camStringItem);
		m_Source.AddString(camStringItem);
	}
	//add the file ID if any opened file exist
	if (m_pOpenedFile != NULL)
		m_Source.AddString(_T(FILE_SOURCE_NAME));

	//select combo item index based on selected source
	//the camera list index is the same as the combo item index
	Camera* selectedCamera = dynamic_cast<Camera*>(m_pSelectedSource);
	if (selectedCamera != NULL )
	{
		INT cameraIndex = m_pPoolRefresher->GetCameraIndexForSerial(selectedCamera->GetCameraSerial());
        if (cameraIndex >= 0)
        {
            m_Source.SetCurSel(cameraIndex);
        }
        else
        {
            m_Source.SetCurSel(0);
        }
	}
    else if (dynamic_cast<FileSource*>(m_pSelectedSource) != NULL)
    {
        m_Source.SetCurSel(m_Source.GetCount() - 1);//select last item
    }
    else if (m_pSelectedSource == NULL)
    {
        if (m_pSelectedSourceIndex != -1)
        {
            //
            // Restore Combo Box Setting
            //
            m_Source.SetCurSel(m_pSelectedSourceIndex);
        }
        else
        {
            m_Source.SetCurSel((m_Source.GetCount() > 0) ? 0 : -1);
        }
    }
}

// refresh the cine combo with the available cines from the source
void CPhDemoCPPDlg::RefreshCineCombo()
{
    int firstFlashCine;

	m_Cine.ResetContent();
	if (dynamic_cast<Camera*>(m_pSelectedSource) != NULL)
	{
		//populate the list with available cines
		Camera* selectedCamera = dynamic_cast<Camera*>(m_pSelectedSource);
		int selectedIndex = 0;
		//RAM cine partitions should not be added on the list for CineStation devices because they do not exist.
		if (selectedCamera->GetSupportsRecordingCines())
		{
			INT startCineNo = CINE_PREVIEW;
			INT lastCineNo = selectedCamera->GetPartitionCount();
            firstFlashCine = selectedCamera->GetFirstFlashCine();
            for (int iCine = startCineNo; iCine <= lastCineNo; iCine++)
			{
				CString cineStr;
                Cine::GetStringForCineNo(&cineStr, iCine, firstFlashCine);
				m_Cine.AddString(cineStr);
				if (iCine == selectedCamera->GetSelectedCinePartNo())
					selectedIndex = m_Cine.GetCount() - 1;
			}
		}

		INT lastFlashCineNo = selectedCamera->GetLastFlashCineNo();
        firstFlashCine = selectedCamera->GetFirstFlashCine();
        for (int iCine = firstFlashCine; iCine <= lastFlashCineNo; iCine++)
		{
			CString cineStr;
            Cine::GetStringForCineNo(&cineStr, iCine, firstFlashCine);
			m_Cine.AddString(cineStr);
			if (iCine == selectedCamera->GetSelectedCinePartNo())
				selectedIndex = m_Cine.GetCount() - 1;
		}
		if (m_Cine.GetCount() > 0)
			m_Cine.SetCurSel(selectedIndex);
	}
	else if (dynamic_cast<FileSource*>(m_pSelectedSource) != NULL)
	{
		if (m_pOpenedFile != NULL)
		{
			TCHAR filePath[MAX_PATH];
			FileSource* fs = dynamic_cast<FileSource*>(m_pSelectedSource);
			fs->GetFilePath(filePath, MAX_PATH);
			TCHAR fname[_MAX_FNAME];  
			_tsplitpath_s(filePath, NULL, 0, NULL, 0, fname, _MAX_FNAME, NULL, 0);
			m_Cine.AddString(fname);
			m_Cine.SetCurSel(0);
		}
	}
}

// Select the source from the selected combo item.
void CPhDemoCPPDlg::SelectSourceFromCombo()
{
    m_pSelectedSourceIndex = m_Source.GetCurSel();
    if (m_pSelectedSourceIndex >= 0)
	{
		CString selectedSourceStr;
		TCHAR src_str_buf[DEFAULT_STR_MAXSZ];
		m_Source.GetLBText(m_Source.GetCurSel(), src_str_buf);
		selectedSourceStr.Append(src_str_buf);
		if (selectedSourceStr.Compare(_T(FILE_SOURCE_NAME))==0)
		{
			m_pSelectedSource = dynamic_cast<ISource*>(m_pOpenedFile);
		}
		else
		{
			//parse camera serial from combo item. The camera serial is an unique ID
			int istart = selectedSourceStr.Find(_T("("))+1;
			int istop = selectedSourceStr.Find(_T(")"));
			CString serialStr = selectedSourceStr.Mid(istart, istop - istart);
			UINT serial = (UINT)_ttoi64(serialStr);
			//select the camera with serial
			m_pSelectedSource = m_pPoolRefresher->GetCameraAt(m_pPoolRefresher->GetCameraIndexForSerial(serial));
			RefreshPartitionCombo();
		}

		Camera* selCam  = dynamic_cast<Camera*>(m_pSelectedSource);
		//show/hide info button
		BOOL isCam = (selCam != NULL);
		if (isCam)
			m_Info.ShowWindow(SW_SHOW);
		else
			m_Info.ShowWindow(SW_HIDE);

		//show/hide camera settings
		BOOL settingsVisible = isCam && selCam->GetSupportsRecordingCines();
		if (settingsVisible)
		{	
			m_Part.ShowWindow(SW_SHOW);
			m_PartStr.ShowWindow(SW_SHOW);
			m_GCamSettings.ShowWindow(SW_SHOW);
		}
		else	
		{
			m_Part.ShowWindow(SW_HIDE);
			m_PartStr.ShowWindow(SW_HIDE);
			m_GCamSettings.ShowWindow(SW_HIDE);
		}

        //
        // Assume the Image Size has changed
        //
        m_pCinePlayer->m_UpdateImageSize = TRUE;
	}
}

// Populates partition combo with possible partitions numbers
void CPhDemoCPPDlg::RefreshPartitionCombo()
{
	m_Part.ResetContent();
	Camera* pSelectedCamera = dynamic_cast<Camera*>(m_pSelectedSource);
	if (pSelectedCamera!=NULL)
	{
		if (pSelectedCamera->GetSupportsRecordingCines())
		{
			//populate partitions combo up to the number of maximum partitions
			UINT maxPartCount = pSelectedCamera->GetMaxPartitionCount();
			if (maxPartCount <= 1)
			{
				m_Part.AddString(_T("1"));
				m_Part.SetCurSel(0);
				m_Part.EnableWindow(FALSE);
			}
			else
			{
				UINT partNo = pSelectedCamera->GetPartitionCount();
				int selectedIndex = 0;
				for (UINT i = 1; i < maxPartCount; i++)
				{
					TCHAR partStr[SMALL_STR_MAXSZ];
					_itot_s(i, partStr, SMALL_STR_MAXSZ, 10);
					m_Part.AddString(partStr);
					if (i == partNo)
						selectedIndex = i - 1;
				}
				m_Part.SetCurSel(selectedIndex);
			}
		}
	}
}

// Selects the cine from combo selected item.
void CPhDemoCPPDlg::SelectCineFromCombo()
{
	Camera* pSelCam  = dynamic_cast<Camera*>(m_pSelectedSource);
	if (pSelCam != NULL)
	{
        int firstFlashCine = pSelCam->GetFirstFlashCine();
        CString selectedItemStr;
		TCHAR str_buf[DEFAULT_STR_MAXSZ];
		m_Cine.GetLBText(m_Cine.GetCurSel(), str_buf);
		selectedItemStr.Append(str_buf);
        pSelCam->SetSelectedCinePartNo(Cine::ParseCineNo(&selectedItemStr, firstFlashCine));
		mLastSelectedCineStatus = pSelCam->GetCinePartitionStatus(pSelCam->GetSelectedCinePartNo());

		//if cine partition is empty
		if (!(mLastSelectedCineStatus.Stored || mLastSelectedCineStatus.Triggered))
			//make the selected empty partition active in camera (start recording)
			pSelCam->RecordSpecificCine(pSelCam->GetSelectedCinePartNo());
	}

	RefreshAcqParameters();
	RefreshPlayInterface();
	RefreshImProcessing();

    //
    // Assume Image Size has changed
    //
    m_pCinePlayer->m_UpdateImageSize = TRUE;
}

// Refreshes acquisition parameters
void CPhDemoCPPDlg::RefreshAcqParameters()
{
	Camera* pSelCam  = dynamic_cast<Camera*>(m_pSelectedSource);
	if (pSelCam!=NULL)
	{
		BOOL selPartIsStored = pSelCam->IsCinePartitionStored(pSelCam->GetSelectedCinePartNo());
		if (selPartIsStored)
		{
			RefreshAcquisitionParamtersStoredCine(pSelCam->CurrentCine());
		}
		else
		{
			RefreshAcquisitionParamtersNotStoredCine(pSelCam);
		}
	}
	else if (dynamic_cast<FileSource*>(m_pSelectedSource)!=NULL) 
	{	
		RefreshAcquisitionParamtersStoredCine(m_pSelectedSource->CurrentCine());
	}
}

// Refreshes acquisition parameters for cine partitions.
void CPhDemoCPPDlg::RefreshAcquisitionParamtersNotStoredCine(Camera* pCamera)
{
    RefreshAcquisitionUI_RW(FALSE);

	ACQUIPARAMS acquisitionParams;
	pCamera->GetAcquisitionParameters(pCamera->GetSelectedCinePartNo(), &acquisitionParams);

	//get the current acquisition resolution
	POINT currentResolution;
	currentResolution.x = acquisitionParams.ImWidth;
	currentResolution.y = acquisitionParams.ImHeight;
	CString currentResStr;
	GetResolutionStr(&currentResStr, &currentResolution);
	//update resolution combo
	m_Resolutions.ResetContent();
	POINT resolutions[MAX_RESOLUTIONS];
	UINT resolutionCount = MAX_RESOLUTIONS;
	pCamera->GetCameraResolutions(resolutions, &resolutionCount);
	//populate resolution combo
	INT selectedIndex = -1;
	for (INT ires = 0; ires < (INT)resolutionCount; ires++)
	{
		POINT res = resolutions[ires];
		CString resStr;
		GetResolutionStr(&resStr, &res);
		m_Resolutions.AddString(resStr);
		if (resStr.Compare(currentResStr)==0)
			selectedIndex = ires;
	}
	if (selectedIndex>=0)
		m_Resolutions.SetCurSel(selectedIndex);
	else
		m_Resolutions.SetWindowText(currentResStr);

	//update bitdepth combo
	m_BitDepth.ResetContent();
	UINT count;
	UINT bitDepths[20];
	//get available bitdepths
	pCamera->GetCameraBitDepths(&count, bitDepths);
	CAMERAOPTIONS camOptions;
	pCamera->GetCamOptions(&camOptions);
	UINT actualBitDepth = camOptions.RAMBitDepth;
	int selectedIndexBitDepth = 0;
	for (INT iBitDepth = 0; iBitDepth < (INT)count; iBitDepth++)
	{
		UINT bitDepth = bitDepths[iBitDepth];
		TCHAR bitDepthStr[SMALL_STR_MAXSZ];
		_itot_s((INT)bitDepth, bitDepthStr, SMALL_STR_MAXSZ, 10);
		m_BitDepth.AddString(bitDepthStr);
		if (bitDepth == actualBitDepth)
			selectedIndexBitDepth = iBitDepth;
	}
	m_BitDepth.SetCurSel(selectedIndexBitDepth);

	//refresh other parameters values

	CString parText;
    parText.Format(L"%.2f", (double)acquisitionParams.dFrameRate);
    m_FrameRate.SetWindowText(parText);

    parText.Format(L"%.2f", (double)acquisitionParams.Exposure / 1000.0);
	m_Exposure.SetWindowText(parText);

	parText.Empty();
    parText.Format(L"%.2f", (double)acquisitionParams.EDRExposure / 1000.0);
	m_EDRExp.SetWindowText(parText);

    parText.Format(L"%d", acquisitionParams.PTFrames);
    m_PTFrames.SetWindowText(parText);

    parText.Format(L"%d", acquisitionParams.ImCount);
    m_ImCount.SetWindowText(parText);

	INT delay = (acquisitionParams.PTFrames > acquisitionParams.ImCount) ? acquisitionParams.PTFrames - acquisitionParams.ImCount : 0;
    parText.Format(L"%d", delay);
    m_Delay.SetWindowText(parText);
}

// Refreshes acquisition parameters for Stored (recorded) cines (files or recorded cine partitions).
void CPhDemoCPPDlg::RefreshAcquisitionParamtersStoredCine(Cine* pCine)
{
    RefreshAcquisitionUI_RW(TRUE);

	m_Resolutions.ResetContent();
	//update resolution combo
	POINT currentResolution;
	currentResolution.x = pCine->GetImWidth();
	currentResolution.y = pCine->GetImHeight();
	CString currentResStr;
	GetResolutionStr(&currentResStr, &currentResolution);
	m_Resolutions.AddString(currentResStr);
	m_Resolutions.SetCurSel(0);

	//update bitdepth combo
	TCHAR bitDepthStr[SMALL_STR_MAXSZ];
	_itot_s((INT)pCine->GetBppReal(), bitDepthStr, SMALL_STR_MAXSZ, 10);
	m_BitDepth.ResetContent();
	m_BitDepth.AddString(bitDepthStr);
	m_BitDepth.SetCurSel(0);

	//update other parameters
	CString parText;

    parText.Format(L"%.2f", (double)pCine->GetFrameRate());
    m_FrameRate.SetWindowText(parText);

    parText.Format(L"%.2f", (double)pCine->GetExposure() / 1000.0);
	m_Exposure.SetWindowText(parText);

	parText.Empty();
    parText.Format(L"%.2f", (double)pCine->GetEDRExposureNs() / 1000.0);
	m_EDRExp.SetWindowText(parText);

    parText.Format(L"%d", pCine->GetPostTriggerFrames());
    m_PTFrames.SetWindowText(parText);

    parText.Format(L"%d", pCine->GetImageCount());
    m_ImCount.SetWindowText(parText);

    parText.Format(L"%d", pCine->GetTriggerDelay());
    m_Delay.SetWindowText(parText);
}

void CPhDemoCPPDlg::GetResolutionStr(CString* pResStr, PPOINT pResolution)
{
	pResStr->Empty();
	TCHAR width[SMALL_STR_MAXSZ];
	TCHAR height[SMALL_STR_MAXSZ];
	_itot_s(pResolution->x, width, SMALL_STR_MAXSZ, 10);
	_itot_s(pResolution->y, height, SMALL_STR_MAXSZ, 10);
	pResStr->Append(width);
	pResStr->Append(_T(" x "));
	pResStr->Append(height);
}

void CPhDemoCPPDlg::ParseResolution(CString* pResStr, PPOINT pResolution)
{
	INT sepIndex = pResStr->Find(_T("x"));
	CString width = pResStr->Mid(0, sepIndex - 1);
	CString height = pResStr->Mid(sepIndex + 1, pResStr->GetLength() - sepIndex - 1);
	pResolution->x = _ttoi(width);
	pResolution->y = _ttoi(height);
}

// Refresh ability to change properties depending on cine stored status.
void CPhDemoCPPDlg::RefreshAcquisitionUI_RW(BOOL isStored)
{
	m_Resolutions.EnableWindow(!isStored);
	m_BitDepth.EnableWindow(!isStored);
	m_FrameRate.SetReadOnly(isStored);
	m_Exposure.SetReadOnly(isStored);
	m_EDRExp.SetReadOnly(isStored);
	m_PTFrames.SetReadOnly(isStored);

	m_SetAcq.EnableWindow(!isStored);
}

// Refreshes image processing options for selected cine.
void CPhDemoCPPDlg::RefreshImProcessing()
{
	Cine* pCine = NULL;
	if (m_pSelectedSource != NULL)
	{
		pCine = m_pSelectedSource->CurrentCine();
	}
	if (pCine == NULL)
		return;

	CString paramText;
    paramText.Format(L"%.2f", pCine->GetBrightness());
	m_Bright.SetWindowText(paramText);
	paramText.Empty();
    paramText.Format(L"%.2f", pCine->GetContrast());
	m_Gain.SetWindowText(paramText);
	paramText.Empty();
    paramText.Format(L"%.2f", pCine->GetGamma());
	m_Gamma.SetWindowText(paramText);
	paramText.Empty();
    paramText.Format(L"%.2f", pCine->GetSaturation());
	m_Saturation.SetWindowText(paramText);
	paramText.Empty();
    paramText.Format(L"%.2f", pCine->GetHue());
	m_Hue.SetWindowText(paramText);

	WBGAIN wbg;
	pCine->GetWhiteBalanceGain(&wbg);
	paramText.Empty();
    paramText.Format(L"%.2f", wbg.R);
	m_WBRed.SetWindowText(paramText);
	paramText.Empty();
    paramText.Format(L"%.2f", wbg.B);
	m_WBBlue.SetWindowText(paramText);
}

void CPhDemoCPPDlg::RefreshPlayInterface()
{
	if (m_pSelectedSource != NULL)
	{
		m_pCinePlayer->SetCurrentCine(m_pSelectedSource->CurrentCine());
	}
}

// Refresh ability to change image processing options depending on image color status.
void CPhDemoCPPDlg::RefreshColorDependentControls(BOOL isColorImage)
{
	m_Saturation.EnableWindow(isColorImage);
	m_Hue.EnableWindow(isColorImage);
	m_WBRed.EnableWindow(isColorImage);
	m_WBBlue.EnableWindow(isColorImage);
}

// Refresh availability of record actions.
void CPhDemoCPPDlg::RefreshRecordActions(CameraStatus camStatus)
{
	if (camStatus == ::Preview)
	{
		m_Capture.EnableWindow(TRUE);
		m_Trigger.EnableWindow(FALSE);
	}
	else if (camStatus == ::RecWaitingForTrigger)
	{
		m_Capture.EnableWindow(FALSE);
		m_Trigger.EnableWindow(TRUE);
	}
	else if (camStatus == ::RecPostriggerFrames || camStatus == ::NotAvailable)
	{
		m_Capture.EnableWindow(FALSE);
		m_Trigger.EnableWindow(FALSE);
	}
}

//refresh UI visibility depending on cine save status
void CPhDemoCPPDlg::OnCineSave(BOOL started)
{
	m_OpenCine.EnableWindow(!started);
	m_SaveCine.EnableWindow(!started);
	int cmdShow = started?SW_SHOW:SW_HIDE;
	m_Progress.ShowWindow(cmdShow);
	m_SaveStatus.ShowWindow(cmdShow);
}
#pragma endregion

#pragma region SetParameters
// Set the acquisition parameters and other options into camera for selected cine partition.
void CPhDemoCPPDlg::SetAcquisitionParams()
{
    BOOL ResolutionChanged = FALSE;

	Camera* pSelCam  = dynamic_cast<Camera*>(m_pSelectedSource);
	if (pSelCam!=NULL && !pSelCam->IsCinePartitionStored(pSelCam->GetSelectedCinePartNo()))
	{
		CAMERAOPTIONS camOptions;
		pSelCam->GetCamOptions(&camOptions);
		TCHAR bitDepthStr[SMALL_STR_MAXSZ];
		m_BitDepth.GetLBText(m_BitDepth.GetCurSel(), bitDepthStr);
		camOptions.RAMBitDepth = _ttoi(bitDepthStr);
		pSelCam->SetCamOptions(&camOptions);

		ACQUIPARAMS acqParams;
		pSelCam->GetAcquisitionParameters(pSelCam->GetSelectedCinePartNo(), &acqParams);
		//set resolution
		CString resStr;
		POINT resolution;
		m_Resolutions.GetLBText(m_Resolutions.GetCurSel(), resStr);
		ParseResolution(&resStr, &resolution); 

        //
        // See if the Resolution has changed
        // if so clear the Display
        //
        if ((acqParams.ImWidth != resolution.x) || (acqParams.ImHeight != resolution.y))
        {
            ResolutionChanged = TRUE;
        }
		acqParams.ImWidth = resolution.x;
		acqParams.ImHeight = resolution.y;

		CString parText;
		m_FrameRate.GetWindowText(parText);
		acqParams.dFrameRate = (double)_ttof(parText);
		m_Exposure.GetWindowText(parText);
		acqParams.Exposure = (UINT)_tstof(parText)*1000;//ns
		m_EDRExp.GetWindowText(parText);
		acqParams.EDRExposure = (UINT)_tstof(parText)*1000;//ns
		m_PTFrames.GetWindowText(parText);
		acqParams.PTFrames = (UINT)_ttoi64(parText);

		pSelCam->SetAcquisitionParameters(pSelCam->GetSelectedCinePartNo(), &acqParams);

        if (ResolutionChanged == TRUE)
        {
            //
            // Assume the Image Size has changed
            //
            m_pCinePlayer->m_UpdateImageSize = TRUE;
        }
	}
}

// Set image processing for selected cine. Selected cine might be the live cine.
void CPhDemoCPPDlg::SetImProcessing()
{
	Cine* pCine = NULL;
	if (m_pSelectedSource!=NULL)
	{
		pCine = m_pSelectedSource->CurrentCine();
	}
	if (pCine == NULL)
		return;

	CString parText;
	m_Bright.GetWindowText(parText);
	pCine->SetBrightness((FLOAT)_tstof(parText));
	m_Gain.GetWindowText(parText);
	pCine->SetContrast((FLOAT)_tstof(parText));
	m_Gamma.GetWindowText(parText);
	pCine->SetGamma((FLOAT)_tstof(parText));

	if (m_pCinePlayer->IsColorImage())
	{
		m_Saturation.GetWindowText(parText);
		pCine->SetSaturation((FLOAT)_tstof(parText));
		m_Hue.GetWindowText(parText);
		pCine->SetHue((FLOAT)_tstof(parText));

		WBGAIN wbg;
		pCine->GetWhiteBalanceGain(&wbg);
		m_WBRed.GetWindowText(parText);
		wbg.R = (FLOAT)_tstof(parText);
		m_WBBlue.GetWindowText(parText);
		wbg.B = (FLOAT)_tstof(parText);
		pCine->SetWhiteBalanceGain(&wbg);
	}
}

// Set the number of partitions from partition combo
void CPhDemoCPPDlg::SetPartitionFromCombo()
{
	Camera* pSelCam = dynamic_cast<Camera*>(m_pSelectedSource);
	if (pSelCam!=NULL)
	{
		if (pSelCam->HasStoredRAMPart() || ShowDeleteAllCinesMessage())
		{
			CString parText;
			m_Part.GetWindowText(parText);
			pSelCam->SetPartitionCount((UINT)_ttoi64(parText));
			pSelCam->DestroySelectedCine();
			RefreshCineCombo();
			SelectCineFromCombo();
		}
		else
		{
			RefreshPartitionCombo();
		}

        //
        // Assume the Image Size has changed
        //
        m_pCinePlayer->m_UpdateImageSize = TRUE;
	}
}
#pragma endregion

#pragma region Actions
// Send record command to selected camera.
void CPhDemoCPPDlg::Record()
{
	Camera* pSelCam = dynamic_cast<Camera*>(m_pSelectedSource);
	if (pSelCam!=NULL)
	{
		INT cineToCapture = pSelCam->GetSelectedCinePartNo();
		//delete all cine partitions and send record command 
		if (cineToCapture == CINE_PREVIEW)
		{
			if (!pSelCam->HasStoredRAMPart() || ShowDeleteAllCinesMessage())
				pSelCam->Record();
		}
		else
		{

			if (pSelCam->IsCinePartitionStored(cineToCapture)
				&& IDNO == AfxMessageBox(_T("Stored cine will be deleted in order to be recorded. Continue?"), MB_YESNO))
				return;
			//record to specific cine partition
			pSelCam->RecordSpecificCine(cineToCapture);
		}
	}
}

// Send software trigger command to selected camera.
void CPhDemoCPPDlg::SendTrigger()
{
	Camera* pSelCam = dynamic_cast<Camera*>(m_pSelectedSource);
	if (pSelCam!=NULL)
	{
		pSelCam->SendSoftwareTrigger();
	}
}

void CPhDemoCPPDlg::OpenFileCine()
{
	StopRefreshTimer();

	char cineFilePath[MAX_PATH];
	//show the open cine dialog
	if (PhGetOpenCineName(cineFilePath, 0))
	{
		if (_access(cineFilePath, 0) == 0)//if file exist
		{
			if (m_pOpenedFile != NULL)
			{
				delete m_pOpenedFile;
				m_pOpenedFile = NULL;
			}
			m_pOpenedFile = new FileSource(cineFilePath);

			m_pSelectedSource = m_pOpenedFile;
			RefreshSourceCombo();

			SelectSourceFromCombo();
			RefreshCineCombo();
			SelectCineFromCombo();

            //
            // Assume the Image Size has changed
            //
            m_pCinePlayer->m_UpdateImageSize = TRUE;
		}
	}

	StartRefreshTimer();
}

/// Start the saving of a cine.
void CPhDemoCPPDlg::StartSaveCine()
{
	StopRefreshTimer();

	if (!CineSaver::IsStarted())
	{
		Cine *pSelectedCine = NULL;
		//Get the selected stored cine. 
		//We need a duplicate because a cine cannot be used to play images and save images at same time.
		if (m_pSelectedSource != NULL)
		{
			//in the case of live images pSelectedCine will be NULL
			pSelectedCine = m_pSelectedSource->CurrentCine();
			if (pSelectedCine->IsLive())
				pSelectedCine = NULL;
		}

		if (pSelectedCine != NULL)
		{
			CineSaver::SetCine(pSelectedCine);
			if (CineSaver::ShowGetCineNameDialog())
			{
				//cine name selection terminated witk OK
				if (CineSaver::StartSave())
					OnCineSave(CineSaver::IsStarted());
				else
				{
					CineSaver::DestroyCine();//destroy the duplicate
					AfxMessageBox(_T("Error while trying to save cine"));
				}
			}
			else
				CineSaver::DestroyCine();//destroy the duplicate
		}
		else
		{
			AfxMessageBox(_T("Not a suitable cine to save."));
		}
	}

	StartRefreshTimer();
}
#pragma endregion

#pragma region Utils
BOOL CPhDemoCPPDlg::ShowDeleteAllCinesMessage()
{
	return AfxMessageBox(_T("All stored cines will be deleted. Continue?"), MB_YESNO) == IDYES;
}

/// Print the status from the camera.
void CPhDemoCPPDlg::PrintCameraStatus(CameraStatus status, INT activePart, CString* camSatusStr)
{
	camSatusStr->Empty();
	switch (status)
	{
	case ::Preview:
		camSatusStr->Append(_T(PREVIEW_CINE_NAME));
		break;
	case ::RecPostriggerFrames:
		camSatusStr->Format(L"Recording in cine partition %d postrigger frames", activePart);
		break;
	case ::RecWaitingForTrigger:
		camSatusStr->Format(L"Recording in cine partition %d, waiting for trigger", activePart);
		break;
	default:
		camSatusStr->Empty();
		break;
	}
}

void CPhDemoCPPDlg::StartRefreshTimer()
{
    refreshTimer = SetTimer(ID_REFRESH, REFRESH_TIMER_INTERVAL, NULL);
}

void CPhDemoCPPDlg::StopRefreshTimer()
{
	KillTimer(refreshTimer);
}

void CPhDemoCPPDlg::ExitApp()
{
	ASSERT(AfxGetApp()->m_pMainWnd != NULL);
	AfxGetApp()->m_pMainWnd->SendMessage(WM_CLOSE);
}
#pragma endregion

#pragma region UI Mesage handlers
void CPhDemoCPPDlg::OnCbnSelendokSource()
{
	SelectSourceFromCombo();
	RefreshCineCombo();
	SelectCineFromCombo();
}

void CPhDemoCPPDlg::OnCbnSelendokCine()
{
	SelectCineFromCombo();
}

void CPhDemoCPPDlg::OnBnClickedSetacq()
{
	SetAcquisitionParams();

	//feedback accepted value
	RefreshAcqParameters();
}

void CPhDemoCPPDlg::OnBnClickedSetImproc()
{
	SetImProcessing();

	//feedback accepted value
	RefreshImProcessing();
	m_pCinePlayer->RefreshImageBuffer();
}

void CPhDemoCPPDlg::OnCbnSelendokPart()
{
	SetPartitionFromCombo();
}

void CPhDemoCPPDlg::OnBnClickedCapture()
{
	Record();
}

void CPhDemoCPPDlg::OnBnClickedTrigger()
{
	SendTrigger();
}

void CPhDemoCPPDlg::OnBnClickedPlay()
{
	if (m_pCinePlayer->IsPlaying())
		m_pCinePlayer->StopPlay();
	else
		m_pCinePlayer->StartPlay();
}

void CPhDemoCPPDlg::OnBnClickedOpenCine()
{
	OpenFileCine();
}

void CPhDemoCPPDlg::OnBnClickedSaveCine()
{
	StartSaveCine();
}

void CPhDemoCPPDlg::OnBnClickedInfo()
{
	StopRefreshTimer();

	Camera* pSelCam  = dynamic_cast<Camera*>(m_pSelectedSource);
	if (pSelCam!=NULL)
	{
		CCameraInfoDlg *pCamInfoDlg = new CCameraInfoDlg(this, pSelCam);
		pCamInfoDlg->DoModal();
		delete pCamInfoDlg;
		pCamInfoDlg = NULL;
	}

	StartRefreshTimer();
}

void CPhDemoCPPDlg::OnHScroll(UINT nSBCode, UINT nPos, CScrollBar* pScrollBar)
{
	if (pScrollBar != NULL && pScrollBar->GetDlgCtrlID() == IDC_FRAMER )
	{
		UpdateData(TRUE);
		//play slider position changed
		INT frame = m_Framer.GetPos();
		m_pCinePlayer->SetCurrentFrame(frame);

		m_pCinePlayer->RefreshImageBuffer();
	}
	else
		CDialog::OnHScroll(nSBCode, nPos, pScrollBar);
}
#pragma endregion

#pragma endregion


void CPhDemoCPPDlg::OnBnClickedSignals()
{
	Camera* pSelCam = dynamic_cast<Camera*>(m_pSelectedSource);
	if (pSelCam != NULL)
	{
		pSelCam->SignalsSetup();
	}
}
