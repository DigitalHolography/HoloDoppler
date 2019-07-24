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

function varargout = PhDemoMatlab(varargin)
% PHDEMOMATLAB M-file for PhDemoMatlab.fig
%      PHDEMOMATLAB, by itself, creates a new PHDEMOMATLAB or raises the existing
%      singleton*.
% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
    'gui_Singleton',  gui_Singleton, ...
    'gui_OpeningFcn', @PhDemoMatlab_OpeningFcn, ...
    'gui_OutputFcn',  @PhDemoMatlab_OutputFcn, ...
    'gui_LayoutFcn',  [] , ...
    'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT
end


function PhDemoMatlab_OpeningFcn(hObject, eventdata, handles, varargin)
handles.output = hObject;
guidata(hObject,handles);

global gLastSelectedCineStatus;
gLastSelectedCineStatus = [];
global GlobalObjects;
GlobalObjects.hPoolBuilder = [];
GlobalObjects.hPoolRefresher = [];
GlobalObjects.hCinePlayer = [];
GlobalObjects.hSelectedSource = []; %the current selected source
GlobalObjects.hOpenedFile = [];     %the current opened file

% Load Dlls
LoadPhantomLibraries();

%If LogAndStgFolder == [] then the Log&STG folder is the default generated in DLL's
%default log folder is \Application Data\Phantom\DLLVersion
GlobalObjects.hPoolBuilder = PoolBuilder([]);
GlobalObjects.hPoolBuilder.Register();

GlobalObjects.hPoolRefresher = PoolRefresher();
GlobalObjects.hPoolRefresher.RefreshCameras();
GlobalObjects.hCinePlayer = CinePlayer();
GlobalObjects.hCineSaver = [];
GlobalObjects.hObject = hObject;

% add cine player events
addlistener(GlobalObjects.hCinePlayer,'CurrentFrame','PostSet', @Player_CurrentFrame_PostSet);
addlistener(GlobalObjects.hCinePlayer,'IsPlaying','PostSet', @Player_IsPlaying_PostSet);
addlistener(GlobalObjects.hCinePlayer,'IsColorImage','PostSet', @Player_IsColorImage_PostSet);

RefreshSourceAndCine();

global gTimerDisplay;
gTimerDisplay = timer('ExecutionMode','fixedSpacing','Period',0.04);
gTimerDisplay.TimerFcn = {@timerDisplay_callbk};
end

function varargout = PhDemoMatlab_OutputFcn(hObject, eventdata, handles)
varargout{1} = handles.output;
StartDisplayTimer();
end

function figurePhDemoMatlab_CloseRequestFcn(hObject, eventdata, handles)
try
    StopDisplayTimer();
    global gTimerDisplay;
    delete(gTimerDisplay);
    
    global GlobalObjects;
    if (~isempty(GlobalObjects.hCineSaver))
        if (GlobalObjects.hCineSaver.Started)
            GlobalObjects.hCineSaver.StopSave();
        end
        GlobalObjects.hCineSaver.delete();
        GlobalObjects.hCineSaver = [];
    end
    
    if (~isempty(GlobalObjects.hCinePlayer))
        GlobalObjects.hCinePlayer.delete();
        GlobalObjects.hCinePlayer = [];
    end
    if (~isempty(GlobalObjects.hOpenedFile))
        GlobalObjects.hOpenedFile.delete();
        GlobalObjects.hOpenedFile = [];
    end
    if (~isempty(GlobalObjects.hSelectedSource) && isvalid(GlobalObjects.hSelectedSource))
        GlobalObjects.hSelectedSource.delete();
        GlobalObjects.hSelectedSource = [];
    end
    if (~isempty(GlobalObjects.hPoolRefresher))
        GlobalObjects.hPoolRefresher.delete();
        GlobalObjects.hPoolRefresher = [];
    end
    try
        if (~isempty(GlobalObjects.hPoolBuilder))
            if (GlobalObjects.hPoolBuilder.IsRegistered)
                GlobalObjects.hPoolBuilder.Unregister();
            end
            GlobalObjects.hPoolBuilder.delete();
            GlobalObjects.hPoolBuilder = [];
        end
    catch ex
        msgbox('Error while unregistering.');
    end
    
    delete(hObject);
    hObject = [];
    %clear all global variables used in this program
    clearvars -global gTimerDisplay gLastSelectedCineStatus GlobalObjects
    UnloadPhantomLibraries();
catch ex
    ex_message = ex.message
    ex_stack_file = ex.stack(1).file
    ex_stack_line = ex.stack(1).line
    errordlg('Error while closing.','Error','modal');
    if (~isempty(hObject))
        delete(hObject);
    end
end
end

%% TIMER
function StartDisplayTimer()
global gTimerDisplay;
if(strcmp(get(gTimerDisplay,'Running'),'on'))
    StopDisplayTimer();
end
start(gTimerDisplay);
end

function StopDisplayTimer()
% stops the image display
global gTimerDisplay;
stop(gTimerDisplay);
end

