#pragma once
#include "Cine.h"
#include "DemoHead.h"
#include "CPictureBox.h"

//Class manages image acquisition displaying of the current cine
class CinePlayer
{
private:
	CPictureBox *m_pPictureBox;
	CButton *m_pButtonPlay;
	CSliderCtrl *m_pPlaySlider;
	CEdit *m_pFrameTextBox;
	CStatic *m_pLbFirstIm, *m_pLbLastIm;
	CStatic *m_pSigGrp, *m_pSigBin, *m_pSigAna;
	Cine *m_pCurrentCine;

	INT mCurrentFrame;
	INT mFirstIm;
	INT mLastIm;
    UINT m_ImgSizeInBytes;
	BOOL mIsPlaying;
	BOOL mIsColorImage;

	void SetPlayRange(INT first, INT last);
	void InitPlayRange(INT first, INT last);
	void RefreshPlayButton();
	void NextFrame();
	void ReduceTo8bpp(FLOAT sensitivity, PIH imgHeader);

public:
	CinePlayer(CPictureBox *pictureBox, CButton *buttonPlay, CSliderCtrl *playSlider, CEdit *frameTextBox, CStatic *firstIm, CStatic *lastIm, CStatic *sigGrp, CStatic *sigBin, CStatic *sigAna);
	~CinePlayer(void);

    BOOL m_UpdateImageSize;

    BOOL IsLive();
	BOOL IsPlaying();
	BOOL IsColorImage();
	void SetCurrentCine(Cine *pCine);
	void SetCurrentFrame(INT value);

	void StartPlay();
	void StopPlay();

	void RefreshImageBuffer();
	void PlayNextImage();

	void UpdatePlayUIVisibility();

	static BOOL IsColorHeader(PIH pIH);
	static BOOL Is16BitHeader(PIH pIH);
	
	void RefreshLiveSignals();

};
