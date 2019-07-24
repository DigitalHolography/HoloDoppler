#include "StdAfx.h"
#include "CinePlayer.h"

CinePlayer::CinePlayer(CPictureBox *pictureBox, CButton *buttonPlay, CSliderCtrl *playSlider, CEdit *frameTextBox, CStatic *firstIm, CStatic *lastIm, CStatic *sigGrp, CStatic *sigBin, CStatic *sigAna)
{
	m_pPictureBox = pictureBox;
	m_pButtonPlay = buttonPlay;
	m_pPlaySlider = playSlider;
	m_pFrameTextBox = frameTextBox;
	m_pLbFirstIm = firstIm;
	m_pLbLastIm = lastIm;
	m_pSigGrp = sigGrp;
	m_pSigBin = sigBin;
	m_pSigAna = sigAna;
	m_pCurrentCine = NULL;
    mIsPlaying = FALSE;
    m_UpdateImageSize = TRUE;
    m_ImgSizeInBytes = 0;
}

CinePlayer::~CinePlayer(void)
{
	m_pCurrentCine = NULL;
}

BOOL CinePlayer::IsPlaying()
{
	return mIsPlaying;
}

BOOL CinePlayer::IsColorImage()
{
	return mIsColorImage;
}

void CinePlayer::SetCurrentCine(Cine *pCine)
{
    BOOL StartCinePlayback = FALSE;

	m_pCurrentCine = pCine;
	if (m_pCurrentCine!=NULL)
	{
		if (m_pCurrentCine->IsLive())
		{
			InitPlayRange(0, 0);//live cine has no image range, always take image 0
			StartPlay();//always show live images
		}
		else
		{
			InitPlayRange(m_pCurrentCine->GetFirstImageNumber(), m_pCurrentCine->GetLastImageNumber());
            StartCinePlayback = TRUE;
		}

		//GetCineImage image flip is inhibited.
		m_pCurrentCine->SetVFlipView(FALSE);
		RefreshImageBuffer();
	}
	else
	{
		StopPlay();
	}
	UpdatePlayUIVisibility();
    if (StartCinePlayback == TRUE)
    {
        StartPlay();
    }
}

void CinePlayer::SetCurrentFrame(INT value)
{
	mCurrentFrame = value;
	m_pPlaySlider->SetPos(value);
	
	CString textVal;
	textVal.Format(L"%d", value);
	m_pFrameTextBox->SetWindowText(textVal);


	textVal.Empty();
	m_pCurrentCine->PrintBinSig(&textVal, mCurrentFrame);
	m_pSigBin->SetWindowText(textVal);

	textVal.Empty();
	m_pCurrentCine->PrintAnaSig(&textVal, mCurrentFrame);
	m_pSigAna->SetWindowText(textVal);

}

void CinePlayer::RefreshLiveSignals()
{
	CString textVal;

	m_pCurrentCine->PrintSigInfo(&textVal);
	m_pSigGrp->SetWindowText(textVal);


	textVal.Empty();
	m_pCurrentCine->PrintBinSig(&textVal, 0);
	m_pSigBin->SetWindowText(textVal);

	textVal.Empty();
	m_pCurrentCine->PrintAnaSig(&textVal, 0);
	m_pSigAna->SetWindowText(textVal);


}


void CinePlayer::SetPlayRange(INT first, INT last)
{
	mFirstIm = first;
	mLastIm = last;
	m_pPlaySlider->SetRange(first, last);
	INT tickFr = (last - first)/10;
	tickFr = (tickFr>0) ? tickFr : 1;
	m_pPlaySlider->SetTicFreq(tickFr);

	CString textVal;
	textVal.Format(L"%d", first);
	m_pLbFirstIm->SetWindowText(textVal);

	textVal.Empty();
	textVal.Format(L"%d", last);
	m_pLbLastIm->SetWindowText(textVal);

	textVal.Empty();
	m_pCurrentCine->PrintSigInfo(&textVal);
	m_pSigGrp->SetWindowText(textVal);
}

void CinePlayer::InitPlayRange(INT first, INT last)
{
	StopPlay();

	SetPlayRange(first, last);
	SetCurrentFrame(first);
	m_pPlaySlider->UpdateWindow();
}

void CinePlayer::RefreshPlayButton()
{
	if (mIsPlaying)
		m_pButtonPlay->SetWindowText(_T("Stop"));
	else
		m_pButtonPlay->SetWindowText(_T("Play"));
}

void CinePlayer::NextFrame()
{
	if(m_pCurrentCine == NULL || m_pCurrentCine->IsLive())
		return;

	INT crtFrame;
	if (mCurrentFrame == mLastIm)
		crtFrame = mFirstIm;
	else
		crtFrame = mCurrentFrame+1;
	SetCurrentFrame(crtFrame);
}

void CinePlayer::ReduceTo8bpp(FLOAT sensitivity, PIH pImgHeader)
{
	REDUCE16TO8PARAMS reduceOption;
	reduceOption.fGain16_8 = sensitivity;
	PhProcessImage(m_pPictureBox->GetImageBufferPtr(), m_pPictureBox->GetImageBufferPtr(), pImgHeader, IMG_PROC_REDUCE16TO8, &reduceOption);
}

