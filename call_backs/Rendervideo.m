function Rendervideo(app)
% main program loop
% Select a file and call other functions
% to perform a full computation and create
% output videos.

if strcmp(app.outputvideoDropDown.Value, 'dark field') && (app.z_reconstruction == app.z_iris)
    app.Switch.Value = 'z_retina';
    app.ZSwitchValueChanged();
end

if ~app.file_loaded
    return
end

% start clock to monitor
% computation duration

tic;

% Generate output directory
output_dirname = create_output_directory_name(app.filepath, app.filename);
output_dirpath = fullfile(app.filepath, output_dirname);
mkdir(output_dirpath);
mkdir(fullfile(output_dirpath, 'avi'));
mkdir(fullfile(output_dirpath, 'mp4'));
mkdir(fullfile(output_dirpath, 'png'));
mkdir(fullfile(output_dirpath, 'mat'));
mkdir(fullfile(output_dirpath, 'log'));
mkdir(fullfile(output_dirpath, 'raw'));

% Logfiles Generation (diary off in the end of the function)
[~, name, ~] = fileparts(app.filename);
% Turn On Diary Logging
diary off
% first turn off diary, so as not to log this script
diary_filename = fullfile(output_dirpath, 'log', 'CommandWindowLog.txt');
% setup temp variable with filename + timestamp, echo off
set(0, 'DiaryFile', diary_filename)
% set the objectproperty DiaryFile of hObject 0 to the temp variable filename
clear diary_filename
% clean up temp variable
diary on
% turn on diary logging
fprintf("======================================\n")
fprintf("Current Folder Path: %s\n", app.filepath)
fprintf("Current File: %s\n", name)
fprintf("Start Computer Time: %s\n", datetime('now', 'Format', 'yyyy/MM/dd HH:mm:ss'))

saveGit(output_dirpath)

% logs = app.cache.notes;
% save_string_cells_to_file(fullfile(output_dirpath, 'log', txt_filename), logs);

% save all gui parameters to a struct.
% The current computation will fetch every parameter
% from the cache and not from the gui.
% The purpose of this is to prevent gui interactions
% to mess up the parameters while a computation is ongoing.
set_up = app.setUpDropDown.Value;

app.cache = GuiCache(app);
num_workers = app.cache.nb_cpu_cores;

aberration_correction = AberrationCorrection();
image_registration = ImageRegistration();

% select parallelism policy
switch app.cache.parallelism
    case 'CPU multithread'
        %                     parfor_arg = app.numCPUCores(0.2);
        % parfor_arg = Inf;
        parfor_arg = num_workers;
        use_multithread = true;
        use_gpu = false;
    case 'GPU parallelization'
        parfor_arg = 3;
        use_multithread = false;
        reset(gpuDevice(1)); % clear memory
        use_gpu = check_GPU_for_render(app, parfor_arg);
    case 'CPU singlethread'
        parfor_arg = 0;
        use_multithread = false;
        use_gpu = false;
    case 'CPU/GPU rendering/optim'
        % TODO
        % parfor_arg = app.numCPUCores(0.2);
        % parfor_arg = Inf;
        parfor_arg = num_workers;
        use_multithread = true;
        reset(gpuDevice(1));
        use_gpu = check_GPU_for_render(app);
        
end

if use_gpu
    disp("Using GPU.")
else
    disp("Not using GPU.")
end

% create proxy variables so that the entire gui
% is not broadcasted to workers
% in the parfor loops
% in parfor (batch_idx = 1:num_batches, parfor_arg)
% error message: "Dot indexing is not supported for variables of this type".

istream = app.interferogram_stream;
j_win = app.cache.batch_size;
j_step = app.cache.batch_stride;
local_time_transform = app.cache.time_transform;
local_blur = app.cache.blur;
local_Nx = app.Nx;
local_Ny = app.Ny;
local_wavelength = app.cache.wavelength;
local_svd = app.SVDCheckBox.Value;
local_output_video = app.cache.output_videos;
local_rephasing = app.cache.rephasing;
local_low_memory = app.cache.low_memory;
local_spatialTransformation = app.cache.spatialTransformation;
local_temporal_filter = app.cache.temporal_filter;
local_SubAp_PCA.Value = app.SubAp_PCA.Value;
local_SubAp_PCA.min = app.SubAp_PCA.min;
local_SubAp_PCA.max = app.SubAp_PCA.max;
local_temporal = app.temporalCheckBox.Value;
local_phi1 = app.phi1EditField.Value;
local_phi2 = app.phi2EditField.Value;
local_spatial = app.spatialCheckBox.Value;
local_nu1 = app.nu1EditField.Value;
local_nu2 = app.nu2EditField.Value;
local_volume_size = floor(j_win / 2);
local_SVDx = app.SVDxCheckBox.Value;
local_SVDx_SubAp_num = app.SVDx_SubApEditField.Value;
localSVDTreshold = app.SVDTresholdCheckBox.Value;
localSVDTresholdValue = app.SVDTresholdEditField.Value;
num_F = app.numFreqEditField.Value;

% FIXME
num_focus = 1;
enable_peripheral_defocus_correction = false;

if ~isempty(app.image_registration)
    local_image_registration = cat(1, app.image_registration.translation_x, app.image_registration.translation_y);
    
    if size(local_image_registration, 2) == floor((app.interferogram_stream.num_frames - app.batchsizeEditField.Value) / app.cache.batch_stride) % if registration from previous folder results
        disp('found last registration that will be used.')
    end
    
else
    local_image_registration = [];
end

% FIXME : add new elements to cache

if local_rephasing
    local_rephasing_data = app.rephasing_data;
else
    local_rephasing_data = [];
end

switch app.cache.spatialTransformation
    case 'angular spectrum'
        local_kernel = app.kernelAngularSpectrum; % propagation kernel initialization
    case 'Fresnel'
        local_kernel = app.kernelFresnel; % propagation kernel initialization
end

acquisition = DopplerAcquisition(app.Nx, app.Ny, app.cache.Fs / 1000, app.cache.z, app.cache.z_retina, app.cache.z_iris, app.cache.wavelength, app.cache.DX, app.cache.DY, app.cache.pix_width, app.cache.pix_height);