function timerDisplay_callbk(obj,event)
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);

try
    %image refreshing
    if (~isempty(GlobalObjects.hSelectedSource))
        GlobalObjects.hCinePlayer.PlayNextImage();
    end
    %Refresh cine save status.
    if (~isempty(GlobalObjects.hCineSaver) && GlobalObjects.hCineSaver.Started)
        GlobalObjects.hCineSaver.UpdateSaveStatus();
    end
    
    %update camera status, current cine stored state
    %detect&refresh parameters changes
    if (isa(GlobalObjects.hSelectedSource,'Camera'))
        %update camera status info
        hSelectedCam = GlobalObjects.hSelectedSource;
        activePart = hSelectedCam.GetActiveCinePartNo();
        camStatus = hSelectedCam.GetCamStatus();
        if (camStatus ~= CameraStatus.NotAvailable)
            camStatusStr = ['Camera status: ' PrintCameraStatus(camStatus, activePart)];
            set(handles.textCamStatus, 'String', camStatusStr);
        else
            set(handles.textCamStatus, 'String', '');
        end
        
        %Refresh availability of record actions based on cam status
        handles = RefreshRecordActions(handles, camStatus);
        hCine = hSelectedCam.CurrentCine();
        if (~isempty(hCine))
            global gLastSelectedCineStatus;
            selectedCineCurrentStatus = hSelectedCam.GetCinePartitionStatus(hSelectedCam.SelectedCinePartNo);
            %if selected partition stored status had been changed, update cine interface
            if (selectedCineCurrentStatus.Stored ~= gLastSelectedCineStatus.Stored)
                SelectCineFromPopupmenu();
                gLastSelectedCineStatus = selectedCineCurrentStatus;
            end
            
            %if parameters were changed by another connection update UI
            if (hSelectedCam.ParametersExternallyChanged())
                RefreshPartitionPopupmenu();
                RefreshAcqParameters();
                RefreshImProcessing();
            end
        end
    else
        handles = RefreshRecordActions(handles, CameraStatus.NotAvailable);
        set(handles.textCamStatus, 'String', '');
    end
    
    % shows image and UI updates
    if (~isempty(GlobalObjects.hSelectedSource))
        %the colormap is set on Player_IsColorImage_PostSet
        h=image(GlobalObjects.hCinePlayer.CurrentImagePixels,'Parent',handles.axesImgPreview, 'CDataMapping','scaled');
        axis(handles.axesImgPreview, 'off');
        axis(handles.axesImgPreview, 'image');
        
        period = double(get(obj,'InstantPeriod'));
        if (~isempty(period) && ~isnan(period))
            set(handles.textFps,'String',['Refresh speed: ' num2str(1/period) ' Hz']);
        end
    end
    
    %Check for camera changes
    RefreshCameraList();

catch ex
    timer_ex_msg = ex.message
    timer_ex_stack_file = ex.stack(1).file
    timer_ex_stack_line = ex.stack(1).line
end
pause(0.02);
end

function handles = RefreshRecordActions(handles, camStatus)
if (camStatus == CameraStatus.Live)
    set(handles.pushbuttonCapture,'String', 'Capture');
    set(handles.pushbuttonCapture,'Enable', 'on');
    set(handles.pushbuttonTrigger,'Enable', 'off');
elseif (camStatus == CameraStatus.RecWaitingForTrigger)
    set(handles.pushbuttonCapture,'String', 'Abort Capture');
    set(handles.pushbuttonCapture,'Enable', 'on');
    set(handles.pushbuttonTrigger,'Enable', 'on');
elseif (camStatus == CameraStatus.RecPostriggerFrames)
    set(handles.pushbuttonCapture,'String', 'Abort Capture');
    set(handles.pushbuttonCapture,'Enable', 'on');
    set(handles.pushbuttonTrigger,'Enable', 'off');
elseif (camStatus == CameraStatus.NotAvailable)
    set(handles.pushbuttonCapture,'String', 'Capture');
    set(handles.pushbuttonCapture,'Enable', 'off');
    set(handles.pushbuttonTrigger,'Enable', 'off');
end
end

%% Refresh UI Methods
function RefreshSourceAndCine()
RefreshSourcePopupmenu();
SelectSourceFromPopupmenu();
RefreshCinePopupmenu();
SelectCineFromPopupmenu();
end

function RefreshSourcePopupmenu()
%Refresh the soruce popupmenu with avaialble cameras, add file selection
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
%populate listbox with current cameras
camCount = GlobalObjects.hPoolRefresher.GetCameraListLength();
srcList = {};
for icam = 1:camCount
    cam = GlobalObjects.hPoolRefresher.GetCameraAt(icam);
    srcList{icam} = cam.ToString();
end
%add the file ID if any opened file exist
if (~isempty(GlobalObjects.hOpenedFile))
    srcList{icam+1} = 'File';
end

set(handles.popupmenuSources,'String',srcList);

