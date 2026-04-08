classdef HoloDopplerClass < handle
% Main class replacing the app

properties
    file % stores main file information : path, camera pixel pitches, dimensions, wavelength used, frame rate etc
    drawer_list cell % stores the path of files to be processed % TODO remove
    reader % class obj to read new parts of the file
    render % RenderingClass
    params % rendering parameters
    video % ImageTypeList % store all the output images classes rendered at the end of a cycle
    running_averages %  cumulative average over time
    registration % store the shifts calculated to register images at the end (so that it can be reversed)
    poolManager % ParallelPoolManager object to manage the parallel pool for the video rendering
end

methods

    function obj = HoloDopplerClass()
        %HoloDopplerClass Construct an instance of this class

        if ~isdeployed
            root = fileparts(mfilename('fullpath'));
            addpath( ...
                fullfile(root, 'FolderManagement'), ...
                fullfile(root, 'Imaging'), ...
                fullfile(root, 'Interface'), ...
                fullfile(root, 'ReaderClasses'), ...
                fullfile(root, 'Rendering'), ...
                fullfile(root, 'Saving'), ...
                fullfile(root, 'Scripts'), ...
                fullfile(root, 'Saving', 'Registering'), ...
                fullfile(root, 'Tools'), ...
                fullfile(root, 'StandardConfigs'));
        end

        obj.render = RenderingClass();
        set(0, 'defaultfigurecolor', [1 1 1]); % background of figures in white
    end

    function LoadFile(obj, file_path, opt)

        arguments
            obj
            file_path
            opt.params = []; % Optional parameters to force in case the default behavior (finding existing in the folder is not ideal)
        end

        % LoadFile

        % 0) Reset the reader and the file
        obj.reader = [];
        obj.file = [];
        obj.render = RenderingClass();
        obj.video = [];
        obj.running_averages = RunningAveragesHolder();
        obj.registration = [];

        % file_path path of the file .holo or .cine
        [dir, name, ext] = fileparts(file_path);
        obj.file.path = file_path;
        obj.file.dir = dir;
        obj.file.name = name;
        obj.file.ext = ext;

        %1 ) Metadata extraction

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

        % 2) Rendering parameters initialization
        obj.params.lambda = obj.file.lambda; % wavelength
        obj.params.fs = obj.file.fs; % camera frame rate
        obj.params.ppx = obj.file.ppx; % pixel pitch of the camera
        obj.params.ppy = obj.file.ppy;

        obj.params.num_frames = obj.file.num_frames;
        obj.params.Nx = obj.file.Nx;
        obj.params.Ny = obj.file.Ny;

        switch obj.file.ext
            case '.holo'
                obj.params.spatialTransformation = 'Fresnel';

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
                obj.params.spatialTransformation = 'Fresnel';
                obj.params.spatialPropagation = 1.13; % meters
        end

        obj.params.frequencyRange1 = obj.render.LastParams.frequencyRange1; % the default from init value of rendering class
        obj.params.frequencyRange2 = obj.params.fs / 2;

        %2)bis) Set Defaults from the StandardConfig

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

        % Define the paths for saved preview, video, and config parameters
        filename = obj.file.name;
        filedir = obj.file.dir;
        last_preview_index = get_highest_number_in_directories(filedir, sprintf('%s_HDPreview', filename));
        preview_params_path = fullfile(filedir, sprintf('%s_HDPreview_%d', filename, last_preview_index), sprintf('%s_HDPreview_%d_input_HD_params.json', filename, last_preview_index));
        last_video_index = get_highest_number_in_directories(filedir, sprintf('%s_HD', filename));
        video_params_path = fullfile(filedir, sprintf('%s_HD_%d', filename, last_video_index), sprintf('%s_HD_%d_input_HD_params.json', filename, last_video_index));
        last_config_index = get_highest_number_in_files(filedir, sprintf('%s_input_HD_params_', filename));
        config_params_path = fullfile(filedir, sprintf('%s_input_HD_params_%d.json', filename, last_config_index));

        % Look for old .mat config files existing in the current folder
        [GuiCacheObj, old_mat_path] = findGUICache(filedir, filename);

        if ~isempty(GuiCacheObj)

            if ~isempty(GuiCacheObj.z)
                p.spatialPropagation = GuiCacheObj.z;
            end

            if ~isempty(GuiCacheObj.z_retina)
                p.spatialPropagation = GuiCacheObj.z_retina;
            end

            if ~isempty(GuiCacheObj.spatialTransformation)
                p.spatialTransformation = GuiCacheObj.spatialTransformation;
            end

            if ~isempty(GuiCacheObj.wavelength)
                p.lambda = GuiCacheObj.wavelength;
            end

            fprintf('Loading z parameter from %s\n', old_mat_path);
            obj.setParams(p); % overwrites the z propagation params with the one found in the old mat
        end

        % Load saved preview parameters if they exist
        if isfile(preview_params_path)
            fprintf('Loading saved preview parameters from %s\n', preview_params_path);
            obj.loadParams(preview_params_path);
        end

        % Load saved video parameters if they exist
        if isfile(video_params_path)
            fprintf('Loading saved video parameters from %s\n', video_params_path);
            obj.loadParams(video_params_path);
        end

        % Load saved config parameters if they exist (prevails over the last computation)
        if isfile(config_params_path)
            fprintf('Loading saved config from %s\n', config_params_path);
            obj.loadParams(config_params_path);
        end

        if ~isempty(opt.params) % if optional parameters were supplied, they take precedence
            obj.setParams(opt.params);
        end

        % 4) Add last params from the default init

        fields = fieldnames(obj.render.LastParams);

        for i = 1:numel(fields)

            if ~isfield(obj.params, fields{i})
                obj.params.(fields{i}) = obj.render.LastParams.(fields{i});
            end

        end

    end

    function setParams(obj, params)
        % set class parameters
        fields = fieldnames(params);

        for i = 1:length(fields)

            if ismember(fields{i}, {'record_time_stamps_us', 'num_frames', 'Nx', 'Ny', 'info'})
                continue % do not set info fields
            end

            if strcmp(fields{i}, 'imageTypes')
                possibleItems = fieldnames(ImageTypeList);
                validItems = intersect(params.(fields{i}), possibleItems);
                obj.params.imageTypes = validItems;
            else
                obj.params.(fields{i}) = params.(fields{i});
            end

        end

    end

    function loadParams(obj, path)
        fprintf('Loading parameters from %s\n', path);
        fid = fopen(path, 'r');

        if fid == -1
            error('HoloDopplerClass:loadParams:cannotOpenFile', 'Cannot open file: %s', path);
        end

        closeFile = onCleanup(@() fclose(fid));
        obj.setParams(jsondecode(fread(fid, inf, '*char')'));
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

        if nargin < 3
            save_z = true;
        end

        parms = obj.params;

        if ~save_z %&& strcmp(ext,'.holo') % if you dont want to save the z and prefer to take the automatic one
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

        index = get_highest_number_in_files(dir, strcat(name, '_', 'input_HD_params'));
        outputPath = fullfile(dir, strcat(name, '_', 'input_HD_params_', num2str(index + 1), '.json'));
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

        index = get_highest_number_in_directories(obj.file.dir, strcat(obj.file.name, '_HDPreview'));
        result_folder_path = fullfile(obj.file.dir, strcat(obj.file.name, '_HDPreview_', num2str(index + 1)));

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

        previewParamsPath = fullfile(result_folder_path, [obj.file.name '_HDPreview_' num2str(index + 1) '_input_HD_params.json']);
        fid = fopen(previewParamsPath, 'w');

        if fid ~= -1
            closeFile = onCleanup(@() fclose(fid));
            fwrite(fid, jsonencode(obj.params, 'PrettyPrint', true), 'char');
        else
            warning('HoloDopplerClass:savePreview:cannotOpenFile', 'Could not write params to %s', previewParamsPath);
        end

    end

    function result_folder_path = VideoRendering(obj)
        %VideoRendering Construct the Video according to the current params
        % Close the waitbar from any previous run if it still exists

        p = obj.params; % to avoid too many obj.params in the code below

        if isempty(obj.reader)
            error("No file loaded")
        end

        if ~p.first_frame
            first_frame = 1;
        else
            first_frame = p.first_frame;
        end

        if ~p.end_frame
            end_frame = obj.file.num_frames;
        else
            end_frame = p.end_frame;
        end

        num_batches = floor((end_frame - first_frame + 1) / p.batchStride);

        if num_batches * p.batchStride + p.batchSize > end_frame
            num_batches = num_batches - 1;
        end

        % Command Message
        fprintf("==============================\n");
        fprintf("Starting Video Rendering\n");
        fprintf("File: %s\n", obj.file.path);
        fprintf("Rendering %d frames.\n", num_batches);
        fprintf("==============================\n");

        if num_batches == 0
            return
        end

        % === Gestion optimisée du pool ===
        if p.parforArg > 0

            if isempty(obj.poolManager)
                obj.poolManager = ParallelPoolManager(p.parforArg);
            end

            obj.poolManager.acquire();
            cleanupPool = onCleanup(@() obj.poolManager.release());
            pool = obj.poolManager.Pool;
            numWorkers = pool.NumWorkers;
        else
            numWorkers = 0;
        end

        fprintf("Using %d workers for parallel processing.\n", numWorkers);

        % === Préparation des données ===
        VideoRenderingTime = tic;

        h = waitbar(0, '');
        N = double(num_batches - 1);
        progress = 1;

        function update_waitbar(sig)
            % signal table
            % 0 => increment value
            % 1 => reset for stage 1 (registration)
            % 2 => reset for stage 2 (video_M0 computation)
            switch sig
                case 0
                    waitbar(progress / N, h);
                    progress = progress + 1;
                case -1
                    waitbar(0, h, 'Registration computation...');
                    progress = 1;
                    disp('Registration computation...')
                case -2
                    waitbar(0, h, 'Video rendering...');
                    progress = 1;
                    disp('Video rendering...')
            end

        end

        % 1) First compute the reference for registration and autofocus if needed, and initialize the video storage

        % Waitbar update for registration computation
        update_waitbar(-1);

        if isempty(obj.video) || numel(obj.video) ~= num_batches
            v(1, num_batches) = ImageTypeList();
            obj.video = v; clear v;
        end

        obj.running_averages = RunningAveragesHolder(); %reset this here

        view_ref = RenderingClass();
        view_ref.setFrames(obj.reader.read_frame_batch(p.refBatchSize, p.framePosition));
        view_ref.Render(p, p.imageTypes, cache_intermediate_results = false);

        if p.applyautofocusfromref
            z_opti = autofocus(view_ref, p); % update the z distance
            p.spatialPropagation = z_opti;
        end

        % 2) Then compute the video frames in batches, and update the registration
        % running average after each batch to speed up the convergence of the registration (especially for long videos)

        % Waitbar update for video rendering
        update_waitbar(-2);

        if p.parforArg == 0

            for i = 1:(num_batches)
                obj.render.setFrames(obj.reader.read_frame_batch(p.batchSize, (i - 1) * p.batchStride + first_frame));
                obj.render.Render(p, p.imageTypes);
                obj.video(i) = ImageTypeList();
                obj.video(i).copy_from(obj.render.Output); % work around against handles
                SH_PSD = calc_registration_from_views(obj.render, view_ref, p);
                obj.running_averages.update(SH_PSD, i, p);

                % update waitbar after each batch
                update_waitbar(0);
            end

        else

            D = parallel.pool.DataQueue;
            afterEach(D, @update_waitbar);
            dq = parallel.pool.DataQueue;

            l_video = obj.video;
            afterEach(dq, @(data) obj.running_averages.update(data{1}, data{2}, p));
            l_reader = obj.reader; % reader used by all the workers (if all the file is loaded in RAM it is way faster)

            % parameters
            batchSize = p.batchSize;
            batchStride = p.batchStride;
            imageTypes = p.imageTypes;

            spatialKernel = generate_spatial_kernel( ...
                obj.file.Nx, ...
                obj.file.Ny, ...
                p.spatialTransformation, ...
                p.spatialPropagation, ...
                p.lambda, p.ppx, p.ppy);

            parfor (i = 1:num_batches, numWorkers) % Utiliser numWorkers du pool manager

                l_view = RenderingClass(precomputeSpatialKernel = spatialKernel);
                l_view.setFrames(l_reader.read_frame_batch(batchSize, (i - 1) * batchStride + first_frame));
                l_view.Render(p, imageTypes, cache_intermediate_results = false);
                l_video(i) = ImageTypeList();
                l_video(i).copy_from(l_view.Output);
                send(D, 0);
                SH_PSD = calc_registration_from_views(l_view, view_ref, p);
                send(dq, {SH_PSD, i});

            end

            obj.video = l_video;
        end

        close(h);

        if p.imageRegistration

            if ismember('power_Doppler', p.imageTypes)
                obj.CalculateRegistration();
                obj.ApplyRegistration();
            else
                disp('You need power_Doppler for registration');
            end

        end

        fprintf("Video Rendering took : %f s\n", toc(VideoRenderingTime));

        % Save the video
        result_folder_path = obj.SaveVideo();
    end

    function result_folder_path = SaveVideo(obj, imageTypes, params)

        p = obj.params; % to avoid too many obj.params in the code below

        if nargin < 2
            imageTypes = p.imageTypes;
        end

        if nargin < 3
            params = p;
        end

        VideoSavingTime = tic;

        disp('Saving video...');

        index = get_highest_number_in_directories(obj.file.dir, strcat(obj.file.name, '_HD_'));
        result_folder_path = fullfile(obj.file.dir, strcat(obj.file.name, '_HD_', num2str(index + 1)));

        if ~isfolder(result_folder_path)
            mkdir(result_folder_path);
            mkdir(fullfile(result_folder_path, 'avi'));
            mkdir(fullfile(result_folder_path, 'raw'));
            mkdir(fullfile(result_folder_path, 'png'));
            mkdir(fullfile(result_folder_path, 'mat')); % for previous versions of PW
        end

        for i = 1:numel(imageTypes)
            tmp = {obj.video.(imageTypes{i})};

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
                export_h5_video(fullfile(result_folder_path, 'raw', output_filename_h5), "SH_Slices", mat_);

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
                elseif strcmp(imageTypes{i}, 'energy_ratio_type')
                    generate_video(mat, result_folder_path, 'energy_ratio_type', export_raw = 1, temporalFilter = 2, square = params.square);
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
                    generate_video(mat, result_folder_path, 'color_band_ratio', cornerNorm = 1.2, substractFlash = false, ...
                        square = params.square, enhance_contrast = false);
                else
                    generate_video(mat, result_folder_path, strcat(imageTypes{i}), temporalFilter = 2, square = params.square);
                end

            else
                fprintf("%s was not found so it cannot be saved.\n", imageTypes{i});
            end

        end

        if p.imageRegistration

            disp('Saving registration...');

            try
                [~, output_dirname] = fileparts(result_folder_path);
                output_filename_h5 = sprintf('%s_%s.h5', output_dirname, 'output');
                export_h5_video(fullfile(result_folder_path, 'raw', output_filename_h5), "registration", obj.registration.shifts);
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

        videoParamsPath = fullfile(result_folder_path, [obj.file.name '_HD_' num2str(index + 1) '_input_HD_params.json']);
        fid = fopen(videoParamsPath, 'w');

        if fid ~= -1
            closeFile2 = onCleanup(@() fclose(fid));
            fwrite(fid, jsonencode(params, 'PrettyPrint', true), 'char');
        else
            warning('HoloDopplerClass:SaveVideo:cannotOpenFile', 'Could not write params to %s', videoParamsPath);
        end

        % copy the HD version file
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

        %saving a small mat for old versions of PW
        cache.Fs = p.fs * 1000;
        cache.batchStride = p.batchStride;
        cache.timeTransform.f1 = p.frequencyRange1;
        cache.timeTransform.f2 = p.frequencyRange2;
        save(fullfile(result_folder_path, 'mat', strcat(obj.file.name, '_HD_', num2str(index + 1), '.mat')), "cache");

        fprintf("Video Saving took : %f s\n", toc(VideoSavingTime));

        fprintf("All done! Results saved in %s\n", result_folder_path);
    end

    function CalculateRegistration(obj)
        %RegisterVideo Register the current Video according to the current params
        if isempty(obj.video)
            error("No video rendered")
        end

        num_batches = numel(obj.video);
        obj.registration = struct('shifts', [], 'rotation', [], 'scale', []);

        video_M0 = zeros(obj.file.Ny, obj.file.Nx, 1, num_batches);

        for i = 1:num_batches

            if not(isempty(obj.video(i).power_Doppler.image))
                video_M0(:, :, 1, i) = obj.video(i).power_Doppler.image;
            end

        end

        numY = size(video_M0, 1);
        numX = size(video_M0, 2);

        if obj.params.registrationDiskRatio > 0
            disk_ratio = obj.params.registrationDiskRatio;
            disk = diskMask(numY, numX, disk_ratio);

            if size(disk, 1) ~= size(video_M0, 1)
                disk = disk';
            end

        else
            disk = ones([numY, numX]);
        end

        video_M0_reg = video_M0 .* disk - disk .* sum(video_M0 .* disk, [1, 2]) / nnz(disk); % minus the mean in the disk of each frame
        video_M0_reg = video_M0_reg ./ (max(abs(video_M0_reg), [], [1, 2])); % rescaling each frame but keeps mean at zero

        obj.render.setFrames(obj.reader.read_frame_batch(obj.params.refBatchSize, obj.params.framePosition));
        obj.render.Render(obj.params, obj.params.imageTypes);

        ref_img = obj.render.Output.power_Doppler.image;

        ref_img = ref_img .* disk - disk .* sum(ref_img .* disk, [1, 2]) / nnz(disk); % minus the mean
        ref_img = ref_img ./ (max(abs(ref_img), [], [1, 2])); % rescaling but keeps mean at zero

        [~, obj.registration.shifts] = register_video_from_reference(video_M0_reg, ref_img);
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

    function UndoRegistration(obj)

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
                        obj.video(i).('SH').parameters.SH(:, :, m) = circshift(obj.video(i).('SH').parameters.SH(:, :, m), - floor(obj.registration.shifts(:, i) .* ratio'));
                    end

                end

                continue
            elseif strcmp(obj.params.imageTypes{j}, 'buckets')
                sz = size(obj.video(1).buckets.parameters.intervals_0);
                numF = sz(4);
                ratio = [sz(1) sz(2)] ./ size(obj.video(1).('power_Doppler').image);

                for i = 1:num_batches

                    for k = 1:numF
                        obj.video(i).('buckets').parameters.intervals_0(:, :, :, k) = circshift(obj.video(i).('buckets').parameters.intervals_0(:, :, :, k), - floor(obj.registration.shifts(:, i) .* ratio'));
                        obj.video(i).('buckets').parameters.intervals_1(:, :, :, k) = circshift(obj.video(i).('buckets').parameters.intervals_1(:, :, :, k), - floor(obj.registration.shifts(:, i) .* ratio'));
                        obj.video(i).('buckets').parameters.intervals_2(:, :, :, k) = circshift(obj.video(i).('buckets').parameters.intervals_2(:, :, :, k), - floor(obj.registration.shifts(:, i) .* ratio'));
                        obj.video(i).('buckets').parameters.M0(:, :, :, k) = circshift(obj.video(i).('buckets').parameters.M0(:, :, :, k), - floor(obj.registration.shifts(:, i) .* ratio'));
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
                obj.video(i).(obj.params.imageTypes{j}).image = circshift(obj.video(i).(obj.params.imageTypes{j}).image, - floor(obj.registration.shifts(:, i) .* ratio'));
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

    function SelfTesting(obj)
        %SelfTesting Run the self testing of the class
        obj.VideoRendering();

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
