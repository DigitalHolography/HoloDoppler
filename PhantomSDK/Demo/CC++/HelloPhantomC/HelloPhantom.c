/*****************************************************************************/
//                                                                   
//  Copyright (C) 1992-2019 Vision Research Inc. All Rights Reserved.
//                                                                   
//  The licensed information contained herein is the property of     
//  Vision Research Inc., Wayne, NJ, USA  and is subject to change   
//  without notice.                                                  
//                                                                   
//  No part of this information may be reproduced, modified or       
//  transmitted in any form or by any means, electronic or           
//  mechanical, for any purpose, without the express written         
//  permission of Vision Research Inc.                               
//                                                                   
/*****************************************************************************/

// HelloPhantom.cpp  simple demo for controlling Phantom cameras
// IT IS A CONSOLE MODE WINDOWS APPLICATION

#define _CRT_SECURE_NO_WARNINGS 
#include "stdio.h"
#include "conio.h"
#define _WINDOWS
#include "windows.h"

#include "..\..\..\inc\phint.h"
#include "..\..\..\inc\phcon.h"
#include "..\..\..\inc\phfile.h"


int main()
{

	int i, CN=0, camCount, serial, Part[1], BufferSize, imgNo, saveType;
	char name[MAX_PATH], FileName[MAX_PATH];
	ACQUIPARAMS aqParams;
	CINEHANDLE CH;
	PCINESTATUS cs;
	IMRANGE imgRng;
	IH ih;
	PBYTE pPixel;

	printf("\n\nHello!\n======\n");

	//First parameter NULL will leave on phantom sdk to choose a folder for log an stg files
	//It will choose  "C:\ProgramData\Phantom\<Version>"
	PhLVRegisterClientEx(NULL, NULL, PHCONHEADERVERSION);
		
	//See if we have Phantom cameras around; add a simulated Miro M310 if not
	PhGetCameraCount(&camCount);
	if (camCount == 0)
		PhAddSimulatedCamera(8001, 11);

	//We have now at least one camera, real or simulated; will work only on first camera
	// Configure the camera in single cine
	Part[0] = 1;	//any nonzero value is acceptable; first partition will fill all available video memory
	PhSetPartitions(CN, 1, Part);

	PhGetCameraID(CN, &serial, name);
	printf("\n%d camera(s) available\n First camera: serial: %d name: %s ", camCount, serial, name);

	// delete cine(s) and start a recording in cine 1
	PhRecordCine(CN);

	printf("\nWait a few seconds to record pretrigger images\nIf you have slow framerate and small number of posttrigger frames, you may have to wait more");
	// to get pretrigger frames we need a delay here
	Sleep(3000); // 3 seconds wait before trigger(might be not enough in any case)
	
	// Trigger the recording
	PhSendSoftwareTrigger(CN);
	
	// CN camera number, CH cine handle
	PhGetCineParams(CN, 1, &aqParams, NULL); 

	printf("\nCine 1 recorded at resolution %dx%d rate: %f", aqParams.ImWidth, aqParams.ImHeight, aqParams.dFrameRate);

	// You can change the params and send them back to camera using
	// PhSetSingleCineParams()

	cs = malloc(sizeof(CINESTATUS)*PhMaxCineCnt(CN));
	// wait until recording finish
	printf("\nWait the end of the recording...");
	do
		PhGetCineStatus(CN, cs);
	while (cs[1].Stored == 0);

	PhNewCineFromCamera(CN, 1, &CH);
	
	//Task 1: read and display the value of a few pixels from the first image of the recorded cine.
	//============================================================================================
	printf("\nTransfer an image from camera and dump a few pixels...\n");
	// Obtain the size of the image buffer
	PhGetCineInfo(CH, GCI_MAXIMGSIZE, &BufferSize);
	
	// Get the number of the first image in cine
	PhGetCineInfo(CH, GCI_FIRSTIMAGENO, &imgNo);
	imgRng.First = imgNo;
	imgRng.Cnt = 1;
	pPixel = malloc(BufferSize);
	PhGetCineImage(CH, &imgRng, pPixel, BufferSize, &ih);

	//Now you have image pixels in buffer and you can do any processing on them
	// for example display the values of a few pixels
	printf("\nDump first image pixel values\n");
	if (ih.biBitCount == 8 || ih.biBitCount == 24)
	{
		//8 bit per sample image monochrome (8bpp) or color (24bpp)
		for (i = 0; i<10; i++)
			printf("%08x   %02x %02x %02x %02x %02x %02x %02x %02x   %02x %02x %02x %02x %02x %02x %02x %02x\n",
			i * 16, 
			pPixel[i    ], pPixel[i + 1], pPixel[i +  2], pPixel[i +  3], pPixel[i +  4], pPixel[i +  5], pPixel[i +  6], pPixel[i +  7],
			pPixel[i + 8], pPixel[i + 9], pPixel[i + 10], pPixel[i + 11], pPixel[i + 12], pPixel[i + 13], pPixel[i + 14], pPixel[i + 15]);
	}
	else
	{
		//16 bit per sample image monochrome (16bpp) or color (48bpp)
		PWORD pPix16 = (PWORD)pPixel;
		for (i = 0; i<10; i++)
			printf("%08x   %04x %04x %04x %04x %04x %04x %04x %04x   %04x %04x %04x %04x %04x %04x %04x %04x\n",
			i * 16,
			pPix16[i    ], pPix16[i + 1], pPix16[i +  2], pPix16[i +  3], pPix16[i +  4], pPix16[i +  5], pPix16[i +  6], pPix16[i +  7],
			pPix16[i + 8], pPix16[i + 9], pPix16[i + 10], pPix16[i + 11], pPix16[i + 12], pPix16[i + 13], pPix16[i + 14], pPix16[i + 15]);
	}
	free(pPixel);
	free(cs);


	//Task 2: save the recording in a raw cine file. It can be played in Pcc application 
	//==================================================================================
	strcpy(FileName, "c:\\ProgramData\\Phantom\\Cine1.cine");
	printf("\nSaving to the cine file:   %s  ...", FileName);
	PhSetUseCase(CH, UC_SAVE);
	
	//Prepare a name and path for the cine
	PhSetCineInfo(CH, GCI_SAVEFILENAME, FileName);

	// Select the destination file format to RAW cine
	saveType = MIFILE_RAWCINE;
	PhSetCineInfo(CH, GCI_SAVEFILETYPE, &saveType);

	//GCI_SAVERANGE allows you to clip the saved recording to the first 10 images
	imgRng.First = imgNo;
	imgRng.Cnt = 10;
	PhSetCineInfo(CH, GCI_SAVERANGE, &imgRng);

	PhWriteCineFile(CH, NULL);

	//Task 3: save the recording as a group of tif image files. 
	//=========================================================
	strcpy(FileName, "c:\\ProgramData\\Phantom\\Img!5.tif");
	printf("\nSaving to separate image files  %s  ...", FileName);
	PhSetCineInfo(CH, GCI_SAVEFILENAME, FileName);
	
	//Select the destination file format to TIF 8 bit
	saveType = SIFILE_TIF8;
	PhSetCineInfo(CH, GCI_SAVEFILETYPE, &saveType);

	//GCI_SAVERANGE allows you to clip the saved recording to the first 10 images
	//this option was set above and remains active

	PhWriteCineFile(CH, NULL);

	PhDestroyCine(CH);
	PhLVUnregisterClient();

	printf("\nAll finished, press Enter to close.\n");
	_getch();
	return 0;
}

