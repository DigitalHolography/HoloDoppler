classdef RenderingClass < handle
    % handles rendering
    properties
        LastParams struct
        Frames uint8
        FramesChanged logical
        SpatialFilterMask logical
        SpatialKernel single
        PhaseFactor single
        FH single
        H single
        SH single
        Output ImageTypeList2
    end

    methods

        function obj = RenderingClass()
            obj.Output = ImageTypeList2();
            obj.setInitParams();
        end

        function setInitParams(obj)

            Params = struct();
            Params.fs = 1; % camera frame rate
            Params.lambda = 852e-9;
            Params.ppx = 20e-6; % pixel pitch of the camera
            Params.ppy = 20e-6;

            Params.spatial_filter = false;
            Params.spatial_filter_range = [0, 1];
            Params.spatial_transformation = "Fresnel";
            Params.spatial_propagation = 0.5;
            Params.svd_filter = 1;
            Params.svdx_filter = false;
            Params.svd_threshold = false;
            Params.svd_stride = [];
            Params.time_transform = "FFT";
            Params.time_range = [0.1,0.5];
            Params.flatfield_gw = 0;
            obj.LastParams = Params;

        end

        function obj = setFrames(obj, frames)
            obj.Frames = frames; 
            obj.FramesChanged = true;
        end

        function showFramesHistogram(obj)
            figure(45);histogram(obj.Frames);
        end

        function obj = freeCache(obj)
            obj.FH = []; 
            obj.H = []; 
            obj.SH = []; 
            obj.FramesChanged = true;
        end

        function obj = Render(obj,Params, image_types, options)
            arguments
                obj
                Params struct % contains all the parameters required for the rendering
                image_types cell % list of chars containing the name of the outputs
                options.cache_intermediate_results logical = true 
            end
            obj.Output.select(image_types{:});

            % Calculate the parameters difference to prevent recalculations
            fields = fieldnames(Params);
            for i = 1:numel(fields)
                if isfield(obj.LastParams,fields{i})
                    ParamChanged.(fields{i}) = Params.(fields{i}) ~= obj.LastParams.(fields{i}) ;
                    % if the parameter was different
                    % there is need to recalculate
                else
                    ParamChanged.(fields{i}) = true; % need to recalculate
                end
            end

            %Fill with the last output params if none given
            fields = fieldnames(obj.LastParams);
            for i = 1:numel(fields)
                if ~isfield(Params,fields{i})
                    ParamChanged.(fields{i}) = true; % need to calculate
                    Params.(fields{i}) = obj.LastParams.(fields{i});
                end
            end

            obj.LastParams = Params;

            if ParamChanged.spatial_filter | ParamChanged.spatial_filter_range | obj.FramesChanged % change or if the frames changed
                if Params.spatial_filter
                    if ParamChanged.spatial_filter_range | obj.FramesChanged
                        [NY,NX,~] = size(obj.Frames);
                        obj.SpatialFilterMask = fftshift(diskMask(NY,NX,Params.spatial_filter_range(:)));
                    end
                    obj.Frames = ifft2(fft2(obj.Frames).*obj.SpatialFilterMask);
                end
            end

            if ParamChanged.spatial_filter | ParamChanged.spatial_filter_range | ParamChanged.spatial_transformation | ParamChanged.spatial_propagation | obj.FramesChanged % change or if the frames changed
                switch Params.spatial_transformation
                    case "angular spectrum"
                        if ParamChanged.spatial_propagation | ParamChanged.spatial_transformation
                            [NY,NX,~] = size(obj.Frames);
                            obj.SpatialKernel = propagation_kernelAngularSpectrum(NX,NY,Params.spatial_propagation,Params.lambda,Params.ppx,Params.ppy,0);
                        end
                        obj.FH = single(fft2(obj.Frames)) .* obj.SpatialKernel;
                    case "Fresnel"
                        if ParamChanged.spatial_propagation | ParamChanged.spatial_transformation
                            [NY,NX,~] = size(obj.Frames);
                            [obj.SpatialKernel,obj.PhaseFactor] = propagation_kernelFresnel(NX,NY,Params.spatial_propagation,Params.lambda,Params.ppx,Params.ppy,0);
                        end
                        obj.FH = single(obj.Frames) .* obj.SpatialKernel;
                    case "None"
                        obj.FH = [];
                        
                end
                switch Params.spatial_transformation
                    case "angular spectrum"
                        obj.H = ifft2(obj.FH);
                    case "Fresnel"
                        obj.H = fftshift(fftshift(fft2(obj.FH),1),2);
                    case "None"
                        obj.H = single(obj.Frames);
                end
            end

            if ~ options.cache_intermediate_results
                obj.FH = [];
            end

            if ParamChanged.spatial_filter | ParamChanged.spatial_filter_range | ParamChanged.spatial_transformation | ParamChanged.spatial_propagation | ParamChanged.svd_filter | ParamChanged.svd_threshold | ParamChanged.time_range  | obj.FramesChanged
                if Params.svd_filter
                    obj.H = svd_filter(obj.H, Params.svd_threshold, Params.time_range(1), Params.fs, Params.svd_stride);
                end
            end

            if ParamChanged.spatial_filter | ParamChanged.spatial_filter_range | ParamChanged.spatial_transformation | ParamChanged.spatial_propagation | ParamChanged.svdx_filter | ParamChanged.svd_threshold | ParamChanged.time_range  | obj.FramesChanged
                if Params.svdx_filter
                    obj.H = svd_x_filter(obj.H,Params.svd_threshold, Params.time_range(1), Params.fs, Params.svd_stride);
                end
            end

            if ParamChanged.spatial_filter | ParamChanged.spatial_filter_range | ParamChanged.spatial_transformation | ParamChanged.spatial_propagation | ParamChanged.svd_filter | ParamChanged.svdx_filter | ParamChanged.svd_threshold | ParamChanged.time_range  | ParamChanged.time_transform | obj.FramesChanged
                switch Params.time_transform
                    case 'PCA'
                        obj.SH = short_time_PCA(obj.H);
                    case 'ICA'
                        obj.SH = short_time_ICA(obj.H);
                    case 'FFT'
                        obj.SH = fft(obj.H, [], 3);
                    case 'None'
                        obj.SH = obj.H;
                end
            end

            if ~ options.cache_intermediate_results
                obj.H = [];
            end

            obj.SH = permute(obj.SH, [2 1 3]); % x<->y transpose due to the lens imaging

            if ~ options.cache_intermediate_results
                obj.SH = [];
            end

            obj.Output.construct_image(Params,obj.SH);

            obj.FramesChanged = false; % reset

        end

        function r = constructImages(obj,image_types)
            arguments
                obj
                image_types cell % list of chars image types
            end
            
            r = cell(1,numel(image_types));
            for i = 1:length(image_types)
                if ~isprop(obj.Output,image_types{i})
                    error(sprintf("%s isnt a known image type try any of [ %s ]",image_types{i},sprintf("%s,",string(fields(obj.Output)))));
                end
            end
            obj.Output.select(image_types{:});

            obj.Output.construct_image(obj.LastParams,obj.SH);

            for i = 1:length(image_types)
                if ~isprop(obj.Output,image_types{i})
                    error(sprintf("%s isnt a known image type try any of [ %s ]",image_types{i},sprintf("%s,",string(fields(obj.Output)))));
                end
                r{i} = mat2gray(obj.Output.(image_types{i}).image);
            end

            
        end


        function r = getImages(obj,image_types)
            arguments
                obj
                image_types cell % list of chars image types
            end
            r = cell(1,numel(image_types));
            for i = 1:length(image_types)
                if ~isprop(obj.Output,image_types{i})
                    error(sprintf("%s isnt a known image type try any of [ %s ]",image_types{i},sprintf("%s,",string(fields(obj.Output)))));
                end
                r{i} = mat2gray(obj.Output.(image_types{i}).image);
            end
        end


        function showFirstFrame(obj)
            figure(1); imshow(rescale(obj.Frames(:,:,1)));
        end

        function selfTesting(obj)
            obj.freeCache();
            obj.setFrames(rescale(rand(10,20,30,'single')));

            obj.setInitParams();

            obj.Render(struct(),{"power_Doppler"});
            obj.Render(struct("spatial_transformation","angular spectrum"),{"power_Doppler"});
            obj.Render(struct("time_transform","PCA"),{"pure_PCA"});
            obj.Render(struct(),{"power_Doppler"});
            obj.Render(struct(),{"directional_Doppler"});
            %montage(obj.constructImages({'directional_Doppler'}));
            obj.Render(struct("time_transform","ICA"),{"directional_Doppler"});

        end

    end
end