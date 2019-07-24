#pragma once
#include "Camera.h"

// CCameraInfoDlg dialog
// A dialog where camera info is shown.
class CCameraInfoDlg : public CDialog
{
	DECLARE_DYNAMIC(CCameraInfoDlg)

private:
	Camera *m_pAttachedCamera;

	//controls
	CEdit m_Name;
	CString m_NameStr;
	CString m_IP;
	UINT m_Serial;
	UINT m_Version;
	CString m_Model;
	UINT m_Firmware;

public:
	CCameraInfoDlg(CWnd* pParent = NULL, Camera *pCam = NULL);   // standard constructor
	virtual ~CCameraInfoDlg();


// Dialog Data
	enum { IDD = IDD_CAMINFO_DIALOG };

protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV support

	DECLARE_MESSAGE_MAP()
public:
	afx_msg void OnBnClickedOk();
	afx_msg void OnEnKillfocusName();
	afx_msg int OnCreate(LPCREATESTRUCT lpCreateStruct);
};
