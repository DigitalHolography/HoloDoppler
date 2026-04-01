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

        Params.spatialFilter = false;
        Params.spatialFilterRange = [0, 1];
        Params.spatialTransformation = "Fresnel";
        Params.spatialPropagation = 0.5;
        Params.PaddingNum = 0;

        Params.svd_filter = 1;
        Params.svdThreshold = false;
        Params.svd_mean = false;
        Params.svdStride = 1;
        Params.timeTransform = "FFT";
        Params.frequencyRange = [6, 10.5];
        Params.frequencyRangeInter = [7, 7];
        Params.indexRange = [3, 10];
        Params.frequencyRange_extra = -1;
        Params.bucketsRanges = [[4; 18.3], [6; 18.3]];
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

    function obj = Render(obj, Params, imageTypes, options)

        arguments
            obj
            Params struct % contains all the parameters required for the rendering
            imageTypes cell % list of chars containing the name of the outputs
            options.cache_intermediate_results logical = true
        end

        obj.Output.select(imageTypes{:});

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

        doFrames = ParamChanged.spatialFilter || ParamChanged.spatialFilterRange || obj.FramesChanged;
        [Nx, Ny, batchSize] = size(obj.Frames);

        if doFrames % change or if the frames changed

            if Params.spatialFilter

                if ParamChanged.spatialFilterRange || obj.FramesChanged || isempty(obj.SpatialFilterMask)
                    [NY, NX, ~] = size(obj.Frames);
                    obj.SpatialFilterMask = fftshift(diskMask(NY, NX, Params.spatialFilterRange(1), Params.spatialFilterRange(2)))';
                end

                obj.Frames = ifft2(fft2(obj.Frames) .* obj.SpatialFilterMask);
            end

        end

        % 2) Spatial transformation (from Frames to H)

        doFH = doFrames || ParamChanged.PaddingNum || ParamChanged.spatialTransformation || ParamChanged.spatialPropagation || ParamChanged.ShackHartmannCorrection || obj.FramesChanged || ~options.cache_intermediate_results;

        if doFH % change or if the frames changed

            switch Params.spatialTransformation
                case "angular spectrum"

                    [NY, NX, ~] = size(obj.Frames);

                    if Params.PaddingNum > 0
                        ND = Params.PaddingNum;
                    else
                        ND = max(NX, NY);
                    end

                    if ParamChanged.spatialPropagation || ParamChanged.PaddingNum || ParamChanged.spatialTransformation || isempty(obj.SpatialKernel)

                        if isempty(Params.ShackHartmannCorrection)
                            obj.SpatialKernel = propagation_kernelAngularSpectrum(ND, ND, Params.spatialPropagation, Params.lambda, Params.ppx, Params.ppy, 0);
                        else
                            obj.SpatialKernel = propagation_kernelAngularSpectrum(NX, NY, Params.spatialPropagation, Params.lambda, Params.ppx, Params.ppy, 0);
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

                    if Params.PaddingNum > 0
                        NY = Params.PaddingNum;
                        NX = Params.PaddingNum;
                    end

                    if ParamChanged.spatialPropagation || ParamChanged.PaddingNum || ParamChanged.spatialTransformation || isempty(obj.SpatialKernel)

                        [obj.SpatialKernel, obj.PhaseFactor] = propagation_kernelFresnel(NX, NY, Params.spatialPropagation, Params.lambda, Params.ppx, Params.ppy, 0);
                    end

                    if Params.PaddingNum > 0
                        obj.FH = single(pad3DToSquare(obj.Frames, Params.PaddingNum)) .* obj.SpatialKernel;
                    else
                        obj.FH = single(obj.Frames) .* obj.SpatialKernel;
                    end

                case "None"
                    obj.FH = [];

            end

            if ~isempty(Params.ShackHartmannCorrection)

                if ~Params.applyShackHartmannfromRef || isempty(obj.ShackHartmannMask) % in case we apply ShackHartmann from precalculated Mask

                    if doFH || ParamChanged.ShackHartmannCorrection || isempty(obj.ShackHartmannMask)
                        [obj.ShackHartmannMask, obj.moment_chunks_crop_array] = calculate_shackhartmannmask(obj.FH, Params.spatialTransformation, Params.spatialPropagation, Params.frequencyRange, Params.fs, Params.flatfield_gw, Params.ShackHartmannCorrection);
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

        doH = doFH || ParamChanged.svd_filter || ...
            (Params.svdThreshold == 0 && ParamChanged.frequencyRange) || ...
            ParamChanged.svdThreshold || obj.FramesChanged || ~options.cache_intermediate_results;

        if doH % change or if the frames changed

            switch Params.spatialTransformation
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
                [obj.H, obj.cov, obj.U] = svd_filter(obj.H, Params.svdThreshold, Params.frequencyRange(1), Params.fs, Params.svdStride, Params.svd_mean);

            end

        end

        if ~Params.svd_filter
            obj.cov = [];
            obj.U = [];
        end

        obj.Output.construct_image_from_SVD(Params, obj.cov, obj.U, size(obj.H));

        % 4) Short-time transformation

        doSH = doH || ParamChanged.timeTransform || obj.FramesChanged || ParamChanged.flip_y || ParamChanged.flip_x || ~options.cache_intermediate_results;

        if doSH

            switch Params.timeTransform
                case 'PCA'
                    obj.SH = short_time_PCA(obj.H);
                case 'ICA'
                    obj.SH = short_time_ICA(obj.H);
                case 'FFT'
                    obj.SH = fft(obj.H, [], 3) ./ sqrt(batchSize);
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

    function r = constructImages(obj, imageTypes)

        arguments
            obj
            imageTypes cell % list of chars image types
        end

        r = cell(1, numel(imageTypes));

        for i = 1:length(imageTypes)

            if ~isprop(obj.Output, imageTypes{i})
                error("%s isnt a known image type try any of [ %s ]", imageTypes{i}, sprintf("%s,", string(fields(obj.Output))));
            end

        end

        obj.Output.select(imageTypes{:});

        obj.Output.construct_image_from_FH(obj.LastParams, obj.FH);

        obj.Output.construct_image_from_SVD(obj.LastParams, obj.cov, obj.U, size(obj.H));

        obj.Output.construct_image_from_ShackHartmann(obj.LastParams, obj.moment_chunks_crop_array, obj.ShackHartmannMask);

        obj.Output.construct_image(obj.LastParams, obj.SH);

        for i = 1:length(imageTypes)

            if ~isprop(obj.Output, imageTypes{i})
                error("%s isnt a known image type try any of [ %s ]", imageTypes{i}, sprintf("%s,", string(fields(obj.Output))));
            end

            r{i} = mat2gray(obj.Output.(imageTypes{i}).image);
        end

    end

    function r = getImages(obj, imageTypes)

        arguments
            obj
            imageTypes cell % list of chars image types
        end

        r = cell(1, numel(imageTypes));

        for i = 1:length(imageTypes)

            if ~isprop(obj.Output, imageTypes{i})
                error("%s isnt a known image type try any of [ %s ]", imageTypes{i}, sprintf("%s,", string(fields(obj.Output))));
            end

            if isempty(obj.Output.(imageTypes{i}).image)

                if ~ismember(imageTypes{i}, {'buckets', 'SH'}) % these dont have explicit out images so it is normal for them not to output an image
                    fprintf("unfortunately %s wasnt outputed \n", imageTypes{i});
                end

                r{i} = [];
            else
                im = obj.Output.(imageTypes{i}).image;
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
        obj.Render(struct("spatialTransformation", "angular spectrum"), {"power_Doppler"});
        obj.Render(struct("timeTransform", "PCA"));
        obj.Render(struct(), {"power_Doppler"});
        obj.Render(struct(), {"directional_Doppler"});
        %montage(obj.constructImages({'directional_Doppler'}));
        obj.Render(struct("timeTransform", "ICA"), {"directional_Doppler"});

    end

end

end
