classdef HoloDopplerClass < handle
% Main application class – GPU‑accelerated video rendering.
%
%   HD = HoloDopplerClass() creates an instance with GPU enabled if
%   a compatible GPU is present. To force CPU‑only:
%       HD.useGPU = false;

properties
    file % file info struct
    drawer_list cell
    reader
    render % RenderingClass
    params % parameters struct
    video % ImageTypeList array (one per batch)
    running_averages
    registration
    poolManager
    useGPU (1, 1) logical = true % set to false to force CPU
end

methods

    function obj = HoloDopplerClass()

        if ~isdeployed
            root = fileparts(mfilename('fullpath'));
            addpath( ...
                fullfile(root, 'FolderManagement'), ...
                fullfile(root, 'Imaging'), ...
                fullfile(root, 'Interface'), ...
                fullfile(root, 'ReaderClasses'), ...
                fullfile(root, 'Rendering'), ...
                fullfile(root, 'Saving'), ...
                fullfile(root, 'Saving', 'Registering'), ...
                fullfile(root, 'Tools'), ...
                fullfile(root, 'StandardConfigs'));
        end

        obj.render = RenderingClass();
        set(0, 'defaultfigurecolor', [1 1 1]);

        % Check GPU availability correctly
        if obj.useGPU

            try

                if ~parallel.gpu.GPUDevice.isAvailable()
                    warning('HoloDopplerClass:GPUNotAvailable', ...
                    'GPU requested but not available. Using CPU.');
                    obj.useGPU = false;
                end

            catch % parallel computing toolbox may not be installed
                warning('HoloDopplerClass:NoParallelToolbox', ...
                'Parallel Computing Toolbox not found. Using CPU.');
                obj.useGPU = false;
            end

        end

    end

    function LoadFile(obj, file_path, opt)

        arguments
            obj
            file_path
            opt.params = [];
        end

        % 0) Reset
        obj.reader = [];
        obj.file = [];
        obj.render = RenderingClass();
        obj.video = [];
        obj.running_averages = RunningAveragesHolder();
        obj.registration = [];

        [dir, name, ext] = fileparts(file_path);
        obj.file.path = file_path;
        obj.file.dir = dir;
        obj.file.name = name;
        obj.file.ext = ext;

        % 1) Metadata extraction

        switch ext
            case '.holo'
                holo_versionThreshold = 5; % current is version 7

                try
                    obj.reader = HoloReader(obj.file.path);
                catch ME
                    obj.file = [];
                    obj.reader = [];
                    MEdisp(ME);
                    error("Couldn't read the holo file with holo reader: %s", ME.message)
                end

                fields = properties(obj.reader);

                for i = 1:numel(fields)

                    if ~strcmp(fields{i}, 'filename')
                        obj.file.info.(fields{i}) = obj.reader.(fields{i});
                    end

                end

                obj.file.Nx = obj.reader.frame_width;
                obj.file.Ny = obj.reader.frame_height;

                if obj.reader.version >= holo_versionThreshold
                    obj.file.lambda = obj.reader.footer.compute_settings.image_rendering.lambda;

                    obj.file.ppx = obj.reader.footer.info.pixel_pitch.x * 1e-6; %given in µm
                    obj.file.ppy = obj.reader.footer.info.pixel_pitch.y * 1e-6; %given in µm
                else
                    fprintf("Old version of Holovibes detected, using default parameters.\n")
                    obj.file.lambda = obj.render.LastParams.lambda;

                    obj.file.ppx = obj.render.LastParams.ppx;
                    obj.file.ppy = obj.render.LastParams.ppy;
                end

                try
                    obj.file.fs = obj.reader.footer.info.camera_fps / 1000; %conversion in kHz;
                catch

                    try
                        obj.file.fs = obj.reader.footer.info.input_fps / 1000; %conversion in kHz;
                    catch
                        obj.file.fs = obj.render.LastParams.fs; % default value if nothing at all found
                    end

                end

                obj.file.num_frames = double(obj.reader.num_frames);
            case '.cine'

                try
                    obj.reader = CineReader(obj.file.path);
                catch ME
                    obj.file = [];
                    obj.reader = [];
                    MEdisp(ME);
                    error("The file is not a valid cine file: %s", ME.message)
                end

                fields = properties(obj.reader);

                for i = 1:numel(fields)

                    if ~strcmp(fields{i}, 'filename') && ~strcmp(fields{i}, 'rephasing_data')
                        obj.file.info.(fields{i}) = obj.reader.(fields{i});
                    end

                end

                obj.file.lambda = 852e-9; % default; cine files do not store wavelength — update manually
                obj.file.Nx = double(obj.reader.frame_width);
                obj.file.Ny = double(obj.reader.frame_height);
                obj.file.ppx = 1 / double(obj.reader.horizontal_pix_per_meter);
                obj.file.ppy = 1 / double(obj.reader.vertical_pix_per_meter);
                obj.file.fs = double(obj.reader.frame_rate) / 1000;
                obj.file.num_frames = double(obj.reader.num_frames);

            otherwise
                obj.file = [];
                obj.reader = [];
                fprintf(2, "Unsupported file extension: %s\n", ext)
        end

        % 2) Initialise default parameters
        obj.params.lambda = obj.file.lambda;
        obj.params.fs = obj.file.fs;
        obj.params.ppx = obj.file.ppx;
        obj.params.ppy = obj.file.ppy;
        obj.params.num_frames = obj.file.num_frames;
        obj.params.Nx = obj.file.Nx;
        obj.params.Ny = obj.file.Ny;

        switch obj.file.ext
            case '.holo'
                obj.params.spatialTransform = 'Fresnel';

                if obj.reader.version >= holo_versionThreshold
                    obj.params.spatialPropagation = obj.reader.footer.compute_settings.image_rendering.propagation_distance;

                    try
                        tmp.first = obj.reader.footer.info.timestamps_us.unix_first;
                        tmp.last = obj.reader.footer.info.timestamps_us.unix_last;
                        obj.params.record_time_stamps_us = tmp;
                    catch ME
                        MEdisp(ME);
                        fprintf("No timestamp info found in the holo file, time related parameters will be set to default values.\n")
                    end

                end

            case '.cine'
                obj.params.spatialTransform = 'Fresnel';
                obj.params.spatialPropagation = 1.13; % meters
        end

        obj.params.frequencyRange1 = obj.render.LastParams.frequencyRange1; % the default from init value of rendering class
        obj.params.frequencyRange2 = obj.params.fs / 2;

        % 2) bis) Set Defaults from the StandardConfig

        stdConfigDir = fullfile(fileparts(mfilename('fullpath')), 'StandardConfigs');

        if isfile(fullfile(stdConfigDir, 'CurrentDefault.txt'))
            DefConfName = readlines(fullfile(stdConfigDir, 'CurrentDefault.txt'));

            if ~isempty(DefConfName)
                DefConfName = strtrim(DefConfName(1));
                paramspath = fullfile(stdConfigDir, sprintf('%s.json', DefConfName));

                if isfile(paramspath)
                    obj.loadParams(paramspath);
                end

            end

        end

        % 3) Look for config or last computation params
        baseOutputDir = fullfile(obj.file.dir, obj.file.name);
        preview_folder = fullfile(baseOutputDir, sprintf('%s_HDPreview', obj.file.name));
        preview_params_path = fullfile(preview_folder, sprintf('%s_HDPreview_input_HD_params.json', obj.file.name));
        video_folder = fullfile(baseOutputDir, sprintf('%s_HD', obj.file.name));
        video_params_path = fullfile(video_folder, sprintf('%s_HD_input_HD_params.json', obj.file.name));
        config_params_path = fullfile(baseOutputDir, sprintf('%s_input_HD_params.json', obj.file.name));

        % Load saved config parameters if they exist (prevails over the last computation)
        if isfile(config_params_path)
            fprintf('Loading saved config from %s\n', config_params_path);
            obj.loadParams(config_params_path);
        elseif isfile(video_params_path)
            fprintf('Loading saved video parameters from %s\n', video_params_path);
            obj.loadParams(video_params_path);
        elseif isfile(preview_params_path)
            fprintf('Loading saved preview parameters from %s\n', preview_params_path);
            obj.loadParams(preview_params_path);
        end

        if ~isempty(opt.params)
            obj.setParams(opt.params);
        end

        % Fill missing fields from LastParams
        fields = fieldnames(obj.render.LastParams);

        for i = 1:numel(fields)

            if ~isfield(obj.params, fields{i})
                obj.params.(fields{i}) = obj.render.LastParams.(fields{i});
            end

        end

    end

    function setParams(obj, params)
        % early exit if not a struct
        if ~isstruct(params)
            warning('HoloDopplerClass:setParams:notAStruct', ...
            'setParams called with non‑struct input – ignoring.');
            return
        end

        % Get the full schema array (static method avoids instantiation)
        schemaArray = HDParamSchema.getFullSchema();
        validParamNames = {schemaArray.param};

        % Only process fields that exist in the schema
        fields = fieldnames(params);
        fieldsToSet = intersect(fields, validParamNames);

        for i = 1:numel(fieldsToSet)
            field = fieldsToSet{i};
            value = params.(field);

            % Special validation for imageTypes
            if strcmp(field, 'imageTypes')
                possibleItems = fieldnames(ImageTypeList);
                obj.params.imageTypes = intersect(value, possibleItems, 'stable');
            else
                obj.params.(field) = value;
            end

        end

    end

    function loadParams(obj, path)
        % load the params from a json file and set them in the class
        fid = fopen(path, 'r');

        if fid == -1
            error('HoloDopplerClass:loadParams:cannotOpenFile', 'Cannot open file: %s', path);
        end

        closeFile = onCleanup(@() fclose(fid));

        raw = fread(fid, inf, '*char')';
        decoded = jsondecode(raw);

        if ~isstruct(decoded)
            warning('HoloDopplerClass:loadParams:notAStruct', ...
                'Config file "%s" does not contain a JSON object – ignoring.', path);
            return;
        end

        obj.setParams(decoded);
    end

    function outputPath = saveParams(obj, filename, save_z)
        % save the params as a configfile for the file filename in the
        % current file directory
        if nargin < 2
            name = obj.file.name;
            dir = obj.file.dir;
        else
            [dir, name, ~] = fileparts(filename);
        end

        baseOutputDir = fullfile(dir, name);

        if ~isfolder(baseOutputDir)
            mkdir(baseOutputDir);
        end

        if nargin < 3
            save_z = true;
        end

        parms = obj.params;

        if isfield(parms, 'record_time_stamps_us') && ~save_z %&& strcmp(ext,'.holo') % if you dont want to save the z and prefer to take the automatic one
            % only for holo files because cine dont save the z
            parms = rmfield(parms, 'spatialPropagation');
        end

        if isfield(parms, 'record_time_stamps_us')
            parms = rmfield(parms, 'record_time_stamps_us'); % remove the info fields if they exist as they should be automatically found when loading the file
        end

        if isfield(parms, 'num_frames')
            parms = rmfield(parms, 'num_frames'); %
        end

        if isfield(parms, 'Nx')
            parms = rmfield(parms, 'Nx'); % s
        end

        if isfield(parms, 'Ny')
            parms = rmfield(parms, 'Ny'); %
        end

        if isfield(parms, 'info')
            parms = rmfield(parms, 'info'); %
        end

        outputPath = fullfile(baseOutputDir, sprintf('%s_input_HD_params.json', name));
        fid = fopen(outputPath, 'w');

        if fid == -1
            error('HoloDopplerClass:saveParams:cannotOpenFile', 'Cannot open file for writing: %s', outputPath);
        end

        closeFile = onCleanup(@() fclose(fid));
        fwrite(fid, jsonencode(parms, 'PrettyPrint', true), 'char');
    end

    function images = PreviewRendering(obj)
        % PreviewRendering Construct the image according to the current params
        if isempty(obj.reader)
            error("No file loaded")
        end

        firstframe = obj.reader.read_frame_batch(1, obj.params.framePosition);

        if ~isequal(obj.render.Frames(:, :, 1), firstframe) || obj.params.batchSize ~= size(obj.render.Frames, 3) % if first frame is different of batch sized changed
            obj.render.setFrames(obj.reader.read_frame_batch(obj.params.batchSize, obj.params.framePosition));
        end

        obj.render.Render(obj.params, obj.params.imageTypes);
        images = obj.render.getImages(obj.params.imageTypes);

        for i = 1:numel(obj.params.imageTypes)
            image = images{i};

            if ~ismember(obj.params.imageTypes{i}, {'broadening'}) && size(image, 1) ~= size(image, 2) % do not resize the graphs
                maxDim = max(size(image, 1), size(image, 2));
                image = imresize(image, [maxDim, maxDim]);
            end

            images{i} = image;
        end

    end

    function images = showPreviewImages(obj, images_types)

        if nargin < 2
            images_types = obj.params.imageTypes;
        end

        images = obj.render.getImages(images_types);
        images_res = cell(1, length(images));

        for i = 1:length(images)

            maxDim = max(size(images{i}));

            if isnumeric(images{i}) & ~isempty(images{i})
                images_res{i} = imresize(rescale(images{i}), [maxDim maxDim]);
            elseif isempty(images{i})
                images_res{i} = zeros(maxDim);
            else
                images_res{i} = imresize(rescale(obj.render.Output.(images_types{i}).image), [maxDim maxDim]);
            end

        end

        figure(18); montage(images_res);
    end

    function savePreview(obj, imageTypes)

        if nargin < 2
            imageTypes = obj.params.imageTypes;
        end

        % Base folder named after the file
        baseOutputDir = fullfile(obj.file.dir, obj.file.name);

        if ~isfolder(baseOutputDir)
            mkdir(baseOutputDir);
        end

        % Fixed preview folder name
        result_folder_path = fullfile(baseOutputDir, sprintf('%s_HDPreview', obj.file.name));

        if ~isfolder(result_folder_path)
            mkdir(result_folder_path);
        end

        images = obj.render.getImages(imageTypes);

        for i = 1:numel(images)

            if isempty(images{i})
                continue
            end

            if ~ismember(imageTypes{i}, {'moment_0', 'moment_1', 'moment_2', 'SVD_cov', 'SVD_U', 'FH_modulus_mean', 'FH_arg_mean', 'broadening'})
                max_dim = max(size(images{i}, 1), size(images{i}, 2));
                imwrite(toImageSource(imresize(images{i}, [max_dim, max_dim])), fullfile(result_folder_path, strcat(obj.file.name, '_', imageTypes{i}, '.png')));
            else
                imwrite(toImageSource(images{i}), fullfile(result_folder_path, strcat(obj.file.name, '_', imageTypes{i}, '.png')));
            end

        end

        % Save parameters inside the preview folder
        previewParamsPath = fullfile(result_folder_path, sprintf('%s_HDPreview_input_HD_params.json', obj.file.name));
        fid = fopen(previewParamsPath, 'w');

        if fid ~= -1
            closeFile = onCleanup(@() fclose(fid));
            fwrite(fid, jsonencode(obj.params, 'PrettyPrint', true), 'char');
        else
            warning('Could not write params to %s', previewParamsPath);
        end

    end

    function result_folder_path = VideoRendering(obj)
        p = obj.params;
        if isempty(obj.reader), error("No file loaded"); end

        if isempty(p.first_frame)
            first_frame = 1;
        else
            first_frame = p.first_frame;
        end

        if isempty(p.end_frame) || p.end_frame <= 0
            end_frame = obj.file.num_frames;
        else
            end_frame = min(p.end_frame, obj.file.num_frames);
        end

        num_batches = floor((end_frame - first_frame + 1) / p.batchStride);

        if num_batches * p.batchStride + p.batchSize > end_frame
            num_batches = num_batches - 1;
        end

        if num_batches <= 0
            fprintf('No batches to process.\n');
            return;
        end

        fprintf("==============================\n");
        fprintf("Starting Video Rendering (GPU=%d)\n", obj.useGPU);
        fprintf("File: %s\n", obj.file.path);
        fprintf("Rendering %d frames, %d batches\n", num_batches * p.batchStride, num_batches);
        fprintf("==============================\n");

        % Precompute spatial kernel
        kernel = single(generate_spatial_kernel( ...
            obj.file.Nx, obj.file.Ny, ...
            p.spatialTransform, p.spatialPropagation, ...
            p.lambda, p.ppx, p.ppy));
        if obj.useGPU, kernel = gpuArray(kernel); end

        % Pool setup
        if p.parforArg > 0
            cluster = parcluster;
            maxWorkers = cluster.NumWorkers;

            if p.parforArg > maxWorkers
                warning('Using max workers %d instead of %d', maxWorkers, p.parforArg);
                p.parforArg = maxWorkers;
            end

            if isempty(obj.poolManager)
                obj.poolManager = ParallelPoolManager(p.parforArg);
            end

            obj.poolManager.acquire();
            cleanupPool = onCleanup(@() obj.poolManager.release());
            numWorkers = obj.poolManager.Pool.NumWorkers;
        else
            numWorkers = 0;
        end

        fprintf("Using %d workers.\n", numWorkers);

        WAITBAR_STEP = 1;
        h = waitbar(0, 'Initialising...');
        progress = 0;

        function update_waitbar(increment)
            progress = progress + increment;

            if mod(progress, WAITBAR_STEP) == 0 || progress == num_batches
                waitbar(progress / num_batches, h, ...
                    sprintf('Video rendering %d/%d (%d%%)', ...
                    progress, num_batches, round(100 * progress / num_batches)));
            end

        end

        % --- Reference for registration (FIXED: isfield → isprop) ---
        refPD = [];

        if p.imageRegistration
            refFrames = obj.reader.read_frame_batch(p.refBatchSize, p.framePosition);
            if obj.useGPU, refFrames = gpuArray(single(refFrames)); end
            refView = RenderingClass('precomputeSpatialKernel', kernel);
            refView.setFrames(refFrames);
            refView.Render(p, p.imageTypes, 'cache_intermediate_results', false);
            % Use isprop instead of isfield for object
            if any(strcmp(fieldnames(refView.Output), 'power_Doppler'))
                refPD = single(refView.Output.power_Doppler.image);
                if obj.useGPU, refPD = gpuArray(refPD); end
                refPD = refPD ./ imgaussfilt(refPD, p.flatfield_gw);
            else
                warning('power_Doppler not selected, registration disabled.');
                p.imageRegistration = false;
            end

        end

        % --- Main batch loop ---
        batchResults = cell(1, num_batches);
        regShifts = cell(1, num_batches);
        tRendering = tic;

        if numWorkers == 0 % serial

            for i = 1:num_batches
                [imgs, shift] = processBatch(obj, i, first_frame, p, kernel, refPD);
                batchResults{i} = imgs;
                if p.imageRegistration, regShifts{i} = shift; end
                update_waitbar(1);
            end

        else % parallel
            cKernel = parallel.pool.Constant(kernel);
            D = parallel.pool.DataQueue;
            afterEach(D, @(x) update_waitbar(x));

            parfor i = 1:num_batches
                [imgs, shift] = processBatch(obj, i, first_frame, p, cKernel.Value, refPD);
                batchResults{i} = imgs;
                if p.imageRegistration, regShifts{i} = shift; end
                send(D, 1);
            end

        end

        close(h);
        fprintf('Rendering took %.2f s\n', toc(tRendering));

        % --- Assemble results into ImageTypeList array ---
        obj.video = ImageTypeList.empty(num_batches, 0);

        for i = 1:num_batches
            obj.video(i) = ImageTypeList();
            flds = fieldnames(batchResults{i});

            for f = 1:numel(flds)
                obj.video(i).(flds{f}).image = batchResults{i}.(flds{f});
            end

        end

        % --- Registration (only if enabled AND power_Doppler present) ---
        if p.imageRegistration && any(strcmp(p.imageTypes, 'power_Doppler'))
            obj.registration.shifts = cell2mat(regShifts); % 2×N
            obj.ApplyRegistration();
        end

        % --- Save video (gathers GPU data to CPU) ---
        result_folder_path = obj.SaveVideo();
    end

    function [outImages, shift] = processBatch(obj, batchIdx, first_frame, p, kernel, refPD)
        frameIdx = first_frame + (batchIdx - 1) * p.batchStride;
        frames = obj.reader.read_frame_batch(p.batchSize, frameIdx);

        if obj.useGPU
            frames = gpuArray(single(frames));
        end

        lr = RenderingClass('precomputeSpatialKernel', kernel);
        lr.setFrames(frames);
        lr.Render(p, p.imageTypes, 'cache_intermediate_results', false);

        outImages = struct();

        for j = 1:numel(p.imageTypes)
            outImages.(p.imageTypes{j}) = lr.Output.(p.imageTypes{j}).image;
        end

        shift = [0; 0];

        if p.imageRegistration && isfield(outImages, 'power_Doppler')
            moving = outImages.power_Doppler;
            moving = moving ./ imgaussfilt(moving, p.flatfield_gw);
            shift = obj.computeRegistrationShift(refPD, moving, p.registrationDiskRatio);
        end

    end

    function result_folder_path = SaveVideo(obj, imageTypes, params)

        if obj.useGPU

            for i = 1:numel(obj.video)
                flds = fieldnames(obj.video(i));

                for f = 1:numel(flds)

                    if isa(obj.video(i).(flds{f}).image, 'gpuArray')
                        obj.video(i).(flds{f}).image = gather(obj.video(i).(flds{f}).image);
                    end

                end

            end

        end

        p = obj.params; % to avoid too many obj.params in the code below

        if nargin < 2
            imageTypes = p.imageTypes;
        end

        if nargin < 3
            params = p;
        end

        VideoSavingTime = tic;

        disp('Saving video...');
        h = waitbar(0, 'Saving video...');
        N = double(numel(imageTypes) - 1);

        % Base folder and fixed HD folder
        baseOutputDir = fullfile(obj.file.dir, obj.file.name);

        if ~isfolder(baseOutputDir)
            mkdir(baseOutputDir);
        end

        result_folder_path = fullfile(baseOutputDir, sprintf('%s_HD', obj.file.name));

        if ~isfolder(result_folder_path)
            mkdir(result_folder_path);
        end

        % Create subdirectories
        if ~isfolder(fullfile(result_folder_path, 'avi'))
            mkdir(fullfile(result_folder_path, 'avi'));
        end

        if ~isfolder(fullfile(result_folder_path, 'raw'))
            mkdir(fullfile(result_folder_path, 'raw'));
        end

        if ~isfolder(fullfile(result_folder_path, 'png'))
            mkdir(fullfile(result_folder_path, 'png'));
        end

        % Save each image type
        for i = 1:numel(imageTypes)
            tmp = {obj.video.(imageTypes{i})};
            waitbar((i - 1) / N, h, sprintf("Saving %s", imageTypes{i}))

            if strcmp(imageTypes{i}, 'SH') %SH extraction
                sz = size(tmp{1}.parameters.SH);
                bs = sz(3); % SH binned batchsize
                sz(3) = bs * length(tmp);
                % align the different frequencies in the time direction
                mat = zeros(sz, 'single');

                for j = 1:length(tmp)
                    mat(:, :, (j - 1) * bs + 1:j * bs) = tmp{j}.parameters.SH;
                end

                generate_video(mat, result_folder_path, 'SH', export_raw = 1, temporalFilter = 2);
                continue

            elseif strcmp(imageTypes{i}, 'buckets')
                sz = size(tmp{1}.parameters.intervals_0);
                sz(3) = length(tmp);
                buckranges = reshape(params.bucketsRanges, [], 2);
                numranges = size(buckranges, 1);
                mat0 = zeros(sz, 'single');
                mat1 = zeros(sz, 'single');
                mat2 = zeros(sz, 'single');
                mat_0 = zeros(sz, 'single');

                for j = 1:length(tmp)

                    for k = 1:numranges
                        mat0(:, :, j, k) = tmp{j}.parameters.intervals_0(:, :, :, k);
                        mat1(:, :, j, k) = tmp{j}.parameters.intervals_1(:, :, :, k);
                        mat2(:, :, j, k) = tmp{j}.parameters.intervals_2(:, :, :, k);
                        mat_0(:, :, j, k) = tmp{j}.parameters.M0(:, :, :, k);
                    end

                end

                for k = 1:numranges
                    generate_video(mat0(:, :, :, k), result_folder_path, strcat('moment0_', num2str(buckranges(k, 1)), '_', num2str(buckranges(k, 2)), 'kHz'), export_raw = params.buckets_raw, temporalFilter = 2, square = params.square);
                    generate_video(mat1(:, :, :, k), result_folder_path, strcat('moment1_', num2str(buckranges(k, 1)), '_', num2str(buckranges(k, 2)), 'kHz'), export_raw = params.buckets_raw, temporalFilter = 2, square = params.square);
                    generate_video(mat2(:, :, :, k), result_folder_path, strcat('moment2_', num2str(buckranges(k, 1)), '_', num2str(buckranges(k, 2)), 'kHz'), export_raw = params.buckets_raw, temporalFilter = 2, square = params.square);
                    generate_video(mat_0(:, :, :, k), result_folder_path, strcat('M0_', num2str(buckranges(k, 1)), '_', num2str(buckranges(k, 2)), 'kHz'), export_raw = 0, temporalFilter = 2, square = params.square);
                end

                continue

            elseif strcmp(imageTypes{i}, 'full_buckets')
                sz = size(tmp{1}.parameters.SH_full);
                numSlices = sz(3);
                sz(3) = numSlices;
                sz(4) = length(tmp);
                mat_ = zeros(sz, 'single');

                for j = 1:length(tmp)

                    for k = 1:numSlices
                        mat_(:, :, k, j) = tmp{j}.parameters.SH_full(:, :, k);
                    end

                end

                [~, output_dirname] = fileparts(result_folder_path);
                output_filename_h5 = sprintf('%s_%s.h5', output_dirname, 'output');
                export_h5_video(fullfile(result_folder_path, 'raw', output_filename_h5), "SH_Slices", single(mat_));

                continue

            elseif strcmp(imageTypes{i}, 'SH_avg')

                if ~isempty(obj.running_averages.running_averages)
                    generate_video(fftshift(obj.running_averages.running_averages.SH, 3), ...
                        result_folder_path, strcat(imageTypes{i}), export_raw = 1, temporalFilter = [], square = params.square);
                end

                mat = [];

            else % image extraction
                sz = size(tmp{1}.image);

                if length(sz) == 2
                    sz = [sz 1];
                end

                sz = [sz length(tmp)];
                mat = zeros(sz, 'single');

                for j = 1:length(tmp)

                    if ~isempty(tmp{j}.image)
                        mat(:, :, :, j) = tmp{j}.image;
                    end

                end

            end

            if all(size(size(mat)) == [1 3])
                mat = repmat(mat, [1 1 1 2]); % double the last frame if only one for tech issues
            end

            if ~isempty(mat)

                if strcmp(imageTypes{i}, 'moment_0') % raw moments are always outputted if they are selected
                    generate_video(mat, result_folder_path, 'moment0', export_raw = 1, temporalFilter = 2, square = params.square); % three cases just to rename each correctly for PW
                elseif strcmp(imageTypes{i}, 'moment_1')
                    generate_video(mat, result_folder_path, 'moment1', export_raw = 1, temporalFilter = 2, square = params.square);
                elseif strcmp(imageTypes{i}, 'moment_2')
                    generate_video(mat, result_folder_path, 'moment2', export_raw = 1, temporalFilter = 2, square = params.square);
                elseif strcmp(imageTypes{i}, 'band_ratio')
                    generate_video(mat, result_folder_path, 'band_ratio', export_raw = 1, temporalFilter = 2, square = params.square);
                elseif strcmp(imageTypes{i}, 'power_Doppler')
                    generate_video(mat, result_folder_path, 'M0', temporalFilter = 2, square = params.square);
                elseif strcmp(imageTypes{i}, 'broadening')
                    generate_video(mat, result_folder_path, 'broadening');
                elseif strcmp(imageTypes{i}, 'f_RMS')
                    generate_video(mat, result_folder_path, 'f_RMS');
                elseif strcmp(imageTypes{i}, 'FH_modulus_mean')
                    generate_video(mat, result_folder_path, 'FH_modulus_mean');
                elseif strcmp(imageTypes{i}, 'FH_arg_mean')
                    generate_video(mat, result_folder_path, 'FH_arg_mean');
                elseif strcmp(imageTypes{i}, 'arg_0')
                    generate_video(mat, result_folder_path, 'arg_0', square = params.square);
                elseif strcmp(imageTypes{i}, 'SVD_cov')
                    generate_video(mat, result_folder_path, 'SVD_cov');
                elseif strcmp(imageTypes{i}, 'SVD_U')
                    generate_video(mat, result_folder_path, 'SVD_U');
                elseif strcmp(imageTypes{i}, 'color_Doppler')
                    generate_video(mat, result_folder_path, 'color_Doppler', square = params.square, enhance_contrast = true);
                elseif strcmp(imageTypes{i}, 'color_band_ratio')
                    generate_video(mat, result_folder_path, 'color_band_ratio', substractFlash = false, ...
                        square = params.square, enhance_contrast = false);
                else
                    generate_video(mat, result_folder_path, strcat(imageTypes{i}), temporalFilter = 2, square = params.square);
                end

            else
                fprintf("%s was not found so it cannot be saved.\n", imageTypes{i});
            end

        end

        close(h);

        if p.imageRegistration

            disp('Saving registration...');

            try
                [~, output_dirname] = fileparts(result_folder_path);
                output_filename_h5 = sprintf('%s_%s.h5', output_dirname, 'output');
                export_h5_video(fullfile(result_folder_path, 'raw', output_filename_h5), "registration", single(obj.registration.shifts));
            catch ME
                MEdisp(ME);
                disp("Error while saving the registration.")
            end

        end

        disp('Saving parameters...');

        try
            str = jsonencode(params);
            [~, output_dirname] = fileparts(result_folder_path);
            output_filename_h5 = sprintf('%s_%s.h5', output_dirname, 'output');
            export_h5_string(fullfile(result_folder_path, 'raw', output_filename_h5), "HD_parameters", str);
        catch ME
            MEdisp(ME);
            disp("Error while saving the parameters.")
        end

        videoParamsPath = fullfile(result_folder_path, sprintf('%s_HD_input_HD_params.json', obj.file.name));
        fid = fopen(videoParamsPath, 'w');

        if fid ~= -1
            closeFile2 = onCleanup(@() fclose(fid));
            fwrite(fid, jsonencode(params, 'PrettyPrint', true), 'char');
        else
            warning('HoloDopplerClass:SaveVideo:cannotOpenFile', 'Could not write params to %s', videoParamsPath);
        end

        % Copy version.txt to the HD folder
        appRoot = fileparts(mfilename('fullpath'));
        copyfile(fullfile(appRoot, 'version.txt'), result_folder_path);

        % Try to get git commit hash and branch, and log to git.txt
        try
            % Get current commit hash
            [~, git_hash] = system('git rev-parse HEAD');
            % Get current branch name
            [~, git_branch] = system('git rev-parse --abbrev-ref HEAD');
            % Get last commit log
            [~, git_log] = system('git log -1 --pretty=oneline');
            % Prepare content
            git_info = sprintf('Commit hash: %s\nBranch: %s\nLast commit: %s', ...
                strtrim(git_hash), strtrim(git_branch), strtrim(git_log));
            % Write to file
            fid_git = fopen(fullfile(result_folder_path, 'git.txt'), 'w');

            if fid_git ~= -1
                closeGit = onCleanup(@() fclose(fid_git));
                fwrite(fid_git, git_info, 'char');
            end

        catch ME
            MEdisp(ME);
            disp('No git info.');
        end

        fprintf("Video Saving took : %f s\n", toc(VideoSavingTime));

        fprintf("All done! Results saved in %s\n", result_folder_path);
    end

    function shift = computeRegistrationShift(~, fixed, moving, diskRatio)
        [ny, nx] = size(fixed);

        if diskRatio > 0
            [X, Y] = meshgrid(1:nx, 1:ny);
            cx = nx / 2; cy = ny / 2;
            a = (nx / 2) * diskRatio; b = (ny / 2) * diskRatio;
            mask = ((X - cx) / a) .^ 2 + ((Y - cy) / b) .^ 2 <= 1;
        else
            mask = true(ny, nx);
        end

        if isa(fixed, 'gpuArray')
            mask = gpuArray(mask);
        end

        fixed = (fixed - mean(fixed(mask))) .* mask;
        moving = (moving - mean(moving(mask))) .* mask;
        fixed = fixed ./ max(abs(fixed(:)));
        moving = moving ./ max(abs(moving(:)));

        cross = fft2(fixed) .* conj(fft2(moving));
        cross = ifft2(cross ./ (abs(cross) +1e-12));
        [~, idx] = max(abs(cross(:)));
        [ky0, kx0] = ind2sub([ny, nx], idx);

        shift_y = ky0 - 1;
        shift_x = kx0 - 1;
        if shift_y > ny / 2, shift_y = shift_y - ny; end
        if shift_x > nx / 2, shift_x = shift_x - nx; end
        shift =- [shift_y; shift_x];
    end

    function ApplyRegistration(obj)
        num_batches = numel(obj.video);

        for j = 1:length(obj.params.imageTypes)

            if ismember(obj.params.imageTypes{j}, {'broadening', 'fRMS', 'FH_modulus_mean', 'FH_arg_mean', 'SVD_cov', 'SVD_U'})
                continue
            end

            if strcmp(obj.params.imageTypes{j}, 'SH') %SH extraction
                sz = size(obj.video(1).SH.parameters.SH);
                bs = sz(3);
                ratio = [sz(1) sz(2)] ./ size(obj.video(1).('power_Doppler').image);

                for i = 1:num_batches

                    for m = 1:bs
                        obj.video(i).('SH').parameters.SH(:, :, m) = circshift(obj.video(i).('SH').parameters.SH(:, :, m), floor(obj.registration.shifts(:, i) .* ratio'));
                    end

                end

                continue
            elseif strcmp(obj.params.imageTypes{j}, 'buckets')
                sz = size(obj.video(1).buckets.parameters.intervals_0);

                if length(sz) > 3
                    numF = sz(4);
                else
                    numF = 1;
                end

                ratio = [sz(1) sz(2)] ./ size(obj.video(1).('power_Doppler').image);

                for i = 1:num_batches

                    for k = 1:numF
                        obj.video(i).('buckets').parameters.intervals_0(:, :, :, k) = circshift(obj.video(i).('buckets').parameters.intervals_0(:, :, :, k), floor(obj.registration.shifts(:, i) .* ratio'));
                        obj.video(i).('buckets').parameters.intervals_1(:, :, :, k) = circshift(obj.video(i).('buckets').parameters.intervals_1(:, :, :, k), floor(obj.registration.shifts(:, i) .* ratio'));
                        obj.video(i).('buckets').parameters.intervals_2(:, :, :, k) = circshift(obj.video(i).('buckets').parameters.intervals_2(:, :, :, k), floor(obj.registration.shifts(:, i) .* ratio'));
                        obj.video(i).('buckets').parameters.M0(:, :, :, k) = circshift(obj.video(i).('buckets').parameters.M0(:, :, :, k), floor(obj.registration.shifts(:, i) .* ratio'));
                    end

                end

                continue

            elseif strcmp(obj.params.imageTypes{j}, 'full_buckets')
                sz = size(obj.video(1).full_buckets.parameters.SH_full);

                ratio = [sz(1) sz(2)] ./ size(obj.video(1).('power_Doppler').image);

                for i = 1:num_batches

                    for k = 1:sz(3)
                        obj.video(i).('full_buckets').parameters.SH_full(:, :, k) = circshift(obj.video(i).('full_buckets').parameters.SH_full(:, :, k), floor(obj.registration.shifts(:, i) .* ratio'));
                    end

                end

                continue

            end

            try % in case of not the same image size
                ratio = [size(obj.video(1).(obj.params.imageTypes{j}).image, 1) size(obj.video(1).(obj.params.imageTypes{j}).image, 2)] ./ size(obj.video(1).('power_Doppler').image);
            catch
                ratio = [1 1];
            end

            for i = 1:num_batches
                obj.video(i).(obj.params.imageTypes{j}).image = circshift(obj.video(i).(obj.params.imageTypes{j}).image, floor(obj.registration.shifts(:, i) .* ratio'));
            end

        end

    end

    function show_SH(obj)

        try
            sha = abs(obj.render.SH);
            implay(rescale(sha, InputMin = min(sha, [], [1, 2]), InputMax = max(sha, [], [1, 2])));
        catch ME
            MEdisp(ME);
        end

    end

end

end

function spatialKernel = generate_spatial_kernel(Nx, Ny, transformation, z, lambda, ppx, ppy)

switch transformation
    case 'Fresnel'
        [spatialKernel, ~] = propagation_kernelFresnel(Nx, Ny, z, lambda, ppx, ppy, 0);
    case 'angular spectrum'
        Nd = max(Nx, Ny);
        spatialKernel = propagation_kernelAngularSpectrum(Nd, Nd, z, lambda, ppx, ppy, 0);
    otherwise
        error('Unknown spatial transformation: %s', transformation);
end

end
