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

function varargout = SimpleMatlabDemo(varargin)
% SIMPLEMATLABDEMO M-file for SimpleMatlabDemo.fig
%      SIMPLEMATLABDEMO, by itself, creates a new SIMPLEMATLABDEMO or raises the existing
%      singleton*.
%
%      H = SIMPLEMATLABDEMO returns the handle to a new SIMPLEMATLABDEMO or the handle to
%      the existing singleton*.
%
%      SIMPLEMATLABDEMO('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in SIMPLEMATLABDEMO.M with the given input arguments.
%
%      SIMPLEMATLABDEMO('Property','Value',...) creates a new SIMPLEMATLABDEMO or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before SimpleMatlabDemo_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to SimpleMatlabDemo_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help SimpleMatlabDemo

% Last Modified by GUIDE v2.5 06-Sep-2017 16:11:02

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
    'gui_Singleton',  gui_Singleton, ...
    'gui_OpeningFcn', @SimpleMatlabDemo_OpeningFcn, ...
    'gui_OutputFcn',  @SimpleMatlabDemo_OutputFcn, ...
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

% --- Executes just before SimpleMatlabDemo is made visible.
function SimpleMatlabDemo_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to SimpleMatlabDemo (see VARARGIN)

% Choose default command line output for SimpleMatlabDemo
handles.output = hObject;

% Update handles structure
guidata(hObject, handles);

% Load Phantom Dlls
LoadPhantomLibraries();

global GObj;
GObj.hObject = hObject;
GObj.currentCamera = 0;
GObj.liveCineHandle = [];
GObj.storedCineHandle = [];
GObj.savingCineHandle = [];
GObj.currentImage = [];
GObj.storedImageRange.First = 0;
GObj.storedImageRange.Cnt = 1;
GObj.playbackActive = false;
GObj.playActive = false;
GObj.saving = false;
GObj.saveProgress = 0;

global CameraList;
CameraList = {};

% Register client
HRES = PhLVRegisterClientEx([], PhConConst.PHCONHEADERVERSION);
if (HRES < 0)
    return;
end

%place a default simulated camera in the case of no camera connected
[HRES, camCount] = PhGetCameraCount();
if (camCount <= 0)
    PhAddSimulatedCamera(660, 1234);
end

UpdateCameraPool();
SelectCamera();
PhConfigPoolUpdate(1500);%how often to check for offline cameras

set(handles.textSaveProgress,'String', '');

%Setup and start the display/refresh timer
global gTimerRefresh;
gTimerRefresh = timer('ExecutionMode','fixedSpacing','Period',0.04);
gTimerRefresh.TimerFcn = {@timerRefresh_callbk};
StartRefreshTimer();
end

% --- Executes when user attempts to close figureMain.
function figureMain_CloseRequestFcn(hObject, eventdata, handles)
% hObject    handle to figureMain (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

try
    %Clean up resources
    StopRefreshTimer();
    global gTimerRefresh;
    delete(gTimerRefresh);
    
    DestroyStoredCine();
    DestroySavingCine();
    
    %Unregister
    try
        PhLVUnregisterClient();
    catch ex
        msgbox('Error while unregistering.','Error');
    end
    clearvars -global gTimerRefresh CameraList GObj
    UnloadPhantomLibraries();
catch ex
    ex_message = ex.message
    ex_stack_file = ex.stack(1).file
    ex_stack_line = ex.stack(1).line
    errordlg('Error while closing.','Error','modal');
end

% Hint: delete(hObject) closes the figure
delete(hObject);
end

% --- Outputs from this function are returned to the command line.
function varargout = SimpleMatlabDemo_OutputFcn(hObject, eventdata, handles)
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;
end

%% Timer events and utils
function timerRefresh_callbk(obj, event)
global GObj;
handles = guidata(GObj.hObject);

try   
    %Refresh cine save status.
    if (GObj.saving)
        [HRES GObj.saveProgress] = PhGetWriteCineFileProgress(GObj.savingCineHandle);
        if (GObj.saveProgress == 100 || HRES<0)
            GObj.saving = false;
            GObj.saveProgress = 0;
            set(handles.buttonSaveCine,'String','Save');
        end
        set(handles.textSaveProgress, 'String', [num2str(GObj.saveProgress) '%']);
        pause(0.02);
        return;%cancel image display
    end
    
    %Image refreshing
    currentImagePixels = [];
    if (GObj.playbackActive == false)
        if (~isempty(GObj.liveCineHandle))
            [currentImagePixels, isColorImage] = GetImageBuffer(GObj.liveCineHandle, 0);
        end
    else
        if (~isempty(GObj.storedCineHandle))
            [currentImagePixels, isColorImage] = GetImageBuffer(GObj.storedCineHandle, GObj.currentImage);
            if (GObj.playActive)
                GObj.currentImage = GObj.storedImageRange.First + mod(GObj.currentImage + 1 - GObj.storedImageRange.First, int32(GObj.storedImageRange.Cnt));
                set(handles.editCrtImg, 'String', GObj.currentImage);
            end
        end
    end
    
    UpdateCineStatus();
    %Check for offline camera
    if (GObj.currentCamera ~= -1)
        offline = PhOffline(GObj.currentCamera);
        if (offline)
            set(handles.textOffline,'Visible','on');
        else
            set(handles.textOffline,'Visible','off');
        end
    end
    
    %Paint image
    if (~isempty(currentImagePixels))
        if (isColorImage)
            colormap(handles.axesImgPreview, 'default');
        else
            colormap(handles.axesImgPreview, gray(2^8));
        end
        h=image(currentImagePixels,'Parent',handles.axesImgPreview, 'CDataMapping','scaled');
        axis(handles.axesImgPreview, 'off');
        axis(handles.axesImgPreview, 'image');
        
        period = double(get(obj,'InstantPeriod'));
        if (~isempty(period) && ~isnan(period))
            set(handles.textFps,'String',['Refresh speed: ' num2str(1/period) ' Hz']);
        end
    end
    
    pause(0.02);
catch ex
    timer_ex_msg = ex.message
    timer_ex_stack_file = ex.stack(1).file
    timer_ex_stack_line = ex.stack(1).line
end
end

function StartRefreshTimer()
global gTimerRefresh;
if(strcmp(get(gTimerRefresh,'Running'),'on'))
    StopRefreshTimer();
end
start(gTimerRefresh);
end

function StopRefreshTimer()
% stops the image display
global gTimerRefresh;
stop(gTimerRefresh);
end

%% UI functions
function changed = UpdateCameraPool()
%check for new cameras
global CameraList;
[HRES, camCount] = PhGetCameraCount();
currentCamCount = length(CameraList);
if (camCount > 0 && camCount > currentCamCount)%new cameras are available?
    for camNr = currentCamCount + 1 : camCount
        [HRES, serial, cameraName] = PhGetCameraID(camNr-1);
        [HRES, partCount, partitionSizes] = PhGetPartitions(camNr - 1);
        if (partCount~=1)
            PhSetPartitions(camNr - 1, 1, 100);%we only support single cine in this demo
        end
        CameraList{camNr} = ['#' num2str(camNr - 1) '. ' cameraName ' (' num2str(serial) ')'];
        changed = true;
    end
end

%Update UI
global GObj;
handles = guidata(GObj.hObject);
% populate camera popmenu with camera list
set(handles.popupmenuCameras,'String',CameraList);
set(handles.popupmenuCameras,'Value',GObj.currentCamera + 1);

%Check if current camera is offline
if (GObj.currentCamera ~= -1)
    offline = PhOffline(GObj.currentCamera);
    if (offline)
        set(handles.textOffline,'Visible','on');
    else
        set(handles.textOffline,'Visible','off');
    end
end

end

function UpdateCineStatus()
global GObj;
handles = guidata(GObj.hObject);

if (GObj.currentCamera ~= -1)
    %Get the cine status of all camera cine partitions
    [HRESULT, cs] = PhGetCineStatus(GObj.currentCamera);
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % What is the camera doing                     %%%
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    if (GObj.playbackActive)
        set(handles.textPlayback, 'Visible','on');
        set(handles.textLive, 'Visible','off');
        set(handles.textRecording, 'Visible','off');
        set(handles.textTriggered, 'Visible','off');
        
        set(handles.textFirstImg, 'Visible','on');
        set(handles.editCrtImg, 'Visible','on');
        set(handles.textLastImg, 'Visible','on');
        
        set(handles.buttonRecord,'Enable', 'off');
        set(handles.buttonSoftTrigger,'Enable', 'off');
        
        set(handles.buttonPlay,'Enable', 'on');
        set(handles.buttonStop,'Enable', 'on');
    else
        
        %
        % Not playback
        %
        set(handles.textPlayback, 'Visible','off');
        
        set(handles.textFirstImg, 'Visible','off');
        set(handles.editCrtImg, 'Visible','off');
        set(handles.textLastImg, 'Visible','off');
        
        set(handles.buttonRecord,'Enable', 'on');
        set(handles.buttonSoftTrigger,'Enable', 'on');
        
        set(handles.buttonPlay,'Enable', 'off');
        set(handles.buttonStop,'Enable', 'off');
        
        %
        % if Cine 0 (the preview Cine) is Active
        % then we are doing Preview
        %
        if (cs(1).Active)
            %
            % Preview Mode
            %
            set(handles.textLive, 'Visible','on');
            set(handles.textRecording, 'Visible','off');
            set(handles.textTriggered, 'Visible','off');
            
            set(handles.buttonRecord,'String', 'Record');
            
            %
            % if we have a Stored Cine
            % we can enable the playback button
            %
            if (cs(2).Stored == true)
                set(handles.checkPlaybackMode,'Enable', 'on');
                set(handles.buttonSaveCine,'Enable', 'on');
                set(handles.textSaveProgress,'Visible', 'on');
            else
                set(handles.checkPlaybackMode,'Enable', 'off');
                set(handles.buttonSaveCine,'Enable', 'off');
                set(handles.textSaveProgress,'Visible', 'off');
                set(handles.textSaveProgress,'String', '');
            end
        elseif (cs(2).Active)
            set(handles.textLive, 'Visible','on');
            
            set(handles.buttonRecord,'String', 'Stop Record');
            
            %
            % are we recording?
            %
            if (cs(2).Stored == false)
                set(handles.textRecording, 'Visible','on');
                
                set(handles.checkPlaybackMode,'Enable','off');
                set(handles.buttonSaveCine,'Enable', 'off');
                set(handles.textSaveProgress,'Visible', 'off');
                set(handles.textSaveProgress,'String', '');
            else
                set(handles.textRecording, 'Visible','off');
            end
            
            %
            % have we been triggered
            %
            if (cs(2).Triggered)
                set(handles.textTriggered, 'Visible','on');
            else
                set(handles.textTriggered, 'Visible','off');
            end
        else
            % some other Cine is active
            % this simple demo only supports Cine 1
            % so just turn off all status
            
            set(handles.textLive, 'Visible','off');
            set(handles.textRecording, 'Visible','off');
            set(handles.textTriggered, 'Visible','off');
            
            set(handles.checkPlaybackMode,'Enable','off');
            set(handles.buttonSaveCine,'Enable', 'off');
            
            set(handles.textSaveProgress,'Visible', 'off');
            set(handles.textSaveProgress,'String', '');
        end
    end
else
    % no cameras
    set(handles.textPlayback, 'Visible','off');
    set(handles.textLive, 'Visible','off');
    set(handles.textRecording, 'Visible','off');
    set(handles.textTriggered, 'Visible','off');
    
    set(handles.checkPlaybackMode,'Enable','off');
    set(handles.buttonSaveCine,'Enable', 'off');
    
    set(handles.textSaveProgress,'Visible', 'off');
    set(handles.textSaveProgress,'String', '');
end
end

function SelectCamera()
global GObj;
handles = guidata(GObj.hObject);
%read camera UI selection
selCamera = get(handles.popupmenuCameras,'Value');

if (selCamera>0)
    GObj.currentCamera = selCamera - 1;
    [HRES GObj.liveCineHandle] = PhGetCineLive(GObj.currentCamera);
    ReadCameraSetup();
end
end

function ReadCameraSetup()
% Read camera setup & update UI
global GObj;
handles = guidata(GObj.hObject);

ip = GetCamIPAddress(GObj.currentCamera);
[HRES, serial, cameraName] = PhGetCameraID(GObj.currentCamera);
camModel = GetCameraModel(GObj.currentCamera);

%Update UI
set(handles.editIPAddress, 'String', ip);
set(handles.editSerial, 'String', num2str(serial));
set(handles.editName, 'String', cameraName);
set(handles.editModel, 'String', camModel);

%% Read the acquisition parameters from a specified camera cine partition
[HRES, acquisitionParams, bmi] = PhGetCineParams(GObj.currentCamera, PhConConst.CINE_PREVIEW);

%% Read camera's resolutions & update UI
[HRES, resolutionCount, resolutions] = PhGetResolutions(GObj.currentCamera);
%Update resolution UI
selectedIndex = -1;
resolutionsStr = {};
currentResStr = GetResolutionStr(acquisitionParams.ImWidth, acquisitionParams.ImHeight);
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

%Update acquisition params UI
set(handles.editExposure, 'String', num2str(NanoSecToMicroSec(acquisitionParams.Exposure)));
set(handles.editFrameRate, 'String', num2str(acquisitionParams.dFrameRate));
end

%% Camera based functions
function ip = GetCamIPAddress(cameraNumber)
ip = blanks(PhConConst.MAXIPSTRSZ);
pVal = libpointer('cstring', ip);
PhGet(cameraNumber, PhConConst.gsIPAddress, pVal);
ip = pVal.Value;
end

function model = GetCameraModel(cameraNumber)
model = blanks(PhIntConst.MAXSTDSTRSZ);
pVal = libpointer('cstring', model);
PhGet(cameraNumber, PhConConst.gsModel, pVal);
model = pVal.Value;
end

%% Cinehandle basic functions
function [CurrentImagePixels, IsColorImage]= GetImageBuffer(cineHandle, currentFrame)
%Read image from cine wrapper
CurrentImagePixels = [];
IsColorImage = false;

if (isempty(cineHandle))
    return;
end

SetVFlipView(cineHandle, false);
PhSetUseCase(cineHandle, PhFileConst.UC_VIEW);

%get the image bufffer from camera
imgRange = get(libstruct('tagIMRANGE'));
imgRange.First = currentFrame;
imgRange.Cnt = 1;

%get cine image buffer size
imgSizeInBytes = GetMaxImageSizeInBytes(cineHandle);

%read cine image into the buffer
[HRES, CurrentImagePixels, imgHeader] = PhGetCineImage(cineHandle, imgRange, imgSizeInBytes);

%transform image pixels to be disaplayed in MATLAB figure
if (HRES >= 0)
    [CurrentImagePixels] = ExtractImageMatrixFromImageBuffer( CurrentImagePixels, imgHeader );
    IsColorImage = IsColorHeader(imgHeader);
    Is16bppImage = Is16BitHeader(imgHeader);
    if (IsColorImage)
        samplespp = 3;
    else
        samplespp = 1;
    end
    bps = GetEffectiveBitsFromIH(imgHeader);
    [CurrentImagePixels, unshiftedImg] = ConstructMatlabImage(CurrentImagePixels, imgHeader.biWidth, imgHeader.biHeight, samplespp, bps);
end
end

function imgSizeInBytes = GetMaxImageSizeInBytes(cineHandle)
pInfVal = libpointer('uint32Ptr',0);
PhGetCineInfo(cineHandle, PhFileConst.GCI_MAXIMGSIZE, pInfVal);
imgSizeInBytes = pInfVal.Value;
end

function SetVFlipView(cineHandle, flipV)
pInfVal = libpointer('int32Ptr',flipV);
PhSetCineInfo(cineHandle, PhFileConst.GCI_VFLIPVIEWACTIVE, pInfVal);
end

function retValue = GetFirstImageNumber(cineHandle)
%First saved/selected image number.
pInfVal = libpointer('int32Ptr',0);
PhGetCineInfo(cineHandle, PhFileConst.GCI_FIRSTIMAGENO, pInfVal);
retValue = pInfVal.Value;
end

function retValue = GetImageCount(cineHandle)
%The number of available/selected images of a cine.
pVal = libpointer('uint32Ptr',0);
PhGetCineInfo(cineHandle, PhFileConst.GCI_IMAGECOUNT, pVal);
retValue = pVal.Value;
end

%% UTILS
function resStr = GetResolutionStr(width, height)
resStr = [num2str(width) 'x' num2str(height)];
end

function [width, height] = ParseResolution(resStr)
resParts = regexp(resStr,'\x', 'split');
width = uint32(str2double(resParts{1}));
height = uint32(str2double(resParts{2}));
end

function retVal = NanoSecToMicroSec(val)
retVal = double(val)/1000;
end

function DestroyStoredCine()
global GObj;
if (~isempty(GObj.storedCineHandle))
    PhDestroyCine(GObj.storedCineHandle);
    GObj.storedCineHandle = [];
end
end

function DestroySavingCine()
global GObj;
if (~isempty(GObj.savingCineHandle))
    if (GObj.saving)
        HRES = PhStopWriteCineFileAsync(GObj.savingCineHandle);
    end
    PhDestroyCine(GObj.savingCineHandle);
    GObj.savingCineHandle = [];
end
end

%% Event Handlers
% --- Executes on selection change in popupmenuCameras.
function popupmenuCameras_Callback(hObject, eventdata, handles)
% hObject    handle to popupmenuCameras (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

global GObj;

StopRefreshTimer();

SelectCamera();

GObj.playbackActive = false;
set(handles.checkPlaybackMode, 'Value', 0);
GObj.playActive = false;
set(handles.buttonPlay, 'Value', 0);
set(handles.buttonPlay,'String','Play');

DestroyStoredCine();
DestroySavingCine();

UpdateCineStatus();

StartRefreshTimer();

end

% --- Executes on button press in buttonRefreshCamPool.
function buttonRefreshCamPool_Callback(hObject, eventdata, handles)
% hObject    handle to buttonRefreshCamPool (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

UpdateCameraPool();

end

% --- Executes on button press in buttonRecord.
function buttonRecord_Callback(hObject, eventdata, handles)
% hObject    handle to buttonRecord (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

global GObj;
[HRESULT, cs] = PhGetCineStatus(GObj.currentCamera);
if (cs(1).Active)%Preview cine is active?
    %first cine stored? Note: We support just first cine in this demo.
    if (cs(2).Stored)
        result = strcmp(questdlg('All stored cines will be deleted. Continue?', 'Delete stored cines', 'No'),'Yes');
        if (result)
            PhRecordCine(GObj.currentCamera);
        end
    else
        PhRecordCine(GObj.currentCamera);
    end
else
    %return to preview
    PhRecordSpecificCine(GObj.currentCamera, PhConConst.CINE_PREVIEW);
end

UpdateCineStatus();

end

% --- Executes on button press in buttonSoftTrigger.
function buttonSoftTrigger_Callback(hObject, eventdata, handles)
% hObject    handle to buttonSoftTrigger (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

global GObj;
[HRESULT, cs] = PhGetCineStatus(GObj.currentCamera);
%if cine 1 is active send trigger otherwise do nothing.
if (cs(2).Active)
    PhSendSoftwareTrigger(GObj.currentCamera);
end

end

% --- Executes on button press in checkPlaybackMode.
function checkPlaybackMode_Callback(hObject, eventdata, handles)
% hObject    handle to checkPlaybackMode (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of checkPlaybackMode

global GObj;
GObj.playbackActive = get(handles.checkPlaybackMode,'Value');

if (~GObj.playbackActive)
    GObj.playActive = false;
    set(handles.buttonPlay, 'Value', 0);
    set(handles.buttonPlay,'String','Play');
else
    DestroyStoredCine();
    [HRES GObj.storedCineHandle] = PhNewCineFromCamera(GObj.currentCamera, 1);
    
    GObj.storedImageRange.First = GetFirstImageNumber(GObj.storedCineHandle);
    GObj.storedImageRange.Cnt = GetImageCount(GObj.storedCineHandle);
    
    set(handles.textFirstImg, 'String', ['[' num2str(GObj.storedImageRange.First)]);
    set(handles.textLastImg, 'String', [num2str(double(GObj.storedImageRange.First) + double(GObj.storedImageRange.Cnt)) ']']);
    
    GObj.currentImage = GObj.storedImageRange.First;
    set(handles.editCrtImg, 'String', GObj.currentImage);
end

UpdateCineStatus();
end

% --- Executes on button press in buttonPlay.
function buttonPlay_Callback(hObject, eventdata, handles)
% hObject    handle to buttonPlay (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of buttonPlay

global GObj;
GObj.playActive = get(hObject,'Value');
if (GObj.playActive)
    set(handles.buttonPlay,'String','Pause');
else
    set(handles.buttonPlay,'String','Play');
end

end

% --- Executes on button press in buttonStop.
function buttonStop_Callback(hObject, eventdata, handles)
% hObject    handle to buttonStop (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
global GObj;
GObj.playActive = false;
set(handles.buttonPlay, 'Value', 0);
set(handles.buttonPlay,'String','Play');
GObj.currentImage = GObj.storedImageRange.First;
set(handles.editCrtImg, 'String', GObj.currentImage);

end

% --- Executes on button press in buttonSaveCine.
function buttonSaveCine_Callback(hObject, eventdata, handles)
% hObject    handle to buttonSaveCine (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

global GObj;
if(GObj.saving)
    HRES = PhStopWriteCineFileAsync(GObj.savingCineHandle);
    GObj.saving = false;
    set(handles.buttonSaveCine,'String','Save');
else
    DestroySavingCine();
    [HRES GObj.savingCineHandle] = PhNewCineFromCamera(GObj.currentCamera, 1);
    if (HRES>=0 && PhGetSaveCineName(GObj.savingCineHandle))
        PhSetUseCase(GObj.savingCineHandle, PhFileConst.UC_SAVE);
        HRES = PhWriteCineFileAsync(GObj.savingCineHandle);
        if (HRES >=0)
            GObj.saving = true;
            set(handles.buttonSaveCine,'String','Stop');
        end
    end
end

end

% --- Executes on button press in buttonSet.
function buttonSet_Callback(hObject, eventdata, handles)
% hObject    handle to buttonSet (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
global GObj;
camName = get(handles.editName,'string');
PhSetCameraName(GObj.currentCamera, camName);

%Set acquisition params 
[HRES, acquisitionParams, bmi] = PhGetCineParams(GObj.currentCamera, PhConConst.CINE_PREVIEW);
resolutions = get(handles.popupmenuResolutions,'String');
[ImW, ImH] = ParseResolution(resolutions{get(handles.popupmenuResolutions,'Value')});
acquisitionParams.ImWidth = uint32(ImW);
acquisitionParams.ImHeight = uint32(ImH);
acquisitionParams.Exposure = str2double(get(handles.editExposure,'String')) * 1000;
acquisitionParams.dFrameRate = str2double(get(handles.editFrameRate,'String'));
PhSetSingleCineParams(GObj.currentCamera, acquisitionParams);

%reflect parameters
ReadCameraSetup();

end

function editCrtImg_Callback(hObject, eventdata, handles)
% hObject    handle to editCrtImg (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

crtImg = str2num(get(hObject,'String'));
global GObj;
GObj.currentImage = crtImg;

end
