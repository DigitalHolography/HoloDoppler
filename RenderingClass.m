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
        Params.Padding_num = 0;

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
            options.cache_intermediate_results logical = true
        end

        obj.Output.select(image_types{:});

        % Calculate the parameters difference to prevent recalculations
        fields = fieldnames(Params);

        for i = 1:numel(fields)

            if isfield(obj.LastParams, fields{i})
                ParamChanged.(fields{i}) = ~isequal(Params.(fields{i}), obj.LastParams.(fields{i}));
                % if the parameter was different
                % there is need to recalculate
            else
                ParamChanged.(fields{i}) = true; % need to recalculate
            end

        end

        %Fill with the last output params if none given
        fields = fieldnames(obj.LastParams);

        for i = 1:numel(fields)

            if ~isfield(Params, fields{i})
                ParamChanged.(fields{i}) = false; % by default user should not need to calculate
                Params.(fields{i}) = obj.LastParams.(fields{i});
            end

        end

        % 1) Apply corrections to interferograms

        doFrames = ParamChanged.spatial_filter || ParamChanged.hilbert_filter || ParamChanged.spatial_filter_range || obj.FramesChanged;
        [Nx, Ny, batch_size] = size(obj.Frames);

        if doFrames % change or if the frames changed

            if Params.hilbert_filter
                tmp = obj.Frames;
                [width, height, batch_size] = size(tmp);
                tmp = reshape(tmp, width * height, batch_size);
                tmp = hilbert(tmp);
                obj.Frames = reshape(tmp, width, height, batch_size);
                clear tmp;
            end

        end

        obj.Output.construct_image_from_Frames(Params, obj.Frames);

        if doFrames % change or if the frames changed

            if Params.spatial_filter

                if ParamChanged.spatial_filter_range || obj.FramesChanged || isempty(obj.SpatialFilterMask)
                    [NY, NX, ~] = size(obj.Frames);
                    obj.SpatialFilterMask = fftshift(diskMask(NY, NX, Params.spatial_filter_range(1), Params.spatial_filter_range(2)))';
                end

                obj.Frames = ifft2(fft2(obj.Frames) .* obj.SpatialFilterMask);
            end

        end

        % 2) Spatial transformation (from Frames to H)

        doFH = doFrames || ParamChanged.Padding_num || ParamChanged.spatial_transformation || ParamChanged.spatial_propagation || ParamChanged.ShackHartmannCorrection || obj.FramesChanged || ~options.cache_intermediate_results;

        if doFH % change or if the frames changed

            switch Params.spatial_transformation
                case "angular spectrum"

                    [NY, NX, ~] = size(obj.Frames);

                    if Params.Padding_num > 0
                        ND = Params.Padding_num;
                    else
                        ND = max(NX, NY);
                    end

                    if ParamChanged.spatial_propagation || ParamChanged.Padding_num || ParamChanged.spatial_transformation || isempty(obj.SpatialKernel)

                        if isempty(Params.ShackHartmannCorrection)
                            obj.SpatialKernel = propagation_kernelAngularSpectrum(ND, ND, Params.spatial_propagation, Params.lambda, Params.ppx, Params.ppy, 0);
                        else
                            obj.SpatialKernel = propagation_kernelAngularSpectrum(NX, NY, Params.spatial_propagation, Params.lambda, Params.ppx, Params.ppy, 0);
                        end

                    end

                    if isempty(Params.ShackHartmannCorrection)
                        obj.FH = fft2(single(pad3DToSquare(obj.Frames, ND))); % zero pading in a square of max(Nx NY) size
                    else
                        obj.FH = fft2(single(obj.Frames));
                    end

                    obj.FH = obj.FH .* fftshift(obj.SpatialKernel);
                case "Fresnel"

                    [NY, NX, ~] = size(obj.Frames);

                    if Params.Padding_num > 0
                        NY = Params.Padding_num;
                        NX = Params.Padding_num;
                    end

                    if ParamChanged.spatial_propagation || ParamChanged.Padding_num || ParamChanged.spatial_transformation || isempty(obj.SpatialKernel)

                        [obj.SpatialKernel, obj.PhaseFactor] = propagation_kernelFresnel(NX, NY, Params.spatial_propagation, Params.lambda, Params.ppx, Params.ppy, 0);
                    end

                    if Params.Padding_num > 0
                        obj.FH = single(pad3DToSquare(obj.Frames, Params.Padding_num)) .* obj.SpatialKernel;
                    else
                        obj.FH = single(obj.Frames) .* obj.SpatialKernel;
                    end

                case "None"
                    obj.FH = [];

            end

            if ~isempty(Params.ShackHartmannCorrection)

                if ~Params.applyshackhartmannfromref || isempty(obj.ShackHartmannMask) % in case we apply ShackHartmann from precalculated Mask

                    if doFH || ParamChanged.ShackHartmannCorrection || isempty(obj.ShackHartmannMask)
                        [obj.ShackHartmannMask, obj.moment_chunks_crop_array] = calculate_shackhartmannmask(obj.FH, Params.spatial_transformation, Params.spatial_propagation, Params.time_range, Params.fs, Params.flatfield_gw, Params.ShackHartmannCorrection);
                    end

                end

                if ~isempty(obj.ShackHartmannMask)
                    obj.FH = obj.FH .* obj.ShackHartmannMask;
                end

            else
                obj.ShackHartmannMask = [];
            end

        end

        obj.Output.construct_image_from_ShackHartmann(Params, obj.moment_chunks_crop_array, obj.ShackHartmannMask);

        doH = doFH || ParamChanged.svd_filter || (Params.svdx_filter && (ParamChanged.svdx_threshold || ParamChanged.svdx_Nsub)) || (Params.svdx_t_filter && (ParamChanged.svdx_t_threshold || ParamChanged.svdx_t_Nsub)) || ParamChanged.svdx_filter || ParamChanged.svdx_t_filter || (Params.svd_threshold == 0 && ParamChanged.time_range) || ParamChanged.svd_threshold || obj.FramesChanged || ~options.cache_intermediate_results;

        if doH % change or if the frames changed

            switch Params.spatial_transformation
                case "angular spectrum"
                    obj.H = ifft2(obj.FH) .* sqrt(Nx * Ny);
                case "Fresnel"
                    obj.H = fftshift(fftshift(fft2(obj.FH), 1), 2) ./ sqrt(Nx * Ny); %.*obj.PhaseFactor;
                case "twin image removal"
                    obj.H = twin_image_removal_(single(obj.Frames), [], ParamChanged, Params);
                case "None"
                    obj.H = single(obj.Frames);
            end

        end

        % obj.H = abs(obj.H); % nothing is in the phase so doing this is ok
        obj.Output.construct_image_from_FH(obj.LastParams, obj.FH);

        if ~options.cache_intermediate_results
            obj.FH = [];
        end

        % 3) H fluctuation batch filtering

        if doH

            if Params.svd_filter
                [obj.H, obj.cov, obj.U] = svd_filter(obj.H, Params.svd_threshold, Params.time_range(1), Params.fs, Params.svd_stride, Params.svd_mean);

            end

        end

        if ~Params.svd_filter
            obj.cov = [];
            obj.U = [];
        end

        obj.Output.construct_image_from_SVD(Params, obj.cov, obj.U, size(obj.H));

        if doH

            if Params.svdx_filter
                obj.H = svd_x_filter(obj.H, Params.svdx_threshold, Params.time_range(1), Params.fs, floor(max(size(obj.H, 1), size(obj.H, 2)) / Params.svdx_Nsub)); % forced
            end

        end

        if doH

            if Params.svdx_t_filter
                obj.H = svd_x_t_filter(obj.H, Params.svdx_t_threshold, Params.time_range(1), Params.fs, floor(max(size(obj.H, 1), size(obj.H, 2)) / Params.svdx_t_Nsub));
            end

        end

        % 4) Short-time transformation

        doSH = doH || ParamChanged.time_transform || obj.FramesChanged || ParamChanged.flip_y || ParamChanged.flip_x || ~options.cache_intermediate_results;

        if doSH

            switch Params.time_transform
                case 'PCA'
                    obj.SH = short_time_PCA(obj.H);
                case 'ICA'
                    obj.SH = short_time_ICA(obj.H);
                case 'FFT'
                    obj.SH = fft(obj.H, [], 3) ./ sqrt(batch_size);
                case 'Wavelet_Morlet'
                    obj.SH = morlet1D_transform_3rdDim(obj.H, [], 3);
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

        if ~options.cache_intermediate_results
            obj.H = [];
        end

        if doSH

            obj.SH = flip(permute(obj.SH, [2 1 3]), 2); % x<->-y transpose due to the lens imaging

            if Params.flip_y
                obj.SH = flip(obj.SH, 1);
            end

            if Params.flip_x
                obj.SH = flip(obj.SH, 2);
            end

        end

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

        obj.Output.construct_image_from_SVD(obj.LastParams, obj.cov, obj.U, size(obj.H));

        obj.Output.construct_image_from_ShackHartmann(obj.LastParams, obj.moment_chunks_crop_array, obj.ShackHartmannMask);

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
        %montage(obj.constructImages({'directional_Doppler'}));
        obj.Render(struct("time_transform", "ICA"), {"directional_Doppler"});

    end

end

end
