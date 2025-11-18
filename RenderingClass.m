classdef RenderingClass < handle
% handles rendering
properties
    LastParams struct
    Frames
    FramesChanged logical
    SpatialFilterMask logical
    SpatialKernel single
    PhaseFactor single
    ShackHartmannMask single
    moment_chunks_crop_array single
    FH single
    H single
    SH single
    cov single
    U single
    Output ImageTypeList2
end

methods

    function obj = RenderingClass()
        obj.Output = ImageTypeList2();
        obj.setInitParams();
    end

    function setInitParams(obj)
        % set the initial parameters for all the parameters used in this class

        Params = struct();
        Params.fs = 1; % camera frame rate
        Params.lambda = 852e-9;
        Params.ppx = 20e-6; % pixel pitch of the camera
        Params.ppy = 20e-6;

        Params.spatial_filter = false;
        Params.hilbert_filter = false;
        Params.spatial_filter_range = [0, 1];
        Params.spatial_transformation = "Fresnel";
        Params.spatial_propagation = 0.5;
        Params.svd_filter = 1;
        Params.svdx_filter = false;
        Params.svdx_t_filter = false;
        Params.svdx_Nsub = 32;
        Params.svdx_t_Nsub = 32;
        Params.svdx_threshold = 10;
        Params.svdx_t_threshold = 100;
        Params.svd_threshold = false;
        Params.svd_mean = false;
        Params.svd_stride = [];
        Params.time_transform = "FFT";
        Params.time_range = [6, 10.5];
        Params.index_range = [3, 10];
        Params.time_range_extra = -1;
        Params.buckets_ranges = [[4; 18.3], [6; 18.3]];
        Params.buckets_raw = false;
        Params.flatfield_gw = 35;
        Params.flip_y = false;
        Params.flip_x = false;
        Params.square = true;
        Params.ShackHartmannCorrection = [];
        obj.LastParams = Params;

    end

    function obj = setFrames(obj, frames)
        obj.Frames = frames;
        obj.FramesChanged = true;
    end

    function showFramesHistogram(obj)

        try
            figure(45); histogram((obj.Frames)); title('Frames histogram');
        catch
            close(45);
        end

    end

    function obj = freeCache(obj)
        obj.FH = [];
        obj.H = [];
        obj.SH = [];
        obj.FramesChanged = true;
    end

    function obj = Render(obj, Params, image_types, options)

        arguments
            obj
            Params struct % contains all the parameters required for the rendering
            image_types cell % list of chars containing the name of the outputs
            options.cache_intermediate_results logical = false % whether to cache intermediate results
        end

        % Calculate the parameters difference to prevent recalculations
        fields = fieldnames(Params);

        for i = 1:numel(fields)

            if isfield(obj.LastParams, fields{i})
                changedParams.(fields{i}) = ~isequal(Params.(fields{i}), obj.LastParams.(fields{i}));
                % if the parameter was different
                % there is need to recalculate
            else
                changedParams.(fields{i}) = true; % need to recalculate
            end

        end

        % Fill with the last output params if none given
        fields = fieldnames(obj.LastParams);

        for i = 1:numel(fields)

            if ~isfield(Params, fields{i})
                changedParams.(fields{i}) = false; % by default user should not need to calculate
                Params.(fields{i}) = obj.LastParams.(fields{i});
            end

        end

        ecoMode = ~options.cache_intermediate_results;
        obj.Output.select(image_types{:});

        % Variables used to determine if recalculation is needed
        [Nx, Ny, batch_size] = size(obj.Frames);
        Nmax = max(Nx, Ny);

        % Camera Params
        fs = Params.fs;
        lambda = Params.lambda;
        ppx = Params.ppx;
        ppy = Params.ppy;

        % Filters Params
        hilbertFilter = Params.hilbert_filter;
        spatialFilter = Params.spatial_filter;
        spatialFilterRange = Params.spatial_filter_range;

        % Time Params
        time_range = Params.time_range;
        f1 = time_range(1);
        timeTransform = Params.time_transform; % Short-time transformation

        % Spatial transformation Params
        spatialTransform = Params.spatial_transformation;
        spatialPropa = Params.spatial_propagation;

        % ShackHartmann Params
        flatfield_gw = Params.flatfield_gw;
        SHCorrection = Params.ShackHartmannCorrection;

        % SVD Params
        doSVD_filter = Params.svd_filter;
        doSVDx_filter = Params.svdx_filter;
        doSVDx_t_filter = Params.svdx_t_filter;
        svdx_Nsub = Params.svdx_Nsub;
        svdx_t_Nsub = Params.svdx_t_Nsub;
        svdx_threshold = Params.svdx_threshold;
        svdx_t_threshold = Params.svdx_t_threshold;
        svd_threshold = Params.svd_threshold;
        svd_mean = Params.svd_mean;
        svd_stride = Params.svd_stride;

        % Flip Params
        flip_y = Params.flip_y;
        flip_x = Params.flip_x;

        % 1) Apply corrections to interferograms
        newFilter = changedParams.spatial_filter ...
            || changedParams.hilbert_filter ...
            || changedParams.spatial_filter_range;

        doFrames = newFilter || obj.FramesChanged;

        if doFrames % change or if the frames changed

            if hilbertFilter
                tmp = obj.Frames;
                tmp = reshape(tmp, Nx * Ny, batch_size);
                tmp = hilbert(tmp);
                obj.Frames = reshape(tmp, Nx, Ny, batch_size);
                clear tmp;
            end

            if spatialFilter

                if changedParams.spatial_filter_range ...
                        || obj.FramesChanged ...
                        || isempty(obj.SpatialFilterMask)
                    disk = diskMask(Nx, Ny, spatialFilterRange(1), spatialFilterRange(2));
                    obj.SpatialFilterMask = fftshift(disk)';
                end

                obj.Frames = ifft2(fft2(obj.Frames) .* obj.SpatialFilterMask);
            end

        end

        % 2) Spatial transformation (from Frames to H)

        newSpatialTransformation = ...
            changedParams.spatial_transformation ...
            || changedParams.spatial_propagation;

        doFH = doFrames || newSpatialTransformation ...
            || changedParams.ShackHartmannCorrection ...
            || ecoMode;

        if doFH % change or if the frames changed

            switch spatialTransform
                case "angular spectrum"

                    if changedParams.spatial_propagation ...
                            || changedParams.spatial_transformation ...
                            || isempty(obj.SpatialKernel)
                        obj.SpatialKernel = propagation_kernelAngularSpectrum(Nmax, Nmax, spatialPropa, lambda, ppx, ppy, 0);
                    end

                    obj.FH = fft2(single(pad3DToSquare(obj.Frames))); % zero pading in a square of max(Nx Ny) size
                    obj.FH = obj.FH .* fftshift(obj.SpatialKernel);

                case "Fresnel"

                    if changedParams.spatial_propagation ...
                            || changedParams.spatial_transformation ...
                            || isempty(obj.SpatialKernel)
                        [obj.SpatialKernel, obj.PhaseFactor] = propagation_kernelFresnel(Ny, Nx, spatialPropa, lambda, ppx, ppy, 0);
                    end

                    obj.FH = single(obj.Frames) .* obj.SpatialKernel;

                case "None"

                    obj.FH = [];

            end

            if ~isempty(SHCorrection) % apply ShackHartmann correction

                if ~Params.applyshackhartmannfromref || isempty(obj.ShackHartmannMask) % in case we apply ShackHartmann from precalculated Mask

                    if doFH || changedParams.ShackHartmannCorrection || isempty(obj.ShackHartmannMask)

                        [obj.ShackHartmannMask, obj.moment_chunks_crop_array] = ...
                            calculate_shackhartmannmask(obj.FH, spatialTransform, spatialPropa, time_range, fs, flatfield_gw, SHCorrection);
                    end

                end

                if ~isempty(obj.ShackHartmannMask)
                    obj.FH = obj.FH .* obj.ShackHartmannMask;
                end

            else
                obj.ShackHartmannMask = [];
            end

        end

        obj.Output.construct_image_from_ShackHartmann(obj.moment_chunks_crop_array, obj.ShackHartmannMask);
        obj.Output.construct_image_from_FH(obj.LastParams, obj.FH);

        % 3) Inverse spatial transformation (from FH to H)

        SVDParamsChanged = ...
            changedParams.svd_filter ...
            || changedParams.svd_threshold ...
            || (svd_threshold == 0 && changedParams.time_range);

        newSVDxParams = (changedParams.svdx_threshold || changedParams.svdx_Nsub);
        SVDxParamsChanged = ...
            (doSVDx_filter && newSVDxParams) ...
            || (doSVDx_t_filter && newSVDxParams) ...
            || changedParams.svdx_filter ...
            || changedParams.svdx_t_filter;

        doH = doFH ...
            || SVDParamsChanged ...
            || SVDxParamsChanged ...
            || ecoMode;

        if doH % change or if the frames changed

            switch spatialTransform
                case "angular spectrum"
                    obj.H = ifft2(obj.FH) .* sqrt(Nx * Ny);
                case "Fresnel"
                    obj.H = fftshift(fftshift(fft2(obj.FH), 1), 2) ./ sqrt(Nx * Ny); %.*obj.PhaseFactor;
                case "None"
                    obj.H = single(obj.Frames);
            end

            if doSVD_filter
                [obj.H, obj.cov, obj.U] = svd_filter(obj.H, svd_threshold, f1, fs, svd_stride, svd_mean);

            end

        end

        if ecoMode
            obj.FH = [];
        end

        if ~doSVD_filter
            obj.cov = [];
            obj.U = [];
        end

        obj.Output.construct_image_from_SVD(obj.cov, obj.U, size(obj.H));

        if doH

            if doSVDx_filter
                obj.H = svd_x_filter(obj.H, svdx_threshold, f1, fs, floor(max(size(obj.H, 1), size(obj.H, 2)) / svdx_Nsub)); % forced
            end

            if doSVDx_t_filter
                obj.H = svd_x_t_filter(obj.H, svdx_t_threshold, f1, fs, floor(max(size(obj.H, 1), size(obj.H, 2)) / svdx_t_Nsub));
            end

        end

        % 4) Short-time transformation

        doSH = doH ...
            || changedParams.time_transform ...
            || changedParams.flip_y ...
            || changedParams.flip_x ...
            || ecoMode;

        if doSH

            switch timeTransform
                case 'PCA'
                    obj.SH = short_time_PCA(obj.H);
                case 'ICA'
                    obj.SH = short_time_ICA(obj.H);
                case 'FFT'
                    obj.SH = fft(obj.H, [], 3) ./ sqrt(batch_size);
                case 'autocorrelation'
                    [a, b, c] = size(obj.H);
                    tmp = reshape(obj.H, a * b, c);
                    out = arrayfun(@(lm) xcorr(tmp(lm, :), 'normalized'), (1:a * b), 'UniformOutput', false);

                    obj.SH = permute(reshape(cell2mat(out), [], a, b), [2 3 1]);
                    %obj.SH = obj.SH(:,:,c/2:(c/2+c-1));
                case 'intercorrelation'
                    obj.SH = intercorrel(obj.H, 3); %TODO Replace template 3
                case 'phase difference'
                    a = angle(obj.H);
                    obj.SH = a; %(:, :, 1:2:end) -a(:, :, 2:2:end);
                case 'None'
                    obj.SH = obj.H;
            end

        end

        %%% obj.SH = svd_filter(obj.SH, 10);

        if ecoMode
            obj.H = [];
        end

        if doSH

            obj.SH = flip(permute(obj.SH, [2 1 3]), 2); % x<->-y transpose due to the lens imaging

            if flip_y
                obj.SH = flip(obj.SH, 1);
            end

            if flip_x
                obj.SH = flip(obj.SH, 2);
            end

        end

        % 5) Construct output images
        obj.Output.construct_image(Params, obj.SH);
        obj.FramesChanged = false; % reset
        obj.LastParams = Params;
    end

    function r = constructImages(obj, image_types)

        arguments
            obj
            image_types cell % list of chars image types
        end

        r = cell(1, numel(image_types));

        for i = 1:length(image_types)

            if ~isprop(obj.Output, image_types{i})
                error("%s isnt a known image type try any of [ %s ]", image_types{i}, sprintf("%s,", string(fields(obj.Output))));
            end

        end

        obj.Output.select(image_types{:});

        obj.Output.construct_image_from_FH(obj.LastParams, obj.FH);

        obj.Output.construct_image_from_SVD(obj.cov, obj.U, size(obj.H));

        obj.Output.construct_image_from_ShackHartmann(obj.moment_chunks_crop_array, obj.ShackHartmannMask);

        obj.Output.construct_image(obj.LastParams, obj.SH);

        for i = 1:length(image_types)

            if ~isprop(obj.Output, image_types{i})
                error("%s isnt a known image type try any of [ %s ]", image_types{i}, sprintf("%s,", string(fields(obj.Output))));
            end

            r{i} = mat2gray(obj.Output.(image_types{i}).image);
        end

    end

    function r = getImages(obj, image_types)

        arguments
            obj
            image_types cell % list of chars image types
        end

        r = cell(1, numel(image_types));

        for i = 1:length(image_types)

            if ~isprop(obj.Output, image_types{i})
                error("%s isnt a known image type try any of [ %s ]", image_types{i}, sprintf("%s,", string(fields(obj.Output))));
            end

            if isempty(obj.Output.(image_types{i}).image)

                if ~ismember(image_types{i}, {'buckets', 'SH'}) % these dont have explicit out images so it is normal for them not to output an image
                    fprintf("unfortunately %s wasnt outputed \n", image_types{i});
                end

                r{i} = [];
            else
                im = obj.Output.(image_types{i}).image;
                r{i} = mat2gray(im);
            end

        end

    end

    function showFirstFrame(obj)
        figure(1); imshow(rescale(obj.Frames(:, :, 1)));
    end

    function selfTesting(obj)
        obj.freeCache();
        obj.setFrames(rescale(rand(10, 20, 30, 'single')));

        obj.setInitParams();

        obj.Render(struct(), {"power_Doppler"});
        obj.Render(struct("spatial_transformation", "angular spectrum"), {"power_Doppler"});
        obj.Render(struct("time_transform", "PCA"), {"pure_PCA"});
        obj.Render(struct(), {"power_Doppler"});
        obj.Render(struct(), {"directional_Doppler"});
        obj.Render(struct("time_transform", "ICA"), {"directional_Doppler"});

    end

end

end