%select popupmenu item index based on selected source
%the camera list index is the same as the popupmenu item index
if (isa(GlobalObjects.hSelectedSource, 'Camera'))
    hSelectedCamera = GlobalObjects.hSelectedSource;
    cameraIndex = hSelectedCamera.GetCameraNumber();
    if (cameraIndex>0)
        set(handles.popupmenuSources,'Value',cameraIndex);
    else
        set(handles.popupmenuSources,'Value',1);
    end
elseif (isa(GlobalObjects.hSelectedSource, 'FileSource'))
    set(handles.popupmenuSources,'Value',icam+1); %select file item
elseif (isempty(GlobalObjects.hSelectedSource))
    set(handles.popupmenuSources,'Value',1);
end

guidata(GlobalObjects.hObject, handles);
end

function RefreshCinePopupmenu()
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
%Refresh the cine popupmenu with the available cines from the source
if (isa(GlobalObjects.hSelectedSource, 'Camera'))
    %populate the list with available cines
    hSelectedCamera = GlobalObjects.hSelectedSource;
    selectedIndex = 1;
    cineIds = {};
    cineIdsIndex = 1;
    %RAM cine partitions should not be added on the list for CineStation devices because they do not exist.
    if (hSelectedCamera.GetSupportsRecordingCines())
        startCineNo = PhConConst.CINE_PREVIEW;
        lastCineNo = hSelectedCamera.GetPartitionCount();
        for iCine = startCineNo:lastCineNo
            cineIds{cineIdsIndex} = Cine.GetStringForCineNo(iCine, hSelectedCamera.GetCameraNumber());
            if (iCine == hSelectedCamera.SelectedCinePartNo)
                selectedIndex = cineIdsIndex;
            end
            cineIdsIndex = cineIdsIndex + 1;
        end
    end
    
    firstFlashCine = hSelectedCamera.GetFirstFlashCineNo();
    lastFlashCineNo = hSelectedCamera.GetLastFlashCineNo();
    for iCine = firstFlashCine:lastFlashCineNo
        cineIds{cineIdsIndex} = Cine.GetStringForCineNo(iCine, hSelectedCamera.GetCameraNumber());
        if (iCine == hSelectedCamera.SelectedCinePartNo)
            selectedIndex = cineIdsIndex;
        end
        cineIdsIndex = cineIdsIndex + 1;
    end
    set(handles.popupmenuCine, 'String', cineIds);
    if (~isempty(cineIds))
        set(handles.popupmenuCine,'Value',selectedIndex);
    end
elseif (isa(GlobalObjects.hSelectedSource, 'FileSource'))
    if (~isempty(GlobalObjects.hOpenedFile))
        fs = GlobalObjects.hSelectedSource;
        [pathstr, name, extra] = fileparts(fs.FilePath);
        set(handles.popupmenuCine, 'String', name);
        set(handles.popupmenuCine,'Value',1);
    end
end
guidata(GlobalObjects.hObject, handles);
end

function SelectSourceFromPopupmenu()
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
%Select the source from the selected popupmenu item.
itemIndex = get(handles.popupmenuSources, 'Value');
if (itemIndex>0)
    sourcesContents = get(handles.popupmenuSources, 'String');
    if(isempty(sourcesContents))
        return;
    end
    selectedSourceStr = sourcesContents{get(handles.popupmenuSources, 'Value')};
    if (strcmp(selectedSourceStr, 'File'))
        GlobalObjects.hSelectedSource = GlobalObjects.hOpenedFile;
    else
        %parse camera serial from popupmenu item. The camera serial is an unique ID
        istart = strfind(selectedSourceStr, '(') + 1;
        istop = strfind(selectedSourceStr, ')') - 1;
        serialStr = selectedSourceStr(istart:istop);
        serial = uint32(str2double(serialStr));
        %select the camera with serial
        GlobalObjects.hSelectedSource = GlobalObjects.hPoolRefresher.GetCameraAt(itemIndex);
        RefreshPartitionPopupmenu();
    end
    
    %show/hide info button
    isCam = isa(GlobalObjects.hSelectedSource, 'Camera');
    if (isCam)
        set(handles.pushbuttonInfo, 'Visible','on');
    else
        set(handles.pushbuttonInfo, 'Visible','off');
    end
    
    %show/hide camera settings
    hSelCam  = GlobalObjects.hSelectedSource;
    settingsVisible = isCam && hSelCam.GetSupportsRecordingCines();
    if (settingsVisible)
        set(handles.uipanelCameraSettings, 'Visible','on');
    else
        set(handles.uipanelCameraSettings, 'Visible','off');
    end
end
guidata(GlobalObjects.hObject, handles);
end

