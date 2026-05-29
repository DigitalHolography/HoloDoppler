classdef HoloDopplerClass < handle
% HoloDopplerClass  GPU-accelerated holographic Doppler video renderer.
%
%   HD = HoloDopplerClass() creates an instance.
%
%   Design rules
%   ------------
%   • HD.params   – rendering parameters ONLY (validated via HDParamSchema).
%                   Single source of truth for all rendering decisions.
%   • HD.file     – file-bound metadata (Nx, Ny, num_frames, fs, lambda,
%                   ppx, ppy, path, dir, name, ext, info).
%                   Never duplicated in HD.params.
%   • All writes to HD.params go through setParams(), which calls
%     HDParamSchema.validate() and replaces any corrupt field with its
%     schema default.

properties
    file % file metadata struct  (Nx, Ny, num_frames, fs, …)
    drawer_list cell
    reader
    render % RenderingClass
    params % rendering parameters struct (schema-validated)
    video % ImageTypeList array (one per batch)
    running_averages
    registration
    poolManager
end

methods

    % =====================================================================
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
        obj.params = HDParamSchema.getDefaults(); % always start clean
        set(0, 'defaultfigurecolor', [1 1 1]);
    end

    % =====================================================================
    function LoadFile(obj, file_path, opt)

        arguments
            obj
            file_path
            opt.params = []
            opt.interactive = true % seul flag restant
        end

        % 0) Reset state
        obj.reader = [];
        obj.file = [];
        obj.render = RenderingClass();
        obj.video = [];
        obj.running_averages = RunningAveragesHolder();
        obj.registration = [];

        [dir_, name, ext] = fileparts(file_path);
        obj.file.path = file_path;
        obj.file.dir = dir_;
        obj.file.name = name;
        obj.file.ext = ext;

        % ------------------------------------------------------------------
        % 1) Lecture des métadonnées (remplit obj.file)
        % ------------------------------------------------------------------
        holo_versionThreshold = 5;

        switch ext
            case '.holo'

                try
                    obj.reader = HoloReader(obj.file.path);
                catch ME
                    obj.file = []; obj.reader = [];
                    MEdisp(ME);
                    error('HoloDopplerClass:LoadFile:holoReadFailed', ...
                        "Couldn't read the holo file: %s", ME.message)
                end

                for f = properties(obj.reader)'
                    fn = f{1};

                    if ~strcmp(fn, 'filename')
                        obj.file.info.(fn) = obj.reader.(fn);
                    end

                end

                obj.file.Nx = obj.reader.frame_width;
                obj.file.Ny = obj.reader.frame_height;

                if obj.reader.version >= holo_versionThreshold
                    obj.file.lambda = obj.reader.footer.compute_settings.image_rendering.lambda;
                    obj.file.ppx = obj.reader.footer.info.pixel_pitch.x * 1e-6;
                    obj.file.ppy = obj.reader.footer.info.pixel_pitch.y * 1e-6;
                else
                    fprintf("Old Holovibes version – using schema defaults for lambda/ppx/ppy.\n")
                    defs = HDParamSchema.getDefaults();
                    obj.file.lambda = defs.lambda_file_default;
                    obj.file.ppx = defs.ppx_file_default;
                    obj.file.ppy = defs.ppy_file_default;
                end

                try
                    obj.file.fs = obj.reader.footer.info.camera_fps / 1000;
                catch

                    try
                        obj.file.fs = obj.reader.footer.info.input_fps / 1000;
                    catch
                        obj.file.fs = 1;
                        fprintf("No fps info found in holo file – defaulting fs to 1 kHz.\n")
                    end

                end

                obj.file.num_frames = double(obj.reader.num_frames);

                try
                    obj.file.record_time_stamps_us.first = obj.reader.footer.info.timestamps_us.unix_first;
                    obj.file.record_time_stamps_us.last = obj.reader.footer.info.timestamps_us.unix_last;
                catch
                    % ignore
                end

            case '.cine'

                try
                    obj.reader = CineReader(obj.file.path);
                catch ME
                    obj.file = []; obj.reader = [];
                    MEdisp(ME);
                    error('HoloDopplerClass:LoadFile:cineReadFailed', ...
                        "The file is not a valid cine file: %s", ME.message)
                end

                for f = properties(obj.reader)'
                    fn = f{1};

                    if ~strcmp(fn, 'filename') && ~strcmp(fn, 'rephasing_data')
                        obj.file.info.(fn) = obj.reader.(fn);
                    end

                end

                obj.file.lambda = 852e-9;
                obj.file.Nx = double(obj.reader.frame_width);
                obj.file.Ny = double(obj.reader.frame_height);
                obj.file.ppx = 1 / double(obj.reader.horizontal_pix_per_meter);
                obj.file.ppy = 1 / double(obj.reader.vertical_pix_per_meter);
                obj.file.fs = double(obj.reader.frame_rate) / 1000;
                obj.file.num_frames = double(obj.reader.num_frames);

            otherwise
                obj.file = []; obj.reader = [];
                fprintf(2, "Unsupported file extension: %s\n", ext)
                return
        end

        % ------------------------------------------------------------------
        % 2) Obtention des paramètres de rendu (UNIQUE SOURCE)
        % ------------------------------------------------------------------
        if isempty(opt.params)
            % Construire le struct fileInfo avec les métadonnées déjà lues
            fileInfo.Nx = obj.file.Nx;
            fileInfo.Ny = obj.file.Ny;
            fileInfo.num_frames = obj.file.num_frames;
            fileInfo.lambda = obj.file.lambda;
            fileInfo.ppx = obj.file.ppx;
            fileInfo.ppy = obj.file.ppy;
            fileInfo.fs = obj.file.fs;
            fileInfo.ext = ext;

            if isfield(obj.file, 'record_time_stamps_us')
                % propagation distance peut être stockée dans le footer .holo
                try
                    fileInfo.propagation_distance = obj.reader.footer.compute_settings.image_rendering.propagation_distance;
                catch
                end

            end

            obj.params = getFileParameters(file_path, fileInfo);
        else
            % Paramètres fournis de l'extérieur (ex: batch après getFileParameters)
            obj.params = HDParamSchema.validate(opt.params);
        end

    end

    % =====================================================================
    function setParams(obj, params)
        % Merge params into obj.params and validate the result.
        % Any field whose value is corrupt is silently replaced by the
        % schema default. Logs a warning per corrected field.
        %
        % File-bound fields (Nx, Ny, num_frames, fs, lambda, ppx, ppy) are
        % silently ignored here – they must be set through HD.file.

        if ~isstruct(params)
            warning('HoloDopplerClass:setParams:notAStruct', ...
            'setParams called with non-struct input – ignoring.');
            return
        end

        fileBound = {'Nx', 'Ny', 'num_frames', 'fs', 'lambda', 'ppx', 'ppy'};

        % Merge incoming fields over current params.
        merged = obj.params;
        fields = fieldnames(params);

        for k = 1:numel(fields)

            if ~ismember(fields{k}, fileBound)
                merged.(fields{k}) = params.(fields{k});
            end

        end

        % Validate the merged struct — corrupt fields fall back to defaults.
        obj.params = HDParamSchema.validate(merged);
    end

    % =====================================================================
    function loadParams(obj, path)
        % Load params from a JSON file and merge-validate into obj.params.
        fid = fopen(path, 'r');

        if fid == -1
            error('HoloDopplerClass:loadParams:cannotOpenFile', ...
                'Cannot open file: %s', path);
        end

        closeFile = onCleanup(@() fclose(fid));

        raw = fread(fid, inf, '*char')';
        decoded = jsondecode(raw);

        if ~isstruct(decoded)
            warning('HoloDopplerClass:loadParams:notAStruct', ...
                'Config file "%s" does not contain a JSON object – ignoring.', path);
            return
        end

        obj.setParams(decoded);
    end

    % =====================================================================
    function outputPath = saveParams(obj, filename, save_z)
        % Save rendering params as a JSON config file.
        % File-bound fields are never saved (they come from the file itself).

        if nargin < 2 || isempty(filename)
            name = obj.file.name;
            dir_ = obj.file.dir;
        else
            [dir_, name, ~] = fileparts(filename);
        end

        if nargin < 3
            save_z = true;
        end

        baseOutputDir = fullfile(dir_, name);

        if ~isfolder(baseOutputDir)
            mkdir(baseOutputDir);
        end

        parms = obj.params;

        % Strip file-bound fields that should never be persisted.
        stripFields = {'Nx', 'Ny', 'num_frames', 'fs', 'lambda', 'ppx', 'ppy', 'info'};

        for k = 1:numel(stripFields)

            if isfield(parms, stripFields{k})
                parms = rmfield(parms, stripFields{k});
            end

        end

        % Optionally strip spatialPropagation so it is re-derived on load.
        if ~save_z && isfield(obj.file, 'record_time_stamps_us')

            if isfield(parms, 'spatialPropagation')
                parms = rmfield(parms, 'spatialPropagation');
            end

        end

        outputPath = fullfile(baseOutputDir, ...
            sprintf('%s_input_HD_params.json', name));
        fid = fopen(outputPath, 'w');

        if fid == -1
            error('HoloDopplerClass:saveParams:cannotOpenFile', ...
                'Cannot open file for writing: %s', outputPath);
        end

        closeFile = onCleanup(@() fclose(fid));
        fwrite(fid, jsonencode(parms, 'PrettyPrint', true), 'char');
    end

    function clearParams(obj)
        % CLEARPARAMS Delete per‑file JSON parameter files for the current file.

        if isempty(obj) || isempty(obj.file)
            warning('clearParams:noFile', 'No file loaded.');
            return;
        end

        filePath = obj.file.path;
        [fileDir, fileName, ~] = fileparts(filePath);
        baseOutputDir = fullfile(fileDir, fileName);

        % The two per‑file config paths (same logic as getFileParameters)
        configPaths = {
                       fullfile(baseOutputDir, sprintf('%s_input_HD_params.json', fileName)), ...
                           fullfile(baseOutputDir, sprintf('%s_HD', fileName), sprintf('%s_HD_input_HD_params.json', fileName))
                       };

        % Keep only files that actually exist
        existing = cell(1, numel(configPaths));

        for k = 1:numel(configPaths)

            if isfile(configPaths{k})
                existing{k} = configPaths{k};
            end

        end

        if isempty(existing)
            fprintf('No parameter files found to delete.\n');
            return;
        end

        % Delete each file and record the deleted path
        for k = 1:numel(existing)
            delete(existing{k});
        end

        fprintf('Deleted all parameter file(s).\n');
    end

    % =====================================================================
    function images = PreviewRendering(obj)
        % Render the current frame batch with current params.
        if isempty(obj.reader)
            error('HoloDopplerClass:PreviewRendering:noFile', 'No file loaded')
        end

        p = obj.params;
        firstframe = obj.reader.read_frame_batch(1, p.framePosition);

        if ~isequal(obj.render.Frames(:, :, 1), firstframe) || ...
                p.batchSize ~= size(obj.render.Frames, 3)
            obj.render.setFrames( ...
                obj.reader.read_frame_batch(p.batchSize, p.framePosition));
        end

        % Pass file metadata alongside rendering params.
        renderParams = obj.buildRenderParams();
        obj.render.Render(renderParams, p.imageTypes);
        images = obj.render.getImages(p.imageTypes);

        for i = 1:numel(p.imageTypes)
            image = images{i};

            if ~ismember(p.imageTypes{i}, {'broadening'}) && ...
                    size(image, 1) ~= size(image, 2)
                maxDim = max(size(image, 1), size(image, 2));
                image = imresize(image, [maxDim, maxDim]);
            end

            images{i} = image;
        end

    end

    % =====================================================================
    function images = showPreviewImages(obj, images_types)

        if nargin < 2
            images_types = obj.params.imageTypes;
        end

        images = obj.render.getImages(images_types);
        images_res = cell(1, length(images));

        for i = 1:length(images)
            maxDim = max(size(images{i}));

            if isnumeric(images{i}) && ~isempty(images{i})
                images_res{i} = imresize(rescale(images{i}), [maxDim maxDim]);
            elseif isempty(images{i})
                images_res{i} = zeros(maxDim);
            else
                images_res{i} = imresize( ...
                    rescale(obj.render.Output.(images_types{i}).image), ...
                    [maxDim maxDim]);
            end

        end

        figure(18); montage(images_res);
    end

    % =====================================================================
    function savePreview(obj, imageTypes)

        if nargin < 2
            imageTypes = obj.params.imageTypes;
        end

        baseOutputDir = fullfile(obj.file.dir, obj.file.name);
        if ~isfolder(baseOutputDir), mkdir(baseOutputDir); end

        result_folder_path = fullfile(baseOutputDir, ...
            sprintf('%s_HDPreview', obj.file.name));
        if ~isfolder(result_folder_path), mkdir(result_folder_path); end

        images = obj.render.getImages(imageTypes);

        for i = 1:numel(images)
            if isempty(images{i}), continue; end

            if ~ismember(imageTypes{i}, ...
                    {'moment_0', 'moment_1', 'moment_2', 'SVD_cov', 'SVD_U', ...
                     'FH_modulus_mean', 'FH_arg_mean', 'broadening'})
                max_dim = max(size(images{i}, 1), size(images{i}, 2));
                imwrite(toImageSource(imresize(images{i}, [max_dim, max_dim])), ...
                    fullfile(result_folder_path, ...
                    strcat(obj.file.name, '_', imageTypes{i}, '.png')));
            else
                imwrite(toImageSource(images{i}), ...
                    fullfile(result_folder_path, ...
                    strcat(obj.file.name, '_', imageTypes{i}, '.png')));
            end

        end

        % Save params snapshot alongside the preview.
        previewParamsPath = fullfile(result_folder_path, ...
            sprintf('%s_HDPreview_input_HD_params.json', obj.file.name));
        fid = fopen(previewParamsPath, 'w');

        if fid ~= -1
            closeFile = onCleanup(@() fclose(fid));
            fwrite(fid, jsonencode(obj.params, 'PrettyPrint', true), 'char');
        else
            warning('HoloDopplerClass:savePreview:cannotWrite', ...
                'Could not write params to %s', previewParamsPath);
        end

    end

    % =====================================================================
    function result_folder_path = VideoRendering(obj)
        p = obj.params;

        if isempty(obj.reader)
            error('HoloDopplerClass:VideoRendering:noFile', 'No file loaded');
        end

        first_frame = p.first_frame;

        if isempty(first_frame) || first_frame < 1
            first_frame = 1;
        end

        end_frame = p.end_frame;

        if isempty(end_frame) || end_frame <= 0 || ~isfinite(end_frame)
            end_frame = obj.file.num_frames;
        else
            end_frame = min(end_frame, obj.file.num_frames);
        end

        num_batches = floor((end_frame - first_frame + 1) / p.batchStride);

        if num_batches * p.batchStride + p.batchSize > end_frame
            num_batches = num_batches - 1;
        end

        if num_batches <= 0
            fprintf('No batches to process.\n');
            return
        end

        fprintf("==============================\n");
        fprintf("Starting Video Rendering\n");
        fprintf("File: %s\n", obj.file.path);
        fprintf("Rendering %d frames, %d batches\n", ...
            num_batches * p.batchStride, num_batches);
        fprintf("==============================\n");

        % Precompute spatial kernel using file metadata.
        kernel = single(generate_spatial_kernel( ...
            obj.file.Nx, obj.file.Ny, ...
            p.spatialTransform, p.spatialPropagation, ...
            obj.file.lambda, obj.file.ppx, obj.file.ppy));

        % Pool setup.
        if p.parforArg > 0
            cluster = parcluster;
            maxWorkers = cluster.NumWorkers;

            if p.parforArg > maxWorkers
                warning('Using max workers %d instead of %d', ...
                    maxWorkers, p.parforArg);
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
        h = waitbar(0, 'Initializing...');
        progress = 0;

        function update_waitbar(increment)
            progress = progress + increment;

            if mod(progress, WAITBAR_STEP) == 0 || progress == num_batches
                waitbar(progress / num_batches, h, ...
                    sprintf('Video rendering %d/%d (%d%%)', ...
                    progress, num_batches, ...
                    round(100 * progress / num_batches)));
            end

        end

        % Build the combined param struct once for workers.
        renderParams = obj.buildRenderParams();

        batchResults = cell(1, num_batches);
        tRendering = tic;

        if numWorkers == 0

            for i = 1:num_batches
                batchResults{i} = processBatch(obj, i, first_frame, renderParams, kernel);
                update_waitbar(1);
            end

        else
            cKernel = parallel.pool.Constant(kernel);
            D = parallel.pool.DataQueue;
            afterEach(D, @(x) update_waitbar(x));

            parfor i = 1:num_batches
                batchResults{i} = processBatch(obj, i, first_frame, renderParams, cKernel.Value);
                send(D, 1);
            end

        end

        close(h);
        fprintf('Rendering took %.2f s\n', toc(tRendering));

        % Assemble results into ImageTypeList array.
        obj.video = ImageTypeList.empty(num_batches, 0);

        for i = 1:num_batches
            obj.video(i) = ImageTypeList();
            flds = fieldnames(batchResults{i});

            for f = 1:numel(flds)
                obj.video(i).(flds{f}).image = batchResults{i}.(flds{f});
            end

        end

        % Registration.
        if p.imageRegistration && any(strcmp(p.imageTypes, 'power_Doppler'))
            obj.CalculateRegistration();
            obj.ApplyRegistration();
        end

        result_folder_path = obj.SaveVideo();
    end

    % =====================================================================
    function [outImages] = processBatch(obj, batchIdx, first_frame, renderParams, kernel)
        frameIdx = first_frame + (batchIdx - 1) * renderParams.batchStride;
        frames = obj.reader.read_frame_batch(renderParams.batchSize, frameIdx);

        lr = RenderingClass('precomputeSpatialKernel', kernel);
        lr.setFrames(frames);
        lr.Render(renderParams, renderParams.imageTypes, ...
            'cache_intermediate_results', false);

        outImages = struct();

        for j = 1:numel(renderParams.imageTypes)
            outImages.(renderParams.imageTypes{j}) = ...
                lr.Output.(renderParams.imageTypes{j}).image;
        end

    end

    % =====================================================================
    function CalculateRegistration(obj)

        if isempty(obj.video)
            error('HoloDopplerClass:CalculateRegistration:noVideo', ...
            'No video rendered')
        end

        num_batches = numel(obj.video);
        obj.registration = struct('shifts', [], 'rotation', [], 'scale', []);

        video_M0 = zeros(obj.file.Ny, obj.file.Nx, 1, num_batches);

        for i = 1:num_batches

            if ~isempty(obj.video(i).power_Doppler.image)
                video_M0(:, :, 1, i) = obj.video(i).power_Doppler.image;
            end

        end

        numY = size(video_M0, 1);
        numX = size(video_M0, 2);

        if obj.params.registrationDiskRatio > 0
            disk = diskMask(numY, numX, obj.params.registrationDiskRatio);
            if size(disk, 1) ~= numY, disk = disk'; end
        else
            disk = ones([numY, numX]);
        end

        video_M0_reg = video_M0 .* disk - disk .* ...
            sum(video_M0 .* disk, [1, 2]) / nnz(disk);
        video_M0_reg = video_M0_reg ./ max(abs(video_M0_reg), [], [1, 2]);

        renderParams = obj.buildRenderParams();
        obj.render.setFrames(obj.reader.read_frame_batch( ...
            obj.params.refBatchSize, obj.params.framePosition));
        obj.render.Render(renderParams, obj.params.imageTypes);
        ref_img = obj.render.Output.power_Doppler.image;

        ref_img = ref_img .* disk - disk .* ...
            sum(ref_img .* disk, [1, 2]) / nnz(disk);
        ref_img = ref_img ./ max(abs(ref_img(:)));

        [~, obj.registration.shifts] = ...
            register_video_from_reference(video_M0_reg, ref_img);
    end

    % =====================================================================
    function result_folder_path = SaveVideo(obj, imageTypes, params)

        p = obj.params;

        if nargin < 2, imageTypes = p.imageTypes; end
        if nargin < 3, params = p; end

        VideoSavingTime = tic;
        disp('Saving video...');
        h = waitbar(0, 'Saving video...');
        N = double(numel(imageTypes) - 1);

        baseOutputDir = fullfile(obj.file.dir, obj.file.name);
        if ~isfolder(baseOutputDir), mkdir(baseOutputDir); end

        result_folder_path = fullfile(baseOutputDir, ...
            sprintf('%s_HD', obj.file.name));
        if ~isfolder(result_folder_path), mkdir(result_folder_path); end

        for sub = {'avi', 'h5', 'png', 'json'}
            subdir = fullfile(result_folder_path, sub{1});
            if ~isfolder(subdir), mkdir(subdir); end
        end

        generateParametersJson(params, obj.file, result_folder_path)

        config = getConfigs();

        for i = 1:numel(imageTypes)
            tmp = {obj.video.(imageTypes{i})};
            waitbar((i - 1) / N, h, ...
                sprintf("Saving %s", strrep(imageTypes{i}, '_', ' ')))

            if strcmp(imageTypes{i}, 'SH')
                sz = size(tmp{1}.parameters.SH);
                bs = sz(3);
                sz(3) = bs * length(tmp);
                mat = zeros(sz, 'single');

                for j = 1:length(tmp)
                    mat(:, :, (j - 1) * bs + 1:j * bs) = tmp{j}.parameters.SH;
                end

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
                        mat0 (:, :, j, k) = tmp{j}.parameters.intervals_0(:, :, :, k);
                        mat1 (:, :, j, k) = tmp{j}.parameters.intervals_1(:, :, :, k);
                        mat2 (:, :, j, k) = tmp{j}.parameters.intervals_2(:, :, :, k);
                        mat_0(:, :, j, k) = tmp{j}.parameters.M0(:, :, :, k);
                    end

                end

                continue

            elseif strcmp(imageTypes{i}, 'full_buckets')
                sz = size(tmp{1}.parameters.SH_full);
                numSl = sz(3);
                sz(4) = length(tmp);
                mat_ = zeros(sz, 'single');

                for j = 1:length(tmp)

                    for k = 1:numSl
                        mat_(:, :, k, j) = tmp{j}.parameters.SH_full(:, :, k);
                    end

                end

                [~, output_dirname] = fileparts(result_folder_path);
                output_filename_h5 = sprintf('%s_%s.h5', output_dirname, 'output');
                export_h5_video( ...
                    fullfile(result_folder_path, 'h5', output_filename_h5), ...
                    "SH_Slices", single(mat_));
                continue

            elseif strcmp(imageTypes{i}, 'SH_avg')
                mat = [];

            else
                sz = size(tmp{1}.image);
                if length(sz) == 2, sz = [sz 1]; end
                sz(end + 1) = length(tmp); %#ok<AGROW>
                mat = zeros(sz, 'single');

                for j = 1:length(tmp)

                    if ~isempty(tmp{j}.image)
                        mat(:, :, :, j) = tmp{j}.image;
                    end

                end

            end

            if all(size(size(mat)) == [1 3])
                mat = repmat(mat, [1 1 1 2]);
            end

            if ~isempty(mat)
                type = imageTypes{i};

                if isfield(config, type)
                    cfg = config.(type);
                    nvPairs = namedargs2cell(cfg.opts);
                    generate_video(mat, result_folder_path, cfg.name, nvPairs{:});
                else
                    generate_video(mat, result_folder_path, type, ...
                        'square', params.square);
                end

            else
                fprintf("%s was not found – skipping.\n", imageTypes{i});
            end

        end

        close(h);

        % ---- Registration ------------------------------------------------
        if p.imageRegistration
            disp('Saving registration...');

            try
                [~, output_dirname] = fileparts(result_folder_path);
                output_filename_h5 = sprintf('%s_%s.h5', output_dirname, 'output');
                export_h5_video( ...
                    fullfile(result_folder_path, 'h5', output_filename_h5), ...
                    "registration", single(obj.registration.shifts));
            catch ME
                MEdisp(ME);
                disp("Error while saving the registration.")
            end

        end

        % ---- Parameters --------------------------------------------------
        disp('Saving parameters...');

        try
            [~, output_dirname] = fileparts(result_folder_path);
            output_filename_h5 = sprintf('%s_%s.h5', output_dirname, 'output');
            export_h5_string( ...
                fullfile(result_folder_path, 'h5', output_filename_h5), ...
                "HD_parameters", jsonencode(params));
        catch ME
            MEdisp(ME);
            disp("Error while saving the parameters.")
        end

        videoParamsPath = fullfile(result_folder_path, ...
            sprintf('%s_HD_input_HD_params.json', obj.file.name));
        fid = fopen(videoParamsPath, 'w');

        if fid ~= -1
            closeFile2 = onCleanup(@() fclose(fid));
            fwrite(fid, jsonencode(params, 'PrettyPrint', true), 'char');
        else
            warning('HoloDopplerClass:SaveVideo:cannotOpenFile', ...
                'Could not write params to %s', videoParamsPath);
        end

        % ---- Version / git -----------------------------------------------
        appRoot = fileparts(mfilename('fullpath'));
        copyfile(fullfile(appRoot, 'version.txt'), result_folder_path);

        try
            [~, git_hash] = system('git rev-parse HEAD');
            [~, git_branch] = system('git rev-parse --abbrev-ref HEAD');
            [~, git_log] = system('git log -1 --pretty=oneline');
            git_info = sprintf('Commit hash: %s\nBranch: %s\nLast commit: %s', ...
                strtrim(git_hash), strtrim(git_branch), strtrim(git_log));
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

    % =====================================================================
    function ApplyRegistration(obj)
        num_batches = numel(obj.video);

        for j = 1:length(obj.params.imageTypes)

            itype = obj.params.imageTypes{j};

            if ismember(itype, {'broadening', 'fRMS', 'FH_modulus_mean', 'FH_arg_mean', 'SVD_cov', 'SVD_U'})
                continue
            end

            pdImage = obj.video(1).('power_Doppler').image;

            if strcmp(itype, 'SH')
                sz = size(obj.video(1).SH.parameters.SH);
                bs = sz(3);
                ratio = [sz(1) sz(2)] ./ size(pdImage);

                for i = 1:num_batches

                    for m = 1:bs
                        obj.video(i).('SH').parameters.SH(:, :, m) = ...
                            circshift( ...
                            obj.video(i).('SH').parameters.SH(:, :, m), ...
                            floor(obj.registration.shifts(:, i) .* ratio'));
                    end

                end

                continue

            elseif strcmp(itype, 'buckets')
                sz = size(obj.video(1).buckets.parameters.intervals_0);

                if numel(sz) > 3
                    numF = sz(4);
                else
                    numF = 1;
                end

                ratio = [sz(1) sz(2)] ./ size(pdImage);

                for i = 1:num_batches

                    for k = 1:numF
                        shift = floor(obj.registration.shifts(:, i) .* ratio');
                        obj.video(i).('buckets').parameters.intervals_0(:, :, :, k) = ...
                            circshift(obj.video(i).('buckets').parameters.intervals_0(:, :, :, k), shift);
                        obj.video(i).('buckets').parameters.intervals_1(:, :, :, k) = ...
                            circshift(obj.video(i).('buckets').parameters.intervals_1(:, :, :, k), shift);
                        obj.video(i).('buckets').parameters.intervals_2(:, :, :, k) = ...
                            circshift(obj.video(i).('buckets').parameters.intervals_2(:, :, :, k), shift);
                        obj.video(i).('buckets').parameters.M0(:, :, :, k) = ...
                            circshift(obj.video(i).('buckets').parameters.M0(:, :, :, k), shift);
                    end

                end

                continue

            elseif strcmp(itype, 'full_buckets')
                sz = size(obj.video(1).full_buckets.parameters.SH_full);
                ratio = [sz(1) sz(2)] ./ size(pdImage);

                for i = 1:num_batches

                    for k = 1:sz(3)
                        obj.video(i).('full_buckets').parameters.SH_full(:, :, k) = ...
                            circshift( ...
                            obj.video(i).('full_buckets').parameters.SH_full(:, :, k), ...
                            floor(obj.registration.shifts(:, i) .* ratio'));
                    end

                end

                continue
            end

            try
                ratio = [size(obj.video(1).(itype).image, 1) ...
                             size(obj.video(1).(itype).image, 2)] ./ size(pdImage);
            catch
                ratio = [1 1];
            end

            for i = 1:num_batches
                obj.video(i).(itype).image = circshift( ...
                    obj.video(i).(itype).image, ...
                    floor(obj.registration.shifts(:, i) .* ratio'));
            end

        end

    end

end % public methods

% =========================================================================
methods (Access = private)

    function rp = buildRenderParams(obj)
        % Merge rendering params with the file-bound metadata that
        % RenderingClass needs (lambda, ppx, ppy, fs, Nx, Ny).
        % This is the ONE place where HD.file values are injected into a
        % params struct passed to the renderer — they are never stored
        % back into HD.params.
        rp = obj.params;
        rp.lambda = obj.file.lambda;
        rp.ppx = obj.file.ppx;
        rp.ppy = obj.file.ppy;
        rp.fs = obj.file.fs;
        rp.Nx = obj.file.Nx;
        rp.Ny = obj.file.Ny;
        rp.num_frames = obj.file.num_frames;
    end

end % private methods

end % classdef

% =========================================================================
% Module-level helpers
% =========================================================================

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

function [config, defaultUnknown] = getConfigs()
config = struct();
defaultOpts = struct('temporalFilter', [], 'square', true, 'export_raw', true, ...
    'substractFlash', true, 'enhance_contrast', false, ...
    'contrast_inversion', false, 'cornerNorm', false, 'export_avg_img', true);

config.moment_0 = struct('name', 'moment0', 'opts', defaultOpts);
config.moment_1 = struct('name', 'moment1', 'opts', defaultOpts);
config.moment_2 = struct('name', 'moment2', 'opts', defaultOpts);
config.band_ratio = struct('name', 'band_ratio', 'opts', defaultOpts);
config.LF_M0 = struct('name', 'LF_M0', 'opts', defaultOpts);
config.HF_M0 = struct('name', 'HF_M0', 'opts', defaultOpts);

opts_pd = defaultOpts;
opts_pd.export_raw = false;
config.power_Doppler = struct('name', 'M0', 'opts', opts_pd);

simpleOpts = struct('temporalFilter', [], 'square', false, 'export_raw', false, ...
    'substractFlash', true, 'enhance_contrast', false);
config.broadening = struct('name', 'broadening', 'opts', simpleOpts);
config.f_RMS = struct('name', 'f_RMS', 'opts', simpleOpts);
config.FH_modulus_mean = struct('name', 'FH_modulus_mean', 'opts', simpleOpts);
config.FH_arg_mean = struct('name', 'FH_arg_mean', 'opts', simpleOpts);

config.arg_0 = struct('name', 'arg_0', 'opts', struct('square', true));
config.SVD_cov = struct('name', 'SVD_cov', 'opts', struct());
config.SVD_U = struct('name', 'SVD_U', 'opts', struct());
config.color_Doppler = struct('name', 'color_Doppler', ...
    'opts', struct('square', true, 'enhance_contrast', true));
config.color_band_ratio = struct('name', 'color_band_ratio', ...
    'opts', struct('substractFlash', false, 'square', true, 'enhance_contrast', false));

defaultUnknown = struct('temporalFilter', 2, 'square', true);
end