local_low_frequency = app.cache.low_frequency;
local_color_f1 = app.cache.color_f1;
local_color_f2 = app.cache.color_f2;
local_color_f3 = app.cache.color_f3;
local_xystride = app.cache.xystride;
local_num_unit_cells_x = app.cache.num_unit_cells_x;
local_r1 = app.cache.r1;
local_image_type_list = ImageTypeList();

% allocate video buffers
%             num_batches = floor((app.interferogram_stream.num_frames - app.cache.batch_size) / app.cache.batch_stride);
local_num_frames = app.interferogram_stream.num_frames;
local_num_batches = floor((app.interferogram_stream.num_frames - app.batchsizeEditField.Value) / app.cache.batch_stride);

if local_low_memory
    [~, output_dirname] = fileparts(output_dirpath);
    output_filename = sprintf('%s_M0_tmp.%s', output_dirname, 'raw');
    fd_M0 = fopen(sprintf('%s\\%s', output_dirpath, output_filename), 'w');
else
    
    switch local_output_video
        case 'power_Doppler'
            local_image_type_list.select('power_Doppler');
            video_M0 = zeros(app.Nx, app.Ny, 1, local_num_batches, 'single');
            
        case 'moments'
            local_image_type_list.select('power_Doppler', 'moment_0', 'moment_1', 'moment_2');
            video_M0 = zeros(app.Nx, app.Ny, 1, local_num_batches, 'single');
            video_moment0 = video_M0;
            video_moment1 = video_M0;
            video_moment2 = video_M0;
            
        case 'all_videos'
            app.time_transform.type = 'FFT';
            local_image_type_list.select('power_Doppler', 'power_1_Doppler', 'power_2_Doppler', 'color_Doppler', 'directional_Doppler', 'M0sM1r', 'velocity_estimate', 'spectrogram', 'moment_0', 'moment_1', 'moment_2')
            
            video_M0 = zeros(app.Nx, app.Ny, 1, local_num_batches, 'single');
            video_M1 = video_M0;
            video_M2 = video_M0;
            video_moment0 = video_M0;
            video_moment1 = video_M0;
            video_moment2 = video_M0;
            video_M1_over_M0 = video_M0;
            video_M2_over_M0 = video_M0;
            video_M_freq_low = video_M0;
            video_M_freq_high = video_M0;
            video_M0_pos = video_M0;
            video_M0_neg = video_M0;
            video_M0sM1r = video_M0;
            
            video_velocity = zeros(app.Nx, app.Ny, 3, local_num_batches, 'single');
            
            video_directional = zeros(local_Nx, local_Ny, 3, local_num_batches, 'single');
            video_fmean = video_directional;
            
            % video_mask = video_M0;
            % psf_through_time = video_M0;
            % spectrogram_array = zeros(j_win, local_num_batches, 'single');
            
            %FIX ME binx biny bint binw à paramétriser et
            %mettre dans le .mat + config
            bin_x = 4;
            bin_y = 4;
            bin_t = 1;
            bin_w = 16;
            % SH_time = zeros(app.Nx, app.Ny, 1, j_win, 1, 'single');
            %FIX ME prévoir les cas ou ça tombe pas entier
            SH_time = zeros(app.Nx / bin_x, app.Ny / bin_y, 1, j_win / bin_w, ceil(local_num_batches / bin_t), 'single');
            % SH_time = zeros(256, 256, 1, 32, ceil(local_num_batches/bin_t), 'single');
            % tmp_SH = zeros(app.Nx, app.Ny, 1, j_win,ceil(local_num_batches/bin_t), 'single');
            % idx_tab_SH_time = 1:ceil(local_num_batches/bin_t);
            % idx_tab_SH_time = repmat(idx_tab_SH_time,2,1);
            % idx_tab_SH_time = reshape(idx_tab_SH_time,[],1);s
            
        case 'dark_field'
            local_image_type_list.select('dark_field_image');
            H_dark_field_stack = 1i * ones(app.Nx, app.Ny, j_win, local_num_batches, 'single');
            video_M0_dark_field = zeros(app.Nx, app.Ny, 1, local_num_batches, 'single');
            
        case 'choroid'
            local_image_type_list.select('power_Doppler', 'moment_0', 'moment_1', 'moment_2', 'choroid');
            video_M0 = zeros(app.Nx, app.Ny, 1, local_num_batches, 'single');
            video_moment0 = video_M0;
            video_moment1 = video_M0;
            video_moment2 = video_M0;
            images_choroid =  zeros(app.Nx, app.Ny, 1, local_num_batches, num_F, 'single');
            
            
    end %switch local_output_video
    
end

% parfor waitbar
% we have to use a DataQueue
% since there are no synchronization
% primitives in matlab (mutex)
D = parallel.pool.DataQueue;
h = waitbar(0, '');
afterEach(D, @update_waitbar);
N = double(local_num_batches - 1);
p = 1;

%% first pass - compute shifts for video registration
registration_pass = app.cache.registration_via_phase;

if registration_pass
    current_batch_idx = 1 + floor(app.positioninfileSlider.Value / (app.cache.batch_size + app.cache.batch_stride));
    shifts = compute_temporal_registration(istream, app.cache, j_win, j_step, current_batch_idx, local_blur, ...
        local_kernel, [], D, use_multithread);
    % tilts zernikes used for translating an image
    zernikes = evaluate_zernikes([1 1], [1 -1], app.Nx, app.Ny);
else
    % declare unused variables to make matlab parfor
    % loop parser happy - stupid matlab
    shifts = zeros(3, local_num_batches, 'single');
    zernikes = zeros(app.Nx, app.Ny, 2, 'single');
end

enable_iterative_optimization = app.IterativeoptimizationCheckBox.Value;
enable_shack_hartmann = app.ShackHartmannCheckBox.Value;
zernike_projection = app.ZernikeProjectionCheckBox.Value;

correction_coefs = [];
correction_zernikes = [];
previous_zernike_indices = [];