function RefreshPartitionPopupmenu()
%Populates partition popupmenu with possible partitions numbers, select the actual number of partitions.
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
if (isa(GlobalObjects.hSelectedSource, 'Camera'))
    hSelectedCamera = GlobalObjects.hSelectedSource;
    if (hSelectedCamera.GetSupportsRecordingCines())
        %populate partitions popupmenu up to the number of maximum partitions
        maxPartCount = hSelectedCamera.GetMaxPartitionCount();
        if (maxPartCount <= 1)
            set(handles.popupmenuPartitions, 'String', '1');
            set(handles.popupmenuPartitions, 'Value', 1);
            set(handles.popupmenuPartitions, 'Enable', 'off');
        else
            partNo = hSelectedCamera.GetPartitionCount();
            selectedIndex = 1;
            partStr = {};
            for i = 1:maxPartCount-1
                partStr{i} = num2str(i);
                if (i == partNo)
                    selectedIndex = i;
                end
            end
            set(handles.popupmenuPartitions, 'String', partStr);
            set(handles.popupmenuPartitions, 'Value', selectedIndex);
            set(handles.popupmenuPartitions, 'Enable', 'on');
        end
    end
end
guidata(GlobalObjects.hObject, handles);
end

function SelectCineFromPopupmenu()
%Selects the cine from popupmenu selected item.
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
cineContents = get(handles.popupmenuCine, 'String');
if (isempty(cineContents))
    return;
end
selectedCineStr = [];
if (iscell(cineContents))
    selectedCineStr = cineContents{get(handles.popupmenuCine, 'Value')};
else
    selectedCineStr = cineContents;
end

if (isa(GlobalObjects.hSelectedSource, 'Camera'))
    hSelCam = GlobalObjects.hSelectedSource;
    hSelCam.SetSelectedCinePartNo(Cine.ParseCineNo(selectedCineStr,hSelCam.GetCameraNumber()));
    global gLastSelectedCineStatus;
    gLastSelectedCineStatus = hSelCam.GetCinePartitionStatus(hSelCam.SelectedCinePartNo);
    %if cine partition is empty
    if (~(gLastSelectedCineStatus.Stored || gLastSelectedCineStatus.Triggered))
        %make the selected empty partition active in camera (start recording)
        hSelCam.RecordSpecificCine(hSelCam.SelectedCinePartNo);
    end
end

RefreshAcqParameters();
RefreshPlayInterface();
RefreshImProcessing();
end

function RefreshAcqParameters()
global GlobalObjects;
%Refreshes acquisition parameters
if (isa(GlobalObjects.hSelectedSource, 'Camera'))
    hSelCam = GlobalObjects.hSelectedSource;
    selPartIsStored = hSelCam.IsCinePartitionStored(hSelCam.SelectedCinePartNo);
    if (selPartIsStored)
        RefreshAcquisitionParamtersStoredCine(hSelCam.CurrentCine());
    else
        RefreshAcquisitionParamtersNotStoredCine(hSelCam);
    end
elseif (isa(GlobalObjects.hSelectedSource, 'FileSource'))
    RefreshAcquisitionParamtersStoredCine(GlobalObjects.hSelectedSource.CurrentCine());
end
end

function handles = SetAcqFieldsEnable(handles, enable)
enableText = LogicalToText(enable);
set(handles.popupmenuBitDepth, 'Enable', enableText);
set(handles.popupmenuResolutions, 'Enable', enableText);
set(handles.editFrameRate, 'Enable', enableText);
set(handles.editExposure, 'Enable', enableText);
set(handles.editEDRExposure, 'Enable', enableText);
set(handles.editPTFrames, 'Enable', enableText);
set(handles.pushbuttonSet, 'Enable', enableText);
end

function RefreshAcquisitionParamtersNotStoredCine(hCamera)
%Refreshes acquisition parameters for cine partitions.
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);

handles = SetAcqFieldsEnable(handles, true);

acquisitionParams = hCamera.GetAcquisitionParameters(hCamera.SelectedCinePartNo);
%get the current acquisition resolution

currentResStr = GetResolutionStr(acquisitionParams.ImWidth, acquisitionParams.ImHeight);

[resolutions, resolutionCount] = hCamera.GetCameraResolutions();

%populate resolution popupmenu
selectedIndex = -1;
resolutionsStr = {};
for ires=1:resolutionCount
    res = resolutions(ires);
    resStr = GetResolutionStr(res.x, res.y);
    resolutionsStr{ires} = resStr;
    if (strcmp(resStr,currentResStr))
        selectedIndex = ires;
    end
end

if (selectedIndex>0)
    set(handles.popupmenuResolutions, 'String', resolutionsStr);
    set(handles.popupmenuResolutions, 'Value', selectedIndex);
else
    resolutionsStr{ires+1} = currentResStr;
    set(handles.popupmenuResolutions, 'String', resolutionsStr);
    set(handles.popupmenuResolutions, 'Value', ires+1);
end

%update bitdepth popupmenu
%get available bitdepths
[bitDepths bdCount] = hCamera.GetCameraBitDepths();
camOptions = hCamera.GetCamOptions();
actualBitDepth = camOptions.RAMBitDepth;
selectedIndexBitDepth = 0;
bitDepthsStr = {};
for iBitDepth=1:bdCount
    bitDepth = bitDepths(iBitDepth);
    bitDepthsStr{iBitDepth} = num2str(bitDepth);
    if (bitDepth == actualBitDepth)
        selectedIndexBitDepth = iBitDepth;
    end
