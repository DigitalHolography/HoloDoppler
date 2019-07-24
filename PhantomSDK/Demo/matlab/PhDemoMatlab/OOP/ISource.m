classdef ISource < handle
    
    methods(Abstract)
        cine = CurrentCine(this)
    end
    
end

