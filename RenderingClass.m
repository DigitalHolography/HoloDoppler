classdef RenderingClass < handle
% Holographic renderer.
%
%   r = RenderingClass() creates an instance of the RenderingClass.
%   r = RenderingClass('precomputeSpatialKernel', kernel)

properties
    Lastparams struct
    Frames single
    FramesChanged logical = false

    SpatialFilterMask logical
    SpatialKernel single % may be gpuArray
    PhaseFactor single
    FH single
    H single
    H_raw single
    SH single
    cov single
    U single

    Output ImageTypeList
end

% -----------------------------------------------------------------------
%  Public interface
% -----------------------------------------------------------------------
methods

    function obj = RenderingClass(options)

        arguments
            options.precomputeSpatialKernel = []
        end

        obj.Output = ImageTypeList();
        obj.setInitparams();

        if ~isempty(options.precomputeSpatialKernel)
            obj.SpatialKernel = single(options.precomputeSpatialKernel); % keep whatever type
        end

    end

    function setInitparams(obj)
        obj.Lastparams = HDParamSchema.getDefaults();
    end

    function setFrames(obj, frames)
        obj.Frames = single(frames);
        obj.FramesChanged = true;
    end

    function Render(obj, params, imageTypes, options)

        arguments
            obj
            params struct
            imageTypes cell = {}
            options.cache_intermediate_results logical = true
        end

        obj.Output.select(imageTypes{:});
        [params, changed] = obj.mergeAndDiff(params);
        [Nx, Ny, batchSize] = size(obj.Frames);

        % Spatial filter
        obj.applySpatialFilter(params, changed, Nx, Ny);

        % Spatial propagation
        doFH = obj.FramesChanged || ...
            changed.PaddingNum || ...
            changed.spatialTransform || ...
            changed.spatialPropagation || ...
            ~options.cache_intermediate_results;
        obj.applySpatialTransform(params, changed, doFH, Nx, Ny);
        obj.Output.construct_image_from_FH(params, obj.FH);

        if ~options.cache_intermediate_results
            obj.FH = [];
        end

        % SVD filter
        doSVD = doFH || ...
            changed.svd_filter || ...
            changed.svdThreshold || ...
            changed.svdStride || ...
            ~options.cache_intermediate_results;
        obj.applySvdFilter(params, doSVD);
        obj.Output.construct_image_from_SVD(params, obj.cov, obj.U, size(obj.H));

        % Time transform
        doSH = doSVD || ...
            changed.timeTransform || ...
            changed.flip_y || ...
            changed.flip_x || ...
            ~options.cache_intermediate_results;
        obj.applyTimeTransform(params, doSH, batchSize);

        if ~options.cache_intermediate_results
            obj.H = [];
        end

        if doSH
            obj.orientOutput(params);
        end

        obj.Output.construct_image(params, obj.SH);

        obj.FramesChanged = false;
        obj.Lastparams = params;
    end

    function r = getImages(obj, imageTypes)
        % Return normalised images for requested types without recomputing.
        obj.validateImageTypes(imageTypes);
        r = obj.collectImages(imageTypes);
    end

end % public methods