end
set(handles.popupmenuBitDepth, 'String', bitDepthsStr);
set(handles.popupmenuBitDepth, 'Value', selectedIndexBitDepth);

%refresh other parameters values
set(handles.editFrameRate, 'String', num2str(acquisitionParams.dFrameRate));
set(handles.editExposure, 'String', num2str(NanoSecToMicroSec(acquisitionParams.Exposure)));
set(handles.editEDRExposure, 'String', num2str(NanoSecToMicroSec(acquisitionParams.EDRExposure)));
set(handles.editImCount, 'String', num2str(acquisitionParams.ImCount));
set(handles.editPTFrames, 'String', num2str(acquisitionParams.PTFrames));
delay = 0;
if (acquisitionParams.PTFrames > acquisitionParams.ImCount)
    delay = acquisitionParams.PTFrames - acquisitionParams.ImCount;
end
set(handles.editDelay, 'String', num2str(delay));

guidata(GlobalObjects.hObject, handles);
end

function RefreshAcquisitionParamtersStoredCine(hCine)
%Refreshes acquisition parameters for Stored (recorded) cines (files or recorded cine partitions).
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);

handles = SetAcqFieldsEnable(handles, false);

%update resolution popupmenu
currentResStr = GetResolutionStr(hCine.GetImWidth(), hCine.GetImHeight());
set(handles.popupmenuResolutions, 'String', currentResStr);
set(handles.popupmenuResolutions, 'Value', 1);

%update bitdepth popupmenu
set(handles.popupmenuBitDepth, 'String', num2str(hCine.GetBppReal()));
set(handles.popupmenuBitDepth, 'Value', 1);

%update other parameters
set(handles.editFrameRate, 'String', num2str(hCine.GetFrameRate()));
set(handles.editExposure, 'String', num2str(NanoSecToMicroSec(hCine.GetExposure())));
set(handles.editEDRExposure, 'String', num2str(NanoSecToMicroSec(hCine.GetEDRExposureNs())));
set(handles.editImCount, 'String', num2str(hCine.GetImageCount()));
set(handles.editPTFrames, 'String', num2str(hCine.GetPostTriggerFrames()));
set(handles.editDelay, 'String', num2str(hCine.GetTriggerDelay()));

guidata(GlobalObjects.hObject, handles);
end

function RefreshImProcessing()
%Refreshes image processing options for selected cine.
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
hCine = [];
if (~isempty(GlobalObjects.hSelectedSource))
    hCine = GlobalObjects.hSelectedSource.CurrentCine();
end

if (isempty(hCine))
    return;
end

set(handles.editBrightness, 'String', hCine.GetBrightness());
set(handles.editGain, 'String', hCine.GetContrast());
set(handles.editGamma, 'String', hCine.GetGamma());
set(handles.editSaturation, 'String', hCine.GetSaturation());
set(handles.editHue, 'String', hCine.GetHue());
wbg = hCine.GetWhiteBalanceGain();
set(handles.editWBRed, 'String', wbg.R);
set(handles.editWBBlue, 'String', wbg.B);

guidata(GlobalObjects.hObject, handles);
end

function RefreshPlayInterface()
global GlobalObjects;
if (~isempty(GlobalObjects.hSelectedSource))
    hCurrentCine = GlobalObjects.hSelectedSource.CurrentCine();
    GlobalObjects.hCinePlayer.SetCurrentCine(hCurrentCine);
    handles = guidata(GlobalObjects.hObject);
    enablePlayer = LogicalToText(~hCurrentCine.IsLive);
    set(handles.pushbuttonPlay, 'Visible', enablePlayer);
    set(handles.textCrtFrame, 'Visible', enablePlayer);
    set(handles.editCrtFrame, 'Visible', enablePlayer);
    set(handles.textImRnglabel, 'Visible', enablePlayer);
    set(handles.textImRange, 'Visible', enablePlayer);
    if (~hCurrentCine.IsLive)
        set(handles.textImRange, 'String', ['[' num2str(GlobalObjects.hCinePlayer.FirstIm) ';' num2str(GlobalObjects.hCinePlayer.LastIm) ']']);
    end
    guidata(GlobalObjects.hObject, handles);
end
end

