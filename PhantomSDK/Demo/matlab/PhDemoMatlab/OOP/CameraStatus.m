classdef(Sealed) CameraStatus
    
    properties(Constant)
        NotAvailable = 1;
        Live = 2;
        RecWaitingForTrigger = 3;
        RecPostriggerFrames = 4;
        Offline = 5;
    end
    
    methods (Access = private)
        function out = CameraStatus()
        end
    end
    
end

