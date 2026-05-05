classdef RenderingClass < handle
% Holographic renderer.
%
%   r = RenderingClass() creates an instance of the RenderingClass.
%   r = RenderingClass('precomputeSpatialKernel', kernel)

properties
    LastParams struct
    Frames single
    FramesChanged logical = false

    SpatialFilterMask logical
    SpatialKernel single % may be gpuArray
    PhaseFactor single
    FH single
    H single
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
        obj.setInitParams();

        if ~isempty(options.precomputeSpatialKernel)
            obj.SpatialKernel = single(options.precomputeSpatialKernel); % keep whatever type
        end

    end

    function setInitParams(obj)
        obj.LastParams = HDParamSchema.getDefaults();
    end

    function setFrames(obj, frames)
        obj.Frames = single(frames);
        obj.FramesChanged = true;
    end

    function Render(obj, Params, imageTypes, options)

        arguments
            obj
            Params struct
            imageTypes cell = {}
            options.cache_intermediate_results logical = true
        end

        obj.Output.select(imageTypes{:});
        [Params, changed] = obj.mergeAndDiff(Params);
        [Nx, Ny, batchSize] = size(obj.Frames);

        % Spatial filter
        obj.applySpatialFilter(Params, changed, Nx, Ny);

        % Spatial propagation
        doFH = obj.FramesChanged || changed.PaddingNum || ...
            changed.spatialTransform || changed.spatialPropagation || ...
            ~options.cache_intermediate_results;
        obj.applySpatialTransform(Params, changed, doFH, Nx, Ny);
        obj.Output.construct_image_from_FH(Params, obj.FH);

        if ~options.cache_intermediate_results
            obj.FH = [];
        end

        % SVD filter
        doSVD = doFH || changed.svd_filter || changed.svdThreshold || ...
            changed.spatialPropagation || changed.frequencyRange1 || changed.frequencyRange2 || ...
            ~options.cache_intermediate_results;
        obj.applySvdFilter(Params, doSVD);
        obj.Output.construct_image_from_SVD(Params, obj.cov, obj.U, size(obj.H));

        % Time transform
        doSH = doSVD || changed.timeTransform || changed.flip_y || changed.flip_x || ...
            ~options.cache_intermediate_results;
        obj.applyTimeTransform(Params, doSH, batchSize);

        if ~options.cache_intermediate_results
            obj.H = [];
        end

        if doSH
            obj.orientOutput(Params);
        end

        obj.Output.construct_image(Params, obj.SH);

        obj.FramesChanged = false;
        obj.LastParams = Params;
    end

    function r = getImages(obj, imageTypes)
        % Return normalised images for requested types without recomputing.
        obj.validateImageTypes(imageTypes);
        r = obj.collectImages(imageTypes);
    end

end % public methods

methods (Access = private)

    function [Params, changed] = mergeAndDiff(obj, Params)
        % Detect changed fields and fill missing ones from LastParams.
        fields = fieldnames(obj.LastParams);

        for i = 1:numel(fields)
            f = fields{i};

            if isfield(Params, f)
                changed.(f) = ~isequal(Params.(f), obj.LastParams.(f));
            else
                changed.(f) = false;
                Params.(f) = obj.LastParams.(f);
            end

        end

        % Handle fields present in Params but not in LastParams.
        newFields = setdiff(fieldnames(Params), fields);

        for i = 1:numel(newFields)
            changed.(newFields{i}) = true;
        end

    end

    function applySpatialFilter(obj, Params, changed, Nx, Ny)
        filterParamsChanged = changed.spatialFilter || ...
            changed.spatialFilterRange1 || ...
            changed.spatialFilterRange2;

        if ~(filterParamsChanged || obj.FramesChanged) || ~Params.spatialFilter
            return
        end

        if filterParamsChanged || obj.FramesChanged || isempty(obj.SpatialFilterMask)
            obj.SpatialFilterMask = fftshift( ...
                diskMask(Nx, Ny, Params.spatialFilterRange1, Params.spatialFilterRange2))';
        end

        obj.Frames = ifft2(fft2(obj.Frames) .* obj.SpatialFilterMask);
    end

    function applySpatialTransform(obj, Params, changed, doFH, Nx, Ny)
        if ~doFH, return; end
        kernelChanged = changed.spatialPropagation || changed.PaddingNum || changed.spatialTransform;

        switch Params.spatialTransform
            case "angular spectrum"
                ND = max([Params.PaddingNum, Nx, Ny]);

                if kernelChanged || isempty(obj.SpatialKernel)
                    obj.SpatialKernel = propagation_kernelAngularSpectrum( ...
                        ND, ND, Params.spatialPropagation, ...
                        Params.lambda, Params.ppx, Params.ppy, 0);
                end

                obj.FH = fft2(single(pad3DToSquare(obj.Frames, ND)));
                obj.FH = obj.FH .* fftshift(obj.SpatialKernel);
                obj.H = ifft2(obj.FH) .* sqrt(Nx * Ny);

            case "Fresnel"
                NxP = max(Params.PaddingNum, Nx);
                NyP = max(Params.PaddingNum, Ny);

                if kernelChanged || isempty(obj.SpatialKernel)
                    [obj.SpatialKernel, obj.PhaseFactor] = propagation_kernelFresnel( ...
                        NyP, NxP, Params.spatialPropagation, ...
                        Params.lambda, Params.ppx, Params.ppy, 0);
                end

                if Params.PaddingNum > 0
                    padded = single(pad3DToSquare(obj.Frames, Params.PaddingNum));
                else
                    padded = single(obj.Frames);
                end

                obj.FH = padded .* obj.SpatialKernel;
                obj.H = fftshift(fftshift(fft2(obj.FH), 1), 2) ./ sqrt(NxP * NyP);

            case "None"
                obj.FH = []; obj.H = single(obj.Frames);

            case "twin image removal"
                obj.FH = [];
                obj.H = twin_image_removal_(single(obj.Frames), [], changed, Params);

            otherwise
                error("RenderingClass: unknown spatialTransform '%s'", ...
                    Params.spatialTransform);
        end

    end

    function applySvdFilter(obj, Params, doSVD)
        if ~doSVD, return, end

        if Params.svd_filter
            [obj.H, obj.cov, obj.U] = svd_filter( ...
                obj.H, Params.svdThreshold, Params.frequencyRange1, ...
                Params.fs, Params.svdStride);
        else
            obj.cov = [];
            obj.U = [];
        end

    end

    function applyTimeTransform(obj, Params, doSH, batchSize)
        if ~doSH, return, end

        [a, b, ~] = size(obj.H);

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
                error("RenderingClass: unknown timeTransform '%s'", Params.timeTransform);
        end

    end

    function orientOutput(obj, Params)
        % Lens transpose: x ↔ −y
        obj.SH = flip(permute(obj.SH, [2 1 3]), 2);

        if Params.flip_y
            obj.SH = flip(obj.SH, 1);
        end

        if Params.flip_x
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