%% SetParameters
function SetAcquisitionParams()
%Set the acquisition parameters and other options into camera for selected cine partition.
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
hSelCam  = GlobalObjects.hSelectedSource;
if (isa(hSelCam,'Camera') && ~hSelCam.IsCinePartitionStored(hSelCam.SelectedCinePartNo))
    camOptions = hSelCam.GetCamOptions();
    contents = get(handles.popupmenuBitDepth, 'String');
    bitDepthStr = contents{get(handles.popupmenuBitDepth, 'Value')};
    camOptions.RAMBitDepth = str2double(bitDepthStr);
    hSelCam.SetCamOptions(camOptions);
    
    acqParams = hSelCam.GetAcquisitionParameters(hSelCam.SelectedCinePartNo);
    %set resolution
    contents = get(handles.popupmenuResolutions, 'String');
    resStr = contents{get(handles.popupmenuResolutions, 'Value')};
    [acqParams.ImWidth acqParams.ImHeight] = ParseResolution(resStr);
    
    parText = get(handles.editFrameRate, 'String');
    acqParams.dFrameRate = uint32(str2double(parText));
    parText = get(handles.editExposure, 'String');
    acqParams.Exposure = uint32(MicroSecToNanoSec(str2double(parText)));
    parText = get(handles.editEDRExposure, 'String');
    acqParams.EDRExposure = uint32(MicroSecToNanoSec(str2double(parText)));
    parText = get(handles.editPTFrames, 'String');
    acqParams.PTFrames = uint32(str2double(parText));
    
    hSelCam.SetAcquisitionParameters(hSelCam.SelectedCinePartNo, acqParams);
end
end


function SetImProcessing()
% Set image processing for selected cine. Selected cine might be the live cine.
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
hCine = [];
if (~isempty(GlobalObjects.hSelectedSource))
    hCine = GlobalObjects.hSelectedSource.CurrentCine();
end
if (isempty(hCine))
    return;
end

parText = get(handles.editBrightness, 'String');
hCine.SetBrightness(single(str2double(parText)));
parText = get(handles.editGain, 'String');
hCine.SetContrast(single(str2double(parText)));

parText = get(handles.editGamma, 'String');
hCine.SetGamma(single(str2double(parText)));

if (GlobalObjects.hCinePlayer.IsColorImage)
    parText = get(handles.editSaturation, 'String');
    hCine.SetSaturation(single(str2double(parText)));
    parText = get(handles.editHue, 'String');
    hCine.SetHue(single(str2double(parText)));
    
    wbg = hCine.GetWhiteBalanceGain();
    parText = get(handles.editWBRed, 'String');
    wbg.R = single(str2double(parText));
    parText = get(handles.editWBBlue, 'String');
    wbg.B = single(str2double(parText));
    hCine.SetWhiteBalanceGain(wbg);
end
end

function SetPartitionFromPopupmenu()
%Set the number of partitions from partition combo
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
if (isa(GlobalObjects.hSelectedSource,'Camera'))
    hSelCam  = GlobalObjects.hSelectedSource;
    %when there are stored cines shoe delete cine message
    if (~hSelCam.HasStoredRAMPart() || ShowDeleteAllCinesMessage())
        contents = get(handles.popupmenuPartitions, 'String');
        partStr = contents{get(handles.popupmenuPartitions, 'Value')};
        hSelCam.SetPartitionCount(uint32(str2double(partStr)));
        hSelCam.DestroySelectedCine();
        RefreshCinePopupmenu();
        SelectCineFromPopupmenu();
    else
        RefreshPartitionPopupmenu();
    end
end
end

%% Actions
function Record()
%Send record command to selected camera.
global GlobalObjects;
if (isa(GlobalObjects.hSelectedSource,'Camera'))
    hSelCam  = GlobalObjects.hSelectedSource;
    cineToCapture = hSelCam.SelectedCinePartNo;
    if (cineToCapture == PhConConst.CINE_PREVIEW || cineToCapture>=hSelectedCamera.GetFirstFlashCineNo())
        if (hSelCam.HasStoredRAMPart() && ~ShowDeleteAllCinesMessage())
            return;
        end
        %delete all cine partitions and send record command
        hSelCam.Record();
    else
        if (hSelCam.IsCinePartitionStored(cineToCapture) && ~ShowStoredCineWillBeDeletedMsg())
            return;
        end
        %record to specific cine partition
        hSelCam.RecordSpecificCine(cineToCapture);
    end
end
end

function AbortRecording()
% Aborts the current recording by selecting Preview partition in camera.
global GlobalObjects;
if (isa(GlobalObjects.hSelectedSource,'Camera'))
    hSelCam  = GlobalObjects.hSelectedSource;
    hSelCam.RecordSpecificCine(PhConConst.CINE_PREVIEW);
    if (~hSelCam.IsCinePartitionStored(hSelCam.SelectedCinePartNo))
        hSelCam.SetSelectedCinePartNo(PhConConst.CINE_PREVIEW);
        RefreshCinePopupmenu();
        SelectCineFromPopupmenu();
    end
end
end

function SendSoftwareTrigger()
%Send software trigger command to selected camera.
global GlobalObjects;
if (isa(GlobalObjects.hSelectedSource,'Camera'))
    hSelCam  = GlobalObjects.hSelectedSource;
    hSelCam.SendSoftwareTrigger();
end
end

