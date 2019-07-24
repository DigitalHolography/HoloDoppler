// CameraInfoDlg.cpp : implementation file
//

#include "stdafx.h"
#include "PhDemoCPP.h"
#include "CameraInfoDlg.h"


// CCameraInfoDlg dialog

IMPLEMENT_DYNAMIC(CCameraInfoDlg, CDialog)

CCameraInfoDlg::CCameraInfoDlg(CWnd* pParent /*=NULL*/, Camera *pCam /*= NULL*/)
: CDialog(CCameraInfoDlg::IDD, pParent)
{
	m_pAttachedCamera = pCam;

	m_NameStr.Empty();
	m_IP.Empty();
	m_Serial = 0;
	m_Version = 0;
	m_Model.Empty();
	m_Firmware = 0;

}

CCameraInfoDlg::~CCameraInfoDlg()
{
}

void CCameraInfoDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);

	DDX_Control(pDX, IDC_NAME, m_Name);
	DDX_Text(pDX, IDC_NAME, m_NameStr);
	DDX_Text(pDX, IDC_IP, m_IP);
	DDX_Text(pDX, IDC_SERIAL, m_Serial);
	DDX_Text(pDX, IDC_VERSION, m_Version);
	DDX_Text(pDX, IDC_MODEL, m_Model);
	DDX_Text(pDX, IDC_FIRMWARE, m_Firmware);
}

BEGIN_MESSAGE_MAP(CCameraInfoDlg, CDialog)
	ON_BN_CLICKED(IDOK, &CCameraInfoDlg::OnBnClickedOk)
	ON_EN_KILLFOCUS(IDC_NAME, &CCameraInfoDlg::OnEnKillfocusName)
	ON_WM_CREATE()
END_MESSAGE_MAP()


// CCameraInfoDlg message handlers

void CCameraInfoDlg::OnBnClickedOk()
{
	CString camNameStr;
	m_Name.GetWindowText(camNameStr);
	m_pAttachedCamera->SetCameraName(&camNameStr);

	OnOK();
}

void CCameraInfoDlg::OnEnKillfocusName()
{
	
}

int CCameraInfoDlg::OnCreate(LPCREATESTRUCT lpCreateStruct)
{
	if (CDialog::OnCreate(lpCreateStruct) == -1)
		return -1;

	if (m_pAttachedCamera!=NULL)
	{
		m_pAttachedCamera->GetCameraName(&m_NameStr);
		m_pAttachedCamera->GetIPAddress(&m_IP);
		m_Serial = m_pAttachedCamera->GetCameraSerial();
		m_Version = m_pAttachedCamera->GetCameraVersion();
		m_pAttachedCamera->GetCameraModel(&m_Model);
		m_Firmware = m_pAttachedCamera->GetFirmwareVersion();
	}

	return 0;
}