if enable_shack_hartmann
    % aberration computation pass
    %
    % Implementation - Shack Hartmann simulation
    
    % shack hartmann params
    zernike_ranks = app.cache.shack_hartmann_zernike_ranks;
    image_subapertures_size_ratio = app.cache.image_subapertures_size_ratio;
    num_subapertures_positions = app.cache.num_subapertures_positions;
    subaperture_margin = app.cache.subaperture_margin;
    ref_image = app.cache.shack_hartmann_ref_image;
    
    calibration_factor = 20;
    corrmap_margin = 0.4;
    
    power_filter_corrector = 1;
    sigma_filter_corrector = 1;
    
    shack_hartmann = ShackHartmann(image_subapertures_size_ratio, num_subapertures_positions, [], calibration_factor, subaperture_margin, corrmap_margin, power_filter_corrector, sigma_filter_corrector, ref_image);
    
    % select subapertures to exclude, depending on the number
    % of subaperture used. This is chosen experimentally, the
    % value of the number of subapertures is constrained in the
    % GUI so the following switch should always branch to a
    % valid choice of excluded_subapertures
    %                 switch num_subapertures
    %                     case 4
    %                         excluded_subapertures = [1; 4; 13; 16];
    %                     case 5
    %                         excluded_subapertures = [1; 5; 21; 25];
    %                     case 6
    %                         excluded_subapertures = [1; 2; 5; 6; 7; 12; 25; 30; 31; 32; 35; 36];
    %                     case 7
    %                         excluded_subapertures = [1; 2; 6; 7; 8; 14; 36; 42; 43; 44; 48; 49];
    %                     case 8
    %                         excluded_subapertures = [1; 2; 7; 8; 9; 16; 49; 56; 57; 58; 63; 64];
    %                     otherwise
    %                         error('Unreachable code was reached. Check value of num_subapertures');
    %                 end
    excluded_subapertures = shack_hartmann.excluded_subapertures();
    
    % perform iterative aberration computation with shack-hartmann
    for r = 2:zernike_ranks
        send(D, 3); % reset progress bar
        
        % r-th zernike line has r+1 zernikes in it
        cur_num_zernikes = r + 1;
        
        % compute indices of the zernikes of current rank
        current_zernike_indices = (cur_num_zernikes * (cur_num_zernikes - 1) / 2):(cur_num_zernikes * (cur_num_zernikes - 1) / 2 + cur_num_zernikes - 1);
        
        % apply previous aberration correction
        [current_correction_coefs, stiched_moments_video, shifts_vector, stitched_correlation_video] = compute_correction_shack_hartmann(istream, app.cache, local_kernel, local_rephasing_data, app.blur, [], D, use_gpu, use_multithread, current_zernike_indices, ...
            shifts, image_subapertures_size_ratio, num_subapertures_positions, calibration_factor, subaperture_margin, corrmap_margin, power_filter_corrector, sigma_filter_corrector, excluded_subapertures, previous_zernike_indices, correction_coefs);
        [~, current_correction_zernikes] = zernike_phase(current_zernike_indices, app.Nx, app.Ny);
        
        correction_coefs = [correction_coefs; current_correction_coefs];
        correction_zernikes = cat(3, correction_zernikes, current_correction_zernikes);
        previous_zernike_indices = [previous_zernike_indices, current_zernike_indices];
    end
    
    measured_phase = stitch_phase(shifts_vector, [], local_Nx, local_Ny, shack_hartmann);
    % save correction coefs and indices for future export
    aberration_correction.shack_hartmann_zernike_indices = previous_zernike_indices;
    aberration_correction.shack_hartmann_zernike_coefs = correction_coefs;
end

if enable_iterative_optimization
    % aberration computation pass
    %
    % Implementation - Entropy optimization
    %
    % here we generate a set of zernike coefficients
    % that represent the aberation present on the
    % reconstructed images
    
    % compute coefficients for high order zernikes
    % we make a different optimization pass for each
    % additional zernike rank
    
    % reset correction indices and coefs arrays that ay have
    % been set by the shack hartmann pass
    zernike_indices = [];
    correction_coefs = [];
    
    zernike_ranks = app.optimizationzernikeranksEditField.Value;
    
    for r = 2:zernike_ranks
        send(D, 4); % reset progress bar
        num_zernikes = r + 1; % map to zernfun zernike ordering
        
        % construct high order zernike indices
        current_zernike_indices = (num_zernikes * (num_zernikes - 1) / 2):(num_zernikes * (num_zernikes - 1) / 2 + num_zernikes - 1);
        
        % compute correction
        current_cor = compute_correction(istream, app.cache, local_kernel, local_rephasing_data, app.blur, [], D, use_gpu, use_multithread, current_zernike_indices, app.cache.zernikes_tol, app.cache.mask_num_iter, ...
            app.cache.max_constraint, shifts, previous_zernike_indices, correction_coefs);
        [~, current_correction_zernikes] = zernike_phase(current_zernike_indices, app.Nx, app.Ny);
        
        % append coefs to correction coefs array
        correction_coefs = [correction_coefs; current_cor];
        correction_zernikes = cat(3, correction_zernikes, current_correction_zernikes);
        previous_zernike_indices = [previous_zernike_indices current_zernike_indices];
        zernike_indices = [zernike_indices current_zernike_indices];
    end
    
    % save correction coefs and indices for future export
    aberration_correction.iterative_opt_zernike_indices = zernike_indices;
    aberration_correction.iterative_opt_zernike_coefs = correction_coefs;
end

if ~enable_shack_hartmann && ~enable_iterative_optimization % no aberration compensation at all
    % define dummy unused variables with good size
    % to make matlab parfor parser happy - stupid matlab
    measured_phase = zeros(app.Nx, app.Ny, local_num_batches, 'single');
    correction_coefs = zeros(3, istream.num_frames, 'single');
    correction_zernikes = zeros(app.Nx, app.Ny, 3, 'single');
end

[rephasing_zernikes, shack_zernikes, iterative_zernikes] = aberration_correction.generate_zernikes(app.Nx, app.Ny);

%% Final pass
% Here we apply all transformations computed in previous passes
% and construct the videos

% There are two ways of doing this, the first one is a 'low
% memory' mode in which the reconstructed data is cached on a
% file on the disk to avoid allocating massive video buffers.
% This is useful when the batch stride is so small that the
% whole video buffer would overflow memory.
%
% The second one is a more straightforward mode in which whole
% video buffers are allocated and stored in RAM. This is the
% default and most simple mode

% FIXME : wrap most routines into functions to factorize the "if
% local_low_memory" statement

poolobj = gcp('nocreate'); % check if a pool already exist

if isempty(poolobj)
    poolobj = parpool(parfor_arg); % create a new pool
elseif poolobj.NumWorkers ~= parfor_arg
    delete(poolobj); %close the current pool to create a new one with correct num of workers
    poolobj = parpool(parfor_arg);
end

