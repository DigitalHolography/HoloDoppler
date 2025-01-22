classdef RenderingClass < handle 
    % handles rendering
    properties
        Params RenderingParametersClass
        LastParams RenderingParametersClass
        Frames 
        FramesS
        FramesChanged logical
        spatial_filter_mask
        kernel
        H
        FH
        SH

        Output ImagesClass

        cache_intermediate_results logical
    end
    
    methods
        
        function obj = RenderingClass()
            
        end

        function obj = setFrames(obj, frames)
            obj.Frames = frames; % set
            FramesChanged = true;
        end

        function obj = Render(obj,image_types)
            Output.select(image_types);

            % Calculate the parameters difference to prevent recalculations
            fields = fieldnames(obj.Params);
            for i = 1:numel(fields)
                if isfield(obj.LastParams,fields{i})
                    IsNewParams.(fields{i}) = obj.Params.(fields{i}) ~= obj.LastParams.(fields{i}) ; 
                    % if the parameter was different 
                    
                    % there is need to recalculate
                else
                    IsNewParams.(fields{i}) = true; % need to recalculate 
                end
            end
            
            if IsNewParams.spatial_filter | obj.FramesChanged % change or if the frames changed
                if obj.Params.spatial_filter
                    if IsNewParams.spatial_filter_ratio
                        obj.spatial_filter_mask = CalculateSpatialFilterMask(obj.Params.spatial_filter_ratio);
                    end
                    obj.FramesS = ifft2(fft2(obj.Frames).*obj.spatial_filter_mask);
                else
                    obj.FramesS = [];
                end 
            end

            if IsNewParams.spatial_transformation | obj.FramesChanged % change or if the frames changed
                switch spatial_transformation
                    case 'angular spectrum'
                        if isempty(obj.FramesS)
                            obj.FH = fft2(obj.Frames) .* kernel;
                        else
                            obj.FH = fft2(obj.FramesS) .* kernel;
                        end
                    case 'Fresnel'
                        if isempty(obj.FramesS)
                            obj.FH = obj.Frames .* kernel;
                        else
                            obj.FH = obj.FramesS .* kernel;
                        end
                end
                switch spatial_transformation
                    case 'angular spectrum'
                        obj.H = ifft2(obj.FH);
                    case 'Fresnel'
                        obj.H = fftshift(fftshift(fft2(obj.FH),1),2);
                end
            end
            
            if svd_filter
                H = svd_filter(H, svd_threshold, f1, fs, svd_treshold_value, svd_stride);
            end
            
            if svdx_filter
                H = svdx_filter(H, svd_threshold, f1, fs, svd_treshold_value, svd_stride);
            end
            
            switch time_transform
                case 'PCA' 
                    SH = short_time_PCA(H);
                case 'FFT' 
                    SH = fft(H, [], 3);
            end





            FramesChanged = false; % reset 
        end

        function obj = getImages(obj,image_types)
            r = cell(1,length(image_types));
            for i = 1:length(image_types)
                r{i} = obj.Output.(image_types{i}).image;
            end
        end

    end
end