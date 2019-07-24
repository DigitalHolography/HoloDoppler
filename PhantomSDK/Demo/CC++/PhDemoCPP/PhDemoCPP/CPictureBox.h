#pragma once
#include "afxwin.h"
#include "DemoHead.h"

//Class used to display a image buffer
class CPictureBox :
	public CStatic
{
private:
	UINT m_BufferSize;
	PBYTE m_pImageBuffer;
	UINT m_BMISize;
	BITMAPINFO *m_pBMI;
    BOOL m_ClearImageDisplay;

public:
	CPictureBox(void);
	~CPictureBox(void);

	PBYTE GetImageBufferPtr();
	void SetImageBufferSize(UINT imgSizeInBytes);
	void SetBMIH(PBITMAPINFOHEADER pBMIH);
    void ClearPictureBox();

protected:
	afx_msg void OnPaint();

	DECLARE_MESSAGE_MAP()
};
