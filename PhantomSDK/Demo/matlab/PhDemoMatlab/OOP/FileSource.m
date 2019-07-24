classdef FileSource < handle & ISource
    
    properties(Access = private)
        AttachedCine = [];
    end
    properties(SetAccess = private)
        FilePath = [];
    end
    
    methods
        function fileSrc = FileSource(cineFilePath)
            fileSrc.AttachedCine = Cine(cineFilePath);
            fileSrc.FilePath = cineFilePath;
        end
        
        %ISource
        function cine = CurrentCine(this)
            cine = this.AttachedCine;
        end
    end
    
end

