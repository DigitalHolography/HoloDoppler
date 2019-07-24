#include "StdAfx.h"
#include "CPictureBox.h"

BEGIN_MESSAGE_MAP(CPictureBox, CStatic)
	ON_WM_PAINT()
END_MESSAGE_MAP()

CPictureBox::CPictureBox(void)
{
	m_pImageBuffer = NULL;
    m_ClearImageDisplay = FALSE; 
	//we will use a maximum of 256 levels of gray for 8bpp bw images that we display
	m_BMISize = sizeof(BITMAPINFOHEADER) + PALETTE_SZ_GRAY * sizeof(RGBQUAD);
	m_pBMI = (PBITMAPINFO)malloc(m_BMISize);

	//generate gray pallete to be used with bw 8bpp images here. They will be used when gray images are displayed.
	RGBQUAD *pRGB = (RGBQUAD*)((PBYTE)m_pBMI + sizeof(BITMAPINFOHEADER));
	for (INT i = 0; i < PALETTE_SZ_GRAY; i++)
	{
		pRGB[i].rgbRed   = (BYTE)i;
		pRGB[i].rgbGreen = (BYTE)i;
		pRGB[i].rgbBlue  = (BYTE)i;
		pRGB[i].rgbReserved = (BYTE)0;
	}
}

CPictureBox::~CPictureBox(void)
{
	if (m_pImageBuffer!=NULL)
	{
		_aligned_free(m_pImageBuffer);
		m_pImageBuffer = NULL;
	}
	free(m_pBMI);
}

PBYTE CPictureBox::GetImageBufferPtr()
{
	return m_pImageBuffer;
}

//alocate image buffer
void CPictureBox::SetImageBufferSize(UINT imgSizeInBytes)
{
    if (imgSizeInBytes != m_BufferSize)
    {
        //
        // must be a new camera so clear the whole display first
        //
        ClearPictureBox();
    }

	if (imgSizeInBytes != m_BufferSize || m_pImageBuffer!=NULL)
	{
		//free old buffer
		if (m_pImageBuffer!=NULL)
		{
			_aligned_free(m_pImageBuffer);
			m_pImageBuffer = NULL;
		}
		m_pImageBuffer = (PBYTE)_aligned_malloc(imgSizeInBytes, 16);//aligned to 16b to help SSE code from PhFile
		m_BufferSize = imgSizeInBytes;
	}
}

void CPictureBox::ClearPictureBox()
{
    m_ClearImageDisplay = TRUE;
    Invalidate(TRUE);
}

void CPictureBox::SetBMIH(PBITMAPINFOHEADER pBMIH)
{
	memcpy(&m_pBMI->bmiHeader, pBMIH, sizeof(BITMAPINFOHEADER));
}

void CPictureBox::OnPaint() 
{
	CPaintDC dc(this); // device context for painting

	CRect clientRect;	
	GetClientRect(&clientRect);

    if (m_pImageBuffer == NULL)
	{
		dc.FillSolidRect(&clientRect, COLOR_BACKGROUND);

        //CStatic::OnPaint();
		return;
	}

	CMemDC mdc(dc, &clientRect);//double buffering

	LONG clientWidth = (clientRect.right - clientRect.left);
	LONG clientHeight = (clientRect.bottom - clientRect.top);

	FLOAT zoomFit = min(clientWidth/(FLOAT)m_pBMI->bmiHeader.biWidth, clientHeight/(FLOAT)m_pBMI->bmiHeader.biHeight);

	CRect previewRect;
    if (m_ClearImageDisplay == TRUE)
    {
        //
        // must be a new camera so clear the whole display first
        //
        m_ClearImageDisplay = FALSE;
        previewRect.left = 0;
        previewRect.right = clientWidth;
        previewRect.top = 0;
        previewRect.bottom = clientHeight;
        memset(m_pImageBuffer, 0xF0, m_BufferSize);
    }
    else
    {
        previewRect.left = (LONG)((FLOAT)clientWidth - (FLOAT)m_pBMI->bmiHeader.biWidth * zoomFit) / 2;
        previewRect.right = (LONG)(previewRect.left + (FLOAT)m_pBMI->bmiHeader.biWidth * zoomFit);
        previewRect.top = (LONG)((FLOAT)clientHeight - (FLOAT)m_pBMI->bmiHeader.biHeight * zoomFit) / 2;
        previewRect.bottom = (LONG)(previewRect.top + (FLOAT)m_pBMI->bmiHeader.biHeight * zoomFit);
    }


	mdc.GetDC().SetStretchBltMode(COLORONCOLOR);
	mdc.GetDC().SetMapMode(MM_TEXT);
	int ret = ::StretchDIBits(mdc.GetDC().GetSafeHdc(), 
		previewRect.left, 
		previewRect.top,
		previewRect.right - previewRect.left,
		previewRect.bottom - previewRect.top, 
		0, 
		0, 
		m_pBMI->bmiHeader.biWidth, 
		m_pBMI->bmiHeader.biHeight,
		m_pImageBuffer,
		m_pBMI,
		DIB_RGB_COLORS,
		SRCCOPY);

	//CStatic::OnPaint();
}