if local_low_memory
    reg_frame_batch = app.interferogram_stream.read_frame_batch(app.refbatchsizeEditField.Value, floor(app.positioninfileSlider.Value));
    reg_FH = fftshift(fft2(reg_frame_batch)) .* app.kernelAngularSpectrum;
    reg_FH = rephase_FH(reg_FH, local_rephasing_data, app.refbatchsizeEditField.Value, floor(app.positioninfileSlider.Value));
    acquisition = DopplerAcquisition(app.Nx, app.Ny, app.Fs / 1000, app.cache.z, app.cache.z_retina, app.cache.z_iris, app.cache.wavelength, app.cache.DX, app.cache.DY, app.pix_width, app.pix_height);
    reg_hologram = reconstruct_hologram(reg_FH, acquisition, app.blur, use_gpu, app.SVDCheckBox.Value, app.SVDxCheckBox.Value, app.SVDx_SubApEditField.Value, [], app.cache.time_transform, local_spatialTransformation);
    
    block_size = 1024; % TODO: this should stay hardcoded but to a higher value
    block_M0 = zeros(app.Nx, app.Ny, 1, block_size);
    send(D, -2); % display 'video construction' on progress bar
    
    for batch_idx = 1:block_size:local_num_batches
        last_iter = min(batch_idx - 1 + block_size, local_num_batches) - batch_idx + 1;
        fprintf("Parfor loop: %u workers\n", parfor_arg)
        tParfor = tic;
        
        parfor (inner_idx = 1:last_iter, parfor_arg)
            frame_batch = istream.read_frame_batch(j_win, (batch_idx - 1 + inner_idx - 1) * j_step);
            FH_par = compute_FH_from_frame_batch(frame_batch, local_kernel, local_spatialTransformation, use_gpu);
            
            if local_rephasing
                FH_par = rephase_FH(FH_par, local_rephasing_data, j_win, (batch_idx - 1 + inner_idx - 1) * j_step);
            end
            
            % add tilted phase for FH registration
            if registration_pass
                FH_par = register_FH(FH_par, shifts(:, batch_idx:(batch_idx + 1) - 1), j_win, 1);
            end
            
            if enable_iterative_optimization || enable_shack_hartmann
                
                if zernike_projection
                    phase = aberration_correction.compute_total_phase(batch_idx, rephasing_zernikes, shack_zernikes, iterative_zernikes);
                    correction = exp(-1i * phase);
                else
                    %                             phase = aberration_correction.compute_total_phase(batch_idx,rephasing_zernikes,[],iterative_zernikes);
                    phase = measured_phase(:, :, batch_idx);
                    correction = exp(-1i * phase);
                end
                
                % apply correction
                FH_par = FH_par .* correction;
            end
            
            if strcmp(set_up, 'Doppler')
                [M0, ~, ~] = reconstruct_hologram(FH_par, acquisition, local_blur, false, local_svd, local_SVDx, local_SVDx_SubAp_num, [], local_time_transform, local_spatialTransformation);
                % save frame to block buffer
                block_M0(:, :, :, inner_idx) = gather(M0);
                send(D, 0);
            end
            
            send(D, 0);
        end
        
        tEndParfor = toc(tParfor);
        fprintf("Parfor loop took %f s\n", tEndParfor)
        
        if app.cache.registration
            
            if size(local_image_registration, 2) == local_num_batches % if registration from previous folder results
                block_M0 = register_video_from_shifts(block_M0(:, :, :, 1:last_iter), local_image_registration(1:2, :));
                shifts(:, batch_idx:batch_idx + last_iter - 1) = local_image_registration(1:2, batch_idx:batch_idx + last_iter - 1);
            else
                [block_M0, block_shifts] = register_video_from_reference(block_M0(:, :, :, 1:last_iter), reg_hologram);
                shifts(:, batch_idx:batch_idx + last_iter - 1) = block_shifts;
            end
            
        end
        
        % write block to file
        fwrite(fd_M0, block_M0(:), 'single');
    end
    
    fclose(fd_M0);
    
    if app.cache.registration
        % save shifts for export
        image_registration.translation_x = shifts(1, :);
        image_registration.translation_y = shifts(2, :);
    end
    
    export_raw = app.saverawvideosCheckBox.Value;
    generate_video_low_memory(sprintf('%s\\%s', output_dirpath, output_filename), app.Nx, app.Ny, 1, local_num_batches, output_dirpath, 'M0', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw);
