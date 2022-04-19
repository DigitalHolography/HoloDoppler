classdef OCTdata
    properties (Access = public)
        stack
        projection_xz
        projection_xy
        range_y
        range_z
    end

    methods
        function obj = OCTdata()
            obj.range_y = 1:10;
            obj.range_z = 1:10;
            obj.stack = zeros(512,512,512);
        end
    end
end