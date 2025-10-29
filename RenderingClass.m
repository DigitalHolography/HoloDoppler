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

        obj = RenderFrames(obj, Params, changedParams, image_types, options);
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