methods (Access = private)

    function [params, changed] = mergeAndDiff(obj, params)
        % Detect changed fields and fill missing ones from Lastparams.
        fields = fieldnames(obj.Lastparams);

        for i = 1:numel(fields)
            f = fields{i};

            if isfield(params, f)
                changed.(f) = ~isequal(params.(f), obj.Lastparams.(f));
            else
                changed.(f) = false;
                params.(f) = obj.Lastparams.(f);
            end

        end

        % Handle fields present in params but not in Lastparams.
        newFields = setdiff(fieldnames(params), fields);

        for i = 1:numel(newFields)
            changed.(newFields{i}) = true;
        end

    end

    function applySpatialFilter(obj, params, changed, Nx, Ny)
        filterparamsChanged = changed.spatialFilter || ...
            changed.spatialFilterRange1 || ...
            changed.spatialFilterRange2;

        if ~(filterparamsChanged || obj.FramesChanged) || ~params.spatialFilter
            return
        end

        if filterparamsChanged || obj.FramesChanged || isempty(obj.SpatialFilterMask)
            obj.SpatialFilterMask = fftshift( ...
                diskMask(Nx, Ny, params.spatialFilterRange1, params.spatialFilterRange2))';
        end

        obj.Frames = ifft2(fft2(obj.Frames) .* obj.SpatialFilterMask);
    end

    function applySpatialTransform(obj, params, changed, doFH, Nx, Ny)
        if ~doFH, return; end

        kernelChanged = ...
            changed.spatialPropagation || ...
            changed.PaddingNum || ...
            changed.spatialTransform;

        switch params.spatialTransform
            case "angular spectrum"
                ND = max([params.PaddingNum, Nx, Ny]);

                if kernelChanged || isempty(obj.SpatialKernel)
                    obj.SpatialKernel = propagation_kernelAngularSpectrum( ...
                        ND, ND, params.spatialPropagation, ...
                        params.lambda, params.ppx, params.ppy, 0);
                end

                hologram_fft = fft2(single(pad3DToSquare(obj.Frames, ND)));
                propagated_fft = hologram_fft .* fftshift(obj.SpatialKernel);
                reconstructed_field = ifft2(propagated_fft) .* sqrt(Nx * Ny);

            case "Fresnel"
                NxP = max(params.PaddingNum, Nx);
                NyP = max(params.PaddingNum, Ny);

                if kernelChanged || isempty(obj.SpatialKernel)
                    [obj.SpatialKernel, obj.PhaseFactor] = propagation_kernelFresnel( ...
                        NyP, NxP, params.spatialPropagation, ...
                        params.lambda, params.ppx, params.ppy, 0);
                end

                if params.PaddingNum > 0
                    padded = single(pad3DToSquare(obj.Frames, params.PaddingNum));
                else
                    padded = single(obj.Frames);
                end

                propagated_fft = padded .* obj.SpatialKernel;
                reconstructed_field = fftshift(fftshift(fft2(propagated_fft), 1), 2) ./ sqrt(NxP * NyP);

            case "None"
                propagated_fft = [];
                reconstructed_field = single(obj.Frames);

            case "twin image removal"
                propagated_fft = [];
                reconstructed_field = twin_image_removal_(single(obj.Frames), [], changed, params);

            otherwise
                error("RenderingClass: unknown spatialTransform '%s'", ...
                    params.spatialTransform);

        end

        obj.FH = propagated_fft;
        obj.H_raw = reconstructed_field;
        obj.H = reconstructed_field;

    end

    function applySvdFilter(obj, params, doSVD)

        fprintf('applySvdFilter: doSVD=%d, svd_filter=%d\n', doSVD, params.svd_filter);
        fprintf('Threshold=%d, f1=%d fs=%s\n', params.svdThreshold, params.frequencyRange1, params.fs);

        if ~doSVD, return, end

        if params.svd_filter
            [obj.H, obj.cov, obj.U] = svd_filter( ...
                obj.H_raw, params.svdThreshold, ...
                params.frequencyRange1, ...
                params.fs, ...
                params.svdStride);
        else
            obj.cov = [];
            obj.U = [];
        end

    end

    function applyTimeTransform(obj, params, doSH, batchSize)
        if ~doSH, return, end

        [a, b, ~] = size(obj.H);

        switch params.timeTransform
            case 'PCA'
                obj.SH = short_time_PCA(obj.H);
            case 'ICA'
                obj.SH = short_time_ICA(obj.H);
            case 'FFT'
                obj.SH = fft(obj.H, [], 3) ./ sqrt(batchSize);
            case 'Wavelet_Morlet'
                obj.SH = morlet1D_transform_3rdDim(obj.H, [], 3);
            case 'autocorrelation'
                tmp = reshape(obj.H, a * b, []);
                out = arrayfun(@(k) xcorr(tmp(k, :), 'normalized'), ...
                    1:a * b, 'UniformOutput', false);
                obj.SH = permute(reshape(cell2mat(out), [], a, b), [2 3 1]);
            case 'intercorrelation'
                obj.SH = intercorrel(obj.H, 3);
            case 'phase difference'
                obj.SH = angle(obj.H);
            case 'None'
                obj.SH = obj.H;
            otherwise
                error("RenderingClass: unknown timeTransform '%s'", params.timeTransform);
        end

    end

    function orientOutput(obj, params)
        % Lens transpose: x ↔ −y
        obj.SH = flip(permute(obj.SH, [2 1 3]), 2);

        if params.flip_y
            obj.SH = flip(obj.SH, 1);
        end

        if params.flip_x
            obj.SH = flip(obj.SH, 2);
        end

    end

    function validateImageTypes(obj, imageTypes)

        for i = 1:numel(imageTypes)

            if ~isprop(obj.Output, imageTypes{i})
                known = sprintf('%s, ', string(fieldnames(obj.Output)));
                error("'%s' is not a known image type. Available: [%s]", ...
                    imageTypes{i}, known);
            end

        end

    end

    function r = collectImages(obj, imageTypes)
        silent = {'buckets', 'full_buckets', 'SH', 'SH_avg'}; % types without a rasterised image
        r = cell(1, numel(imageTypes));

        for i = 1:numel(imageTypes)
            im = obj.Output.(imageTypes{i}).image;

            if isempty(im)

                if ~ismember(imageTypes{i}, silent)
                    fprintf("Warning: '%s' produced no image.\n", imageTypes{i});
                end

                r{i} = [];
            else
                r{i} = mat2gray(im);
            end

        end

    end

end % private methods

end % classdef