else % ~local_low_memory
    send(D, -2); % display 'video construction' on progress bar
    fprintf("Parfor loop: %u workers\n", parfor_arg)
    tParfor = tic;
    
    parfor batch_idx = 1:local_num_batches
        
        % for batch_idx = 1:num_batches
        frame_batch = istream.read_frame_batch(j_win, (batch_idx - 1) * j_step);
        use_gpu_par = use_gpu;
        FH_par = compute_FH_from_frame_batch(frame_batch, local_kernel, local_spatialTransformation, use_gpu);
        local_image_type_list_par = local_image_type_list;
        
        if local_rephasing
            FH_par = rephase_FH(FH_par, local_rephasing_data, j_win, (batch_idx - 1) * j_step);
        end
        
        % add tilted phase for FH registration
        if registration_pass
            FH_par = register_FH(FH_par, shifts(:, batch_idx:(batch_idx + 1) - 1), j_win, 1);
        end
        
        if enable_iterative_optimization || enable_shack_hartmann
            
            if zernike_projection
                phase = aberration_correction.compute_total_phase(batch_idx, rephasing_zernikes, shack_zernikes, iterative_zernikes);
                correction = exp(-1i * phase);
            else
                %                             phase = aberration_correction.compute_total_phase(batch_idx,rephasing_zernikes,[],iterative_zernikes);
                phase = measured_phase(:, :, batch_idx);
                correction = exp(-1i * phase);
            end
            
            % apply correction
            FH_par = FH_par .* correction;
        end
        
        if strcmp(set_up, 'Doppler')
            local_image_type_list_par.construct_image(FH_par, local_wavelength, acquisition, local_blur, use_gpu, local_svd, localSVDTreshold, local_SVDx, localSVDTresholdValue, local_SVDx_SubAp_num, [], local_color_f1, local_color_f2, local_color_f3, ...
                0, local_spatialTransformation, local_time_transform, local_SubAp_PCA, local_xystride, local_num_unit_cells_x, local_r1, ...
                local_temporal, local_phi1, local_phi2, local_spatial, local_nu1, local_nu2, num_F);
            
            switch local_output_video
                case 'all_videos'
                    %                         [M0, sqrt_M0, M1, M2, M_freq_low, M_freq_high, M0_pos, M0_neg, M1sM0r, velocity] = reconstruct_hologram_extra(FH_par, local_wavelength, local_f1, local_f2, acquisition, local_blur, false, local_svd, [],...
                    %                             local_color_f1, local_color_f2, local_color_f3);
                    
                    tmp_video_M0 = gather(local_image_type_list_par.power_Doppler.image);
                    video_M0(:, :, :, batch_idx) = tmp_video_M0;
                    video_M1(:, :, :, batch_idx) = gather(local_image_type_list_par.power_1_Doppler.image);
                    video_M2(:, :, :, batch_idx) = gather(local_image_type_list_par.power_2_Doppler.image);
                    video_moment0(:, :, :, batch_idx) = gather(local_image_type_list_par.moment_0.image);
                    video_moment1(:, :, :, batch_idx) = gather(local_image_type_list_par.moment_1.image);
                    video_moment2(:, :, :, batch_idx) = gather(local_image_type_list_par.moment_2.image);
                    video_M1_over_M0(:, :, :, batch_idx) = gather(local_image_type_list_par.power_1_Doppler.image) ./ gather(local_image_type_list_par.power_Doppler.image);
                    video_M2_over_M0(:, :, :, batch_idx) = gather(local_image_type_list_par.power_2_Doppler.image) ./ gather(local_image_type_list_par.power_Doppler.parameters.M0_sqrt);
                    video_M_freq_low(:, :, :, batch_idx) = gather(local_image_type_list_par.color_Doppler.parameters.freq_low);
                    video_M_freq_high(:, :, :, batch_idx) = gather(local_image_type_list_par.color_Doppler.parameters.freq_high);
                    tmp_video_M0_pos = gather(local_image_type_list_par.directional_Doppler.parameters.M0_pos);
                    video_M0_pos(:, :, :, batch_idx) = tmp_video_M0_pos;
                    tmp_video_M0_neg = gather(local_image_type_list_par.directional_Doppler.parameters.M0_neg);
                    video_M0_neg(:, :, :, batch_idx) = tmp_video_M0_neg;
                    tmp_video_M0sM1r = gather(local_image_type_list_par.M0sM1r.image);
                    video_M0sM1r(:, :, :, batch_idx) = tmp_video_M0sM1r;
                    video_velocity(:, :, :, batch_idx) = gather(local_image_type_list_par.velocity_estimate.image);
                    video_directional(:, :, :, batch_idx) = construct_directional_video(tmp_video_M0_pos, tmp_video_M0_neg, local_temporal_filter);
                    video_fmean(:, :, :, batch_idx) = construct_fmean_video(tmp_video_M0sM1r, tmp_video_M0, local_temporal_filter);
                    
                    % video_mask(:,:,:,batch_idx) = gather(local_images_par.spectrogram.image);
                    % spectrogram_array(:,batch_idx) = gather(local_images_par.spectrogram.parameters.vector);
                    
                    bin_t = 1;
                    
                    if (batch_idx / bin_t) == round(batch_idx / bin_t)
                        %tmp_SH(:,:,:,:,batch_idx) = gather(local_images_par.spectrogram.parameters.SH);
                        % FIXME : Binning propre x,y,w,t
                        %SH_time(:,:,:,:,batch_idx) = tmp_SH(1:size(SH_time,1),1:size(SH_time,2),1,1:size(SH_time,4),batch_idx);
                        SH_time(:, :, :, :, batch_idx) = gather(local_image_type_list_par.spectrogram.parameters.SH);
                    end
                    
                    % FIXME : modify entire reconstruct hologram
                    % extras to acquire additional videos
                case 'dark_field'
                    H_dark_field_stack(:, :, :, batch_idx) = gather(local_image_type_list_par.dark_field_image.parameters.H);
                    video_M0_dark_field(:, :, :, batch_idx) = gather(local_image_type_list_par.dark_field_image.image);
                case 'power_Doppler'
                    tmp_video_M0 = gather(local_image_type_list_par.power_Doppler.image);
                    video_M0(:, :, :, batch_idx) = tmp_video_M0;
                case 'moments'
                    tmp_video_M0 = gather(local_image_type_list_par.power_Doppler.image);
                    video_M0(:, :, :, batch_idx) = tmp_video_M0;
                    video_moment0(:, :, :, batch_idx) = gather(local_image_type_list_par.moment_0.image);
                    video_moment1(:, :, :, batch_idx) = gather(local_image_type_list_par.moment_1.image);
                    video_moment2(:, :, :, batch_idx) = gather(local_image_type_list_par.moment_2.image);
                case 'choroid'
                    tmp_video_M0 = gather(local_image_type_list_par.power_Doppler.image);
                    video_M0(:, :, :, batch_idx) = tmp_video_M0;
                    video_moment0(:, :, :, batch_idx) = gather(local_image_type_list_par.moment_0.image);
                    video_moment1(:, :, :, batch_idx) = gather(local_image_type_list_par.moment_1.image);
                    video_moment2(:, :, :, batch_idx) = gather(local_image_type_list_par.moment_2.image);
                    images_choroid(:, :, :, batch_idx, :) = gather(local_image_type_list_par.choroid.parameters.intervals);
                    
            end
            
        end
        
        send(D, 0);
    end
    
    
    
    tEndParfor = toc(tParfor);
    fprintf("Parfor loop took %f s\n", tEndParfor)
    
    if strcmp(local_output_video, 'all_videos')
        % generate color video
        if local_low_frequency
            video_color = construct_colored_video(video_M_freq_high, video_M_freq_low);
        else
            video_color = construct_colored_video(video_M_freq_low, video_M_freq_high);
        end
        
        % generate directional video
        
    end
    
    if app.cache.registration
        % post reconstruction image registration.
        % This registration is performed on the final video,
        % it does not use tilts zernikes to perform the
        % registration.
        tRegistration = tic;
        fprintf("Registration...\n")
        
        % If iterative registration import last registration before
        % calculating the next one
        
        if size(local_image_registration, 2) == local_num_batches && app.cache.iterative_registration % si iterative registration est activée et une registration précédente a été trouvée
            disp('Importing last registration.')
            video_M0 = register_video_from_shifts(video_M0, local_image_registration(1:2, :));
        end
        
        % construct treshold M0
        Nx = size(video_M0, 1);
        Ny = size(video_M0, 2);
        
        if app.cache.registration_disc
            [X, Y] = meshgrid(linspace(-Nx / 2, Nx / 2, Nx), linspace(-Ny / 2, Ny / 2, Ny));
            disc_ratio = app.cache.registration_disc_ratio;
            disc = X .^ 2 + Y .^ 2 < (disc_ratio * min(Nx, Ny) / 2) ^ 2;
        else
            disc = ones([Nx, Ny]);
        end
        
        disc = disc'; % TODO: Understand
        video_M0_reg = video_M0 .* disc - disc .* sum(video_M0 .* disc, [1, 2]) / nnz(disc); % minus the mean in the disc of each frame
        video_M0_reg = video_M0_reg ./ (max(abs(video_M0_reg), [], [1, 2])); % rescaling each frame but keeps mean at zero
        
        % % construct reference image
        ref_batch_idx = min(floor((app.cache.position_in_file) / app.cache.batch_stride) + 1, size(video_M0, 4));
        
        reg_frame_batch = app.interferogram_stream.read_frame_batch(app.cache.ref_batch_size, floor(ref_batch_idx * app.cache.batch_stride));
        
        switch app.cache.spatialTransformation
            case 'angular spectrum'
                reg_FH = fftshift(fft2(reg_frame_batch)) .* local_kernel;
            case 'Fresnel'
                reg_FH = (reg_frame_batch) .* local_kernel;
        end
        
        reg_FH = rephase_FH(reg_FH, local_rephasing_data, app.cache.ref_batch_size, floor(ref_batch_idx * app.cache.batch_stride));
        acquisition = DopplerAcquisition(app.Nx, app.Ny, app.Fs / 1000, app.cache.z, app.cache.z_retina, app.cache.z_iris, app.cache.wavelength, app.cache.DX, app.cache.DY, app.pix_width, app.pix_height);
        reg_hologram = reconstruct_hologram(reg_FH, acquisition, app.blur, use_gpu, app.SVDCheckBox.Value, app.SVDxCheckBox.Value, app.SVDx_SubApEditField.Value, [], app.time_transform, local_spatialTransformation);
        
        reg_hologram = reg_hologram .* disc - disc .* sum(reg_hologram .* disc, [1, 2]) / nnz(disc); % minus the mean
        reg_hologram = reg_hologram ./ (max(abs(reg_hologram), [], [1, 2])); % rescaling but keeps mean at zero
        
        switch app.cache.spatialTransformation
            case 'Fresnel'
                reg_hologram = flip(flip(reg_hologram, 1), 2);
        end
        
        if app.showrefCheckBox.Value
            frame_ = video_M0_reg(:, :, 1, ref_batch_idx);
            
            figure(7)
            montage({mat2gray(frame_) mat2gray(reg_hologram)})
            title('Current frame vs calculated reference for registration')
            % plot the mean of M0 columns for registration
            plot_columns_reg(video_M0_reg, reg_hologram, output_dirpath);
        end
        
        switch local_output_video
            case 'moments'
                
                if size(local_image_registration, 2) == local_num_batches && ~app.cache.iterative_registration % if registration from previous folder results
                    disp('rendering from old registration')
                    video_M0 = register_video_from_shifts(video_M0, local_image_registration(1:2, :));
                    shifts(1:2, :) = local_image_registration(1:2, :);
                else
                    % FIXME : use "reg_hologram" as reference (current preview from frontend)
                    [video_M0_reg, shifts(1:2, :)] = register_video_from_reference(video_M0_reg, reg_hologram);
                    video_M0 = register_video_from_shifts(video_M0, shifts(1:2, :));
                end
                
                video_moment0 = register_video_from_shifts(video_moment0, shifts);
                video_moment1 = register_video_from_shifts(video_moment1, shifts);
                video_moment2 = register_video_from_shifts(video_moment2, shifts);
                
            case 'power_Doppler'
                
                if size(local_image_registration, 2) == local_num_batches && ~app.cache.iterative_registration % if registration from previous folder results
                    video_M0 = register_video_from_shifts(video_M0, local_image_registration(1:2, :));
                    shifts(1:2, :) = local_image_registration(1:2, :);
                else
                    % FIXME : use "reg_hologram" as reference (current preview from frontend)
                    [video_M0_reg, shifts(1:2, :)] = register_video_from_reference(video_M0_reg, reg_hologram);
                    video_M0 = register_video_from_shifts(video_M0, shifts(1:2, :));
                end
                
            case 'all_videos'
                
                if size(local_image_registration, 2) == local_num_batches && ~app.cache.iterative_registration % if registration from previous folder results
                    video_M0 = register_video_from_shifts(video_M0, local_image_registration(1:2, :));
                    shifts(1:2, :) = local_image_registration(1:2, :);
                else
                    % FIXME : use "reg_hologram" as reference (current preview from frontend)
                    [video_M0_reg, shifts(1:2, :)] = register_video_from_reference(video_M0_reg, reg_hologram);
                    video_M0 = register_video_from_shifts(video_M0, shifts(1:2, :));
                end
                
                video_M1 = register_video_from_shifts(video_M1, shifts);
                video_M2 = register_video_from_shifts(video_M2, shifts);
                video_moment0 = register_video_from_shifts(video_moment0, shifts);
                video_moment1 = register_video_from_shifts(video_moment1, shifts);
                video_moment2 = register_video_from_shifts(video_moment2, shifts);
                video_M1_over_M0 = register_video_from_shifts(video_M1_over_M0, shifts);
                video_M2_over_M0 = register_video_from_shifts(video_M2_over_M0, shifts);
                video_color = register_video_from_shifts(video_color, shifts);
                video_M_freq_high = register_video_from_shifts(video_M_freq_high, shifts);
                video_M_freq_low = register_video_from_shifts(video_M_freq_low, shifts);
                video_M0_pos = register_video_from_shifts(video_M0_pos, shifts);
                video_M0_neg = register_video_from_shifts(video_M0_neg, shifts);
                video_M0sM1r = register_video_from_shifts(video_M0sM1r, shifts);
                video_velocity = register_video_from_shifts(video_velocity, shifts);
                video_directional = register_video_from_shifts(video_directional, shifts);
                video_fmean = register_video_from_shifts(video_fmean, shifts);
            case 'dark_field'
                
                if size(local_image_registration, 2) == local_num_batches % if registration from previous folder results
                    video_M0_dark_field = register_video_from_shifts(video_M0_dark_field, local_image_registration(1:2, :));
                    shifts(1:2, :) = local_image_registration(1:2, :);
                else
                    [video_M0_dark_field, shifts] = register_video_from_reference(video_M0_dark_field, video_M0_dark_field(:, :, :, ref_batch_idx));
                end
                
        end
        
        % save shifts for export
        image_registration.translation_x = shifts(1, :);
        image_registration.translation_y = shifts(2, :);
        image_registration.translation_z = shifts(3, :);
        
        tEndRegistration = toc(tRegistration);
        fprintf("Registration took %f s\n", tEndRegistration)
    end
    
    %% long time processing
    
    export_raw = app.saverawvideosCheckBox.Value;
    
    fprintf("Video generation...\n")
    tVideoGen = tic;
    % FIXME add 'or' statement
    % add colors to M0_registration
    video_M0_reg = cat(3, rescale(video_M0_reg), repmat(rescale(reg_hologram), [1, 1, 1, size(video_M0, 4)]), rescale(video_M0(:, :, 1, :))); % new in red, ref in green, old in blue
    
    switch local_output_video
        case 'power_Doppler'
            generate_video(video_M0, output_dirpath, 'M0', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, 1);
            generate_video(video_M0_reg, output_dirpath, 'M0_registration', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, 1);
        case 'moments'
            generate_video(video_M0, output_dirpath, 'M0', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, 1);
            generate_video(video_M0_reg, output_dirpath, 'M0_registration', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, 1);
            generate_video(video_moment0, output_dirpath, 'moment0', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, 1);
            generate_video(video_moment1, output_dirpath, 'moment1', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, 1);
            generate_video(video_moment2, output_dirpath, 'moment2', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, 1);
            
        case 'all_videos'
            generate_video(video_M0, output_dirpath, 'M0', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, 1);
            generate_video(video_M0_reg, output_dirpath, 'M0_registration', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, 1);
            
            generate_video(video_moment0, output_dirpath, 'moment0', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, 1);
            generate_video(video_moment1, output_dirpath, 'moment1', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, 1);
            generate_video(video_moment2, output_dirpath, 'moment2', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, 1);
            
            generate_video(video_M1_over_M0, output_dirpath, 'NormalizedDopplerAVG', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, 1);
            generate_video(video_M2_over_M0, output_dirpath, 'NormalizedDopplerRMS', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, 1);
            
            % no contrast enhancement for color video, it's already
            % been done previously
            generate_video(video_color, output_dirpath, 'Color', [], app.cache.temporal_filter, local_low_frequency, 0, 1);
            generate_video(video_directional, output_dirpath, 'Directional', [], [], false, 0);
            generate_video(video_fmean, output_dirpath, 'Fmean', [], [], false, 0);
            generate_video(video_M0_pos, output_dirpath, 'M0pos', [], app.cache.temporal_filter, local_low_frequency, 0, 1);
            generate_video(video_M0_neg, output_dirpath, 'M0neg', [], app.cache.temporal_filter, local_low_frequency, 0, 1);
            generate_video(video_velocity, output_dirpath, 'Velocity', [], app.cache.temporal_filter, local_low_frequency, 0, 1);
            
            SH_time = reshape(SH_time, size(SH_time, 1), size(SH_time, 2), size(SH_time, 3), size(SH_time, 4) * size(SH_time, 5));
            generate_video(SH_time, output_dirpath, 'SH', [], [], false, true, 1);
            
            if enable_shack_hartmann
                % phase video
                video_phase = correction_phase_video(aberration_correction, app.Nx, app.Ny);
                video_measured_phase = mesured_phase_video(shifts_vector, num_subapertures_positions, measured_phase);
                video_PSF2D = PSF2D_video(aberration_correction, app.Nx, app.Ny);
                generate_video(video_measured_phase, output_dirpath, 'MeasuredPhase', [], [], false, false, 1);
                generate_video(video_phase, output_dirpath, 'ZernikePhase', [], [], false, false, 1);
                generate_video(video_PSF2D, output_dirpath, 'PSF2D', [], [], false, false, 1);
                generate_video(stiched_moments_video, output_dirpath, 'StichedMoments', [], [], false, false, 1);
                generate_video(stitched_correlation_video, output_dirpath, 'StichedCorrelations', [], [], false, false, 1);
            end
            
            % generate additional images
            
            [color_img, img_low_freq, img_high_freq] = construct_colored_image(video_M_freq_low, video_M_freq_high);
            
            % convert spectrogram_matrix_video to one spectrogram
            %                     spectrogram_matrix_video = squeeze(spectrogram_matrix_video(:,:,:,1));%reshape(spectrogram_matrix_video, app.Nx, app.Ny, j_win * local_num_batches);
            %                     S_video = (fft(spectrogram_matrix_video, [], 3));
            %
            %                         S_video = squeeze(mean(abs(spectrogram_matrix_video), 2));
            %                         figure(1);
            %                         set(figure(1), 'Visible', 'off');
            %                         plot(S_video);
            
            color_output_filename = sprintf('%s_%s.%s', output_dirname, 'Color', 'png');
            img_low_freq_output_filename = sprintf('%s_%s.%s', output_dirname, 'M0_high_flow', 'png');
            img_high_freq_output_filename = sprintf('%s_%s.%s', output_dirname, 'M0_low_flow', 'png');
            
            imwrite(color_img, fullfile(output_dirpath, 'png',  color_output_filename));
            imwrite(img_low_freq, fullfile(output_dirpath, 'png',  img_low_freq_output_filename));
            imwrite(img_high_freq, fullfile(output_dirpath, 'png',  img_high_freq_output_filename));
            imwrite(RI, fullfile(output_dirpath, 'png',  RI_output_filename));
            % imwrite(mat2gray((abs(spectrogram_array.^2))), fullfile(output_dirpath, 'png',  'spectrogram_artery.png'));
            
        case 'dark_field'
            generate_video(video_M0_dark_field, output_dirpath, 'M0_dark_field', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, 1);
            
            %                         [file_name, suffix] = get_last_file_name(app.filepath, 'H_dark_field_stack');
            %                         output_dirname_df = sprintf('%s%s_%d.mat', app.filepath, 'H_dark_field_stack', suffix + 1);
            output_dirname_df = fullfile(app.filepath, output_dirname, 'mat', 'H_dark_field_stack.mat');
            save(output_dirname_df, 'H_dark_field_stack', '-v7.3');
            
        case 'choroid'
            generate_video(video_M0, output_dirpath, 'M0', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, 1);
            generate_video(video_M0_reg, output_dirpath, 'M0_registration', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, 1);
            generate_video(video_moment0, output_dirpath, 'moment0', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, 1);
            generate_video(video_moment1, output_dirpath, 'moment1', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, 1);
            generate_video(video_moment2, output_dirpath, 'moment2', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, 1);
            for freq_idx = 1:num_F
                generate_video(images_choroid(:, :, :, :, freq_idx), output_dirpath, sprintf('choroid_%d', freq_idx), 0.0005, app.cache.temporal_filter, local_low_frequency, 0, 1, NoIntensity=1);
            end
            
    end
    
    tEndVideoGen = toc(tVideoGen);
    fprintf("Video Generation took %f s\n", tEndVideoGen)
    
