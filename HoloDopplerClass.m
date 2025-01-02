classdef HoloDopplerClass < handle
    % Main class replacing the app

    properties
        fileInfo % struct stores file information path, camera pixel pitches, dimensions, 
        reader % class obj to read new parts of the file

        PreviewImage
        PreviewVideo % store all the preview images rendered at the end of a cycle
        registrationShifts % store the shifts calculated to register images at the end (so that it can be reversed)

        GUIcache % caches the GUI parameters when rendering

        currentBatch % struct with current frames, H, FH, SH, U, S, V and cov
        frameBatchCache % struct with maximum frame batchs to process to avoid long read sequences
    end

    methods
        function getGUICache(obj,cache)
            %getGUICache Set the GUI cache according to the rendering mode

        end

        function PreviewRendering(obj,inputArg1,inputArg2)
            %PreviewRendering Construct the image according to 
            obj.PreviewImage = inputArg1 + inputArg2;
        end

        function outputArg = VideoRendering(obj,inputArg)
            %METHOD1 Summary of this method goes here
            %   Detailed explanation goes here
            outputArg = obj.Property1 + inputArg;
        end
    end
end