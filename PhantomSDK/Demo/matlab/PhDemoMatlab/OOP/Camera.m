classdef Camera < handle & ISource
    %Class for controlling a Phantom camera, setting camera options or
    %parameters and reading camera info
    
    %% Properties
    properties(SetAccess = private, Hidden)
        % A camera identifier used in dlls acces. The camera order and number can be changed when NotifyDeviceChanged() is called.
        CameraNumber;
        % Serial is a unique camera id that does not change in a session. It will be buffered. Is assigned in
        % constructor.
        Serial;
        
        %Selected cine partition number (helper buffer). Used to keep track of cine partition selection.
        SelectedCinePartNo;
    end
    
    properties(Access = private, Hidden)
        % Cine from which live images are taken. Also image processing options will be read or set with this cine.
        LiveCine = [];
        %the currently selected cine from SelectedCinePartNo number
        SelectedCine = [];
    end
    
    %% Constructor
    methods
        function cam = Camera(cameraNo)
            cam.CameraNumber = cameraNo;
            % create the live cine
            % if GetSupportsRecordingCines return false the live cine will not exist
            if (cam.GetSupportsRecordingCines())
                cam.LiveCine = Cine(uint32(cam.CameraNumber), int32(PhConConst.CINE_CURRENT));
            end
            % We need camera serial whatever it is connected or not. Serial is unique, is not changing and
            % will be available when camera is offline.
            [HRES, cam.Serial, cameraName] = PhGetCameraID(cameraNo);
            cam.SelectedCinePartNo = PhConConst.CINE_PREVIEW;
            cam.SelectedCine = [];
        end
    end
    
    %% Delete
    methods
        function delete(this)
            if (~isempty(this.LiveCine))
                this.LiveCine.delete();
                this.LiveCine = [];
            end
            this.DestroySelectedCine();
        end
        
        function DestroySelectedCine(this)
            if (~isempty(this.SelectedCine))
                this.SelectedCine.delete();
                this.SelectedCine = [];
            end
        end
    end
    
    %% Selected Cine
    methods
        function SetSelectedCinePartNo(this, partNo)
            %destroys the old selected cine
            this.DestroySelectedCine();
            
            this.SelectedCinePartNo = partNo;
        end
        
        %ISource
        %Get a cine from which to read images. Can be either live cine or selected cine.
        function cine = CurrentCine(this)
            if (this.IsCinePartitionStored(this.SelectedCinePartNo))
                %if needed create the selected cine
                if (isempty(this.SelectedCine))
                    this.SelectedCine = Cine(this.CameraNumber, this.SelectedCinePartNo);
                end
                cine = this.SelectedCine;
            else
                cine = this.LiveCine;
                %the selected cine partition is not stored, destroy the cine
                this.DestroySelectedCine();
            end
        end
    end
    
    %% Main Methods
    methods
        %% CameraInfo
        function camNr = GetCameraNumber(this)
            camNr = this.CameraNumber;
        end
        
        function offline = IsOffline(this)
            [offline] = PhOffline(this.CameraNumber);
        end
        
        function cameraName = GetCameraName(this)
            [HRES, serial, cameraName] = PhGetCameraID(this.CameraNumber);
        end
        
        function SetCameraName(this, cameraNameStr)
            PhSetCameraName(this.CameraNumber, cameraNameStr);
        end
        
        function camVersion = GetCameraVersion(this)
            [HRES, camVersion ] = PhGetVersion(this.CameraNumber, PhConConst.GV_CAMERA);
        end
        
        function cameraModel = GetCameraModel(this)
            %alloc enought memory
            cameraModel = blanks(PhIntConst.MAXSTDSTRSZ);
            pVal = libpointer('cstring', cameraModel);
            PhGet(this.CameraNumber, PhConConst.gsModel, pVal);
            cameraModel = pVal.Value;
        end
        
        function fmwVersion = GetFirmwareVersion(this)
            [HRES, fmwVersion] = PhGetVersion(this.CameraNumber, PhConConst.GV_FIRMWARE);
        end
        
        function ip = GetIPAddress(this)
            ip = blanks(PhConConst.MAXIPSTRSZ);
            pVal = libpointer('cstring', ip);
            PhGet(this.CameraNumber, PhConConst.gsIPAddress, pVal);
            ip = pVal.Value;
        end
        
        %% Camera Options & Parameters
        function cameraOptions = GetCamOptions(this)
            [HRES, cameraOptions] = PhGetCameraOptions(this.CameraNumber);
        end
        
        function SetCamOptions(this, cameraOptions)
            PhSetCameraOptions(this.CameraNumber, cameraOptions);
        end
        
        function acquisitionParams = GetAcquisitionParameters(this, partNo)
            %Read the acquisition parameters from a specified camera cine partition.
            [HRES, acquisitionParams, bmi] = PhGetCineParams(this.CameraNumber, partNo);
        end
        
        function SetAcquisitionParameters(this, partNo, acquisitionParams)
            %Set the acquisition parameters to a specified camera cine partition.
            if (this.IsOnSinglePartition())
                PhSetSingleCineParams(this.CameraNumber, acquisitionParams);
            else
                PhSetCineParams(this.CameraNumber, partNo, acquisitionParams);
            end
        end
        
        function changed = ParametersExternallyChanged(this)
            %Were camera options or parameteres changed by annother connection or another application instance?
            [HRES, changed] = PhParamsChanged(this.CameraNumber);
        end
        
        function [resolutions, resCnt] = GetCameraResolutions(this)
            [HRES, resCnt, resolutions] = PhGetResolutions(this.CameraNumber);
        end
        
        function [bitDepths, cnt] = GetCameraBitDepths(this)
            [HRES, cnt, bitDepths] = PhGetBitDepths(this.CameraNumber);
        end
        
        %% Camera Partitons/Cines Infos
        function isOnSinglePart = IsOnSinglePartition(this)
            isOnSinglePart = this.GetPartitionCount()==1;
        end
        
        function cineStatuses = GetRAMCinePartitionStatus(this)
            %Get the cine status of all camera cine partitions
            [HRESULT, cineStatuses] = PhGetCineStatus(this.CameraNumber);
        end
        
        function cs = GetCinePartitionStatus(this, partNo)
            if (partNo >= PhConConst.CINE_PREVIEW && partNo < PhFirstFlashCine(this.CameraNumber))
                cstats = this.GetRAMCinePartitionStatus();
                cs = cstats(partNo+1);
            elseif (partNo <= this.GetLastFlashCineNo())
                cs = libstruct('tagCINESTATUS');
                cs.Stored = true;
            else
                cs = libstruct('tagCINESTATUS');
                cs.Stored = false;
            end
        end
        
        function isStored = IsCinePartitionStored(this, partNo)
            cs = this.GetCinePartitionStatus(partNo);
            isStored = cs.Stored;
        end
        
        
        function hasStoredRAMPart = HasStoredRAMPart(this)
            %Determine if the camera has a stored cine partition in RAM.
            if (this.GetSupportsRecordingCines())
                cstats = this.GetRAMCinePartitionStatus();
                partCount = this.GetPartitionCount();
                for i=PhConConst.CINE_FIRST:partCount
                    if (cstats(i+1).Stored)
                        hasStoredRAMPart = true;
                        return;
                    end
                end
            end
            hasStoredRAMPart = false;
        end
        
        function activePartNo = GetActiveCinePartNo(this)
            %Determine the current cine partition number where the recording is taking place.
            cstats = this.GetRAMCinePartitionStatus();
            partCount = this.GetPartitionCount();
            for i=PhConConst.CINE_PREVIEW:partCount
                if (cstats(i+1).Active)
                    activePartNo = i;
                    return;
                end
            end
            activePartNo = PhConConst.CINE_PREVIEW;
        end
        
        % Status info
        function status = GetCamStatus(this)
            %Get the status of the camera.
            if (this.IsOffline())
                status = CameraStatus.Offline;
            elseif (this.GetSupportsRecordingCines())
                activeCineNo = this.GetActiveCinePartNo();
                if (activeCineNo == PhConConst.CINE_PREVIEW)
                    status = CameraStatus.Live;
                else
                    cstats = this.GetRAMCinePartitionStatus();
                    if (cstats(activeCineNo+1).Triggered)
                        status = CameraStatus.RecPostriggerFrames;
                    else
                        status = CameraStatus.RecWaitingForTrigger;
                    end
                end
            else
                status = CameraStatus.NotAvailable;
            end
        end
        
        function [partCount, partitionSizes] = GetPartitionCount(this)
            %Get the number of camera RAM cine partitions.
            [HRES, partCount, partitionSizes] = PhGetPartitions(this.CameraNumber);
        end
        
        function SetPartitionCount(this, partitionsNo)
            %Set the number of camera RAM cine partitions.
            partitionWeights = Camera.GenerateEqualPartitionsWeights(partitionsNo);
            PhSetPartitions(this.CameraNumber, partitionsNo, partitionWeights);
        end
        
        function maxPartCount = GetMaxPartitionCount(this)
            %Get the maximum number of RAM cine partitions.
            pVal = libpointer('uint32Ptr',0);
            PhGet(this.CameraNumber, PhConConst.gsMaxPartitionCount, pVal);
            maxPartCount = pVal.Value;
        end
        
        function ramCnt = GetRamCineCount(this)
            %Get the count of the recorded cine partitions in camera RAM.
            [HRES, ramCnt, flashCnt] = PhGetCineCount(this.CameraNumber);
        end
        
        function flashCnt = GetFlashCineCount(this)
            %Get the count of the cines in camera flash/CineMag.
            [HRES, ramCnt, flashCnt] = PhGetCineCount(this.CameraNumber);
        end
        
        function lastRamCineNo = GetLastRamCineNo(this)
            lastRamCineNo = (PhConConst.CINE_FIRST + this.GetRamCineCount() - 1);
        end
        
        function firstFlashCineNo = GetFirstFlashCineNo(this)
            firstFlashCineNo = PhFirstFlashCine(this.CameraNumber);
        end
        
        function lastFlashCineNo = GetLastFlashCineNo(this)
            lastFlashCineNo = (PhFirstFlashCine(this.CameraNumber) + this.GetFlashCineCount() - 1);
        end
        
        function supportsRecCines = GetSupportsRecordingCines(this)
            %Is false when the device does not have acqusition parts.
            %As a result it will not provide live images or recording actions.
            %The device can be a CineStation.
            pVal = libpointer('int32Ptr',0);
            PhGet(this.CameraNumber, PhConConst.gsSupportsRecordingCines, pVal);
            supportsRecCines = pVal.Value~=0;
        end
        
        %% Actions
        function Record(this)
            %Deletes all stored cine partitions and start recording
            PhRecordCine(this.CameraNumber);
        end
        
        function RecordSpecificCine(this, cineNo)
            %Start recording in specified cine partition. Its content is deleted.
            PhRecordSpecificCine(this.CameraNumber, cineNo);
        end
        
        function SendSoftwareTrigger(this)
            %Send a software trigger to camera.
            PhSendSoftwareTrigger(this.CameraNumber);
        end
    end
    
    %% Util Methods
    methods
        function camStr = ToString(this)
            camStr =[this.GetCameraName() ' (' num2str(this.Serial) ')'];
        end
    end
    
    methods (Static)
        function weights = GenerateEqualPartitionsWeights(count)
            %Create equal length partition weights.
            weights = zeros(count,1,'uint32');
            for i = 1:count
                percent = 100 / double(count);
                %multiply by 100 to get 2 point precision into int weights
                weights(i) = 100 * percent;
            end
        end
    end
    
end

