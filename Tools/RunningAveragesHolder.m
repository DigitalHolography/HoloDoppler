classdef RunningAveragesHolder < handle
    properties
        running_averages
    end
    methods
        function obj = RunningAveragesHolder()
            obj.running_averages = [];
        end
        function update(obj, SH_PSD, idx, params)
            for i=1:numel(params.image_types)
                if ismember(params.image_types{i}, {'SH_avg'})
                    fprintf("idx : %d \n", idx);
                    if isempty(obj.running_averages)
                        obj.running_averages.SH = SH_PSD;
                    else
                        obj.running_averages.SH = obj.running_averages.SH + SH_PSD;
                    end
                end
            end
        end
    end
end