void CinePlayer::StartPlay()
{
    mIsPlaying = TRUE;
	RefreshPlayButton();
}

void CinePlayer::StopPlay()
{
    mIsPlaying = FALSE;
	RefreshPlayButton();
}

void CinePlayer::PlayNextImage()
{
	if(mIsPlaying)
	{
		RefreshImageBuffer();
		NextFrame();
	}
}

BOOL CinePlayer::IsLive()
{
    BOOL Live = FALSE;

    if (m_pCurrentCine != NULL )
    {
        Live = m_pCurrentCine->IsLive();
    }
    return (Live);
}



//get the image from camera and updates the displayed image buffer
void CinePlayer::RefreshImageBuffer()
{
	if (m_pCurrentCine == NULL)
		return;

    try
    {    
        IH imgHeader;
        IMRANGE imrange;
        imrange.First = mCurrentFrame;
        imrange.Cnt = 1;

        //
        // if camera/cine changed get new image buffer Size
        //
        if ((m_UpdateImageSize == TRUE) || (m_ImgSizeInBytes == 0))
        {
            UINT imgSizeInBytes = m_pCurrentCine->GetMaxImageSizeInBytes();
            m_ImgSizeInBytes = imgSizeInBytes;
            m_pPictureBox->SetImageBufferSize(imgSizeInBytes);

            m_pPictureBox->ClearPictureBox();
            m_UpdateImageSize = FALSE;      
        }

        try
        {
            //read cine image into the buffer
            HRESULT result = m_pCurrentCine->GetCineImage(m_pPictureBox->GetImageBufferPtr(), &imrange, &imgHeader, m_ImgSizeInBytes);
            if (result < 0)
            {
                //
                // want image refresh if camera disconnected (Offline)
                // to support showing black image with offline message
                //
                if (ErrorHandler::IsConnectionError(result) == FALSE)
                {
                    ErrorHandler::CheckError(result);
                    return;
                }
            }
        }
        catch (CException* e)
        {
            //
            // If we go offline while we are doing a GetCineImage
            // that routine can throw an Exception
            // this is not bad, since we lost the connection. 
            // So... let catch it here and just move on
            // no need to recover anything, we now know we are offline
            //
            TCHAR err_message[DEFAULT_STR_MAXSZ];
            e->GetErrorMessage(err_message, DEFAULT_STR_MAXSZ);
            //AfxMessageBox(err_message);
            return;
        }

        if (imgHeader.biWidth <= 0 && imgHeader.biHeight <= 0)
            return;

        mIsColorImage = IsColorHeader(&imgHeader);

        BOOL is16bpp = Is16BitHeader(&imgHeader);
        //if needed reduce image bitdepth to 8bpp in order to be displayed
        //the image will be 8bpp at drawing
        if (is16bpp)
        {
            ReduceTo8bpp(m_pCurrentCine->GetSensitivity(), &imgHeader);
        }

        //associate the bitmap header with image buffer.
        BITMAPINFOHEADER bmiHeader;
        //refresh the bitmap info
        bmiHeader = *(PBITMAPINFOHEADER)(&imgHeader);
        //IH is bigger than BMIH, reassign the size
        bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
        m_pPictureBox->SetBMIH(&bmiHeader);

        m_pPictureBox->Invalidate(TRUE);
    }
	catch (CException* e)
	{
		TCHAR err_message[DEFAULT_STR_MAXSZ];
		e->GetErrorMessage(err_message, DEFAULT_STR_MAXSZ);
		AfxMessageBox(err_message);
	}
	
	if (m_pCurrentCine->IsLive())
		RefreshLiveSignals();

}

void CinePlayer::UpdatePlayUIVisibility()
{
    BOOL frameControlVisible = TRUE;
	//do not show play interface for live images
	if (m_pCurrentCine == NULL || m_pCurrentCine->IsLive())
        frameControlVisible = FALSE;

	INT showSelector = frameControlVisible ? SW_SHOW : SW_HIDE;

	m_pButtonPlay->ShowWindow(showSelector);
	m_pPlaySlider->ShowWindow(showSelector);
	m_pLbFirstIm->ShowWindow(showSelector);
	m_pLbLastIm->ShowWindow(showSelector);
	m_pFrameTextBox->ShowWindow(showSelector);
	
	//m_pSigGrp->ShowWindow(showSelector);
	//m_pSigBin->ShowWindow(showSelector);
	//m_pSigAna->ShowWindow(showSelector);
}

BOOL CinePlayer::IsColorHeader(PIH pIH)
{
	if (pIH->biBitCount == 8 || pIH->biBitCount == 16)
		return FALSE;
	else
		return TRUE;
}

BOOL CinePlayer::Is16BitHeader(PIH pIH)
{
	if (pIH->biBitCount == 16 || pIH->biBitCount == 48)
		return TRUE;
	else
		return FALSE;
}