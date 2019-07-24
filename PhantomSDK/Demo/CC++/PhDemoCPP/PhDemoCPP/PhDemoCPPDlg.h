
// PhDemoCPPDlg.h : header file
//

#pragma once
#include "Resource.h"

#include "DemoHead.h"

#include "PoolBuilder.h"
#include "PoolRefresher.h"
#include "Camera.h"
#include "FileSource.h"
#include "ISource.h"
#include "CineSaver.h"
#include "CinePlayer.h"

#include "CPictureBox.h"
#include "CameraInfoDlg.h"
#include "afxwin.h"

#define ID_REFRESH	1000

#define FILE_SOURCE_NAME "File"
#define REFRESH_TIMER_INTERVAL 30

//
// check for new cameras every 5 seconds
//
#define REFRESH_CAMERA_POOL_INTERVAL    5000/REFRESH_TIMER_INTERVAL
#define MAX_RESOLUTIONS                 100

// CPhDemoCPPDlg dialog
class CPhDemoCPPDlg : public CDialog
{
	// Construction
public:
	CPhDemoCPPDlg(CWnd* pParent = NULL);	// standard constructor

	// Dialog Data
	enum { IDD = IDD_PHDEMOCPP_DIALOG };

	//Top
	CComboBox	m_Source;
	CButton		m_Info;
	CComboBox	m_Cine;
	CButton		m_Capture;
	CButton		m_Trigger;
	CButton		m_OpenCine;
	CButton		m_SaveCine;

	//Right
	CComboBox	m_Part;
	CStatic		m_PartStr;
	CStatic		m_GCamSettings;

	//Acquisition
	CComboBox	m_Resolutions;
	CComboBox	m_BitDepth;
	CEdit 		m_FrameRate;
	CEdit 		m_Exposure;
	CEdit 		m_EDRExp;
	CEdit 		m_PTFrames;
	CEdit 		m_ImCount;
	CEdit 		m_Delay;
	CButton		m_SetAcq;

	//ImProcessing
	CEdit		m_Bright;
	CEdit		m_Gain;
	CEdit		m_Gamma;
	CEdit		m_Saturation;
	CEdit		m_Hue;
	CEdit		m_WBRed;
	CEdit		m_WBBlue;
	CButton		m_SetImProc;

	//CinePlayer
	CPictureBox	m_PreviewBox;
	CButton		m_BtnPlay;
	CSliderCtrl	m_Framer;
	CStatic		m_FirstIm;
	CStatic		m_LastIm;
	CEdit		m_CrtFr;

	//Bottom
	CStatic		m_RefreshSpeed;
	CStatic		m_CamStatus;

	CStatic		m_SaveStatus;
	CProgressCtrl	m_Progress;

protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV support

private:
	PoolBuilder*		m_pPoolBuilder;
	PoolRefresher*		m_pPoolRefresher;
	CinePlayer*			m_pCinePlayer;

	//the current selected source
	ISource*			m_pSelectedSource;
    INT                 m_pSelectedSourceIndex;;
	//the current opened file
	FileSource*			m_pOpenedFile;

	//refresh frequency members
	LARGE_INTEGER		liStart;
	LARGE_INTEGER		liStop;

	CINESTATUS			mLastSelectedCineStatus;
	UINT_PTR			refreshTimer;
    UINT                cameraPoolRefreshTimer;

private:
	void InitPhDemo();
	void StopPhDemo();

	void RefreshSourceAndCine();

	// Refresh the soruce combo with avaialble cameras, add file selection
	void RefreshSourceCombo();
	// Refresh the cine combo with the available cines from the source
	void RefreshCineCombo();
	// Select the source from the selected combo item.
	void SelectSourceFromCombo();

	// Populates partition combo with possible partitions numbers
	void RefreshPartitionCombo();
	// Selects the cine from combo selected item.
	void SelectCineFromCombo();
	// Refreshes acquisition parameters
	void RefreshAcqParameters();
	// Refreshes acquisition parameters for cine partitions.
	void RefreshAcquisitionParamtersNotStoredCine(Camera* pSelCamera);
	// Refreshes acquisition parameters for Stored (recorded) cines (files or recorded cine partitions).
	void RefreshAcquisitionParamtersStoredCine(Cine* pCine);
	void GetResolutionStr(CString* pResStr, PPOINT pResolution);
	void ParseResolution(CString* pResStr, PPOINT pResolution);
	// Refresh ability to change properties depending on cine stored status.
	void RefreshAcquisitionUI_RW(BOOL isStored);
	// Refreshes image processing options for selected cine.
	void RefreshImProcessing();
	void RefreshPlayInterface();
	// Refresh ability to change image processing options depending on image color status.
	void RefreshColorDependentControls(BOOL isColorImage);
	// Refresh availability of record actions.
	void RefreshRecordActions(CameraStatus camStatus);
	// Set the acquisition parameters and other options into camera for selected cine partition.
	void SetAcquisitionParams();
	// Set image processing for selected cine. Selected cine might be the live cine.
	void SetImProcessing();
	// Set the number of partitions from partition combo
	void SetPartitionFromCombo();

    // check the camera pool for new cameras
    void RefreshCameraPool();

	// Send record command to selected camera.
	void Record();
	// Send software trigger command to selected camera.
	void SendTrigger();
	void OpenFileCine();
	void StartSaveCine();
	void OnCineSave(BOOL started);

	BOOL ShowDeleteAllCinesMessage();
	void PrintCameraStatus(CameraStatus status, INT activePart, CString* camSatusStr);
	void StartRefreshTimer();
	void StopRefreshTimer();
	void ExitApp(void);

	// Implementation
protected:
	HICON m_hIcon;

	// Generated message map functions
	virtual BOOL OnInitDialog();
    afx_msg void OnSysCommand(UINT nID, LPARAM lParam);
	afx_msg void OnTimer(UINT_PTR nIDEvent);
	afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	DECLARE_MESSAGE_MAP()

public:
	afx_msg void OnCbnSelendokSource();
	afx_msg void OnCbnSelendokCine();
	afx_msg void OnBnClickedSetacq();
	afx_msg void OnBnClickedSetImproc();
	afx_msg void OnCbnSelendokPart();
	afx_msg void OnDestroy();
	afx_msg void OnBnClickedCapture();
	afx_msg void OnBnClickedTrigger();
	afx_msg void OnBnClickedPlay();
	afx_msg void OnBnClickedOpenCine();
	afx_msg void OnBnClickedSaveCine();
	afx_msg void OnBnClickedInfo();
	afx_msg void OnHScroll(UINT nSBCode, UINT nPos, CScrollBar* pScrollBar);
	CButton m_Signals;
	afx_msg void OnBnClickedSignals();
	CStatic m_SigGrp;
	CStatic m_SigBin;
	CStatic m_SigAna;
};