end % local_low_memory

    function update_waitbar(sig)
        % signal table
        % 0 => increment value
        % 1 => reset for stage 1 (registration)
        % 2 => reset for stage 2 (video_M0 computation)
        switch sig
            case 0
                waitbar(p / N, h);
                p = p + 1;
            case -1
                waitbar(0, h, 'Translation registration...');
                p = 1;
                disp('Translation registration...')
            case -2
                waitbar(0, h, 'Image rendering...');
                p = 1;
                disp('Image rendering...')
            case 1
                waitbar(0, h, 'Optimizing defocus...');
                p = 1;
                disp('Optimizing defocus...')
            case 2
                waitbar(0, h, 'Optimizing astigmatism...');
                p = 1;
                disp('Optimizing astigmatism...')
            case 3
                waitbar(0, h, 'Shack-Hartmann...')
                p = 1;
                disp('Shack-Hartmann...')
            otherwise
                waitbar(0, h, 'Iterative optimization...');
                p = 1;
                disp('Iterative optimization')
        end
        
    end

fprintf("Additional data export...\n")

% export shifts to AberrationCorrection struct as zernikes
if registration_pass || app.cache.registration
    magic_number = 710;
    aberration_correction.rephasing_zernike_indices = [1 2];
    aberration_correction.rephasing_zernike_coefs = [shifts(1, :) / local_Nx; shifts(2, :) / local_Ny] * magic_number * 2;
    aberration_correction.rephasing_in_z_coefs = shifts(3, :) / j_win * magic_number * 2;