function OpenFileCine()
global GlobalObjects;
%show the open cine dialog
[ dlgRes, cineFilePath ] = PhGetOpenCineName();
if (dlgRes)
    if (exist(cineFilePath,'file')==2)%if file exist
        if (~isempty(GlobalObjects.hOpenedFile))
            delete(GlobalObjects.hOpenedFile);
            GlobalObjects.hOpenedFile = [];
        end
        GlobalObjects.hOpenedFile = FileSource(cineFilePath);
        
        GlobalObjects.hSelectedSource = GlobalObjects.hOpenedFile;
        RefreshSourcePopupmenu();
        
        SelectSourceFromPopupmenu();
        RefreshCinePopupmenu();
        SelectCineFromPopupmenu();
    end
end
end

function StartSaveCine()
%Start the saving of a cine.
global GlobalObjects;
if (~isempty(GlobalObjects.hCineSaver))
    if (GlobalObjects.hCineSaver.Started)
        errordlg('A save is underway. Please wait.','Error','modal');
    else
        %delete the old cine saver
        GlobalObjects.hCineSaver.delete();
        GlobalObjects.hCineSaver = [];
    end
end
if (isempty(GlobalObjects.hCineSaver))
    hSelectedCine = [];
    %Get the selected stored cine.
    %We need a duplicate because a cine cannot be used to play images and save images at same time.
    if (~isempty(GlobalObjects.hSelectedSource))
        hSelectedCine = GlobalObjects.hSelectedSource.CurrentCine();
        if (hSelectedCine.IsLive())
            hSelectedCine=[];
            %in the case of live cine the SelectedCine will be empty
        end
    end
    if (~isempty(hSelectedCine))
        GlobalObjects.hCineSaver = CineSaver(hSelectedCine);
        addlistener(GlobalObjects.hCineSaver, 'Started', 'PostSet', @CineSaver_Started_PostSet);
        addlistener(GlobalObjects.hCineSaver, 'SaveProgress', 'PostSet', @CineSaver_SaveProgress_PostSet);
        if (GlobalObjects.hCineSaver.ShowGetCineNameDialog())
            %cine name selection terminated witk OK
            if (~GlobalObjects.hCineSaver.StartSaveCine())
                GlobalObjects.hCineSaver.delete();
                GlobalObjects.hCineSaver = [];
                msgbox('Not a suitable cine to save.');
            end
        end
    end
end
end
%% Utils
function retVal = MicroSecToNanoSec(val)
retVal = double(val)*1000;
end

function retVal = NanoSecToMicroSec(val)
retVal = double(val)/1000;
end

function resStr = GetResolutionStr(width, height)
resStr = [num2str(width) 'x' num2str(height)];
end

function [width height] = ParseResolution(resStr)
resParts = regexp(resStr,'\x', 'split');
width = uint32(str2double(resParts{1}));
height = uint32(str2double(resParts{2}));
end

function result = ShowStoredCineWillBeDeletedMsg()
result = strcmp(questdlg('The selected cine will be deleted. Continue?', 'Delete stored cines', 'No'),'Yes');
end

function result = ShowDeleteAllCinesMessage()
result = strcmp(questdlg('All stored cine partitions will be deleted. Continue?','Delete stored cines', 'No'),'Yes');
end

function camSatusStr = PrintCameraStatus(status, activePart)
%Print the status from the camera.
switch (status)
    case CameraStatus.Live
        camSatusStr = 'Live';
    case CameraStatus.RecPostriggerFrames
        camSatusStr = ['Recording in cine partition ' num2str(activePart) ' postrigger frames.'];
    case CameraStatus.RecWaitingForTrigger
        camSatusStr= ['Recording in cine partition ' num2str(activePart) ', waiting for trigger'];
    case CameraStatus.Offline
        camSatusStr = 'Offline';
    otherwise
        camSatusStr = '';
end
end

function logicalText = LogicalToText(value)
if (value)
    logicalText = 'on';
else
    logicalText = 'off';
end
end

function RefreshCameraList()
global GlobalObjects;
changed = GlobalObjects.hPoolRefresher.RefreshCameras();
if (changed)
    RefreshSourceAndCine();
end
end

%% EventHandlers
%% Cine player events
function Player_CurrentFrame_PostSet(src, event)
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
set(handles.editCrtFrame,'String', num2str(GlobalObjects.hCinePlayer.CurrentFrame));
guidata(GlobalObjects.hObject, handles);
end

function Player_IsPlaying_PostSet(src, event)
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
if (GlobalObjects.hCinePlayer.IsPlaying)
    set(handles.pushbuttonPlay, 'String', 'Stop');
else
    set(handles.pushbuttonPlay, 'String', 'Play');
end
guidata(GlobalObjects.hObject, handles);
end

function Player_IsColorImage_PostSet(src, event)
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
%Set the color map
if (GlobalObjects.hCinePlayer.IsColorImage)
    colormap(handles.axesImgPreview, 'default');
else
    colormap(handles.axesImgPreview, gray(2^8));
end
%enables/disables controls based on IsColorImage Property
enable = LogicalToText(GlobalObjects.hCinePlayer.IsColorImage);
set(handles.editSaturation, 'Enable', enable);
set(handles.editHue, 'Enable', enable);
set(handles.editWBRed, 'Enable', enable);
set(handles.editWBBlue, 'Enable', enable);
guidata(GlobalObjects.hObject, handles);
end

