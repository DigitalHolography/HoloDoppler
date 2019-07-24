%====================================================================
%                                                                   
%  Copyright (C) 1992-2019 Vision Research Inc. All Rights Reserved.
%                                                                   
%  The licensed information contained herein is the property of     
%  Vision Research Inc., Wayne, NJ, USA  and is subject to change   
%  without notice.                                                  
%                                                                   
%  No part of this information may be reproduced, modified or       
%  transmitted in any form or by any means, electronic or           
%  mechanical, for any purpose, without the express written         
%  permission of Vision Research Inc.                               
%                                                                   
%====================================================================

function [matlabIm, unshiftedIm] = ReadCineFileImage(fileName, imageNo, showImage)
%Read an image specified by imageNo from a cine located at the path specified by fileName parameter.
% RETRUNS:
% matlabIm - 1D Gray/3D RGB matrix. For 16bpp images the pixel values are alligned to 16bits
% unshiftedIm - 1D Gray/3D RGB matrix with image pixel values unshifted

% Usage:
% LoadPhantomLibraries();
% RegisterPhantom(true); %Register the Phantom dll's ignoring connected cameras. 
%						 %Use this function once at the begining of your work
% [matlabIm, origIm] = ReadCineFileImage('D:\Cine\test.cine', -3000, true);
% other work with cine files
% .....................
% UnregisterPhantom(); %Use this function when you finished your work
% UnloadPhantomLibraries();

%% Create the cine handle from the cine file.
%Is recomended that cine handle creation should be done once for a batch of image readings. 
%This will increase speed.
[HRES, cineHandle] = PhNewCineFromFile(fileName);
if (HRES<0)
	[message] = PhGetErrorMessage( HRES );
    error(['Cine handle creation error: ' message]);
end

%% Get information about cine
%read the saved range
pFirstIm = libpointer('int32Ptr',0);
PhGetCineInfo(cineHandle, PhFileConst.GCI_FIRSTIMAGENO, pFirstIm);
firstIm = pFirstIm.Value;
pImCount = libpointer('uint32Ptr',0);
PhGetCineInfo(cineHandle, PhFileConst.GCI_IMAGECOUNT, pImCount);
lastIm = int32(double(firstIm) + double(pImCount.Value) - 1);
if (imageNo<firstIm || imageNo>lastIm)
    error(['Image number must be in saved cine range [' num2str(firstIm) ';' num2str(lastIm) ']']);
end
%get cine image buffer size
pInfVal = libpointer('uint32Ptr',0);
PhGetCineInfo(cineHandle, PhFileConst.GCI_MAXIMGSIZE, pInfVal);
imgSizeInBytes = pInfVal.Value;
%The image flip for GetCineImage function is inhibated.
pInfVal = libpointer('int32Ptr',false);
PhSetCineInfo(cineHandle, PhFileConst.GCI_VFLIPVIEWACTIVE, pInfVal);
%Create the image reange to be readed
imgRange = get(libstruct('tagIMRANGE'));
%take one image at imageNo
imgRange.First = imageNo;
imgRange.Cnt = 1;

%% Read the cine image into the buffer 
%The image will have image processings applied 
[HRES, unshiftedIm, imgHeader] = PhGetCineImage(cineHandle, imgRange, imgSizeInBytes);
%destroys the handle
PhDestroyCine(cineHandle);
%% Read image information from header
isColorImage = IsColorHeader(imgHeader);
is16bppImage = Is16BitHeader(imgHeader);

%% Transform 1D image pixels to 1D/3D image pixels to be used with MATLAB
if (HRES >= 0)
    [unshiftedIm] = ExtractImageMatrixFromImageBuffer(unshiftedIm, imgHeader);
    if (isColorImage)
        samplespp = 3;
    else
        samplespp = 1;
    end
    bps = GetEffectiveBitsFromIH(imgHeader);
    [matlabIm, unshiftedIm] = ConstructMatlabImage(unshiftedIm, imgHeader.biWidth, imgHeader.biHeight, samplespp, bps);
end

%% Show image
if (showImage)
    if (isColorImage)
        figure, image(matlabIm,'CDataMapping','scaled'),colormap('default');
    else
        figure, image(matlabIm,'CDataMapping','scaled'),colormap(gray(2^8));
    end
end