end

numX = size(images_choroid, 1);
numY = size(images_choroid, 2);
[X, Y] = meshgrid(1:X, 1:Y);
L = (numX + numY) / 2;
mkdir(fullfile(output_dirpath, 'txt'));
fileID = fopen(fullfile(output_dirpath, 'txt', 'intervals.txt'),'w');

meanIm = mean(images_choroid(:, :, :, :, freq_idx), [3 4]);
maskDiaphragm = ((X-numX/2)^2 + (Y-numY/2)^2) < L * 0.4;
T = graythresh(meanIm);
for freq_idx = 1:num_F
    meanIm = mean(images_choroid(:, :, :, :, freq_idx), [3 4]);
    binIm = imbinarize(meanIm, T);
    fprintf(fileID, "Interval %d: %0.2d%%\n", freq_idx, 100 * nnz(binIm .* maskDiaphragm) / (nnz(maskDiaphragm)));
end
fclose(fileID);

% add computed correction to rephasing data
new_rephasing_data = RephasingData(app.cache.batch_size, app.cache.batch_stride, aberration_correction);
new_rephasing_data = new_rephasing_data.compute_frame_ranges();
% update rephasing array
rephasing_data = [local_rephasing_data new_rephasing_data];

% export patient informations to text file_M0

% export some workspace variables to .mat file
mat_filename = sprintf('%s.mat', output_dirname);
cache = app.cache;

