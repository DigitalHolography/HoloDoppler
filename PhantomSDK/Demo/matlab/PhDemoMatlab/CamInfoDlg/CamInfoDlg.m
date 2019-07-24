function varargout = CamInfoDlg(varargin)
% CAMINFODLG M-file for CamInfoDlg.fig
%      CAMINFODLG, by itself, creates a new CAMINFODLG or raises the existing
%      singleton*.
%
%      H = CAMINFODLG returns the handle to a new CAMINFODLG or the handle to
%      the existing singleton*.
%
%      CAMINFODLG('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in CAMINFODLG.M with the given input arguments.
%
%      CAMINFODLG('Property','Value',...) creates a new CAMINFODLG or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before CamInfoDlg_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to CamInfoDlg_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help CamInfoDlg

% Last Modified by GUIDE v2.5 21-Jul-2011 12:03:07

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @CamInfoDlg_OpeningFcn, ...
                   'gui_OutputFcn',  @CamInfoDlg_OutputFcn, ...
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


% --- Executes just before CamInfoDlg is made visible.
function CamInfoDlg_OpeningFcn(hObject, eventdata, handles, varargin)
% Choose default command line output for CamInfoDlg
handles.output = hObject;
if (nargin>=1 && isa(varargin{1},'Camera'))
    handles.hCamera = varargin{1};
else
    error('Figure needs camera as first parameter');
end

set(handles.editName, 'String', handles.hCamera.GetCameraName());
set(handles.editIP, 'String', handles.hCamera.GetIPAddress());
set(handles.editSerial, 'String', num2str(handles.hCamera.Serial));
set(handles.editVersion, 'String', num2str(handles.hCamera.GetCameraVersion()));
set(handles.editModel, 'String', handles.hCamera.GetCameraModel());
set(handles.editFirmware, 'String', num2str(handles.hCamera.GetFirmwareVersion()));
% Update handles structure
guidata(hObject, handles);

% make modal dialog wait for Ok or close
uiwait(handles.figureCamInfo);


% --- Executes when user attempts to close figureCamInfo.
function figureCamInfo_CloseRequestFcn(hObject, eventdata, handles)

if isequal(get(hObject, 'waitstatus'), 'waiting')
    % The GUI is still in UIWAIT, us UIRESUME
    uiresume(hObject);
else
    % The GUI is no longer waiting, just close it
    delete(hObject);
end


% --- Outputs from this function are returned to the command line.
function varargout = CamInfoDlg_OutputFcn(hObject, eventdata, handles) 

varargout{1} = handles.output;
delete(handles.figureCamInfo);

% --- Executes on button press in pushbuttonOk.
function pushbuttonOk_Callback(hObject, eventdata, handles)
cameraName = get(handles.editName,'String');
handles.hCamera.SetCameraName(cameraName);
handles.hCamera = [];
uiresume(handles.figureCamInfo);


% --- Executes on key press with focus on editName and none of its controls.
function editName_KeyPressFcn(hObject, eventdata, handles)
if (strcmp(eventdata.Key,'return'))
    cameraName = get(handles.editName,'String');
    handles.hCamera.SetCameraName(cameraName);
end

% --- Executes during object creation, after setting all properties.
function editName_CreateFcn(hObject, eventdata, handles)
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function editIP_CreateFcn(hObject, eventdata, handles)
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function editSerial_CreateFcn(hObject, eventdata, handles)
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function editVersion_CreateFcn(hObject, eventdata, handles)
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes during object creation, after setting all properties.
function editModel_CreateFcn(hObject, eventdata, handles)
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

% --- Executes during object creation, after setting all properties.
function editFirmware_CreateFcn(hObject, eventdata, handles)
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end
