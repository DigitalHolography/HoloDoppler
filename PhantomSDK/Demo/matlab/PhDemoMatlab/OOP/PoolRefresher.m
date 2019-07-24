classdef PoolRefresher < handle
    %Class to manage the online list of cameras
    
    properties(Access = private)
        CameraList = {};
    end
    
    methods
        function poolRefresher = PoolRefresher()
            [HRES, camCount] = PhGetCameraCount();
            if (camCount <= 0)
                %place a default simulated camera in the case of no camera
                %connected at startup
                PhAddSimulatedCamera(660, 1234);
            end
        end
        
        function cam = GetCameraAt(this, camIndex)
            if (camIndex>=1 && camIndex<=length(this.CameraList))
                cam = this.CameraList{camIndex};
            else
                cam = [];
            end
        end
        
        function camListLength = GetCameraListLength(this)
            camListLength = length(this.CameraList);
        end
        
        function changed = RefreshCameras(this)
            changed = this.UpdateCameraList();
        end
    end
    
    methods(Access = private)
        function changed = UpdateCameraList(this)
            changed = false;
            [HRES, camCount] = PhGetCameraCount();
            currentCamCount = this.GetCameraListLength();
            if (camCount > 0 && camCount > currentCamCount)
                for camNr = currentCamCount+1:camCount
                    cam = Camera(camNr-1);
                    this.CameraList{camNr} = cam;
                    changed = true;
                end
            end
        end
    end
    
end

