classdef RenderingClass < handle
% Holographic renderer.
%
%   r = RenderingClass() creates an instance.
%   r = RenderingClass('precomputeSpatialKernel', kernel)

properties
    LastParams struct % last rendering parameters (validated)
    Frames single
    FramesChanged logical = false

    SpatialFilterMask logical
    SpatialKernel single % may be gpuArray
    PhaseFactor single
    FH single
    H single
    H_raw single % raw complex field (only if SVD needed)
    SH single
    cov single
    U single

    Output ImageTypeList
end

properties (Access = private)
    % Last optical parameters used to compute SpatialKernel
    lastLambda single = []
    lastPpx single = []
    lastPpy single = []
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
            obj.SpatialKernel = single(options.precomputeSpatialKernel);
        end

    end

    function setInitParams(obj)
        obj.LastParams = HDParamSchema.getDefaults();
    end

    function setFrames(obj, frames)
        obj.Frames = single(frames);
        obj.FramesChanged = true;
    end

    function Render(obj, p, imageTypes, options)

        arguments
            obj
            p struct
            imageTypes cell = {}
            options.cache_intermediate_results logical = true
        end

        obj.Output.select(imageTypes{:});
        [p, changed] = obj.mergeAndDiff(p);
        [Nx, Ny, batchSize] = size(obj.Frames);

        % Spatial filter
        obj.applySpatialFilter(p, changed, Nx, Ny);

        % Spatial propagation
        doFH = obj.FramesChanged || ...
            changed.PaddingNum || ...
            changed.spatialTransform || ...
            changed.spatialPropagation || ...
            ~options.cache_intermediate_results;
        obj.applySpatialTransform(p, changed, doFH, Nx, Ny);
        obj.Output.construct_image_from_FH(p, obj.FH);

        if ~options.cache_intermediate_results
            obj.FH = [];
        end

        % SVD filter
        doSVD = doFH || ...
            changed.svd_filter || ...
            changed.svdThreshold || ...
            changed.svdStride || ...
            changed.frequencyRange1 || ... % restored from original
            changed.frequencyRange2 || ...
            changed.spatialPropagation || ...
            ~options.cache_intermediate_results;
        obj.applySvdFilter(p, doSVD);
        obj.Output.construct_image_from_SVD(p, obj.cov, obj.U, size(obj.H));

        % Time transform
        doSH = doSVD || ...
            changed.timeTransform || ...
            changed.flip_y || ...
            changed.flip_x || ...
            ~options.cache_intermediate_results;
        obj.applyTimeTransform(p, doSH, batchSize);

        if ~options.cache_intermediate_results
            obj.H = [];
            obj.H_raw = []; % also clear raw field if not needed
        end

        if doSH
            obj.orientOutput(p);
        end

        obj.Output.construct_image(p, obj.SH);

        obj.FramesChanged = false;
        obj.LastParams = p;
    end

    function r = getImages(obj, imageTypes)
        % Return normalised images for requested types without recomputing.
        obj.validateImageTypes(imageTypes);
        r = obj.collectImages(imageTypes);
    end

end % public methods