if exist(fullfile(output_dirpath, 'mat'), 'dir')
    output_dirpath_mat = fullfile(output_dirpath, 'mat');
else
    output_dirpath_mat = output_dirpath;
end

save(fullfile(output_dirpath_mat, mat_filename), 'cache');

% export the most useful parameters to a json file in the log
% folder

s = struct();
s.wavelength = cache.wavelength;
s.fs = cache.Fs;
s.time_transform = cache.time_transform;
s.spatial_transform = cache.spatialTransformation;
s.depth.z = cache.(cache.z_switch);
s.depth.z_switch = cache.z_switch;
s.batch_size = cache.batch_size;
s.ref_batch_size = cache.ref_batch_size;
s.batch_stride = cache.batch_stride;
s.SVD = cache.SVD;
s.SVDx = local_SVDx;
s.SVDxSubAp = local_SVDx_SubAp_num;
JSON_parameters = jsonencode(s, PrettyPrint = true);
fid = fopen(fullfile(output_dirpath, 'log', 'RenderingParameters.json'), "wt+");
fprintf(fid, JSON_parameters);
fclose(fid);
%             disp(s)

save(fullfile(output_dirpath_mat, mat_filename), 'aberration_correction', '-append');
save(fullfile(output_dirpath_mat, mat_filename), 'image_registration', '-append');

if app.cache.rephasing
    save(fullfile(output_dirpath_mat, mat_filename), 'rephasing_data', '-append');
end

% save(fullfile(output_dirpath, mat_filename), 'cache');
%
% save(fullfile(output_dirpath, mat_filename), 'aberration_correction', '-append');
% save(fullfile(output_dirpath, mat_filename), 'image_registration', '-append');
%
% if app.cache.rephasing
%     save(fullfile(output_dirpath, mat_filename), 'rephasing_data', '-append');
% end

%%Saving of power data for normalization, PNG/VIDEO & TXT files %%
%PNG/VIDEO%

if ~isempty(app.NotesTextArea.Value)
    disp(app.NotesTextArea.Value)
end

% close progress bar window
close(h);

fprintf("End Computer Time: %s\n", datetime('now', 'Format', 'yyyy/MM/dd HH:mm:ss'))
% display elapsed time
toc;

% disable diary
diary off;
end
