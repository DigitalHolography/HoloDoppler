classdef PoolBuilder < handle
    
    properties(SetAccess = private)
        StgAndLogFolder = [];
        IsRegistered = false;
    end
    
    methods
        function poolBuilderObj = PoolBuilder(stgAndLogFolder)
            this.StgAndLogFolder = stgAndLogFolder;
            this.IsRegistered = false;
        end
        
        function HRES = Register(this)
            HRES = PhLVRegisterClientEx(this.StgAndLogFolder, PhConConst.PHCONHEADERVERSION);
            % if no errors eccoured during register mark as registered
            if (HRES >= 0)
                this.IsRegistered = true;
            end
            PhConfigPoolUpdate(1500);
        end
        
        function HRES = Unregister(this)
            HRES = PhLVUnregisterClient();
        end
    end
end