methods (Access = private)

    function [p, changed] = mergeAndDiff(obj, p)
        % Detect changed fields and fill missing ones from LastParams.
        fields = fieldnames(obj.LastParams);

        for i = 1:numel(fields)
            f = fields{i};

            if isfield(p, f)
                changed.(f) = ~isequal(p.(f), obj.LastParams.(f));
            else
                changed.(f) = false;
                p.(f) = obj.LastParams.(f);
            end

        end

        newFields = setdiff(fieldnames(p), fields);

        for i = 1:numel(newFields)
            changed.(newFields{i}) = true;
        end

    end

    function applySpatialFilter(obj, p, changed, Nx, Ny)
        filterParamsChanged = changed.spatialFilter || ...
            changed.spatialFilterRange1 || ...
            changed.spatialFilterRange2;

        if ~(filterParamsChanged || obj.FramesChanged) || ~p.spatialFilter
            return
        end

        if filterParamsChanged || obj.FramesChanged || isempty(obj.SpatialFilterMask)
            obj.SpatialFilterMask = fftshift( ...
                diskMask(Nx, Ny, p.spatialFilterRange1, p.spatialFilterRange2))';
        end

        obj.Frames = ifft2(fft2(obj.Frames) .* obj.SpatialFilterMask);
    end

    function applySpatialTransform(obj, p, changed, doFH, Nx, Ny)

        if ~doFH
            return
        end

        kernelChanged = changed.spatialPropagation || ...
            changed.PaddingNum || ...
            changed.spatialTransform;

        % Also recompute kernel if optical parameters have changed
        opticalChanged = ~isequal(p.lambda, obj.lastLambda) || ...
            ~isequal(p.ppx, obj.lastPpx) || ...
            ~isequal(p.ppy, obj.lastPpy);

        if kernelChanged || opticalChanged || isempty(obj.SpatialKernel)

            switch p.spatialTransform
                case "angular spectrum"
                    ND = max([p.PaddingNum, Nx, Ny]);
                    obj.SpatialKernel = propagation_kernelAngularSpectrum( ...
                        ND, ND, p.spatialPropagation, ...
                        p.lambda, p.ppx, p.ppy, 0);
                case "Fresnel"
                    NxP = max(p.PaddingNum, Nx);
                    NyP = max(p.PaddingNum, Ny);
                    [obj.SpatialKernel, obj.PhaseFactor] = propagation_kernelFresnel( ...
                        NyP, NxP, p.spatialPropagation, ...
                        p.lambda, p.ppx, p.ppy, 0);
                otherwise
                    % No kernel needed for other transforms
            end

            % Store last optical parameters
            obj.lastLambda = p.lambda;
            obj.lastPpx = p.ppx;
            obj.lastPpy = p.ppy;
        end

        switch p.spatialTransform
            case "angular spectrum"
                ND = max([p.PaddingNum, Nx, Ny]);
                hologram_fft = fft2(single(pad3DToSquare(obj.Frames, ND)));
                propagated_fft = hologram_fft .* fftshift(obj.SpatialKernel);
                reconstructed_field = ifft2(propagated_fft) .* sqrt(Nx * Ny);
                obj.FH = propagated_fft;
                obj.H = reconstructed_field;

                if p.svd_filter
                    obj.H_raw = reconstructed_field; % store only if needed
                else
                    obj.H_raw = [];
                end

            case "Fresnel"
                NxP = max(p.PaddingNum, Nx);
                NyP = max(p.PaddingNum, Ny);

                if p.PaddingNum > 0
                    padded = single(pad3DToSquare(obj.Frames, p.PaddingNum));
                else
                    padded = single(obj.Frames);
                end

                propagated_fft = padded .* obj.SpatialKernel;
                reconstructed_field = fftshift(fftshift(fft2(propagated_fft), 1), 2) ./ sqrt(NxP * NyP);
                obj.FH = propagated_fft;
                obj.H = reconstructed_field;

                if p.svd_filter
                    obj.H_raw = reconstructed_field;
                else
                    obj.H_raw = [];
                end

            case "None"
                obj.FH = [];
                obj.H = single(obj.Frames);
                obj.H_raw = []; % no SVD possible

            case "twin image removal"
                obj.FH = [];
                reconstructed_field = twin_image_removal_(single(obj.Frames), [], changed, p);
                obj.H = reconstructed_field;

                if p.svd_filter
                    obj.H_raw = reconstructed_field;
                else
                    obj.H_raw = [];
                end

            otherwise
                error("RenderingClass: unknown spatialTransform '%s'", ...
                    p.spatialTransform);
        end

    end

    function applySvdFilter(obj, p, doSVD)

        if ~doSVD
            return
        end

        if p.svd_filter

            if isempty(obj.H_raw)
                % Should not happen if svd_filter is true and we stored it
                warning('RenderingClass:noRawField', ...
                'H_raw is empty but svd_filter is true – using H instead.');
                src = obj.H;
            else
                src = obj.H_raw;
            end

            [obj.H, obj.cov, obj.U] = svd_filter( ...
                src, p.svdThreshold, ...
                p.frequencyRange1, ...
                p.fs, ...
                p.svdStride);
        else
            obj.cov = [];
            obj.U = [];
        end

    end

    function applyTimeTransform(obj, p, doSH, batchSize)

        if ~doSH
            return
        end

        [a, b, ~] = size(obj.H);

        switch p.timeTransform
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
                error("RenderingClass: unknown timeTransform '%s'", p.timeTransform);
        end

    end

    function orientOutput(obj, p)
        % Lens transpose: x ↔ −y
        obj.SH = flip(permute(obj.SH, [2 1 3]), 2);

        if p.flip_y
            obj.SH = flip(obj.SH, 1);
        end

        if p.flip_x
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
        silent = {'buckets', 'full_buckets', 'SH', 'SH_avg'};
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
