classdef HoloDopplerClass < handle
    % Main class replacing the app

    properties
        fileInfo % struct stores file information path, camera pixel pitches, dimensions, 
        reader % class obj to read new parts of the file

        currentImage % Current preview image class containing all the types of images
        Video % store all the preview images classes rendered at the end of a cycle
        Registration % store the shifts calculated to register images at the end (so that it can be reversed)

        GUIcache % struct caches the GUI parameters when rendering

        currentBatch % struct with current frames, H, FH, SH, U, S, V and cov
        frameBatchCache % struct with maximum frame batchs to process to avoid long read sequences
    end

    methods
        function obj = HoloDopplerClass(fileInfo)
            %HoloDopplerClass Construct an instance of this class
            obj.fileInfo = fileInfo;
            switch obj.fileInfo.ext
                case 'holo'
                    obj.reader = HoloReader(obj.fileInfo.path);
                case 'cine'
                    obj.reader = CineReader(obj.fileInfo.path);
            end
            obj.currentImage = HoloDopplerImage();
            obj.Video = HoloDopplerVideo();
            obj.Registration = struct();
            obj.GUIcache = struct();
            obj.currentBatch = struct();
            obj.frameBatchCache = struct();
        end

        function getGUICache(obj,GUIapp)
            %getGUICache Set the GUI cache according to the parameters from the GUI
        end

        function PreviewRendering(obj)
            %PreviewRendering Construct the image according to the current GUIcache
            obj.PreviewImage;
        end

        function VideoRendering(obj)
            %VideoRendering Construct the Video according to the current GUIcache
        end

        function RegisterVideo(obj)
            %RegisterVideo Register the current Video according to the current GUIcache

        end
    end
end