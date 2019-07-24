classdef Cine < handle
%A class that encapsulates a cine handle.
    
    %% Properties
    properties (Constant)
        PREVIEW_NAME = 'Preview';
    end
    
    properties(Access = private)
        CineHandle = [];
    end
    
    properties(SetAccess = private)
        IsLive;
    end
    
    %% Constructor
    methods (Access = public)
        function cine = Cine(varargin)
            if (nargin == 1)
                arg1 = varargin{1};
                %file cine constructor
                if (ischar(arg1))
                    [HRES cine.CineHandle] = PhNewCineFromFile(arg1);
                    cine.IsLive = false;
                elseif (isa(arg1, 'Cine'))
                    %COPY CONSTRUCTOR
                    cineObj = arg1;
                    cine.CineHandle = 0;
                    if (cineObj.CineHandle~=0)
                        if (cineObj.IsLive)
                            cine.CineHandle = cineObj.CineHandle;
                        else
                            [HRES, cine.CineHandle] = PhDuplicateCine(cineObj.CineHandle);
                        end
                    end
                    cine.IsLive = cineObj.IsLive;
                else
                    error('Bad parameter type');
                end
            elseif (nargin == 2)
                %camera cine constructor
                arg1 = varargin{1};
                arg2 = varargin{2};
                if (isfinite(arg1) && isfinite(arg2) && isscalar(arg1) && isscalar(arg2))
                    cameraNumber = uint32(arg1);
                    cineNumber = int32(arg2);
                    if (cineNumber == PhConConst.CINE_PREVIEW || cineNumber < PhConConst.CINE_CURRENT)
                        error('Bad cine number');
                    end
                    if (cineNumber == PhConConst.CINE_CURRENT)
                        %Live cine case
                        [HRES cine.CineHandle] = PhGetCineLive(cameraNumber);
                        cine.IsLive = true;
                    else
                        [HRES cine.CineHandle] = PhNewCineFromCamera(cameraNumber, cineNumber);
                        cine.IsLive = false;
                    end
                else
                    error('Bad parameter type');
                end
            else
                error('Arguments number mismatch');
            end
        end
    end
    
    %% Methods
    methods (Access = public)
        %% CineHandle manipulation
        function delete(this)
            if (this.CineHandle~=0 && ~this.IsLive)
                PhDestroyCine(this.CineHandle);
            end
        end
        
        %% GeneralInfo
        %First saved image number.
        function retValue = GetFirstImageNumber(this)
            pInfVal = libpointer('int32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_FIRSTIMAGENO, pInfVal);
            retValue = pInfVal.Value;
        end
        
        %The number of images a cine contains.
        function retValue = GetImageCount(this)
            pVal = libpointer('uint32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_IMAGECOUNT, pVal);
            retValue = pVal.Value;
        end
        
        %The number of frames after the trigger.
        function retValue = GetPostTriggerFrames(this)
            pInfVal = libpointer('uint32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_POSTTRIGGER, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function retValue = GetLastImageNumber(this)
            retValue = int32(double(this.GetFirstImageNumber()) + double(this.GetImageCount()) - 1);
        end
        
        %Trigger delay in frames.
        %Setting postrigger frames larger than cine partition image
        %capacity will work as a trigger delay.
        function retValue = GetTriggerDelay(this)
            if (this.GetPostTriggerFrames() <= this.GetImageCount())
                retValue = 0;
            else
                retValue = this.GetPostTriggerFrames() - this.GetImageCount();
            end
        end
        
        function retValue = GetCameraSerial(this)
            pInfVal = libpointer('int32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_CAMERASERIAL, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function retValue = GetCameraVersion(this)
            pInfVal = libpointer('int32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_CAMERAVERSION, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function retValue = GetFileType(this)
            pInfVal = libpointer('int32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_FROMFILETYPE, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function retValue = IsFileCine(this)
            pInfVal = libpointer('int32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_ISFILECINE, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function retValue = HasMetaWB(this)
            pInfVal = libpointer('int32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_WBISMETA, pInfVal);
            retValue = (pInfVal.Value~=0);
        end
        
        %% UseCase
        function cineUseCaseID = GetUseCase(this)
            [HRES cineUseCaseID] = PhGetUseCase(this.CineHandle);
        end
        
        function SetUseCase(this, CineUseCaseID)
            PhSetUseCase(this.CineHandle, CineUseCaseID);
        end
        
        %% Cine Metadata
        function retValue = IsColor(this)
            pInfVal = libpointer('int32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_ISCOLORCINE, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function retValue = Is16Bpp(this)
            pInfVal = libpointer('int32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_IS16BPPCINE, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function retValue = GetBppReal(this)
            pInfVal = libpointer('int32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_REALBPP, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function retValue = GetImWidth(this)
            pInfVal = libpointer('int32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_IMWIDTH, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function retValue = GetImHeight(this)
            pInfVal = libpointer('int32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_IMHEIGHT, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function retValue = GetFrameRate(this)
            pInfVal = libpointer('uint32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_FRAMERATE, pInfVal);
            retValue = pInfVal.Value;
        end
        
        %Note: retValueurns exposure in ns
        function retValue = GetExposure(this)
            pInfVal = libpointer('uint32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_EXPOSURENS, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function retValue = GetEDRExposureNs(this)
            pInfVal = libpointer('uint32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_EDREXPOSURENS, pInfVal);
            retValue = pInfVal.Value;
        end
        
        %% ImageProcessing
        function retValue = GetBrightness(this)
            pInfVal = libpointer('singlePtr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_BRIGHT, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function SetBrightness(this, value)
            pInfVal = libpointer('singlePtr',value);
            PhSetCineInfo(this.CineHandle, PhFileConst.GCI_BRIGHT, pInfVal);
        end
        
        function retValue = GetContrast(this)
            pInfVal = libpointer('singlePtr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_CONTRAST, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function SetContrast(this, value)
            pInfVal = libpointer('singlePtr',value);
            PhSetCineInfo(this.CineHandle, PhFileConst.GCI_CONTRAST, pInfVal);
        end
        
        function retValue = GetGamma(this)
            pInfVal = libpointer('singlePtr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_GAMMA, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function SetGamma(this, value)
            pInfVal = libpointer('singlePtr',value);
            PhSetCineInfo(this.CineHandle, PhFileConst.GCI_GAMMA, pInfVal);
        end
        
        function retValue = GetSaturation(this)
            pInfVal = libpointer('singlePtr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_SATURATION, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function SetSaturation(this, value)
            pInfVal = libpointer('singlePtr',value);
            PhSetCineInfo(this.CineHandle, PhFileConst.GCI_SATURATION, pInfVal);
        end
        
        function retValue = GetHue(this)
            pInfVal = libpointer('singlePtr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_HUE, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function SetHue(this, value)
            pInfVal = libpointer('singlePtr',value);
            PhSetCineInfo(this.CineHandle, PhFileConst.GCI_HUE, pInfVal);
        end
        
        function retValue = GetSensitivity(this)
            pInfVal = libpointer('singlePtr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_GAIN16_8, pInfVal);
            retValue = pInfVal.Value;
        end
        
        function wbValue = GetWhiteBalanceGain(this)
            wbValue = libstruct('tagWBGAIN');
            pInfVal = libpointer('tagWBGAIN', wbValue);
            if(this.HasMetaWB())
                PhGetCineInfo(this.CineHandle, PhFileConst.GCI_WB, pInfVal);%get the WB applied before image interpolation (on raw image)
            else
                PhGetCineInfo(this.CineHandle, PhFileConst.GCI_WBVIEW, pInfVal);%get the WB applied on already interpolated images
            end
            wbValue = pInfVal.Value;
        end
        
        function SetWhiteBalanceGain(this, wbValue)
            pWBVal= libpointer('tagWBGAIN', wbValue);
            if (this.HasMetaWB())
                PhSetCineInfo(this.CineHandle, PhFileConst.GCI_WB, pWBVal);%will be set before image interpolation (on raw image)
            else
                PhSetCineInfo(this.CineHandle, PhFileConst.GCI_WBVIEW, pWBVal);%will be set on already interpolated images
            end
        end
        
        %% GetImage
        function [HRES, pixels, IH] = GetCineImage(this, imgRange, bufferSize)
            [HRES, pixels, IH] = PhGetCineImage(this.CineHandle, imgRange, bufferSize);
        end
        
        function imgSizeInBytes = GetMaxImageSizeInBytes(this)
            pInfVal = libpointer('uint32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_MAXIMGSIZE, pInfVal);
            imgSizeInBytes = pInfVal.Value;
        end
        
        function SetVFlipView(this, flipV)
            pInfVal = libpointer('int32Ptr',flipV);
            PhSetCineInfo(this.CineHandle, PhFileConst.GCI_VFLIPVIEWACTIVE, pInfVal);
        end
        
        function dlgRes = GetSaveCineName(this)
            %will show the dialog to browse for a file where the cine will be saved.
            dlgRes = (PhGetSaveCineName(this.CineHandle) ~= 0);
        end
        
        function [HRES] = StartSaveCineAsync(this)
            HRES = PhWriteCineFileAsync(this.CineHandle);
        end
        
        function [HRES] = StopSaveCineAsync(this)
            [HRES] = PhStopWriteCineFileAsync(this.CineHandle);
        end
        
        function [HRES progress] = GetSaveCineFileProgress(this)
            [HRES progress] = PhGetWriteCineFileProgress(this.CineHandle);
        end
        
        function [error] = GetSaveCineError(this)
            pInfVal = libpointer('int32Ptr',0);
            PhGetCineInfo(this.CineHandle, PhFileConst.GCI_WRITEERR, pInfVal);
            error = pInfVal.Value;
        end
    end
    
    %% Utils
    methods (Access = public, Static)
        function cineNo = ParseCineNo(cineStr, camNr)
            if (strcmp(cineStr,Cine.PREVIEW_NAME))
                cineNo = PhConConst.CINE_PREVIEW;
            elseif (strcmp(cineStr(1), 'F'))
                %the cine is from flash
                cineNo = int32(str2double(cineStr(2:length(cineStr))));
                cineNo = int32(PhFirstFlashCine(camNr)) + cineNo - 1;%flash cine number
            else
                %the cine is from ram
                cineNo = int32(str2double(cineStr(1:length(cineStr))));
            end
        end
        
        function cineStr = GetStringForCineNo(cineNo, camNr)
            if (cineNo == PhConConst.CINE_PREVIEW)
                cineStr = Cine.PREVIEW_NAME;
            elseif(cineNo >= PhFirstFlashCine(camNr))
                cineStr = ['F' num2str(cineNo - PhFirstFlashCine(camNr) + 1)];
            else
                cineStr = num2str(cineNo);
            end
        end
    end
    
end

