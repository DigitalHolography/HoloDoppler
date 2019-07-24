
// PhSimpleDemoDlg.h : header file
//

#pragma once
#include "DemoHead.h"
#include "CPictureBox.h"
#include "afxwin.h"

#define ID_REFRESH_TIMER	        1000
#define ID_CAMERA_POOL_TIMER	    1001
#define UPDATE_RATE                 10      // update dialog every 10 refresh ticks;

#define REFRESH_TIMER_INTERVAL      100
#define CAMERA_POOL_TIMER_INTERVAL  3000
#define MAX_RESOLUTIONS             100

// CPhSimpleDemoDlg dialog
class CPhSimpleDemoDlg : public CDialog
{
// Construction
public:
	CPhSimpleDemoDlg(CWnd* pParent = NULL);	// standard constructor


// Dialog Data
	enum { IDD = IDD_PHSIMPLEDEMOCPP_DIALOG };

    CStatic		m_OfflineLabel;
    CStatic		m_LiveLabel;
    CStatic		m_RecordingLabel;
    CStatic		m_TriggeredLabel;
    CStatic		m_PlaybackLabel;

    CComboBox	m_CameraComboBox;
    CComboBox	m_ResComboBox;

    CButton		m_recordButton;
    CButton		m_TriggerButton;
    CButton		m_PlaybackButton;
    CButton		m_SetButton;
    CButton		m_PauseButton;
    CButton		m_StopButton;
    CButton		m_SaveButton;

    CEdit		m_IpAddrEditBox;
    CEdit		m_SerialNumEditBox;
    CEdit		m_CameraNameEditBox;
    CEdit		m_ModelEditBox;
    CEdit		m_ExpEditBox;
    CEdit		m_FrameRateEditBox;

    CStatic		m_SaveCineToFileLabel;


    CEdit		m_FirstImageEditBox;
    CEdit		m_CurrentImageEditBox;
    CEdit		m_LastImageEditBox;

    CProgressCtrl	m_SaveProgressBar;
    CPictureBox     m_ImagePictureBox;

	protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV support
    virtual BOOL PreTranslateMessage(MSG* pMsg);

private:
    UINT_PTR			m_RefreshTimer;
    UINT_PTR			m_CameraPoolTimer;

    //
    // handle max cameras
    //
    CAMERAID m_CamId[MAXCAMERACNT];               // max number of possible cameras
    UINT m_CameraCount;
    INT m_CurrentCamera;
    BOOL m_Offline;
    BOOL m_PlaybackActive;
    BOOL m_WarningMessageShown[MAXCAMERACNT];     // max number of possible cameras
    BOOL m_SaveInProgress;
    BOOL m_ClearImageDisplay;

    INT m_DialogUpdateTick;
    UINT m_MaxImageSizeInBytes;
    UINT m_ImageSizeInBytes;
    INT m_CurrentImage;                           // used for Stored cine playback
    UINT m_CurrentPercent;

    BOOL m_PauseCheck;
    CINEHANDLE m_LiveCineHandle;
    CINEHANDLE m_StoredCineHandle;
    CINEHANDLE m_SaveCineHandle;
    IMRANGE m_ImageRange;
    IMRANGE m_StoredImageRange;                 // used for stored cine
    ACQUIPARAMS m_AcquiParams;
    

// Implementation
protected:
	HICON m_hIcon;

	// Generated message map functions
	virtual BOOL OnInitDialog();
    afx_msg void OnTimer(UINT_PTR nIDEvent);
    afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	DECLARE_MESSAGE_MAP()
public:
    afx_msg void OnBnClickedRecordButton();
    afx_msg void OnBnClickedTriggerButton();
    afx_msg void OnBnClickedPlaybackModeButton();
    afx_msg void OnBnClickedPauseButton();
    afx_msg void OnBnClickedStopButton();
    afx_msg void OnBnClickedSaveButton();
    afx_msg void OnCbnSelchangeCameraCombo();
    afx_msg void OnBnClickedSetButton();
    afx_msg void OnDestroy();


    void SimpleDemo_FormClosing();
    void UpdateCameraControls();
    void UpdateCineStatus(PCINESTATUS pCinestatus);
    UINT IpFromString(CString ip);
    void UpdateCameraPool(void);
    void SetImageBufferSize(CINEHANDLE CineHandle);
    void RefreshTimerTick(void);
    void Ip2text(UINT ip, CString* Text);
    void UpdateCineSaveProgressInfo(UINT Percent);
    int ResComboBox_Ctrl();
    int ExpEditBox_Ctrl();
    int FrameRateEditBox_Ctrl();
    static BOOL WINAPI SaveCineProgressChanged(UINT Percent, CINEHANDLE CineHandle);
    void SetPauseButton(BOOL State);
};