%% Cine saver events
function CineSaver_Started_PostSet(src, event)
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
set(handles.textSaveProgress, 'Visible', LogicalToText(GlobalObjects.hCineSaver.Started));
set(handles.pushbuttonOpenCine, 'Enable', LogicalToText(~GlobalObjects.hCineSaver.Started));
set(handles.pushbuttonSaveCine, 'Enable', LogicalToText(~GlobalObjects.hCineSaver.Started));
guidata(GlobalObjects.hObject, handles);
end

function CineSaver_SaveProgress_PostSet(src, event)
global GlobalObjects;
handles = guidata(GlobalObjects.hObject);
progress = num2str(GlobalObjects.hCineSaver.SaveProgress);
set(handles.textSaveProgress, 'String', ['Save cine progress: ' progress '%']);
guidata(GlobalObjects.hObject, handles);
end

%% UI Events
%% TOP controls
function pushbuttonRefreshPool_Callback(hObject, eventdata, handles)
StopDisplayTimer();
RefreshCameraList();
%restart refresh timer
StartDisplayTimer();
end

function popupmenuSources_Callback(hObject, eventdata, handles)
StopDisplayTimer();
SelectSourceFromPopupmenu();
RefreshCinePopupmenu();
SelectCineFromPopupmenu();
StartDisplayTimer();
end

% --- Executes on button press in pushbuttonInfo.
function pushbuttonInfo_Callback(hObject, eventdata, handles)
StopDisplayTimer();
global GlobalObjects;
if (isa(GlobalObjects.hSelectedSource,'Camera'))
    CamInfoDlg(GlobalObjects.hSelectedSource);
end
StartDisplayTimer();
end

function popupmenuCine_Callback(hObject, eventdata, handles)
StopDisplayTimer();
SelectCineFromPopupmenu();
StartDisplayTimer();
end

function pushbuttonCapture_Callback(hObject, eventdata, handles)
StopDisplayTimer();
global GlobalObjects;
hSelectedCam = GlobalObjects.hSelectedSource;
camStatus = hSelectedCam.GetCamStatus();
if (camStatus == CameraStatus.RecWaitingForTrigger || camStatus == CameraStatus.RecPostriggerFrames)
    AbortRecording();
else
    Record();
end
StartDisplayTimer();
end

function pushbuttonTrigger_Callback(hObject, eventdata, handles)
SendSoftwareTrigger();
end

function pushbuttonOpenCine_Callback(hObject, eventdata, handles)
StopDisplayTimer();
OpenFileCine();
StartDisplayTimer();
end

function pushbuttonSaveCine_Callback(hObject, eventdata, handles)
StopDisplayTimer();
StartSaveCine();
StartDisplayTimer();
end

function pushbuttonExportCurrentImage_Callback(hObject, eventdata, handles)
StopDisplayTimer();
global GlobalObjects;
assignin('base', 'exportedPhImage', GlobalObjects.hCinePlayer.CurrentImagePixels);
StartDisplayTimer();
end

%% BUTTOM
function pushbuttonPlay_Callback(hObject, eventdata, handles)
global GlobalObjects;
if (GlobalObjects.hCinePlayer.IsPlaying)
    GlobalObjects.hCinePlayer.StopPlay();
else
    GlobalObjects.hCinePlayer.StartPlay();
end
end

function editCrtFrame_KeyPressFcn(hObject, eventdata, handles)
% eventdata  structure with the following fields (see UICONTROL)
%	Key: name of the key that was pressed, in lower case
%	Character: character interpretation of the key(s) that was pressed
%	Modifier: name(s) of the modifier key(s) (i.e., control, shift) pressed

if (strcmp(eventdata.Key,'return')) % if enter key is pressed
    uicontrol(hObject);%used to refocus in order to update string property
    crtFrameStr = get(handles.editCrtFrame,'String');
    global GlobalObjects;
    GlobalObjects.hCinePlayer.CurrentFrame = int32(str2double(crtFrameStr));
    GlobalObjects.hCinePlayer.RefreshImageBuffer();
end
end

%% RIGHT
function popupmenuPartitions_Callback(hObject, eventdata, handles)
StopDisplayTimer();
SetPartitionFromPopupmenu();
%feedback accepted value
RefreshPartitionPopupmenu();
StartDisplayTimer();
end

function pushbuttonSet_Callback(hObject, eventdata, handles)
StopDisplayTimer();
SetAcquisitionParams();
%feedback accepted values
RefreshAcqParameters();
StartDisplayTimer();
end

function pushbuttonSetImProc_Callback(hObject, eventdata, handles)
StopDisplayTimer();
SetImProcessing();
%feedback accepted values
RefreshImProcessing();
global GlobalObjects;
GlobalObjects.hCinePlayer.RefreshImageBuffer();
StartDisplayTimer();
end

%% Create Control Events
function axesImgPreview_CreateFcn(hObject, eventdata, handles)
axis(hObject,'off');
end

