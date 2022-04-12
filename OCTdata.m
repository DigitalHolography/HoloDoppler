classdef OCTdata
    properties (Access = public)
        stack
        range_y
        range_z
        projection_xz
        projection_xy
    end

    methods
        function obj = OCTdata()
            obj.range_y = 1 : 10;
            obj.range_z = 1 : 10;
        end
    end
end