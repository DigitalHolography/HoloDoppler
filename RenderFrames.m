function obj = RenderFrames(obj, Params, changedParams, image_types, options)
% RenderFrames - Renders the frames stored in the object according to the given parameters
%
% Inputs:
%   obj: the RenderingClass object
%   Params: struct with rendering parameters
%   image_types: cell array of strings specifying which image types to render
%   options: struct with rendering options
%
% Outputs:
%   obj: updated object with rendered images

arguments
    obj
    Params struct % contains all the parameters required for the rendering
    changedParams struct % contains flags indicating which parameters have changed
    image_types cell % list of chars containing the name of the outputs
    options.cache_intermediate_results logical = true
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
svd_filter = Params.svd_filter;
svdx_filter = Params.svdx_filter;
svdx_t_filter = Params.svdx_t_filter;
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

framesChanged = obj.FramesChanged;
newFilter = changedParams.spatial_filter ...
    || changedParams.hilbert_filter ...
    || changedParams.spatial_filter_range;

doFrames = newFilter || framesChanged;

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
                || framesChanged ...
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
    (svdx_filter && newSVDxParams) ...
    || (svdx_t_filter && newSVDxParams) ...
    || changedParams.svdx_filter ...
    || changedParams.svdx_t_filter;

doH = doFH ...
    || SVDParamsChanged ...
    || SVDxParamsChanged ...
    || ecoMode;

if doH % change or if the frames changed

    switch spatialTransform
        case "angular spectrum"
            obj.H = ifft2(obj.FH);
        case "Fresnel"
            obj.H = fftshift(fftshift(fft2(obj.FH), 1), 2); %.*obj.PhaseFactor;
        case "None"
            obj.H = single(obj.Frames);
    end

    if svd_filter
        [obj.H, obj.cov, obj.U] = svd_filter(obj.H, svd_threshold, f1, fs, svd_stride, svd_mean);

    end

end

if ecoMode
    obj.FH = [];
end

if ~svd_filter
    obj.cov = [];
    obj.U = [];
end

obj.Output.construct_image_from_SVD(obj.cov, obj.U, size(obj.H));

if doH

    if svdx_filter
        obj.H = svd_x_filter(obj.H, svdx_threshold, f1, fs, floor(max(size(obj.H, 1), size(obj.H, 2)) / svdx_Nsub)); % forced
    end

    if svdx_t_filter
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
            obj.SH = fft(obj.H, [], 3);
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
