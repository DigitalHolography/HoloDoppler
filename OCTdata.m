classdef OCTdata
    properties (Access = public)
        stack
        projection_xz
        projection_xy
        range_y
        range_z

        layer_1
        layer_2
    end

    methods
        function obj = OCTdata()
            obj.range_y = 1:10;
            obj.range_z = 1:10;
            obj.stack = zeros(512,512,512);
            obj.layer_1 = [];
            obj.layer_2 = [];
        end
    end
end