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

% Load Phantom SDK libraries and register as a client
LoadPhantomLibraries();
str = sprintf('\n\nHello!\n======\nLooking for Phantom cameras...\nIf log is enabled, please browse the open windows; you may have a dialog behind\n');
disp(str);

%Path for log and stg files is not set; will be chosen in Phantom dll's 
%to c:\ProgramData\Phantom\<version>
PhLVRegisterClientEx([], PhConConst.PHCONHEADERVERSION);

% See if we have Phantom cameras around; add a simulated Miro M310 if not
[~, camCount] = PhGetCameraCount();
if(camCount==0)
    PhAddSimulatedCamera(8001, 11);   
end

% We have now at least one camera, real or simulated; will work only on first camera 
CN=0;
% Configure the camera in single cine
PhSetPartitions(CN, 1, 1);

[~, serial, name] = PhGetCameraID(CN);
str = sprintf('\n%d Phantom camera(s) available\nFirst camera: serial: %d name: %s ', camCount, serial, name);
disp(str);

% CN camera number ,  CH cine handle
[~, aqParams, bmi] = PhGetCineParams(CN, 1);

str = sprintf('\nCine 1 recorded at resolution %dx%d rate: %f', aqParams.ImWidth, aqParams.ImHeight, aqParams.dFrameRate);
disp(str);
% You can change the params and send them back to camera using
% PhSetSingleCineParams()

% delete cine(s) and start a recording in cine 1
PhRecordCine(CN);
% to get pretrigger frames we need a delay here
pause(3.0); %3 seconds wait before trigger (might be not enough)
% Trigger the recording
PhSendSoftwareTrigger(CN);

%wait until recording finish
while (1)
    [~, cs] = PhGetCineStatus(CN);
    if (cs(2).Stored == 1)
        break;
    end
end

[~, CH] = PhNewCineFromCamera(CN, 1);

pInfVal = libpointer('uint32Ptr', 0);
PhGetCineInfo(CH, PhFileConst.GCI_MAXIMGSIZE, pInfVal);
BufferSize = pInfVal.Value;

% Get the number of the first image in cine
pInfVal = libpointer('int32Ptr', 0);
PhGetCineInfo(CH,PhFileConst.GCI_FIRSTIMAGENO, pInfVal);
imgNo = pInfVal.Value;

flipV = 0;
pInfVal = libpointer('int32Ptr',flipV);
PhSetCineInfo(CH, PhFileConst.GCI_VFLIPVIEWACTIVE, pInfVal);
            
%Task 1: read and display an image from the recorded cine.
%=========================================================
imgRng = get(libstruct('tagIMRANGE'));
imgRng.First = imgNo;
imgRng.Cnt = 1;
[HRES, unshiftedIm, imgHeader] = PhGetCineImage(CH, imgRng, BufferSize);

% Convert the C style array of pixels to Matlab format

isColorImage = IsColorHeader(imgHeader);
is16bppImage = Is16BitHeader(imgHeader);

% Transform 1D image pixels to 1D/3D image pixels to be used with MATLAB
[unshiftedIm] = ExtractImageMatrixFromImageBuffer(unshiftedIm, imgHeader);
if (isColorImage)
    samplespp = 3;
else
    samplespp = 1;
end
bps = GetEffectiveBitsFromIH(imgHeader);
[matlabIm, unshiftedIm] = ConstructMatlabImage(unshiftedIm, imgHeader.biWidth, imgHeader.biHeight, samplespp, bps);


% Use Matlab function to paint image 
% You can add here whatever processing or analysis you want 
% An example: paint the image on screen in a separate window
if (isColorImage)
    figure, image(matlabIm,'CDataMapping','scaled'),colormap('default');
else
    figure, image(matlabIm,'CDataMapping','scaled'),colormap(gray(2^8));
end
%
%Task 2: save the recording in a raw cine file. It can be played in Pcc application 
%==================================================================================
FileName = 'c:\ProgramData\Phantom\Cine1.cine';
str = sprintf('\nSaving to the cine file:   %s  ...', FileName);
disp(str);
PhSetUseCase(CH, PhFileConst.UC_SAVE);

% Prepare a save name and path for the cine
pInfVal = libpointer('cstring', FileName);
PhSetCineInfo(CH, PhFileConst.GCI_SAVEFILENAME, pInfVal); 

% Get the number of the first image in cine
saveType = libpointer('uint32Ptr', PhFileConst.MIFILE_RAWCINE);
PhSetCineInfo(CH, PhFileConst.GCI_SAVEFILETYPE, saveType);

%GCI_SAVERANGE allows you to clip the saved recording, 
%for example, to the first 10 images
imgRng = get(libstruct('tagIMRANGE'));
imgRng.First = imgNo;
imgRng.Cnt = 10;
pimgRng = libpointer('tagIMRANGE', imgRng);
PhSetCineInfo(CH, PhFileConst.GCI_SAVERANGE, pimgRng);
pimgRng = [];

PhWriteCineFile(CH);

%Task 3: save the recording as a group of tif image files. 
%=========================================================
FileName = 'c:\ProgramData\Phantom\Img!5.tif';
% Set the save file name in the cine
str = sprintf('\nSaving to separate image files  %s  ...', FileName);
disp(str);


pInfVal = libpointer('cstring', FileName);
PhSetCineInfo(CH, PhFileConst.GCI_SAVEFILENAME, pInfVal); 
% Select the desired file type to save
saveType = libpointer('uint32Ptr', PhFileConst.SIFILE_TIF8);
PhSetCineInfo(CH, PhFileConst.GCI_SAVEFILETYPE, saveType);

% leave the clip set for 10 images
PhWriteCineFile(CH);

PhDestroyCine(CH);
PhLVUnregisterClient();
UnloadPhantomLibraries();
